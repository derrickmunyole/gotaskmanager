import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'super-secret-key'
    FERNET_KEY = os.environ.get('FERNET_KEY')
    REFRESH_SECRET_KEY = os.environ.get('REFRESH_SECRET_KEY') or 'super-secret-refresh_key'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'postgresql://localhost:5432'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
