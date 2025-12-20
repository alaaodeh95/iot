/**
 * Main App Component for IoT Smart Home Dashboard
 */
import { useState, useEffect } from 'react';
import {
  ThemeProvider,
  createTheme,
  CssBaseline,
  AppBar,
  Toolbar,
  Typography,
  Container,
  Grid,
  Paper,
  Box,
  Chip,
  Alert,
  Tabs,
  Tab,
  Button,
  Stack,
  Divider,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  SelectChangeEvent
} from '@mui/material';
import {
  Home,
  WifiOff,
  Wifi,
  Security as SecurityIcon,
  Dashboard as DashboardIcon,
  Analytics as AnalyticsIcon,
  Timeline as TimelineIcon,
  Download as DownloadIcon,
  Refresh as RefreshIcon,
  Info as InfoIcon
} from '@mui/icons-material';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend
} from 'recharts';
import SensorCard from './components/SensorCard';
import SecurityStatus from './components/SecurityStatus';
import ActuatorCard from './components/ActuatorCard';
import SystemInfo from './components/SystemInfo';
import { socketService } from './services/socket';
import { apiService } from './services/api';
import { securityService } from './services/security';
import type {
  SensorData,
  ActuatorStatus,
  SystemStatus,
  DecisionLog,
  AnalyticsSummary,
  AnalyticsExport,
  ModelStatus,
  AnalyticsExportXlsx,
  AnalyticsExportParquet,
  AnalyticsCharts
} from './types';

const darkTheme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#90caf9'
    },
    secondary: {
      main: '#f48fb1'
    }
  }
});

function App() {
  const [sensorData, setSensorData] = useState<Map<string, SensorData>>(new Map());
  const [actuators, setActuators] = useState<ActuatorStatus[]>([]);
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentTab, setCurrentTab] = useState(0);
  const [authError, setAuthError] = useState<string | null>(null);
  const [decisions, setDecisions] = useState<DecisionLog[]>([]);
  const [analytics, setAnalytics] = useState<AnalyticsSummary | null>(null);
  const [mlStatus, setMlStatus] = useState<ModelStatus | null>(null);
  const [exportCsv, setExportCsv] = useState<AnalyticsExport | null>(null);
  const [exportXlsx] = useState<AnalyticsExportXlsx | null>(null);
  const [exportParquet] = useState<AnalyticsExportParquet | null>(null);
  const [charts] = useState<AnalyticsCharts['charts'] | null>(null);
  const [loadingAnalytics, setLoadingAnalytics] = useState(false);
  const [loadingDrift, setLoadingDrift] = useState(false);
  const [selectedSensorType, setSelectedSensorType] = useState<string>('temperature');
  const [sensorHistory, setSensorHistory] = useState<
    Record<string, { timestamp: string; value: number; device_id: string; location?: string }[]>
  >({});

  useEffect(() => {
    // Connect to WebSocket
    socketService.connect();

    // Check connection status
    const checkConnection = setInterval(() => {
      setConnected(socketService.isConnected());
    }, 1000);

    // Listen for sensor updates
    const handleSensorUpdate = (data: SensorData) => {
      setSensorData(prev => {
        const newData = new Map(prev);
        newData.set(data.device_id, data);
        return newData;
      });

      // Track numeric readings for chart history
      setSensorHistory(prev => {
        const updated = { ...prev };
        data.readings.forEach(reading => {
          if (typeof reading.value === 'number') {
            const arr = updated[reading.sensor_type] ? [...updated[reading.sensor_type]] : [];
            arr.push({
              timestamp: data.timestamp || new Date().toISOString(),
              value: reading.value as number,
              device_id: data.device_id,
              location: data.location
            });
            updated[reading.sensor_type] = arr.slice(-200);
          }
        });
        return updated;
      });
    };

    // Listen for actuator updates
    const handleActuatorUpdate = (data: ActuatorStatus) => {
      setActuators(prev => {
        const index = prev.findIndex(a => a.actuator_id === data.actuator_id);
        if (index >= 0) {
          const newActuators = [...prev];
          newActuators[index] = data;
          return newActuators;
        }
        return [...prev, data];
      });
    };

    socketService.on('sensor_update', handleSensorUpdate);
    socketService.on('actuator_update', handleActuatorUpdate);

    // Initial data fetch with security handling
    const fetchInitialData = async () => {
      try {
        console.log('🚀 Starting secure data fetch...');

        const [actuatorsData, statusData] = await Promise.all([
          apiService.getActuators(),
          apiService.getSystemStatus()
        ]);

        setActuators(actuatorsData);
        setSystemStatus(statusData);
        setError(null);
        setAuthError(null);

        console.log('✅ Initial data loaded successfully');
      } catch (err: any) {
        console.error('❌ Error fetching initial data:', err);

        if (err.response?.status === 401) {
          const authMsg = 'Authentication failed. Please check your API key configuration.';
          setAuthError(authMsg);
          setError(authMsg);
          securityService.handleAuthError(err);
        } else if (err.response?.status === 403) {
          const forbiddenMsg = 'Access denied. Check your permissions.';
          setAuthError(forbiddenMsg);
          setError(forbiddenMsg);
        } else if (err.code === 'ECONNREFUSED') {
          setError('Failed to connect to backend. Please ensure the controller is running.');
        } else {
          setError(`Connection error: ${err.message || 'Unknown error'}`);
        }
      }
    };

    fetchInitialData();
    refreshAnalytics();
    refreshDecisions();

    // Periodic status update
    const statusInterval = setInterval(async () => {
      try {
        const status = await apiService.getSystemStatus();
        setSystemStatus(status);
      } catch (err) {
        console.error('Error fetching status:', err);
      }
    }, 5000);

    return () => {
      clearInterval(checkConnection);
      clearInterval(statusInterval);
      socketService.off('sensor_update', handleSensorUpdate);
      socketService.off('actuator_update', handleActuatorUpdate);
      socketService.disconnect();
    };
  }, []);

  const refreshDecisions = async () => {
    try {
      const items = await apiService.getRecentDecisions(30);
      setDecisions(items);
    } catch (err) {
      console.error('Error fetching decisions:', err);
    }
  };

  const refreshAnalytics = async (hours: number = 24) => {
    try {
      setLoadingAnalytics(true);
      const summary = await apiService.getAnalyticsSummary(hours);
      setAnalytics(summary);
      const status = await apiService.getMlStatus();
      setMlStatus(status);
    } catch (err) {
      console.error('Error fetching analytics:', err);
    } finally {
      setLoadingAnalytics(false);
    }
  };

  const handleExport = async (hours: number = 24) => {
    try {
      const data = await apiService.exportAnalytics(hours);
      setExportCsv(data);
    } catch (err) {
      console.error('Error exporting analytics:', err);
    }
  };

  const handleTrain = async (hours: number = 168) => {
    try {
      const status = await apiService.trainMl(hours);
      setMlStatus(status);
    } catch (err) {
      console.error('Error training ML model:', err);
    }
  };

  const handleDriftCheck = async (hours: number = 24) => {
    try {
      setLoadingDrift(true);
      const status = await apiService.checkMlDrift(hours);
      setMlStatus(status);
    } catch (err) {
      console.error('Error checking drift:', err);
    } finally {
      setLoadingDrift(false);
    }
  };

  const handleSensorValueChange = async (deviceId: string, location: string, sensorType: string, value: number) => {
    try {
      await apiService.overrideSensorValue(deviceId, location, sensorType, value);
    } catch (err) {
      console.error('Error overriding sensor value:', err);
    }
  };

  const handleActuatorToggle = async (actuatorId: string, newState: string) => {
    try {
      await apiService.controlActuator(actuatorId, newState);
    } catch (err) {
      console.error('Error controlling actuator:', err);
    }
  };

  return (
    <ThemeProvider theme={darkTheme}>
      <CssBaseline />
      <Box sx={{ flexGrow: 1, minHeight: '100vh', backgroundColor: 'background.default' }}>
        <AppBar position="static">
          <Toolbar>
            <Home sx={{ mr: 2 }} />
            <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
              IoT Smart Home Dashboard
            </Typography>
            <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
              {systemStatus && (
                <>
                  <Chip
                    label={`${systemStatus.sensors.readings_last_hour} readings/hr`}
                    size="small"
                    color="primary"
                  />
                  <Chip
                    label={`${systemStatus.actuators.active}/${systemStatus.actuators.total} active`}
                    size="small"
                    color="secondary"
                  />
                </>
              )}
              <Chip
                icon={connected ? <Wifi /> : <WifiOff />}
                label={connected ? 'Connected' : 'Disconnected'}
                color={connected ? 'success' : 'error'}
                size="small"
              />
            </Box>
          </Toolbar>
        </AppBar>

        {/* Navigation Tabs */}
        <Paper sx={{ borderRadius: 0 }}>
          <Tabs
            value={currentTab}
            onChange={(_, newValue) => setCurrentTab(newValue)}
            centered
            sx={{ borderBottom: 1, borderColor: 'divider' }}
          >
            <Tab icon={<DashboardIcon />} label="Dashboard" />
            <Tab icon={<SecurityIcon />} label="Security" />
            <Tab icon={<AnalyticsIcon />} label="Analytics" />
            <Tab icon={<InfoIcon />} label="System Info" />
          </Tabs>
        </Paper>

        <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
          {/* Authentication Error Alert */}
          {authError && (
            <Alert severity="error" sx={{ mb: 3 }}>
              <Typography variant="h6">Authentication Error</Typography>
              {authError}
              <Box sx={{ mt: 1 }}>
                <Typography variant="body2">
                  Check your <code>VITE_API_KEY</code> environment variable or switch to the Security tab for
                  diagnostics.
                </Typography>
              </Box>
            </Alert>
          )}

          {/* General Error Alert */}
          {error && !authError && (
            <Alert severity="error" sx={{ mb: 3 }}>
              {error}
            </Alert>
          )}

          {/* Dashboard Tab Content */}
          {currentTab === 0 && (
            <>
              {/* Sensors Section - Grouped by Location */}
              <Paper elevation={3} sx={{ p: 3, mb: 4 }}>
                <Typography variant="h5" gutterBottom sx={{ mb: 3 }}>
                  📊 Live Sensors
                </Typography>
                {sensorData.size === 0 ? (
                  <Alert severity="info">
                    Waiting for sensor data... Please ensure the sensor service is running.
                  </Alert>
                ) : (
                  (() => {
                    // Group sensors by location
                    const sensorsByLocation = new Map<string, Array<{ data: SensorData; reading: any; idx: number }>>();
                    
                    Array.from(sensorData.values()).forEach(data => {
                      if (!sensorsByLocation.has(data.location)) {
                        sensorsByLocation.set(data.location, []);
                      }
                      data.readings.forEach((reading, idx) => {
                        sensorsByLocation.get(data.location)!.push({ data, reading, idx });
                      });
                    });

                    // Sort locations alphabetically
                    const sortedLocations = Array.from(sensorsByLocation.keys()).sort();

                    return (
                      <Stack spacing={4}>
                        {sortedLocations.map(location => (
                          <Box key={location}>
                            <Typography variant="h6" gutterBottom sx={{ mb: 2, color: 'primary.main' }}>
                              📍 {location.charAt(0).toUpperCase() + location.slice(1).replace('_', ' ')}
                            </Typography>
                            <Grid container spacing={2}>
                              {sensorsByLocation.get(location)!.map(({ data, reading, idx }) => (
                                <Grid item xs={12} sm={6} md={4} lg={3} key={`${data.device_id}-${idx}`}>
                                  <SensorCard
                                    deviceId={data.device_id}
                                    location={data.location}
                                    reading={reading}
                                    format={data.format}
                                    onValueChange={(sensorType, value) =>
                                      handleSensorValueChange(data.device_id, data.location, sensorType, value)
                                    }
                                  />
                                </Grid>
                              ))}
                            </Grid>
                          </Box>
                        ))}
                      </Stack>
                    );
                  })()
                )}
              </Paper>

              {/* Actuators Section - Grouped by Location */}
              <Paper elevation={3} sx={{ p: 3 }}>
                <Typography variant="h5" gutterBottom sx={{ mb: 3 }}>
                  🎛️ Actuators
                </Typography>
                {actuators.length === 0 ? (
                  <Alert severity="info">Loading actuators...</Alert>
                ) : (
                  (() => {
                    // Group actuators by location
                    const actuatorsByLocation = new Map<string, ActuatorStatus[]>();
                    
                    actuators.forEach(actuator => {
                      const location = actuator.location || 'system';
                      if (!actuatorsByLocation.has(location)) {
                        actuatorsByLocation.set(location, []);
                      }
                      actuatorsByLocation.get(location)!.push(actuator);
                    });

                    // Sort locations: whole_house/system first, then alphabetically
                    const sortedLocations = Array.from(actuatorsByLocation.keys()).sort((a, b) => {
                      if (a === 'whole_house' || a === 'system') return -1;
                      if (b === 'whole_house' || b === 'system') return 1;
                      return a.localeCompare(b);
                    });

                    return (
                      <Stack spacing={4}>
                        {sortedLocations.map(location => (
                          <Box key={location}>
                            <Typography variant="h6" gutterBottom sx={{ mb: 2, color: 'secondary.main' }}>
                              🏠 {location === 'whole_house' ? 'Whole House' : location.charAt(0).toUpperCase() + location.slice(1).replace('_', ' ')}
                            </Typography>
                            <Grid container spacing={2}>
                              {actuatorsByLocation.get(location)!.map(actuator => (
                                <Grid item xs={12} sm={6} md={4} lg={3} key={actuator.actuator_id}>
                                  <ActuatorCard actuator={actuator} onToggle={handleActuatorToggle} />
                                </Grid>
                              ))}
                            </Grid>
                          </Box>
                        ))}
                      </Stack>
                    );
                  })()
                )}
              </Paper>
            </>
          )}

          {/* Security Tab Content */}
          {currentTab === 1 && (
            <>
              <SecurityStatus />

              {/* Security Information */}
              <Paper elevation={3} sx={{ p: 3, mt: 4 }}>
                <Typography variant="h5" gutterBottom>
                  🔒 Security Information
                </Typography>

                <Grid container spacing={3}>
                  <Grid item xs={12} md={6}>
                    <Box>
                      <Typography variant="h6" gutterBottom>
                        API Configuration
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Base URL: {import.meta.env.VITE_API_URL || 'http://localhost:5000'}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        API Key: {securityService.getApiKey().slice(0, 12)}...
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        HTTPS: {securityService.shouldUseHttps() ? 'Enabled' : 'Disabled'}
                      </Typography>
                    </Box>
                  </Grid>

                  <Grid item xs={12} md={6}>
                    <Box>
                      <Typography variant="h6" gutterBottom>
                        Environment Variables
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Set <code>VITE_API_KEY</code> in your .env file
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Set <code>VITE_API_URL</code> for custom backend URL
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Set <code>VITE_ENABLE_HTTPS=true</code> for SSL
                      </Typography>
                    </Box>
                  </Grid>
                </Grid>
              </Paper>

              <Paper elevation={3} sx={{ p: 3, mt: 4 }}>
                <Typography variant="h6" gutterBottom>
                  🧾 Sample Payloads (JSON & XML/SOAP)
                </Typography>
                <Stack spacing={2}>
                  <Box>
                    <Typography variant="subtitle2">Roof Station JSON</Typography>
                    <Typography variant="body2" component="pre" sx={{ whiteSpace: 'pre-wrap' }}>
                      {`{
  "device_id": "roof_station",
  "location": "roof",
  "readings": [
    {"sensor_type":"temperature","value":28.4,"unit":"°C"},
    {"sensor_type":"humidity","value":55.2,"unit":"%"},
    {"sensor_type":"pressure","value":1012.3,"unit":"hPa"}
  ],
  "format": "json"
}`}
                    </Typography>
                  </Box>
                  <Divider />
                  <Box>
                    <Typography variant="subtitle2">Dust Cleaner SOAP/XML</Typography>
                    <Typography variant="body2" component="pre" sx={{ whiteSpace: 'pre-wrap' }}>
                      {`<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">
  <soapenv:Body>
    <sensor_data>
      <device_id>dust_cleaner</device_id>
      <location>mobile</location>
      <sensor>
        <type>distance</type><value>42.1</value><unit>cm</unit>
      </sensor>
      <sensor>
        <type>object_detection</type><value>chair</value><unit>string</unit>
      </sensor>
      <sensor>
        <type>signal_strength</type><value>-48</value><unit>dBm</unit>
      </sensor>
    </sensor_data>
  </soapenv:Body>
</soapenv:Envelope>`}
                    </Typography>
                  </Box>
                </Stack>
              </Paper>
            </>
          )}

          {/* Analytics Tab Content */}
          {currentTab === 2 && (
            <Stack spacing={3}>
              <Paper elevation={3} sx={{ p: 3 }}>
                <Stack
                  direction="row"
                  spacing={2}
                  alignItems="center"
                  justifyContent="space-between"
                  sx={{ mb: 2 }}
                >
                  <Typography variant="h5">📊 Live Sensor Chart</Typography>
                  <FormControl size="small" sx={{ minWidth: 200 }}>
                    <InputLabel id="sensor-type-label">Sensor Type</InputLabel>
                    <Select
                      labelId="sensor-type-label"
                      value={selectedSensorType}
                      label="Sensor Type"
                      onChange={(e: SelectChangeEvent<string>) => setSelectedSensorType(e.target.value)}
                    >
                      {Array.from(
                        new Set(
                          Object.keys(sensorHistory).concat(
                            Array.from(sensorData.values()).flatMap(d =>
                              d.readings.map(r => r.sensor_type)
                            )
                          )
                        )
                      ).map(type => (
                        <MenuItem value={type} key={type}>
                          {type}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Stack>
                <Box sx={{ height: 280 }}>
                  {sensorHistory[selectedSensorType]?.length ? (
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={sensorHistory[selectedSensorType]}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis
                          dataKey="timestamp"
                          tickFormatter={(v: string) => v.split('T')[1]?.slice(0, 8) || v}
                          minTickGap={20}
                        />
                        <YAxis />
                        <Tooltip />
                        <Legend />
                        <Line type="monotone" dataKey="value" stroke="#90caf9" dot={false} />
                      </LineChart>
                    </ResponsiveContainer>
                  ) : (
                    <Alert severity="info">No data yet for selected sensor.</Alert>
                  )}
                </Box>
              </Paper>
              <Paper elevation={3} sx={{ p: 3 }}>
                <Stack
                  direction="row"
                  spacing={2}
                  alignItems="center"
                  justifyContent="space-between"
                >
                  <Typography variant="h5">📈 Analytics & Gateway</Typography>
                  <Stack direction="row" spacing={1}>
                    <Button
                      variant="contained"
                      size="small"
                      startIcon={<RefreshIcon />}
                      onClick={() => refreshAnalytics(24)}
                    >
                      Refresh
                    </Button>
                    <Button
                      variant="outlined"
                      size="small"
                      startIcon={<DownloadIcon />}
                      onClick={() => handleExport(24)}
                    >
                      Export CSV
                    </Button>
                  </Stack>
                </Stack>

                {loadingAnalytics && (
                  <Alert severity="info" sx={{ mt: 2 }}>
                    Loading analytics...
                  </Alert>
                )}

                {analytics && (
                  <Grid container spacing={2} sx={{ mt: 1 }}>
                    <Grid item xs={12} md={6}>
                      <Typography variant="subtitle1">Sensor Summary (last 24h)</Typography>
                      <Box component="ul" sx={{ pl: 2, mt: 1 }}>
                        {analytics.sensor_summary.map(s => (
                          <li key={s.sensor_type}>
                            {s.sensor_type}: count={s.count}, avg={s.avg?.toFixed(2) ?? 'N/A'}, min={s.min ?? 'N/A'},{' '}
                            max={s.max ?? 'N/A'}
                          </li>
                        ))}
                      </Box>
                    </Grid>
                    <Grid item xs={12} md={6}>
                      <Typography variant="subtitle1">Actuator Usage</Typography>
                      <Box component="ul" sx={{ pl: 2, mt: 1 }}>
                        {analytics.actuator_usage.map(a => (
                          <li key={a.actuator_id}>
                            {a.actuator_id}: {a.count} commands (states: {a.states.join(', ')})
                          </li>
                        ))}
                      </Box>
                    </Grid>
                    <Grid item xs={12} md={6}>
                      <Typography variant="subtitle1">Gateway Statistics</Typography>
                      <Box component="ul" sx={{ pl: 2, mt: 1 }}>
                        <li>Total batches: {analytics.gateway_statistics.total_processed}</li>
                        <li>Batches with outliers: {analytics.gateway_statistics.batches_with_outliers}</li>
                        <li>Total outliers filtered: {analytics.gateway_statistics.total_outliers_filtered}</li>
                        <li>
                          Filter rate: {(analytics.gateway_statistics.filter_rate * 100).toFixed(2)}%
                        </li>
                      </Box>
                    </Grid>
                    <Grid item xs={12} md={6}>
                      <Typography variant="subtitle1">Decision Summary</Typography>
                      <Box component="ul" sx={{ pl: 2, mt: 1 }}>
                        <li>Total decisions: {analytics.decision_summary.total}</li>
                        <li>Last window: {analytics.decision_summary.last_hours}</li>
                      </Box>
                    </Grid>
                  </Grid>
                )}

                {exportCsv && (
                  <Alert severity="success" sx={{ mt: 2 }}>
                    Export ready. Copy CSV from console/logs or download below.
                  </Alert>
                )}
                {(exportXlsx || exportParquet || exportCsv) && (
                  <Stack spacing={1} sx={{ mt: 2 }}>
                    {exportCsv && (
                      <Button
                        component="a"
                        href={`data:text/csv;base64,${btoa(exportCsv.readings_csv)}`}
                        download="readings.csv"
                        variant="outlined"
                        size="small"
                      >
                        Download Readings CSV
                      </Button>
                    )}
                    {exportCsv && (
                      <Button
                        component="a"
                        href={`data:text/csv;base64,${btoa(exportCsv.commands_csv)}`}
                        download="commands.csv"
                        variant="outlined"
                        size="small"
                      >
                        Download Commands CSV
                      </Button>
                    )}
                    {exportXlsx && (
                      <Button
                        component="a"
                        href={`data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,${exportXlsx.xlsx_base64}`}
                        download="analytics.xlsx"
                        variant="contained"
                        size="small"
                      >
                        Download XLSX
                      </Button>
                    )}
                    {exportParquet && (
                      <Stack direction="row" spacing={1}>
                        <Button
                          component="a"
                          href={`data:application/octet-stream;base64,${exportParquet.readings_parquet_base64}`}
                          download="readings.parquet"
                          variant="contained"
                          size="small"
                        >
                          Download Readings Parquet
                        </Button>
                        <Button
                          component="a"
                          href={`data:application/octet-stream;base64,${exportParquet.commands_parquet_base64}`}
                          download="commands.parquet"
                          variant="contained"
                          size="small"
                        >
                          Download Commands Parquet
                        </Button>
                        <Button
                          component="a"
                          href={`data:application/octet-stream;base64,${exportParquet.gateway_parquet_base64}`}
                          download="gateway_logs.parquet"
                          variant="contained"
                          size="small"
                        >
                          Download Gateway Parquet
                        </Button>
                      </Stack>
                    )}
                  </Stack>
                )}
                {charts && (
                  <Grid container spacing={2} sx={{ mt: 2 }}>
                    {charts.sensor_avg && (
                      <Grid item xs={12} md={6}>
                        <Paper variant="outlined" sx={{ p: 2 }}>
                          <Typography variant="subtitle1">Sensor Averages</Typography>
                          <Box
                            component="img"
                            src={`data:image/png;base64,${charts.sensor_avg}`}
                            alt="sensor averages"
                            sx={{ width: '100%', mt: 1 }}
                          />
                        </Paper>
                      </Grid>
                    )}
                    {charts.actuator_counts && (
                      <Grid item xs={12} md={6}>
                        <Paper variant="outlined" sx={{ p: 2 }}>
                          <Typography variant="subtitle1">Actuator Command Counts</Typography>
                          <Box
                            component="img"
                            src={`data:image/png;base64,${charts.actuator_counts}`}
                            alt="actuator counts"
                            sx={{ width: '100%', mt: 1 }}
                          />
                        </Paper>
                      </Grid>
                    )}
                  </Grid>
                )}
              </Paper>

              <Paper elevation={3} sx={{ p: 3 }}>
                <Stack direction="row" spacing={2} alignItems="center" justifyContent="space-between">
                  <Typography variant="h5">🤖 ML Model Status</Typography>
                  <Stack direction="row" spacing={1}>
                    <Button variant="outlined" size="small" onClick={() => refreshAnalytics(24)}>
                      Refresh
                    </Button>
                    <Button variant="contained" size="small" startIcon={<RefreshIcon />} onClick={() => handleTrain(168)}>
                      Retrain (7d)
                    </Button>
                    <Button variant="outlined" size="small" disabled={loadingDrift} onClick={() => handleDriftCheck(24)}>
                      {loadingDrift ? 'Checking drift...' : 'Check Drift (24h)'}
                    </Button>
                  </Stack>
                </Stack>
                {mlStatus ? (
                  <Box sx={{ mt: 2 }}>
                    <Typography variant="body2">Loaded: {mlStatus.loaded ? 'Yes' : 'No'}</Typography>
                    <Typography variant="body2">Version: {mlStatus.version ?? 'N/A'}</Typography>
                    <Typography variant="body2">Last trained: {mlStatus.last_trained || 'N/A'}</Typography>
                    <Typography variant="body2">Next retrain: {mlStatus.next_retrain_at || 'N/A'}</Typography>
                    <Typography variant="body2">
                      Training window (h): {mlStatus.training_window_hours ?? 'N/A'}
                    </Typography>
                    <Typography variant="body2">Samples: {mlStatus.samples}</Typography>
                    <Typography variant="body2">Features: {mlStatus.features.join(', ')}</Typography>
                    <Typography variant="body2">Algorithm: {mlStatus.algorithm}</Typography>
                    <Typography variant="body2">F1: {mlStatus.f1 ?? 'N/A'}</Typography>
                    <Typography variant="body2">Drift score: {mlStatus.drift_score ?? 'N/A'}</Typography>
                    <Typography variant="body2">Drift checked: {mlStatus.drift_checked_at || 'N/A'}</Typography>
                  </Box>
                ) : (
                  <Alert severity="info" sx={{ mt: 2 }}>
                    No ML status yet.
                  </Alert>
                )}
              </Paper>

              <Paper elevation={3} sx={{ p: 3 }}>
                <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 1 }}>
                  <TimelineIcon fontSize="small" />
                  <Typography variant="h6">Recent Decisions</Typography>
                </Stack>
                {decisions.length === 0 && <Alert severity="info">No decisions yet.</Alert>}
                <Stack spacing={1}>
                  {decisions.map(d => (
                    <Paper key={d.decision_id} variant="outlined" sx={{ p: 1.5 }}>
                      <Typography variant="subtitle2">{d.trigger_sensor}</Typography>
                      <Typography variant="caption" color="text.secondary">
                        {d.timestamp}
                      </Typography>
                      <Typography variant="body2">Condition: {d.condition}</Typography>
                      <Typography variant="body2">
                        Actions: {d.actions.map(a => `${a.actuator_id}:${a.state}`).join(', ')}
                      </Typography>
                    </Paper>
                  ))}
                </Stack>
              </Paper>
            </Stack>
          )}

          {/* System Info Tab Content */}
          {currentTab === 3 && (
            <SystemInfo />
          )}

          {/* Footer */}
          <Box sx={{ mt: 4, textAlign: 'center' }}>
            <Typography variant="caption" color="text.secondary">
              IoT Smart Home Simulation System | Real-time monitoring with secure authentication
            </Typography>
          </Box>
        </Container>
      </Box>
    </ThemeProvider>
  );
}

export default App;
