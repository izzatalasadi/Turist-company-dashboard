import logging
from flask import Flask, current_app
from search_engine.extensions import db, migrate, login_manager, socketio, limiter, cors, csrf
from search_engine.config import Config
from search_engine.models import User, Flight
from werkzeug.security import generate_password_hash
from flask.cli import with_appcontext
import click
from pyflightdata import FlightData
from apscheduler.schedulers.background import BackgroundScheduler
import atexit
from search_engine.flight_data import FlightInfo

def update_flight_info(app):
    print("Updating flight info periodically")
    
    with app.app_context():  # Ensure you have the app context for DB access
        flights = Flight.query.all()  # Retrieve all flights from your database
        logging.info(f"All flights: {flights}")
        flight_info_obj = FlightInfo(flights)
        flights_info = flight_info_obj.get_flights_info()

        for flight in flights:
            try:
                # Fetch latest flight data from the API
                logging.info(f"Flight-{flight.flight_number}: {flights_info[flight.flight_number]}")
                
                if flights_info:
                    new_arrival_date = flights_info[flight.flight_number][0]
                    new_arrival_time = flights_info[flight.flight_number][1]
                    
                    # Parse the data and update the database record
                    if flight.arrival_time != new_arrival_time:
                        flight.arrival_time = new_arrival_time
                    if flight.arrival_date != new_arrival_date:
                        flight.arrival_date = new_arrival_date 
                    
                    db.session.commit()
                    logging.info(f"Updated flight: {flight.flight_number}, arrival time: {flight.arrival_time}")
                else:
                    logging.warning(f"No new data found for flight {flight.flight_number}")
            except Exception as e:
                logging.error(f"Failed to fetch or update data for flight {flight.flight_number}: {e}")

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class or Config)

    with app.app_context():
        from . import routes
        from search_engine.models import User, Flight

    from .routes import main_bp, auth_bp, app_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(app_bp)
    
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app) 
    socketio.init_app(app, cors_allowed_origins="*")
    limiter.init_app(app)
    cors.init_app(app, resources={r"/*": {"origins": "*"}})
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    @app.cli.command("create-admin")
    @click.argument('username')
    @click.argument('password')
    @click.argument('email')
    @with_appcontext
    def create_admin(username, password, email):
        if User.query.filter_by(username=username).first():
            print('Admin user already exists.')
            return
        new_user = User(
            username=username,
            password_hash=generate_password_hash(password),
            email=email,
            is_admin=True
        )
        db.session.add(new_user)
        db.session.commit()
        logging.info(f'{new_user.username} user created successfully.')
    
    app.cli.add_command(create_admin)

    # Initialize the scheduler with the Flask app context
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=update_flight_info, args=[app], trigger="interval", minutes=10)
    scheduler.start()

    # Shut down the scheduler when exiting the app
    atexit.register(lambda: scheduler.shutdown())

    return app
