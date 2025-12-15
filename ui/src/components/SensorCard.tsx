/**
 * Sensor Card Component
 * Displays individual sensor readings with sliders for manual control
 */
import React, { useState } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Slider,
  Box,
  Chip,
  Switch,
  FormControlLabel,
  Tooltip
} from '@mui/material';
import {
  Thermostat,
  WaterDrop,
  LightMode,
  DirectionsRun,
  Cloud,
  Sensors,
  Warning,
  CheckCircle,
  VolumeUp,
  Vibration,
  Bolt,
  WbSunny,
  Opacity
} from '@mui/icons-material';
import type { SensorReading } from '../types';

interface SensorCardProps {
  deviceId: string;
  location: string;
  reading: SensorReading;
  format?: 'json' | 'xml';
  onValueChange?: (sensorType: string, value: number) => void;
}

const getSensorIcon = (sensorType: string) => {
  const iconProps = { sx: { fontSize: 40 } };
  
  switch (sensorType) {
    case 'temperature':
      return <Thermostat {...iconProps} color="error" />;
    case 'humidity':
      return <WaterDrop {...iconProps} color="info" />;
    case 'light':
      return <LightMode {...iconProps} color="warning" />;
    case 'motion':
      return <DirectionsRun {...iconProps} color="success" />;
    case 'pressure':
      return <Cloud {...iconProps} color="primary" />;
    case 'co2':
    case 'gas':
      return <Warning {...iconProps} color="warning" />;
    case 'sound':
      return <VolumeUp {...iconProps} color="secondary" />;
    case 'vibration':
      return <Vibration {...iconProps} color="info" />;
    case 'energy':
      return <Bolt {...iconProps} color="warning" />;
    case 'uv':
      return <WbSunny {...iconProps} color="warning" />;
    case 'rain':
      return <Opacity {...iconProps} color="info" />;
    case 'glass_break':
      return <Warning {...iconProps} color="error" />;
    case 'pressure_mat':
      return <DirectionsRun {...iconProps} color="success" />;
    default:
      return <Sensors {...iconProps} color="action" />;
  }
};

const getSensorColor = (sensorType: string, value: number | string): string => {
  if (typeof value !== 'number') return 'info';
  
  switch (sensorType) {
    case 'temperature':
      if (value > 30) return 'error';
      if (value < 18) return 'info';
      return 'success';
    case 'humidity':
      if (value > 70 || value < 30) return 'warning';
      return 'success';
    case 'co2':
    case 'gas':
      if (value > 1000) return 'error';
      if (value > 800) return 'warning';
      return 'success';
    case 'light':
      if (value < 200) return 'info';
      return 'success';
    case 'sound':
      if (value >= 95) return 'error';
      if (value >= 75) return 'warning';
      return 'success';
    case 'vibration':
      if (value >= 0.6) return 'error';
      if (value >= 0.3) return 'warning';
      return 'success';
    case 'energy':
      if (value >= 2500) return 'error';
      if (value >= 1500) return 'warning';
      return 'success';
    case 'uv':
      if (value >= 8) return 'warning';
      return 'success';
    case 'rain':
    case 'glass_break':
    case 'pressure_mat':
      return value === 1 ? 'warning' : 'info';
    default:
      return 'info';
  }
};

const getValueDisplay = (value: number | string, unit: string): string => {
  if (typeof value === 'number') {
    return `${value.toFixed(1)} ${unit}`;
  }
  if (typeof value === 'string') return value;
  return value === 1 ? 'ON' : 'OFF';
};

const getSensorRange = (sensorType: string): { min: number; max: number } => {
  const ranges: Record<string, { min: number; max: number }> = {
    temperature: { min: 15, max: 40 },
    humidity: { min: 20, max: 80 },
    pressure: { min: 980, max: 1040 },
    light: { min: 0, max: 1000 },
    co2: { min: 400, max: 2500 },
    gas: { min: 0, max: 2000 },
    distance: { min: 5, max: 400 },
    signal_strength: { min: -90, max: -20 },
    sound: { min: 20, max: 120 },
    vibration: { min: 0, max: 2 },
    energy: { min: 0, max: 5000 },
    uv: { min: 0, max: 15 },
    rain: { min: 0, max: 1 },
    glass_break: { min: 0, max: 1 },
    pressure_mat: { min: 0, max: 1 }
  };
  
  return ranges[sensorType] || { min: 0, max: 100 };
};

export const SensorCard: React.FC<SensorCardProps> = ({
  deviceId,
  location,
  reading,
  format = 'json',
  onValueChange
}) => {
  const [manualMode, setManualMode] = useState(false);
  const [manualValue, setManualValue] = useState<number>(
    typeof reading.value === 'number' ? reading.value : 0
  );

  const isNumeric = typeof reading.value === 'number';
  const range = getSensorRange(reading.sensor_type);
  const color = getSensorColor(reading.sensor_type, reading.value);

  const handleSliderChange = (_event: Event, newValue: number | number[]) => {
    const value = Array.isArray(newValue) ? newValue[0] : newValue;
    setManualValue(value);
  };

  const handleSliderCommit = (_event: React.SyntheticEvent | Event, newValue: number | number[]) => {
    const value = Array.isArray(newValue) ? newValue[0] : newValue;
    if (onValueChange) {
      onValueChange(reading.sensor_type, value);
    }
  };

  const handleManualModeToggle = (event: React.ChangeEvent<HTMLInputElement>) => {
    setManualMode(event.target.checked);
    if (!event.target.checked && onValueChange) {
      // Reset to automatic mode
      onValueChange(reading.sensor_type, -999); // Special value to clear override
    }
  };

  return (
    <Card 
      sx={{ 
        height: '100%',
        position: 'relative',
        border: `2px solid`,
        borderColor: `${color}.main`,
        transition: 'all 0.3s ease',
        '&:hover': {
          boxShadow: 6,
          transform: 'translateY(-4px)'
        }
      }}
    >
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', mb: 2 }}>
          <Box>
            <Typography variant="h6" component="div" gutterBottom>
              {reading.sensor_type.replace(/_/g, ' ').toUpperCase()}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              {location} • {deviceId}
            </Typography>
          </Box>
          <Box sx={{ textAlign: 'right' }}>
            {getSensorIcon(reading.sensor_type)}
            <Box sx={{ mt: 1 }}>
              <Chip 
                label={format.toUpperCase()} 
                size="small" 
                color={format === 'xml' ? 'secondary' : 'primary'}
                sx={{ fontSize: '0.7rem' }}
              />
            </Box>
          </Box>
        </Box>

        <Box sx={{ textAlign: 'center', my: 3 }}>
          <Typography variant="h3" component="div" color={`${color}.main`}>
            {manualMode && isNumeric ? manualValue.toFixed(1) : 
             getValueDisplay(reading.value, reading.unit)}
          </Typography>
          {reading.object_name && (
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              Object: {reading.object_name}
            </Typography>
          )}
        </Box>

        {isNumeric && onValueChange && (
          <Box sx={{ mt: 2 }}>
            <FormControlLabel
              control={
                <Switch
                  checked={manualMode}
                  onChange={handleManualModeToggle}
                  size="small"
                />
              }
              label={
                <Typography variant="caption">
                  Manual Control
                </Typography>
              }
            />
            
            {manualMode && (
              <Box sx={{ px: 1, mt: 1 }}>
                <Slider
                  value={manualValue}
                  onChange={handleSliderChange}
                  onChangeCommitted={handleSliderCommit}
                  min={range.min}
                  max={range.max}
                  step={(range.max - range.min) / 100}
                  valueLabelDisplay="auto"
                  marks={[
                    { value: range.min, label: String(range.min) },
                    { value: range.max, label: String(range.max) }
                  ]}
                />
              </Box>
            )}
          </Box>
        )}

        <Box sx={{ mt: 2, display: 'flex', justifyContent: 'center' }}>
          <Tooltip title={`Status: ${color}`}>
            <CheckCircle color={color as any} fontSize="small" />
          </Tooltip>
        </Box>
      </CardContent>
    </Card>
  );
};

export default SensorCard;
