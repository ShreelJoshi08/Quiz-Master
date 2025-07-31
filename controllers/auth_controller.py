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
        required_fields = ['full_name', 'mobile_number', 'password', 'address', 'pin_code']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing fields'}), 400

        # Validate mobile number format (10 digits only)
        import re
        mobile_pattern = r'^[0-9]{10}$'
        if not re.match(mobile_pattern, data['mobile_number']):
            return jsonify({'error': 'Mobile number must be exactly 10 digits'}), 400

        if User.query.filter_by(mobile_number=data['mobile_number']).first():
            return jsonify({'error': 'Mobile number already registered'}), 409

        hashed_pw = generate_password_hash(data['password'])
        
        # Generate a default email based on mobile number if not provided
        email = data.get('email') or f"user{data['mobile_number']}@parking.com"
        
        user = User(
            full_name=data['full_name'],
            email=email,
            mobile_number=data['mobile_number'],
            password=hashed_pw,
            address=data['address'],
            pin_code=data['pin_code']
        )
        db.session.add(user)
        db.session.commit()
        return jsonify({'message': 'User registered successfully. Please login.'}), 201
    else:
        return render_template('register.html')

# ------------------------------
# User/Admin Login
# ------------------------------
@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    login_field = data.get('login_field')  # Can be either email or mobile number
    password = data.get('password')
    
    if not login_field or not password:
        return jsonify({'error': 'Login field and password are required'}), 400
    
    # Determine if login_field is email or mobile number
    import re
    mobile_pattern = r'^[0-9]{10}$'
    email_pattern = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
    
    is_mobile = re.match(mobile_pattern, login_field)
    is_email = re.match(email_pattern, login_field)
    
    if not is_mobile and not is_email:
        return jsonify({'error': 'Please enter a valid mobile number or email address'}), 400
    
    admin = None
    user = None
    
    # Search for admin
    if is_mobile:
        admin = Admin.query.filter_by(mobile_number=login_field).first()
    elif is_email:
        admin = Admin.query.filter_by(email=login_field).first()
    
    # Check admin authentication
    if admin and check_password_hash(admin.password, password):
        return jsonify({
            'message': 'Admin login successful',
            'admin_id': admin.id,
            'mobile_number': admin.mobile_number,
            'email': admin.email,
            'user_type': 'admin',
            'redirect_url': '/admin'
        }), 200
    
    # Search for user if not admin
    if is_mobile:
        user = User.query.filter_by(mobile_number=login_field).first()
    elif is_email:
        user = User.query.filter_by(email=login_field).first()
    
    # Check user authentication
    if user and check_password_hash(user.password, password):
        return jsonify({
            'message': 'Login successful',
            'user_id': user.id,
            'full_name': user.full_name,
            'user_type': 'user',
            'redirect_url': '/user'
        }), 200
    
    # If neither admin nor user found
    return jsonify({'error': 'Invalid credentials'}), 401

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
