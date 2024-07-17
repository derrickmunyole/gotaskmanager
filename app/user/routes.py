import datetime
import logging
from functools import wraps

import jwt
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required
from flask_restx import Namespace, Resource, fields
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from werkzeug.exceptions import BadRequest
from werkzeug.security import generate_password_hash
from http import HTTPStatus

from .model import User
from .. import db

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


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization', None)
        if not token:
            return jsonify({'message': 'Token is missing!'}), HTTPStatus.FORBIDDEN
        try:
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user = data['user']
        except Exception as e:
            return jsonify({'message': str(e)}), HTTPStatus.FORBIDDEN
        return f(current_user, *args, **kwargs)

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
            username = data.get('username')
            password = data.get('password')

            user = User.query.filter_by(username=username).first()
            if user is None:
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
                'exp': datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=30)
            }, current_app.config['SECRET_KEY'], algorithm='HS256')

            refresh_token = jwt.encode({
                'user_id': 1,
                'exp': datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=30)
            }, current_app.config['REFRESH_SECRET_KEY'], algorithm='HS256')

            refresh_tokens[refresh_token] = 1

            return {
                'success': True,
                'message': 'Logged in successfully!',
                'access_token': access_token,
                'refresh_token': refresh_token
            }, HTTPStatus.OK
        except BadRequest as e:
            return {
                'success': False,
                'message': 'Invalid request: {}'.format(e)
            }, HTTPStatus.BAD_REQUEST
        except Exception as e:
            return {
                'success': False,
                'message': 'There was an error while trying to log in: {}'.format(e)
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

        except BadRequest as e:
            return {
                'success': False,
                'message': f'Invalid request: {str(e)}'
            }, HTTPStatus.BAD_REQUEST

        except SQLAlchemyError as e:
            logger.error("Database error while registering user", exc_info=True)
            return {
                'success': False,
                'error': "Database error occurred. Please try again later."
            }, HTTPStatus.INTERNAL_SERVER_ERROR

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Registration error: {str(e)}')
            return {
                'success': False,
                'message': 'An unexpected error occurred'
            }, HTTPStatus.INTERNAL_SERVER_ERROR


@ns.route('/update')
class UpdateUser(Resource):
    @ns.expect(user_update_model)
    @ns.response(200, 'Update successful', user_update_model)
    @ns.response(400, 'Bad request', user_update_model)
    @ns.response(401, 'Update failed', user_update_model)
    @ns.response(500, 'Internal server error', user_update_model)
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
    @ns.response(200, 'Logged out successfully', user_logout_model)
    @ns.response(400, 'Bad request', user_logout_model)
    @ns.response(401, 'Logout failed', user_logout_model)
    @ns.response(500, 'Internal server error', user_logout_model)
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
