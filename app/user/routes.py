import logging
import secrets
from datetime import timedelta
from functools import wraps
from http import HTTPStatus

from cryptography.fernet import Fernet
from flask import Blueprint, request, jsonify, current_app, make_response
from flask_login import login_required
from flask_restx import Namespace, Resource, fields, abort
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.exceptions import BadRequest
from werkzeug.security import generate_password_hash

from app.models import User, Session
from app.session_manager import SessionManager
from .. import db

logger = logging.getLogger(__name__)
bp = Blueprint('user', __name__)
ns = Namespace('user', description='User related operations')

user_login_model = ns.model('UserLogin', {
    'username': fields.String(required=True, description='Username'),
    'password': fields.String(required=True, description='Password')
})

user_register_model = ns.model('UserRegister', {
    'username': fields.String(required=True, description='The username'),
    'email': fields.String(required=True, description='The email'),
    'password': fields.String(required=True, description='The password')
})

user_update_model = ns.model('UserUpdate', {
    'username': fields.String(description='The username'),
    'email': fields.String(description='The email'),
    'password': fields.String(description='The password')
})

user_logout_model = ns.model('UserLogout', {
    'refresh_token': fields.String(required=True, description='Refresh Token')
})

refresh_session_model = ns.model('RefreshSession', {
    # This model is intentionally left empty because we're using cookies for the session ID
})

refresh_session_response_model = ns.model('RefreshSessionResponse', {
    'success': fields.Boolean(description='Indicates if the session refresh was successful'),
    'message': fields.String(description='A message describing the result of the operation')
})

user_model = ns.model('User', {
    'id': fields.Integer,
    'first_name': fields.String,
    'last_name': fields.String,
    'email': fields.String,
    'username': fields.String
})


def session_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        encrypted_session_id = request.cookies.get('session_id')

        print(encrypted_session_id)

        if not encrypted_session_id:
            abort(HTTPStatus.UNAUTHORIZED, 'Session ID is missing!')

        try:
            # Decrypt the session ID
            fernet_key = Fernet(current_app.config['FERNET_KEY'].encode())
            session_id = fernet_key.decrypt(encrypted_session_id.encode('ascii')).decode('utf-8')

            print(f'Decrypted SessionId: {session_id}')

            if not SessionManager.is_session_valid(session_id):
                abort(HTTPStatus.UNAUTHORIZED, 'Invalid or expired session')

            SessionManager.renew_session(session_id)

            session = Session.query.filter_by(session_id=session_id).first()

            print(f'SESSION: {session}')
            current_user = User.query.get(session.user_id)

            print(f'CURRENT USER: {current_user}')
            if not current_user:
                abort(HTTPStatus.UNAUTHORIZED, 'User not found')

            return f(*args, current_user=current_user, **kwargs)

        except Exception as e:
            abort(HTTPStatus.UNAUTHORIZED, str(e))

    return decorated


# Constants for session durations
SESSION_DURATION = timedelta(days=14)
COOKIE_NAME_SESSION_ID = 'session_id'


@ns.route('/login')
class UserLogin(Resource):
    @ns.expect(user_login_model)
    @ns.response(HTTPStatus.OK, 'Success', user_login_model)
    @ns.response(HTTPStatus.UNAUTHORIZED, 'Login failed', user_login_model)
    @ns.response(HTTPStatus.INTERNAL_SERVER_ERROR, 'Internal server error')
    @ns.response(HTTPStatus.BAD_REQUEST, 'Bad request', user_login_model)
    def post(self):
        try:
            data = request.get_json()
            email = data.get('email')
            password = data.get('password')

            current_app.logger.info(f"Login attempt for email: {email}")

            user = User.query.filter_by(email=email).first()
            if user is None:
                current_app.logger.warning(f"User not found for email: {email}")
                return {
                    'success': False,
                    'message': 'User not found. Please register first.'
                }, HTTPStatus.NOT_FOUND

            if not user.check_password(password):
                return {
                    'success': False,
                    'message': 'Incorrect password. Please try again.'
                }, HTTPStatus.UNAUTHORIZED

            session_id = secrets.token_urlsafe(32)

            SessionManager.create_session(user.id, session_id)

            fernet_key = Fernet(current_app.config['FERNET_KEY'])
            encrypted_session_id = fernet_key.encrypt(session_id.encode('ascii')).decode('utf-8')

            response = make_response({
                'success': True,
                'message': 'Successfully logged in.'
            })

            # Set the encrypted session ID as an HTTPOnly cookie
            response.set_cookie(
                COOKIE_NAME_SESSION_ID,
                encrypted_session_id,
                httponly=True,
                secure=True,  # Use this in production with HTTPS
                samesite='Lax',
                max_age=int(SESSION_DURATION.total_seconds())
            )

            return response
        except Exception as e:
            current_app.logger.error(f"Login error: {str(e)}")
            return {
                'success': False,
                'message': 'An error occurred during login.'
            }, HTTPStatus.INTERNAL_SERVER_ERROR


@ns.route('/register')
class UserRegister(Resource):
    @ns.expect(user_register_model)
    @ns.response(HTTPStatus.CREATED, 'Registration successful')
    @ns.response(HTTPStatus.CONFLICT, 'User already exists')
    @ns.response(HTTPStatus.BAD_REQUEST, 'Bad request')
    @ns.response(HTTPStatus.INTERNAL_SERVER_ERROR, 'Internal server error')
    def post(self):
        try:
            data = request.get_json()
            username = data.get('username')
            first_name = data.get('first_name')
            last_name = data.get('last_name')
            email = data.get('email')
            password = data.get('password')

            if not all([username, first_name, last_name, email, password]):
                return {
                    'success': False,
                    'message': 'Missing required fields'
                }, HTTPStatus.BAD_REQUEST

            existing_user = User.query.filter(
                (User.username == username) | (User.email == email)
            ).first()

            if existing_user:
                return {
                    'success': False,
                    'message': 'Username or email already exists'
                }, HTTPStatus.CONFLICT

            new_user = User(
                first_name=first_name,
                last_name=last_name,
                username=username,
                email=email
            )
            new_user.set_password(password)

            db.session.add(new_user)
            db.session.commit()

            return {
                'success': True,
                'message': 'Registered successfully!'
            }, HTTPStatus.CREATED

        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Database error while registering user: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': "Database error occurred. Please try again later."
            }, HTTPStatus.INTERNAL_SERVER_ERROR
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Registration error: {str(e)}', exc_info=True)
            return {
                'success': False,
                'message': 'An unexpected error occurred'
            }, HTTPStatus.INTERNAL_SERVER_ERROR


@ns.route('/refresh-session')
class RefreshSession(Resource):
    @ns.expect(refresh_session_model)
    @ns.response(HTTPStatus.OK, 'Success', refresh_session_response_model)
    @ns.response(HTTPStatus.BAD_REQUEST, 'Bad request')
    @ns.response(HTTPStatus.UNAUTHORIZED, 'Unauthorized')
    def post(self):
        try:
            # Get the encrypted session ID from the cookie

            encrypted_session_id = request.cookies.get('session_id')

            if not encrypted_session_id:
                return {'message': 'No session ID provided'}, HTTPStatus.UNAUTHORIZED

            # Decrypt the session ID
            fernet_key = Fernet(current_app.config['FERNET_KEY'])
            session_id = fernet_key.decrypt(encrypted_session_id.encode('ascii')).decode('utf-8')

            # Use the SessionManager to validate and refresh the session
            if SessionManager.is_session_valid(session_id):
                # Renew the session
                SessionManager.renew_session(session_id)

                # Get the user associated with this session
                session = Session.query.filter_by(session_id=session_id).first()
                user = User.query.get(session.user_id)

                response = make_response({
                    'success': True,
                    'message': 'Session refreshed successfully'
                })

                # Optionally, you might want to issue a new session ID for added security
                new_session_id = secrets.token_urlsafe(32)
                SessionManager.update_session_id(session_id, new_session_id)

                encrypted_new_session_id = fernet_key.encrypt(new_session_id.encode('ascii')).decode('utf-8')

                response.set_cookie('session_id',
                                    encrypted_new_session_id,
                                    httponly=True,
                                    secure=True,
                                    samesite='Lax',
                                    max_age=int(SESSION_DURATION.total_seconds())
                                    )

                return response

            else:
                return {'message': 'Invalid or expired session'}, HTTPStatus.UNAUTHORIZED

        except Exception as e:
            current_app.logger.error(f"Session refresh error: {str(e)}")
            return {'message': 'An error occurred while refreshing the session'}, HTTPStatus.INTERNAL_SERVER_ERROR


@ns.route('/update')
class UpdateUser(Resource):
    @ns.expect(user_update_model)
    @ns.response(HTTPStatus.OK, 'Update successful', user_update_model)
    @ns.response(HTTPStatus.BAD_REQUEST, 'Bad request', user_update_model)
    @ns.response(HTTPStatus.UNAUTHORIZED, 'Update failed', user_update_model)
    @ns.response(HTTPStatus.INTERNAL_SERVER_ERROR, 'Internal server error', user_update_model)
    @login_required
    def post(self):
        try:
            data = request.get_json()
            username = data.get('username')
            email = data.get('email')
            password = data.get('password')

            if not username and not email and not password:
                return jsonify({
                    'message': 'No data provided to update',
                    'success': False
                }), 401

            user = User.query.filter_by(username=username).first()

            if username:
                if User.query.filter_by(username=username).first() is not None:
                    return {
                        'success': False,
                        'message': 'Username already exists'
                    }, 401
                user.username = username

            if email:
                if User.query.filter_by(email=email).first() is not None:
                    return {
                        'success': False,
                        'message': 'Email already exists'
                    }
                user.email = email

            if password:
                user.password_hash = generate_password_hash(password)

            db.session.commit()
            return {
                'success': True,
                'message': 'User information updated successfully'
            }, 200
        except BadRequest as e:
            return {
                'success': False,
                'message': 'Invalid request: {}'.format(e)
            }, 400
        except SQLAlchemyError as e:
            db.session.rollback()
            return {
                'success': False,
                'message': 'Database error: ' + str(e)
            }, 500
        except Exception as e:
            logger.error({
                'success': False,
                'message': 'There was an error updating your data!'
            }, exc_info=e), 500


@ns.route('/logout')
class UserLogout(Resource):
    @ns.expect(user_logout_model)
    @ns.response(HTTPStatus.OK, 'Logged out successfully', user_logout_model)
    @ns.response(HTTPStatus.BAD_REQUEST, 'Bad request', user_logout_model)
    @ns.response(HTTPStatus.UNAUTHORIZED, 'Logout failed', user_logout_model)
    @ns.response(HTTPStatus.INTERNAL_SERVER_ERROR, 'Internal server error', user_logout_model)
    @session_required
    def post(self, current_user):
        try:
            encrypted_session_id = request.cookies.get('session_id')
            fernet_key = Fernet(current_app.config['FERNET_KEY'].encode())
            session_id = fernet_key.decrypt(encrypted_session_id.encode('ascii')).decode('utf-8')

            if SessionManager.invalidate_session(session_id):
                return jsonify({'message': 'Logged out successfully!'}), 200
            return jsonify({'message': 'Invalid session!'}), 400
        except Exception as e:
            return jsonify({'message': 'There was an error while trying to log out: {}'.format(e)}), 500


@ns.route('/info')
class UserInfo(Resource):
    @session_required
    @ns.response(HTTPStatus.OK, 'Success')
    @ns.response(HTTPStatus.UNAUTHORIZED, 'Unauthorized')
    @ns.marshal_with(user_model)
    def get(self, **kwargs):
        user = kwargs.get('current_user')
        return user, HTTPStatus.OK


@ns.route('/check-auth')
class CheckAuth(Resource):
    @session_required
    def get(self, current_user):
        return {
            'isAuthenticated': True,
            'userId': current_user.id,
            'email': current_user.email
        }
