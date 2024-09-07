import logging
import secrets
import uuid
from datetime import datetime, timezone, timedelta
from functools import wraps
from http import HTTPStatus

import jwt
from cryptography.fernet import Fernet
from flask import Blueprint, request, jsonify, current_app, make_response
from flask_login import login_required
from flask_restx import Namespace, Resource, fields, abort
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.exceptions import BadRequest
from werkzeug.security import generate_password_hash

from .model import User
from .. import db
from ..refreshtoken.model import RefreshToken
from ..tokenblacklist.model import TokenBlacklist

refresh_tokens = {}  # TODO: This should be a persistent store in production

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

refresh_token_model = ns.model('RefreshTokenInput', {
    'session_id': fields.String(required=True, description='Encrypted Session ID')
})

user_model = ns.model('User', {
    'id': fields.Integer,
    'first_name': fields.String,
    'last_name': fields.String,
    'email': fields.String,
    'username': fields.String
})


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        encrypted_token = request.cookies.get('access_token')

        if not encrypted_token:
            abort(HTTPStatus.UNAUTHORIZED, 'Token is missing!')

        try:
            # Decrypt the token
            fernet_key = Fernet(current_app.config['FERNET_KEY'].encode())
            decrypted_token = fernet_key.decrypt(encrypted_token.encode('ascii')).decode('utf-8')

            # Decode the JWT token
            data = jwt.decode(decrypted_token, current_app.config['SECRET_KEY'], algorithms=['HS256'])

            # Convert exp to a timezone-aware datetime
            exp_datetime = datetime.fromtimestamp(data['exp'], tz=timezone.utc)

            # Compare with the current UTC time
            if exp_datetime < datetime.now(timezone.utc):
                return jsonify({'message': 'Token has expired'}), 401

            # Check if the token is blacklisted
            if TokenBlacklist.is_blacklisted(decrypted_token):
                abort(HTTPStatus.UNAUTHORIZED, 'Token has been invalidated')

            # Get the current user
            current_user = User.query.get(data['user_id'])
            if not current_user:
                abort(HTTPStatus.UNAUTHORIZED, 'User not found')

            return f(*args, current_user=current_user, **kwargs)

        except jwt.ExpiredSignatureError:
            abort(HTTPStatus.UNAUTHORIZED, 'Token has expired')
        except (jwt.InvalidTokenError, Exception) as e:
            abort(HTTPStatus.UNAUTHORIZED, str(e))

    return decorated


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

            access_token = jwt.encode({
                'user_id': user.id,
                'exp': datetime.now(timezone.utc) + timedelta(minutes=30),
                'jti': str(uuid.uuid4())
            }, current_app.config['SECRET_KEY'], algorithm='HS256')

            # Generate a unique session ID
            session_id = secrets.token_urlsafe(32)
            print(f"Type: {type(session_id)} Value: {session_id}")

            # Generate a refresh token
            refresh_token = secrets.token_urlsafe(64)

            # Create a new RefreshToken instance
            new_refresh_token = RefreshToken(
                user_id=user.id,
                token=refresh_token,
                session_id=session_id,
                created_at=datetime.now(timezone.utc),
                expires_at=datetime.now(timezone.utc) + timedelta(minutes=30)
            )

            # Add and commit the new refresh token to the database
            db.session.add(new_refresh_token)
            db.session.commit()

            fernet_key = Fernet(current_app.config['FERNET_KEY'])

            encrypted_access_token = fernet_key.encrypt(access_token.encode('ascii')).decode('utf-8')
            encrypted_session_id = fernet_key.encrypt(session_id.encode('ascii')).decode('utf-8')

            response = make_response({
                'success': True,
                'message': 'Successfully logged in.',
                'session_id': encrypted_session_id
            })

            response.set_cookie(
                'access_token',
                encrypted_access_token,
                httponly=True,
                secure=True,
                samesite='Strict',
                max_age=1800
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
    @token_required
    def post(self, current_user):
        try:
            data = request.get_json()
            refresh_token = data.get('refresh_token')
            if refresh_token in refresh_tokens:
                del refresh_tokens[refresh_token]
                return jsonify({'message': 'Logged out successfully!'}), 200
            return jsonify({'message': 'Invalid refresh token!'}), 400
        except Exception as e:
            return jsonify({'message': 'There was an error while trying to log out: {}'.format(e)}), 500


@ns.route('/refresh-token')
class RefreshTokenResource(Resource):
    @ns.expect(refresh_token_model)
    @ns.response(HTTPStatus.OK, 'Token refreshed successfully')
    @ns.response(HTTPStatus.BAD_REQUEST, 'Invalid session')
    @ns.response(HTTPStatus.UNAUTHORIZED, 'Unauthorized')
    def post(self):
        try:
            encrypted_session_id = request.json.get('session_id')
            current_app.logger.info(f"Received refresh token request with session_id: {encrypted_session_id}")

            if not encrypted_session_id:
                current_app.logger.warning("Session ID is missing in the request")
                return {'error': 'Session ID is missing'}, HTTPStatus.BAD_REQUEST

            # Decrypt the session ID
            fernet_key = Fernet(current_app.config['FERNET_KEY'])
            try:
                session_id = fernet_key.decrypt(encrypted_session_id.encode('ascii')).decode('utf-8')
                current_app.logger.info(f"Decrypted session ID: {session_id}")
            except Exception as decrypt_error:
                current_app.logger.error(f"Failed to decrypt session ID: {str(decrypt_error)}")
                return {'error': 'Invalid session ID'}, HTTPStatus.BAD_REQUEST

            refresh_token_entry = RefreshToken.query.filter_by(session_id=session_id).first()

            if not refresh_token_entry:
                current_app.logger.warning(f"No refresh token found for session ID: {session_id}")
                return {'error': 'Invalid session'}, 400

            # Check if the refresh token has expired
            if refresh_token_entry.created_at.replace(tzinfo=timezone.utc) + timedelta(days=7) < datetime.now(
                    timezone.utc):
                current_app.logger.warning(f"Refresh token expired for session ID: {session_id}")
                return {'error': 'Refresh token expired'}, 401

            # Generate new access token
            new_access_token = jwt.encode({
                'user_id': refresh_token_entry.user_id,
                'exp': datetime.now(timezone.utc) + timedelta(minutes=30),
                'jti': str(uuid.uuid4())
            }, current_app.config['SECRET_KEY'], algorithm='HS256')

            # Generate new refresh token but keep the same session ID
            new_refresh_token = secrets.token_urlsafe(64)

            # Update the refresh token in the database
            refresh_token_entry.token = new_refresh_token
            refresh_token_entry.created_at = datetime.now(timezone.utc)
            refresh_token_entry.expires_at = datetime.now(timezone.utc) + timedelta(days=7)
            db.session.commit()

            updated_entry = RefreshToken.query.filter_by(session_id=session_id).first()
            if updated_entry and updated_entry.token == new_refresh_token:
                current_app.logger.info(f"Successfully updated refresh token for session ID: {session_id}")
            else:
                current_app.logger.warning(f"Failed to update refresh token for session ID: {session_id}")

            # Encrypt the new access token
            encrypted_access_token = fernet_key.encrypt(new_access_token.encode()).decode('utf-8')

            # Create response with the same encrypted session ID
            response = make_response(jsonify({
                'message': 'Token refreshed',
                'session_id': encrypted_session_id  # Use the same encrypted session ID
            }))

            # Set the new encrypted access token as a secure cookie
            response.set_cookie(
                'access_token',
                encrypted_access_token,
                httponly=True,
                secure=True,
                samesite='Strict',
                max_age=1800  # 30 minutes
            )

            return response

        except Exception as e:
            current_app.logger.error(f"Refresh token error: {str(e)}")
            return {'error': 'An error occurred while refreshing the token'}, 500


@ns.route('/info')
class UserInfo(Resource):
    @token_required
    @ns.response(HTTPStatus.OK, 'Success')
    @ns.response(HTTPStatus.UNAUTHORIZED, 'Unauthorized')
    @ns.marshal_with(user_model)
    def get(self, **kwargs):
        user = kwargs.get('current_user')
        return user, HTTPStatus.OK
