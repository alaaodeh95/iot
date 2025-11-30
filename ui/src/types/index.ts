/**
 * Type definitions for IoT Smart Home Dashboard
 */

export interface SensorReading {
  sensor_type: string;
  value: number | string;
  unit: string;
  object_name?: string;
}

export interface SensorData {
  device_id: string;
  location: string;
  readings: SensorReading[];
  timestamp: string;
  format?: 'json' | 'xml';
}

export interface ActuatorStatus {
  actuator_id: string;
  actuator_type: string;
  state: string;
  value?: number;
  location: string;
  last_updated: string;
}

export interface DecisionLog {
  decision_id: string;
  trigger_sensor: string;
  trigger_value: any;
  condition: string;
  actions: ActuatorCommand[];
  timestamp: string;
}

export interface ActuatorCommand {
  actuator_id: string;
  actuator_type: string;
  state: string;
  value?: number;
  reason: string;
  timestamp: string;
  triggered_by: string;
}

export interface SystemStatus {
  status: string;
  timestamp: string;
  sensors: {
    total_readings: number;
    readings_last_hour: number;
  };
  actuators: {
    total: number;
    active: number;
    states: Record<string, string>;
  };
  decisions: {
    total: number;
    decisions_last_hour: number;
  };
}

export interface SensorConfig {
  sensors: Record<string, {
    type: string;
    location: string;
    sensors: string[];
    update_interval: number;
    gateway_enabled: boolean;
  }>;
  ranges: Record<string, {
    min?: number;
    max?: number;
    unit: string;
    values?: string[];
  }>;
  object_types: string[];
}

export interface GatewayStats {
  total_processed: number;
  total_outliers: number;
  filter_rate: number;
  recent_logs?: any[];
}
