import React from 'react';
import { Container, Row, Col } from '../ui/Grid';
import { Card, CardHeader, CardContent, MetricCard } from '../ui/Card';

// Mock data for the dashboard
const mockMetrics = {
  totalInvoices: {
    title: 'Total Invoices',
    value: '2,547',
    change: {
      value: '12.5%',
      type: 'increase' as const
    }
  },
  pendingInvoices: {
    title: 'Pending Invoices',
    value: '128',
    change: {
      value: '3.2%',
      type: 'decrease' as const
    }
  },
  successRate: {
    title: 'Success Rate',
    value: '98.4%',
    change: {
      value: '0.7%',
      type: 'increase' as const
    }
  },
  totalValue: {
    title: 'Total Value',
    value: '₦ 4.5M',
    change: {
      value: '15.3%',
      type: 'increase' as const
    }
  }
};

// Recent activity mock data
const recentActivity = [
  { id: 1, description: 'Invoice #INV-3847 processed successfully', timestamp: '10 minutes ago', status: 'success' },
  { id: 2, description: 'Invoice #INV-3846 validation failed', timestamp: '25 minutes ago', status: 'error' },
  { id: 3, description: 'Integration with Odoo updated', timestamp: '1 hour ago', status: 'info' },
  { id: 4, description: 'Invoice #INV-3845 processed successfully', timestamp: '2 hours ago', status: 'success' },
  { id: 5, description: 'System maintenance completed', timestamp: '5 hours ago', status: 'info' },
];

const MetricsDashboard: React.FC = () => {
  return (
    <Container>
      <div style={{ padding: 'var(--spacing-6) 0' }}>
        <h1 style={{ marginBottom: 'var(--spacing-6)' }}>Dashboard</h1>
        
        {/* Metrics Cards */}
        <Row gap={6}>
          <Col span={12} md={6} lg={3}>
            <MetricCard 
              title={mockMetrics.totalInvoices.title}
              value={mockMetrics.totalInvoices.value}
              change={mockMetrics.totalInvoices.change}
            />
          </Col>
          <Col span={12} md={6} lg={3}>
            <MetricCard 
              title={mockMetrics.pendingInvoices.title}
              value={mockMetrics.pendingInvoices.value}
              change={mockMetrics.pendingInvoices.change}
            />
          </Col>
          <Col span={12} md={6} lg={3}>
            <MetricCard 
              title={mockMetrics.successRate.title}
              value={mockMetrics.successRate.value}
              change={mockMetrics.successRate.change}
            />
          </Col>
          <Col span={12} md={6} lg={3}>
            <MetricCard 
              title={mockMetrics.totalValue.title}
              value={mockMetrics.totalValue.value}
              change={mockMetrics.totalValue.change}
            />
          </Col>
        </Row>
        
        {/* Summary and Activity Cards */}
        <Row gap={6} style={{ marginTop: 'var(--spacing-8)' }}>
          {/* Invoice Summary Card */}
          <Col span={12} lg={8}>
            <Card variant="default">
              <CardHeader 
                title="Invoice Processing Status" 
                subtitle="Last 30 days activity"
              />
              <CardContent>
                <div style={{ height: '250px', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'var(--color-background-alt)', borderRadius: 'var(--border-radius-md)' }}>
                  <p style={{ color: 'var(--color-text-secondary)' }}>Chart placeholder</p>
                </div>
              </CardContent>
            </Card>
          </Col>
          
          {/* Recent Activity Card */}
          <Col span={12} lg={4}>
            <Card variant="default" style={{ height: '100%' }}>
              <CardHeader 
                title="Recent Activity" 
                subtitle="System events and notifications"
              />
              <CardContent>
                <div>
                  {recentActivity.map(activity => (
                    <div 
                      key={activity.id} 
                      style={{ 
                        padding: 'var(--spacing-3) 0',
                        borderBottom: activity.id !== recentActivity.length ? '1px solid var(--color-border)' : 'none',
                      }}
                    >
                      <div style={{ 
                        display: 'flex', 
                        alignItems: 'flex-start'
                      }}>
                        <div 
                          style={{ 
                            width: '8px', 
                            height: '8px', 
                            borderRadius: '50%', 
                            backgroundColor: 
                              activity.status === 'success' ? 'var(--color-success)' : 
                              activity.status === 'error' ? 'var(--color-error)' : 
                              'var(--color-info)',
                            marginTop: '6px',
                            marginRight: 'var(--spacing-3)',
                          }} 
                        />
                        <div>
                          <p style={{ 
                            fontSize: 'var(--font-size-sm)',
                            margin: 0,
                            marginBottom: 'var(--spacing-1)',
                          }}>
                            {activity.description}
                          </p>
                          <span style={{ 
                            fontSize: 'var(--font-size-xs)',
                            color: 'var(--color-text-muted)', 
                          }}>
                            {activity.timestamp}
                          </span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </Col>
        </Row>
        
        {/* Integration Status Card */}
        <Row style={{ marginTop: 'var(--spacing-8)' }}>
          <Col span={12}>
            <Card variant="default">
              <CardHeader 
                title="Integration Status" 
                subtitle="Current status of connected systems"
              />
              <CardContent>
                <div style={{ overflowX: 'auto' }}>
                  <table style={{ 
                    width: '100%', 
                    borderCollapse: 'collapse',
                    fontSize: 'var(--font-size-sm)',
                  }}>
                    <thead>
                      <tr style={{ borderBottom: '2px solid var(--color-border)' }}>
                        <th style={{ textAlign: 'left', padding: 'var(--spacing-3)', fontWeight: 'var(--font-weight-semibold)' }}>Integration</th>
                        <th style={{ textAlign: 'left', padding: 'var(--spacing-3)', fontWeight: 'var(--font-weight-semibold)' }}>Status</th>
                        <th style={{ textAlign: 'left', padding: 'var(--spacing-3)', fontWeight: 'var(--font-weight-semibold)' }}>Last Sync</th>
                        <th style={{ textAlign: 'left', padding: 'var(--spacing-3)', fontWeight: 'var(--font-weight-semibold)' }}>Transactions</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr style={{ borderBottom: '1px solid var(--color-border)' }}>
                        <td style={{ padding: 'var(--spacing-3)' }}>Odoo ERP</td>
                        <td style={{ padding: 'var(--spacing-3)' }}>
                          <span style={{ 
                            backgroundColor: 'var(--color-success-light)', 
                            color: 'var(--color-success)', 
                            padding: 'var(--spacing-1) var(--spacing-2)',
                            borderRadius: 'var(--border-radius-full)',
                            fontSize: 'var(--font-size-xs)',
                            fontWeight: 'var(--font-weight-medium)',
                          }}>
                            Active
                          </span>
                        </td>
                        <td style={{ padding: 'var(--spacing-3)' }}>5 minutes ago</td>
                        <td style={{ padding: 'var(--spacing-3)' }}>1,245</td>
                      </tr>
                      <tr style={{ borderBottom: '1px solid var(--color-border)' }}>
                        <td style={{ padding: 'var(--spacing-3)' }}>FIRS API</td>
                        <td style={{ padding: 'var(--spacing-3)' }}>
                          <span style={{ 
                            backgroundColor: 'var(--color-success-light)', 
                            color: 'var(--color-success)', 
                            padding: 'var(--spacing-1) var(--spacing-2)',
                            borderRadius: 'var(--border-radius-full)',
                            fontSize: 'var(--font-size-xs)',
                            fontWeight: 'var(--font-weight-medium)',
                          }}>
                            Active
                          </span>
                        </td>
                        <td style={{ padding: 'var(--spacing-3)' }}>15 minutes ago</td>
                        <td style={{ padding: 'var(--spacing-3)' }}>2,547</td>
                      </tr>
                      <tr>
                        <td style={{ padding: 'var(--spacing-3)' }}>Legacy System</td>
                        <td style={{ padding: 'var(--spacing-3)' }}>
                          <span style={{ 
                            backgroundColor: 'var(--color-warning-light)', 
                            color: 'var(--color-warning)', 
                            padding: 'var(--spacing-1) var(--spacing-2)',
                            borderRadius: 'var(--border-radius-full)',
                            fontSize: 'var(--font-size-xs)',
                            fontWeight: 'var(--font-weight-medium)',
                          }}>
                            Degraded
                          </span>
                        </td>
                        <td style={{ padding: 'var(--spacing-3)' }}>3 hours ago</td>
                        <td style={{ padding: 'var(--spacing-3)' }}>128</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          </Col>
        </Row>
      </div>
    </Container>
  );
};

export default MetricsDashboard; 