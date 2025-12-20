"""
Gateway component for filtering outliers from sensor data
Acts as an intermediate tier between sensors and main server
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from collections import deque
import statistics
import requests
import sys
import os
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(env_path)

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.config import Config
from backend.security import RequestEncryption

logger = logging.getLogger(__name__)

class SensorGateway:
    """Gateway for filtering sensor data outliers"""
    
    def __init__(self, controller_url: str):
        """Initialize gateway with security"""
        self.controller_url = controller_url
        self.config = Config.OUTLIER_DETECTION
        self.sensor_windows = {}  # Store recent readings for each sensor
        self.statistics_log = []
        self.encryption = RequestEncryption(Config.GATEWAY_API_KEY)
        
        logger.info(f"Secure gateway initialized, forwarding to {controller_url}")
    
    def process_sensor_data(self, sensor_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process sensor data through gateway
        Filters outliers and forwards clean data to controller
        """
        device_id = sensor_data.get('device_id')
        location = sensor_data.get('location')
        readings = sensor_data.get('readings', [])
        
        logger.info(f"Gateway processing data from {device_id} ({len(readings)} readings)")
        
        # Filter outliers from readings
        filtered_readings = []
        outliers_detected = 0
        outlier_details = []
        
        for reading in readings:
            sensor_type = reading.get('sensor_type')
            value = reading.get('value')
            
            # Only filter numeric values
            if isinstance(value, (int, float)):
                is_outlier, reason = self._is_outlier(sensor_type, value, device_id)
                
                if is_outlier:
                    outliers_detected += 1
                    outlier_details.append({
                        'sensor_type': sensor_type,
                        'value': value,
                        'reason': reason
                    })
                    logger.warning(f"Outlier detected: {sensor_type}={value} ({reason})")
                else:
                    filtered_readings.append(reading)
                    self._update_window(device_id, sensor_type, value)
            else:
                # Non-numeric values pass through
                filtered_readings.append(reading)
        
        # Log gateway processing
        gateway_log = {
            'device_id': device_id,
            'location': location,
            'timestamp': datetime.utcnow(),
            'original_count': len(readings),
            'filtered_count': len(filtered_readings),
            'outliers_detected': outliers_detected,
            'outlier_details': outlier_details
        }
        
        self.statistics_log.append(gateway_log)
        if len(self.statistics_log) > 1000:
            self.statistics_log = self.statistics_log[-1000:]
        
        # Prepare data to forward
        forwarded_data = {
            'device_id': device_id,
            'location': location,
            'readings': filtered_readings,
            'gateway_processed': True,
            'gateway_stats': {
                'outliers_removed': outliers_detected,
                'outlier_details': outlier_details
            }
        }
        
        # Forward to controller with security headers
        try:
            # Prepare secure headers
            headers = {
                'Content-Type': 'application/json',
                'X-Gateway-Key': Config.GATEWAY_API_KEY,
                'User-Agent': 'IoT-Gateway/1.0'
            }
            
            # Encrypt sensitive data if configured
            if hasattr(Config, 'ENABLE_DATA_ENCRYPTION') and Config.ENABLE_DATA_ENCRYPTION:
                forwarded_data = self.encryption.encrypt_sensor_data(forwarded_data)
            
            response = requests.post(
                f"{self.controller_url}/api/sensor-data/gateway",
                json=forwarded_data,
                headers=headers,
                timeout=10,
                verify=True  # Verify SSL certificates
            )
            
            if response.status_code == 200:
                logger.info(f"Data forwarded successfully ({len(filtered_readings)} readings)")
                return {
                    'status': 'success',
                    'forwarded': True,
                    'outliers_filtered': outliers_detected
                }
            else:
                logger.error(f"Controller returned error: {response.status_code}")
                return {
                    'status': 'error',
                    'message': f"Controller error: {response.status_code}"
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error forwarding to controller: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def _is_outlier(
        self, 
        sensor_type: str, 
        value: float, 
        device_id: str
    ) -> tuple[bool, str]:
        """
        Determine if a value is an outlier
        Uses multiple methods: range check, IQR method
        """
        
        # Method 1: Range check (hard limits)
        if sensor_type in self.config['ranges']:
            range_limits = self.config['ranges'][sensor_type]
            if value < range_limits['min']:
                return True, f"Below minimum: {value} < {range_limits['min']}"
            if value > range_limits['max']:
                return True, f"Above maximum: {value} > {range_limits['max']}"
        
        # Method 2: IQR (Interquartile Range) method
        if self.config['method'] == 'iqr':
            window_key = f"{device_id}_{sensor_type}"
            
            if window_key in self.sensor_windows:
                window = list(self.sensor_windows[window_key])
                
                if len(window) >= 5:  # Need enough data points
                    try:
                        q1 = statistics.quantiles(window, n=4)[0]  # 25th percentile
                        q3 = statistics.quantiles(window, n=4)[2]  # 75th percentile
                        iqr = q3 - q1
                        
                        lower_bound = q1 - (self.config['multiplier'] * iqr)
                        upper_bound = q3 + (self.config['multiplier'] * iqr)
                        
                        if value < lower_bound:
                            return True, f"IQR outlier: {value} < {lower_bound:.2f}"
                        if value > upper_bound:
                            return True, f"IQR outlier: {value} > {upper_bound:.2f}"
                    except Exception as e:
                        logger.debug(f"IQR calculation error: {e}")
        
        return False, ""
    
    def _update_window(self, device_id: str, sensor_type: str, value: float):
        """Update sliding window of sensor values"""
        window_key = f"{device_id}_{sensor_type}"
        
        if window_key not in self.sensor_windows:
            self.sensor_windows[window_key] = deque(maxlen=self.config['window_size'])
        
        self.sensor_windows[window_key].append(value)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get gateway filtering statistics"""
        if not self.statistics_log:
            return {
                'total_processed': 0,
                'total_outliers': 0,
                'filter_rate': 0
            }
        
        total_processed = sum(log['original_count'] for log in self.statistics_log)
        total_outliers = sum(log['outliers_detected'] for log in self.statistics_log)
        
        return {
            'total_processed': total_processed,
            'total_outliers': total_outliers,
            'filter_rate': (total_outliers / total_processed) if total_processed > 0 else 0,
            'recent_logs': self.statistics_log[-10:]
        }
