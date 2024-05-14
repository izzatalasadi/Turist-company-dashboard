import os

class Config(object):
    # General Config
    SECRET_KEY = 'CPr4ftfxzHDhzxRwJxv3aNEv5ItikxsCNxhUNmaDag8='
    FLASK_APP = 'run.py'
    FLASK_ENV = 'development'

    # Database
    SQLALCHEMY_DATABASE_URI = 'sqlite:///mydatabase.db'
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
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True
    SECRET_KEY = os.environ.get('SECRET_KEY')

    @property
    def SQLALCHEMY_DATABASE_URI(self):
        uri = os.getenv("DATABASE_URL")
        if uri and uri.startswith("postgres://"):
            uri = uri.replace("postgres://", "postgresql://", 1)
        # Append SSL mode if the URI exists
        if uri:
            uri += "?sslmode=require"
        return uri
