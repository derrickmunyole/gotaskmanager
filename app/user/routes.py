import jwt
import datetime
from flask import Blueprint, request, jsonify, current_app
from flask_login import current_user, login_user, login_required
from werkzeug.security import generate_password_hash

from .model import User
from .. import db

bp = Blueprint('user', __name__)


@bp.route('/login', methods=['POST'])
def login():
    if current_user.is_authenticated:
        return jsonify({'success': True, 'message': 'Already logged in'}), 200

    data = request.get_json()
    username = data['username']
    password = data['password']

    user = User.query.filter_by(username=username).first()
    if user and user.check_password(password):
        login_user(user)

        token = jwt.encode({
            'user_id': user.id,
            'exp': datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1)
        }, current_app.config['SECRET_KEY'], algorithm='HS256')

        return jsonify({'success': True, 'message': 'Logged in', 'token': token}), 200
    else:
        return jsonify({'success': False, 'message': 'Invalid username or password'}), 401


@bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if User.query.filter_by(username=username).first() is not None:
        return jsonify({{'success': False, 'message': 'Username already exists'}}), 401

    if User.query.filter_by(email=email).first() is not None:
        return jsonify({{'success': False, 'message': 'Email already exists'}}), 401

    new_user = User(
        username=username,
        email=email,
        password_hash=generate_password_hash(password)
    )

    db.session.add(new_user)
    db.session.commit()

    return jsonify({'success': True, 'message': 'User registered successfully'}), 201


@bp.route('/update', methods=['PUT'])
@login_required
def update_user():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('username')

    if not username and not email and not password:
        return jsonify({'message': 'No data provided to update', 'success': False}), 401

    user = User.query.get(current_user.id)

    if username:
        if User.query.filter_by('username').first() is None:
            return jsonify({'message': 'Username already exists', 'success': False}), 401
        user.username = username

    if email:
        if User.query.filter_by('email').first() is not None:
            return jsonify({'message': 'Email already exists', 'success': False}), 401
        user.email = email

    if password:
        user.password_hash = generate_password_hash(password)

    db.session.commit()

    return jsonify({'success': True, 'message': 'User information updated successfully'}), 200



