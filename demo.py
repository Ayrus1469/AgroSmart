#!/usr/bin/env python3
"""
AgroSmart Demo Script
This script demonstrates how to interact with the AgroSmart API programmatically.
"""

import requests
import json

# Application URL
BASE_URL = "http://localhost:5001"

def test_agromart_api():
    """Test the AgroSmart API functionality"""
    
    print("🌱 AgroSmart API Demo")
    print("=" * 50)
    
    # Create a session for cookies
    session = requests.Session()
    
    # Test 1: Login
    print("1. Testing login...")
    login_data = {
        'username': 'farmer',
        'password': '12345'
    }
    
    response = session.post(f"{BASE_URL}/login", data=login_data, allow_redirects=False)
    if response.status_code in [302, 303]:
        print("   ✅ Login successful!")
    else:
        print("   ❌ Login failed!")
        return
    
    # Test 2: Access dashboard
    print("2. Testing dashboard access...")
    response = session.get(f"{BASE_URL}/dashboard")
    if response.status_code == 200:
        print("   ✅ Dashboard accessible!")
        print(f"   📄 Page size: {len(response.text)} characters")
    else:
        print("   ❌ Dashboard access failed!")
        return
    
    # Test 3: Make fertilizer prediction
    print("3. Testing fertilizer prediction...")
    
    test_cases = [
        {
            "name": "Cotton on Loamy Soil",
            "data": {
                "Temperature": 25.0,
                "Humidity": 65.0,
                "Moisture": 45.0,
                "Nitrogen": 120.0,
                "Phosphorus": 60.0,
                "Potassium": 80.0,
                "Soil Type": "Loamy",
                "Crop Type": "Cotton"
            }
        },
        {
            "name": "Wheat on Black Soil",
            "data": {
                "Temperature": 22.0,
                "Humidity": 70.0,
                "Moisture": 50.0,
                "Nitrogen": 100.0,
                "Phosphorus": 45.0,
                "Potassium": 60.0,
                "Soil Type": "Black",
                "Crop Type": "Wheat"
            }
        },
        {
            "name": "Rice on Clayey Soil",
            "data": {
                "Temperature": 28.0,
                "Humidity": 80.0,
                "Moisture": 60.0,
                "Nitrogen": 140.0,
                "Phosphorus": 70.0,
                "Potassium": 90.0,
                "Soil Type": "Clayey",
                "Crop Type": "Rice"
            }
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"   Test {i}: {test_case['name']}")
        
        response = session.post(
            f"{BASE_URL}/predict",
            headers={'Content-Type': 'application/json'},
            data=json.dumps(test_case['data'])
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Recommendation: {result['recommendation']}")
            print(f"      Confidence: {result['confidence']:.1f}%")
            print(f"      Method: {result['method']}")
        else:
            try:
                error = response.json()
                print(f"   ❌ Error: {error.get('error', 'Unknown error')}")
            except:
                print(f"   ❌ HTTP Error: {response.status_code}")
        print()
    
    print("4. Testing logout...")
    response = session.get(f"{BASE_URL}/logout")
    if response.status_code in [302, 303]:
        print("   ✅ Logout successful!")
    else:
        print("   ❌ Logout failed!")
    
    print("\n🎉 Demo completed!")
    print(f"\nTo use the web interface, visit: {BASE_URL}")
    print("Login credentials: farmer / 12345")

if __name__ == "__main__":
    try:
        test_agromart_api()
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to AgroSmart application.")
        print("Make sure the application is running on port 5001.")
        print("Run: python3 working_app.py")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")