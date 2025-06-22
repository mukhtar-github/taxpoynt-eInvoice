/**
 * Real-Time Dashboard Component
 * 
 * Features:
 * - Live metrics updates via WebSocket
 * - Real-time activity feed streaming
 * - Integration status monitoring
 * - Critical event notifications
 * - Auto-refresh controls
 * - Connection status indicators
 */

import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardHeader, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Switch } from '@/components/ui/Switch';
import ConnectedActivityFeed from './ConnectedActivityFeed';
import { useWebSocket } from '@/hooks/useWebSocket';
import { 
  Activity, 
  Wifi, 
  WifiOff, 
  RefreshCw, 
  Bell, 
  Settings,
  Zap,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Pause,
  Play
} from 'lucide-react';
import { cn } from '@/utils/cn';

interface RealTimeDashboardProps {
  className?: string;
  defaultAutoRefresh?: boolean;
  refreshInterval?: number;
}

interface DashboardMetrics {
  total_irns: number;
  active_irns: number;
  total_validations: number;
  success_rate: number;
  active_integrations: number;
  total_requests: number;
  error_rate: number;
  avg_response_time: number;
}

export const RealTimeDashboard: React.FC<RealTimeDashboardProps> = ({
  className = '',
  defaultAutoRefresh = true,
  refreshInterval = 30000
}) => {
  const [autoRefresh, setAutoRefresh] = useState(defaultAutoRefresh);
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [notifications, setNotifications] = useState<any[]>([]);
  const [showNotifications, setShowNotifications] = useState(false);

  // WebSocket connection for real-time updates
  const {
    isConnected,
    isConnecting,
    error: wsError,
    lastMessage,
    connectionCount,
    connect,
    disconnect,
    subscribe,
    requestUpdate
  } = useWebSocket({
    autoConnect: autoRefresh,
    subscriptions: ['metrics', 'activities', 'alerts', 'integrations']
  });

  // Handle real-time metric updates
  useEffect(() => {
    const unsubscribeMetrics = subscribe('metrics_update', (data) => {
      console.log('Received metrics update:', data);
      if (data && data.irn_summary) {
        setMetrics({
          total_irns: data.irn_summary.total_irns || 0,
          active_irns: data.irn_summary.active_irns || 0,
          total_validations: data.validation_summary?.total_validations || 0,
          success_rate: data.validation_summary?.success_rate || 0,
          active_integrations: data.odoo_summary?.active_integrations || 0,
          total_requests: data.system_summary?.total_requests || 0,
          error_rate: data.system_summary?.error_rate || 0,
          avg_response_time: data.system_summary?.avg_response_time || 0
        });
      }
    });

    const unsubscribeAlerts = subscribe('critical_alert', (data) => {
      console.log('Received critical alert:', data);
      const notification = {
        id: Date.now(),
        type: data.alert_type || 'alert',
        title: data.title || 'Alert',
        message: data.message || '',
        severity: data.severity || 'medium',
        timestamp: new Date().toISOString()
      };
      
      setNotifications(prev => [notification, ...prev.slice(0, 9)]); // Keep last 10
      
      // Show browser notification if supported
      if (Notification.permission === 'granted') {
        new Notification(notification.title, {
          body: notification.message,
          icon: '/icons/favicon.svg'
        });
      }
    });

    return () => {
      unsubscribeMetrics();
      unsubscribeAlerts();
    };
  }, [subscribe]);

  // Handle auto-refresh toggle
  const handleAutoRefreshToggle = useCallback(() => {
    setAutoRefresh(prev => {
      const newValue = !prev;
      if (newValue) {
        connect();
      } else {
        disconnect();
      }
      return newValue;
    });
  }, [connect, disconnect]);

  // Manual refresh
  const handleManualRefresh = useCallback(() => {
    requestUpdate('metrics');
    requestUpdate('activities');
  }, [requestUpdate]);

  // Request notification permission
  useEffect(() => {
    if ('Notification' in window && Notification.permission === 'default') {
      Notification.requestPermission();
    }
  }, []);

  // Connection status indicator
  const getConnectionStatus = () => {
    if (isConnecting) {
      return {
        icon: RefreshCw,
        color: 'text-yellow-500',
        bgColor: 'bg-yellow-100',
        label: 'Connecting...',
        description: 'Establishing real-time connection'
      };
    }
    
    if (isConnected) {
      return {
        icon: Wifi,
        color: 'text-green-500',
        bgColor: 'bg-green-100',
        label: 'Connected',
        description: `Live updates enabled • ${connectionCount} active connections`
      };
    }
    
    if (wsError) {
      return {
        icon: WifiOff,
        color: 'text-red-500',
        bgColor: 'bg-red-100',
        label: 'Connection Error',
        description: wsError
      };
    }
    
    return {
      icon: WifiOff,
      color: 'text-gray-500',
      bgColor: 'bg-gray-100',
      label: 'Disconnected',
      description: 'Real-time updates disabled'
    };
  };

  const connectionStatus = getConnectionStatus();
  const StatusIcon = connectionStatus.icon;

  return (
    <div className={cn('space-y-6', className)}>
      {/* Real-Time Controls Header */}
      <Card>
        <CardHeader className="pb-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className={cn(
                'flex items-center justify-center w-10 h-10 rounded-lg',
                connectionStatus.bgColor
              )}>
                <StatusIcon className={cn('w-5 h-5', connectionStatus.color)} />
              </div>
              <div>
                <h2 className="text-xl font-semibold flex items-center gap-2">
                  Real-Time Dashboard
                  <Badge 
                    variant={isConnected ? 'success' : 'secondary'}
                    className="text-xs"
                  >
                    {connectionStatus.label}
                  </Badge>
                </h2>
                <p className="text-sm text-gray-600">
                  {connectionStatus.description}
                </p>
              </div>
            </div>
            
            <div className="flex items-center gap-4">
              {/* Notifications */}
              <div className="relative">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowNotifications(!showNotifications)}
                  className="relative"
                >
                  <Bell className="w-4 h-4" />
                  {notifications.length > 0 && (
                    <div className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 text-white text-xs rounded-full flex items-center justify-center">
                      {notifications.length > 9 ? '9+' : notifications.length}
                    </div>
                  )}
                </Button>
                
                {showNotifications && (
                  <div className="absolute right-0 top-full mt-2 w-80 bg-white border rounded-lg shadow-lg z-50 max-h-96 overflow-y-auto">
                    <div className="p-3 border-b">
                      <h3 className="font-semibold">Recent Notifications</h3>
                    </div>
                    {notifications.length === 0 ? (
                      <div className="p-4 text-center text-gray-500">
                        No notifications
                      </div>
                    ) : (
                      notifications.map(notification => (
                        <div key={notification.id} className="p-3 border-b last:border-b-0">
                          <div className="flex items-start gap-2">
                            <AlertTriangle className="w-4 h-4 text-orange-500 mt-0.5 flex-shrink-0" />
                            <div className="flex-1">
                              <div className="font-medium text-sm">{notification.title}</div>
                              <div className="text-xs text-gray-600">{notification.message}</div>
                              <div className="text-xs text-gray-400 mt-1">
                                {new Date(notification.timestamp).toLocaleTimeString()}
                              </div>
                            </div>
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                )}
              </div>

              {/* Auto-refresh toggle */}
              <div className="flex items-center gap-2">
                <Switch
                  checked={autoRefresh}
                  onCheckedChange={handleAutoRefreshToggle}
                />
                <span className="text-sm text-gray-600">
                  {autoRefresh ? 'Auto-refresh On' : 'Auto-refresh Off'}
                </span>
              </div>

              {/* Manual refresh */}
              <Button
                variant="outline"
                size="sm"
                onClick={handleManualRefresh}
                disabled={isConnecting}
              >
                <RefreshCw className={cn('w-4 h-4', isConnecting && 'animate-spin')} />
                Refresh
              </Button>
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Live Metrics Cards */}
      {metrics && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Total IRNs</p>
                  <p className="text-2xl font-bold">{metrics.total_irns.toLocaleString()}</p>
                </div>
                <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
                  <Activity className="w-4 h-4 text-blue-600" />
                </div>
              </div>
              <div className="flex items-center gap-1 mt-2">
                <CheckCircle className="w-3 h-3 text-green-500" />
                <span className="text-xs text-green-600">
                  {metrics.active_irns} active
                </span>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Success Rate</p>
                  <p className="text-2xl font-bold">{metrics.success_rate.toFixed(1)}%</p>
                </div>
                <div className="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center">
                  <CheckCircle className="w-4 h-4 text-green-600" />
                </div>
              </div>
              <div className="flex items-center gap-1 mt-2">
                <span className="text-xs text-gray-600">
                  {metrics.total_validations} validations
                </span>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Integrations</p>
                  <p className="text-2xl font-bold">{metrics.active_integrations}</p>
                </div>
                <div className="w-8 h-8 bg-purple-100 rounded-lg flex items-center justify-center">
                  <Zap className="w-4 h-4 text-purple-600" />
                </div>
              </div>
              <div className="flex items-center gap-1 mt-2">
                <CheckCircle className="w-3 h-3 text-green-500" />
                <span className="text-xs text-green-600">All active</span>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Error Rate</p>
                  <p className="text-2xl font-bold">{metrics.error_rate.toFixed(1)}%</p>
                </div>
                <div className={cn(
                  'w-8 h-8 rounded-lg flex items-center justify-center',
                  metrics.error_rate > 5 ? 'bg-red-100' : 'bg-green-100'
                )}>
                  {metrics.error_rate > 5 ? (
                    <XCircle className="w-4 h-4 text-red-600" />
                  ) : (
                    <CheckCircle className="w-4 h-4 text-green-600" />
                  )}
                </div>
              </div>
              <div className="flex items-center gap-1 mt-2">
                <span className="text-xs text-gray-600">
                  {metrics.avg_response_time.toFixed(0)}ms avg
                </span>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Real-Time Activity Feed */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold flex items-center gap-2">
              <Activity className="w-5 h-5" />
              Live Activity Feed
            </h3>
            <div className="flex items-center gap-2">
              {isConnected && (
                <Badge variant="success" className="flex items-center gap-1">
                  <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                  Live
                </Badge>
              )}
            </div>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          <ConnectedActivityFeed
            maxHeight="500px"
            showFilter={true}
            pollInterval={autoRefresh ? refreshInterval : 0}
            pageSize={10}
          />
        </CardContent>
      </Card>
    </div>
  );
};

export default RealTimeDashboard;