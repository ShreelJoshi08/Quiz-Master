from flask import Blueprint, request, jsonify, render_template
from werkzeug.security import generate_password_hash, check_password_hash
from models.db import db, User
from models.db import Admin

auth_bp = Blueprint('auth', __name__)

# ------------------------------
# User Registration
# ------------------------------
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.get_json()
        required_fields = ['full_name', 'email', 'password', 'address', 'pin_code']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing fields'}), 400

        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email already registered'}), 409

        hashed_pw = generate_password_hash(data['password'])
        user = User(
            full_name=data['full_name'],
            email=data['email'],
            password=hashed_pw,
            address=data['address'],
            pin_code=data['pin_code']
        )
        db.session.add(user)
        db.session.commit()
        return jsonify({'message': 'User registered successfully'}), 201
    else:
        return render_template('register.html')

# ------------------------------
# User/Admin Login
# ------------------------------
@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    # First check if it's an admin login
    admin = Admin.query.filter_by(email=email).first()
    if admin and check_password_hash(admin.password, password):
        return jsonify({
            'message': 'Admin login successful',
            'admin_id': admin.id,
            'admin_email': admin.email,
            'user_type': 'admin'
        }), 200
    
    # If not admin, check if it's a regular user
    user = User.query.filter_by(email=email).first()
    if user and check_password_hash(user.password, password):
        return jsonify({
            'message': 'Login successful',
            'user_id': user.id,
            'full_name': user.full_name,
            'user_type': 'user'
        }), 200
    
    # If neither admin nor user found
    return jsonify({'error': 'Invalid email or password'}), 401

@auth_bp.route('/')
def home():
    return render_template('login.html')




@auth_bp.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'GET':
        return render_template('admin_login.html')
    
    data = request.get_json()
    admin = Admin.query.filter_by(username=data.get('username')).first()

    if not admin or not check_password_hash(admin.password, data.get('password')):
        return jsonify({'error': 'Invalid admin credentials'}), 401

    return jsonify({
        'message': 'Admin login successful',
        'admin_id': admin.id
    }), 200
