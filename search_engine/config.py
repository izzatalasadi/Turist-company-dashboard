import os

class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY', 'CPr4ftfxzHDhzxRwJxv3aNEv5ItikxsCNxhUNmaDag8=')
    FLASK_APP = 'run.py'
    FLASK_ENV = 'development'
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
    SQLALCHEMY_DATABASE_URI = 'sqlite:///mydatabase.db'

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

class ProductionConfig(Config):
    FLASK_ENV = 'production'
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True

    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "").replace("postgres://", "postgresql://", 1)
