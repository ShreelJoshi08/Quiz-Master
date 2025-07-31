import sqlite3

def check_database():
    conn = sqlite3.connect('parking_realtime.db')
    cursor = conn.cursor()
    
    print("=== DATABASE STRUCTURE ===")
    
    # Check users table structure
    print("\nUsers table structure:")
    cursor.execute("PRAGMA table_info(users)")
    columns = cursor.fetchall()
    for col in columns:
        print(f"  {col[1]} ({col[2]}) - nullable: {not col[3]}")
    
    # Check admin table structure
    print("\nAdmin table structure:")
    cursor.execute("PRAGMA table_info(admin)")
    columns = cursor.fetchall()
    for col in columns:
        print(f"  {col[1]} ({col[2]}) - nullable: {not col[3]}")
    
    # Check if there are any users
    print("\n=== DATABASE CONTENT ===")
    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]
    print(f"\nTotal users: {user_count}")
    
    if user_count > 0:
        cursor.execute("SELECT id, full_name, email, mobile_number FROM users LIMIT 5")
        users = cursor.fetchall()
        print("Sample users:")
        for user in users:
            print(f"  ID: {user[0]}, Name: {user[1]}, Email: {user[2]}, Mobile: {user[3]}")
    
    # Check if there are any admins
    cursor.execute("SELECT COUNT(*) FROM admin")
    admin_count = cursor.fetchone()[0]
    print(f"\nTotal admins: {admin_count}")
    
    if admin_count > 0:
        cursor.execute("SELECT id, email, mobile_number FROM admin LIMIT 5")
        admins = cursor.fetchall()
        print("Sample admins:")
        for admin in admins:
            print(f"  ID: {admin[0]}, Email: {admin[1]}, Mobile: {admin[2]}")
    
    conn.close()

if __name__ == "__main__":
    check_database()
