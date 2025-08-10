/**
 * Combined Metrics Grid Component
 * ===============================
 * 
 * Displays comprehensive metrics combining data from both SI and APP interfaces
 * in a responsive grid layout with real-time updates and trend indicators.
 * 
 * Features:
 * - Real-time metric updates
 * - SI and APP metric comparison
 * - Trend analysis and indicators
 * - Interactive metric cards
 * - Performance benchmarking
 * - Alert integration
 * 
 * @author TaxPoynt Development Team
 * @version 1.0.0
 */

import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Statistic, Badge, Tooltip, Progress, Space, Button } from 'antd';
import {
  ArrowUpOutlined,
  ArrowDownOutlined,
  TrendingUpOutlined,
  TrendingDownOutlined,
  IntegrationOutlined,
  SendOutlined,
  ShieldCheckOutlined,
  CheckCircleOutlined,
  ExclamationTriangleOutlined,
  InfoCircleOutlined,
  ReloadOutlined
} from '@ant-design/icons';

import type { UnifiedDashboardMetrics, DashboardComponentProps } from '../../types';

interface CombinedMetricsGridProps extends DashboardComponentProps {
  metrics: UnifiedDashboardMetrics | null;
  showTrends?: boolean;
  compactView?: boolean;
  onMetricClick?: (metricKey: string, source: 'si' | 'app' | 'hybrid') => void;
}

interface MetricTrend {
  direction: 'up' | 'down' | 'stable';
  percentage: number;
  period: string;
}

interface MetricDefinition {
  key: string;
  title: string;
  description: string;
  source: 'si' | 'app' | 'hybrid' | 'cross_role';
  format: 'number' | 'percentage' | 'duration' | 'currency';
  thresholds: {
    excellent: number;
    good: number;
    warning: number;
  };
  icon: React.ReactNode;
}

const METRIC_DEFINITIONS: MetricDefinition[] = [
  // SI Metrics
  {
    key: 'si_processing_success_rate',
    title: 'SI Processing Success Rate',
    description: 'Percentage of successfully processed documents through SI interface',
    source: 'si',
    format: 'percentage',
    thresholds: { excellent: 98, good: 95, warning: 90 },
    icon: <IntegrationOutlined />
  },
  {
    key: 'si_active_connections',
    title: 'Active SI Connections',
    description: 'Number of currently active system integrations',
    source: 'si',
    format: 'number',
    thresholds: { excellent: 40, good: 30, warning: 20 },
    icon: <IntegrationOutlined />
  },
  {
    key: 'si_documents_processed_today',
    title: 'Documents Processed Today',
    description: 'Total number of documents processed through SI today',
    source: 'si',
    format: 'number',
    thresholds: { excellent: 2000, good: 1000, warning: 500 },
    icon: <CheckCircleOutlined />
  },
  {
    key: 'si_compliance_score',
    title: 'SI Compliance Score',
    description: 'Overall compliance score for SI operations',
    source: 'si',
    format: 'percentage',
    thresholds: { excellent: 95, good: 90, warning: 80 },
    icon: <ShieldCheckOutlined />
  },

  // APP Metrics
  {
    key: 'app_transmission_success_rate',
    title: 'APP Transmission Success',
    description: 'Percentage of successful FIRS transmissions',
    source: 'app',
    format: 'percentage',
    thresholds: { excellent: 98, good: 95, warning: 90 },
    icon: <SendOutlined />
  },
  {
    key: 'app_total_transmissions',
    title: 'Total Transmissions',
    description: 'Total number of documents transmitted to FIRS',
    source: 'app',
    format: 'number',
    thresholds: { excellent: 2000, good: 1000, warning: 500 },
    icon: <SendOutlined />
  },
  {
    key: 'app_pending_transmissions',
    title: 'Pending Transmissions',
    description: 'Number of documents waiting for transmission',
    source: 'app',
    format: 'number',
    thresholds: { excellent: 10, good: 25, warning: 50 },
    icon: <ExclamationTriangleOutlined />
  },
  {
    key: 'app_security_score',
    title: 'Security Score',
    description: 'Overall security compliance score for APP operations',
    source: 'app',
    format: 'percentage',
    thresholds: { excellent: 95, good: 90, warning: 80 },
    icon: <ShieldCheckOutlined />
  },

  // Hybrid Metrics
  {
    key: 'hybrid_end_to_end_completion_rate',
    title: 'End-to-End Success Rate',
    description: 'Percentage of documents successfully processed from SI to APP',
    source: 'hybrid',
    format: 'percentage',
    thresholds: { excellent: 95, good: 90, warning: 85 },
    icon: <TrendingUpOutlined />
  },
  {
    key: 'hybrid_unified_compliance_score',
    title: 'Unified Compliance Score',
    description: 'Combined compliance score across SI and APP operations',
    source: 'hybrid',
    format: 'percentage',
    thresholds: { excellent: 95, good: 90, warning: 80 },
    icon: <CheckCircleOutlined />
  },

  // Cross-Role Metrics
  {
    key: 'cross_role_handoff_success_rate',
    title: 'SI to APP Handoff Success',
    description: 'Success rate of document handoffs from SI to APP',
    source: 'cross_role',
    format: 'percentage',
    thresholds: { excellent: 98, good: 95, warning: 90 },
    icon: <ArrowUpOutlined />
  },
  {
    key: 'cross_role_workflow_efficiency',
    title: 'Workflow Efficiency',
    description: 'Overall efficiency of cross-role workflow orchestration',
    source: 'cross_role',
    format: 'percentage',
    thresholds: { excellent: 95, good: 90, warning: 85 },
    icon: <TrendingUpOutlined />
  }
];

export const CombinedMetricsGrid: React.FC<CombinedMetricsGridProps> = ({
  metrics,
  showTrends = true,
  compactView = false,
  onMetricClick,
  refreshInterval = 30000,
  className,
  ...props
}) => {
  const [trends, setTrends] = useState<Record<string, MetricTrend>>({});
  const [loading, setLoading] = useState(false);

  // Generate mock trends for demonstration
  useEffect(() => {
    if (metrics) {
      const mockTrends: Record<string, MetricTrend> = {};
      METRIC_DEFINITIONS.forEach(def => {
        mockTrends[def.key] = {
          direction: Math.random() > 0.5 ? 'up' : Math.random() > 0.3 ? 'down' : 'stable',
          percentage: Math.round((Math.random() * 10 + 1) * 10) / 10,
          period: '24h'
        };
      });
      setTrends(mockTrends);
    }
  }, [metrics]);

  const getMetricValue = (metricKey: string): number => {
    if (!metrics) return 0;

    const keyMap: Record<string, number> = {
      'si_processing_success_rate': metrics.si_metrics.processing_success_rate,
      'si_active_connections': metrics.si_metrics.active_connections,
      'si_documents_processed_today': metrics.si_metrics.documents_processed_today,
      'si_compliance_score': metrics.si_metrics.compliance_score,
      'app_transmission_success_rate': metrics.app_metrics.transmission_success_rate,
      'app_total_transmissions': metrics.app_metrics.total_transmissions,
      'app_pending_transmissions': metrics.app_metrics.pending_transmissions,
      'app_security_score': metrics.app_metrics.security_score,
      'hybrid_end_to_end_completion_rate': metrics.hybrid_metrics.end_to_end_completion_rate,
      'hybrid_unified_compliance_score': metrics.hybrid_metrics.unified_compliance_score,
      'cross_role_handoff_success_rate': metrics.cross_role_metrics.handoff_success_rate,
      'cross_role_workflow_efficiency': metrics.cross_role_metrics.workflow_orchestration_efficiency
    };

    return keyMap[metricKey] || 0;
  };

  const getMetricColor = (metricKey: string, value: number): string => {
    const definition = METRIC_DEFINITIONS.find(def => def.key === metricKey);
    if (!definition) return '#666';

    const { thresholds } = definition;
    
    // For metrics where lower is better (like pending_transmissions)
    const isInverse = metricKey.includes('pending') || metricKey.includes('failed');
    
    if (isInverse) {
      if (value <= thresholds.excellent) return '#52c41a';
      if (value <= thresholds.good) return '#faad14';
      return '#ff4d4f';
    } else {
      if (value >= thresholds.excellent) return '#52c41a';
      if (value >= thresholds.good) return '#faad14';
      return '#ff4d4f';
    }
  };

  const getTrendIcon = (trend: MetricTrend) => {
    switch (trend.direction) {
      case 'up':
        return <ArrowUpOutlined style={{ color: '#52c41a' }} />;
      case 'down':
        return <ArrowDownOutlined style={{ color: '#ff4d4f' }} />;
      default:
        return <TrendingUpOutlined style={{ color: '#666' }} />;
    }
  };

  const getSourceColor = (source: string): string => {
    switch (source) {
      case 'si': return '#722ed1';
      case 'app': return '#1890ff';
      case 'hybrid': return '#13c2c2';
      case 'cross_role': return '#fa8c16';
      default: return '#666';
    }
  };

  const handleMetricClick = (definition: MetricDefinition) => {
    if (onMetricClick) {
      onMetricClick(definition.key, definition.source as any);
    }
  };

  const renderMetricCard = (definition: MetricDefinition) => {
    const value = getMetricValue(definition.key);
    const trend = trends[definition.key];
    const color = getMetricColor(definition.key, value);

    return (
      <Col 
        xs={24} 
        sm={compactView ? 12 : 24} 
        md={compactView ? 8 : 12} 
        lg={compactView ? 6 : 8} 
        key={definition.key}
      >
        <Card 
          size={compactView ? 'small' : 'default'}
          hoverable
          onClick={() => handleMetricClick(definition)}
          style={{ cursor: onMetricClick ? 'pointer' : 'default' }}
          bodyStyle={{ padding: compactView ? '12px' : '24px' }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div style={{ flex: 1 }}>
              <div style={{ display: 'flex', alignItems: 'center', marginBottom: 8 }}>
                <Badge 
                  color={getSourceColor(definition.source)}
                  text={definition.source.toUpperCase()}
                  style={{ marginRight: 8 }}
                />
                {showTrends && trend && (
                  <Tooltip title={`${trend.direction === 'up' ? '+' : trend.direction === 'down' ? '-' : ''}${trend.percentage}% (${trend.period})`}>
                    {getTrendIcon(trend)}
                  </Tooltip>
                )}
              </div>
              
              <Statistic
                title={
                  <Tooltip title={definition.description}>
                    <span style={{ fontSize: compactView ? 12 : 14 }}>
                      {definition.title}
                      <InfoCircleOutlined style={{ marginLeft: 4, color: '#666' }} />
                    </span>
                  </Tooltip>
                }
                value={value}
                suffix={definition.format === 'percentage' ? '%' : undefined}
                precision={definition.format === 'percentage' ? 1 : 0}
                valueStyle={{ 
                  color, 
                  fontSize: compactView ? 18 : 24
                }}
                prefix={definition.icon}
              />

              {/* Performance indicator */}
              {!compactView && (
                <div style={{ marginTop: 8 }}>
                  <Progress
                    percent={definition.format === 'percentage' ? value : Math.min((value / definition.thresholds.excellent) * 100, 100)}
                    showInfo={false}
                    strokeColor={color}
                    size="small"
                    trailColor="#f0f0f0"
                  />
                </div>
              )}
            </div>
          </div>
        </Card>
      </Col>
    );
  };

  if (!metrics) {
    return (
      <Card className={className} {...props}>
        <div style={{ textAlign: 'center', padding: '40px 0' }}>
          <ReloadOutlined spin style={{ fontSize: 24, marginBottom: 16 }} />
          <p>Loading metrics...</p>
        </div>
      </Card>
    );
  }

  return (
    <div className={`combined-metrics-grid ${className || ''}`} {...props}>
      {!compactView && (
        <div style={{ marginBottom: 16 }}>
          <Row justify="space-between" align="middle">
            <Col>
              <h3 style={{ margin: 0 }}>System Performance Metrics</h3>
              <p style={{ margin: '4px 0 0 0', color: '#666' }}>
                Real-time performance indicators across all systems
              </p>
            </Col>
            <Col>
              <Space>
                {showTrends && (
                  <Badge status="processing" text="Trends: 24h" />
                )}
                <Badge status="success" text={`Updated: ${metrics.timestamp.toLocaleTimeString()}`} />
              </Space>
            </Col>
          </Row>
        </div>
      )}

      <Row gutter={[16, 16]}>
        {METRIC_DEFINITIONS.map(renderMetricCard)}
      </Row>

      {!compactView && (
        <Card size="small" style={{ marginTop: 16 }}>
          <Row gutter={16}>
            <Col xs={24} sm={6}>
              <Statistic
                title="System Health"
                value={Math.round(
                  (metrics.si_metrics.processing_success_rate + 
                   metrics.app_metrics.transmission_success_rate + 
                   metrics.hybrid_metrics.end_to_end_completion_rate) / 3
                )}
                suffix="%"
                prefix={<CheckCircleOutlined />}
                valueStyle={{ color: '#52c41a' }}
              />
            </Col>
            <Col xs={24} sm={6}>
              <Statistic
                title="Total Documents"
                value={metrics.si_metrics.documents_processed_today + metrics.app_metrics.total_transmissions}
                prefix={<TrendingUpOutlined />}
                valueStyle={{ color: '#1890ff' }}
              />
            </Col>
            <Col xs={24} sm={6}>
              <Statistic
                title="Avg Processing Time"
                value={metrics.si_metrics.average_processing_time}
                suffix="min"
                precision={1}
                prefix={<ExclamationTriangleOutlined />}
                valueStyle={{ color: '#fa8c16' }}
              />
            </Col>
            <Col xs={24} sm={6}>
              <Statistic
                title="Avg Response Time"
                value={metrics.app_metrics.average_response_time}
                suffix="sec"
                precision={1}
                prefix={<SendOutlined />}
                valueStyle={{ color: '#722ed1' }}
              />
            </Col>
          </Row>
        </Card>
      )}
    </div>
  );
};

export default CombinedMetricsGrid;