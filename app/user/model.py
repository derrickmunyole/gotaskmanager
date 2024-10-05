from flask_login import UserMixin
from sqlalchemy.orm import declarative_base
from werkzeug.security import check_password_hash, generate_password_hash
from app import db

Base = declarative_base()


class User(Base, UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    username = db.Column(db.String(64), index=True)
    email = db.Column(db.String(120), index=True)
    password_hash = db.Column(db.Text)
    tasks = db.relationship('Task', back_populates="assignee", lazy='dynamic')
    refresh_tokens = db.relationship('RefreshToken', back_populates='user', lazy='dynamic')

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
