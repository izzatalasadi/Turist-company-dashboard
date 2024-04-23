from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_socketio import SocketIO
from flask_wtf.csrf import CSRFProtect
from redis import Redis


# Initialize extensions without specific apps
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()

login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.session_protection ='strong'

csrf = CSRFProtect()
socketio = SocketIO()

# Connect to Redis
redis = Redis(host='localhost', port=6379, db=0)  # Adjust parameters as necessary

# Initialize Limiter with Redis storage
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri='redis://localhost:6379'  # Use Redis as the backend for rate limiting
)
cors = CORS()
