import jwt
from sqlalchemy import DateTime, func

from app import db
from datetime import datetime, timezone


class TokenBlacklist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(36), nullable=False, unique=True)
    created_at = db.Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    @classmethod
    def is_blacklisted(cls, token):
        jti = jwt.decode(token, options={"verify_signature": False})['jti']
        return cls.query.filter_by(jti=jti).first() is not None

    @classmethod
    def add(cls, token):
        jti = jwt.decode(token, options={"verify_signature": False})['jti']
        blacklisted_token = cls(jti=jti)
        db.session.add(blacklisted_token)
        db.session.commit()
