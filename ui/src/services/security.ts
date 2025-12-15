/**
 * Security service for managing authentication and security features
 */

interface SecurityConfig {
  apiKey: string;
  enableHttps: boolean;
  socketAuth: boolean;
}

interface ApiKeyValidationResult {
  valid: boolean;
  message: string;
  serverTime?: string;
  version?: string;
}

class SecurityService {
  private config: SecurityConfig;

  constructor() {
    this.config = {
      apiKey: import.meta.env.VITE_API_KEY || 'iot-secure-api-key-2024',
      enableHttps: import.meta.env.VITE_ENABLE_HTTPS === 'true',
      socketAuth: import.meta.env.VITE_SOCKET_AUTH === 'true'
    };
  }

  /**
   * Get the current API key
   */
  getApiKey(): string {
    return this.config.apiKey;
  }

  /**
   * Get security configuration
   */
  getConfig(): SecurityConfig {
    return { ...this.config };
  }

  /**
   * Validate API key with the server
   */
  async validateApiKey(baseUrl: string): Promise<ApiKeyValidationResult> {
    try {
      const response = await fetch(`${baseUrl}/api/status`, {
        method: 'GET',
        headers: {
          'X-API-Key': this.config.apiKey,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        return {
          valid: true,
          message: 'API key validation successful',
          serverTime: data.timestamp,
          version: data.version
        };
      } else if (response.status === 401) {
        return {
          valid: false,
          message: 'Invalid API key - authentication failed'
        };
      } else {
        return {
          valid: false,
          message: `Server error: ${response.status}`
        };
      }
    } catch (error) {
      return {
        valid: false,
        message: `Connection error: ${error instanceof Error ? error.message : 'Unknown error'}`
      };
    }
  }

  /**
   * Get secure headers for API requests
   */
  getSecureHeaders(): Record<string, string> {
    return {
      'X-API-Key': this.config.apiKey,
      'Content-Type': 'application/json',
      'User-Agent': 'IoT-Dashboard/1.0',
      'X-Request-Time': new Date().toISOString()
    };
  }

  /**
   * Get WebSocket auth options
   */
  getSocketAuthOptions(): any {
    if (!this.config.socketAuth) {
      return {};
    }

    return {
      auth: {
        'x-api-key': this.config.apiKey
      },
      extraHeaders: {
        'X-API-Key': this.config.apiKey,
        'User-Agent': 'IoT-Dashboard/1.0'
      }
    };
  }

  /**
   * Check if HTTPS should be used
   */
  shouldUseHttps(): boolean {
    return this.config.enableHttps;
  }

  /**
   * Get the appropriate protocol
   */
  getProtocol(): string {
    return this.shouldUseHttps() ? 'https' : 'http';
  }

  /**
   * Get the appropriate WebSocket protocol
   */
  getWebSocketProtocol(): string {
    return this.shouldUseHttps() ? 'wss' : 'ws';
  }

  /**
   * Update API key (useful for testing or key rotation)
   */
  updateApiKey(newKey: string): void {
    this.config.apiKey = newKey;
    console.log('🔑 API key updated');
  }

  /**
   * Log security event
   */
  logSecurityEvent(event: string, details: any): void {
    console.log(`🛡️ Security Event: ${event}`, details);
  }

  /**
   * Handle authentication error
   */
  handleAuthError(error: any): void {
    console.error('🚫 Authentication Error:', error);
    
    if (error.response?.status === 401) {
      this.logSecurityEvent('AUTH_FAILED', {
        timestamp: new Date().toISOString(),
        message: 'API key authentication failed',
        suggestion: 'Check VITE_API_KEY environment variable'
      });
    } else if (error.response?.status === 403) {
      this.logSecurityEvent('ACCESS_DENIED', {
        timestamp: new Date().toISOString(),
        message: 'Access forbidden',
        suggestion: 'Check user permissions'
      });
    } else if (error.response?.status === 429) {
      this.logSecurityEvent('RATE_LIMITED', {
        timestamp: new Date().toISOString(),
        message: 'Rate limit exceeded',
        suggestion: 'Reduce request frequency'
      });
    }
  }
}

// Export singleton instance
export const securityService = new SecurityService();
export default securityService;
