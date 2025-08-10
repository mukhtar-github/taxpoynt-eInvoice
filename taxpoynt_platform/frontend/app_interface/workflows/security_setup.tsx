/**
 * Security Setup Workflow Component
 * =================================
 * 
 * Guided workflow for configuring comprehensive security settings
 * and compliance measures for Access Point Providers.
 * 
 * Features:
 * - Authentication and authorization setup
 * - SSL/TLS certificate management
 * - API security configuration
 * - Audit logging and monitoring
 * - Compliance rule configuration
 * - Access control and permissions
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
  Switch,
  Slider,
  Row,
  Col,
  InputNumber,
  Table,
  Tag,
  Timeline,
  Checkbox
} from 'antd';
import {
  ShieldCheckOutlined,
  SafetyCertificateOutlined,
  KeyOutlined,
  AuditOutlined,
  LockOutlined,
  CheckCircleOutlined,
  ExclamationTriangleOutlined,
  UploadOutlined,
  UserOutlined,
  WarningOutlined,
  RocketOutlined
} from '@ant-design/icons';

// Import types
import type { SecurityRule, AccessPolicy, AuditConfiguration } from '../types';

const { Step } = Steps;
const { Option } = Select;
const { TextArea } = Input;
const { Title, Text } = Typography;

interface SecuritySetupProps {
  onComplete?: (config: SecurityConfiguration) => void;
  onCancel?: () => void;
  className?: string;
}

interface SecurityConfiguration {
  authenticationSettings: AuthenticationSettings;
  certificateSettings: CertificateSettings;
  apiSecurity: APISecuritySettings;
  auditConfiguration: AuditConfiguration;
  accessPolicies: AccessPolicy[];
  complianceRules: SecurityRule[];
}

interface AuthenticationSettings {
  method: 'oauth2' | 'jwt' | 'api_key' | 'certificate';
  tokenExpiryMinutes: number;
  enableMFA: boolean;
  passwordPolicy: PasswordPolicy;
  sessionTimeout: number;
}

interface PasswordPolicy {
  minLength: number;
  requireUppercase: boolean;
  requireLowercase: boolean;
  requireNumbers: boolean;
  requireSpecialChars: boolean;
  expiryDays: number;
}

interface CertificateSettings {
  sslCertificate: string;
  privateKey: string;
  caCertificate: string;
  certificatePassword?: string;
  autoRenewal: boolean;
  expiryNotificationDays: number;
}

interface APISecuritySettings {
  enableRateLimit: boolean;
  rateLimitPerMinute: number;
  enableIPWhitelist: boolean;
  allowedIPs: string[];
  enableRequestSigning: boolean;
  encryptionMethod: string;
}

interface SecurityStep {
  title: string;
  description: string;
  status: 'wait' | 'process' | 'finish' | 'error';
}

export const SecuritySetupWorkflow: React.FC<SecuritySetupProps> = ({ 
  onComplete, 
  onCancel, 
  className 
}) => {
  // State management
  const [currentStep, setCurrentStep] = useState(0);
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [setupComplete, setSetupComplete] = useState(false);
  const [configuration, setConfiguration] = useState<Partial<SecurityConfiguration>>({});
  const [validationErrors, setValidationErrors] = useState<string[]>([]);
  const [securityRules, setSecurityRules] = useState<SecurityRule[]>([]);
  const [securityScore, setSecurityScore] = useState(0);
  
  // Security setup steps
  const securitySteps: SecurityStep[] = [
    {
      title: 'Authentication Setup',
      description: 'Configure user authentication and authorization',
      status: currentStep > 0 ? 'finish' : currentStep === 0 ? 'process' : 'wait'
    },
    {
      title: 'Certificate Management',
      description: 'Install and configure SSL/TLS certificates',
      status: currentStep > 1 ? 'finish' : currentStep === 1 ? 'process' : 'wait'
    },
    {
      title: 'API Security',
      description: 'Configure API security and access controls',
      status: currentStep > 2 ? 'finish' : currentStep === 2 ? 'process' : 'wait'
    },
    {
      title: 'Audit & Compliance',
      description: 'Set up audit logging and compliance monitoring',
      status: currentStep > 3 ? 'finish' : currentStep === 3 ? 'process' : 'wait'
    },
    {
      title: 'Security Validation',
      description: 'Validate security configuration and generate report',
      status: setupComplete ? 'finish' : currentStep === 4 ? 'process' : 'wait'
    }
  ];

  // Default security rules
  const defaultSecurityRules: SecurityRule[] = [
    {
      id: '1',
      name: 'Strong Authentication',
      description: 'Enforce multi-factor authentication for admin users',
      category: 'authentication',
      severity: 'high',
      enabled: true,
      compliance: ['PCI-DSS', 'GDPR']
    },
    {
      id: '2',
      name: 'Data Encryption',
      description: 'Encrypt all data in transit and at rest',
      category: 'encryption',
      severity: 'critical',
      enabled: true,
      compliance: ['PCI-DSS', 'FIRS']
    },
    {
      id: '3',
      name: 'Access Logging',
      description: 'Log all API access and administrative actions',
      category: 'audit',
      severity: 'medium',
      enabled: true,
      compliance: ['FIRS', 'ISO27001']
    }
  ];

  useEffect(() => {
    // Initialize form with default values
    form.setFieldsValue({
      method: 'oauth2',
      tokenExpiryMinutes: 60,
      enableMFA: true,
      sessionTimeout: 30,
      minLength: 8,
      requireUppercase: true,
      requireLowercase: true,
      requireNumbers: true,
      requireSpecialChars: true,
      expiryDays: 90,
      autoRenewal: true,
      expiryNotificationDays: 30,
      enableRateLimit: true,
      rateLimitPerMinute: 1000,
      enableIPWhitelist: false,
      enableRequestSigning: true,
      encryptionMethod: 'AES-256-GCM'
    });
    
    setSecurityRules(defaultSecurityRules);
    calculateSecurityScore();
  }, [form]);

  const calculateSecurityScore = () => {
    // Simple security score calculation
    let score = 0;
    const formValues = form.getFieldsValue();
    
    if (formValues.enableMFA) score += 25;
    if (formValues.minLength >= 8) score += 15;
    if (formValues.enableRateLimit) score += 20;
    if (formValues.enableRequestSigning) score += 25;
    if (formValues.autoRenewal) score += 15;
    
    setSecurityScore(Math.min(score, 100));
  };

  const handleNext = async () => {
    try {
      setLoading(true);
      const values = await form.validateFields();
      
      // Update configuration
      setConfiguration(prev => ({ ...prev, ...values }));
      
      // Move to next step
      setCurrentStep(prev => Math.min(prev + 1, securitySteps.length - 1));
      
      calculateSecurityScore();
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

  const handleValidateSecurity = async () => {
    try {
      setLoading(true);
      
      // Simulate security validation
      await new Promise(resolve => setTimeout(resolve, 3000));
      
      calculateSecurityScore();
      
      if (securityScore >= 80) {
        setSetupComplete(true);
      } else {
        setValidationErrors([
          'Security score is below recommended threshold (80%).',
          'Consider enabling additional security features.',
          'Review certificate configuration and access policies.'
        ]);
      }
    } catch (error) {
      setValidationErrors(['Security validation failed. Please review your configuration.']);
    } finally {
      setLoading(false);
    }
  };

  const handleComplete = async () => {
    try {
      setLoading(true);
      
      // Finalize configuration
      const finalConfig: SecurityConfiguration = {
        authenticationSettings: configuration.authenticationSettings || {} as AuthenticationSettings,
        certificateSettings: configuration.certificateSettings || {} as CertificateSettings,
        apiSecurity: configuration.apiSecurity || {} as APISecuritySettings,
        auditConfiguration: configuration.auditConfiguration || {} as AuditConfiguration,
        accessPolicies: configuration.accessPolicies || [],
        complianceRules: securityRules
      };
      
      // Simulate saving configuration
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      if (onComplete) {
        onComplete(finalConfig);
      }
    } catch (error) {
      setValidationErrors(['Failed to save security configuration. Please try again.']);
    } finally {
      setLoading(false);
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'red';
      case 'high': return 'orange';
      case 'medium': return 'blue';
      case 'low': return 'green';
      default: return 'default';
    }
  };

  const securityRulesColumns = [
    {
      title: 'Rule',
      dataIndex: 'name',
      key: 'name',
      render: (name: string, record: SecurityRule) => (
        <div>
          <strong>{name}</strong>
          <br />
          <Text type="secondary" style={{ fontSize: '12px' }}>{record.description}</Text>
        </div>
      )
    },
    {
      title: 'Category',
      dataIndex: 'category',
      key: 'category',
      render: (category: string) => (
        <Tag color="blue">{category.toUpperCase()}</Tag>
      )
    },
    {
      title: 'Severity',
      dataIndex: 'severity',
      key: 'severity',
      render: (severity: string) => (
        <Tag color={getSeverityColor(severity)}>{severity.toUpperCase()}</Tag>
      )
    },
    {
      title: 'Compliance',
      dataIndex: 'compliance',
      key: 'compliance',
      render: (compliance: string[]) => (
        <Space>
          {compliance.map(c => (
            <Tag key={c} size="small">{c}</Tag>
          ))}
        </Space>
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
          <Card title="Authentication Setup" className="security-step-card">
            <Form form={form} layout="vertical">
              <Alert
                type="info"
                message="Configure Authentication Method"
                description="Choose secure authentication method and configure access policies."
                showIcon
                style={{ marginBottom: 24 }}
              />
              
              <Row gutter={16}>
                <Col xs={24} md={12}>
                  <Form.Item
                    name="method"
                    label="Authentication Method"
                    rules={[{ required: true }]}
                  >
                    <Select size="large">
                      <Option value="oauth2">OAuth 2.0 (Recommended)</Option>
                      <Option value="jwt">JWT Tokens</Option>
                      <Option value="api_key">API Keys</Option>
                      <Option value="certificate">Certificate-based</Option>
                    </Select>
                  </Form.Item>
                </Col>
                <Col xs={24} md={12}>
                  <Form.Item
                    name="tokenExpiryMinutes"
                    label="Token Expiry (minutes)"
                    rules={[{ required: true, type: 'number', min: 15, max: 1440 }]}
                  >
                    <InputNumber size="large" style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
              </Row>

              <Row gutter={16}>
                <Col xs={24} md={12}>
                  <Form.Item
                    name="enableMFA"
                    label="Enable Multi-Factor Authentication"
                    valuePropName="checked"
                  >
                    <Switch checkedChildren="ON" unCheckedChildren="OFF" />
                  </Form.Item>
                </Col>
                <Col xs={24} md={12}>
                  <Form.Item
                    name="sessionTimeout"
                    label="Session Timeout (minutes)"
                    rules={[{ required: true, type: 'number', min: 5, max: 120 }]}
                  >
                    <InputNumber size="large" style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
              </Row>

              <Divider>Password Policy</Divider>

              <Row gutter={16}>
                <Col xs={24} md={12}>
                  <Form.Item
                    name="minLength"
                    label="Minimum Password Length"
                    rules={[{ required: true, type: 'number', min: 6, max: 32 }]}
                  >
                    <Slider
                      min={6}
                      max={32}
                      marks={{ 6: '6', 12: '12', 20: '20', 32: '32' }}
                    />
                  </Form.Item>
                </Col>
                <Col xs={24} md={12}>
                  <Form.Item
                    name="expiryDays"
                    label="Password Expiry (days)"
                    rules={[{ required: true, type: 'number', min: 30, max: 365 }]}
                  >
                    <InputNumber size="large" style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
              </Row>

              <Row gutter={16}>
                <Col xs={12} md={6}>
                  <Form.Item name="requireUppercase" valuePropName="checked">
                    <Checkbox>Require Uppercase</Checkbox>
                  </Form.Item>
                </Col>
                <Col xs={12} md={6}>
                  <Form.Item name="requireLowercase" valuePropName="checked">
                    <Checkbox>Require Lowercase</Checkbox>
                  </Form.Item>
                </Col>
                <Col xs={12} md={6}>
                  <Form.Item name="requireNumbers" valuePropName="checked">
                    <Checkbox>Require Numbers</Checkbox>
                  </Form.Item>
                </Col>
                <Col xs={12} md={6}>
                  <Form.Item name="requireSpecialChars" valuePropName="checked">
                    <Checkbox>Special Characters</Checkbox>
                  </Form.Item>
                </Col>
              </Row>
            </Form>
          </Card>
        );

      case 1:
        return (
          <Card title="Certificate Management" className="security-step-card">
            <Alert
              type="warning"
              message="SSL Certificate Configuration"
              description="Upload and configure SSL certificates for secure communication with FIRS and clients."
              showIcon
              style={{ marginBottom: 24 }}
            />

            <Form form={form} layout="vertical">
              <Form.Item
                name="sslCertificate"
                label="SSL Certificate (.crt or .pem)"
                rules={[{ required: true, message: 'SSL certificate is required' }]}
              >
                <Upload.Dragger
                  name="certificate"
                  accept=".crt,.pem"
                  beforeUpload={() => false}
                  onChange={(info) => console.log('Certificate uploaded:', info.file)}
                >
                  <p className="ant-upload-drag-icon">
                    <SafetyCertificateOutlined />
                  </p>
                  <p className="ant-upload-text">Click or drag SSL certificate to upload</p>
                </Upload.Dragger>
              </Form.Item>

              <Form.Item
                name="privateKey"
                label="Private Key (.key)"
                rules={[{ required: true, message: 'Private key is required' }]}
              >
                <Upload.Dragger
                  name="privateKey"
                  accept=".key"
                  beforeUpload={() => false}
                  onChange={(info) => console.log('Private key uploaded:', info.file)}
                >
                  <p className="ant-upload-drag-icon">
                    <KeyOutlined />
                  </p>
                  <p className="ant-upload-text">Click or drag private key to upload</p>
                </Upload.Dragger>
              </Form.Item>

              <Row gutter={16}>
                <Col xs={24} md={12}>
                  <Form.Item
                    name="certificatePassword"
                    label="Certificate Password (if encrypted)"
                  >
                    <Input.Password size="large" placeholder="Enter password if required" />
                  </Form.Item>
                </Col>
                <Col xs={24} md={12}>
                  <Form.Item
                    name="expiryNotificationDays"
                    label="Expiry Notification (days before)"
                    rules={[{ type: 'number', min: 1, max: 90 }]}
                  >
                    <InputNumber size="large" style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
              </Row>

              <Form.Item
                name="autoRenewal"
                label="Enable Automatic Certificate Renewal"
                valuePropName="checked"
              >
                <Switch 
                  checkedChildren="ON" 
                  unCheckedChildren="OFF"
                  onChange={calculateSecurityScore}
                />
              </Form.Item>
            </Form>
          </Card>
        );

      case 2:
        return (
          <Card title="API Security Configuration" className="security-step-card">
            <Form form={form} layout="vertical">
              <Alert
                type="success"
                message="API Protection Settings"
                description="Configure rate limiting, IP restrictions, and encryption for API endpoints."
                showIcon
                style={{ marginBottom: 24 }}
              />

              <Row gutter={16}>
                <Col xs={24} md={12}>
                  <Form.Item
                    name="enableRateLimit"
                    label="Enable Rate Limiting"
                    valuePropName="checked"
                  >
                    <Switch 
                      checkedChildren="ON" 
                      unCheckedChildren="OFF"
                      onChange={calculateSecurityScore}
                    />
                  </Form.Item>
                </Col>
                <Col xs={24} md={12}>
                  <Form.Item
                    name="rateLimitPerMinute"
                    label="Rate Limit (requests/minute)"
                    rules={[{ type: 'number', min: 10, max: 10000 }]}
                  >
                    <InputNumber size="large" style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
              </Row>

              <Row gutter={16}>
                <Col xs={24} md={12}>
                  <Form.Item
                    name="enableIPWhitelist"
                    label="Enable IP Whitelist"
                    valuePropName="checked"
                  >
                    <Switch checkedChildren="ON" unCheckedChildren="OFF" />
                  </Form.Item>
                </Col>
                <Col xs={24} md={12}>
                  <Form.Item
                    name="enableRequestSigning"
                    label="Enable Request Signing"
                    valuePropName="checked"
                  >
                    <Switch 
                      checkedChildren="ON" 
                      unCheckedChildren="OFF"
                      onChange={calculateSecurityScore}
                    />
                  </Form.Item>
                </Col>
              </Row>

              <Form.Item
                name="allowedIPs"
                label="Allowed IP Addresses (one per line)"
              >
                <TextArea
                  rows={4}
                  placeholder="192.168.1.100&#10;10.0.0.0/8&#10;172.16.0.0/12"
                />
              </Form.Item>

              <Form.Item
                name="encryptionMethod"
                label="Data Encryption Method"
                rules={[{ required: true }]}
              >
                <Select size="large">
                  <Option value="AES-256-GCM">AES-256-GCM (Recommended)</Option>
                  <Option value="AES-192-GCM">AES-192-GCM</Option>
                  <Option value="ChaCha20-Poly1305">ChaCha20-Poly1305</Option>
                </Select>
              </Form.Item>
            </Form>
          </Card>
        );

      case 3:
        return (
          <Card title="Audit & Compliance Configuration" className="security-step-card">
            <Alert
              type="info"
              message="Compliance and Audit Settings"
              description="Configure audit logging, compliance rules, and monitoring for regulatory requirements."
              showIcon
              style={{ marginBottom: 24 }}
            />

            <Table
              columns={securityRulesColumns}
              dataSource={securityRules}
              rowKey="id"
              pagination={false}
              size="small"
              style={{ marginBottom: 24 }}
            />

            <Form form={form} layout="vertical">
              <Divider>Audit Configuration</Divider>

              <Row gutter={16}>
                <Col xs={24} md={12}>
                  <Form.Item
                    name="enableAuditLogging"
                    label="Enable Audit Logging"
                    valuePropName="checked"
                  >
                    <Switch checkedChildren="ON" unCheckedChildren="OFF" />
                  </Form.Item>
                </Col>
                <Col xs={24} md={12}>
                  <Form.Item
                    name="logRetentionDays"
                    label="Log Retention Period (days)"
                    rules={[{ type: 'number', min: 30, max: 2555 }]}
                  >
                    <InputNumber size="large" style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
              </Row>

              <Form.Item
                name="auditEvents"
                label="Events to Audit"
                rules={[{ required: true }]}
              >
                <Select mode="multiple" size="large" placeholder="Select events to audit">
                  <Option value="login">User Login/Logout</Option>
                  <Option value="api_access">API Access</Option>
                  <Option value="admin_actions">Administrative Actions</Option>
                  <Option value="data_access">Data Access</Option>
                  <Option value="configuration_changes">Configuration Changes</Option>
                  <Option value="security_events">Security Events</Option>
                </Select>
              </Form.Item>
            </Form>
          </Card>
        );

      case 4:
        return (
          <Card title="Security Validation" className="security-step-card">
            <div style={{ textAlign: 'center', padding: '40px 20px' }}>
              {!loading && !setupComplete ? (
                <div>
                  <ShieldCheckOutlined style={{ fontSize: 48, color: '#1890ff', marginBottom: 24 }} />
                  <Title level={3}>Validate Security Configuration</Title>
                  <div style={{ marginBottom: 24 }}>
                    <Progress 
                      type="circle" 
                      percent={securityScore}
                      format={() => `${securityScore}%`}
                      strokeColor={securityScore >= 80 ? '#52c41a' : securityScore >= 60 ? '#faad14' : '#ff4d4f'}
                    />
                  </div>
                  <Text type="secondary">
                    Current Security Score: {securityScore}% (Minimum: 80%)
                  </Text>
                  <div style={{ marginTop: 32 }}>
                    <Button 
                      type="primary" 
                      size="large"
                      icon={<ShieldCheckOutlined />}
                      onClick={handleValidateSecurity}
                    >
                      Validate Security Configuration
                    </Button>
                  </div>
                </div>
              ) : loading ? (
                <div>
                  <Progress 
                    type="circle" 
                    percent={75} 
                    status="active"
                    strokeColor="#1890ff"
                  />
                  <Title level={3} style={{ marginTop: 24 }}>Validating Security...</Title>
                  <Text type="secondary">
                    Checking certificates, policies, and compliance rules.
                  </Text>
                </div>
              ) : (
                <Result
                  status="success"
                  icon={<CheckCircleOutlined style={{ color: '#52c41a' }} />}
                  title="Security Configuration Validated!"
                  subTitle={`Security Score: ${securityScore}% - Configuration meets security requirements.`}
                  extra={[
                    <Button 
                      type="primary" 
                      key="complete" 
                      size="large" 
                      onClick={handleComplete}
                      icon={<RocketOutlined />}
                    >
                      Complete Security Setup
                    </Button>,
                    <Button key="revalidate" onClick={() => setSetupComplete(false)}>
                      Revalidate
                    </Button>
                  ]}
                />
              )}
            </div>
          </Card>
        );

      default:
        return null;
    }
  };

  if (setupComplete && !loading) {
    return (
      <Result
        status="success"
        title="Security Setup Complete!"
        subTitle="Your Access Point Provider security configuration is complete and compliant."
        extra={[
          <Button type="primary" key="done" onClick={onComplete}>
            Continue to Dashboard
          </Button>
        ]}
      />
    );
  }

  return (
    <div className={`security-setup-workflow ${className || ''}`}>
      {/* Header */}
      <div style={{ marginBottom: 32 }}>
        <Title level={2}>
          <ShieldCheckOutlined style={{ marginRight: 12, color: '#1890ff' }} />
          Security Setup
        </Title>
        <Text type="secondary">
          Configure comprehensive security settings and compliance measures for your APP
        </Text>
      </div>

      {/* Security Score Display */}
      <Card style={{ marginBottom: 24 }}>
        <Row justify="space-between" align="middle">
          <Col>
            <Text strong>Security Configuration Progress</Text>
          </Col>
          <Col>
            <Progress 
              percent={securityScore} 
              status={securityScore >= 80 ? 'success' : 'active'}
              format={() => `${securityScore}%`}
            />
          </Col>
        </Row>
      </Card>

      {/* Progress Steps */}
      <Card style={{ marginBottom: 24 }}>
        <Steps current={currentStep} status={validationErrors.length > 0 ? 'error' : 'process'}>
          {securitySteps.map((step, index) => (
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
          message="Security Configuration Issues"
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
          </Space>
        </div>
      </Card>
    </div>
  );
};

export default SecuritySetupWorkflow;