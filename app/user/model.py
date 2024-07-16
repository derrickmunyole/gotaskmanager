from flask_login import UserMixin
from werkzeug.security import check_password_hash

from app import db


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    username = db.Column(db.String(64), index=True)
    email = db.Column(db.String(120), index=True)
    password_hash = db.Column(db.Text)
    tasks = db.relationship('Task', back_populates="assignee", lazy='dynamic')

    def __init__(self, username, email, password_hash):
        self.username = username
        self.email = email
        self.password_hash = password_hash

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
