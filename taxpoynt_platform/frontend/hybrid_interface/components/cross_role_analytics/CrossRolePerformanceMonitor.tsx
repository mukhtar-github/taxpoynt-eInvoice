/**
 * Cross-Role Performance Monitor Component
 * ========================================
 * 
 * Specialized monitoring component that tracks performance metrics
 * specifically related to cross-role operations, handoffs, and
 * end-to-end process efficiency between SI and APP interfaces.
 * 
 * Features:
 * - SI to APP handoff monitoring
 * - End-to-end process tracking
 * - Bottleneck identification and analysis
 * - Cross-role workflow efficiency metrics
 * - Real-time performance alerts
 * - SLA compliance tracking
 * 
 * @author TaxPoynt Development Team
 * @version 1.0.0
 */

import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Progress, Alert, Badge, Timeline, Statistic, Table, Button, Space } from 'antd';
import {
  SwapOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
  ExclamationTriangleOutlined,
  ArrowRightOutlined,
  TrendingUpOutlined,
  TrendingDownOutlined,
  WarningOutlined,
  ReloadOutlined,
  BarChartOutlined
} from '@ant-design/icons';

import type { 
  CrossRoleMetrics, 
  EndToEndProcess,
  ProcessBottleneck,
  DashboardComponentProps 
} from '../../types';

interface CrossRolePerformanceMonitorProps extends DashboardComponentProps {
  showDetails?: boolean;
  alertThresholds?: {
    handoffSuccessRate: number;
    processingTime: number;
    endToEndSuccess: number;
  };
  onBottleneckClick?: (bottleneck: ProcessBottleneck) => void;
  onProcessClick?: (processId: string) => void;
}

interface HandoffMetrics {
  stage_from: string;
  stage_to: string;
  total_handoffs: number;
  successful_handoffs: number;
  failed_handoffs: number;
  average_handoff_time: number;
  success_rate: number;
  trend: 'improving' | 'declining' | 'stable';
}

interface ProcessStageMetrics {
  stage: string;
  interface: 'si' | 'app' | 'shared';
  average_duration: number;
  expected_duration: number;
  efficiency_score: number;
  bottleneck_risk: 'low' | 'medium' | 'high';
  current_load: number;
}

interface PerformanceAlert {
  id: string;
  type: 'sla_breach' | 'bottleneck' | 'handoff_failure' | 'performance_degradation';
  severity: 'low' | 'medium' | 'high' | 'critical';
  title: string;
  message: string;
  stage?: string;
  timestamp: Date;
  actionable: boolean;
}

export const CrossRolePerformanceMonitor: React.FC<CrossRolePerformanceMonitorProps> = ({
  showDetails = true,
  alertThresholds = {
    handoffSuccessRate: 95,
    processingTime: 300, // 5 minutes
    endToEndSuccess: 90
  },
  onBottleneckClick,
  onProcessClick,
  refreshInterval = 10000,
  autoRefresh = true,
  className,
  ...props
}) => {
  // State management
  const [crossRoleMetrics, setCrossRoleMetrics] = useState<CrossRoleMetrics | null>(null);
  const [handoffMetrics, setHandoffMetrics] = useState<HandoffMetrics[]>([]);
  const [stageMetrics, setStageMetrics] = useState<ProcessStageMetrics[]>([]);
  const [activeProcesses, setActiveProcesses] = useState<EndToEndProcess[]>([]);
  const [performanceAlerts, setPerformanceAlerts] = useState<PerformanceAlert[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    loadPerformanceData();

    if (autoRefresh) {
      const interval = setInterval(loadPerformanceData, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [autoRefresh, refreshInterval]);

  const loadPerformanceData = async () => {
    try {
      setRefreshing(true);

      const [metricsData, handoffData, stageData, processData, alertData] = await Promise.all([
        fetchCrossRoleMetrics(),
        fetchHandoffMetrics(),
        fetchStageMetrics(),
        fetchActiveProcesses(),
        fetchPerformanceAlerts()
      ]);

      setCrossRoleMetrics(metricsData);
      setHandoffMetrics(handoffData);
      setStageMetrics(stageData);
      setActiveProcesses(processData);
      setPerformanceAlerts(alertData);
      setLoading(false);
    } catch (error) {
      console.error('Failed to load cross-role performance data:', error);
    } finally {
      setRefreshing(false);
    }
  };

  // Mock API functions
  const fetchCrossRoleMetrics = async (): Promise<CrossRoleMetrics> => {
    return {
      si_to_app_handoffs: 2680,
      successful_handoffs: 2598,
      failed_handoffs: 82,
      handoff_success_rate: 97.0,
      integration_to_transmission_time: 5.2,
      workflow_orchestration_efficiency: 94.8
    };
  };

  const fetchHandoffMetrics = async (): Promise<HandoffMetrics[]> => {
    return [
      {
        stage_from: 'data_extraction',
        stage_to: 'validation',
        total_handoffs: 1250,
        successful_handoffs: 1235,
        failed_handoffs: 15,
        average_handoff_time: 0.8,
        success_rate: 98.8,
        trend: 'stable'
      },
      {
        stage_from: 'validation',
        stage_to: 'transformation',
        total_handoffs: 1235,
        successful_handoffs: 1198,
        failed_handoffs: 37,
        average_handoff_time: 1.2,
        success_rate: 97.0,
        trend: 'declining'
      },
      {
        stage_from: 'transformation',
        stage_to: 'transmission',
        total_handoffs: 1198,
        successful_handoffs: 1185,
        failed_handoffs: 13,
        average_handoff_time: 0.5,
        success_rate: 98.9,
        trend: 'improving'
      },
      {
        stage_from: 'transmission',
        stage_to: 'acknowledgment',
        total_handoffs: 1185,
        successful_handoffs: 1165,
        failed_handoffs: 20,
        average_handoff_time: 2.1,
        success_rate: 98.3,
        trend: 'stable'
      }
    ];
  };

  const fetchStageMetrics = async (): Promise<ProcessStageMetrics[]> => {
    return [
      {
        stage: 'data_extraction',
        interface: 'si',
        average_duration: 3.2,
        expected_duration: 3.0,
        efficiency_score: 93.8,
        bottleneck_risk: 'low',
        current_load: 68
      },
      {
        stage: 'validation',
        interface: 'shared',
        average_duration: 4.8,
        expected_duration: 3.5,
        efficiency_score: 72.9,
        bottleneck_risk: 'high',
        current_load: 89
      },
      {
        stage: 'transformation',
        interface: 'si',
        average_duration: 2.1,
        expected_duration: 2.0,
        efficiency_score: 95.2,
        bottleneck_risk: 'low',
        current_load: 54
      },
      {
        stage: 'transmission',
        interface: 'app',
        average_duration: 1.8,
        expected_duration: 2.0,
        efficiency_score: 111.1,
        bottleneck_risk: 'low',
        current_load: 72
      },
      {
        stage: 'acknowledgment',
        interface: 'app',
        average_duration: 0.9,
        expected_duration: 1.0,
        efficiency_score: 111.1,
        bottleneck_risk: 'low',
        current_load: 45
      }
    ];
  };

  const fetchActiveProcesses = async (): Promise<EndToEndProcess[]> => {
    return [
      {
        process_id: 'proc-001',
        name: 'Invoice Batch Processing',
        description: 'Large batch processing for monthly invoices',
        document_reference: 'BATCH-2024-001',
        current_stage: 'validation',
        status: 'active',
        progress_percentage: 68,
        started_at: new Date(Date.now() - 2 * 60 * 60 * 1000),
        estimated_completion: new Date(Date.now() + 45 * 60 * 1000),
        sla_status: 'at_risk',
        stage_durations: {
          'data_extraction': 35,
          'validation': 48,
          'transformation': 0,
          'transmission': 0,
          'acknowledgment': 0,
          'completed': 0,
          'failed': 0
        },
        efficiency_score: 78.5,
        bottlenecks: [
          {
            stage: 'validation',
            expected_duration: 25,
            actual_duration: 48,
            delay_percentage: 92,
            root_causes: ['High validation complexity', 'Resource contention'],
            recommended_actions: ['Scale validation workers', 'Optimize validation rules']
          }
        ]
      }
    ];
  };

  const fetchPerformanceAlerts = async (): Promise<PerformanceAlert[]> => {
    return [
      {
        id: 'alert-001',
        type: 'bottleneck',
        severity: 'high',
        title: 'Validation Stage Bottleneck',
        message: 'Validation stage is operating at 89% capacity with 92% delays',
        stage: 'validation',
        timestamp: new Date(Date.now() - 10 * 60 * 1000),
        actionable: true
      },
      {
        id: 'alert-002',
        type: 'handoff_failure',
        severity: 'medium',
        title: 'Increased Handoff Failures',
        message: 'Validation to transformation handoffs showing 3% failure rate',
        stage: 'validation',
        timestamp: new Date(Date.now() - 25 * 60 * 1000),
        actionable: true
      }
    ];
  };

  const getEfficiencyColor = (score: number): string => {
    if (score >= 95) return '#52c41a';
    if (score >= 85) return '#faad14';
    return '#ff4d4f';
  };

  const getBottleneckRiskColor = (risk: string): string => {
    switch (risk) {
      case 'low': return '#52c41a';
      case 'medium': return '#faad14';
      case 'high': return '#ff4d4f';
      default: return '#666';
    }
  };

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'improving':
        return <TrendingUpOutlined style={{ color: '#52c41a' }} />;
      case 'declining':
        return <TrendingDownOutlined style={{ color: '#ff4d4f' }} />;
      default:
        return <ArrowRightOutlined style={{ color: '#666' }} />;
    }
  };

  const getSeverityColor = (severity: string): string => {
    switch (severity) {
      case 'critical': return '#ff4d4f';
      case 'high': return '#fa8c16';
      case 'medium': return '#faad14';
      case 'low': return '#52c41a';
      default: return '#666';
    }
  };

  // Table columns for handoff metrics
  const handoffColumns = [
    {
      title: 'Handoff Stage',
      key: 'handoff',
      render: (record: HandoffMetrics) => (
        <div>
          <strong>{record.stage_from.replace('_', ' ')}</strong>
          <ArrowRightOutlined style={{ margin: '0 8px', color: '#666' }} />
          <strong>{record.stage_to.replace('_', ' ')}</strong>
        </div>
      )
    },
    {
      title: 'Success Rate',
      dataIndex: 'success_rate',
      key: 'success_rate',
      render: (rate: number) => (
        <div>
          <strong style={{ color: rate >= alertThresholds.handoffSuccessRate ? '#52c41a' : '#ff4d4f' }}>
            {rate.toFixed(1)}%
          </strong>
          <Progress 
            percent={rate} 
            size="small" 
            status={rate >= alertThresholds.handoffSuccessRate ? 'success' : 'exception'}
            showInfo={false}
            style={{ marginTop: 4 }}
          />
        </div>
      )
    },
    {
      title: 'Avg Time',
      dataIndex: 'average_handoff_time',
      key: 'average_handoff_time',
      render: (time: number) => `${time.toFixed(1)}s`
    },
    {
      title: 'Volume',
      key: 'volume',
      render: (record: HandoffMetrics) => (
        <div>
          <div>{record.total_handoffs.toLocaleString()}</div>
          <small style={{ color: '#666' }}>
            {record.failed_handoffs} failed
          </small>
        </div>
      )
    },
    {
      title: 'Trend',
      dataIndex: 'trend',
      key: 'trend',
      render: (trend: string) => (
        <div style={{ display: 'flex', alignItems: 'center' }}>
          {getTrendIcon(trend)}
          <span style={{ marginLeft: 4, textTransform: 'capitalize' }}>
            {trend}
          </span>
        </div>
      )
    }
  ];

  // Table columns for stage metrics
  const stageColumns = [
    {
      title: 'Stage',
      key: 'stage',
      render: (record: ProcessStageMetrics) => (
        <div>
          <strong>{record.stage.replace('_', ' ').toUpperCase()}</strong>
          <br />
          <Badge 
            color={record.interface === 'si' ? '#722ed1' : record.interface === 'app' ? '#1890ff' : '#13c2c2'}
            text={record.interface.toUpperCase()}
          />
        </div>
      )
    },
    {
      title: 'Performance',
      key: 'performance',
      render: (record: ProcessStageMetrics) => (
        <div>
          <Statistic
            value={record.efficiency_score}
            suffix="%"
            precision={1}
            valueStyle={{ 
              fontSize: 16,
              color: getEfficiencyColor(record.efficiency_score)
            }}
          />
          <Progress 
            percent={Math.min(record.efficiency_score, 100)}
            size="small"
            strokeColor={getEfficiencyColor(record.efficiency_score)}
            showInfo={false}
          />
        </div>
      )
    },
    {
      title: 'Duration',
      key: 'duration',
      render: (record: ProcessStageMetrics) => (
        <div>
          <div>
            <strong>{record.average_duration.toFixed(1)}m</strong>
            <span style={{ color: '#666', fontSize: 12 }}>
              {' '}(exp: {record.expected_duration.toFixed(1)}m)
            </span>
          </div>
          <div style={{ fontSize: 11, color: record.average_duration > record.expected_duration ? '#ff4d4f' : '#52c41a' }}>
            {record.average_duration > record.expected_duration ? 'Over' : 'Under'} by{' '}
            {Math.abs(record.average_duration - record.expected_duration).toFixed(1)}m
          </div>
        </div>
      )
    },
    {
      title: 'Load',
      dataIndex: 'current_load',
      key: 'current_load',
      render: (load: number) => (
        <Progress
          type="circle"
          size={40}
          percent={load}
          format={() => `${load}%`}
          strokeColor={load > 80 ? '#ff4d4f' : load > 60 ? '#faad14' : '#52c41a'}
        />
      )
    },
    {
      title: 'Risk',
      dataIndex: 'bottleneck_risk',
      key: 'bottleneck_risk',
      render: (risk: string) => (
        <Badge 
          color={getBottleneckRiskColor(risk)}
          text={risk.toUpperCase()}
        />
      )
    }
  ];

  if (loading) {
    return (
      <Card className={className} {...props}>
        <div style={{ textAlign: 'center', padding: '40px 0' }}>
          <ReloadOutlined spin style={{ fontSize: 24, marginBottom: 16 }} />
          <p>Loading cross-role performance data...</p>
        </div>
      </Card>
    );
  }

  return (
    <div className={`cross-role-performance-monitor ${className || ''}`} {...props}>
      {/* Header */}
      <div style={{ marginBottom: 16 }}>
        <Row justify="space-between" align="middle">
          <Col>
            <h3 style={{ margin: 0, display: 'flex', alignItems: 'center' }}>
              <SwapOutlined style={{ marginRight: 8, color: '#1890ff' }} />
              Cross-Role Performance Monitor
              {refreshing && <ReloadOutlined spin style={{ marginLeft: 8, color: '#52c41a' }} />}
            </h3>
            <p style={{ margin: '4px 0 0 0', color: '#666' }}>
              Monitor handoffs and end-to-end process efficiency
            </p>
          </Col>
          <Col>
            <Button icon={<ReloadOutlined />} onClick={loadPerformanceData} loading={refreshing}>
              Refresh
            </Button>
          </Col>
        </Row>
      </div>

      {/* Performance Alerts */}
      {performanceAlerts.length > 0 && (
        <div style={{ marginBottom: 16 }}>
          {performanceAlerts.map(alert => (
            <Alert
              key={alert.id}
              type={alert.severity === 'critical' || alert.severity === 'high' ? 'error' : 'warning'}
              message={alert.title}
              description={`${alert.message} - ${alert.timestamp.toLocaleTimeString()}`}
              showIcon
              closable
              style={{ marginBottom: 8 }}
            />
          ))}
        </div>
      )}

      {/* Key Metrics Row */}
      {crossRoleMetrics && (
        <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
          <Col xs={24} sm={6}>
            <Card size="small">
              <Statistic
                title="Handoff Success Rate"
                value={crossRoleMetrics.handoff_success_rate}
                suffix="%"
                precision={1}
                prefix={<SwapOutlined />}
                valueStyle={{ color: getEfficiencyColor(crossRoleMetrics.handoff_success_rate) }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={6}>
            <Card size="small">
              <Statistic
                title="Avg Integration Time"
                value={crossRoleMetrics.integration_to_transmission_time}
                suffix="min"
                precision={1}
                prefix={<ClockCircleOutlined />}
                valueStyle={{ color: '#fa8c16' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={6}>
            <Card size="small">
              <Statistic
                title="Orchestration Efficiency"
                value={crossRoleMetrics.workflow_orchestration_efficiency}
                suffix="%"
                precision={1}
                prefix={<BarChartOutlined />}
                valueStyle={{ color: getEfficiencyColor(crossRoleMetrics.workflow_orchestration_efficiency) }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={6}>
            <Card size="small">
              <Statistic
                title="Total Handoffs"
                value={crossRoleMetrics.si_to_app_handoffs}
                prefix={<CheckCircleOutlined />}
                valueStyle={{ color: '#1890ff' }}
              />
            </Card>
          </Col>
        </Row>
      )}

      {/* Detailed Tables */}
      {showDetails && (
        <Row gutter={[16, 16]}>
          <Col xs={24} lg={12}>
            <Card title="Stage Handoff Performance" size="small">
              <Table
                columns={handoffColumns}
                dataSource={handoffMetrics}
                rowKey="stage_from"
                pagination={false}
                size="small"
              />
            </Card>
          </Col>

          <Col xs={24} lg={12}>
            <Card title="Processing Stage Metrics" size="small">
              <Table
                columns={stageColumns}
                dataSource={stageMetrics}
                rowKey="stage"
                pagination={false}
                size="small"
              />
            </Card>
          </Col>
        </Row>
      )}

      {/* Active Process Timeline */}
      {activeProcesses.length > 0 && (
        <Card title="Active End-to-End Processes" size="small" style={{ marginTop: 16 }}>
          {activeProcesses.map(process => (
            <div key={process.process_id} style={{ marginBottom: 16 }}>
              <Row justify="space-between" align="middle">
                <Col>
                  <strong>{process.name}</strong>
                  <Badge 
                    status={process.sla_status === 'on_track' ? 'success' : 'warning'}
                    text={process.sla_status.replace('_', ' ').toUpperCase()}
                    style={{ marginLeft: 8 }}
                  />
                </Col>
                <Col>
                  <Button 
                    type="link" 
                    size="small"
                    onClick={() => onProcessClick && onProcessClick(process.process_id)}
                  >
                    View Details
                  </Button>
                </Col>
              </Row>
              
              <Progress 
                percent={process.progress_percentage} 
                status={process.sla_status === 'breached' ? 'exception' : 'active'}
                style={{ marginTop: 8 }}
              />
              
              <div style={{ marginTop: 8, fontSize: 12, color: '#666' }}>
                Current Stage: <strong>{process.current_stage.replace('_', ' ')}</strong> | 
                Efficiency: <strong>{process.efficiency_score}%</strong> |
                ETA: <strong>{process.estimated_completion.toLocaleTimeString()}</strong>
              </div>

              {process.bottlenecks.length > 0 && (
                <Alert
                  type="warning"
                  message={`Bottleneck: ${process.bottlenecks[0].stage} stage delayed by ${process.bottlenecks[0].delay_percentage.toFixed(0)}%`}
                  size="small"
                  style={{ marginTop: 8 }}
                  action={
                    <Button 
                      size="small" 
                      type="link"
                      onClick={() => onBottleneckClick && onBottleneckClick(process.bottlenecks[0])}
                    >
                      Analyze
                    </Button>
                  }
                />
              )}
            </div>
          ))}
        </Card>
      )}
    </div>
  );
};

export default CrossRolePerformanceMonitor;