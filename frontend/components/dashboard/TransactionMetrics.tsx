import React, { useState, useEffect } from 'react';
import { 
  Card, 
  CardHeader, 
  CardContent, 
  CardTitle, 
  CardDescription 
} from '../ui/Card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/Tabs';
import { Badge } from '../ui/Badge';
import { BarChart, LineChart } from '../ui/Charts';
import { Loader2, TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { fetchValidationMetrics, fetchB2BVsB2CMetrics } from '../../services/dashboardService';
import { createDataset } from '../ui/Charts';

export interface TransactionMetricsData {
  daily: {
    labels: string[];
    datasets: {
      label: string;
      data: number[];
    }[];
  };
  weekly: {
    labels: string[];
    datasets: {
      label: string;
      data: number[];
    }[];
  };
  monthly: {
    labels: string[];
    datasets: {
      label: string;
      data: number[];
    }[];
  };
  summary: {
    totalCount: number;
    successCount: number;
    failureCount: number;
    averagePerDay: number;
    trend: 'up' | 'down' | 'stable';
    changePercentage: number;
  };
}

interface TransactionMetricsProps {
  data?: TransactionMetricsData;
  isLoading?: boolean;
  useRealData?: boolean;
  timeRange?: string;
  organizationId?: string;
  refreshInterval?: number;
  summaryData?: {
    total_requests: number;
    error_rate: number;
    avg_response_time: number;
  };
}

const TransactionMetrics: React.FC<TransactionMetricsProps> = ({ 
  data: propData,
  isLoading: propIsLoading = false,
  useRealData = false,
  timeRange = '24h',
  organizationId,
  refreshInterval = 30000
}) => {
  // State for real-time data
  const [localData, setLocalData] = useState<TransactionMetricsData | undefined>(propData);
  const [loading, setLoading] = useState<boolean>(propIsLoading);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());
  
  // Generate transaction metrics from API data
  const generateMetricsFromApiData = async () => {
    try {
      // Fetch validation metrics and B2B vs B2C metrics
      const validationMetrics = await fetchValidationMetrics(timeRange, organizationId);
      const b2bVsB2cMetrics = await fetchB2BVsB2CMetrics(timeRange, organizationId);
      
      // Transform hourly validation data for charts
      const hourlyLabels = validationMetrics.hourly_validation
        .map(item => new Date(item.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}))
        .reverse();
      
      const hourlySuccess = validationMetrics.hourly_validation
        .map(item => item.success)
        .reverse();
      
      const hourlyFailure = validationMetrics.hourly_validation
        .map(item => item.failure)
        .reverse();
      
      // Transform B2B vs B2C daily data
      const dailyLabels = b2bVsB2cMetrics.daily_breakdown
        .slice(0, 7)
        .map(item => item.date)
        .reverse();
      
      const dailyB2B = b2bVsB2cMetrics.daily_breakdown
        .slice(0, 7)
        .map(item => item.b2b_count)
        .reverse();
      
      const dailyB2C = b2bVsB2cMetrics.daily_breakdown
        .slice(0, 7)
        .map(item => item.b2c_count)
        .reverse();
      
      // Calculate monthly totals (mock based on daily breakdown)
      const monthlyLabels = ['Week 1', 'Week 2', 'Week 3', 'Week 4'];
      const monthlyData = [0, 0, 0, 0];
      
      // Calculate trend
      const recentTotal = validationMetrics.hourly_validation
        .slice(0, 12)
        .reduce((sum, item) => sum + item.total, 0);
      
      const olderTotal = validationMetrics.hourly_validation
        .slice(12, 24)
        .reduce((sum, item) => sum + item.total, 0);
      
      const changePercentage = olderTotal > 0 
        ? ((recentTotal - olderTotal) / olderTotal) * 100 
        : 0;
      
      const trend = changePercentage > 2 
        ? 'up' 
        : changePercentage < -2 
          ? 'down' 
          : 'stable';
      
      // Calculate average per day
      const avgPerDay = validationMetrics.total_count / 
        (timeRange === '24h' ? 1 : timeRange === '7d' ? 7 : 30);
      
      // Create metrics data structure
      const newMetricsData: TransactionMetricsData = {
        daily: {
          labels: hourlyLabels,
          datasets: [
            createDataset('Success', hourlySuccess, 'success'),
            createDataset('Failed', hourlyFailure, 'danger'),
          ],
        },
        weekly: {
          labels: dailyLabels,
          datasets: [
            createDataset('B2B', dailyB2B, 'primary'),
            createDataset('B2C', dailyB2C, 'danger'),
          ],
        },
        monthly: {
          labels: monthlyLabels,
          datasets: [
            createDataset('Transactions', monthlyData, 'primary'),
          ],
        },
        summary: {
          totalCount: validationMetrics.total_count,
          successCount: validationMetrics.success_count,
          failureCount: validationMetrics.failure_count,
          averagePerDay: Math.round(avgPerDay),
          trend: trend,
          changePercentage: Math.abs(changePercentage)
        },
      };
      
      return newMetricsData;
    } catch (error) {
      console.error('Error generating metrics from API:', error);
      throw error;
    }
  };
  
  // Fetch real data from API
  const fetchRealTimeData = async () => {
    if (!useRealData) return;
    
    try {
      setLoading(true);
      setError(null);
      
      const metricsData = await generateMetricsFromApiData();
      setLocalData(metricsData);
      setLastUpdated(new Date());
    } catch (err) {
      console.error('Error fetching transaction metrics:', err);
      setError('Failed to load transaction metrics data');
    } finally {
      setLoading(false);
    }
  };
  
  useEffect(() => {
    // Initial fetch
    if (useRealData) {
      fetchRealTimeData();
    }
    
    // Set up polling for real-time updates
    let intervalId: NodeJS.Timeout | undefined;
    
    if (useRealData && refreshInterval > 0) {
      intervalId = setInterval(fetchRealTimeData, refreshInterval);
    }
    
    return () => {
      if (intervalId) clearInterval(intervalId);
    };
  }, [useRealData, timeRange, organizationId, refreshInterval]);
  
  // Use the prop values as fallback if real data isn't available
  const displayData = localData || propData;
  const isLoadingData = loading || propIsLoading;
  
  // Handle case where no data is available
  if (!displayData && !isLoadingData) {
    return (
      <Card>
        <CardHeader>
          <div className="flex justify-between items-start">
            <div>
              <CardTitle>Transaction Metrics</CardTitle>
              <CardDescription>
                Overview of transaction volume and success rates
                {useRealData && (
                  <div className="text-xs text-muted-foreground mt-1">
                    Last updated: {lastUpdated.toLocaleTimeString()}
                  </div>
                )}
              </CardDescription>
            </div>
            {useRealData && (
              <Badge variant="outline">
                {timeRange === '24h' ? 'Last 24h' : timeRange === '7d' ? 'Last 7 days' : 'Last 30 days'}
              </Badge>
            )}
          </div>
        </CardHeader>
        <CardContent>
          {isLoadingData ? (
            <div className="flex items-center justify-center h-64">
              <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
          ) : (
            <div className="text-center text-muted-foreground">No transaction data available</div>
          )}
        </CardContent>
      </Card>
    );
  }
  
  // Render trend icon
  const renderTrendIcon = () => {
    if (!displayData) return null;
    
    switch (displayData.summary.trend) {
      case 'up':
        return <TrendingUp className="text-success h-4 w-4" />;
      case 'down':
        return <TrendingDown className="text-destructive h-4 w-4" />;
      default:
        return <Minus className="text-muted-foreground h-4 w-4" />;
    }
  };
  const trendBadge = () => {
    if (!displayData) return null;
    
    const { trend, changePercentage } = displayData.summary;
    
    if (trend === 'up') {
      return (
        <Badge variant="success" className="ml-2">
          +{changePercentage}%
        </Badge>
      );
    } else if (trend === 'down') {
      return (
        <Badge variant="destructive" className="ml-2">
          -{changePercentage}%
        </Badge>
      );
    } 
    
    return (
      <Badge variant="outline" className="ml-2">
        {changePercentage}%
      </Badge>
    );
  };

  return (
    <Card className="shadow-sm">
      <CardHeader>
        <div className="flex justify-between items-start">
          <div>
            <CardTitle>Transaction Metrics</CardTitle>
            <CardDescription>
              Invoice transaction volume and trends
              {useRealData && (
                <div className="text-xs text-muted-foreground mt-1">
                  Last updated: {lastUpdated.toLocaleTimeString()}
                </div>
              )}
            </CardDescription>
          </div>
          {useRealData && (
            <Badge variant="outline">
              {timeRange === '24h' ? 'Last 24h' : timeRange === '7d' ? 'Last 7 days' : 'Last 30 days'}
            </Badge>
          )}
        </div>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="py-4 text-center">Loading transaction metrics...</div>
        ) : error ? (
          <div className="flex items-center justify-center h-64 flex-col">
            <div className="text-destructive mb-2">{error}</div>
          </div>
        ) : displayData && (
          <>
            {/* Summary stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
              <div className="bg-background rounded-lg p-3 border">
                <div className="text-sm text-muted-foreground">Total</div>
                <div className="text-2xl font-semibold">{displayData.summary.totalCount.toLocaleString()}</div>
              </div>
              <div className="bg-background rounded-lg p-3 border">
                <div className="text-sm text-muted-foreground">Success</div>
                <div className="text-2xl font-semibold text-green-500">
                  {((displayData.summary.successCount / displayData.summary.totalCount) * 100).toFixed(1)}%
                </div>
              </div>
              <div className="bg-background rounded-lg p-3 border">
                <div className="text-sm text-muted-foreground">Daily Avg</div>
                <div className="text-2xl font-semibold">{displayData.summary.averagePerDay}</div>
              </div>
              <div className="bg-background rounded-lg p-3 border">
                <div className="text-sm text-muted-foreground">Trend</div>
                <div className="text-2xl font-semibold flex items-center gap-1">
                  {renderTrendIcon()}
                  {displayData.summary.trend === 'up' ? (
                    <span className="text-green-500">+{displayData.summary.changePercentage.toFixed(1)}%</span>
                  ) : displayData.summary.trend === 'down' ? (
                    <span className="text-red-500">-{displayData.summary.changePercentage.toFixed(1)}%</span>
                  ) : (
                    <span>Stable</span>
                  )}
                </div>
              </div>
            </div>

            <Tabs defaultValue="daily" className="w-full">
              <TabsList>
                <TabsTrigger value="daily">Daily</TabsTrigger>
                <TabsTrigger value="weekly">Weekly</TabsTrigger>
                <TabsTrigger value="monthly">Monthly</TabsTrigger>
              </TabsList>
              
              <div className="h-64 mt-4">
                <TabsContent value="daily" className="h-full">
                  <BarChart 
                    data={displayData.daily || { labels: [], datasets: [] }}
                    options={{
                      responsive: true,
                      maintainAspectRatio: false,
                      scales: {
                        y: {
                          beginAtZero: true,
                        }
                      }
                    }}
                  />
                </TabsContent>
                
                <TabsContent value="weekly" className="h-full">
                  <BarChart 
                    data={localData?.weekly || { labels: [], datasets: [] }}
                    options={{
                      responsive: true,
                      maintainAspectRatio: false,
                      scales: {
                        y: {
                          beginAtZero: true,
                        }
                      }
                    }}
                  />
                </TabsContent>
                
                <TabsContent value="monthly" className="h-full">
                  <LineChart 
                    data={localData?.monthly || { labels: [], datasets: [] }}
                    options={{
                      responsive: true,
                      maintainAspectRatio: false,
                      scales: {
                        y: {
                          beginAtZero: true,
                        }
                      }
                    }}
                  />
                </TabsContent>
              </div>
            </Tabs>
          </>
        )}
      </CardContent>
    </Card>
  );
};

export default TransactionMetrics;
