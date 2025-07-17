import sqlite3

def add_sample_data():
    print("=== Adding Sample Parking Data ===")
    
    conn = sqlite3.connect('parking_realtime.db')
    cursor = conn.cursor()
    
    # Add sample parking lots
    sample_lots = [
        ('Downtown Mall Parking', '123 Main Street, Downtown', '12345', 5.00, 20),
        ('Airport Parking Lot A', '456 Airport Road', '67890', 8.00, 15),
        ('Shopping Center Parking', '789 Shopping Ave', '11111', 3.50, 25),
        ('Office Complex Parking', '321 Business Blvd', '22222', 6.00, 30),
        ('Hospital Parking', '654 Medical Drive', '33333', 4.00, 40)
    ]
    
    for lot in sample_lots:
        try:
            cursor.execute('''
                INSERT INTO parking_lots (location_name, address, pin_code, price, max_spots)
                VALUES (?, ?, ?, ?, ?)
            ''', lot)
            lot_id = cursor.lastrowid
            
            # Add parking spots for this lot
            for i in range(lot[4]):  # max_spots
                cursor.execute('''
                    INSERT INTO parking_spots (lot_id, status)
                    VALUES (?, 'vacant')
                ''', (lot_id,))
            
            print(f"Added {lot[0]} with {lot[4]} spots")
            
        except sqlite3.IntegrityError:
            print(f"Lot {lot[0]} already exists, skipping...")
    
    conn.commit()
    conn.close()
    print("Sample data added successfully!")

if __name__ == "__main__":
    add_sample_data() 