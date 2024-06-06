from datetime import datetime, timedelta
import logging
from flask import Flask
from search_engine.extensions import db, migrate, login_manager, socketio, limiter, cors, csrf
from search_engine.models import Flight
from werkzeug.security import generate_password_hash
from flask.cli import with_appcontext
import click
from apscheduler.schedulers.background import BackgroundScheduler
import atexit
from search_engine.flight_data import FlightInfo


def update_flight_info(app):
    with app.app_context():
        try:
            logging.info("Starting update of flight info.")
            flights = Flight.query.all()
            if not flights:
                logging.warning("No flights found in the database.")
                return

            logging.info(f"Found {len(flights)} flights to update.")
            flight_info_obj = FlightInfo([flight.flight_number for flight in flights])
            flights_info = flight_info_obj.get_flights_info()

            for flight in flights:
                try:
                    if flight.flight_number in flights_info:
                        flight_data = flights_info[flight.flight_number]
                        new_arrival_date = flight_data[0]
                        new_arrival_time = flight_data[1]

                        updated = False
                        if flight.arrival_date != new_arrival_date:
                            flight.arrival_date = new_arrival_date
                            updated = True
                        if flight.arrival_time != new_arrival_time:
                            flight.arrival_time = new_arrival_time
                            updated = True

                        flight.updated = updated  # Set the updated flag
                        db.session.commit()

                        if updated:
                            logging.info(f"Updated flight {flight.flight_number}: arrival_date={flight.arrival_date}, arrival_time={flight.arrival_time}")
                        else:
                            logging.info(f"No changes for flight {flight.flight_number}")

                    else:
                        logging.warning(f"No data found for flight {flight.flight_number}")

                except Exception as e:
                    logging.error(f"Error updating flight {flight.flight_number}: {e}")

        except Exception as e:
            logging.error(f"Failed to update flight info: {e}")
            
# Create app
def create_app(config_class):
    app = Flask(__name__)
    app.config.from_object(config_class)
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7) 

    with app.app_context():
        from search_engine.models import User

    from .routes import main_bp, auth_bp, app_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(app_bp)
    
    db.init_app(app)
    
    # Adding logging
    logging.basicConfig(level=logging.DEBUG)
    app.logger.debug(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")

    
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
    scheduler.add_job(func=update_flight_info, args=[app], trigger="interval", minutes=3)
    scheduler.start()

    # Shut down the scheduler when exiting the app
    atexit.register(lambda: scheduler.shutdown())
    
    return app
