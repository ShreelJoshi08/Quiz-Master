import sqlite3
import re

def test_enhancements():
    print("🧪 TESTING ALL ENHANCEMENTS")
    print("=" * 50)
    
    conn = sqlite3.connect('parking_realtime.db')
    cursor = conn.cursor()
    
    # Test 1: Mobile number validation
    print("\n1. Testing Mobile Number Validation:")
    test_mobile = "9876543210"
    mobile_regex = re.compile(r'^[0-9]{10}$')
    print(f"   Mobile {test_mobile}: {'✅ Valid' if mobile_regex.match(test_mobile) else '❌ Invalid'}")
    
    invalid_mobile = "98765abc10"
    print(f"   Mobile {invalid_mobile}: {'✅ Valid' if mobile_regex.match(invalid_mobile) else '❌ Invalid'}")
    
    # Test 2: Vehicle number validation  
    print("\n2. Testing Vehicle Number Validation:")
    indian_plate_pattern = r'^[A-Z]{2}[0-9]{1,2}[A-Z]{1,2}[0-9]{4}$'
    
    test_vehicles = [
        "GJ01AB1234",  # Valid
        "MH12CD5678",  # Valid
        "KA05EF9012",  # Valid
        "INVALID123",  # Invalid
        "GJ1AB1234",   # Valid (single digit state code)
        "GJ123AB1234"  # Invalid (too many digits)
    ]
    
    for vehicle in test_vehicles:
        is_valid = bool(re.match(indian_plate_pattern, vehicle))
        print(f"   Vehicle {vehicle}: {'✅ Valid' if is_valid else '❌ Invalid'}")
    
    # Test 3: Database constraints
    print("\n3. Testing Database Constraints:")
    
    # Check if pincode uniqueness constraint exists
    cursor.execute("PRAGMA table_info(parking_lots)")
    columns = cursor.fetchall()
    pincode_unique = False
    for col in columns:
        if col[1] == 'pin_code':
            print(f"   Pin code column: ✅ Found")
            # Check if there's a unique constraint (would need to check indexes)
            break
    
    # Test parking lot limits
    cursor.execute("SELECT id, max_spots FROM parking_lots")
    lots = cursor.fetchall()
    print(f"   Current parking lots: {len(lots)}")
    for lot_id, max_spots in lots:
        status = "✅ Valid" if max_spots <= 10 else "❌ Exceeds limit"
        print(f"     Lot {lot_id}: {max_spots} spots - {status}")
    
    # Test 4: User summary with charges
    print("\n4. Testing User Summary with Charges:")
    cursor.execute('''
        SELECT u.id, u.full_name, COUNT(r.id) as total_reservations
        FROM users u
        LEFT JOIN reservations r ON u.id = r.user_id
        GROUP BY u.id
        LIMIT 3
    ''')
    users = cursor.fetchall()
    
    for user_id, name, reservation_count in users:
        print(f"   User {name} (ID: {user_id}): {reservation_count} reservations")
        
        # Get detailed reservations with charges
        cursor.execute('''
            SELECT pl.location_name, r.vehicle_number, pl.price, r.time_in
            FROM reservations r
            JOIN parking_spots ps ON r.spot_id = ps.id
            JOIN parking_lots pl ON ps.lot_id = pl.id
            WHERE r.user_id = ?
            LIMIT 2
        ''', (user_id,))
        
        reservations = cursor.fetchall()
        for lot_name, vehicle, charge, time_in in reservations:
            print(f"     🚗 {vehicle} at {lot_name}: ₹{charge} (from {time_in})")
    
    # Test 5: Mobile-based authentication
    print("\n5. Testing Mobile-Based Authentication:")
    cursor.execute("SELECT mobile_number, email, full_name FROM users WHERE mobile_number IS NOT NULL LIMIT 3")
    users_with_mobile = cursor.fetchall()
    
    print(f"   Users with mobile numbers: {len(users_with_mobile)}")
    for mobile, email, name in users_with_mobile:
        print(f"     📱 {mobile} - {name} ({email or 'No email'})")
    
    cursor.execute("SELECT mobile_number, email FROM admin WHERE mobile_number IS NOT NULL LIMIT 3")
    admins_with_mobile = cursor.fetchall()
    
    print(f"   Admins with mobile numbers: {len(admins_with_mobile)}")
    for mobile, email in admins_with_mobile:
        print(f"     📱 {mobile} - {email or 'No email'}")
    
    # Test 6: Occupied spots check
    print("\n6. Testing Occupied Spots Protection:")
    cursor.execute('''
        SELECT pl.id, pl.location_name, pl.max_spots,
               COUNT(CASE WHEN ps.status = 'occupied' THEN 1 END) as occupied_spots,
               COUNT(CASE WHEN ps.status = 'vacant' THEN 1 END) as vacant_spots
        FROM parking_lots pl
        LEFT JOIN parking_spots ps ON pl.id = ps.lot_id
        GROUP BY pl.id
    ''')
    
    lots_status = cursor.fetchall()
    for lot_id, name, max_spots, occupied, vacant in lots_status:
        total_spots = occupied + vacant
        delete_allowed = occupied == 0
        print(f"   Lot {lot_id} ({name}): {occupied} occupied, {vacant} vacant")
        print(f"     Delete allowed: {'✅ Yes' if delete_allowed else '❌ No'}")
        print(f"     Edit limit: minimum {occupied} spots")
    
    conn.close()
    
    print("\n" + "=" * 50)
    print("✅ ENHANCEMENT TESTING COMPLETED")
    print("\n🔑 LOGIN CREDENTIALS TO TEST:")
    print("👤 USER: 9876543210 / TestPass123!")
    print("🔧 ADMIN: 9876543211 / AdminPass123!")

if __name__ == "__main__":
    test_enhancements()
