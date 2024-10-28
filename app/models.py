from sqlalchemy import DateTime
from datetime import datetime, timezone

from app import db
from app.utils.db_utils import UtcNow
from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    username = db.Column(db.String(64), index=True)
    email = db.Column(db.String(120), index=True)
    password_hash = db.Column(db.Text)
    view_mode = db.Column(db.String(80))

    tasks = relationship('Task', back_populates='assignee')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Task(db.Model):
    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime)
    completed = db.Column(db.Boolean, default=False)
    due_date = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    status = db.Column(db.String(80))
    priority = db.Column(db.Integer)

    assignee_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    assignee = relationship('User', back_populates='tasks')

    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'))
    project = relationship('Project', back_populates='tasks')

    tags = relationship('Tag', secondary='task_tags', back_populates='tasks')
    comments = relationship('Comment', back_populates='task')

    estimated_time = db.Column(db.Integer)  # in minutes
    actual_time = db.Column(db.Integer)  # in minutes

    is_recurring = db.Column(db.Boolean, default=False)
    recurrence_pattern = db.Column(db.String(80))  # e.g., "daily", "weekly", "monthly"

    parent_task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'))
    subtasks = db.relationship('Subtask', backref='task')


class Subtask(db.Model):
    __tablename__ = 'subtasks'

    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'))
    name = db.Column(db.String(80), unique=True, nullable=False)


class Project(db.Model):
    __tablename__ = 'projects'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    duration = db.Column(db.Integer)
    deadline = db.Column(db.DateTime)
    status = db.Column(db.String(80))
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))

    tasks = relationship('Task', back_populates='project')


class Tag(db.Model):
    __tablename__ = 'tags'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

    tasks = relationship('Task', secondary='task_tags', back_populates='tags')


class Comment(db.Model):
    __tablename__ = 'comments'

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False)

    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=False)
    task = relationship('Task', back_populates='comments')


# Association table for Task and Tag
task_tags = db.Table('task_tags',
                     db.Column('task_id', db.Integer, db.ForeignKey('tasks.id'), primary_key=True),
                     db.Column('tag_id', db.Integer, db.ForeignKey('tags.id'), primary_key=True)
                     )


class RefreshToken(Base, db.Model):
    __tablename__ = 'refresh_tokens'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    token = db.Column(db.String(255), unique=True, nullable=False)
    session_id = db.Column(db.String(255), unique=True, nullable=False)
    created_at = db.Column(DateTime(timezone=True), nullable=False, server_default=UtcNow())
    expires_at = db.Column(DateTime(timezone=True), nullable=False)
    user = db.relationship('User', backref='refresh_tokens')


class Session(db.Model):
    __tablename__ = 'sessions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    session_id = db.Column(db.String(64), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)

    @staticmethod
    def create(user_id, session_id, expiration_delta):
        return Session(
            user_id=user_id,
            session_id=session_id,
            created_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + expiration_delta
        )

    def __repr__(self):
        return f'<Session {self.session_id}>'
