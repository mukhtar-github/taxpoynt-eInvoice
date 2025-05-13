import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../ui/Card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/Tabs';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell } from 'recharts';
import { IRNMetrics, fetchIRNMetrics } from '../../services/dashboardService';
import { Loader2, AlertCircle } from 'lucide-react';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/Select';
import { Badge } from '../ui/Badge';

interface EnhancedIRNMetricsCardProps {
  timeRange?: string;
  organizationId?: string;
  refreshInterval?: number; // in milliseconds
  isLoading?: boolean;
  useRealData?: boolean;
  summaryData?: {
    total_irns: number;
    active_irns: number;
    unused_irns: number;
    expired_irns: number;
  };
}

const EnhancedIRNMetricsCard: React.FC<EnhancedIRNMetricsCardProps> = ({ 
  timeRange = '24h',
  organizationId,
  refreshInterval = 10000, // Default to 10s for real-time updates
  isLoading,
  useRealData = true,
  summaryData
}) => {
  const [loading, setLoading] = useState<boolean>(isLoading !== undefined ? isLoading : true);
  const [error, setError] = useState<string | null>(null);
  const [metrics, setMetrics] = useState<IRNMetrics | null>(null);
  const [selectedTimeRange, setSelectedTimeRange] = useState<string>(timeRange);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());

  const loadIRNMetrics = async (selectedTimeRange: string, organizationId: string | undefined) => {
    try {
      setError(null);
      const data = await fetchIRNMetrics(selectedTimeRange, organizationId);
      setMetrics(data);
      setLastUpdated(new Date());
    } catch (error) {
      console.error('Error fetching IRN metrics:', error);
      setError('Failed to load IRN metrics data. Please try again later.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Only fetch metrics if using real data and no summary data is provided
    if (useRealData && !summaryData) {
      loadIRNMetrics(selectedTimeRange, organizationId);
      
      // Set up polling for real-time updates
      const intervalId = setInterval(() => loadIRNMetrics(selectedTimeRange, organizationId), refreshInterval);
      
      return () => clearInterval(intervalId);
    } else if (!useRealData && summaryData) {
      // Use provided summary data instead of fetching
      setLoading(false);
    }
  }, [selectedTimeRange, organizationId, refreshInterval, useRealData, summaryData]);

  const handleTimeRangeChange = (value: string) => {
    setSelectedTimeRange(value);
    setLoading(true);
    if (useRealData && !summaryData) {
      loadIRNMetrics(value, organizationId);
    }
  };
  
  // Transform data for charts
  const transformHourlyData = () => {
    if (!metrics) return [];
    
    return metrics.hourly_generation.map(item => ({
      time: new Date(item.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}),
      count: item.count
    })).reverse();
  };
  
  const transformDailyData = () => {
    if (!metrics) return [];
    
    return metrics.daily_generation.map(item => ({
      date: item.date,
      count: item.count
    })).reverse().slice(0, 14); // Last 2 weeks
  };
  
  const transformStatusData = () => {
    // Use summaryData when useRealData is false and summaryData is provided
    if (!useRealData && summaryData) {
      return [
        { name: 'Unused', value: summaryData.unused_irns },
        { name: 'Active', value: summaryData.active_irns },
        { name: 'Expired', value: summaryData.expired_irns },
        { name: 'Total', value: summaryData.total_irns }
      ];
    }
    
    // Use fetched metrics as the default source
    if (!metrics) return [];
    
    return [
      { name: 'Unused', value: metrics.status_counts.unused },
      { name: 'Active', value: metrics.status_counts.active },
      { name: 'Used', value: metrics.status_counts.used },
      { name: 'Expired', value: metrics.status_counts.expired },
      { name: 'Cancelled', value: metrics.status_counts.cancelled }
    ];
  };
  
  const getStatusColor = (status: string) => {
    const colors = {
      'Unused': '#3b82f6', // blue
      'Active': '#22c55e', // green
      'Used': '#6366f1',  // indigo
      'Expired': '#f59e0b', // amber
      'Cancelled': '#f43f5e' // rose
    };
    return colors[status] || '#94a3b8'; // default to slate
  };
  
  // Calculate real-time generation rate (per hour)
  const calculateGenerationRate = () => {
    if (!metrics || !metrics.hourly_generation.length) return 0;
    
    // Use the most recent hour's data
    const recentHour = metrics.hourly_generation[0];
    return recentHour.count;
  };
  
  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex justify-between items-center">
          <div>
            <CardTitle className="text-lg font-semibold">IRN Generation Metrics</CardTitle>
            <CardDescription>
              Real-time metrics for Invoice Reference Numbers
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
        {loading ? (
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
            {/* Top stats - summary metrics */}
            <div className="grid grid-cols-4 gap-4 mb-6">
              <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow-sm">
                <div className="text-sm text-muted-foreground">Total IRNs</div>
                <div className="text-2xl font-semibold">{metrics?.total_count.toLocaleString() || 0}</div>
              </div>
              <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow-sm">
                <div className="text-sm text-muted-foreground">Active IRNs</div>
                <div className="text-2xl font-semibold text-green-600">
                  {metrics?.status_counts.active.toLocaleString() || 0}
                </div>
              </div>
              <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow-sm">
                <div className="text-sm text-muted-foreground">Generation Rate</div>
                <div className="text-2xl font-semibold">
                  {calculateGenerationRate()}<span className="text-sm text-muted-foreground">/hr</span>
                </div>
              </div>
              <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow-sm">
                <div className="text-sm text-muted-foreground">Unused IRNs</div>
                <div className="text-2xl font-semibold text-blue-600">
                  {metrics?.status_counts.unused.toLocaleString() || 0}
                </div>
              </div>
            </div>
            
            <Tabs defaultValue="hourly">
              <TabsList className="mb-4">
                <TabsTrigger value="hourly">Hourly Trend</TabsTrigger>
                <TabsTrigger value="daily">Daily Trend</TabsTrigger>
                <TabsTrigger value="status">Status Breakdown</TabsTrigger>
              </TabsList>
              
              <TabsContent value="hourly">
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={transformHourlyData()}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="time" />
                      <YAxis />
                      <Tooltip />
                      <Legend />
                      <Line 
                        type="monotone" 
                        dataKey="count" 
                        stroke="#3b82f6" 
                        strokeWidth={2}
                        name="IRN Generated"
                        dot={{ r: 3 }}
                        activeDot={{ r: 5 }}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </TabsContent>
              
              <TabsContent value="daily">
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={transformDailyData()}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="date" />
                      <YAxis />
                      <Tooltip />
                      <Legend />
                      <Bar dataKey="count" fill="#3b82f6" name="IRN Generated" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </TabsContent>
              
              <TabsContent value="status">
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={transformStatusData()}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="name" />
                      <YAxis />
                      <Tooltip />
                      <Legend />
                      <Bar dataKey="value" name="Count" fill="#3b82f6">
                        {transformStatusData().map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={getStatusColor(entry.name)} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </TabsContent>
            </Tabs>
          </>
        )}
      </CardContent>
    </Card>
  );
};

export default EnhancedIRNMetricsCard;
