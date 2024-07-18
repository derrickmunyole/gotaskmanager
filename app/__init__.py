from flask import Flask
from flask_migrate import Migrate
from flask_restx import Api
from flask_sqlalchemy import SQLAlchemy

from config import Config

db = SQLAlchemy()
migrate = Migrate()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)

    api = Api(app, version='1.0', title='Task Management API', description='An API for a task manager application')

    # Import and register namespaces
    from app.user.routes import ns as user_ns
    from app.task.routes import ns as task_ns
    from app.project.routes import project_ns
    from app.comment.routes import comments_ns
    from app.tag.routes import tags_ns

    api.add_namespace(user_ns, path='/user')
    api.add_namespace(task_ns, path='/task')
    api.add_namespace(project_ns, path='/project')
    api.add_namespace(comments_ns, path='/comment')
    api.add_namespace(tags_ns, path='/tag')

    from app import models

    return app
