import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY')
    FLASK_APP = 'manage.py'
    FLASK_ENV = 'development'
    SQLALCHEMY_DATABASE_URI = os.getenv('SQLALCHEMY_DATABASE_URI', 'sqlite:///site.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Session
    SESSION_TYPE = 'filesystem'
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True
    SESSION_FILE_DIR = os.environ.get('FLASK_SESSION_DIR') or './flask_session'

    # CSRF
    WTF_CSRF_ENABLED = True

    # File
    UPLOAD_FOLDER = '/Data/uploads/'

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'  # Use in-memory SQLite database for testing
    WTF_CSRF_ENABLED = False  # Disable CSRF protection for testing

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///site.db'

class ProductionConfig(Config):
    FLASK_ENV = os.environ.get('FLASK_ENV', 'production')
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    SQLALCHEMY_DATABASE_URI = database_url or 'sqlite:///site.db'
