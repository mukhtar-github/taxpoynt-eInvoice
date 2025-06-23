/**
 * Integration Performance Metrics Component
 * Specialized bar charts for integration performance visualization
 */

import React, { useState, useMemo } from 'react';
import { Card, CardHeader, CardContent, CardTitle, CardDescription } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';
import { BarChart, RechartsBarChart } from '../ui/Charts';
import { 
  BarChart3, 
  Activity, 
  CheckCircle2, 
  AlertTriangle, 
  XCircle,
  Zap,
  Timer,
  Download,
  RefreshCw,
  Settings
} from 'lucide-react';

interface IntegrationMetric {
  name: string;
  type: 'ERP' | 'CRM' | 'POS' | 'API';
  successRate: number;
  avgResponseTime: number;
  totalRequests: number;
  failedRequests: number;
  uptime: number;
  lastSync: string;
  status: 'healthy' | 'warning' | 'critical';
}

interface IntegrationPerformanceProps {
  timeRange?: '24h' | '7d' | '30d' | '90d';
  className?: string;
  viewType?: 'success-rate' | 'response-time' | 'volume' | 'uptime';
  showDetails?: boolean;
}

const generateIntegrationData = (timeRange: string): IntegrationMetric[] => {
  const multiplier = timeRange === '24h' ? 0.1 : timeRange === '7d' ? 1 : timeRange === '30d' ? 4 : 12;
  
  const baseData = [
    {
      name: 'Odoo ERP',
      type: 'ERP' as const,
      baseRequests: 5000,
      baseUptime: 99.8,
      baseResponseTime: 245
    },
    {
      name: 'SAP Business One',
      type: 'ERP' as const,
      baseRequests: 3200,
      baseUptime: 98.9,
      baseResponseTime: 312
    },
    {
      name: 'QuickBooks',
      type: 'ERP' as const,
      baseRequests: 2800,
      baseUptime: 97.5,
      baseResponseTime: 189
    },
    {
      name: 'HubSpot CRM',
      type: 'CRM' as const,
      baseRequests: 1500,
      baseUptime: 99.2,
      baseResponseTime: 156
    },
    {
      name: 'Salesforce',
      type: 'CRM' as const,
      baseRequests: 1200,
      baseUptime: 99.6,
      baseResponseTime: 203
    },
    {
      name: 'FIRS API',
      type: 'API' as const,
      baseRequests: 8500,
      baseUptime: 99.9,
      baseResponseTime: 423
    },
    {
      name: 'Square POS',
      type: 'POS' as const,
      baseRequests: 800,
      baseUptime: 96.8,
      baseResponseTime: 134
    },
    {
      name: 'Custom REST API',
      type: 'API' as const,
      baseRequests: 650,
      baseUptime: 95.2,
      baseResponseTime: 289
    }
  ];

  return baseData.map(integration => {
    const totalRequests = Math.round(integration.baseRequests * multiplier);
    const variation = 0.95 + Math.random() * 0.1; // 5% variation
    const successRate = integration.baseUptime * variation;
    const failedRequests = Math.round(totalRequests * ((100 - successRate) / 100));
    const avgResponseTime = Math.round(integration.baseResponseTime * (0.8 + Math.random() * 0.4));
    
    const getStatus = (successRate: number, responseTime: number): 'healthy' | 'warning' | 'critical' => {
      if (successRate >= 98 && responseTime <= 300) return 'healthy';
      if (successRate >= 95 && responseTime <= 500) return 'warning';
      return 'critical';
    };

    const getLastSync = () => {
      const minutes = Math.floor(Math.random() * 60);
      if (minutes < 5) return 'Just now';
      if (minutes < 60) return `${minutes} minutes ago`;
      return `${Math.floor(minutes / 60)} hours ago`;
    };

    return {
      name: integration.name,
      type: integration.type,
      successRate: Math.min(99.9, successRate),
      avgResponseTime,
      totalRequests,
      failedRequests,
      uptime: Math.min(99.9, integration.baseUptime * variation),
      lastSync: getLastSync(),
      status: getStatus(successRate, avgResponseTime)
    };
  });
};

export const IntegrationPerformanceMetrics: React.FC<IntegrationPerformanceProps> = ({
  timeRange = '30d',
  className = '',
  viewType = 'success-rate',
  showDetails = true
}) => {
  const [selectedView, setSelectedView] = useState(viewType);
  const [isLoading, setIsLoading] = useState(false);
  
  const integrationData = useMemo(() => generateIntegrationData(timeRange), [timeRange]);
  
  // Calculate summary metrics
  const totalRequests = integrationData.reduce((sum, integration) => sum + integration.totalRequests, 0);
  const totalFailures = integrationData.reduce((sum, integration) => sum + integration.failedRequests, 0);
  const overallSuccessRate = totalRequests > 0 ? ((totalRequests - totalFailures) / totalRequests) * 100 : 0;
  const avgResponseTime = integrationData.reduce((sum, integration) => sum + integration.avgResponseTime, 0) / integrationData.length;
  
  const healthyCount = integrationData.filter(i => i.status === 'healthy').length;
  const warningCount = integrationData.filter(i => i.status === 'warning').length;
  const criticalCount = integrationData.filter(i => i.status === 'critical').length;

  // Prepare chart data based on selected view
  const getChartData = () => {
    const labels = integrationData.map(i => i.name);
    
    switch (selectedView) {
      case 'success-rate':
        return {
          labels,
          datasets: [{
            label: 'Success Rate (%)',
            data: integrationData.map(i => i.successRate),
            backgroundColor: integrationData.map(i => 
              i.status === 'healthy' ? 'rgba(16, 185, 129, 0.8)' :
              i.status === 'warning' ? 'rgba(245, 158, 11, 0.8)' :
              'rgba(239, 68, 68, 0.8)'
            ),
            borderColor: integrationData.map(i => 
              i.status === 'healthy' ? 'rgb(16, 185, 129)' :
              i.status === 'warning' ? 'rgb(245, 158, 11)' :
              'rgb(239, 68, 68)'
            ),
            borderWidth: 2
          }]
        };
      case 'response-time':
        return {
          labels,
          datasets: [{
            label: 'Response Time (ms)',
            data: integrationData.map(i => i.avgResponseTime),
            backgroundColor: integrationData.map(i => 
              i.avgResponseTime <= 200 ? 'rgba(16, 185, 129, 0.8)' :
              i.avgResponseTime <= 400 ? 'rgba(245, 158, 11, 0.8)' :
              'rgba(239, 68, 68, 0.8)'
            ),
            borderColor: 'rgba(59, 130, 246, 1)',
            borderWidth: 2
          }]
        };
      case 'volume':
        return {
          labels,
          datasets: [{
            label: 'Total Requests',
            data: integrationData.map(i => i.totalRequests),
            backgroundColor: 'rgba(139, 92, 246, 0.8)',
            borderColor: 'rgb(139, 92, 246)',
            borderWidth: 2
          }]
        };
      case 'uptime':
        return {
          labels,
          datasets: [{
            label: 'Uptime (%)',
            data: integrationData.map(i => i.uptime),
            backgroundColor: integrationData.map(i => 
              i.uptime >= 99 ? 'rgba(16, 185, 129, 0.8)' :
              i.uptime >= 97 ? 'rgba(245, 158, 11, 0.8)' :
              'rgba(239, 68, 68, 0.8)'
            ),
            borderColor: 'rgba(34, 197, 94, 1)',
            borderWidth: 2
          }]
        };
      default:
        return { labels: [], datasets: [] };
    }
  };

  const chartData = getChartData();

  const handleRefresh = () => {
    setIsLoading(true);
    setTimeout(() => setIsLoading(false), 1000);
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircle2 className="w-4 h-4 text-green-500" />;
      case 'warning':
        return <AlertTriangle className="w-4 h-4 text-amber-500" />;
      case 'critical':
        return <XCircle className="w-4 h-4 text-red-500" />;
      default:
        return <Activity className="w-4 h-4 text-gray-500" />;
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'ERP':
        return <BarChart3 className="w-4 h-4 text-blue-500" />;
      case 'CRM':
        return <Activity className="w-4 h-4 text-purple-500" />;
      case 'POS':
        return <Zap className="w-4 h-4 text-green-500" />;
      case 'API':
        return <Settings className="w-4 h-4 text-orange-500" />;
      default:
        return <Activity className="w-4 h-4 text-gray-500" />;
    }
  };

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="w-5 h-5 text-purple-600" />
              Integration Performance
            </CardTitle>
            <CardDescription>
              Performance metrics and health monitoring for all integrations
            </CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="success">
              {healthyCount} Healthy
            </Badge>
            {warningCount > 0 && (
              <Badge variant="warning">
                {warningCount} Warning
              </Badge>
            )}
            {criticalCount > 0 && (
              <Badge variant="destructive">
                {criticalCount} Critical
              </Badge>
            )}
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
        {/* Summary Metrics */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-gray-50 rounded-lg p-3">
            <div className="text-sm text-gray-600">Overall Success Rate</div>
            <div className="text-lg font-bold text-green-600">
              {overallSuccessRate.toFixed(1)}%
            </div>
          </div>
          <div className="bg-gray-50 rounded-lg p-3">
            <div className="text-sm text-gray-600">Avg Response Time</div>
            <div className="text-lg font-bold text-blue-600">
              {avgResponseTime.toFixed(0)}ms
            </div>
          </div>
          <div className="bg-gray-50 rounded-lg p-3">
            <div className="text-sm text-gray-600">Total Requests</div>
            <div className="text-lg font-bold text-gray-900">
              {totalRequests.toLocaleString()}
            </div>
          </div>
          <div className="bg-gray-50 rounded-lg p-3">
            <div className="text-sm text-gray-600">Failed Requests</div>
            <div className="text-lg font-bold text-red-600">
              {totalFailures.toLocaleString()}
            </div>
          </div>
        </div>

        {/* View Selector */}
        <div className="flex flex-wrap gap-2 mb-6">
          <div className="flex rounded-lg border border-gray-200 p-1">
            {(['success-rate', 'response-time', 'volume', 'uptime'] as const).map((view) => (
              <button
                key={view}
                onClick={() => setSelectedView(view)}
                className={`px-3 py-1 text-sm font-medium rounded-md transition-colors ${
                  selectedView === view
                    ? 'bg-blue-500 text-white'
                    : 'text-gray-600 hover:text-gray-800'
                }`}
              >
                {view === 'success-rate' ? 'Success Rate' :
                 view === 'response-time' ? 'Response Time' :
                 view === 'volume' ? 'Volume' : 'Uptime'}
              </button>
            ))}
          </div>
        </div>

        {/* Chart */}
        <div className="h-80 mb-6">
          <BarChart
            data={chartData}
            gradientType="purple"
            animate={true}
            height={300}
            options={{
              responsive: true,
              maintainAspectRatio: false,
              scales: {
                y: {
                  beginAtZero: true,
                  max: selectedView === 'success-rate' || selectedView === 'uptime' ? 100 : undefined,
                  ticks: {
                    callback: function(value: any) {
                      if (selectedView === 'success-rate' || selectedView === 'uptime') {
                        return value + '%';
                      } else if (selectedView === 'response-time') {
                        return value + 'ms';
                      } else {
                        return value.toLocaleString();
                      }
                    }
                  }
                }
              },
              plugins: {
                tooltip: {
                  callbacks: {
                    label: function(context: any) {
                      const integration = integrationData[context.dataIndex];
                      let suffix = '';
                      if (selectedView === 'success-rate' || selectedView === 'uptime') suffix = '%';
                      else if (selectedView === 'response-time') suffix = 'ms';
                      return `${context.dataset.label}: ${context.parsed.y}${suffix}`;
                    }
                  }
                }
              }
            }}
          />
        </div>

        {/* Detailed Integration List */}
        {showDetails && (
          <div className="space-y-4">
            <h4 className="font-semibold text-gray-900">Integration Details</h4>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              {integrationData.map((integration, index) => (
                <div key={index} className="border rounded-lg p-4">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                      {getTypeIcon(integration.type)}
                      <span className="font-medium text-gray-900">{integration.name}</span>
                      <Badge variant="outline" className="text-xs">
                        {integration.type}
                      </Badge>
                    </div>
                    {getStatusIcon(integration.status)}
                  </div>
                  
                  <div className="grid grid-cols-2 gap-3 text-sm">
                    <div>
                      <div className="text-gray-600">Success Rate</div>
                      <div className="font-semibold">{integration.successRate.toFixed(1)}%</div>
                    </div>
                    <div>
                      <div className="text-gray-600">Response Time</div>
                      <div className="font-semibold">{integration.avgResponseTime}ms</div>
                    </div>
                    <div>
                      <div className="text-gray-600">Requests</div>
                      <div className="font-semibold">{integration.totalRequests.toLocaleString()}</div>
                    </div>
                    <div>
                      <div className="text-gray-600">Last Sync</div>
                      <div className="font-semibold">{integration.lastSync}</div>
                    </div>
                  </div>
                  
                  {integration.failedRequests > 0 && (
                    <div className="mt-3 p-2 bg-red-50 rounded text-sm">
                      <span className="text-red-600 font-medium">
                        {integration.failedRequests} failed requests
                      </span>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default IntegrationPerformanceMetrics;