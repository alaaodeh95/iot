"""
Configuration for IoT Smart Home System
"""
import os
from typing import Dict, Any

class Config:
    """Main configuration class"""
    
    # Server Configuration
    CONTROLLER_HOST = os.getenv('CONTROLLER_HOST', 'localhost')
    CONTROLLER_PORT = int(os.getenv('CONTROLLER_PORT', 5000))
    
    # MongoDB Configuration
    MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
    MONGODB_DATABASE = os.getenv('MONGODB_DATABASE', 'IOT')
    
    # Sensor Service Configuration
    SENSOR_SERVICE_HOST = os.getenv('SENSOR_SERVICE_HOST', 'localhost')
    SENSOR_SERVICE_PORT = int(os.getenv('SENSOR_SERVICE_PORT', 5001))
    
    # Gateway Configuration
    GATEWAY_PORT = int(os.getenv('GATEWAY_PORT', 5002))
    
    # Simulation Configuration
    SIMULATION_INTERVAL = float(os.getenv('SIMULATION_INTERVAL', 3.0))  # seconds
    CONTINUOUS_MODE = os.getenv('CONTINUOUS_MODE', 'true').lower() == 'true'
    FIXED_CYCLES = int(os.getenv('FIXED_CYCLES', 20))
    
    # Decision Rules Configuration
    DECISION_RULES = {
        'temperature': {
            'high_threshold': 30.0,  # °C
            'low_threshold': 18.0,
            'critical_high': 40.0,
            'critical_low': 10.0
        },
        'humidity': {
            'high_threshold': 70.0,  # %
            'low_threshold': 30.0
        },
        'light': {
            'dark_threshold': 200.0,  # lux
            'bright_threshold': 800.0
        },
        'co2': {
            'warning_threshold': 1000.0,  # ppm
            'critical_threshold': 2000.0
        },
        'motion': {
            'timeout': 300  # seconds before auto-off
        },
        'distance': {
            'obstacle_threshold': 50.0,  # cm
            'critical_threshold': 20.0
        },
        'gas': {
            'warning_threshold': 800.0,  # ppm
            'critical_threshold': 1500.0
        },
        'smoke': {
            'detected_action': 'alarm'
        },
        'water_leak': {
            'detected_action': 'shutdown'
        }
    }
    
    # Sensor Configuration
    SENSORS = {
        'roof_station': {
            'type': 'json',
            'location': 'roof',
            'sensors': ['temperature', 'humidity', 'pressure'],
            'update_interval': 2.0,
            'gateway_enabled': True
        },
        'living_room': {
            'type': 'json',
            'location': 'living_room',
            'sensors': ['motion', 'light', 'temperature'],
            'update_interval': 1.0,
            'gateway_enabled': False
        },
        'kitchen': {
            'type': 'json',
            'location': 'kitchen',
            'sensors': ['gas', 'smoke', 'temperature'],
            'update_interval': 1.0,
            'gateway_enabled': False
        },
        'dust_cleaner': {
            'type': 'xml',
            'location': 'mobile',
            'sensors': ['distance', 'object_detection', 'signal_strength'],
            'update_interval': 0.5,
            'gateway_enabled': False
        },
        'bedroom': {
            'type': 'json',
            'location': 'bedroom',
            'sensors': ['temperature', 'light', 'door_sensor'],
            'update_interval': 2.0,
            'gateway_enabled': False
        },
        'basement': {
            'type': 'json',
            'location': 'basement',
            'sensors': ['water_leak', 'humidity', 'temperature'],
            'update_interval': 2.0,
            'gateway_enabled': False
        },
        'entrance': {
            'type': 'json',
            'location': 'entrance',
            'sensors': ['motion', 'door_sensor', 'rfid'],
            'update_interval': 0.5,
            'gateway_enabled': False
        }
    }
    
    # Actuator Configuration
    ACTUATORS = {
        'hvac_system': {
            'type': 'climate_control',
            'location': 'whole_house',
            'states': ['off', 'heating', 'cooling', 'fan_only']
        },
        'living_room_lights': {
            'type': 'light',
            'location': 'living_room',
            'dimmable': True
        },
        'bedroom_lights': {
            'type': 'light',
            'location': 'bedroom',
            'dimmable': True
        },
        'kitchen_exhaust': {
            'type': 'fan',
            'location': 'kitchen',
            'states': ['off', 'low', 'medium', 'high']
        },
        'entrance_lights': {
            'type': 'light',
            'location': 'entrance',
            'dimmable': False
        },
        'fire_alarm': {
            'type': 'alarm',
            'location': 'whole_house',
            'priority': 'critical'
        },
        'gas_alarm': {
            'type': 'alarm',
            'location': 'kitchen',
            'priority': 'critical'
        },
        'water_shutoff': {
            'type': 'valve',
            'location': 'basement',
            'priority': 'high'
        },
        'dust_cleaner_motor': {
            'type': 'motor',
            'location': 'mobile',
            'states': ['off', 'cleaning', 'paused', 'returning']
        },
        'dehumidifier': {
            'type': 'appliance',
            'location': 'basement',
            'states': ['off', 'on']
        },
        'door_lock': {
            'type': 'lock',
            'location': 'entrance',
            'states': ['locked', 'unlocked']
        }
    }
    
    # Gateway Outlier Detection Configuration
    OUTLIER_DETECTION = {
        'enabled': True,
        'method': 'iqr',  # interquartile range
        'window_size': 10,  # number of readings to consider
        'multiplier': 1.5,  # IQR multiplier for outlier detection
        'ranges': {
            'temperature': {'min': -20, 'max': 60},
            'humidity': {'min': 0, 'max': 100},
            'pressure': {'min': 900, 'max': 1100},
            'light': {'min': 0, 'max': 100000},
            'co2': {'min': 300, 'max': 5000},
            'distance': {'min': 0, 'max': 400}
        }
    }
    
    # CORS Configuration
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:3000').split(',')
    
    # Logging Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    @classmethod
    def get_sensor_ranges(cls) -> Dict[str, Dict[str, Any]]:
        """Get realistic sensor value ranges"""
        return {
            'temperature': {'min': 15.0, 'max': 40.0, 'unit': '°C'},
            'humidity': {'min': 20.0, 'max': 80.0, 'unit': '%'},
            'pressure': {'min': 980.0, 'max': 1040.0, 'unit': 'hPa'},
            'light': {'min': 0.0, 'max': 1000.0, 'unit': 'lux'},
            'motion': {'min': 0, 'max': 1, 'unit': 'boolean'},
            'co2': {'min': 400.0, 'max': 2500.0, 'unit': 'ppm'},
            'gas': {'min': 0.0, 'max': 2000.0, 'unit': 'ppm'},
            'smoke': {'min': 0, 'max': 1, 'unit': 'boolean'},
            'distance': {'min': 5.0, 'max': 400.0, 'unit': 'cm'},
            'door_sensor': {'min': 0, 'max': 1, 'unit': 'boolean'},
            'water_leak': {'min': 0, 'max': 1, 'unit': 'boolean'},
            'signal_strength': {'min': -90.0, 'max': -20.0, 'unit': 'dBm'},
            'rfid': {'values': ['None', 'Tag001', 'Tag002', 'Tag003', 'Tag004'], 'unit': 'string'}
        }
    
    @classmethod
    def get_object_types(cls) -> list:
        """Get possible object types for camera detection"""
        return [
            'chair', 'table', 'sofa', 'wall', 'door', 'person', 
            'pet', 'toy', 'shoe', 'book', 'plant', 'box', 'none'
        ]
