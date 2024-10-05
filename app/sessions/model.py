from .. import db
from datetime import datetime, timezone


class Session(db.Model):
    __tablename__ = 'sessions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    session_id = db.Column(db.String(64), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    expires_at = db.Column(db.DateTime, nullable=False)

    def __repr__(self):
        return f'<Session {self.session_id}>'
