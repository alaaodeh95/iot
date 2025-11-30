/**
 * API service for communicating with the IoT backend
 */
import axios from 'axios';
import type { ActuatorStatus, SystemStatus, DecisionLog, SensorConfig } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
});

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
