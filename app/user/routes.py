import jwt
import datetime
import logging
from flask import Blueprint, request, jsonify, current_app
from flask_login import current_user, login_user, login_required
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.exceptions import BadRequest
from werkzeug.security import generate_password_hash
from flask_restx import Namespace, Resource, fields

from .model import User
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


@ns.route('/login')
class UserLogin(Resource):
    @ns.expect(user_login_model)
    @ns.response(200, 'Success', user_login_model)
    @ns.response(401, 'Login failed', user_login_model)
    @ns.response(500, 'Internal server error')
    @ns.response(400, 'Bad request', user_login_model)
    def post(self):
        try:
            if current_user.is_authenticated:
                return {
                    'success': True,
                    'message': 'You are already logged in!'
                }, 200

            data = request.get_json()
            username = data.get('username')
            password = data.get('password')

            user = User.query.filter_by(username=username).first()
            if user is None:
                return {
                    'success': False,
                    'message': 'User not found. Please register first.'
                }, 404

            if not user.check_password(password):
                return {
                    'success': False,
                    'message': 'Incorrect password. Please try again.'
                }, 401

            jwt_token = jwt.encode({
                'user_id': user.id,
                'exp': datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=30)
            }, current_app.config['SECRET_KEY'], algorithm='HS256')

            return {
                'success': True,
                'message': 'Logged in successfully!',
                'token': jwt_token
            }, 200
        except BadRequest as e:
            return {
                'success': False,
                'message': 'Invalid request: {}'.format(e)
            }, 400
        except Exception as e:
            return {
                'success': False,
                'message': 'There was an error while trying to log in: {}'.format(e)
            }, 500


@ns.route('/register')
class UserRegister(Resource):
    @ns.expect(user_register_model)
    @ns.response(200, 'Registration successful', user_register_model)
    @ns.response(500, 'Internal server error', user_register_model)
    @ns.response(400, 'Bad request', user_register_model)
    @ns.response(401, 'Registration failed', user_register_model)
    def post(self):
        try:
            data = request.get_json()
            username = data.get('username')
            email = data.get('email')
            password = data.get('password')

            if User.query.filter_by(username=username).first():
                return jsonify({
                    'success': False,
                    'message': 'User already exists!'
                }), 401

            if User.query.filter_by(email=email).first():
                return jsonify({
                    'success': False,
                    'message': 'Email already exists!'
                }), 401

            new_user = User(
                username=username,
                email=email,
                password_hash=generate_password_hash(password)
            )

            db.session.add(new_user)
            db.session.commit()

            return {
                'success': True,
                'message': 'Registered successfully!'
            }, 201
        except BadRequest as e:
            return {
                'success': False,
                'message': 'Invalid request: {}'.format(e)
            }, 400
        except SQLAlchemyError as e:
            db.session.rollback()
            return {
                'success': False,
                'message': 'Database error: {}'.format(e)

            }, 500
        except Exception as e:
            logger.error({
                'success': False,
                'message': 'Something went wrong: {}'.format(e)
            }), 500


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

