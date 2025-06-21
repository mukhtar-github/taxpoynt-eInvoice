/**
 * Enhanced Dashboard Example - Week 2 Implementation
 * 
 * This component demonstrates how to use all the Week 2 dashboard enhancements:
 * - Enhanced layout with mobile bottom navigation
 * - Animated metric cards with micro-interactions
 * - Activity feed with real-time updates
 * - Quick actions floating buttons
 * - Mobile-first responsive design
 */

import React, { useState, useEffect } from 'react';
import { 
  TrendingUp, 
  FileText, 
  CheckCircle, 
  AlertTriangle,
  Users,
  Link as LinkIcon,
  Activity,
  Zap
} from 'lucide-react';

// Import our enhanced components
import { EnhancedMetricCard, MetricCardGrid } from './EnhancedMetricCard';
import { ActivityFeed, ActivityItem } from './ActivityFeed';
import { QuickActions, QuickAction } from './QuickActions';
import { Card, CardHeader, CardContent } from '../ui/Card';

// Sample data for demonstration
const generateSampleMetrics = () => ({
  totalInvoices: {
    current: 1245,
    previous: 1180,
    loading: false
  },
  weeklyTransactions: {
    current: 856,
    previous: 732,
    loading: false
  },
  monthlyRevenue: {
    current: 2456000,
    previous: 2234000,
    loading: false
  },
  successRate: {
    current: 94.6,
    previous: 91.2,
    loading: false
  }
});

const generateSampleActivities = (): ActivityItem[] => [
  {
    id: '1',
    type: 'invoice_generated',
    title: 'Invoice batch generated',
    description: '25 invoices created for HubSpot deals',
    timestamp: new Date(Date.now() - 5 * 60 * 1000), // 5 minutes ago
    metadata: {
      user: 'John Doe',
      integration: 'HubSpot',
      count: 25,
      status: 'success'
    }
  },
  {
    id: '2',
    type: 'integration_sync',
    title: 'ERP synchronization completed',
    description: 'Odoo integration synced successfully',
    timestamp: new Date(Date.now() - 15 * 60 * 1000), // 15 minutes ago
    metadata: {
      integration: 'Odoo ERP',
      count: 156,
      status: 'success'
    }
  },
  {
    id: '3',
    type: 'error',
    title: 'FIRS submission failed',
    description: 'Network timeout during submission',
    timestamp: new Date(Date.now() - 30 * 60 * 1000), // 30 minutes ago
    metadata: {
      status: 'error',
      count: 3
    }
  },
  {
    id: '4',
    type: 'user_action',
    title: 'New CRM connection added',
    description: 'Connected to HubSpot CRM instance',
    timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000), // 2 hours ago
    metadata: {
      user: 'Jane Smith',
      integration: 'HubSpot',
      status: 'success'
    }
  },
  {
    id: '5',
    type: 'system_event',
    title: 'Certificate renewed',
    description: 'Digital certificate automatically renewed',
    timestamp: new Date(Date.now() - 24 * 60 * 60 * 1000), // 1 day ago
    metadata: {
      status: 'success'
    }
  }
];

// Custom quick actions for this dashboard
const dashboardQuickActions: QuickAction[] = [
  {
    id: 'generate-irn',
    label: 'Generate IRN',
    icon: FileText,
    onClick: () => console.log('Generate IRN clicked'),
    color: 'primary',
    pulse: true
  },
  {
    id: 'sync-all',
    label: 'Sync All Integrations',
    icon: LinkIcon,
    onClick: () => console.log('Sync all clicked'),
    color: 'success'
  },
  {
    id: 'view-activity',
    label: 'Activity Log',
    icon: Activity,
    onClick: () => console.log('Activity log clicked'),
    color: 'primary'
  },
  {
    id: 'platform-tools',
    label: 'Platform Tools',
    icon: Zap,
    onClick: () => console.log('Platform tools clicked'),
    color: 'warning',
    badge: '3'
  }
];

export const EnhancedDashboardExample: React.FC = () => {
  const [metrics, setMetrics] = useState(generateSampleMetrics());
  const [activities, setActivities] = useState<ActivityItem[]>(generateSampleActivities());
  const [activitiesLoading, setActivitiesLoading] = useState(false);

  // Simulate real-time updates
  useEffect(() => {
    const interval = setInterval(() => {
      // Randomly update one metric to show animation
      const metricKeys = Object.keys(metrics) as Array<keyof typeof metrics>;
      const randomMetric = metricKeys[Math.floor(Math.random() * metricKeys.length)];
      
      setMetrics(prev => ({
        ...prev,
        [randomMetric]: {
          ...prev[randomMetric],
          previous: prev[randomMetric].current,
          current: prev[randomMetric].current + Math.floor(Math.random() * 10) - 5
        }
      }));
    }, 10000); // Update every 10 seconds

    return () => clearInterval(interval);
  }, []);

  // Handle activity refresh
  const handleActivityRefresh = async () => {
    setActivitiesLoading(true);
    
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    // Add a new random activity
    const newActivity: ActivityItem = {
      id: Date.now().toString(),
      type: 'system_event',
      title: 'System check completed',
      description: 'All systems are operating normally',
      timestamp: new Date(),
      metadata: {
        status: 'success'
      }
    };
    
    setActivities(prev => [newActivity, ...prev]);
    setActivitiesLoading(false);
  };

  // Handle load more activities
  const handleLoadMoreActivities = async () => {
    // Simulate loading more activities
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    const moreActivities = generateSampleActivities().map(activity => ({
      ...activity,
      id: `${activity.id}_${Date.now()}`,
      timestamp: new Date(activity.timestamp.getTime() - 24 * 60 * 60 * 1000) // One day older
    }));
    
    setActivities(prev => [...prev, ...moreActivities]);
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col xs:flex-row xs:items-center xs:justify-between gap-4">
        <div>
          <h1 className="text-2xl xs:text-3xl font-bold text-text-primary">
            Enhanced Dashboard
          </h1>
          <p className="text-text-secondary mt-1">
            Week 2 UI/UX improvements demonstration
          </p>
        </div>
        
        {/* Quick stats summary for mobile */}
        <div className="xs:hidden bg-primary/5 rounded-lg p-3">
          <div className="text-xs text-text-secondary uppercase tracking-wide font-medium mb-1">
            Today's Summary
          </div>
          <div className="text-lg font-bold text-primary">
            {metrics.totalInvoices.current} invoices • {metrics.successRate.current}% success
          </div>
        </div>
      </div>

      {/* Enhanced Metrics Grid */}
      <MetricCardGrid>
        <EnhancedMetricCard
          title="Total Invoices (Today)"
          value={metrics.totalInvoices.current}
          previousValue={metrics.totalInvoices.previous}
          icon={<FileText className="w-6 h-6" />}
          loading={metrics.totalInvoices.loading}
          countUp={true}
          animationDuration={2000}
          onClick={() => console.log('Invoices clicked')}
        />
        
        <EnhancedMetricCard
          title="Weekly Transactions"
          value={metrics.weeklyTransactions.current}
          previousValue={metrics.weeklyTransactions.previous}
          icon={<TrendingUp className="w-6 h-6" />}
          loading={metrics.weeklyTransactions.loading}
          countUp={true}
          animationDuration={2500}
        />
        
        <EnhancedMetricCard
          title="Monthly Revenue"
          value={metrics.monthlyRevenue.current}
          previousValue={metrics.monthlyRevenue.previous}
          prefix="₦"
          icon={<CheckCircle className="w-6 h-6" />}
          loading={metrics.monthlyRevenue.loading}
          countUp={true}
          animationDuration={3000}
          formatValue={(value) => `${(value / 1000000).toFixed(1)}M`}
        />
        
        <EnhancedMetricCard
          title="Success Rate"
          value={metrics.successRate.current}
          previousValue={metrics.successRate.previous}
          suffix="%"
          precision={1}
          icon={<AlertTriangle className="w-6 h-6" />}
          loading={metrics.successRate.loading}
          countUp={true}
          animationDuration={1500}
        />
      </MetricCardGrid>

      {/* Dashboard Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Activity Feed - Takes 2 columns on large screens */}
        <div className="lg:col-span-2">
          <ActivityFeed
            activities={activities}
            loading={activitiesLoading}
            onRefresh={handleActivityRefresh}
            onLoadMore={handleLoadMoreActivities}
            hasMore={true}
            showFilter={true}
            maxHeight="500px"
          />
        </div>
        
        {/* Side Panel */}
        <div className="space-y-6">
          {/* Quick Stats Card */}
          <Card variant="elevated">
            <CardHeader title="System Status" />
            <CardContent>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-text-secondary">FIRS API</span>
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 bg-success rounded-full"></div>
                    <span className="text-sm font-medium text-success">Online</span>
                  </div>
                </div>
                
                <div className="flex items-center justify-between">
                  <span className="text-sm text-text-secondary">Integrations</span>
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 bg-success rounded-full"></div>
                    <span className="text-sm font-medium text-success">3 Active</span>
                  </div>
                </div>
                
                <div className="flex items-center justify-between">
                  <span className="text-sm text-text-secondary">Last Sync</span>
                  <span className="text-sm font-medium text-text-primary">2 min ago</span>
                </div>
              </div>
            </CardContent>
          </Card>
          
          {/* Integration Status */}
          <Card variant="elevated">
            <CardHeader title="Active Integrations" />
            <CardContent>
              <div className="space-y-3">
                {[
                  { name: 'HubSpot CRM', status: 'syncing', count: 25 },
                  { name: 'Odoo ERP', status: 'connected', count: 156 },
                  { name: 'Square POS', status: 'error', count: 0 }
                ].map((integration, index) => (
                  <div key={index} className="flex items-center justify-between p-2 rounded-lg bg-gray-50 hover:bg-gray-100 transition-colors">
                    <div className="flex items-center gap-3">
                      <div className={`w-2 h-2 rounded-full ${
                        integration.status === 'connected' ? 'bg-success' :
                        integration.status === 'syncing' ? 'bg-warning animate-pulse' :
                        'bg-error'
                      }`} />
                      <span className="text-sm font-medium">{integration.name}</span>
                    </div>
                    <span className="text-xs text-text-secondary">
                      {integration.count} items
                    </span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Quick Actions FAB */}
      <QuickActions 
        actions={dashboardQuickActions}
        position="bottom-right"
        autoHide={true}
      />
    </div>
  );
};

export default EnhancedDashboardExample;