from flask import Flask, request
from flask_migrate import Migrate
from flask_restx import Api
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

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

    api.add_namespace(user_ns, path='/api/user')
    api.add_namespace(task_ns, path='/api/tasks')
    api.add_namespace(project_ns, path='/api/projects')
    api.add_namespace(comments_ns, path='/api/comments')
    api.add_namespace(tags_ns, path='/api/tags')

    from app import models

    # Configure CORS
    CORS(app, resources={r"/api/*": {
        "origins": "http://localhost:3000",
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }})

    @app.after_request
    def add_cors_headers(response):
        response.headers['Access-Control-Allow-Origin'] = 'http://localhost:3000'
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response

    @app.route('/api/<path:path>', methods=['OPTIONS'])
    def handle_options(path):
        return '', 204

    return app
