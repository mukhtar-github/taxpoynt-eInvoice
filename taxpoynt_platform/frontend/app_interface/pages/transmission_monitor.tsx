/**
 * APP Transmission Monitor Page
 * =============================
 * 
 * Dedicated page for comprehensive transmission monitoring and management.
 * Provides detailed view of document transmission pipeline to FIRS.
 * 
 * Features:
 * - Real-time transmission status monitoring
 * - Queue management and prioritization
 * - Batch processing controls
 * - Performance analytics
 * - Error handling and retry mechanisms
 * 
 * @author TaxPoynt Development Team
 * @version 1.0.0
 */

import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Tabs, Button, Space, Statistic, Alert, Badge } from 'antd';
import {
  SendOutlined,
  MonitorOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  ReloadOutlined,
  SettingOutlined
} from '@ant-design/icons';

// Import APP Interface components
import { TransmissionMonitor } from '../components/transmission_dashboard/TransmissionMonitor';
import { TransmissionQueue } from '../components/transmission_dashboard/TransmissionQueue';

// Import types
import type { TransmissionMetrics, QueueStatus } from '../types';

const { TabPane } = Tabs;

interface TransmissionMonitorPageProps {
  className?: string;
}

interface TransmissionStats {
  totalTransmissions: number;
  successfulTransmissions: number;
  failedTransmissions: number;
  pendingTransmissions: number;
  averageProcessingTime: number;
  successRate: number;
  queueLength: number;
  activeConnections: number;
}

export const TransmissionMonitorPage: React.FC<TransmissionMonitorPageProps> = ({ className }) => {
  // State management
  const [stats, setStats] = useState<TransmissionStats | null>(null);
  const [queueStatus, setQueueStatus] = useState<QueueStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');

  // Auto-refresh functionality
  useEffect(() => {
    loadTransmissionData();
    const interval = setInterval(loadTransmissionData, 10000); // 10 seconds for real-time monitoring
    return () => clearInterval(interval);
  }, []);

  const loadTransmissionData = async () => {
    try {
      setRefreshing(true);
      
      // Simulate API calls to transmission services
      const [statsData, queueData] = await Promise.all([
        fetchTransmissionStats(),
        fetchQueueStatus()
      ]);

      setStats(statsData);
      setQueueStatus(queueData);
      setLoading(false);
    } catch (error) {
      console.error('Failed to load transmission data:', error);
    } finally {
      setRefreshing(false);
    }
  };

  // Mock API functions (replace with actual API calls)
  const fetchTransmissionStats = async (): Promise<TransmissionStats> => {
    return {
      totalTransmissions: 15420,
      successfulTransmissions: 15180,
      failedTransmissions: 240,
      pendingTransmissions: 87,
      averageProcessingTime: 2.3,
      successRate: 98.4,
      queueLength: 156,
      activeConnections: 8
    };
  };

  const fetchQueueStatus = async (): Promise<QueueStatus> => {
    return {
      total: 156,
      processing: 12,
      pending: 87,
      failed: 8,
      priority: 49,
      throughput: 45.2
    };
  };

  const handleRefresh = () => {
    loadTransmissionData();
  };

  const getStatusColor = (rate: number) => {
    if (rate >= 98) return '#52c41a';
    if (rate >= 95) return '#faad14';
    return '#ff4d4f';
  };

  if (loading) {
    return (
      <div style={{ padding: 24, textAlign: 'center' }}>
        <MonitorOutlined spin style={{ fontSize: 24, marginBottom: 16 }} />
        <p>Loading Transmission Monitor...</p>
      </div>
    );
  }

  return (
    <div className={`transmission-monitor-page ${className || ''}`}>
      {/* Page Header */}
      <div style={{ marginBottom: 24 }}>
        <Row justify="space-between" align="middle">
          <Col>
            <h1 style={{ margin: 0, display: 'flex', alignItems: 'center' }}>
              <SendOutlined style={{ marginRight: 12, color: '#1890ff' }} />
              Transmission Monitor
              {refreshing && <ReloadOutlined spin style={{ marginLeft: 12, color: '#52c41a' }} />}
            </h1>
            <p style={{ margin: '4px 0 0 0', color: '#666' }}>
              Real-time FIRS transmission monitoring and queue management
            </p>
          </Col>
          <Col>
            <Space>
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
              title="Total Transmissions"
              value={stats?.totalTransmissions}
              prefix={<SendOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Success Rate"
              value={stats?.successRate}
              suffix="%"
              precision={1}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: getStatusColor(stats?.successRate || 0) }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Queue Length"
              value={stats?.queueLength}
              prefix={<ClockCircleOutlined />}
              valueStyle={{ color: stats?.queueLength && stats.queueLength > 100 ? '#faad14' : '#52c41a' }}
              suffix="docs"
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Active Connections"
              value={stats?.activeConnections}
              prefix={<MonitorOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
      </Row>

      {/* Status Alerts */}
      {stats && (
        <div style={{ marginBottom: 24 }}>
          {stats.failedTransmissions > 0 && (
            <Alert
              type="warning"
              message={`${stats.failedTransmissions} failed transmissions require attention`}
              description="Review failed transmissions and retry if necessary"
              showIcon
              closable
              style={{ marginBottom: 8 }}
              action={
                <Button size="small" type="text">
                  View Failed
                </Button>
              }
            />
          )}
          {stats.queueLength > 200 && (
            <Alert
              type="info"
              message="High queue volume detected"
              description="Consider scaling transmission workers for optimal performance"
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
                  status="processing" 
                  text={`${stats?.pendingTransmissions || 0} pending`}
                />
                <Badge 
                  status={stats?.successRate && stats.successRate > 95 ? 'success' : 'error'}
                  text={`${stats?.successRate || 0}% success`}
                />
              </Space>
            )
          }}
        >
          <TabPane 
            tab={
              <span>
                <MonitorOutlined />
                Real-time Monitor
              </span>
            } 
            key="overview"
          >
            <TransmissionMonitor />
          </TabPane>

          <TabPane 
            tab={
              <span>
                <ClockCircleOutlined />
                Queue Management
              </span>
            } 
            key="queue"
          >
            <TransmissionQueue />
          </TabPane>

          <TabPane 
            tab={
              <span>
                <ExclamationCircleOutlined />
                Failed Transmissions
              </span>
            } 
            key="failed"
          >
            <div style={{ padding: '20px 0' }}>
              <Alert
                type="info"
                message="Failed Transmission Analysis"
                description="Detailed analysis and retry mechanisms for failed transmissions will be displayed here."
                showIcon
              />
            </div>
          </TabPane>

          <TabPane 
            tab={
              <span>
                <SettingOutlined />
                Settings
              </span>
            } 
            key="settings"
          >
            <div style={{ padding: '20px 0' }}>
              <Alert
                type="info"
                message="Transmission Settings"
                description="Configure transmission parameters, retry policies, and queue management settings."
                showIcon
              />
            </div>
          </TabPane>
        </Tabs>
      </Card>
    </div>
  );
};

export default TransmissionMonitorPage;