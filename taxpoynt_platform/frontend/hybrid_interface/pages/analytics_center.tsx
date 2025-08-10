/**
 * Analytics Center Page (Hybrid Interface)
 * ========================================
 * 
 * Comprehensive analytics hub that provides cross-role insights,
 * performance metrics, and business intelligence across SI and APP operations.
 * 
 * Features:
 * - Cross-role performance analytics
 * - Business intelligence dashboards
 * - Comparative metrics (SI vs APP)
 * - Trend analysis and forecasting
 * - Custom report generation
 * - Real-time data visualization
 * 
 * @author TaxPoynt Development Team
 * @version 1.0.0
 */

import React, { useState, useEffect } from 'react';
import { 
  Card, 
  Row, 
  Col, 
  Tabs, 
  Select, 
  DatePicker, 
  Button, 
  Space,
  Statistic,
  Alert,
  Spin
} from 'antd';
import {
  BarChartOutlined,
  LineChartOutlined,
  PieChartOutlined,
  TrendingUpOutlined,
  DownloadOutlined,
  ReloadOutlined,
  FilterOutlined
} from '@ant-design/icons';

// Import analytics components
import { AnalyticsAggregator } from '../components/cross_role_analytics/AnalyticsAggregator';
import { CrossRolePerformanceMonitor } from '../components/cross_role_analytics/CrossRolePerformanceMonitor';

const { TabPane } = Tabs;
const { RangePicker } = DatePicker;
const { Option } = Select;

interface AnalyticsCenterProps {
  userRole: 'si' | 'app' | 'hybrid' | 'admin';
  organizationId: string;
}

interface AnalyticsFilters {
  dateRange: [any, any] | null;
  scope: 'si' | 'app' | 'combined';
  metrics: string[];
}

export const AnalyticsCenter: React.FC<AnalyticsCenterProps> = ({
  userRole,
  organizationId
}) => {
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');
  const [filters, setFilters] = useState<AnalyticsFilters>({
    dateRange: null,
    scope: 'combined',
    metrics: ['revenue', 'transactions', 'compliance']
  });

  const [analyticsData, setAnalyticsData] = useState<any>(null);

  useEffect(() => {
    loadAnalyticsData();
  }, [filters]);

  const loadAnalyticsData = async () => {
    setLoading(true);
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      setAnalyticsData({
        totalRevenue: 245000,
        totalTransactions: 1543,
        complianceScore: 94.2,
        growthRate: 12.5,
        topPerformingServices: ['E-Invoice Generation', 'FIRS Submission', 'Data Validation']
      });
    } catch (error) {
      console.error('Failed to load analytics data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleExportReport = () => {
    // Export logic
    console.log('Exporting analytics report...');
  };

  const handleRefreshData = () => {
    loadAnalyticsData();
  };

  return (
    <div style={{ padding: '24px' }}>
      {/* Page Header */}
      <div style={{ marginBottom: '24px' }}>
        <Row justify="space-between" align="middle">
          <Col>
            <h2 style={{ margin: 0, display: 'flex', alignItems: 'center' }}>
              <BarChartOutlined style={{ marginRight: '12px', color: '#1890ff' }} />
              Analytics Center
            </h2>
            <p style={{ margin: '4px 0 0 0', color: '#666' }}>
              Cross-role insights and performance analytics
            </p>
          </Col>
          <Col>
            <Space>
              <Button icon={<FilterOutlined />} onClick={() => {}}>
                Advanced Filters
              </Button>
              <Button icon={<ReloadOutlined />} onClick={handleRefreshData} loading={loading}>
                Refresh
              </Button>
              <Button type="primary" icon={<DownloadOutlined />} onClick={handleExportReport}>
                Export Report
              </Button>
            </Space>
          </Col>
        </Row>
      </div>

      {/* Filters Section */}
      <Card style={{ marginBottom: '24px' }} size="small">
        <Row gutter={[16, 16]} align="middle">
          <Col xs={24} sm={8}>
            <Space direction="vertical" style={{ width: '100%' }}>
              <label>Date Range</label>
              <RangePicker 
                style={{ width: '100%' }}
                value={filters.dateRange}
                onChange={(dates) => setFilters({...filters, dateRange: dates})}
              />
            </Space>
          </Col>
          
          <Col xs={24} sm={8}>
            <Space direction="vertical" style={{ width: '100%' }}>
              <label>Scope</label>
              <Select 
                style={{ width: '100%' }}
                value={filters.scope}
                onChange={(value) => setFilters({...filters, scope: value})}
              >
                <Option value="combined">Combined (SI + APP)</Option>
                <Option value="si">SI Operations Only</Option>
                <Option value="app">APP Operations Only</Option>
              </Select>
            </Space>
          </Col>
          
          <Col xs={24} sm={8}>
            <Space direction="vertical" style={{ width: '100%' }}>
              <label>Metrics</label>
              <Select 
                mode="multiple"
                style={{ width: '100%' }}
                value={filters.metrics}
                onChange={(values) => setFilters({...filters, metrics: values})}
              >
                <Option value="revenue">Revenue</Option>
                <Option value="transactions">Transactions</Option>
                <Option value="compliance">Compliance</Option>
                <Option value="performance">Performance</Option>
              </Select>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* Key Metrics Overview */}
      {analyticsData && (
        <Row gutter={[24, 24]} style={{ marginBottom: '24px' }}>
          <Col xs={24} sm={6}>
            <Card>
              <Statistic
                title="Total Revenue"
                value={analyticsData.totalRevenue}
                precision={2}
                prefix="₦"
                suffix={
                  <span style={{ fontSize: '14px', color: '#52c41a' }}>
                    <TrendingUpOutlined /> +{analyticsData.growthRate}%
                  </span>
                }
              />
            </Card>
          </Col>
          
          <Col xs={24} sm={6}>
            <Card>
              <Statistic
                title="Total Transactions"
                value={analyticsData.totalTransactions}
                suffix={
                  <span style={{ fontSize: '14px', color: '#1890ff' }}>
                    this month
                  </span>
                }
              />
            </Card>
          </Col>
          
          <Col xs={24} sm={6}>
            <Card>
              <Statistic
                title="Compliance Score"
                value={analyticsData.complianceScore}
                precision={1}
                suffix="%"
                valueStyle={{ color: analyticsData.complianceScore >= 90 ? '#52c41a' : '#fa8c16' }}
              />
            </Card>
          </Col>
          
          <Col xs={24} sm={6}>
            <Card>
              <Statistic
                title="Growth Rate"
                value={analyticsData.growthRate}
                precision={1}
                suffix="%"
                prefix={<TrendingUpOutlined />}
                valueStyle={{ color: '#52c41a' }}
              />
            </Card>
          </Col>
        </Row>
      )}

      {/* Main Analytics Content */}
      <Spin spinning={loading}>
        <Tabs activeKey={activeTab} onChange={setActiveTab}>
          <TabPane
            tab={
              <span>
                <PieChartOutlined />
                Overview
              </span>
            }
            key="overview"
          >
            <Row gutter={[24, 24]}>
              <Col xs={24} lg={12}>
                <AnalyticsAggregator 
                  currentView={filters.scope}
                  organizationId={organizationId}
                  userRole={userRole}
                />
              </Col>
              
              <Col xs={24} lg={12}>
                <CrossRolePerformanceMonitor
                  scope={filters.scope}
                  organizationId={organizationId}
                  dateRange={filters.dateRange}
                />
              </Col>
            </Row>
          </TabPane>

          <TabPane
            tab={
              <span>
                <LineChartOutlined />
                Performance Trends
              </span>
            }
            key="trends"
          >
            <Card title="Performance Trends Analysis">
              <CrossRolePerformanceMonitor
                scope={filters.scope}
                organizationId={organizationId}
                dateRange={filters.dateRange}
                showTrends={true}
              />
            </Card>
          </TabPane>

          <TabPane
            tab={
              <span>
                <BarChartOutlined />
                Comparative Analysis
              </span>
            }
            key="comparison"
          >
            <Alert
              type="info"
              message="Comparative Analysis"
              description="Compare performance metrics between SI and APP operations to identify opportunities for optimization."
              style={{ marginBottom: '24px' }}
            />
            
            <Row gutter={[24, 24]}>
              <Col span={24}>
                <Card title="SI vs APP Performance Comparison">
                  <AnalyticsAggregator 
                    currentView="combined"
                    organizationId={organizationId}
                    userRole={userRole}
                    showComparison={true}
                  />
                </Card>
              </Col>
            </Row>
          </TabPane>

          <TabPane
            tab={
              <span>
                <TrendingUpOutlined />
                Business Intelligence
              </span>
            }
            key="intelligence"
          >
            <Alert
              type="warning"
              message="Advanced Analytics"
              description="AI-powered insights and predictive analytics will be available in the next release."
              style={{ marginBottom: '24px' }}
            />
            
            <Card title="Business Intelligence Dashboard" style={{ textAlign: 'center', padding: '48px' }}>
              <p style={{ fontSize: '16px', color: '#666' }}>
                Advanced BI features coming soon...
              </p>
            </Card>
          </TabPane>
        </Tabs>
      </Spin>
    </div>
  );
};

export default AnalyticsCenter;