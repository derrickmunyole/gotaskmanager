from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from config import Config

db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
login.login_view = 'main.login'


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)

    from app.user import model as user_model
    from app.task import model as task_model
    from app.user.routes import bp as user_bp
    from app.task.routes import bp as task_bp

    app.register_blueprint(user_bp, url_prefix='/user')
    app.register_blueprint(task_bp, url_prefix='/task')

    return app

