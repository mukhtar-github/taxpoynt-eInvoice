/**
 * Cross-Role Troubleshooting Workflow (Hybrid Interface)
 * ======================================================
 * 
 * Comprehensive troubleshooting and diagnostic workflow that spans
 * both SI and APP operations. Provides systematic problem resolution
 * with cross-role visibility and collaborative debugging capabilities.
 * 
 * Features:
 * - Cross-role issue diagnosis and resolution
 * - Systematic troubleshooting workflows
 * - Real-time diagnostic tools and monitoring
 * - Collaborative problem-solving interface
 * - Knowledge base integration
 * - Escalation and notification management
 * - Root cause analysis and prevention
 * 
 * @author TaxPoynt Development Team
 * @version 1.0.0
 */

import React, { useState, useEffect } from 'react';
import {
  Card,
  Steps,
  Button,
  Space,
  Alert,
  Table,
  Modal,
  Form,
  Input,
  Select,
  Tabs,
  Row,
  Col,
  Timeline,
  Badge,
  Tag,
  Collapse,
  Descriptions,
  Progress,
  List,
  Tooltip,
  Divider,
  Tree
} from 'antd';
import {
  BugOutlined,
  SearchOutlined,
  ToolOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  ClockCircleOutlined,
  TeamOutlined,
  FileTextOutlined,
  AlertOutlined,
  PlayCircleOutlined,
  ReloadOutlined,
  BookOutlined,
  PhoneOutlined,
  WarningOutlined
} from '@ant-design/icons';

const { Step } = Steps;
const { TabPane } = Tabs;
const { Panel } = Collapse;
const { TextArea } = Input;
const { Option } = Select;

interface TroubleshootingProps {
  issueId?: string;
  organizationId: string;
  userRole: 'si' | 'app' | 'hybrid' | 'admin';
  onResolutionComplete?: (result: any) => void;
}

interface TroubleshootingStep {
  id: string;
  name: string;
  description: string;
  type: 'diagnostic' | 'action' | 'validation' | 'escalation';
  status: 'pending' | 'in_progress' | 'completed' | 'skipped' | 'failed';
  role: 'si' | 'app' | 'hybrid' | 'external';
  estimatedTime: number; // minutes
  actualTime?: number;
  assignee?: string;
  prerequisites: string[];
  tools: string[];
  expectedResult: string;
  actualResult?: string;
  nextSteps?: string[];
}

interface TroubleshootingSession {
  id: string;
  title: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  category: 'integration' | 'compliance' | 'performance' | 'security' | 'data';
  status: 'open' | 'investigating' | 'resolved' | 'escalated' | 'closed';
  reporter: string;
  assignee?: string;
  startTime: Date;
  lastUpdated: Date;
  resolutionTime?: Date;
  affectedSystems: string[];
  affectedRoles: ('si' | 'app' | 'hybrid')[];
  description: string;
  steps: TroubleshootingStep[];
  knowledgeBaseArticles: string[];
  similarIssues: string[];
  rootCause?: string;
  resolution?: string;
  preventionMeasures?: string[];
}

export const Troubleshooting: React.FC<TroubleshootingProps> = ({
  issueId,
  organizationId,
  userRole,
  onResolutionComplete
}) => {
  const [currentSession, setCurrentSession] = useState<TroubleshootingSession | null>(null);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [selectedStep, setSelectedStep] = useState<TroubleshootingStep | null>(null);
  const [activeTab, setActiveTab] = useState('workflow');
  const [newIssueModalVisible, setNewIssueModalVisible] = useState(false);

  // Sample troubleshooting session
  const sampleSession: TroubleshootingSession = {
    id: issueId || 'trouble-001',
    title: 'FIRS Submission Failures - ISO 20022 Format Issues',
    severity: 'high',
    category: 'integration',
    status: 'investigating',
    reporter: 'system-monitor',
    assignee: 'tech-support',
    startTime: new Date(Date.now() - 2 * 60 * 60 * 1000),
    lastUpdated: new Date(Date.now() - 10 * 60 * 1000),
    affectedSystems: ['FIRS Integration API', 'ISO 20022 Validator', 'Submission Queue'],
    affectedRoles: ['app', 'hybrid'],
    description: 'Multiple FIRS submissions are failing due to ISO 20022 message format validation errors. The issue started approximately 2 hours ago and is affecting 15% of submission attempts.',
    steps: [
      {
        id: 'step-1',
        name: 'Initial Problem Assessment',
        description: 'Analyze error logs and identify the scope of the issue',
        type: 'diagnostic',
        status: 'completed',
        role: 'hybrid',
        estimatedTime: 15,
        actualTime: 12,
        assignee: 'tech-support',
        prerequisites: [],
        tools: ['Log Analyzer', 'Error Dashboard'],
        expectedResult: 'Clear understanding of error patterns and affected volume',
        actualResult: '15% failure rate, consistent format validation errors in payment instruction messages',
        nextSteps: ['step-2']
      },
      {
        id: 'step-2',
        name: 'ISO 20022 Format Validation',
        description: 'Deep dive into message format validation failures',
        type: 'diagnostic',
        status: 'completed',
        role: 'app',
        estimatedTime: 20,
        actualTime: 18,
        assignee: 'compliance-team',
        prerequisites: ['step-1'],
        tools: ['ISO 20022 Schema Validator', 'Message Inspector'],
        expectedResult: 'Identify specific schema violations',
        actualResult: 'Found missing mandatory field: Ultimate Creditor (UltmtCdtr) in payment messages',
        nextSteps: ['step-3']
      },
      {
        id: 'step-3',
        name: 'Data Source Investigation',
        description: 'Trace back to SI layer to identify data mapping issues',
        type: 'diagnostic',
        status: 'in_progress',
        role: 'si',
        estimatedTime: 30,
        assignee: 'integration-specialist',
        prerequisites: ['step-2'],
        tools: ['Data Mapper', 'ERP Connector Logs'],
        expectedResult: 'Identify where Ultimate Creditor mapping is failing',
        actualResult: undefined
      },
      {
        id: 'step-4',
        name: 'Fix Data Mapping Configuration',
        description: 'Update data transformation rules to include missing field',
        type: 'action',
        status: 'pending',
        role: 'si',
        estimatedTime: 45,
        prerequisites: ['step-3'],
        tools: ['Configuration Manager', 'Data Transformer'],
        expectedResult: 'Updated mapping to populate Ultimate Creditor field',
        actualResult: undefined
      },
      {
        id: 'step-5',
        name: 'Test and Validate Fix',
        description: 'Test the fix with sample data and validate against ISO 20022 schema',
        type: 'validation',
        status: 'pending',
        role: 'hybrid',
        estimatedTime: 25,
        prerequisites: ['step-4'],
        tools: ['Test Data Generator', 'Schema Validator'],
        expectedResult: 'Successful validation of test messages',
        actualResult: undefined
      },
      {
        id: 'step-6',
        name: 'Deploy Fix and Monitor',
        description: 'Deploy the configuration changes and monitor for resolution',
        type: 'action',
        status: 'pending',
        role: 'hybrid',
        estimatedTime: 20,
        prerequisites: ['step-5'],
        tools: ['Deployment Manager', 'Real-time Monitor'],
        expectedResult: 'Zero format validation errors in new submissions',
        actualResult: undefined
      }
    ],
    knowledgeBaseArticles: [
      'ISO 20022 Common Validation Errors',
      'FIRS Submission Format Requirements',
      'Data Mapping Best Practices'
    ],
    similarIssues: [
      'FIRS-2024-003: Missing Debtor Agent Reference',
      'FIRS-2024-001: Invalid Currency Code Format'
    ]
  };

  useEffect(() => {
    setCurrentSession(sampleSession);
  }, [issueId]);

  const handleStepAction = (stepId: string, action: 'start' | 'complete' | 'skip' | 'fail') => {
    if (!currentSession) return;

    setCurrentSession(prev => {
      if (!prev) return prev;
      
      return {
        ...prev,
        lastUpdated: new Date(),
        steps: prev.steps.map(step => {
          if (step.id === stepId) {
            switch (action) {
              case 'start':
                return { ...step, status: 'in_progress', assignee: userRole };
              case 'complete':
                return { 
                  ...step, 
                  status: 'completed',
                  actualTime: step.estimatedTime // Simulate completion time
                };
              case 'skip':
                return { ...step, status: 'skipped' };
              case 'fail':
                return { ...step, status: 'failed' };
              default:
                return step;
            }
          }
          return step;
        })
      };
    });
  };

  const handleStepClick = (step: TroubleshootingStep) => {
    setSelectedStep(step);
    setModalVisible(true);
  };

  const getStepIcon = (step: TroubleshootingStep) => {
    switch (step.type) {
      case 'diagnostic': return <SearchOutlined />;
      case 'action': return <ToolOutlined />;
      case 'validation': return <CheckCircleOutlined />;
      case 'escalation': return <PhoneOutlined />;
      default: return <BugOutlined />;
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return '#ff4d4f';
      case 'high': return '#fa8c16';
      case 'medium': return '#faad14';
      case 'low': return '#52c41a';
      default: return '#d9d9d9';
    }
  };

  const getCurrentStepIndex = () => {
    if (!currentSession) return 0;
    const activeStep = currentSession.steps.findIndex(s => s.status === 'in_progress');
    return activeStep >= 0 ? activeStep : 
           currentSession.steps.findIndex(s => s.status === 'pending');
  };

  if (!currentSession) {
    return (
      <Card style={{ textAlign: 'center', padding: '48px' }}>
        <BugOutlined style={{ fontSize: '48px', color: '#d9d9d9' }} />
        <h3>No Active Troubleshooting Session</h3>
        <p>Start a new troubleshooting session or select an existing issue to resolve.</p>
        <Button type="primary" icon={<PlayCircleOutlined />} onClick={() => setNewIssueModalVisible(true)}>
          Start New Session
        </Button>
      </Card>
    );
  }

  return (
    <div>
      {/* Session Header */}
      <Card style={{ marginBottom: '24px' }}>
        <Row justify="space-between" align="middle">
          <Col>
            <div>
              <h3 style={{ margin: 0, display: 'flex', alignItems: 'center' }}>
                <BugOutlined style={{ marginRight: '8px', color: getSeverityColor(currentSession.severity) }} />
                {currentSession.title}
                <Badge 
                  status={
                    currentSession.status === 'resolved' ? 'success' :
                    currentSession.status === 'investigating' ? 'processing' :
                    currentSession.status === 'escalated' ? 'warning' : 'default'
                  }
                  text={currentSession.status.toUpperCase()}
                  style={{ marginLeft: '12px' }}
                />
                <Tag 
                  color={getSeverityColor(currentSession.severity)}
                  style={{ marginLeft: '8px' }}
                >
                  {currentSession.severity.toUpperCase()}
                </Tag>
              </h3>
              <p style={{ margin: '4px 0 0 0', color: '#666' }}>
                Issue ID: {currentSession.id} | 
                Started: {currentSession.startTime.toLocaleString()} | 
                Category: {currentSession.category}
              </p>
            </div>
          </Col>
          <Col>
            <Space>
              <Button icon={<TeamOutlined />}>
                Assign
              </Button>
              <Button icon={<PhoneOutlined />}>
                Escalate
              </Button>
              <Button icon={<FileTextOutlined />}>
                Export Log
              </Button>
              <Button type="primary" icon={<CheckCircleOutlined />}>
                Mark Resolved
              </Button>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* Issue Summary */}
      <Row gutter={[24, 24]} style={{ marginBottom: '24px' }}>
        <Col xs={24} lg={16}>
          <Card title="Issue Description" size="small">
            <p>{currentSession.description}</p>
            <Descriptions column={2} size="small">
              <Descriptions.Item label="Affected Systems">
                {currentSession.affectedSystems.map(system => (
                  <Tag key={system} color="blue">{system}</Tag>
                ))}
              </Descriptions.Item>
              <Descriptions.Item label="Affected Roles">
                {currentSession.affectedRoles.map(role => (
                  <Tag key={role} color={
                    role === 'si' ? 'blue' : role === 'app' ? 'green' : 'purple'
                  }>
                    {role.toUpperCase()}
                  </Tag>
                ))}
              </Descriptions.Item>
              <Descriptions.Item label="Reporter">{currentSession.reporter}</Descriptions.Item>
              <Descriptions.Item label="Assignee">{currentSession.assignee || 'Unassigned'}</Descriptions.Item>
            </Descriptions>
          </Card>
        </Col>
        
        <Col xs={24} lg={8}>
          <Card title="Progress Overview" size="small">
            <div style={{ marginBottom: '16px' }}>
              <Progress 
                percent={Math.round(
                  (currentSession.steps.filter(s => s.status === 'completed').length / 
                   currentSession.steps.length) * 100
                )}
                status={currentSession.status === 'resolved' ? 'success' : 'active'}
              />
            </div>
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                <span>Completed:</span>
                <span>{currentSession.steps.filter(s => s.status === 'completed').length} / {currentSession.steps.length}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                <span>In Progress:</span>
                <span>{currentSession.steps.filter(s => s.status === 'in_progress').length}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span>Estimated Time Left:</span>
                <span>
                  {currentSession.steps
                    .filter(s => s.status === 'pending')
                    .reduce((sum, s) => sum + s.estimatedTime, 0)} min
                </span>
              </div>
            </div>
          </Card>
        </Col>
      </Row>

      {/* Main Content */}
      <Tabs activeKey={activeTab} onChange={setActiveTab}>
        <TabPane
          tab={
            <span>
              <ToolOutlined />
              Troubleshooting Workflow
            </span>
          }
          key="workflow"
        >
          <Card title="Resolution Steps">
            <Steps current={getCurrentStepIndex()} direction="vertical" size="small">
              {currentSession.steps.map((step, index) => (
                <Step
                  key={step.id}
                  title={
                    <div style={{ cursor: 'pointer' }} onClick={() => handleStepClick(step)}>
                      <Space>
                        {step.name}
                        <Tag color={
                          step.type === 'diagnostic' ? 'blue' :
                          step.type === 'action' ? 'green' :
                          step.type === 'validation' ? 'purple' : 'orange'
                        }>
                          {step.type.toUpperCase()}
                        </Tag>
                        <Tag color={
                          step.role === 'si' ? 'blue' : 
                          step.role === 'app' ? 'green' : 
                          step.role === 'hybrid' ? 'purple' : 'orange'
                        }>
                          {step.role.toUpperCase()}
                        </Tag>
                      </Space>
                    </div>
                  }
                  description={
                    <div>
                      <p style={{ margin: '8px 0', fontSize: '14px' }}>{step.description}</p>
                      <div style={{ marginBottom: '8px' }}>
                        <strong>Expected:</strong> {step.expectedResult}
                      </div>
                      {step.actualResult && (
                        <div style={{ marginBottom: '8px', color: '#52c41a' }}>
                          <strong>Actual:</strong> {step.actualResult}
                        </div>
                      )}
                      <div style={{ marginBottom: '8px' }}>
                        <Space>
                          {step.tools.map(tool => (
                            <Tag key={tool} icon={<ToolOutlined />}>{tool}</Tag>
                          ))}
                        </Space>
                      </div>
                      {step.status === 'in_progress' && step.assignee === userRole && (
                        <Space>
                          <Button size="small" type="primary" onClick={() => handleStepAction(step.id, 'complete')}>
                            Mark Complete
                          </Button>
                          <Button size="small" onClick={() => handleStepAction(step.id, 'skip')}>
                            Skip
                          </Button>
                          <Button size="small" danger onClick={() => handleStepAction(step.id, 'fail')}>
                            Mark Failed
                          </Button>
                        </Space>
                      )}
                      {step.status === 'pending' && (
                        <Button size="small" onClick={() => handleStepAction(step.id, 'start')}>
                          Start Step
                        </Button>
                      )}
                      {step.estimatedTime && (
                        <div style={{ marginTop: '4px', fontSize: '12px', color: '#666' }}>
                          <ClockCircleOutlined /> Est. {step.estimatedTime} min
                          {step.actualTime && ` | Actual: ${step.actualTime} min`}
                        </div>
                      )}
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
              <BookOutlined />
              Knowledge Base
            </span>
          }
          key="knowledge"
        >
          <Row gutter={[24, 24]}>
            <Col xs={24} lg={12}>
              <Card title="Related Articles" size="small">
                <List
                  dataSource={currentSession.knowledgeBaseArticles}
                  renderItem={article => (
                    <List.Item
                      actions={[
                        <Button size="small" type="link" icon={<BookOutlined />}>
                          View
                        </Button>
                      ]}
                    >
                      <List.Item.Meta
                        avatar={<FileTextOutlined />}
                        title={article}
                      />
                    </List.Item>
                  )}
                />
              </Card>
            </Col>
            
            <Col xs={24} lg={12}>
              <Card title="Similar Issues" size="small">
                <List
                  dataSource={currentSession.similarIssues}
                  renderItem={issue => (
                    <List.Item
                      actions={[
                        <Button size="small" type="link">
                          View Details
                        </Button>
                      ]}
                    >
                      <List.Item.Meta
                        avatar={<BugOutlined />}
                        title={issue}
                        description="Previously resolved"
                      />
                    </List.Item>
                  )}
                />
              </Card>
            </Col>
          </Row>
        </TabPane>

        <TabPane
          tab={
            <span>
              <AlertOutlined />
              System Diagnostics
            </span>
          }
          key="diagnostics"
        >
          <Alert
            type="info"
            message="Real-time Diagnostics"
            description="Live system monitoring and diagnostic tools for affected components."
            style={{ marginBottom: '24px' }}
          />
          
          <Row gutter={[24, 24]}>
            <Col xs={24} lg={8}>
              <Card title="System Health" size="small">
                <div style={{ textAlign: 'center' }}>
                  <Progress 
                    type="circle" 
                    percent={85} 
                    status="active"
                    strokeColor={{ '0%': '#108ee9', '100%': '#87d068' }}
                  />
                  <p style={{ marginTop: '16px' }}>Overall System Health</p>
                </div>
              </Card>
            </Col>
            
            <Col xs={24} lg={16}>
              <Card title="Component Status" size="small">
                <List
                  dataSource={currentSession.affectedSystems}
                  renderItem={system => (
                    <List.Item>
                      <List.Item.Meta
                        avatar={
                          <Badge 
                            status={system.includes('FIRS') ? 'warning' : 'success'}
                            dot
                          />
                        }
                        title={system}
                        description={
                          system.includes('FIRS') ? 
                          'Experiencing validation errors' : 
                          'Operating normally'
                        }
                      />
                      <Button size="small" icon={<ReloadOutlined />}>
                        Refresh
                      </Button>
                    </List.Item>
                  )}
                />
              </Card>
            </Col>
          </Row>
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
                  selectedStep.type === 'diagnostic' ? 'blue' :
                  selectedStep.type === 'action' ? 'green' :
                  selectedStep.type === 'validation' ? 'purple' : 'orange'
                }>
                  {selectedStep.type.toUpperCase()}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="Role">
                <Tag color={
                  selectedStep.role === 'si' ? 'blue' : 
                  selectedStep.role === 'app' ? 'green' : 
                  selectedStep.role === 'hybrid' ? 'purple' : 'orange'
                }>
                  {selectedStep.role.toUpperCase()}
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
                {selectedStep.assignee || 'Unassigned'}
              </Descriptions.Item>
              <Descriptions.Item label="Estimated Time">
                {selectedStep.estimatedTime} minutes
              </Descriptions.Item>
              <Descriptions.Item label="Actual Time">
                {selectedStep.actualTime ? `${selectedStep.actualTime} minutes` : 'N/A'}
              </Descriptions.Item>
            </Descriptions>
            
            <Divider />
            
            <div style={{ marginBottom: '16px' }}>
              <h4>Description:</h4>
              <p>{selectedStep.description}</p>
            </div>
            
            <div style={{ marginBottom: '16px' }}>
              <h4>Expected Result:</h4>
              <p>{selectedStep.expectedResult}</p>
            </div>
            
            {selectedStep.actualResult && (
              <div style={{ marginBottom: '16px' }}>
                <h4>Actual Result:</h4>
                <p style={{ color: '#52c41a' }}>{selectedStep.actualResult}</p>
              </div>
            )}
            
            <div style={{ marginBottom: '16px' }}>
              <h4>Tools Required:</h4>
              <div>
                {selectedStep.tools.map(tool => (
                  <Tag key={tool} icon={<ToolOutlined />}>{tool}</Tag>
                ))}
              </div>
            </div>
            
            {selectedStep.prerequisites.length > 0 && (
              <div>
                <h4>Prerequisites:</h4>
                <div>
                  {selectedStep.prerequisites.map(prereq => (
                    <Tag key={prereq}>{prereq}</Tag>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </Modal>

      {/* New Issue Modal */}
      <Modal
        title="Start New Troubleshooting Session"
        open={newIssueModalVisible}
        onCancel={() => setNewIssueModalVisible(false)}
        onOk={() => {
          // Handle new issue creation
          setNewIssueModalVisible(false);
        }}
      >
        <Form layout="vertical">
          <Form.Item label="Issue Title" name="title" rules={[{ required: true }]}>
            <Input placeholder="Brief description of the issue" />
          </Form.Item>
          
          <Form.Item label="Severity" name="severity" rules={[{ required: true }]}>
            <Select placeholder="Select severity level">
              <Option value="low">Low</Option>
              <Option value="medium">Medium</Option>
              <Option value="high">High</Option>
              <Option value="critical">Critical</Option>
            </Select>
          </Form.Item>
          
          <Form.Item label="Category" name="category" rules={[{ required: true }]}>
            <Select placeholder="Select issue category">
              <Option value="integration">Integration</Option>
              <Option value="compliance">Compliance</Option>
              <Option value="performance">Performance</Option>
              <Option value="security">Security</Option>
              <Option value="data">Data</Option>
            </Select>
          </Form.Item>
          
          <Form.Item label="Description" name="description" rules={[{ required: true }]}>
            <TextArea rows={4} placeholder="Detailed description of the issue" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default Troubleshooting;