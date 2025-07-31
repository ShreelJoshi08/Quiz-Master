#!/usr/bin/env python3
"""
Export all users and admins data from the database
"""

import sqlite3

def export_all_data():
    conn = sqlite3.connect('parking_realtime.db')
    cursor = conn.cursor()
    
    print('='*60)
    print('USERS AND ADMINS DATA EXPORT')
    print('='*60)
    
    # Export Users
    print('\n=== USER ACCOUNTS ===')
    cursor.execute('SELECT id, full_name, email, mobile_number, address, pin_code, password FROM users')
    users = cursor.fetchall()
    print(f'Total Users: {len(users)}\n')
    
    for i, user in enumerate(users, 1):
        print(f'{i}. USER ID: {user[0]}')
        print(f'   Name: {user[1]}')
        print(f'   Email: {user[2] or "Not Set"}')
        print(f'   Mobile: {user[3] or "Not Set"}')
        print(f'   Address: {user[4] or "Not Set"}')
        print(f'   PIN Code: {user[5] or "Not Set"}')
        print(f'   Password: {user[6]}')
        print()
    
    # Export Admins
    print('\n=== ADMIN ACCOUNTS ===')
    cursor.execute('SELECT id, email, mobile, mobile_number, password FROM admin')
    admins = cursor.fetchall()
    print(f'Total Admins: {len(admins)}\n')
    
    for i, admin in enumerate(admins, 1):
        print(f'{i}. ADMIN ID: {admin[0]}')
        print(f'   Email: {admin[1]}')
        print(f'   Mobile (old): {admin[2] or "Not Set"}')
        print(f'   Mobile Number: {admin[3] or "Not Set"}')
        print(f'   Password: {admin[4]}')
        print()
    
    # Database Summary
    print('\n=== DATABASE SUMMARY ===')
    cursor.execute('SELECT COUNT(*) FROM parking_lots')
    lot_count = cursor.fetchone()[0]
    print(f'Total Parking Lots: {lot_count}')
    
    cursor.execute('SELECT COUNT(*) FROM parking_spots')
    spot_count = cursor.fetchone()[0]
    print(f'Total Parking Spots: {spot_count}')
    
    cursor.execute('SELECT COUNT(*) FROM reservations')
    reservation_count = cursor.fetchone()[0]
    print(f'Total Reservations: {reservation_count}')
    
    # Show some parking lots details
    if lot_count > 0:
        print('\n=== PARKING LOTS DETAILS ===')
        cursor.execute('SELECT id, location_name, address, pin_code, price, max_spots FROM parking_lots')
        lots = cursor.fetchall()
        for i, lot in enumerate(lots, 1):
            print(f'{i}. LOT ID: {lot[0]} - {lot[1]}')
            print(f'   Address: {lot[2]}')
            print(f'   PIN Code: {lot[3]}')
            print(f'   Price: ₹{lot[4]}/hour')
            print(f'   Max Spots: {lot[5]}')
            print()
    
    conn.close()
    print('='*60)

if __name__ == "__main__":
    export_all_data()
