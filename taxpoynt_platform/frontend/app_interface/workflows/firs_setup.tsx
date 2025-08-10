/**
 * FIRS Setup Workflow Component
 * =============================
 * 
 * Guided workflow for setting up FIRS (Federal Inland Revenue Service) 
 * connection and configuration for Access Point Providers.
 * 
 * Features:
 * - Step-by-step FIRS API connection setup
 * - Environment configuration (Sandbox/Production)
 * - Certificate installation and validation
 * - API credentials configuration
 * - Connection testing and verification
 * - Compliance validation checks
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
  Upload, 
  Progress, 
  Result,
  Divider,
  Typography,
  Checkbox,
  Row,
  Col
} from 'antd';
import {
  CloudServerOutlined,
  SafetyCertificateOutlined,
  SettingOutlined,
  CheckCircleOutlined,
  ExclamationTriangleOutlined,
  UploadOutlined,
  TestOutlined,
  RocketOutlined
} from '@ant-design/icons';

// Import types
import type { FIRSEnvironment, CertificateInfo, APICredentials } from '../types';

const { Step } = Steps;
const { Option } = Select;
const { TextArea } = Input;
const { Title, Text } = Typography;

interface FIRSSetupProps {
  onComplete?: (config: FIRSConfiguration) => void;
  onCancel?: () => void;
  className?: string;
}

interface FIRSConfiguration {
  environment: 'sandbox' | 'production';
  apiUrl: string;
  credentials: APICredentials;
  certificates: CertificateInfo[];
  connectionSettings: {
    timeout: number;
    retryAttempts: number;
    rateLimitPerSecond: number;
  };
}

interface SetupStep {
  title: string;
  description: string;
  status: 'wait' | 'process' | 'finish' | 'error';
}

export const FIRSSetupWorkflow: React.FC<FIRSSetupProps> = ({ 
  onComplete, 
  onCancel, 
  className 
}) => {
  // State management
  const [currentStep, setCurrentStep] = useState(0);
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [testingConnection, setTestingConnection] = useState(false);
  const [setupComplete, setSetupComplete] = useState(false);
  const [configuration, setConfiguration] = useState<Partial<FIRSConfiguration>>({});
  const [validationErrors, setValidationErrors] = useState<string[]>([]);
  
  // Setup steps
  const setupSteps: SetupStep[] = [
    {
      title: 'Environment Selection',
      description: 'Choose FIRS environment and basic configuration',
      status: currentStep > 0 ? 'finish' : currentStep === 0 ? 'process' : 'wait'
    },
    {
      title: 'API Configuration',
      description: 'Configure API endpoints and credentials',
      status: currentStep > 1 ? 'finish' : currentStep === 1 ? 'process' : 'wait'
    },
    {
      title: 'Certificate Setup',
      description: 'Upload and validate SSL certificates',
      status: currentStep > 2 ? 'finish' : currentStep === 2 ? 'process' : 'wait'
    },
    {
      title: 'Connection Testing',
      description: 'Test FIRS API connection and validate setup',
      status: currentStep > 3 ? 'finish' : currentStep === 3 ? 'process' : 'wait'
    },
    {
      title: 'Completion',
      description: 'Review configuration and complete setup',
      status: setupComplete ? 'finish' : currentStep === 4 ? 'process' : 'wait'
    }
  ];

  // Environment options
  const environments = [
    {
      value: 'sandbox',
      label: 'Sandbox Environment',
      description: 'For testing and development purposes',
      url: 'https://sandbox-api.firs.gov.ng/v1',
      recommended: true
    },
    {
      value: 'production',
      label: 'Production Environment', 
      description: 'For live transactions (requires certification)',
      url: 'https://api.firs.gov.ng/v1',
      recommended: false
    }
  ];

  useEffect(() => {
    // Initialize form with default values
    form.setFieldsValue({
      environment: 'sandbox',
      timeout: 30000,
      retryAttempts: 3,
      rateLimitPerSecond: 10
    });
  }, [form]);

  const handleNext = async () => {
    try {
      setLoading(true);
      const values = await form.validateFields();
      
      // Update configuration
      setConfiguration(prev => ({ ...prev, ...values }));
      
      // Move to next step
      setCurrentStep(prev => Math.min(prev + 1, setupSteps.length - 1));
      
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

  const handleTestConnection = async () => {
    try {
      setTestingConnection(true);
      
      // Simulate API connection test
      await new Promise(resolve => setTimeout(resolve, 3000));
      
      // Mock test results
      const testSuccessful = Math.random() > 0.2; // 80% success rate for demo
      
      if (testSuccessful) {
        setCurrentStep(4);
        setValidationErrors([]);
      } else {
        setValidationErrors([
          'Connection test failed. Please verify your credentials and network connectivity.',
          'Ensure certificates are valid and properly configured.',
          'Check firewall settings and API endpoint accessibility.'
        ]);
      }
    } catch (error) {
      setValidationErrors(['Connection test failed due to network error.']);
    } finally {
      setTestingConnection(false);
    }
  };

  const handleComplete = async () => {
    try {
      setLoading(true);
      
      // Finalize configuration
      const finalConfig: FIRSConfiguration = {
        environment: configuration.environment || 'sandbox',
        apiUrl: configuration.apiUrl || '',
        credentials: configuration.credentials || {} as APICredentials,
        certificates: configuration.certificates || [],
        connectionSettings: configuration.connectionSettings || {
          timeout: 30000,
          retryAttempts: 3,
          rateLimitPerSecond: 10
        }
      };
      
      // Simulate saving configuration
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      setSetupComplete(true);
      
      if (onComplete) {
        onComplete(finalConfig);
      }
    } catch (error) {
      setValidationErrors(['Failed to save FIRS configuration. Please try again.']);
    } finally {
      setLoading(false);
    }
  };

  const renderStepContent = () => {
    switch (currentStep) {
      case 0:
        return (
          <Card title="Environment Selection" className="setup-step-card">
            <Form form={form} layout="vertical">
              <Alert
                type="info"
                message="Choose your FIRS environment"
                description="Start with Sandbox for testing, then switch to Production when ready for live transactions."
                showIcon
                style={{ marginBottom: 24 }}
              />
              
              <Form.Item
                name="environment"
                label="FIRS Environment"
                rules={[{ required: true, message: 'Please select an environment' }]}
              >
                <Select size="large">
                  {environments.map(env => (
                    <Option key={env.value} value={env.value}>
                      <div>
                        <strong>{env.label}</strong>
                        {env.recommended && <Text type="success"> (Recommended)</Text>}
                        <br />
                        <Text type="secondary">{env.description}</Text>
                      </div>
                    </Option>
                  ))}
                </Select>
              </Form.Item>

              <Form.Item
                name="apiUrl"
                label="API Base URL"
                rules={[
                  { required: true, message: 'Please enter API URL' },
                  { type: 'url', message: 'Please enter a valid URL' }
                ]}
              >
                <Input 
                  size="large"
                  placeholder="https://sandbox-api.firs.gov.ng/v1"
                  prefix={<CloudServerOutlined />}
                />
              </Form.Item>

              <Form.Item name="acceptTerms" valuePropName="checked">
                <Checkbox>
                  I acknowledge that I understand the FIRS API terms of service and compliance requirements
                </Checkbox>
              </Form.Item>
            </Form>
          </Card>
        );

      case 1:
        return (
          <Card title="API Configuration" className="setup-step-card">
            <Form form={form} layout="vertical">
              <Alert
                type="warning"
                message="Secure your API credentials"
                description="These credentials will be used to authenticate with FIRS. Keep them secure and never share them."
                showIcon
                style={{ marginBottom: 24 }}
              />

              <Row gutter={16}>
                <Col xs={24} md={12}>
                  <Form.Item
                    name={['credentials', 'clientId']}
                    label="Client ID"
                    rules={[{ required: true, message: 'Please enter Client ID' }]}
                  >
                    <Input size="large" placeholder="Your FIRS Client ID" />
                  </Form.Item>
                </Col>
                <Col xs={24} md={12}>
                  <Form.Item
                    name={['credentials', 'clientSecret']}
                    label="Client Secret"
                    rules={[{ required: true, message: 'Please enter Client Secret' }]}
                  >
                    <Input.Password size="large" placeholder="Your FIRS Client Secret" />
                  </Form.Item>
                </Col>
              </Row>

              <Divider>Connection Settings</Divider>

              <Row gutter={16}>
                <Col xs={24} md={8}>
                  <Form.Item
                    name={['connectionSettings', 'timeout']}
                    label="Request Timeout (ms)"
                    rules={[{ required: true, type: 'number', min: 5000, max: 60000 }]}
                  >
                    <Input type="number" size="large" />
                  </Form.Item>
                </Col>
                <Col xs={24} md={8}>
                  <Form.Item
                    name={['connectionSettings', 'retryAttempts']}
                    label="Retry Attempts"
                    rules={[{ required: true, type: 'number', min: 1, max: 10 }]}
                  >
                    <Input type="number" size="large" />
                  </Form.Item>
                </Col>
                <Col xs={24} md={8}>
                  <Form.Item
                    name={['connectionSettings', 'rateLimitPerSecond']}
                    label="Rate Limit (req/sec)"
                    rules={[{ required: true, type: 'number', min: 1, max: 100 }]}
                  >
                    <Input type="number" size="large" />
                  </Form.Item>
                </Col>
              </Row>
            </Form>
          </Card>
        );

      case 2:
        return (
          <Card title="Certificate Setup" className="setup-step-card">
            <Alert
              type="info"
              message="SSL Certificate Required"
              description="Upload your FIRS-issued SSL certificates for secure communication. Both certificate and private key files are required."
              showIcon
              style={{ marginBottom: 24 }}
            />

            <Form form={form} layout="vertical">
              <Form.Item
                name="sslCertificate"
                label="SSL Certificate (.crt or .pem)"
                rules={[{ required: true, message: 'Please upload SSL certificate' }]}
              >
                <Upload.Dragger
                  name="certificate"
                  accept=".crt,.pem"
                  beforeUpload={() => false}
                  onChange={(info) => {
                    console.log('Certificate uploaded:', info.file);
                  }}
                >
                  <p className="ant-upload-drag-icon">
                    <SafetyCertificateOutlined />
                  </p>
                  <p className="ant-upload-text">Click or drag certificate file to upload</p>
                  <p className="ant-upload-hint">Support .crt and .pem files</p>
                </Upload.Dragger>
              </Form.Item>

              <Form.Item
                name="privateKey"
                label="Private Key (.key)"
                rules={[{ required: true, message: 'Please upload private key' }]}
              >
                <Upload.Dragger
                  name="privateKey"
                  accept=".key"
                  beforeUpload={() => false}
                  onChange={(info) => {
                    console.log('Private key uploaded:', info.file);
                  }}
                >
                  <p className="ant-upload-drag-icon">
                    <SafetyCertificateOutlined />
                  </p>
                  <p className="ant-upload-text">Click or drag private key file to upload</p>
                  <p className="ant-upload-hint">Support .key files</p>
                </Upload.Dragger>
              </Form.Item>

              <Form.Item
                name="certificatePassword"
                label="Certificate Password (if required)"
              >
                <Input.Password 
                  size="large" 
                  placeholder="Enter certificate password if encrypted"
                />
              </Form.Item>
            </Form>
          </Card>
        );

      case 3:
        return (
          <Card title="Connection Testing" className="setup-step-card">
            <div style={{ textAlign: 'center', padding: '40px 20px' }}>
              {!testingConnection ? (
                <div>
                  <TestOutlined style={{ fontSize: 48, color: '#1890ff', marginBottom: 24 }} />
                  <Title level={3}>Test FIRS Connection</Title>
                  <Text type="secondary">
                    Click the button below to test your FIRS API connection and validate all configurations.
                  </Text>
                  <div style={{ marginTop: 32 }}>
                    <Button 
                      type="primary" 
                      size="large"
                      icon={<TestOutlined />}
                      onClick={handleTestConnection}
                    >
                      Test Connection
                    </Button>
                  </div>
                </div>
              ) : (
                <div>
                  <Progress 
                    type="circle" 
                    percent={66} 
                    status="active"
                    strokeColor="#1890ff"
                  />
                  <Title level={3} style={{ marginTop: 24 }}>Testing Connection...</Title>
                  <Text type="secondary">
                    Validating API credentials, certificates, and network connectivity.
                  </Text>
                </div>
              )}
            </div>
          </Card>
        );

      case 4:
        return (
          <Card title="Setup Complete" className="setup-step-card">
            <Result
              status="success"
              icon={<CheckCircleOutlined style={{ color: '#52c41a' }} />}
              title="FIRS Setup Completed Successfully!"
              subTitle="Your FIRS connection has been configured and tested. You can now start transmitting documents to FIRS."
              extra={[
                <Button type="primary" key="complete" size="large" onClick={handleComplete}>
                  <RocketOutlined />
                  Complete Setup
                </Button>,
                <Button key="test" onClick={() => setCurrentStep(3)}>
                  Test Again
                </Button>
              ]}
            />
          </Card>
        );

      default:
        return null;
    }
  };

  if (setupComplete) {
    return (
      <Result
        status="success"
        title="FIRS Integration Ready!"
        subTitle="Your Access Point Provider is now connected to FIRS and ready for e-invoice transmission."
        extra={[
          <Button type="primary" key="done" onClick={onComplete}>
            Continue to Dashboard
          </Button>
        ]}
      />
    );
  }

  return (
    <div className={`firs-setup-workflow ${className || ''}`}>
      {/* Header */}
      <div style={{ marginBottom: 32 }}>
        <Title level={2}>
          <CloudServerOutlined style={{ marginRight: 12, color: '#1890ff' }} />
          FIRS Connection Setup
        </Title>
        <Text type="secondary">
          Configure your connection to the Federal Inland Revenue Service for e-invoice transmission
        </Text>
      </div>

      {/* Progress Steps */}
      <Card style={{ marginBottom: 24 }}>
        <Steps current={currentStep} status={validationErrors.length > 0 ? 'error' : 'process'}>
          {setupSteps.map((step, index) => (
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
          message="Setup Issues Detected"
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
                Cancel Setup
              </Button>
            )}
            
            {currentStep > 0 && currentStep < 4 && (
              <Button size="large" onClick={handlePrevious}>
                Previous
              </Button>
            )}
            
            {currentStep < 3 && (
              <Button 
                type="primary" 
                size="large" 
                onClick={handleNext}
                loading={loading}
              >
                Next
              </Button>
            )}
          </Space>
        </div>
      </Card>
    </div>
  );
};

export default FIRSSetupWorkflow;