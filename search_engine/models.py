# search_engine/models.py
from datetime import datetime, timedelta
import logging
from .extensions import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(512), nullable=False)
    email = db.Column(db.String(120), index=True, unique=True) 
    mobile = db.Column(db.String(120), unique=False, nullable=True)
    profile_picture = db.Column(db.String(120), nullable=True, default='face1.jpeg')
    bio = db.Column(db.Text, nullable=True)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    is_admin = db.Column(db.Boolean, default=False)
    # Add a relationship to the Guest model
    guests_checked = db.relationship('Guest', backref='checked_by_user', lazy='dynamic', cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<User {self.username}, {self.email}>'
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def update_last_seen(self):
        try:
            self.last_seen = datetime.utcnow()
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error updating last seen: {e}")

    
    def is_online(self):
        if self.last_seen:
            return datetime.utcnow() - self.last_seen < timedelta(minutes=5)
        return False

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    read = db.Column(db.Boolean, default=False, nullable=False)  # New field

    sender = db.relationship("User", foreign_keys=[sender_id], backref="sent_messages")
    receiver = db.relationship("User", foreign_keys=[receiver_id], backref="received_messages")

class Activity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref=db.backref('activities', lazy=True))
    event = db.Column(db.String(100))
    description = db.Column(db.String(255))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    checked_in = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f"<Activity {self.event} by {self.user.username} at {self.timestamp}>"
    
class Flight(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    flight_number = db.Column(db.String(100), nullable=False)
    departure_from = db.Column(db.String(100), nullable=True)
    arrival_time = db.Column(db.String(100), nullable=True)  # Changed from String to DateTime for better handling
    arrival_date = db.Column(db.String(100), nullable=True)  # Changed from String to DateTime for better handling

    def __str__(self):
        return f"{self.flight_number}"
class Guest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    booking = db.Column(db.String(100), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    flight_id = db.Column(db.Integer, db.ForeignKey('flight.id'))  
    departure_from = db.Column(db.String(100), nullable=True)
    arriving_date = db.Column(db.String(100), nullable=True)
    arrival_time = db.Column(db.String(100), nullable=True)  
    transportation = db.Column(db.String(100))
    status = db.Column(db.String(100))  # Checked, Unchecked
    checked_time = db.Column(db.DateTime, default=None)
    checked_by = db.Column(db.Integer, db.ForeignKey('user.id')) 
    comments = db.Column(db.Text)

    flight = db.relationship('Flight', backref='guests')

    def __repr__(self):
        return f'<Guest {self.booking}>'
