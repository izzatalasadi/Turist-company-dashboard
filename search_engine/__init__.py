#name_search_engine/search_engine/__init__py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate
from search_engine.config import Config

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.session_protection ='strong'

from search_engine.models import User
from search_engine.routes import auth_bp

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
    
def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    
    migrate = Migrate(app, db)
    login_manager.init_app(app)
    
    CSRFProtect(app)
    
    app.register_blueprint(auth_bp)

    return app
