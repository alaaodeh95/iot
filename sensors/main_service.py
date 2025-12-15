"""
Main Sensor Service
Runs all sensor devices and sends data to controller
Supports both JSON and XML data formats
"""
import logging
import time
import threading
import requests
from typing import Dict, List, Optional
import xml.etree.ElementTree as ET
from xml.dom import minidom
import sys
import os
import random

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.config import Config
from sensors.sensor_simulator import SensorDevice
from sensors.gateway import SensorGateway
from backend.security import SecurityManager, RequestEncryption

logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format=Config.LOG_FORMAT
)
logger = logging.getLogger(__name__)

class SensorService:
    """Main sensor service coordinating all devices"""
    
    def __init__(self):
        """Initialize secure sensor service"""
        # Use HTTPS if SSL is enabled
        protocol = "https" if Config.SSL_ENABLED else "http"
        self.controller_url = f"{protocol}://{Config.CONTROLLER_HOST}:{Config.CONTROLLER_PORT}"
        
        self.devices: Dict[str, SensorDevice] = {}
        self.gateway = SensorGateway(self.controller_url)
        self.running = False
        self.threads: List[threading.Thread] = []
        
        # Initialize security components
        self.security_manager = SecurityManager(Config)
        self.device_tokens: Dict[str, str] = {}
        self.encryption = RequestEncryption(Config.API_KEY)
        self.demo_mode = Config.DEMO_MODE
        
        # Initialize devices from config
        self._initialize_devices()
        
        if self.demo_mode:
            logger.info("DEMO_MODE enabled: forcing fixed cycles with verbose per-cycle logs")
        
        # Authenticate all devices on startup
        self._authenticate_devices()
        
        logger.info(f"Secure sensor service initialized with {len(self.devices)} devices")
    
    def _initialize_devices(self):
        """Initialize all sensor devices from configuration"""
        for device_id, config in Config.SENSORS.items():
            device = SensorDevice(
                device_id=device_id,
                location=config['location'],
                sensor_types=config['sensors']
            )
            self.devices[device_id] = device
            logger.info(f"Initialized device: {device_id} at {config['location']}")
    
    def start(self):
        """Start all sensor devices"""
        self.running = True
        logger.info("Starting sensor service...")
        
        # Start each device in its own thread
        for device_id, device in self.devices.items():
            config = Config.SENSORS[device_id]
            
            thread = threading.Thread(
                target=self._run_device,
                args=(device, config),
                daemon=True,
                name=f"Device-{device_id}"
            )
            thread.start()
            self.threads.append(thread)
            logger.info(f"Started device thread: {device_id}")
        
        logger.info(f"All {len(self.devices)} devices started")
        
        # Keep main thread alive and refresh tokens periodically
        try:
            token_refresh_counter = 0
            while self.running:
                time.sleep(1)
                token_refresh_counter += 1
                
                # Refresh tokens every hour (3600 seconds)
                if token_refresh_counter >= 3600:
                    self._refresh_device_tokens()
                    token_refresh_counter = 0
                    
        except KeyboardInterrupt:
            logger.info("Received shutdown signal")
            self.stop()
    
    def stop(self):
        """Stop all sensor devices"""
        logger.info("Stopping sensor service...")
        self.running = False
        
        # Wait for threads to finish
        for thread in self.threads:
            thread.join(timeout=2)
        
        logger.info("Sensor service stopped")
    
    def _run_device(self, device: SensorDevice, config: Dict):
        """Run a single sensor device"""
        device_id = device.device_id
        interval = config['update_interval']
        data_format = config['type']
        use_gateway = config.get('gateway_enabled', False)
        
        logger.info(
            f"Device {device_id} running (interval={interval}s, "
            f"format={data_format}, gateway={use_gateway})"
        )
        
        cycle_count = 0
        max_cycles = Config.FIXED_CYCLES if (self.demo_mode or not Config.CONTINUOUS_MODE) else float('inf')
        
        while self.running and cycle_count < max_cycles:
            try:
                # Read sensor data
                sensor_data = device.read_all()
                
                # Send data based on format
                if data_format == 'json':
                    send_result = self._send_json_data(sensor_data, use_gateway)
                elif data_format == 'xml':
                    send_result = self._send_xml_data(sensor_data)
                else:
                    send_result = {'status': 'skipped', 'reason': 'unknown format'}
                
                cycle_count += 1
                
                if self.demo_mode:
                    logger.info(
                        f"[DEMO] Cycle {cycle_count}/{max_cycles} device={device_id} "
                        f"format={data_format} readings={len(sensor_data['readings'])} "
                        f"gateway={use_gateway} result={send_result}"
                    )
                
                # Add occasional outliers for gateway testing (5% chance)
                if use_gateway and random.random() < 0.05:
                    self._inject_outlier(device)
                
                time.sleep(interval)
                
            except Exception as e:
                logger.error(f"Error in device {device_id}: {e}", exc_info=True)
                time.sleep(interval)
        
        logger.info(f"Device {device_id} completed {cycle_count} cycles (demo_mode={self.demo_mode})")
    
    def _authenticate_devices(self):
        """Authenticate all devices and obtain JWT tokens"""
        logger.info("Authenticating devices...")
        
        for device_id in self.devices.keys():
            try:
                token = self._get_device_token(device_id)
                if token:
                    self.device_tokens[device_id] = token
                    logger.info(f"Device {device_id} authenticated successfully")
                else:
                    logger.error(f"Failed to authenticate device {device_id}")
            except Exception as e:
                logger.error(f"Authentication error for device {device_id}: {e}")
    
    def _get_device_token(self, device_id: str) -> Optional[str]:
        """Get JWT token for a specific device"""
        try:
            headers = {
                'Content-Type': 'application/json',
                'X-API-Key': Config.API_KEY
            }
            
            response = requests.post(
                f"{self.controller_url}/api/device/token",
                json={'device_id': device_id},
                headers=headers,
                timeout=10,
                verify=True if Config.SSL_ENABLED else False
            )
            
            if response.status_code == 200:
                return response.json().get('token')
            else:
                logger.error(f"Token request failed: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting token for {device_id}: {e}")
            return None
    
    def _refresh_device_tokens(self):
        """Refresh JWT tokens for all devices"""
        logger.info("Refreshing device tokens...")
        self._authenticate_devices()
    
    def _create_secure_headers(self, device_id: str, data: Dict) -> Dict[str, str]:
        """Create secure headers for API requests"""
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': f'IoT-Device/{device_id}'
        }
        
        # Add JWT token
        if device_id in self.device_tokens:
            headers['Authorization'] = f'Bearer {self.device_tokens[device_id]}'
        
        # Add request signature if enabled
        if Config.ENABLE_REQUEST_SIGNING:
            try:
                signature = self.security_manager.sign_request(data, device_id)
                headers['X-Signature'] = signature
            except Exception as e:
                logger.error(f"Error signing request for {device_id}: {e}")
        
        return headers
    
    def _send_json_data(self, sensor_data: Dict, use_gateway: bool):
        """Send sensor data in JSON format with security"""
        device_id = sensor_data['device_id']
        
        try:
            if use_gateway:
                # Send through gateway for outlier filtering
                result = self.gateway.process_sensor_data(sensor_data)
                if result['status'] == 'success':
                    logger.debug(
                        f"Secure JSON data from {device_id} sent via gateway "
                        f"(outliers filtered: {result.get('outliers_filtered', 0)})"
                    )
                return {
                    'status': result.get('status', 'unknown'),
                    'gateway': True,
                    'outliers_filtered': result.get('outliers_filtered', 0)
                }
            else:
                # Encrypt sensitive data if needed
                secure_data = sensor_data.copy()
                if hasattr(Config, 'ENABLE_DATA_ENCRYPTION') and Config.ENABLE_DATA_ENCRYPTION:
                    secure_data = self.encryption.encrypt_sensor_data(secure_data)
                
                # Create secure headers
                headers = self._create_secure_headers(device_id, secure_data)
                
                # Send directly to controller with authentication
                response = requests.post(
                    f"{self.controller_url}/api/sensor-data",
                    json=secure_data,
                    headers=headers,
                    timeout=10,
                    verify=True if Config.SSL_ENABLED else False
                )
                
                if response.status_code == 200:
                    logger.debug(f"JSON data from {device_id} sent successfully")
                    return {'status': 'success', 'gateway': False}
                else:
                    logger.warning(
                        f"Controller returned status {response.status_code} "
                        f"for {device_id}"
                    )
                    return {'status': 'error', 'gateway': False, 'code': response.status_code}
                    
        except requests.exceptions.RequestException as e:
            logger.error(f"Error sending JSON data from {device_id}: {e}")
            return {'status': 'error', 'gateway': use_gateway, 'message': str(e)}
    
    def _send_xml_data(self, sensor_data: Dict):
        """Send sensor data in XML/SOAP format"""
        device_id = sensor_data['device_id']
        
        try:
            # Create XML structure
            root = ET.Element('sensor_data')
            
            # Add device info
            ET.SubElement(root, 'device_id').text = device_id
            ET.SubElement(root, 'location').text = sensor_data['location']
            ET.SubElement(root, 'timestamp').text = sensor_data['timestamp']
            
            # Add sensors
            sensors = ET.SubElement(root, 'sensors')
            for reading in sensor_data['readings']:
                sensor = ET.SubElement(sensors, 'sensor')
                ET.SubElement(sensor, 'type').text = reading['sensor_type']
                ET.SubElement(sensor, 'value').text = str(reading['value'])
                ET.SubElement(sensor, 'unit').text = reading['unit']
                
                # Add object name for distance sensors
                if 'object_name' in reading:
                    ET.SubElement(sensor, 'object_name').text = reading['object_name']
            
            # Convert to string with pretty formatting
            xml_str = self._prettify_xml(root)
            
            # Send to controller
            response = requests.post(
                f"{self.controller_url}/api/sensor-data/xml",
                data=xml_str.encode('utf-8'),
                headers={'Content-Type': 'application/xml'},
                timeout=5
            )
            
            if response.status_code == 200:
                logger.debug(f"XML data from {device_id} sent successfully")
            else:
                logger.warning(
                    f"Controller returned status {response.status_code} "
                    f"for {device_id}"
                )
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error sending XML data from {device_id}: {e}")
        except Exception as e:
            logger.error(f"Error creating XML for {device_id}: {e}", exc_info=True)
    
    def _prettify_xml(self, elem: ET.Element) -> str:
        """Return a pretty-printed XML string"""
        rough_string = ET.tostring(elem, encoding='utf-8')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ", encoding="utf-8").decode('utf-8')
    
    def _inject_outlier(self, device: SensorDevice):
        """Inject an outlier for gateway testing"""
        import random
        
        # Pick a random numeric sensor
        numeric_sensors = [
            s for s in device.sensors 
            if s.sensor_type in ['temperature', 'humidity', 'pressure']
        ]
        
        if numeric_sensors:
            sensor = random.choice(numeric_sensors)
            
            # Generate an outlier value
            if sensor.sensor_type == 'temperature':
                outlier = random.choice([random.uniform(-30, 0), random.uniform(50, 80)])
            elif sensor.sensor_type == 'humidity':
                outlier = random.choice([random.uniform(-10, 5), random.uniform(95, 110)])
            elif sensor.sensor_type == 'pressure':
                outlier = random.choice([random.uniform(800, 900), random.uniform(1100, 1200)])
            else:
                return
            
            # Temporarily override sensor value
            original_override = sensor.manual_override
            sensor.set_manual_value(outlier)
            
            logger.debug(f"Injected outlier: {sensor.sensor_type}={outlier}")
            
            # Read and send
            sensor_data = device.read_all()
            self._send_json_data(sensor_data, use_gateway=True)
            
            # Restore original override
            if original_override is not None:
                sensor.set_manual_value(original_override)
            else:
                sensor.clear_manual_value()
    
    def get_device(self, device_id: str) -> SensorDevice:
        """Get a specific device"""
        return self.devices.get(device_id)
    
    def set_sensor_value(self, device_id: str, sensor_type: str, value):
        """Set manual value for a sensor (for UI control)"""
        device = self.devices.get(device_id)
        if device:
            return device.set_sensor_value(sensor_type, value)
        return False
    
    def get_gateway_stats(self):
        """Get gateway statistics"""
        return self.gateway.get_statistics()

def main():
    """Main entry point"""
    logger.info("="*60)
    logger.info("IoT Smart Home - Sensor Service")
    logger.info("="*60)
    logger.info(f"Controller URL: http://{Config.CONTROLLER_HOST}:{Config.CONTROLLER_PORT}")
    logger.info(f"Simulation Mode: {'Continuous' if Config.CONTINUOUS_MODE else f'{Config.FIXED_CYCLES} cycles'}")
    logger.info(f"Gateway Enabled: {Config.OUTLIER_DETECTION['enabled']}")
    logger.info("="*60)
    
    service = SensorService()
    
    try:
        service.start()
    except KeyboardInterrupt:
        logger.info("\nShutdown requested")
        service.stop()
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        service.stop()

if __name__ == '__main__':
    import random  # Import here for outlier injection
    main()
