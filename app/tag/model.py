from app import db
from app.task_tags.model import task_tags_m2m


class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    tasks = db.relationship('Task', secondary=task_tags_m2m, back_populates='tags')
