from flask import Flask, render_template, jsonify, request
from models.db import db, ParkingLot, ParkingSpot, User, Reservation
from controllers.auth_controller import auth_bp
from controllers.lot_controller import lot_controller
from datetime import datetime

app = Flask(__name__, static_folder='static', template_folder='templates')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///parking.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = '86c86e83ce4817c850a16884d831e667e58087f9a940b21a8b292cc3dcfaf977'

app.register_blueprint(auth_bp)
app.register_blueprint(lot_controller)

db.init_app(app)

# Create DB
with app.app_context():
    db.create_all()

@app.route('/admin')
def admin_dashboard():
    return render_template('admin.html')

@app.route('/api/admin/lots')
def api_get_lots():
    lots = ParkingLot.query.all()
    result = []
    for lot in lots:
        spots = ParkingSpot.query.filter_by(lot_id=lot.id).all()
        spot_list = []
        for idx, spot in enumerate(spots):
            # Generate spot name (e.g., A1, A2, B1, ...)
            row = chr(65 + (idx // 5))  # 5 spots per row: A, B, C, ...
            col = (idx % 5) + 1
            name = f"{row}{col}"
            spot_list.append({
                'id': spot.id,
                'name': name,
                'status': spot.status
            })
        occupied = sum(1 for s in spot_list if s['status'] == 'occupied')
        result.append({
            'id': lot.id,
            'location_name': lot.location_name,
            'address': lot.address,
            'pin_code': lot.pin_code,
            'price': lot.price,
            'max_spots': lot.max_spots,
            'occupied': occupied,
            'spots': spot_list
        })
    return jsonify({'lots': result})

@app.route('/api/admin/lots/<int:lot_id>/spots')
def api_get_spots(lot_id):
    spots = ParkingSpot.query.filter_by(lot_id=lot_id).all()
    return jsonify({'spots': [
        {'id': spot.id, 'status': spot.status} for spot in spots
    ]})

@app.route('/api/admin/lots/<int:lot_id>/spots', methods=['POST'])
def api_add_spot(lot_id):
    data = request.get_json()
    spot = ParkingSpot(lot_id=lot_id, status=data.get('status', 'vacant'))
    db.session.add(spot)
    db.session.commit()
    return jsonify({'message': 'Spot added', 'id': spot.id}), 201

@app.route('/api/admin/spots/<int:spot_id>', methods=['PUT'])
def api_update_spot(spot_id):
    data = request.get_json()
    spot = ParkingSpot.query.get_or_404(spot_id)
    spot.status = data.get('status', spot.status)
    db.session.commit()
    return jsonify({'message': 'Spot updated'})

@app.route('/api/admin/spots/<int:spot_id>', methods=['DELETE'])
def api_delete_spot(spot_id):
    spot = ParkingSpot.query.get_or_404(spot_id)
    db.session.delete(spot)
    db.session.commit()
    return jsonify({'message': 'Spot deleted'})

@app.route('/api/admin/lots', methods=['POST'])
def api_add_lot():
    data = request.get_json()
    lot = ParkingLot(
        location_name=data['location_name'],
        address=data['address'],
        pin_code=data['pin_code'],
        price=data['price'],
        max_spots=data['max_spots']
    )
    db.session.add(lot)
    db.session.commit()
    return jsonify({'message': 'Lot added', 'id': lot.id}), 201

@app.route('/api/admin/lots/<int:lot_id>', methods=['PUT'])
def api_edit_lot(lot_id):
    data = request.get_json()
    lot = ParkingLot.query.get_or_404(lot_id)
    lot.location_name = data.get('location_name', lot.location_name)
    lot.address = data.get('address', lot.address)
    lot.pin_code = data.get('pin_code', lot.pin_code)
    lot.price = data.get('price', lot.price)
    lot.max_spots = data.get('max_spots', lot.max_spots)
    db.session.commit()
    return jsonify({'message': 'Lot updated'})

@app.route('/api/admin/lots/<int:lot_id>', methods=['DELETE'])
def api_delete_lot(lot_id):
    lot = ParkingLot.query.get_or_404(lot_id)
    db.session.delete(lot)
    db.session.commit()
    return jsonify({'message': 'Lot deleted'})

@app.route('/api/admin/spots/<int:spot_id>/details')
def api_spot_details(spot_id):
    reservation = Reservation.query.filter_by(spot_id=spot_id).order_by(Reservation.time_in.desc()).first()
    if not reservation:
        return jsonify({'error': 'No reservation found'}), 404
    user = User.query.get(reservation.user_id)
    spot = ParkingSpot.query.get(spot_id)
    lot = ParkingLot.query.get(spot.lot_id)
    # Calculate cost
    time_in = reservation.time_in
    time_out = reservation.time_out or datetime.utcnow()
    duration_hours = (time_out - time_in).total_seconds() / 3600
    duration_hours = max(1, int(duration_hours + 0.99))  # round up to next hour, min 1 hour
    estimated_cost = duration_hours * lot.price
    return jsonify({
        'user_id': user.id,
        'user_name': user.full_name,
        'user_email': user.email,
        'vehicle_number': reservation.vehicle_number,
        'time_in': reservation.time_in.strftime('%Y-%m-%d %H:%M'),
        'time_out': reservation.time_out.strftime('%Y-%m-%d %H:%M') if reservation.time_out else None,
        'estimated_cost': estimated_cost
    })

@app.route('/api/admin/summary')
def api_admin_summary():
    lots = ParkingLot.query.all()
    total_lots = len(lots)
    total_spots = 0
    total_occupied = 0
    lot_names = []
    lot_occupied = []
    lot_vacant = []
    revenues = []
    for lot in lots:
        spots = ParkingSpot.query.filter_by(lot_id=lot.id).all()
        occupied = sum(1 for s in spots if s.status == 'occupied')
        vacant = sum(1 for s in spots if s.status == 'vacant')
        total_spots += len(spots)
        total_occupied += occupied
        lot_names.append(lot.location_name)
        lot_occupied.append(occupied)
        lot_vacant.append(vacant)
        # Calculate revenue: count completed reservations for this lot
        spot_ids = [s.id for s in spots]
        if spot_ids:
            from models.db import Reservation
            completed_reservations = Reservation.query.filter(Reservation.spot_id.in_(spot_ids), Reservation.time_out != None).count()
        else:
            completed_reservations = 0
        revenues.append(completed_reservations * lot.price)
    total_vacant = total_spots - total_occupied
    return jsonify({
        'total_lots': total_lots,
        'total_spots': total_spots,
        'total_occupied': total_occupied,
        'total_vacant': total_vacant,
        'lot_names': lot_names,
        'lot_occupied': lot_occupied,
        'lot_vacant': lot_vacant,
        'revenues': revenues
    })

@app.route('/api/user/lots')
def user_get_lots():
    lots = ParkingLot.query.all()
    result = []
    for lot in lots:
        spots = ParkingSpot.query.filter_by(lot_id=lot.id, status='vacant').all()
        result.append({
            'id': lot.id,
            'location_name': lot.location_name,
            'address': lot.address,
            'pin_code': lot.pin_code,
            'price': lot.price,
            'available_spots': len(spots)
        })
    return jsonify({'lots': result})

@app.route('/api/user/reserve', methods=['POST'])
def user_reserve_spot():
    data = request.get_json()
    user_id = data.get('user_id')
    lot_id = data.get('lot_id')
    vehicle_number = data.get('vehicle_number', 'N/A')
    # Find first available spot in the lot
    spot = ParkingSpot.query.filter_by(lot_id=lot_id, status='vacant').first()
    if not spot:
        return jsonify({'error': 'No available spots in this lot'}), 400
    # Mark spot as occupied
    spot.status = 'occupied'
    # Create reservation
    reservation = Reservation(
        spot_id=spot.id,
        user_id=user_id,
        vehicle_number=vehicle_number
    )
    db.session.add(reservation)
    db.session.commit()
    return jsonify({'message': 'Spot reserved', 'lot_id': lot_id, 'spot_id': spot.id, 'reservation_id': reservation.id})

@app.route('/api/user/vacate', methods=['POST'])
def user_vacate_spot():
    data = request.get_json()
    user_id = data.get('user_id')
    if not user_id:
        print("Missing user_id in request")
        return jsonify({'error': 'Missing user_id'}), 400
    reservation = Reservation.query.filter_by(user_id=user_id, time_out=None).order_by(Reservation.time_in.desc()).first()
    if not reservation:
        print(f"No active reservation found for user_id={user_id}")
        return jsonify({'error': 'No active reservation found'}), 400
    try:
        time_in = reservation.time_in
        time_out = datetime.utcnow()
        spot = ParkingSpot.query.get(reservation.spot_id)
        lot = ParkingLot.query.get(spot.lot_id)
        duration_hours = (time_out - time_in).total_seconds() / 3600
        duration_hours = max(1, int(duration_hours + 0.99))  # round up to next hour, min 1 hour
        estimated_cost = duration_hours * lot.price
        reservation.time_out = time_out
        if not spot:
            print(f"Spot not found for spot_id={reservation.spot_id}")
            return jsonify({'error': 'Spot not found'}), 400
        if spot.status == 'vacant':
            print(f"Spot {spot.id} is already vacant for user {user_id}")
            db.session.commit()
            return jsonify({'message': 'Spot was already vacant, but reservation ended.', 'cost': estimated_cost})
        spot.status = 'vacant'
        db.session.commit()
        print(f"Spot {spot.id} vacated for user {user_id}")
        return jsonify({'message': f'Spot vacated. You have to pay {estimated_cost} for {duration_hours} hour(s).', 'cost': estimated_cost, 'hours': duration_hours})
    except Exception as e:
        db.session.rollback()
        print(f"Error vacating spot: {e}")
        return jsonify({'error': 'Database error', 'details': str(e)}), 500

@app.route('/api/user/summary/<int:user_id>')
def user_summary(user_id):
    reservations = Reservation.query.filter_by(user_id=user_id).order_by(Reservation.time_in.desc()).all()
    result = []
    for r in reservations:
        lot = ParkingLot.query.join(ParkingSpot).filter(ParkingSpot.id == r.spot_id, ParkingSpot.lot_id == ParkingLot.id).first()
        spot = ParkingSpot.query.get(r.spot_id)
        duration = None
        if r.time_out:
            duration = str(r.time_out - r.time_in)
        result.append({
            'lot_name': lot.location_name if lot else '',
            'spot': spot.id if spot else '',
            'vehicle_number': r.vehicle_number,
            'time_in': r.time_in.strftime('%Y-%m-%d %H:%M'),
            'time_out': r.time_out.strftime('%Y-%m-%d %H:%M') if r.time_out else '',
            'duration': duration or ''
        })
    return jsonify({'reservations': result})

@app.route('/api/user/lots/search')
def user_search_lots():
    location = request.args.get('location', '').strip().lower()
    pincode = request.args.get('pincode', '').strip()
    name = request.args.get('name', '').strip().lower()
    available_only = request.args.get('available_only', 'false').lower() == 'true'

    lots_query = ParkingLot.query
    if location:
        lots_query = lots_query.filter(ParkingLot.address.ilike(f"%{location}%"))
    if pincode:
        lots_query = lots_query.filter(ParkingLot.pin_code == pincode)
    if name:
        lots_query = lots_query.filter(ParkingLot.location_name.ilike(f"%{name}%"))
    lots = lots_query.all()
    result = []
    for lot in lots:
        spots = ParkingSpot.query.filter_by(lot_id=lot.id, status='vacant').all()
        available_spots = len(spots)
        if available_only and available_spots == 0:
            continue
        result.append({
            'id': lot.id,
            'location_name': lot.location_name,
            'address': lot.address,
            'pin_code': lot.pin_code,
            'price': lot.price,
            'available_spots': available_spots
        })
    return jsonify({'lots': result})

@app.route('/user.html')
def user_dashboard():
    return render_template('user.html')

if __name__ == '__main__':
    app.run(debug=True)
