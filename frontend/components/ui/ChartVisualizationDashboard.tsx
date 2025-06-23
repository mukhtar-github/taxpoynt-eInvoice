/**
 * Chart Visualization Dashboard - Week 7 Implementation
 * 
 * Business Intelligence & Analytics Dashboard featuring:
 * - Gradient-styled charts matching design system
 * - Responsive chart containers for mobile/desktop
 * - Interactive tooltips and data points
 * - Standardized chart types across platform
 * - Real-time data visualization capabilities
 */

import React, { useState, useMemo } from 'react';
import { 
  BarChart, 
  LineChart, 
  DoughnutChart,
  AreaChart,
  RechartsBarChart,
  ResponsiveChartContainer,
  gradientColors 
} from './Charts';
import { Card } from './Card';
import { Button } from './Button';
import { Badge } from './Badge';
import { 
  TrendingUp, 
  TrendingDown, 
  Download, 
  Filter, 
  RefreshCw,
  Calendar,
  BarChart3,
  PieChart,
  LineChart as LineChartIcon,
  Activity
} from 'lucide-react';

// Mock data for demonstration
const invoiceProcessingData = {
  labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
  datasets: [{
    label: 'Invoices Processed',
    data: [1200, 1900, 3000, 5000, 4200, 3800],
  }]
};

const revenueData = [
  { name: 'Jan', value: 4000 },
  { name: 'Feb', value: 3000 },
  { name: 'Mar', value: 5000 },
  { name: 'Apr', value: 4500 },
  { name: 'May', value: 6000 },
  { name: 'Jun', value: 5500 }
];

const integrationStatusData = {
  labels: ['Odoo ERP', 'FIRS API', 'SAP', 'QuickBooks', 'Xero'],
  datasets: [{
    label: 'Success Rate (%)',
    data: [98.5, 97.2, 99.1, 96.8, 94.3],
  }]
};

const submissionTrendsData = [
  { name: 'Week 1', successful: 1200, failed: 50, pending: 25 },
  { name: 'Week 2', successful: 1350, failed: 42, pending: 18 },
  { name: 'Week 3', successful: 1580, failed: 38, pending: 22 },
  { name: 'Week 4', successful: 1720, failed: 31, pending: 15 }
];

const complianceMetricsData = {
  labels: ['Compliant', 'Pending Review', 'Non-Compliant'],
  datasets: [{
    label: 'Compliance Status',
    data: [85, 12, 3],
    backgroundColor: [
      'rgba(16, 185, 129, 0.8)',
      'rgba(245, 158, 11, 0.8)', 
      'rgba(239, 68, 68, 0.8)'
    ],
    borderColor: [
      'rgb(16, 185, 129)',
      'rgb(245, 158, 11)',
      'rgb(239, 68, 68)'
    ]
  }]
};

interface MetricCardProps {
  title: string;
  value: string | number;
  change: number;
  trend: 'up' | 'down';
  icon: React.ReactNode;
  color?: 'primary' | 'success' | 'warning' | 'error';
}

const MetricCard: React.FC<MetricCardProps> = ({ 
  title, 
  value, 
  change, 
  trend, 
  icon, 
  color = 'primary' 
}) => {
  const colorClasses = {
    primary: 'text-blue-600 bg-blue-50',
    success: 'text-green-600 bg-green-50',
    warning: 'text-amber-600 bg-amber-50',
    error: 'text-red-600 bg-red-50'
  };

  return (
    <Card className="p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600 mb-1">{title}</p>
          <p className="text-2xl font-bold text-gray-900">{value}</p>
          <div className="flex items-center mt-2">
            {trend === 'up' ? (
              <TrendingUp className="w-4 h-4 text-green-500 mr-1" />
            ) : (
              <TrendingDown className="w-4 h-4 text-red-500 mr-1" />
            )}
            <span className={`text-sm font-medium ${
              trend === 'up' ? 'text-green-600' : 'text-red-600'
            }`}>
              {change > 0 ? '+' : ''}{change}%
            </span>
            <span className="text-sm text-gray-500 ml-1">vs last month</span>
          </div>
        </div>
        <div className={`p-3 rounded-lg ${colorClasses[color]}`}>
          {icon}
        </div>
      </div>
    </Card>
  );
};

export const ChartVisualizationDashboard: React.FC = () => {
  const [timeRange, setTimeRange] = useState<'7d' | '30d' | '90d' | '1y'>('30d');
  const [chartType, setChartType] = useState<'bar' | 'line' | 'area'>('area');

  const metrics = [
    {
      title: 'Total Invoices',
      value: '24,847',
      change: 12.5,
      trend: 'up' as const,
      icon: <BarChart3 className="w-6 h-6" />,
      color: 'primary' as const
    },
    {
      title: 'Success Rate',
      value: '98.2%',
      change: 2.1,
      trend: 'up' as const,
      icon: <TrendingUp className="w-6 h-6" />,
      color: 'success' as const
    },
    {
      title: 'Revenue',
      value: '₦28.5M',
      change: 8.3,
      trend: 'up' as const,
      icon: <Activity className="w-6 h-6" />,
      color: 'primary' as const
    },
    {
      title: 'Failed Submissions',
      value: '342',
      change: -15.2,
      trend: 'down' as const,
      icon: <TrendingDown className="w-6 h-6" />,
      color: 'error' as const
    }
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Business Intelligence Dashboard</h1>
          <p className="text-gray-600 mt-1">Real-time analytics and performance metrics</p>
        </div>
        <div className="flex items-center gap-3 mt-4 sm:mt-0">
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value as any)}
            className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="7d">Last 7 Days</option>
            <option value="30d">Last 30 Days</option>
            <option value="90d">Last 90 Days</option>
            <option value="1y">Last Year</option>
          </select>
          <Button variant="outline" size="sm">
            <RefreshCw className="w-4 h-4" />
          </Button>
          <Button variant="outline" size="sm">
            <Download className="w-4 h-4" />
          </Button>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {metrics.map((metric, index) => (
          <MetricCard key={index} {...metric} />
        ))}
      </div>

      {/* Chart Selection */}
      <div className="flex items-center gap-2 mb-4">
        <span className="text-sm font-medium text-gray-700">Chart Type:</span>
        <div className="flex rounded-lg border border-gray-200 p-1">
          {(['bar', 'line', 'area'] as const).map((type) => (
            <button
              key={type}
              onClick={() => setChartType(type)}
              className={`px-3 py-1 text-sm font-medium rounded-md transition-colors ${
                chartType === type
                  ? 'bg-blue-500 text-white'
                  : 'text-gray-600 hover:text-gray-800'
              }`}
            >
              {type.charAt(0).toUpperCase() + type.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* Main Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Invoice Processing Trends */}
        <ResponsiveChartContainer
          title="Invoice Processing Trends"
          subtitle="Monthly invoice processing volume"
          height={400}
          actions={
            <div className="flex items-center gap-2">
              <Badge variant="secondary">Live</Badge>
              <Button variant="outline" size="sm">
                <Filter className="w-4 h-4" />
              </Button>
            </div>
          }
        >
          {chartType === 'bar' ? (
            <BarChart 
              data={invoiceProcessingData} 
              gradientType="primary"
              animate={true}
            />
          ) : chartType === 'line' ? (
            <LineChart 
              data={invoiceProcessingData} 
              gradientType="primary"
              animate={true}
            />
          ) : (
            <AreaChart 
              data={revenueData} 
              dataKey="value"
              gradientType="primary"
              animate={true}
            />
          )}
        </ResponsiveChartContainer>

        {/* Integration Performance */}
        <ResponsiveChartContainer
          title="Integration Performance"
          subtitle="Success rates across all integrations"
          height={400}
          actions={
            <Badge variant="success">All Systems Operational</Badge>
          }
        >
          <RechartsBarChart
            data={submissionTrendsData.map(item => ({
              name: item.name,
              value: (item.successful / (item.successful + item.failed + item.pending)) * 100
            }))}
            dataKey="value"
            gradientType="success"
            animate={true}
          />
        </ResponsiveChartContainer>

        {/* Revenue Analytics */}
        <ResponsiveChartContainer
          title="Revenue Analytics"
          subtitle="Monthly revenue from e-invoice processing"
          height={400}
          actions={
            <div className="flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-green-500" />
              <span className="text-sm font-medium text-green-600">+18.3%</span>
            </div>
          }
        >
          <AreaChart 
            data={revenueData} 
            dataKey="value"
            gradientType="success"
            animate={true}
          />
        </ResponsiveChartContainer>

        {/* Compliance Status */}
        <ResponsiveChartContainer
          title="Compliance Status"
          subtitle="Current compliance distribution"
          height={400}
          actions={
            <Badge variant="success">98.5% Compliant</Badge>
          }
        >
          <DoughnutChart 
            data={complianceMetricsData}
            gradientType="success"
          />
        </ResponsiveChartContainer>
      </div>

      {/* Submission Trends - Full Width */}
      <ResponsiveChartContainer
        title="Weekly Submission Trends"
        subtitle="Detailed breakdown of submission statuses over time"
        height={500}
        actions={
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm">
              <Calendar className="w-4 h-4 mr-2" />
              Custom Range
            </Button>
            <Button variant="outline" size="sm">
              <Download className="w-4 h-4" />
            </Button>
          </div>
        }
      >
        <AreaChart
          data={submissionTrendsData}
          dataKey="successful"
          gradientType="primary"
          animate={true}
          height={450}
        />
      </ResponsiveChartContainer>
    </div>
  );
};

export default ChartVisualizationDashboard;