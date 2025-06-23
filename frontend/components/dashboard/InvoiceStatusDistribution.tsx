/**
 * Invoice Status Distribution Component
 * Specialized pie/donut charts for invoice status visualization
 */

import React, { useState, useMemo } from 'react';
import { Card, CardHeader, CardContent, CardTitle, CardDescription } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';
import { DoughnutChart } from '../ui/Charts';
import { 
  PieChart, 
  FileText, 
  CheckCircle2, 
  Clock, 
  XCircle, 
  FileX, 
  Edit3,
  Download,
  RefreshCw
} from 'lucide-react';

interface InvoiceStatus {
  status: string;
  count: number;
  percentage: number;
  color: string;
  icon: React.ReactNode;
  description: string;
}

interface InvoiceStatusDistributionProps {
  timeRange?: '24h' | '7d' | '30d' | '90d' | '1y';
  className?: string;
  showDetails?: boolean;
  chartType?: 'pie' | 'doughnut';
}

const generateInvoiceStatusData = (timeRange: string): InvoiceStatus[] => {
  // Base counts that vary by time range
  const multiplier = timeRange === '24h' ? 0.1 : timeRange === '7d' ? 1 : timeRange === '30d' ? 4 : timeRange === '90d' ? 12 : 50;
  
  const baseCounts = {
    processed: Math.round(1847 * multiplier),
    pending: Math.round(234 * multiplier),
    failed: Math.round(89 * multiplier),
    cancelled: Math.round(23 * multiplier),
    draft: Math.round(156 * multiplier),
    reviewed: Math.round(78 * multiplier)
  };

  const total = Object.values(baseCounts).reduce((sum, count) => sum + count, 0);

  return [
    {
      status: 'Processed',
      count: baseCounts.processed,
      percentage: (baseCounts.processed / total) * 100,
      color: 'rgba(16, 185, 129, 0.8)',
      icon: <CheckCircle2 className="w-4 h-4" />,
      description: 'Successfully processed and submitted to FIRS'
    },
    {
      status: 'Pending',
      count: baseCounts.pending,
      percentage: (baseCounts.pending / total) * 100,
      color: 'rgba(59, 130, 246, 0.8)',
      icon: <Clock className="w-4 h-4" />,
      description: 'Awaiting processing or FIRS response'
    },
    {
      status: 'Draft',
      count: baseCounts.draft,
      percentage: (baseCounts.draft / total) * 100,
      color: 'rgba(245, 158, 11, 0.8)',
      icon: <Edit3 className="w-4 h-4" />,
      description: 'Created but not yet submitted'
    },
    {
      status: 'Failed',
      count: baseCounts.failed,
      percentage: (baseCounts.failed / total) * 100,
      color: 'rgba(239, 68, 68, 0.8)',
      icon: <XCircle className="w-4 h-4" />,
      description: 'Failed processing due to errors'
    },
    {
      status: 'Under Review',
      count: baseCounts.reviewed,
      percentage: (baseCounts.reviewed / total) * 100,
      color: 'rgba(139, 92, 246, 0.8)',
      icon: <FileText className="w-4 h-4" />,
      description: 'Under manual review or validation'
    },
    {
      status: 'Cancelled',
      count: baseCounts.cancelled,
      percentage: (baseCounts.cancelled / total) * 100,
      color: 'rgba(156, 163, 175, 0.8)',
      icon: <FileX className="w-4 h-4" />,
      description: 'Cancelled by user or system'
    }
  ];
};

export const InvoiceStatusDistribution: React.FC<InvoiceStatusDistributionProps> = ({
  timeRange = '30d',
  className = '',
  showDetails = true,
  chartType = 'doughnut'
}) => {
  const [isLoading, setIsLoading] = useState(false);
  
  const statusData = useMemo(() => generateInvoiceStatusData(timeRange), [timeRange]);
  
  const totalInvoices = statusData.reduce((sum, status) => sum + status.count, 0);
  const successfulInvoices = statusData.find(s => s.status === 'Processed')?.count || 0;
  const successRate = totalInvoices > 0 ? (successfulInvoices / totalInvoices) * 100 : 0;

  // Prepare chart data
  const chartData = {
    labels: statusData.map(status => status.status),
    datasets: [
      {
        label: 'Invoice Status',
        data: statusData.map(status => status.count),
        backgroundColor: statusData.map(status => status.color),
        borderColor: statusData.map(status => status.color.replace('0.8', '1')),
        borderWidth: 2,
        hoverOffset: 4
      }
    ]
  };

  const handleRefresh = () => {
    setIsLoading(true);
    setTimeout(() => setIsLoading(false), 1000);
  };

  const getStatusBadgeVariant = (status: string) => {
    switch (status) {
      case 'Processed':
        return 'success';
      case 'Failed':
        return 'destructive';
      case 'Pending':
      case 'Under Review':
        return 'secondary';
      case 'Cancelled':
        return 'outline';
      default:
        return 'secondary';
    }
  };

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <PieChart className="w-5 h-5 text-blue-600" />
              Invoice Status Distribution
            </CardTitle>
            <CardDescription>
              Current breakdown of invoice statuses across all processing stages
            </CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="outline">
              {totalInvoices.toLocaleString()} Total
            </Badge>
            <Badge variant="success">
              {successRate.toFixed(1)}% Success
            </Badge>
            <Button variant="outline" size="sm" onClick={handleRefresh} disabled={isLoading}>
              <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
            </Button>
            <Button variant="outline" size="sm">
              <Download className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Chart */}
          <div className="flex flex-col items-center">
            <div className="h-80 w-full max-w-sm">
              <DoughnutChart
                data={chartData}
                gradientType="primary"
                height={300}
                options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  plugins: {
                    legend: {
                      display: false // We'll create a custom legend
                    },
                    tooltip: {
                      callbacks: {
                        label: function(context: any) {
                          const status = statusData[context.dataIndex];
                          return `${status.status}: ${status.count.toLocaleString()} (${status.percentage.toFixed(1)}%)`;
                        }
                      }
                    }
                  },
                  cutout: chartType === 'doughnut' ? '60%' : '0%'
                }}
              />
            </div>
            
            {/* Center statistics for doughnut chart */}
            {chartType === 'doughnut' && (
              <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
                <div className="text-2xl font-bold text-gray-900">
                  {totalInvoices.toLocaleString()}
                </div>
                <div className="text-sm text-gray-500">Total Invoices</div>
              </div>
            )}
          </div>

          {/* Status Details */}
          <div className="space-y-4">
            <h4 className="font-semibold text-gray-900">Status Breakdown</h4>
            
            <div className="space-y-3">
              {statusData.map((status, index) => (
                <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center gap-3">
                    <div 
                      className="w-4 h-4 rounded-full" 
                      style={{ backgroundColor: status.color }}
                    />
                    <div className="flex items-center gap-2">
                      {status.icon}
                      <span className="font-medium text-gray-900">{status.status}</span>
                    </div>
                  </div>
                  
                  <div className="text-right">
                    <div className="font-semibold text-gray-900">
                      {status.count.toLocaleString()}
                    </div>
                    <div className="text-sm text-gray-500">
                      {status.percentage.toFixed(1)}%
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {showDetails && (
              <div className="mt-6 pt-4 border-t">
                <h5 className="font-medium text-gray-900 mb-3">Key Metrics</h5>
                <div className="grid grid-cols-2 gap-4">
                  <div className="text-center p-3 bg-green-50 rounded-lg">
                    <div className="text-lg font-bold text-green-600">
                      {successRate.toFixed(1)}%
                    </div>
                    <div className="text-sm text-gray-600">Success Rate</div>
                  </div>
                  <div className="text-center p-3 bg-blue-50 rounded-lg">
                    <div className="text-lg font-bold text-blue-600">
                      {(statusData.find(s => s.status === 'Pending')?.percentage || 0).toFixed(1)}%
                    </div>
                    <div className="text-sm text-gray-600">Pending</div>
                  </div>
                  <div className="text-center p-3 bg-red-50 rounded-lg">
                    <div className="text-lg font-bold text-red-600">
                      {(statusData.find(s => s.status === 'Failed')?.percentage || 0).toFixed(1)}%
                    </div>
                    <div className="text-sm text-gray-600">Failure Rate</div>
                  </div>
                  <div className="text-center p-3 bg-amber-50 rounded-lg">
                    <div className="text-lg font-bold text-amber-600">
                      {(statusData.find(s => s.status === 'Draft')?.percentage || 0).toFixed(1)}%
                    </div>
                    <div className="text-sm text-gray-600">Drafts</div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Status descriptions */}
        {showDetails && (
          <div className="mt-6 pt-4 border-t">
            <h5 className="font-medium text-gray-900 mb-3">Status Descriptions</h5>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {statusData.map((status, index) => (
                <div key={index} className="flex items-start gap-3 p-3 border rounded-lg">
                  <div 
                    className="w-3 h-3 rounded-full mt-1.5 flex-shrink-0" 
                    style={{ backgroundColor: status.color }}
                  />
                  <div>
                    <div className="font-medium text-gray-900">{status.status}</div>
                    <div className="text-sm text-gray-600">{status.description}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default InvoiceStatusDistribution;