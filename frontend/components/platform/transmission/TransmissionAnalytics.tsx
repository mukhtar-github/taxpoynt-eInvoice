import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../../ui/Card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../ui/Select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../ui/Tabs';
import { Badge } from '../../ui/Badge';
import { Button } from '../../ui/Button';
import { Loader2, BarChart, PieChart, LineChart, Clock, RefreshCw, Calendar } from 'lucide-react';
import transmissionApiService from '../../../services/transmissionApiService';
import { useToast } from '../../ui/Toast';

interface TransmissionAnalyticsProps {
  organizationId?: string;
  refreshInterval?: number; // in milliseconds
  defaultTimeRange?: string;
  defaultMetrics?: string[];
}

// Define analytics data structure
interface AnalyticsData {
  volume?: any;
  success_rate?: any;
  performance?: any;
  retries?: any;
  errors?: any;
  metadata: {
    start_date: string;
    end_date: string;
    interval: string;
    organization_id?: string;
  };
}

const TransmissionAnalytics: React.FC<TransmissionAnalyticsProps> = ({
  organizationId,
  refreshInterval = 60000,
  defaultTimeRange = '7d',
  defaultMetrics = ['volume', 'success_rate', 'performance']
}) => {
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [timeRange, setTimeRange] = useState<string>(defaultTimeRange);
  const [timeInterval, setTimeInterval] = useState<'hour' | 'day' | 'week' | 'month'>('day');
  const [activeTab, setActiveTab] = useState<string>('volume');
  const toast = useToast();

  const timeRangeOptions = [
    { value: '24h', label: 'Last 24 Hours' },
    { value: '7d', label: 'Last 7 Days' },
    { value: '30d', label: 'Last 30 Days' },
    { value: '90d', label: 'Last 3 Months' }
  ];

  const intervalOptions = [
    { value: 'hour', label: 'Hourly' },
    { value: 'day', label: 'Daily' },
    { value: 'week', label: 'Weekly' },
    { value: 'month', label: 'Monthly' }
  ];

  const fetchAnalyticsData = async () => {
    try {
      setLoading(true);
      
      // Calculate date range from timeRange
      const endDate = new Date();
      let startDate = new Date();
      
      switch (timeRange) {
        case '24h':
          startDate.setHours(startDate.getHours() - 24);
          break;
        case '7d':
          startDate.setDate(startDate.getDate() - 7);
          break;
        case '30d':
          startDate.setDate(startDate.getDate() - 30);
          break;
        case '90d':
          startDate.setDate(startDate.getDate() - 90);
          break;
        default:
          startDate.setDate(startDate.getDate() - 7);
      }
      
      const response = await transmissionApiService.getTransmissionAnalytics(
        startDate,
        endDate,
        organizationId,
        timeInterval,
        defaultMetrics
      );
      
      if (response.error) {
        setError(response.error);
        return;
      }
      
      setAnalytics(response.data as AnalyticsData);
      setError(null);
    } catch (err) {
      setError('Failed to fetch transmission analytics data');
      console.error('Analytics fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalyticsData();
    
    // Set up refresh interval
    if (refreshInterval > 0) {
      const intervalId = setInterval(fetchAnalyticsData, refreshInterval);
      return () => clearInterval(intervalId);
    }
  }, [timeRange, timeInterval, organizationId]);

  const handleTimeRangeChange = (value: string) => {
    setTimeRange(value);
    
    // Adjust interval based on timeRange for better visualization
    if (value === '24h') {
      setTimeInterval('hour');
    } else if (value === '7d') {
      setTimeInterval('day');
    } else if (value === '30d') {
      setTimeInterval('day');
    } else {
      setTimeInterval('week');
    }
  };

  const handleRefresh = () => {
    fetchAnalyticsData();
  };

  // Render volume metrics chart
  const renderVolumeChart = () => {
    if (!analytics?.volume) return <div className="text-gray-500 text-center py-8">No volume data available</div>;
    
    const data = analytics.volume;
    
    return (
      <div className="space-y-6">
        <div className="bg-gray-50 rounded-lg p-4">
          <h3 className="text-sm font-medium mb-3">Transmission Volume by Status</h3>
          <div className="h-64 relative">
            {/* Replace with your preferred chart library component */}
            <div className="flex justify-center items-center h-full">
              <div className="text-gray-500">Chart visualization would display here</div>
            </div>
          </div>
        </div>
        
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {['completed', 'failed', 'pending', 'retrying'].map(status => (
            <div key={status} className="bg-gray-50 p-3 rounded-lg">
              <div className="text-sm text-gray-500 mb-1 capitalize">{status}</div>
              <div className="text-xl font-semibold">
                {data.summary?.[status] || 0}
              </div>
            </div>
          ))}
        </div>
        
        <div className="bg-white rounded-lg border p-3">
          <h3 className="text-sm font-medium mb-2">Volume Trends</h3>
          <div className="h-40 relative">
            {/* Replace with your preferred chart library component */}
            <div className="flex justify-center items-center h-full">
              <div className="text-gray-500">Trend visualization would display here</div>
            </div>
          </div>
        </div>
      </div>
    );
  };

  // Render success rate metrics chart
  const renderSuccessRateChart = () => {
    if (!analytics?.success_rate) return <div className="text-gray-500 text-center py-8">No success rate data available</div>;
    
    const data = analytics.success_rate;
    
    return (
      <div className="space-y-6">
        <div className="bg-gray-50 rounded-lg p-4">
          <h3 className="text-sm font-medium mb-3">Success Rate Over Time</h3>
          <div className="h-64 relative">
            {/* Replace with your preferred chart library component */}
            <div className="flex justify-center items-center h-full">
              <div className="text-gray-500">Chart visualization would display here</div>
            </div>
          </div>
        </div>
        
        <div className="grid grid-cols-2 gap-3">
          <div className="bg-gray-50 p-3 rounded-lg">
            <div className="text-sm text-gray-500 mb-1">Average Success Rate</div>
            <div className="text-xl font-semibold">
              {(data.average_success_rate || 0).toFixed(1)}%
            </div>
          </div>
          <div className="bg-gray-50 p-3 rounded-lg">
            <div className="text-sm text-gray-500 mb-1">First Attempt Success</div>
            <div className="text-xl font-semibold">
              {(data.first_attempt_success_rate || 0).toFixed(1)}%
            </div>
          </div>
        </div>
      </div>
    );
  };

  // Render performance metrics chart
  const renderPerformanceChart = () => {
    if (!analytics?.performance) return <div className="text-gray-500 text-center py-8">No performance data available</div>;
    
    const data = analytics.performance;
    
    return (
      <div className="space-y-6">
        <div className="bg-gray-50 rounded-lg p-4">
          <h3 className="text-sm font-medium mb-3">Processing Time Breakdown</h3>
          <div className="h-64 relative">
            {/* Replace with your preferred chart library component */}
            <div className="flex justify-center items-center h-full">
              <div className="text-gray-500">Chart visualization would display here</div>
            </div>
          </div>
        </div>
        
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          <div className="bg-gray-50 p-3 rounded-lg">
            <div className="text-sm text-gray-500 mb-1">Avg Processing Time</div>
            <div className="text-xl font-semibold">
              {(data.avg_processing_time_ms || 0).toFixed(0)} ms
            </div>
          </div>
          <div className="bg-gray-50 p-3 rounded-lg">
            <div className="text-sm text-gray-500 mb-1">Avg Encryption Time</div>
            <div className="text-xl font-semibold">
              {(data.avg_encryption_time_ms || 0).toFixed(0)} ms
            </div>
          </div>
          <div className="bg-gray-50 p-3 rounded-lg">
            <div className="text-sm text-gray-500 mb-1">Avg Network Time</div>
            <div className="text-xl font-semibold">
              {(data.avg_network_time_ms || 0).toFixed(0)} ms
            </div>
          </div>
        </div>
        
        <div className="bg-white rounded-lg border p-3">
          <h3 className="text-sm font-medium mb-2">Performance Trends</h3>
          <div className="h-40 relative">
            {/* Replace with your preferred chart library component */}
            <div className="flex justify-center items-center h-full">
              <div className="text-gray-500">Trend visualization would display here</div>
            </div>
          </div>
        </div>
      </div>
    );
  };

  // Render retry metrics chart
  const renderRetryChart = () => {
    if (!analytics?.retries) return <div className="text-gray-500 text-center py-8">No retry data available</div>;
    
    const data = analytics.retries;
    
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          <div className="bg-gray-50 p-3 rounded-lg">
            <div className="text-sm text-gray-500 mb-1">Total Retries</div>
            <div className="text-xl font-semibold">
              {data.total_retries || 0}
            </div>
          </div>
          <div className="bg-gray-50 p-3 rounded-lg">
            <div className="text-sm text-gray-500 mb-1">Avg Attempts</div>
            <div className="text-xl font-semibold">
              {(data.avg_attempts || 0).toFixed(1)}
            </div>
          </div>
          <div className="bg-gray-50 p-3 rounded-lg">
            <div className="text-sm text-gray-500 mb-1">Recovery Rate</div>
            <div className="text-xl font-semibold">
              {(data.recovery_rate || 0).toFixed(1)}%
            </div>
          </div>
        </div>
        
        <div className="bg-gray-50 rounded-lg p-4">
          <h3 className="text-sm font-medium mb-3">Retry Distribution</h3>
          <div className="h-64 relative">
            {/* Replace with your preferred chart library component */}
            <div className="flex justify-center items-center h-full">
              <div className="text-gray-500">Chart visualization would display here</div>
            </div>
          </div>
        </div>
      </div>
    );
  };

  // Render error metrics chart
  const renderErrorChart = () => {
    if (!analytics?.errors) return <div className="text-gray-500 text-center py-8">No error data available</div>;
    
    const data = analytics.errors;
    
    return (
      <div className="space-y-6">
        <div className="bg-gray-50 rounded-lg p-4">
          <h3 className="text-sm font-medium mb-3">Top Error Categories</h3>
          <div className="h-64 relative">
            {/* Replace with your preferred chart library component */}
            <div className="flex justify-center items-center h-full">
              <div className="text-gray-500">Chart visualization would display here</div>
            </div>
          </div>
        </div>
        
        <div className="bg-white rounded-lg border p-4">
          <h3 className="text-sm font-medium mb-2">Common Error Patterns</h3>
          {data.top_errors ? (
            <ul className="divide-y">
              {data.top_errors.map((error: any, index: number) => (
                <li key={index} className="py-2">
                  <div className="flex justify-between">
                    <span className="text-sm font-medium truncate max-w-xs">{error.message}</span>
                    <Badge variant="outline">{error.count}</Badge>
                  </div>
                  <p className="text-xs text-gray-500 mt-1">{error.category}</p>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-gray-500 py-2">No error data available</p>
          )}
        </div>
      </div>
    );
  };

  return (
    <Card className="shadow-md border-l-4 border-l-cyan-500">
      <CardHeader className="pb-2">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <CardTitle className="text-lg flex items-center space-x-2">
            <BarChart className="h-5 w-5 text-cyan-600" />
            <span>Transmission Analytics</span>
            <Badge variant="outline" className="ml-2 bg-cyan-50 text-cyan-800">APP</Badge>
          </CardTitle>
          
          <div className="flex items-center space-x-2">
            <div className="flex items-center space-x-2">
              <Calendar className="h-4 w-4 text-gray-500" />
              <Select value={timeRange} onValueChange={handleTimeRangeChange}>
                <SelectTrigger className="h-8 w-[130px]">
                  <SelectValue placeholder="Time Range" />
                </SelectTrigger>
                <SelectContent>
                  {timeRangeOptions.map(option => (
                    <SelectItem key={option.value} value={option.value}>
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            <div className="flex items-center space-x-2">
              <Clock className="h-4 w-4 text-gray-500" />
              <Select 
                value={timeInterval} 
                onValueChange={(value: string) => {
                  // Type-check to ensure value is a valid interval type
                  if (value === 'hour' || value === 'day' || value === 'week' || value === 'month') {
                    setTimeInterval(value);
                  }
                }}
              >
                <SelectTrigger className="h-8 w-[110px]">
                  <SelectValue placeholder="Interval" />
                </SelectTrigger>
                <SelectContent>
                  {intervalOptions.map(option => (
                    <SelectItem key={option.value} value={option.value}>
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            <Button 
              variant="ghost" 
              size="sm" 
              onClick={handleRefresh}
              disabled={loading}
            >
              {loading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <RefreshCw className="h-4 w-4" />
              )}
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {loading && !analytics ? (
          <div className="flex justify-center items-center py-8">
            <Loader2 className="h-8 w-8 text-cyan-600 animate-spin" />
          </div>
        ) : error ? (
          <div className="text-red-500 py-4 text-center">
            {error}
          </div>
        ) : analytics ? (
          <div>
            <Tabs value={activeTab} onValueChange={setActiveTab} className="mt-2">
              <TabsList className="mb-4">
                <TabsTrigger value="volume" className="flex items-center">
                  <BarChart className="h-4 w-4 mr-1" />
                  Volume
                </TabsTrigger>
                <TabsTrigger value="success">
                  <PieChart className="h-4 w-4 mr-1" />
                  Success Rate
                </TabsTrigger>
                <TabsTrigger value="performance">
                  <LineChart className="h-4 w-4 mr-1" />
                  Performance
                </TabsTrigger>
                <TabsTrigger value="retries">
                  <RefreshCw className="h-4 w-4 mr-1" />
                  Retries
                </TabsTrigger>
                <TabsTrigger value="errors">
                  <Loader2 className="h-4 w-4 mr-1" />
                  Errors
                </TabsTrigger>
              </TabsList>
              
              <TabsContent value="volume" className="mt-2">
                {renderVolumeChart()}
              </TabsContent>
              
              <TabsContent value="success" className="mt-2">
                {renderSuccessRateChart()}
              </TabsContent>
              
              <TabsContent value="performance" className="mt-2">
                {renderPerformanceChart()}
              </TabsContent>
              
              <TabsContent value="retries" className="mt-2">
                {renderRetryChart()}
              </TabsContent>
              
              <TabsContent value="errors" className="mt-2">
                {renderErrorChart()}
              </TabsContent>
            </Tabs>
            
            <div className="text-xs text-gray-500 mt-4 text-right">
              Data from {new Date(analytics.metadata.start_date).toLocaleDateString()} to {new Date(analytics.metadata.end_date).toLocaleDateString()}
            </div>
          </div>
        ) : (
          <div className="text-gray-500 py-4 text-center">
            No analytics data available
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default TransmissionAnalytics;
