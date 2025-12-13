"""
Simple Security Test Script for IoT Smart Home System
"""
import requests
import time
from datetime import datetime

def test_security(base_url="http://localhost:5000"):
    """Test basic security features"""
    print("IoT Security Tests")
    print("=" * 40)
    
    # Test 1: Unauthenticated access should be rejected
    print("1. Testing unauthenticated access...")
    try:
        response = requests.get(f"{base_url}/api/status", timeout=5)
        if response.status_code == 401:
            print("✓ Unauthenticated request correctly rejected")
        else:
            print(f"❌ Expected 401, got {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: API Key authentication
    print("\\n2. Testing API key authentication...")
    api_key = "iot-secure-api-key-2024"  # Default from config
    headers = {"X-API-Key": api_key}
    
    try:
        response = requests.get(f"{base_url}/api/status", headers=headers, timeout=5)
        if response.status_code == 200:
            print("✓ API key authentication successful")
            print(f"  Response: {response.json().get('status')}")
        else:
            print(f"❌ API key auth failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: Wrong API key
    print("\\n3. Testing invalid API key...")
    headers = {"X-API-Key": "wrong-key"}
    try:
        response = requests.get(f"{base_url}/api/status", headers=headers, timeout=5)
        if response.status_code == 401:
            print("✓ Invalid API key correctly rejected")
        else:
            print(f"❌ Expected 401, got {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 4: Device token generation
    print("\\n4. Testing device token generation...")
    headers = {"X-API-Key": api_key, "Content-Type": "application/json"}
    try:
        response = requests.post(
            f"{base_url}/api/device/token",
            json={"device_id": "roof_station"},
            headers=headers,
            timeout=5
        )
        if response.status_code == 200:
            token_data = response.json()
            print("✓ Device token generated successfully")
            print(f"  Device: {token_data.get('device_id')}")
            print(f"  Expires in: {token_data.get('expires_in')} seconds")
            return token_data.get('token')  # Return token for further tests
        else:
            print(f"❌ Token generation failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    return None

def test_device_communication(base_url="http://localhost:5000", token=None):
    """Test device communication with authentication"""
    if not token:
        print("\\n❌ No token available for device communication test")
        return
    
    print("\\n5. Testing authenticated device communication...")
    
    # Create test sensor data
    sensor_data = {
        "device_id": "roof_station",
        "location": "roof",
        "readings": [
            {
                "sensor_type": "temperature",
                "value": 25.5,
                "unit": "°C",
                "timestamp": datetime.utcnow().isoformat()
            }
        ]
    }
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/sensor-data",
            json=sensor_data,
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            print("✓ Authenticated sensor data sent successfully")
            result = response.json()
            print(f"  Processed: {result.get('readings_processed', 'N/A')} readings")
        else:
            print(f"❌ Sensor data failed: {response.status_code}")
            try:
                error = response.json()
                print(f"  Error: {error.get('error')}")
            except:
                print(f"  Response: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    """Run security tests"""
    print("Starting IoT Security Tests...")
    print("Make sure the controller is running on localhost:5000\\n")
    
    # Check server availability
    try:
        response = requests.get("http://localhost:5000/", timeout=5)
        print(f"✓ Server is accessible (status: {response.status_code})\\n")
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        print("Please start the controller first: python backend/controller/main.py")
        return
    
    # Run basic security tests
    token = test_security()
    
    # Run device communication tests
    test_device_communication(token=token)
    
    print("\\n" + "=" * 40)
    print("Security tests completed!")

if __name__ == "__main__":
    main()