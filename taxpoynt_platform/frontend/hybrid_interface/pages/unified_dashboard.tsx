/**
 * Unified Dashboard Page (Hybrid Interface)
 * ========================================
 * 
 * Main hybrid interface dashboard that combines SI and APP activities
 * into a unified view for users who need visibility across both roles.
 * 
 * Features:
 * - Combined metrics from SI and APP interfaces
 * - Role switching capabilities
 * - Cross-role analytics and insights
 * - Unified activity timeline
 * - Platform compliance monitoring (admin-only)
 * 
 * @author TaxPoynt Development Team
 * @version 1.0.0
 */

import React, { useState, useEffect } from 'react';
import { Layout, Row, Col, Card, Switch, Alert, Button, Space } from 'antd';
import {
  DashboardOutlined,
  SwapOutlined,
  BarChartOutlined,
  SettingOutlined,
  BellOutlined
} from '@ant-design/icons';

// Import hybrid interface components
import { UnifiedDashboard } from '../components/unified_dashboard/UnifiedDashboard';
import { CombinedMetricsGrid } from '../components/unified_dashboard/CombinedMetricsGrid';
import { RoleSwitcher } from '../components/unified_dashboard/RoleSwitcher';
import { AnalyticsAggregator } from '../components/cross_role_analytics/AnalyticsAggregator';
import { PlatformComplianceDashboard } from '../components/compliance_overview/PlatformComplianceDashboard';

const { Header, Content, Sider } = Layout;

interface UnifiedDashboardPageProps {
  userRole: 'si' | 'app' | 'hybrid' | 'admin';
  organizationId: string;
}

export const UnifiedDashboardPage: React.FC<UnifiedDashboardPageProps> = ({
  userRole,
  organizationId
}) => {
  const [currentView, setCurrentView] = useState<'si' | 'app' | 'combined'>('combined');
  const [showNotifications, setShowNotifications] = useState(true);
  const [collapsed, setCollapsed] = useState(false);

  // Check if user has admin privileges for platform compliance
  const hasAdminAccess = userRole === 'admin' || userRole === 'hybrid';

  return (
    <Layout style={{ minHeight: '100vh' }}>
      {/* Header */}
      <Header style={{ background: '#fff', padding: '0 24px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <DashboardOutlined style={{ fontSize: '24px', marginRight: '12px', color: '#1890ff' }} />
          <h1 style={{ margin: 0, fontSize: '20px' }}>TaxPoynt Unified Dashboard</h1>
        </div>
        
        <Space>
          <RoleSwitcher 
            currentRole={currentView} 
            onRoleChange={setCurrentView}
            availableRoles={['si', 'app', 'combined']}
          />
          <Button icon={<BellOutlined />} onClick={() => setShowNotifications(!showNotifications)}>
            Notifications
          </Button>
          <Button icon={<SettingOutlined />}>Settings</Button>
        </Space>
      </Header>

      <Layout>
        {/* Sidebar */}
        <Sider 
          collapsible 
          collapsed={collapsed} 
          onCollapse={setCollapsed}
          style={{ background: '#fff' }}
        >
          <div style={{ padding: '16px' }}>
            <Card size="small" title="Quick Actions">
              <Button type="primary" block style={{ marginBottom: '8px' }}>
                <SwapOutlined /> Switch Role
              </Button>
              <Button block style={{ marginBottom: '8px' }}>
                <BarChartOutlined /> Analytics
              </Button>
              {hasAdminAccess && (
                <Button block>
                  <SettingOutlined /> Platform Admin
                </Button>
              )}
            </Card>
          </div>
        </Sider>

        {/* Main Content */}
        <Layout style={{ padding: '24px' }}>
          <Content>
            {/* Notification Bar */}
            {showNotifications && (
              <Alert
                type="info"
                message="Welcome to your Unified Dashboard"
                description="Monitor your SI and APP activities from a single interface. Switch between roles using the controls above."
                closable
                onClose={() => setShowNotifications(false)}
                style={{ marginBottom: '24px' }}
              />
            )}

            {/* Combined Metrics Grid */}
            <Row gutter={[24, 24]} style={{ marginBottom: '24px' }}>
              <Col span={24}>
                <CombinedMetricsGrid 
                  currentView={currentView}
                  organizationId={organizationId}
                  userRole={userRole}
                />
              </Col>
            </Row>

            {/* Main Dashboard Components */}
            <Row gutter={[24, 24]}>
              {/* Unified Dashboard */}
              <Col xs={24} lg={16}>
                <UnifiedDashboard 
                  currentView={currentView}
                  organizationId={organizationId}
                  userRole={userRole}
                />
              </Col>

              {/* Analytics Aggregator */}
              <Col xs={24} lg={8}>
                <AnalyticsAggregator 
                  currentView={currentView}
                  organizationId={organizationId}
                  userRole={userRole}
                />
              </Col>
            </Row>

            {/* Platform Compliance Dashboard - Admin Only */}
            {hasAdminAccess && (
              <Row gutter={[24, 24]} style={{ marginTop: '24px' }}>
                <Col span={24}>
                  <Card title="Platform Compliance (Admin Only)">
                    <PlatformComplianceDashboard 
                      showDetails={true}
                      className="platform-compliance-section"
                    />
                  </Card>
                </Col>
              </Row>
            )}
          </Content>
        </Layout>
      </Layout>
    </Layout>
  );
};

export default UnifiedDashboardPage;