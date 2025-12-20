/**
 * System Information Component
 * Displays architecture, configurations, and technical details
 */
import {
  Box,
  Paper,
  Typography,
  Grid,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Card,
  CardContent,
  Stack,
  Divider,
  Alert
} from '@mui/material';
import {
  ExpandMore,
  CheckCircle,
  Architecture,
  Memory,
  DataObject,
  Security,
  Settings,
  Code,
  Assessment
} from '@mui/icons-material';

const SystemInfo = () => {
  const stats = [
    { label: 'Sensor Types', value: '20+', color: '#4ade80' },
    { label: 'Devices', value: '7', color: '#60a5fa' },
    { label: 'Actuators', value: '11', color: '#f59e0b' },
    { label: 'Data Formats', value: '2', color: '#ec4899' }
  ];

  const sensors = [
    { name: '🌡️ Temperature', type: 'Numeric', range: '15-40°C' },
    { name: '💧 Humidity', type: 'Numeric', range: '20-80%' },
    { name: '⏱️ Pressure', type: 'Numeric', range: '980-1040 hPa' },
    { name: '💡 Light', type: 'Numeric', range: '0-1000 lux' },
    { name: '🚶 Motion', type: 'Boolean', range: '0/1' },
    { name: '💨 CO2', type: 'Numeric', range: '400-2000 ppm' },
    { name: '⚠️ Gas', type: 'Numeric', range: '0-2000 ppm' },
    { name: '🔥 Smoke', type: 'Boolean', range: '0/1' },
    { name: '📏 Distance', type: 'Numeric', range: '0-300 cm' },
    { name: '🚪 Door Sensor', type: 'Boolean', range: 'Open/Closed' },
    { name: '💧 Water Leak', type: 'Boolean', range: '0/1' },
    { name: '🔖 RFID', type: 'String', range: 'Tag IDs' },
    { name: '📶 Signal', type: 'Numeric', range: '-90 to -30 dBm' },
    { name: '🔊 Sound', type: 'Numeric', range: '30-100 dB' },
    { name: '📳 Vibration', type: 'Numeric', range: '0-1 g' },
    { name: '⚡ Energy', type: 'Numeric', range: '0-2000 W' },
    { name: '☀️ UV', type: 'Numeric', range: '0-11 index' },
    { name: '🌧️ Rain', type: 'Boolean', range: '0/1' },
    { name: '🪟 Glass Break', type: 'Boolean', range: '0/1' },
    { name: '🦶 Pressure Mat', type: 'Boolean', range: '0/1' }
  ];

  const decisionRules = [
    { trigger: 'Temperature > 30°C', action: 'HVAC → Cooling' },
    { trigger: 'Temperature < 18°C', action: 'HVAC → Heating' },
    { trigger: 'Motion + Light < 200 lux', action: 'Lights → ON (80%)' },
    { trigger: 'CO2 > 1500 ppm', action: 'HVAC → Fan Only' },
    { trigger: 'Gas > 1500 ppm', action: 'Alarm + Exhaust' },
    { trigger: 'Smoke Detected', action: 'Fire Alarm + HVAC OFF' },
    { trigger: 'Water Leak', action: 'Shutoff Valve' },
    { trigger: 'Distance < 50cm', action: 'Pause Cleaner' }
  ];

  const apiEndpoints = [
    { endpoint: '/api/sensor-data', method: 'POST', purpose: 'Receive JSON sensor data' },
    { endpoint: '/api/sensor-data/xml', method: 'POST', purpose: 'Receive XML sensor data' },
    { endpoint: '/api/sensor-data/gateway', method: 'POST', purpose: 'Gateway-filtered data' },
    { endpoint: '/api/actuators', method: 'GET', purpose: 'Get actuator statuses' },
    { endpoint: '/api/actuators/<id>', method: 'POST', purpose: 'Control actuator' },
    { endpoint: '/api/status', method: 'GET', purpose: 'System status' },
    { endpoint: '/api/ml/status', method: 'GET', purpose: 'ML model status' },
    { endpoint: '/api/ml/train', method: 'POST', purpose: 'Trigger ML training' }
  ];

  const componentFiles = [
    { file: 'sensors/sensor_simulator.py', lines: 851, purpose: 'All 20+ sensor implementations' },
    { file: 'sensors/main_service.py', lines: 455, purpose: 'Sensor orchestrator & JSON/XML' },
    { file: 'sensors/gateway.py', lines: 196, purpose: 'Outlier detection & filtering' },
    { file: 'backend/controller/main.py', lines: 804, purpose: 'REST API & WebSocket server' },
    { file: 'backend/controller/decision_engine.py', lines: 658, purpose: '20+ automation rules' },
    { file: 'backend/controller/ml_model.py', lines: 242, purpose: 'ML lifecycle management' },
    { file: 'backend/controller/database.py', lines: '450+', purpose: 'MongoDB & analytics' },
    { file: 'backend/security.py', lines: '400+', purpose: 'JWT, encryption, auth' },
    { file: 'backend/config.py', lines: '500+', purpose: 'System configuration' }
  ];

  return (
    <Box sx={{ pb: 4 }}>
      {/* Header Stats */}
      <Paper elevation={3} sx={{ p: 3, mb: 3, background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}>
        <Typography variant="h4" gutterBottom sx={{ color: 'white', fontWeight: 'bold' }}>
          🏠 IoT Smart Home System Information
        </Typography>
        <Typography variant="subtitle1" sx={{ color: 'rgba(255,255,255,0.9)', mb: 3 }}>
          Complete Technical Overview - Phase 1 & 2 Implementation
        </Typography>
        
        <Grid container spacing={2}>
          {stats.map((stat, idx) => (
            <Grid item xs={6} sm={3} key={idx}>
              <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'rgba(255,255,255,0.1)', backdropFilter: 'blur(10px)' }}>
                <Typography variant="h3" sx={{ color: stat.color, fontWeight: 'bold' }}>
                  {stat.value}
                </Typography>
                <Typography variant="body2" sx={{ color: 'white' }}>
                  {stat.label}
                </Typography>
              </Paper>
            </Grid>
          ))}
        </Grid>
      </Paper>

      {/* System Architecture */}
      <Accordion defaultExpanded>
        <AccordionSummary expandIcon={<ExpandMore />}>
          <Architecture sx={{ mr: 1 }} />
          <Typography variant="h6">System Architecture</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Stack spacing={2}>
            <Card sx={{ bgcolor: 'rgba(102, 126, 234, 0.1)' }}>
              <CardContent>
                <Typography variant="h6" color="primary" gutterBottom>
                  📡 SENSOR LAYER
                </Typography>
                <Typography variant="body2" paragraph>
                  <strong>7 Devices with 20+ Sensor Types</strong>
                </Typography>
                <Grid container spacing={1}>
                  {['🏠 Roof Station (JSON + Gateway)', '🛋️ Living Room (JSON)', '🍳 Kitchen (JSON)', 
                    '🛏️ Bedroom (JSON)', '🧹 Dust Cleaner (XML/SOAP)', '🏚️ Basement (JSON)', 
                    '🚪 Entrance (JSON)'].map((device, idx) => (
                    <Grid item xs={12} sm={6} md={4} key={idx}>
                      <Chip label={device} size="small" />
                    </Grid>
                  ))}
                </Grid>
              </CardContent>
            </Card>

            <Typography align="center" variant="h4">⬇️</Typography>

            <Card sx={{ bgcolor: 'rgba(251, 191, 36, 0.1)' }}>
              <CardContent>
                <Typography variant="h6" color="warning.main" gutterBottom>
                  🛡️ GATEWAY LAYER
                </Typography>
                <Typography variant="body2" paragraph>
                  <strong>Outlier Detection & Data Quality</strong>
                </Typography>
                <Stack direction="row" spacing={1} flexWrap="wrap">
                  <Chip label="IQR Method" color="warning" size="small" />
                  <Chip label="Range Validation" color="warning" size="small" />
                  <Chip label="Sliding Window" color="warning" size="small" />
                  <Chip label="Statistics Tracking" color="warning" size="small" />
                </Stack>
              </CardContent>
            </Card>

            <Typography align="center" variant="h4">⬇️</Typography>

            <Card sx={{ bgcolor: 'rgba(34, 197, 94, 0.1)' }}>
              <CardContent>
                <Typography variant="h6" color="success.main" gutterBottom>
                  ⚙️ CONTROLLER LAYER
                </Typography>
                <Typography variant="body2" paragraph>
                  <strong>Central Processing & Decision Making</strong>
                </Typography>
                <Grid container spacing={1}>
                  {['REST API (Flask)', 'WebSocket (SocketIO)', 'Decision Engine', 
                    'ML Model', 'MongoDB', 'Security Manager'].map((comp, idx) => (
                    <Grid item xs={6} sm={4} md={2} key={idx}>
                      <Chip label={comp} color="success" size="small" />
                    </Grid>
                  ))}
                </Grid>
              </CardContent>
            </Card>

            <Typography align="center" variant="h4">⬇️</Typography>

            <Card sx={{ bgcolor: 'rgba(236, 72, 153, 0.1)' }}>
              <CardContent>
                <Typography variant="h6" color="secondary" gutterBottom>
                  🎛️ ACTUATOR LAYER
                </Typography>
                <Typography variant="body2" paragraph>
                  <strong>11 Smart Actuators</strong>
                </Typography>
                <Grid container spacing={1}>
                  {['❄️ HVAC System', '💡 Smart Lights (3)', '🌪️ Fans', '🚨 Alarms', 
                    '💧 Water Shutoff', '🧹 Dust Cleaner', '💨 Dehumidifier', '🔒 Door Lock'].map((act, idx) => (
                    <Grid item xs={6} sm={4} md={3} key={idx}>
                      <Chip label={act} color="secondary" size="small" />
                    </Grid>
                  ))}
                </Grid>
              </CardContent>
            </Card>
          </Stack>
        </AccordionDetails>
      </Accordion>

      {/* Sensors Details */}
      <Accordion>
        <AccordionSummary expandIcon={<ExpandMore />}>
          <Memory sx={{ mr: 1 }} />
          <Typography variant="h6">Sensor Components (20+ Types)</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Alert severity="info" sx={{ mb: 2 }}>
            <strong>File:</strong> sensors/sensor_simulator.py (851 lines)
          </Alert>
          <TableContainer component={Paper} variant="outlined">
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell><strong>Sensor Type</strong></TableCell>
                  <TableCell><strong>Data Type</strong></TableCell>
                  <TableCell><strong>Range/Values</strong></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {sensors.map((sensor, idx) => (
                  <TableRow key={idx} hover>
                    <TableCell>{sensor.name}</TableCell>
                    <TableCell>{sensor.type}</TableCell>
                    <TableCell>{sensor.range}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </AccordionDetails>
      </Accordion>

      {/* Gateway Details */}
      <Accordion>
        <AccordionSummary expandIcon={<ExpandMore />}>
          <Security sx={{ mr: 1 }} />
          <Typography variant="h6">Gateway Outlier Detection</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Alert severity="info" sx={{ mb: 2 }}>
            <strong>File:</strong> sensors/gateway.py (196 lines)
          </Alert>
          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <Card variant="outlined">
                <CardContent>
                  <Typography variant="subtitle1" color="primary" gutterBottom>
                    IQR Method
                  </Typography>
                  <Typography variant="body2" component="pre" sx={{ fontSize: '0.75rem', whiteSpace: 'pre-wrap' }}>
{`Lower Bound = Q1 - 1.5 × IQR
Upper Bound = Q3 + 1.5 × IQR

If value < Lower or value > Upper:
    → Flag as outlier`}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={6}>
              <Card variant="outlined">
                <CardContent>
                  <Typography variant="subtitle1" color="primary" gutterBottom>
                    Range Validation
                  </Typography>
                  <Typography variant="body2" component="pre" sx={{ fontSize: '0.75rem', whiteSpace: 'pre-wrap' }}>
{`Temperature: -20°C to 50°C
Humidity: 0% to 100%
Pressure: 900 hPa to 1100 hPa
CO2: 0 ppm to 5000 ppm`}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </AccordionDetails>
      </Accordion>

      {/* Decision Rules */}
      <Accordion>
        <AccordionSummary expandIcon={<ExpandMore />}>
          <Settings sx={{ mr: 1 }} />
          <Typography variant="h6">Decision Engine Rules (20+)</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Alert severity="info" sx={{ mb: 2 }}>
            <strong>File:</strong> backend/controller/decision_engine.py (658 lines)
          </Alert>
          <Grid container spacing={2}>
            {decisionRules.map((rule, idx) => (
              <Grid item xs={12} sm={6} md={4} key={idx}>
                <Card variant="outlined">
                  <CardContent>
                    <Typography variant="body2" color="text.secondary">
                      <strong>{rule.trigger}</strong>
                    </Typography>
                    <Divider sx={{ my: 1 }} />
                    <Typography variant="body2" color="primary">
                      → {rule.action}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </AccordionDetails>
      </Accordion>

      {/* API Endpoints */}
      <Accordion>
        <AccordionSummary expandIcon={<ExpandMore />}>
          <DataObject sx={{ mr: 1 }} />
          <Typography variant="h6">REST API Endpoints</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Alert severity="info" sx={{ mb: 2 }}>
            <strong>File:</strong> backend/controller/main.py (804 lines)
          </Alert>
          <TableContainer component={Paper} variant="outlined">
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell><strong>Endpoint</strong></TableCell>
                  <TableCell><strong>Method</strong></TableCell>
                  <TableCell><strong>Purpose</strong></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {apiEndpoints.map((api, idx) => (
                  <TableRow key={idx} hover>
                    <TableCell><code>{api.endpoint}</code></TableCell>
                    <TableCell>
                      <Chip label={api.method} size="small" color={api.method === 'POST' ? 'primary' : 'default'} />
                    </TableCell>
                    <TableCell>{api.purpose}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </AccordionDetails>
      </Accordion>

      {/* ML Model */}
      <Accordion>
        <AccordionSummary expandIcon={<ExpandMore />}>
          <Assessment sx={{ mr: 1 }} />
          <Typography variant="h6">Machine Learning Model</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Alert severity="info" sx={{ mb: 2 }}>
            <strong>File:</strong> backend/controller/ml_model.py (242 lines)
          </Alert>
          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <Card variant="outlined">
                <CardContent>
                  <Typography variant="subtitle1" color="primary" gutterBottom>
                    Model Specifications
                  </Typography>
                  <Typography variant="body2" component="pre" sx={{ fontSize: '0.75rem' }}>
{`Algorithm: RandomForestClassifier
Trees: 80
Max Depth: 6
Features: Temperature, Humidity, CO2
Target: HVAC State
  - off
  - fan_only
  - cooling
  - heating`}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={6}>
              <Card variant="outlined">
                <CardContent>
                  <Typography variant="subtitle1" color="primary" gutterBottom>
                    Model Lifecycle
                  </Typography>
                  <Stack spacing={1} alignItems="center" sx={{ mt: 2 }}>
                    <Chip icon={<CheckCircle />} label="1. Train (7 days data)" color="success" />
                    <Typography>⬇️</Typography>
                    <Chip icon={<CheckCircle />} label="2. Deploy" color="success" />
                    <Typography>⬇️</Typography>
                    <Chip label="3. Monitor Drift" color="warning" />
                    <Typography>⬇️</Typography>
                    <Chip icon={<CheckCircle />} label="4. Retrain (24h)" color="success" />
                  </Stack>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </AccordionDetails>
      </Accordion>

      {/* Component Files */}
      <Accordion>
        <AccordionSummary expandIcon={<ExpandMore />}>
          <Code sx={{ mr: 1 }} />
          <Typography variant="h6">Component Files & Implementation</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <TableContainer component={Paper} variant="outlined">
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell><strong>File</strong></TableCell>
                  <TableCell><strong>Lines</strong></TableCell>
                  <TableCell><strong>Purpose</strong></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {componentFiles.map((file, idx) => (
                  <TableRow key={idx} hover>
                    <TableCell><code style={{ fontSize: '0.75rem' }}>{file.file}</code></TableCell>
                    <TableCell>{file.lines}</TableCell>
                    <TableCell>{file.purpose}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </AccordionDetails>
      </Accordion>

      {/* Requirements Status */}
      <Paper elevation={3} sx={{ p: 3, mt: 3, bgcolor: 'rgba(74, 222, 128, 0.1)' }}>
        <Typography variant="h6" gutterBottom sx={{ color: 'success.main' }}>
          ✅ Implementation Status
        </Typography>
        <Grid container spacing={2}>
          <Grid item xs={12} md={6}>
            <Typography variant="subtitle2" gutterBottom>Phase 1 Requirements</Typography>
            <Stack spacing={0.5}>
              <Chip icon={<CheckCircle />} label="3+ Sensor Types (20+)" color="success" size="small" />
              <Chip icon={<CheckCircle />} label="Central Controller" color="success" size="small" />
              <Chip icon={<CheckCircle />} label="Decision Rules" color="success" size="small" />
              <Chip icon={<CheckCircle />} label="2+ Actuators (11)" color="success" size="small" />
              <Chip icon={<CheckCircle />} label="Gateway Tier" color="success" size="small" />
              <Chip icon={<CheckCircle />} label="JSON & XML Formats" color="success" size="small" />
            </Stack>
          </Grid>
          <Grid item xs={12} md={6}>
            <Typography variant="subtitle2" gutterBottom>Phase 2 Requirements</Typography>
            <Stack spacing={0.5}>
              <Chip icon={<CheckCircle />} label="Additional Sensors" color="success" size="small" />
              <Chip icon={<CheckCircle />} label="Multi-tier Architecture" color="success" size="small" />
              <Chip icon={<CheckCircle />} label="Data Analytics" color="success" size="small" />
              <Chip icon={<CheckCircle />} label="ML Model" color="success" size="small" />
              <Chip icon={<CheckCircle />} label="Drift Detection" color="success" size="small" />
              <Chip icon={<CheckCircle />} label="Prescriptive Analysis" color="success" size="small" />
            </Stack>
          </Grid>
        </Grid>
      </Paper>
    </Box>
  );
};

export default SystemInfo;
