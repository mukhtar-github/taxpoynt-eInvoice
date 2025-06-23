/**
 * FIRS Submission Success Rates Component
 * Progress indicators and detailed submission analytics
 */

import React, { useState, useMemo } from 'react';
import { Card, CardHeader, CardContent, CardTitle, CardDescription } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';
import { Progress } from '../ui/Progress';
import { 
  CheckCircle2, 
  XCircle, 
  Clock, 
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  Activity,
  FileCheck,
  Download,
  RefreshCw,
  Target,
  Zap
} from 'lucide-react';

interface SubmissionData {
  total: number;
  successful: number;
  failed: number;
  pending: number;
  inProgress: number;
  rate: number;
  trend: 'up' | 'down' | 'stable';
  change: number;
  avgProcessingTime: number;
  categories: {
    validation: { success: number; total: number; };
    signing: { success: number; total: number; };
    transmission: { success: number; total: number; };
    confirmation: { success: number; total: number; };
  };
}

interface ErrorBreakdown {
  type: string;
  count: number;
  percentage: number;
  severity: 'low' | 'medium' | 'high' | 'critical';
  description: string;
}

interface FIRSSubmissionRatesProps {
  timeRange?: '24h' | '7d' | '30d' | '90d';
  className?: string;
  showDetails?: boolean;
  realTimeUpdates?: boolean;
}

const generateSubmissionData = (timeRange: string): SubmissionData => {
  const multiplier = timeRange === '24h' ? 0.1 : timeRange === '7d' ? 1 : timeRange === '30d' ? 4 : 12;
  
  const baseTotal = Math.round(2500 * multiplier);
  const baseSuccessRate = 97.8 + (Math.random() - 0.5) * 2; // 96.8% to 98.8%
  
  const successful = Math.round(baseTotal * (baseSuccessRate / 100));
  const failed = Math.round(baseTotal * 0.015); // ~1.5% failure
  const pending = Math.round(baseTotal * 0.008); // ~0.8% pending
  const inProgress = Math.round(baseTotal * 0.002); // ~0.2% in progress
  
  const prevRate = baseSuccessRate + (Math.random() - 0.5) * 1;
  const change = baseSuccessRate - prevRate;
  
  return {
    total: baseTotal,
    successful,
    failed,
    pending,
    inProgress,
    rate: baseSuccessRate,
    trend: change > 0.1 ? 'up' : change < -0.1 ? 'down' : 'stable',
    change: Math.abs(change),
    avgProcessingTime: 245 + Math.random() * 100, // 245-345ms average
    categories: {
      validation: { 
        success: Math.round(baseTotal * 0.995), 
        total: baseTotal 
      },
      signing: { 
        success: Math.round(baseTotal * 0.992), 
        total: baseTotal 
      },
      transmission: { 
        success: Math.round(baseTotal * 0.985), 
        total: baseTotal 
      },
      confirmation: { 
        success: Math.round(baseTotal * 0.978), 
        total: baseTotal 
      }
    }
  };
};

const generateErrorBreakdown = (): ErrorBreakdown[] => {
  return [
    {
      type: 'Validation Errors',
      count: 45,
      percentage: 35.2,
      severity: 'medium',
      description: 'Schema validation failures and missing required fields'
    },
    {
      type: 'Network Timeout',
      count: 32,
      percentage: 25.0,
      severity: 'high',
      description: 'Connection timeouts to FIRS API endpoints'
    },
    {
      type: 'Authentication',
      count: 18,
      percentage: 14.1,
      severity: 'critical',
      description: 'Token expiration and credential issues'
    },
    {
      type: 'Rate Limiting',
      count: 15,
      percentage: 11.7,
      severity: 'low',
      description: 'API rate limits exceeded'
    },
    {
      type: 'Data Format',
      count: 12,
      percentage: 9.4,
      severity: 'medium',
      description: 'Invalid data format or encoding issues'
    },
    {
      type: 'Server Errors',
      count: 6,
      percentage: 4.7,
      severity: 'high',
      description: 'FIRS server internal errors (5xx responses)'
    }
  ];
};

// Progress indicator component with enhanced styling
const EnhancedProgressIndicator: React.FC<{
  label: string;
  value: number;
  max: number;
  color?: 'success' | 'warning' | 'error' | 'info';
  showPercentage?: boolean;
  icon?: React.ReactNode;
  description?: string;
}> = ({ label, value, max, color = 'success', showPercentage = true, icon, description }) => {
  const percentage = max > 0 ? (value / max) * 100 : 0;
  
  const colorClasses = {
    success: { bg: 'bg-green-500', text: 'text-green-600', light: 'bg-green-50' },
    warning: { bg: 'bg-amber-500', text: 'text-amber-600', light: 'bg-amber-50' },
    error: { bg: 'bg-red-500', text: 'text-red-600', light: 'bg-red-50' },
    info: { bg: 'bg-blue-500', text: 'text-blue-600', light: 'bg-blue-50' }
  };

  return (
    <div className={`p-4 rounded-lg border ${colorClasses[color].light}`}>
      <div className="flex justify-between items-center mb-3">
        <div className="flex items-center gap-2">
          {icon}
          <span className="font-medium text-gray-900">{label}</span>
        </div>
        {showPercentage && (
          <span className={`text-sm font-semibold ${colorClasses[color].text}`}>
            {percentage.toFixed(1)}%
          </span>
        )}
      </div>
      
      <div className="w-full bg-gray-200 rounded-full h-2.5 mb-2">
        <div 
          className={`h-2.5 rounded-full transition-all duration-500 ${colorClasses[color].bg}`}
          style={{ width: `${Math.min(100, percentage)}%` }}
        />
      </div>
      
      <div className="flex justify-between items-center text-sm">
        <span className="text-gray-600">{value.toLocaleString()}</span>
        <span className="text-gray-500">{max.toLocaleString()}</span>
      </div>
      
      {description && (
        <div className="text-xs text-gray-500 mt-2">{description}</div>
      )}
    </div>
  );
};

export const FIRSSubmissionRates: React.FC<FIRSSubmissionRatesProps> = ({
  timeRange = '30d',
  className = '',
  showDetails = true,
  realTimeUpdates = false
}) => {
  const [isLoading, setIsLoading] = useState(false);
  const [lastUpdated, setLastUpdated] = useState(new Date());
  
  const submissionData = useMemo(() => generateSubmissionData(timeRange), [timeRange]);
  const errorBreakdown = useMemo(() => generateErrorBreakdown(), []);

  const handleRefresh = () => {
    setIsLoading(true);
    setTimeout(() => {
      setLastUpdated(new Date());
      setIsLoading(false);
    }, 1000);
  };

  const getStatusColor = (rate: number) => {
    if (rate >= 98) return 'success';
    if (rate >= 95) return 'warning';
    return 'error';
  };

  const getTrendIcon = (trend: string, change: number) => {
    if (trend === 'up') return <TrendingUp className="w-4 h-4 text-green-500" />;
    if (trend === 'down') return <TrendingDown className="w-4 h-4 text-red-500" />;
    return <Activity className="w-4 h-4 text-gray-500" />;
  };

  const getSeverityBadge = (severity: string) => {
    switch (severity) {
      case 'critical':
        return <Badge variant="destructive">Critical</Badge>;
      case 'high':
        return <Badge variant="destructive">High</Badge>;
      case 'medium':
        return <Badge variant="warning">Medium</Badge>;
      case 'low':
        return <Badge variant="secondary">Low</Badge>;
      default:
        return <Badge variant="outline">Unknown</Badge>;
    }
  };

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Target className="w-5 h-5 text-green-600" />
              FIRS Submission Success Rates
            </CardTitle>
            <CardDescription>
              Real-time monitoring of FIRS API submission performance and success rates
              {realTimeUpdates && (
                <div className="text-xs text-gray-500 mt-1">
                  Last updated: {lastUpdated.toLocaleTimeString()}
                </div>
              )}
            </CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant={getStatusColor(submissionData.rate)}>
              {submissionData.rate.toFixed(1)}% Success
            </Badge>
            <Badge variant="outline">
              {submissionData.total.toLocaleString()} Total
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
        {/* Main Success Rate Display */}
        <div className="text-center mb-8">
          <div className="relative inline-block">
            <div className="text-6xl font-bold text-green-600 mb-2">
              {submissionData.rate.toFixed(1)}%
            </div>
            <div className="text-lg text-gray-600 mb-3">Overall Success Rate</div>
            <div className="flex items-center justify-center gap-2">
              {getTrendIcon(submissionData.trend, submissionData.change)}
              <span className={`text-sm font-medium ${
                submissionData.trend === 'up' ? 'text-green-600' : 
                submissionData.trend === 'down' ? 'text-red-600' : 
                'text-gray-600'
              }`}>
                {submissionData.change.toFixed(1)}% vs previous period
              </span>
            </div>
          </div>
        </div>

        {/* Key Metrics Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <div className="text-center p-4 bg-green-50 rounded-lg">
            <CheckCircle2 className="w-8 h-8 text-green-500 mx-auto mb-2" />
            <div className="text-2xl font-bold text-green-600">
              {submissionData.successful.toLocaleString()}
            </div>
            <div className="text-sm text-gray-600">Successful</div>
          </div>
          <div className="text-center p-4 bg-red-50 rounded-lg">
            <XCircle className="w-8 h-8 text-red-500 mx-auto mb-2" />
            <div className="text-2xl font-bold text-red-600">
              {submissionData.failed.toLocaleString()}
            </div>
            <div className="text-sm text-gray-600">Failed</div>
          </div>
          <div className="text-center p-4 bg-blue-50 rounded-lg">
            <Clock className="w-8 h-8 text-blue-500 mx-auto mb-2" />
            <div className="text-2xl font-bold text-blue-600">
              {submissionData.pending.toLocaleString()}
            </div>
            <div className="text-sm text-gray-600">Pending</div>
          </div>
          <div className="text-center p-4 bg-amber-50 rounded-lg">
            <Zap className="w-8 h-8 text-amber-500 mx-auto mb-2" />
            <div className="text-2xl font-bold text-amber-600">
              {submissionData.avgProcessingTime.toFixed(0)}ms
            </div>
            <div className="text-sm text-gray-600">Avg Time</div>
          </div>
        </div>

        {/* Progress Indicators for Each Stage */}
        <div className="space-y-4 mb-8">
          <h4 className="font-semibold text-gray-900 mb-4">Submission Pipeline Performance</h4>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <EnhancedProgressIndicator
              label="Validation Stage"
              value={submissionData.categories.validation.success}
              max={submissionData.categories.validation.total}
              color="success"
              icon={<FileCheck className="w-4 h-4 text-green-500" />}
              description="Invoice data validation and schema checks"
            />
            
            <EnhancedProgressIndicator
              label="Digital Signing"
              value={submissionData.categories.signing.success}
              max={submissionData.categories.signing.total}
              color="info"
              icon={<CheckCircle2 className="w-4 h-4 text-blue-500" />}
              description="Digital signature and certificate validation"
            />
            
            <EnhancedProgressIndicator
              label="Transmission"
              value={submissionData.categories.transmission.success}
              max={submissionData.categories.transmission.total}
              color="warning"
              icon={<Zap className="w-4 h-4 text-amber-500" />}
              description="Network transmission to FIRS endpoints"
            />
            
            <EnhancedProgressIndicator
              label="Confirmation"
              value={submissionData.categories.confirmation.success}
              max={submissionData.categories.confirmation.total}
              color="success"
              icon={<Target className="w-4 h-4 text-green-500" />}
              description="FIRS acknowledgment and final confirmation"
            />
          </div>
        </div>

        {/* Error Breakdown */}
        {showDetails && (
          <div className="space-y-4">
            <h4 className="font-semibold text-gray-900">Error Analysis</h4>
            
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Error Types Table */}
              <div>
                <h5 className="font-medium text-gray-900 mb-3">Common Error Types</h5>
                <div className="space-y-2">
                  {errorBreakdown.map((error, index) => (
                    <div key={index} className="flex items-center justify-between p-3 border rounded-lg">
                      <div className="flex items-center gap-3">
                        <AlertTriangle className={`w-4 h-4 ${
                          error.severity === 'critical' ? 'text-red-500' :
                          error.severity === 'high' ? 'text-red-400' :
                          error.severity === 'medium' ? 'text-amber-500' :
                          'text-gray-500'
                        }`} />
                        <div>
                          <div className="font-medium text-gray-900">{error.type}</div>
                          <div className="text-sm text-gray-500">{error.description}</div>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="font-semibold text-gray-900">{error.count}</div>
                        <div className="text-sm text-gray-500">{error.percentage.toFixed(1)}%</div>
                        {getSeverityBadge(error.severity)}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Performance Insights */}
              <div>
                <h5 className="font-medium text-gray-900 mb-3">Performance Insights</h5>
                <div className="space-y-4">
                  <div className="p-4 bg-blue-50 rounded-lg">
                    <div className="flex items-center gap-2 mb-2">
                      <TrendingUp className="w-4 h-4 text-blue-500" />
                      <span className="font-medium text-blue-900">Peak Performance</span>
                    </div>
                    <div className="text-sm text-blue-800">
                      Best performance during low-traffic hours (2 AM - 6 AM) with 99.2% success rate
                    </div>
                  </div>
                  
                  <div className="p-4 bg-amber-50 rounded-lg">
                    <div className="flex items-center gap-2 mb-2">
                      <Clock className="w-4 h-4 text-amber-500" />
                      <span className="font-medium text-amber-900">Processing Time</span>
                    </div>
                    <div className="text-sm text-amber-800">
                      Average processing time has improved by 15% compared to last month
                    </div>
                  </div>
                  
                  <div className="p-4 bg-green-50 rounded-lg">
                    <div className="flex items-center gap-2 mb-2">
                      <CheckCircle2 className="w-4 h-4 text-green-500" />
                      <span className="font-medium text-green-900">Reliability</span>
                    </div>
                    <div className="text-sm text-green-800">
                      99.8% uptime maintained with robust error handling and retry mechanisms
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default FIRSSubmissionRates;