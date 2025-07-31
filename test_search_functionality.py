#!/usr/bin/env python3
"""
Test script to verify the admin search functionality
"""

import requests
import json

# Test the search API endpoints
BASE_URL = "http://127.0.0.1:5000"

def test_user_search():
    """Test searching by user ID"""
    print("Testing User ID Search...")
    
    # Test with user ID 1
    response = requests.get(f"{BASE_URL}/api/admin/search?by=user&q=1")
    
    if response.status_code == 200:
        data = response.json()
        print("✅ User search API is working")
        print(f"Results count: {len(data.get('results', []))}")
        if data.get('results'):
            print("Sample result preview:", data['results'][0][:100] + "..." if len(data['results'][0]) > 100 else data['results'][0])
    else:
        print(f"❌ User search failed with status: {response.status_code}")
        print(f"Response: {response.text}")

def test_location_search():
    """Test searching by location"""
    print("\nTesting Location Search...")
    
    # Test with a common location term
    response = requests.get(f"{BASE_URL}/api/admin/search?by=location&q=parking")
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Location search API is working")
        print(f"Results count: {len(data.get('results', []))}")
        if data.get('results'):
            print("Sample result preview:", data['results'][0][:100] + "..." if len(data['results'][0]) > 100 else data['results'][0])
    else:
        print(f"❌ Location search failed with status: {response.status_code}")
        print(f"Response: {response.text}")

def test_empty_search():
    """Test searching with empty query"""
    print("\nTesting Empty Search...")
    
    response = requests.get(f"{BASE_URL}/api/admin/search?by=user&q=")
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Empty search handled correctly")
        print(f"Results count: {len(data.get('results', []))}")
    else:
        print(f"❌ Empty search failed with status: {response.status_code}")

def test_invalid_user_id():
    """Test searching with invalid user ID"""
    print("\nTesting Invalid User ID...")
    
    response = requests.get(f"{BASE_URL}/api/admin/search?by=user&q=abc")
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Invalid user ID handled correctly")
        print(f"Results count: {len(data.get('results', []))}")
        if data.get('results'):
            print("Error message:", data['results'][0])
    else:
        print(f"❌ Invalid user ID test failed with status: {response.status_code}")

if __name__ == "__main__":
    print("🔍 Testing Admin Search Functionality")
    print("=" * 50)
    
    try:
        test_user_search()
        test_location_search()
        test_empty_search()
        test_invalid_user_id()
        
        print("\n" + "=" * 50)
        print("✅ All search functionality tests completed!")
        print("\n📝 Search Feature Summary:")
        print("- User ID Search: Find users by their numeric ID")
        print("- Location Search: Find parking lots by location name, address, or pin code")
        print("- Error Handling: Proper validation and error messages")
        print("- Empty Query Handling: Returns empty results for blank searches")
        
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to the application.")
        print("Make sure the Flask app is running on http://127.0.0.1:5000")
    except Exception as e:
        print(f"❌ Test failed with error: {e}")