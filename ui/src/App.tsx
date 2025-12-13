/**
 * Main App Component for IoT Smart Home Dashboard
 */
import React, { useState, useEffect } from 'react';
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
  Tab
} from '@mui/material';
import { 
  Home, 
  WifiOff, 
  Wifi, 
  Security as SecurityIcon,
  Dashboard as DashboardIcon
} from '@mui/icons-material';
import SensorCard from './components/SensorCard';
import SecurityStatus from './components/SecurityStatus';
import ActuatorCard from './components/ActuatorCard';
import { socketService } from './services/socket';
import { apiService } from './services/api';
import { securityService } from './services/security';
import type { SensorData, ActuatorStatus, SystemStatus } from './types';

const darkTheme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#90caf9',
    },
    secondary: {
      main: '#f48fb1',
    },
  },
});

function App() {
  const [sensorData, setSensorData] = useState<Map<string, SensorData>>(new Map());
  const [actuators, setActuators] = useState<ActuatorStatus[]>([]);
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentTab, setCurrentTab] = useState(0);
  const [authError, setAuthError] = useState<string | null>(null);

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
                  Check your <code>VITE_API_KEY</code> environment variable or switch to the Security tab for diagnostics.
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
              {/* Sensors Section */}
              <Paper elevation={3} sx={{ p: 3, mb: 4 }}>
            <Typography variant="h5" gutterBottom sx={{ mb: 3 }}>
              📊 Live Sensors
            </Typography>
            <Grid container spacing={3}>
              {Array.from(sensorData.values()).map((data) =>
                data.readings.map((reading, idx) => (
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
                ))
              )}
              {sensorData.size === 0 && (
                <Grid item xs={12}>
                  <Alert severity="info">
                    Waiting for sensor data... Please ensure the sensor service is running.
                  </Alert>
                </Grid>
              )}
            </Grid>
          </Paper>

          {/* Actuators Section */}
          <Paper elevation={3} sx={{ p: 3 }}>
            <Typography variant="h5" gutterBottom sx={{ mb: 3 }}>
              🎛️ Actuators
            </Typography>
            <Grid container spacing={3}>
              {actuators.map((actuator) => (
                <Grid item xs={12} sm={6} md={4} lg={3} key={actuator.actuator_id}>
                  <ActuatorCard
                    actuator={actuator}
                    onToggle={handleActuatorToggle}
                  />
                </Grid>
              ))}
              {actuators.length === 0 && (
                <Grid item xs={12}>
                  <Alert severity="info">
                    Loading actuators...
                  </Alert>
                </Grid>
              )}
            </Grid>
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
            </>
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
