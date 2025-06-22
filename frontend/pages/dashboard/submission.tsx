import React, { useState, useEffect, useCallback } from 'react';
import { NextPage } from 'next';
import Head from 'next/head';
import { useRouter } from 'next/router';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/Select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../components/ui/Tabs';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Badge } from '../../components/ui/Badge';
import { Switch } from '../../components/ui/Switch';
import { Loader2, AlertTriangle, RefreshCw, Wifi, WifiOff, Bell, Activity, CheckCircle, XCircle } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useWebSocket } from '../../hooks/useWebSocket';
import AppDashboardLayout from '../../components/layouts/AppDashboardLayout';
import SubmissionMetricsCard from '../../components/dashboard/SubmissionMetricsCard';
import RetryMetricsCard from '../../components/dashboard/RetryMetricsCard';
import ApiStatusOverview from '../../components/dashboard/ApiStatusOverview';
import {
  fetchSubmissionMetrics,
  fetchRetryMetrics,
  fetchOdooSubmissionMetrics,
  SubmissionMetrics,
  RetryMetrics
} from '../../services/submissionDashboardService';
import { cn } from '../../utils/cn';
import { format } from 'date-fns';

const timeRangeOptions = [
  { value: '24h', label: 'Last 24 Hours' },
  { value: '7d', label: 'Last 7 Days' },
  { value: '30d', label: 'Last 30 Days' },
  { value: 'all', label: 'All Time' }
];

const SubmissionDashboard: NextPage = () => {
  const router = useRouter();
  const { isAuthenticated, isLoading } = useAuth();
  
  // Redirect to login if not authenticated
  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/auth/login?redirect=' + encodeURIComponent(router.pathname));
    }
  }, [isAuthenticated, isLoading, router]);
  
  // State for filters and data
  const [timeRange, setTimeRange] = useState('24h');
  const [activeTab, setActiveTab] = useState('overview');
  const [isDataLoading, setIsDataLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());
  const [notifications, setNotifications] = useState<any[]>([]);
  const [showNotifications, setShowNotifications] = useState(false);
  
  // State for metrics data
  const [submissionMetrics, setSubmissionMetrics] = useState<SubmissionMetrics | null>(null);
  const [retryMetrics, setRetryMetrics] = useState<RetryMetrics | null>(null);
  const [odooMetrics, setOdooMetrics] = useState<SubmissionMetrics | null>(null);
  const [realTimeSubmissionMetrics, setRealTimeSubmissionMetrics] = useState<SubmissionMetrics | null>(null);
  const [realTimeRetryMetrics, setRealTimeRetryMetrics] = useState<RetryMetrics | null>(null);

  // Create safe default data to prevent undefined errors
  const defaultSubmissionMetrics: SubmissionMetrics = {
    timestamp: new Date().toISOString(),
    summary: {
      total_submissions: 0,
      success_count: 0,
      failed_count: 0,
      pending_count: 0,
      success_rate: 0,
      avg_processing_time: 0,
      common_errors: []
    },
    status_breakdown: [],
    hourly_submissions: [],
    daily_submissions: [],
    common_errors: [],
    time_range: '24h'
  };
  
  const defaultRetryMetrics: RetryMetrics = {
    timestamp: new Date().toISOString(),
    metrics: {
      total_retries: 0,
      success_count: 0,
      failed_count: 0,
      pending_count: 0,
      success_rate: 0,
      avg_attempts: 0,
      max_attempts_reached_count: 0
    },
    retry_breakdown_by_status: [],
    retry_breakdown_by_severity: [],
    time_range: '24h'
  };

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
    subscriptions: ['submissions', 'retries', 'alerts', 'odoo_submissions']
  });



  // Handle real-time updates
  useEffect(() => {
    const unsubscribeSubmissions = subscribe('submission_update', (data) => {
      console.log('Received submission update:', data);
      if (data && data.submission_metrics) {
        setRealTimeSubmissionMetrics(data.submission_metrics);
        setLastUpdated(new Date());
      }
    });

    const unsubscribeRetries = subscribe('retry_update', (data) => {
      console.log('Received retry update:', data);
      if (data && data.retry_metrics) {
        setRealTimeRetryMetrics(data.retry_metrics);
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
      unsubscribeSubmissions();
      unsubscribeRetries();
      unsubscribeAlerts();
    };
  }, [subscribe]);

  // Create a function to fetch all dashboard data
  const fetchDashboardData = async () => {
    setIsDataLoading(true);
    setError(null);
    
    try {
      // Use Promise.allSettled to fetch all metrics with enhanced error handling
      const [submissionResult, retryResult, odooResult] = await Promise.allSettled([
        fetchSubmissionMetrics(timeRange).catch(err => {
          console.log('Submission metrics error:', err);
          return defaultSubmissionMetrics;
        }),
        fetchRetryMetrics(timeRange).catch(err => {
          console.log('Retry metrics error:', err);
          return defaultRetryMetrics;
        }),
        fetchOdooSubmissionMetrics(timeRange).catch(err => {
          console.log('Odoo metrics error:', err);
          return defaultSubmissionMetrics;
        })
      ]);
      
      // Safely process results, ensuring we always have default data if needed
      setSubmissionMetrics(
        submissionResult.status === 'fulfilled' ? 
          submissionResult.value || defaultSubmissionMetrics : 
          defaultSubmissionMetrics
      );
      
      setRetryMetrics(
        retryResult.status === 'fulfilled' ? 
          retryResult.value || defaultRetryMetrics : 
          defaultRetryMetrics
      );
      
      setOdooMetrics(
        odooResult.status === 'fulfilled' ? 
          odooResult.value || defaultSubmissionMetrics : 
          defaultSubmissionMetrics
      );

      // Request real-time updates
      requestUpdate('submissions');
      requestUpdate('retries');
      requestUpdate('odoo_submissions');
      setLastUpdated(new Date());
    } catch (err) {
      console.error('Error fetching dashboard data:', err);
      setError('Unable to fetch dashboard data. Please try again later.');
    } finally {
      setIsDataLoading(false);
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

  // Use real-time data if available, fallback to fetched data
  const displaySubmissionMetrics = realTimeSubmissionMetrics || submissionMetrics;
  const displayRetryMetrics = realTimeRetryMetrics || retryMetrics;

  // Request notification permission
  useEffect(() => {
    if ('Notification' in window && Notification.permission === 'default') {
      Notification.requestPermission();
    }
  }, []);

  // Call the fetch function when component mounts or filters change
  useEffect(() => {
    fetchDashboardData();
  }, [timeRange]);

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin" />
        <span className="ml-2">Loading...</span>
      </div>
    );
  }

  // If not authenticated, don't render anything (will redirect)
  if (!isAuthenticated) {
    return null;
  }

  return (
    <>
      <Head>
        <title>Submission Dashboard | TaxPoynt eInvoice</title>
        <meta name="description" content="Monitor e-invoice submission metrics and status" />
      </Head>

      <AppDashboardLayout>
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
                    <h1 className="text-2xl font-bold tracking-tight flex items-center gap-2">
                      Submission Dashboard
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

                  <div className="w-[150px]">
                    <Select
                      value={timeRange}
                      onValueChange={(value) => setTimeRange(value)}
                    >
                      <SelectTrigger className="w-full">
                        <SelectValue placeholder="Select time range" />
                      </SelectTrigger>
                      <SelectContent>
                        {timeRangeOptions.map((option) => (
                          <SelectItem key={option.value} value={option.value}>
                            {option.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  
                  <Button 
                    variant="outline"
                    size="icon"
                    onClick={() => fetchDashboardData()}
                    disabled={isDataLoading}
                    title="Refresh data"
                  >
                    {isDataLoading ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <RefreshCw className="h-4 w-4" />
                    )}
                  </Button>
                </div>
              </div>
            </CardHeader>
          </Card>

          {/* Status indicators */}
          <div className="flex flex-wrap gap-2">
            <Badge variant="outline">Last updated: {format(lastUpdated, 'HH:mm:ss')}</Badge>
            <Badge variant="secondary">Time range: {timeRangeOptions.find(o => o.value === timeRange)?.label}</Badge>
            {(realTimeSubmissionMetrics || realTimeRetryMetrics) && (
              <Badge variant="success" className="flex items-center gap-1">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                Real-time Data
              </Badge>
            )}
          </div>

          {/* Error display */}
          {error && (
            <Card className="border-red-300 shadow-sm">
              <CardContent className="flex items-center space-x-2 p-4">
                <AlertTriangle className="h-5 w-5 text-red-500" />
                <p className="text-sm text-red-800">{error}</p>
              </CardContent>
            </Card>
          )}
          
          {/* Dashboard content */}
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList>
              <TabsTrigger value="overview">Overview</TabsTrigger>
              <TabsTrigger value="odoo">Odoo</TabsTrigger>
              <TabsTrigger value="retry">Retry Metrics</TabsTrigger>
            </TabsList>
            
            <TabsContent value="overview" className="space-y-4">
              {/* API Status */}
              <ApiStatusOverview />
              
              {/* Submission Metrics */}
              {displaySubmissionMetrics ? (
                <SubmissionMetricsCard metrics={displaySubmissionMetrics} isLoading={isDataLoading} />
              ) : (
                <div className="text-center py-12">
                  <p>No submission metrics available. Try changing the filters or refreshing the page.</p>
                </div>
              )}
            </TabsContent>
            
            <TabsContent value="odoo" className="space-y-4">
              {odooMetrics ? (
                <>
                  <Card>
                    <CardHeader>
                      <CardTitle>Odoo Integration Metrics</CardTitle>
                      <CardDescription>
                        Submission metrics for invoices from Odoo
                      </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div className="bg-white rounded-lg p-4 shadow-sm border">
                          <p className="text-sm font-medium text-gray-500">Total Submissions</p>
                          <p className="text-3xl font-bold">{odooMetrics.summary.total_submissions}</p>
                        </div>
                        
                        <div className="bg-white rounded-lg p-4 shadow-sm border">
                          <p className="text-sm font-medium text-gray-500">Success Rate</p>
                          <p className="text-3xl font-bold">{odooMetrics.summary.success_rate}%</p>
                        </div>
                        
                        <div className="bg-white rounded-lg p-4 shadow-sm border">
                          <p className="text-sm font-medium text-gray-500">Average Processing Time</p>
                          <p className="text-3xl font-bold">{odooMetrics.summary.avg_processing_time}s</p>
                        </div>
                      </div>
                      
                      <div className="flex space-x-4 justify-end mt-4">
                        <Button
                          onClick={() => router.push('/dashboard/integrations')}
                        >
                          Manage Integrations
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                </>
              ) : (
                <div className="text-center py-12">
                  <p>No Odoo metrics available. Try changing the filters or refreshing the page.</p>
                </div>
              )}
            </TabsContent>
            
            <TabsContent value="retry" className="space-y-4">
              {retryMetrics ? (
                <>
                  <Card>
                    <CardHeader>
                      <CardTitle>Retry Metrics</CardTitle>
                      <CardDescription>
                        Statistics for failed submission retry attempts
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <RetryMetricsCard metrics={displayRetryMetrics} isLoading={isDataLoading} />
                      
                      <div className="flex space-x-4 justify-end mt-6">
                        <Button 
                          variant="outline"
                          onClick={() => router.push('/dashboard/retry-queue')}
                          className="flex-1"
                        >
                          View Retry Queue
                        </Button>
                        
                        <Button 
                          variant="outline"
                          onClick={() => router.push('/dashboard/retry-config')}
                          className="flex-1"
                        >
                          Retry Configuration
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                </>
              ) : (
                <div className="text-center py-12">
                  <p>No retry metrics available. Try changing the filters or refreshing the page.</p>
                </div>
              )}
            </TabsContent>
          </Tabs>
        </div>
      </AppDashboardLayout>
    </>
  );
};

export default SubmissionDashboard;
