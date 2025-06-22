import React, { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/router';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../components/ui/Tabs';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Badge } from '../../components/ui/Badge';
import { Switch } from '../../components/ui/Switch';
import { 
  Layers,
  Shield,
  Activity,
  FileText,
  Bell,
  Settings,
  HelpCircle,
  ChevronRight,
  Wifi,
  WifiOff,
  RefreshCw,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Clock
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useWebSocket } from '../../hooks/useWebSocket';
import AppDashboardLayout from '../../components/layouts/AppDashboardLayout';
import CertificateManagementInterface from '../../components/platform/certificate/CertificateManagementInterface';
import TransmissionMonitoringDashboard from '../../components/platform/transmission/TransmissionMonitoringDashboard';
import ComplianceSummaryVisualization from '../../components/platform/compliance/ComplianceSummaryVisualization';
import ContextualHelp from '../../components/platform/common/ContextualHelp';
import { cn } from '../../utils/cn';
import { format } from 'date-fns';


// Help content for platform dashboard
const platformHelp = {
  overview: "The Platform Dashboard provides a centralized view of all your e-invoicing platform functionality.",
  certificate: "Manage digital certificates required for signing electronic invoices in compliance with FIRS regulations.",
  transmission: "Monitor and manage the transmission of e-invoices to FIRS, including statistics and error handling.",
  compliance: "Track your compliance status with FIRS regulations and identify areas for improvement."
};

interface PlatformMetrics {
  certificate_status: string;
  certificate_expiry: string;
  transmission_rate: number;
  compliance_score: number;
  last_transmission: string;
  pending_issues: number;
  total_certificates: number;
  active_transmissions: number;
}

const PlatformDashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState<string>('overview');
  const [organizationId, setOrganizationId] = useState<string>('');
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());
  const [notifications, setNotifications] = useState<any[]>([]);
  const [showNotifications, setShowNotifications] = useState(false);
  const [platformMetrics, setPlatformMetrics] = useState<PlatformMetrics | null>(null);
  const router = useRouter();
  const { user, isLoading } = useAuth();

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
    subscriptions: ['platform', 'certificates', 'transmissions', 'compliance', 'alerts']
  });

  // Handle real-time platform updates
  useEffect(() => {
    const unsubscribePlatform = subscribe('platform_update', (data) => {
      console.log('Received platform update:', data);
      if (data && data.platform_metrics) {
        setPlatformMetrics({
          certificate_status: data.platform_metrics.certificate_status || 'Unknown',
          certificate_expiry: data.platform_metrics.certificate_expiry || '',
          transmission_rate: data.platform_metrics.transmission_rate || 0,
          compliance_score: data.platform_metrics.compliance_score || 0,
          last_transmission: data.platform_metrics.last_transmission || '',
          pending_issues: data.platform_metrics.pending_issues || 0,
          total_certificates: data.platform_metrics.total_certificates || 0,
          active_transmissions: data.platform_metrics.active_transmissions || 0
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
      
      setNotifications(prev => [notification, ...prev.slice(0, 9)]);
      
      if (Notification.permission === 'granted') {
        new Notification(notification.title, {
          body: notification.message,
          icon: '/icons/favicon.svg'
        });
      }
    });

    return () => {
      unsubscribePlatform();
      unsubscribeAlerts();
    };
  }, [subscribe]);
  
  useEffect(() => {
    // If user exists, we'll use their ID as the organization ID for now
    // In a real implementation, you might fetch the organization ID from an API
    if (user && user.id) {
      setOrganizationId(user.id);
    }
    
    // Check if tab is specified in URL
    if (router.query.tab && typeof router.query.tab === 'string') {
      setActiveTab(router.query.tab);
    }
  }, [user, router.query]);

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
    requestUpdate('platform');
    requestUpdate('certificates');
    requestUpdate('transmissions');
    requestUpdate('compliance');
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
  
  // Handle tab change
  const handleTabChange = (value: string) => {
    setActiveTab(value);
    
    // Update URL without reloading the page
    router.push(
      {
        pathname: router.pathname,
        query: { ...router.query, tab: value },
      },
      undefined,
      { shallow: true }
    );
  };
  
  if (isLoading) {
    return (
      <AppDashboardLayout>
        <div className="flex justify-center items-center h-96">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-cyan-500"></div>
        </div>
      </AppDashboardLayout>
    );
  }
  
  if (!user || !organizationId) {
    return (
      <AppDashboardLayout>
        <div className="text-center p-8">
          <h2 className="text-xl font-semibold text-gray-800">Authentication Required</h2>
          <p className="mt-2 text-gray-600">Please log in to access the Platform Dashboard.</p>
          <Button 
            className="mt-4"
            onClick={() => router.push('/auth/login')}
          >
            Go to Login
          </Button>
        </div>
      </AppDashboardLayout>
    );
  }
  
  return (
    <AppDashboardLayout>
      <div className="container mx-auto px-4 py-6">
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
                  <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
                    <Layers className="h-6 w-6 text-cyan-600" />
                    Platform Dashboard
                    <Badge 
                      variant={isConnected ? 'success' : 'secondary'}
                      className="text-xs"
                    >
                      {connectionStatus.label}
                    </Badge>
                    <ContextualHelp content={platformHelp.overview}>
                      <HelpCircle className="h-4 w-4 text-gray-400" />
                    </ContextualHelp>
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
                
                <Button variant="outline" size="sm">
                  <Settings className="h-4 w-4 mr-1" />
                  Settings
                </Button>
              </div>
            </div>
          </CardHeader>
        </Card>

        {/* Status indicators */}
        <div className="flex flex-wrap gap-2 mb-6">
          <Badge variant="outline">Last updated: {format(lastUpdated, 'HH:mm:ss')}</Badge>
          {platformMetrics && (
            <Badge variant="success" className="flex items-center gap-1">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
              Real-time Data
            </Badge>
          )}
        </div>
        
        <Tabs value={activeTab} onValueChange={handleTabChange}>
          <TabsList className="grid grid-cols-4 mb-8">
            <TabsTrigger value="overview">
              <Layers className="h-4 w-4 mr-2" />
              Overview
            </TabsTrigger>
            <TabsTrigger value="certificates">
              <Shield className="h-4 w-4 mr-2" />
              Certificates
            </TabsTrigger>
            <TabsTrigger value="transmission">
              <Activity className="h-4 w-4 mr-2" />
              Transmission
            </TabsTrigger>
            <TabsTrigger value="compliance">
              <FileText className="h-4 w-4 mr-2" />
              Compliance
            </TabsTrigger>
          </TabsList>
          
          <TabsContent value="overview" className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {/* Certificate Management Card */}
              <Card className="relative overflow-hidden border-l-4 border-l-cyan-500">
                <CardHeader className="pb-2">
                  <CardTitle className="flex items-center">
                    <Shield className="h-5 w-5 text-cyan-600 mr-2" />
                    Certificate Management
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-gray-500 mb-4">
                    Manage digital certificates for e-invoice signing compliant with FIRS regulations.
                  </p>
                  <div className="flex justify-between items-center">
                    <Button 
                      variant="outline" 
                      size="sm"
                      onClick={() => handleTabChange('certificates')}
                    >
                      View Certificates
                      <ChevronRight className="h-4 w-4 ml-1" />
                    </Button>
                    <Badge className="bg-green-100 text-green-800">Active</Badge>
                  </div>
                </CardContent>
              </Card>
              
              {/* Transmission Monitoring Card */}
              <Card className="relative overflow-hidden border-l-4 border-l-cyan-500">
                <CardHeader className="pb-2">
                  <CardTitle className="flex items-center">
                    <Activity className="h-5 w-5 text-cyan-600 mr-2" />
                    Transmission Monitoring
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-gray-500 mb-4">
                    Monitor e-invoice transmissions to FIRS, track status, and handle errors.
                  </p>
                  <div className="flex justify-between items-center">
                    <Button 
                      variant="outline" 
                      size="sm"
                      onClick={() => handleTabChange('transmission')}
                    >
                      View Transmissions
                      <ChevronRight className="h-4 w-4 ml-1" />
                    </Button>
                    <Badge className="bg-blue-100 text-blue-800">Active</Badge>
                  </div>
                </CardContent>
              </Card>
              
              {/* Compliance Summary Card */}
              <Card className="relative overflow-hidden border-l-4 border-l-cyan-500">
                <CardHeader className="pb-2">
                  <CardTitle className="flex items-center">
                    <FileText className="h-5 w-5 text-cyan-600 mr-2" />
                    Compliance Summary
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-gray-500 mb-4">
                    Track compliance with FIRS regulations and get recommendations for improvement.
                  </p>
                  <div className="flex justify-between items-center">
                    <Button 
                      variant="outline" 
                      size="sm"
                      onClick={() => handleTabChange('compliance')}
                    >
                      View Compliance
                      <ChevronRight className="h-4 w-4 ml-1" />
                    </Button>
                    <Badge className="bg-yellow-100 text-yellow-800">85%</Badge>
                  </div>
                </CardContent>
              </Card>
            </div>
            
            {/* Quick Overview Dashboard */}
            <Card>
              <CardHeader>
                <CardTitle>Platform Health Overview</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="bg-white p-6 rounded-lg border shadow-sm">
                    <div className="flex justify-between items-start">
                      <div>
                        <p className="text-sm text-gray-500">Certificate Status</p>
                        <h3 className="text-2xl font-bold mt-1">
                          {platformMetrics?.certificate_status || 'Active'}
                        </h3>
                        <p className="text-xs text-gray-500 mt-1">
                          {platformMetrics?.certificate_expiry || 'Valid until Jan 15, 2026'}
                        </p>
                      </div>
                      <div className={cn(
                        'p-2 rounded-full',
                        platformMetrics?.certificate_status === 'Active' ? 'bg-green-100' : 'bg-red-100'
                      )}>
                        {platformMetrics?.certificate_status === 'Active' ? (
                          <CheckCircle className="h-5 w-5 text-green-600" />
                        ) : (
                          <XCircle className="h-5 w-5 text-red-600" />
                        )}
                      </div>
                    </div>
                    {platformMetrics && (
                      <div className="flex items-center gap-1 mt-2">
                        <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                        <span className="text-xs text-green-600">Live</span>
                      </div>
                    )}
                  </div>
                  
                  <div className="bg-white p-6 rounded-lg border shadow-sm">
                    <div className="flex justify-between items-start">
                      <div>
                        <p className="text-sm text-gray-500">Transmission Rate</p>
                        <h3 className="text-2xl font-bold mt-1">
                          {platformMetrics?.transmission_rate?.toFixed(1) || '98.2'}%
                        </h3>
                        <p className="text-xs text-gray-500 mt-1">
                          {platformMetrics?.active_transmissions || 0} active transmissions
                        </p>
                      </div>
                      <div className="p-2 rounded-full bg-blue-100">
                        <Activity className="h-5 w-5 text-blue-600" />
                      </div>
                    </div>
                    {platformMetrics && (
                      <div className="flex items-center gap-1 mt-2">
                        <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" />
                        <span className="text-xs text-blue-600">Live</span>
                      </div>
                    )}
                  </div>
                  
                  <div className="bg-white p-6 rounded-lg border shadow-sm">
                    <div className="flex justify-between items-start">
                      <div>
                        <p className="text-sm text-gray-500">Compliance Score</p>
                        <h3 className="text-2xl font-bold mt-1">
                          {platformMetrics?.compliance_score || 85}%
                        </h3>
                        <p className="text-xs text-gray-500 mt-1">
                          {platformMetrics?.pending_issues || 2} issues need attention
                        </p>
                      </div>
                      <div className={cn(
                        'p-2 rounded-full',
                        (platformMetrics?.compliance_score || 85) >= 90 ? 'bg-green-100' : 'bg-yellow-100'
                      )}>
                        <FileText className={cn(
                          'h-5 w-5',
                          (platformMetrics?.compliance_score || 85) >= 90 ? 'text-green-600' : 'text-yellow-600'
                        )} />
                      </div>
                    </div>
                    {platformMetrics && (
                      <div className="flex items-center gap-1 mt-2">
                        <div className="w-2 h-2 bg-yellow-500 rounded-full animate-pulse" />
                        <span className="text-xs text-yellow-600">Live</span>
                      </div>
                    )}
                  </div>
                </div>
                
                <div className="mt-4 p-4 bg-cyan-50 rounded-md border border-cyan-200">
                  <div className="flex items-start">
                    <Bell className="h-5 w-5 text-cyan-600 mr-3 mt-0.5" />
                    <div>
                      <h4 className="text-sm font-medium text-cyan-800">Important Platform Notices</h4>
                      <p className="text-sm text-cyan-700 mt-1">
                        FIRS has announced changes to the e-invoicing API that will take effect on July 1, 2025.
                        An update to your certificates will be required before this date.
                      </p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
          
          <TabsContent value="certificates">
            <CertificateManagementInterface organizationId={organizationId} />
          </TabsContent>
          
          <TabsContent value="transmission">
            <TransmissionMonitoringDashboard organizationId={organizationId} />
          </TabsContent>
          
          <TabsContent value="compliance">
            <ComplianceSummaryVisualization organizationId={organizationId} />
          </TabsContent>
        </Tabs>
      </div>
    </AppDashboardLayout>
  );
};

export default PlatformDashboard;
