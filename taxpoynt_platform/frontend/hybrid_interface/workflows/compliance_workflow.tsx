/**
 * Compliance Workflow (Hybrid Interface)
 * ======================================
 * 
 * Automated compliance workflow orchestration for TaxPoynt platform
 * obligations. Manages compliance processes, audits, and certification
 * renewals according to FIRS-mandated standards.
 * 
 * Features:
 * - Automated compliance checking workflows
 * - Certification renewal processes
 * - Audit trail management
 * - Risk assessment workflows
 * - Regulatory reporting automation
 * - Platform compliance monitoring
 * 
 * IMPORTANT: This handles TaxPoynt's platform compliance workflows,
 * NOT customer business compliance processes.
 * 
 * @author TaxPoynt Development Team
 * @version 1.0.0
 * @access Admin-Only
 */

import React, { useState, useEffect } from 'react';
import {
  Card,
  Steps,
  Button,
  Space,
  Alert,
  Timeline,
  Progress,
  Badge,
  Table,
  Modal,
  Form,
  Input,
  Select,
  DatePicker,
  Row,
  Col,
  Statistic,
  Tabs,
  Descriptions,
  Tag
} from 'antd';
import {
  ShieldCheckOutlined,
  AuditOutlined,
  SafetyCertificateOutlined,
  ClockCircleOutlined,
  PlayCircleOutlined,
  PauseCircleOutlined,
  CheckCircleOutlined,
  ExclamationTriangleOutlined,
  FileTextOutlined,
  SettingOutlined,
  CalendarOutlined,
  AlertOutlined
} from '@ant-design/icons';

const { Step } = Steps;
const { TabPane } = Tabs;
const { Option } = Select;

interface ComplianceWorkflowProps {
  workflowId?: string;
  organizationId: string;
  userRole: 'si' | 'app' | 'hybrid' | 'admin';
  onWorkflowComplete?: (result: any) => void;
}

interface WorkflowStep {
  id: string;
  name: string;
  type: 'validation' | 'audit' | 'certification' | 'reporting';
  status: 'pending' | 'in_progress' | 'completed' | 'failed' | 'skipped';
  progress: number;
  startTime?: Date;
  endTime?: Date;
  duration?: number;
  assignee: 'system' | 'admin' | 'external_auditor';
  requirements: string[];
  outputs: string[];
  nextDeadline?: Date;
}

interface ComplianceWorkflow {
  id: string;
  name: string;
  type: 'annual_audit' | 'certification_renewal' | 'risk_assessment' | 'regulatory_check';
  status: 'draft' | 'active' | 'completed' | 'failed' | 'scheduled';
  priority: 'low' | 'medium' | 'high' | 'critical';
  startDate: Date;
  targetDate: Date;
  completionDate?: Date;
  steps: WorkflowStep[];
  standards: string[]; // FIRS-mandated standards
  metadata: Record<string, any>;
}

export const ComplianceWorkflow: React.FC<ComplianceWorkflowProps> = ({
  workflowId,
  organizationId,
  userRole,
  onWorkflowComplete
}) => {
  const [currentWorkflow, setCurrentWorkflow] = useState<ComplianceWorkflow | null>(null);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [selectedStep, setSelectedStep] = useState<WorkflowStep | null>(null);
  const [activeTab, setActiveTab] = useState('overview');

  // Check admin access
  const hasAdminAccess = userRole === 'admin' || userRole === 'hybrid';

  // Sample compliance workflow
  const sampleWorkflow: ComplianceWorkflow = {
    id: workflowId || 'comp-wf-001',
    name: 'ISO 27001 Annual Compliance Audit',
    type: 'annual_audit',
    status: 'active',
    priority: 'high',
    startDate: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000),
    targetDate: new Date(Date.now() + 23 * 24 * 60 * 60 * 1000),
    steps: [
      {
        id: 'step-1',
        name: 'Pre-Audit Assessment',
        type: 'validation',
        status: 'completed',
        progress: 100,
        startTime: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000),
        endTime: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000),
        duration: 2 * 24 * 60 * 60, // 2 days in seconds
        assignee: 'admin',
        requirements: ['Policy Documentation', 'Risk Registry', 'Control Matrix'],
        outputs: ['Pre-audit Report', 'Gap Analysis']
      },
      {
        id: 'step-2',
        name: 'Security Controls Review',
        type: 'audit',
        status: 'completed',
        progress: 100,
        startTime: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000),
        endTime: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000),
        duration: 2 * 24 * 60 * 60,
        assignee: 'system',
        requirements: ['Access Controls', 'Encryption Standards', 'Monitoring Systems'],
        outputs: ['Control Assessment Report', 'Compliance Matrix']
      },
      {
        id: 'step-3',
        name: 'External Auditor Assessment',
        type: 'audit',
        status: 'in_progress',
        progress: 60,
        startTime: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000),
        assignee: 'external_auditor',
        requirements: ['Documentation Review', 'Technical Testing', 'Interview Sessions'],
        outputs: []
      },
      {
        id: 'step-4',
        name: 'Remediation Actions',
        type: 'validation',
        status: 'pending',
        progress: 0,
        assignee: 'admin',
        requirements: ['Action Plan', 'Implementation Timeline'],
        outputs: []
      },
      {
        id: 'step-5',
        name: 'Certification Renewal',
        type: 'certification',
        status: 'pending',
        progress: 0,
        assignee: 'external_auditor',
        requirements: ['Final Audit Report', 'Management Approval'],
        outputs: [],
        nextDeadline: new Date(Date.now() + 23 * 24 * 60 * 60 * 1000)
      }
    ],
    standards: ['ISO_27001', 'NITDA_GDPR'],
    metadata: {
      auditor: 'SecureAudit Nigeria Ltd',
      costCenter: 'IT-COMPLIANCE',
      businessImpact: 'High'
    }
  };

  useEffect(() => {
    if (hasAdminAccess) {
      setCurrentWorkflow(sampleWorkflow);
    }
  }, [workflowId, hasAdminAccess]);

  const handleStepAction = (stepId: string, action: 'start' | 'complete' | 'skip') => {
    if (!currentWorkflow) return;

    setCurrentWorkflow(prev => {
      if (!prev) return prev;
      
      return {
        ...prev,
        steps: prev.steps.map(step => {
          if (step.id === stepId) {
            switch (action) {
              case 'start':
                return { ...step, status: 'in_progress', startTime: new Date() };
              case 'complete':
                return { 
                  ...step, 
                  status: 'completed', 
                  progress: 100,
                  endTime: new Date(),
                  duration: step.startTime ? 
                    Math.floor((Date.now() - step.startTime.getTime()) / 1000) : undefined
                };
              case 'skip':
                return { ...step, status: 'skipped' };
              default:
                return step;
            }
          }
          return step;
        })
      };
    });
  };

  const handleStepClick = (step: WorkflowStep) => {
    setSelectedStep(step);
    setModalVisible(true);
  };

  const getStepIcon = (step: WorkflowStep) => {
    switch (step.type) {
      case 'validation': return <ShieldCheckOutlined />;
      case 'audit': return <AuditOutlined />;
      case 'certification': return <SafetyCertificateOutlined />;
      case 'reporting': return <FileTextOutlined />;
      default: return <SettingOutlined />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return '#52c41a';
      case 'in_progress': return '#1890ff';
      case 'failed': return '#ff4d4f';
      case 'pending': return '#d9d9d9';
      case 'skipped': return '#faad14';
      default: return '#d9d9d9';
    }
  };

  const getCurrentStepIndex = () => {
    if (!currentWorkflow) return 0;
    const activeStep = currentWorkflow.steps.findIndex(s => s.status === 'in_progress');
    return activeStep >= 0 ? activeStep : 
           currentWorkflow.steps.findIndex(s => s.status === 'pending');
  };

  // Access control check
  if (!hasAdminAccess) {
    return (
      <Card>
        <Alert
          type="warning"
          message="Access Restricted"
          description="Compliance workflows are only available to TaxPoynt administrators. These workflows manage platform compliance obligations, not customer processes."
          showIcon
        />
      </Card>
    );
  }

  if (!currentWorkflow) {
    return (
      <Card style={{ textAlign: 'center', padding: '48px' }}>
        <AuditOutlined style={{ fontSize: '48px', color: '#d9d9d9' }} />
        <h3>No Active Compliance Workflow</h3>
        <p>Create a new compliance workflow to get started.</p>
        <Button type="primary" icon={<PlayCircleOutlined />}>
          Create Workflow
        </Button>
      </Card>
    );
  }

  return (
    <div>
      {/* Workflow Header */}
      <Card style={{ marginBottom: '24px' }}>
        <Row justify="space-between" align="middle">
          <Col>
            <div>
              <h3 style={{ margin: 0, display: 'flex', alignItems: 'center' }}>
                <AuditOutlined style={{ marginRight: '8px', color: '#1890ff' }} />
                {currentWorkflow.name}
                <Badge 
                  status={
                    currentWorkflow.status === 'active' ? 'processing' :
                    currentWorkflow.status === 'completed' ? 'success' :
                    currentWorkflow.status === 'failed' ? 'error' : 'default'
                  }
                  text={currentWorkflow.status.toUpperCase()}
                  style={{ marginLeft: '12px' }}
                />
                <Tag 
                  color={
                    currentWorkflow.priority === 'critical' ? 'red' :
                    currentWorkflow.priority === 'high' ? 'orange' :
                    currentWorkflow.priority === 'medium' ? 'blue' : 'default'
                  }
                  style={{ marginLeft: '8px' }}
                >
                  {currentWorkflow.priority.toUpperCase()}
                </Tag>
              </h3>
              <p style={{ margin: '4px 0 0 0', color: '#666' }}>
                Target Date: {currentWorkflow.targetDate.toLocaleDateString()} | 
                Standards: {currentWorkflow.standards.join(', ')}
              </p>
            </div>
          </Col>
          <Col>
            <Space>
              <Button icon={<CalendarOutlined />}>
                Schedule
              </Button>
              <Button icon={<FileTextOutlined />}>
                Export Report
              </Button>
              <Button type="primary" icon={<SettingOutlined />}>
                Configure
              </Button>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* Key Metrics */}
      <Row gutter={[24, 24]} style={{ marginBottom: '24px' }}>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="Overall Progress"
              value={Math.round(currentWorkflow.steps.reduce((sum, step) => sum + step.progress, 0) / currentWorkflow.steps.length)}
              suffix="%"
              prefix={<ShieldCheckOutlined />}
            />
          </Card>
        </Col>
        
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="Completed Steps"
              value={currentWorkflow.steps.filter(s => s.status === 'completed').length}
              suffix={`/ ${currentWorkflow.steps.length}`}
              prefix={<CheckCircleOutlined />}
            />
          </Card>
        </Col>
        
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="Days Remaining"
              value={Math.ceil((currentWorkflow.targetDate.getTime() - Date.now()) / (1000 * 60 * 60 * 24))}
              suffix="days"
              prefix={<ClockCircleOutlined />}
              valueStyle={{ color: Math.ceil((currentWorkflow.targetDate.getTime() - Date.now()) / (1000 * 60 * 60 * 24)) <= 7 ? '#ff4d4f' : '#52c41a' }}
            />
          </Card>
        </Col>
        
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="Standards"
              value={currentWorkflow.standards.length}
              suffix="covered"
              prefix={<SafetyCertificateOutlined />}
            />
          </Card>
        </Col>
      </Row>

      {/* Main Content */}
      <Tabs activeKey={activeTab} onChange={setActiveTab}>
        <TabPane
          tab={
            <span>
              <PlayCircleOutlined />
              Workflow Steps
            </span>
          }
          key="overview"
        >
          <Card title="Compliance Workflow Progress">
            <Steps current={getCurrentStepIndex()} direction="vertical" size="small">
              {currentWorkflow.steps.map((step, index) => (
                <Step
                  key={step.id}
                  title={
                    <div style={{ cursor: 'pointer' }} onClick={() => handleStepClick(step)}>
                      <Space>
                        {step.name}
                        <Tag color={
                          step.type === 'validation' ? 'blue' :
                          step.type === 'audit' ? 'green' :
                          step.type === 'certification' ? 'purple' : 'orange'
                        }>
                          {step.type.toUpperCase()}
                        </Tag>
                        <Tag>{step.assignee.replace('_', ' ').toUpperCase()}</Tag>
                      </Space>
                    </div>
                  }
                  description={
                    <div>
                      <Progress 
                        percent={step.progress} 
                        size="small"
                        status={step.status === 'failed' ? 'exception' : undefined}
                      />
                      <div style={{ marginTop: '8px' }}>
                        {step.status === 'in_progress' && (
                          <Space>
                            <Button size="small" onClick={() => handleStepAction(step.id, 'complete')}>
                              Mark Complete
                            </Button>
                            <Button size="small" onClick={() => handleStepAction(step.id, 'skip')}>
                              Skip
                            </Button>
                          </Space>
                        )}
                        {step.status === 'pending' && step.assignee === 'admin' && (
                          <Button size="small" type="primary" onClick={() => handleStepAction(step.id, 'start')}>
                            Start Step
                          </Button>
                        )}
                        {step.nextDeadline && (
                          <div style={{ marginTop: '4px', fontSize: '12px', color: '#fa8c16' }}>
                            <CalendarOutlined /> Deadline: {step.nextDeadline.toLocaleDateString()}
                          </div>
                        )}
                      </div>
                    </div>
                  }
                  status={
                    step.status === 'completed' ? 'finish' :
                    step.status === 'in_progress' ? 'process' :
                    step.status === 'failed' ? 'error' : 'wait'
                  }
                  icon={getStepIcon(step)}
                />
              ))}
            </Steps>
          </Card>
        </TabPane>

        <TabPane
          tab={
            <span>
              <ClockCircleOutlined />
              Timeline
            </span>
          }
          key="timeline"
        >
          <Card title="Workflow Timeline">
            <Timeline>
              {currentWorkflow.steps.map(step => (
                <Timeline.Item
                  key={step.id}
                  color={getStatusColor(step.status)}
                  dot={getStepIcon(step)}
                >
                  <div>
                    <strong>{step.name}</strong>
                    <Space style={{ marginLeft: '8px' }}>
                      <Tag color={
                        step.type === 'validation' ? 'blue' :
                        step.type === 'audit' ? 'green' :
                        step.type === 'certification' ? 'purple' : 'orange'
                      }>
                        {step.type}
                      </Tag>
                      <Badge 
                        status={
                          step.status === 'completed' ? 'success' :
                          step.status === 'in_progress' ? 'processing' :
                          step.status === 'failed' ? 'error' : 'default'
                        }
                        text={step.status.replace('_', ' ').toUpperCase()}
                      />
                    </Space>
                    <br />
                    {step.startTime && (
                      <span style={{ color: '#666', fontSize: '12px' }}>
                        Started: {step.startTime.toLocaleString()}
                        {step.endTime && ` | Completed: ${step.endTime.toLocaleString()}`}
                      </span>
                    )}
                  </div>
                </Timeline.Item>
              ))}
            </Timeline>
          </Card>
        </TabPane>

        <TabPane
          tab={
            <span>
              <FileTextOutlined />
              Requirements
            </span>
          }
          key="requirements"
        >
          <Card title="Step Requirements & Outputs">
            <Table
              size="small"
              columns={[
                {
                  title: 'Step',
                  dataIndex: 'name',
                  key: 'name',
                  render: (name: string, record: WorkflowStep) => (
                    <div>
                      <strong>{name}</strong>
                      <br />
                      <Badge 
                        status={
                          record.status === 'completed' ? 'success' :
                          record.status === 'in_progress' ? 'processing' :
                          record.status === 'failed' ? 'error' : 'default'
                        }
                        text={record.status.replace('_', ' ').toUpperCase()}
                      />
                    </div>
                  )
                },
                {
                  title: 'Requirements',
                  dataIndex: 'requirements',
                  key: 'requirements',
                  render: (requirements: string[]) => (
                    <div>
                      {requirements.map(req => (
                        <Tag key={req} style={{ marginBottom: '2px' }}>
                          {req}
                        </Tag>
                      ))}
                    </div>
                  )
                },
                {
                  title: 'Outputs',
                  dataIndex: 'outputs',
                  key: 'outputs',
                  render: (outputs: string[]) => (
                    <div>
                      {outputs.map(output => (
                        <Tag key={output} color="success" style={{ marginBottom: '2px' }}>
                          {output}
                        </Tag>
                      ))}
                    </div>
                  )
                },
                {
                  title: 'Assignee',
                  dataIndex: 'assignee',
                  key: 'assignee',
                  render: (assignee: string) => (
                    <Tag color={
                      assignee === 'admin' ? 'blue' :
                      assignee === 'system' ? 'green' : 'orange'
                    }>
                      {assignee.replace('_', ' ').toUpperCase()}
                    </Tag>
                  )
                }
              ]}
              dataSource={currentWorkflow.steps}
              rowKey="id"
              pagination={false}
            />
          </Card>
        </TabPane>
      </Tabs>

      {/* Step Details Modal */}
      <Modal
        title={`Step Details: ${selectedStep?.name}`}
        open={modalVisible}
        onCancel={() => {
          setModalVisible(false);
          setSelectedStep(null);
        }}
        width={700}
        footer={[
          <Button key="close" onClick={() => setModalVisible(false)}>
            Close
          </Button>
        ]}
      >
        {selectedStep && (
          <div>
            <Descriptions column={2} size="small">
              <Descriptions.Item label="Type">
                <Tag color={
                  selectedStep.type === 'validation' ? 'blue' :
                  selectedStep.type === 'audit' ? 'green' :
                  selectedStep.type === 'certification' ? 'purple' : 'orange'
                }>
                  {selectedStep.type.toUpperCase()}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="Status">
                <Badge 
                  status={
                    selectedStep.status === 'completed' ? 'success' :
                    selectedStep.status === 'in_progress' ? 'processing' :
                    selectedStep.status === 'failed' ? 'error' : 'default'
                  }
                  text={selectedStep.status.replace('_', ' ').toUpperCase()}
                />
              </Descriptions.Item>
              <Descriptions.Item label="Assignee">
                <Tag color={
                  selectedStep.assignee === 'admin' ? 'blue' :
                  selectedStep.assignee === 'system' ? 'green' : 'orange'
                }>
                  {selectedStep.assignee.replace('_', ' ').toUpperCase()}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="Progress">
                <Progress percent={selectedStep.progress} size="small" />
              </Descriptions.Item>
              <Descriptions.Item label="Duration">
                {selectedStep.duration ? 
                  `${Math.round(selectedStep.duration / (24 * 60 * 60))} days` : 'N/A'
                }
              </Descriptions.Item>
              <Descriptions.Item label="Next Deadline">
                {selectedStep.nextDeadline ? 
                  selectedStep.nextDeadline.toLocaleDateString() : 'N/A'
                }
              </Descriptions.Item>
            </Descriptions>
            
            <div style={{ marginTop: '16px' }}>
              <h4>Requirements:</h4>
              <div>
                {selectedStep.requirements.map(req => (
                  <Tag key={req}>{req}</Tag>
                ))}
              </div>
            </div>
            
            {selectedStep.outputs.length > 0 && (
              <div style={{ marginTop: '16px' }}>
                <h4>Outputs:</h4>
                <div>
                  {selectedStep.outputs.map(output => (
                    <Tag key={output} color="success">{output}</Tag>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </Modal>
    </div>
  );
};

export default ComplianceWorkflow;