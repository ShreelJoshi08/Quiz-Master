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
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            address TEXT,
            pin_code TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admin (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS parking_lots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            location_name TEXT NOT NULL,
            address TEXT NOT NULL,
            pin_code TEXT NOT NULL,
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
            cursor.execute('''
                INSERT INTO users (full_name, email, password, address, pin_code)
                VALUES (?, ?, ?, ?, ?)
            ''', (data['full_name'], data['email'], data['password'], data['address'], data['pin_code']))
            conn.commit()
            return jsonify({'message': 'User registered successfully'}), 201
        except sqlite3.IntegrityError:
            return jsonify({'error': 'Email already registered'}), 409
        finally:
            conn.close()
    return render_template('register.html')

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    conn = sqlite3.connect('parking_realtime.db')
    cursor = conn.cursor()
    
    # Check admin first
    cursor.execute('SELECT * FROM admin WHERE email = ? AND password = ?', (data['email'], data['password']))
    admin = cursor.fetchone()
    if admin:
        conn.close()
        return jsonify({
            'message': 'Admin login successful',
            'admin_id': admin[0],
            'admin_email': admin[1],
            'user_type': 'admin'
        }), 200
    
    # Check user
    cursor.execute('SELECT * FROM users WHERE email = ? AND password = ?', (data['email'], data['password']))
    user = cursor.fetchone()
    conn.close()
    
    if user:
        return jsonify({
            'message': 'Login successful',
            'user_id': user[0],
            'full_name': user[1],
            'user_type': 'user'
        }), 200
    
    return jsonify({'error': 'Invalid email or password'}), 401

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
            # Ensure correct types
            max_spots = int(data['max_spots'])
            price = float(data['price'])
            # Add parking lot
            cursor.execute('''
                INSERT INTO parking_lots (location_name, address, pin_code, price, max_spots)
                VALUES (?, ?, ?, ?, ?)
            ''', (data['location_name'], data['address'], data['pin_code'], price, max_spots))
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
        # Delete parking spots first
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
    cursor.execute('''
        UPDATE parking_lots SET location_name=?, address=?, pin_code=?, price=?, max_spots=? WHERE id=?
    ''', (
        data.get('location_name'),
        data.get('address'),
        data.get('pin_code'),
        float(data.get('price', 0)),
        int(data.get('max_spots', 0)),
        lot_id
    ))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Lot updated'})

@app.route('/api/admin/lots/<int:lot_id>/spots', methods=['POST'])
def api_add_spot(lot_id):
    conn = sqlite3.connect('parking_realtime.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO parking_spots (lot_id, status) VALUES (?, 'vacant')
    ''', (lot_id,))
    conn.commit()
    spot_id = cursor.lastrowid
    conn.close()
    return jsonify({'message': 'Spot added', 'id': spot_id}), 201

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
    cursor.execute('DELETE FROM parking_spots WHERE id=?', (spot_id,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Spot deleted'})

@app.route('/api/admin/users', methods=['GET'])
def api_admin_users():
    conn = sqlite3.connect('parking_realtime.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, email, full_name, address, pin_code FROM users')
    users = [
        {
            'id': row[0],
            'email': row[1],
            'full_name': row[2],
            'address': row[3],
            'pin_code': row[4]
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
    
    # Find available spot
    cursor.execute('''
        SELECT ps.id FROM parking_spots ps
        WHERE ps.lot_id = ? AND ps.status = 'vacant'
        LIMIT 1
    ''', (data['lot_id'],))
    
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
    ''', (spot[0], data['user_id'], data['vehicle_number']))
    
    conn.commit()
    conn.close()
    
    # Emit real-time update
    socketio.emit('spot_reserved', {
        'lot_id': data['lot_id'],
        'spot_id': spot[0],
        'vehicle_number': data['vehicle_number']
    })
    
    return jsonify({'message': 'Spot reserved successfully', 'spot_id': spot[0]})

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

@app.route('/api/user/summary/<int:user_id>')
def user_summary(user_id):
    conn = sqlite3.connect('parking_realtime.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT pl.location_name, ps.id, r.vehicle_number, r.time_in, r.time_out
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
            'vehicle_number': row[2],
            'time_in': row[3],
            'time_out': row[4] or ''
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
            SELECT r.user_id, r.vehicle_number, r.time_in, u.full_name, u.email
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
            spot['user_email'] = res[4]
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
        time.sleep(5)  # Update every 5 seconds

# Start background thread
update_thread = threading.Thread(target=background_updates, daemon=True)
update_thread.start()

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000) 