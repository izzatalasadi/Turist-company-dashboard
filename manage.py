# manage.py
from search_engine import create_app, socketio
from search_engine.config import ProductionConfig,DevelopmentConfig,TestingConfig
import os

# Create app instance with specific config
app = create_app(ProductionConfig)

if __name__ == '__main__':
    # Run the app with SocketIO support and debugging enabled
    #app.run()
    socketio.run(app, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
