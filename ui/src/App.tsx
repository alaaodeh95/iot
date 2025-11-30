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
  Alert
} from '@mui/material';
import { Home, WifiOff, Wifi } from '@mui/icons-material';
import SensorCard from './components/SensorCard';
import ActuatorCard from './components/ActuatorCard';
import { socketService } from './services/socket';
import { apiService } from './services/api';
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

    // Initial data fetch
    const fetchInitialData = async () => {
      try {
        const [actuatorsData, statusData] = await Promise.all([
          apiService.getActuators(),
          apiService.getSystemStatus()
        ]);
        setActuators(actuatorsData);
        setSystemStatus(statusData);
        setError(null);
      } catch (err) {
        console.error('Error fetching initial data:', err);
        setError('Failed to connect to backend. Please ensure the controller is running.');
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

        <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
          {error && (
            <Alert severity="error" sx={{ mb: 3 }}>
              {error}
            </Alert>
          )}

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

          {/* Footer */}
          <Box sx={{ mt: 4, textAlign: 'center' }}>
            <Typography variant="caption" color="text.secondary">
              IoT Smart Home Simulation System | Real-time monitoring with JSON & XML support
            </Typography>
          </Box>
        </Container>
      </Box>
    </ThemeProvider>
  );
}

export default App;
