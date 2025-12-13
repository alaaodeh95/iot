"""
Security Test Script for IoT Smart Home System
Tests authentication, authorization, and security features
"""
import requests
import json
import time
from datetime import datetime
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from backend.config import Config
from backend.security import SecurityManager

class SecurityTester:
    """Test security implementation"""
    
    def __init__(self, base_url="http://localhost:5000"):
        """Initialize security tester"""
        self.base_url = base_url
        self.security_manager = SecurityManager(Config)
        self.device_tokens = {}
        
        print(f"Security Tester initialized for {base_url}")
        print("=" * 50)
    
    def test_unauthenticated_access(self):
        """Test that protected endpoints reject unauthenticated requests"""
        print("🔒 Testing unauthenticated access...")
        
        try:
            # Test sensor data endpoint without auth
            response = requests.post(
                f"{self.base_url}/api/sensor-data",
                json={"device_id": "test", "readings": []},
                timeout=5
            )
            
            if response.status_code == 401:
                print("✓ Sensor data endpoint correctly rejects unauthenticated requests")
            else:
                print(f"❌ Sensor data endpoint should return 401, got {response.status_code}")
        except Exception as e:
            print(f"❌ Error testing sensor endpoint: {e}")
        
        try:
            # Test system status without API key
            response = requests.get(f"{self.base_url}/api/status", timeout=5)
            
            if response.status_code == 401:
                print("✓ System status endpoint correctly rejects requests without API key")
            else:
                print(f"❌ System status should return 401, got {response.status_code}")
        except Exception as e:
            print(f"❌ Error testing status endpoint: {e}")
    
    def test_api_key_authentication(self):
        """Test API key authentication"""
        print("🔑 Testing API key authentication...")
        
        try:
            # Test with correct API key
            headers = {"X-API-Key": Config.API_KEY}
            response = requests.get(f"{self.base_url}/api/status", headers=headers, timeout=5)
            
            if response.status_code == 200:
                print("✓ API key authentication successful")
            else:
                print(f"❌ API key authentication failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Error testing valid API key: {e}")
        
        try:
            # Test with wrong API key
            headers = {"X-API-Key": "wrong-key"}
            response = requests.get(f"{self.base_url}/api/status", headers=headers, timeout=5)
        
        if response.status_code == 401:
            print("✓ Invalid API key correctly rejected")
        else:
            print(f"❌ Invalid API key should return 401, got {response.status_code}")
    
    def test_device_token_generation(self):
        """Test JWT token generation for devices"""
        print("🎫 Testing device token generation...")
        
        headers = {
            "X-API-Key": Config.API_KEY,
            "Content-Type": "application/json"
        }
        
        for device_id in ["roof_station", "living_room", "kitchen"]:\n            response = requests.post(\n                f\"{self.base_url}/api/device/token\",\n                json={\"device_id\": device_id},\n                headers=headers,\n                timeout=5\n            )\n            \n            if response.status_code == 200:\n                token_data = response.json()\n                self.device_tokens[device_id] = token_data['token']\n                print(f\"✓ Token generated for {device_id}\")\n            else:\n                print(f\"❌ Token generation failed for {device_id}: {response.status_code}\")\n    \n    def test_device_authentication(self):\n        \"\"\"Test device authentication with JWT tokens\"\"\"\n        print(\"📱 Testing device authentication...\")\n        \n        if not self.device_tokens:\n            print(\"❌ No tokens available for testing\")\n            return\n        \n        device_id = \"roof_station\"\n        if device_id not in self.device_tokens:\n            print(f\"❌ No token for {device_id}\")\n            return\n        \n        # Create test sensor data\n        sensor_data = {\n            \"device_id\": device_id,\n            \"location\": \"roof\",\n            \"readings\": [\n                {\n                    \"sensor_type\": \"temperature\",\n                    \"value\": 25.5,\n                    \"unit\": \"°C\",\n                    \"timestamp\": datetime.utcnow().isoformat()\n                }\n            ]\n        }\n        \n        # Create headers with JWT token\n        headers = {\n            \"Authorization\": f\"Bearer {self.device_tokens[device_id]}\",\n            \"Content-Type\": \"application/json\"\n        }\n        \n        # Add signature if request signing is enabled\n        if Config.ENABLE_REQUEST_SIGNING:\n            try:\n                signature = self.security_manager.sign_request(sensor_data, device_id)\n                headers[\"X-Signature\"] = signature\n                print(f\"✓ Request signature added: {signature[:16]}...\")\n            except Exception as e:\n                print(f\"❌ Error creating signature: {e}\")\n        \n        # Send authenticated request\n        response = requests.post(\n            f\"{self.base_url}/api/sensor-data\",\n            json=sensor_data,\n            headers=headers,\n            timeout=10\n        )\n        \n        if response.status_code == 200:\n            print(\"✓ Device authentication successful\")\n            print(\"✓ Sensor data sent successfully\")\n        else:\n            print(f\"❌ Device authentication failed: {response.status_code}\")\n            try:\n                print(f\"Error: {response.json()}\")\n            except:\n                print(f\"Error: {response.text}\")\n    \n    def test_gateway_authentication(self):\n        \"\"\"Test gateway authentication\"\"\"\n        print(\"🌉 Testing gateway authentication...\")\n        \n        # Create test gateway data\n        gateway_data = {\n            \"device_id\": \"roof_station\",\n            \"location\": \"roof\",\n            \"readings\": [\n                {\n                    \"sensor_type\": \"temperature\",\n                    \"value\": 24.8,\n                    \"unit\": \"°C\",\n                    \"timestamp\": datetime.utcnow().isoformat()\n                }\n            ],\n            \"gateway_processed\": True,\n            \"gateway_stats\": {\n                \"outliers_removed\": 0,\n                \"outlier_details\": []\n            }\n        }\n        \n        # Test with correct gateway key\n        headers = {\n            \"X-Gateway-Key\": Config.GATEWAY_API_KEY,\n            \"Content-Type\": \"application/json\"\n        }\n        \n        response = requests.post(\n            f\"{self.base_url}/api/sensor-data/gateway\",\n            json=gateway_data,\n            headers=headers,\n            timeout=10\n        )\n        \n        if response.status_code == 200:\n            print(\"✓ Gateway authentication successful\")\n        else:\n            print(f\"❌ Gateway authentication failed: {response.status_code}\")\n        \n        # Test with wrong gateway key\n        headers[\"X-Gateway-Key\"] = \"wrong-gateway-key\"\n        response = requests.post(\n            f\"{self.base_url}/api/sensor-data/gateway\",\n            json=gateway_data,\n            headers=headers,\n            timeout=5\n        )\n        \n        if response.status_code == 401:\n            print(\"✓ Invalid gateway key correctly rejected\")\n        else:\n            print(f\"❌ Invalid gateway key should return 401, got {response.status_code}\")\n    \n    def test_rate_limiting(self):\n        \"\"\"Test rate limiting functionality\"\"\"\n        print(\"⏱️  Testing rate limiting...\")\n        \n        if \"roof_station\" not in self.device_tokens:\n            print(\"❌ No token available for rate limit testing\")\n            return\n        \n        device_id = \"roof_station\"\n        headers = {\n            \"Authorization\": f\"Bearer {self.device_tokens[device_id]}\",\n            \"Content-Type\": \"application/json\"\n        }\n        \n        # Send multiple rapid requests\n        success_count = 0\n        rate_limited_count = 0\n        \n        for i in range(5):  # Send 5 requests quickly\n            sensor_data = {\n                \"device_id\": device_id,\n                \"location\": \"roof\",\n                \"readings\": [\n                    {\n                        \"sensor_type\": \"temperature\",\n                        \"value\": 25.0 + i,\n                        \"unit\": \"°C\",\n                        \"timestamp\": datetime.utcnow().isoformat()\n                    }\n                ]\n            }\n            \n            # Add signature if needed\n            if Config.ENABLE_REQUEST_SIGNING:\n                try:\n                    signature = self.security_manager.sign_request(sensor_data, device_id)\n                    headers[\"X-Signature\"] = signature\n                except Exception as e:\n                    print(f\"❌ Error creating signature: {e}\")\n            \n            response = requests.post(\n                f\"{self.base_url}/api/sensor-data\",\n                json=sensor_data,\n                headers=headers,\n                timeout=5\n            )\n            \n            if response.status_code == 200:\n                success_count += 1\n            elif response.status_code == 429:\n                rate_limited_count += 1\n            \n            time.sleep(0.1)  # Small delay between requests\n        \n        print(f\"✓ Rate limiting test completed: {success_count} success, {rate_limited_count} rate limited\")\n    \n    def test_security_headers(self):\n        \"\"\"Test security headers in responses\"\"\"\n        print(\"🛡️  Testing security headers...\")\n        \n        headers = {\"X-API-Key\": Config.API_KEY}\n        response = requests.get(f\"{self.base_url}/api/status\", headers=headers, timeout=5)\n        \n        security_headers = [\n            'X-Content-Type-Options',\n            'X-Frame-Options',\n            'X-XSS-Protection'\n        ]\n        \n        for header in security_headers:\n            if header in response.headers:\n                print(f\"✓ {header}: {response.headers[header]}\")\n            else:\n                print(f\"❌ Missing security header: {header}\")\n    \n    def run_all_tests(self):\n        \"\"\"Run all security tests\"\"\"\n        print(\"Starting Security Tests...\")\n        print(\"=\" * 50)\n        \n        try:\n            self.test_unauthenticated_access()\n            print()\n            \n            self.test_api_key_authentication()\n            print()\n            \n            self.test_device_token_generation()\n            print()\n            \n            self.test_device_authentication()\n            print()\n            \n            self.test_gateway_authentication()\n            print()\n            \n            self.test_rate_limiting()\n            print()\n            \n            self.test_security_headers()\n            print()\n            \n            print(\"=\" * 50)\n            print(\"✅ Security tests completed!\")\n            \n        except Exception as e:\n            print(f\"❌ Test error: {e}\")\n            \n        except KeyboardInterrupt:\n            print(\"\\n⏹️  Tests interrupted by user\")\n\ndef main():\n    \"\"\"Run security tests\"\"\"\n    print(\"IoT Smart Home Security Tests\")\n    print(\"Make sure the controller server is running on localhost:5000\")\n    print()\n    \n    # Check if server is accessible\n    try:\n        response = requests.get(\"http://localhost:5000/\", timeout=5)\n        if response.status_code == 200:\n            print(\"✓ Controller server is accessible\")\n            print()\n        else:\n            print(\"❌ Controller server returned non-200 status\")\n            return\n    except Exception as e:\n        print(f\"❌ Cannot connect to controller server: {e}\")\n        print(\"Please start the controller server first\")\n        return\n    \n    # Run tests\n    tester = SecurityTester()\n    tester.run_all_tests()\n\nif __name__ == \"__main__\":\n    main()