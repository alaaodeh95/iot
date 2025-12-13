#!/usr/bin/env node

/**
 * UI Security Setup Script
 * Sets up environment variables and security configuration for the frontend
 */

const fs = require('fs');
const path = require('path');

function setupUI() {
  console.log('🔧 Setting up UI Security Configuration...');
  
  // Check if .env exists
  const envPath = path.join(__dirname, '.env');
  const envExamplePath = path.join(__dirname, '.env.example');
  
  if (!fs.existsSync(envPath)) {
    if (fs.existsSync(envExamplePath)) {
      // Copy .env.example to .env
      fs.copyFileSync(envExamplePath, envPath);
      console.log('✅ Created .env file from .env.example');
    } else {
      // Create basic .env file
      const envContent = `VITE_API_URL=http://localhost:5000
VITE_API_KEY=iot-secure-api-key-2024
VITE_ENABLE_HTTPS=false
VITE_SOCKET_AUTH=true
VITE_LOG_LEVEL=info`;
      
      fs.writeFileSync(envPath, envContent);
      console.log('✅ Created .env file with default values');
    }
  } else {
    console.log('ℹ️ .env file already exists');
  }
  
  // Verify package.json has required dependencies
  const packageJsonPath = path.join(__dirname, 'package.json');
  
  if (fs.existsSync(packageJsonPath)) {
    const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));
    const requiredDeps = ['axios', 'socket.io-client'];
    const missingDeps = requiredDeps.filter(dep => !packageJson.dependencies[dep]);
    
    if (missingDeps.length > 0) {
      console.log('⚠️ Missing dependencies:', missingDeps.join(', '));
      console.log('   Run: npm install ' + missingDeps.join(' '));
    } else {
      console.log('✅ All required dependencies are present');
    }
  }
  
  console.log('');
  console.log('🚀 UI Setup Complete!');
  console.log('');
  console.log('Next steps:');
  console.log('1. Update .env file with your API key if different from default');
  console.log('2. Start the backend controller: cd ../backend/controller && python main.py');
  console.log('3. Start the UI development server: npm run dev');
  console.log('4. Open the Security tab in the UI to test connections');
  console.log('');
  console.log('Environment variables:');
  console.log('- VITE_API_URL: Backend server URL');
  console.log('- VITE_API_KEY: API key for authentication (must match backend)');
  console.log('- VITE_ENABLE_HTTPS: Enable HTTPS connections');
  console.log('- VITE_SOCKET_AUTH: Enable WebSocket authentication');
}

// Run setup if this script is executed directly
if (require.main === module) {
  setupUI();
}

module.exports = setupUI;