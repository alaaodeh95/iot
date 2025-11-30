/**
 * WebSocket service for real-time updates
 */
import { io, Socket } from 'socket.io-client';
import type { SensorData, ActuatorStatus, DecisionLog } from '../types';

const SOCKET_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

class SocketService {
  private socket: Socket | null = null;
  private listeners: Map<string, Set<Function>> = new Map();

  connect() {
    if (this.socket?.connected) {
      return;
    }

    this.socket = io(SOCKET_URL, {
      transports: ['websocket', 'polling'],
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionAttempts: 5
    });

    this.socket.on('connect', () => {
      console.log('Connected to WebSocket server');
    });

    this.socket.on('disconnect', () => {
      console.log('Disconnected from WebSocket server');
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
