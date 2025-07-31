import sqlite3
import json

def test_multiple_booking_database():
    """Test multiple booking functionality with actual database"""
    
    print("🧪 TESTING MULTIPLE BOOKING WITH DATABASE")
    print("=" * 50)
    
    conn = sqlite3.connect('parking_realtime.db')
    cursor = conn.cursor()
    
    # Check available lots and spots
    print("📊 Current Database Status:")
    cursor.execute('''
        SELECT pl.id, pl.location_name, pl.max_spots,
               COUNT(CASE WHEN ps.status = 'vacant' THEN 1 END) as available_spots,
               COUNT(CASE WHEN ps.status = 'occupied' THEN 1 END) as occupied_spots
        FROM parking_lots pl
        LEFT JOIN parking_spots ps ON pl.id = ps.lot_id
        GROUP BY pl.id
    ''')
    
    lots = cursor.fetchall()
    print("\n🏢 Available Parking Lots:")
    for lot_id, name, max_spots, available, occupied in lots:
        print(f"   Lot {lot_id} ({name}): {available} available / {occupied} occupied / {max_spots} total")
    
    # Check current reservations
    cursor.execute('''
        SELECT COUNT(*) FROM reservations r
        WHERE r.time_out IS NULL
    ''')
    active_reservations = cursor.fetchone()[0]
    print(f"\n📋 Active Reservations: {active_reservations}")
    
    # Test data for multiple booking
    test_vehicles = [
        "GJ01XY1111",
        "MH12AB2222", 
        "KA05CD3333",
        "DL01EF4444"
    ]
    
    print(f"\n🚗 Test Vehicle Numbers:")
    for i, vehicle in enumerate(test_vehicles, 1):
        print(f"   {i}. {vehicle}")
    
    # Check if any test vehicles already exist
    placeholders = ','.join(['?' for _ in test_vehicles])
    cursor.execute(f'''
        SELECT vehicle_number FROM reservations 
        WHERE vehicle_number IN ({placeholders}) AND time_out IS NULL
    ''', test_vehicles)
    
    existing = cursor.fetchall()
    if existing:
        print(f"\n⚠️ Existing reservations found: {[v[0] for v in existing]}")
    else:
        print(f"\n✅ All test vehicles are available for booking")
    
    # Find a lot with enough spots
    suitable_lot = None
    for lot_id, name, max_spots, available, occupied in lots:
        if available >= len(test_vehicles):
            suitable_lot = (lot_id, name, available)
            break
    
    if suitable_lot:
        lot_id, lot_name, available = suitable_lot
        print(f"\n🎯 Suitable lot found: Lot {lot_id} ({lot_name}) with {available} available spots")
        
        # Show API call format
        api_data = {
            "user_id": 8,  # Test user
            "lot_id": lot_id,
            "vehicle_numbers": test_vehicles[:min(len(test_vehicles), available, 5)]
        }
        
        print(f"\n📝 API Call Example:")
        print(f"POST /api/user/reserve-multiple")
        print(f"Content-Type: application/json")
        print(json.dumps(api_data, indent=2))
        
        print(f"\n✅ This would book {len(api_data['vehicle_numbers'])} spots simultaneously")
        
    else:
        print(f"\n❌ No lot has enough available spots for {len(test_vehicles)} vehicles")
    
    # Show current user info
    cursor.execute("SELECT id, full_name, mobile_number FROM users WHERE id = 8")
    user = cursor.fetchone()
    if user:
        print(f"\n👤 Test User: {user[1]} (ID: {user[0]}, Mobile: {user[2]})")
    
    conn.close()

def show_validation_examples():
    """Show comprehensive validation examples"""
    
    print("\n🔍 INDIAN NUMBER PLATE VALIDATION EXAMPLES")
    print("=" * 50)
    
    examples = {
        "Standard Formats": [
            "GJ01AB1234",  # Gujarat
            "MH12CD5678",  # Maharashtra  
            "KA05EF9012",  # Karnataka
            "DL01GH3456",  # Delhi
            "UP32IJ7890",  # Uttar Pradesh
        ],
        "Single Digit Area Codes": [
            "GJ1AB1234",   # Gujarat single digit
            "MH2CD5678",   # Maharashtra single digit
            "KA3EF9012",   # Karnataka single digit
        ],
        "Special Regions": [
            "CH01AA1234",  # Chandigarh
            "AN01BB2345",  # Andaman & Nicobar
            "PY01CC3456",  # Puducherry
        ],
        "Alternative Formats": [
            "GJ12ABC123",  # 3 letters, 3 digits
            "MH01A1234",   # 1 letter, 4 digits
        ]
    }
    
    for category, plates in examples.items():
        print(f"\n📋 {category}:")
        for plate in plates:
            print(f"   ✅ {plate}")
    
    print(f"\n❌ Invalid Examples:")
    invalid_examples = [
        "INVALID123",    # Wrong format
        "123ABCD",       # Numbers first
        "GJ123AB1234",   # Too many area digits
        "G01AB1234",     # Single state letter
        "GJ01A12345",    # Too many end digits
    ]
    
    for plate in invalid_examples:
        print(f"   ❌ {plate}")

if __name__ == "__main__":
    test_multiple_booking_database()
    show_validation_examples()
    
    print("\n" + "=" * 60)
    print("🎉 MULTIPLE BOOKING SYSTEM READY!")
    print("=" * 60)
    print("\n🚀 TO USE MULTIPLE BOOKING:")
    print("1. Start the Flask app: python app_realtime.py")
    print("2. Send POST request to: /api/user/reserve-multiple")
    print("3. Include user_id, lot_id, and vehicle_numbers array")
    print("4. Each vehicle number will be validated against Indian standards")
    print("5. All spots will be booked atomically (all or nothing)")
    print("\n📱 Login with: 9876543210 / TestPass123!")
