import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'super-secret-key'
    FERNET_KEY = os.environ.get('FERNET_KEY')
    REFRESH_SECRET_KEY = os.environ.get('REFRESH_SECRET_KEY') or 'super-secret-refresh_key'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///dev.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    FLASK_ENV = os.environ.get('FLASK_ENV')
    FLASK_MODE = os.environ.get('FLASK_MODE', 'production')

    @classmethod
    def is_production(cls):
        return cls.FLASK_MODE == 'production'


class TestConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'sqlite:///test.db'
