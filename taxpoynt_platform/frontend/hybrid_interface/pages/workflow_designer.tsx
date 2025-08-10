/**
 * Workflow Designer Page (Hybrid Interface)
 * =========================================
 * 
 * Visual workflow design and orchestration tool that allows users to create,
 * modify, and manage end-to-end business processes across SI and APP operations.
 * 
 * Features:
 * - Drag-and-drop workflow builder
 * - Pre-built workflow templates
 * - Cross-role process orchestration
 * - Workflow testing and validation
 * - Process automation setup
 * - Integration with SI and APP services
 * 
 * @author TaxPoynt Development Team
 * @version 1.0.0
 */

import React, { useState, useEffect } from 'react';
import {
  Layout,
  Card,
  Button,
  Space,
  Drawer,
  List,
  Typography,
  Tag,
  Modal,
  Form,
  Input,
  Select,
  Alert,
  Divider,
  Tooltip
} from 'antd';
import {
  PlusOutlined,
  PlayCircleOutlined,
  SaveOutlined,
  CopyOutlined,
  DeleteOutlined,
  SettingOutlined,
  BranchesOutlined,
  NodeIndexOutlined,
  ApiOutlined
} from '@ant-design/icons';

// Import workflow components
import { WorkflowDesigner } from '../components/workflow_orchestration/WorkflowDesigner';
import { WorkflowOrchestrator } from '../components/workflow_orchestration/WorkflowOrchestrator';

const { Sider, Content } = Layout;
const { Title, Text } = Typography;
const { Option } = Select;

interface WorkflowDesignerPageProps {
  userRole: 'si' | 'app' | 'hybrid' | 'admin';
  organizationId: string;
}

interface WorkflowTemplate {
  id: string;
  name: string;
  description: string;
  category: 'si' | 'app' | 'hybrid';
  complexity: 'simple' | 'medium' | 'complex';
  estimatedSetupTime: number; // minutes
  requiredServices: string[];
}

interface WorkflowNode {
  id: string;
  type: 'start' | 'process' | 'decision' | 'integration' | 'end';
  label: string;
  config: Record<string, any>;
}

export const WorkflowDesignerPage: React.FC<WorkflowDesignerPageProps> = ({
  userRole,
  organizationId
}) => {
  const [sidebarVisible, setSidebarVisible] = useState(true);
  const [templatesDrawerVisible, setTemplatesDrawerVisible] = useState(false);
  const [currentWorkflow, setCurrentWorkflow] = useState<any>(null);
  const [workflowNodes, setWorkflowNodes] = useState<WorkflowNode[]>([]);
  const [isPreviewMode, setIsPreviewMode] = useState(false);
  const [saveModalVisible, setSaveModalVisible] = useState(false);

  // Predefined workflow templates
  const workflowTemplates: WorkflowTemplate[] = [
    {
      id: 'erp-to-firs',
      name: 'ERP to FIRS E-Invoice',
      description: 'Extract invoice data from ERP system and submit to FIRS',
      category: 'hybrid',
      complexity: 'medium',
      estimatedSetupTime: 15,
      requiredServices: ['ERP Connector', 'Data Validator', 'FIRS Submitter']
    },
    {
      id: 'bulk-validation',
      name: 'Bulk Document Validation',
      description: 'Validate multiple documents against UBL and Nigerian standards',
      category: 'si',
      complexity: 'simple',
      estimatedSetupTime: 10,
      requiredServices: ['UBL Validator', 'Schema Checker']
    },
    {
      id: 'compliance-monitoring',
      name: 'Automated Compliance Monitoring',
      description: 'Monitor platform compliance across all FIRS-mandated standards',
      category: 'app',
      complexity: 'complex',
      estimatedSetupTime: 30,
      requiredServices: ['Compliance Engine', 'Alert System', 'Reporting Service']
    },
    {
      id: 'customer-onboarding',
      name: 'Customer Onboarding Flow',
      description: 'Complete customer registration and setup process',
      category: 'hybrid',
      complexity: 'medium',
      estimatedSetupTime: 20,
      requiredServices: ['Authentication', 'Registration Service', 'Notification Service']
    }
  ];

  const availableNodes = [
    { type: 'start', label: 'Start Process', icon: <PlayCircleOutlined /> },
    { type: 'process', label: 'Data Processing', icon: <ApiOutlined /> },
    { type: 'decision', label: 'Decision Point', icon: <BranchesOutlined /> },
    { type: 'integration', label: 'Service Integration', icon: <NodeIndexOutlined /> },
    { type: 'end', label: 'End Process', icon: <SaveOutlined /> }
  ];

  const handleTemplateSelect = (template: WorkflowTemplate) => {
    setCurrentWorkflow({
      id: `workflow-${Date.now()}`,
      name: template.name,
      description: template.description,
      category: template.category,
      nodes: generateTemplateNodes(template),
      connections: []
    });
    setTemplatesDrawerVisible(false);
  };

  const generateTemplateNodes = (template: WorkflowTemplate): WorkflowNode[] => {
    // Generate basic workflow structure based on template
    const nodes: WorkflowNode[] = [
      {
        id: 'start-1',
        type: 'start',
        label: 'Start',
        config: {}
      }
    ];

    if (template.category === 'hybrid') {
      nodes.push({
        id: 'process-1',
        type: 'process',
        label: 'Data Extraction',
        config: { service: 'erp-connector' }
      });
      
      nodes.push({
        id: 'decision-1',
        type: 'decision',
        label: 'Validation Check',
        config: { conditions: ['data_valid', 'schema_compliant'] }
      });
    }

    nodes.push({
      id: 'end-1',
      type: 'end',
      label: 'Complete',
      config: {}
    });

    return nodes;
  };

  const handleSaveWorkflow = async (values: any) => {
    try {
      // Save workflow logic
      console.log('Saving workflow:', { ...currentWorkflow, ...values });
      setSaveModalVisible(false);
      // Show success message
    } catch (error) {
      console.error('Failed to save workflow:', error);
    }
  };

  const handleRunWorkflow = () => {
    if (currentWorkflow) {
      setIsPreviewMode(true);
      // Simulate workflow execution
      console.log('Running workflow:', currentWorkflow);
    }
  };

  return (
    <Layout style={{ minHeight: '100vh', background: '#f5f5f5' }}>
      {/* Sidebar with workflow tools */}
      <Sider 
        width={280} 
        style={{ background: '#fff' }}
        collapsed={!sidebarVisible}
        collapsedWidth={0}
      >
        <div style={{ padding: '16px' }}>
          <Title level={4}>Workflow Tools</Title>
          
          <Divider />
          
          <Space direction="vertical" style={{ width: '100%' }}>
            <Button 
              type="primary" 
              icon={<PlusOutlined />} 
              block
              onClick={() => setTemplatesDrawerVisible(true)}
            >
              New from Template
            </Button>
            
            <Button 
              icon={<BranchesOutlined />} 
              block
              onClick={() => setCurrentWorkflow({ 
                id: `workflow-${Date.now()}`, 
                name: 'Custom Workflow', 
                nodes: [], 
                connections: [] 
              })}
            >
              Blank Workflow
            </Button>
          </Space>
          
          <Divider />
          
          <Title level={5}>Available Nodes</Title>
          <List
            size="small"
            dataSource={availableNodes}
            renderItem={(node) => (
              <List.Item 
                style={{ 
                  padding: '8px 12px', 
                  cursor: 'pointer',
                  border: '1px solid #d9d9d9',
                  marginBottom: '8px',
                  borderRadius: '4px'
                }}
                onClick={() => {
                  // Add node to current workflow
                  console.log('Adding node:', node);
                }}
              >
                <Space>
                  {node.icon}
                  <Text>{node.label}</Text>
                </Space>
              </List.Item>
            )}
          />
        </div>
      </Sider>

      {/* Main Content Area */}
      <Layout>
        {/* Toolbar */}
        <div style={{ 
          background: '#fff', 
          padding: '12px 24px', 
          borderBottom: '1px solid #f0f0f0',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <Space>
            <Button 
              type="text"
              icon={<SettingOutlined />}
              onClick={() => setSidebarVisible(!sidebarVisible)}
            />
            <Title level={4} style={{ margin: 0 }}>
              {currentWorkflow?.name || 'Workflow Designer'}
            </Title>
          </Space>
          
          <Space>
            <Button icon={<SaveOutlined />} onClick={() => setSaveModalVisible(true)}>
              Save
            </Button>
            <Button icon={<CopyOutlined />}>
              Duplicate
            </Button>
            <Button 
              type="primary" 
              icon={<PlayCircleOutlined />}
              onClick={handleRunWorkflow}
              disabled={!currentWorkflow}
            >
              Run Workflow
            </Button>
          </Space>
        </div>

        {/* Designer Canvas */}
        <Content style={{ padding: '24px', overflow: 'hidden' }}>
          {currentWorkflow ? (
            <Card style={{ height: '100%' }}>
              {isPreviewMode ? (
                <WorkflowOrchestrator 
                  workflow={currentWorkflow}
                  onComplete={() => setIsPreviewMode(false)}
                  organizationId={organizationId}
                />
              ) : (
                <WorkflowDesigner
                  workflow={currentWorkflow}
                  onChange={setCurrentWorkflow}
                  availableServices={['ERP Connector', 'FIRS Submitter', 'Data Validator']}
                  userRole={userRole}
                />
              )}
            </Card>
          ) : (
            <Card style={{ textAlign: 'center', height: '100%' }}>
              <div style={{ paddingTop: '10%' }}>
                <BranchesOutlined style={{ fontSize: '64px', color: '#d9d9d9', marginBottom: '24px' }} />
                <Title level={3} style={{ color: '#999' }}>Welcome to Workflow Designer</Title>
                <Text style={{ fontSize: '16px', color: '#666' }}>
                  Create a new workflow from a template or start with a blank canvas
                </Text>
                <div style={{ marginTop: '24px' }}>
                  <Space>
                    <Button 
                      type="primary" 
                      size="large"
                      icon={<PlusOutlined />}
                      onClick={() => setTemplatesDrawerVisible(true)}
                    >
                      Choose Template
                    </Button>
                    <Button 
                      size="large"
                      icon={<BranchesOutlined />}
                      onClick={() => setCurrentWorkflow({ 
                        id: `workflow-${Date.now()}`, 
                        name: 'Custom Workflow', 
                        nodes: [], 
                        connections: [] 
                      })}
                    >
                      Start from Scratch
                    </Button>
                  </Space>
                </div>
              </div>
            </Card>
          )}
        </Content>
      </Layout>

      {/* Templates Drawer */}
      <Drawer
        title="Workflow Templates"
        placement="right"
        width={400}
        open={templatesDrawerVisible}
        onClose={() => setTemplatesDrawerVisible(false)}
      >
        <List
          dataSource={workflowTemplates}
          renderItem={(template) => (
            <List.Item
              actions={[
                <Button 
                  type="primary" 
                  size="small"
                  onClick={() => handleTemplateSelect(template)}
                >
                  Use Template
                </Button>
              ]}
            >
              <List.Item.Meta
                title={
                  <Space>
                    {template.name}
                    <Tag color={
                      template.category === 'si' ? 'blue' : 
                      template.category === 'app' ? 'green' : 'purple'
                    }>
                      {template.category.toUpperCase()}
                    </Tag>
                  </Space>
                }
                description={
                  <div>
                    <Text style={{ display: 'block', marginBottom: '8px' }}>
                      {template.description}
                    </Text>
                    <Space>
                      <Tag color={
                        template.complexity === 'simple' ? 'green' :
                        template.complexity === 'medium' ? 'orange' : 'red'
                      }>
                        {template.complexity}
                      </Tag>
                      <Text type="secondary">~{template.estimatedSetupTime} min</Text>
                    </Space>
                  </div>
                }
              />
            </List.Item>
          )}
        />
      </Drawer>

      {/* Save Workflow Modal */}
      <Modal
        title="Save Workflow"
        open={saveModalVisible}
        onCancel={() => setSaveModalVisible(false)}
        onOk={() => {
          // Trigger form submission
        }}
      >
        <Form
          layout="vertical"
          onFinish={handleSaveWorkflow}
        >
          <Form.Item
            name="name"
            label="Workflow Name"
            rules={[{ required: true, message: 'Please enter a workflow name' }]}
            initialValue={currentWorkflow?.name}
          >
            <Input placeholder="Enter workflow name" />
          </Form.Item>
          
          <Form.Item
            name="description"
            label="Description"
            initialValue={currentWorkflow?.description}
          >
            <Input.TextArea placeholder="Describe what this workflow does" />
          </Form.Item>
          
          <Form.Item
            name="category"
            label="Category"
            rules={[{ required: true, message: 'Please select a category' }]}
            initialValue={currentWorkflow?.category}
          >
            <Select placeholder="Select category">
              <Option value="si">SI Operations</Option>
              <Option value="app">APP Operations</Option>
              <Option value="hybrid">Cross-Role</Option>
            </Select>
          </Form.Item>
        </Form>
      </Modal>
    </Layout>
  );
};

export default WorkflowDesignerPage;