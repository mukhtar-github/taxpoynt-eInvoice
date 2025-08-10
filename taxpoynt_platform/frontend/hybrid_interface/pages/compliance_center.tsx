/**
 * Compliance Center Page (Hybrid Interface)
 * =========================================
 * 
 * Comprehensive compliance management hub for TaxPoynt platform administrators.
 * Focuses on TaxPoynt's obligations as an APP service provider according to
 * FIRS-mandated standards.
 * 
 * Features:
 * - Platform compliance dashboard (admin-only)
 * - FIRS-mandated standards monitoring
 * - Certification management and renewals
 * - Compliance workflow automation
 * - Regulatory reporting and audit trails
 * - Risk assessment and mitigation
 * 
 * IMPORTANT: This is for TaxPoynt's platform compliance, NOT customer compliance.
 * 
 * @author TaxPoynt Development Team
 * @version 1.0.0
 * @access Admin-Only
 */

import React, { useState, useEffect } from 'react';
import {
  Layout,
  Card,
  Row,
  Col,
  Tabs,
  Alert,
  Button,
  Space,
  Timeline,
  Progress,
  Badge,
  Table,
  Modal,
  Form,
  Input,
  Select,
  DatePicker
} from 'antd';
import {
  ShieldCheckOutlined,
  ExclamationTriangleOutlined,
  CalendarOutlined,
  FileTextOutlined,
  SettingOutlined,
  AuditOutlined,
  SafetyCertificateOutlined,
  ApiOutlined,
  AlertOutlined
} from '@ant-design/icons';

// Import compliance components
import { PlatformComplianceDashboard } from '../components/compliance_overview/PlatformComplianceDashboard';

const { Content } = Layout;
const { TabPane } = Tabs;
const { Option } = Select;

interface ComplianceCenterProps {
  userRole: 'si' | 'app' | 'hybrid' | 'admin';
  organizationId: string;
}

interface ComplianceStandard {
  code: string;
  name: string;
  status: 'compliant' | 'non_compliant' | 'pending' | 'expired';
  lastAudit: Date;
  nextDeadline: Date;
  score: number;
  criticalIssues: number;
}

export const ComplianceCenter: React.FC<ComplianceCenterProps> = ({
  userRole,
  organizationId
}) => {
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [modalVisible, setModalVisible] = useState(false);
  const [selectedStandard, setSelectedStandard] = useState<string | null>(null);

  // Check admin access
  const hasAdminAccess = userRole === 'admin' || userRole === 'hybrid';

  // FIRS-mandated compliance standards
  const complianceStandards: ComplianceStandard[] = [
    {
      code: 'UBL',
      name: 'Universal Business Language',
      status: 'compliant',
      lastAudit: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000),
      nextDeadline: new Date(Date.now() + 60 * 24 * 60 * 60 * 1000),
      score: 94.8,
      criticalIssues: 0
    },
    {
      code: 'WCO_HS',
      name: 'WCO Harmonized System Code',
      status: 'compliant',
      lastAudit: new Date(Date.now() - 45 * 24 * 60 * 60 * 1000),
      nextDeadline: new Date(Date.now() + 45 * 24 * 60 * 60 * 1000),
      score: 89.2,
      criticalIssues: 0
    },
    {
      code: 'NITDA_GDPR',
      name: 'NITDA GDPR & NDPA',
      status: 'compliant',
      lastAudit: new Date(Date.now() - 15 * 24 * 60 * 60 * 1000),
      nextDeadline: new Date(Date.now() + 75 * 24 * 60 * 60 * 1000),
      score: 92.6,
      criticalIssues: 0
    },
    {
      code: 'ISO_20022',
      name: 'ISO 20022',
      status: 'non_compliant',
      lastAudit: new Date(Date.now() - 60 * 24 * 60 * 60 * 1000),
      nextDeadline: new Date(Date.now() + 15 * 24 * 60 * 60 * 1000),
      score: 87.5,
      criticalIssues: 2
    },
    {
      code: 'ISO_27001',
      name: 'ISO 27001',
      status: 'compliant',
      lastAudit: new Date(Date.now() - 90 * 24 * 60 * 60 * 1000),
      nextDeadline: new Date(Date.now() + 90 * 24 * 60 * 60 * 1000),
      score: 95.3,
      criticalIssues: 0
    },
    {
      code: 'LEI',
      name: 'Legal Entity Identifier',
      status: 'compliant',
      lastAudit: new Date(Date.now() - 180 * 24 * 60 * 60 * 1000),
      nextDeadline: new Date(Date.now() + 120 * 24 * 60 * 60 * 1000),
      score: 98.7,
      criticalIssues: 0
    },
    {
      code: 'PEPPOL',
      name: 'PEPPOL',
      status: 'pending',
      lastAudit: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000),
      nextDeadline: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000),
      score: 85.1,
      criticalIssues: 1
    }
  ];

  // Recent compliance activities
  const recentActivities = [
    {
      timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000),
      type: 'audit',
      title: 'ISO 27001 Security Control Assessment',
      status: 'completed',
      details: 'All security controls reviewed and validated'
    },
    {
      timestamp: new Date(Date.now() - 6 * 60 * 60 * 1000),
      type: 'certification',
      title: 'APP Certificate Renewal Initiated',
      status: 'in_progress',
      details: 'FIRS APP certification renewal process started'
    },
    {
      timestamp: new Date(Date.now() - 24 * 60 * 60 * 1000),
      type: 'issue',
      title: 'ISO 20022 Format Validation Issue',
      status: 'resolved',
      details: 'Message format validation rules updated'
    }
  ];

  // Table columns for compliance standards
  const standardsColumns = [
    {
      title: 'Standard',
      key: 'standard',
      render: (record: ComplianceStandard) => (
        <div>
          <strong>{record.name}</strong>
          <br />
          <span style={{ color: '#666', fontSize: '12px' }}>{record.code}</span>
        </div>
      )
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const statusConfig = {
          compliant: { color: 'success', text: 'Compliant' },
          non_compliant: { color: 'error', text: 'Non-Compliant' },
          pending: { color: 'warning', text: 'Pending' },
          expired: { color: 'error', text: 'Expired' }
        };
        const config = statusConfig[status as keyof typeof statusConfig];
        return <Badge status={config.color as any} text={config.text} />;
      }
    },
    {
      title: 'Compliance Score',
      dataIndex: 'score',
      key: 'score',
      render: (score: number) => (
        <Progress 
          percent={score} 
          size="small"
          status={score >= 90 ? 'success' : score >= 80 ? 'active' : 'exception'}
        />
      )
    },
    {
      title: 'Critical Issues',
      dataIndex: 'criticalIssues',
      key: 'issues',
      render: (issues: number) => (
        <span style={{ color: issues > 0 ? '#ff4d4f' : '#52c41a' }}>
          {issues > 0 ? `${issues} Issues` : 'No Issues'}
        </span>
      )
    },
    {
      title: 'Next Deadline',
      dataIndex: 'nextDeadline',
      key: 'deadline',
      render: (date: Date) => {
        const daysLeft = Math.ceil((date.getTime() - Date.now()) / (1000 * 60 * 60 * 24));
        return (
          <span style={{ color: daysLeft <= 30 ? '#ff4d4f' : daysLeft <= 60 ? '#fa8c16' : '#52c41a' }}>
            {date.toLocaleDateString()}
            <br />
            <small>({daysLeft} days)</small>
          </span>
        );
      }
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (record: ComplianceStandard) => (
        <Space>
          <Button 
            size="small" 
            onClick={() => {
              setSelectedStandard(record.code);
              setModalVisible(true);
            }}
          >
            Manage
          </Button>
        </Space>
      )
    }
  ];

  // Access control check
  if (!hasAdminAccess) {
    return (
      <div style={{ padding: '24px' }}>
        <Alert
          type="warning"
          message="Access Restricted"
          description="The Compliance Center is only available to TaxPoynt administrators. This section monitors platform compliance obligations, not customer compliance."
          showIcon
        />
      </div>
    );
  }

  return (
    <Layout style={{ padding: '24px', background: '#f5f5f5' }}>
      <Content>
        {/* Page Header */}
        <div style={{ marginBottom: '24px' }}>
          <Row justify="space-between" align="middle">
            <Col>
              <h2 style={{ margin: 0, display: 'flex', alignItems: 'center' }}>
                <ShieldCheckOutlined style={{ marginRight: '12px', color: '#1890ff' }} />
                TaxPoynt Compliance Center (Admin Only)
              </h2>
              <p style={{ margin: '4px 0 0 0', color: '#666' }}>
                Platform compliance monitoring for FIRS-mandated APP service provider standards
              </p>
            </Col>
            <Col>
              <Space>
                <Button icon={<SettingOutlined />}>
                  Compliance Settings
                </Button>
                <Button icon={<AuditOutlined />}>
                  Schedule Audit
                </Button>
                <Button type="primary" icon={<FileTextOutlined />}>
                  Generate Report
                </Button>
              </Space>
            </Col>
          </Row>
        </div>

        {/* Important Notice */}
        <Alert
          type="info"
          message="Platform Compliance Focus"
          description="This center monitors TaxPoynt's compliance obligations as an APP service provider. Customer business compliance is handled separately through their respective interfaces."
          showIcon
          style={{ marginBottom: '24px' }}
        />

        {/* Main Tabs */}
        <Tabs activeKey={activeTab} onChange={setActiveTab}>
          <TabPane
            tab={
              <span>
                <ShieldCheckOutlined />
                Platform Dashboard
              </span>
            }
            key="dashboard"
          >
            <PlatformComplianceDashboard 
              showDetails={true}
              className="compliance-center-dashboard"
            />
          </TabPane>

          <TabPane
            tab={
              <span>
                <SafetyCertificateOutlined />
                Standards Management
              </span>
            }
            key="standards"
          >
            <Card title="FIRS-Mandated Compliance Standards">
              <Table
                columns={standardsColumns}
                dataSource={complianceStandards}
                rowKey="code"
                pagination={false}
                size="small"
              />
            </Card>
          </TabPane>

          <TabPane
            tab={
              <span>
                <CalendarOutlined />
                Audit Timeline
              </span>
            }
            key="timeline"
          >
            <Row gutter={[24, 24]}>
              <Col xs={24} lg={16}>
                <Card title="Recent Compliance Activities">
                  <Timeline>
                    {recentActivities.map((activity, index) => (
                      <Timeline.Item
                        key={index}
                        color={
                          activity.status === 'completed' ? 'green' :
                          activity.status === 'in_progress' ? 'blue' : 'orange'
                        }
                        dot={
                          activity.type === 'audit' ? <AuditOutlined /> :
                          activity.type === 'certification' ? <SafetyCertificateOutlined /> :
                          <AlertOutlined />
                        }
                      >
                        <div>
                          <strong>{activity.title}</strong>
                          <br />
                          <span style={{ color: '#666' }}>{activity.details}</span>
                          <br />
                          <small style={{ color: '#999' }}>
                            {activity.timestamp.toLocaleString()}
                          </small>
                        </div>
                      </Timeline.Item>
                    ))}
                  </Timeline>
                </Card>
              </Col>
              
              <Col xs={24} lg={8}>
                <Card title="Upcoming Deadlines">
                  <Space direction="vertical" style={{ width: '100%' }}>
                    {complianceStandards
                      .filter(s => {
                        const daysLeft = Math.ceil((s.nextDeadline.getTime() - Date.now()) / (1000 * 60 * 60 * 24));
                        return daysLeft <= 90;
                      })
                      .sort((a, b) => a.nextDeadline.getTime() - b.nextDeadline.getTime())
                      .map(standard => {
                        const daysLeft = Math.ceil((standard.nextDeadline.getTime() - Date.now()) / (1000 * 60 * 60 * 24));
                        return (
                          <Card key={standard.code} size="small">
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                              <div>
                                <strong>{standard.name}</strong>
                                <br />
                                <span style={{ fontSize: '12px', color: '#666' }}>
                                  {standard.nextDeadline.toLocaleDateString()}
                                </span>
                              </div>
                              <Badge 
                                count={daysLeft <= 30 ? `${daysLeft}d` : null}
                                style={{ backgroundColor: daysLeft <= 30 ? '#ff4d4f' : '#52c41a' }}
                              />
                            </div>
                          </Card>
                        );
                      })
                    }
                  </Space>
                </Card>
              </Col>
            </Row>
          </TabPane>

          <TabPane
            tab={
              <span>
                <ApiOutlined />
                Platform APIs
              </span>
            }
            key="apis"
          >
            <Alert
              type="info"
              message="Platform API Compliance"
              description="Monitor API compliance for secure data transmission and FIRS integration endpoints."
              style={{ marginBottom: '24px' }}
            />
            
            <Card title="API Compliance Status">
              <Row gutter={[16, 16]}>
                <Col xs={24} sm={8}>
                  <Card size="small">
                    <div style={{ textAlign: 'center' }}>
                      <ApiOutlined style={{ fontSize: '32px', color: '#52c41a' }} />
                      <h3>FIRS Integration API</h3>
                      <Badge status="success" text="Compliant" />
                    </div>
                  </Card>
                </Col>
                
                <Col xs={24} sm={8}>
                  <Card size="small">
                    <div style={{ textAlign: 'center' }}>
                      <SafetyCertificateOutlined style={{ fontSize: '32px', color: '#1890ff' }} />
                      <h3>Certificate Management</h3>
                      <Badge status="processing" text="Active" />
                    </div>
                  </Card>
                </Col>
                
                <Col xs={24} sm={8}>
                  <Card size="small">
                    <div style={{ textAlign: 'center' }}>
                      <ShieldCheckOutlined style={{ fontSize: '32px', color: '#faad14' }} />
                      <h3>Security Endpoints</h3>
                      <Badge status="warning" text="Review Required" />
                    </div>
                  </Card>
                </Col>
              </Row>
            </Card>
          </TabPane>
        </Tabs>

        {/* Standard Management Modal */}
        <Modal
          title={`Manage Compliance Standard: ${selectedStandard}`}
          open={modalVisible}
          onCancel={() => {
            setModalVisible(false);
            setSelectedStandard(null);
          }}
          width={600}
          footer={[
            <Button key="cancel" onClick={() => setModalVisible(false)}>
              Cancel
            </Button>,
            <Button key="submit" type="primary">
              Update Standard
            </Button>
          ]}
        >
          <Form layout="vertical">
            <Form.Item label="Compliance Status">
              <Select defaultValue="compliant">
                <Option value="compliant">Compliant</Option>
                <Option value="non_compliant">Non-Compliant</Option>
                <Option value="pending">Pending Review</Option>
              </Select>
            </Form.Item>
            
            <Form.Item label="Next Review Date">
              <DatePicker style={{ width: '100%' }} />
            </Form.Item>
            
            <Form.Item label="Notes">
              <Input.TextArea placeholder="Add compliance notes or action items" />
            </Form.Item>
          </Form>
        </Modal>
      </Content>
    </Layout>
  );
};

export default ComplianceCenter;