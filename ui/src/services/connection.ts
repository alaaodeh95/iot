/**
 * Connection service for testing and validating secure connections
 */
import { securityService } from './security';
import { apiService } from './api';

interface ConnectionTestResult {
  success: boolean;
  message: string;
  details?: any;
  timestamp: string;
}

interface SystemHealthCheck {
  api: ConnectionTestResult;
  websocket: ConnectionTestResult;
  authentication: ConnectionTestResult;
  overall: 'healthy' | 'degraded' | 'unhealthy';
}

class ConnectionService {
  private baseUrl: string;

  constructor() {
    this.baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:5000';
  }

  /**
   * Test API connection with authentication
   */
  async testApiConnection(): Promise<ConnectionTestResult> {
    try {
      console.log('🔍 Testing API connection...');
      
      const systemStatus = await apiService.getSystemStatus();
      
      return {
        success: true,
        message: 'API connection successful',
        details: {
          status: systemStatus.status,
          timestamp: systemStatus.timestamp,
          version: systemStatus.version || 'Unknown'
        },
        timestamp: new Date().toISOString()
      };
    } catch (error: any) {
      let message = 'API connection failed';
      let details = {};

      if (error.response?.status === 401) {
        message = 'Authentication failed - invalid API key';
        details = { 
          status: error.response.status,
          suggestion: 'Check VITE_API_KEY environment variable'
        };
      } else if (error.response?.status === 403) {
        message = 'Access forbidden';
        details = { status: error.response.status };
      } else if (error.code === 'ECONNREFUSED') {
        message = 'Connection refused - server may be offline';
        details = { code: error.code };
      } else if (error.code === 'TIMEOUT') {
        message = 'Connection timeout';
        details = { code: error.code };
      } else {
        details = { 
          message: error.message,
          code: error.code,
          status: error.response?.status
        };
      }

      return {
        success: false,
        message,
        details,
        timestamp: new Date().toISOString()
      };
    }
  }

  /**
   * Test WebSocket connection
   */
  async testWebSocketConnection(): Promise<ConnectionTestResult> {
    try {
      console.log('🔍 Testing WebSocket connection...');
      
      // Simple WebSocket test using native WebSocket API
      const wsUrl = this.baseUrl.replace('http://', 'ws://').replace('https://', 'wss://') + '/socket.io/?EIO=4&transport=websocket';
      
      return new Promise((resolve) => {
        const timeout = setTimeout(() => {
          resolve({
            success: false,
            message: 'WebSocket connection timeout',
            details: { timeout: '5 seconds' },
            timestamp: new Date().toISOString()
          });
        }, 5000);

        try {
          const testWs = new WebSocket(wsUrl);
          
          testWs.onopen = () => {
            clearTimeout(timeout);
            testWs.close();
            resolve({
              success: true,
              message: 'WebSocket connection successful',
              details: { 
                url: wsUrl,
                readyState: 'OPEN'
              },
              timestamp: new Date().toISOString()
            });
          };

          testWs.onerror = (error) => {
            clearTimeout(timeout);
            resolve({
              success: false,
              message: 'WebSocket connection failed',
              details: { 
                error: 'Connection error',
                url: wsUrl
              },
              timestamp: new Date().toISOString()
            });
          };

          testWs.onclose = (event) => {
            if (!event.wasClean) {
              clearTimeout(timeout);
              resolve({
                success: false,
                message: 'WebSocket connection closed unexpectedly',
                details: { 
                  code: event.code,
                  reason: event.reason
                },
                timestamp: new Date().toISOString()
              });
            }
          };

        } catch (error: any) {
          clearTimeout(timeout);
          resolve({
            success: false,
            message: 'WebSocket setup failed',
            details: { error: error.message },
            timestamp: new Date().toISOString()
          });
        }
      });
      
    } catch (error: any) {
      return {
        success: false,
        message: 'WebSocket test failed',
        details: { error: error.message },
        timestamp: new Date().toISOString()
      };
    }
  }

  /**
   * Test authentication with current API key
   */
  async testAuthentication(): Promise<ConnectionTestResult> {
    try {
      console.log('🔍 Testing authentication...');
      
      const validation = await securityService.validateApiKey(this.baseUrl);
      
      return {
        success: validation.valid,
        message: validation.message,
        details: {
          serverTime: validation.serverTime,
          version: validation.version,
          apiKey: securityService.getApiKey().slice(0, 8) + '...' // Show only first 8 chars
        },
        timestamp: new Date().toISOString()
      };
    } catch (error: any) {
      return {
        success: false,
        message: 'Authentication test failed',
        details: { error: error.message },
        timestamp: new Date().toISOString()
      };
    }
  }

  /**
   * Perform comprehensive system health check
   */
  async performHealthCheck(): Promise<SystemHealthCheck> {
    console.log('🏥 Performing system health check...');

    const [api, websocket, authentication] = await Promise.all([
      this.testApiConnection(),
      this.testWebSocketConnection(),
      this.testAuthentication()
    ]);

    // Determine overall health
    let overall: 'healthy' | 'degraded' | 'unhealthy' = 'healthy';
    
    const failureCount = [api, websocket, authentication].filter(test => !test.success).length;
    
    if (failureCount === 0) {
      overall = 'healthy';
    } else if (failureCount === 1) {
      overall = 'degraded';
    } else {
      overall = 'unhealthy';
    }

    const healthCheck = {
      api,
      websocket,
      authentication,
      overall
    };

    console.log(`🏥 Health check complete: ${overall.toUpperCase()}`, healthCheck);
    
    return healthCheck;
  }

  /**
   * Get connection recommendations based on test results
   */
  getConnectionRecommendations(healthCheck: SystemHealthCheck): string[] {
    const recommendations: string[] = [];

    if (!healthCheck.api.success) {
      if (healthCheck.api.details?.status === 401) {
        recommendations.push('Update VITE_API_KEY environment variable with correct API key');
      } else if (healthCheck.api.details?.code === 'ECONNREFUSED') {
        recommendations.push('Start the IoT controller server (python backend/controller/main.py)');
      } else if (healthCheck.api.details?.code === 'TIMEOUT') {
        recommendations.push('Check network connectivity and server responsiveness');
      } else {
        recommendations.push('Verify IoT controller server is running and accessible');
      }
    }

    if (!healthCheck.websocket.success) {
      recommendations.push('Check WebSocket configuration and server support');
      recommendations.push('Verify CORS settings allow WebSocket connections');
    }

    if (!healthCheck.authentication.success) {
      recommendations.push('Verify API key configuration on both client and server');
      recommendations.push('Check security settings in backend configuration');
    }

    if (healthCheck.overall === 'healthy') {
      recommendations.push('All systems are functioning correctly');
    } else if (healthCheck.overall === 'degraded') {
      recommendations.push('Some features may be limited due to connection issues');
    } else {
      recommendations.push('Multiple system failures detected - check server status');
    }

    return recommendations;
  }
}

// Export singleton instance
export const connectionService = new ConnectionService();
export default connectionService;