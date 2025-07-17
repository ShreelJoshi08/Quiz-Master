from models.db import db, Admin
from werkzeug.security import generate_password_hash
from app import app

with app.app_context():
    Email = input("Enter admin Email: ")
    password = input("Enter admin password: ")
    if Admin.query.filter_by(email=Email).first():
        print("Admin already exists!")
    else:
        admin = Admin(
            email=Email,
            password=generate_password_hash(password)
        )
        db.session.add(admin)
        db.session.commit()
        print("Admin user created successfully!")