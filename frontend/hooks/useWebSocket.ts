/**
 * WebSocket Hook for Real-Time Dashboard Updates
 * 
 * Provides WebSocket connectivity for:
 * - Real-time activity feed updates
 * - Live metrics streaming
 * - Integration status notifications
 * - Critical event alerts
 * - Auto-reconnection and error handling
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import { useAuth } from './useAuth';

export interface WebSocketMessage {
  type: string;
  data?: any;
  timestamp: string;
  metric_type?: string;
}

export interface WebSocketConfig {
  autoConnect?: boolean;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
  subscriptions?: string[];
  endpoint?: 'dashboard' | 'activities' | 'integrations';
}

export interface WebSocketState {
  isConnected: boolean;
  isConnecting: boolean;
  error: string | null;
  lastMessage: WebSocketMessage | null;
  connectionCount: number;
}

const DEFAULT_CONFIG: Required<WebSocketConfig> = {
  autoConnect: true,
  reconnectInterval: 3000, // 3 seconds
  maxReconnectAttempts: 5,
  subscriptions: ['activities', 'metrics', 'integrations', 'alerts'],
  endpoint: 'dashboard'
};

export const useWebSocket = (config: WebSocketConfig = {}) => {
  const { user, token } = useAuth();
  const finalConfig = { ...DEFAULT_CONFIG, ...config };
  
  const [state, setState] = useState<WebSocketState>({
    isConnected: false,
    isConnecting: false,
    error: null,
    lastMessage: null,
    connectionCount: 0
  });

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const messageHandlersRef = useRef<Map<string, ((data: any) => void)[]>>(new Map());

  // Get WebSocket URL
  const getWebSocketUrl = useCallback(() => {
    const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    const wsUrl = baseUrl.replace('http', 'ws');
    const organizationId = user?.organization_id || 'default';
    const endpoint = finalConfig.endpoint;
    
    return `${wsUrl}/api/v1/ws/${endpoint}/${organizationId}?token=${token}`;
  }, [user?.organization_id, token, finalConfig.endpoint]);

  // Connect to WebSocket
  const connect = useCallback(() => {
    if (!user || !token) {
      setState(prev => ({ ...prev, error: 'Authentication required' }));
      return;
    }

    if (wsRef.current?.readyState === WebSocket.CONNECTING) {
      return; // Already connecting
    }

    setState(prev => ({ ...prev, isConnecting: true, error: null }));

    try {
      const url = getWebSocketUrl();
      wsRef.current = new WebSocket(url);

      wsRef.current.onopen = () => {
        console.log('WebSocket connected');
        setState(prev => ({ 
          ...prev, 
          isConnected: true, 
          isConnecting: false, 
          error: null 
        }));
        reconnectAttemptsRef.current = 0;

        // Send subscription preferences
        if (wsRef.current) {
          wsRef.current.send(JSON.stringify({
            type: 'subscribe',
            subscriptions: finalConfig.subscriptions
          }));
        }
      };

      wsRef.current.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          setState(prev => ({ ...prev, lastMessage: message }));

          // Call registered handlers
          const handlers = messageHandlersRef.current.get(message.type) || [];
          handlers.forEach(handler => {
            try {
              handler(message.data);
            } catch (error) {
              console.error('Error in message handler:', error);
            }
          });

          // Handle specific message types
          switch (message.type) {
            case 'connection_info':
              setState(prev => ({ 
                ...prev, 
                connectionCount: message.data?.total_connections || 0 
              }));
              break;
            case 'error':
              console.error('WebSocket error message:', message.data);
              break;
          }
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error);
        setState(prev => ({ 
          ...prev, 
          error: 'Connection error',
          isConnecting: false 
        }));
      };

      wsRef.current.onclose = (event) => {
        console.log('WebSocket closed:', event.code, event.reason);
        setState(prev => ({ 
          ...prev, 
          isConnected: false, 
          isConnecting: false 
        }));

        // Attempt reconnection if not closed intentionally
        if (event.code !== 1000 && reconnectAttemptsRef.current < finalConfig.maxReconnectAttempts) {
          reconnectAttemptsRef.current += 1;
          console.log(`Attempting to reconnect... (${reconnectAttemptsRef.current}/${finalConfig.maxReconnectAttempts})`);
          
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, finalConfig.reconnectInterval);
        } else if (reconnectAttemptsRef.current >= finalConfig.maxReconnectAttempts) {
          setState(prev => ({ 
            ...prev, 
            error: 'Maximum reconnection attempts reached' 
          }));
        }
      };

    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      setState(prev => ({ 
        ...prev, 
        error: 'Failed to connect',
        isConnecting: false 
      }));
    }
  }, [user, token, getWebSocketUrl, finalConfig]);

  // Disconnect WebSocket
  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (wsRef.current) {
      wsRef.current.close(1000, 'Intentional disconnect');
      wsRef.current = null;
    }

    setState(prev => ({ 
      ...prev, 
      isConnected: false, 
      isConnecting: false,
      error: null 
    }));
  }, []);

  // Send message to WebSocket
  const sendMessage = useCallback((message: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
      return true;
    }
    console.warn('WebSocket not connected, message not sent:', message);
    return false;
  }, []);

  // Subscribe to specific message types
  const subscribe = useCallback((messageType: string, handler: (data: any) => void) => {
    const handlers = messageHandlersRef.current.get(messageType) || [];
    handlers.push(handler);
    messageHandlersRef.current.set(messageType, handlers);

    // Return unsubscribe function
    return () => {
      const currentHandlers = messageHandlersRef.current.get(messageType) || [];
      const index = currentHandlers.indexOf(handler);
      if (index > -1) {
        currentHandlers.splice(index, 1);
        if (currentHandlers.length === 0) {
          messageHandlersRef.current.delete(messageType);
        } else {
          messageHandlersRef.current.set(messageType, currentHandlers);
        }
      }
    };
  }, []);

  // Request specific data updates
  const requestUpdate = useCallback((dataType: string) => {
    return sendMessage({
      type: 'request_update',
      data_type: dataType
    });
  }, [sendMessage]);

  // Update subscription preferences
  const updateSubscriptions = useCallback((subscriptions: string[]) => {
    return sendMessage({
      type: 'subscribe',
      subscriptions
    });
  }, [sendMessage]);

  // Auto-connect on mount if enabled
  useEffect(() => {
    if (finalConfig.autoConnect && user && token) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [finalConfig.autoConnect, user, token, connect, disconnect]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  return {
    ...state,
    connect,
    disconnect,
    sendMessage,
    subscribe,
    requestUpdate,
    updateSubscriptions,
    reconnectAttempts: reconnectAttemptsRef.current,
    maxReconnectAttempts: finalConfig.maxReconnectAttempts
  };
};