"""
Data models for IoT system
"""
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field, asdict
from enum import Enum

class DataFormat(Enum):
    """Data format types"""
    JSON = "json"
    XML = "xml"

class ActuatorState(Enum):
    """Actuator states"""
    OFF = "off"
    ON = "on"
    HEATING = "heating"
    COOLING = "cooling"
    FAN_ONLY = "fan_only"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CLEANING = "cleaning"
    PAUSED = "paused"
    RETURNING = "returning"
    LOCKED = "locked"
    UNLOCKED = "unlocked"

@dataclass
class SensorReading:
    """Individual sensor reading"""
    sensor_id: str
    sensor_type: str
    value: Any
    unit: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    location: str = ""
    format: str = "json"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    def to_mongo(self) -> Dict[str, Any]:
        """Convert to MongoDB document"""
        return {
            'sensor_id': self.sensor_id,
            'sensor_type': self.sensor_type,
            'value': self.value,
            'unit': self.unit,
            'timestamp': self.timestamp,
            'location': self.location,
            'format': self.format
        }

@dataclass
class SensorGroup:
    """Group of sensor readings (e.g., from one device)"""
    device_id: str
    location: str
    readings: List[SensorReading]
    timestamp: datetime = field(default_factory=datetime.utcnow)
    format: str = "json"
    gateway_processed: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'device_id': self.device_id,
            'location': self.location,
            'readings': [r.to_dict() for r in self.readings],
            'timestamp': self.timestamp.isoformat(),
            'format': self.format,
            'gateway_processed': self.gateway_processed
        }
    
    def to_mongo(self) -> Dict[str, Any]:
        """Convert to MongoDB document"""
        return {
            'device_id': self.device_id,
            'location': self.location,
            'readings': [r.to_mongo() for r in self.readings],
            'timestamp': self.timestamp,
            'format': self.format,
            'gateway_processed': self.gateway_processed
        }

@dataclass
class ActuatorCommand:
    """Command to control an actuator"""
    actuator_id: str
    actuator_type: str
    state: str
    value: Optional[Any] = None
    reason: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    triggered_by: str = "system"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    def to_mongo(self) -> Dict[str, Any]:
        """Convert to MongoDB document"""
        return {
            'actuator_id': self.actuator_id,
            'actuator_type': self.actuator_type,
            'state': self.state,
            'value': self.value,
            'reason': self.reason,
            'timestamp': self.timestamp,
            'triggered_by': self.triggered_by
        }

@dataclass
class ActuatorStatus:
    """Current status of an actuator"""
    actuator_id: str
    actuator_type: str
    state: str
    value: Optional[Any] = None
    location: str = ""
    last_updated: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data['last_updated'] = self.last_updated.isoformat()
        return data

@dataclass
class DecisionLog:
    """Log of decision made by controller"""
    decision_id: str
    trigger_sensor: str
    trigger_value: Any
    condition: str
    actions: List[ActuatorCommand]
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'decision_id': self.decision_id,
            'trigger_sensor': self.trigger_sensor,
            'trigger_value': self.trigger_value,
            'condition': self.condition,
            'actions': [a.to_dict() for a in self.actions],
            'timestamp': self.timestamp.isoformat()
        }
    
    def to_mongo(self) -> Dict[str, Any]:
        """Convert to MongoDB document"""
        return {
            'decision_id': self.decision_id,
            'trigger_sensor': self.trigger_sensor,
            'trigger_value': self.trigger_value,
            'condition': self.condition,
            'actions': [a.to_mongo() for a in self.actions],
            'timestamp': self.timestamp
        }

@dataclass
class SystemStatus:
    """Overall system status"""
    total_sensors: int
    active_sensors: int
    total_actuators: int
    active_actuators: int
    alerts: List[str]
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data
