import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/Tabs';
import { BarChart, BarChart3, FileBarChart, PieChart, LineChart, Timer } from 'lucide-react';
import { 
  SubmissionMetrics, 
  StatusBreakdownModel, 
  HourlySubmissionModel,
  DailySubmissionModel
} from '../../services/submissionDashboardService';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { Line, Bar, Pie } from 'react-chartjs-2';

// Inline formatters until the utils/formatters module is recognized
const formatNumber = (value: number, decimals: number = 0): string => {
  if (isNaN(value)) return '0';
  
  return new Intl.NumberFormat('en-NG', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value);
};

const formatDuration = (ms: number): string => {
  if (ms < 1000) {
    return `${ms}ms`;
  }
  
  if (ms < 60000) {
    return `${(ms / 1000).toFixed(1)}s`;
  }
  
  const minutes = Math.floor(ms / 60000);
  const seconds = Math.floor((ms % 60000) / 1000);
  
  return `${minutes}m ${seconds}s`;
};

// Register ChartJS components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend
);

interface SubmissionMetricsCardProps {
  metrics: SubmissionMetrics;
  isLoading?: boolean;
  title?: string;
  description?: string;
}

const SubmissionMetricsCard: React.FC<SubmissionMetricsCardProps> = ({
  metrics,
  isLoading = false,
  title = 'Invoice Submission Metrics',
  description = 'Processing metrics and status visualizations for invoice submissions'
}) => {
  const [activeTab, setActiveTab] = useState('overview');

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>{title}</CardTitle>
          <CardDescription>{description}</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-64 flex items-center justify-center">
            <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-500"></div>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Prepare data for status breakdown pie chart
  const statusLabels = metrics.status_breakdown.map(item => item.status);
  const statusData = metrics.status_breakdown.map(item => item.count);
  const statusColors = metrics.status_breakdown.map(item => {
    switch (item.status) {
      case 'accepted':
      case 'signed':
        return 'rgba(34, 197, 94, 0.7)'; // green
      case 'rejected':
      case 'failed':
      case 'error':
      case 'cancelled':
        return 'rgba(239, 68, 68, 0.7)'; // red
      case 'pending':
      case 'processing':
      case 'validated':
        return 'rgba(59, 130, 246, 0.7)'; // blue
      default:
        return 'rgba(156, 163, 175, 0.7)'; // gray
    }
  });

  const statusChartData = {
    labels: statusLabels,
    datasets: [
      {
        label: 'Submissions',
        data: statusData,
        backgroundColor: statusColors,
        borderColor: statusColors.map(color => color.replace('0.7', '1')),
        borderWidth: 1,
      },
    ],
  };

  // Prepare data for hourly line chart
  const hourlyLabels = metrics.hourly_submissions.map(item => `${new Date(item.timestamp).getHours()}:00`).reverse();
  const hourlyData = {
    labels: hourlyLabels,
    datasets: [
      {
        label: 'Total',
        data: metrics.hourly_submissions.map(item => item.total).reverse(),
        borderColor: 'rgba(99, 102, 241, 1)',
        backgroundColor: 'rgba(99, 102, 241, 0.1)',
        tension: 0.3,
        fill: true,
      },
      {
        label: 'Success',
        data: metrics.hourly_submissions.map(item => item.success).reverse(),
        borderColor: 'rgba(34, 197, 94, 1)',
        backgroundColor: 'rgba(34, 197, 94, 0.1)',
        tension: 0.3,
        fill: true,
      },
      {
        label: 'Failed',
        data: metrics.hourly_submissions.map(item => item.failed).reverse(),
        borderColor: 'rgba(239, 68, 68, 1)',
        backgroundColor: 'rgba(239, 68, 68, 0.1)',
        tension: 0.3,
        fill: true,
      }
    ],
  };

  // Prepare data for daily bar chart
  const dailyLabels = metrics.daily_submissions.map(item => item.date).reverse();
  const dailyData = {
    labels: dailyLabels,
    datasets: [
      {
        label: 'Success',
        data: metrics.daily_submissions.map(item => item.success).reverse(),
        backgroundColor: 'rgba(34, 197, 94, 0.7)',
      },
      {
        label: 'Failed',
        data: metrics.daily_submissions.map(item => item.failed).reverse(),
        backgroundColor: 'rgba(239, 68, 68, 0.7)',
      },
      {
        label: 'Pending',
        data: metrics.daily_submissions.map(item => item.pending).reverse(),
        backgroundColor: 'rgba(59, 130, 246, 0.7)',
      }
    ],
  };

  // Calculate success rate color based on the value
  const getSuccessRateColor = (rate: number) => {
    if (rate >= 90) return 'text-green-500';
    if (rate >= 75) return 'text-yellow-500';
    return 'text-red-500';
  };

  return (
    <Card className="shadow-md">
      <CardHeader>
        <div className="flex justify-between items-center">
          <div>
            <CardTitle>{title}</CardTitle>
            <CardDescription>{description}</CardDescription>
          </div>
          <Badge variant="outline" className="ml-2">
            {metrics.time_range === '24h' ? 'Last 24 Hours' : 
             metrics.time_range === '7d' ? 'Last 7 Days' :
             metrics.time_range === '30d' ? 'Last 30 Days' : 'All Time'}
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <Tabs defaultValue="overview" value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid grid-cols-4 mb-6">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="status">Status</TabsTrigger>
            <TabsTrigger value="trends">Trends</TabsTrigger>
            <TabsTrigger value="errors">Errors</TabsTrigger>
          </TabsList>
          
          <TabsContent value="overview" className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
              <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow">
                <div className="flex justify-between items-start">
                  <div>
                    <p className="text-gray-500 dark:text-gray-400 text-sm">Total Submissions</p>
                    <h4 className="text-2xl font-bold">{formatNumber(metrics.summary.total_submissions)}</h4>
                  </div>
                  <FileBarChart className="text-blue-500" />
                </div>
              </div>
              
              <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow">
                <div className="flex justify-between items-start">
                  <div>
                    <p className="text-gray-500 dark:text-gray-400 text-sm">Success Rate</p>
                    <h4 className={`text-2xl font-bold ${getSuccessRateColor(metrics.summary.success_rate)}`}>
                      {metrics.summary.success_rate.toFixed(1)}%
                    </h4>
                  </div>
                  <BarChart3 className="text-green-500" />
                </div>
              </div>
              
              <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow">
                <div className="flex justify-between items-start">
                  <div>
                    <p className="text-gray-500 dark:text-gray-400 text-sm">Avg Processing Time</p>
                    <h4 className="text-2xl font-bold">{formatDuration(metrics.summary.avg_processing_time)}</h4>
                  </div>
                  <Timer className="text-purple-500" />
                </div>
              </div>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h4 className="font-medium mb-2">Status Distribution</h4>
                <div className="h-64">
                  <Pie data={statusChartData} options={{ 
                    maintainAspectRatio: false,
                    plugins: {
                      legend: {
                        position: 'right',
                      },
                      tooltip: {
                        callbacks: {
                          label: function(context) {
                            const label = context.label || '';
                            const value = context.raw as number;
                            const percentage = metrics.status_breakdown.find(item => item.status === label)?.percentage || 0;
                            return `${label}: ${value} (${percentage.toFixed(1)}%)`;
                          }
                        }
                      }
                    }
                  }} />
                </div>
              </div>
              
              <div>
                <h4 className="font-medium mb-2">Submission Trends (Last 24 Hours)</h4>
                <div className="h-64">
                  <Line data={hourlyData} options={{ 
                    maintainAspectRatio: false,
                    scales: {
                      y: {
                        beginAtZero: true,
                      }
                    }
                  }} />
                </div>
              </div>
            </div>
          </TabsContent>
          
          <TabsContent value="status">
            <div className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow">
                  <p className="text-gray-500 dark:text-gray-400 text-sm">Success</p>
                  <h4 className="text-2xl font-bold text-green-500">{formatNumber(metrics.summary.success_count)}</h4>
                  <p className="text-sm text-gray-500 mt-1">
                    {(metrics.summary.success_count / metrics.summary.total_submissions * 100).toFixed(1)}% of total
                  </p>
                </div>
                
                <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow">
                  <p className="text-gray-500 dark:text-gray-400 text-sm">Failed</p>
                  <h4 className="text-2xl font-bold text-red-500">{formatNumber(metrics.summary.failed_count)}</h4>
                  <p className="text-sm text-gray-500 mt-1">
                    {(metrics.summary.failed_count / metrics.summary.total_submissions * 100).toFixed(1)}% of total
                  </p>
                </div>
                
                <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow">
                  <p className="text-gray-500 dark:text-gray-400 text-sm">Pending</p>
                  <h4 className="text-2xl font-bold text-blue-500">{formatNumber(metrics.summary.pending_count)}</h4>
                  <p className="text-sm text-gray-500 mt-1">
                    {(metrics.summary.pending_count / metrics.summary.total_submissions * 100).toFixed(1)}% of total
                  </p>
                </div>
              </div>
              
              <div>
                <h4 className="font-medium mb-4">Status Breakdown</h4>
                <div className="h-80">
                  <Pie data={statusChartData} options={{ 
                    maintainAspectRatio: false,
                    plugins: {
                      legend: {
                        position: 'right',
                      }
                    }
                  }} />
                </div>
              </div>
              
              {metrics.odoo_metrics && (
                <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow mt-4">
                  <h4 className="font-medium mb-2">Odoo Integration Metrics</h4>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-gray-500 dark:text-gray-400 text-sm">Total Odoo Submissions</p>
                      <h4 className="text-xl font-bold">{formatNumber(metrics.odoo_metrics.total_odoo_submissions)}</h4>
                    </div>
                    <div>
                      <p className="text-gray-500 dark:text-gray-400 text-sm">% of All Submissions</p>
                      <h4 className="text-xl font-bold">{metrics.odoo_metrics.percentage_of_all_submissions.toFixed(1)}%</h4>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </TabsContent>
          
          <TabsContent value="trends">
            <div className="space-y-6">
              <div>
                <h4 className="font-medium mb-2">Hourly Submission Activity</h4>
                <div className="h-80">
                  <Line data={hourlyData} options={{ 
                    maintainAspectRatio: false,
                    scales: {
                      y: {
                        beginAtZero: true,
                      }
                    }
                  }} />
                </div>
              </div>
              
              <div>
                <h4 className="font-medium mb-2">Daily Submission Volume</h4>
                <div className="h-80">
                  <Bar data={dailyData} options={{ 
                    maintainAspectRatio: false,
                    scales: {
                      x: {
                        stacked: true,
                      },
                      y: {
                        stacked: true,
                        beginAtZero: true,
                      }
                    }
                  }} />
                </div>
              </div>
            </div>
          </TabsContent>
          
          <TabsContent value="errors">
            <div className="space-y-4">
              <h4 className="font-medium">Common Errors</h4>
              {metrics.common_errors.length > 0 ? (
                <div className="overflow-x-auto">
                  <table className="min-w-full bg-white dark:bg-gray-800 shadow rounded-lg">
                    <thead>
                      <tr className="border-b dark:border-gray-700">
                        <th className="py-3 px-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Error Type</th>
                        <th className="py-3 px-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Count</th>
                        <th className="py-3 px-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Percentage</th>
                        <th className="py-3 px-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Severity</th>
                      </tr>
                    </thead>
                    <tbody>
                      {metrics.common_errors.map((error, index) => (
                        <tr key={index} className="border-b dark:border-gray-700">
                          <td className="py-3 px-4">{error.error_type}</td>
                          <td className="py-3 px-4">{error.count}</td>
                          <td className="py-3 px-4">{error.percentage.toFixed(1)}%</td>
                          <td className="py-3 px-4">
                            <Badge variant={
                              error.severity === 'critical' ? 'destructive' :
                              error.severity === 'high' ? 'destructive' :
                              error.severity === 'medium' ? 'warning' :
                              'secondary'
                            }>
                              {error.severity}
                            </Badge>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow text-center">
                  <p className="text-gray-500">No errors recorded in this time period.</p>
                </div>
              )}
            </div>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
};

export default SubmissionMetricsCard;
