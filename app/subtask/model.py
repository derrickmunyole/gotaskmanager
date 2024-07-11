from app import db


class Subtask(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'))
    name = db.Column(db.String(80), unique=True, nullable=False)