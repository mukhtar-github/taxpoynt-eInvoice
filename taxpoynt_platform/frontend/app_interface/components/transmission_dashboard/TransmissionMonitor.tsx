/**
 * Transmission Monitor Component
 * =============================
 * 
 * Real-time monitoring dashboard for FIRS document transmission pipeline.
 * Connects to app_services/transmission/ backend services for live status tracking.
 * 
 * Features:
 * - Real-time transmission status monitoring
 * - Live submission pipeline tracking
 * - Transmission statistics and metrics
 * - Error handling and retry management
 * - Batch and individual document monitoring
 * - Performance analytics and SLA tracking
 */

import React, { useState, useEffect, useCallback } from 'react';
import { 
  Card, 
  CardContent, 
  CardHeader, 
  CardTitle,
  Button,
  Badge,
  Progress,
  ScrollArea,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
  Alert,
  AlertDescription,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Input
} from '@/components/ui';
import { 
  Activity, 
  Send, 
  CheckCircle, 
  XCircle, 
  Clock,
  RefreshCw,
  AlertTriangle,
  BarChart3,
  Filter,
  Search,
  Download,
  Eye,
  Pause,
  Play,
  RotateCcw,
  Zap,
  TrendingUp,
  Users,
  FileText,
  Timer
} from 'lucide-react';

// Import types
import { 
  TransmissionJob, 
  TransmissionStats, 
  TransmissionStatus,
  StatusAlert,
  DailyVolume
} from '../../types';

// Mock data - in real implementation, this would come from API
const mockTransmissionJobs: TransmissionJob[] = [
  {
    id: 'tx_001',
    document_id: 'doc_12345',
    document_type: 'invoice',
    status: 'transmitted',
    priority: 'high',
    created_at: new Date(),
    submitted_at: new Date(),
    acknowledged_at: new Date(),
    retry_count: 0,
    max_retries: 3,
    transmission_metadata: {
      source_system: 'SAP ERP',
      taxpayer_tin: '12345678901234',
      document_reference: 'INV-2024-001',
      submission_method: 'real_time',
      transmission_id: 'tx_firs_001',
      firs_reference: 'FIRS_REF_001'
    }
  },
  {
    id: 'tx_002',
    document_id: 'doc_12346',
    document_type: 'credit_note',
    status: 'failed',
    priority: 'normal',
    created_at: new Date(Date.now() - 3600000),
    retry_count: 2,
    max_retries: 3,
    transmission_metadata: {
      source_system: 'Odoo',
      taxpayer_tin: '98765432109876',
      document_reference: 'CN-2024-001',
      submission_method: 'batch'
    },
    error_details: {
      error_code: 'VALIDATION_ERROR',
      error_message: 'Invalid VAT calculation',
      error_category: 'validation',
      context: {},
      resolution_suggestions: ['Check VAT rate configuration', 'Verify calculation formula'],
      documentation_links: ['https://docs.firs.gov.ng/validation']
    }
  },
  {
    id: 'tx_003',
    document_id: 'doc_12347',
    document_type: 'invoice',
    status: 'transmitting',
    priority: 'normal',
    created_at: new Date(Date.now() - 1800000),
    submitted_at: new Date(Date.now() - 300000),
    retry_count: 0,
    max_retries: 3,
    transmission_metadata: {
      source_system: 'QuickBooks',
      taxpayer_tin: '11111111111111',
      document_reference: 'QB-INV-001',
      submission_method: 'real_time',
      transmission_id: 'tx_firs_003'
    }
  }
];

const mockTransmissionStats: TransmissionStats = {
  total_submissions: 1247,
  successful_transmissions: 1175,
  failed_transmissions: 72,
  pending_transmissions: 15,
  success_rate: 94.2,
  average_response_time: 2.3,
  daily_volume: [
    { date: '2024-01-01', count: 45, success_count: 42, failure_count: 3 },
    { date: '2024-01-02', count: 52, success_count: 49, failure_count: 3 },
    { date: '2024-01-03', count: 38, success_count: 36, failure_count: 2 }
  ],
  status_breakdown: [
    { status: 'transmitted', count: 1175, percentage: 94.2 },
    { status: 'failed', count: 72, percentage: 5.8 },
    { status: 'transmitting', count: 8, percentage: 0.6 },
    { status: 'pending', count: 15, percentage: 1.2 }
  ]
};

const mockAlerts: StatusAlert[] = [
  {
    id: 'alert_001',
    type: 'high_error_rate',
    severity: 'high',
    title: 'High Error Rate Detected',
    description: 'Error rate has exceeded 10% threshold in the last hour',
    timestamp: new Date(Date.now() - 1800000),
    affected_documents: ['doc_12346', 'doc_12348'],
    resolution_steps: ['Check FIRS connectivity', 'Review validation rules'],
    status: 'active'
  }
];

export const TransmissionMonitor: React.FC = () => {
  const [activeTab, setActiveTab] = useState('live');
  const [transmissionJobs, setTransmissionJobs] = useState<TransmissionJob[]>(mockTransmissionJobs);
  const [transmissionStats, setTransmissionStats] = useState<TransmissionStats>(mockTransmissionStats);
  const [alerts, setAlerts] = useState<StatusAlert[]>(mockAlerts);
  const [isAutoRefresh, setIsAutoRefresh] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState(5000);
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [searchTerm, setSearchTerm] = useState('');

  // Auto-refresh functionality
  useEffect(() => {
    if (!isAutoRefresh) return;

    const interval = setInterval(() => {
      // In real implementation, this would call API endpoints
      console.log('Refreshing transmission data...');
      // fetchTransmissionJobs();
      // fetchTransmissionStats();
    }, refreshInterval);

    return () => clearInterval(interval);
  }, [isAutoRefresh, refreshInterval]);

  const getStatusIcon = (status: TransmissionStatus) => {
    switch (status) {
      case 'transmitted': return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'acknowledged': return <CheckCircle className="h-4 w-4 text-blue-500" />;
      case 'transmitting': return <Send className="h-4 w-4 text-yellow-500 animate-pulse" />;
      case 'pending': return <Clock className="h-4 w-4 text-gray-500" />;
      case 'failed': return <XCircle className="h-4 w-4 text-red-500" />;
      case 'retrying': return <RefreshCw className="h-4 w-4 text-orange-500 animate-spin" />;
      default: return <AlertTriangle className="h-4 w-4 text-gray-500" />;
    }
  };

  const getStatusColor = (status: TransmissionStatus) => {
    switch (status) {
      case 'transmitted': return 'bg-green-100 text-green-800 border-green-200';
      case 'acknowledged': return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'transmitting': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'pending': return 'bg-gray-100 text-gray-800 border-gray-200';
      case 'failed': return 'bg-red-100 text-red-800 border-red-200';
      case 'retrying': return 'bg-orange-100 text-orange-800 border-orange-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return 'bg-red-100 text-red-800 border-red-200';
      case 'normal': return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'low': return 'bg-gray-100 text-gray-800 border-gray-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const handleRetryTransmission = (jobId: string) => {
    console.log('Retrying transmission:', jobId);
    // In real implementation, this would call retry API
  };

  const handlePauseTransmission = (jobId: string) => {
    console.log('Pausing transmission:', jobId);
    // In real implementation, this would call pause API
  };

  const filteredJobs = transmissionJobs.filter(job => 
    (filterStatus === 'all' || job.status === filterStatus) &&
    (searchTerm === '' || 
     job.document_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
     job.transmission_metadata.document_reference.toLowerCase().includes(searchTerm.toLowerCase()) ||
     job.transmission_metadata.taxpayer_tin.includes(searchTerm))
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Activity className="h-6 w-6 text-blue-600" />
            Transmission Monitor
          </h2>
          <p className="text-gray-600 mt-1">
            Real-time monitoring of FIRS document transmission pipeline
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button
            variant={isAutoRefresh ? "default" : "outline"}
            size="sm"
            onClick={() => setIsAutoRefresh(!isAutoRefresh)}
          >
            {isAutoRefresh ? <Pause className="h-4 w-4 mr-2" /> : <Play className="h-4 w-4 mr-2" />}
            {isAutoRefresh ? 'Pause' : 'Resume'} Auto-refresh
          </Button>
          <Button variant="outline" size="sm">
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
        </div>
      </div>

      {/* Active Alerts */}
      {alerts.length > 0 && (
        <div className="space-y-2">
          {alerts.map(alert => (
            <Alert key={alert.id} className="border-orange-200 bg-orange-50">
              <AlertTriangle className="h-4 w-4 text-orange-600" />
              <AlertDescription>
                <div className="flex items-center justify-between">
                  <div>
                    <span className="font-medium">{alert.title}</span>
                    <span className="ml-2 text-sm">{alert.description}</span>
                  </div>
                  <Badge variant="outline" className="bg-orange-100 text-orange-800">
                    {alert.severity}
                  </Badge>
                </div>
              </AlertDescription>
            </Alert>
          ))}
        </div>
      )}

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Success Rate</p>
                <p className="text-2xl font-bold text-green-600">
                  {transmissionStats.success_rate}%
                </p>
              </div>
              <TrendingUp className="h-8 w-8 text-green-600" />
            </div>
            <Progress value={transmissionStats.success_rate} className="mt-2" />
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Total Submissions</p>
                <p className="text-2xl font-bold text-blue-600">
                  {transmissionStats.total_submissions.toLocaleString()}
                </p>
              </div>
              <FileText className="h-8 w-8 text-blue-600" />
            </div>
            <div className="mt-2 text-sm text-gray-600">
              {transmissionStats.successful_transmissions} successful
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Avg Response Time</p>
                <p className="text-2xl font-bold text-purple-600">
                  {transmissionStats.average_response_time}s
                </p>
              </div>
              <Timer className="h-8 w-8 text-purple-600" />
            </div>
            <div className="mt-2">
              <Badge variant="outline" className="bg-green-50 text-green-700">
                Within SLA
              </Badge>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Active Transmissions</p>
                <p className="text-2xl font-bold text-orange-600">
                  {transmissionStats.pending_transmissions}
                </p>
              </div>
              <Zap className="h-8 w-8 text-orange-600" />
            </div>
            <div className="mt-2 text-sm text-gray-600">
              {transmissionJobs.filter(j => j.status === 'transmitting').length} in progress
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Content */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="live">Live Monitor</TabsTrigger>
          <TabsTrigger value="queue">Queue Status</TabsTrigger>
          <TabsTrigger value="analytics">Analytics</TabsTrigger>
          <TabsTrigger value="errors">Error Analysis</TabsTrigger>
        </TabsList>

        <TabsContent value="live" className="space-y-6">
          {/* Live Transmission Table */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span>Live Transmissions</span>
                <div className="flex items-center gap-3">
                  <div className="flex items-center gap-2">
                    <Input
                      placeholder="Search documents..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      className="w-48"
                    />
                    <Select value={filterStatus} onValueChange={setFilterStatus}>
                      <SelectTrigger className="w-40">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">All Status</SelectItem>
                        <SelectItem value="pending">Pending</SelectItem>
                        <SelectItem value="transmitting">Transmitting</SelectItem>
                        <SelectItem value="transmitted">Transmitted</SelectItem>
                        <SelectItem value="acknowledged">Acknowledged</SelectItem>
                        <SelectItem value="failed">Failed</SelectItem>
                        <SelectItem value="retrying">Retrying</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Document</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Priority</TableHead>
                    <TableHead>Source</TableHead>
                    <TableHead>Submitted</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredJobs.map(job => (
                    <TableRow key={job.id}>
                      <TableCell>
                        <div>
                          <p className="font-medium">{job.transmission_metadata.document_reference}</p>
                          <p className="text-sm text-gray-600">TIN: {job.transmission_metadata.taxpayer_tin}</p>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className="capitalize">
                          {job.document_type.replace('_', ' ')}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          {getStatusIcon(job.status)}
                          <Badge variant="outline" className={getStatusColor(job.status)}>
                            {job.status}
                          </Badge>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className={getPriorityColor(job.priority)}>
                          {job.priority}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <span className="text-sm">{job.transmission_metadata.source_system}</span>
                      </TableCell>
                      <TableCell>
                        <span className="text-sm">
                          {job.submitted_at ? job.submitted_at.toLocaleTimeString() : 'Not submitted'}
                        </span>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Button variant="outline" size="sm">
                            <Eye className="h-3 w-3" />
                          </Button>
                          {job.status === 'failed' && (
                            <Button 
                              variant="outline" 
                              size="sm"
                              onClick={() => handleRetryTransmission(job.id)}
                            >
                              <RotateCcw className="h-3 w-3" />
                            </Button>
                          )}
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="queue" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Queue Status Overview</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {transmissionStats.status_breakdown.map(item => (
                  <div key={item.status} className="p-4 border rounded-lg">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-medium capitalize">{item.status.replace('_', ' ')}</span>
                      {getStatusIcon(item.status)}
                    </div>
                    <div className="text-2xl font-bold text-gray-900">{item.count}</div>
                    <div className="text-sm text-gray-600">{item.percentage}% of total</div>
                    <Progress value={item.percentage} className="mt-2 h-2" />
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="analytics" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Daily Volume Trends</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {transmissionStats.daily_volume.map(day => (
                  <div key={day.date} className="flex items-center justify-between p-4 border rounded-lg">
                    <div>
                      <span className="font-medium">{day.date}</span>
                      <div className="text-sm text-gray-600">
                        {day.success_count} successful, {day.failure_count} failed
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-lg font-bold">{day.count}</div>
                      <div className="text-sm text-gray-600">total submissions</div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="errors" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Recent Transmission Errors</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {transmissionJobs.filter(job => job.status === 'failed').map(job => (
                  <div key={job.id} className="p-4 border-l-4 border-red-400 bg-red-50 rounded-r-lg">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h4 className="font-medium text-red-900">
                          {job.transmission_metadata.document_reference}
                        </h4>
                        <p className="text-sm text-red-700 mt-1">
                          {job.error_details?.error_message}
                        </p>
                        <div className="mt-2 flex items-center gap-4 text-xs text-red-600">
                          <span>Error Code: {job.error_details?.error_code}</span>
                          <span>Category: {job.error_details?.error_category}</span>
                          <span>Retry: {job.retry_count}/{job.max_retries}</span>
                        </div>
                      </div>
                      <Button 
                        variant="outline" 
                        size="sm"
                        onClick={() => handleRetryTransmission(job.id)}
                      >
                        <RotateCcw className="h-3 w-3 mr-1" />
                        Retry
                      </Button>
                    </div>
                    {job.error_details?.resolution_suggestions && (
                      <div className="mt-3 p-3 bg-yellow-50 rounded border">
                        <h5 className="text-sm font-medium text-yellow-900 mb-2">Resolution Suggestions:</h5>
                        <ul className="text-sm text-yellow-800 space-y-1">
                          {job.error_details.resolution_suggestions.map((suggestion, index) => (
                            <li key={index} className="flex items-start gap-2">
                              <span>•</span>
                              <span>{suggestion}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};