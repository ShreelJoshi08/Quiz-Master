import sqlite3
import random

def cleanup_and_create_dummy_data():
    conn = sqlite3.connect('parking_realtime.db')
    cursor = conn.cursor()
    
    print("=== CLEANING UP DATABASE ===")
    
    # Remove users with null mobile numbers
    cursor.execute("SELECT COUNT(*) FROM users WHERE mobile_number IS NULL")
    null_users_count = cursor.fetchone()[0]
    print(f"Found {null_users_count} users with NULL mobile numbers")
    
    if null_users_count > 0:
        cursor.execute("DELETE FROM users WHERE mobile_number IS NULL")
        print(f"Deleted {null_users_count} users with NULL mobile numbers")
    
    # Remove admins with null mobile numbers and add dummy mobile numbers
    cursor.execute("SELECT id, email FROM admin WHERE mobile_number IS NULL")
    null_admins = cursor.fetchall()
    print(f"Found {len(null_admins)} admins with NULL mobile numbers")
    
    for admin_id, email in null_admins:
        # Generate a dummy mobile number (starting with 9 and 9 more random digits)
        dummy_mobile = '9' + ''.join([str(random.randint(0, 9)) for _ in range(9)])
        cursor.execute("UPDATE admin SET mobile_number = ? WHERE id = ?", (dummy_mobile, admin_id))
        print(f"Updated admin ID {admin_id} ({email}) with mobile number: {dummy_mobile}")
    
    print("\n=== CREATING DUMMY USER ===")
    
    # Create a dummy user with all required fields
    dummy_user_data = {
        'full_name': 'Test User',
        'email': 'testuser@example.com',
        'mobile_number': '9876543210',
        'password': 'TestPass123!',
        'address': '123 Test Street, Test City',
        'pin_code': '123456'
    }
    
    try:
        cursor.execute('''
            INSERT INTO users (full_name, email, mobile_number, password, address, pin_code)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            dummy_user_data['full_name'],
            dummy_user_data['email'],
            dummy_user_data['mobile_number'],
            dummy_user_data['password'],
            dummy_user_data['address'],
            dummy_user_data['pin_code']
        ))
        
        user_id = cursor.lastrowid
        print(f"Created dummy user with ID: {user_id}")
        print("DUMMY USER CREDENTIALS:")
        print(f"  Email: {dummy_user_data['email']}")
        print(f"  Mobile: {dummy_user_data['mobile_number']}")
        print(f"  Password: {dummy_user_data['password']}")
        print(f"  Full Name: {dummy_user_data['full_name']}")
        
    except sqlite3.IntegrityError as e:
        print(f"User creation failed (probably already exists): {e}")
        # Try to find existing user with same email or mobile
        cursor.execute("SELECT * FROM users WHERE email = ? OR mobile_number = ?", 
                      (dummy_user_data['email'], dummy_user_data['mobile_number']))
        existing_user = cursor.fetchone()
        if existing_user:
            print("Existing user found with same email/mobile:")
            print(f"  ID: {existing_user[0]}")
            print(f"  Full Name: {existing_user[1]}")
            print(f"  Email: {existing_user[2]}")
            print(f"  Mobile: {existing_user[3]}")
            print(f"  Password: {existing_user[4]}")
    
    print("\n=== CREATING DUMMY ADMIN ===")
    
    # Create a dummy admin
    dummy_admin_data = {
        'email': 'testadmin@example.com',
        'mobile_number': '9876543211',
        'password': 'AdminPass123!'
    }
    
    try:
        cursor.execute('''
            INSERT INTO admin (email, mobile_number, password)
            VALUES (?, ?, ?)
        ''', (
            dummy_admin_data['email'],
            dummy_admin_data['mobile_number'],
            dummy_admin_data['password']
        ))
        
        admin_id = cursor.lastrowid
        print(f"Created dummy admin with ID: {admin_id}")
        print("DUMMY ADMIN CREDENTIALS:")
        print(f"  Email: {dummy_admin_data['email']}")
        print(f"  Mobile: {dummy_admin_data['mobile_number']}")
        print(f"  Password: {dummy_admin_data['password']}")
        
    except sqlite3.IntegrityError as e:
        print(f"Admin creation failed (probably already exists): {e}")
        # Try to find existing admin with same email or mobile
        cursor.execute("SELECT * FROM admin WHERE email = ? OR mobile_number = ?", 
                      (dummy_admin_data['email'], dummy_admin_data['mobile_number']))
        existing_admin = cursor.fetchone()
        if existing_admin:
            print("Existing admin found with same email/mobile:")
            print(f"  ID: {existing_admin[0]}")
            print(f"  Email: {existing_admin[1]}")
            print(f"  Mobile: {existing_admin[2] if len(existing_admin) > 2 else 'N/A'}")
            print(f"  Password: {existing_admin[-1]}")  # Password is last column
    
    conn.commit()
    
    print("\n=== FINAL DATABASE STATE ===")
    
    # Show final users
    cursor.execute("SELECT id, full_name, email, mobile_number, password FROM users")
    users = cursor.fetchall()
    print(f"\nTotal users: {len(users)}")
    for user in users:
        print(f"  ID: {user[0]}, Name: {user[1]}, Email: {user[2]}, Mobile: {user[3]}, Password: {user[4]}")
    
    # Show final admins
    cursor.execute("SELECT id, email, mobile_number, password FROM admin")
    admins = cursor.fetchall()
    print(f"\nTotal admins: {len(admins)}")
    for admin in admins:
        print(f"  ID: {admin[0]}, Email: {admin[1]}, Mobile: {admin[2]}, Password: {admin[3]}")
    
    conn.close()
    
    return dummy_user_data, dummy_admin_data

if __name__ == "__main__":
    user_creds, admin_creds = cleanup_and_create_dummy_data()
    
    print("\n" + "="*50)
    print("SUMMARY - USE THESE CREDENTIALS TO LOGIN:")
    print("="*50)
    print("\nUSER LOGIN:")
    print(f"  Email or Mobile: {user_creds['email']} or {user_creds['mobile_number']}")
    print(f"  Password: {user_creds['password']}")
    
    print("\nADMIN LOGIN:")
    print(f"  Email or Mobile: {admin_creds['email']} or {admin_creds['mobile_number']}")
    print(f"  Password: {admin_creds['password']}")
    print("="*50)
