"""
Main IoT Controller Server
Handles REST API, WebSocket, and sensor data processing
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import uuid
import sys
import os
import io
import base64
import threading
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
load_dotenv(env_path)

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.config import Config
from backend.controller.database import DatabaseManager
from backend.controller.decision_engine import DecisionEngine
from backend.controller.ml_model import MLModelManager
from backend.security import (
    SecurityManager, require_api_key, require_device_auth, 
    require_gateway_auth, add_security_headers, RequestEncryption
)
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
app.config['SECRET_KEY'] = Config.JWT_SECRET_KEY
CORS(app, resources={r"/*": {"origins": "*"}})  # Allow all origins for development

# Initialize SocketIO with authentication
socketio = SocketIO(app, cors_allowed_origins="*")  # Allow all origins for development

# Initialize security components
security_manager = SecurityManager(Config)
app.security_manager = security_manager
request_encryption = RequestEncryption(Config.API_KEY)

# Add security headers to all responses
@app.after_request
def after_request(response):
    return add_security_headers(response)

# Initialize components
db = DatabaseManager(Config.MONGODB_URI, Config.MONGODB_DATABASE)
decision_engine = DecisionEngine()
ml_manager = MLModelManager(db)
ml_scheduler: Optional[threading.Timer] = None

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
        
        # Decrypt data if encrypted
        if data.get('encrypted'):
            data = request_encryption.decrypt_sensor_data(data)
        
        # Process sensor data
        result = process_sensor_data(data, format='json')
        
        # Emit real-time update via WebSocket
        socketio.emit('sensor_update', {
            'device_id': data.get('device_id'),
            'location': data.get('location'),
            'readings': data.get('readings'),
            'timestamp': datetime.utcnow().isoformat(),
            'authenticated': True
        })
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error processing JSON sensor data: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/sensor-data/gateway', methods=['POST'])
@require_gateway_auth
def receive_gateway_data():
    """Receive sensor data from gateway with authentication"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        logger.info(f"Received gateway data from {data.get('device_id')} (gateway processed)")
        
        # Persist gateway log
        db.store_gateway_log({
            'device_id': data.get('device_id'),
            'location': data.get('location'),
            'timestamp': datetime.utcnow(),
            'original_count': len(data.get('readings', [])) + data.get('gateway_stats', {}).get('outliers_removed', 0),
            'filtered_count': len(data.get('readings', [])),
            'outliers_detected': data.get('gateway_stats', {}).get('outliers_removed', 0),
            'outlier_details': data.get('gateway_stats', {}).get('outlier_details', [])
        })
        
        # Process gateway-filtered data
        result = process_sensor_data(data, format='json')
        
        # Emit real-time update via WebSocket
        socketio.emit('sensor_update', {
            'device_id': data.get('device_id'),
            'location': data.get('location'),
            'readings': data.get('readings'),
            'timestamp': datetime.utcnow().isoformat(),
            'gateway_processed': True,
            'gateway_stats': data.get('gateway_stats', {})
        })
        
        return jsonify({
            'status': 'success',
            'readings_processed': len(data.get('readings', [])),
            'gateway_stats': data.get('gateway_stats', {})
        })
        
    except Exception as e:
        logger.error(f"Error processing gateway data: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/device/token', methods=['POST'])
@require_api_key
def generate_device_token():
    """Generate JWT token for device authentication"""
    try:
        data = request.get_json()
        device_id = data.get('device_id')
        
        if not device_id:
            return jsonify({'error': 'Device ID required'}), 400
        
        if device_id not in Config.DEVICE_KEYS:
            return jsonify({'error': 'Unknown device'}), 404
        
        token = security_manager.generate_device_token(device_id)
        
        logger.info(f"Generated token for device: {device_id}")
        
        return jsonify({
            'token': token,
            'device_id': device_id,
            'expires_in': Config.JWT_EXPIRATION_HOURS * 3600  # seconds
        })
        
    except Exception as e:
        logger.error(f"Error generating device token: {e}", exc_info=True)
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
    
    # ML-assisted decisions
    ml_commands = ml_manager.predict_commands(device_id, location, readings_data)
    
    # Rule-based decisions
    rule_commands = decision_engine.process_sensor_data(data)
    
    commands = ml_commands + rule_commands
    
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
            condition='ml_and_rules',
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


def _get_recent_dataframes(hours: int = 24):
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    readings = list(db.sensor_readings.find({'timestamp': {'$gte': cutoff}}))
    commands = list(db.actuator_commands.find({'timestamp': {'$gte': cutoff}}))
    gateway_logs = list(db.gateway_logs.find({'timestamp': {'$gte': cutoff}}))
    reading_rows = []
    for r in readings:
        for rd in r.get('readings', []):
            reading_rows.append({
                'timestamp': r.get('timestamp'),
                'device_id': r.get('device_id'),
                'location': r.get('location'),
                'sensor_type': rd.get('sensor_type'),
                'value': rd.get('value'),
                'unit': rd.get('unit'),
                'format': r.get('format'),
                'gateway_processed': r.get('gateway_processed', False)
            })
    import pandas as pd
    df_readings = pd.DataFrame(reading_rows)
    df_commands = pd.DataFrame(commands)
    df_gateway = pd.DataFrame(gateway_logs)
    return df_readings, df_commands, df_gateway

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
@require_api_key
def control_actuator(actuator_id: str):
    """Manually control an actuator"""
    try:
        data = request.get_json()
        state = data.get('state')
        value = data.get('value')
        
        if actuator_id not in actuator_states:
            return jsonify({'error': 'Actuator not found'}), 404
        
        # Set manual override to prevent automated rules from overriding
        decision_engine.set_manual_override(actuator_id)
        
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
        
        logger.info(f"Manual control: {actuator_id} set to {state} (override active for 1 hour)")
        
        return jsonify({
            'status': 'success',
            'actuator': actuator_states[actuator_id].to_dict(),
            'manual_override': True,
            'override_expires_in_seconds': 3600
        })
        
    except Exception as e:
        logger.error(f"Error controlling actuator: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/status', methods=['GET'])
@require_api_key
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

@app.route('/api/analytics/summary', methods=['GET'])
def analytics_summary():
    """Descriptive analytics summary"""
    try:
        hours = int(request.args.get('hours', 24))
        sensor_summary = db.get_sensor_aggregate_summary(hours)
        actuator_usage = db.get_actuator_usage(hours)
        decision_summary = db.get_decision_summary(hours)
        gateway_stats = db.get_gateway_statistics(hours)
        model_status = ml_manager.get_status()
        return jsonify({
            'sensor_summary': sensor_summary,
            'actuator_usage': actuator_usage,
            'decision_summary': decision_summary,
            'gateway_statistics': gateway_stats,
            'model_status': model_status
        })
    except Exception as e:
        logger.error(f"Error in analytics summary: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics/export', methods=['GET'])
def analytics_export():
    """Export recent sensor and actuator data as CSV"""
    try:
        import pandas as pd
        hours = int(request.args.get('hours', 24))
        df_readings, df_commands, _ = _get_recent_dataframes(hours)
        csv_readings = df_readings.to_csv(index=False)
        csv_commands = df_commands.to_csv(index=False)
        return jsonify({
            'readings_csv': csv_readings,
            'commands_csv': csv_commands
        })
    except Exception as e:
        logger.error(f"Error exporting analytics: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics/export/xlsx', methods=['GET'])
def analytics_export_xlsx():
    """Export recent sensor and actuator data as XLSX (base64)"""
    try:
        import pandas as pd
        hours = int(request.args.get('hours', 24))
        df_readings, df_commands, df_gateway = _get_recent_dataframes(hours)
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            df_readings.to_excel(writer, index=False, sheet_name="readings")
            df_commands.to_excel(writer, index=False, sheet_name="commands")
            df_gateway.to_excel(writer, index=False, sheet_name="gateway_logs")
        buffer.seek(0)
        b64 = base64.b64encode(buffer.read()).decode('utf-8')
        return jsonify({'xlsx_base64': b64})
    except Exception as e:
        logger.error(f"Error exporting XLSX: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics/export/parquet', methods=['GET'])
def analytics_export_parquet():
    """Export recent sensor and actuator data as Parquet (base64)"""
    try:
        hours = int(request.args.get('hours', 24))
        df_readings, df_commands, df_gateway = _get_recent_dataframes(hours)
        buf_readings = io.BytesIO()
        buf_commands = io.BytesIO()
        buf_gateway = io.BytesIO()
        df_readings.to_parquet(buf_readings, index=False)
        df_commands.to_parquet(buf_commands, index=False)
        df_gateway.to_parquet(buf_gateway, index=False)
        buf_readings.seek(0)
        buf_commands.seek(0)
        buf_gateway.seek(0)
        return jsonify({
            'readings_parquet_base64': base64.b64encode(buf_readings.read()).decode('utf-8'),
            'commands_parquet_base64': base64.b64encode(buf_commands.read()).decode('utf-8'),
            'gateway_parquet_base64': base64.b64encode(buf_gateway.read()).decode('utf-8')
        })
    except Exception as e:
        logger.error(f"Error exporting Parquet: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics/charts', methods=['GET'])
def analytics_charts():
    """Return simple descriptive charts as base64 PNG"""
    try:
        hours = int(request.args.get('hours', 24))
        df_readings, df_commands, _ = _get_recent_dataframes(hours)
        charts = {}

        if not df_readings.empty:
            # Average value per sensor type
            plt.clf()
            agg = df_readings.groupby('sensor_type')['value'].mean().sort_values()
            agg.plot(kind='bar', title=f'Avg sensor values (last {hours}h)')
            buf = io.BytesIO()
            plt.tight_layout()
            plt.savefig(buf, format='png')
            buf.seek(0)
            charts['sensor_avg'] = base64.b64encode(buf.read()).decode('utf-8')

        if not df_commands.empty:
            plt.clf()
            agg_cmd = df_commands.groupby('actuator_id')['state'].count().sort_values()
            agg_cmd.plot(kind='bar', title=f'Actuator command counts (last {hours}h)')
            buf2 = io.BytesIO()
            plt.tight_layout()
            plt.savefig(buf2, format='png')
            buf2.seek(0)
            charts['actuator_counts'] = base64.b64encode(buf2.read()).decode('utf-8')

        return jsonify({'charts': charts})
    except Exception as e:
        logger.error(f"Error generating charts: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/ml/status', methods=['GET'])
def ml_status():
    """Get ML model status"""
    try:
        return jsonify(ml_manager.get_status())
    except Exception as e:
        logger.error(f"Error getting ML status: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/ml/train', methods=['POST'])
def ml_train():
    """Trigger ML retraining"""
    try:
        hours = int(request.json.get('hours', 168)) if request.is_json else 168
        status = ml_manager.train_from_db(hours=hours)
        return jsonify(status)
    except Exception as e:
        logger.error(f"Error training ML model: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/ml/drift', methods=['GET'])
def ml_drift():
    """Run drift check on recent data window"""
    try:
        hours = int(request.args.get('hours', 24))
        status = ml_manager.check_drift(hours=hours)
        return jsonify(status)
    except Exception as e:
        logger.error(f"Error checking drift: {e}", exc_info=True)
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

@app.route('/api/sensors/<device_id>/<sensor_type>/override', methods=['POST', 'DELETE'])
def control_sensor_override(device_id: str, sensor_type: str):
    """Set or clear manual override for a specific sensor"""
    try:
        if request.method == 'POST':
            data = request.get_json()
            value = data.get('value')
            
            # Send command to sensor service to set manual override
            # For now, just emit via WebSocket so sensor service can listen
            socketio.emit('sensor_manual_override', {
                'device_id': device_id,
                'sensor_type': sensor_type,
                'value': value,
                'action': 'set'
            })
            
            logger.info(f"Manual override set: {device_id}/{sensor_type} = {value}")
            
            return jsonify({
                'status': 'success',
                'device_id': device_id,
                'sensor_type': sensor_type,
                'value': value,
                'manual_override': True
            })
        
        elif request.method == 'DELETE':
            # Clear manual override
            socketio.emit('sensor_manual_override', {
                'device_id': device_id,
                'sensor_type': sensor_type,
                'action': 'clear'
            })
            
            logger.info(f"Manual override cleared: {device_id}/{sensor_type}")
            
            return jsonify({
                'status': 'success',
                'device_id': device_id,
                'sensor_type': sensor_type,
                'manual_override': False
            })
        
    except Exception as e:
        logger.error(f"Error controlling sensor override: {e}", exc_info=True)
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


def _schedule_ml(interval_hours: int = 24):
    """Background scheduler for periodic ML retrain + drift check."""
    global ml_scheduler
    try:
        ml_manager.train_from_db(hours=168, train_interval_hours=interval_hours)
        ml_manager.check_drift(hours=24)
    except Exception as exc:
        logger.error("Scheduled ML task failed: %s", exc, exc_info=True)
    # reschedule
    ml_scheduler = threading.Timer(interval_hours * 3600, _schedule_ml, args=[interval_hours])
    ml_scheduler.daemon = True
    ml_scheduler.start()

def main():
    """Main entry point"""
    logger.info("Starting IoT Smart Home Controller")
    logger.info(f"MongoDB: {Config.MONGODB_DATABASE}")
    logger.info(f"Host: {Config.CONTROLLER_HOST}:{Config.CONTROLLER_PORT}")
    logger.info(f"Using API Key: {Config.API_KEY[:20]}... (length: {len(Config.API_KEY)})")
    
    # Kick off periodic ML lifecycle (daily by default)
    _schedule_ml(interval_hours=24)
    
    try:
        # Configure SSL if enabled
        ssl_context = None
        if Config.SSL_ENABLED:
            import ssl
            # Convert to absolute paths
            cert_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', Config.SSL_CERT_PATH))
            key_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', Config.SSL_KEY_PATH))
            
            ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            ssl_context.load_cert_chain(
                certfile=cert_path,
                keyfile=key_path
            )
            logger.info(f"SSL/TLS enabled with certificate: {cert_path}")
        
        socketio.run(
            app,
            host=Config.CONTROLLER_HOST,
            port=Config.CONTROLLER_PORT,
            debug=False,
            allow_unsafe_werkzeug=True,
            ssl_context=ssl_context
        )
    except KeyboardInterrupt:
        logger.info("Shutting down controller")
        if ml_scheduler:
            ml_scheduler.cancel()
        db.close()
    except Exception as e:
        logger.error(f"Error running controller: {e}", exc_info=True)
        if ml_scheduler:
            ml_scheduler.cancel()
        db.close()


if __name__ == '__main__':
    main()
