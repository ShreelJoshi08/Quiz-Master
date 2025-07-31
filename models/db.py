from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# --------------------------
# User Table
# --------------------------
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=True)  # Made nullable since we're using mobile
    mobile_number = db.Column(db.String(10), unique=True, nullable=False)  # New mobile field
    password = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200))
    pin_code = db.Column(db.String(10))

    reservations = db.relationship('Reservation', backref='user', lazy=True)

# --------------------------
# Admin Login (if required)
# --------------------------
class Admin(db.Model):
    __tablename__ = 'admin'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=True)  # Made nullable since we're using mobile
    mobile_number = db.Column(db.String(10), unique=True, nullable=False)  # New mobile field
    password = db.Column(db.String(200), nullable=False)

# --------------------------
# Parking Lot
# --------------------------
class ParkingLot(db.Model):
    __tablename__ = 'parking_lots'
    id = db.Column(db.Integer, primary_key=True)
    location_name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    pin_code = db.Column(db.String(10), unique=True, nullable=False)  # Unique constraint added
    price = db.Column(db.Float, nullable=False)
    max_spots = db.Column(db.Integer, nullable=False, default=10)  # Default max 10 spots

    spots = db.relationship('ParkingSpot', backref='lot', lazy=True)

# --------------------------
# Parking Spot
# --------------------------
class ParkingSpot(db.Model):
    __tablename__ = 'parking_spots'
    id = db.Column(db.Integer, primary_key=True)
    lot_id = db.Column(db.Integer, db.ForeignKey('parking_lots.id'), nullable=False)
    status = db.Column(db.String(10), default='vacant')  # 'vacant' or 'occupied'

    reservations = db.relationship('Reservation', backref='spot', lazy=True)

# --------------------------
# Reservation
# --------------------------
class Reservation(db.Model):
    __tablename__ = 'reservations'
    id = db.Column(db.Integer, primary_key=True)
    spot_id = db.Column(db.Integer, db.ForeignKey('parking_spots.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    vehicle_number = db.Column(db.String(20), nullable=False)
    time_in = db.Column(db.DateTime, default=datetime.utcnow)
    time_out = db.Column(db.DateTime, nullable=True)
