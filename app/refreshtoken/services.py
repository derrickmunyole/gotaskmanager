import jwt
from datetime import datetime, timedelta, timezone
from flask import current_app


def generate_new_access_token(user_id):
    return jwt.encode({
        'user_id': user_id,
        'exp': datetime.now(timezone.utc) + timedelta(minutes=15)
    }, current_app.config['SECRET_KEY'], algorithm='HS256')
