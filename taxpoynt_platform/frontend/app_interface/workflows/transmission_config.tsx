/**
 * Transmission Configuration Workflow Component
 * =============================================
 * 
 * Guided workflow for configuring document transmission settings
 * and queue management for Access Point Providers.
 * 
 * Features:
 * - Transmission queue configuration
 * - Priority and routing rules setup
 * - Retry and error handling policies
 * - Performance optimization settings
 * - Batch processing configuration
 * - Monitoring and alerting setup
 * 
 * @author TaxPoynt Development Team
 * @version 1.0.0
 */

import React, { useState, useEffect } from 'react';
import { 
  Steps, 
  Card, 
  Form, 
  Input, 
  Select, 
  Button, 
  Space, 
  Alert, 
  Progress, 
  Result,
  Divider,
  Typography,
  Switch,
  Slider,
  Row,
  Col,
  InputNumber,
  Table,
  Tag
} from 'antd';
import {
  SendOutlined,
  SettingOutlined,
  ThunderboltOutlined,
  CheckCircleOutlined,
  ExclamationTriangleOutlined,
  ClockCircleOutlined,
  BellOutlined,
  RocketOutlined,
  BarsOutlined
} from '@ant-design/icons';

// Import types
import type { TransmissionRule, QueueConfiguration, AlertConfiguration } from '../types';

const { Step } = Steps;
const { Option } = Select;
const { Title, Text } = Typography;

interface TransmissionConfigProps {
  onComplete?: (config: TransmissionConfiguration) => void;
  onCancel?: () => void;
  className?: string;
}

interface TransmissionConfiguration {
  queueSettings: QueueConfiguration;
  priorityRules: TransmissionRule[];
  retryPolicy: RetryPolicy;
  performanceSettings: PerformanceSettings;
  alertConfiguration: AlertConfiguration;
}

interface RetryPolicy {
  maxAttempts: number;
  backoffStrategy: 'linear' | 'exponential' | 'fixed';
  baseDelay: number;
  maxDelay: number;
  retryOnErrors: string[];
}

interface PerformanceSettings {
  maxConcurrentTransmissions: number;
  batchSize: number;
  processingTimeout: number;
  enableCompression: boolean;
  connectionPoolSize: number;
}

interface ConfigStep {
  title: string;
  description: string;
  status: 'wait' | 'process' | 'finish' | 'error';
}

export const TransmissionConfigWorkflow: React.FC<TransmissionConfigProps> = ({ 
  onComplete, 
  onCancel, 
  className 
}) => {
  // State management
  const [currentStep, setCurrentStep] = useState(0);
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [configComplete, setConfigComplete] = useState(false);
  const [configuration, setConfiguration] = useState<Partial<TransmissionConfiguration>>({});
  const [validationErrors, setValidationErrors] = useState<string[]>([]);
  const [priorityRules, setPriorityRules] = useState<TransmissionRule[]>([]);
  
  // Configuration steps
  const configSteps: ConfigStep[] = [
    {
      title: 'Queue Configuration',
      description: 'Configure transmission queue and processing settings',
      status: currentStep > 0 ? 'finish' : currentStep === 0 ? 'process' : 'wait'
    },
    {
      title: 'Priority Rules',
      description: 'Set up document priority and routing rules',
      status: currentStep > 1 ? 'finish' : currentStep === 1 ? 'process' : 'wait'
    },
    {
      title: 'Retry Policies',
      description: 'Configure error handling and retry mechanisms',
      status: currentStep > 2 ? 'finish' : currentStep === 2 ? 'process' : 'wait'
    },
    {
      title: 'Performance Settings',
      description: 'Optimize transmission performance and throughput',
      status: currentStep > 3 ? 'finish' : currentStep === 3 ? 'process' : 'wait'
    },
    {
      title: 'Alerts & Monitoring',
      description: 'Configure monitoring and alert notifications',
      status: configComplete ? 'finish' : currentStep === 4 ? 'process' : 'wait'
    }
  ];

  // Default priority rules
  const defaultPriorityRules: TransmissionRule[] = [
    {
      id: '1',
      name: 'Critical Documents',
      condition: 'documentType === "invoice" && amount > 1000000',
      priority: 1,
      description: 'High-value invoices (> ₦1M)',
      enabled: true
    },
    {
      id: '2',
      name: 'Government Clients',
      condition: 'clientType === "government"',
      priority: 2,
      description: 'Government sector documents',
      enabled: true
    },
    {
      id: '3',
      name: 'Standard Processing',
      condition: 'true',
      priority: 3,
      description: 'Default priority for all other documents',
      enabled: true
    }
  ];

  useEffect(() => {
    // Initialize form with default values
    form.setFieldsValue({
      maxQueueSize: 10000,
      maxConcurrentTransmissions: 50,
      batchSize: 100,
      processingTimeout: 30000,
      enableCompression: true,
      connectionPoolSize: 20,
      maxAttempts: 3,
      backoffStrategy: 'exponential',
      baseDelay: 1000,
      maxDelay: 60000
    });
    
    setPriorityRules(defaultPriorityRules);
  }, [form]);

  const handleNext = async () => {
    try {
      setLoading(true);
      const values = await form.validateFields();
      
      // Update configuration
      setConfiguration(prev => ({ ...prev, ...values }));
      
      // Move to next step
      setCurrentStep(prev => Math.min(prev + 1, configSteps.length - 1));
      
      setValidationErrors([]);
    } catch (error) {
      console.error('Validation failed:', error);
      setValidationErrors(['Please complete all required fields correctly.']);
    } finally {
      setLoading(false);
    }
  };

  const handlePrevious = () => {
    setCurrentStep(prev => Math.max(prev - 1, 0));
    setValidationErrors([]);
  };

  const handleComplete = async () => {
    try {
      setLoading(true);
      
      // Finalize configuration
      const finalConfig: TransmissionConfiguration = {
        queueSettings: configuration.queueSettings || {} as QueueConfiguration,
        priorityRules: priorityRules,
        retryPolicy: configuration.retryPolicy || {} as RetryPolicy,
        performanceSettings: configuration.performanceSettings || {} as PerformanceSettings,
        alertConfiguration: configuration.alertConfiguration || {} as AlertConfiguration
      };
      
      // Simulate saving configuration
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      setConfigComplete(true);
      
      if (onComplete) {
        onComplete(finalConfig);
      }
    } catch (error) {
      setValidationErrors(['Failed to save transmission configuration. Please try again.']);
    } finally {
      setLoading(false);
    }
  };

  const priorityColumns = [
    {
      title: 'Rule Name',
      dataIndex: 'name',
      key: 'name',
      render: (name: string, record: TransmissionRule) => (
        <div>
          <strong>{name}</strong>
          <br />
          <Text type="secondary" style={{ fontSize: '12px' }}>{record.description}</Text>
        </div>
      )
    },
    {
      title: 'Priority',
      dataIndex: 'priority',
      key: 'priority',
      render: (priority: number) => (
        <Tag color={priority === 1 ? 'red' : priority === 2 ? 'orange' : 'blue'}>
          Priority {priority}
        </Tag>
      )
    },
    {
      title: 'Condition',
      dataIndex: 'condition',
      key: 'condition',
      render: (condition: string) => (
        <Text code style={{ fontSize: '11px' }}>{condition}</Text>
      )
    },
    {
      title: 'Status',
      dataIndex: 'enabled',
      key: 'enabled',
      render: (enabled: boolean) => (
        <Tag color={enabled ? 'green' : 'default'}>
          {enabled ? 'Active' : 'Disabled'}
        </Tag>
      )
    }
  ];

  const renderStepContent = () => {
    switch (currentStep) {
      case 0:
        return (
          <Card title="Queue Configuration" className="config-step-card">
            <Form form={form} layout="vertical">
              <Alert
                type="info"
                message="Configure Transmission Queue"
                description="Set up your document transmission queue parameters for optimal processing."
                showIcon
                style={{ marginBottom: 24 }}
              />
              
              <Row gutter={16}>
                <Col xs={24} md={12}>
                  <Form.Item
                    name="maxQueueSize"
                    label="Maximum Queue Size"
                    rules={[{ required: true, type: 'number', min: 1000, max: 100000 }]}
                  >
                    <InputNumber
                      size="large"
                      style={{ width: '100%' }}
                      formatter={value => `${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
                      parser={value => value!.replace(/\$\s?|(,*)/g, '')}
                    />
                  </Form.Item>
                </Col>
                <Col xs={24} md={12}>
                  <Form.Item
                    name="queueType"
                    label="Queue Type"
                    rules={[{ required: true }]}
                  >
                    <Select size="large">
                      <Option value="priority">Priority Queue</Option>
                      <Option value="fifo">First In, First Out</Option>
                      <Option value="lifo">Last In, First Out</Option>
                    </Select>
                  </Form.Item>
                </Col>
              </Row>

              <Divider>Processing Settings</Divider>

              <Row gutter={16}>
                <Col xs={24} md={8}>
                  <Form.Item
                    name="processingTimeout"
                    label="Processing Timeout (ms)"
                    rules={[{ required: true, type: 'number', min: 5000, max: 300000 }]}
                  >
                    <InputNumber size="large" style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
                <Col xs={24} md={8}>
                  <Form.Item
                    name="deadLetterThreshold"
                    label="Dead Letter Threshold"
                    rules={[{ required: true, type: 'number', min: 1, max: 10 }]}
                  >
                    <InputNumber size="large" style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
                <Col xs={24} md={8}>
                  <Form.Item
                    name="cleanupInterval"
                    label="Cleanup Interval (hours)"
                    rules={[{ required: true, type: 'number', min: 1, max: 168 }]}
                  >
                    <InputNumber size="large" style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
              </Row>
            </Form>
          </Card>
        );

      case 1:
        return (
          <Card title="Priority Rules" className="config-step-card">
            <Alert
              type="info"
              message="Document Priority Configuration"
              description="Define rules to prioritize document transmission based on business requirements."
              showIcon
              style={{ marginBottom: 24 }}
            />

            <Table
              columns={priorityColumns}
              dataSource={priorityRules}
              rowKey="id"
              pagination={false}
              size="small"
              style={{ marginBottom: 24 }}
            />

            <Form form={form} layout="vertical">
              <Divider>Priority Settings</Divider>
              
              <Row gutter={16}>
                <Col xs={24} md={12}>
                  <Form.Item
                    name="enablePriorityQueue"
                    label="Enable Priority-based Processing"
                    valuePropName="checked"
                  >
                    <Switch />
                  </Form.Item>
                </Col>
                <Col xs={24} md={12}>
                  <Form.Item
                    name="priorityQueueSize"
                    label="Priority Queue Slots"
                    rules={[{ type: 'number', min: 10, max: 1000 }]}
                  >
                    <InputNumber size="large" style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
              </Row>
            </Form>
          </Card>
        );

      case 2:
        return (
          <Card title="Retry Policies" className="config-step-card">
            <Form form={form} layout="vertical">
              <Alert
                type="warning"
                message="Configure Error Handling"
                description="Set up retry mechanisms for failed transmissions to ensure reliable document delivery."
                showIcon
                style={{ marginBottom: 24 }}
              />

              <Row gutter={16}>
                <Col xs={24} md={12}>
                  <Form.Item
                    name="maxAttempts"
                    label="Maximum Retry Attempts"
                    rules={[{ required: true, type: 'number', min: 1, max: 10 }]}
                  >
                    <Slider
                      min={1}
                      max={10}
                      marks={{ 1: '1', 5: '5', 10: '10' }}
                      tooltip={{ formatter: value => `${value} attempts` }}
                    />
                  </Form.Item>
                </Col>
                <Col xs={24} md={12}>
                  <Form.Item
                    name="backoffStrategy"
                    label="Backoff Strategy"
                    rules={[{ required: true }]}
                  >
                    <Select size="large">
                      <Option value="linear">Linear Backoff</Option>
                      <Option value="exponential">Exponential Backoff</Option>
                      <Option value="fixed">Fixed Delay</Option>
                    </Select>
                  </Form.Item>
                </Col>
              </Row>

              <Row gutter={16}>
                <Col xs={24} md={12}>
                  <Form.Item
                    name="baseDelay"
                    label="Base Delay (ms)"
                    rules={[{ required: true, type: 'number', min: 100, max: 10000 }]}
                  >
                    <InputNumber size="large" style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
                <Col xs={24} md={12}>
                  <Form.Item
                    name="maxDelay"
                    label="Maximum Delay (ms)"
                    rules={[{ required: true, type: 'number', min: 1000, max: 300000 }]}
                  >
                    <InputNumber size="large" style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
              </Row>

              <Form.Item
                name="retryOnErrors"
                label="Retry on Error Types"
                rules={[{ required: true }]}
              >
                <Select mode="multiple" size="large" placeholder="Select error types to retry">
                  <Option value="network">Network Errors</Option>
                  <Option value="timeout">Timeout Errors</Option>
                  <Option value="rate_limit">Rate Limit Errors</Option>
                  <Option value="server_error">Server Errors (5xx)</Option>
                  <Option value="authentication">Authentication Errors</Option>
                </Select>
              </Form.Item>
            </Form>
          </Card>
        );

      case 3:
        return (
          <Card title="Performance Settings" className="config-step-card">
            <Form form={form} layout="vertical">
              <Alert
                type="success"
                message="Optimize Performance"
                description="Configure performance parameters to maximize throughput while maintaining system stability."
                showIcon
                style={{ marginBottom: 24 }}
              />

              <Row gutter={16}>
                <Col xs={24} md={12}>
                  <Form.Item
                    name="maxConcurrentTransmissions"
                    label="Max Concurrent Transmissions"
                    rules={[{ required: true, type: 'number', min: 1, max: 200 }]}
                  >
                    <Slider
                      min={1}
                      max={200}
                      marks={{ 1: '1', 50: '50', 100: '100', 200: '200' }}
                      tooltip={{ formatter: value => `${value} connections` }}
                    />
                  </Form.Item>
                </Col>
                <Col xs={24} md={12}>
                  <Form.Item
                    name="batchSize"
                    label="Batch Processing Size"
                    rules={[{ required: true, type: 'number', min: 1, max: 1000 }]}
                  >
                    <Slider
                      min={1}
                      max={1000}
                      marks={{ 1: '1', 100: '100', 500: '500', 1000: '1000' }}
                      tooltip={{ formatter: value => `${value} documents` }}
                    />
                  </Form.Item>
                </Col>
              </Row>

              <Row gutter={16}>
                <Col xs={24} md={12}>
                  <Form.Item
                    name="connectionPoolSize"
                    label="Connection Pool Size"
                    rules={[{ required: true, type: 'number', min: 5, max: 100 }]}
                  >
                    <InputNumber size="large" style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
                <Col xs={24} md={12}>
                  <Form.Item
                    name="enableCompression"
                    label="Enable Data Compression"
                    valuePropName="checked"
                  >
                    <Switch checkedChildren="ON" unCheckedChildren="OFF" />
                  </Form.Item>
                </Col>
              </Row>

              <Divider>Advanced Settings</Divider>

              <Row gutter={16}>
                <Col xs={24} md={12}>
                  <Form.Item
                    name="enableCaching"
                    label="Enable Response Caching"
                    valuePropName="checked"
                  >
                    <Switch checkedChildren="ON" unCheckedChildren="OFF" />
                  </Form.Item>
                </Col>
                <Col xs={24} md={12}>
                  <Form.Item
                    name="cacheExpiryMinutes"
                    label="Cache Expiry (minutes)"
                    rules={[{ type: 'number', min: 1, max: 1440 }]}
                  >
                    <InputNumber size="large" style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
              </Row>
            </Form>
          </Card>
        );

      case 4:
        return (
          <Card title="Alerts & Monitoring" className="config-step-card">
            <Form form={form} layout="vertical">
              <Alert
                type="info"
                message="Configure Monitoring"
                description="Set up alerts and monitoring to track transmission performance and detect issues."
                showIcon
                style={{ marginBottom: 24 }}
              />

              <Divider>Queue Alerts</Divider>
              <Row gutter={16}>
                <Col xs={24} md={12}>
                  <Form.Item
                    name="queueSizeAlert"
                    label="Queue Size Alert Threshold (%)"
                    rules={[{ type: 'number', min: 50, max: 95 }]}
                  >
                    <Slider
                      min={50}
                      max={95}
                      marks={{ 50: '50%', 75: '75%', 90: '90%', 95: '95%' }}
                    />
                  </Form.Item>
                </Col>
                <Col xs={24} md={12}>
                  <Form.Item
                    name="processingTimeAlert"
                    label="Processing Time Alert (seconds)"
                    rules={[{ type: 'number', min: 30, max: 300 }]}
                  >
                    <InputNumber size="large" style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
              </Row>

              <Divider>Error Rate Alerts</Divider>
              <Row gutter={16}>
                <Col xs={24} md={12}>
                  <Form.Item
                    name="errorRateThreshold"
                    label="Error Rate Threshold (%)"
                    rules={[{ type: 'number', min: 1, max: 50 }]}
                  >
                    <Slider
                      min={1}
                      max={50}
                      marks={{ 1: '1%', 10: '10%', 25: '25%', 50: '50%' }}
                    />
                  </Form.Item>
                </Col>
                <Col xs={24} md={12}>
                  <Form.Item
                    name="successRateThreshold"
                    label="Success Rate Alert Threshold (%)"
                    rules={[{ type: 'number', min: 50, max: 99 }]}
                  >
                    <Slider
                      min={50}
                      max={99}
                      marks={{ 85: '85%', 90: '90%', 95: '95%', 99: '99%' }}
                    />
                  </Form.Item>
                </Col>
              </Row>

              <Divider>Notification Settings</Divider>
              <Form.Item
                name="notificationChannels"
                label="Notification Channels"
                rules={[{ required: true }]}
              >
                <Select mode="multiple" size="large" placeholder="Select notification channels">
                  <Option value="email">Email</Option>
                  <Option value="sms">SMS</Option>
                  <Option value="webhook">Webhook</Option>
                  <Option value="slack">Slack</Option>
                </Select>
              </Form.Item>
            </Form>
          </Card>
        );

      default:
        return null;
    }
  };

  if (configComplete) {
    return (
      <Result
        status="success"
        title="Transmission Configuration Complete!"
        subTitle="Your transmission settings have been configured and optimized for maximum performance."
        extra={[
          <Button type="primary" key="done" onClick={onComplete}>
            Continue to Dashboard
          </Button>
        ]}
      />
    );
  }

  return (
    <div className={`transmission-config-workflow ${className || ''}`}>
      {/* Header */}
      <div style={{ marginBottom: 32 }}>
        <Title level={2}>
          <SendOutlined style={{ marginRight: 12, color: '#1890ff' }} />
          Transmission Configuration
        </Title>
        <Text type="secondary">
          Configure document transmission settings, queue management, and performance optimization
        </Text>
      </div>

      {/* Progress Steps */}
      <Card style={{ marginBottom: 24 }}>
        <Steps current={currentStep} status={validationErrors.length > 0 ? 'error' : 'process'}>
          {configSteps.map((step, index) => (
            <Step 
              key={index}
              title={step.title} 
              description={step.description}
              status={step.status}
            />
          ))}
        </Steps>
      </Card>

      {/* Error Messages */}
      {validationErrors.length > 0 && (
        <Alert
          type="error"
          message="Configuration Issues Detected"
          description={
            <ul style={{ margin: 0, paddingLeft: 20 }}>
              {validationErrors.map((error, index) => (
                <li key={index}>{error}</li>
              ))}
            </ul>
          }
          showIcon
          closable
          style={{ marginBottom: 24 }}
        />
      )}

      {/* Step Content */}
      <div style={{ marginBottom: 32 }}>
        {renderStepContent()}
      </div>

      {/* Navigation */}
      <Card>
        <div style={{ textAlign: 'center' }}>
          <Space size="large">
            {onCancel && (
              <Button size="large" onClick={onCancel}>
                Cancel Configuration
              </Button>
            )}
            
            {currentStep > 0 && (
              <Button size="large" onClick={handlePrevious}>
                Previous
              </Button>
            )}
            
            {currentStep < 4 && (
              <Button 
                type="primary" 
                size="large" 
                onClick={handleNext}
                loading={loading}
              >
                Next
              </Button>
            )}

            {currentStep === 4 && (
              <Button 
                type="primary" 
                size="large" 
                onClick={handleComplete}
                loading={loading}
                icon={<RocketOutlined />}
              >
                Complete Configuration
              </Button>
            )}
          </Space>
        </div>
      </Card>
    </div>
  );
};

export default TransmissionConfigWorkflow;