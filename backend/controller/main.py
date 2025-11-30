"""
Main IoT Controller Server
Handles REST API, WebSocket, and sensor data processing
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import logging
from datetime import datetime
from typing import Dict, Any, List
import uuid
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.config import Config
from backend.controller.database import DatabaseManager
from backend.controller.decision_engine import DecisionEngine
from backend.models import (
    SensorReading, SensorGroup, ActuatorCommand, 
    ActuatorStatus, DecisionLog
)

# Configure logging
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format=Config.LOG_FORMAT
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'iot-smart-home-secret-key'
CORS(app, resources={r"/*": {"origins": Config.CORS_ORIGINS}})

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins=Config.CORS_ORIGINS)

# Initialize components
db = DatabaseManager(Config.MONGODB_URI, Config.MONGODB_DATABASE)
decision_engine = DecisionEngine()

# Store current actuator states
actuator_states: Dict[str, ActuatorStatus] = {}

# Initialize actuator states
for actuator_id, config in Config.ACTUATORS.items():
    actuator_states[actuator_id] = ActuatorStatus(
        actuator_id=actuator_id,
        actuator_type=config['type'],
        state='off',
        location=config['location']
    )
    db.update_actuator_status(actuator_id, actuator_states[actuator_id].to_dict())


@app.route('/')
def index():
    """API root"""
    return jsonify({
        'service': 'IoT Smart Home Controller',
        'version': '1.0.0',
        'status': 'running',
        'endpoints': {
            'sensor_data': '/api/sensor-data',
            'sensor_data_xml': '/api/sensor-data/xml',
            'actuators': '/api/actuators',
            'actuator_control': '/api/actuators/<actuator_id>',
            'system_status': '/api/status',
            'statistics': '/api/statistics',
            'recent_decisions': '/api/decisions',
            'sensor_override': '/api/sensor-override'
        }
    })


@app.route('/api/sensor-data', methods=['POST'])
def receive_sensor_data_json():
    """Receive sensor data in JSON format"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        logger.info(f"Received JSON sensor data from {data.get('device_id')}")
        
        # Process sensor data
        result = process_sensor_data(data, format='json')
        
        # Emit real-time update via WebSocket
        socketio.emit('sensor_update', {
            'device_id': data.get('device_id'),
            'location': data.get('location'),
            'readings': data.get('readings'),
            'timestamp': datetime.utcnow().isoformat()
        })
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error processing JSON sensor data: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/sensor-data/xml', methods=['POST'])
def receive_sensor_data_xml():
    """Receive sensor data in XML/SOAP format"""
    try:
        xml_data = request.data.decode('utf-8')
        
        if not xml_data:
            return jsonify({'error': 'No data provided'}), 400
        
        logger.info("Received XML sensor data")
        
        # Parse XML data
        import xml.etree.ElementTree as ET
        root = ET.fromstring(xml_data)
        
        # Extract sensor data from XML
        device_id = root.find('.//device_id').text if root.find('.//device_id') is not None else 'unknown'
        location = root.find('.//location').text if root.find('.//location') is not None else 'unknown'
        
        readings = []
        for sensor in root.findall('.//sensor'):
            sensor_type = sensor.find('type').text if sensor.find('type') is not None else ''
            value_elem = sensor.find('value')
            unit = sensor.find('unit').text if sensor.find('unit') is not None else ''
            
            # Parse value (handle different types)
            if value_elem is not None:
                value_text = value_elem.text
                try:
                    value = float(value_text)
                except ValueError:
                    value = value_text
            else:
                value = None
            
            readings.append({
                'sensor_type': sensor_type,
                'value': value,
                'unit': unit
            })
        
        data = {
            'device_id': device_id,
            'location': location,
            'readings': readings,
            'format': 'xml'
        }
        
        # Process sensor data
        result = process_sensor_data(data, format='xml')
        
        # Emit real-time update via WebSocket
        socketio.emit('sensor_update', {
            'device_id': device_id,
            'location': location,
            'readings': readings,
            'timestamp': datetime.utcnow().isoformat(),
            'format': 'xml'
        })
        
        # Return XML response
        response_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<response>
    <status>success</status>
    <message>Data processed successfully</message>
    <actuator_commands>{len(result.get('commands', []))}</actuator_commands>
</response>"""
        
        return response_xml, 200, {'Content-Type': 'application/xml'}
        
    except Exception as e:
        logger.error(f"Error processing XML sensor data: {e}", exc_info=True)
        error_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<response>
    <status>error</status>
    <message>{str(e)}</message>
</response>"""
        return error_xml, 500, {'Content-Type': 'application/xml'}


def process_sensor_data(data: Dict[str, Any], format: str = 'json') -> Dict[str, Any]:
    """Process incoming sensor data and make decisions"""
    
    # Create sensor group
    device_id = data.get('device_id')
    location = data.get('location')
    readings_data = data.get('readings', [])
    gateway_processed = data.get('gateway_processed', False)
    
    # Store in database
    sensor_group_data = {
        'device_id': device_id,
        'location': location,
        'readings': readings_data,
        'timestamp': datetime.utcnow(),
        'format': format,
        'gateway_processed': gateway_processed
    }
    db.store_sensor_group(sensor_group_data)
    
    # Make decisions using decision engine
    commands = decision_engine.process_sensor_data(data)
    
    # Execute actuator commands
    executed_commands = []
    for command in commands:
        execute_actuator_command(command)
        executed_commands.append(command.to_dict())
    
    # Log decision if commands were issued
    if commands:
        decision_log = DecisionLog(
            decision_id=str(uuid.uuid4()),
            trigger_sensor=device_id,
            trigger_value=str(readings_data),
            condition='automated_rule',
            actions=commands
        )
        db.store_decision_log(decision_log.to_mongo())
        
        # Emit decision via WebSocket
        socketio.emit('decision_made', decision_log.to_dict())
    
    logger.info(f"Processed sensor data from {device_id} at {location}, issued {len(commands)} commands")
    
    return {
        'status': 'success',
        'device_id': device_id,
        'location': location,
        'readings_count': len(readings_data),
        'commands': executed_commands,
        'gateway_processed': gateway_processed
    }


def execute_actuator_command(command: ActuatorCommand):
    """Execute an actuator command"""
    actuator_id = command.actuator_id
    
    # Update actuator state
    if actuator_id in actuator_states:
        actuator_states[actuator_id].state = command.state
        actuator_states[actuator_id].value = command.value
        actuator_states[actuator_id].last_updated = datetime.utcnow()
        
        # Update in database
        db.update_actuator_status(actuator_id, actuator_states[actuator_id].to_dict())
        
        # Store command in database
        db.store_actuator_command(command.to_mongo())
        
        # Update decision engine's actuator state cache
        decision_engine.update_actuator_state(actuator_id, command.state)
        
        # Emit actuator update via WebSocket
        socketio.emit('actuator_update', actuator_states[actuator_id].to_dict())
        
        logger.info(f"Executed command: {actuator_id} -> {command.state} ({command.reason})")
    else:
        logger.warning(f"Unknown actuator: {actuator_id}")


@app.route('/api/actuators', methods=['GET'])
def get_actuators():
    """Get all actuator statuses"""
    return jsonify({
        'actuators': [status.to_dict() for status in actuator_states.values()]
    })


@app.route('/api/actuators/<actuator_id>', methods=['POST'])
def control_actuator(actuator_id: str):
    """Manually control an actuator"""
    try:
        data = request.get_json()
        state = data.get('state')
        value = data.get('value')
        
        if actuator_id not in actuator_states:
            return jsonify({'error': 'Actuator not found'}), 404
        
        # Create manual command
        command = ActuatorCommand(
            actuator_id=actuator_id,
            actuator_type=actuator_states[actuator_id].actuator_type,
            state=state,
            value=value,
            reason='Manual override via API',
            triggered_by='user'
        )
        
        execute_actuator_command(command)
        
        return jsonify({
            'status': 'success',
            'actuator': actuator_states[actuator_id].to_dict()
        })
        
    except Exception as e:
        logger.error(f"Error controlling actuator: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/status', methods=['GET'])
def get_system_status():
    """Get overall system status"""
    try:
        overview = db.get_system_overview()
        
        active_actuators = sum(1 for a in actuator_states.values() if a.state != 'off')
        
        return jsonify({
            'status': 'operational',
            'timestamp': datetime.utcnow().isoformat(),
            'sensors': {
                'total_readings': overview['total_sensor_readings'],
                'readings_last_hour': overview['readings_last_hour']
            },
            'actuators': {
                'total': len(actuator_states),
                'active': active_actuators,
                'states': {aid: a.state for aid, a in actuator_states.items()}
            },
            'decisions': {
                'total': overview['total_decisions'],
                'decisions_last_hour': overview['decisions_last_hour']
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting system status: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    """Get system statistics"""
    try:
        sensor_type = request.args.get('sensor_type')
        location = request.args.get('location')
        
        if not sensor_type:
            return jsonify({'error': 'sensor_type parameter required'}), 400
        
        stats = db.get_sensor_statistics(sensor_type, location)
        gateway_stats = db.get_gateway_statistics()
        
        return jsonify({
            'sensor_statistics': stats,
            'gateway_statistics': gateway_stats
        })
        
    except Exception as e:
        logger.error(f"Error getting statistics: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/decisions', methods=['GET'])
def get_recent_decisions():
    """Get recent decision logs"""
    try:
        limit = int(request.args.get('limit', 50))
        decisions = db.get_recent_decisions(limit)
        
        # Convert ObjectId to string
        for decision in decisions:
            decision['_id'] = str(decision['_id'])
            if 'timestamp' in decision:
                decision['timestamp'] = decision['timestamp'].isoformat()
        
        return jsonify({'decisions': decisions})
        
    except Exception as e:
        logger.error(f"Error getting decisions: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/sensor-override', methods=['POST'])
def sensor_override():
    """Manually inject sensor values (for testing/demo)"""
    try:
        data = request.get_json()
        
        # Process as normal sensor data but mark as manual
        data['manual_override'] = True
        result = process_sensor_data(data, format='json')
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in sensor override: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/sensors/config', methods=['GET'])
def get_sensor_config():
    """Get sensor configuration"""
    return jsonify({
        'sensors': Config.SENSORS,
        'ranges': Config.get_sensor_ranges(),
        'object_types': Config.get_object_types()
    })


@socketio.on('connect')
def handle_connect():
    """Handle WebSocket connection"""
    logger.info('Client connected to WebSocket')
    emit('connection_response', {'status': 'connected'})


@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnection"""
    logger.info('Client disconnected from WebSocket')


@socketio.on('request_status')
def handle_status_request():
    """Handle status request via WebSocket"""
    emit('status_update', {
        'actuators': [status.to_dict() for status in actuator_states.values()],
        'timestamp': datetime.utcnow().isoformat()
    })


def main():
    """Main entry point"""
    logger.info("Starting IoT Smart Home Controller")
    logger.info(f"MongoDB: {Config.MONGODB_DATABASE}")
    logger.info(f"Host: {Config.CONTROLLER_HOST}:{Config.CONTROLLER_PORT}")
    
    try:
        socketio.run(
            app,
            host=Config.CONTROLLER_HOST,
            port=Config.CONTROLLER_PORT,
            debug=False,
            allow_unsafe_werkzeug=True
        )
    except KeyboardInterrupt:
        logger.info("Shutting down controller")
        db.close()
    except Exception as e:
        logger.error(f"Error running controller: {e}", exc_info=True)
        db.close()


if __name__ == '__main__':
    main()
