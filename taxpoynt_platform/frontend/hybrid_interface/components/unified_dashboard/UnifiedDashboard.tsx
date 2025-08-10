/**
 * Unified Dashboard Component
 * ===========================
 * 
 * Main dashboard component that combines metrics and insights from both
 * System Integrator (SI) and Access Point Provider (APP) interfaces.
 * 
 * Features:
 * - Combined real-time metrics from SI and APP
 * - Cross-role performance indicators
 * - End-to-end process monitoring
 * - Unified alerts and notifications
 * - Role-aware content display
 * - Interactive workflow status
 * 
 * @author TaxPoynt Development Team
 * @version 1.0.0
 */

import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Statistic, Alert, Badge, Timeline, Progress, Tabs, Space, Button } from 'antd';
import {
  DashboardOutlined,
  IntegrationOutlined,
  SendOutlined,
  CheckCircleOutlined,
  ExclamationTriangleOutlined,
  ClockCircleOutlined,
  TrophyOutlined,
  RocketOutlined,
  SyncOutlined,
  BarChartOutlined,
  SettingOutlined
} from '@ant-design/icons';

// Import existing components for reuse
import { TransmissionMonitor } from '../../app_interface/components/transmission_dashboard/TransmissionMonitor';
import { FIRSConnectionManager } from '../../app_interface/components/firs_communication/FIRSConnectionManager';

// Import types
import type { 
  UnifiedDashboardMetrics, 
  HybridRole, 
  EndToEndProcess, 
  CrossRoleWorkflow,
  DashboardComponentProps
} from '../types';

interface UnifiedDashboardProps extends DashboardComponentProps {
  userRole: HybridRole;
  onRoleSwitch?: (newRole: HybridRole) => void;
  onNavigateToInterface?: (interfaceType: 'si' | 'app') => void;
}

interface DashboardAlert {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error';
  title: string;
  message: string;
  timestamp: Date;
  actionable: boolean;
  action?: {
    label: string;
    onClick: () => void;
  };
}

export const UnifiedDashboard: React.FC<UnifiedDashboardProps> = ({
  userRole,
  onRoleSwitch,
  onNavigateToInterface,
  refreshInterval = 30000,
  autoRefresh = true,
  onRefresh,
  dateRange,
  filters,
  className,
  loading: externalLoading = false,
  ...props
}) => {
  // State management
  const [metrics, setMetrics] = useState<UnifiedDashboardMetrics | null>(null);
  const [endToEndProcesses, setEndToEndProcesses] = useState<EndToEndProcess[]>([]);
  const [activeWorkflows, setActiveWorkflows] = useState<CrossRoleWorkflow[]>([]);
  const [alerts, setAlerts] = useState<DashboardAlert[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');

  // Auto-refresh functionality
  useEffect(() => {
    loadDashboardData();
    
    if (autoRefresh) {
      const interval = setInterval(loadDashboardData, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [autoRefresh, refreshInterval, dateRange, filters]);

  const loadDashboardData = async () => {
    try {
      setRefreshing(true);
      
      // Simulate API calls to both SI and APP services
      const [metricsData, processesData, workflowsData, alertsData] = await Promise.all([
        fetchUnifiedMetrics(),
        fetchEndToEndProcesses(),
        fetchActiveWorkflows(),
        fetchDashboardAlerts()
      ]);

      setMetrics(metricsData);
      setEndToEndProcesses(processesData);
      setActiveWorkflows(workflowsData);
      setAlerts(alertsData);
      setLoading(false);
      
      if (onRefresh) {
        onRefresh();
      }
    } catch (error) {
      console.error('Failed to load unified dashboard data:', error);
      setAlerts(prev => [...prev, {
        id: Date.now().toString(),
        type: 'error',
        title: 'Dashboard Error',
        message: 'Failed to load dashboard data. Please try refreshing.',
        timestamp: new Date(),
        actionable: true,
        action: {
          label: 'Retry',
          onClick: loadDashboardData
        }
      }]);
    } finally {
      setRefreshing(false);
    }
  };

  // Mock API functions (replace with actual API calls)
  const fetchUnifiedMetrics = async (): Promise<UnifiedDashboardMetrics> => {
    return {
      si_metrics: {
        total_integrations: 45,
        active_connections: 42,
        failed_connections: 3,
        documents_processed_today: 2847,
        processing_success_rate: 97.8,
        average_processing_time: 3.2,
        compliance_score: 94.5
      },
      app_metrics: {
        total_transmissions: 2650,
        successful_transmissions: 2598,
        failed_transmissions: 52,
        pending_transmissions: 23,
        firs_connection_status: 'connected',
        transmission_success_rate: 98.0,
        average_response_time: 1.8,
        security_score: 96.2
      },
      hybrid_metrics: {
        end_to_end_completion_rate: 96.5,
        cross_role_workflow_count: 12,
        unified_compliance_score: 95.1,
        total_documents_in_pipeline: 234,
        average_end_to_end_time: 8.7,
        bottleneck_stage: 'validation'
      },
      cross_role_metrics: {
        si_to_app_handoffs: 2680,
        successful_handoffs: 2598,
        failed_handoffs: 82,
        handoff_success_rate: 97.0,
        integration_to_transmission_time: 5.2,
        workflow_orchestration_efficiency: 94.8
      },
      timestamp: new Date()
    };
  };

  const fetchEndToEndProcesses = async (): Promise<EndToEndProcess[]> => {
    return [
      {
        process_id: 'proc-001',
        name: 'Monthly Invoice Batch - December 2024',
        description: 'Processing December invoice batch for corporate clients',
        document_reference: 'BATCH-DEC-2024-001',
        current_stage: 'transmission',
        status: 'active',
        progress_percentage: 78,
        started_at: new Date(Date.now() - 2 * 60 * 60 * 1000),
        estimated_completion: new Date(Date.now() + 45 * 60 * 1000),
        sla_status: 'on_track',
        stage_durations: {
          'data_extraction': 45,
          'validation': 23,
          'transformation': 12,
          'transmission': 15,
          'acknowledgment': 0,
          'completed': 0,
          'failed': 0
        },
        efficiency_score: 92.5,
        bottlenecks: []
      },
      {
        process_id: 'proc-002',
        name: 'Credit Note Processing - Client ABC Ltd',
        description: 'Processing credit notes for client refunds',
        document_reference: 'CN-ABC-2024-045',
        current_stage: 'validation',
        status: 'active',
        progress_percentage: 45,
        started_at: new Date(Date.now() - 30 * 60 * 1000),
        estimated_completion: new Date(Date.now() + 25 * 60 * 1000),
        sla_status: 'at_risk',
        stage_durations: {
          'data_extraction': 8,
          'validation': 22,
          'transformation': 0,
          'transmission': 0,
          'acknowledgment': 0,
          'completed': 0,
          'failed': 0
        },
        efficiency_score: 78.2,
        bottlenecks: [
          {
            stage: 'validation',
            expected_duration: 15,
            actual_duration: 22,
            delay_percentage: 46.7,
            root_causes: ['Complex validation rules', 'Data quality issues'],
            recommended_actions: ['Review validation configuration', 'Improve data preprocessing']
          }
        ]
      }
    ];
  };

  const fetchActiveWorkflows = async (): Promise<CrossRoleWorkflow[]> => {
    return [
      {
        id: 'wf-001',
        name: 'End-to-End Invoice Processing',
        description: 'Complete invoice lifecycle from ERP to FIRS',
        type: 'end_to_end_invoice',
        status: 'active',
        stages: [],
        triggers: [],
        created_by: 'system',
        created_at: new Date(),
        updated_at: new Date(),
        execution_history: []
      }
    ];
  };

  const fetchDashboardAlerts = async (): Promise<DashboardAlert[]> => {
    return [
      {
        id: 'alert-001',
        type: 'warning',
        title: 'Validation Bottleneck Detected',
        message: 'Validation stage is taking 45% longer than expected for current batch',
        timestamp: new Date(Date.now() - 15 * 60 * 1000),
        actionable: true,
        action: {
          label: 'Review Validation',
          onClick: () => console.log('Navigate to validation center')
        }
      },
      {
        id: 'alert-002',
        type: 'info',
        title: 'System Integration Completed',
        message: 'New ERP connection for ClientCorp has been successfully established',
        timestamp: new Date(Date.now() - 45 * 60 * 1000),
        actionable: false
      }
    ];
  };

  const getMetricColor = (value: number, thresholds: { good: number; warning: number }): string => {
    if (value >= thresholds.good) return '#52c41a';
    if (value >= thresholds.warning) return '#faad14';
    return '#ff4d4f';
  };

  const handleQuickAction = (action: string) => {
    switch (action) {
      case 'switch_to_si':
        if (onNavigateToInterface) onNavigateToInterface('si');
        break;
      case 'switch_to_app':
        if (onNavigateToInterface) onNavigateToInterface('app');
        break;
      case 'view_workflows':
        setActiveTab('workflows');
        break;
      case 'view_processes':
        setActiveTab('processes');
        break;
      default:
        console.log(`Quick action: ${action}`);
    }
  };

  if (loading || externalLoading) {
    return (
      <div style={{ padding: 24, textAlign: 'center' }}>
        <SyncOutlined spin style={{ fontSize: 24, marginBottom: 16 }} />
        <p>Loading Unified Dashboard...</p>
      </div>
    );
  }

  return (
    <div className={`unified-dashboard ${className || ''}`} {...props}>
      {/* Header */}
      <div style={{ marginBottom: 24 }}>
        <Row justify="space-between" align="middle">
          <Col>
            <h1 style={{ margin: 0, display: 'flex', alignItems: 'center' }}>
              <DashboardOutlined style={{ marginRight: 12, color: '#1890ff' }} />
              Hybrid Interface Dashboard
              {refreshing && <SyncOutlined spin style={{ marginLeft: 12, color: '#52c41a' }} />}
            </h1>
            <p style={{ margin: '4px 0 0 0', color: '#666' }}>
              Unified view of System Integration and Access Point Provider operations
            </p>
          </Col>
          <Col>
            <Space>
              <Badge status="success" text={`Role: ${userRole.replace('_', ' ').toUpperCase()}`} />
              <Button icon={<SyncOutlined />} onClick={loadDashboardData} loading={refreshing}>
                Refresh
              </Button>
              <Button icon={<SettingOutlined />} type="default">
                Settings
              </Button>
            </Space>
          </Col>
        </Row>
      </div>

      {/* Alert Section */}
      {alerts.length > 0 && (
        <div style={{ marginBottom: 24 }}>
          {alerts.slice(0, 3).map(alert => (
            <Alert
              key={alert.id}
              type={alert.type}
              message={alert.title}
              description={`${alert.message} - ${alert.timestamp.toLocaleTimeString()}`}
              showIcon
              closable
              style={{ marginBottom: 8 }}
              action={alert.actionable && alert.action ? (
                <Button size="small" type="link" onClick={alert.action.onClick}>
                  {alert.action.label}
                </Button>
              ) : undefined}
            />
          ))}
        </div>
      )}

      {/* Key Metrics Overview */}
      {metrics && (
        <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
          <Col xs={24} sm={12} md={6}>
            <Card>
              <Statistic
                title="End-to-End Success Rate"
                value={metrics.hybrid_metrics.end_to_end_completion_rate}
                suffix="%"
                precision={1}
                prefix={<TrophyOutlined />}
                valueStyle={{ color: getMetricColor(metrics.hybrid_metrics.end_to_end_completion_rate, { good: 95, warning: 90 }) }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card>
              <Statistic
                title="SI Processing Success"
                value={metrics.si_metrics.processing_success_rate}
                suffix="%"
                precision={1}
                prefix={<IntegrationOutlined />}
                valueStyle={{ color: getMetricColor(metrics.si_metrics.processing_success_rate, { good: 95, warning: 90 }) }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card>
              <Statistic
                title="APP Transmission Success"
                value={metrics.app_metrics.transmission_success_rate}
                suffix="%"
                precision={1}
                prefix={<SendOutlined />}
                valueStyle={{ color: getMetricColor(metrics.app_metrics.transmission_success_rate, { good: 95, warning: 90 }) }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card>
              <Statistic
                title="Unified Compliance Score"
                value={metrics.hybrid_metrics.unified_compliance_score}
                suffix="%"
                precision={1}
                prefix={<CheckCircleOutlined />}
                valueStyle={{ color: getMetricColor(metrics.hybrid_metrics.unified_compliance_score, { good: 90, warning: 80 }) }}
              />
            </Card>
          </Col>
        </Row>
      )}

      {/* Main Dashboard Content */}
      <Tabs activeKey={activeTab} onChange={setActiveTab}>
        <Tabs.TabPane
          tab={
            <span>
              <BarChartOutlined />
              Overview
            </span>
          }
          key="overview"
        >
          <Row gutter={[16, 16]}>
            {/* Cross-Role Performance */}
            <Col xs={24} lg={12}>
              <Card title="Cross-Role Performance" size="small">
                {metrics && (
                  <div>
                    <Row gutter={16}>
                      <Col span={12}>
                        <Statistic
                          title="Handoff Success Rate"
                          value={metrics.cross_role_metrics.handoff_success_rate}
                          suffix="%"
                          precision={1}
                        />
                      </Col>
                      <Col span={12}>
                        <Statistic
                          title="Avg End-to-End Time"
                          value={metrics.hybrid_metrics.average_end_to_end_time}
                          suffix="min"
                          precision={1}
                        />
                      </Col>
                    </Row>
                    <div style={{ marginTop: 16 }}>
                      <p>Pipeline Status:</p>
                      <Progress 
                        percent={Math.round((metrics.hybrid_metrics.total_documents_in_pipeline / 500) * 100)}
                        format={() => `${metrics.hybrid_metrics.total_documents_in_pipeline} docs`}
                        status="active"
                      />
                    </div>
                  </div>
                )}
              </Card>
            </Col>

            {/* System Health Overview */}
            <Col xs={24} lg={12}>
              <Card title="System Health" size="small">
                {metrics && (
                  <div>
                    <Timeline>
                      <Timeline.Item 
                        color={metrics.si_metrics.active_connections > 40 ? 'green' : 'orange'}
                        dot={metrics.si_metrics.active_connections > 40 ? <CheckCircleOutlined /> : <ExclamationTriangleOutlined />}
                      >
                        SI Integrations: {metrics.si_metrics.active_connections}/{metrics.si_metrics.total_integrations} active
                      </Timeline.Item>
                      <Timeline.Item 
                        color={metrics.app_metrics.firs_connection_status === 'connected' ? 'green' : 'red'}
                        dot={metrics.app_metrics.firs_connection_status === 'connected' ? <CheckCircleOutlined /> : <ExclamationTriangleOutlined />}
                      >
                        FIRS Connection: {metrics.app_metrics.firs_connection_status.toUpperCase()}
                      </Timeline.Item>
                      <Timeline.Item 
                        color={metrics.app_metrics.pending_transmissions < 50 ? 'green' : 'orange'}
                        dot={<ClockCircleOutlined />}
                      >
                        Pending Transmissions: {metrics.app_metrics.pending_transmissions}
                      </Timeline.Item>
                    </Timeline>
                  </div>
                )}
              </Card>
            </Col>
          </Row>
        </Tabs.TabPane>

        <Tabs.TabPane
          tab={
            <span>
              <RocketOutlined />
              Active Processes
            </span>
          }
          key="processes"
        >
          <Row gutter={[16, 16]}>
            {endToEndProcesses.map(process => (
              <Col xs={24} lg={12} key={process.process_id}>
                <Card 
                  title={process.name}
                  size="small"
                  extra={
                    <Badge 
                      status={process.sla_status === 'on_track' ? 'success' : 'warning'}
                      text={process.sla_status.replace('_', ' ').toUpperCase()}
                    />
                  }
                >
                  <div style={{ marginBottom: 16 }}>
                    <p style={{ margin: '0 0 8px 0' }}>
                      <strong>Stage:</strong> {process.current_stage.replace('_', ' ').toUpperCase()}
                    </p>
                    <Progress percent={process.progress_percentage} status="active" />
                  </div>
                  
                  <Row gutter={8}>
                    <Col span={12}>
                      <small>Started: {process.started_at.toLocaleTimeString()}</small>
                    </Col>
                    <Col span={12}>
                      <small>ETA: {process.estimated_completion.toLocaleTimeString()}</small>
                    </Col>
                  </Row>
                  
                  {process.bottlenecks.length > 0 && (
                    <Alert
                      type="warning"
                      message="Bottleneck detected"
                      description={`${process.bottlenecks[0].stage} stage delayed by ${process.bottlenecks[0].delay_percentage.toFixed(1)}%`}
                      showIcon
                      style={{ marginTop: 8 }}
                      size="small"
                    />
                  )}
                </Card>
              </Col>
            ))}
          </Row>
        </Tabs.TabPane>

        <Tabs.TabPane
          tab={
            <span>
              <IntegrationOutlined />
              SI Interface
            </span>
          }
          key="si"
        >
          <div style={{ padding: '20px 0' }}>
            <Alert
              type="info"
              message="System Integrator Interface"
              description="Access SI-specific tools and monitoring here, or switch to the full SI interface."
              showIcon
              action={
                <Button type="primary" onClick={() => handleQuickAction('switch_to_si')}>
                  Open SI Interface
                </Button>
              }
            />
          </div>
        </Tabs.TabPane>

        <Tabs.TabPane
          tab={
            <span>
              <SendOutlined />
              APP Interface
            </span>
          }
          key="app"
        >
          <Row gutter={[16, 16]}>
            <Col xs={24} lg={12}>
              <Card title="FIRS Connection Status" size="small">
                <FIRSConnectionManager compact />
              </Card>
            </Col>
            <Col xs={24} lg={12}>
              <Card title="Transmission Monitor" size="small">
                <TransmissionMonitor compact />
              </Card>
            </Col>
          </Row>
        </Tabs.TabPane>
      </Tabs>
    </div>
  );
};

export default UnifiedDashboard;