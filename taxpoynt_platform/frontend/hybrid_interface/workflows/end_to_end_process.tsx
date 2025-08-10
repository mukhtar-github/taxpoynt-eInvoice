/**
 * End-to-End Process Workflow (Hybrid Interface)
 * ==============================================
 * 
 * Comprehensive end-to-end business process orchestration that spans
 * both SI and APP operations, providing complete visibility and control
 * over the entire customer journey from data extraction to FIRS submission.
 * 
 * Features:
 * - Full process visualization from ERP to FIRS
 * - Real-time status tracking across all stages
 * - Cross-role handoff management
 * - Error handling and recovery workflows
 * - Performance monitoring and optimization
 * - Automated notifications and escalations
 * 
 * @author TaxPoynt Development Team
 * @version 1.0.0
 */

import React, { useState, useEffect } from 'react';
import {
  Steps,
  Card,
  Row,
  Col,
  Timeline,
  Progress,
  Alert,
  Button,
  Space,
  Badge,
  Statistic,
  Descriptions,
  Modal,
  Tabs,
  Table,
  Tag
} from 'antd';
import {
  PlayCircleOutlined,
  PauseCircleOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  ClockCircleOutlined,
  ApiOutlined,
  DatabaseOutlined,
  CloudUploadOutlined,
  FileTextOutlined,
  ShieldCheckOutlined
} from '@ant-design/icons';

const { Step } = Steps;
const { TabPane } = Tabs;

interface EndToEndProcessProps {
  processId?: string;
  organizationId: string;
  userRole: 'si' | 'app' | 'hybrid' | 'admin';
  onProcessComplete?: (result: any) => void;
}

interface ProcessStage {
  id: string;
  name: string;
  role: 'si' | 'app' | 'hybrid';
  status: 'pending' | 'in_progress' | 'completed' | 'failed' | 'skipped';
  progress: number;
  startTime?: Date;
  endTime?: Date;
  duration?: number; // seconds
  dependencies: string[];
  outputs: any[];
  errors: any[];
}

interface ProcessInstance {
  id: string;
  name: string;
  type: 'invoice_processing' | 'bulk_submission' | 'compliance_check';
  status: 'running' | 'completed' | 'failed' | 'paused';
  startTime: Date;
  endTime?: Date;
  stages: ProcessStage[];
  metadata: Record<string, any>;
}

export const EndToEndProcess: React.FC<EndToEndProcessProps> = ({
  processId,
  organizationId,
  userRole,
  onProcessComplete
}) => {
  const [currentProcess, setCurrentProcess] = useState<ProcessInstance | null>(null);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [selectedStage, setSelectedStage] = useState<ProcessStage | null>(null);
  const [refreshInterval, setRefreshInterval] = useState<NodeJS.Timeout | null>(null);

  // Sample process definition
  const sampleProcess: ProcessInstance = {
    id: processId || 'proc-001',
    name: 'ERP to FIRS E-Invoice Submission',
    type: 'invoice_processing',
    status: 'running',
    startTime: new Date(Date.now() - 5 * 60 * 1000),
    stages: [
      {
        id: 'data-extraction',
        name: 'Data Extraction from ERP',
        role: 'si',
        status: 'completed',
        progress: 100,
        startTime: new Date(Date.now() - 5 * 60 * 1000),
        endTime: new Date(Date.now() - 4 * 60 * 1000),
        duration: 60,
        dependencies: [],
        outputs: ['invoice_data.json', 'customer_data.json'],
        errors: []
      },
      {
        id: 'data-validation',
        name: 'Schema & Business Rule Validation',
        role: 'si',
        status: 'completed',
        progress: 100,
        startTime: new Date(Date.now() - 4 * 60 * 1000),
        endTime: new Date(Date.now() - 3 * 60 * 1000),
        duration: 45,
        dependencies: ['data-extraction'],
        outputs: ['validated_invoice.json'],
        errors: []
      },
      {
        id: 'ubl-transformation',
        name: 'UBL Document Generation',
        role: 'hybrid',
        status: 'completed',
        progress: 100,
        startTime: new Date(Date.now() - 3 * 60 * 1000),
        endTime: new Date(Date.now() - 2 * 60 * 1000),
        duration: 30,
        dependencies: ['data-validation'],
        outputs: ['ubl_invoice.xml'],
        errors: []
      },
      {
        id: 'irn-generation',
        name: 'IRN & QR Code Generation',
        role: 'app',
        status: 'in_progress',
        progress: 75,
        startTime: new Date(Date.now() - 2 * 60 * 1000),
        dependencies: ['ubl-transformation'],
        outputs: [],
        errors: []
      },
      {
        id: 'firs-submission',
        name: 'FIRS Secure Transmission',
        role: 'app',
        status: 'pending',
        progress: 0,
        dependencies: ['irn-generation'],
        outputs: [],
        errors: []
      },
      {
        id: 'confirmation',
        name: 'Confirmation & Archival',
        role: 'hybrid',
        status: 'pending',
        progress: 0,
        dependencies: ['firs-submission'],
        outputs: [],
        errors: []
      }
    ],
    metadata: {
      invoiceCount: 1,
      totalAmount: 150000,
      customerName: 'ABC Manufacturing Ltd'
    }
  };

  useEffect(() => {
    setCurrentProcess(sampleProcess);
    
    // Set up real-time updates
    const interval = setInterval(() => {
      updateProcessStatus();
    }, 2000);
    
    setRefreshInterval(interval);
    
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [processId]);

  const updateProcessStatus = () => {
    if (!currentProcess) return;

    // Simulate process progression
    setCurrentProcess(prev => {
      if (!prev) return prev;
      
      const updatedStages = prev.stages.map(stage => {
        if (stage.status === 'in_progress' && stage.progress < 100) {
          return {
            ...stage,
            progress: Math.min(stage.progress + 5, 100)
          };
        }
        return stage;
      });

      return {
        ...prev,
        stages: updatedStages
      };
    });
  };

  const handleStageClick = (stage: ProcessStage) => {
    setSelectedStage(stage);
    setModalVisible(true);
  };

  const handlePauseProcess = () => {
    if (currentProcess) {
      setCurrentProcess({
        ...currentProcess,
        status: 'paused'
      });
    }
  };

  const handleResumeProcess = () => {
    if (currentProcess) {
      setCurrentProcess({
        ...currentProcess,
        status: 'running'
      });
    }
  };

  const getStageIcon = (stage: ProcessStage) => {
    switch (stage.role) {
      case 'si': return <DatabaseOutlined />;
      case 'app': return <CloudUploadOutlined />;
      case 'hybrid': return <ApiOutlined />;
      default: return <FileTextOutlined />;
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': return <CheckCircleOutlined style={{ color: '#52c41a' }} />;
      case 'in_progress': return <PlayCircleOutlined style={{ color: '#1890ff' }} />;
      case 'failed': return <ExclamationCircleOutlined style={{ color: '#ff4d4f' }} />;
      case 'paused': return <PauseCircleOutlined style={{ color: '#faad14' }} />;
      default: return <ClockCircleOutlined style={{ color: '#d9d9d9' }} />;
    }
  };

  const currentStageIndex = currentProcess?.stages.findIndex(s => s.status === 'in_progress') || 0;

  if (!currentProcess) {
    return (
      <Card style={{ textAlign: 'center', padding: '48px' }}>
        <PlayCircleOutlined style={{ fontSize: '48px', color: '#d9d9d9' }} />
        <h3>No Active Process</h3>
        <p>Start a new end-to-end process to monitor its progress here.</p>
      </Card>
    );
  }

  return (
    <div>
      {/* Process Header */}
      <Card style={{ marginBottom: '24px' }}>
        <Row justify="space-between" align="middle">
          <Col>
            <div>
              <h3 style={{ margin: 0, display: 'flex', alignItems: 'center' }}>
                {getStatusIcon(currentProcess.status)}
                <span style={{ marginLeft: '8px' }}>{currentProcess.name}</span>
                <Badge 
                  status={currentProcess.status === 'running' ? 'processing' : 'default'}
                  text={currentProcess.status.toUpperCase()}
                  style={{ marginLeft: '12px' }}
                />
              </h3>
              <p style={{ margin: '4px 0 0 0', color: '#666' }}>
                Process ID: {currentProcess.id} | Started: {currentProcess.startTime.toLocaleString()}
              </p>
            </div>
          </Col>
          <Col>
            <Space>
              {currentProcess.status === 'running' ? (
                <Button icon={<PauseCircleOutlined />} onClick={handlePauseProcess}>
                  Pause
                </Button>
              ) : (
                <Button icon={<PlayCircleOutlined />} onClick={handleResumeProcess}>
                  Resume
                </Button>
              )}
              <Button icon={<FileTextOutlined />}>
                Export Log
              </Button>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* Process Overview */}
      <Row gutter={[24, 24]} style={{ marginBottom: '24px' }}>
        <Col xs={24} sm={8}>
          <Card>
            <Statistic
              title="Overall Progress"
              value={Math.round(currentProcess.stages.reduce((sum, stage) => sum + stage.progress, 0) / currentProcess.stages.length)}
              suffix="%"
              prefix={<Progress type="circle" percent={Math.round(currentProcess.stages.reduce((sum, stage) => sum + stage.progress, 0) / currentProcess.stages.length)} size={60} />}
            />
          </Card>
        </Col>
        
        <Col xs={24} sm={8}>
          <Card>
            <Statistic
              title="Processing Time"
              value={Math.round((Date.now() - currentProcess.startTime.getTime()) / 1000)}
              suffix="seconds"
              prefix={<ClockCircleOutlined />}
            />
          </Card>
        </Col>
        
        <Col xs={24} sm={8}>
          <Card>
            <Statistic
              title="Active Stage"
              value={currentProcess.stages[currentStageIndex]?.name || 'Completed'}
              prefix={getStageIcon(currentProcess.stages[currentStageIndex])}
            />
          </Card>
        </Col>
      </Row>

      {/* Process Flow */}
      <Tabs defaultActiveKey="flow">
        <TabPane tab="Process Flow" key="flow">
          <Card title="End-to-End Process Flow">
            <Steps current={currentStageIndex} size="small" direction="vertical">
              {currentProcess.stages.map((stage, index) => (
                <Step
                  key={stage.id}
                  title={
                    <div style={{ cursor: 'pointer' }} onClick={() => handleStageClick(stage)}>
                      <Space>
                        {stage.name}
                        <Tag color={
                          stage.role === 'si' ? 'blue' : 
                          stage.role === 'app' ? 'green' : 'purple'
                        }>
                          {stage.role.toUpperCase()}
                        </Tag>
                      </Space>
                    </div>
                  }
                  description={
                    <div>
                      <Progress 
                        percent={stage.progress} 
                        size="small" 
                        status={stage.status === 'failed' ? 'exception' : undefined}
                      />
                      <div style={{ marginTop: '4px', fontSize: '12px', color: '#666' }}>
                        {stage.status === 'completed' && stage.duration && 
                          `Completed in ${stage.duration}s`
                        }
                        {stage.status === 'in_progress' && 
                          'In progress...'
                        }
                        {stage.status === 'pending' && 
                          'Waiting for dependencies'
                        }
                      </div>
                    </div>
                  }
                  status={
                    stage.status === 'completed' ? 'finish' :
                    stage.status === 'in_progress' ? 'process' :
                    stage.status === 'failed' ? 'error' : 'wait'
                  }
                  icon={stage.status === 'in_progress' ? <PlayCircleOutlined /> : undefined}
                />
              ))}
            </Steps>
          </Card>
        </TabPane>

        <TabPane tab="Timeline View" key="timeline">
          <Card title="Process Timeline">
            <Timeline>
              {currentProcess.stages.map(stage => (
                <Timeline.Item
                  key={stage.id}
                  color={
                    stage.status === 'completed' ? 'green' :
                    stage.status === 'in_progress' ? 'blue' :
                    stage.status === 'failed' ? 'red' : 'gray'
                  }
                  dot={getStageIcon(stage)}
                >
                  <div>
                    <strong>{stage.name}</strong>
                    <Tag style={{ marginLeft: '8px' }} color={
                      stage.role === 'si' ? 'blue' : 
                      stage.role === 'app' ? 'green' : 'purple'
                    }>
                      {stage.role.toUpperCase()}
                    </Tag>
                    <br />
                    {stage.startTime && (
                      <span style={{ color: '#666', fontSize: '12px' }}>
                        Started: {stage.startTime.toLocaleTimeString()}
                        {stage.endTime && ` | Completed: ${stage.endTime.toLocaleTimeString()}`}
                        {stage.duration && ` (${stage.duration}s)`}
                      </span>
                    )}
                  </div>
                </Timeline.Item>
              ))}
            </Timeline>
          </Card>
        </TabPane>

        <TabPane tab="Data Flow" key="data">
          <Card title="Data Flow & Outputs">
            <Table
              size="small"
              columns={[
                {
                  title: 'Stage',
                  dataIndex: 'name',
                  key: 'name',
                  render: (name: string, record: ProcessStage) => (
                    <div>
                      <strong>{name}</strong>
                      <br />
                      <Tag color={
                        record.role === 'si' ? 'blue' : 
                        record.role === 'app' ? 'green' : 'purple'
                      }>
                        {record.role.toUpperCase()}
                      </Tag>
                    </div>
                  )
                },
                {
                  title: 'Status',
                  dataIndex: 'status',
                  key: 'status',
                  render: (status: string) => (
                    <Badge 
                      status={
                        status === 'completed' ? 'success' :
                        status === 'in_progress' ? 'processing' :
                        status === 'failed' ? 'error' : 'default'
                      }
                      text={status.replace('_', ' ').toUpperCase()}
                    />
                  )
                },
                {
                  title: 'Outputs',
                  dataIndex: 'outputs',
                  key: 'outputs',
                  render: (outputs: string[]) => (
                    <div>
                      {outputs.map(output => (
                        <Tag key={output} style={{ marginBottom: '2px' }}>
                          {output}
                        </Tag>
                      ))}
                    </div>
                  )
                },
                {
                  title: 'Errors',
                  dataIndex: 'errors',
                  key: 'errors',
                  render: (errors: any[]) => (
                    <span style={{ color: errors.length > 0 ? '#ff4d4f' : '#52c41a' }}>
                      {errors.length > 0 ? `${errors.length} errors` : 'No errors'}
                    </span>
                  )
                }
              ]}
              dataSource={currentProcess.stages}
              rowKey="id"
              pagination={false}
            />
          </Card>
        </TabPane>
      </Tabs>

      {/* Stage Details Modal */}
      <Modal
        title={`Stage Details: ${selectedStage?.name}`}
        open={modalVisible}
        onCancel={() => {
          setModalVisible(false);
          setSelectedStage(null);
        }}
        width={600}
        footer={[
          <Button key="close" onClick={() => setModalVisible(false)}>
            Close
          </Button>
        ]}
      >
        {selectedStage && (
          <div>
            <Descriptions column={2} size="small">
              <Descriptions.Item label="Role">
                <Tag color={
                  selectedStage.role === 'si' ? 'blue' : 
                  selectedStage.role === 'app' ? 'green' : 'purple'
                }>
                  {selectedStage.role.toUpperCase()}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="Status">
                <Badge 
                  status={
                    selectedStage.status === 'completed' ? 'success' :
                    selectedStage.status === 'in_progress' ? 'processing' :
                    selectedStage.status === 'failed' ? 'error' : 'default'
                  }
                  text={selectedStage.status.replace('_', ' ').toUpperCase()}
                />
              </Descriptions.Item>
              <Descriptions.Item label="Progress">
                <Progress percent={selectedStage.progress} size="small" />
              </Descriptions.Item>
              <Descriptions.Item label="Duration">
                {selectedStage.duration ? `${selectedStage.duration} seconds` : 'N/A'}
              </Descriptions.Item>
            </Descriptions>
            
            {selectedStage.outputs.length > 0 && (
              <div style={{ marginTop: '16px' }}>
                <h4>Outputs:</h4>
                <div>
                  {selectedStage.outputs.map(output => (
                    <Tag key={output}>{output}</Tag>
                  ))}
                </div>
              </div>
            )}
            
            {selectedStage.errors.length > 0 && (
              <div style={{ marginTop: '16px' }}>
                <Alert
                  type="error"
                  message="Stage Errors"
                  description={selectedStage.errors.join(', ')}
                />
              </div>
            )}
          </div>
        )}
      </Modal>
    </div>
  );
};

export default EndToEndProcess;