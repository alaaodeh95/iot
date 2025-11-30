"""
Sensor simulation for IoT Smart Home
Generates realistic sensor data with various types
"""
import random
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.config import Config

logger = logging.getLogger(__name__)

class BaseSensor:
    """Base class for all sensors"""
    
    def __init__(self, sensor_type: str, location: str, unit: str):
        self.sensor_type = sensor_type
        self.location = location
        self.unit = unit
        self.current_value = None
        self.manual_override = None  # For UI control
    
    def read(self) -> Dict[str, Any]:
        """Read sensor value"""
        if self.manual_override is not None:
            value = self.manual_override
        else:
            value = self._generate_value()
        
        self.current_value = value
        
        return {
            'sensor_type': self.sensor_type,
            'value': value,
            'unit': self.unit
        }
    
    def _generate_value(self):
        """Generate sensor value - to be overridden by subclasses"""
        raise NotImplementedError
    
    def set_manual_value(self, value):
        """Set manual override value"""
        self.manual_override = value
    
    def clear_manual_value(self):
        """Clear manual override"""
        self.manual_override = None

class TemperatureSensor(BaseSensor):
    """Temperature sensor"""
    
    def __init__(self, location: str):
        super().__init__('temperature', location, '°C')
        self.base_temp = random.uniform(20, 25)
        self.trend = 0
    
    def _generate_value(self):
        # Realistic temperature with slow drift
        ranges = Config.get_sensor_ranges()['temperature']
        
        # Add small random change
        change = random.uniform(-0.5, 0.5)
        self.base_temp += change
        
        # Add trend (slow drift)
        self.trend += random.uniform(-0.1, 0.1)
        self.trend = max(-2, min(2, self.trend))
        
        value = self.base_temp + self.trend
        
        # Keep within realistic bounds
        value = max(ranges['min'], min(ranges['max'], value))
        
        return round(value, 1)

class HumiditySensor(BaseSensor):
    """Humidity sensor"""
    
    def __init__(self, location: str):
        super().__init__('humidity', location, '%')
        self.base_humidity = random.uniform(40, 60)
    
    def _generate_value(self):
        ranges = Config.get_sensor_ranges()['humidity']
        
        # Small variations
        change = random.uniform(-2, 2)
        self.base_humidity += change
        
        # Keep within bounds
        self.base_humidity = max(ranges['min'], min(ranges['max'], self.base_humidity))
        
        return round(self.base_humidity, 1)

class PressureSensor(BaseSensor):
    """Atmospheric pressure sensor"""
    
    def __init__(self, location: str):
        super().__init__('pressure', location, 'hPa')
        self.base_pressure = random.uniform(1000, 1020)
    
    def _generate_value(self):
        ranges = Config.get_sensor_ranges()['pressure']
        
        # Very slow changes
        change = random.uniform(-0.5, 0.5)
        self.base_pressure += change
        
        self.base_pressure = max(ranges['min'], min(ranges['max'], self.base_pressure))
        
        return round(self.base_pressure, 1)

class LightSensor(BaseSensor):
    """Light level sensor"""
    
    def __init__(self, location: str):
        super().__init__('light', location, 'lux')
        self.base_light = random.uniform(200, 600)
    
    def _generate_value(self):
        ranges = Config.get_sensor_ranges()['light']
        
        # Moderate variations
        change = random.uniform(-50, 50)
        self.base_light += change
        
        self.base_light = max(ranges['min'], min(ranges['max'], self.base_light))
        
        return round(self.base_light, 1)

class MotionSensor(BaseSensor):
    """PIR motion sensor"""
    
    def __init__(self, location: str):
        super().__init__('motion', location, 'boolean')
        self.motion_probability = 0.3  # 30% chance of motion
    
    def _generate_value(self):
        return 1 if random.random() < self.motion_probability else 0

class CO2Sensor(BaseSensor):
    """CO2 sensor"""
    
    def __init__(self, location: str):
        super().__init__('co2', location, 'ppm')
        self.base_co2 = random.uniform(400, 800)
    
    def _generate_value(self):
        ranges = Config.get_sensor_ranges()['co2']
        
        change = random.uniform(-20, 20)
        self.base_co2 += change
        
        self.base_co2 = max(ranges['min'], min(ranges['max'], self.base_co2))
        
        return round(self.base_co2, 1)

class GasSensor(BaseSensor):
    """Gas sensor (CO, natural gas)"""
    
    def __init__(self, location: str):
        super().__init__('gas', location, 'ppm')
        self.base_gas = random.uniform(0, 100)
        self.spike_chance = 0.05  # 5% chance of spike
    
    def _generate_value(self):
        ranges = Config.get_sensor_ranges()['gas']
        
        # Occasional spikes
        if random.random() < self.spike_chance:
            return round(random.uniform(500, 1000), 1)
        
        change = random.uniform(-5, 5)
        self.base_gas += change
        
        self.base_gas = max(ranges['min'], min(ranges['max'], self.base_gas))
        
        return round(self.base_gas, 1)

class SmokeSensor(BaseSensor):
    """Smoke detector"""
    
    def __init__(self, location: str):
        super().__init__('smoke', location, 'boolean')
        self.detection_probability = 0.01  # 1% chance
    
    def _generate_value(self):
        return 1 if random.random() < self.detection_probability else 0

class DistanceSensor(BaseSensor):
    """Ultrasonic distance sensor"""
    
    def __init__(self, location: str):
        super().__init__('distance', location, 'cm')
        self.base_distance = random.uniform(100, 200)
    
    def _generate_value(self):
        ranges = Config.get_sensor_ranges()['distance']
        
        # Simulate object detection
        if random.random() < 0.2:  # 20% chance of obstacle
            return round(random.uniform(10, 80), 1)
        
        change = random.uniform(-10, 10)
        self.base_distance += change
        
        self.base_distance = max(ranges['min'], min(ranges['max'], self.base_distance))
        
        return round(self.base_distance, 1)

class DoorSensor(BaseSensor):
    """Door/window contact sensor"""
    
    def __init__(self, location: str):
        super().__init__('door_sensor', location, 'boolean')
        self.state = 1  # 1 = closed, 0 = open
        self.change_probability = 0.1
    
    def _generate_value(self):
        if random.random() < self.change_probability:
            self.state = 1 - self.state
        return self.state

class WaterLeakSensor(BaseSensor):
    """Water leak detector"""
    
    def __init__(self, location: str):
        super().__init__('water_leak', location, 'boolean')
        self.detection_probability = 0.005  # 0.5% chance
    
    def _generate_value(self):
        return 1 if random.random() < self.detection_probability else 0

class RFIDSensor(BaseSensor):
    """RFID/NFC reader"""
    
    def __init__(self, location: str):
        super().__init__('rfid', location, 'string')
    
    def _generate_value(self):
        ranges = Config.get_sensor_ranges()['rfid']
        return random.choice(ranges['values'])

class SignalStrengthSensor(BaseSensor):
    """Signal strength sensor"""
    
    def __init__(self, location: str):
        super().__init__('signal_strength', location, 'dBm')
        self.base_strength = random.uniform(-70, -30)
    
    def _generate_value(self):
        ranges = Config.get_sensor_ranges()['signal_strength']
        
        change = random.uniform(-5, 5)
        self.base_strength += change
        
        self.base_strength = max(ranges['min'], min(ranges['max'], self.base_strength))
        
        return round(self.base_strength, 1)

class ObjectDetectionSensor(BaseSensor):
    """Object detection (camera-based)"""
    
    def __init__(self, location: str):
        super().__init__('object_detection', location, 'string')
    
    def _generate_value(self):
        objects = Config.get_object_types()
        return random.choice(objects)

class SensorDevice:
    """Represents a device with multiple sensors"""
    
    def __init__(
        self, 
        device_id: str, 
        location: str, 
        sensor_types: List[str]
    ):
        self.device_id = device_id
        self.location = location
        self.sensors: List[BaseSensor] = []
        
        # Create sensors based on types
        sensor_classes = {
            'temperature': TemperatureSensor,
            'humidity': HumiditySensor,
            'pressure': PressureSensor,
            'light': LightSensor,
            'motion': MotionSensor,
            'co2': CO2Sensor,
            'gas': GasSensor,
            'smoke': SmokeSensor,
            'distance': DistanceSensor,
            'door_sensor': DoorSensor,
            'water_leak': WaterLeakSensor,
            'rfid': RFIDSensor,
            'signal_strength': SignalStrengthSensor,
            'object_detection': ObjectDetectionSensor
        }
        
        for sensor_type in sensor_types:
            if sensor_type in sensor_classes:
                sensor = sensor_classes[sensor_type](location)
                self.sensors.append(sensor)
            else:
                logger.warning(f"Unknown sensor type: {sensor_type}")
    
    def read_all(self) -> Dict[str, Any]:
        """Read all sensors in this device"""
        readings = [sensor.read() for sensor in self.sensors]
        
        # Add object name for distance sensors (dust cleaner)
        for reading in readings:
            if reading['sensor_type'] == 'distance':
                # Find object detection sensor
                obj_reading = next(
                    (r for r in readings if r['sensor_type'] == 'object_detection'),
                    None
                )
                if obj_reading:
                    reading['object_name'] = obj_reading['value']
        
        return {
            'device_id': self.device_id,
            'location': self.location,
            'readings': readings,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def set_sensor_value(self, sensor_type: str, value: Any):
        """Set manual value for a specific sensor"""
        for sensor in self.sensors:
            if sensor.sensor_type == sensor_type:
                sensor.set_manual_value(value)
                return True
        return False
    
    def clear_sensor_override(self, sensor_type: str):
        """Clear manual override for a sensor"""
        for sensor in self.sensors:
            if sensor.sensor_type == sensor_type:
                sensor.clear_manual_value()
                return True
        return False
