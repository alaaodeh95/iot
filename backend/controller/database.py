"""
MongoDB database manager for IoT system
"""
from pymongo import MongoClient, DESCENDING
from pymongo.collection import Collection
from pymongo.database import Database
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages MongoDB connections and operations"""
    
    def __init__(self, uri: str, database_name: str):
        """Initialize database connection"""
        self.client: MongoClient = MongoClient(uri)
        self.db: Database = self.client[database_name]
        
        # Collections
        self.sensor_readings: Collection = self.db['sensor_readings']
        self.actuator_commands: Collection = self.db['actuator_commands']
        self.actuator_status: Collection = self.db['actuator_status']
        self.decision_logs: Collection = self.db['decision_logs']
        self.gateway_logs: Collection = self.db['gateway_logs']
        self.system_logs: Collection = self.db['system_logs']
        
        # Create indexes
        self._create_indexes()
        
        logger.info(f"Connected to MongoDB database: {database_name}")
    
    def _create_indexes(self):
        """Create database indexes for performance"""
        # Sensor readings indexes
        self.sensor_readings.create_index([('timestamp', DESCENDING)])
        self.sensor_readings.create_index([('sensor_id', 1), ('timestamp', DESCENDING)])
        self.sensor_readings.create_index([('location', 1), ('timestamp', DESCENDING)])
        
        # Actuator commands indexes
        self.actuator_commands.create_index([('timestamp', DESCENDING)])
        self.actuator_commands.create_index([('actuator_id', 1), ('timestamp', DESCENDING)])
        
        # Decision logs indexes
        self.decision_logs.create_index([('timestamp', DESCENDING)])
        
        logger.info("Database indexes created")
    
    def store_sensor_reading(self, reading_data: Dict[str, Any]) -> str:
        """Store a sensor reading"""
        result = self.sensor_readings.insert_one(reading_data)
        return str(result.inserted_id)
    
    def store_sensor_group(self, group_data: Dict[str, Any]) -> str:
        """Store a group of sensor readings"""
        result = self.sensor_readings.insert_one(group_data)
        return str(result.inserted_id)
    
    def store_actuator_command(self, command_data: Dict[str, Any]) -> str:
        """Store an actuator command"""
        result = self.actuator_commands.insert_one(command_data)
        return str(result.inserted_id)
    
    def update_actuator_status(self, actuator_id: str, status_data: Dict[str, Any]):
        """Update actuator status"""
        self.actuator_status.update_one(
            {'actuator_id': actuator_id},
            {'$set': status_data},
            upsert=True
        )
    
    def get_actuator_status(self, actuator_id: str) -> Optional[Dict[str, Any]]:
        """Get current actuator status"""
        return self.actuator_status.find_one({'actuator_id': actuator_id})
    
    def get_all_actuator_statuses(self) -> List[Dict[str, Any]]:
        """Get all actuator statuses"""
        return list(self.actuator_status.find())
    
    def store_decision_log(self, decision_data: Dict[str, Any]) -> str:
        """Store a decision log"""
        result = self.decision_logs.insert_one(decision_data)
        return str(result.inserted_id)
    
    def store_gateway_log(self, log_data: Dict[str, Any]) -> str:
        """Store a gateway processing log"""
        result = self.gateway_logs.insert_one(log_data)
        return str(result.inserted_id)
    
    def get_recent_sensor_readings(
        self, 
        sensor_id: Optional[str] = None,
        location: Optional[str] = None,
        minutes: int = 10,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get recent sensor readings"""
        query = {}
        if sensor_id:
            query['sensor_id'] = sensor_id
        if location:
            query['location'] = location
        
        # Add time filter
        cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)
        query['timestamp'] = {'$gte': cutoff_time}
        
        return list(
            self.sensor_readings
            .find(query)
            .sort('timestamp', DESCENDING)
            .limit(limit)
        )
    
    def get_sensor_statistics(
        self,
        sensor_type: str,
        location: Optional[str] = None,
        hours: int = 24
    ) -> Dict[str, Any]:
        """Get statistics for a sensor type"""
        query = {'sensor_type': sensor_type}
        if location:
            query['location'] = location
        
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        query['timestamp'] = {'$gte': cutoff_time}
        
        readings = list(self.sensor_readings.find(query))
        
        if not readings:
            return {
                'count': 0,
                'avg': None,
                'min': None,
                'max': None
            }
        
        values = [r.get('value') for r in readings if isinstance(r.get('value'), (int, float))]
        
        if not values:
            return {
                'count': len(readings),
                'avg': None,
                'min': None,
                'max': None
            }
        
        return {
            'count': len(values),
            'avg': sum(values) / len(values),
            'min': min(values),
            'max': max(values)
        }
    
    def get_recent_decisions(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent decision logs"""
        return list(
            self.decision_logs
            .find()
            .sort('timestamp', DESCENDING)
            .limit(limit)
        )
    
    def get_actuator_history(
        self,
        actuator_id: str,
        hours: int = 24,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get actuator command history"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        return list(
            self.actuator_commands
            .find({
                'actuator_id': actuator_id,
                'timestamp': {'$gte': cutoff_time}
            })
            .sort('timestamp', DESCENDING)
            .limit(limit)
        )
    
    def get_gateway_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """Get gateway filtering statistics"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        logs = list(self.gateway_logs.find({
            'timestamp': {'$gte': cutoff_time}
        }))
        
        total_processed = len(logs)
        outliers_detected = sum(1 for log in logs if log.get('outliers_detected', 0) > 0)
        total_outliers = sum(log.get('outliers_detected', 0) for log in logs)
        
        return {
            'total_processed': total_processed,
            'batches_with_outliers': outliers_detected,
            'total_outliers_filtered': total_outliers,
            'filter_rate': (total_outliers / total_processed) if total_processed > 0 else 0
        }
    
    def cleanup_old_data(self, days: int = 30):
        """Remove data older than specified days"""
        cutoff_time = datetime.utcnow() - timedelta(days=days)
        
        # Clean sensor readings
        result = self.sensor_readings.delete_many({'timestamp': {'$lt': cutoff_time}})
        logger.info(f"Deleted {result.deleted_count} old sensor readings")
        
        # Clean actuator commands
        result = self.actuator_commands.delete_many({'timestamp': {'$lt': cutoff_time}})
        logger.info(f"Deleted {result.deleted_count} old actuator commands")
        
        # Clean decision logs
        result = self.decision_logs.delete_many({'timestamp': {'$lt': cutoff_time}})
        logger.info(f"Deleted {result.deleted_count} old decision logs")
        
        # Clean gateway logs
        result = self.gateway_logs.delete_many({'timestamp': {'$lt': cutoff_time}})
        logger.info(f"Deleted {result.deleted_count} old gateway logs")
    
    def get_system_overview(self) -> Dict[str, Any]:
        """Get system overview statistics"""
        now = datetime.utcnow()
        last_hour = now - timedelta(hours=1)
        
        return {
            'total_sensor_readings': self.sensor_readings.count_documents({}),
            'readings_last_hour': self.sensor_readings.count_documents({
                'timestamp': {'$gte': last_hour}
            }),
            'total_actuator_commands': self.actuator_commands.count_documents({}),
            'commands_last_hour': self.actuator_commands.count_documents({
                'timestamp': {'$gte': last_hour}
            }),
            'total_decisions': self.decision_logs.count_documents({}),
            'decisions_last_hour': self.decision_logs.count_documents({
                'timestamp': {'$gte': last_hour}
            }),
            'active_actuators': self.actuator_status.count_documents({}),
            'timestamp': now
        }
    
    def get_sensor_aggregate_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Aggregate statistics per sensor_type over the last N hours"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        pipeline = [
            {"$match": {"timestamp": {"$gte": cutoff_time}}},
            {"$unwind": "$readings"},
            {"$group": {
                "_id": "$readings.sensor_type",
                "count": {"$sum": 1},
                "avg": {"$avg": "$readings.value"},
                "min": {"$min": "$readings.value"},
                "max": {"$max": "$readings.value"}
            }},
            {"$project": {
                "sensor_type": "$_id",
                "count": 1,
                "avg": 1,
                "min": 1,
                "max": 1,
                "_id": 0
            }}
        ]
        return list(self.sensor_readings.aggregate(pipeline))

    def get_actuator_usage(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Usage frequency per actuator over the last N hours"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        pipeline = [
            {"$match": {"timestamp": {"$gte": cutoff_time}}},
            {"$group": {
                "_id": "$actuator_id",
                "count": {"$sum": 1},
                "states": {"$addToSet": "$state"}
            }},
            {"$project": {
                "actuator_id": "$_id",
                "count": 1,
                "states": 1,
                "_id": 0
            }}
        ]
        return list(self.actuator_commands.aggregate(pipeline))

    def get_decision_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Decision volume summary"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        total = self.decision_logs.count_documents({})
        recent = self.decision_logs.count_documents({"timestamp": {"$gte": cutoff_time}})
        return {"total": total, "last_hours": recent}

    def get_recent_gateway_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Fetch recent gateway logs"""
        logs = list(
            self.gateway_logs.find()
            .sort('timestamp', DESCENDING)
            .limit(limit)
        )
        for log in logs:
            if 'timestamp' in log:
                log['timestamp'] = log['timestamp'].isoformat()
            log['_id'] = str(log['_id'])
        return logs

    def close(self):
        """Close database connection"""
        self.client.close()
        logger.info("Database connection closed")
