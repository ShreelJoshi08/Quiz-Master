from models.db import db, Admin
from werkzeug.security import generate_password_hash
from app import app

def create_admin_user():
    with app.app_context():
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