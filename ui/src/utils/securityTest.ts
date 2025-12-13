/**
 * UI Security Test Script
 * Tests the frontend security configuration and connection
 */

// This script can be run in the browser console to test security features

async function testUISecurity() {
  console.log('🔍 Testing UI Security Configuration...');
  
  // Test 1: Check environment variables
  console.log('\n1. Environment Configuration:');
  console.log('   API URL:', import.meta.env.VITE_API_URL || 'http://localhost:5000');
  console.log('   API Key:', (import.meta.env.VITE_API_KEY || '').slice(0, 12) + '...');
  console.log('   HTTPS:', import.meta.env.VITE_ENABLE_HTTPS === 'true');
  console.log('   Socket Auth:', import.meta.env.VITE_SOCKET_AUTH === 'true');
  
  // Test 2: Test API connection
  console.log('\n2. Testing API Connection...');
  try {
    const response = await fetch('/api/status', {
      headers: {
        'X-API-Key': import.meta.env.VITE_API_KEY || 'iot-secure-api-key-2024',
        'Content-Type': 'application/json'
      }
    });
    
    if (response.ok) {
      const data = await response.json();
      console.log('   ✅ API connection successful');
      console.log('   Server status:', data.status);
      console.log('   Server time:', data.timestamp);
    } else {
      console.log('   ❌ API connection failed:', response.status, response.statusText);
    }
  } catch (error) {
    console.log('   ❌ API connection error:', error.message);
  }
  
  // Test 3: Check security service
  console.log('\n3. Testing Security Service...');
  try {
    if (window.securityService) {
      const config = window.securityService.getConfig();
      console.log('   ✅ Security service loaded');
      console.log('   Config:', config);
    } else {
      console.log('   ❌ Security service not available');
    }
  } catch (error) {
    console.log('   ❌ Security service error:', error.message);
  }
  
  // Test 4: Check WebSocket connection
  console.log('\n4. Testing WebSocket...');
  try {
    const socket = io({
      auth: {
        'x-api-key': import.meta.env.VITE_API_KEY || 'iot-secure-api-key-2024'
      }
    });
    
    socket.on('connect', () => {
      console.log('   ✅ WebSocket connected with auth');
      socket.disconnect();
    });
    
    socket.on('connect_error', (error) => {
      console.log('   ❌ WebSocket connection error:', error.message);
    });
  } catch (error) {
    console.log('   ❌ WebSocket setup error:', error.message);
  }
  
  console.log('\n🔒 Security test completed!');
}

// Export for use in browser console
if (typeof window !== 'undefined') {
  window.testUISecurity = testUISecurity;
  console.log('💡 Run testUISecurity() in the console to test security features');
}

export default testUISecurity;