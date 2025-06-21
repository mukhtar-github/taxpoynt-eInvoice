/**
 * Integration Data Visualization Components
 * 
 * Week 3 Implementation: Advanced data visualization with:
 * - Integration performance charts and graphs
 * - Real-time sync status visualizations
 * - Mobile-responsive chart layouts
 * - Interactive data exploration
 * - Gradient-based modern styling
 */

import React, { useState, useMemo } from 'react';
import { 
  TrendingUp, 
  TrendingDown, 
  Activity, 
  BarChart3, 
  PieChart, 
  LineChart,
  Calendar,
  Filter,
  Download,
  RefreshCw,
  AlertTriangle,
  CheckCircle,
  Clock
} from 'lucide-react';

import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { LoadingSpinner } from '@/components/ui/LoadingStates';

// Mock data types (replace with actual API types)
interface IntegrationMetric {
  id: string;
  name: string;
  platform: string;
  type: 'erp' | 'crm' | 'pos';
  syncCount: number;
  successRate: number;
  avgResponseTime: number;
  errorCount: number;
  lastSync: string;
  trend: 'up' | 'down' | 'stable';
}

interface SyncActivityData {
  timestamp: string;
  integration: string;
  status: 'success' | 'error' | 'warning';
  recordsProcessed: number;
  duration: number;
}

interface ChartDataPoint {
  label: string;
  value: number;
  color?: string;
  metadata?: any;
}

// Custom SVG Chart Components (lightweight alternative to chart libraries)

// Simple Bar Chart Component
export const SimpleBarChart: React.FC<{
  data: ChartDataPoint[];
  height?: number;
  showValues?: boolean;
  className?: string;
}> = ({ data, height = 200, showValues = true, className }) => {
  const maxValue = Math.max(...data.map(d => d.value));
  const chartPadding = 40;
  const barWidth = (100 - chartPadding) / data.length;

  return (
    <div className={`w-full ${className}`}>
      <svg width="100%" height={height} className="overflow-visible">
        {/* Grid lines */}
        {[0, 25, 50, 75, 100].map(percent => (
          <g key={percent}>
            <line
              x1="0"
              y1={height - (height * percent / 100)}
              x2="100%"
              y2={height - (height * percent / 100)}
              stroke="#e5e7eb"
              strokeWidth="1"
            />
            <text
              x="0"
              y={height - (height * percent / 100) - 5}
              fontSize="10"
              fill="#6b7280"
            >
              {Math.round(maxValue * percent / 100)}
            </text>
          </g>
        ))}
        
        {/* Bars */}
        {data.map((item, index) => {
          const barHeight = (item.value / maxValue) * (height - 40);
          const x = (index * barWidth) + (barWidth / 4);
          
          return (
            <g key={index}>
              {/* Bar with gradient */}
              <defs>
                <linearGradient id={`gradient-${index}`} x1="0%" y1="0%" x2="0%" y2="100%">
                  <stop offset="0%" stopColor={item.color || '#3b82f6'} stopOpacity="0.8" />
                  <stop offset="100%" stopColor={item.color || '#3b82f6'} stopOpacity="0.4" />
                </linearGradient>
              </defs>
              
              <rect
                x={`${x}%`}
                y={height - barHeight - 20}
                width={`${barWidth / 2}%`}
                height={barHeight}
                fill={`url(#gradient-${index})`}
                rx="4"
                className="transition-all duration-300 hover:opacity-80 cursor-pointer"
              />
              
              {/* Value labels */}
              {showValues && (
                <text
                  x={`${x + (barWidth / 4)}%`}
                  y={height - barHeight - 25}
                  textAnchor="middle"
                  fontSize="10"
                  fill="#374151"
                  fontWeight="500"
                >
                  {item.value}
                </text>
              )}
              
              {/* X-axis labels */}
              <text
                x={`${x + (barWidth / 4)}%`}
                y={height - 5}
                textAnchor="middle"
                fontSize="10"
                fill="#6b7280"
              >
                {item.label.length > 8 ? `${item.label.slice(0, 8)}...` : item.label}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
};

// Simple Line Chart Component
export const SimpleLineChart: React.FC<{
  data: ChartDataPoint[];
  height?: number;
  showDots?: boolean;
  className?: string;
}> = ({ data, height = 200, showDots = true, className }) => {
  const maxValue = Math.max(...data.map(d => d.value));
  const minValue = Math.min(...data.map(d => d.value));
  const range = maxValue - minValue || 1;

  const points = data.map((item, index) => {
    const x = (index / (data.length - 1)) * 100;
    const y = height - 40 - ((item.value - minValue) / range) * (height - 80);
    return `${x},${y}`;
  }).join(' ');

  return (
    <div className={`w-full ${className}`}>
      <svg width="100%" height={height} className="overflow-visible">
        {/* Grid lines */}
        {[0, 25, 50, 75, 100].map(percent => (
          <line
            key={percent}
            x1="0"
            y1={height - 40 - (percent / 100) * (height - 80)}
            x2="100%"
            y2={height - 40 - (percent / 100) * (height - 80)}
            stroke="#e5e7eb"
            strokeWidth="1"
          />
        ))}
        
        {/* Area under curve (gradient fill) */}
        <defs>
          <linearGradient id="area-gradient" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="#3b82f6" stopOpacity="0.3" />
            <stop offset="100%" stopColor="#3b82f6" stopOpacity="0.05" />
          </linearGradient>
        </defs>
        
        <path
          d={`M 0,${height - 40} L ${points} L 100,${height - 40} Z`}
          fill="url(#area-gradient)"
        />
        
        {/* Line */}
        <polyline
          points={points}
          fill="none"
          stroke="#3b82f6"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          className="drop-shadow-sm"
        />
        
        {/* Data points */}
        {showDots && data.map((item, index) => {
          const x = (index / (data.length - 1)) * 100;
          const y = height - 40 - ((item.value - minValue) / range) * (height - 80);
          
          return (
            <circle
              key={index}
              cx={`${x}%`}
              cy={y}
              r="4"
              fill="#ffffff"
              stroke="#3b82f6"
              strokeWidth="2"
              className="hover:r-6 transition-all duration-200 cursor-pointer drop-shadow-sm"
            />
          );
        })}
        
        {/* X-axis labels */}
        {data.map((item, index) => {
          const x = (index / (data.length - 1)) * 100;
          return (
            <text
              key={index}
              x={`${x}%`}
              y={height - 10}
              textAnchor="middle"
              fontSize="10"
              fill="#6b7280"
            >
              {item.label}
            </text>
          );
        })}
      </svg>
    </div>
  );
};

// Integration Performance Overview
export const IntegrationPerformanceChart: React.FC<{
  integrations: IntegrationMetric[];
  isLoading?: boolean;
  className?: string;
}> = ({ integrations, isLoading = false, className }) => {
  const [viewType, setViewType] = useState<'success-rate' | 'sync-count' | 'response-time'>('success-rate');

  const chartData = useMemo(() => {
    return integrations.map(integration => ({
      label: integration.name,
      value: viewType === 'success-rate' 
        ? integration.successRate
        : viewType === 'sync-count'
        ? integration.syncCount
        : integration.avgResponseTime,
      color: integration.type === 'erp' 
        ? '#8b5cf6' 
        : integration.type === 'crm' 
        ? '#f59e0b' 
        : '#10b981',
      metadata: integration
    }));
  }, [integrations, viewType]);

  return (
    <Card className={`p-6 ${className}`}>
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold mb-1">Integration Performance</h3>
          <p className="text-sm text-text-secondary">
            Monitor sync performance across all integrations
          </p>
        </div>
        
        <div className="flex gap-2 mt-4 sm:mt-0">
          <select
            value={viewType}
            onChange={(e) => setViewType(e.target.value as any)}
            className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary focus:border-transparent"
          >
            <option value="success-rate">Success Rate (%)</option>
            <option value="sync-count">Sync Count</option>
            <option value="response-time">Response Time (ms)</option>
          </select>
          
          <Button variant="outline" size="sm">
            <Download className="w-4 h-4" />
          </Button>
        </div>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center h-64">
          <LoadingSpinner size="lg" />
        </div>
      ) : (
        <SimpleBarChart 
          data={chartData} 
          height={250}
          className="mb-4"
        />
      )}

      {/* Legend */}
      <div className="flex flex-wrap gap-4 text-sm">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 bg-purple-500 rounded"></div>
          <span>ERP Systems</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 bg-amber-500 rounded"></div>
          <span>CRM Systems</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 bg-emerald-500 rounded"></div>
          <span>POS Systems</span>
        </div>
      </div>
    </Card>
  );
};

// Real-time Sync Activity Monitor
export const SyncActivityMonitor: React.FC<{
  activities: SyncActivityData[];
  isLoading?: boolean;
  className?: string;
}> = ({ activities, isLoading = false, className }) => {
  const [timeRange, setTimeRange] = useState<'1h' | '6h' | '24h' | '7d'>('6h');

  const activityTrend = useMemo(() => {
    // Group activities by hour for trend visualization
    const now = new Date();
    const hoursBack = timeRange === '1h' ? 1 : timeRange === '6h' ? 6 : timeRange === '24h' ? 24 : 168;
    const points: ChartDataPoint[] = [];

    for (let i = hoursBack; i >= 0; i--) {
      const time = new Date(now.getTime() - i * 60 * 60 * 1000);
      const hourActivities = activities.filter(activity => {
        const activityTime = new Date(activity.timestamp);
        return Math.abs(activityTime.getTime() - time.getTime()) < 30 * 60 * 1000; // 30 min window
      });

      points.push({
        label: time.getHours().toString().padStart(2, '0') + ':00',
        value: hourActivities.reduce((sum, activity) => sum + activity.recordsProcessed, 0)
      });
    }

    return points;
  }, [activities, timeRange]);

  return (
    <Card className={`p-6 ${className}`}>
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold mb-1 flex items-center gap-2">
            <Activity className="w-5 h-5 text-primary" />
            Sync Activity
          </h3>
          <p className="text-sm text-text-secondary">
            Real-time synchronization monitoring
          </p>
        </div>
        
        <div className="flex gap-2 mt-4 sm:mt-0">
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value as any)}
            className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary focus:border-transparent"
          >
            <option value="1h">Last Hour</option>
            <option value="6h">Last 6 Hours</option>
            <option value="24h">Last 24 Hours</option>
            <option value="7d">Last 7 Days</option>
          </select>
          
          <Button variant="outline" size="sm">
            <RefreshCw className="w-4 h-4" />
          </Button>
        </div>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center h-48">
          <LoadingSpinner size="lg" />
        </div>
      ) : (
        <SimpleLineChart 
          data={activityTrend}
          height={200}
          className="mb-6"
        />
      )}

      {/* Recent Activity List */}
      <div className="border-t pt-4">
        <h4 className="font-medium mb-3">Recent Activity</h4>
        <div className="space-y-3 max-h-32 overflow-y-auto">
          {activities.slice(0, 5).map((activity, index) => (
            <div key={index} className="flex items-center justify-between text-sm">
              <div className="flex items-center gap-3">
                {activity.status === 'success' ? (
                  <CheckCircle className="w-4 h-4 text-success" />
                ) : activity.status === 'error' ? (
                  <AlertTriangle className="w-4 h-4 text-error" />
                ) : (
                  <Clock className="w-4 h-4 text-warning" />
                )}
                <span className="font-medium">{activity.integration}</span>
                <span className="text-text-secondary">
                  {activity.recordsProcessed} records
                </span>
              </div>
              <div className="text-text-secondary">
                {new Date(activity.timestamp).toLocaleTimeString()}
              </div>
            </div>
          ))}
        </div>
      </div>
    </Card>
  );
};

// Integration Health Dashboard
export const IntegrationHealthDashboard: React.FC<{
  integrations: IntegrationMetric[];
  isLoading?: boolean;
  className?: string;
}> = ({ integrations, isLoading = false, className }) => {
  const healthMetrics = useMemo(() => {
    const total = integrations.length;
    const healthy = integrations.filter(i => i.successRate >= 95 && i.errorCount === 0).length;
    const warning = integrations.filter(i => i.successRate >= 80 && i.successRate < 95).length;
    const critical = integrations.filter(i => i.successRate < 80 || i.errorCount > 0).length;

    return { total, healthy, warning, critical };
  }, [integrations]);

  const healthData: ChartDataPoint[] = [
    { label: 'Healthy', value: healthMetrics.healthy, color: '#10b981' },
    { label: 'Warning', value: healthMetrics.warning, color: '#f59e0b' },
    { label: 'Critical', value: healthMetrics.critical, color: '#ef4444' }
  ];

  return (
    <div className={`grid grid-cols-1 lg:grid-cols-2 gap-6 ${className}`}>
      {/* Health Overview */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">Integration Health</h3>
        
        {isLoading ? (
          <div className="flex items-center justify-center h-32">
            <LoadingSpinner size="lg" />
          </div>
        ) : (
          <>
            {/* Health metrics grid */}
            <div className="grid grid-cols-3 gap-4 mb-6">
              <div className="text-center">
                <div className="text-2xl font-bold text-success">{healthMetrics.healthy}</div>
                <div className="text-sm text-text-secondary">Healthy</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-warning">{healthMetrics.warning}</div>
                <div className="text-sm text-text-secondary">Warning</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-error">{healthMetrics.critical}</div>
                <div className="text-sm text-text-secondary">Critical</div>
              </div>
            </div>

            {/* Health distribution chart */}
            <SimpleBarChart 
              data={healthData}
              height={150}
              showValues={true}
            />
          </>
        )}
      </Card>

      {/* Integration Status List */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">Integration Status</h3>
        
        {isLoading ? (
          <div className="flex items-center justify-center h-32">
            <LoadingSpinner size="lg" />
          </div>
        ) : (
          <div className="space-y-3 max-h-80 overflow-y-auto">
            {integrations.map((integration) => (
              <div key={integration.id} className="flex items-center justify-between p-3 border border-gray-200 rounded-lg">
                <div className="flex items-center gap-3">
                  <div className={`w-3 h-3 rounded-full ${
                    integration.successRate >= 95 && integration.errorCount === 0
                      ? 'bg-success'
                      : integration.successRate >= 80
                      ? 'bg-warning'
                      : 'bg-error'
                  }`} />
                  <div>
                    <div className="font-medium">{integration.name}</div>
                    <div className="text-sm text-text-secondary capitalize">
                      {integration.platform} {integration.type}
                    </div>
                  </div>
                </div>
                
                <div className="text-right">
                  <div className="text-sm font-medium">
                    {integration.successRate}% success
                  </div>
                  <div className="text-xs text-text-secondary">
                    {integration.errorCount} errors
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
};

export default {
  SimpleBarChart,
  SimpleLineChart,
  IntegrationPerformanceChart,
  SyncActivityMonitor,
  IntegrationHealthDashboard
};