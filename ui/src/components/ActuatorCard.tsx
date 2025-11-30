/**
 * Actuator Card Component
 * Displays actuator status with manual controls
 */
import React from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Chip,
  IconButton,
  Tooltip
} from '@mui/material';
import {
  PowerSettingsNew,
  AcUnit,
  Whatshot,
  Air,
  LightbulbOutlined,
  Warning,
  Lock,
  LockOpen
} from '@mui/icons-material';
import type { ActuatorStatus } from '../types';

interface ActuatorCardProps {
  actuator: ActuatorStatus;
  onToggle?: (actuatorId: string, newState: string) => void;
}

const getActuatorIcon = (type: string, state: string) => {
  const iconProps = { sx: { fontSize: 48 } };
  const isActive = state !== 'off';
  
  switch (type) {
    case 'climate_control':
      if (state === 'heating') return <Whatshot {...iconProps} color="error" />;
      if (state === 'cooling') return <AcUnit {...iconProps} color="info" />;
      return <Air {...iconProps} color={isActive ? 'primary' : 'disabled'} />;
    case 'light':
      return <LightbulbOutlined {...iconProps} color={isActive ? 'warning' : 'disabled'} />;
    case 'alarm':
      return <Warning {...iconProps} color={isActive ? 'error' : 'disabled'} />;
    case 'lock':
      return state === 'locked' ? 
        <Lock {...iconProps} color="success" /> : 
        <LockOpen {...iconProps} color="warning" />;
    case 'fan':
    case 'motor':
    case 'appliance':
      return <Air {...iconProps} color={isActive ? 'primary' : 'disabled'} />;
    default:
      return <PowerSettingsNew {...iconProps} color={isActive ? 'success' : 'disabled'} />;
  }
};

const getStateColor = (state: string): "default" | "primary" | "secondary" | "error" | "info" | "success" | "warning" => {
  switch (state) {
    case 'off': return 'default';
    case 'on': return 'success';
    case 'heating': return 'error';
    case 'cooling': return 'info';
    case 'high': return 'error';
    case 'medium': return 'warning';
    case 'low': return 'info';
    case 'cleaning': return 'primary';
    case 'paused': return 'warning';
    case 'locked': return 'success';
    case 'unlocked': return 'warning';
    default: return 'primary';
  }
};

export const ActuatorCard: React.FC<ActuatorCardProps> = ({ actuator, onToggle }) => {
  const isActive = actuator.state !== 'off';
  const stateColor = getStateColor(actuator.state);

  const handleToggle = () => {
    if (onToggle) {
      const newState = isActive ? 'off' : 'on';
      onToggle(actuator.actuator_id, newState);
    }
  };

  return (
    <Card
      sx={{
        height: '100%',
        backgroundColor: isActive ? 'action.hover' : 'background.paper',
        border: `2px solid`,
        borderColor: isActive ? `${stateColor}.main` : 'divider',
        transition: 'all 0.3s ease',
        '&:hover': {
          boxShadow: 4,
          transform: 'translateY(-2px)'
        }
      }}
    >
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', mb: 2 }}>
          <Box>
            <Typography variant="h6" component="div" gutterBottom>
              {actuator.actuator_id.replace(/_/g, ' ').toUpperCase()}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              {actuator.location}
            </Typography>
          </Box>
          <Tooltip title={onToggle ? 'Click to toggle' : 'Automatic control'}>
            <IconButton
              onClick={handleToggle}
              disabled={!onToggle}
              sx={{
                backgroundColor: isActive ? `${stateColor}.main` : 'action.disabled',
                color: 'white',
                '&:hover': {
                  backgroundColor: isActive ? `${stateColor}.dark` : 'action.disabled',
                }
              }}
            >
              <PowerSettingsNew />
            </IconButton>
          </Tooltip>
        </Box>

        <Box sx={{ textAlign: 'center', my: 3 }}>
          {getActuatorIcon(actuator.actuator_type, actuator.state)}
        </Box>

        <Box sx={{ textAlign: 'center', mt: 2 }}>
          <Chip
            label={actuator.state.toUpperCase()}
            color={stateColor}
            sx={{ fontWeight: 'bold', mb: 1 }}
          />
          <Typography variant="caption" display="block" color="text.secondary">
            Type: {actuator.actuator_type}
          </Typography>
          {actuator.value !== undefined && actuator.value !== null && (
            <Typography variant="caption" display="block" color="text.secondary">
              Value: {actuator.value}
            </Typography>
          )}
        </Box>
      </CardContent>
    </Card>
  );
};

export default ActuatorCard;
