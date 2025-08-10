/**
 * FIRS Connection Manager Component
 * ================================
 * 
 * Manages FIRS API connections, health monitoring, and communication settings.
 * Connects to app_services/firs_communication/ backend services.
 * 
 * Features:
 * - Real-time FIRS connection monitoring
 * - API health checks and diagnostics
 * - Connection failover management
 * - Rate limiting and throttling controls
 * - Certificate-based authentication
 * - Environment switching (Sandbox/Production)
 */

import React, { useState, useEffect } from 'react';
import { 
  Card, 
  CardContent, 
  CardHeader, 
  CardTitle,
  Button,
  Badge,
  Progress,
  Alert,
  AlertDescription,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Input,
  Switch,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow
} from '@/components/ui';
import { 
  Wifi, 
  WifiOff, 
  CheckCircle, 
  XCircle,
  AlertTriangle,
  Settings,
  RefreshCw,
  Globe,
  Shield,
  Clock,
  Zap,
  Activity,
  Server,
  Key,
  Eye,
  Edit,
  Trash2,
  Plus
} from 'lucide-react';

import { 
  FIRSConnection, 
  FIRSHealthCheck, 
  FIRSResponse,
  ServiceAvailability,
  RateLimit
} from '../../types';

// Mock data
const mockFIRSConnections: FIRSConnection[] = [
  {
    id: 'firs_prod',
    name: 'FIRS Production',
    environment: 'production',
    status: 'connected',
    endpoint_url: 'https://api.firs.gov.ng/v2',
    certificate_id: 'cert_prod_001',
    last_ping: new Date(),
    response_time: 245,
    uptime_percentage: 99.8,
    api_version: '2.1',
    rate_limit: {
      requests_per_minute: 120,
      current_usage: 45,
      reset_time: new Date(Date.now() + 60000)
    }
  },
  {
    id: 'firs_sandbox',
    name: 'FIRS Sandbox',
    environment: 'sandbox',
    status: 'connected',
    endpoint_url: 'https://sandbox-api.firs.gov.ng/v2',
    certificate_id: 'cert_sandbox_001',
    last_ping: new Date(Date.now() - 30000),
    response_time: 180,
    uptime_percentage: 99.2,
    api_version: '2.1',
    rate_limit: {
      requests_per_minute: 60,
      current_usage: 12,
      reset_time: new Date(Date.now() + 45000)
    }
  }
];

const mockHealthCheck: FIRSHealthCheck = {
  connection_id: 'firs_prod',
  timestamp: new Date(),
  status: 'healthy',
  response_time: 245,
  service_availability: [
    { service: 'Invoice Submission', status: 'available', last_check: new Date() },
    { service: 'Document Validation', status: 'available', last_check: new Date() },
    { service: 'Status Inquiry', status: 'available', last_check: new Date() },
    { service: 'Certificate Management', status: 'degraded', last_check: new Date(Date.now() - 300000) }
  ]
};

const mockRecentResponses: FIRSResponse[] = [
  {
    request_id: 'req_001',
    status_code: 200,
    response_time: 245,
    timestamp: new Date(),
    firs_tracking_id: 'FIRS_TRK_001'
  },
  {
    request_id: 'req_002',
    status_code: 422,
    response_time: 180,
    timestamp: new Date(Date.now() - 300000),
    error_message: 'Validation error: Invalid VAT calculation'
  },
  {
    request_id: 'req_003',
    status_code: 200,
    response_time: 320,
    timestamp: new Date(Date.now() - 600000),
    firs_tracking_id: 'FIRS_TRK_002'
  }
];

export const FIRSConnectionManager: React.FC = () => {
  const [connections, setConnections] = useState<FIRSConnection[]>(mockFIRSConnections);
  const [activeConnection, setActiveConnection] = useState<FIRSConnection>(mockFIRSConnections[0]);
  const [healthCheck, setHealthCheck] = useState<FIRSHealthCheck>(mockHealthCheck);
  const [recentResponses, setRecentResponses] = useState<FIRSResponse[]>(mockRecentResponses);
  const [isHealthCheckRunning, setIsHealthCheckRunning] = useState(false);
  const [autoFailover, setAutoFailover] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'connected': return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'disconnected': return <XCircle className="h-4 w-4 text-red-500" />;
      case 'error': return <AlertTriangle className="h-4 w-4 text-red-500" />;
      case 'maintenance': return <Settings className="h-4 w-4 text-yellow-500" />;
      default: return <AlertTriangle className="h-4 w-4 text-gray-500" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'connected': return 'bg-green-100 text-green-800 border-green-200';
      case 'disconnected': return 'bg-red-100 text-red-800 border-red-200';
      case 'error': return 'bg-red-100 text-red-800 border-red-200';
      case 'maintenance': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getServiceStatusIcon = (status: string) => {
    switch (status) {
      case 'available': return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'degraded': return <AlertTriangle className="h-4 w-4 text-yellow-500" />;
      case 'unavailable': return <XCircle className="h-4 w-4 text-red-500" />;
      default: return <AlertTriangle className="h-4 w-4 text-gray-500" />;
    }
  };

  const getResponseStatusColor = (statusCode: number) => {
    if (statusCode >= 200 && statusCode < 300) return 'text-green-600';
    if (statusCode >= 400 && statusCode < 500) return 'text-yellow-600';
    if (statusCode >= 500) return 'text-red-600';
    return 'text-gray-600';
  };

  const handleHealthCheck = async (connectionId: string) => {
    setIsHealthCheckRunning(true);
    
    try {
      // Simulate health check API call
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // Update health check results
      console.log('Health check completed for:', connectionId);
      
    } catch (error) {
      console.error('Health check failed:', error);
    } finally {
      setIsHealthCheckRunning(false);
    }
  };

  const handleSwitchConnection = (connectionId: string) => {
    const connection = connections.find(c => c.id === connectionId);
    if (connection) {
      setActiveConnection(connection);
      console.log('Switched to connection:', connectionId);
    }
  };

  const handleTestConnection = (connectionId: string) => {
    console.log('Testing connection:', connectionId);
    // In real implementation, this would test the connection
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Globe className="h-6 w-6 text-blue-600" />
            FIRS Connection Manager
          </h2>
          <p className="text-gray-600 mt-1">
            Manage FIRS API connections and monitor communication health
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            size="sm"
            onClick={() => handleHealthCheck(activeConnection.id)}
            disabled={isHealthCheckRunning}
          >
            {isHealthCheckRunning ? (
              <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
            ) : (
              <Activity className="h-4 w-4 mr-2" />
            )}
            Health Check
          </Button>
          <Button variant="outline" size="sm">
            <Plus className="h-4 w-4 mr-2" />
            Add Connection
          </Button>
        </div>
      </div>

      {/* Active Connection Status */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span className="flex items-center gap-2">
              {activeConnection.status === 'connected' ? (
                <Wifi className="h-5 w-5 text-green-600" />
              ) : (
                <WifiOff className="h-5 w-5 text-red-600" />
              )}
              Active Connection: {activeConnection.name}
            </span>
            <Badge variant="outline" className={getStatusColor(activeConnection.status)}>
              {activeConnection.status}
            </Badge>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">
                {activeConnection.response_time}ms
              </div>
              <div className="text-sm text-gray-600">Response Time</div>
              <Progress 
                value={Math.min((activeConnection.response_time / 1000) * 100, 100)} 
                className="mt-2"
              />
            </div>

            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">
                {activeConnection.uptime_percentage}%
              </div>
              <div className="text-sm text-gray-600">Uptime</div>
              <Progress value={activeConnection.uptime_percentage} className="mt-2" />
            </div>

            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">
                {activeConnection.rate_limit.current_usage}
              </div>
              <div className="text-sm text-gray-600">
                / {activeConnection.rate_limit.requests_per_minute} RPM
              </div>
              <Progress 
                value={(activeConnection.rate_limit.current_usage / activeConnection.rate_limit.requests_per_minute) * 100} 
                className="mt-2"
              />
            </div>

            <div className="text-center">
              <div className="text-2xl font-bold text-orange-600">
                v{activeConnection.api_version}
              </div>
              <div className="text-sm text-gray-600">API Version</div>
              <div className="mt-2">
                <Badge variant="outline" className="bg-blue-50 text-blue-700">
                  {activeConnection.environment}
                </Badge>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Auto-failover Alert */}
      {!autoFailover && (
        <Alert className="border-yellow-200 bg-yellow-50">
          <AlertTriangle className="h-4 w-4 text-yellow-600" />
          <AlertDescription>
            Auto-failover is disabled. Manual intervention may be required if the primary connection fails.
          </AlertDescription>
        </Alert>
      )}

      {/* Main Content */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="health">Health Monitor</TabsTrigger>
          <TabsTrigger value="connections">Connections</TabsTrigger>
          <TabsTrigger value="settings">Settings</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          {/* Service Availability */}
          <Card>
            <CardHeader>
              <CardTitle>FIRS Service Availability</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {healthCheck.service_availability.map(service => (
                  <div key={service.service} className="flex items-center justify-between p-4 border rounded-lg">
                    <div className="flex items-center gap-3">
                      {getServiceStatusIcon(service.status)}
                      <div>
                        <span className="font-medium">{service.service}</span>
                        <div className="text-sm text-gray-600">
                          Last check: {service.last_check.toLocaleTimeString()}
                        </div>
                      </div>
                    </div>
                    <Badge 
                      variant="outline" 
                      className={
                        service.status === 'available' ? 'bg-green-100 text-green-800' :
                        service.status === 'degraded' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-red-100 text-red-800'
                      }
                    >
                      {service.status}
                    </Badge>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Recent API Responses */}
          <Card>
            <CardHeader>
              <CardTitle>Recent API Responses</CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Request ID</TableHead>
                    <TableHead>Status Code</TableHead>
                    <TableHead>Response Time</TableHead>
                    <TableHead>Timestamp</TableHead>
                    <TableHead>FIRS Tracking</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {recentResponses.map(response => (
                    <TableRow key={response.request_id}>
                      <TableCell className="font-mono text-sm">
                        {response.request_id}
                      </TableCell>
                      <TableCell>
                        <Badge 
                          variant="outline" 
                          className={getResponseStatusColor(response.status_code)}
                        >
                          {response.status_code}
                        </Badge>
                      </TableCell>
                      <TableCell>{response.response_time}ms</TableCell>
                      <TableCell>{response.timestamp.toLocaleTimeString()}</TableCell>
                      <TableCell>
                        {response.firs_tracking_id ? (
                          <span className="font-mono text-sm">{response.firs_tracking_id}</span>
                        ) : (
                          <span className="text-gray-400">-</span>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="health" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span>Connection Health Status</span>
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={() => handleHealthCheck(activeConnection.id)}
                  disabled={isHealthCheckRunning}
                >
                  {isHealthCheckRunning ? (
                    <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                  ) : (
                    <RefreshCw className="h-4 w-4 mr-2" />
                  )}
                  Run Health Check
                </Button>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                <div className="text-center">
                  <div className={`text-6xl font-bold ${
                    healthCheck.status === 'healthy' ? 'text-green-600' :
                    healthCheck.status === 'degraded' ? 'text-yellow-600' :
                    'text-red-600'
                  }`}>
                    {healthCheck.status === 'healthy' ? '✓' :
                     healthCheck.status === 'degraded' ? '⚠' : '✗'}
                  </div>
                  <div className="text-xl font-medium capitalize mt-2">
                    {healthCheck.status}
                  </div>
                  <div className="text-sm text-gray-600">
                    Last check: {healthCheck.timestamp.toLocaleString()}
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div className="text-center p-4 border rounded-lg">
                    <div className="text-2xl font-bold text-blue-600">
                      {healthCheck.response_time}ms
                    </div>
                    <div className="text-sm text-gray-600">Response Time</div>
                  </div>

                  <div className="text-center p-4 border rounded-lg">
                    <div className="text-2xl font-bold text-green-600">
                      {healthCheck.service_availability.filter(s => s.status === 'available').length}
                    </div>
                    <div className="text-sm text-gray-600">Services Available</div>
                  </div>

                  <div className="text-center p-4 border rounded-lg">
                    <div className="text-2xl font-bold text-yellow-600">
                      {healthCheck.service_availability.filter(s => s.status === 'degraded').length}
                    </div>
                    <div className="text-sm text-gray-600">Services Degraded</div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="connections" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Available Connections</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {connections.map(connection => (
                  <div key={connection.id} className="p-4 border rounded-lg">
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-3">
                        {getStatusIcon(connection.status)}
                        <div>
                          <h4 className="font-medium">{connection.name}</h4>
                          <p className="text-sm text-gray-600">{connection.endpoint_url}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge variant="outline" className={getStatusColor(connection.status)}>
                          {connection.status}
                        </Badge>
                        <Badge variant="outline" className={
                          connection.environment === 'production' ? 'bg-red-100 text-red-800' : 'bg-blue-100 text-blue-800'
                        }>
                          {connection.environment}
                        </Badge>
                      </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-3 text-sm">
                      <div>
                        <span className="text-gray-600">Response Time:</span>
                        <span className="ml-2 font-medium">{connection.response_time}ms</span>
                      </div>
                      <div>
                        <span className="text-gray-600">Uptime:</span>
                        <span className="ml-2 font-medium">{connection.uptime_percentage}%</span>
                      </div>
                      <div>
                        <span className="text-gray-600">Rate Limit:</span>
                        <span className="ml-2 font-medium">{connection.rate_limit.requests_per_minute} RPM</span>
                      </div>
                      <div>
                        <span className="text-gray-600">API Version:</span>
                        <span className="ml-2 font-medium">v{connection.api_version}</span>
                      </div>
                    </div>

                    <div className="flex items-center justify-between">
                      <div className="text-sm text-gray-600">
                        Certificate: {connection.certificate_id}
                      </div>
                      <div className="flex gap-2">
                        <Button 
                          variant="outline" 
                          size="sm"
                          onClick={() => handleTestConnection(connection.id)}
                        >
                          <Activity className="h-3 w-3 mr-1" />
                          Test
                        </Button>
                        <Button 
                          variant={activeConnection.id === connection.id ? "default" : "outline"} 
                          size="sm"
                          onClick={() => handleSwitchConnection(connection.id)}
                          disabled={activeConnection.id === connection.id}
                        >
                          {activeConnection.id === connection.id ? 'Active' : 'Switch'}
                        </Button>
                        <Button variant="outline" size="sm">
                          <Edit className="h-3 w-3" />
                        </Button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="settings" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Connection Settings</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <label className="font-medium">Auto-failover</label>
                  <p className="text-sm text-gray-600">
                    Automatically switch to backup connection on failure
                  </p>
                </div>
                <Switch
                  checked={autoFailover}
                  onCheckedChange={setAutoFailover}
                />
              </div>

              <div>
                <label className="block font-medium mb-2">Health Check Interval (seconds)</label>
                <Input type="number" defaultValue="60" className="w-32" />
              </div>

              <div>
                <label className="block font-medium mb-2">Connection Timeout (seconds)</label>
                <Input type="number" defaultValue="30" className="w-32" />
              </div>

              <div>
                <label className="block font-medium mb-2">Retry Attempts</label>
                <Input type="number" defaultValue="3" className="w-32" />
              </div>

              <div className="flex gap-3 pt-4">
                <Button>Save Settings</Button>
                <Button variant="outline">Reset to Defaults</Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};