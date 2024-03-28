# config.py
import os

class Config(object):
    # General Config
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-should-change-this'
    FLASK_APP = 'run.py'
    FLASK_ENV = 'development'

    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///mydatabase.db'
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

class DevelopmentConfig(Config):
    DEBUG = True

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'  # Use in-memory SQLite database for tests

class ProductionConfig(Config):
    FLASK_ENV = 'production'
    # For production, use a secure, random value for the SECRET_KEY!
    # SECRET_KEY should be generated with a random key-making tool and stored safely
    SECRET_KEY = os.environ.get('SECRET_KEY')
    DEBUG = False
    TESTING = False
    # Define production database URI
    SQLALCHEMY_DATABASE_URI = os.environ.get('PROD_DATABASE_URL')
    SESSION_COOKIE_SECURE = True

# You can add more configuration classes if needed
