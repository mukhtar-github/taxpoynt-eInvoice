/**
 * TaxPoynt Platform Compliance Dashboard (Admin-Only)
 * ===================================================
 * 
 * Platform compliance monitoring dashboard for TaxPoynt administrators.
 * Tracks TaxPoynt's obligations as an Access Point Provider (APP) according
 * to FIRS-mandated standards for service providers.
 * 
 * Features:
 * - FIRS-mandated standards compliance tracking (7 standards)
 * - Platform security and certification monitoring  
 * - APP service provider obligation tracking
 * - Real-time platform compliance score calculation
 * - Infrastructure compliance violations tracking
 * - Certification renewal deadline management
 * - Automated platform compliance reporting
 * - Admin-only visibility and controls
 * 
 * IMPORTANT: This dashboard monitors TaxPoynt's platform compliance,
 * NOT customer business compliance.
 * 
 * @author TaxPoynt Development Team
 * @version 2.0.0
 * @access Admin-Only
 */

import React, { useState, useEffect } from 'react';
import { 
  Card, 
  Row, 
  Col, 
  Progress, 
  Alert, 
  Badge, 
  Table, 
  Timeline, 
  Statistic, 
  Tabs,
  Button,
  Space,
  Tooltip,
  Calendar,
  List,
  Divider
} from 'antd';
import {
  ShieldCheckOutlined,
  ExclamationTriangleOutlined,
  CalendarOutlined,
  FileTextOutlined,
  TrophyOutlined,
  WarningOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  EyeOutlined,
  DownloadOutlined,
  ReloadOutlined,
  BankOutlined,
  SafetyCertificateOutlined
} from '@ant-design/icons';

import type { 
  UnifiedComplianceStatus,
  ComplianceCategory,
  ComplianceViolation,
  ComplianceDeadline,
  ComplianceRequirement,
  DashboardComponentProps
} from '../../types';

interface UnifiedComplianceOverviewProps extends DashboardComponentProps {
  showDetails?: boolean;
  regulatoryBodies?: string[];
  onViolationClick?: (violation: ComplianceViolation) => void;
  onRequirementClick?: (requirement: ComplianceRequirement) => void;
  onDeadlineClick?: (deadline: ComplianceDeadline) => void;
}

interface ComplianceAlert {
  id: string;
  type: 'violation' | 'deadline' | 'requirement' | 'audit';
  severity: 'critical' | 'high' | 'medium' | 'low';
  title: string;
  message: string;
  regulatory_body: string;
  due_date?: Date;
  timestamp: Date;
  actionable: boolean;
}

interface RegulatoryBodyStatus {
  body: string;
  name: string;
  compliance_score: number;
  active_requirements: number;
  violations: number;
  upcoming_deadlines: number;
  last_assessment: Date;
  status: 'compliant' | 'non_compliant' | 'pending';
}

const { TabPane } = Tabs;

// FIRS-Mandated Compliance Standards for Service Providers (APP)
const FIRS_MANDATED_STANDARDS = [
  { code: 'UBL', name: 'Universal Business Language', description: 'Document format standards', icon: <FileTextOutlined />, color: '#1890ff' },
  { code: 'WCO_HS', name: 'WCO Harmonized System Code', description: 'World Customs Organization classification', icon: <BankOutlined />, color: '#52c41a' },
  { code: 'NITDA_GDPR', name: 'NITDA GDPR & NDPA', description: 'Nigerian data protection requirements', icon: <SafetyCertificateOutlined />, color: '#722ed1' },
  { code: 'ISO_20022', name: 'ISO 20022', description: 'Financial messaging standards', icon: <ShieldCheckOutlined />, color: '#fa8c16' },
  { code: 'ISO_27001', name: 'ISO 27001', description: 'Information security management', icon: <TrophyOutlined />, color: '#13c2c2' },
  { code: 'LEI', name: 'Legal Entity Identifier', description: 'Global entity identification', icon: <FileTextOutlined />, color: '#faad14' },
  { code: 'PEPPOL', name: 'PEPPOL', description: 'Pan-European Public Procurement Online', icon: <BankOutlined />, color: '#eb2f96' }
];

export const PlatformComplianceDashboard: React.FC<UnifiedComplianceOverviewProps> = ({
  showDetails = true,
  regulatoryBodies = ['UBL', 'WCO_HS', 'NITDA_GDPR', 'ISO_20022', 'ISO_27001', 'LEI', 'PEPPOL'],
  onViolationClick,
  onRequirementClick,
  onDeadlineClick,
  refreshInterval = 300000, // 5 minutes
  autoRefresh = true,
  className,
  ...props
}) => {
  // State management
  const [complianceStatus, setComplianceStatus] = useState<UnifiedComplianceStatus | null>(null);
  const [regulatoryStatuses, setRegulatoryStatuses] = useState<RegulatoryBodyStatus[]>([]);
  const [complianceAlerts, setComplianceAlerts] = useState<ComplianceAlert[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    loadComplianceData();

    if (autoRefresh) {
      const interval = setInterval(loadComplianceData, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [autoRefresh, refreshInterval]);

  const loadComplianceData = async () => {
    try {
      setRefreshing(true);

      const [statusData, regulatoryData, alertsData] = await Promise.all([
        fetchUnifiedComplianceStatus(),
        fetchRegulatoryBodyStatuses(),
        fetchComplianceAlerts()
      ]);

      setComplianceStatus(statusData);
      setRegulatoryStatuses(regulatoryData);
      setComplianceAlerts(alertsData);
      setLoading(false);
    } catch (error) {
      console.error('Failed to load compliance data:', error);
    } finally {
      setRefreshing(false);
    }
  };

  // Mock API functions
  const fetchUnifiedComplianceStatus = async (): Promise<UnifiedComplianceStatus> => {
    return {
      overall_score: 91.4,
      compliance_categories: [
        {
          category_id: 'ubl_standards',
          name: 'UBL Standards',
          description: 'Universal Business Language document format compliance',
          score: 94.8,
          weight: 20,
          status: 'compliant',
          last_assessed: new Date(),
          requirements: []
        },
        {
          category_id: 'wco_hs_codes',
          name: 'WCO HS Codes',
          description: 'World Customs Organization Harmonized System classification',
          score: 89.2,
          weight: 15,
          status: 'compliant',
          last_assessed: new Date(),
          requirements: []
        },
        {
          category_id: 'nitda_gdpr_ndpa',
          name: 'NITDA GDPR & NDPA',
          description: 'Nigerian data protection and privacy requirements',
          score: 92.6,
          weight: 15,
          status: 'compliant',
          last_assessed: new Date(),
          requirements: []
        },
        {
          category_id: 'iso_20022',
          name: 'ISO 20022',
          description: 'Financial messaging standards implementation',
          score: 87.5,
          weight: 15,
          status: 'non_compliant',
          last_assessed: new Date(),
          requirements: []
        },
        {
          category_id: 'iso_27001',
          name: 'ISO 27001',
          description: 'Information security management system',
          score: 95.3,
          weight: 20,
          status: 'compliant',
          last_assessed: new Date(),
          requirements: []
        },
        {
          category_id: 'lei',
          name: 'Legal Entity Identifier',
          description: 'Global entity identification compliance',
          score: 98.7,
          weight: 5,
          status: 'compliant',
          last_assessed: new Date(),
          requirements: []
        },
        {
          category_id: 'peppol',
          name: 'PEPPOL',
          description: 'Pan-European Public Procurement Online standards',
          score: 85.1,
          weight: 10,
          status: 'pending',
          last_assessed: new Date(),
          requirements: []
        }
      ],
      recent_violations: [
        {
          violation_id: 'viol-001',
          requirement_id: 'req-iso20022-001',
          severity: 'major',
          description: 'ISO 20022 financial message format validation failed for transaction batch',
          detected_at: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000),
          status: 'investigating',
          resolution_steps: ['Review message structure', 'Update validation rules', 'Reprocess batch'],
          assigned_to: 'compliance_team'
        }
      ],
      upcoming_deadlines: [
        {
          deadline_id: 'deadline-001',
          requirement_id: 'req-ubl-001',
          title: 'UBL Document Format Compliance Review',
          due_date: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000),
          priority: 'high',
          progress_percentage: 75,
          assigned_roles: ['app_user'],
          estimated_hours: 4
        },
        {
          deadline_id: 'deadline-002',
          requirement_id: 'req-nitda-gdpr-001',
          title: 'NITDA GDPR Annual Data Protection Assessment',
          due_date: new Date(Date.now() + 14 * 24 * 60 * 60 * 1000),
          priority: 'medium',
          progress_percentage: 45,
          assigned_roles: ['hybrid_user'],
          estimated_hours: 12
        },
        {
          deadline_id: 'deadline-003',
          requirement_id: 'req-iso27001-001',
          title: 'ISO 27001 Security Management Review',
          due_date: new Date(Date.now() + 21 * 24 * 60 * 60 * 1000),
          priority: 'medium',
          progress_percentage: 60,
          assigned_roles: ['admin'],
          estimated_hours: 8
        }
      ],
      compliance_trends: [
        {
          period: '2024-01',
          score: 91.5,
          improvement: 2.3,
          key_factors: ['Enhanced UBL document generation', 'Improved ISO 20022 compliance']
        },
        {
          period: '2024-02',
          score: 93.8,
          improvement: 2.3,
          key_factors: ['NITDA GDPR framework implementation', 'ISO 27001 certification progress']
        }
      ],
      recommendations: [
        {
          recommendation_id: 'rec-001',
          title: 'Enhance ISO 20022 Message Validation',
          description: 'Implement comprehensive validation for ISO 20022 financial message formats',
          priority: 'high',
          estimated_impact: 5.7,
          estimated_effort: 16,
          recommended_actions: [
            'Update message schema validation',
            'Implement real-time format checking',
            'Create automated error correction'
          ],
          deadline: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000)
        },
        {
          recommendation_id: 'rec-002',
          title: 'Complete PEPPOL Integration',
          description: 'Finalize PEPPOL compliance for EU procurement integration',
          priority: 'medium',
          estimated_impact: 4.2,
          estimated_effort: 24,
          recommended_actions: [
            'Complete PEPPOL network certification',
            'Implement PEPPOL BIS 3.0 standards',
            'Set up cross-border e-invoicing'
          ],
          deadline: new Date(Date.now() + 45 * 24 * 60 * 60 * 1000)
        }
      ]
    };
  };

  const fetchRegulatoryBodyStatuses = async (): Promise<RegulatoryBodyStatus[]> => {
    return [
      {
        body: 'UBL',
        name: 'Universal Business Language',
        compliance_score: 94.8,
        active_requirements: 8,
        violations: 0,
        upcoming_deadlines: 1,
        last_assessment: new Date(),
        status: 'compliant'
      },
      {
        body: 'WCO_HS',
        name: 'WCO Harmonized System',
        compliance_score: 89.2,
        active_requirements: 6,
        violations: 0,
        upcoming_deadlines: 2,
        last_assessment: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000),
        status: 'compliant'
      },
      {
        body: 'NITDA_GDPR',
        name: 'NITDA GDPR & NDPA',
        compliance_score: 92.6,
        active_requirements: 5,
        violations: 0,
        upcoming_deadlines: 1,
        last_assessment: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000),
        status: 'compliant'
      },
      {
        body: 'ISO_20022',
        name: 'ISO 20022',
        compliance_score: 87.5,
        active_requirements: 7,
        violations: 1,
        upcoming_deadlines: 3,
        last_assessment: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000),
        status: 'non_compliant'
      },
      {
        body: 'ISO_27001',
        name: 'ISO 27001',
        compliance_score: 95.3,
        active_requirements: 9,
        violations: 0,
        upcoming_deadlines: 2,
        last_assessment: new Date(),
        status: 'compliant'
      },
      {
        body: 'LEI',
        name: 'Legal Entity Identifier',
        compliance_score: 98.7,
        active_requirements: 3,
        violations: 0,
        upcoming_deadlines: 1,
        last_assessment: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000),
        status: 'compliant'
      },
      {
        body: 'PEPPOL',
        name: 'PEPPOL',
        compliance_score: 85.1,
        active_requirements: 4,
        violations: 0,
        upcoming_deadlines: 2,
        last_assessment: new Date(Date.now() - 4 * 24 * 60 * 60 * 1000),
        status: 'pending'
      }
    ];
  };

  const fetchComplianceAlerts = async (): Promise<ComplianceAlert[]> => {
    return [
      {
        id: 'alert-001',
        type: 'deadline',
        severity: 'high',
        title: 'APP Certification Renewal Due',
        message: 'FIRS APP certification renewal required within 30 days',
        regulatory_body: 'UBL',
        due_date: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000),
        timestamp: new Date(),
        actionable: true
      },
      {
        id: 'alert-002',
        type: 'violation',
        severity: 'medium',
        title: 'Platform Security Alert',
        message: 'ISO 27001 compliance check detected configuration drift',
        regulatory_body: 'ISO_27001',
        timestamp: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000),
        actionable: true
      }
    ];
  };

  const getComplianceColor = (score: number): string => {
    if (score >= 95) return '#52c41a';
    if (score >= 90) return '#faad14';
    if (score >= 80) return '#fa8c16';
    return '#ff4d4f';
  };

  const getStatusColor = (status: string): string => {
    switch (status) {
      case 'compliant': return '#52c41a';
      case 'non_compliant': return '#ff4d4f';
      case 'pending': return '#faad14';
      default: return '#666';
    }
  };

  const getSeverityColor = (severity: string): string => {
    switch (severity) {
      case 'critical': return '#ff4d4f';
      case 'high': return '#fa8c16';
      case 'medium': return '#faad14';
      case 'low': return '#52c41a';
      default: return '#666';
    }
  };

  const getFIRSStandardInfo = (code: string) => {
    return FIRS_MANDATED_STANDARDS.find(standard => standard.code === code) || 
           { code, name: code, description: 'Standard compliance', icon: <FileTextOutlined />, color: '#666' };
  };

  // Table columns for violations
  const violationColumns = [
    {
      title: 'Violation',
      key: 'violation',
      render: (record: ComplianceViolation) => (
        <div>
          <strong>{record.description}</strong>
          <br />
          <small style={{ color: '#666' }}>
            ID: {record.violation_id} | Detected: {record.detected_at.toLocaleDateString()}
          </small>
        </div>
      )
    },
    {
      title: 'Severity',
      dataIndex: 'severity',
      key: 'severity',
      render: (severity: string) => (
        <Badge 
          color={getSeverityColor(severity)}
          text={severity.toUpperCase()}
        />
      )
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Badge 
          status={status === 'resolved' ? 'success' : 'processing'}
          text={status.replace('_', ' ').toUpperCase()}
        />
      )
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (record: ComplianceViolation) => (
        <Space>
          <Button 
            size="small" 
            icon={<EyeOutlined />}
            onClick={() => onViolationClick && onViolationClick(record)}
          >
            View
          </Button>
        </Space>
      )
    }
  ];

  // Table columns for deadlines
  const deadlineColumns = [
    {
      title: 'Requirement',
      dataIndex: 'title',
      key: 'title',
      render: (title: string, record: ComplianceDeadline) => (
        <div>
          <strong>{title}</strong>
          <br />
          <small style={{ color: '#666' }}>
            Due: {record.due_date.toLocaleDateString()}
          </small>
        </div>
      )
    },
    {
      title: 'Priority',
      dataIndex: 'priority',
      key: 'priority',
      render: (priority: string) => (
        <Badge 
          color={priority === 'critical' ? 'red' : priority === 'high' ? 'orange' : 'blue'}
          text={priority.toUpperCase()}
        />
      )
    },
    {
      title: 'Progress',
      dataIndex: 'progress_percentage',
      key: 'progress',
      render: (progress: number) => (
        <Progress 
          percent={progress} 
          size="small"
          status={progress < 50 ? 'exception' : progress < 80 ? 'active' : 'success'}
        />
      )
    },
    {
      title: 'Days Left',
      key: 'days_left',
      render: (record: ComplianceDeadline) => {
        const daysLeft = Math.ceil((record.due_date.getTime() - Date.now()) / (1000 * 60 * 60 * 24));
        return (
          <span style={{ color: daysLeft <= 7 ? '#ff4d4f' : daysLeft <= 14 ? '#fa8c16' : '#52c41a' }}>
            {daysLeft} days
          </span>
        );
      }
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (record: ComplianceDeadline) => (
        <Space>
          <Button 
            size="small" 
            icon={<EyeOutlined />}
            onClick={() => onDeadlineClick && onDeadlineClick(record)}
          >
            View
          </Button>
        </Space>
      )
    }
  ];

  if (loading) {
    return (
      <Card className={className} {...props}>
        <div style={{ textAlign: 'center', padding: '40px 0' }}>
          <ReloadOutlined spin style={{ fontSize: 24, marginBottom: 16 }} />
          <p>Loading compliance data...</p>
        </div>
      </Card>
    );
  }

  return (
    <div className={`unified-compliance-overview ${className || ''}`} {...props}>
      {/* Header */}
      <div style={{ marginBottom: 16 }}>
        <Row justify="space-between" align="middle">
          <Col>
            <h3 style={{ margin: 0, display: 'flex', alignItems: 'center' }}>
              <ShieldCheckOutlined style={{ marginRight: 8, color: '#1890ff' }} />
              TaxPoynt Platform Compliance (Admin Dashboard)
              {refreshing && <ReloadOutlined spin style={{ marginLeft: 8, color: '#52c41a' }} />}
            </h3>
            <p style={{ margin: '4px 0 0 0', color: '#666' }}>
              FIRS-mandated APP service provider compliance monitoring
            </p>
          </Col>
          <Col>
            <Space>
              <Button icon={<ReloadOutlined />} onClick={loadComplianceData} loading={refreshing}>
                Refresh
              </Button>
              <Button icon={<DownloadOutlined />} type="default">
                Export Report
              </Button>
            </Space>
          </Col>
        </Row>
      </div>

      {/* Compliance Alerts */}
      {complianceAlerts.length > 0 && (
        <div style={{ marginBottom: 16 }}>
          {complianceAlerts.slice(0, 3).map(alert => (
            <Alert
              key={alert.id}
              type={alert.severity === 'critical' || alert.severity === 'high' ? 'error' : 'warning'}
              message={`${getFIRSStandardInfo(alert.regulatory_body).name}: ${alert.title}`}
              description={alert.message}
              showIcon
              closable
              style={{ marginBottom: 8 }}
            />
          ))}
        </div>
      )}

      {/* Overall Compliance Score */}
      {complianceStatus && (
        <Card style={{ marginBottom: 16 }}>
          <Row gutter={[24, 16]} align="middle">
            <Col xs={24} sm={8}>
              <div style={{ textAlign: 'center' }}>
                <Progress
                  type="circle"
                  percent={complianceStatus.overall_score}
                  format={() => `${complianceStatus.overall_score.toFixed(1)}%`}
                  strokeColor={getComplianceColor(complianceStatus.overall_score)}
                  size={120}
                />
                <h4 style={{ marginTop: 16, marginBottom: 0 }}>Platform Compliance Score</h4>
              </div>
            </Col>
            
            <Col xs={24} sm={16}>
              <Row gutter={[16, 16]}>
                <Col xs={12} sm={6}>
                  <Statistic
                    title="Platform Requirements"
                    value={complianceStatus.compliance_categories.reduce((sum, cat) => sum + cat.requirements.length, 0)}
                    prefix={<FileTextOutlined />}
                  />
                </Col>
                <Col xs={12} sm={6}>
                  <Statistic
                    title="Platform Issues"
                    value={complianceStatus.recent_violations.length}
                    prefix={<ExclamationTriangleOutlined />}
                    valueStyle={{ color: complianceStatus.recent_violations.length > 0 ? '#ff4d4f' : '#52c41a' }}
                  />
                </Col>
                <Col xs={12} sm={6}>
                  <Statistic
                    title="Certification Renewals"
                    value={complianceStatus.upcoming_deadlines.length}
                    prefix={<ClockCircleOutlined />}
                    valueStyle={{ color: complianceStatus.upcoming_deadlines.length > 5 ? '#fa8c16' : '#1890ff' }}
                  />
                </Col>
                <Col xs={12} sm={6}>
                  <Statistic
                    title="Platform Improvements"
                    value={complianceStatus.recommendations.length}
                    prefix={<TrophyOutlined />}
                    valueStyle={{ color: '#722ed1' }}
                  />
                </Col>
              </Row>
            </Col>
          </Row>
        </Card>
      )}

      {/* Regulatory Body Status */}
      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        {regulatoryStatuses.map(status => {
          const standardInfo = getFIRSStandardInfo(status.body);
          return (
            <Col xs={24} sm={12} lg={8} key={status.body}>
              <Card 
                size="small"
                title={
                  <div style={{ display: 'flex', alignItems: 'center' }}>
                    <span style={{ color: standardInfo.color, marginRight: 8 }}>
                      {standardInfo.icon}
                    </span>
                    {status.body}
                  </div>
                }
                extra={
                  <Badge 
                    color={getStatusColor(status.status)}
                    text={status.status.replace('_', ' ').toUpperCase()}
                  />
                }
              >
                <div style={{ marginBottom: 12 }}>
                  <Progress
                    percent={status.compliance_score}
                    strokeColor={getComplianceColor(status.compliance_score)}
                    format={() => `${status.compliance_score.toFixed(1)}%`}
                  />
                </div>
                
                <Row gutter={8}>
                  <Col span={12}>
                    <div style={{ fontSize: 11, color: '#666' }}>Requirements</div>
                    <strong>{status.active_requirements}</strong>
                  </Col>
                  <Col span={12}>
                    <div style={{ fontSize: 11, color: '#666' }}>Violations</div>
                    <strong style={{ color: status.violations > 0 ? '#ff4d4f' : '#52c41a' }}>
                      {status.violations}
                    </strong>
                  </Col>
                </Row>
              </Card>
            </Col>
          );
        })}
      </Row>

      {/* Main Content Tabs */}
      {showDetails && complianceStatus && (
        <Card>
          <Tabs activeKey={activeTab} onChange={setActiveTab}>
            <TabPane
              tab={
                <span>
                  <TrophyOutlined />
                  Categories ({complianceStatus.compliance_categories.length})
                </span>
              }
              key="categories"
            >
              <Row gutter={[16, 16]}>
                {complianceStatus.compliance_categories.map(category => (
                  <Col xs={24} lg={12} key={category.category_id}>
                    <Card
                      size="small"
                      title={category.name}
                      extra={
                        <Badge 
                          color={getComplianceColor(category.score)}
                          text={`${category.score.toFixed(1)}%`}
                        />
                      }
                    >
                      <p style={{ color: '#666', marginBottom: 12, fontSize: 12 }}>
                        {category.description}
                      </p>
                      
                      <Progress
                        percent={category.score}
                        strokeColor={getComplianceColor(category.score)}
                        style={{ marginBottom: 8 }}
                      />
                      
                      <div style={{ fontSize: 11, color: '#999' }}>
                        Weight: {category.weight}% | Last assessed: {category.last_assessed.toLocaleDateString()}
                      </div>
                    </Card>
                  </Col>
                ))}
              </Row>
            </TabPane>

            <TabPane
              tab={
                <span>
                  <ExclamationTriangleOutlined />
                  Violations ({complianceStatus.recent_violations.length})
                </span>
              }
              key="violations"
            >
              <Table
                columns={violationColumns}
                dataSource={complianceStatus.recent_violations}
                rowKey="violation_id"
                pagination={{ pageSize: 10 }}
                size="small"
              />
            </TabPane>

            <TabPane
              tab={
                <span>
                  <CalendarOutlined />
                  Deadlines ({complianceStatus.upcoming_deadlines.length})
                </span>
              }
              key="deadlines"
            >
              <Table
                columns={deadlineColumns}
                dataSource={complianceStatus.upcoming_deadlines}
                rowKey="deadline_id"
                pagination={{ pageSize: 10 }}
                size="small"
              />
            </TabPane>

            <TabPane
              tab={
                <span>
                  <TrophyOutlined />
                  Recommendations ({complianceStatus.recommendations.length})
                </span>
              }
              key="recommendations"
            >
              <List
                dataSource={complianceStatus.recommendations}
                renderItem={recommendation => (
                  <List.Item
                    actions={[
                      <Button size="small" type="primary">Implement</Button>,
                      <Button size="small" icon={<EyeOutlined />}>Details</Button>
                    ]}
                  >
                    <List.Item.Meta
                      title={
                        <div>
                          {recommendation.title}
                          <Badge 
                            color={getSeverityColor(recommendation.priority)}
                            text={recommendation.priority.toUpperCase()}
                            style={{ marginLeft: 8 }}
                          />
                        </div>
                      }
                      description={
                        <div>
                          <p style={{ marginBottom: 4 }}>{recommendation.description}</p>
                          <div style={{ fontSize: 11, color: '#666' }}>
                            Impact: +{recommendation.estimated_impact}% | 
                            Effort: {recommendation.estimated_effort}h |
                            Due: {recommendation.deadline?.toLocaleDateString()}
                          </div>
                        </div>
                      }
                    />
                  </List.Item>
                )}
              />
            </TabPane>
          </Tabs>
        </Card>
      )}
    </div>
  );
};

export default PlatformComplianceDashboard;