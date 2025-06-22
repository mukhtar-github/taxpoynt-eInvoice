import React, { useState, useEffect, useCallback } from 'react';
import DashboardLayout from '../../components/layouts/DashboardLayout';
import ProtectedRoute from '../../components/auth/ProtectedRoute';
import EnhancedIRNMetricsCard from '../../components/dashboard/EnhancedIRNMetricsCard';
import ValidationMetricsCard from '../../components/dashboard/ValidationMetricsCard';
import B2BvsB2CMetricsCard from '../../components/dashboard/B2BvsB2CMetricsCard';
import OdooIntegrationMetricsCard from '../../components/dashboard/OdooIntegrationMetricsCard';
import ConnectedActivityFeed from '../../components/dashboard/ConnectedActivityFeed';
import { fetchDashboardSummary, DashboardSummary } from '../../services/dashboardService';
import { useWebSocket } from '../../hooks/useWebSocket';
import { Card, CardContent, CardHeader } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Badge } from '../../components/ui/Badge';
import { Switch } from '../../components/ui/Switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/Select';
import { Input } from '../../components/ui/Input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../components/ui/Tabs';
import { Download, Filter, RefreshCw, Search, Wifi, WifiOff, Activity, Bell, AlertTriangle, CheckCircle, XCircle } from 'lucide-react';
import { format } from 'date-fns';
import { cn } from '../../utils/cn';
import Head from 'next/head';

// Mock organization data for filtering (in a real app, this would come from an API)
const organizations = [
  { id: '1', name: 'Organization 1' },
  { id: '2', name: 'Organization 2' },
  { id: '3', name: 'Organization 3' }
];

interface MetricsDashboardData {
  total_irns: number;
  active_irns: number;
  total_validations: number;
  success_rate: number;
  active_integrations: number;
  total_requests: number;
  error_rate: number;
  avg_response_time: number;
  b2b_percentage: number;
  b2c_percentage: number;
  b2b_success_rate: number;
  b2c_success_rate: number;
}

const MetricsDashboard: React.FC = () => {
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [showFilters, setShowFilters] = useState(false);
  const [timeRange, setTimeRange] = useState('24h');
  const [selectedOrg, setSelectedOrg] = useState<string | undefined>(undefined);
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [realTimeMetrics, setRealTimeMetrics] = useState<MetricsDashboardData | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());
  const [autoRefresh, setAutoRefresh] = useState(true);
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
    subscriptions: ['metrics', 'activities', 'alerts', 'validations', 'integrations']
  });

  const fetchSummary = async () => {
    try {
      const data = await fetchDashboardSummary();
      setSummary(data);
    } catch (error) {
      console.error('Failed to fetch dashboard summary:', error);
    }
  };

  // Handle real-time metric updates
  useEffect(() => {
    const unsubscribeMetrics = subscribe('metrics_update', (data) => {
      console.log('Received metrics update:', data);
      if (data && data.irn_summary) {
        setRealTimeMetrics({
          total_irns: data.irn_summary.total_irns || 0,
          active_irns: data.irn_summary.active_irns || 0,
          total_validations: data.validation_summary?.total_validations || 0,
          success_rate: data.validation_summary?.success_rate || 0,
          active_integrations: data.odoo_summary?.active_integrations || 0,
          total_requests: data.system_summary?.total_requests || 0,
          error_rate: data.system_summary?.error_rate || 0,
          avg_response_time: data.system_summary?.avg_response_time || 0,
          b2b_percentage: data.b2b_vs_b2c_summary?.b2b_percentage || 0,
          b2c_percentage: data.b2b_vs_b2c_summary?.b2c_percentage || 0,
          b2b_success_rate: data.b2b_vs_b2c_summary?.b2b_success_rate || 0,
          b2c_success_rate: data.b2b_vs_b2c_summary?.b2c_success_rate || 0
        });
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

  useEffect(() => {
    fetchSummary();
    
    // Set up an interval to update the summary every minute (fallback to polling)
    const intervalId = setInterval(fetchSummary, 60000);
    
    return () => clearInterval(intervalId);
  }, []);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    
    try {
      await fetchSummary();
      // Request real-time updates
      requestUpdate('metrics');
      requestUpdate('activities');
      requestUpdate('validations');
      setLastUpdated(new Date());
    } catch (error) {
      console.error('Error refreshing dashboard data:', error);
    } finally {
      setIsRefreshing(false);
    }
  };

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

  // Use real-time data if available, fall back to summary
  const displayMetrics = realTimeMetrics || (summary ? {
    total_irns: summary.irn_summary.total_irns,
    active_irns: summary.irn_summary.active_irns,
    total_validations: summary.validation_summary.total_validations,
    success_rate: summary.validation_summary.success_rate,
    active_integrations: summary.odoo_summary?.active_integrations || 0,
    total_requests: summary.system_summary?.total_requests || 0,
    error_rate: summary.system_summary?.error_rate || 0,
    avg_response_time: summary.system_summary?.avg_response_time || 0,
    b2b_percentage: summary.b2b_vs_b2c_summary.b2b_percentage,
    b2c_percentage: summary.b2b_vs_b2c_summary.b2c_percentage,
    b2b_success_rate: summary.b2b_vs_b2c_summary.b2b_success_rate,
    b2c_success_rate: summary.b2b_vs_b2c_summary.b2c_success_rate
  } : null);

  const handleTimeRangeChange = (value: string) => {
    setTimeRange(value);
  };

  const handleOrgChange = (value: string) => {
    setSelectedOrg(value === 'all' ? undefined : value);
  };

  const toggleFilters = () => {
    setShowFilters(!showFilters);
  };
  
  const handleExport = () => {
    // Placeholder for export functionality
    alert('Export functionality would generate a report with current dashboard metrics');
  };
  
  // Time range options for the Select
  const timeRangeOptions = [
    { value: '24h', label: '24 Hours' },
    { value: '7d', label: '7 Days' },
    { value: '30d', label: '30 Days' },
    { value: 'all', label: 'All Time' }
  ];

  return (
    <>
      <Head>
        <title>FIRS e-Invoice Dashboard | Metrics</title>
      </Head>
      
      <DashboardLayout>
        <div className="p-6">
          {/* Real-Time Status Header */}
          <Card className="mb-6">
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
                    <h1 className="text-2xl font-heading font-semibold flex items-center gap-2">
                      Metrics Dashboard
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
                      {autoRefresh ? 'Live' : 'Manual'}
                    </span>
                  </div>

                  <Button 
                    variant="outline" 
                    size="sm"
                    className="flex items-center gap-1"
                    onClick={handleRefresh}
                    disabled={isRefreshing}
                  >
                    <RefreshCw size={14} className={isRefreshing ? 'animate-spin' : ''} />
                    <span>{isRefreshing ? 'Refreshing...' : 'Refresh'}</span>
                  </Button>
                  <Button 
                    variant="outline" 
                    size="sm"
                    className="flex items-center gap-1"
                    onClick={toggleFilters}
                  >
                    <Filter size={14} />
                    <span>Filter</span>
                  </Button>
                  <Button 
                    variant="default" 
                    size="sm"
                    className="flex items-center gap-1"
                    onClick={handleExport}
                  >
                    <Download size={14} />
                    <span>Export</span>
                  </Button>
                </div>
              </div>
            </CardHeader>
          </Card>

          <header className="mb-8">
            
            {showFilters && (
              <Card className="mb-4">
                <CardContent className="pt-6">
                  <div className="flex flex-wrap gap-4">
                    <div className="flex-1">
                      <label className="text-sm font-medium mb-1 block">Search</label>
                      <div className="relative">
                        <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                        <Input
                          placeholder="Search invoices, organizations..."
                          className="pl-8"
                          value={searchQuery}
                          onChange={(e) => setSearchQuery(e.target.value)}
                        />
                      </div>
                    </div>
                    <div className="w-40">
                      <label className="text-sm font-medium mb-1 block">Time Range</label>
                      <Select value={timeRange} onValueChange={handleTimeRangeChange}>
                        <SelectTrigger>
                          <SelectValue placeholder="Select range" />
                        </SelectTrigger>
                        <SelectContent>
                          {timeRangeOptions.map(option => (
                            <SelectItem key={option.value} value={option.value}>{option.label}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="w-60">
                      <label className="text-sm font-medium mb-1 block">Organization</label>
                      <Select value={selectedOrg || 'all'} onValueChange={handleOrgChange}>
                        <SelectTrigger>
                          <SelectValue placeholder="Select organization" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="all">All Organizations</SelectItem>
                          {organizations.map(org => (
                            <SelectItem key={org.id} value={org.id}>{org.name}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}
            
            <div className="flex flex-wrap gap-2">
              <Badge variant="outline">Last updated: {format(lastUpdated, 'HH:mm:ss')}</Badge>
              <Badge variant="secondary">Time range: {timeRangeOptions.find(o => o.value === timeRange)?.label}</Badge>
              <Badge variant="outline">
                Organization: {selectedOrg ? organizations.find(o => o.id === selectedOrg)?.name : 'All'}
              </Badge>
              {realTimeMetrics && (
                <Badge variant="success" className="flex items-center gap-1">
                  <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                  Real-time Data
                </Badge>
              )}
            </div>
          </header>

          {/* Real-Time Summary Stats Cards */}
          {displayMetrics && (
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
              <Card>
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-600">Total IRNs</p>
                      <p className="text-2xl font-bold">{displayMetrics.total_irns.toLocaleString()}</p>
                    </div>
                    <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
                      <Activity className="w-4 h-4 text-blue-600" />
                    </div>
                  </div>
                  <div className="flex items-center gap-1 mt-2">
                    <CheckCircle className="w-3 h-3 text-green-500" />
                    <span className="text-xs text-green-600">
                      {displayMetrics.active_irns.toLocaleString()} active
                    </span>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-600">Success Rate</p>
                      <p className="text-2xl font-bold">{displayMetrics.success_rate.toFixed(1)}%</p>
                    </div>
                    <div className="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center">
                      <CheckCircle className="w-4 h-4 text-green-600" />
                    </div>
                  </div>
                  <div className="flex items-center gap-1 mt-2">
                    <span className="text-xs text-gray-600">
                      {displayMetrics.total_validations.toLocaleString()} validations
                    </span>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-600">B2B vs B2C</p>
                      <p className="text-2xl font-bold">
                        {displayMetrics.b2b_percentage.toFixed(1)}% / {displayMetrics.b2c_percentage.toFixed(1)}%
                      </p>
                    </div>
                    <div className="w-8 h-8 bg-purple-100 rounded-lg flex items-center justify-center">
                      <Activity className="w-4 h-4 text-purple-600" />
                    </div>
                  </div>
                  <div className="flex items-center gap-1 mt-2">
                    <CheckCircle className="w-3 h-3 text-green-500" />
                    <span className="text-xs text-green-600">
                      B2B: {displayMetrics.b2b_success_rate.toFixed(1)}%
                    </span>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-600">Error Rate</p>
                      <p className="text-2xl font-bold">{displayMetrics.error_rate.toFixed(1)}%</p>
                    </div>
                    <div className={cn(
                      'w-8 h-8 rounded-lg flex items-center justify-center',
                      displayMetrics.error_rate > 5 ? 'bg-red-100' : 'bg-green-100'
                    )}>
                      {displayMetrics.error_rate > 5 ? (
                        <XCircle className="w-4 h-4 text-red-600" />
                      ) : (
                        <CheckCircle className="w-4 h-4 text-green-600" />
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-1 mt-2">
                    <span className="text-xs text-gray-600">
                      {displayMetrics.avg_response_time.toFixed(0)}ms avg
                    </span>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Tabs for different dashboard views */}
          <Tabs defaultValue="all" className="mb-8">
            <TabsList>
              <TabsTrigger value="all">All Metrics</TabsTrigger>
              <TabsTrigger value="validation">Validation</TabsTrigger>
              <TabsTrigger value="integration">Integration</TabsTrigger>
              <TabsTrigger value="irn">IRN Status</TabsTrigger>
            </TabsList>
            
            <TabsContent value="all" className="mt-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <EnhancedIRNMetricsCard 
                  timeRange={timeRange} 
                  organizationId={selectedOrg} 
                />
                <ValidationMetricsCard 
                  timeRange={timeRange} 
                  organizationId={selectedOrg} 
                />
                <OdooIntegrationMetricsCard 
                  timeRange={timeRange} 
                  organizationId={selectedOrg} 
                />
                <B2BvsB2CMetricsCard 
                  timeRange={timeRange} 
                  organizationId={selectedOrg} 
                />
              </div>
            </TabsContent>
            
            <TabsContent value="validation" className="mt-6">
              <div className="grid grid-cols-1 gap-6">
                <ValidationMetricsCard 
                  timeRange={timeRange} 
                  organizationId={selectedOrg} 
                />
                <B2BvsB2CMetricsCard 
                  timeRange={timeRange} 
                  organizationId={selectedOrg} 
                />
              </div>
            </TabsContent>
            
            <TabsContent value="integration" className="mt-6">
              <div className="grid grid-cols-1 gap-6">
                <OdooIntegrationMetricsCard 
                  timeRange={timeRange} 
                  organizationId={selectedOrg} 
                  refreshInterval={15000} // More frequent updates for integration status
                />
              </div>
            </TabsContent>
            
            <TabsContent value="irn" className="mt-6">
              <div className="grid grid-cols-1 gap-6">
                <EnhancedIRNMetricsCard 
                  timeRange={timeRange} 
                  organizationId={selectedOrg} 
                />
              </div>
            </TabsContent>
          </Tabs>
        </div>
      </DashboardLayout>
    </>
  );
};

// Wrap the component with ProtectedRoute
const ProtectedMetricsDashboard = () => {
  return (
    <ProtectedRoute>
      <MetricsDashboard />
    </ProtectedRoute>
  );
};

export default ProtectedMetricsDashboard;
