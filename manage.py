# manage.py
from search_engine import create_app, socketio
from search_engine.config import ProductionConfig,DevelopmentConfig

# Create app instance with specific config
app = create_app(ProductionConfig)

if __name__ == '__main__':
    # Run the app with SocketIO support and debugging enabled
    socketio.run(app)
    #socketio.run(app, debug=True)
