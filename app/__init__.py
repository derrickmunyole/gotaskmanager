from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_restx import Api

from config import Config


db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
login.login_view = 'main.login'


@login.user_loader
def load_user(user_id):
    from .user.model import User
    return User.query.get(int(user_id))


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)

    api = Api(app, version='1.0', title='Task Management API', description='An API for a task manager application')

    from app.user import model as user_model
    from app.task import model as task_model
    from app.project import model as project_model
    from app.tag import model as tag_model
    from app.task_tags import model as task_tag_model
    from app.subtask import model as subtask_model
    from app.comment import model as comment_model
    from app.user.routes import bp as user_bp
    from app.task.routes import bp as task_bp

    app.register_blueprint(user_bp, url_prefix='/user')
    app.register_blueprint(task_bp, url_prefix='/task')

    from app.user.routes import ns as user_ns
    from app.task.routes import ns as task_ns
    from app.project.routes import project_ns
    from app.comment.routes import comments_ns
    api.add_namespace(user_ns, path='/user')
    api.add_namespace(task_ns, path='/task')
    api.add_namespace(project_ns, path='/project')
    api.add_namespace(comments_ns, path='/comment')

    return app

