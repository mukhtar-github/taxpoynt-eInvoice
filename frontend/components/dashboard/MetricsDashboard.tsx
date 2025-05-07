import React from 'react';
import { Container, Row, Col } from '../ui/Grid';
import { Card, CardHeader, CardContent, MetricCard } from '../ui/Card';
import { Typography } from '../ui/Typography';
import { Badge } from '../ui/Badge';

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
      <div className="py-6">
        <Typography.Heading level="h1" className="mb-6">Dashboard</Typography.Heading>
        
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

        {/* Main Dashboard Content */}
        <div className="mt-8">
          <Row gap={6}>
            {/* Main Activity Section */}
            <Col span={12} lg={8}>
              <Card className="mb-6">
                <CardHeader 
                  title="Recent Activity" 
                  subtitle="Latest system events and transactions"
                />
                <CardContent>
                  <div className="space-y-4">
                    {recentActivity.map(item => (
                      <div key={item.id} className="flex justify-between items-center p-3 bg-background-alt rounded-md">
                        <div>
                          <Typography.Text weight="medium">{item.description}</Typography.Text>
                          <Typography.Text variant="secondary" size="sm">{item.timestamp}</Typography.Text>
                        </div>
                        <Badge 
                          variant={
                            item.status === 'success' ? 'success' : 
                            item.status === 'error' ? 'destructive' : 
                            'secondary'
                          }
                        >
                          {item.status}
                        </Badge>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
              {/* Invoice Summary Card */}
              <Card variant="default">
                <CardHeader 
                  title="Invoice Processing Status" 
                  subtitle="Last 30 days activity"
                />
                <CardContent>
                  <div className="h-64 flex items-center justify-center bg-background-alt rounded-md">
                    <Typography.Text variant="secondary">Chart placeholder</Typography.Text>
                  </div>
                </CardContent>
              </Card>
            </Col>
            {/* Recent Activity Card */}
            <Col span={12} lg={4}>
              <Card variant="default" className="h-full">
                <CardHeader 
                  title="Integration Status" 
                  subtitle="Current status of connected systems"
                />
                <CardContent>
                  <div className="overflow-x-auto">
                    <table className="w-full border-collapse text-sm">
                      <thead>
                        <tr className="border-b-2 border-border">
                          <th className="text-left p-3 font-semibold">Integration</th>
                          <th className="text-left p-3 font-semibold">Status</th>
                          <th className="text-left p-3 font-semibold">Last Sync</th>
                          <th className="text-left p-3 font-semibold">Transactions</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr className="border-b border-border">
                          <td className="p-3">Odoo ERP</td>
                          <td className="p-3">
                            <Badge variant="success">Active</Badge>
                          </td>
                          <td className="p-3">5 minutes ago</td>
                          <td className="p-3">1,245</td>
                        </tr>
                        <tr className="border-b border-border">
                          <td className="p-3">FIRS API</td>
                          <td className="p-3">
                            <Badge variant="success">Active</Badge>
                          </td>
                          <td className="p-3">15 minutes ago</td>
                          <td className="p-3">2,547</td>
                        </tr>
                        <tr>
                          <td className="p-3">Legacy System</td>
                          <td className="p-3">
                            <Badge variant="warning">Degraded</Badge>
                          </td>
                          <td className="p-3">3 hours ago</td>
                          <td className="p-3">128</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </CardContent>
              </Card>
            </Col>
          </Row>
        </div>
      </div>
    </Container>
  );
};

export default MetricsDashboard;