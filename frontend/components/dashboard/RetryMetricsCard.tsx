import React from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/Tabs';
import { RefreshCw, CheckCircle, XCircle, AlarmClock, AlertTriangle } from 'lucide-react';
import { RetryMetrics, StatusBreakdownModel } from '../../services/submissionDashboardService';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { Bar, Pie, Doughnut } from 'react-chartjs-2';

// Inline formatter until the utils/formatters module is recognized
const formatNumber = (value: number, decimals: number = 0): string => {
  if (isNaN(value)) return '0';
  
  return new Intl.NumberFormat('en-NG', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value);
};

// Register ChartJS components
ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend
);

interface RetryMetricsCardProps {
  metrics: RetryMetrics;
  isLoading?: boolean;
  title?: string;
  description?: string;
}

const RetryMetricsCard: React.FC<RetryMetricsCardProps> = ({
  metrics,
  isLoading = false,
  title = 'Retry Metrics',
  description = 'Analytics for submission retry attempts and error recovery'
}) => {
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
  const statusLabels = metrics.retry_breakdown_by_status.map(item => item.status);
  const statusData = metrics.retry_breakdown_by_status.map(item => item.count);
  const statusColors = metrics.retry_breakdown_by_status.map(item => {
    switch (item.status) {
      case 'success':
        return 'rgba(34, 197, 94, 0.7)'; // green
      case 'failed':
        return 'rgba(239, 68, 68, 0.7)'; // red
      case 'pending':
        return 'rgba(59, 130, 246, 0.7)'; // blue
      case 'max_attempts_reached':
        return 'rgba(245, 158, 11, 0.7)'; // amber
      default:
        return 'rgba(156, 163, 175, 0.7)'; // gray
    }
  });

  const statusChartData = {
    labels: statusLabels,
    datasets: [
      {
        label: 'Retries',
        data: statusData,
        backgroundColor: statusColors,
        borderColor: statusColors.map(color => color.replace('0.7', '1')),
        borderWidth: 1,
      },
    ],
  };

  // Prepare data for severity breakdown chart
  const severityLabels = metrics.retry_breakdown_by_severity.map(item => item.status);
  const severityData = metrics.retry_breakdown_by_severity.map(item => item.count);
  const severityColors = metrics.retry_breakdown_by_severity.map(item => {
    switch (item.status) {
      case 'critical':
        return 'rgba(220, 38, 38, 0.7)'; // deep red
      case 'high':
        return 'rgba(239, 68, 68, 0.7)'; // red
      case 'medium':
        return 'rgba(245, 158, 11, 0.7)'; // amber
      case 'low':
        return 'rgba(59, 130, 246, 0.7)'; // blue
      default:
        return 'rgba(156, 163, 175, 0.7)'; // gray
    }
  });

  const severityChartData = {
    labels: severityLabels,
    datasets: [
      {
        label: 'Severity',
        data: severityData,
        backgroundColor: severityColors,
        borderColor: severityColors.map(color => color.replace('0.7', '1')),
        borderWidth: 1,
      },
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
        <Tabs defaultValue="overview">
          <TabsList className="grid grid-cols-2 mb-6">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="breakdown">Breakdown</TabsTrigger>
          </TabsList>
          
          <TabsContent value="overview" className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
              <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow">
                <div className="flex justify-between items-start">
                  <div>
                    <p className="text-gray-500 dark:text-gray-400 text-sm">Total Retries</p>
                    <h4 className="text-2xl font-bold">{formatNumber(metrics.metrics.total_retries)}</h4>
                  </div>
                  <RefreshCw className="text-blue-500" />
                </div>
              </div>
              
              <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow">
                <div className="flex justify-between items-start">
                  <div>
                    <p className="text-gray-500 dark:text-gray-400 text-sm">Success Rate</p>
                    <h4 className={`text-2xl font-bold ${getSuccessRateColor(metrics.metrics.success_rate)}`}>
                      {metrics.metrics.success_rate.toFixed(1)}%
                    </h4>
                  </div>
                  <CheckCircle className="text-green-500" />
                </div>
              </div>
              
              <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow">
                <div className="flex justify-between items-start">
                  <div>
                    <p className="text-gray-500 dark:text-gray-400 text-sm">Avg Attempts</p>
                    <h4 className="text-2xl font-bold">{metrics.metrics.avg_attempts.toFixed(1)}</h4>
                  </div>
                  <AlarmClock className="text-purple-500" />
                </div>
              </div>
              
              <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow">
                <div className="flex justify-between items-start">
                  <div>
                    <p className="text-gray-500 dark:text-gray-400 text-sm">Max Attempts Reached</p>
                    <h4 className="text-2xl font-bold">{formatNumber(metrics.metrics.max_attempts_reached_count)}</h4>
                  </div>
                  <AlertTriangle className="text-amber-500" />
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
                            const percentage = metrics.retry_breakdown_by_status.find(item => item.status === label)?.percentage || 0;
                            return `${label}: ${value} (${percentage.toFixed(1)}%)`;
                          }
                        }
                      }
                    }
                  }} />
                </div>
              </div>
              
              <div>
                <h4 className="font-medium mb-2">Severity Distribution</h4>
                <div className="h-64">
                  <Doughnut data={severityChartData} options={{ 
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
                            const percentage = metrics.retry_breakdown_by_severity.find(item => item.status === label)?.percentage || 0;
                            return `${label}: ${value} (${percentage.toFixed(1)}%)`;
                          }
                        }
                      }
                    }
                  }} />
                </div>
              </div>
            </div>
          </TabsContent>
          
          <TabsContent value="breakdown">
            <div className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow">
                  <p className="text-gray-500 dark:text-gray-400 text-sm">Success</p>
                  <h4 className="text-2xl font-bold text-green-500">{formatNumber(metrics.metrics.success_count)}</h4>
                  <p className="text-sm text-gray-500 mt-1">
                    {(metrics.metrics.success_count / metrics.metrics.total_retries * 100).toFixed(1)}% of total
                  </p>
                </div>
                
                <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow">
                  <p className="text-gray-500 dark:text-gray-400 text-sm">Failed</p>
                  <h4 className="text-2xl font-bold text-red-500">{formatNumber(metrics.metrics.failed_count)}</h4>
                  <p className="text-sm text-gray-500 mt-1">
                    {(metrics.metrics.failed_count / metrics.metrics.total_retries * 100).toFixed(1)}% of total
                  </p>
                </div>
                
                <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow">
                  <p className="text-gray-500 dark:text-gray-400 text-sm">Pending</p>
                  <h4 className="text-2xl font-bold text-blue-500">{formatNumber(metrics.metrics.pending_count)}</h4>
                  <p className="text-sm text-gray-500 mt-1">
                    {(metrics.metrics.pending_count / metrics.metrics.total_retries * 100).toFixed(1)}% of total
                  </p>
                </div>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h4 className="font-medium mb-4">Status Breakdown</h4>
                  <div className="overflow-x-auto">
                    <table className="min-w-full bg-white dark:bg-gray-800 shadow rounded-lg">
                      <thead>
                        <tr className="border-b dark:border-gray-700">
                          <th className="py-3 px-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                          <th className="py-3 px-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Count</th>
                          <th className="py-3 px-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Percentage</th>
                        </tr>
                      </thead>
                      <tbody>
                        {metrics.retry_breakdown_by_status.map((status, index) => (
                          <tr key={index} className="border-b dark:border-gray-700">
                            <td className="py-3 px-4">
                              <span className={`inline-flex items-center ${
                                status.status === 'success' ? 'text-green-500' :
                                status.status === 'failed' ? 'text-red-500' :
                                status.status === 'pending' ? 'text-blue-500' :
                                status.status === 'max_attempts_reached' ? 'text-amber-500' :
                                'text-gray-500'
                              }`}>
                                {status.status}
                              </span>
                            </td>
                            <td className="py-3 px-4">{status.count}</td>
                            <td className="py-3 px-4">{status.percentage.toFixed(1)}%</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
                
                <div>
                  <h4 className="font-medium mb-4">Severity Breakdown</h4>
                  <div className="overflow-x-auto">
                    <table className="min-w-full bg-white dark:bg-gray-800 shadow rounded-lg">
                      <thead>
                        <tr className="border-b dark:border-gray-700">
                          <th className="py-3 px-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Severity</th>
                          <th className="py-3 px-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Count</th>
                          <th className="py-3 px-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Percentage</th>
                        </tr>
                      </thead>
                      <tbody>
                        {metrics.retry_breakdown_by_severity.map((severity, index) => (
                          <tr key={index} className="border-b dark:border-gray-700">
                            <td className="py-3 px-4">
                              <Badge variant={
                                severity.status === 'critical' ? 'destructive' :
                                severity.status === 'high' ? 'destructive' :
                                severity.status === 'medium' ? 'warning' :
                                'secondary'
                              }>
                                {severity.status}
                              </Badge>
                            </td>
                            <td className="py-3 px-4">{severity.count}</td>
                            <td className="py-3 px-4">{severity.percentage.toFixed(1)}%</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            </div>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
};

export default RetryMetricsCard;
