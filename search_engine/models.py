# search_engine/models.py
from datetime import datetime
from .extensions import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import relationship

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False) 
    mobile = db.Column(db.String(120), unique=False, nullable=True)
    profile_picture = db.Column(db.String(120), nullable=True, default='face1.jpg')
    bio = db.Column(db.Text, nullable=True)
    is_admin = db.Column(db.Boolean, default=False)
    # Add a relationship to the Guest model
    guests_checked = db.relationship('Guest', backref='checked_by_user', lazy=True)
    
    def __repr__(self):
        return f'<User {self.username}, {self.email}>'
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    
    # Define relationships
    sender = relationship("User", foreign_keys=[sender_id])
    receiver = relationship("User", foreign_keys=[receiver_id])
     
''' class Flight(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    flight_number = db.Column(db.String(100), nullable=False)
    departure_from = db.Column(db.String(100), nullable=True)
    arrival_time = db.Column(db.String(100))
     '''
class Guest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    booking = db.Column(db.String(100), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    departure_from = db.Column(db.String(100), nullable=True)
    arriving_date = db.Column(db.String(100))
    arrival_time = db.Column(db.String(100))
    transportation = db.Column(db.String(100))
    status = db.Column(db.String(100))  # Checked, Unchecked
    checked_time = db.Column(db.DateTime, default=None)
    checked_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    flight = db.Column(db.String(100), nullable=False)
    comments = db.Column(db.Text)

    def __repr__(self):
        return f'<Guest {self.booking}>'
