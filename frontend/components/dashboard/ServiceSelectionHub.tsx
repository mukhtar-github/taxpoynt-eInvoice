/**
 * Service Selection Hub Component
 * 
 * Central dashboard that helps users choose between SI and APP services
 * with real-time data and clear value propositions
 */

import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Switch } from '@/components/ui/Switch';
import { 
  ArrowRight, 
  Database, 
  Shield, 
  FileText, 
  Users, 
  Package, 
  Activity, 
  CheckCircle, 
  XCircle, 
  Clock,
  TrendingUp,
  AlertTriangle,
  Zap,
  Bell,
  Wifi,
  WifiOff,
  RefreshCw
} from 'lucide-react';
import { useWebSocket } from '@/hooks/useWebSocket';
import { useAuth } from '@/context/AuthContext';
import { cn } from '@/utils/cn';
import { format } from 'date-fns';
import Link from 'next/link';

interface ServiceMetrics {
  si_services: {
    connected_erps: number;
    total_invoices: number;
    total_customers: number;
    total_products: number;
    last_sync: string | null;
    connection_status: 'connected' | 'disconnected' | 'pending';
    recent_activity_count: number;
  };
  app_services: {
    certificate_status: 'active' | 'expired' | 'expiring_soon';
    certificate_expiry: string;
    transmission_rate: number;
    compliance_score: number;
    active_transmissions: number;
    pending_issues: number;
  };
  system_health: {
    total_users: number;
    system_status: 'operational' | 'degraded' | 'down';
    uptime_percentage: number;
  };
}

export const ServiceSelectionHub: React.FC = () => {
  const { user } = useAuth();
  const [serviceMetrics, setServiceMetrics] = useState<ServiceMetrics | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());
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
    subscriptions: ['service_metrics', 'system_health', 'alerts']
  });

  // Handle real-time service updates
  useEffect(() => {
    const unsubscribeMetrics = subscribe('service_metrics_update', (data) => {
      console.log('Received service metrics update:', data);
      if (data && data.service_metrics) {
        setServiceMetrics(data.service_metrics);
        setLastUpdated(new Date());
      }
    });

    const unsubscribeHealth = subscribe('system_health_update', (data) => {
      console.log('Received system health update:', data);
      if (data && data.system_health) {
        setServiceMetrics(prev => prev ? {
          ...prev,
          system_health: data.system_health
        } : null);
        setLastUpdated(new Date());
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
      
      setNotifications(prev => [notification, ...prev.slice(0, 9)]);
      
      if (Notification.permission === 'granted') {
        new Notification(notification.title, {
          body: notification.message,
          icon: '/icons/favicon.svg'
        });
      }
    });

    return () => {
      unsubscribeMetrics();
      unsubscribeHealth();
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

  // Manual refresh function
  const handleManualRefresh = useCallback(() => {
    requestUpdate('service_metrics');
    requestUpdate('system_health');
    setLastUpdated(new Date());
  }, [requestUpdate]);

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
        label: 'Live',
        description: `Real-time updates active • ${connectionCount} connections`
      };
    }
    
    if (wsError) {
      return {
        icon: WifiOff,
        color: 'text-red-500',
        bgColor: 'bg-red-100',
        label: 'Error',
        description: wsError
      };
    }
    
    return {
      icon: WifiOff,
      color: 'text-gray-500',
      bgColor: 'bg-gray-100',
      label: 'Offline',
      description: 'Real-time updates disabled'
    };
  };

  const connectionStatus = getConnectionStatus();
  const StatusIcon = connectionStatus.icon;

  // Request notification permission
  useEffect(() => {
    if ('Notification' in window && Notification.permission === 'default') {
      Notification.requestPermission();
    }
  }, []);

  // Mock data for demonstration (replace with real API call)
  useEffect(() => {
    if (!serviceMetrics) {
      const mockMetrics: ServiceMetrics = {
        si_services: {
          connected_erps: 2,
          total_invoices: 543,
          total_customers: 128,
          total_products: 87,
          last_sync: new Date().toISOString(),
          connection_status: 'connected',
          recent_activity_count: 15
        },
        app_services: {
          certificate_status: 'active',
          certificate_expiry: '2026-01-15T00:00:00Z',
          transmission_rate: 98.2,
          compliance_score: 85,
          active_transmissions: 12,
          pending_issues: 2
        },
        system_health: {
          total_users: 1247,
          system_status: 'operational',
          uptime_percentage: 99.9
        }
      };
      setServiceMetrics(mockMetrics);
    }
  }, [serviceMetrics]);

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'Never';
    const date = new Date(dateString);
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
      hour12: true
    });
  };

  const getCertificateStatusBadge = (status: string) => {
    switch (status) {
      case 'active':
        return <Badge variant="success">Active</Badge>;
      case 'expiring_soon':
        return <Badge variant="warning">Expiring Soon</Badge>;
      case 'expired':
        return <Badge variant="destructive">Expired</Badge>;
      default:
        return <Badge variant="secondary">Unknown</Badge>;
    }
  };

  const getConnectionStatusIcon = (status: string) => {
    switch (status) {
      case 'connected':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'pending':
        return <Clock className="w-5 h-5 text-yellow-500" />;
      case 'disconnected':
        return <XCircle className="w-5 h-5 text-red-500" />;
      default:
        return <XCircle className="w-5 h-5 text-gray-400" />;
    }
  };

  return (
    <div className="space-y-6">
      {/* Real-Time Status Header */}
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
                <h1 className="text-2xl font-bold flex items-center gap-2">
                  Welcome to TaxPoynt eInvoice
                  <Badge 
                    variant={isConnected ? 'success' : 'secondary'}
                    className="text-xs"
                  >
                    {connectionStatus.label}
                  </Badge>
                </h1>
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
                  <Bell className="w-4 h-4 mr-1" />
                  Notifications
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
                  {autoRefresh ? 'Live' : 'Manual'}
                </span>
              </div>

              <Button 
                variant="outline" 
                size="sm"
                onClick={handleManualRefresh}
                disabled={isConnecting}
              >
                <RefreshCw className={cn('h-4 w-4 mr-1', isConnecting && 'animate-spin')} />
                Refresh
              </Button>
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Status indicators */}
      <div className="flex flex-wrap gap-2">
        <Badge variant="outline">Last updated: {format(lastUpdated, 'HH:mm:ss')}</Badge>
        {serviceMetrics && (
          <Badge variant="success" className="flex items-center gap-1">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
            Real-time Data
          </Badge>
        )}
        {user && (
          <Badge variant="secondary">Welcome back, {user.full_name || user.email}</Badge>
        )}
      </div>

      {/* Service Selection Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* System Integration (SI) Services */}
        <Card className="relative overflow-hidden border-l-4 border-l-blue-500 hover:shadow-lg transition-all duration-300">
          <CardHeader className="pb-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="p-3 bg-blue-100 rounded-lg">
                  <Database className="w-6 h-6 text-blue-600" />
                </div>
                <div>
                  <CardTitle className="text-xl">System Integration (SI)</CardTitle>
                  <p className="text-sm text-gray-600 mt-1">
                    Connect and manage your ERP systems
                  </p>
                </div>
              </div>
              {serviceMetrics && (
                <div className="flex items-center gap-2">
                  {getConnectionStatusIcon(serviceMetrics.si_services.connection_status)}
                  {serviceMetrics && (
                    <div className="flex items-center gap-1">
                      <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" />
                      <span className="text-xs text-blue-600">Live</span>
                    </div>
                  )}
                </div>
              )}
            </div>
          </CardHeader>
          
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="text-center p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center justify-center mb-2">
                  <FileText className="w-5 h-5 text-blue-600" />
                </div>
                <div className="font-semibold text-lg">
                  {serviceMetrics?.si_services.total_invoices.toLocaleString() || '0'}
                </div>
                <div className="text-xs text-gray-600">Invoices</div>
              </div>
              
              <div className="text-center p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center justify-center mb-2">
                  <Users className="w-5 h-5 text-emerald-600" />
                </div>
                <div className="font-semibold text-lg">
                  {serviceMetrics?.si_services.total_customers.toLocaleString() || '0'}
                </div>
                <div className="text-xs text-gray-600">Customers</div>
              </div>
              
              <div className="text-center p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center justify-center mb-2">
                  <Package className="w-5 h-5 text-amber-600" />
                </div>
                <div className="font-semibold text-lg">
                  {serviceMetrics?.si_services.total_products.toLocaleString() || '0'}
                </div>
                <div className="text-xs text-gray-600">Products</div>
              </div>
              
              <div className="text-center p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center justify-center mb-2">
                  <Activity className="w-5 h-5 text-purple-600" />
                </div>
                <div className="font-semibold text-lg">
                  {serviceMetrics?.si_services.recent_activity_count || '0'}
                </div>
                <div className="text-xs text-gray-600">Recent Activity</div>
              </div>
            </div>

            <div className="p-3 bg-blue-50 rounded-lg border border-blue-200">
              <div className="flex items-center justify-between">
                <div>
                  <div className="font-medium text-blue-800">
                    {serviceMetrics?.si_services.connected_erps || 0} ERP System(s) Connected
                  </div>
                  <div className="text-sm text-blue-600">
                    Last sync: {formatDate(serviceMetrics?.si_services.last_sync || null)}
                  </div>
                </div>
                <div className="flex items-center gap-1">
                  <Zap className="w-4 h-4 text-blue-600" />
                  <span className="text-sm font-medium text-blue-800">Active</span>
                </div>
              </div>
            </div>

            <Button 
              asChild 
              className="w-full bg-blue-600 hover:bg-blue-700 text-white"
              size="lg"
            >
              <Link href="/dashboard/si">
                Go to SI Dashboard
                <ArrowRight className="w-4 h-4 ml-2" />
              </Link>
            </Button>
          </CardContent>
        </Card>

        {/* Access Point Provider (APP) Services */}
        <Card className="relative overflow-hidden border-l-4 border-l-cyan-500 hover:shadow-lg transition-all duration-300">
          <CardHeader className="pb-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="p-3 bg-cyan-100 rounded-lg">
                  <Shield className="w-6 h-6 text-cyan-600" />
                </div>
                <div>
                  <CardTitle className="text-xl">Access Point Provider (APP)</CardTitle>
                  <p className="text-sm text-gray-600 mt-1">
                    Manage certificates, compliance & transmission
                  </p>
                </div>
              </div>
              {serviceMetrics && (
                <div className="flex items-center gap-2">
                  {getCertificateStatusBadge(serviceMetrics.app_services.certificate_status)}
                  {serviceMetrics && (
                    <div className="flex items-center gap-1">
                      <div className="w-2 h-2 bg-cyan-500 rounded-full animate-pulse" />
                      <span className="text-xs text-cyan-600">Live</span>
                    </div>
                  )}
                </div>
              )}
            </div>
          </CardHeader>
          
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="text-center p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center justify-center mb-2">
                  <TrendingUp className="w-5 h-5 text-cyan-600" />
                </div>
                <div className="font-semibold text-lg">
                  {serviceMetrics?.app_services.transmission_rate.toFixed(1) || '0'}%
                </div>
                <div className="text-xs text-gray-600">Transmission Rate</div>
              </div>
              
              <div className="text-center p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center justify-center mb-2">
                  <CheckCircle className="w-5 h-5 text-green-600" />
                </div>
                <div className="font-semibold text-lg">
                  {serviceMetrics?.app_services.compliance_score || '0'}%
                </div>
                <div className="text-xs text-gray-600">Compliance Score</div>
              </div>
              
              <div className="text-center p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center justify-center mb-2">
                  <Activity className="w-5 h-5 text-blue-600" />
                </div>
                <div className="font-semibold text-lg">
                  {serviceMetrics?.app_services.active_transmissions || '0'}
                </div>
                <div className="text-xs text-gray-600">Active Transmissions</div>
              </div>
              
              <div className="text-center p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center justify-center mb-2">
                  <AlertTriangle className="w-5 h-5 text-amber-600" />
                </div>
                <div className="font-semibold text-lg">
                  {serviceMetrics?.app_services.pending_issues || '0'}
                </div>
                <div className="text-xs text-gray-600">Pending Issues</div>
              </div>
            </div>

            <div className="p-3 bg-cyan-50 rounded-lg border border-cyan-200">
              <div className="flex items-center justify-between">
                <div>
                  <div className="font-medium text-cyan-800">
                    Certificate Status: {serviceMetrics?.app_services.certificate_status || 'Active'}
                  </div>
                  <div className="text-sm text-cyan-600">
                    Expires: {formatDate(serviceMetrics?.app_services.certificate_expiry || null)}
                  </div>
                </div>
                <div className="flex items-center gap-1">
                  <Shield className="w-4 h-4 text-cyan-600" />
                  <span className="text-sm font-medium text-cyan-800">Secure</span>
                </div>
              </div>
            </div>

            <Button 
              asChild 
              className="w-full bg-cyan-600 hover:bg-cyan-700 text-white"
              size="lg"
            >
              <Link href="/dashboard/app">
                Go to APP Dashboard
                <ArrowRight className="w-4 h-4 ml-2" />
              </Link>
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* Quick Access Section */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Zap className="w-5 h-5" />
            Quick Access
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <Button variant="outline" className="h-auto py-3 px-4 justify-start" asChild>
              <Link href="/dashboard/metrics">
                <Activity className="h-4 w-4 mr-2" />
                Analytics & Reports
              </Link>
            </Button>
            
            <Button variant="outline" className="h-auto py-3 px-4 justify-start" asChild>
              <Link href="/dashboard/submission">
                <FileText className="h-4 w-4 mr-2" />
                FIRS Submissions
              </Link>
            </Button>
            
            <Button variant="outline" className="h-auto py-3 px-4 justify-start" asChild>
              <Link href="/dashboard/organization">
                <Users className="h-4 w-4 mr-2" />
                Organization Settings
              </Link>
            </Button>
            
            <Button variant="outline" className="h-auto py-3 px-4 justify-start" asChild>
              <Link href="/help">
                <Bell className="h-4 w-4 mr-2" />
                Help & Support
              </Link>
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* System Health Overview */}
      {serviceMetrics && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="w-5 h-5" />
              System Health
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <div className="font-semibold text-lg">
                  {serviceMetrics.system_health.total_users.toLocaleString()}
                </div>
                <div className="text-sm text-gray-600">Total Users</div>
              </div>
              
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <div className="font-semibold text-lg capitalize">
                  {serviceMetrics.system_health.system_status}
                </div>
                <div className="text-sm text-gray-600">System Status</div>
              </div>
              
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <div className="font-semibold text-lg">
                  {serviceMetrics.system_health.uptime_percentage}%
                </div>
                <div className="text-sm text-gray-600">Uptime</div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default ServiceSelectionHub;