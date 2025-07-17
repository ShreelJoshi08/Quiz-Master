import sqlite3

def create_admin_user():
    print("=== Create Admin User for Real-time Parking System ===")
    email = input("Enter admin email: ")
    password = input("Enter admin password: ")
    
    conn = sqlite3.connect('parking_realtime.db')
    cursor = conn.cursor()
    
    # Check if admin already exists
    cursor.execute('SELECT * FROM admin WHERE email = ?', (email,))
    if cursor.fetchone():
        print("Admin with this email already exists!")
        conn.close()
        return
    
    # Create new admin user
    try:
        cursor.execute('INSERT INTO admin (email, password) VALUES (?, ?)', (email, password))
        conn.commit()
        print(f"Admin user '{email}' created successfully!")
    except Exception as e:
        print(f"Error creating admin user: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    create_admin_user() 