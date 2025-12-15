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
  version?: string;
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

export interface SensorAggregate {
  sensor_type: string;
  count: number;
  avg: number | null;
  min: number | null;
  max: number | null;
}

export interface ActuatorUsage {
  actuator_id: string;
  count: number;
  states: string[];
}

export interface DecisionSummary {
  total: number;
  last_hours: number;
}

export interface ModelStatus {
  loaded: boolean;
  last_trained: string | null;
  samples: number;
  features: string[];
  algorithm: string;
  f1: number | null;
  version?: number;
  training_window_hours?: number;
  drift_score?: number | null;
  drift_checked_at?: string | null;
  next_retrain_at?: string | null;
  baseline_stats?: Record<string, { mean: number; std: number }>;
}

export interface AnalyticsSummary {
  sensor_summary: SensorAggregate[];
  actuator_usage: ActuatorUsage[];
  decision_summary: DecisionSummary;
  gateway_statistics: {
    total_processed: number;
    batches_with_outliers: number;
    total_outliers_filtered: number;
    filter_rate: number;
  };
  model_status: ModelStatus;
}

export interface AnalyticsExport {
  readings_csv: string;
  commands_csv: string;
}

export interface AnalyticsExportXlsx {
  xlsx_base64: string;
}

export interface AnalyticsExportParquet {
  readings_parquet_base64: string;
  commands_parquet_base64: string;
  gateway_parquet_base64: string;
}

export interface AnalyticsCharts {
  charts: {
    sensor_avg?: string;
    actuator_counts?: string;
  };
}

export interface GatewayStats {
  total_processed: number;
  total_outliers: number;
  filter_rate: number;
  recent_logs?: any[];
}
