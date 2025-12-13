/**
 * API service for communicating with the IoT backend
 */
import axios from 'axios';
import type { ActuatorStatus, SystemStatus, DecisionLog, SensorConfig } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';
const API_KEY = import.meta.env.VITE_API_KEY || 'iot-secure-api-key-2024';

// Security configuration
const securityConfig = {
  apiKey: API_KEY,
  enableHttps: import.meta.env.VITE_ENABLE_HTTPS === 'true',
  socketAuth: import.meta.env.VITE_SOCKET_AUTH === 'true'
};

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': securityConfig.apiKey,
    'User-Agent': 'IoT-Dashboard/1.0'
  }
});

// Add request interceptor for security headers
api.interceptors.request.use(
  (config) => {
    // Ensure API key is always included
    if (!config.headers['X-API-Key']) {
      config.headers['X-API-Key'] = securityConfig.apiKey;
    }
    
    // Add timestamp for request tracking
    config.headers['X-Request-Time'] = new Date().toISOString();
    
    console.log(`🔐 API Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error('🚫 Request interceptor error:', error);
    return Promise.reject(error);
  }
);

// Add response interceptor for error handling
api.interceptors.response.use(
  (response) => {
    console.log(`✅ API Response: ${response.status} ${response.config.url}`);
    return response;
  },
  (error) => {
    if (error.response?.status === 401) {
      console.error('🔒 Authentication failed - check API key');
      // Could trigger a re-authentication flow here
    } else if (error.response?.status === 403) {
      console.error('🚫 Access forbidden');
    } else if (error.response?.status === 429) {
      console.error('⏱️ Rate limited - too many requests');
    }
    console.error('❌ API Error:', error.response?.status, error.message);
    return Promise.reject(error);
  }
);

export const apiService = {
  /**
   * Get all actuator statuses
   */
  getActuators: async (): Promise<ActuatorStatus[]> => {
    const response = await api.get('/api/actuators');
    return response.data.actuators;
  },

  /**
   * Control an actuator
   */
  controlActuator: async (
    actuatorId: string,
    state: string,
    value?: number
  ): Promise<ActuatorStatus> => {
    const response = await api.post(`/api/actuators/${actuatorId}`, {
      state,
      value
    });
    return response.data.actuator;
  },

  /**
   * Get system status
   */
  getSystemStatus: async (): Promise<SystemStatus> => {
    const response = await api.get('/api/status');
    return response.data;
  },

  /**
   * Get recent decisions
   */
  getRecentDecisions: async (limit: number = 50): Promise<DecisionLog[]> => {
    const response = await api.get('/api/decisions', {
      params: { limit }
    });
    return response.data.decisions;
  },

  /**
   * Get sensor configuration
   */
  getSensorConfig: async (): Promise<SensorConfig> => {
    const response = await api.get('/api/sensors/config');
    return response.data;
  },

  /**
   * Override sensor value (for testing)
   */
  overrideSensorValue: async (
    deviceId: string,
    location: string,
    sensorType: string,
    value: number | string
  ): Promise<any> => {
    const response = await api.post('/api/sensor-override', {
      device_id: deviceId,
      location: location,
      readings: [
        {
          sensor_type: sensorType,
          value: value,
          unit: ''
        }
      ]
    });
    return response.data;
  },

  /**
   * Get statistics for a sensor type
   */
  getSensorStatistics: async (
    sensorType: string,
    location?: string
  ): Promise<any> => {
    const response = await api.get('/api/statistics', {
      params: {
        sensor_type: sensorType,
        location
      }
    });
    return response.data;
  }
};

export default apiService;
