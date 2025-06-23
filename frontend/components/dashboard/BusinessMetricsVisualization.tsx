/**
 * Business Metrics Visualization Component - Day 3-4 Implementation
 * 
 * Comprehensive business intelligence dashboard featuring:
 * - Revenue trends over time (line charts)
 * - Invoice status distribution (pie/donut charts)
 * - Integration performance metrics (bar charts)
 * - FIRS submission success rates (progress indicators)
 * - Geographic distribution visualization
 */

import React, { useState, useEffect, useMemo } from 'react';
import { Card, CardHeader, CardContent, CardTitle, CardDescription } from '../ui/Card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/Tabs';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';
import { 
  LineChart, 
  BarChart, 
  DoughnutChart,
  AreaChart,
  ResponsiveChartContainer 
} from '../ui/Charts';
import { 
  TrendingUp, 
  TrendingDown, 
  DollarSign, 
  FileText, 
  CheckCircle2, 
  AlertCircle,
  BarChart3,
  PieChart,
  Download,
  RefreshCw,
  Calendar,
  MapPin,
  Users,
  Activity
} from 'lucide-react';

// Data interfaces
interface RevenueData {
  labels: string[];
  datasets: Array<{
    label: string;
    data: number[];
    backgroundColor?: string;
    borderColor?: string;
    borderWidth?: number;
    fill?: boolean;
    tension?: number;
  }>;
}

interface InvoiceStatusData {
  labels: string[];
  datasets: Array<{
    label: string;
    data: number[];
    backgroundColor: string[];
    borderColor?: string[];
    borderWidth?: number;
  }>;
}

interface IntegrationPerformanceData {
  labels: string[];
  datasets: Array<{
    label: string;
    data: number[];
    backgroundColor?: string;
    borderColor?: string;
  }>;
}

interface SubmissionRateData {
  total: number;
  successful: number;
  failed: number;
  pending: number;
  rate: number;
  trend: 'up' | 'down' | 'stable';
  change: number;
}

interface GeographicData {
  region: string;
  invoiceCount: number;
  revenue: number;
  successRate: number;
}

interface BusinessMetricsProps {
  timeRange?: '24h' | '7d' | '30d' | '90d' | '1y';
  organizationId?: string;
  refreshInterval?: number;
  className?: string;
}

// Mock data generators
const generateRevenueData = (timeRange: string): RevenueData => {
  const getLabels = () => {
    switch (timeRange) {
      case '24h':
        return Array.from({ length: 24 }, (_, i) => `${i}:00`);
      case '7d':
        return ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
      case '30d':
        return Array.from({ length: 30 }, (_, i) => `Day ${i + 1}`);
      case '90d':
        return Array.from({ length: 12 }, (_, i) => `Week ${i + 1}`);
      case '1y':
        return ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
      default:
        return ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'];
    }
  };

  const labels = getLabels();
  const baseRevenue = 50000;
  
  return {
    labels,
    datasets: [
      {
        label: 'Invoice Revenue',
        data: labels.map(() => baseRevenue + Math.random() * 30000),
        borderColor: 'rgb(59, 130, 246)',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        borderWidth: 3,
        fill: true,
        tension: 0.4
      },
      {
        label: 'Processing Fees',
        data: labels.map(() => Math.random() * 5000 + 2000),
        borderColor: 'rgb(16, 185, 129)',
        backgroundColor: 'rgba(16, 185, 129, 0.1)',
        borderWidth: 2,
        fill: true,
        tension: 0.4
      }
    ]
  };
};

const generateInvoiceStatusData = (): InvoiceStatusData => {
  return {
    labels: ['Processed', 'Pending', 'Failed', 'Cancelled', 'Draft'],
    datasets: [
      {
        label: 'Invoice Status',
        data: [1847, 234, 89, 23, 156],
        backgroundColor: [
          'rgba(16, 185, 129, 0.8)',  // Success - Green
          'rgba(59, 130, 246, 0.8)',  // Pending - Blue
          'rgba(239, 68, 68, 0.8)',   // Failed - Red
          'rgba(156, 163, 175, 0.8)', // Cancelled - Gray
          'rgba(245, 158, 11, 0.8)'   // Draft - Amber
        ],
        borderColor: [
          'rgb(16, 185, 129)',
          'rgb(59, 130, 246)',
          'rgb(239, 68, 68)',
          'rgb(156, 163, 175)',
          'rgb(245, 158, 11)'
        ],
        borderWidth: 2
      }
    ]
  };
};

const generateIntegrationPerformanceData = (): IntegrationPerformanceData => {
  return {
    labels: ['Odoo ERP', 'SAP', 'QuickBooks', 'Xero', 'FIRS API', 'Custom API'],
    datasets: [
      {
        label: 'Success Rate (%)',
        data: [98.5, 96.2, 94.8, 97.1, 99.2, 92.3],
        backgroundColor: [
          'rgba(139, 92, 246, 0.8)',
          'rgba(59, 130, 246, 0.8)',
          'rgba(16, 185, 129, 0.8)',
          'rgba(245, 158, 11, 0.8)',
          'rgba(239, 68, 68, 0.8)',
          'rgba(156, 163, 175, 0.8)'
        ],
        borderColor: 'rgba(255, 255, 255, 0.8)'
      }
    ]
  };
};

const generateSubmissionRateData = (): SubmissionRateData => {
  const total = 2349;
  const successful = 2298;
  const failed = 28;
  const pending = 23;
  
  return {
    total,
    successful,
    failed,
    pending,
    rate: (successful / total) * 100,
    trend: 'up',
    change: 2.3
  };
};

const generateGeographicData = (): GeographicData[] => {
  return [
    { region: 'Lagos', invoiceCount: 1247, revenue: 3250000, successRate: 98.2 },
    { region: 'Abuja', invoiceCount: 892, revenue: 2180000, successRate: 97.8 },
    { region: 'Kano', invoiceCount: 456, revenue: 1120000, successRate: 96.5 },
    { region: 'Port Harcourt', invoiceCount: 334, revenue: 890000, successRate: 97.1 },
    { region: 'Ibadan', invoiceCount: 298, revenue: 780000, successRate: 95.9 },
    { region: 'Others', invoiceCount: 567, revenue: 1480000, successRate: 96.8 }
  ];
};

// Progress indicator component
const ProgressIndicator: React.FC<{
  value: number;
  max: number;
  label: string;
  color?: 'primary' | 'success' | 'warning' | 'error';
  showPercentage?: boolean;
}> = ({ value, max, label, color = 'primary', showPercentage = true }) => {
  const percentage = (value / max) * 100;
  
  const colorClasses = {
    primary: 'bg-blue-500',
    success: 'bg-green-500',
    warning: 'bg-amber-500',
    error: 'bg-red-500'
  };

  return (
    <div className="space-y-2">
      <div className="flex justify-between items-center">
        <span className="text-sm font-medium text-gray-700">{label}</span>
        {showPercentage && (
          <span className="text-sm text-gray-500">{percentage.toFixed(1)}%</span>
        )}
      </div>
      <div className="w-full bg-gray-200 rounded-full h-3">
        <div 
          className={`h-3 rounded-full transition-all duration-300 ${colorClasses[color]}`}
          style={{ width: `${percentage}%` }}
        />
      </div>
      <div className="flex justify-between items-center text-xs text-gray-500">
        <span>{value.toLocaleString()}</span>
        <span>{max.toLocaleString()}</span>
      </div>
    </div>
  );
};

// Metric card component
const MetricCard: React.FC<{
  title: string;
  value: string | number;
  change?: number;
  trend?: 'up' | 'down' | 'stable';
  icon: React.ReactNode;
  color?: 'primary' | 'success' | 'warning' | 'error';
}> = ({ title, value, change, trend, icon, color = 'primary' }) => {
  const colorClasses = {
    primary: 'text-blue-600 bg-blue-50',
    success: 'text-green-600 bg-green-50',
    warning: 'text-amber-600 bg-amber-50',
    error: 'text-red-600 bg-red-50'
  };

  return (
    <Card>
      <CardContent className="p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-gray-600 mb-1">{title}</p>
            <p className="text-2xl font-bold text-gray-900">{value}</p>
            {change !== undefined && (
              <div className="flex items-center mt-2">
                {trend === 'up' ? (
                  <TrendingUp className="w-4 h-4 text-green-500 mr-1" />
                ) : trend === 'down' ? (
                  <TrendingDown className="w-4 h-4 text-red-500 mr-1" />
                ) : null}
                <span className={`text-sm font-medium ${
                  trend === 'up' ? 'text-green-600' : 
                  trend === 'down' ? 'text-red-600' : 
                  'text-gray-600'
                }`}>
                  {change > 0 ? '+' : ''}{change}%
                </span>
                <span className="text-sm text-gray-500 ml-1">vs last period</span>
              </div>
            )}
          </div>
          <div className={`p-3 rounded-lg ${colorClasses[color]}`}>
            {icon}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export const BusinessMetricsVisualization: React.FC<BusinessMetricsProps> = ({
  timeRange = '30d',
  organizationId,
  refreshInterval = 300000, // 5 minutes
  className = ''
}) => {
  const [selectedTimeRange, setSelectedTimeRange] = useState(timeRange);
  const [lastUpdated, setLastUpdated] = useState(new Date());
  const [isLoading, setIsLoading] = useState(false);

  // Generate data based on time range
  const revenueData = useMemo(() => generateRevenueData(selectedTimeRange), [selectedTimeRange]);
  const invoiceStatusData = useMemo(() => generateInvoiceStatusData(), []);
  const integrationPerformanceData = useMemo(() => generateIntegrationPerformanceData(), []);
  const submissionRateData = useMemo(() => generateSubmissionRateData(), []);
  const geographicData = useMemo(() => generateGeographicData(), []);

  // Calculate key metrics
  const totalRevenue = revenueData.datasets[0].data.reduce((sum, value) => sum + value, 0);
  const totalInvoices = invoiceStatusData.datasets[0].data.reduce((sum, value) => sum + value, 0);
  const averageInvoiceValue = totalRevenue / totalInvoices;

  // Refresh data
  const handleRefresh = () => {
    setIsLoading(true);
    setTimeout(() => {
      setLastUpdated(new Date());
      setIsLoading(false);
    }, 1000);
  };

  // Auto refresh
  useEffect(() => {
    if (refreshInterval > 0) {
      const interval = setInterval(() => {
        setLastUpdated(new Date());
      }, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [refreshInterval]);

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Business Metrics Dashboard</h1>
          <p className="text-gray-600 mt-1">
            Comprehensive view of revenue, invoices, and integration performance
          </p>
        </div>
        <div className="flex items-center gap-3 mt-4 sm:mt-0">
          <select
            value={selectedTimeRange}
            onChange={(e) => setSelectedTimeRange(e.target.value as any)}
            className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="24h">Last 24 Hours</option>
            <option value="7d">Last 7 Days</option>
            <option value="30d">Last 30 Days</option>
            <option value="90d">Last 90 Days</option>
            <option value="1y">Last Year</option>
          </select>
          <Button variant="outline" size="sm" onClick={handleRefresh} disabled={isLoading}>
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
          </Button>
          <Button variant="outline" size="sm">
            <Download className="w-4 h-4" />
          </Button>
        </div>
      </div>

      {/* Key Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          title="Total Revenue"
          value={`₦${(totalRevenue / 1000000).toFixed(1)}M`}
          change={8.2}
          trend="up"
          icon={<DollarSign className="w-6 h-6" />}
          color="success"
        />
        <MetricCard
          title="Total Invoices"
          value={totalInvoices.toLocaleString()}
          change={12.5}
          trend="up"
          icon={<FileText className="w-6 h-6" />}
          color="primary"
        />
        <MetricCard
          title="Success Rate"
          value={`${submissionRateData.rate.toFixed(1)}%`}
          change={submissionRateData.change}
          trend={submissionRateData.trend}
          icon={<CheckCircle2 className="w-6 h-6" />}
          color="success"
        />
        <MetricCard
          title="Avg Invoice Value"
          value={`₦${averageInvoiceValue.toLocaleString()}`}
          change={-2.1}
          trend="down"
          icon={<Activity className="w-6 h-6" />}
          color="warning"
        />
      </div>

      {/* Main Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Revenue Trends */}
        <ResponsiveChartContainer
          title="Revenue Trends"
          subtitle={`Revenue performance over ${selectedTimeRange}`}
          height={400}
          actions={
            <Badge variant="success">
              <TrendingUp className="w-4 h-4 mr-1" />
              +8.2%
            </Badge>
          }
        >
          <AreaChart
            data={revenueData.datasets[0].data.map((value, index) => ({
              name: revenueData.labels[index],
              value: value,
              fees: revenueData.datasets[1].data[index]
            }))}
            dataKey="value"
            gradientType="success"
            animate={true}
            height={350}
          />
        </ResponsiveChartContainer>

        {/* Invoice Status Distribution */}
        <ResponsiveChartContainer
          title="Invoice Status Distribution"
          subtitle="Current status breakdown of all invoices"
          height={400}
          actions={
            <Badge variant="secondary">
              {totalInvoices} Total
            </Badge>
          }
        >
          <DoughnutChart
            data={invoiceStatusData}
            gradientType="primary"
            height={350}
          />
        </ResponsiveChartContainer>
      </div>

      {/* Integration Performance and FIRS Submission */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Integration Performance */}
        <div className="lg:col-span-2">
          <ResponsiveChartContainer
            title="Integration Performance"
            subtitle="Success rates across all connected systems"
            height={400}
            actions={
              <Badge variant="success">All Systems Operational</Badge>
            }
          >
            <BarChart
              data={integrationPerformanceData}
              gradientType="purple"
              animate={true}
              height={350}
            />
          </ResponsiveChartContainer>
        </div>

        {/* FIRS Submission Rates */}
        <Card>
          <CardHeader>
            <CardTitle>FIRS Submission Rates</CardTitle>
            <CardDescription>Real-time submission status and success rates</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="text-center">
              <div className="text-3xl font-bold text-green-600">
                {submissionRateData.rate.toFixed(1)}%
              </div>
              <div className="text-sm text-gray-500">Overall Success Rate</div>
              <Badge variant="success" className="mt-2">
                <TrendingUp className="w-3 h-3 mr-1" />
                +{submissionRateData.change}%
              </Badge>
            </div>

            <div className="space-y-4">
              <ProgressIndicator
                value={submissionRateData.successful}
                max={submissionRateData.total}
                label="Successful Submissions"
                color="success"
              />
              <ProgressIndicator
                value={submissionRateData.pending}
                max={submissionRateData.total}
                label="Pending Submissions"
                color="warning"
              />
              <ProgressIndicator
                value={submissionRateData.failed}
                max={submissionRateData.total}
                label="Failed Submissions"
                color="error"
              />
            </div>

            <div className="grid grid-cols-2 gap-4 pt-4 border-t">
              <div className="text-center">
                <div className="text-lg font-semibold">{submissionRateData.total}</div>
                <div className="text-xs text-gray-500">Total</div>
              </div>
              <div className="text-center">
                <div className="text-lg font-semibold text-green-600">
                  {submissionRateData.successful}
                </div>
                <div className="text-xs text-gray-500">Success</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Geographic Distribution */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <MapPin className="w-5 h-5" />
            Geographic Distribution
          </CardTitle>
          <CardDescription>Invoice processing distribution across regions</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {geographicData.map((region, index) => (
              <div key={index} className="bg-gray-50 rounded-lg p-4">
                <div className="flex items-center justify-between mb-3">
                  <h4 className="font-semibold text-gray-900">{region.region}</h4>
                  <Badge variant="outline">
                    {region.successRate.toFixed(1)}%
                  </Badge>
                </div>
                
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Invoices:</span>
                    <span className="font-medium">{region.invoiceCount.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Revenue:</span>
                    <span className="font-medium">₦{(region.revenue / 1000000).toFixed(1)}M</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2 mt-3">
                    <div 
                      className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${region.successRate}%` }}
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Last Updated */}
      <div className="text-center text-sm text-gray-500">
        Last updated: {lastUpdated.toLocaleString()}
      </div>
    </div>
  );
};

export default BusinessMetricsVisualization;