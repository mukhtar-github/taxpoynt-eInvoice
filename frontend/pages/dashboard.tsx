import React, { useState } from 'react';
import DashboardLayout from '../components/layouts/DashboardLayout';
import IRNStatusMonitor, { IRNStatusItem } from '../components/dashboard/IRNStatusMonitor';
import IntegrationStatus, { IntegrationItem } from '../components/dashboard/IntegrationStatus';
import TransactionMetrics, { TransactionMetricsData } from '../components/dashboard/TransactionMetrics';
import { createDataset } from '../components/ui/Charts';
import { Card, CardHeader, CardContent, CardTitle, CardDescription } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Download, Filter, RefreshCw } from 'lucide-react';

// Mock data for the dashboard
const mockIRNStatusData = {
  recentItems: [
    {
      id: '1',
      invoiceNumber: 'INV-3847',
      status: 'completed',
      timestamp: '10 minutes ago',
      businessName: 'TechNova Solutions',
    },
    {
      id: '2',
      invoiceNumber: 'INV-3846',
      status: 'failed',
      timestamp: '25 minutes ago',
      businessName: 'GlobeX Financials',
      errorMessage: 'Invalid invoice format: Missing required field "taxAmount"',
    },
    {
      id: '3',
      invoiceNumber: 'INV-3845',
      status: 'processing',
      timestamp: '30 minutes ago',
      businessName: 'Quantum Industries',
    },
    {
      id: '4',
      invoiceNumber: 'INV-3844',
      status: 'completed',
      timestamp: '45 minutes ago',
      businessName: 'Atlas Corp',
    },
    {
      id: '5',
      invoiceNumber: 'INV-3843',
      status: 'pending',
      timestamp: '1 hour ago',
      businessName: 'StellarWave Technologies',
    },
  ] as IRNStatusItem[],
  summary: {
    total: 245,
    pending: 18,
    processing: 12,
    completed: 198,
    failed: 17,
    successRate: 80.8,
  },
};

const mockIntegrationData = [
  {
    id: '1',
    name: 'Odoo ERP',
    description: 'Invoice source system integration',
    status: 'online',
    lastSyncTime: '5 minutes ago',
    responseTime: 428,
  },
  {
    id: '2',
    name: 'FIRS API',
    description: 'Nigerian tax authority integration',
    status: 'degraded',
    lastSyncTime: '15 minutes ago',
    responseTime: 1250,
    errorMessage: 'Intermittent timeout issues detected',
  },
  {
    id: '3',
    name: 'SAP Integration',
    description: 'Enterprise resource planning system',
    status: 'offline',
    lastSyncTime: '2 hours ago',
    errorMessage: 'Connection refused: Authentication failed',
  },
  {
    id: '4',
    name: 'QuickBooks',
    description: 'Financial management software',
    status: 'online',
    lastSyncTime: '30 minutes ago',
    responseTime: 312,
  },
] as IntegrationItem[];

const mockTransactionData: TransactionMetricsData = {
  daily: {
    labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
    datasets: [
      createDataset('Successful', [25, 32, 28, 42, 35, 18, 27], 'success'),
      createDataset('Failed', [5, 3, 2, 4, 3, 1, 2], 'danger'),
    ],
  },
  weekly: {
    labels: ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
    datasets: [
      createDataset('Successful', [165, 178, 195, 187], 'success'),
      createDataset('Failed', [12, 15, 8, 10], 'danger'),
    ],
  },
  monthly: {
    labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
    datasets: [
      createDataset('Transactions', [580, 620, 750, 810, 925, 890], 'primary'),
    ],
  },
  summary: {
    totalCount: 2547,
    successCount: 2430,
    failureCount: 117,
    averagePerDay: 85,
    trend: 'up' as const,
    changePercentage: 12.5,
  },
};

const Dashboard: React.FC = () => {
  const [isRefreshing, setIsRefreshing] = useState(false);

  const handleRefresh = () => {
    setIsRefreshing(true);
    // Simulate API call
    setTimeout(() => {
      setIsRefreshing(false);
    }, 1500);
  };

  return (
    <DashboardLayout>
      <div className="p-6">
        <header className="mb-8">
          <div className="flex justify-between items-center mb-4">
            <h1 className="text-2xl font-heading font-semibold">Monitoring Dashboard</h1>
            <div className="flex gap-3">
              <Button 
                variant="outline" 
                size="sm"
                className="flex items-center gap-1"
                onClick={handleRefresh}
                disabled={isRefreshing}
              >
                <RefreshCw size={14} className={isRefreshing ? 'animate-spin' : ''} />
                <span>{isRefreshing ? 'Refreshing...' : 'Refresh'}</span>
              </Button>
              <Button 
                variant="outline" 
                size="sm"
                className="flex items-center gap-1"
              >
                <Filter size={14} />
                <span>Filter</span>
              </Button>
              <Button 
                variant="default" 
                size="sm"
                className="flex items-center gap-1"
              >
                <Download size={14} />
                <span>Export</span>
              </Button>
            </div>
          </div>
          
          <div className="flex flex-wrap gap-2">
            <Badge variant="outline">Last updated: Now</Badge>
            <Badge variant="secondary">Time range: Today</Badge>
            <Badge variant="outline">Organization: All</Badge>
          </div>
        </header>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
          <Card className="md:col-span-1">
            <CardHeader>
              <CardTitle>System Health</CardTitle>
              <CardDescription>Current system status</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-sm">API Uptime</span>
                  <Badge variant="success">99.9%</Badge>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm">Database</span>
                  <Badge variant="success">Online</Badge>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm">Storage</span>
                  <Badge variant="warning">78% Used</Badge>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm">FIRS Connection</span>
                  <Badge variant="secondary">Degraded</Badge>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm">Scheduled Tasks</span>
                  <Badge variant="success">Running</Badge>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="md:col-span-2">
            <CardHeader>
              <CardTitle>Quick Summary</CardTitle>
              <CardDescription>Key metrics at a glance</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="p-3 bg-background-alt rounded-md">
                  <div className="text-sm text-text-secondary mb-1">Generated IRNs</div>
                  <div className="text-xl font-semibold">245</div>
                </div>
                <div className="p-3 bg-background-alt rounded-md">
                  <div className="text-sm text-text-secondary mb-1">Success Rate</div>
                  <div className="text-xl font-semibold">80.8%</div>
                </div>
                <div className="p-3 bg-background-alt rounded-md">
                  <div className="text-sm text-text-secondary mb-1">Active Integrations</div>
                  <div className="text-xl font-semibold">3/4</div>
                </div>
                <div className="p-3 bg-background-alt rounded-md">
                  <div className="text-sm text-text-secondary mb-1">API Calls Today</div>
                  <div className="text-xl font-semibold">1,204</div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* IRN Status Monitor */}
        <div className="mb-6">
          <IRNStatusMonitor 
            recentItems={mockIRNStatusData.recentItems}
            summary={mockIRNStatusData.summary}
            isLoading={isRefreshing}
          />
        </div>

        {/* Transaction Metrics */}
        <div className="mb-6">
          <TransactionMetrics 
            data={mockTransactionData}
            isLoading={isRefreshing}
          />
        </div>

        {/* Integration Status */}
        <div className="mb-6">
          <IntegrationStatus 
            integrations={mockIntegrationData}
            isLoading={isRefreshing}
            onRefresh={handleRefresh}
          />
        </div>
      </div>
    </DashboardLayout>
  );
};

export default Dashboard;
