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
        self.manual_override = {}  # Track manually controlled actuators
        self.manual_override_timeout = 3600  # 1 hour in seconds
        
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
        
        # Collect all temperature readings (don't process individually)
        temp_readings = []
        
        # Process each reading
        for reading in readings:
            sensor_type = reading.get('sensor_type')
            value = reading.get('value')
            
            # Route to appropriate decision logic
            if sensor_type == 'temperature':
                # Collect temperature readings instead of processing immediately
                temp_readings.append({'value': value, 'location': location})
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
            elif sensor_type == 'sound':
                commands.extend(self._process_sound(value, location))
            elif sensor_type == 'vibration':
                commands.extend(self._process_vibration(value, location))
            elif sensor_type == 'energy':
                commands.extend(self._process_energy(value, location))
            elif sensor_type == 'uv':
                commands.extend(self._process_uv(value, location))
            elif sensor_type == 'rain':
                commands.extend(self._process_rain(value, location))
            elif sensor_type == 'glass_break':
                commands.extend(self._process_glass_break(value, location))
            elif sensor_type == 'pressure_mat':
                commands.extend(self._process_pressure_mat(value, location))
        
        # Process aggregated temperature readings (after collecting from all sensors)
        if temp_readings:
            # Get all recent temperature readings from history across all locations
            all_temps = self._get_all_recent_temperatures()
            # Make a single HVAC decision based on aggregated data
            commands.extend(self._process_aggregated_temperature(all_temps))
        
        # Cross-sensor intelligence (combine multiple sensor inputs)
        commands.extend(self._cross_sensor_decisions(device_id, location, readings))
        
        return commands
    
    def _process_temperature(self, temp: float, location: str) -> List[ActuatorCommand]:
        """Process temperature readings with hysteresis to prevent oscillation"""
        commands = []
        rules = self.rules['temperature']
        current_state = self.actuator_states.get('hvac_system', 'off')
        
        # Hysteresis buffer (deadband) in degrees
        HYSTERESIS = 2.0
        
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
        
        # High temperature - turn on cooling (only if not already cooling)
        elif temp > rules['high_threshold']:
            if current_state != 'cooling':
                commands.append(ActuatorCommand(
                    actuator_id='hvac_system',
                    actuator_type='climate_control',
                    state='cooling',
                    reason=f'High temperature: {temp}°C at {location}'
                ))
        
        # Temperature dropped below (high_threshold - hysteresis) - turn off cooling
        elif temp <= (rules['high_threshold'] - HYSTERESIS) and current_state == 'cooling':
            commands.append(ActuatorCommand(
                actuator_id='hvac_system',
                actuator_type='climate_control',
                state='off',
                reason=f'Temperature cooled to {temp}°C at {location}'
            ))
        
        # Low temperature - turn on heating (only if not already heating)
        elif temp < rules['low_threshold']:
            if current_state != 'heating':
                commands.append(ActuatorCommand(
                    actuator_id='hvac_system',
                    actuator_type='climate_control',
                    state='heating',
                    reason=f'Low temperature: {temp}°C at {location}'
                ))
        
        # Temperature rose above (low_threshold + hysteresis) - turn off heating
        elif temp >= (rules['low_threshold'] + HYSTERESIS) and current_state == 'heating':
            commands.append(ActuatorCommand(
                actuator_id='hvac_system',
                actuator_type='climate_control',
                state='off',
                reason=f'Temperature warmed to {temp}°C at {location}'
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
        
        # Check for recent motion (but allow automation without motion too)
        has_recent_motion = self._has_recent_motion(location)
        
        if light_level < rules['dark_threshold']:
            # Dark - turn on lights (prioritize motion, but work without it too)
            light_id = f'{location}_lights'
            if light_id in Config.ACTUATORS:
                reason = f'Dark environment: {light_level} lux'
                if has_recent_motion:
                    reason += ' with motion'
                reason += f' at {location}'
                
                commands.append(ActuatorCommand(
                    actuator_id=light_id,
                    actuator_type='light',
                    state='on',
                    value=80,  # 80% brightness
                    reason=reason
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
            # Critical gas level - sound alarm (no cooldown for safety)
            current_alarm_state = self.actuator_states.get('gas_alarm', 'off')
            if current_alarm_state != 'on':
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
        else:
            # Normal gas level - turn off alarm and exhaust
            current_alarm_state = self.actuator_states.get('gas_alarm', 'off')
            current_exhaust_state = self.actuator_states.get('kitchen_exhaust', 'off')
            
            if current_alarm_state == 'on':
                commands.append(ActuatorCommand(
                    actuator_id='gas_alarm',
                    actuator_type='alarm',
                    state='off',
                    reason=f'Gas level normalized: {gas_level} ppm at {location}'
                ))
            
            if current_exhaust_state != 'off':
                commands.append(ActuatorCommand(
                    actuator_id='kitchen_exhaust',
                    actuator_type='fan',
                    state='off',
                    reason=f'Gas level normalized: {gas_level} ppm at {location}'
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
        
        if leak == 1:
            # Water leak detected - shut off water (no cooldown for safety)
            current_state = self.actuator_states.get('water_shutoff', 'on')
            if current_state != 'off':
                commands.append(ActuatorCommand(
                    actuator_id='water_shutoff',
                    actuator_type='valve',
                    state='off',
                    reason=f'Water leak detected at {location}'
                ))
        elif leak == 0:
            # No leak - turn water back on if it was off
            current_state = self.actuator_states.get('water_shutoff', 'on')
            if current_state == 'off':
                commands.append(ActuatorCommand(
                    actuator_id='water_shutoff',
                    actuator_type='valve',
                    state='on',
                    reason=f'Water leak cleared at {location}'
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

    def _process_sound(self, sound: float, location: str) -> List[ActuatorCommand]:
        commands = []
        rules = self.rules.get('sound', {})
        if not rules:
            return commands
        if sound >= rules['critical_threshold']:
            commands.append(ActuatorCommand(
                actuator_id='siren',
                actuator_type='alarm',
                state='on',
                reason=f'Critical noise {sound} dB at {location}'
            ))
        elif sound >= rules['warning_threshold']:
            # optional logging only
            pass
        return commands

    def _process_vibration(self, vib: float, location: str) -> List[ActuatorCommand]:
        commands = []
        rules = self.rules.get('vibration', {})
        if not rules:
            return commands
        if vib >= rules['critical_threshold']:
            commands.append(ActuatorCommand(
                actuator_id='siren',
                actuator_type='alarm',
                state='on',
                reason=f'Critical vibration {vib}g at {location}'
            ))
        return commands

    def _process_energy(self, watts: float, location: str) -> List[ActuatorCommand]:
        commands = []
        rules = self.rules.get('energy', {})
        if not rules:
            return commands
        if watts >= rules['critical_threshold']:
            commands.append(ActuatorCommand(
                actuator_id='smart_plug',
                actuator_type='switch',
                state='off',
                reason=f'Critical energy draw {watts}W at {location}'
            ))
        elif watts >= rules['high_threshold']:
            commands.append(ActuatorCommand(
                actuator_id='smart_plug',
                actuator_type='switch',
                state='off',
                reason=f'High energy draw {watts}W at {location}'
            ))
        return commands

    def _process_uv(self, uv: float, location: str) -> List[ActuatorCommand]:
        commands = []
        rules = self.rules.get('uv', {})
        if not rules:
            return commands
        if uv >= rules['high_threshold']:
            commands.append(ActuatorCommand(
                actuator_id='rain_shutter',
                actuator_type='shutter',
                state='closed',
                reason=f'High UV index {uv} at {location}'
            ))
        return commands

    def _process_rain(self, rain: int, location: str) -> List[ActuatorCommand]:
        commands = []
        if rain == 1:
            commands.append(ActuatorCommand(
                actuator_id='rain_shutter',
                actuator_type='shutter',
                state='closed',
                reason=f'Rain detected at {location}'
            ))
        return commands

    def _process_glass_break(self, detected: int, location: str) -> List[ActuatorCommand]:
        commands = []
        if detected == 1 and self._can_send_alert('glass_break'):
            commands.append(ActuatorCommand(
                actuator_id='siren',
                actuator_type='alarm',
                state='on',
                reason=f'Glass break detected at {location}'
            ))
        return commands

    def _process_pressure_mat(self, present: int, location: str) -> List[ActuatorCommand]:
        commands = []
        if present == 1 and location == 'entrance':
            commands.append(ActuatorCommand(
                actuator_id='entrance_lights',
                actuator_type='light',
                state='on',
                reason='Presence detected on pressure mat'
            ))
        return commands
    
    def _get_all_recent_temperatures(self) -> List[Dict[str, Any]]:
        """Get all recent temperature readings from all locations"""
        temps = []
        cutoff_time = datetime.utcnow() - timedelta(minutes=5)  # Last 5 minutes
        
        for key, history in self.sensor_history.items():
            if '_temperature' in key and history:
                # Get the most recent reading
                recent = history[-1]
                if recent['timestamp'] >= cutoff_time:
                    location = key.split('_temperature')[0]
                    temps.append({
                        'location': location,
                        'value': recent['value'],
                        'timestamp': recent['timestamp']
                    })
        
        return temps
    
    def set_manual_override(self, actuator_id: str):
        """Mark an actuator as manually controlled"""
        self.manual_override[actuator_id] = datetime.utcnow()
        logger.info(f"Manual override enabled for {actuator_id}")
    
    def clear_manual_override(self, actuator_id: str):
        """Clear manual override for an actuator"""
        if actuator_id in self.manual_override:
            del self.manual_override[actuator_id]
            logger.info(f"Manual override cleared for {actuator_id}")
    
    def is_manually_overridden(self, actuator_id: str) -> bool:
        """Check if actuator is currently under manual control"""
        if actuator_id not in self.manual_override:
            return False
        
        # Check if override has expired
        time_since_override = (datetime.utcnow() - self.manual_override[actuator_id]).total_seconds()
        if time_since_override > self.manual_override_timeout:
            # Override expired, clear it
            del self.manual_override[actuator_id]
            logger.info(f"Manual override expired for {actuator_id}")
            return False
        
        return True
    
    def _process_aggregated_temperature(self, all_temps: List[Dict[str, Any]]) -> List[ActuatorCommand]:
        """
        Process all temperature readings together to make a single HVAC decision
        Uses weighted average based on location importance
        """
        commands = []
        
        if not all_temps:
            return commands
        
        # Check if HVAC is manually controlled
        if self.is_manually_overridden('hvac_system'):
            logger.debug("HVAC system is manually controlled, skipping automated control")
            return commands
        
        rules = self.rules['temperature']
        current_state = self.actuator_states.get('hvac_system', 'off')
        HYSTERESIS = 2.0
        
        # Location weights (living areas more important than utility)
        LOCATION_WEIGHTS = {
            'living_room': 1.5,
            'bedroom': 1.5,
            'kitchen': 1.0,
            'roof': 0.5,
            'basement': 0.3
        }
        
        # Calculate weighted average temperature
        total_weight = 0
        weighted_sum = 0
        max_temp = -999
        min_temp = 999
        
        for temp_data in all_temps:
            location = temp_data['location']
            value = temp_data['value']
            weight = LOCATION_WEIGHTS.get(location, 1.0)
            
            weighted_sum += value * weight
            total_weight += weight
            max_temp = max(max_temp, value)
            min_temp = min(min_temp, value)
        
        avg_temp = weighted_sum / total_weight if total_weight > 0 else 0
        
        logger.info(f"Temperature aggregation: avg={avg_temp:.1f}°C, max={max_temp:.1f}°C, min={min_temp:.1f}°C, locations={len(all_temps)}")
        
        # Critical high temperature (use max temp for safety)
        if max_temp >= rules['critical_high']:
            commands.append(ActuatorCommand(
                actuator_id='hvac_system',
                actuator_type='climate_control',
                state='cooling',
                reason=f'Critical temperature detected: max={max_temp:.1f}°C across {len(all_temps)} locations'
            ))
            commands.append(ActuatorCommand(
                actuator_id='fire_alarm',
                actuator_type='alarm',
                state='on',
                reason=f'Temperature critically high: {max_temp:.1f}°C'
            ))
        
        # High temperature - turn on cooling (use weighted average)
        elif avg_temp > rules['high_threshold']:
            if current_state != 'cooling':
                commands.append(ActuatorCommand(
                    actuator_id='hvac_system',
                    actuator_type='climate_control',
                    state='cooling',
                    reason=f'High average temperature: {avg_temp:.1f}°C across {len(all_temps)} locations'
                ))
        
        # Temperature dropped - turn off cooling (use weighted average with hysteresis)
        elif avg_temp <= (rules['high_threshold'] - HYSTERESIS) and current_state == 'cooling':
            commands.append(ActuatorCommand(
                actuator_id='hvac_system',
                actuator_type='climate_control',
                state='off',
                reason=f'Temperature normalized: avg={avg_temp:.1f}°C across {len(all_temps)} locations'
            ))
        
        # Low temperature - turn on heating (use min temp for comfort)
        elif min_temp < rules['low_threshold']:
            if current_state != 'heating':
                commands.append(ActuatorCommand(
                    actuator_id='hvac_system',
                    actuator_type='climate_control',
                    state='heating',
                    reason=f'Low temperature detected: min={min_temp:.1f}°C across {len(all_temps)} locations'
                ))
        
        # Temperature rose - turn off heating (use weighted average with hysteresis)
        elif avg_temp >= (rules['low_threshold'] + HYSTERESIS) and current_state == 'heating':
            commands.append(ActuatorCommand(
                actuator_id='hvac_system',
                actuator_type='climate_control',
                state='off',
                reason=f'Temperature normalized: avg={avg_temp:.1f}°C across {len(all_temps)} locations'
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
