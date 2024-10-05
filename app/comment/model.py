from datetime import datetime, timezone

from app import db


class Comment(db.Model):
    __tablename__ = 'comments'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    content = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    task = db.relationship('Task', back_populates='comments')
