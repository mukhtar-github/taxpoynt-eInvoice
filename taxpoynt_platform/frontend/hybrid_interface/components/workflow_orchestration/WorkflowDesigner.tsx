/**
 * Workflow Designer Component
 * ===========================
 * 
 * Visual workflow designer that allows users to create and edit
 * cross-role workflows using a drag-and-drop interface. Supports
 * stage configuration, dependency mapping, and validation rules.
 * 
 * Features:
 * - Drag-and-drop workflow stage creation
 * - Visual dependency mapping and flow control
 * - Stage configuration and validation rules
 * - Cross-role permission management
 * - Workflow validation and testing
 * - Template creation and sharing
 * - Import/export workflow definitions
 * 
 * @author TaxPoynt Development Team
 * @version 1.0.0
 */

import React, { useState, useEffect, useRef } from 'react';
import { 
  Card, 
  Row, 
  Col, 
  Button, 
  Drawer, 
  Form, 
  Input, 
  Select, 
  Switch, 
  InputNumber,
  Space,
  Alert,
  Tabs,
  Badge,
  Tooltip,
  Modal
} from 'antd';
import {
  PlusOutlined,
  SettingOutlined,
  SaveOutlined,
  PlayCircleOutlined,
  DownloadOutlined,
  UploadOutlined,
  DeleteOutlined,
  CopyOutlined,
  LinkOutlined,
  CheckCircleOutlined,
  ExclamationTriangleOutlined
} from '@ant-design/icons';

import type { 
  CrossRoleWorkflow, 
  WorkflowStage, 
  WorkflowAction, 
  ErrorHandlingRule,
  WorkflowComponentProps 
} from '../../types';

interface WorkflowDesignerProps extends WorkflowComponentProps {
  workflow?: CrossRoleWorkflow;
  onSave?: (workflow: CrossRoleWorkflow) => void;
  onTest?: (workflow: CrossRoleWorkflow) => void;
  onExport?: (workflow: CrossRoleWorkflow) => void;
  templates?: WorkflowStage[];
}

interface StagePosition {
  id: string;
  x: number;
  y: number;
}

interface Connection {
  from: string;
  to: string;
}

interface ValidationResult {
  isValid: boolean;
  errors: string[];
  warnings: string[];
}

const { Option } = Select;
const { TextArea } = Input;
const { TabPane } = Tabs;

const STAGE_TEMPLATES: WorkflowStage[] = [
  {
    id: 'template-extraction',
    name: 'Data Extraction',
    description: 'Extract data from source systems',
    stage_type: 'data_extraction',
    role_responsible: 'si',
    required_permissions: ['si_view', 'data_access'],
    estimated_duration: 3,
    dependencies: [],
    actions: [],
    validation_rules: [],
    error_handling: []
  },
  {
    id: 'template-validation',
    name: 'Data Validation',
    description: 'Validate extracted data against business rules',
    stage_type: 'validation',
    role_responsible: 'hybrid',
    required_permissions: ['validation_access'],
    estimated_duration: 2,
    dependencies: [],
    actions: [],
    validation_rules: [],
    error_handling: []
  },
  {
    id: 'template-transformation',
    name: 'Data Transformation',
    description: 'Transform data to required format',
    stage_type: 'transformation',
    role_responsible: 'si',
    required_permissions: ['si_manage'],
    estimated_duration: 1,
    dependencies: [],
    actions: [],
    validation_rules: [],
    error_handling: []
  },
  {
    id: 'template-transmission',
    name: 'FIRS Transmission',
    description: 'Transmit data to FIRS',
    stage_type: 'transmission',
    role_responsible: 'app',
    required_permissions: ['app_manage', 'firs_transmit'],
    estimated_duration: 2,
    dependencies: [],
    actions: [],
    validation_rules: [],
    error_handling: []
  }
];

export const WorkflowDesigner: React.FC<WorkflowDesignerProps> = ({
  workflow,
  onSave,
  onTest,
  onExport,
  templates = STAGE_TEMPLATES,
  className,
  ...props
}) => {
  // State management
  const [designerWorkflow, setDesignerWorkflow] = useState<CrossRoleWorkflow | null>(workflow || null);
  const [stages, setStages] = useState<WorkflowStage[]>([]);
  const [stagePositions, setStagePositions] = useState<StagePosition[]>([]);
  const [connections, setConnections] = useState<Connection[]>([]);
  const [selectedStage, setSelectedStage] = useState<WorkflowStage | null>(null);
  const [drawerVisible, setDrawerVisible] = useState(false);
  const [validation, setValidation] = useState<ValidationResult>({ isValid: true, errors: [], warnings: [] });
  const [form] = Form.useForm();
  const canvasRef = useRef<HTMLDivElement>(null);

  // Initialize designer with workflow data
  useEffect(() => {
    if (workflow) {
      setDesignerWorkflow(workflow);
      setStages(workflow.stages);
      
      // Initialize positions for existing stages
      const positions = workflow.stages.map((stage, index) => ({
        id: stage.id,
        x: 100 + (index % 3) * 250,
        y: 100 + Math.floor(index / 3) * 150
      }));
      setStagePositions(positions);

      // Initialize connections based on dependencies
      const conns: Connection[] = [];
      workflow.stages.forEach(stage => {
        stage.dependencies.forEach(depId => {
          conns.push({ from: depId, to: stage.id });
        });
      });
      setConnections(conns);
    }
  }, [workflow]);

  // Validate workflow whenever stages or connections change
  useEffect(() => {
    validateWorkflow();
  }, [stages, connections]);

  const validateWorkflow = () => {
    const errors: string[] = [];
    const warnings: string[] = [];

    // Check for isolated stages
    const connectedStages = new Set();
    connections.forEach(conn => {
      connectedStages.add(conn.from);
      connectedStages.add(conn.to);
    });

    if (stages.length > 1) {
      const isolatedStages = stages.filter(stage => !connectedStages.has(stage.id));
      if (isolatedStages.length > 0) {
        warnings.push(`${isolatedStages.length} stages are not connected to the workflow`);
      }
    }

    // Check for circular dependencies
    const hasCycle = checkForCycles(stages, connections);
    if (hasCycle) {
      errors.push('Workflow contains circular dependencies');
    }

    // Check for missing required permissions
    stages.forEach(stage => {
      if (stage.required_permissions.length === 0) {
        warnings.push(`Stage "${stage.name}" has no required permissions defined`);
      }
    });

    // Check for unrealistic durations
    stages.forEach(stage => {
      if (stage.estimated_duration > 60) {
        warnings.push(`Stage "${stage.name}" has a very long estimated duration (${stage.estimated_duration}min)`);
      }
    });

    setValidation({
      isValid: errors.length === 0,
      errors,
      warnings
    });
  };

  const checkForCycles = (stages: WorkflowStage[], connections: Connection[]): boolean => {
    const visited = new Set<string>();
    const recursionStack = new Set<string>();

    const hasCycleDFS = (stageId: string): boolean => {
      visited.add(stageId);
      recursionStack.add(stageId);

      const outgoingConnections = connections.filter(conn => conn.from === stageId);
      for (const conn of outgoingConnections) {
        if (!visited.has(conn.to)) {
          if (hasCycleDFS(conn.to)) return true;
        } else if (recursionStack.has(conn.to)) {
          return true;
        }
      }

      recursionStack.delete(stageId);
      return false;
    };

    for (const stage of stages) {
      if (!visited.has(stage.id)) {
        if (hasCycleDFS(stage.id)) return true;
      }
    }

    return false;
  };

  const addStage = (template: WorkflowStage) => {
    const newStage: WorkflowStage = {
      ...template,
      id: `stage-${Date.now()}`,
      name: `${template.name} ${stages.length + 1}`,
      dependencies: []
    };

    setStages(prev => [...prev, newStage]);
    
    // Position the new stage
    const newPosition: StagePosition = {
      id: newStage.id,
      x: 100 + (stages.length % 3) * 250,
      y: 100 + Math.floor(stages.length / 3) * 150
    };
    setStagePositions(prev => [...prev, newPosition]);
  };

  const editStage = (stage: WorkflowStage) => {
    setSelectedStage(stage);
    form.setFieldsValue({
      ...stage,
      required_permissions: stage.required_permissions.join(',')
    });
    setDrawerVisible(true);
  };

  const saveStageChanges = async () => {
    try {
      const values = await form.validateFields();
      
      if (selectedStage) {
        const updatedStage: WorkflowStage = {
          ...selectedStage,
          ...values,
          required_permissions: values.required_permissions ? values.required_permissions.split(',').map((p: string) => p.trim()) : []
        };

        setStages(prev => prev.map(s => s.id === selectedStage.id ? updatedStage : s));
        setDrawerVisible(false);
        setSelectedStage(null);
        form.resetFields();
      }
    } catch (error) {
      console.error('Failed to save stage changes:', error);
    }
  };

  const deleteStage = (stageId: string) => {
    Modal.confirm({
      title: 'Delete Stage',
      content: 'Are you sure you want to delete this stage?',
      onOk: () => {
        setStages(prev => prev.filter(s => s.id !== stageId));
        setStagePositions(prev => prev.filter(p => p.id !== stageId));
        setConnections(prev => prev.filter(c => c.from !== stageId && c.to !== stageId));
      }
    });
  };

  const addConnection = (fromId: string, toId: string) => {
    const newConnection = { from: fromId, to: toId };
    setConnections(prev => [...prev, newConnection]);

    // Update dependencies in the target stage
    setStages(prev => prev.map(stage => {
      if (stage.id === toId) {
        return {
          ...stage,
          dependencies: [...stage.dependencies, fromId]
        };
      }
      return stage;
    }));
  };

  const removeConnection = (fromId: string, toId: string) => {
    setConnections(prev => prev.filter(c => !(c.from === fromId && c.to === toId)));

    // Remove dependency from target stage
    setStages(prev => prev.map(stage => {
      if (stage.id === toId) {
        return {
          ...stage,
          dependencies: stage.dependencies.filter(dep => dep !== fromId)
        };
      }
      return stage;
    }));
  };

  const saveWorkflow = () => {
    if (!designerWorkflow) return;

    const updatedWorkflow: CrossRoleWorkflow = {
      ...designerWorkflow,
      stages,
      updated_at: new Date()
    };

    setDesignerWorkflow(updatedWorkflow);
    
    if (onSave) {
      onSave(updatedWorkflow);
    }
  };

  const testWorkflow = () => {
    if (!designerWorkflow) return;

    const workflowToTest: CrossRoleWorkflow = {
      ...designerWorkflow,
      stages
    };

    if (onTest) {
      onTest(workflowToTest);
    }
  };

  const exportWorkflow = () => {
    if (!designerWorkflow) return;

    const workflowToExport: CrossRoleWorkflow = {
      ...designerWorkflow,
      stages
    };

    if (onExport) {
      onExport(workflowToExport);
    }
  };

  const getRoleColor = (role: string): string => {
    switch (role) {
      case 'si': return '#722ed1';
      case 'app': return '#1890ff';
      case 'hybrid': return '#13c2c2';
      default: return '#666';
    }
  };

  const renderStage = (stage: WorkflowStage) => {
    const position = stagePositions.find(p => p.id === stage.id);
    if (!position) return null;

    return (
      <div
        key={stage.id}
        style={{
          position: 'absolute',
          left: position.x,
          top: position.y,
          width: 200,
          cursor: 'move'
        }}
        onClick={() => editStage(stage)}
      >
        <Card
          size="small"
          title={
            <div style={{ display: 'flex', alignItems: 'center', fontSize: 12 }}>
              <span style={{ marginRight: 4 }}>{stage.name}</span>
              <Badge 
                color={getRoleColor(stage.role_responsible)}
                text={stage.role_responsible.toUpperCase()}
                style={{ fontSize: 10 }}
              />
            </div>
          }
          extra={
            <Space>
              <Tooltip title="Edit Stage">
                <Button
                  type="text"
                  size="small"
                  icon={<SettingOutlined />}
                  onClick={(e) => {
                    e.stopPropagation();
                    editStage(stage);
                  }}
                />
              </Tooltip>
              <Tooltip title="Delete Stage">
                <Button
                  type="text"
                  size="small"
                  danger
                  icon={<DeleteOutlined />}
                  onClick={(e) => {
                    e.stopPropagation();
                    deleteStage(stage.id);
                  }}
                />
              </Tooltip>
            </Space>
          }
          style={{
            border: `2px solid ${getRoleColor(stage.role_responsible)}`,
            borderRadius: 8
          }}
        >
          <div style={{ fontSize: 11, color: '#666' }}>
            <div>{stage.description}</div>
            <div style={{ marginTop: 4 }}>
              Duration: {stage.estimated_duration}min
            </div>
            {stage.dependencies.length > 0 && (
              <div>
                Dependencies: {stage.dependencies.length}
              </div>
            )}
          </div>
        </Card>
      </div>
    );
  };

  return (
    <div className={`workflow-designer ${className || ''}`} {...props}>
      {/* Header */}
      <div style={{ marginBottom: 16 }}>
        <Row justify="space-between" align="middle">
          <Col>
            <h3 style={{ margin: 0 }}>Workflow Designer</h3>
            <p style={{ margin: '4px 0 0 0', color: '#666' }}>
              Design cross-role workflows with drag-and-drop interface
            </p>
          </Col>
          <Col>
            <Space>
              <Button
                icon={<SaveOutlined />}
                type="primary"
                onClick={saveWorkflow}
                disabled={!validation.isValid}
              >
                Save
              </Button>
              <Button
                icon={<PlayCircleOutlined />}
                onClick={testWorkflow}
                disabled={!validation.isValid}
              >
                Test
              </Button>
              <Button
                icon={<DownloadOutlined />}
                onClick={exportWorkflow}
              >
                Export
              </Button>
            </Space>
          </Col>
        </Row>
      </div>

      {/* Validation Status */}
      {(!validation.isValid || validation.warnings.length > 0) && (
        <div style={{ marginBottom: 16 }}>
          {validation.errors.map((error, index) => (
            <Alert
              key={`error-${index}`}
              type="error"
              message={error}
              style={{ marginBottom: 4 }}
              size="small"
            />
          ))}
          {validation.warnings.map((warning, index) => (
            <Alert
              key={`warning-${index}`}
              type="warning"
              message={warning}
              style={{ marginBottom: 4 }}
              size="small"
            />
          ))}
        </div>
      )}

      <Row gutter={16}>
        {/* Stage Templates Panel */}
        <Col span={6}>
          <Card title="Stage Templates" size="small">
            <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
              {templates.map(template => (
                <Card
                  key={template.id}
                  size="small"
                  hoverable
                  style={{ 
                    marginBottom: 8, 
                    cursor: 'pointer',
                    border: `1px solid ${getRoleColor(template.role_responsible)}`
                  }}
                  onClick={() => addStage(template)}
                >
                  <div style={{ fontSize: 12 }}>
                    <div style={{ fontWeight: 'bold', marginBottom: 4 }}>
                      {template.name}
                    </div>
                    <Badge 
                      color={getRoleColor(template.role_responsible)}
                      text={template.role_responsible.toUpperCase()}
                      style={{ fontSize: 10 }}
                    />
                    <div style={{ color: '#666', marginTop: 4 }}>
                      {template.description}
                    </div>
                  </div>
                </Card>
              ))}
            </div>
            
            <Button
              type="dashed"
              block
              icon={<PlusOutlined />}
              style={{ marginTop: 8 }}
            >
              Custom Stage
            </Button>
          </Card>
        </Col>

        {/* Design Canvas */}
        <Col span={18}>
          <Card 
            title="Workflow Canvas" 
            size="small"
            style={{ height: '600px' }}
          >
            <div
              ref={canvasRef}
              style={{
                position: 'relative',
                width: '100%',
                height: '550px',
                border: '1px dashed #d9d9d9',
                borderRadius: 4,
                overflow: 'auto',
                backgroundColor: '#fafafa'
              }}
            >
              {stages.length === 0 ? (
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  height: '100%',
                  color: '#999',
                  fontSize: 16
                }}>
                  Drag stage templates here to start building your workflow
                </div>
              ) : (
                stages.map(renderStage)
              )}

              {/* Render connections */}
              <svg
                style={{
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  width: '100%',
                  height: '100%',
                  pointerEvents: 'none'
                }}
              >
                {connections.map((connection, index) => {
                  const fromPos = stagePositions.find(p => p.id === connection.from);
                  const toPos = stagePositions.find(p => p.id === connection.to);
                  
                  if (!fromPos || !toPos) return null;

                  return (
                    <line
                      key={index}
                      x1={fromPos.x + 100}
                      y1={fromPos.y + 50}
                      x2={toPos.x + 100}
                      y2={toPos.y + 50}
                      stroke="#1890ff"
                      strokeWidth={2}
                      markerEnd="url(#arrowhead)"
                    />
                  );
                })}
                
                <defs>
                  <marker
                    id="arrowhead"
                    markerWidth="10"
                    markerHeight="7"
                    refX="10"
                    refY="3.5"
                    orient="auto"
                  >
                    <polygon
                      points="0 0, 10 3.5, 0 7"
                      fill="#1890ff"
                    />
                  </marker>
                </defs>
              </svg>
            </div>
          </Card>
        </Col>
      </Row>

      {/* Stage Configuration Drawer */}
      <Drawer
        title={`Configure Stage: ${selectedStage?.name || ''}`}
        placement="right"
        width={500}
        onClose={() => setDrawerVisible(false)}
        visible={drawerVisible}
        extra={
          <Space>
            <Button onClick={() => setDrawerVisible(false)}>Cancel</Button>
            <Button type="primary" onClick={saveStageChanges}>Save</Button>
          </Space>
        }
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="name"
            label="Stage Name"
            rules={[{ required: true, message: 'Please enter stage name' }]}
          >
            <Input />
          </Form.Item>

          <Form.Item
            name="description"
            label="Description"
            rules={[{ required: true, message: 'Please enter description' }]}
          >
            <TextArea rows={3} />
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="role_responsible"
                label="Responsible Role"
                rules={[{ required: true }]}
              >
                <Select>
                  <Option value="si">System Integrator</Option>
                  <Option value="app">Access Point Provider</Option>
                  <Option value="hybrid">Hybrid User</Option>
                  <Option value="system">System Automated</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="estimated_duration"
                label="Duration (minutes)"
                rules={[{ required: true, type: 'number', min: 1 }]}
              >
                <InputNumber min={1} max={120} />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            name="required_permissions"
            label="Required Permissions (comma-separated)"
          >
            <TextArea 
              rows={2}
              placeholder="e.g., si_view, data_access, validation_manage"
            />
          </Form.Item>

          <Tabs defaultActiveKey="actions">
            <TabPane tab="Actions" key="actions">
              <Alert
                type="info"
                message="Stage Actions"
                description="Define the specific actions this stage will perform."
                style={{ marginBottom: 16 }}
              />
              <Button type="dashed" block icon={<PlusOutlined />}>
                Add Action
              </Button>
            </TabPane>

            <TabPane tab="Validation Rules" key="validation">
              <Alert
                type="info"
                message="Validation Rules"
                description="Define validation rules that must pass for this stage."
                style={{ marginBottom: 16 }}
              />
              <Button type="dashed" block icon={<PlusOutlined />}>
                Add Validation Rule
              </Button>
            </TabPane>

            <TabPane tab="Error Handling" key="errors">
              <Alert
                type="info"
                message="Error Handling"
                description="Configure how errors should be handled in this stage."
                style={{ marginBottom: 16 }}
              />
              <Button type="dashed" block icon={<PlusOutlined />}>
                Add Error Handler
              </Button>
            </TabPane>
          </Tabs>
        </Form>
      </Drawer>
    </div>
  );
};

export default WorkflowDesigner;