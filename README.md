# IoT Smart Home Simulation System

A comprehensive IoT simulation system demonstrating smart home automation with real-time sensor monitoring, intelligent decision-making, and actuator control.

## 🏗️ Architecture

The system consists of three main components:

1. **Backend Controller** (Python) - Main server with REST API, WebSocket, and MongoDB integration
2. **Sensor Service** (Python) - Simulates multiple sensor devices with JSON and XML communication
3. **React UI** (TypeScript) - Real-time dashboard with interactive controls

### Key Features

- ✅ **7 Sensor Devices** across different locations (roof, living room, kitchen, bedroom, basement, entrance, dust cleaner)
- ✅ **Multiple Sensor Types**: Temperature, humidity, pressure, light, motion, CO2, gas, smoke, water leak, door sensors, RFID, distance, and more
- ✅ **JSON & XML Communication**: Roof station uses JSON, dust cleaner uses XML/SOAP
- ✅ **Gateway with Outlier Filtering**: IQR-based outlier detection for data quality
- ✅ **Intelligent Decision Engine**: 20+ automation rules for smart home control
- ✅ **11 Actuators**: HVAC, lights, fans, alarms, locks, water shutoff, dehumidifier, and more
- ✅ **Real-time WebSocket Updates**: Instant UI updates for all changes
- ✅ **MongoDB Storage**: All sensor readings, decisions, and actuator commands stored
- ✅ **Interactive UI**: Manual sensor value overrides with sliders
- ✅ **Dark Theme Dashboard**: Modern, responsive interface with Material-UI

## 📋 Prerequisites

- Python 3.10 or higher
- Node.js 18 or higher
- MongoDB running locally on default port (27017)
- npm or yarn package manager

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Install backend dependencies
cd backend
pip install -r requirements.txt
cd ..

# Install sensor service dependencies
cd sensors
pip install -r requirements.txt
cd ..

# Install UI dependencies
cd ui
npm install
cd ..
```

### 2. Start MongoDB

Ensure MongoDB is running:
```bash
# On macOS with Homebrew
brew services start mongodb-community

# Or manually
mongod --dbpath /path/to/data/directory
```

### 3. Start the System

You need to run three services in separate terminals:

#### Terminal 1: Backend Controller
```bash
cd backend/controller
python main.py
```
Server will start on http://localhost:5000

#### Terminal 2: Sensor Service
```bash
cd sensors
python main_service.py
```
All sensor devices will start simulating and sending data

#### Terminal 3: React UI
```bash
cd ui
npm run dev
```
Dashboard will be available at http://localhost:3000

## 📊 System Components

### Backend Controller (Port 5000)

**REST API Endpoints:**
- `GET /` - API information
- `POST /api/sensor-data` - Receive sensor data (JSON)
- `POST /api/sensor-data/xml` - Receive sensor data (XML)
- `GET /api/actuators` - Get all actuator statuses
- `POST /api/actuators/<id>` - Control an actuator
- `GET /api/status` - Get system status
- `GET /api/statistics` - Get sensor statistics
- `GET /api/decisions` - Get recent decisions
- `POST /api/sensor-override` - Manual sensor value override

**WebSocket Events:**
- `sensor_update` - Real-time sensor readings
- `actuator_update` - Actuator state changes
- `decision_made` - Automated decisions
- `status_update` - System status updates

### Sensor Devices

1. **Roof Station** (JSON, via Gateway)
   - Temperature, Humidity, Pressure sensors
   - Outlier filtering enabled

2. **Living Room** (JSON)
   - Motion, Light, Temperature sensors

3. **Kitchen** (JSON)
   - Gas, Smoke, Temperature sensors

4. **Dust Cleaner** (XML/SOAP)
   - Distance, Object Detection, Signal Strength sensors
   - Sends SOAP-formatted XML messages

5. **Bedroom** (JSON)
   - Temperature, Light, Door sensors

6. **Basement** (JSON)
   - Water Leak, Humidity, Temperature sensors

7. **Entrance** (JSON)
   - Motion, Door, RFID sensors

### Decision Rules Examples

- Temperature > 30°C → Turn on HVAC (cooling)
- Temperature < 18°C → Turn on HVAC (heating)
- Motion detected + Light < 200 lux → Turn on lights
- CO2 > 1000 ppm → Activate ventilation
- Gas level > 1500 ppm → Sound alarm + max ventilation
- Smoke detected → Fire alarm + shut down HVAC
- Water leak detected → Shut off water valve
- Humidity > 70% in basement → Turn on dehumidifier
- Distance < 50cm (dust cleaner) → Pause motor
- Door opened at entrance → Turn on entrance light

### Actuators

1. **HVAC System** - Climate control (whole house)
2. **Living Room Lights** - Dimmable lighting
3. **Bedroom Lights** - Dimmable lighting
4. **Kitchen Exhaust** - Variable speed fan
5. **Entrance Lights** - On/off lighting
6. **Fire Alarm** - Critical priority alarm
7. **Gas Alarm** - Kitchen safety alarm
8. **Water Shutoff Valve** - Emergency water control
9. **Dust Cleaner Motor** - Cleaning robot control
10. **Dehumidifier** - Basement humidity control
11. **Door Lock** - Entrance security

## 🎨 UI Features

- **Live Sensor Cards**: Real-time sensor values with color-coded status indicators
- **Manual Control Sliders**: Override sensor values for testing
- **Actuator Cards**: Current state and manual toggle controls
- **Format Badges**: JSON/XML indicators for each sensor
- **Connection Status**: WebSocket connection indicator
- **System Statistics**: Readings per hour, active actuators
- **Responsive Design**: Works on desktop, tablet, and mobile
- **Dark Theme**: Modern, easy-on-eyes interface

## 🛠️ Configuration

### Environment Variables

Backend (`backend/config.py`):
- `CONTROLLER_HOST` - Controller host (default: 0.0.0.0)
- `CONTROLLER_PORT` - Controller port (default: 5000)
- `MONGODB_URI` - MongoDB connection string
- `MONGODB_DATABASE` - Database name (default: IOT)
- `SIMULATION_INTERVAL` - Sensor update interval (default: 3.0 seconds)
- `CONTINUOUS_MODE` - Run continuously or fixed cycles (default: true)

UI (`.env` file in `ui/` directory):
```bash
VITE_API_URL=http://localhost:5000
```

## 📝 Database Collections

MongoDB automatically creates these collections:
- `sensor_readings` - All sensor data with timestamps
- `actuator_commands` - History of all actuator commands
- `actuator_status` - Current state of each actuator
- `decision_logs` - All automated decisions made
- `gateway_logs` - Outlier filtering statistics
- `system_logs` - General system events

## 🔧 Development

### Adding a New Sensor

1. Add sensor class to `sensors/sensor_simulator.py`
2. Add sensor configuration to `backend/config.py` `SENSORS` dict
3. Add decision logic in `backend/controller/decision_engine.py`
4. UI will automatically display new sensors

### Adding a New Actuator

1. Add actuator configuration to `backend/config.py` `ACTUATORS` dict
2. Add control logic in `backend/controller/decision_engine.py`
3. UI will automatically display new actuators

## 📖 Project Structure

```
IOT/
├── backend/
│   ├── config.py                 # System configuration
│   ├── requirements.txt          # Python dependencies
│   ├── models/                   # Data models
│   │   ├── __init__.py
│   │   └── sensor_data.py
│   └── controller/               # Main controller
│       ├── main.py              # Flask app & WebSocket
│       ├── database.py          # MongoDB manager
│       └── decision_engine.py   # Automation rules
├── sensors/
│   ├── requirements.txt         # Python dependencies
│   ├── main_service.py         # Main sensor service
│   ├── sensor_simulator.py     # Sensor implementations
│   └── gateway.py              # Outlier filtering gateway
├── ui/
│   ├── package.json            # Node dependencies
│   ├── vite.config.ts          # Vite configuration
│   ├── tsconfig.json           # TypeScript config
│   ├── index.html              # HTML entry point
│   └── src/
│       ├── main.tsx            # React entry point
│       ├── App.tsx             # Main app component
│       ├── types/              # TypeScript types
│       ├── services/           # API & WebSocket services
│       └── components/         # React components
│           ├── SensorCard.tsx
│           └── ActuatorCard.tsx
└── docs/
    └── Project Requirements.md
```

## 🧪 Testing

### Test Sensor Override
```bash
curl -X POST http://localhost:5000/api/sensor-override \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "living_room",
    "location": "living_room",
    "readings": [{"sensor_type": "temperature", "value": 35, "unit": "°C"}]
  }'
```

### Test Actuator Control
```bash
curl -X POST http://localhost:5000/api/actuators/hvac_system \
  -H "Content-Type: application/json" \
  -d '{"state": "cooling"}'
```

### Get System Status
```bash
curl http://localhost:5000/api/status
```

## 📊 Monitoring

- **Backend Logs**: Real-time console output with timestamps
- **MongoDB**: Use MongoDB Compass to view stored data
- **UI**: Live dashboard shows all sensor readings and actuator states
- **Gateway Stats**: View outlier filtering in console logs

## 🔍 Troubleshooting

**MongoDB Connection Error:**
- Ensure MongoDB is running: `brew services list` or `mongod --version`
- Check MongoDB is on default port 27017

**WebSocket Not Connecting:**
- Verify backend controller is running on port 5000
- Check CORS settings in `backend/config.py`

**No Sensor Data:**
- Confirm sensor service is running
- Check controller URL in sensor service logs
- Verify network connectivity between services

**UI Not Loading:**
- Run `npm install` in ui directory
- Check port 3000 is not in use
- Verify VITE_API_URL points to backend

## 📚 Technologies Used

**Backend:**
- Flask - Web framework
- Flask-SocketIO - WebSocket support
- PyMongo - MongoDB driver
- Python threading - Concurrent operations

**Sensors:**
- Python standard library
- Requests - HTTP client
- XML/ElementTree - XML processing

**Frontend:**
- React 18 - UI framework
- TypeScript - Type safety
- Material-UI - Component library
- Socket.io-client - WebSocket client
- Axios - HTTP client
- Vite - Build tool

## 👥 Authors

IoT Smart Home Simulation System
Educational project for IoT systems understanding

## 📄 License

Educational use only
