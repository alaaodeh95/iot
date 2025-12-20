# IoT Smart Home Simulation System

A comprehensive IoT simulation system demonstrating smart home automation with real-time sensor monitoring, intelligent decision-making, machine learning, and actuator control.

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Components & Files](#components--files)
- [Features Implementation](#features-implementation)
- [Prerequisites](#prerequisites)
- [Installation & Setup](#installation--setup)
- [Usage](#usage)
- [API Documentation](#api-documentation)
- [Configuration](#configuration)
- [Security](#security)
- [Technologies](#technologies)

---

## 🎯 Overview

This project implements a complete IoT smart home system that fulfills university project requirements including:

- **Phase 1**: Basic IoT simulation with sensors, controller, and actuators
- **Phase 2**: Advanced features including ML model, data analytics, gateway filtering, and multi-format communication

The system simulates 20+ sensor types across 7 devices, processes data through an intelligent gateway, makes decisions using both rule-based logic and machine learning, and controls 11 different actuators.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    SENSOR LAYER                              │
│  7 Devices × Multiple Sensors = 20+ Sensor Types            │
│  • Roof Station (JSON via Gateway)                          │
│  • Living Room, Kitchen, Bedroom (JSON)                     │
│  • Dust Cleaner (XML/SOAP)                                  │
│  • Basement, Entrance (JSON)                                │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    GATEWAY LAYER                             │
│  • IQR-based Outlier Detection                              │
│  • Statistical Filtering                                     │
│  • Data Quality Assurance                                    │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                  CONTROLLER LAYER                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  REST API    │  │  WebSocket   │  │   Security   │     │
│  │  (Flask)     │  │  (SocketIO)  │  │  (JWT/Auth)  │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Decision   │  │  ML Model    │  │   Database   │     │
│  │   Engine     │  │  Manager     │  │  (MongoDB)   │     │
│  │ (Rule-based) │  │ (Predictive) │  │              │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                   ACTUATOR LAYER                             │
│  11 Actuators: HVAC, Lights, Fans, Alarms, etc.            │
└─────────────────────────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    UI LAYER                                  │
│  React Dashboard with Real-time Monitoring & Control        │
└─────────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
iot/
│
├── backend/                          # Backend Controller Service
│   ├── config.py                     # System configuration & settings
│   ├── requirements.txt              # Python dependencies
│   ├── security.py                   # Security implementation (JWT, encryption)
│   │
│   ├── models/                       # Data Models
│   │   ├── __init__.py              # Model exports
│   │   └── sensor_data.py           # Sensor/Actuator data models
│   │
│   └── controller/                   # Main Controller
│       ├── main.py                   # Flask REST API & WebSocket server
│       ├── database.py               # MongoDB manager & analytics
│       ├── decision_engine.py        # Rule-based decision logic
│       └── ml_model.py              # ML model lifecycle management
│
├── sensors/                          # Sensor Service
│   ├── requirements.txt              # Python dependencies
│   ├── main_service.py              # Main sensor orchestrator
│   ├── sensor_simulator.py          # 20+ sensor implementations
│   └── gateway.py                   # Outlier filtering gateway
│
├── ui/                              # React Frontend
│   ├── package.json                 # Node dependencies
│   ├── vite.config.ts               # Vite build configuration
│   ├── tsconfig.json                # TypeScript configuration
│   ├── index.html                   # HTML entry point
│   │
│   └── src/
│       ├── main.tsx                 # React entry point
│       ├── App.tsx                  # Main application component
│       │
│       ├── types/                   # TypeScript Types
│       │   └── index.ts             # Type definitions
│       │
│       ├── services/                # API Services
│       │   ├── api.ts               # REST API client
│       │   ├── socket.ts            # WebSocket client
│       │   ├── connection.ts        # Connection management
│       │   └── security.ts          # Security utilities
│       │
│       ├── components/              # React Components
│       │   ├── SensorCard.tsx       # Sensor display & control
│       │   ├── ActuatorCard.tsx     # Actuator display & control
│       │   └── SecurityStatus.tsx   # Security status display
│       │
│       ├── styles/                  # Styling
│       └── utils/                   # Utilities
│           └── securityTest.ts      # Security testing
│
├── model_store/                     # ML Model Storage
│   └── hvac_model.pkl              # Trained ML model
│
├── certs/                           # SSL Certificates (optional)
│   ├── server.crt
│   └── server.key
│
├── .env                             # Environment variables (generated)
├── .gitignore                       # Git ignore rules
├── security_setup.py                # Security initialization script
├── test_security.py                 # Security test suite
├── test_security_simple.py          # Simple security tests
├── Project Requirments.md           # Project requirements
├── SECURITY.md                      # Security documentation
└── README.md                        # This file
```

---

## 🔧 Components & Files

### 1. Sensor Layer

#### **`sensors/sensor_simulator.py`** (851 lines)
**Purpose**: Implements all sensor types with realistic data generation

**Contains**:
- `BaseSensor` - Abstract base class for all sensors
- 20+ Sensor Classes:
  - `TemperatureSensor` - Temperature readings (15-40°C)
  - `HumiditySensor` - Humidity levels (20-80%)
  - `PressureSensor` - Atmospheric pressure (980-1040 hPa)
  - `LightSensor` - Light intensity (0-1000 lux)
  - `MotionSensor` - PIR motion detection (boolean)
  - `CO2Sensor` - CO2 concentration (400-2000 ppm)
  - `GasSensor` - Gas detection (0-2000 ppm)
  - `SmokeSensor` - Smoke detection (boolean)
  - `DistanceSensor` - Ultrasonic distance (0-300 cm)
  - `DoorSensor` - Door/window contact (boolean)
  - `WaterLeakSensor` - Water leak detection (boolean)
  - `RFIDSensor` - RFID tag reader (string)
  - `SignalStrengthSensor` - Signal strength (-90 to -30 dBm)
  - `SoundSensor` - Sound level (30-100 dB)
  - `VibrationSensor` - Vibration detection (0-1 g)
  - `EnergySensor` - Power consumption (0-2000 W)
  - `UVSensor` - UV index (0-11)
  - `RainSensor` - Rain detection (boolean)
  - `GlassBreakSensor` - Glass break detection (boolean)
  - `PressureMatSensor` - Floor pressure (boolean)
  - `ObjectDetectionSensor` - Camera-based object detection (string)
- `SensorDevice` - Device with multiple sensors

**Key Features**:
- Realistic value generation with trends and noise
- Manual value override for testing
- Sensor grouping by device
- Configurable ranges from `backend/config.py`

---

#### **`sensors/main_service.py`** (455 lines)
**Purpose**: Main sensor service that orchestrates all sensor devices

**Contains**:
- `SensorService` - Main service coordinator
- Device initialization from configuration
- Multi-threaded sensor reading (one thread per device)
- **JSON data transmission** (for most sensors)
- **XML/SOAP data transmission** (for dust cleaner)
- Gateway integration for outlier filtering
- Security features:
  - JWT device authentication
  - Token refresh mechanism
  - Request signing
  - Data encryption (optional)

**Key Functions**:
- `_initialize_devices()` - Set up all sensor devices
- `_authenticate_devices()` - Obtain JWT tokens
- `_send_json_data()` - Send JSON-formatted data
- `_send_xml_data()` - Send XML/SOAP-formatted data
- `_inject_outlier()` - Test gateway with outliers

**Data Formats**:
1. **JSON** (Example: Roof Station)
```json
{
  "device_id": "roof_station",
  "location": "roof",
  "readings": [
    {"sensor_type": "temperature", "value": 23.5, "unit": "°C"},
    {"sensor_type": "humidity", "value": 55.2, "unit": "%"},
    {"sensor_type": "pressure", "value": 1013.2, "unit": "hPa"}
  ],
  "timestamp": "2025-12-19T14:42:00.000Z"
}
```

2. **XML/SOAP** (Example: Dust Cleaner)
```xml
<sensor_data>
  <device_id>dust_cleaner</device_id>
  <location>living_room</location>
  <timestamp>2025-12-19T14:42:00.000Z</timestamp>
  <sensors>
    <sensor>
      <type>distance</type>
      <value>125.5</value>
      <unit>cm</unit>
      <object_name>chair</object_name>
    </sensor>
    <sensor>
      <type>signal_strength</type>
      <value>-45.3</value>
      <unit>dBm</unit>
    </sensor>
  </sensors>
</sensor_data>
```

---

#### **`sensors/gateway.py`** (196 lines)
**Purpose**: Intermediate tier that filters outliers before forwarding to controller

**Contains**:
- `SensorGateway` - Gateway for data quality assurance
- IQR (Interquartile Range) outlier detection
- Sliding window for historical values
- Range-based validation
- Gateway statistics tracking

**Key Functions**:
- `process_sensor_data()` - Main processing pipeline
- `_is_outlier()` - Multi-method outlier detection
  - Range check (hard limits)
  - IQR method (statistical)
- `_update_window()` - Maintain sliding window
- `get_statistics()` - Gateway performance metrics

**Outlier Detection Methods**:
1. **Range Check**: Hard limits (e.g., temp must be -20 to 50°C)
2. **IQR Method**: Q1 - 1.5×IQR to Q3 + 1.5×IQR

**Configuration** (in `backend/config.py`):
```python
OUTLIER_DETECTION = {
    'enabled': True,
    'method': 'iqr',
    'window_size': 20,
    'multiplier': 1.5,
    'ranges': {...}
}
```

---

### 2. Controller Layer

#### **`backend/controller/main.py`** (804 lines)
**Purpose**: Central controller with REST API, WebSocket, and orchestration

**Contains**:
- Flask REST API server
- Flask-SocketIO WebSocket server
- Request routing and handling
- Security middleware
- ML model scheduler

**REST API Endpoints**:

| Endpoint | Method | Purpose | Authentication |
|----------|--------|---------|----------------|
| `/` | GET | API information | None |
| `/api/sensor-data` | POST | Receive JSON sensor data | JWT Device Token |
| `/api/sensor-data/xml` | POST | Receive XML sensor data | None |
| `/api/sensor-data/gateway` | POST | Receive gateway-filtered data | Gateway Key |
| `/api/device/token` | POST | Generate device JWT token | API Key |
| `/api/actuators` | GET | Get all actuator statuses | None |
| `/api/actuators/<id>` | POST | Control actuator manually | API Key |
| `/api/status` | GET | Get system status | API Key |
| `/api/statistics` | GET | Get sensor statistics | None |
| `/api/decisions` | GET | Get recent decisions | None |
| `/api/sensor-override` | POST | Manual sensor injection | None |
| `/api/sensors/config` | GET | Get sensor configuration | None |
| `/api/analytics/summary` | GET | Descriptive analytics | None |
| `/api/analytics/export` | GET | Export CSV data | None |
| `/api/analytics/export/xlsx` | GET | Export Excel data | None |
| `/api/analytics/export/parquet` | GET | Export Parquet data | None |
| `/api/analytics/charts` | GET | Generate charts (PNG base64) | None |
| `/api/ml/status` | GET | ML model status | None |
| `/api/ml/train` | POST | Trigger ML retraining | None |
| `/api/ml/drift` | GET | Check data drift | None |

**WebSocket Events**:
- `connect` - Client connected
- `disconnect` - Client disconnected
- `request_status` - Request system status
- `sensor_update` - Real-time sensor data (emitted)
- `actuator_update` - Actuator state change (emitted)
- `decision_made` - Decision logged (emitted)

**Key Functions**:
- `receive_sensor_data_json()` - Process JSON sensor data
- `receive_sensor_data_xml()` - Process XML sensor data
- `receive_gateway_data()` - Process gateway-filtered data
- `process_sensor_data()` - Main processing pipeline
- `execute_actuator_command()` - Execute actuator commands
- `_schedule_ml()` - Background ML retraining scheduler

---

#### **`backend/controller/decision_engine.py`** (658 lines)
**Purpose**: Rule-based decision making for smart home automation

**Contains**:
- `DecisionEngine` - Rule processor
- 20+ decision rules
- Multi-sensor correlation logic
- Actuator state management
- Alert cooldown system

**Decision Rules** (by sensor type):

| Sensor | Condition | Action |
|--------|-----------|--------|
| Temperature | > 30°C | HVAC → Cooling |
| Temperature | < 18°C | HVAC → Heating |
| Temperature | 18-30°C | HVAC → Off/Fan |
| Humidity | > 70% (basement) | Dehumidifier → On |
| Light | < 200 lux + motion | Lights → On (80%) |
| Light | > 600 lux | Lights → Off |
| Motion | Detected + dark | Lights → On |
| Motion | Timeout (5 min) | Lights → Off |
| CO2 | > 1500 ppm | HVAC → Fan Only |
| CO2 | > 1000 ppm (kitchen) | Kitchen Exhaust → High |
| Gas | > 1500 ppm | Gas Alarm + Exhaust |
| Smoke | Detected | Fire Alarm + HVAC Off |
| Distance | < 50 cm | Dust Cleaner → Pause |
| Water Leak | Detected | Water Shutoff → Close |
| Door | Open (entrance) | Entrance Lights → On |
| Sound | > 80 dB | Siren → On |
| Vibration | > 0.5g | Siren → On |
| Energy | > 1800W | Smart Plug → Off |
| UV | > 8 | Shutters → Closed |
| Rain | Detected | Shutters → Closed |
| Glass Break | Detected | Siren → On |

**Cross-Sensor Intelligence**:
- Kitchen Safety: High temp + gas → Emergency exhaust
- Entrance Security: Motion + door + no RFID → Security alert
- Trend Analysis: Historical data for smart predictions

**Key Functions**:
- `process_sensor_data()` - Main entry point
- `_process_temperature()` - Temperature rules
- `_process_motion()` - Motion-based automation
- `_process_co2()` - Air quality management
- `_cross_sensor_decisions()` - Multi-sensor logic
- `_has_recent_motion()` - Motion timeout check
- `_can_send_alert()` - Alert cooldown

---

#### **`backend/controller/ml_model.py`** (242 lines)
**Purpose**: Machine learning model lifecycle management

**Contains**:
- `MLModelManager` - ML operations
- RandomForestClassifier for HVAC control
- Model training from historical data
- Model versioning and persistence
- Drift detection
- Automatic retraining scheduler

**ML Model Details**:
- **Algorithm**: RandomForestClassifier (80 trees, max depth 6)
- **Features**: Temperature, Humidity, CO2
- **Target**: HVAC state (off, fan_only, cooling, heating)
- **Training Data**: Historical actuator commands + sensor context
- **Fallback**: Synthetic data generation if insufficient history
- **Metrics**: F1 score (macro average)

**Key Functions**:
- `train_from_db()` - Train model from MongoDB data
  - Window: 168 hours (7 days)
  - Minimum samples: 20 (else synthetic)
  - Train/validation split: 80/20
  - Saves to `model_store/hvac_model.pkl`
  
- `check_drift()` - Monitor data drift
  - Method: Z-score comparison
  - Window: 24 hours
  - Baseline: Training data statistics
  - Threshold: Configurable multiplier
  
- `predict_commands()` - Make predictions
  - Input: Current sensor readings
  - Output: Actuator commands
  - Fallback: Heuristic rules if model unavailable
  
- `get_status()` - Model metadata
  - Version, training date, samples
  - F1 score, drift score
  - Next retrain schedule

**Model Lifecycle**:
```
1. Initial Training → 2. Deploy → 3. Monitor (Drift) → 4. Retrain (24h)
```

**Status Example**:
```json
{
  "loaded": true,
  "last_trained": "2025-12-19T12:00:00",
  "samples": 1250,
  "f1": 0.87,
  "version": 3,
  "drift_score": 0.15,
  "drift_checked_at": "2025-12-19T14:00:00",
  "next_retrain_at": "2025-12-20T12:00:00"
}
```

---

#### **`backend/controller/database.py`** (450+ lines)
**Purpose**: MongoDB interface and data analytics

**Contains**:
- `DatabaseManager` - MongoDB operations
- CRUD operations for all collections
- Aggregation queries for analytics
- Data export functions

**MongoDB Collections**:

1. **sensor_readings**
   - All sensor data with timestamps
   - Device ID, location, readings array
   - Format indicator (json/xml)
   - Gateway processed flag

2. **actuator_commands**
   - History of all commands
   - Actuator ID, state, value
   - Reason, triggered_by
   - Timestamp

3. **actuator_status**
   - Current state of each actuator
   - Last updated timestamp

4. **decision_logs**
   - Automated decisions made
   - Trigger sensor/value
   - Condition applied
   - Actions taken

5. **gateway_logs**
   - Gateway processing statistics
   - Outliers detected/removed
   - Outlier details

6. **system_logs**
   - General system events

**Key Functions**:
- `store_sensor_group()` - Save sensor readings
- `store_actuator_command()` - Log commands
- `update_actuator_status()` - Update states
- `store_decision_log()` - Log decisions
- `store_gateway_log()` - Gateway statistics
- `get_sensor_statistics()` - Aggregate sensor data
- `get_sensor_aggregate_summary()` - Descriptive analytics
- `get_actuator_usage()` - Actuator usage stats
- `get_gateway_statistics()` - Gateway performance
- `get_system_overview()` - System health

**Analytics Capabilities**:
- Descriptive statistics (mean, min, max, std)
- Time-series aggregation
- Export to CSV, Excel, Parquet
- Chart generation (matplotlib)

---

#### **`backend/security.py`** (400+ lines)
**Purpose**: Comprehensive security implementation

**Contains**:
- `SecurityManager` - Main security coordinator
- `RequestEncryption` - Data encryption
- Authentication decorators
- Security utilities

**Security Features**:

1. **Authentication**
   - JWT tokens for devices (24h expiration)
   - API keys for system access
   - Gateway authentication keys
   - Device-specific keys

2. **Authorization**
   - Role-based access control
   - Endpoint-level permissions
   - Device identity verification

3. **Data Protection**
   - AES encryption (optional)
   - HMAC-SHA256 request signing
   - SSL/TLS support

4. **Rate Limiting**
   - Configurable per endpoint
   - Token bucket algorithm
   - Abuse prevention

**Decorators**:
- `@require_api_key` - API key validation
- `@require_device_auth` - JWT device token
- `@require_gateway_auth` - Gateway key
- `@add_security_headers` - Security headers

**Key Functions**:
- `generate_device_token()` - Create JWT
- `verify_device_token()` - Validate JWT
- `verify_api_key()` - Check API key
- `sign_request()` - HMAC signature
- `verify_signature()` - Verify signature
- `encrypt_sensor_data()` - AES encryption
- `decrypt_sensor_data()` - AES decryption

---

#### **`backend/config.py`** (500+ lines)
**Purpose**: Centralized configuration

**Contains**:
- System settings
- Sensor configurations
- Actuator definitions
- Decision rule thresholds
- Security settings

**Key Configurations**:

1. **Sensors** (7 devices):
```python
SENSORS = {
    'roof_station': {
        'location': 'roof',
        'sensors': ['temperature', 'humidity', 'pressure'],
        'type': 'json',
        'gateway_enabled': True,
        'update_interval': 5.0
    },
    # ... 6 more devices
}
```

2. **Actuators** (11 types):
```python
ACTUATORS = {
    'hvac_system': {
        'type': 'climate_control',
        'location': 'whole_house',
        'states': ['off', 'fan_only', 'cooling', 'heating']
    },
    # ... 10 more actuators
}
```

3. **Decision Rules**:
```python
DECISION_RULES = {
    'temperature': {
        'low_threshold': 18,
        'high_threshold': 28,
        'critical_high': 40
    },
    # ... rules for all sensor types
}
```

4. **Outlier Detection**:
```python
OUTLIER_DETECTION = {
    'enabled': True,
    'method': 'iqr',
    'window_size': 20,
    'multiplier': 1.5,
    'ranges': {
        'temperature': {'min': -20, 'max': 50},
        # ... ranges for all sensors
    }
}
```

---

### 3. Frontend Layer

#### **`ui/src/App.tsx`** (350+ lines)
**Purpose**: Main React application

**Contains**:
- Application layout
- Real-time data management
- WebSocket connection
- State management

**Key Features**:
- Material-UI dark theme
- Responsive grid layout
- Real-time updates via WebSocket
- Connection status indicator
- Error handling

**Components Used**:
- `SensorCard` - Display sensors
- `ActuatorCard` - Display actuators
- `SecurityStatus` - Security info
- System statistics display

---

#### **`ui/src/components/SensorCard.tsx`** (250+ lines)
**Purpose**: Sensor display and manual control

**Features**:
- Real-time value updates
- Color-coded status indicators
- Manual value override with sliders
- Format badges (JSON/XML)
- Gateway processing indicator
- Unit display

**Status Colors**:
- 🟢 Green: Normal
- 🟡 Yellow: Warning
- 🔴 Red: Critical

---

#### **`ui/src/components/ActuatorCard.tsx`** (150+ lines)
**Purpose**: Actuator display and control

**Features**:
- Current state display
- Manual toggle controls
- Last updated timestamp
- State-based styling
- Loading indicators

---

#### **`ui/src/services/api.ts`** (200+ lines)
**Purpose**: REST API client

**Functions**:
- `getActuators()` - Fetch actuators
- `controlActuator()` - Manual control
- `getSystemStatus()` - System health
- `getStatistics()` - Analytics
- `getDecisions()` - Decision history
- `overrideSensor()` - Manual injection
- `getSensorConfig()` - Sensor setup

---

#### **`ui/src/services/socket.ts`** (100+ lines)
**Purpose**: WebSocket client

**Events Handled**:
- `sensor_update` - Live sensor data
- `actuator_update` - State changes
- `decision_made` - Automation logs
- `connection_response` - Handshake
- `connect` / `disconnect` - Status

---

### 4. Supporting Files

#### **`backend/models/sensor_data.py`** (200+ lines)
**Purpose**: Data models and schemas

**Classes**:
- `SensorReading` - Individual sensor reading
- `SensorGroup` - Device with multiple sensors
- `ActuatorCommand` - Command to actuator
- `ActuatorStatus` - Current actuator state
- `DecisionLog` - Automated decision record

**Methods**:
- `to_dict()` - Convert to dictionary
- `to_mongo()` - MongoDB document format
- `from_mongo()` - Parse from MongoDB

---

#### **`security_setup.py`** (150+ lines)
**Purpose**: Initial security setup

**Actions**:
- Generate cryptographic keys
- Create `.env` file
- Generate SSL certificates (optional)
- Create device keys
- Generate `SECURITY.md` documentation

---

#### **`test_security.py`** & **`test_security_simple.py`**
**Purpose**: Security testing

**Tests**:
- API key validation
- JWT token generation/verification
- Device authentication
- Gateway authentication
- Rate limiting
- Request signing
- Encryption/decryption

---

## 🎯 Features Implementation

### Phase 1 Requirements ✅

| Requirement | Implementation | Files |
|------------|----------------|-------|
| 3+ Sensor Types | 20+ sensor types | `sensors/sensor_simulator.py` |
| Random Value Generation | Realistic algorithms | `sensors/sensor_simulator.py` (lines 45-425) |
| Central Controller | Flask REST API | `backend/controller/main.py` |
| Decision Rules | 20+ automation rules | `backend/controller/decision_engine.py` |
| 2+ Actuators | 11 actuator types | `backend/config.py` (lines 150-250) |
| Console Logging | Comprehensive logs | All `.py` files |
| Modular Code | Separate classes | Project structure |
| Gateway Tier | Outlier filtering | `sensors/gateway.py` |
| JSON Format | Roof station | `sensors/main_service.py` (lines 220-280) |
| XML Format | Dust cleaner | `sensors/main_service.py` (lines 320-380) |

### Phase 2 Requirements ✅

| Requirement | Implementation | Files |
|------------|----------------|-------|
| Additional Sensors | 20 sensor types total | `sensors/sensor_simulator.py` |
| Multi-tier (Sensor→Gateway→Cloud) | Complete pipeline | `sensors/gateway.py`, `main_service.py` |
| Data Analytics | Descriptive analytics | `backend/controller/database.py` (lines 200-350) |
| Export Formats | CSV, Excel, Parquet | `backend/controller/main.py` (lines 550-650) |
| Visualization | Chart generation | `backend/controller/main.py` (lines 670-710) |
| ML Model | RandomForest HVAC control | `backend/controller/ml_model.py` |
| Model Training | From historical data | `ml_model.py` (lines 50-120) |
| Model Modification | Automatic retraining | `ml_model.py` (lines 122-145) |
| Drift Detection | Statistical monitoring | `ml_model.py` (lines 147-180) |
| Prescriptive Analysis | ML-guided decisions | `main.py` (lines 280-290) |

---

## 🚀 Prerequisites

- **Python**: 3.10 or higher
- **Node.js**: 18 or higher
- **MongoDB**: 4.4 or higher (running on port 27017)
- **pip**: Python package manager
- **npm**: Node package manager

---

## 📦 Installation & Setup

### 1. Clone Repository
```bash
git clone <repository-url>
cd iot
```

### 2. Security Setup (First Time)
```bash
python security_setup.py
```

This generates:
- `.env` file with API keys and JWT secrets
- Device authentication keys
- SSL certificates (optional)
- `SECURITY.md` documentation

### 3. Install Backend Dependencies
```bash
cd backend
pip install -r requirements.txt
cd ..
```

### 4. Install Sensor Dependencies
```bash
cd sensors
pip install -r requirements.txt
cd ..
```

### 5. Install UI Dependencies
```bash
cd ui
npm install
cd ..
```

### 6. Start MongoDB
```bash
# macOS with Homebrew
brew services start mongodb-community

# Or manually
mongod --dbpath /path/to/data
```

---

## 🎮 Usage

### Start All Services

**Terminal 1: Backend Controller**
```bash
cd backend/controller
python main.py
```
- Starts on `http://localhost:5000`
- REST API + WebSocket server
- Connects to MongoDB
- Initializes ML model

**Terminal 2: Sensor Service**
```bash
cd sensors
python main_service.py
```
- Starts 7 sensor devices
- Sends data every 3-5 seconds
- Uses JSON and XML formats
- Routes through gateway (roof station)

**Terminal 3: React UI**
```bash
cd ui
npm run dev
```
- Opens on `http://localhost:3000`
- Real-time dashboard
- Manual controls

### Demo Mode

For fixed cycles (non-continuous):
```python
# In backend/config.py
CONTINUOUS_MODE = False
FIXED_CYCLES = 20  # Run 20 cycles then stop
DEMO_MODE = True   # Verbose logging
```

---

## 📡 API Documentation

### Sensor Data Submission

**JSON Format:**
```bash
curl -X POST http://localhost:5000/api/sensor-data \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -d '{
    "device_id": "living_room",
    "location": "living_room",
    "readings": [
      {"sensor_type": "temperature", "value": 23.5, "unit": "°C"},
      {"sensor_type": "motion", "value": 1, "unit": "boolean"}
    ]
  }'
```

**XML Format:**
```bash
curl -X POST http://localhost:5000/api/sensor-data/xml \
  -H "Content-Type: application/xml" \
  -d '<sensor_data>
    <device_id>dust_cleaner</device_id>
    <location>living_room</location>
    <sensors>
      <sensor>
        <type>distance</type>
        <value>125</value>
        <unit>cm</unit>
      </sensor>
    </sensors>
  </sensor_data>'
```

### Manual Actuator Control

```bash
curl -X POST http://localhost:5000/api/actuators/hvac_system \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <YOUR_API_KEY>" \
  -d '{"state": "cooling"}'
```

### Get System Status

```bash
curl http://localhost:5000/api/status \
  -H "X-API-Key: <YOUR_API_KEY>"
```

### ML Model Operations

**Get Status:**
```bash
curl http://localhost:5000/api/ml/status
```

**Trigger Training:**
```bash
curl -X POST http://localhost:5000/api/ml/train \
  -H "Content-Type: application/json" \
  -d '{"hours": 168}'
```

**Check Drift:**
```bash
curl http://localhost:5000/api/ml/drift?hours=24
```

---

## ⚙️ Configuration

### Environment Variables (`.env`)

```bash
# API Keys
IOT_API_KEY=<generated>
JWT_SECRET_KEY=<generated>
GATEWAY_API_KEY=<generated>

# Device Keys
DEVICE_KEY_roof_station=<generated>
DEVICE_KEY_living_room=<generated>
# ... for each device

# Security
SSL_ENABLED=false
ENABLE_REQUEST_SIGNING=true
ENABLE_DATA_ENCRYPTION=false

# Server
CONTROLLER_HOST=0.0.0.0
CONTROLLER_PORT=5000
```

### MongoDB Configuration

```python
# backend/config.py
MONGODB_URI = "mongodb://localhost:27017/"
MONGODB_DATABASE = "IOT"
```

### Sensor Update Intervals

```python
# backend/config.py
SENSORS = {
    'roof_station': {
        'update_interval': 5.0,  # seconds
        # ...
    }
}
```

### Decision Rule Thresholds

```python
# backend/config.py
DECISION_RULES = {
    'temperature': {
        'low_threshold': 18,
        'high_threshold': 28,
        'critical_high': 40
    }
}
```

---

## 🔒 Security

### Authentication Flow

1. **Device Registration**: Each device has unique key in config
2. **Token Request**: Device requests JWT from `/api/device/token`
3. **Authenticated Requests**: Include JWT in `Authorization: Bearer <token>`
4. **Token Refresh**: Automatic refresh every hour

### Testing Security

```bash
# Run comprehensive tests
python test_security.py

# Run simple tests
python test_security_simple.py
```

### Security Best Practices

✅ Implemented:
- API key validation
- JWT token authentication
- Request signing (HMAC-SHA256)
- Optional data encryption (AES)
- Rate limiting
- Secure headers (CSP, HSTS, etc.)
- SSL/TLS support

See `SECURITY.md` for complete documentation.

---

## 🛠️ Technologies

### Backend
- **Flask** 3.0+ - Web framework
- **Flask-SocketIO** 5.3+ - WebSocket support
- **Flask-CORS** - Cross-origin requests
- **PyMongo** 4.6+ - MongoDB driver
- **PyJWT** 2.8+ - JWT tokens
- **scikit-learn** 1.4+ - Machine learning
- **pandas** 2.2+ - Data analysis
- **matplotlib** 3.8+ - Visualization
- **cryptography** 42.0+ - Encryption

### Sensors
- **requests** 2.31+ - HTTP client
- **xml.etree.ElementTree** - XML processing

### Frontend
- **React** 18.2+ - UI framework
- **TypeScript** 5.2+ - Type safety
- **Material-UI** 5.15+ - Components
- **Socket.io-client** 4.7+ - WebSocket
- **Axios** 1.6+ - HTTP client
- **Vite** 5.0+ - Build tool

### Database
- **MongoDB** 4.4+ - NoSQL database

---

## 📊 Monitoring & Debugging

### View Logs

**Backend:**
```bash
cd backend/controller
python main.py
# Watch console output
```

**Sensors:**
```bash
cd sensors
python main_service.py
# Watch console output
```

### MongoDB Data

```bash
# Connect to MongoDB
mongosh

# Switch to IOT database
use IOT

# View collections
show collections

# Query sensor readings
db.sensor_readings.find().limit(10)

# Query decisions
db.decision_logs.find().sort({timestamp: -1}).limit(5)
```

### WebSocket Monitoring

Open browser console while viewing UI to see WebSocket messages.

---

## 🧪 Testing

### Manual Sensor Override

**UI**: Use sliders on sensor cards

**API**:
```bash
curl -X POST http://localhost:5000/api/sensor-override \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "living_room",
    "location": "living_room",
    "readings": [
      {"sensor_type": "temperature", "value": 35, "unit": "°C"}
    ]
  }'
```

### Test Gateway Outlier Filtering

The system automatically injects occasional outliers (5% chance) for gateway testing.

Manual outlier:
```bash
curl -X POST http://localhost:5000/api/sensor-override \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "roof_station",
    "location": "roof",
    "readings": [
      {"sensor_type": "temperature", "value": 999, "unit": "°C"}
    ]
  }'
```

Gateway will filter this and log it.

### Test ML Model

```bash
# Check model status
curl http://localhost:5000/api/ml/status

# Force retrain
curl -X POST http://localhost:5000/api/ml/train

# Check drift
curl http://localhost:5000/api/ml/drift
```

---

## 📈 Data Analytics

### Export Data

**CSV Format:**
```bash
curl http://localhost:5000/api/analytics/export?hours=24 > data.json
# Extract CSV from JSON response
```

**Excel Format:**
```bash
curl http://localhost:5000/api/analytics/export/xlsx?hours=24 > data.json
# Base64 decode the xlsx_base64 field
```

**Parquet Format:**
```bash
curl http://localhost:5000/api/analytics/export/parquet?hours=24 > data.json
# Base64 decode the parquet fields
```

### Generate Charts

```bash
curl http://localhost:5000/api/analytics/charts?hours=24 > charts.json
# Base64 decode the PNG images
```

---

## 🐛 Troubleshooting

### MongoDB Connection Failed
```
Solution: Ensure MongoDB is running
brew services start mongodb-community
```

### WebSocket Not Connecting
```
Solution: Check CORS settings in backend/config.py
CORS_ORIGINS = ["http://localhost:3000"]
```

### No Sensor Data
```
Solution: Verify sensor service is running
cd sensors && python main_service.py
```

### JWT Token Expired
```
Solution: Tokens auto-refresh every hour
Or restart sensor service to get new tokens
```

### ML Model Not Loading
```
Solution: Train model first
curl -X POST http://localhost:5000/api/ml/train
```

---

## 📚 Additional Documentation

- **Project Requirements**: `Project Requirments.md`
- **Security Guide**: `SECURITY.md`
- **Sensor Specifications**: `sensors.pdf`
- **Sample Data**: `sensors-sample data.pdf`

---

## 👥 Contributors

IoT Smart Home Simulation System  
Educational Project for IoT Systems Understanding

---

## 📄 License

Educational Use Only

---

## 🎓 Educational Value

This project demonstrates:

1. **IoT Architecture**: Multi-tier sensor → gateway → controller → actuator
2. **Data Formats**: JSON and XML/SOAP communication
3. **Real-time Systems**: WebSocket for live updates
4. **Data Analytics**: Descriptive statistics and visualization
5. **Machine Learning**: Model training, deployment, monitoring, retraining
6. **Security**: Authentication, authorization, encryption
7. **Database Design**: NoSQL data modeling
8. **API Design**: RESTful endpoints
9. **Frontend Development**: React, TypeScript, Material-UI
10. **System Integration**: Multiple services working together

Perfect for understanding modern IoT system design and implementation!
