from flask import Flask
from search_engine.extensions import db, migrate, login_manager, socketio, limiter, cors, csrf
from search_engine.config import Config
from search_engine.models import User

def create_app(config_class=None):
    app = Flask(__name__)
    # Load default configuration from Config class
    app.config.from_object(Config)
    
    # Load configuration from the specified class, if any
    if config_class is not None:
        app.config.from_object(config_class)
    
    with app.app_context():
        from . import routes  # Import routes here
        from . import models  # This should work now without causing circular imports

    from .routes import main_bp, auth_bp, app_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(app_bp)

    # Initialize extensions with the app
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app) 
    socketio.init_app(app, cors_allowed_origins="*")
    limiter.init_app(app)
    cors.init_app(app, resources={r"/*": {"origins": "*"}})
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))  # Adjust based on how your User model is set up

    
    
    return app
