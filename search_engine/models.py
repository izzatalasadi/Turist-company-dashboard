# search_engine/models.py
from datetime import datetime
from . import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=False)
    # Add a relationship to the Guest model
    guests_checked = db.relationship('Guest', backref='checked_by_user', lazy=True)
    
    def __repr__(self):
        return f'{self.username}'
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Guest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    booking = db.Column(db.String(100), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    flight = db.Column(db.String(100), nullable=False)
    departure_from = db.Column(db.String(100), nullable=True)
    arriving_date = db.Column(db.String(100))
    arrival_time = db.Column(db.String(100))
    transportation = db.Column(db.String(100))
    status = db.Column(db.String(100))  # Checked, Unchecked
    checked_time = db.Column(db.DateTime, default=datetime.utcnow)
    checked_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    comments = db.Column(db.Text)

    def __repr__(self):
        return f'<Guest {self.booking}>'
class ButtonState(db.Model):
    __tablename__ = 'button_state'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    booking_number = db.Column(db.String(120), nullable=False)
    status = db.Column(db.String(10), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)