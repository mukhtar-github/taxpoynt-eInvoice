/**
 * Status Tracker Component
 * ========================
 * 
 * Real-time status tracking interface for document lifecycle monitoring.
 * Connects to app_services/status_management/ backend services.
 * 
 * Features:
 * - End-to-end document status tracking
 * - Real-time status updates and notifications
 * - SLA monitoring and breach alerts
 * - Status history and audit trail
 * - Milestone tracking and progress visualization
 * - Performance analytics and reporting
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
  ScrollArea,
  Alert,
  AlertDescription,
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
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Input,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger
} from '@/components/ui';
import { 
  Activity, 
  Clock, 
  CheckCircle,
  XCircle,
  AlertTriangle,
  Info,
  Send,
  FileText,
  Eye,
  RefreshCw,
  Search,
  Filter,
  Calendar,
  Timer,
  Target,
  TrendingUp,
  BarChart3,
  Bell,
  Play,
  Pause,
  MapPin,
  Route
} from 'lucide-react';

import { 
  DocumentStatus, 
  StatusHistoryEntry, 
  Milestone,
  StatusAlert,
  TransmissionStatus
} from '../../types';

// Mock data
const mockDocumentStatuses: DocumentStatus[] = [
  {
    document_id: 'doc_12345',
    current_status: 'transmitted',
    status_history: [
      {
        status: 'pending',
        timestamp: new Date(Date.now() - 7200000),
        duration: 5,
        notes: 'Document queued for processing',
        system_generated: true
      },
      {
        status: 'transmitting',
        timestamp: new Date(Date.now() - 3600000),
        duration: 45,
        notes: 'Transmission to FIRS initiated',
        system_generated: true
      },
      {
        status: 'transmitted',
        timestamp: new Date(Date.now() - 1800000),
        notes: 'Successfully transmitted to FIRS',
        system_generated: true
      }
    ],
    milestones: [
      {
        id: 'validate',
        name: 'Document Validation',
        description: 'Initial document validation and formatting',
        target_time: 5,
        actual_time: 3,
        status: 'completed',
        critical: false
      },
      {
        id: 'queue',
        name: 'Queue Processing',
        description: 'Document added to transmission queue',
        target_time: 10,
        actual_time: 5,
        status: 'completed',
        critical: false
      },
      {
        id: 'transmit',
        name: 'FIRS Transmission',
        description: 'Document transmitted to FIRS API',
        target_time: 30,
        actual_time: 25,
        status: 'completed',
        critical: true
      },
      {
        id: 'acknowledge',
        name: 'FIRS Acknowledgment',
        description: 'Acknowledgment received from FIRS',
        target_time: 60,
        status: 'pending',
        critical: true
      }
    ],
    estimated_completion: new Date(Date.now() + 1800000),
    sla_status: 'on_track'
  },
  {
    document_id: 'doc_12346',
    current_status: 'failed',
    status_history: [
      {
        status: 'pending',
        timestamp: new Date(Date.now() - 10800000),
        duration: 2,
        system_generated: true
      },
      {
        status: 'transmitting',
        timestamp: new Date(Date.now() - 9000000),
        duration: 30,
        system_generated: true
      },
      {
        status: 'failed',
        timestamp: new Date(Date.now() - 7200000),
        notes: 'Validation error: Invalid VAT calculation',
        system_generated: true
      }
    ],
    milestones: [
      {
        id: 'validate',
        name: 'Document Validation',
        description: 'Initial document validation and formatting',
        target_time: 5,
        actual_time: 30,
        status: 'overdue',
        critical: false
      },
      {
        id: 'queue',
        name: 'Queue Processing',
        description: 'Document added to transmission queue',
        target_time: 10,
        status: 'pending',
        critical: false
      }
    ],
    sla_status: 'breached'
  },
  {
    document_id: 'doc_12347',
    current_status: 'acknowledged',
    status_history: [
      {
        status: 'pending',
        timestamp: new Date(Date.now() - 14400000),
        duration: 3,
        system_generated: true
      },
      {
        status: 'transmitting',
        timestamp: new Date(Date.now() - 12600000),
        duration: 25,
        system_generated: true
      },
      {
        status: 'transmitted',
        timestamp: new Date(Date.now() - 10800000),
        duration: 45,
        system_generated: true
      },
      {
        status: 'acknowledged',
        timestamp: new Date(Date.now() - 7200000),
        notes: 'FIRS acknowledgment received - Success',
        system_generated: true
      }
    ],
    milestones: [
      {
        id: 'validate',
        name: 'Document Validation',
        description: 'Initial document validation and formatting',
        target_time: 5,
        actual_time: 3,
        status: 'completed',
        critical: false
      },
      {
        id: 'queue',
        name: 'Queue Processing',
        description: 'Document added to transmission queue',
        target_time: 10,
        actual_time: 5,
        status: 'completed',
        critical: false
      },
      {
        id: 'transmit',
        name: 'FIRS Transmission',
        description: 'Document transmitted to FIRS API',
        target_time: 30,
        actual_time: 25,
        status: 'completed',
        critical: true
      },
      {
        id: 'acknowledge',
        name: 'FIRS Acknowledgment',
        description: 'Acknowledgment received from FIRS',
        target_time: 60,
        actual_time: 45,
        status: 'completed',
        critical: true
      }
    ],
    sla_status: 'on_track'
  }
];

const mockStatusAlerts: StatusAlert[] = [
  {
    id: 'alert_001',
    type: 'sla_breach',
    severity: 'high',
    title: 'SLA Breach Alert',
    description: 'Document doc_12346 has exceeded processing time SLA',
    timestamp: new Date(Date.now() - 3600000),
    affected_documents: ['doc_12346'],
    resolution_steps: [
      'Review validation errors',
      'Check system capacity',
      'Contact technical team if needed'
    ],
    status: 'active'
  },
  {
    id: 'alert_002',
    type: 'high_error_rate',
    severity: 'medium',
    title: 'High Error Rate Detected',
    description: 'Error rate has increased to 15% in the last hour',
    timestamp: new Date(Date.now() - 1800000),
    affected_documents: ['doc_12346', 'doc_12348', 'doc_12349'],
    resolution_steps: [
      'Review common error patterns',
      'Check data quality',
      'Verify FIRS API status'
    ],
    status: 'acknowledged'
  }
];

export const StatusTracker: React.FC = () => {
  const [activeTab, setActiveTab] = useState('overview');
  const [documentStatuses, setDocumentStatuses] = useState<DocumentStatus[]>(mockDocumentStatuses);
  const [statusAlerts, setStatusAlerts] = useState<StatusAlert[]>(mockStatusAlerts);
  const [selectedStatus, setSelectedStatus] = useState<string>('all');
  const [selectedSLA, setSelectedSLA] = useState<string>('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedDocument, setSelectedDocument] = useState<DocumentStatus | null>(null);

  const getStatusIcon = (status: TransmissionStatus) => {
    switch (status) {
      case 'pending': return <Clock className="h-4 w-4 text-gray-500" />;
      case 'transmitting': return <Send className="h-4 w-4 text-blue-500 animate-pulse" />;
      case 'transmitted': return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'acknowledged': return <CheckCircle className="h-4 w-4 text-blue-500" />;
      case 'failed': return <XCircle className="h-4 w-4 text-red-500" />;
      case 'retrying': return <RefreshCw className="h-4 w-4 text-orange-500 animate-spin" />;
      default: return <AlertTriangle className="h-4 w-4 text-gray-500" />;
    }
  };

  const getStatusColor = (status: TransmissionStatus) => {
    switch (status) {
      case 'pending': return 'bg-gray-100 text-gray-800 border-gray-200';
      case 'transmitting': return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'transmitted': return 'bg-green-100 text-green-800 border-green-200';
      case 'acknowledged': return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'failed': return 'bg-red-100 text-red-800 border-red-200';
      case 'retrying': return 'bg-orange-100 text-orange-800 border-orange-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getSLAStatusColor = (status: string) => {
    switch (status) {
      case 'on_track': return 'bg-green-100 text-green-800 border-green-200';
      case 'at_risk': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'breached': return 'bg-red-100 text-red-800 border-red-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getMilestoneStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'pending': return <Clock className="h-4 w-4 text-gray-500" />;
      case 'overdue': return <AlertTriangle className="h-4 w-4 text-red-500" />;
      default: return <Clock className="h-4 w-4 text-gray-500" />;
    }
  };

  const getMilestoneProgress = (milestones: Milestone[]) => {
    const completed = milestones.filter(m => m.status === 'completed').length;
    return Math.round((completed / milestones.length) * 100);
  };

  const getTotalProcessingTime = (history: StatusHistoryEntry[]) => {
    return history.reduce((total, entry) => total + (entry.duration || 0), 0);
  };

  const filteredDocuments = documentStatuses.filter(doc => 
    (selectedStatus === 'all' || doc.current_status === selectedStatus) &&
    (selectedSLA === 'all' || doc.sla_status === selectedSLA) &&
    (searchTerm === '' || doc.document_id.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  const statusSummary = {
    total: documentStatuses.length,
    pending: documentStatuses.filter(d => d.current_status === 'pending').length,
    transmitting: documentStatuses.filter(d => d.current_status === 'transmitting').length,
    transmitted: documentStatuses.filter(d => d.current_status === 'transmitted').length,
    acknowledged: documentStatuses.filter(d => d.current_status === 'acknowledged').length,
    failed: documentStatuses.filter(d => d.current_status === 'failed').length,
    sla_breached: documentStatuses.filter(d => d.sla_status === 'breached').length
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Activity className="h-6 w-6 text-blue-600" />
            Status Tracker
          </h2>
          <p className="text-gray-600 mt-1">
            Real-time document lifecycle monitoring and SLA tracking
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-200">
            {statusSummary.total} Documents Tracked
          </Badge>
          <Button variant="outline" size="sm">
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
        </div>
      </div>

      {/* Active Alerts */}
      {statusAlerts.filter(a => a.status === 'active').length > 0 && (
        <div className="space-y-2">
          {statusAlerts.filter(a => a.status === 'active').map(alert => (
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

      {/* Status Summary */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Total Documents</p>
                <p className="text-2xl font-bold text-blue-600">
                  {statusSummary.total}
                </p>
              </div>
              <FileText className="h-8 w-8 text-blue-600" />
            </div>
            <div className="mt-2 text-sm text-gray-600">
              {statusSummary.acknowledged} completed
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">In Progress</p>
                <p className="text-2xl font-bold text-orange-600">
                  {statusSummary.transmitting + statusSummary.transmitted}
                </p>
              </div>
              <Send className="h-8 w-8 text-orange-600" />
            </div>
            <div className="mt-2 text-sm text-gray-600">
              {statusSummary.pending} pending
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Success Rate</p>
                <p className="text-2xl font-bold text-green-600">
                  {Math.round((statusSummary.acknowledged / statusSummary.total) * 100)}%
                </p>
              </div>
              <Target className="h-8 w-8 text-green-600" />
            </div>
            <Progress 
              value={(statusSummary.acknowledged / statusSummary.total) * 100} 
              className="mt-2" 
            />
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">SLA Breaches</p>
                <p className="text-2xl font-bold text-red-600">
                  {statusSummary.sla_breached}
                </p>
              </div>
              <AlertTriangle className="h-8 w-8 text-red-600" />
            </div>
            <div className="mt-2">
              {statusSummary.sla_breached === 0 ? (
                <Badge variant="outline" className="bg-green-50 text-green-700">
                  All On Track
                </Badge>
              ) : (
                <Badge variant="outline" className="bg-red-50 text-red-700">
                  Attention Required
                </Badge>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Content */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="tracking">Document Tracking</TabsTrigger>
          <TabsTrigger value="milestones">Milestones</TabsTrigger>
          <TabsTrigger value="analytics">Analytics</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          {/* Status Distribution */}
          <Card>
            <CardHeader>
              <CardTitle>Status Distribution</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                <div className="text-center p-4 border rounded-lg">
                  <div className="flex items-center justify-center gap-2 mb-2">
                    <Clock className="h-5 w-5 text-gray-500" />
                    <span className="font-medium">Pending</span>
                  </div>
                  <div className="text-2xl font-bold text-gray-600">{statusSummary.pending}</div>
                </div>

                <div className="text-center p-4 border rounded-lg">
                  <div className="flex items-center justify-center gap-2 mb-2">
                    <Send className="h-5 w-5 text-blue-500" />
                    <span className="font-medium">Transmitting</span>
                  </div>
                  <div className="text-2xl font-bold text-blue-600">{statusSummary.transmitting}</div>
                </div>

                <div className="text-center p-4 border rounded-lg">
                  <div className="flex items-center justify-center gap-2 mb-2">
                    <CheckCircle className="h-5 w-5 text-green-500" />
                    <span className="font-medium">Transmitted</span>
                  </div>
                  <div className="text-2xl font-bold text-green-600">{statusSummary.transmitted}</div>
                </div>

                <div className="text-center p-4 border rounded-lg">
                  <div className="flex items-center justify-center gap-2 mb-2">
                    <CheckCircle className="h-5 w-5 text-blue-500" />
                    <span className="font-medium">Acknowledged</span>
                  </div>
                  <div className="text-2xl font-bold text-blue-600">{statusSummary.acknowledged}</div>
                </div>

                <div className="text-center p-4 border rounded-lg">
                  <div className="flex items-center justify-center gap-2 mb-2">
                    <XCircle className="h-5 w-5 text-red-500" />
                    <span className="font-medium">Failed</span>
                  </div>
                  <div className="text-2xl font-bold text-red-600">{statusSummary.failed}</div>
                </div>

                <div className="text-center p-4 border rounded-lg">
                  <div className="flex items-center justify-center gap-2 mb-2">
                    <AlertTriangle className="h-5 w-5 text-red-500" />
                    <span className="font-medium">SLA Breached</span>
                  </div>
                  <div className="text-2xl font-bold text-red-600">{statusSummary.sla_breached}</div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Recent Status Changes */}
          <Card>
            <CardHeader>
              <CardTitle>Recent Status Changes</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {documentStatuses.slice(0, 5).map(doc => (
                  <div key={doc.document_id} className="flex items-center justify-between p-3 border rounded-lg">
                    <div className="flex items-center gap-3">
                      {getStatusIcon(doc.current_status)}
                      <div>
                        <p className="font-medium">{doc.document_id}</p>
                        <p className="text-sm text-gray-600">
                          Last updated: {doc.status_history[doc.status_history.length - 1]?.timestamp.toLocaleTimeString()}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant="outline" className={getStatusColor(doc.current_status)}>
                        {doc.current_status}
                      </Badge>
                      <Badge variant="outline" className={getSLAStatusColor(doc.sla_status)}>
                        {doc.sla_status.replace('_', ' ')}
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="tracking" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span>Document Status Tracking</span>
                <div className="flex items-center gap-3">
                  <Input
                    placeholder="Search documents..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-48"
                  />
                  <Select value={selectedStatus} onValueChange={setSelectedStatus}>
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
                    </SelectContent>
                  </Select>
                  <Select value={selectedSLA} onValueChange={setSelectedSLA}>
                    <SelectTrigger className="w-32">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All SLA</SelectItem>
                      <SelectItem value="on_track">On Track</SelectItem>
                      <SelectItem value="at_risk">At Risk</SelectItem>
                      <SelectItem value="breached">Breached</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Document ID</TableHead>
                    <TableHead>Current Status</TableHead>
                    <TableHead>Progress</TableHead>
                    <TableHead>Processing Time</TableHead>
                    <TableHead>SLA Status</TableHead>
                    <TableHead>ETA</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredDocuments.map(doc => (
                    <TableRow key={doc.document_id}>
                      <TableCell className="font-mono">{doc.document_id}</TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          {getStatusIcon(doc.current_status)}
                          <Badge variant="outline" className={getStatusColor(doc.current_status)}>
                            {doc.current_status}
                          </Badge>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Progress value={getMilestoneProgress(doc.milestones)} className="w-16 h-2" />
                          <span className="text-sm text-gray-600">
                            {getMilestoneProgress(doc.milestones)}%
                          </span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <span className="text-sm">
                          {getTotalProcessingTime(doc.status_history)}min
                        </span>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className={getSLAStatusColor(doc.sla_status)}>
                          {doc.sla_status.replace('_', ' ')}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <span className="text-sm">
                          {doc.estimated_completion ? doc.estimated_completion.toLocaleTimeString() : '-'}
                        </span>
                      </TableCell>
                      <TableCell>
                        <Dialog>
                          <DialogTrigger asChild>
                            <Button 
                              variant="outline" 
                              size="sm"
                              onClick={() => setSelectedDocument(doc)}
                            >
                              <Eye className="h-3 w-3 mr-1" />
                              Details
                            </Button>
                          </DialogTrigger>
                          <DialogContent className="max-w-4xl">
                            <DialogHeader>
                              <DialogTitle>Document Status Details - {doc.document_id}</DialogTitle>
                            </DialogHeader>
                            <div className="space-y-6">
                              {/* Status Timeline */}
                              <div>
                                <h4 className="font-medium mb-3">Status Timeline</h4>
                                <div className="space-y-3">
                                  {doc.status_history.map((entry, index) => (
                                    <div key={index} className="flex items-center gap-3 p-3 border rounded-lg">
                                      {getStatusIcon(entry.status)}
                                      <div className="flex-1">
                                        <div className="flex items-center gap-2">
                                          <span className="font-medium capitalize">{entry.status.replace('_', ' ')}</span>
                                          <Badge variant="outline" className="text-xs">
                                            {entry.timestamp.toLocaleString()}
                                          </Badge>
                                        </div>
                                        {entry.notes && (
                                          <p className="text-sm text-gray-600 mt-1">{entry.notes}</p>
                                        )}
                                        {entry.duration && (
                                          <p className="text-xs text-gray-500">Duration: {entry.duration} minutes</p>
                                        )}
                                      </div>
                                    </div>
                                  ))}
                                </div>
                              </div>

                              {/* Milestones */}
                              <div>
                                <h4 className="font-medium mb-3">Milestones</h4>
                                <div className="space-y-2">
                                  {doc.milestones.map(milestone => (
                                    <div key={milestone.id} className="flex items-center justify-between p-3 border rounded-lg">
                                      <div className="flex items-center gap-3">
                                        {getMilestoneStatusIcon(milestone.status)}
                                        <div>
                                          <p className="font-medium">{milestone.name}</p>
                                          <p className="text-sm text-gray-600">{milestone.description}</p>
                                        </div>
                                      </div>
                                      <div className="text-right">
                                        <div className="text-sm">
                                          {milestone.actual_time ? `${milestone.actual_time}min` : `Target: ${milestone.target_time}min`}
                                        </div>
                                        <Badge 
                                          variant="outline" 
                                          className={`text-xs ${
                                            milestone.status === 'completed' ? 'bg-green-100 text-green-800' :
                                            milestone.status === 'overdue' ? 'bg-red-100 text-red-800' :
                                            'bg-gray-100 text-gray-800'
                                          }`}
                                        >
                                          {milestone.status}
                                        </Badge>
                                      </div>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            </div>
                          </DialogContent>
                        </Dialog>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="milestones" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Milestone Performance</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Milestone completion rates would go here */}
                <div className="space-y-4">
                  <h4 className="font-medium">Milestone Completion Times</h4>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between p-3 border rounded-lg">
                      <span>Document Validation</span>
                      <div className="text-right">
                        <div className="text-sm font-medium">Avg: 3.2min</div>
                        <div className="text-xs text-gray-600">Target: 5min</div>
                      </div>
                    </div>
                    <div className="flex items-center justify-between p-3 border rounded-lg">
                      <span>Queue Processing</span>
                      <div className="text-right">
                        <div className="text-sm font-medium">Avg: 5.8min</div>
                        <div className="text-xs text-gray-600">Target: 10min</div>
                      </div>
                    </div>
                    <div className="flex items-center justify-between p-3 border rounded-lg">
                      <span>FIRS Transmission</span>
                      <div className="text-right">
                        <div className="text-sm font-medium">Avg: 26.5min</div>
                        <div className="text-xs text-gray-600">Target: 30min</div>
                      </div>
                    </div>
                  </div>
                </div>

                <div>
                  <h4 className="font-medium mb-4">Performance Trends</h4>
                  <div className="text-center p-8 border rounded-lg bg-gray-50">
                    <BarChart3 className="h-12 w-12 mx-auto mb-4 text-gray-400" />
                    <p className="text-gray-600">Performance analytics chart would be displayed here</p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="analytics" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Processing Analytics</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="text-center p-6 border rounded-lg">
                  <div className="text-3xl font-bold text-blue-600">
                    {Math.round(documentStatuses.reduce((sum, doc) => sum + getTotalProcessingTime(doc.status_history), 0) / documentStatuses.length)}min
                  </div>
                  <p className="text-sm text-gray-600 mt-2">Average Processing Time</p>
                  <div className="mt-2">
                    <Badge variant="outline" className="bg-green-50 text-green-700">
                      12% improvement
                    </Badge>
                  </div>
                </div>

                <div className="text-center p-6 border rounded-lg">
                  <div className="text-3xl font-bold text-green-600">
                    {Math.round((1 - statusSummary.sla_breached / statusSummary.total) * 100)}%
                  </div>
                  <p className="text-sm text-gray-600 mt-2">SLA Compliance</p>
                  <div className="mt-2">
                    <Badge variant="outline" className="bg-green-50 text-green-700">
                      On Target
                    </Badge>
                  </div>
                </div>

                <div className="text-center p-6 border rounded-lg">
                  <div className="text-3xl font-bold text-purple-600">
                    {Math.round((statusSummary.acknowledged / statusSummary.total) * 100)}%
                  </div>
                  <p className="text-sm text-gray-600 mt-2">Success Rate</p>
                  <div className="mt-2">
                    <Badge variant="outline" className="bg-purple-50 text-purple-700">
                      +5% this week
                    </Badge>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};