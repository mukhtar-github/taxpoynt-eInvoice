import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../ui/Card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/Tabs';
import { BarChart, Bar, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { B2BvsB2CMetrics, fetchB2BVsB2CMetrics } from '../../services/dashboardService';
import { Loader2 } from 'lucide-react';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/Select';

interface B2BvsB2CMetricsCardProps {
  timeRange?: string;
  organizationId?: string;
  isLoading?: boolean;
  useRealData?: boolean;
  summaryData?: {
    b2b_percentage: number;
    b2c_percentage: number;
    b2b_success_rate: number;
    b2c_success_rate: number;
    b2b_count: number;
    b2c_count: number;
    daily_breakdown?: any[];
  };
}

const B2BvsB2CMetricsCard: React.FC<B2BvsB2CMetricsCardProps> = ({ 
  timeRange = '24h',
  organizationId,
  isLoading,
  useRealData = false,
  summaryData
}) => {
  const [loading, setLoading] = useState<boolean>(true);
  const [metrics, setMetrics] = useState<B2BvsB2CMetrics | null>(null);
  const [selectedTimeRange, setSelectedTimeRange] = useState<string>(timeRange);

  const fetchMetrics = async () => {
    setLoading(true);
    try {
      const data = await fetchB2BVsB2CMetrics(selectedTimeRange, organizationId);
      setMetrics(data);
    } catch (error) {
      console.error('Error fetching B2B vs B2C metrics:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Only fetch data when using real data (API calls)
    if (useRealData) {
      fetchMetrics();
      // Set up polling for real-time updates
      const intervalId = setInterval(fetchMetrics, 30000); // Update every 30 seconds
      return () => clearInterval(intervalId);
    }
  }, [selectedTimeRange, organizationId, useRealData]);

  const handleTimeRangeChange = (value: string) => {
    setSelectedTimeRange(value);
  };

  // Helper function to get data from summaryData prop or metrics state
  const getDataSource = () => {
    if (summaryData) {
      return summaryData;
    }
    return metrics;
  };
  
  // Transform data for charts
  const transformBreakdownData = () => {
    const dataSource = getDataSource();
    if (!dataSource) return [];

    const b2bPercentage = dataSource.b2b_percentage;
    const b2cPercentage = dataSource.b2c_percentage;

    return [
      { name: 'B2B', value: b2bPercentage },
      { name: 'B2C', value: b2cPercentage }
    ];
  };
  
  const transformSuccessRateData = () => {
    const dataSource = getDataSource();
    if (!dataSource) return [];

    return [
      { name: 'B2B', value: dataSource.b2b_success_rate },
      { name: 'B2C', value: dataSource.b2c_success_rate }
    ];
  };

  const transformDailyData = () => {
    const dataSource = getDataSource();
    if (!dataSource) return [];
    
    // Return most recent 7 days
    return (dataSource.daily_breakdown || [])
      .slice(0, 7)
      .map(day => ({
        date: day.date,
        B2B: day.b2b_count,
        B2C: day.b2c_count
      }))
      .reverse();
  };
  
  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex justify-between items-center">
          <div>
            <CardTitle className="text-lg font-semibold">B2B vs B2C Metrics</CardTitle>
            <CardDescription>Comparison of business and consumer invoices</CardDescription>
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
        {/* Use external isLoading prop if provided, otherwise use internal loading state */}
        {(isLoading !== undefined ? isLoading : loading) ? (
          <div className="flex items-center justify-center h-64">
            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          </div>
        ) : (
          <Tabs defaultValue="breakdown">
            <TabsList className="mb-4">
              <TabsTrigger value="breakdown">Distribution</TabsTrigger>
              <TabsTrigger value="success">Success Rate</TabsTrigger>
              <TabsTrigger value="daily">Daily Trend</TabsTrigger>
            </TabsList>
            
            <TabsContent value="breakdown">
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={transformBreakdownData()}>
                    <XAxis dataKey="name" />
                    <YAxis domain={[0, 100]} tickFormatter={(value) => `${value}%`} />
                    <Tooltip formatter={(value) => [`${value}%`, 'Percentage']} />
                    <Bar dataKey="value" fill="#3b82f6" name="Percentage" />
                  </BarChart>
                </ResponsiveContainer>
                
                <div className="grid grid-cols-2 gap-4 mt-4">
                  <div className="bg-gray-50 dark:bg-gray-800 p-3 rounded-md text-center">
                    <div className="text-sm text-muted-foreground">B2B Invoices</div>
                    <div className="text-2xl font-semibold">{getDataSource()?.b2b_count || 0}</div>
                    <div className="text-sm text-muted-foreground">
                      {getDataSource()?.b2b_percentage?.toFixed(1) || 0}%
                    </div>
                  </div>
                  <div className="bg-gray-50 dark:bg-gray-800 p-3 rounded-md text-center">
                    <div className="text-sm text-muted-foreground">B2C Invoices</div>
                    <div className="text-2xl font-semibold">{getDataSource()?.b2c_count || 0}</div>
                    <div className="text-sm text-muted-foreground">
                      {getDataSource()?.b2c_percentage?.toFixed(1) || 0}%
                    </div>
                  </div>
                </div>
              </div>
            </TabsContent>
            
            <TabsContent value="success">
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={transformSuccessRateData()}>
                    <XAxis dataKey="name" />
                    <YAxis domain={[0, 100]} tickFormatter={(value) => `${value}%`} />
                    <Tooltip formatter={(value) => [`${value}%`, 'Success Rate']} />
                    <Bar dataKey="value" fill="#22c55e" name="Success Rate" />
                  </BarChart>
                </ResponsiveContainer>
                
                <div className="grid grid-cols-2 gap-4 mt-4">
                  <div className="bg-gray-50 dark:bg-gray-800 p-3 rounded-md text-center">
                    <div className="text-sm text-muted-foreground">B2B Success Rate</div>
                    <div className="text-2xl font-semibold">
                      {getDataSource()?.b2b_success_rate?.toFixed(1) || 0}%
                    </div>
                  </div>
                  <div className="bg-gray-50 dark:bg-gray-800 p-3 rounded-md text-center">
                    <div className="text-sm text-muted-foreground">B2C Success Rate</div>
                    <div className="text-2xl font-semibold">
                      {getDataSource()?.b2c_success_rate?.toFixed(1) || 0}%
                    </div>
                  </div>
                </div>
              </div>
            </TabsContent>
            
            <TabsContent value="daily">
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={transformDailyData()}>
                    <XAxis dataKey="date" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="B2B" fill="#3b82f6" name="B2B Invoices" />
                    <Bar dataKey="B2C" fill="#10b981" name="B2C Invoices" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </TabsContent>
          </Tabs>
        )}
      </CardContent>
    </Card>
  );
};

export default B2BvsB2CMetricsCard;
