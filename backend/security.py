"""
Security utilities for IoT Smart Home System
Handles authentication, encryption, and request signing
"""
import hashlib
import hmac
import time
import jwt
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple
from functools import wraps
from flask import request, jsonify, current_app
import logging

logger = logging.getLogger(__name__)

class SecurityManager:
    """Handles all security operations"""
    
    def __init__(self, config):
        """Initialize security manager with configuration"""
        self.config = config
        self.api_key = config.API_KEY
        self.gateway_key = config.GATEWAY_API_KEY
        self.device_keys = config.DEVICE_KEYS
        self.jwt_secret = config.JWT_SECRET_KEY
        self.jwt_algorithm = config.JWT_ALGORITHM
        self.rate_limits = {}  # Track rate limiting per device
        
    def generate_device_token(self, device_id: str) -> str:
        """Generate JWT token for device authentication"""
        if device_id not in self.device_keys:
            raise ValueError(f"Unknown device: {device_id}")
        
        payload = {
            'device_id': device_id,
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(hours=self.config.JWT_EXPIRATION_HOURS),
            'type': 'device'
        }
        
        return jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
    
    def verify_device_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token and return payload"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            return None
        except jwt.InvalidTokenError:
            logger.warning("Invalid token")
            return None
    
    def sign_request(self, data: Dict[str, Any], device_id: str) -> str:
        """Create HMAC signature for request data"""
        if device_id not in self.device_keys:
            raise ValueError(f"Unknown device: {device_id}")
        
        # Create canonical string from data
        canonical_string = self._create_canonical_string(data)
        
        # Sign with device-specific key
        signature = hmac.new(
            self.device_keys[device_id].encode('utf-8'),
            canonical_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return signature
    
    def verify_request_signature(self, data: Dict[str, Any], signature: str, device_id: str) -> bool:
        """Verify request signature"""
        try:
            expected_signature = self.sign_request(data, device_id)
            return hmac.compare_digest(signature, expected_signature)
        except Exception as e:
            logger.error(f"Signature verification error: {e}")
            return False
    
    def _create_canonical_string(self, data: Dict[str, Any]) -> str:
        """Create canonical string representation of data for signing"""
        # Sort keys for consistent signing
        import json
        return json.dumps(data, sort_keys=True, separators=(',', ':'))
    
    def check_rate_limit(self, device_id: str) -> bool:
        """Check if device is within rate limits"""
        current_time = time.time()
        minute_window = int(current_time // 60)  # 1-minute windows
        
        if device_id not in self.rate_limits:
            self.rate_limits[device_id] = {}
        
        device_limits = self.rate_limits[device_id]
        
        # Clean old windows (keep only last 2 minutes)
        old_windows = [w for w in device_limits.keys() if w < minute_window - 1]
        for window in old_windows:
            del device_limits[window]
        
        # Check current window
        current_count = device_limits.get(minute_window, 0)
        
        if current_count >= self.config.RATE_LIMIT_PER_MINUTE:
            logger.warning(f"Rate limit exceeded for device {device_id}")
            return False
        
        # Increment counter
        device_limits[minute_window] = current_count + 1
        return True


def require_api_key(f):
    """Decorator to require API key authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        
        if not api_key:
            return jsonify({'error': 'API key required'}), 401
        
        # Get security manager from app context
        security_mgr = current_app.security_manager
        
        if api_key != security_mgr.api_key:
            return jsonify({'error': 'Invalid API key'}), 401
        
        return f(*args, **kwargs)
    return decorated_function


def require_device_auth(f):
    """Decorator to require device authentication (JWT + signature)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check for JWT token
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'JWT token required'}), 401
        
        token = auth_header.split(' ')[1]
        security_mgr = current_app.security_manager
        
        # Verify token
        payload = security_mgr.verify_device_token(token)
        if not payload:
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        device_id = payload.get('device_id')
        
        # Check rate limiting
        if not security_mgr.check_rate_limit(device_id):
            return jsonify({'error': 'Rate limit exceeded'}), 429
        
        # Verify request signature if enabled
        if security_mgr.config.ENABLE_REQUEST_SIGNING:
            signature = request.headers.get('X-Signature')
            if not signature:
                return jsonify({'error': 'Request signature required'}), 401
            
            request_data = request.get_json() if request.is_json else {}
            if not security_mgr.verify_request_signature(request_data, signature, device_id):
                return jsonify({'error': 'Invalid request signature'}), 401
        
        # Add device info to request context
        request.device_id = device_id
        request.device_payload = payload
        
        return f(*args, **kwargs)
    return decorated_function


def require_gateway_auth(f):
    """Decorator to require gateway authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        gateway_key = request.headers.get('X-Gateway-Key')
        
        if not gateway_key:
            return jsonify({'error': 'Gateway key required'}), 401
        
        security_mgr = current_app.security_manager
        
        if gateway_key != security_mgr.gateway_key:
            return jsonify({'error': 'Invalid gateway key'}), 401
        
        return f(*args, **kwargs)
    return decorated_function


def add_security_headers(response):
    """Add security headers to response"""
    from backend.config import Config
    
    for header, value in Config.SECURITY_HEADERS.items():
        response.headers[header] = value
    
    return response


class RequestEncryption:
    """Handles request/response encryption for sensitive data"""
    
    def __init__(self, key: str):
        """Initialize with encryption key"""
        from cryptography.fernet import Fernet
        import base64
        
        # Generate key from string (for demo - use proper key derivation in production)
        key_bytes = hashlib.sha256(key.encode()).digest()
        self.fernet = Fernet(base64.urlsafe_b64encode(key_bytes))
    
    def encrypt_data(self, data: str) -> str:
        """Encrypt string data"""
        return self.fernet.encrypt(data.encode()).decode()
    
    def decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt string data"""
        return self.fernet.decrypt(encrypted_data.encode()).decode()
    
    def encrypt_sensor_data(self, sensor_data: Dict[str, Any]) -> Dict[str, Any]:
        """Encrypt sensitive sensor data"""
        import json
        
        # Encrypt the readings array (most sensitive data)
        if 'readings' in sensor_data:
            readings_json = json.dumps(sensor_data['readings'])
            sensor_data['readings_encrypted'] = self.encrypt_data(readings_json)
            del sensor_data['readings']
            sensor_data['encrypted'] = True
        
        return sensor_data
    
    def decrypt_sensor_data(self, encrypted_sensor_data: Dict[str, Any]) -> Dict[str, Any]:
        """Decrypt sensor data"""
        import json
        
        if encrypted_sensor_data.get('encrypted') and 'readings_encrypted' in encrypted_sensor_data:
            readings_json = self.decrypt_data(encrypted_sensor_data['readings_encrypted'])
            encrypted_sensor_data['readings'] = json.loads(readings_json)
            del encrypted_sensor_data['readings_encrypted']
            del encrypted_sensor_data['encrypted']
        
        return encrypted_sensor_data