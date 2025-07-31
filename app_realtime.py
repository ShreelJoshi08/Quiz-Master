from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
import sqlite3
import json
from datetime import datetime
import threading
import time

app = Flask(__name__, static_folder='static', template_folder='templates')
app.config['SECRET_KEY'] = '86c86e83ce4817c850a16884d831e667e58087f9a940b21a8b292cc3dcfaf977'
socketio = SocketIO(app, cors_allowed_origins="*")

# Database initialization
def init_db():
    conn = sqlite3.connect('parking_realtime.db')
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT UNIQUE,
            mobile_number TEXT UNIQUE,
            password TEXT NOT NULL,
            address TEXT,
            pin_code TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admin (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE,
            mobile_number TEXT UNIQUE,
            password TEXT NOT NULL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS parking_lots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            location_name TEXT NOT NULL,
            address TEXT NOT NULL,
            pin_code TEXT UNIQUE NOT NULL,
            price REAL NOT NULL,
            max_spots INTEGER NOT NULL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS parking_spots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lot_id INTEGER,
            status TEXT DEFAULT 'vacant',
            FOREIGN KEY (lot_id) REFERENCES parking_lots (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reservations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            spot_id INTEGER,
            user_id INTEGER,
            vehicle_number TEXT NOT NULL,
            time_in DATETIME DEFAULT CURRENT_TIMESTAMP,
            time_out DATETIME,
            FOREIGN KEY (spot_id) REFERENCES parking_spots (id),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Check if mobile_number column exists in users table and add it if not
    cursor.execute("PRAGMA table_info(users)")
    columns = [column[1] for column in cursor.fetchall()]
    if 'mobile_number' not in columns:
        print("Adding mobile_number column to users table...")
        cursor.execute("ALTER TABLE users ADD COLUMN mobile_number TEXT")
        # Remove NOT NULL constraint from email column if it exists
        cursor.execute("CREATE TABLE users_new AS SELECT id, full_name, email, mobile_number, password, address, pin_code FROM users")
        cursor.execute("DROP TABLE users")
        cursor.execute('''
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                email TEXT UNIQUE,
                mobile_number TEXT UNIQUE,
                password TEXT NOT NULL,
                address TEXT,
                pin_code TEXT
            )
        ''')
        cursor.execute("INSERT INTO users SELECT * FROM users_new")
        cursor.execute("DROP TABLE users_new")
    
    # Check if mobile_number column exists in admin table and add it if not
    cursor.execute("PRAGMA table_info(admin)")
    columns = [column[1] for column in cursor.fetchall()]
    if 'mobile_number' not in columns:
        print("Adding mobile_number column to admin table...")
        cursor.execute("ALTER TABLE admin ADD COLUMN mobile_number TEXT")
    
    conn.commit()
    conn.close()

# Initialize database
init_db()

# Store active users for real-time updates
active_users = {}

@app.route('/')
def home():
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.get_json()
        conn = sqlite3.connect('parking_realtime.db')
        cursor = conn.cursor()
        
        try:
            # Register user with mobile number (email can be optional)
            cursor.execute('''
                INSERT INTO users (full_name, mobile_number, password, address, pin_code)
                VALUES (?, ?, ?, ?, ?)
            ''', (data['full_name'], data['mobile_number'], data['password'], data['address'], data['pin_code']))
            conn.commit()
            return jsonify({'message': 'User registered successfully'}), 201
        except sqlite3.IntegrityError:
            return jsonify({'error': 'Mobile number already registered'}), 409
        finally:
            conn.close()
    return render_template('register.html')

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    conn = sqlite3.connect('parking_realtime.db')
    cursor = conn.cursor()
    
    login_field = data['login_field']
    password = data['password']
    
    # Prioritize mobile number authentication (10 digits)
    is_mobile = login_field.isdigit() and len(login_field) == 10
    
    # Check admin first by mobile number
    admin = None
    if is_mobile:
        cursor.execute('SELECT * FROM admin WHERE mobile_number = ? AND password = ?', (login_field, password))
        admin = cursor.fetchone()
    
    # If no admin found by mobile and it could be email format, try email
    if not admin and not is_mobile:
        cursor.execute('SELECT * FROM admin WHERE email = ? AND password = ?', (login_field, password))
        admin = cursor.fetchone()
    
    if admin:
        conn.close()
        return jsonify({
            'message': 'Admin login successful',
            'admin_id': admin[0],
            'email': admin[1] if len(admin) > 1 else '',
            'mobile_number': admin[2] if len(admin) > 2 else '',
            'user_type': 'admin',
            'redirect_url': '/admin'
        }), 200
    
    # Check user by mobile number
    user = None
    if is_mobile:
        cursor.execute('SELECT * FROM users WHERE mobile_number = ? AND password = ?', (login_field, password))
        user = cursor.fetchone()
    
    # If no user found by mobile and it could be email format, try email
    if not user and not is_mobile:
        cursor.execute('SELECT * FROM users WHERE email = ? AND password = ?', (login_field, password))
        user = cursor.fetchone()
    
    conn.close()
    
    if user:
        return jsonify({
            'message': 'Login successful',
            'user_id': user[0],
            'full_name': user[1],
            'mobile_number': user[3] if len(user) > 3 else '',
            'user_type': 'user',
            'redirect_url': '/user'
        }), 200
    
    return jsonify({'error': 'Invalid mobile number or password'}), 401

@app.route('/admin')
def admin_dashboard():
    return render_template('admin_realtime.html')

@app.route('/api/admin/lots', methods=['GET', 'POST'])
def api_admin_lots():
    if request.method == 'POST':
        data = request.get_json()
        conn = sqlite3.connect('parking_realtime.db')
        cursor = conn.cursor()
        try:
            # Validate inputs
            max_spots = int(data['max_spots'])
            price = float(data['price'])
            pin_code = data['pin_code']
            
            # Check max spots constraint (maximum 10)
            if max_spots > 10:
                conn.close()
                return jsonify({'error': 'Maximum 10 parking spots allowed per lot'}), 400
            
            if max_spots < 1:
                conn.close()
                return jsonify({'error': 'Minimum 1 parking spot required'}), 400
            
            # Check pincode uniqueness
            cursor.execute('SELECT COUNT(*) FROM parking_lots WHERE pin_code = ?', (pin_code,))
            if cursor.fetchone()[0] > 0:
                conn.close()
                return jsonify({'error': 'Pincode already exists. Each parking lot must have a unique pincode'}), 400
            
            # Add parking lot
            cursor.execute('''
                INSERT INTO parking_lots (location_name, address, pin_code, price, max_spots)
                VALUES (?, ?, ?, ?, ?)
            ''', (data['location_name'], data['address'], pin_code, price, max_spots))
            lot_id = cursor.lastrowid
            
            # Add parking spots for this lot
            for i in range(max_spots):
                cursor.execute('''
                    INSERT INTO parking_spots (lot_id, status)
                    VALUES (?, 'vacant')
                ''', (lot_id,))
            
            conn.commit()
            conn.close()
            
            # Emit real-time update
            socketio.emit('new_lot_added', {
                'lot_id': lot_id,
                'location_name': data['location_name'],
                'max_spots': max_spots
            })
            return jsonify({'message': 'Parking lot added successfully', 'lot_id': lot_id}), 201
            
        except ValueError:
            conn.close()
            return jsonify({'error': 'Invalid number format for spots or price'}), 400
        except sqlite3.IntegrityError as e:
            conn.rollback()
            conn.close()
            if 'pin_code' in str(e):
                return jsonify({'error': 'Pincode already exists'}), 400
            return jsonify({'error': 'Database constraint violation'}), 400
        except Exception as e:
            conn.rollback()
            conn.close()
            return jsonify({'error': str(e)}), 500
    
    # GET request - return all lots
    conn = sqlite3.connect('parking_realtime.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT pl.*, COUNT(ps.id) as available_spots
        FROM parking_lots pl
        LEFT JOIN parking_spots ps ON pl.id = ps.lot_id AND ps.status = 'vacant'
        GROUP BY pl.id
    ''')
    lots = []
    lot_rows = cursor.fetchall()
    for row in lot_rows:
        lot_id = row[0]
        # Get all spots for this lot
        cursor.execute('SELECT id, status FROM parking_spots WHERE lot_id = ?', (lot_id,))
        spots = [{'id': s[0], 'status': s[1]} for s in cursor.fetchall()]
        # Count occupied spots
        occupied = sum(1 for s in spots if s['status'] == 'occupied')
        lots.append({
            'id': row[0],
            'location_name': row[1],
            'address': row[2],
            'pin_code': row[3],
            'price': row[4],
            'max_spots': row[5],
            'available_spots': row[6] or 0,
            'occupied': occupied,
            'spots': spots
        })
    conn.close()
    return jsonify({'lots': lots})

@app.route('/api/admin/lots/<int:lot_id>', methods=['DELETE'])
def api_delete_lot(lot_id):
    conn = sqlite3.connect('parking_realtime.db')
    cursor = conn.cursor()
    
    try:
        # Check if any spots in this lot are occupied
        cursor.execute('''
            SELECT COUNT(*) FROM parking_spots 
            WHERE lot_id = ? AND status = 'occupied'
        ''', (lot_id,))
        occupied_count = cursor.fetchone()[0]
        
        if occupied_count > 0:
            conn.close()
            return jsonify({
                'error': f'Cannot delete parking lot. {occupied_count} spots are currently occupied. Please wait for all spots to be vacant before deletion.'
            }), 400
        
        # Delete reservations for this lot's spots first
        cursor.execute('''
            DELETE FROM reservations 
            WHERE spot_id IN (SELECT id FROM parking_spots WHERE lot_id = ?)
        ''', (lot_id,))
        
        # Delete parking spots
        cursor.execute('DELETE FROM parking_spots WHERE lot_id = ?', (lot_id,))
        
        # Delete parking lot
        cursor.execute('DELETE FROM parking_lots WHERE id = ?', (lot_id,))
        
        conn.commit()
        conn.close()
        
        # Emit real-time update
        socketio.emit('lot_deleted', {'lot_id': lot_id})
        
        return jsonify({'message': 'Parking lot deleted successfully'})
        
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({'error': str(e)}), 500

# --- ADMIN: Edit Lot Info (PUT), Add Spot (POST), List Spots (GET), Delete Spot (DELETE) ---
@app.route('/api/admin/lots/<int:lot_id>', methods=['PUT'])
def api_edit_lot(lot_id):
    data = request.get_json()
    conn = sqlite3.connect('parking_realtime.db')
    cursor = conn.cursor()
    
    try:
        new_max_spots = int(data.get('max_spots', 0))
        new_pin_code = data.get('pin_code')
        
        # Check max spots constraint (maximum 10)
        if new_max_spots > 10:
            conn.close()
            return jsonify({'error': 'Maximum 10 parking spots allowed per lot'}), 400
        
        if new_max_spots < 1:
            conn.close()
            return jsonify({'error': 'Minimum 1 parking spot required'}), 400
        
        # Check if reducing spots below occupied count
        cursor.execute('''
            SELECT COUNT(*) FROM parking_spots 
            WHERE lot_id = ? AND status = 'occupied'
        ''', (lot_id,))
        occupied_count = cursor.fetchone()[0]
        
        if new_max_spots < occupied_count:
            conn.close()
            return jsonify({
                'error': f'Cannot reduce spots to {new_max_spots}. {occupied_count} spots are currently occupied. Minimum allowed: {occupied_count}'
            }), 400
        
        # Check pincode uniqueness (exclude current lot)
        cursor.execute('''
            SELECT COUNT(*) FROM parking_lots 
            WHERE pin_code = ? AND id != ?
        ''', (new_pin_code, lot_id))
        if cursor.fetchone()[0] > 0:
            conn.close()
            return jsonify({'error': 'Pincode already exists. Each parking lot must have a unique pincode'}), 400
        
        # Get current max_spots
        cursor.execute('SELECT max_spots FROM parking_lots WHERE id = ?', (lot_id,))
        current_max_spots = cursor.fetchone()[0]
        
        # Update lot information
        cursor.execute('''
            UPDATE parking_lots SET location_name=?, address=?, pin_code=?, price=?, max_spots=? WHERE id=?
        ''', (
            data.get('location_name'),
            data.get('address'),
            new_pin_code,
            float(data.get('price', 0)),
            new_max_spots,
            lot_id
        ))
        
        # Adjust spots if needed
        if new_max_spots > current_max_spots:
            # Add new spots
            for i in range(current_max_spots, new_max_spots):
                cursor.execute('''
                    INSERT INTO parking_spots (lot_id, status)
                    VALUES (?, 'vacant')
                ''', (lot_id,))
        elif new_max_spots < current_max_spots:
            # Remove excess vacant spots (we already checked occupied spots)
            cursor.execute('''
                DELETE FROM parking_spots 
                WHERE lot_id = ? AND status = 'vacant'
                AND id IN (
                    SELECT id FROM parking_spots 
                    WHERE lot_id = ? AND status = 'vacant'
                    LIMIT ?
                )
            ''', (lot_id, lot_id, current_max_spots - new_max_spots))
        
        conn.commit()
        conn.close()
        return jsonify({'message': 'Lot updated successfully'})
        
    except ValueError:
        conn.close()
        return jsonify({'error': 'Invalid number format'}), 400
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/lots/<int:lot_id>/spots', methods=['POST'])
def api_add_spot(lot_id):
    conn = sqlite3.connect('parking_realtime.db')
    cursor = conn.cursor()
    
    try:
        # Check current spot count
        cursor.execute('SELECT COUNT(*) FROM parking_spots WHERE lot_id = ?', (lot_id,))
        current_spots = cursor.fetchone()[0]
        
        if current_spots >= 10:
            conn.close()
            return jsonify({'error': 'Maximum 10 parking spots allowed per lot'}), 400
        
        cursor.execute('''
            INSERT INTO parking_spots (lot_id, status) VALUES (?, 'vacant')
        ''', (lot_id,))
        
        # Update max_spots in parking_lots table
        cursor.execute('''
            UPDATE parking_lots SET max_spots = ? WHERE id = ?
        ''', (current_spots + 1, lot_id))
        
        conn.commit()
        spot_id = cursor.lastrowid
        conn.close()
        return jsonify({'message': 'Spot added', 'id': spot_id}), 201
        
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/lots/<int:lot_id>/spots', methods=['GET'])
def api_get_spots(lot_id):
    conn = sqlite3.connect('parking_realtime.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, status FROM parking_spots WHERE lot_id=?', (lot_id,))
    spots = [{'id': row[0], 'status': row[1]} for row in cursor.fetchall()]
    conn.close()
    return jsonify({'spots': spots})

@app.route('/api/admin/spots/<int:spot_id>', methods=['DELETE'])
def api_delete_spot(spot_id):
    conn = sqlite3.connect('parking_realtime.db')
    cursor = conn.cursor()
    
    try:
        # First check if the spot is currently occupied
        cursor.execute('SELECT status, lot_id FROM parking_spots WHERE id = ?', (spot_id,))
        result = cursor.fetchone()
        
        if not result:
            conn.close()
            return jsonify({'error': 'Parking spot not found'}), 404
        
        status, lot_id = result
        
        if status == 'occupied':
            conn.close()
            return jsonify({'error': 'Cannot delete occupied parking spot. Please wait for the spot to be vacant.'}), 400
        
        # Check if lot would have less than 1 spot after deletion
        cursor.execute('SELECT COUNT(*) FROM parking_spots WHERE lot_id = ?', (lot_id,))
        current_spots = cursor.fetchone()[0]
        
        if current_spots <= 1:
            conn.close()
            return jsonify({'error': 'Cannot delete spot. Each parking lot must have at least 1 spot.'}), 400
        
        # Delete any pending reservations for this spot
        cursor.execute('DELETE FROM reservations WHERE spot_id = ? AND time_out IS NULL', (spot_id,))
        
        # Delete the spot
        cursor.execute('DELETE FROM parking_spots WHERE id = ?', (spot_id,))
        
        # Update the max_spots count in parking_lots table
        cursor.execute('''
            UPDATE parking_lots SET max_spots = max_spots - 1 WHERE id = ?
        ''', (lot_id,))
        
        conn.commit()
        conn.close()
        
        # Emit real-time update
        socketio.emit('spot_deleted', {
            'lot_id': lot_id,
            'spot_id': spot_id
        })
        
        return jsonify({'message': 'Parking spot deleted successfully'})
        
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/users', methods=['GET'])
def api_admin_users():
    conn = sqlite3.connect('parking_realtime.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, email, mobile_number, full_name, address, pin_code FROM users')
    users = [
        {
            'id': row[0],
            'email': row[1] if row[1] else '',
            'mobile_number': row[2] if row[2] else '',
            'full_name': row[3],
            'address': row[4],
            'pin_code': row[5]
        }
        for row in cursor.fetchall()
    ]
    conn.close()
    return jsonify({'users': users})

@app.route('/api/admin/summary', methods=['GET'])
def api_admin_summary():
    conn = sqlite3.connect('parking_realtime.db')
    cursor = conn.cursor()
    # Revenue per lot (count of reservations * price)
    cursor.execute('''
        SELECT pl.id, pl.location_name, pl.price, COUNT(r.id) as total_reservations
        FROM parking_lots pl
        LEFT JOIN parking_spots ps ON pl.id = ps.lot_id
        LEFT JOIN reservations r ON ps.id = r.spot_id
        GROUP BY pl.id
    ''')
    revenue_data = [
        {
            'lot_id': row[0],
            'location_name': row[1],
            'price': row[2],
            'total_reservations': row[3],
            'revenue': (row[2] or 0) * (row[3] or 0)
        }
        for row in cursor.fetchall()
    ]
    # Occupancy summary (available and occupied spots per lot)
    cursor.execute('''
        SELECT pl.id, pl.location_name,
            SUM(CASE WHEN ps.status = 'vacant' THEN 1 ELSE 0 END) as available,
            SUM(CASE WHEN ps.status = 'occupied' THEN 1 ELSE 0 END) as occupied
        FROM parking_lots pl
        LEFT JOIN parking_spots ps ON pl.id = ps.lot_id
        GROUP BY pl.id
    ''')
    occupancy_data = [
        {
            'lot_id': row[0],
            'location_name': row[1],
            'available': row[2] or 0,
            'occupied': row[3] or 0
        }
        for row in cursor.fetchall()
    ]
    conn.close()
    return jsonify({'revenue': revenue_data, 'occupancy': occupancy_data})

@app.route('/user.html')
def user_dashboard():
    return render_template('user.html')

@app.route('/user')
def user():
    return render_template('user.html')

# Real-time API endpoints
@app.route('/api/user/lots')
def user_get_lots():
    conn = sqlite3.connect('parking_realtime.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT pl.*, COUNT(ps.id) as available_spots
        FROM parking_lots pl
        LEFT JOIN parking_spots ps ON pl.id = ps.lot_id AND ps.status = 'vacant'
        GROUP BY pl.id
    ''')
    
    lots = []
    for row in cursor.fetchall():
        lots.append({
            'id': row[0],
            'location_name': row[1],
            'address': row[2],
            'pin_code': row[3],
            'price': row[4],
            'available_spots': row[5] or 0
        })
    
    conn.close()
    return jsonify({'lots': lots})

@app.route('/api/user/reserve', methods=['POST'])
def user_reserve_spot():
    data = request.get_json()
    conn = sqlite3.connect('parking_realtime.db')
    cursor = conn.cursor()
    
    try:
        vehicle_number = data['vehicle_number'].upper().strip()
        user_id = data['user_id']
        lot_id = data['lot_id']
        
        # Validate Indian number plate format (comprehensive)
        import re
        # Enhanced Indian number plate patterns
        patterns = [
            r'^[A-Z]{2}[0-9]{1,2}[A-Z]{1,2}[0-9]{4}$',  # Standard: GJ01AB1234, MH12CD5678
            r'^[A-Z]{2}[0-9]{1,2}[A-Z]{3}[0-9]{4}$',   # Three letters: DL8CAF2023
            r'^[A-Z]{2}[0-9]{2}[A-Z]{1,3}[0-9]{1,4}$',  # Alternative formats
            r'^[A-Z]{3}[0-9]{1,4}$',                      # Three letter codes: CAA1234
            r'^[A-Z]{2}[0-9]{1,2}[A-Z][0-9]{1,4}$',     # Two letter middle: GJ01A1234
            r'^[A-Z]{2}[0-9]{1,2}[A-Z]{1,2}[0-9]{1,4}$' # Variable ending numbers
        ]
        
        is_valid = any(re.match(pattern, vehicle_number) for pattern in patterns)
        if not is_valid:
            conn.close()
            return jsonify({'error': 'Invalid vehicle number format. Please use Indian number plate format (e.g., GJ01AB1234, MH12CD5678, etc.)'}), 400
        
        # Check if vehicle number is already in use by any active reservation
        cursor.execute('''
            SELECT COUNT(*) FROM reservations r
            JOIN parking_spots ps ON r.spot_id = ps.id
            WHERE r.vehicle_number = ? AND r.time_out IS NULL
        ''', (vehicle_number,))
        
        if cursor.fetchone()[0] > 0:
            conn.close()
            return jsonify({'error': 'Vehicle number already has an active reservation'}), 400
        
        # Find available spot
        cursor.execute('''
            SELECT ps.id FROM parking_spots ps
            WHERE ps.lot_id = ? AND ps.status = 'vacant'
            LIMIT 1
        ''', (lot_id,))
        
        spot = cursor.fetchone()
        if not spot:
            conn.close()
            return jsonify({'error': 'No available spots in this lot'}), 400
        
        # Reserve the spot
        cursor.execute('''
            UPDATE parking_spots SET status = 'occupied' WHERE id = ?
        ''', (spot[0],))
        
        cursor.execute('''
            INSERT INTO reservations (spot_id, user_id, vehicle_number)
            VALUES (?, ?, ?)
        ''', (spot[0], user_id, vehicle_number))
        
        conn.commit()
        conn.close()
        
        # Emit real-time update
        socketio.emit('spot_reserved', {
            'lot_id': lot_id,
            'spot_id': spot[0],
            'vehicle_number': vehicle_number
        })
        
        return jsonify({'message': 'Spot reserved successfully', 'spot_id': spot[0]})
        
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/reserve-multiple', methods=['POST'])
def user_reserve_multiple_spots():
    data = request.get_json()
    conn = sqlite3.connect('parking_realtime.db')
    cursor = conn.cursor()
    
    try:
        user_id = data['user_id']
        lot_id = data['lot_id']
        vehicle_numbers = data['vehicle_numbers']  # List of vehicle numbers
        
        # Validate input
        if not isinstance(vehicle_numbers, list):
            conn.close()
            return jsonify({'error': 'vehicle_numbers must be a list'}), 400
        
        if len(vehicle_numbers) == 0:
            conn.close()
            return jsonify({'error': 'At least one vehicle number required'}), 400
        
        if len(vehicle_numbers) > 5:  # Limit to 5 vehicles max
            conn.close()
            return jsonify({'error': 'Maximum 5 vehicles can be booked at once'}), 400
        
        # Enhanced Indian number plate validation
        import re
        patterns = [
            r'^[A-Z]{2}[0-9]{1,2}[A-Z]{1,2}[0-9]{4}$',  # Standard: GJ01AB1234, MH12CD5678
            r'^[A-Z]{2}[0-9]{1,2}[A-Z]{3}[0-9]{4}$',   # Three letters: DL8CAF2023
            r'^[A-Z]{2}[0-9]{2}[A-Z]{1,3}[0-9]{1,4}$',  # Alternative formats
            r'^[A-Z]{3}[0-9]{1,4}$',                      # Three letter codes: CAA1234
            r'^[A-Z]{2}[0-9]{1,2}[A-Z][0-9]{1,4}$',     # Two letter middle: GJ01A1234
            r'^[A-Z]{2}[0-9]{1,2}[A-Z]{1,2}[0-9]{1,4}$' # Variable ending numbers
        ]
        
        def validate_indian_plate(vehicle_number):
            vehicle_number = vehicle_number.upper().strip()
            return any(re.match(pattern, vehicle_number) for pattern in patterns)
        
        # Clean and validate all vehicle numbers
        clean_vehicles = []
        for vehicle in vehicle_numbers:
            clean_vehicle = vehicle.upper().strip()
            if not validate_indian_plate(clean_vehicle):
                conn.close()
                return jsonify({'error': f'Invalid vehicle number format: {vehicle}. Please use Indian number plate format'}), 400
            clean_vehicles.append(clean_vehicle)
        
        # Check for duplicate vehicle numbers in the request
        if len(set(clean_vehicles)) != len(clean_vehicles):
            conn.close()
            return jsonify({'error': 'Duplicate vehicle numbers in request'}), 400
        
        # Check if any vehicle numbers are already in use
        placeholders = ','.join(['?' for _ in clean_vehicles])
        cursor.execute(f'''
            SELECT r.vehicle_number FROM reservations r
            JOIN parking_spots ps ON r.spot_id = ps.id
            WHERE r.vehicle_number IN ({placeholders}) AND r.time_out IS NULL
        ''', clean_vehicles)
        
        existing_vehicles = cursor.fetchall()
        if existing_vehicles:
            existing_list = [v[0] for v in existing_vehicles]
            conn.close()
            return jsonify({'error': f'Vehicle numbers already have active reservations: {", ".join(existing_list)}'}), 400
        
        # Check available spots
        cursor.execute('''
            SELECT ps.id FROM parking_spots ps
            WHERE ps.lot_id = ? AND ps.status = 'vacant'
            ORDER BY ps.id
        ''', (lot_id,))
        
        available_spots = cursor.fetchall()
        if len(available_spots) < len(clean_vehicles):
            conn.close()
            return jsonify({'error': f'Only {len(available_spots)} spots available, but {len(clean_vehicles)} vehicles requested'}), 400
        
        # Reserve the spots
        successful_reservations = []
        reserved_spot_ids = []
        
        for i, vehicle_number in enumerate(clean_vehicles):
            spot_id = available_spots[i][0]
            
            # Update spot status
            cursor.execute('''
                UPDATE parking_spots SET status = 'occupied' WHERE id = ?
            ''', (spot_id,))
            
            # Create reservation
            cursor.execute('''
                INSERT INTO reservations (spot_id, user_id, vehicle_number)
                VALUES (?, ?, ?)
            ''', (spot_id, user_id, vehicle_number))
            
            successful_reservations.append({
                'vehicle_number': vehicle_number,
                'spot_id': spot_id
            })
            reserved_spot_ids.append(spot_id)
        
        conn.commit()
        conn.close()
        
        # Emit real-time updates for each reservation
        for reservation in successful_reservations:
            socketio.emit('spot_reserved', {
                'lot_id': lot_id,
                'spot_id': reservation['spot_id'],
                'vehicle_number': reservation['vehicle_number']
            })
        
        return jsonify({
            'message': f'Successfully reserved {len(successful_reservations)} spots',
            'reservations': successful_reservations,
            'total_spots': len(successful_reservations)
        }), 201
        
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/vacate', methods=['POST'])
def user_vacate_spot():
    data = request.get_json()
    conn = sqlite3.connect('parking_realtime.db')
    cursor = conn.cursor()
    
    # Find active reservation
    cursor.execute('''
        SELECT r.spot_id, r.user_id
        FROM reservations r
        WHERE r.user_id = ? AND r.time_out IS NULL
        ORDER BY r.time_in DESC LIMIT 1
    ''', (data['user_id'],))
    
    reservation = cursor.fetchone()
    if not reservation:
        conn.close()
        return jsonify({'error': 'No active reservation found'}), 400
    
    # Vacate the spot
    cursor.execute('''
        UPDATE parking_spots SET status = 'vacant' WHERE id = ?
    ''', (reservation[0],))
    
    cursor.execute('''
        UPDATE reservations SET time_out = CURRENT_TIMESTAMP WHERE spot_id = ? AND time_out IS NULL
    ''', (reservation[0],))
    
    # Fetch lot_id for the spot
    cursor.execute('SELECT lot_id FROM parking_spots WHERE id = ?', (reservation[0],))
    lot_id_row = cursor.fetchone()
    lot_id = lot_id_row[0] if lot_id_row else None
    
    conn.commit()
    conn.close()
    
    # Emit real-time update with correct lot_id
    socketio.emit('spot_vacated', {
        'lot_id': lot_id,
        'spot_id': reservation[0]
    })
    
    return jsonify({'message': 'Spot vacated successfully'})

@app.route('/api/user/vacate-specific', methods=['POST'])
def user_vacate_specific_spot():
    data = request.get_json()
    conn = sqlite3.connect('parking_realtime.db')
    cursor = conn.cursor()
    
    try:
        user_id = data['user_id']
        spot_id = data['spot_id']
        vehicle_number = data['vehicle_number']
        
        # Verify the reservation belongs to the user and is active
        cursor.execute('''
            SELECT r.spot_id, r.user_id, r.vehicle_number
            FROM reservations r
            WHERE r.user_id = ? AND r.spot_id = ? AND r.vehicle_number = ? AND r.time_out IS NULL
        ''', (user_id, spot_id, vehicle_number))
        
        reservation = cursor.fetchone()
        if not reservation:
            conn.close()
            return jsonify({'error': 'No matching active reservation found'}), 400
        
        # Vacate the spot
        cursor.execute('''
            UPDATE parking_spots SET status = 'vacant' WHERE id = ?
        ''', (spot_id,))
        
        cursor.execute('''
            UPDATE reservations SET time_out = CURRENT_TIMESTAMP 
            WHERE spot_id = ? AND user_id = ? AND vehicle_number = ? AND time_out IS NULL
        ''', (spot_id, user_id, vehicle_number))
        
        # Fetch lot_id for the spot
        cursor.execute('SELECT lot_id FROM parking_spots WHERE id = ?', (spot_id,))
        lot_id_row = cursor.fetchone()
        lot_id = lot_id_row[0] if lot_id_row else None
        
        conn.commit()
        conn.close()
        
        # Emit real-time update
        socketio.emit('spot_vacated', {
            'lot_id': lot_id,
            'spot_id': spot_id,
            'vehicle_number': vehicle_number
        })
        
        return jsonify({'message': 'Spot vacated successfully'})
        
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/vacate-multiple', methods=['POST'])
def user_vacate_multiple_spots():
    data = request.get_json()
    conn = sqlite3.connect('parking_realtime.db')
    cursor = conn.cursor()
    
    try:
        user_id = data['user_id']
        vehicle_numbers = data.get('vehicle_numbers', [])  # Optional: specific vehicles to vacate
        
        # If no specific vehicles provided, get all active reservations for user
        if not vehicle_numbers:
            cursor.execute('''
                SELECT r.vehicle_number, r.spot_id, ps.lot_id
                FROM reservations r
                JOIN parking_spots ps ON r.spot_id = ps.id
                WHERE r.user_id = ? AND r.time_out IS NULL
                ORDER BY r.time_in DESC
            ''', (user_id,))
        else:
            # Vacate specific vehicles
            placeholders = ','.join(['?' for _ in vehicle_numbers])
            cursor.execute(f'''
                SELECT r.vehicle_number, r.spot_id, ps.lot_id
                FROM reservations r
                JOIN parking_spots ps ON r.spot_id = ps.id
                WHERE r.user_id = ? AND r.vehicle_number IN ({placeholders}) AND r.time_out IS NULL
                ORDER BY r.time_in DESC
            ''', [user_id] + vehicle_numbers)
        
        active_reservations = cursor.fetchall()
        
        if not active_reservations:
            conn.close()
            return jsonify({'error': 'No active reservations found'}), 400
        
        # Vacate all found reservations
        vacated_spots = []
        
        for vehicle_number, spot_id, lot_id in active_reservations:
            # Update spot status to vacant
            cursor.execute('''
                UPDATE parking_spots SET status = 'vacant' WHERE id = ?
            ''', (spot_id,))
            
            # Update reservation with checkout time
            cursor.execute('''
                UPDATE reservations SET time_out = CURRENT_TIMESTAMP 
                WHERE spot_id = ? AND time_out IS NULL
            ''', (spot_id,))
            
            vacated_spots.append({
                'vehicle_number': vehicle_number,
                'spot_id': spot_id,
                'lot_id': lot_id
            })
        
        conn.commit()
        conn.close()
        
        # Emit real-time updates for each vacated spot
        for spot in vacated_spots:
            socketio.emit('spot_vacated', {
                'lot_id': spot['lot_id'],
                'spot_id': spot['spot_id']
            })
        
        return jsonify({
            'message': f'Successfully vacated {len(vacated_spots)} spots',
            'vacated_spots': vacated_spots,
            'total_vacated': len(vacated_spots)
        })
        
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/summary/<int:user_id>')
def user_summary(user_id):
    conn = sqlite3.connect('parking_realtime.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT pl.location_name, ps.id, r.vehicle_number, r.time_in, r.time_out, pl.price
        FROM reservations r
        JOIN parking_spots ps ON r.spot_id = ps.id
        JOIN parking_lots pl ON ps.lot_id = pl.id
        WHERE r.user_id = ?
        ORDER BY r.time_in DESC
    ''', (user_id,))
    
    reservations = []
    for row in cursor.fetchall():
        reservations.append({
            'lot_name': row[0],
            'spot': row[1],
            'spot_id': row[1],  # Add spot_id field for consistency
            'vehicle_number': row[2],
            'time_in': row[3],
            'time_out': row[4] or '',
            'charge': row[5]  # Add charge column
        })
    
    conn.close()
    return jsonify({'reservations': reservations})

@app.route('/api/user/lots/search')
def user_search_lots():
    location = request.args.get('location', '').strip().lower()
    pincode = request.args.get('pincode', '').strip()
    name = request.args.get('name', '').strip().lower()
    available_only = request.args.get('available_only', 'false').lower() == 'true'

    conn = sqlite3.connect('parking_realtime.db')
    cursor = conn.cursor()
    
    query = '''
        SELECT pl.*, COUNT(ps.id) as available_spots
        FROM parking_lots pl
        LEFT JOIN parking_spots ps ON pl.id = ps.lot_id AND ps.status = 'vacant'
    '''
    
    conditions = []
    params = []
    
    if location:
        conditions.append("LOWER(pl.address) LIKE ?")
        params.append(f"%{location}%")
    if pincode:
        conditions.append("pl.pin_code = ?")
        params.append(pincode)
    if name:
        conditions.append("LOWER(pl.location_name) LIKE ?")
        params.append(f"%{name}%")
    
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    
    query += " GROUP BY pl.id"
    
    if available_only:
        query += " HAVING available_spots > 0"
    
    cursor.execute(query, params)
    
    lots = []
    for row in cursor.fetchall():
        available_spots = row[5] or 0
        if not available_only or available_spots > 0:
            lots.append({
                'id': row[0],
                'location_name': row[1],
                'address': row[2],
                'pin_code': row[3],
                'price': row[4],
                'available_spots': available_spots
            })
    
    conn.close()
    return jsonify({'lots': lots})

@app.route('/api/admin/spots/<int:spot_id>', methods=['GET'])
def api_admin_spot_details(spot_id):
    conn = sqlite3.connect('parking_realtime.db')
    cursor = conn.cursor()
    # Get spot status
    cursor.execute('SELECT id, lot_id, status FROM parking_spots WHERE id = ?', (spot_id,))
    spot_row = cursor.fetchone()
    if not spot_row:
        conn.close()
        return jsonify({'error': 'Spot not found'}), 404
    spot = {'id': spot_row[0], 'lot_id': spot_row[1], 'status': spot_row[2]}
    # If occupied, get reservation and user details
    if spot['status'] == 'occupied':
        cursor.execute('''
            SELECT r.user_id, r.vehicle_number, r.time_in, u.full_name, u.email, u.mobile_number
            FROM reservations r
            JOIN users u ON r.user_id = u.id
            WHERE r.spot_id = ? AND r.time_out IS NULL
            ORDER BY r.time_in DESC LIMIT 1
        ''', (spot_id,))
        res = cursor.fetchone()
        if res:
            spot['user_id'] = res[0]
            spot['vehicle_number'] = res[1]
            spot['time_in'] = res[2]
            spot['user_name'] = res[3]
            spot['user_email'] = res[4] if res[4] else ''
            spot['user_mobile'] = res[5] if res[5] else ''
    conn.close()
    return jsonify(spot)

@app.route('/api/admin/profile', methods=['PUT'])
def update_admin_profile():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    if not email or not password:
        return jsonify({'error': 'Email and password required'}), 400
    conn = sqlite3.connect('parking_realtime.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE admin SET email=?, password=? WHERE id=1', (email, password))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Profile updated successfully'})

@app.route('/api/admin/search', methods=['GET'])
def api_admin_search():
    search_by = request.args.get('by', '')
    search_query = request.args.get('q', '').strip()
    
    if not search_query:
        return jsonify({'results': []})
    
    conn = sqlite3.connect('parking_realtime.db')
    cursor = conn.cursor()
    results = []
    
    try:
        if search_by == 'user':
            # Search by User ID
            try:
                user_id = int(search_query)
                cursor.execute('''
                    SELECT u.id, u.email, u.full_name, u.address, u.pin_code, u.mobile_number
                    FROM users u 
                    WHERE u.id = ?
                ''', (user_id,))
                user = cursor.fetchone()
                
                if user:
                    # Get user's reservations with lot price for cost calculation
                    cursor.execute('''
                        SELECT r.id, r.vehicle_number, r.time_in, r.time_out,
                               pl.location_name, ps.id as spot_id, pl.price
                        FROM reservations r
                        JOIN parking_spots ps ON r.spot_id = ps.id
                        JOIN parking_lots pl ON ps.lot_id = pl.id
                        WHERE r.user_id = ?
                        ORDER BY r.time_in DESC
                        LIMIT 5
                    ''', (user_id,))
                    reservations = cursor.fetchall()
                    
                    result_html = f'''
                    <div class="card">
                        <div class="card-header">
                            <h6 class="mb-0">User Details (ID: {user[0]})</h6>
                        </div>
                        <div class="card-body">
                            <p><strong>Name:</strong> {user[2]}</p>
                            <p><strong>Email:</strong> {user[1] if user[1] else 'Not provided'}</p>
                            <p><strong>Mobile:</strong> {user[5]}</p>
                            <p><strong>Address:</strong> {user[3] if user[3] else 'Not provided'}</p>
                            <p><strong>Pin Code:</strong> {user[4] if user[4] else 'Not provided'}</p>
                        </div>
                    </div>
                    '''
                    
                    if reservations:
                        result_html += '''
                        <div class="card mt-2">
                            <div class="card-header">
                                <h6 class="mb-0">Recent Reservations</h6>
                            </div>
                            <div class="card-body">
                                <div class="table-responsive">
                                    <table class="table table-sm">
                                        <thead>
                                            <tr>
                                                <th>Vehicle</th>
                                                <th>Location</th>
                                                <th>Time In</th>
                                                <th>Time Out</th>
                                                <th>Status</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                        '''
                        for res in reservations:
                            time_out = res[3] if res[3] else 'Active'
                            status = 'Completed' if res[3] else 'Active'
                            result_html += f'''
                            <tr>
                                <td>{res[1]}</td>
                                <td>{res[4]}</td>
                                <td>{res[2]}</td>
                                <td>{time_out}</td>
                                <td><span class="badge bg-{'success' if res[3] else 'primary'}">{status}</span></td>
                            </tr>
                            '''
                        result_html += '''
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </div>
                        '''
                    
                    results.append(result_html)
                else:
                    results.append('<div class="alert alert-warning">No user found with this ID.</div>')
                    
            except ValueError:
                results.append('<div class="alert alert-danger">Please enter a valid numeric User ID.</div>')
                
        elif search_by == 'location':
            # Search by Location
            cursor.execute('''
                SELECT pl.id, pl.location_name, pl.address, pl.pin_code, pl.price, pl.max_spots,
                       COUNT(CASE WHEN ps.status = 'occupied' THEN 1 END) as occupied_spots
                FROM parking_lots pl
                LEFT JOIN parking_spots ps ON pl.id = ps.lot_id
                WHERE LOWER(pl.location_name) LIKE LOWER(?) 
                   OR LOWER(pl.address) LIKE LOWER(?)
                   OR pl.pin_code LIKE ?
                GROUP BY pl.id, pl.location_name, pl.address, pl.pin_code, pl.price, pl.max_spots
            ''', (f'%{search_query}%', f'%{search_query}%', f'%{search_query}%'))
            
            lots = cursor.fetchall()
            
            if lots:
                for lot in lots:
                    lot_id, location_name, address, pin_code, price, max_spots, occupied_spots = lot
                    available_spots = max_spots - occupied_spots
                    
                    # Get spot details for visualization
                    cursor.execute('''
                        SELECT id, status FROM parking_spots 
                        WHERE lot_id = ? 
                        ORDER BY id
                    ''', (lot_id,))
                    spots = cursor.fetchall()
                    
                    # Create spot grid visualization
                    spot_grid = ''
                    for spot in spots:
                        spot_status = 'occupied' if spot[1] == 'occupied' else 'available'
                        spot_letter = 'O' if spot[1] == 'occupied' else 'A'
                        spot_grid += f'<div class="spot-box spot-{spot_status}" title="Spot {spot[0]}">{spot_letter}</div>'
                    
                    result_html = f'''
                    <div class="card">
                        <div class="card-header">
                            <h6 class="mb-0">{location_name}</h6>
                        </div>
                        <div class="card-body">
                            <p><strong>Address:</strong> {address}</p>
                            <p><strong>Pin Code:</strong> {pin_code}</p>
                            <p><strong>Price:</strong> ₹{price}/hour</p>
                            <p><strong>Occupancy:</strong> {occupied_spots}/{max_spots} spots occupied</p>
                            <div class="mt-3">
                                <strong>Spot Status:</strong>
                                <div class="occupancy-grid mt-2">
                                    {spot_grid}
                                </div>
                            </div>
                            <div class="mt-2">
                                <small class="text-muted">
                                    <span class="spot-box spot-available me-2">A</span> Available
                                    <span class="spot-box spot-occupied ms-3 me-2">O</span> Occupied
                                </small>
                            </div>
                        </div>
                    </div>
                    '''
                    results.append(result_html)
            else:
                results.append('<div class="alert alert-warning">No parking lots found matching your search.</div>')
        
        else:
            results.append('<div class="alert alert-danger">Invalid search type.</div>')
            
    except Exception as e:
        results.append(f'<div class="alert alert-danger">Search error: {str(e)}</div>')
    finally:
        conn.close()
    
    return jsonify({'results': results})

# WebSocket events
@socketio.on('connect')
def handle_connect():
    print(f'Client connected: {request.sid}')

@socketio.on('disconnect')
def handle_disconnect():
    print(f'Client disconnected: {request.sid}')

@socketio.on('join_user')
def handle_join_user(data):
    user_id = data.get('user_id')
    active_users[request.sid] = user_id
    print(f'User {user_id} joined')

@socketio.on('leave_user')
def handle_leave_user():
    if request.sid in active_users:
        del active_users[request.sid]

# Background task for real-time updates
def background_updates():
    previous_status = {}
    
    while True:
        # Check for spot availability changes
        conn = sqlite3.connect('parking_realtime.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT pl.id, pl.location_name, COUNT(ps.id) as available_spots
            FROM parking_lots pl
            LEFT JOIN parking_spots ps ON pl.id = ps.lot_id AND ps.status = 'vacant'
            GROUP BY pl.id
        ''')
        
        current_status = {row[0]: row[2] for row in cursor.fetchall()}
        conn.close()
        
        # Check for changes and notify users
        for lot_id, available_spots in current_status.items():
            if lot_id in previous_status:
                if previous_status[lot_id] == 0 and available_spots > 0:
                    # Spots became available
                    socketio.emit('spots_available', {
                        'lot_id': lot_id,
                        'available_spots': available_spots,
                        'message': f'Spots are now available at lot {lot_id}!'
                    })
                elif previous_status[lot_id] > 0 and available_spots == 0:
                    # Spots became full
                    socketio.emit('spots_full', {
                        'lot_id': lot_id,
                        'message': f'Lot {lot_id} is now full!'
                    })
        
        # Emit general availability update
        socketio.emit('availability_update', current_status)
        
        previous_status = current_status.copy()
        time.sleep(3)  # Update every 5 seconds

# Start background thread
update_thread = threading.Thread(target=background_updates, daemon=True)
update_thread.start()

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000) 