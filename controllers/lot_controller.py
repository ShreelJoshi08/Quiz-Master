from flask import Blueprint, request, jsonify
from models.db import db, ParkingLot

# Create Blueprint for parking lot routes
lot_controller = Blueprint('lot_controller', __name__)

@lot_controller.route('/add-parking-lot', methods=['POST'])
def add_parking_lot():
    data = request.get_json()

    required_fields = ['location_name', 'address', 'price', 'pin_code', 'max_spots']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing field: {field}"}), 400

    try:
        new_lot = ParkingLot(
            location_name=data['location_name'],
            address=data['address'],
            price=float(data['price']),
            pin_code=str(data['pin_code']),
            max_spots=int(data['max_spots'])
        )
        db.session.add(new_lot)
        db.session.commit()

        return jsonify({"message": "Parking lot added successfully"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@lot_controller.route('/api/admin/lots/<int:lot_id>', methods=['PUT'])
def update_parking_lot(lot_id):
    data = request.get_json()
    lot = ParkingLot.query.get(lot_id)
    if not lot:
        return jsonify({'error': 'Parking lot not found'}), 404

    lot.location_name = data.get('location_name', lot.location_name)
    lot.address = data.get('address', lot.address)
    lot.pin_code = data.get('pin_code', lot.pin_code)
    lot.price = data.get('price', lot.price)
    lot.max_spots = data.get('max_spots', lot.max_spots)

    db.session.commit()
    return jsonify({'message': 'Parking lot updated successfully'})
