from sqlalchemy import DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from app import db
from app.utils.db_utils import UtcNow

Base = declarative_base()


class RefreshToken(Base,db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    token = db.Column(db.String(255), unique=True, nullable=False)
    session_id = db.Column(db.String(255), unique=True, nullable=False)
    created_at = db.Column(DateTime(timezone=True), nullable=False, server_default=UtcNow())
    expires_at = db.Column(DateTime(timezone=True), nullable=False)
    user = db.relationship('User', back_populates='refresh_tokens')
