from flask import Flask
from models.db import db, Admin
from werkzeug.security import generate_password_hash

# Create a minimal Flask app for admin creation
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///parking.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = '86c86e83ce4817c850a16884d831e667e58087f9a940b21a8b292cc3dcfaf977'

db.init_app(app)

def create_admin_user():
    with app.app_context():
        # Create tables if they don't exist
        db.create_all()
        
        print("=== Create Admin User ===")
        email = input("Enter admin email: ")
        password = input("Enter admin password: ")
        
        # Check if admin already exists
        if Admin.query.filter_by(email=email).first():
            print("Admin with this email already exists!")
            return
        
        # Create new admin user
        admin = Admin(
            email=email,
            password=generate_password_hash(password)
        )
        
        try:
            db.session.add(admin)
            db.session.commit()
            print(f"Admin user '{email}' created successfully!")
        except Exception as e:
            print(f"Error creating admin user: {e}")
            db.session.rollback()

if __name__ == "__main__":
    create_admin_user() 