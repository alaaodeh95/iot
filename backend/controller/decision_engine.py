"""
Decision engine for IoT Smart Home system
Implements intelligent automation rules
"""
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging
from collections import defaultdict

from backend.models import ActuatorCommand
from backend.config import Config

logger = logging.getLogger(__name__)

class DecisionEngine:
    """Intelligent decision making engine for smart home automation"""
    
    def __init__(self):
        """Initialize decision engine"""
        self.rules = Config.DECISION_RULES
        self.sensor_history = defaultdict(list)
        self.last_motion_time = {}
        self.actuator_states = {}
        self.alert_cooldown = {}  # Prevent alert spam
        
    def process_sensor_data(self, sensor_data: Dict[str, Any]) -> List[ActuatorCommand]:
        """
        Process sensor data and make decisions
        Returns list of actuator commands to execute
        """
        commands = []
        
        # Extract sensor information
        device_id = sensor_data.get('device_id')
        location = sensor_data.get('location')
        readings = sensor_data.get('readings', [])
        
        # Store in history for trend analysis
        self._update_history(device_id, readings)
        
        # Process each reading
        for reading in readings:
            sensor_type = reading.get('sensor_type')
            value = reading.get('value')
            
            # Route to appropriate decision logic
            if sensor_type == 'temperature':
                commands.extend(self._process_temperature(value, location))
            elif sensor_type == 'humidity':
                commands.extend(self._process_humidity(value, location))
            elif sensor_type == 'light':
                commands.extend(self._process_light(value, location))
            elif sensor_type == 'motion':
                commands.extend(self._process_motion(value, location))
            elif sensor_type == 'co2':
                commands.extend(self._process_co2(value, location))
            elif sensor_type == 'gas':
                commands.extend(self._process_gas(value, location))
            elif sensor_type == 'smoke':
                commands.extend(self._process_smoke(value, location))
            elif sensor_type == 'distance':
                commands.extend(self._process_distance(value, location, reading))
            elif sensor_type == 'water_leak':
                commands.extend(self._process_water_leak(value, location))
            elif sensor_type == 'door_sensor':
                commands.extend(self._process_door_sensor(value, location))
        
        # Cross-sensor intelligence (combine multiple sensor inputs)
        commands.extend(self._cross_sensor_decisions(device_id, location, readings))
        
        return commands
    
    def _process_temperature(self, temp: float, location: str) -> List[ActuatorCommand]:
        """Process temperature readings"""
        commands = []
        rules = self.rules['temperature']
        
        # Critical high temperature
        if temp >= rules['critical_high']:
            commands.append(ActuatorCommand(
                actuator_id='hvac_system',
                actuator_type='climate_control',
                state='cooling',
                reason=f'Critical high temperature: {temp}°C at {location}'
            ))
            commands.append(ActuatorCommand(
                actuator_id='fire_alarm',
                actuator_type='alarm',
                state='on',
                reason=f'Temperature critically high: {temp}°C'
            ))
        
        # High temperature - turn on cooling
        elif temp > rules['high_threshold']:
            commands.append(ActuatorCommand(
                actuator_id='hvac_system',
                actuator_type='climate_control',
                state='cooling',
                reason=f'High temperature: {temp}°C at {location}'
            ))
        
        # Low temperature - turn on heating
        elif temp < rules['low_threshold']:
            commands.append(ActuatorCommand(
                actuator_id='hvac_system',
                actuator_type='climate_control',
                state='heating',
                reason=f'Low temperature: {temp}°C at {location}'
            ))
        
        # Comfortable temperature - fan only or off
        elif rules['low_threshold'] <= temp <= rules['high_threshold']:
            current_state = self.actuator_states.get('hvac_system', 'off')
            if current_state in ['heating', 'cooling']:
                commands.append(ActuatorCommand(
                    actuator_id='hvac_system',
                    actuator_type='climate_control',
                    state='off',
                    reason=f'Temperature normalized: {temp}°C at {location}'
                ))
        
        return commands
    
    def _process_humidity(self, humidity: float, location: str) -> List[ActuatorCommand]:
        """Process humidity readings"""
        commands = []
        rules = self.rules['humidity']
        
        # High humidity
        if humidity > rules['high_threshold']:
            if location == 'basement':
                commands.append(ActuatorCommand(
                    actuator_id='dehumidifier',
                    actuator_type='appliance',
                    state='on',
                    reason=f'High humidity: {humidity}% at {location}'
                ))
        
        # Low humidity
        elif humidity < rules['low_threshold']:
            # Could add humidifier control here
            pass
        
        # Normal humidity
        else:
            if location == 'basement':
                current_state = self.actuator_states.get('dehumidifier', 'off')
                if current_state == 'on':
                    commands.append(ActuatorCommand(
                        actuator_id='dehumidifier',
                        actuator_type='appliance',
                        state='off',
                        reason=f'Humidity normalized: {humidity}% at {location}'
                    ))
        
        return commands
    
    def _process_light(self, light_level: float, location: str) -> List[ActuatorCommand]:
        """Process light sensor readings"""
        commands = []
        rules = self.rules['light']
        
        # Only auto-control if there's recent motion
        has_recent_motion = self._has_recent_motion(location)
        
        if light_level < rules['dark_threshold'] and has_recent_motion:
            # Dark and motion detected - turn on lights
            light_id = f'{location}_lights'
            if light_id in Config.ACTUATORS:
                commands.append(ActuatorCommand(
                    actuator_id=light_id,
                    actuator_type='light',
                    state='on',
                    value=80,  # 80% brightness
                    reason=f'Dark environment: {light_level} lux with motion at {location}'
                ))
        
        elif light_level > rules['bright_threshold']:
            # Bright - turn off lights to save energy
            light_id = f'{location}_lights'
            if light_id in Config.ACTUATORS:
                current_state = self.actuator_states.get(light_id, 'off')
                if current_state == 'on':
                    commands.append(ActuatorCommand(
                        actuator_id=light_id,
                        actuator_type='light',
                        state='off',
                        reason=f'Bright environment: {light_level} lux at {location}'
                    ))
        
        return commands
    
    def _process_motion(self, motion: int, location: str) -> List[ActuatorCommand]:
        """Process motion sensor readings"""
        commands = []
        
        if motion == 1:
            # Motion detected
            self.last_motion_time[location] = datetime.utcnow()
            
            # Turn on lights if dark
            light_id = f'{location}_lights'
            if light_id in Config.ACTUATORS:
                # Check if it's dark
                recent_light = self._get_recent_sensor_value(location, 'light')
                if recent_light is not None and recent_light < self.rules['light']['dark_threshold']:
                    commands.append(ActuatorCommand(
                        actuator_id=light_id,
                        actuator_type='light',
                        state='on',
                        value=80,
                        reason=f'Motion detected in dark area at {location}'
                    ))
        
        else:
            # No motion - check if we should turn off lights
            self._check_motion_timeout(location, commands)
        
        return commands
    
    def _process_co2(self, co2_level: float, location: str) -> List[ActuatorCommand]:
        """Process CO2 sensor readings"""
        commands = []
        rules = self.rules['co2']
        
        if co2_level > rules['critical_threshold']:
            # Critical CO2 level
            commands.append(ActuatorCommand(
                actuator_id='hvac_system',
                actuator_type='climate_control',
                state='fan_only',
                reason=f'Critical CO2 level: {co2_level} ppm at {location}'
            ))
            if location == 'kitchen':
                commands.append(ActuatorCommand(
                    actuator_id='kitchen_exhaust',
                    actuator_type='fan',
                    state='high',
                    reason=f'Critical CO2 level: {co2_level} ppm'
                ))
        
        elif co2_level > rules['warning_threshold']:
            # Warning CO2 level - increase ventilation
            commands.append(ActuatorCommand(
                actuator_id='hvac_system',
                actuator_type='climate_control',
                state='fan_only',
                reason=f'Elevated CO2 level: {co2_level} ppm at {location}'
            ))
        
        return commands
    
    def _process_gas(self, gas_level: float, location: str) -> List[ActuatorCommand]:
        """Process gas sensor readings"""
        commands = []
        rules = self.rules['gas']
        
        if gas_level > rules['critical_threshold']:
            # Critical gas level - sound alarm
            if self._can_send_alert('gas_alarm'):
                commands.append(ActuatorCommand(
                    actuator_id='gas_alarm',
                    actuator_type='alarm',
                    state='on',
                    reason=f'Critical gas level: {gas_level} ppm at {location}'
                ))
                commands.append(ActuatorCommand(
                    actuator_id='kitchen_exhaust',
                    actuator_type='fan',
                    state='high',
                    reason=f'Emergency ventilation for gas: {gas_level} ppm'
                ))
        
        elif gas_level > rules['warning_threshold']:
            # Warning level
            commands.append(ActuatorCommand(
                actuator_id='kitchen_exhaust',
                actuator_type='fan',
                state='medium',
                reason=f'Elevated gas level: {gas_level} ppm at {location}'
            ))
        
        return commands
    
    def _process_smoke(self, smoke: int, location: str) -> List[ActuatorCommand]:
        """Process smoke sensor readings"""
        commands = []
        
        if smoke == 1 and self._can_send_alert('fire_alarm'):
            # Smoke detected - trigger alarm
            commands.append(ActuatorCommand(
                actuator_id='fire_alarm',
                actuator_type='alarm',
                state='on',
                reason=f'Smoke detected at {location}'
            ))
            # Turn off potentially dangerous appliances
            commands.append(ActuatorCommand(
                actuator_id='hvac_system',
                actuator_type='climate_control',
                state='off',
                reason='Fire safety protocol'
            ))
        
        return commands
    
    def _process_distance(self, distance: float, location: str, reading: Dict) -> List[ActuatorCommand]:
        """Process distance sensor readings (dust cleaner)"""
        commands = []
        rules = self.rules['distance']
        
        if distance < rules['critical_threshold']:
            # Very close obstacle - stop immediately
            commands.append(ActuatorCommand(
                actuator_id='dust_cleaner_motor',
                actuator_type='motor',
                state='paused',
                reason=f'Critical obstacle at {distance}cm'
            ))
        
        elif distance < rules['obstacle_threshold']:
            # Obstacle detected - pause or navigate
            object_name = reading.get('object_name', 'unknown')
            commands.append(ActuatorCommand(
                actuator_id='dust_cleaner_motor',
                actuator_type='motor',
                state='paused',
                reason=f'Obstacle detected: {object_name} at {distance}cm'
            ))
        
        return commands
    
    def _process_water_leak(self, leak: int, location: str) -> List[ActuatorCommand]:
        """Process water leak sensor readings"""
        commands = []
        
        if leak == 1 and self._can_send_alert('water_leak'):
            # Water leak detected - shut off water
            commands.append(ActuatorCommand(
                actuator_id='water_shutoff',
                actuator_type='valve',
                state='off',
                reason=f'Water leak detected at {location}'
            ))
        
        return commands
    
    def _process_door_sensor(self, door_state: int, location: str) -> List[ActuatorCommand]:
        """Process door/window sensor readings"""
        commands = []
        
        if door_state == 0 and location == 'entrance':
            # Door open at entrance - turn on entrance light
            commands.append(ActuatorCommand(
                actuator_id='entrance_lights',
                actuator_type='light',
                state='on',
                reason='Entrance door opened'
            ))
        
        return commands
    
    def _cross_sensor_decisions(
        self, 
        device_id: str, 
        location: str, 
        readings: List[Dict]
    ) -> List[ActuatorCommand]:
        """Make decisions based on multiple sensor inputs"""
        commands = []
        
        # Extract sensor values
        sensor_values = {r['sensor_type']: r['value'] for r in readings}
        
        # Kitchen safety: High temp + gas detected
        if location == 'kitchen':
            temp = sensor_values.get('temperature')
            gas = sensor_values.get('gas')
            
            if temp and gas and temp > 35 and gas > 500:
                if self._can_send_alert('kitchen_emergency'):
                    commands.append(ActuatorCommand(
                        actuator_id='kitchen_exhaust',
                        actuator_type='fan',
                        state='high',
                        reason=f'Kitchen emergency: temp={temp}°C, gas={gas}ppm'
                    ))
        
        # Entrance security: Motion + door open + no RFID
        if location == 'entrance':
            motion = sensor_values.get('motion')
            door = sensor_values.get('door_sensor')
            rfid = sensor_values.get('rfid')
            
            if motion == 1 and door == 0 and rfid == 'None':
                # Potential unauthorized entry
                commands.append(ActuatorCommand(
                    actuator_id='entrance_lights',
                    actuator_type='light',
                    state='on',
                    value=100,
                    reason='Potential unauthorized entry detected'
                ))
        
        return commands
    
    def _update_history(self, device_id: str, readings: List[Dict]):
        """Update sensor history for trend analysis"""
        for reading in readings:
            key = f"{device_id}_{reading['sensor_type']}"
            self.sensor_history[key].append({
                'value': reading['value'],
                'timestamp': datetime.utcnow()
            })
            # Keep only recent history
            if len(self.sensor_history[key]) > 100:
                self.sensor_history[key] = self.sensor_history[key][-100:]
    
    def _has_recent_motion(self, location: str, timeout_seconds: int = 300) -> bool:
        """Check if there was recent motion in location"""
        if location not in self.last_motion_time:
            return False
        
        time_since_motion = (datetime.utcnow() - self.last_motion_time[location]).total_seconds()
        return time_since_motion < timeout_seconds
    
    def _check_motion_timeout(self, location: str, commands: List[ActuatorCommand]):
        """Check if motion timeout expired and turn off lights"""
        if not self._has_recent_motion(location, timeout_seconds=300):
            light_id = f'{location}_lights'
            if light_id in Config.ACTUATORS:
                current_state = self.actuator_states.get(light_id, 'off')
                if current_state == 'on':
                    commands.append(ActuatorCommand(
                        actuator_id=light_id,
                        actuator_type='light',
                        state='off',
                        reason=f'No motion timeout at {location}'
                    ))
    
    def _get_recent_sensor_value(
        self, 
        location: str, 
        sensor_type: str
    ) -> Optional[float]:
        """Get most recent sensor value for a location"""
        key = f"{location}_{sensor_type}"
        if key in self.sensor_history and self.sensor_history[key]:
            return self.sensor_history[key][-1]['value']
        return None
    
    def _can_send_alert(self, alert_id: str, cooldown_seconds: int = 60) -> bool:
        """Check if we can send an alert (prevent spam)"""
        if alert_id not in self.alert_cooldown:
            self.alert_cooldown[alert_id] = datetime.utcnow()
            return True
        
        time_since_last = (datetime.utcnow() - self.alert_cooldown[alert_id]).total_seconds()
        if time_since_last > cooldown_seconds:
            self.alert_cooldown[alert_id] = datetime.utcnow()
            return True
        
        return False
    
    def update_actuator_state(self, actuator_id: str, state: str):
        """Update cached actuator state"""
        self.actuator_states[actuator_id] = state
