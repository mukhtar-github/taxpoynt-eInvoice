/**
 * Revenue Trends Chart Component
 * Specialized chart for visualizing revenue trends over time with line charts
 */

import React, { useState, useMemo } from 'react';
import { Card, CardHeader, CardContent, CardTitle, CardDescription } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';
import { LineChart, AreaChart } from '../ui/Charts';
import { TrendingUp, TrendingDown, DollarSign, Download, Settings } from 'lucide-react';

interface RevenueDataPoint {
  date: string;
  totalRevenue: number;
  processingFees: number;
  subscriptionRevenue: number;
  otherRevenue: number;
}

interface RevenueTrendsProps {
  timeRange?: '24h' | '7d' | '30d' | '90d' | '1y';
  className?: string;
  showBreakdown?: boolean;
  chartType?: 'line' | 'area';
}

const generateRevenueData = (timeRange: string): RevenueDataPoint[] => {
  const getDateLabels = () => {
    const now = new Date();
    const points: string[] = [];
    
    switch (timeRange) {
      case '24h':
        for (let i = 23; i >= 0; i--) {
          const date = new Date(now.getTime() - i * 60 * 60 * 1000);
          points.push(`${date.getHours()}:00`);
        }
        break;
      case '7d':
        for (let i = 6; i >= 0; i--) {
          const date = new Date(now.getTime() - i * 24 * 60 * 60 * 1000);
          points.push(date.toLocaleDateString('en-US', { weekday: 'short' }));
        }
        break;
      case '30d':
        for (let i = 29; i >= 0; i--) {
          const date = new Date(now.getTime() - i * 24 * 60 * 60 * 1000);
          points.push(date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }));
        }
        break;
      case '90d':
        for (let i = 12; i >= 0; i--) {
          const date = new Date(now.getTime() - i * 7 * 24 * 60 * 60 * 1000);
          points.push(`Week ${13 - i}`);
        }
        break;
      case '1y':
        for (let i = 11; i >= 0; i--) {
          const date = new Date(now.getFullYear(), now.getMonth() - i, 1);
          points.push(date.toLocaleDateString('en-US', { month: 'short' }));
        }
        break;
      default:
        return [];
    }
    
    return points;
  };

  const labels = getDateLabels();
  const baseRevenue = timeRange === '24h' ? 5000 : timeRange === '7d' ? 50000 : 150000;
  
  return labels.map((date, index) => {
    const variation = 0.8 + Math.random() * 0.4; // 80% to 120% variation
    const trend = Math.sin((index / labels.length) * Math.PI * 2) * 0.2 + 1; // Sine wave trend
    
    const totalRevenue = Math.round(baseRevenue * variation * trend);
    const processingFees = Math.round(totalRevenue * 0.025); // 2.5% processing fees
    const subscriptionRevenue = Math.round(totalRevenue * 0.15); // 15% subscription
    const otherRevenue = Math.round(totalRevenue * 0.05); // 5% other
    
    return {
      date,
      totalRevenue,
      processingFees,
      subscriptionRevenue,
      otherRevenue
    };
  });
};

export const RevenueTrendsChart: React.FC<RevenueTrendsProps> = ({
  timeRange = '30d',
  className = '',
  showBreakdown = true,
  chartType = 'area'
}) => {
  const [selectedMetric, setSelectedMetric] = useState<'total' | 'breakdown'>('total');
  
  const revenueData = useMemo(() => generateRevenueData(timeRange), [timeRange]);
  
  // Calculate summary metrics
  const currentPeriodRevenue = revenueData.reduce((sum, point) => sum + point.totalRevenue, 0);
  const previousPeriodRevenue = currentPeriodRevenue * (0.92 + Math.random() * 0.16); // Mock previous period
  const revenueGrowth = ((currentPeriodRevenue - previousPeriodRevenue) / previousPeriodRevenue) * 100;
  
  const avgDailyRevenue = currentPeriodRevenue / revenueData.length;
  const highestDay = Math.max(...revenueData.map(d => d.totalRevenue));
  const lowestDay = Math.min(...revenueData.map(d => d.totalRevenue));

  // Prepare chart data
  const chartData = {
    labels: revenueData.map(d => d.date),
    datasets: selectedMetric === 'total' ? [
      {
        label: 'Total Revenue',
        data: revenueData.map(d => d.totalRevenue),
        borderColor: 'rgb(59, 130, 246)',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        borderWidth: 3,
        fill: true,
        tension: 0.4
      }
    ] : [
      {
        label: 'Invoice Revenue',
        data: revenueData.map(d => d.totalRevenue - d.processingFees - d.subscriptionRevenue - d.otherRevenue),
        borderColor: 'rgb(59, 130, 246)',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        borderWidth: 2,
        fill: true,
        tension: 0.4
      },
      {
        label: 'Processing Fees',
        data: revenueData.map(d => d.processingFees),
        borderColor: 'rgb(16, 185, 129)',
        backgroundColor: 'rgba(16, 185, 129, 0.1)',
        borderWidth: 2,
        fill: true,
        tension: 0.4
      },
      {
        label: 'Subscriptions',
        data: revenueData.map(d => d.subscriptionRevenue),
        borderColor: 'rgb(139, 92, 246)',
        backgroundColor: 'rgba(139, 92, 246, 0.1)',
        borderWidth: 2,
        fill: true,
        tension: 0.4
      },
      {
        label: 'Other Revenue',
        data: revenueData.map(d => d.otherRevenue),
        borderColor: 'rgb(245, 158, 11)',
        backgroundColor: 'rgba(245, 158, 11, 0.1)',
        borderWidth: 2,
        fill: true,
        tension: 0.4
      }
    ]
  };

  const formatCurrency = (amount: number) => {
    if (amount >= 1000000) {
      return `₦${(amount / 1000000).toFixed(1)}M`;
    } else if (amount >= 1000) {
      return `₦${(amount / 1000).toFixed(0)}K`;
    } else {
      return `₦${amount.toLocaleString()}`;
    }
  };

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <DollarSign className="w-5 h-5 text-green-600" />
              Revenue Trends
            </CardTitle>
            <CardDescription>
              Revenue performance over {timeRange} with growth analysis
            </CardDescription>
          </div>
          <div className="flex items-center gap-2">
            {showBreakdown && (
              <div className="flex rounded-lg border border-gray-200 p-1">
                <button
                  onClick={() => setSelectedMetric('total')}
                  className={`px-3 py-1 text-sm font-medium rounded-md transition-colors ${
                    selectedMetric === 'total'
                      ? 'bg-blue-500 text-white'
                      : 'text-gray-600 hover:text-gray-800'
                  }`}
                >
                  Total
                </button>
                <button
                  onClick={() => setSelectedMetric('breakdown')}
                  className={`px-3 py-1 text-sm font-medium rounded-md transition-colors ${
                    selectedMetric === 'breakdown'
                      ? 'bg-blue-500 text-white'
                      : 'text-gray-600 hover:text-gray-800'
                  }`}
                >
                  Breakdown
                </button>
              </div>
            )}
            <Badge variant={revenueGrowth > 0 ? "success" : "destructive"}>
              {revenueGrowth > 0 ? (
                <TrendingUp className="w-3 h-3 mr-1" />
              ) : (
                <TrendingDown className="w-3 h-3 mr-1" />
              )}
              {Math.abs(revenueGrowth).toFixed(1)}%
            </Badge>
            <Button variant="outline" size="sm">
              <Download className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {/* Summary Metrics */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-gray-50 rounded-lg p-3">
            <div className="text-sm text-gray-600">Total Revenue</div>
            <div className="text-lg font-bold text-gray-900">
              {formatCurrency(currentPeriodRevenue)}
            </div>
          </div>
          <div className="bg-gray-50 rounded-lg p-3">
            <div className="text-sm text-gray-600">Daily Average</div>
            <div className="text-lg font-bold text-gray-900">
              {formatCurrency(avgDailyRevenue)}
            </div>
          </div>
          <div className="bg-gray-50 rounded-lg p-3">
            <div className="text-sm text-gray-600">Highest Day</div>
            <div className="text-lg font-bold text-green-600">
              {formatCurrency(highestDay)}
            </div>
          </div>
          <div className="bg-gray-50 rounded-lg p-3">
            <div className="text-sm text-gray-600">Lowest Day</div>
            <div className="text-lg font-bold text-red-600">
              {formatCurrency(lowestDay)}
            </div>
          </div>
        </div>

        {/* Chart */}
        <div className="h-80">
          {chartType === 'area' ? (
            <AreaChart
              data={revenueData.map((point, index) => ({
                name: point.date,
                value: selectedMetric === 'total' ? point.totalRevenue : point.totalRevenue - point.processingFees - point.subscriptionRevenue - point.otherRevenue,
                fees: point.processingFees,
                subscriptions: point.subscriptionRevenue,
                other: point.otherRevenue
              }))}
              dataKey="value"
              gradientType="success"
              animate={true}
              height={300}
            />
          ) : (
            <LineChart
              data={chartData}
              gradientType="success"
              animate={true}
              height={300}
              options={{
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                  y: {
                    beginAtZero: true,
                    ticks: {
                      callback: function(value: any) {
                        return formatCurrency(value);
                      }
                    }
                  }
                },
                plugins: {
                  tooltip: {
                    callbacks: {
                      label: function(context: any) {
                        return `${context.dataset.label}: ${formatCurrency(context.parsed.y)}`;
                      }
                    }
                  }
                }
              }}
            />
          )}
        </div>

        {/* Revenue Breakdown (if breakdown view is selected) */}
        {selectedMetric === 'breakdown' && (
          <div className="mt-6 grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center p-3 border rounded-lg">
              <div className="text-sm text-gray-600">Processing Fees</div>
              <div className="text-lg font-semibold text-green-600">
                {formatCurrency(revenueData.reduce((sum, d) => sum + d.processingFees, 0))}
              </div>
              <div className="text-xs text-gray-500">
                {((revenueData.reduce((sum, d) => sum + d.processingFees, 0) / currentPeriodRevenue) * 100).toFixed(1)}%
              </div>
            </div>
            <div className="text-center p-3 border rounded-lg">
              <div className="text-sm text-gray-600">Subscriptions</div>
              <div className="text-lg font-semibold text-purple-600">
                {formatCurrency(revenueData.reduce((sum, d) => sum + d.subscriptionRevenue, 0))}
              </div>
              <div className="text-xs text-gray-500">
                {((revenueData.reduce((sum, d) => sum + d.subscriptionRevenue, 0) / currentPeriodRevenue) * 100).toFixed(1)}%
              </div>
            </div>
            <div className="text-center p-3 border rounded-lg">
              <div className="text-sm text-gray-600">Invoice Revenue</div>
              <div className="text-lg font-semibold text-blue-600">
                {formatCurrency(revenueData.reduce((sum, d) => sum + (d.totalRevenue - d.processingFees - d.subscriptionRevenue - d.otherRevenue), 0))}
              </div>
              <div className="text-xs text-gray-500">
                {((revenueData.reduce((sum, d) => sum + (d.totalRevenue - d.processingFees - d.subscriptionRevenue - d.otherRevenue), 0) / currentPeriodRevenue) * 100).toFixed(1)}%
              </div>
            </div>
            <div className="text-center p-3 border rounded-lg">
              <div className="text-sm text-gray-600">Other Revenue</div>
              <div className="text-lg font-semibold text-amber-600">
                {formatCurrency(revenueData.reduce((sum, d) => sum + d.otherRevenue, 0))}
              </div>
              <div className="text-xs text-gray-500">
                {((revenueData.reduce((sum, d) => sum + d.otherRevenue, 0) / currentPeriodRevenue) * 100).toFixed(1)}%
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default RevenueTrendsChart;