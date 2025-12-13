/**
 * Security Status Component
 * Displays security connection status and health information
 */
import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Chip,
  Button,
  Alert,
  AlertTitle,
  CircularProgress,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Divider
} from '@mui/material';
import {
  Security,
  CheckCircle,
  Error,
  Warning,
  Refresh,
  ExpandMore,
  Wifi,
  Key,
  Shield,
  Lightbulb
} from '@mui/icons-material';
import { connectionService } from '../services/connection';
import { securityService } from '../services/security';

interface SystemHealthCheck {
  api: {
    success: boolean;
    message: string;
    details?: any;
    timestamp: string;
  };
  websocket: {
    success: boolean;
    message: string;
    details?: any;
    timestamp: string;
  };
  authentication: {
    success: boolean;
    message: string;
    details?: any;
    timestamp: string;
  };
  overall: 'healthy' | 'degraded' | 'unhealthy';
}

const SecurityStatus: React.FC = () => {
  const [healthCheck, setHealthCheck] = useState<SystemHealthCheck | null>(null);
  const [loading, setLoading] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<string>('');

  const runHealthCheck = async () => {
    setLoading(true);
    try {
      const result = await connectionService.performHealthCheck();
      setHealthCheck(result);
      setLastUpdate(new Date().toLocaleTimeString());
    } catch (error) {
      console.error('Health check failed:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    runHealthCheck();
  }, []);

  const getStatusColor = (success: boolean) => {
    return success ? 'success' : 'error';
  };

  const getStatusIcon = (success: boolean) => {
    return success ? <CheckCircle /> : <Error />;
  };

  const getOverallStatusColor = (overall: string) => {
    switch (overall) {
      case 'healthy': return 'success';
      case 'degraded': return 'warning';
      case 'unhealthy': return 'error';
      default: return 'default';
    }
  };

  const getOverallStatusIcon = (overall: string) => {
    switch (overall) {
      case 'healthy': return <CheckCircle />;
      case 'degraded': return <Warning />;
      case 'unhealthy': return <Error />;
      default: return <Security />;
    }
  };

  const securityConfig = securityService.getConfig();

  return (
    <Card elevation={3}>
      <CardContent>
        <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
          <Typography variant="h6" component="div" display="flex" alignItems="center" gap={1}>
            <Security />
            Security Status
          </Typography>
          <Button
            variant="outlined"
            size="small"
            startIcon={loading ? <CircularProgress size={16} /> : <Refresh />}
            onClick={runHealthCheck}
            disabled={loading}
          >
            {loading ? 'Testing...' : 'Test Connection'}
          </Button>
        </Box>

        {healthCheck && (
          <>
            {/* Overall Status */}
            <Box mb={3}>
              <Alert 
                severity={getOverallStatusColor(healthCheck.overall)} 
                icon={getOverallStatusIcon(healthCheck.overall)}
                sx={{ mb: 2 }}
              >
                <AlertTitle>
                  System Status: {healthCheck.overall.toUpperCase()}
                </AlertTitle>
                {healthCheck.overall === 'healthy' && 'All security systems are operational'}
                {healthCheck.overall === 'degraded' && 'Some systems have issues but core functionality works'}
                {healthCheck.overall === 'unhealthy' && 'Multiple system failures detected'}
              </Alert>
              
              {lastUpdate && (
                <Typography variant="caption" color="text.secondary">
                  Last updated: {lastUpdate}
                </Typography>
              )}
            </Box>

            {/* Individual System Status */}
            <Box mb={3}>
              <Typography variant="h6" gutterBottom>
                System Components
              </Typography>
              
              <Box display="flex" gap={1} flexWrap="wrap" mb={2}>
                <Chip
                  icon={getStatusIcon(healthCheck.api.success)}
                  label={`API ${healthCheck.api.success ? 'Connected' : 'Failed'}`}
                  color={getStatusColor(healthCheck.api.success)}
                  variant="outlined"
                />
                <Chip
                  icon={getStatusIcon(healthCheck.websocket.success)}
                  label={`WebSocket ${healthCheck.websocket.success ? 'Connected' : 'Failed'}`}
                  color={getStatusColor(healthCheck.websocket.success)}
                  variant="outlined"
                />
                <Chip
                  icon={getStatusIcon(healthCheck.authentication.success)}
                  label={`Auth ${healthCheck.authentication.success ? 'Valid' : 'Invalid'}`}
                  color={getStatusColor(healthCheck.authentication.success)}
                  variant="outlined"
                />
              </Box>
            </Box>

            {/* Detailed Results */}
            <Accordion>
              <AccordionSummary expandIcon={<ExpandMore />}>
                <Typography variant="subtitle1">Detailed Test Results</Typography>
              </AccordionSummary>
              <AccordionDetails>
                <List>
                  <ListItem>
                    <ListItemIcon>
                      <Wifi color={healthCheck.api.success ? 'success' : 'error'} />
                    </ListItemIcon>
                    <ListItemText
                      primary="API Connection"
                      secondary={
                        <Box>
                          <Typography variant="body2">{healthCheck.api.message}</Typography>
                          {healthCheck.api.details && (
                            <Typography variant="caption" color="text.secondary">
                              {JSON.stringify(healthCheck.api.details, null, 2)}
                            </Typography>
                          )}
                        </Box>
                      }
                    />
                  </ListItem>
                  
                  <Divider />
                  
                  <ListItem>
                    <ListItemIcon>
                      <Shield color={healthCheck.websocket.success ? 'success' : 'error'} />
                    </ListItemIcon>
                    <ListItemText
                      primary="WebSocket Connection"
                      secondary={
                        <Box>
                          <Typography variant="body2">{healthCheck.websocket.message}</Typography>
                          {healthCheck.websocket.details && (
                            <Typography variant="caption" color="text.secondary">
                              {JSON.stringify(healthCheck.websocket.details, null, 2)}
                            </Typography>
                          )}
                        </Box>
                      }
                    />
                  </ListItem>
                  
                  <Divider />
                  
                  <ListItem>
                    <ListItemIcon>
                      <Key color={healthCheck.authentication.success ? 'success' : 'error'} />
                    </ListItemIcon>
                    <ListItemText
                      primary="Authentication"
                      secondary={
                        <Box>
                          <Typography variant="body2">{healthCheck.authentication.message}</Typography>
                          {healthCheck.authentication.details && (
                            <Typography variant="caption" color="text.secondary">
                              {JSON.stringify(healthCheck.authentication.details, null, 2)}
                            </Typography>
                          )}
                        </Box>
                      }
                    />
                  </ListItem>
                </List>
              </AccordionDetails>
            </Accordion>

            {/* Security Configuration */}
            <Accordion>
              <AccordionSummary expandIcon={<ExpandMore />}>
                <Typography variant="subtitle1">Security Configuration</Typography>
              </AccordionSummary>
              <AccordionDetails>
                <List>
                  <ListItem>
                    <ListItemText
                      primary="API Key"
                      secondary={`${securityConfig.apiKey.slice(0, 12)}...`}
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemText
                      primary="HTTPS Enabled"
                      secondary={securityConfig.enableHttps ? 'Yes' : 'No'}
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemText
                      primary="WebSocket Auth"
                      secondary={securityConfig.socketAuth ? 'Enabled' : 'Disabled'}
                    />
                  </ListItem>
                </List>
              </AccordionDetails>
            </Accordion>

            {/* Recommendations */}
            <Accordion>
              <AccordionSummary expandIcon={<ExpandMore />}>
                <Typography variant="subtitle1">Recommendations</Typography>
              </AccordionSummary>
              <AccordionDetails>
                <List>
                  {connectionService.getConnectionRecommendations(healthCheck).map((recommendation, index) => (
                    <ListItem key={index}>
                      <ListItemIcon>
                        <Lightbulb />
                      </ListItemIcon>
                      <ListItemText primary={recommendation} />
                    </ListItem>
                  ))}
                </List>
              </AccordionDetails>
            </Accordion>
          </>
        )}

        {!healthCheck && !loading && (
          <Box textAlign="center" py={4}>
            <Typography variant="body1" color="text.secondary">
              Click "Test Connection" to check system status
            </Typography>
          </Box>
        )}
      </CardContent>
    </Card>
  );
};

export default SecurityStatus;