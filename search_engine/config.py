
import os

class Config(object):
    # General Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY', 'CPr4ftfxzHDhzxRwJxv3aNEv5ItikxsCNxhUNmaDag8=')
    FLASK_APP = 'run.py'
    FLASK_ENV = 'development'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    @property
    def SQLALCHEMY_DATABASE_URI(self):
        uri = os.getenv('DATABASE_URL')
        if uri and uri.startswith("postgres://"):
            uri = uri.replace("postgres://", "postgresql://", 1)
        # Ensure SSL mode is used where necessary
        if uri and 'heroku' in uri:
            return uri + "?sslmode=require"
        return uri

    # Session Configuration
    SESSION_TYPE = 'filesystem'
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True
    SESSION_FILE_DIR = os.environ.get('FLASK_SESSION_DIR', './flask_session')

    # CSRF Protection
    WTF_CSRF_ENABLED = True

    # File Uploads
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', '/Data/uploads/')

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_ECHO = True  # If you want to see SQLAlchemy queries for debugging

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'  # Use in-memory SQLite for tests

class ProductionConfig(Config):
    FLASK_ENV = 'production'
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True  # Use secure cookies in production
    SECRET_KEY = os.environ.get('SECRET_KEY')  # Ensure secret key is set in production
