/**
 * APP FIRS Dashboard Page
 * =======================
 * 
 * Comprehensive FIRS interaction dashboard for Access Point Providers.
 * Manages all aspects of FIRS communication, API health, and compliance.
 * 
 * Features:
 * - FIRS API connection monitoring
 * - Environment management (Sandbox/Production)
 * - Certificate lifecycle management
 * - API rate limiting and quotas
 * - Compliance status tracking
 * - Error logging and diagnostics
 * 
 * @author TaxPoynt Development Team
 * @version 1.0.0
 */

import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Tabs, Button, Space, Statistic, Alert, Badge, Timeline, Progress } from 'antd';
import {
  CloudServerOutlined,
  SafetyCertificateOutlined,
  ApiOutlined,
  ExclamationTriangleOutlined,
  CheckCircleOutlined,
  DisconnectOutlined,
  SettingOutlined,
  ReloadOutlined,
  WarningOutlined
} from '@ant-design/icons';

// Import APP Interface components
import { FIRSConnectionManager } from '../components/firs_communication/FIRSConnectionManager';

// Import types
import type { FIRSConnectionStatus, CertificateInfo, APIQuotaInfo } from '../types';

const { TabPane } = Tabs;

interface FIRSDashboardProps {
  className?: string;
}

interface FIRSEnvironment {
  name: string;
  url: string;
  status: 'active' | 'inactive' | 'maintenance';
  lastSync: Date;
  responseTime: number;
}

interface FIRSMetrics {
  totalRequests: number;
  successfulRequests: number;
  failedRequests: number;
  averageResponseTime: number;
  uptime: number;
  lastDowntime: Date | null;
  rateLimitUsage: number;
  rateLimitRemaining: number;
}

export const FIRSDashboardPage: React.FC<FIRSDashboardProps> = ({ className }) => {
  // State management
  const [connectionStatus, setConnectionStatus] = useState<FIRSConnectionStatus | null>(null);
  const [environments, setEnvironments] = useState<FIRSEnvironment[]>([]);
  const [metrics, setMetrics] = useState<FIRSMetrics | null>(null);
  const [certificates, setCertificates] = useState<CertificateInfo[]>([]);
  const [quotaInfo, setQuotaInfo] = useState<APIQuotaInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [activeTab, setActiveTab] = useState('connection');

  // Auto-refresh functionality
  useEffect(() => {
    loadFIRSData();
    const interval = setInterval(loadFIRSData, 30000); // 30 seconds
    return () => clearInterval(interval);
  }, []);

  const loadFIRSData = async () => {
    try {
      setRefreshing(true);
      
      // Simulate API calls to FIRS communication services
      const [statusData, envData, metricsData, certData, quotaData] = await Promise.all([
        fetchConnectionStatus(),
        fetchEnvironments(),
        fetchFIRSMetrics(),
        fetchCertificates(),
        fetchQuotaInfo()
      ]);

      setConnectionStatus(statusData);
      setEnvironments(envData);
      setMetrics(metricsData);
      setCertificates(certData);
      setQuotaInfo(quotaData);
      setLoading(false);
    } catch (error) {
      console.error('Failed to load FIRS data:', error);
    } finally {
      setRefreshing(false);
    }
  };

  // Mock API functions (replace with actual API calls)
  const fetchConnectionStatus = async (): Promise<FIRSConnectionStatus> => {
    return {
      isConnected: true,
      environment: 'production',
      lastSync: new Date(),
      latency: 245,
      certificateStatus: 'valid',
      rateLimitRemaining: 4850
    };
  };

  const fetchEnvironments = async (): Promise<FIRSEnvironment[]> => {
    return [
      {
        name: 'Production',
        url: 'https://api.firs.gov.ng/v1',
        status: 'active',
        lastSync: new Date(),
        responseTime: 245
      },
      {
        name: 'Sandbox',
        url: 'https://sandbox-api.firs.gov.ng/v1',
        status: 'active',
        lastSync: new Date(Date.now() - 5000),
        responseTime: 180
      }
    ];
  };

  const fetchFIRSMetrics = async (): Promise<FIRSMetrics> => {
    return {
      totalRequests: 125420,
      successfulRequests: 123890,
      failedRequests: 1530,
      averageResponseTime: 245,
      uptime: 99.87,
      lastDowntime: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000),
      rateLimitUsage: 150,
      rateLimitRemaining: 4850
    };
  };

  const fetchCertificates = async (): Promise<CertificateInfo[]> => {
    return [
      {
        id: 'cert-prod-001',
        name: 'Production Certificate',
        type: 'SSL/TLS',
        status: 'valid',
        expiryDate: new Date(Date.now() + 90 * 24 * 60 * 60 * 1000),
        issuer: 'FIRS CA',
        environment: 'production'
      },
      {
        id: 'cert-sandbox-001',
        name: 'Sandbox Certificate',
        type: 'SSL/TLS',
        status: 'valid',
        expiryDate: new Date(Date.now() + 180 * 24 * 60 * 60 * 1000),
        issuer: 'FIRS CA',
        environment: 'sandbox'
      }
    ];
  };

  const fetchQuotaInfo = async (): Promise<APIQuotaInfo> => {
    return {
      dailyLimit: 5000,
      dailyUsed: 150,
      monthlyLimit: 150000,
      monthlyUsed: 12450,
      resetTime: new Date(Date.now() + 24 * 60 * 60 * 1000)
    };
  };

  const handleRefresh = () => {
    loadFIRSData();
  };

  const getEnvironmentStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'success';
      case 'maintenance': return 'warning';
      case 'inactive': return 'error';
      default: return 'default';
    }
  };

  const getCertificateStatusColor = (status: string) => {
    switch (status) {
      case 'valid': return 'success';
      case 'expiring': return 'warning';
      case 'expired': return 'error';
      default: return 'default';
    }
  };

  if (loading) {
    return (
      <div style={{ padding: 24, textAlign: 'center' }}>
        <CloudServerOutlined spin style={{ fontSize: 24, marginBottom: 16 }} />
        <p>Loading FIRS Dashboard...</p>
      </div>
    );
  }

  return (
    <div className={`firs-dashboard-page ${className || ''}`}>
      {/* Page Header */}
      <div style={{ marginBottom: 24 }}>
        <Row justify="space-between" align="middle">
          <Col>
            <h1 style={{ margin: 0, display: 'flex', alignItems: 'center' }}>
              <CloudServerOutlined style={{ marginRight: 12, color: '#1890ff' }} />
              FIRS Dashboard
              {refreshing && <ReloadOutlined spin style={{ marginLeft: 12, color: '#52c41a' }} />}
            </h1>
            <p style={{ margin: '4px 0 0 0', color: '#666' }}>
              Federal Inland Revenue Service integration and monitoring
            </p>
          </Col>
          <Col>
            <Space>
              <Badge 
                status={connectionStatus?.isConnected ? 'success' : 'error'}
                text={connectionStatus?.isConnected ? 'Connected' : 'Disconnected'}
              />
              <Button icon={<ReloadOutlined />} onClick={handleRefresh} loading={refreshing}>
                Refresh
              </Button>
              <Button icon={<SettingOutlined />} type="default">
                Settings
              </Button>
            </Space>
          </Col>
        </Row>
      </div>

      {/* Key Metrics Overview */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="API Uptime"
              value={metrics?.uptime}
              suffix="%"
              precision={2}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: metrics?.uptime && metrics.uptime > 99 ? '#52c41a' : '#faad14' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Success Rate"
              value={metrics ? ((metrics.successfulRequests / metrics.totalRequests) * 100) : 0}
              suffix="%"
              precision={1}
              prefix={<ApiOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Avg Response"
              value={metrics?.averageResponseTime}
              suffix="ms"
              prefix={<CloudServerOutlined />}
              valueStyle={{ color: metrics?.averageResponseTime && metrics.averageResponseTime < 500 ? '#52c41a' : '#faad14' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Rate Limit"
              value={quotaInfo ? `${quotaInfo.dailyUsed}/${quotaInfo.dailyLimit}` : '0/0'}
              prefix={<WarningOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
      </Row>

      {/* Connection Status Alerts */}
      {connectionStatus && (
        <div style={{ marginBottom: 24 }}>
          {!connectionStatus.isConnected && (
            <Alert
              type="error"
              message="FIRS Connection Lost"
              description="Unable to connect to FIRS servers. Check network connectivity and certificates."
              showIcon
              icon={<DisconnectOutlined />}
              closable
              style={{ marginBottom: 8 }}
            />
          )}
          {connectionStatus.certificateStatus !== 'valid' && (
            <Alert
              type="warning"
              message="Certificate Issue Detected"
              description="SSL certificate may be expired or invalid. Review certificate status."
              showIcon
              closable
              style={{ marginBottom: 8 }}
            />
          )}
        </div>
      )}

      {/* Main Content Tabs */}
      <Card>
        <Tabs 
          activeKey={activeTab} 
          onChange={setActiveTab}
          tabBarExtraContent={{
            right: (
              <Space>
                <Badge 
                  status={connectionStatus?.isConnected ? 'success' : 'error'}
                  text={connectionStatus?.environment?.toUpperCase() || 'UNKNOWN'}
                />
              </Space>
            )
          }}
        >
          <TabPane 
            tab={
              <span>
                <CloudServerOutlined />
                Connection Status
              </span>
            } 
            key="connection"
          >
            <FIRSConnectionManager />
          </TabPane>

          <TabPane 
            tab={
              <span>
                <ApiOutlined />
                Environments
              </span>
            } 
            key="environments"
          >
            <Row gutter={[16, 16]}>
              {environments.map((env, index) => (
                <Col xs={24} lg={12} key={index}>
                  <Card 
                    title={env.name}
                    extra={
                      <Badge 
                        status={getEnvironmentStatusColor(env.status) as any}
                        text={env.status.toUpperCase()}
                      />
                    }
                  >
                    <Space direction="vertical" style={{ width: '100%' }}>
                      <div>
                        <strong>URL:</strong> {env.url}
                      </div>
                      <div>
                        <strong>Response Time:</strong> {env.responseTime}ms
                      </div>
                      <div>
                        <strong>Last Sync:</strong> {env.lastSync.toLocaleString()}
                      </div>
                    </Space>
                  </Card>
                </Col>
              ))}
            </Row>
          </TabPane>

          <TabPane 
            tab={
              <span>
                <SafetyCertificateOutlined />
                Certificates
              </span>
            } 
            key="certificates"
          >
            <Row gutter={[16, 16]}>
              {certificates.map((cert) => (
                <Col xs={24} lg={12} key={cert.id}>
                  <Card 
                    title={cert.name}
                    extra={
                      <Badge 
                        status={getCertificateStatusColor(cert.status) as any}
                        text={cert.status.toUpperCase()}
                      />
                    }
                  >
                    <Timeline>
                      <Timeline.Item icon={<SafetyCertificateOutlined />}>
                        <strong>Type:</strong> {cert.type}
                      </Timeline.Item>
                      <Timeline.Item icon={<CheckCircleOutlined />}>
                        <strong>Issuer:</strong> {cert.issuer}
                      </Timeline.Item>
                      <Timeline.Item 
                        icon={<ExclamationTriangleOutlined />}
                        color={new Date(cert.expiryDate).getTime() - Date.now() < 30 * 24 * 60 * 60 * 1000 ? 'red' : 'green'}
                      >
                        <strong>Expires:</strong> {cert.expiryDate.toLocaleDateString()}
                      </Timeline.Item>
                    </Timeline>
                  </Card>
                </Col>
              ))}
            </Row>
          </TabPane>

          <TabPane 
            tab={
              <span>
                <WarningOutlined />
                API Quotas
              </span>
            } 
            key="quotas"
          >
            {quotaInfo && (
              <Row gutter={[16, 16]}>
                <Col xs={24} lg={12}>
                  <Card title="Daily Usage">
                    <Progress
                      percent={Math.round((quotaInfo.dailyUsed / quotaInfo.dailyLimit) * 100)}
                      format={() => `${quotaInfo.dailyUsed} / ${quotaInfo.dailyLimit}`}
                      status="active"
                    />
                    <p style={{ marginTop: 12, marginBottom: 0 }}>
                      Resets: {quotaInfo.resetTime.toLocaleString()}
                    </p>
                  </Card>
                </Col>
                <Col xs={24} lg={12}>
                  <Card title="Monthly Usage">
                    <Progress
                      percent={Math.round((quotaInfo.monthlyUsed / quotaInfo.monthlyLimit) * 100)}
                      format={() => `${quotaInfo.monthlyUsed} / ${quotaInfo.monthlyLimit}`}
                      status="active"
                    />
                    <p style={{ marginTop: 12, marginBottom: 0 }}>
                      Current billing period
                    </p>
                  </Card>
                </Col>
              </Row>
            )}
          </TabPane>
        </Tabs>
      </Card>
    </div>
  );
};

export default FIRSDashboardPage;