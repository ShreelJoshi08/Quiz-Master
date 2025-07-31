import sqlite3
import requests
import json

def test_login():
    # Get a sample user from database
    conn = sqlite3.connect('parking_realtime.db')
    cursor = conn.cursor()
    cursor.execute("SELECT email, password FROM users LIMIT 1")
    user = cursor.fetchone()
    
    if user:
        print(f"Testing login with email: {user[0]}")
        
        # Test login API
        login_data = {
            'login_field': user[0],  # email
            'password': user[1]      # password
        }
        
        try:
            response = requests.post('http://localhost:5000/login', 
                                   json=login_data,
                                   headers={'Content-Type': 'application/json'})
            
            print(f"Response status: {response.status_code}")
            print(f"Response body: {response.text}")
            
        except requests.exceptions.ConnectionError:
            print("Cannot connect to server. Make sure the Flask app is running.")
        except Exception as e:
            print(f"Error: {e}")
    else:
        print("No users found in database")
    
    conn.close()

if __name__ == "__main__":
    test_login()
