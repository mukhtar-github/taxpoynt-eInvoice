import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../ui/Card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/Tabs';
import { LineChart, Line, BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { ValidationMetrics, CommonError, fetchValidationMetrics } from '../../services/dashboardService';
import { Loader2, AlertCircle } from 'lucide-react';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/Select';
import { Badge } from '../ui/Badge';
import { Progress } from '../ui/Progress';

interface ValidationMetricsCardProps {
  timeRange?: string;
  organizationId?: string;
  refreshInterval?: number; // in milliseconds
  isLoading?: boolean;
  useRealData?: boolean;
  summaryData?: {
    total_validations: number;
    success_rate: number;
    common_errors: CommonError[];
  };
}

const COLORS = ['#ef4444', '#f97316', '#f59e0b', '#eab308', '#84cc16', '#22c55e'];

const ValidationMetricsCard: React.FC<ValidationMetricsCardProps> = ({ 
  timeRange = '24h',
  organizationId,
  refreshInterval = 30000, // Default to 30s for real-time updates
  isLoading: externalLoading,
  useRealData = true,
  summaryData
}) => {
  const [loading, setLoading] = useState<boolean>(externalLoading !== undefined ? externalLoading : true);
  const [error, setError] = useState<string | null>(null);
  const [metrics, setMetrics] = useState<ValidationMetrics | null>(null);
  const [selectedTimeRange, setSelectedTimeRange] = useState<string>(timeRange);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());

  const fetchMetrics = async () => {
    try {
      setError(null);
      const data = await fetchValidationMetrics(selectedTimeRange, organizationId);
      setMetrics(data);
      setLastUpdated(new Date());
    } catch (error) {
      console.error('Error fetching validation metrics:', error);
      setError('Failed to load validation metrics data. Please try again later.');
    } finally {
      setLoading(false);
    }
  };

  // Handle external loading state changes
  useEffect(() => {
    if (externalLoading !== undefined) {
      setLoading(externalLoading);
    }
  }, [externalLoading]);

  // Handle summary data passed from parent
  useEffect(() => {
    if (summaryData) {
      const transformedData: ValidationMetrics = {
        total_count: summaryData.total_validations,
        success_count: Math.round(summaryData.total_validations * (summaryData.success_rate / 100)),
        failure_count: Math.round(summaryData.total_validations * ((100 - summaryData.success_rate) / 100)),
        success_rate: summaryData.success_rate,
        common_errors: summaryData.common_errors,
        hourly_validation: [] // We might not have this data in the summary
        ,
        time_range: ''
      };
      setMetrics(transformedData);
      setLastUpdated(new Date());
    }
  }, [summaryData]);

  // Only fetch data if we're using real data and no summary data is provided
  useEffect(() => {
    if (useRealData && !summaryData) {
      fetchMetrics();
      
      // Set up polling for real-time updates
      const intervalId = setInterval(fetchMetrics, refreshInterval);
      
      return () => clearInterval(intervalId);
    }
  }, [selectedTimeRange, organizationId, refreshInterval, useRealData, summaryData]);

  const handleTimeRangeChange = (value: string) => {
    setSelectedTimeRange(value);
    if (externalLoading === undefined) {
      setLoading(true);
    }
  };
  
  // Transform data for charts
  const transformHourlyData = () => {
    if (!metrics) return [];
    
    return metrics.hourly_validation
      .map(item => ({
        time: new Date(item.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}),
        success: item.success,
        failure: item.failure,
        rate: item.success_rate
      }))
      .reverse();
  };
  
  const transformErrorData = () => {
    if (!metrics || !metrics.common_errors.length) return [];
    
    return metrics.common_errors.map(error => ({
      name: error.error_code,
      value: error.count,
      percentage: error.percentage
    }));
  };
  
  const getSuccessRateColor = (rate: number) => {
    if (rate >= 95) return 'bg-green-500';
    if (rate >= 85) return 'bg-yellow-500';
    return 'bg-red-500';
  };
  
  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex justify-between items-center">
          <div>
            <CardTitle className="text-lg font-semibold">Validation Metrics</CardTitle>
            <CardDescription>
              Error rates and validation performance
              <div className="mt-1">
                <Badge variant="outline" className="text-xs">
                  Last updated: {lastUpdated.toLocaleTimeString()}
                </Badge>
              </div>
            </CardDescription>
          </div>
          <Select value={selectedTimeRange} onValueChange={handleTimeRangeChange}>
            <SelectTrigger className="w-[100px]">
              <SelectValue placeholder="Time range" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="24h">24 Hours</SelectItem>
              <SelectItem value="7d">7 Days</SelectItem>
              <SelectItem value="30d">30 Days</SelectItem>
              <SelectItem value="all">All Time</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </CardHeader>
      <CardContent>
        {loading || externalLoading ? (
          <div className="flex items-center justify-center h-64">
            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          </div>
        ) : error ? (
          <div className="flex items-center justify-center h-64 flex-col">
            <AlertCircle className="h-8 w-8 text-destructive mb-2" />
            <p className="text-destructive">{error}</p>
          </div>
        ) : (
          <>
            {/* Top stats - validation rates */}
            <div className="space-y-4 mb-6">
              <div className="flex justify-between mb-1">
                <div className="flex flex-col">
                  <span className="text-sm text-muted-foreground">Success Rate</span>
                  <span className="text-2xl font-semibold">{metrics?.success_rate.toFixed(1) || 0}%</span>
                </div>
                <div className="flex flex-col text-right">
                  <span className="text-sm text-muted-foreground">Total Validations</span>
                  <span className="text-2xl font-semibold">{metrics?.total_count.toLocaleString() || 0}</span>
                </div>
              </div>
              
              <Progress 
                value={metrics?.success_rate || 0} 
                max={100} 
                className={`h-2 ${getSuccessRateColor(metrics?.success_rate || 0)}`}
              />
              
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-emerald-50 dark:bg-emerald-900/20 p-3 rounded-md">
                  <div className="text-sm text-muted-foreground">Successful</div>
                  <div className="text-xl font-semibold text-emerald-600 dark:text-emerald-400">
                    {metrics?.success_count.toLocaleString() || 0}
                  </div>
                </div>
                <div className="bg-red-50 dark:bg-red-900/20 p-3 rounded-md">
                  <div className="text-sm text-muted-foreground">Failed</div>
                  <div className="text-xl font-semibold text-red-600 dark:text-red-400">
                    {metrics?.failure_count.toLocaleString() || 0}
                  </div>
                </div>
              </div>
            </div>
            
            <Tabs defaultValue="trends">
              <TabsList className="mb-4">
                <TabsTrigger value="trends">Success Rate Trends</TabsTrigger>
                <TabsTrigger value="errors">Common Errors</TabsTrigger>
              </TabsList>
              
              <TabsContent value="trends">
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={transformHourlyData()}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="time" />
                      <YAxis yAxisId="left" />
                      <YAxis yAxisId="right" orientation="right" tickFormatter={(value) => `${value}%`} domain={[0, 100]} />
                      <Tooltip />
                      <Legend />
                      <Line 
                        yAxisId="left"
                        type="monotone" 
                        dataKey="success" 
                        stroke="#22c55e" 
                        strokeWidth={2}
                        name="Successful"
                        dot={{ r: 2 }}
                      />
                      <Line 
                        yAxisId="left"
                        type="monotone" 
                        dataKey="failure" 
                        stroke="#ef4444" 
                        strokeWidth={2}
                        name="Failed"
                        dot={{ r: 2 }}
                      />
                      <Line 
                        yAxisId="right"
                        type="monotone" 
                        dataKey="rate" 
                        stroke="#3b82f6" 
                        strokeWidth={2}
                        name="Success Rate (%)"
                        dot={{ r: 2 }}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </TabsContent>
              
              <TabsContent value="errors">
                <div className="grid md:grid-cols-2 gap-6">
                  <div className="h-64">
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={transformErrorData()}
                          cx="50%"
                          cy="50%"
                          labelLine={false}
                          label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                          outerRadius={80}
                          fill="#8884d8"
                          dataKey="value"
                        >
                          {transformErrorData().map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                          ))}
                        </Pie>
                        <Tooltip formatter={(value, name, props) => [`${value} occurrences`, name]} />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                  
                  <div className="space-y-3 max-h-64 overflow-auto">
                    <h3 className="font-medium">Top Validation Errors</h3>
                    {metrics?.common_errors.map((err, index) => (
                      <div key={index} className="bg-gray-50 dark:bg-gray-800 p-3 rounded-md">
                        <div className="flex justify-between">
                          <span className="font-medium truncate max-w-[70%]" title={err.error_code}>
                            {err.error_code}
                          </span>
                          <Badge variant="outline">{err.percentage.toFixed(1)}%</Badge>
                        </div>
                        <div className="text-sm text-muted-foreground mt-1">
                          {err.count} occurrences
                        </div>
                        <Progress 
                          value={err.percentage} 
                          max={100} 
                          className="h-1 mt-2"
                        />
                      </div>
                    ))}
                  </div>
                </div>
              </TabsContent>
            </Tabs>
          </>
        )}
      </CardContent>
    </Card>
  );
};

export default ValidationMetricsCard;
