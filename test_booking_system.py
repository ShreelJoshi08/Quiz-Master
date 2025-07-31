#!/usr/bin/env python3
"""
Test script to verify the booking system is working correctly
"""

import requests
import json

BASE_URL = "http://127.0.0.1:5000"

def test_user_login():
    """Test user login"""
    print("=== Testing User Login ===")
    response = requests.post(f"{BASE_URL}/login", json={
        "login_field": "9876543210",
        "password": "TestPass123!"
    })
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Login successful: {data}")
        return data.get('user_id')
    else:
        print(f"❌ Login failed: {response.status_code} - {response.text}")
        return None

def test_get_lots():
    """Test getting available parking lots"""
    print("\n=== Testing Get Parking Lots ===")
    response = requests.get(f"{BASE_URL}/api/user/lots")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Got {len(data['lots'])} parking lots")
        for lot in data['lots']:
            print(f"   Lot {lot['id']}: {lot['location_name']} - {lot['available_spots']} spots available")
        return data['lots']
    else:
        print(f"❌ Failed to get lots: {response.status_code} - {response.text}")
        return []

def test_reserve_spot(user_id, lot_id):
    """Test reserving a parking spot"""
    print(f"\n=== Testing Spot Reservation ===")
    vehicle_number = "MH12AB3456"  # Valid Indian number plate
    
    response = requests.post(f"{BASE_URL}/api/user/reserve", json={
        "user_id": user_id,
        "lot_id": lot_id,
        "vehicle_number": vehicle_number
    })
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Spot reserved successfully: {data}")
        return True
    else:
        data = response.json() if response.content else {}
        print(f"❌ Reservation failed: {response.status_code} - {data.get('error', response.text)}")
        return False

def test_multiple_booking(user_id, lot_id):
    """Test multiple vehicle booking"""
    print(f"\n=== Testing Multiple Vehicle Booking ===")
    vehicle_numbers = ["GJ01AB1234", "MH12CD5678", "DL8CAF2023"]
    
    response = requests.post(f"{BASE_URL}/api/user/reserve-multiple", json={
        "user_id": user_id,
        "lot_id": lot_id,
        "vehicle_numbers": vehicle_numbers
    })
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Multiple booking successful: {data}")
        return True
    else:
        data = response.json() if response.content else {}
        print(f"❌ Multiple booking failed: {response.status_code} - {data.get('error', response.text)}")
        return False

def test_admin_create_lot():
    """Test admin creating a new parking lot"""
    print(f"\n=== Testing Admin Create Lot ===")
    
    response = requests.post(f"{BASE_URL}/api/admin/lots", json={
        "location_name": "Test Mall",
        "address": "123 Test Street, Test City",
        "pin_code": "123456",
        "price": 50.0,
        "max_spots": 8
    })
    
    if response.status_code == 201:
        data = response.json()
        print(f"✅ Lot created successfully: {data}")
        return data.get('lot_id')
    else:
        data = response.json() if response.content else {}
        print(f"❌ Lot creation failed: {response.status_code} - {data.get('error', response.text)}")
        return None

def test_admin_create_lot_invalid():
    """Test admin creating lot with invalid max spots (>10)"""
    print(f"\n=== Testing Admin Create Lot (Invalid - >10 spots) ===")
    
    response = requests.post(f"{BASE_URL}/api/admin/lots", json={
        "location_name": "Invalid Mall",
        "address": "456 Invalid Street",
        "pin_code": "654321",
        "price": 60.0,
        "max_spots": 15  # Should fail - more than 10
    })
    
    if response.status_code == 400:
        data = response.json()
        print(f"✅ Correctly rejected invalid lot: {data.get('error')}")
        return True
    else:
        print(f"❌ Should have rejected lot with >10 spots: {response.status_code}")
        return False

def main():
    print("🚗 Testing Parking Management System")
    print("=" * 50)
    
    # Test user login
    user_id = test_user_login()
    if not user_id:
        print("Cannot continue without valid user login")
        return
    
    # Test getting lots
    lots = test_get_lots()
    if not lots:
        print("No parking lots available for testing")
        return
    
    # Find a lot with available spots
    available_lot = None
    for lot in lots:
        if lot['available_spots'] > 0:
            available_lot = lot
            break
    
    if not available_lot:
        print("No lots with available spots found")
        # Test admin creating a lot
        lot_id = test_admin_create_lot()
        if lot_id:
            available_lot = {'id': lot_id, 'available_spots': 8}
    
    if available_lot:
        # Test single booking
        test_reserve_spot(user_id, available_lot['id'])
        
        # Test multiple booking (if enough spots)
        if available_lot['available_spots'] >= 3:
            test_multiple_booking(user_id, available_lot['id'])
    
    # Test admin validation
    test_admin_create_lot_invalid()
    
    print("\n🎉 Testing Complete!")

if __name__ == "__main__":
    main()
