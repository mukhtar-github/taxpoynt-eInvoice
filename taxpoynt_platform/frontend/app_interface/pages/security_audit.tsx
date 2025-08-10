/**
 * APP Security Audit Page
 * =======================
 * 
 * Comprehensive security audit interface for Access Point Providers.
 * Monitors security events, compliance status, and access controls.
 * 
 * Features:
 * - Security event monitoring and logging
 * - Certificate lifecycle management
 * - Access control and permissions audit
 * - Compliance status tracking
 * - Security incident response
 * - Audit trail and reporting
 * 
 * @author TaxPoynt Development Team
 * @version 1.0.0
 */

import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Tabs, Button, Space, Table, Alert, Badge, Timeline, Statistic } from 'antd';
import {
  ShieldCheckOutlined,
  SafetyCertificateOutlined,
  AuditOutlined,
  ExclamationTriangleOutlined,
  UserOutlined,
  LockOutlined,
  ReloadOutlined,
  DownloadOutlined,
  WarningOutlined
} from '@ant-design/icons';

// Import APP Interface components
import { SecurityAuditCenter } from '../components/security_center/SecurityAuditCenter';

// Import types
import type { SecurityEvent, CertificateInfo, AccessLog, ComplianceStatus } from '../types';

const { TabPane } = Tabs;

interface SecurityAuditPageProps {
  className?: string;
}

interface SecurityMetrics {
  totalEvents: number;
  criticalEvents: number;
  warningEvents: number;
  infoEvents: number;
  blockedAttempts: number;
  activeUsers: number;
  certificateStatus: string;
  complianceScore: number;
}

export const SecurityAuditPage: React.FC<SecurityAuditPageProps> = ({ className }) => {
  // State management
  const [metrics, setMetrics] = useState<SecurityMetrics | null>(null);
  const [securityEvents, setSecurityEvents] = useState<SecurityEvent[]>([]);
  const [accessLogs, setAccessLogs] = useState<AccessLog[]>([]);
  const [certificates, setCertificates] = useState<CertificateInfo[]>([]);
  const [complianceStatus, setComplianceStatus] = useState<ComplianceStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');

  // Auto-refresh functionality
  useEffect(() => {
    loadSecurityData();
    const interval = setInterval(loadSecurityData, 60000); // 1 minute
    return () => clearInterval(interval);
  }, []);

  const loadSecurityData = async () => {
    try {
      setRefreshing(true);
      
      // Simulate API calls to security services
      const [metricsData, eventsData, logsData, certData, complianceData] = await Promise.all([
        fetchSecurityMetrics(),
        fetchSecurityEvents(),
        fetchAccessLogs(),
        fetchCertificates(),
        fetchComplianceStatus()
      ]);

      setMetrics(metricsData);
      setSecurityEvents(eventsData);
      setAccessLogs(logsData);
      setCertificates(certData);
      setComplianceStatus(complianceData);
      setLoading(false);
    } catch (error) {
      console.error('Failed to load security data:', error);
    } finally {
      setRefreshing(false);
    }
  };

  // Mock API functions (replace with actual API calls)
  const fetchSecurityMetrics = async (): Promise<SecurityMetrics> => {
    return {
      totalEvents: 1247,
      criticalEvents: 3,
      warningEvents: 15,
      infoEvents: 1229,
      blockedAttempts: 47,
      activeUsers: 342,
      certificateStatus: 'valid',
      complianceScore: 96.5
    };
  };

  const fetchSecurityEvents = async (): Promise<SecurityEvent[]> => {
    return [
      {
        id: '1',
        timestamp: new Date(Date.now() - 15 * 60000),
        type: 'authentication',
        severity: 'warning',
        message: 'Multiple failed login attempts detected',
        source: '192.168.1.45',
        user: 'admin@company.com',
        resolved: false
      },
      {
        id: '2',
        timestamp: new Date(Date.now() - 2 * 60 * 60000),
        type: 'certificate',
        severity: 'info',
        message: 'Certificate renewal completed successfully',
        source: 'system',
        user: 'system',
        resolved: true
      }
    ];
  };

  const fetchAccessLogs = async (): Promise<AccessLog[]> => {
    return [
      {
        id: '1',
        timestamp: new Date(Date.now() - 5 * 60000),
        user: 'john.doe@company.com',
        action: 'LOGIN',
        resource: '/app/transmission',
        ipAddress: '192.168.1.100',
        userAgent: 'Mozilla/5.0 Chrome/91.0',
        success: true
      },
      {
        id: '2',
        timestamp: new Date(Date.now() - 10 * 60000),
        user: 'jane.smith@company.com',
        action: 'ACCESS',
        resource: '/app/firs-dashboard',
        ipAddress: '192.168.1.105',
        userAgent: 'Mozilla/5.0 Firefox/89.0',
        success: true
      }
    ];
  };

  const fetchCertificates = async (): Promise<CertificateInfo[]> => {
    return [
      {
        id: 'cert-001',
        name: 'Production SSL Certificate',
        type: 'SSL/TLS',
        status: 'valid',
        expiryDate: new Date(Date.now() + 90 * 24 * 60 * 60 * 1000),
        issuer: 'FIRS CA',
        environment: 'production'
      }
    ];
  };

  const fetchComplianceStatus = async (): Promise<ComplianceStatus> => {
    return {
      overallScore: 96.5,
      categories: {
        authentication: 98,
        encryption: 95,
        accessControl: 97,
        auditLogging: 96,
        dataProtection: 95
      },
      lastAssessment: new Date(),
      nextAssessment: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000)
    };
  };

  const handleRefresh = () => {
    loadSecurityData();
  };

  const handleExportAuditLog = () => {
    // Implementation for exporting audit logs
    console.log('Exporting audit log...');
  };

  const getComplianceColor = (score: number) => {
    if (score >= 95) return '#52c41a';
    if (score >= 90) return '#faad14';
    return '#ff4d4f';
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'error';
      case 'warning': return 'warning';
      case 'info': return 'success';
      default: return 'default';
    }
  };

  // Table columns for security events
  const eventColumns = [
    {
      title: 'Timestamp',
      dataIndex: 'timestamp',
      key: 'timestamp',
      render: (timestamp: Date) => timestamp.toLocaleString()
    },
    {
      title: 'Type',
      dataIndex: 'type',
      key: 'type',
      render: (type: string) => (
        <Badge status="processing" text={type.charAt(0).toUpperCase() + type.slice(1)} />
      )
    },
    {
      title: 'Severity',
      dataIndex: 'severity',
      key: 'severity',
      render: (severity: string) => (
        <Badge status={getSeverityColor(severity) as any} text={severity.toUpperCase()} />
      )
    },
    {
      title: 'Message',
      dataIndex: 'message',
      key: 'message'
    },
    {
      title: 'Source',
      dataIndex: 'source',
      key: 'source'
    },
    {
      title: 'Status',
      dataIndex: 'resolved',
      key: 'resolved',
      render: (resolved: boolean) => (
        <Badge 
          status={resolved ? 'success' : 'warning'} 
          text={resolved ? 'Resolved' : 'Open'} 
        />
      )
    }
  ];

  // Table columns for access logs
  const accessColumns = [
    {
      title: 'Timestamp',
      dataIndex: 'timestamp',
      key: 'timestamp',
      render: (timestamp: Date) => timestamp.toLocaleString()
    },
    {
      title: 'User',
      dataIndex: 'user',
      key: 'user'
    },
    {
      title: 'Action',
      dataIndex: 'action',
      key: 'action',
      render: (action: string) => (
        <Badge status="processing" text={action} />
      )
    },
    {
      title: 'Resource',
      dataIndex: 'resource',
      key: 'resource'
    },
    {
      title: 'IP Address',
      dataIndex: 'ipAddress',
      key: 'ipAddress'
    },
    {
      title: 'Status',
      dataIndex: 'success',
      key: 'success',
      render: (success: boolean) => (
        <Badge 
          status={success ? 'success' : 'error'} 
          text={success ? 'Success' : 'Failed'} 
        />
      )
    }
  ];

  if (loading) {
    return (
      <div style={{ padding: 24, textAlign: 'center' }}>
        <ShieldCheckOutlined spin style={{ fontSize: 24, marginBottom: 16 }} />
        <p>Loading Security Audit...</p>
      </div>
    );
  }

  return (
    <div className={`security-audit-page ${className || ''}`}>
      {/* Page Header */}
      <div style={{ marginBottom: 24 }}>
        <Row justify="space-between" align="middle">
          <Col>
            <h1 style={{ margin: 0, display: 'flex', alignItems: 'center' }}>
              <ShieldCheckOutlined style={{ marginRight: 12, color: '#1890ff' }} />
              Security Audit
              {refreshing && <ReloadOutlined spin style={{ marginLeft: 12, color: '#52c41a' }} />}
            </h1>
            <p style={{ margin: '4px 0 0 0', color: '#666' }}>
              Security monitoring, compliance tracking, and audit management
            </p>
          </Col>
          <Col>
            <Space>
              <Button icon={<DownloadOutlined />} onClick={handleExportAuditLog}>
                Export Audit Log
              </Button>
              <Button icon={<ReloadOutlined />} onClick={handleRefresh} loading={refreshing}>
                Refresh
              </Button>
            </Space>
          </Col>
        </Row>
      </div>

      {/* Security Metrics Overview */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Compliance Score"
              value={metrics?.complianceScore}
              suffix="%"
              precision={1}
              prefix={<AuditOutlined />}
              valueStyle={{ color: getComplianceColor(metrics?.complianceScore || 0) }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Security Events"
              value={metrics?.totalEvents}
              prefix={<WarningOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Critical Events"
              value={metrics?.criticalEvents}
              prefix={<ExclamationTriangleOutlined />}
              valueStyle={{ color: metrics?.criticalEvents && metrics.criticalEvents > 0 ? '#ff4d4f' : '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Active Users"
              value={metrics?.activeUsers}
              prefix={<UserOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
      </Row>

      {/* Security Alerts */}
      {metrics && (
        <div style={{ marginBottom: 24 }}>
          {metrics.criticalEvents > 0 && (
            <Alert
              type="error"
              message={`${metrics.criticalEvents} critical security events require immediate attention`}
              description="Review critical security events and take necessary action"
              showIcon
              closable
              style={{ marginBottom: 8 }}
            />
          )}
          {metrics.complianceScore < 90 && (
            <Alert
              type="warning"
              message="Compliance score below recommended threshold"
              description="Review compliance status and address identified issues"
              showIcon
              closable
              style={{ marginBottom: 8 }}
            />
          )}
        </div>
      )}

      {/* Main Content Tabs */}
      <Card>
        <Tabs 
          activeKey={activeTab} 
          onChange={setActiveTab}
          tabBarExtraContent={{
            right: (
              <Space>
                <Badge 
                  status={metrics?.criticalEvents === 0 ? 'success' : 'error'}
                  text={`${metrics?.criticalEvents || 0} critical`}
                />
                <Badge 
                  status="processing"
                  text={`${metrics?.complianceScore || 0}% compliance`}
                />
              </Space>
            )
          }}
        >
          <TabPane 
            tab={
              <span>
                <AuditOutlined />
                Security Center
              </span>
            } 
            key="overview"
          >
            <SecurityAuditCenter />
          </TabPane>

          <TabPane 
            tab={
              <span>
                <WarningOutlined />
                Security Events
              </span>
            } 
            key="events"
          >
            <Table
              columns={eventColumns}
              dataSource={securityEvents}
              rowKey="id"
              pagination={{ pageSize: 10 }}
              size="middle"
            />
          </TabPane>

          <TabPane 
            tab={
              <span>
                <UserOutlined />
                Access Logs
              </span>
            } 
            key="access"
          >
            <Table
              columns={accessColumns}
              dataSource={accessLogs}
              rowKey="id"
              pagination={{ pageSize: 10 }}
              size="middle"
            />
          </TabPane>

          <TabPane 
            tab={
              <span>
                <SafetyCertificateOutlined />
                Certificates
              </span>
            } 
            key="certificates"
          >
            <Row gutter={[16, 16]}>
              {certificates.map((cert) => (
                <Col xs={24} lg={12} key={cert.id}>
                  <Card 
                    title={cert.name}
                    extra={
                      <Badge 
                        status={cert.status === 'valid' ? 'success' : 'warning'}
                        text={cert.status.toUpperCase()}
                      />
                    }
                  >
                    <Timeline>
                      <Timeline.Item icon={<SafetyCertificateOutlined />}>
                        <strong>Type:</strong> {cert.type}
                      </Timeline.Item>
                      <Timeline.Item icon={<LockOutlined />}>
                        <strong>Issuer:</strong> {cert.issuer}
                      </Timeline.Item>
                      <Timeline.Item 
                        icon={<ExclamationTriangleOutlined />}
                        color={new Date(cert.expiryDate).getTime() - Date.now() < 30 * 24 * 60 * 60 * 1000 ? 'red' : 'green'}
                      >
                        <strong>Expires:</strong> {cert.expiryDate.toLocaleDateString()}
                      </Timeline.Item>
                    </Timeline>
                  </Card>
                </Col>
              ))}
            </Row>
          </TabPane>

          <TabPane 
            tab={
              <span>
                <AuditOutlined />
                Compliance
              </span>
            } 
            key="compliance"
          >
            {complianceStatus && (
              <div>
                <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
                  <Col span={24}>
                    <Card title="Compliance Overview">
                      <Statistic
                        title="Overall Compliance Score"
                        value={complianceStatus.overallScore}
                        suffix="%"
                        precision={1}
                        valueStyle={{ fontSize: 32, color: getComplianceColor(complianceStatus.overallScore) }}
                      />
                      <p style={{ marginTop: 16, marginBottom: 0 }}>
                        Last Assessment: {complianceStatus.lastAssessment.toLocaleDateString()}
                      </p>
                      <p style={{ marginBottom: 0 }}>
                        Next Assessment: {complianceStatus.nextAssessment.toLocaleDateString()}
                      </p>
                    </Card>
                  </Col>
                </Row>
                
                <Row gutter={[16, 16]}>
                  {Object.entries(complianceStatus.categories).map(([category, score]) => (
                    <Col xs={24} sm={12} md={8} key={category}>
                      <Card>
                        <Statistic
                          title={category.charAt(0).toUpperCase() + category.slice(1).replace(/([A-Z])/g, ' $1')}
                          value={score}
                          suffix="%"
                          valueStyle={{ color: getComplianceColor(score) }}
                        />
                      </Card>
                    </Col>
                  ))}
                </Row>
              </div>
            )}
          </TabPane>
        </Tabs>
      </Card>
    </div>
  );
};

export default SecurityAuditPage;