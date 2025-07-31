import sqlite3

def force_delete_all_lots():
    """
    Forcefully delete ALL parking lots, spots, and reservations from the database
    WARNING: This will permanently delete all data!
    """
    conn = sqlite3.connect('parking_realtime.db')
    cursor = conn.cursor()
    
    try:
        print("🚨 FORCE DELETING ALL PARKING LOTS...")
        
        # Step 1: Delete all reservations first
        cursor.execute('DELETE FROM reservations')
        deleted_reservations = cursor.rowcount
        print(f"✅ Deleted {deleted_reservations} reservations")
        
        # Step 2: Delete all parking spots
        cursor.execute('DELETE FROM parking_spots')
        deleted_spots = cursor.rowcount
        print(f"✅ Deleted {deleted_spots} parking spots")
        
        # Step 3: Delete all parking lots
        cursor.execute('DELETE FROM parking_lots')
        deleted_lots = cursor.rowcount
        print(f"✅ Deleted {deleted_lots} parking lots")
        
        # Commit all changes
        conn.commit()
        print("\n🎉 ALL PARKING LOTS FORCEFULLY DELETED!")
        print("Database is now clean of all parking data.")
        
        # Verify deletion
        cursor.execute('SELECT COUNT(*) FROM parking_lots')
        remaining_lots = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM parking_spots')
        remaining_spots = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM reservations')
        remaining_reservations = cursor.fetchone()[0]
        
        print(f"\n📊 VERIFICATION:")
        print(f"   Remaining lots: {remaining_lots}")
        print(f"   Remaining spots: {remaining_spots}")
        print(f"   Remaining reservations: {remaining_reservations}")
        
        if remaining_lots == 0 and remaining_spots == 0 and remaining_reservations == 0:
            print("✅ SUCCESS: All parking data has been completely removed!")
        else:
            print("❌ WARNING: Some data may still remain!")
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    # Ask for confirmation
    print("⚠️  WARNING: This will PERMANENTLY DELETE ALL parking lots, spots, and reservations!")
    print("⚠️  This action CANNOT be undone!")
    
    confirm = input("\nType 'DELETE ALL' to confirm: ").strip()
    
    if confirm == "DELETE ALL":
        force_delete_all_lots()
    else:
        print("❌ Operation cancelled. No data was deleted.")
