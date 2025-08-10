/**
 * Security Audit Center Component
 * ===============================
 * 
 * Comprehensive security monitoring and audit interface for APP providers.
 * Connects to app_services/security_compliance/ backend services.
 * 
 * Features:
 * - Certificate lifecycle management
 * - Security audit logging and monitoring
 * - Access control and permission management
 * - Threat detection and incident response
 * - Compliance monitoring and reporting
 * - Security metrics and analytics
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
  Switch,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger
} from '@/components/ui';
import { 
  Shield, 
  AlertTriangle, 
  CheckCircle,
  XCircle,
  Key,
  Lock,
  Eye,
  EyeOff,
  Calendar,
  Clock,
  User,
  Activity,
  FileText,
  Download,
  RefreshCw,
  Settings,
  Bell,
  Search,
  Filter,
  BarChart3,
  TrendingUp,
  AlertOctagon,
  Zap,
  Globe,
  Server
} from 'lucide-react';

import { 
  Certificate, 
  SecurityAudit, 
  SecurityMetrics,
  SecurityLevel
} from '../../types';

// Mock data
const mockCertificates: Certificate[] = [
  {
    id: 'cert_001',
    name: 'FIRS Production Signing Certificate',
    type: 'firs_signing',
    status: 'valid',
    issuer: 'FIRS Certificate Authority',
    subject: 'CN=TaxPoynt APP Production',
    serial_number: '1A2B3C4D5E6F7890',
    valid_from: new Date('2024-01-01'),
    valid_to: new Date('2025-01-01'),
    fingerprint: 'SHA256: 1A:2B:3C:4D:5E:6F:7A:8B:9C:0D:1E:2F:3A:4B:5C:6D',
    key_size: 2048,
    algorithm: 'RSA-SHA256',
    usage: ['Digital Signature', 'Key Encipherment'],
    certificate_chain: ['Root CA', 'Intermediate CA', 'End Entity']
  },
  {
    id: 'cert_002', 
    name: 'SSL/TLS Certificate',
    type: 'ssl_tls',
    status: 'expiring_soon',
    issuer: 'Let\'s Encrypt Authority X3',
    subject: 'CN=api.taxpoynt.com',
    serial_number: '9F8E7D6C5B4A39281736',
    valid_from: new Date('2024-01-15'),
    valid_to: new Date('2024-12-15'),
    fingerprint: 'SHA256: 9F:8E:7D:6C:5B:4A:39:28:17:36:45:54:63:72:81:90',
    key_size: 2048,
    algorithm: 'RSA-SHA256',
    usage: ['Server Authentication'],
    certificate_chain: ['ISRG Root X1', 'R3', 'End Entity']
  },
  {
    id: 'cert_003',
    name: 'API Client Certificate',
    type: 'client_auth',
    status: 'expired',
    issuer: 'Internal CA',
    subject: 'CN=API Client Sandbox',
    serial_number: '5F4E3D2C1B0A98765432',
    valid_from: new Date('2023-06-01'),
    valid_to: new Date('2024-06-01'),
    fingerprint: 'SHA256: 5F:4E:3D:2C:1B:0A:98:76:54:32:10:FE:DC:BA:98:76',
    key_size: 2048,
    algorithm: 'RSA-SHA256',
    usage: ['Client Authentication'],
    certificate_chain: ['Internal Root CA', 'End Entity']
  }
];

const mockSecurityAudits: SecurityAudit[] = [
  {
    id: 'audit_001',
    timestamp: new Date(),
    audit_type: 'certificate',
    severity: 'high',
    title: 'Certificate Expiring Soon',
    description: 'SSL/TLS certificate for api.taxpoynt.com expires in 30 days',
    affected_resources: ['cert_002'],
    recommendations: ['Renew certificate before expiration', 'Set up auto-renewal'],
    status: 'open',
    assigned_to: 'security-team'
  },
  {
    id: 'audit_002',
    timestamp: new Date(Date.now() - 3600000),
    audit_type: 'access',
    severity: 'medium',
    title: 'Multiple Failed Login Attempts',
    description: '5 failed login attempts detected from IP 192.168.1.100',
    affected_resources: ['user_session_manager'],
    recommendations: ['Review access logs', 'Consider IP blocking'],
    status: 'in_progress'
  },
  {
    id: 'audit_003',
    timestamp: new Date(Date.now() - 7200000),
    audit_type: 'transmission',
    severity: 'low',
    title: 'Transmission Security Check',
    description: 'All transmissions properly encrypted and authenticated',
    affected_resources: ['transmission_service'],
    recommendations: [],
    status: 'resolved'
  }
];

const mockSecurityMetrics: SecurityMetrics = {
  certificate_status: {
    total: 15,
    valid: 12,
    expiring_soon: 2,
    expired: 1,
    revoked: 0
  },
  access_attempts: {
    total_attempts: 1247,
    successful_attempts: 1195,
    failed_attempts: 52,
    blocked_attempts: 8,
    suspicious_activities: 3
  },
  transmission_security: {
    encrypted_transmissions: 2456,
    total_transmissions: 2456,
    encryption_rate: 100,
    security_violations: 0
  },
  vulnerability_summary: {
    critical: 0,
    high: 1,
    medium: 3,
    low: 7,
    total: 11
  },
  compliance_score: 94
};

export const SecurityAuditCenter: React.FC = () => {
  const [activeTab, setActiveTab] = useState('overview');
  const [certificates, setCertificates] = useState<Certificate[]>(mockCertificates);
  const [securityAudits, setSecurityAudits] = useState<SecurityAudit[]>(mockSecurityAudits);
  const [securityMetrics, setSecurityMetrics] = useState<SecurityMetrics>(mockSecurityMetrics);
  const [selectedSeverity, setSelectedSeverity] = useState<string>('all');
  const [selectedType, setSelectedType] = useState<string>('all');
  const [searchTerm, setSearchTerm] = useState('');

  const getCertificateStatusIcon = (status: string) => {
    switch (status) {
      case 'valid': return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'expiring_soon': return <AlertTriangle className="h-4 w-4 text-yellow-500" />;
      case 'expired': return <XCircle className="h-4 w-4 text-red-500" />;
      case 'revoked': return <XCircle className="h-4 w-4 text-red-500" />;
      default: return <AlertTriangle className="h-4 w-4 text-gray-500" />;
    }
  };

  const getCertificateStatusColor = (status: string) => {
    switch (status) {
      case 'valid': return 'bg-green-100 text-green-800 border-green-200';
      case 'expiring_soon': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'expired': return 'bg-red-100 text-red-800 border-red-200';
      case 'revoked': return 'bg-red-100 text-red-800 border-red-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getSeverityIcon = (severity: SecurityLevel) => {
    switch (severity) {
      case 'high': return <AlertOctagon className="h-4 w-4 text-red-500" />;
      case 'medium': return <AlertTriangle className="h-4 w-4 text-yellow-500" />;
      case 'low': return <AlertTriangle className="h-4 w-4 text-blue-500" />;
      default: return <AlertTriangle className="h-4 w-4 text-gray-500" />;
    }
  };

  const getSeverityColor = (severity: SecurityLevel) => {
    switch (severity) {
      case 'high': return 'bg-red-100 text-red-800 border-red-200';
      case 'medium': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'low': return 'bg-blue-100 text-blue-800 border-blue-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getComplianceScoreColor = (score: number) => {
    if (score >= 95) return 'text-green-600';
    if (score >= 85) return 'text-blue-600';
    if (score >= 70) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getDaysUntilExpiry = (expiryDate: Date) => {
    const today = new Date();
    const diffTime = expiryDate.getTime() - today.getTime();
    return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
  };

  const handleRenewCertificate = (certificateId: string) => {
    console.log('Renewing certificate:', certificateId);
    // In real implementation, this would call certificate renewal API
  };

  const handleAuditAction = (auditId: string, action: string) => {
    console.log('Audit action:', action, 'for audit:', auditId);
    // In real implementation, this would call audit management API
  };

  const filteredAudits = securityAudits.filter(audit => 
    (selectedSeverity === 'all' || audit.severity === selectedSeverity) &&
    (selectedType === 'all' || audit.audit_type === selectedType) &&
    (searchTerm === '' || 
     audit.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
     audit.description.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Shield className="h-6 w-6 text-blue-600" />
            Security Audit Center
          </h2>
          <p className="text-gray-600 mt-1">
            Comprehensive security monitoring and compliance management
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Badge variant="outline" className={`${getComplianceScoreColor(securityMetrics.compliance_score)} border`}>
            Compliance: {securityMetrics.compliance_score}%
          </Badge>
          <Button variant="outline" size="sm">
            <Download className="h-4 w-4 mr-2" />
            Export Report
          </Button>
        </div>
      </div>

      {/* Critical Alerts */}
      {securityAudits.filter(a => a.severity === 'high' && a.status === 'open').length > 0 && (
        <Alert className="border-red-200 bg-red-50">
          <AlertOctagon className="h-4 w-4 text-red-600" />
          <AlertDescription>
            <div className="flex items-center justify-between">
              <span>
                <strong>Critical Security Alert:</strong> {securityAudits.filter(a => a.severity === 'high' && a.status === 'open').length} high-severity issues require immediate attention
              </span>
              <Button variant="outline" size="sm">
                <Eye className="h-3 w-3 mr-1" />
                Review
              </Button>
            </div>
          </AlertDescription>
        </Alert>
      )}

      {/* Security Metrics Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Compliance Score</p>
                <p className={`text-2xl font-bold ${getComplianceScoreColor(securityMetrics.compliance_score)}`}>
                  {securityMetrics.compliance_score}%
                </p>
              </div>
              <Shield className="h-8 w-8 text-blue-600" />
            </div>
            <Progress value={securityMetrics.compliance_score} className="mt-2" />
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Active Certificates</p>
                <p className="text-2xl font-bold text-green-600">
                  {securityMetrics.certificate_status.valid}/{securityMetrics.certificate_status.total}
                </p>
              </div>
              <Key className="h-8 w-8 text-green-600" />
            </div>
            <div className="mt-2 text-sm text-red-600">
              {securityMetrics.certificate_status.expiring_soon} expiring soon
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Login Success Rate</p>
                <p className="text-2xl font-bold text-purple-600">
                  {Math.round((securityMetrics.access_attempts.successful_attempts / securityMetrics.access_attempts.total_attempts) * 100)}%
                </p>
              </div>
              <User className="h-8 w-8 text-purple-600" />
            </div>
            <div className="mt-2 text-sm text-gray-600">
              {securityMetrics.access_attempts.failed_attempts} failed attempts
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Security Violations</p>
                <p className="text-2xl font-bold text-orange-600">
                  {securityMetrics.transmission_security.security_violations}
                </p>
              </div>
              <AlertTriangle className="h-8 w-8 text-orange-600" />
            </div>
            <div className="mt-2">
              <Badge variant="outline" className="bg-green-50 text-green-700">
                All Clear
              </Badge>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Content */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="certificates">Certificates</TabsTrigger>
          <TabsTrigger value="audits">Security Audits</TabsTrigger>
          <TabsTrigger value="access">Access Control</TabsTrigger>
          <TabsTrigger value="compliance">Compliance</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          {/* Security Dashboard */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Certificate Status Overview</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center justify-between p-3 border rounded-lg">
                    <div className="flex items-center gap-3">
                      <CheckCircle className="h-5 w-5 text-green-500" />
                      <span>Valid Certificates</span>
                    </div>
                    <Badge variant="outline" className="bg-green-100 text-green-800">
                      {securityMetrics.certificate_status.valid}
                    </Badge>
                  </div>
                  
                  <div className="flex items-center justify-between p-3 border rounded-lg">
                    <div className="flex items-center gap-3">
                      <AlertTriangle className="h-5 w-5 text-yellow-500" />
                      <span>Expiring Soon</span>
                    </div>
                    <Badge variant="outline" className="bg-yellow-100 text-yellow-800">
                      {securityMetrics.certificate_status.expiring_soon}
                    </Badge>
                  </div>
                  
                  <div className="flex items-center justify-between p-3 border rounded-lg">
                    <div className="flex items-center gap-3">
                      <XCircle className="h-5 w-5 text-red-500" />
                      <span>Expired</span>
                    </div>
                    <Badge variant="outline" className="bg-red-100 text-red-800">
                      {securityMetrics.certificate_status.expired}
                    </Badge>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Vulnerability Summary</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center justify-between p-3 border rounded-lg">
                    <div className="flex items-center gap-3">
                      <div className="w-3 h-3 bg-red-500 rounded-full"></div>
                      <span>Critical</span>
                    </div>
                    <Badge variant="outline" className="bg-red-100 text-red-800">
                      {securityMetrics.vulnerability_summary.critical}
                    </Badge>
                  </div>
                  
                  <div className="flex items-center justify-between p-3 border rounded-lg">
                    <div className="flex items-center gap-3">
                      <div className="w-3 h-3 bg-orange-500 rounded-full"></div>
                      <span>High</span>
                    </div>
                    <Badge variant="outline" className="bg-orange-100 text-orange-800">
                      {securityMetrics.vulnerability_summary.high}
                    </Badge>
                  </div>
                  
                  <div className="flex items-center justify-between p-3 border rounded-lg">
                    <div className="flex items-center gap-3">
                      <div className="w-3 h-3 bg-yellow-500 rounded-full"></div>
                      <span>Medium</span>
                    </div>
                    <Badge variant="outline" className="bg-yellow-100 text-yellow-800">
                      {securityMetrics.vulnerability_summary.medium}
                    </Badge>
                  </div>
                  
                  <div className="flex items-center justify-between p-3 border rounded-lg">
                    <div className="flex items-center gap-3">
                      <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
                      <span>Low</span>
                    </div>
                    <Badge variant="outline" className="bg-blue-100 text-blue-800">
                      {securityMetrics.vulnerability_summary.low}
                    </Badge>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Recent Security Events */}
          <Card>
            <CardHeader>
              <CardTitle>Recent Security Events</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {securityAudits.slice(0, 5).map(audit => (
                  <div key={audit.id} className="flex items-center justify-between p-3 border rounded-lg">
                    <div className="flex items-center gap-3">
                      {getSeverityIcon(audit.severity)}
                      <div>
                        <p className="font-medium text-sm">{audit.title}</p>
                        <p className="text-xs text-gray-600">{audit.timestamp.toLocaleString()}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant="outline" className={getSeverityColor(audit.severity)}>
                        {audit.severity}
                      </Badge>
                      <Badge variant="outline" className={
                        audit.status === 'open' ? 'bg-red-100 text-red-800' :
                        audit.status === 'in_progress' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-green-100 text-green-800'
                      }>
                        {audit.status.replace('_', ' ')}
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="certificates" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span>Certificate Management</span>
                <Button size="sm">
                  <Key className="h-4 w-4 mr-2" />
                  Add Certificate
                </Button>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Certificate</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Issuer</TableHead>
                    <TableHead>Expiry</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {certificates.map(cert => (
                    <TableRow key={cert.id}>
                      <TableCell>
                        <div>
                          <p className="font-medium">{cert.name}</p>
                          <p className="text-sm text-gray-600">{cert.subject}</p>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className="capitalize">
                          {cert.type.replace('_', ' ')}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          {getCertificateStatusIcon(cert.status)}
                          <Badge variant="outline" className={getCertificateStatusColor(cert.status)}>
                            {cert.status.replace('_', ' ')}
                          </Badge>
                        </div>
                      </TableCell>
                      <TableCell className="text-sm">{cert.issuer}</TableCell>
                      <TableCell>
                        <div>
                          <p className="text-sm">{cert.valid_to.toLocaleDateString()}</p>
                          <p className="text-xs text-gray-600">
                            {cert.status === 'expired' ? 'Expired' : `${getDaysUntilExpiry(cert.valid_to)} days`}
                          </p>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex gap-2">
                          <Button variant="outline" size="sm">
                            <Eye className="h-3 w-3" />
                          </Button>
                          <Button variant="outline" size="sm">
                            <Download className="h-3 w-3" />
                          </Button>
                          {(cert.status === 'expiring_soon' || cert.status === 'expired') && (
                            <Button 
                              variant="outline" 
                              size="sm"
                              onClick={() => handleRenewCertificate(cert.id)}
                            >
                              <RefreshCw className="h-3 w-3" />
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

        <TabsContent value="audits" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span>Security Audit Log</span>
                <div className="flex items-center gap-3">
                  <Input
                    placeholder="Search audits..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-48"
                  />
                  <Select value={selectedSeverity} onValueChange={setSelectedSeverity}>
                    <SelectTrigger className="w-32">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Severities</SelectItem>
                      <SelectItem value="high">High</SelectItem>
                      <SelectItem value="medium">Medium</SelectItem>
                      <SelectItem value="low">Low</SelectItem>
                    </SelectContent>
                  </Select>
                  <Select value={selectedType} onValueChange={setSelectedType}>
                    <SelectTrigger className="w-32">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Types</SelectItem>
                      <SelectItem value="certificate">Certificate</SelectItem>
                      <SelectItem value="access">Access</SelectItem>
                      <SelectItem value="transmission">Transmission</SelectItem>
                      <SelectItem value="configuration">Configuration</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {filteredAudits.map(audit => (
                  <div key={audit.id} className="p-4 border rounded-lg">
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-start gap-3">
                        {getSeverityIcon(audit.severity)}
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <h4 className="font-medium">{audit.title}</h4>
                            <Badge variant="outline" className={getSeverityColor(audit.severity)}>
                              {audit.severity}
                            </Badge>
                            <Badge variant="outline" className="text-xs capitalize">
                              {audit.audit_type}
                            </Badge>
                          </div>
                          <p className="text-sm text-gray-600 mb-2">{audit.description}</p>
                          <div className="flex items-center gap-4 text-xs text-gray-500">
                            <span>{audit.timestamp.toLocaleString()}</span>
                            {audit.assigned_to && <span>Assigned: {audit.assigned_to}</span>}
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge variant="outline" className={
                          audit.status === 'open' ? 'bg-red-100 text-red-800' :
                          audit.status === 'in_progress' ? 'bg-yellow-100 text-yellow-800' :
                          'bg-green-100 text-green-800'
                        }>
                          {audit.status.replace('_', ' ')}
                        </Badge>
                        <Button variant="outline" size="sm">
                          <Eye className="h-3 w-3" />
                        </Button>
                      </div>
                    </div>
                    
                    {audit.recommendations.length > 0 && (
                      <div className="p-3 bg-blue-50 rounded border border-blue-200">
                        <h5 className="text-sm font-medium text-blue-900 mb-2">Recommendations:</h5>
                        <ul className="text-sm text-blue-800 space-y-1">
                          {audit.recommendations.map((rec, index) => (
                            <li key={index} className="flex items-start gap-2">
                              <span>•</span>
                              <span>{rec}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {audit.status === 'open' && (
                      <div className="flex gap-2 mt-3">
                        <Button variant="outline" size="sm" onClick={() => handleAuditAction(audit.id, 'acknowledge')}>
                          Acknowledge
                        </Button>
                        <Button variant="outline" size="sm" onClick={() => handleAuditAction(audit.id, 'assign')}>
                          Assign
                        </Button>
                        <Button variant="outline" size="sm" onClick={() => handleAuditAction(audit.id, 'resolve')}>
                          Mark Resolved
                        </Button>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="access" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Access Control Dashboard</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="text-center p-6 border rounded-lg">
                  <div className="text-3xl font-bold text-green-600">
                    {Math.round((securityMetrics.access_attempts.successful_attempts / securityMetrics.access_attempts.total_attempts) * 100)}%
                  </div>
                  <p className="text-sm text-gray-600 mt-2">Success Rate</p>
                  <div className="mt-2 text-xs text-gray-500">
                    {securityMetrics.access_attempts.successful_attempts.toLocaleString()} successful
                  </div>
                </div>

                <div className="text-center p-6 border rounded-lg">
                  <div className="text-3xl font-bold text-red-600">
                    {securityMetrics.access_attempts.failed_attempts}
                  </div>
                  <p className="text-sm text-gray-600 mt-2">Failed Attempts</p>
                  <div className="mt-2 text-xs text-gray-500">
                    {securityMetrics.access_attempts.blocked_attempts} blocked
                  </div>
                </div>

                <div className="text-center p-6 border rounded-lg">
                  <div className="text-3xl font-bold text-orange-600">
                    {securityMetrics.access_attempts.suspicious_activities}
                  </div>
                  <p className="text-sm text-gray-600 mt-2">Suspicious Activities</p>
                  <div className="mt-2">
                    <Badge variant="outline" className="bg-orange-100 text-orange-800 text-xs">
                      Under Review
                    </Badge>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Access Control Settings</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <label className="font-medium">Two-Factor Authentication</label>
                  <p className="text-sm text-gray-600">Require 2FA for all administrative access</p>
                </div>
                <Switch defaultChecked />
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <label className="font-medium">IP Restriction</label>
                  <p className="text-sm text-gray-600">Limit access to specified IP ranges</p>
                </div>
                <Switch defaultChecked />
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <label className="font-medium">Session Timeout</label>
                  <p className="text-sm text-gray-600">Automatic logout after inactivity</p>
                </div>
                <Switch defaultChecked />
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <label className="font-medium">Failed Login Protection</label>
                  <p className="text-sm text-gray-600">Temporary account lockout after failed attempts</p>
                </div>
                <Switch defaultChecked />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="compliance" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Compliance Overview</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-center mb-6">
                <div className={`text-6xl font-bold ${getComplianceScoreColor(securityMetrics.compliance_score)}`}>
                  {securityMetrics.compliance_score}%
                </div>
                <p className="text-xl font-medium mt-2">Overall Compliance Score</p>
                <Progress value={securityMetrics.compliance_score} className="mt-4 h-3" />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <h4 className="font-medium">Security Standards</h4>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between p-3 border rounded-lg">
                      <span>ISO 27001</span>
                      <Badge variant="outline" className="bg-green-100 text-green-800">Compliant</Badge>
                    </div>
                    <div className="flex items-center justify-between p-3 border rounded-lg">
                      <span>SOC 2 Type II</span>
                      <Badge variant="outline" className="bg-green-100 text-green-800">Compliant</Badge>
                    </div>
                    <div className="flex items-center justify-between p-3 border rounded-lg">
                      <span>GDPR</span>
                      <Badge variant="outline" className="bg-yellow-100 text-yellow-800">Partial</Badge>
                    </div>
                  </div>
                </div>

                <div className="space-y-4">
                  <h4 className="font-medium">Nigerian Regulations</h4>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between p-3 border rounded-lg">
                      <span>NDPR Compliance</span>
                      <Badge variant="outline" className="bg-green-100 text-green-800">Compliant</Badge>
                    </div>
                    <div className="flex items-center justify-between p-3 border rounded-lg">
                      <span>CBN Guidelines</span>
                      <Badge variant="outline" className="bg-green-100 text-green-800">Compliant</Badge>
                    </div>
                    <div className="flex items-center justify-between p-3 border rounded-lg">
                      <span>FIRS Security Requirements</span>
                      <Badge variant="outline" className="bg-green-100 text-green-800">Compliant</Badge>
                    </div>
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