/**
 * Workflow Orchestrator Component
 * ===============================
 * 
 * Advanced workflow orchestration component that manages and coordinates
 * complex workflows spanning both SI and APP interfaces. Provides visual
 * workflow design, execution monitoring, and automated orchestration.
 * 
 * Features:
 * - Visual workflow designer and editor
 * - Cross-role workflow execution monitoring
 * - Automated workflow triggering and scheduling
 * - Real-time execution status tracking
 * - Error handling and retry mechanisms
 * - Workflow templates and best practices
 * - Performance analytics and optimization
 * 
 * @author TaxPoynt Development Team
 * @version 1.0.0
 */

import React, { useState, useEffect, useCallback } from 'react';
import { 
  Card, 
  Row, 
  Col, 
  Button, 
  Table, 
  Badge, 
  Progress, 
  Modal, 
  Form, 
  Input, 
  Select, 
  Alert, 
  Timeline,
  Tabs,
  Space,
  Tooltip,
  Dropdown
} from 'antd';
import {
  PlayCircleOutlined,
  PauseCircleOutlined,
  StopOutlined,
  SettingOutlined,
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  CopyOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
  ExclamationTriangleOutlined,
  ReloadOutlined,
  EyeOutlined,
  BranchesOutlined,
  RocketOutlined
} from '@ant-design/icons';

import type { 
  CrossRoleWorkflow, 
  WorkflowExecution,
  WorkflowStage,
  WorkflowComponentProps,
  WorkflowStatus,
  WorkflowType
} from '../../types';

interface WorkflowOrchestratorProps extends WorkflowComponentProps {
  showDesigner?: boolean;
  allowEdit?: boolean;
  onWorkflowExecute?: (workflowId: string) => void;
  onWorkflowEdit?: (workflow: CrossRoleWorkflow) => void;
  onWorkflowDelete?: (workflowId: string) => void;
}

interface WorkflowTemplate {
  id: string;
  name: string;
  description: string;
  type: WorkflowType;
  category: string;
  stages: WorkflowStage[];
  estimated_duration: number;
  complexity: 'simple' | 'medium' | 'complex';
  usage_count: number;
}

const { Option } = Select;
const { TextArea } = Input;
const { TabPane } = Tabs;

export const WorkflowOrchestrator: React.FC<WorkflowOrchestratorProps> = ({
  workflowId,
  executionId,
  readOnly = false,
  onWorkflowChange,
  onExecutionUpdate,
  showDesigner = true,
  allowEdit = true,
  onWorkflowExecute,
  onWorkflowEdit,
  onWorkflowDelete,
  className,
  loading: externalLoading = false,
  ...props
}) => {
  // State management
  const [workflows, setWorkflows] = useState<CrossRoleWorkflow[]>([]);
  const [activeExecutions, setActiveExecutions] = useState<WorkflowExecution[]>([]);
  const [templates, setTemplates] = useState<WorkflowTemplate[]>([]);
  const [selectedWorkflow, setSelectedWorkflow] = useState<CrossRoleWorkflow | null>(null);
  const [selectedExecution, setSelectedExecution] = useState<WorkflowExecution | null>(null);
  const [loading, setLoading] = useState(true);
  const [modalVisible, setModalVisible] = useState(false);
  const [modalMode, setModalMode] = useState<'create' | 'edit' | 'view'>('view');
  const [activeTab, setActiveTab] = useState('workflows');
  const [form] = Form.useForm();

  useEffect(() => {
    loadWorkflowData();
  }, []);

  useEffect(() => {
    if (workflowId) {
      const workflow = workflows.find(w => w.id === workflowId);
      if (workflow) {
        setSelectedWorkflow(workflow);
      }
    }
  }, [workflowId, workflows]);

  useEffect(() => {
    if (executionId) {
      const execution = activeExecutions.find(e => e.id === executionId);
      if (execution) {
        setSelectedExecution(execution);
        if (onExecutionUpdate) {
          onExecutionUpdate(execution);
        }
      }
    }
  }, [executionId, activeExecutions, onExecutionUpdate]);

  const loadWorkflowData = async () => {
    try {
      setLoading(true);

      const [workflowData, executionData, templateData] = await Promise.all([
        fetchWorkflows(),
        fetchActiveExecutions(),
        fetchTemplates()
      ]);

      setWorkflows(workflowData);
      setActiveExecutions(executionData);
      setTemplates(templateData);
    } catch (error) {
      console.error('Failed to load workflow data:', error);
    } finally {
      setLoading(false);
    }
  };

  // Mock API functions
  const fetchWorkflows = async (): Promise<CrossRoleWorkflow[]> => {
    return [
      {
        id: 'wf-001',
        name: 'End-to-End Invoice Processing',
        description: 'Complete invoice lifecycle from ERP extraction to FIRS transmission',
        type: 'end_to_end_invoice',
        status: 'active',
        stages: [
          {
            id: 'stage-1',
            name: 'Data Extraction',
            description: 'Extract invoice data from ERP system',
            stage_type: 'data_extraction',
            role_responsible: 'si',
            required_permissions: ['si_view', 'erp_access'],
            estimated_duration: 3,
            dependencies: [],
            actions: [],
            validation_rules: [],
            error_handling: []
          },
          {
            id: 'stage-2',
            name: 'Validation',
            description: 'Validate invoice data against business rules',
            stage_type: 'validation',
            role_responsible: 'hybrid',
            required_permissions: ['validation_access'],
            estimated_duration: 2,
            dependencies: ['stage-1'],
            actions: [],
            validation_rules: [],
            error_handling: []
          },
          {
            id: 'stage-3',
            name: 'FIRS Transmission',
            description: 'Transmit validated invoice to FIRS',
            stage_type: 'transmission',
            role_responsible: 'app',
            required_permissions: ['app_view', 'firs_transmit'],
            estimated_duration: 1,
            dependencies: ['stage-2'],
            actions: [],
            validation_rules: [],
            error_handling: []
          }
        ],
        triggers: [],
        created_by: 'admin',
        created_at: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000),
        updated_at: new Date(),
        execution_history: []
      },
      {
        id: 'wf-002',
        name: 'Compliance Audit Workflow',
        description: 'Automated compliance checking across all systems',
        type: 'compliance_check',
        status: 'active',
        stages: [],
        triggers: [],
        created_by: 'admin',
        created_at: new Date(Date.now() - 14 * 24 * 60 * 60 * 1000),
        updated_at: new Date(),
        execution_history: []
      }
    ];
  };

  const fetchActiveExecutions = async (): Promise<WorkflowExecution[]> => {
    return [
      {
        id: 'exec-001',
        workflow_id: 'wf-001',
        status: 'running',
        started_at: new Date(Date.now() - 15 * 60 * 1000),
        triggered_by: 'scheduler',
        stage_executions: [
          {
            stage_id: 'stage-1',
            status: 'completed',
            started_at: new Date(Date.now() - 15 * 60 * 1000),
            completed_at: new Date(Date.now() - 12 * 60 * 1000),
            duration: 3,
            retry_count: 0
          },
          {
            stage_id: 'stage-2',
            status: 'running',
            started_at: new Date(Date.now() - 12 * 60 * 1000),
            retry_count: 0
          },
          {
            stage_id: 'stage-3',
            status: 'pending',
            retry_count: 0
          }
        ],
        metrics: {
          total_documents_processed: 150,
          successful_documents: 148,
          failed_documents: 2,
          data_volume: 2048000,
          api_calls_made: 45,
          cache_hits: 23,
          performance_score: 92.5
        }
      }
    ];
  };

  const fetchTemplates = async (): Promise<WorkflowTemplate[]> => {
    return [
      {
        id: 'tpl-001',
        name: 'Basic Invoice Processing',
        description: 'Simple end-to-end invoice processing workflow',
        type: 'end_to_end_invoice',
        category: 'Invoice Management',
        stages: [],
        estimated_duration: 6,
        complexity: 'simple',
        usage_count: 45
      },
      {
        id: 'tpl-002',
        name: 'Compliance Monitoring',
        description: 'Automated compliance checking and reporting',
        type: 'compliance_check',
        category: 'Compliance',
        stages: [],
        estimated_duration: 10,
        complexity: 'medium',
        usage_count: 23
      }
    ];
  };

  const handleWorkflowAction = useCallback(async (action: string, workflow: CrossRoleWorkflow) => {
    switch (action) {
      case 'execute':
        if (onWorkflowExecute) {
          onWorkflowExecute(workflow.id);
        }
        break;
      case 'edit':
        setSelectedWorkflow(workflow);
        setModalMode('edit');
        setModalVisible(true);
        form.setFieldsValue(workflow);
        break;
      case 'view':
        setSelectedWorkflow(workflow);
        setModalMode('view');
        setModalVisible(true);
        break;
      case 'delete':
        Modal.confirm({
          title: 'Delete Workflow',
          content: `Are you sure you want to delete "${workflow.name}"?`,
          onOk: () => {
            if (onWorkflowDelete) {
              onWorkflowDelete(workflow.id);
            }
          }
        });
        break;
      default:
        console.log(`Action ${action} not implemented`);
    }
  }, [onWorkflowExecute, onWorkflowDelete, form]);

  const handleCreateWorkflow = () => {
    setSelectedWorkflow(null);
    setModalMode('create');
    setModalVisible(true);
    form.resetFields();
  };

  const handleModalOk = async () => {
    if (modalMode === 'view') {
      setModalVisible(false);
      return;
    }

    try {
      const values = await form.validateFields();
      
      if (modalMode === 'create') {
        const newWorkflow: CrossRoleWorkflow = {
          id: `wf-${Date.now()}`,
          name: values.name,
          description: values.description,
          type: values.type,
          status: 'draft',
          stages: [],
          triggers: [],
          created_by: 'current_user',
          created_at: new Date(),
          updated_at: new Date(),
          execution_history: []
        };
        
        setWorkflows(prev => [...prev, newWorkflow]);
        
        if (onWorkflowChange) {
          onWorkflowChange(newWorkflow);
        }
      } else if (modalMode === 'edit' && selectedWorkflow) {
        const updatedWorkflow = {
          ...selectedWorkflow,
          ...values,
          updated_at: new Date()
        };
        
        setWorkflows(prev => prev.map(w => w.id === selectedWorkflow.id ? updatedWorkflow : w));
        
        if (onWorkflowChange) {
          onWorkflowChange(updatedWorkflow);
        }
        
        if (onWorkflowEdit) {
          onWorkflowEdit(updatedWorkflow);
        }
      }
      
      setModalVisible(false);
    } catch (error) {
      console.error('Failed to save workflow:', error);
    }
  };

  const getStatusColor = (status: WorkflowStatus): string => {
    switch (status) {
      case 'active': return 'success';
      case 'paused': return 'warning';
      case 'failed': return 'error';
      case 'completed': return 'success';
      case 'draft': return 'default';
      default: return 'processing';
    }
  };

  const getExecutionStatusColor = (status: string): string => {
    switch (status) {
      case 'completed': return 'success';
      case 'running': return 'processing';
      case 'failed': return 'error';
      case 'paused': return 'warning';
      default: return 'default';
    }
  };

  // Table columns for workflows
  const workflowColumns = [
    {
      title: 'Workflow',
      key: 'workflow',
      render: (record: CrossRoleWorkflow) => (
        <div>
          <strong>{record.name}</strong>
          <br />
          <small style={{ color: '#666' }}>{record.description}</small>
        </div>
      )
    },
    {
      title: 'Type',
      dataIndex: 'type',
      key: 'type',
      render: (type: WorkflowType) => (
        <Badge status="processing" text={type.replace('_', ' ').toUpperCase()} />
      )
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: WorkflowStatus) => (
        <Badge status={getStatusColor(status) as any} text={status.toUpperCase()} />
      )
    },
    {
      title: 'Stages',
      dataIndex: 'stages',
      key: 'stages',
      render: (stages: WorkflowStage[]) => `${stages.length} stages`
    },
    {
      title: 'Last Updated',
      dataIndex: 'updated_at',
      key: 'updated_at',
      render: (date: Date) => date.toLocaleDateString()
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (record: CrossRoleWorkflow) => {
        const menuItems = [
          {
            key: 'execute',
            icon: <PlayCircleOutlined />,
            label: 'Execute',
            disabled: record.status !== 'active'
          },
          {
            key: 'view',
            icon: <EyeOutlined />,
            label: 'View Details'
          }
        ];

        if (allowEdit && !readOnly) {
          menuItems.push(
            {
              key: 'edit',
              icon: <EditOutlined />,
              label: 'Edit'
            },
            {
              key: 'copy',
              icon: <CopyOutlined />,
              label: 'Duplicate'
            },
            { type: 'divider' as const },
            {
              key: 'delete',
              icon: <DeleteOutlined />,
              label: 'Delete',
              danger: true
            }
          );
        }

        return (
          <Space>
            <Button
              type="primary"
              size="small"
              icon={<PlayCircleOutlined />}
              onClick={() => handleWorkflowAction('execute', record)}
              disabled={record.status !== 'active'}
            >
              Execute
            </Button>
            <Dropdown
              menu={{
                items: menuItems,
                onClick: ({ key }) => handleWorkflowAction(key, record)
              }}
              placement="bottomRight"
            >
              <Button size="small" icon={<SettingOutlined />} />
            </Dropdown>
          </Space>
        );
      }
    }
  ];

  // Table columns for executions
  const executionColumns = [
    {
      title: 'Execution',
      key: 'execution',
      render: (record: WorkflowExecution) => {
        const workflow = workflows.find(w => w.id === record.workflow_id);
        return (
          <div>
            <strong>{workflow?.name || 'Unknown Workflow'}</strong>
            <br />
            <small style={{ color: '#666' }}>ID: {record.id}</small>
          </div>
        );
      }
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Badge status={getExecutionStatusColor(status) as any} text={status.toUpperCase()} />
      )
    },
    {
      title: 'Progress',
      key: 'progress',
      render: (record: WorkflowExecution) => {
        const completed = record.stage_executions.filter(s => s.status === 'completed').length;
        const total = record.stage_executions.length;
        const percent = total > 0 ? Math.round((completed / total) * 100) : 0;
        
        return (
          <div>
            <Progress 
              percent={percent} 
              size="small"
              status={record.status === 'failed' ? 'exception' : 'active'}
            />
            <small style={{ color: '#666' }}>
              {completed}/{total} stages
            </small>
          </div>
        );
      }
    },
    {
      title: 'Started',
      dataIndex: 'started_at',
      key: 'started_at',
      render: (date: Date) => (
        <div>
          <div>{date.toLocaleTimeString()}</div>
          <small style={{ color: '#666' }}>{date.toLocaleDateString()}</small>
        </div>
      )
    },
    {
      title: 'Duration',
      key: 'duration',
      render: (record: WorkflowExecution) => {
        const duration = record.total_duration || 
          (Date.now() - record.started_at.getTime()) / 1000 / 60;
        return `${duration.toFixed(1)}m`;
      }
    },
    {
      title: 'Performance',
      key: 'performance',
      render: (record: WorkflowExecution) => (
        <Tooltip title={`${record.metrics.successful_documents}/${record.metrics.total_documents_processed} docs processed`}>
          <div style={{ color: record.metrics.performance_score > 90 ? '#52c41a' : '#faad14' }}>
            {record.metrics.performance_score.toFixed(1)}%
          </div>
        </Tooltip>
      )
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (record: WorkflowExecution) => (
        <Space>
          <Button
            size="small"
            icon={<EyeOutlined />}
            onClick={() => setSelectedExecution(record)}
          >
            View
          </Button>
          {record.status === 'running' && (
            <Button
              size="small"
              icon={<PauseCircleOutlined />}
              onClick={() => console.log('Pause execution', record.id)}
            >
              Pause
            </Button>
          )}
        </Space>
      )
    }
  ];

  if (loading || externalLoading) {
    return (
      <Card className={className} {...props}>
        <div style={{ textAlign: 'center', padding: '40px 0' }}>
          <ReloadOutlined spin style={{ fontSize: 24, marginBottom: 16 }} />
          <p>Loading workflow orchestrator...</p>
        </div>
      </Card>
    );
  }

  return (
    <div className={`workflow-orchestrator ${className || ''}`} {...props}>
      {/* Header */}
      <div style={{ marginBottom: 16 }}>
        <Row justify="space-between" align="middle">
          <Col>
            <h3 style={{ margin: 0, display: 'flex', alignItems: 'center' }}>
              <BranchesOutlined style={{ marginRight: 8, color: '#1890ff' }} />
              Workflow Orchestrator
            </h3>
            <p style={{ margin: '4px 0 0 0', color: '#666' }}>
              Design, execute, and monitor cross-role workflows
            </p>
          </Col>
          <Col>
            <Space>
              {allowEdit && !readOnly && (
                <Button
                  type="primary"
                  icon={<PlusOutlined />}
                  onClick={handleCreateWorkflow}
                >
                  Create Workflow
                </Button>
              )}
              <Button
                icon={<ReloadOutlined />}
                onClick={loadWorkflowData}
              >
                Refresh
              </Button>
            </Space>
          </Col>
        </Row>
      </div>

      {/* Main Content */}
      <Card>
        <Tabs activeKey={activeTab} onChange={setActiveTab}>
          <TabPane
            tab={
              <span>
                <SettingOutlined />
                Workflows ({workflows.length})
              </span>
            }
            key="workflows"
          >
            <Table
              columns={workflowColumns}
              dataSource={workflows}
              rowKey="id"
              pagination={{ pageSize: 10 }}
              size="middle"
            />
          </TabPane>

          <TabPane
            tab={
              <span>
                <ClockCircleOutlined />
                Active Executions ({activeExecutions.length})
              </span>
            }
            key="executions"
          >
            <Table
              columns={executionColumns}
              dataSource={activeExecutions}
              rowKey="id"
              pagination={{ pageSize: 10 }}
              size="middle"
            />
          </TabPane>

          <TabPane
            tab={
              <span>
                <RocketOutlined />
                Templates ({templates.length})
              </span>
            }
            key="templates"
          >
            <Row gutter={[16, 16]}>
              {templates.map(template => (
                <Col xs={24} md={12} lg={8} key={template.id}>
                  <Card
                    size="small"
                    title={template.name}
                    extra={
                      <Badge 
                        color={template.complexity === 'simple' ? 'green' : 
                               template.complexity === 'medium' ? 'orange' : 'red'}
                        text={template.complexity.toUpperCase()}
                      />
                    }
                    actions={[
                      <Button type="link" size="small" icon={<EyeOutlined />}>
                        Preview
                      </Button>,
                      <Button type="link" size="small" icon={<CopyOutlined />}>
                        Use Template
                      </Button>
                    ]}
                  >
                    <p style={{ marginBottom: 8, color: '#666', fontSize: 12 }}>
                      {template.description}
                    </p>
                    <div style={{ fontSize: 11, color: '#999' }}>
                      <div>Category: {template.category}</div>
                      <div>Est. Duration: {template.estimated_duration}min</div>
                      <div>Used: {template.usage_count} times</div>
                    </div>
                  </Card>
                </Col>
              ))}
            </Row>
          </TabPane>
        </Tabs>
      </Card>

      {/* Workflow Modal */}
      <Modal
        title={
          modalMode === 'create' ? 'Create New Workflow' :
          modalMode === 'edit' ? 'Edit Workflow' :
          'Workflow Details'
        }
        visible={modalVisible}
        onOk={handleModalOk}
        onCancel={() => setModalVisible(false)}
        width={800}
        footer={modalMode === 'view' ? [
          <Button key="close" onClick={() => setModalVisible(false)}>
            Close
          </Button>
        ] : undefined}
      >
        <Form form={form} layout="vertical">
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="name"
                label="Workflow Name"
                rules={[{ required: true, message: 'Please enter workflow name' }]}
              >
                <Input disabled={modalMode === 'view'} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="type"
                label="Workflow Type"
                rules={[{ required: true, message: 'Please select workflow type' }]}
              >
                <Select disabled={modalMode === 'view'}>
                  <Option value="end_to_end_invoice">End-to-End Invoice</Option>
                  <Option value="compliance_check">Compliance Check</Option>
                  <Option value="data_sync">Data Sync</Option>
                  <Option value="error_resolution">Error Resolution</Option>
                  <Option value="batch_processing">Batch Processing</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>
          
          <Form.Item
            name="description"
            label="Description"
            rules={[{ required: true, message: 'Please enter description' }]}
          >
            <TextArea rows={3} disabled={modalMode === 'view'} />
          </Form.Item>

          {modalMode === 'view' && selectedWorkflow && (
            <div>
              <h4>Workflow Stages</h4>
              <Timeline>
                {selectedWorkflow.stages.map((stage, index) => (
                  <Timeline.Item
                    key={stage.id}
                    color={stage.role_responsible === 'si' ? '#722ed1' : 
                           stage.role_responsible === 'app' ? '#1890ff' : '#13c2c2'}
                  >
                    <div>
                      <strong>{stage.name}</strong>
                      <Badge 
                        color={stage.role_responsible === 'si' ? '#722ed1' : 
                               stage.role_responsible === 'app' ? '#1890ff' : '#13c2c2'}
                        text={stage.role_responsible.toUpperCase()}
                        style={{ marginLeft: 8 }}
                      />
                    </div>
                    <div style={{ color: '#666', fontSize: 12 }}>
                      {stage.description}
                    </div>
                    <div style={{ color: '#999', fontSize: 11 }}>
                      Est. Duration: {stage.estimated_duration}min
                    </div>
                  </Timeline.Item>
                ))}
              </Timeline>
            </div>
          )}
        </Form>
      </Modal>

      {/* Execution Details Modal */}
      {selectedExecution && (
        <Modal
          title={`Execution Details - ${selectedExecution.id}`}
          visible={!!selectedExecution}
          onCancel={() => setSelectedExecution(null)}
          footer={[
            <Button key="close" onClick={() => setSelectedExecution(null)}>
              Close
            </Button>
          ]}
          width={900}
        >
          <Row gutter={16} style={{ marginBottom: 16 }}>
            <Col span={8}>
              <Statistic
                title="Status"
                value={selectedExecution.status.toUpperCase()}
                valueStyle={{ 
                  color: getExecutionStatusColor(selectedExecution.status) === 'success' ? '#52c41a' : 
                         getExecutionStatusColor(selectedExecution.status) === 'error' ? '#ff4d4f' : '#faad14'
                }}
              />
            </Col>
            <Col span={8}>
              <Statistic
                title="Performance Score"
                value={selectedExecution.metrics.performance_score}
                suffix="%"
                precision={1}
                valueStyle={{ color: selectedExecution.metrics.performance_score > 90 ? '#52c41a' : '#faad14' }}
              />
            </Col>
            <Col span={8}>
              <Statistic
                title="Documents Processed"
                value={selectedExecution.metrics.successful_documents}
                suffix={`/${selectedExecution.metrics.total_documents_processed}`}
                valueStyle={{ color: '#1890ff' }}
              />
            </Col>
          </Row>

          <h4>Stage Execution Timeline</h4>
          <Timeline>
            {selectedExecution.stage_executions.map((stageExec, index) => (
              <Timeline.Item
                key={stageExec.stage_id}
                color={
                  stageExec.status === 'completed' ? 'green' :
                  stageExec.status === 'running' ? 'blue' :
                  stageExec.status === 'failed' ? 'red' :
                  'gray'
                }
                dot={
                  stageExec.status === 'completed' ? <CheckCircleOutlined /> :
                  stageExec.status === 'running' ? <ClockCircleOutlined /> :
                  stageExec.status === 'failed' ? <ExclamationTriangleOutlined /> :
                  <ClockCircleOutlined />
                }
              >
                <div>
                  <strong>Stage {index + 1}</strong>
                  <Badge 
                    status={getExecutionStatusColor(stageExec.status) as any}
                    text={stageExec.status.toUpperCase()}
                    style={{ marginLeft: 8 }}
                  />
                </div>
                {stageExec.started_at && (
                  <div style={{ fontSize: 12, color: '#666' }}>
                    Started: {stageExec.started_at.toLocaleTimeString()}
                  </div>
                )}
                {stageExec.completed_at && stageExec.duration && (
                  <div style={{ fontSize: 12, color: '#666' }}>
                    Duration: {stageExec.duration}min
                  </div>
                )}
                {stageExec.retry_count > 0 && (
                  <div style={{ fontSize: 12, color: '#fa8c16' }}>
                    Retries: {stageExec.retry_count}
                  </div>
                )}
              </Timeline.Item>
            ))}
          </Timeline>
        </Modal>
      )}
    </div>
  );
};

export default WorkflowOrchestrator;