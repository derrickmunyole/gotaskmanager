from app import db
from app.task_tags.model import task_tags_m2m


class Task(db.Model):
    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime)
    due_date = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    status = db.Column(db.String(80))
    priority = db.Column(db.Integer)

    # Foreign key
    assignee_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'))

    # Relationships
    assignee = db.relationship('User', back_populates='tasks')
    project = db.relationship('Project', back_populates='tasks')
    tags = db.relationship('Tag', secondary=task_tags_m2m, back_populates='tasks')
    comments = db.relationship('Comment', back_populates='tasks')

    estimated_time = db.Column(db.Integer)  # in minutes
    actual_time = db.Column(db.Integer)  # in minutes

    is_recurring = db.Column(db.Boolean, default=False)
    recurrence_pattern = db.Column(db.String(80))  # e.g., "daily", "weekly", "monthly"

    parent_task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'))
    subtasks = db.relationship('Subtask', backref='task')
