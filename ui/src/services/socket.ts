/**
 * WebSocket service for real-time updates with security
 */
import { io, Socket } from 'socket.io-client';
import type { SensorData, ActuatorStatus, DecisionLog } from '../types';
import { securityService } from './security';

const SOCKET_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

class SocketService {
  private socket: Socket | null = null;
  private listeners: Map<string, Set<Function>> = new Map();
  private connectionAttempts: number = 0;
  private maxConnectionAttempts: number = 5;

  connect() {
    if (this.socket?.connected) {
      return;
    }

    console.log('🔌 Connecting to secure WebSocket server...');
    
    // Get security configuration
    const authOptions = securityService.getSocketAuthOptions();
    const secureUrl = securityService.shouldUseHttps() 
      ? SOCKET_URL.replace('http://', 'https://')
      : SOCKET_URL;

    this.socket = io(secureUrl, {
      transports: ['websocket', 'polling'],
      reconnection: true,
      reconnectionDelay: 2000,
      reconnectionAttempts: this.maxConnectionAttempts,
      timeout: 10000,
      forceNew: true,
      ...authOptions
    });

    this.socket.on('connect', () => {
      console.log('✅ Connected to secure WebSocket server');
      this.connectionAttempts = 0;
      securityService.logSecurityEvent('WEBSOCKET_CONNECTED', {
        timestamp: new Date().toISOString(),
        socketId: this.socket?.id
      });
    });

    this.socket.on('disconnect', (reason) => {
      console.log(`🔌 Disconnected from WebSocket server: ${reason}`);
      securityService.logSecurityEvent('WEBSOCKET_DISCONNECTED', {
        timestamp: new Date().toISOString(),
        reason
      });
    });

    this.socket.on('connect_error', (error) => {
      this.connectionAttempts++;
      console.error(`❌ WebSocket connection error (attempt ${this.connectionAttempts}):`, error.message);
      
      if (this.connectionAttempts >= this.maxConnectionAttempts) {
        console.error('🚨 Max WebSocket connection attempts reached');
        securityService.logSecurityEvent('WEBSOCKET_MAX_RETRIES', {
          timestamp: new Date().toISOString(),
          attempts: this.connectionAttempts,
          error: error.message
        });
      }
    });

    this.socket.on('error', (error) => {
      console.error('⚠️ WebSocket error:', error);
      securityService.handleAuthError(error);
    });

    this.socket.on('sensor_update', (data: SensorData) => {
      this.emit('sensor_update', data);
    });

    this.socket.on('actuator_update', (data: ActuatorStatus) => {
      this.emit('actuator_update', data);
    });

    this.socket.on('decision_made', (data: DecisionLog) => {
      this.emit('decision_made', data);
    });

    this.socket.on('status_update', (data: any) => {
      this.emit('status_update', data);
    });
  }

  disconnect() {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
  }

  on(event: string, callback: Function) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    this.listeners.get(event)!.add(callback);
  }

  off(event: string, callback: Function) {
    const listeners = this.listeners.get(event);
    if (listeners) {
      listeners.delete(callback);
    }
  }

  private emit(event: string, data: any) {
    const listeners = this.listeners.get(event);
    if (listeners) {
      listeners.forEach(callback => callback(data));
    }
  }

  requestStatus() {
    if (this.socket?.connected) {
      this.socket.emit('request_status');
    }
  }

  isConnected(): boolean {
    return this.socket?.connected || false;
  }
}

export const socketService = new SocketService();
export default socketService;
