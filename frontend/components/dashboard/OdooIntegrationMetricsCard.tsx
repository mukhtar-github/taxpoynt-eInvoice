import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../ui/Card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/Tabs';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { OdooIntegrationMetrics, IntegrationStatus, fetchOdooIntegrationMetrics } from '../../services/dashboardService';
import { Loader2, AlertCircle, CheckCircle2, XCircle, FileMinus } from 'lucide-react';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/Select';
import { Badge } from '../ui/Badge';
import { formatDistanceToNow } from 'date-fns';

interface OdooIntegrationMetricsCardProps {
  timeRange?: string;
  organizationId?: string;
  refreshInterval?: number; // in milliseconds
  isLoading?: boolean;
  useRealData?: boolean;
  summaryData?: {
    active_integrations: number;
    total_invoices: number;
    success_rate: number;
  };
}

const OdooIntegrationMetricsCard: React.FC<OdooIntegrationMetricsCardProps> = ({ 
  timeRange = '24h',
  organizationId,
  refreshInterval = 30000 // Default to 30s for real-time updates
}) => {
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [metrics, setMetrics] = useState<OdooIntegrationMetrics | null>(null);
  const [selectedTimeRange, setSelectedTimeRange] = useState<string>(timeRange);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());

  const fetchMetrics = async () => {
    try {
      setError(null);
      const data = await fetchOdooIntegrationMetrics(selectedTimeRange, organizationId);
      setMetrics(data);
      setLastUpdated(new Date());
    } catch (error) {
      console.error('Error fetching Odoo integration metrics:', error);
      setError('Failed to load Odoo integration metrics data. Please try again later.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMetrics();
    
    // Set up polling for real-time updates
    const intervalId = setInterval(fetchMetrics, refreshInterval);
    
    return () => clearInterval(intervalId);
  }, [selectedTimeRange, organizationId, refreshInterval]);

  const handleTimeRangeChange = (value: string) => {
    setSelectedTimeRange(value);
    setLoading(true);
  };
  
  // Transform data for charts
  const transformHourlyData = () => {
    if (!metrics) return [];
    
    return metrics.hourly_counts
      .map(item => ({
        time: new Date(item.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}),
        count: item.count
      }))
      .reverse();
  };
  
  // Format last validated time as relative time
  const formatLastValidated = (timestamp: string | null) => {
    if (!timestamp) return 'Never';
    
    try {
      return formatDistanceToNow(new Date(timestamp), { addSuffix: true });
    } catch (error) {
      return 'Unknown';
    }
  };
  
  // Status badge for integration
  const getStatusBadge = (isActive: boolean) => {
    if (isActive) {
      return <Badge variant="success">Active</Badge>;
    }
    return <Badge variant="destructive">Inactive</Badge>;
  };
  
  // Status icon for integration
  const getStatusIcon = (status: IntegrationStatus) => {
    if (status.is_active) {
      if (status.last_validation_success === true) {
        return <CheckCircle2 className="h-5 w-5 text-green-500" />;
      } else if (status.last_validation_success === false) {
        return <FileMinus className="h-5 w-5 text-amber-500" />;
      }
      return <CheckCircle2 className="h-5 w-5 text-green-500" />;
    }
    return <XCircle className="h-5 w-5 text-red-500" />;
  };
  
  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex justify-between items-center">
          <div>
            <CardTitle className="text-lg font-semibold">Odoo Integration Status</CardTitle>
            <CardDescription>
              Real-time monitoring of Odoo integration performance
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
            {/* Top stats - integration summary */}
            <div className="grid grid-cols-4 gap-4 mb-6">
              <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow-sm">
                <div className="text-sm text-muted-foreground">Total Integrations</div>
                <div className="text-2xl font-semibold">{metrics?.total_integrations || 0}</div>
              </div>
              <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow-sm">
                <div className="text-sm text-muted-foreground">Active</div>
                <div className="text-2xl font-semibold text-green-600">
                  {metrics?.active_integrations || 0}
                </div>
              </div>
              <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow-sm">
                <div className="text-sm text-muted-foreground">Invoices Processed</div>
                <div className="text-2xl font-semibold">
                  {metrics?.total_invoices.toLocaleString() || 0}
                </div>
              </div>
              <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow-sm">
                <div className="text-sm text-muted-foreground">Success Rate</div>
                <div className="text-2xl font-semibold">
                  {metrics?.success_rate.toFixed(1) || 0}%
                </div>
              </div>
            </div>
            
            <Tabs defaultValue="overview">
              <TabsList className="mb-4">
                <TabsTrigger value="overview">Activity Trend</TabsTrigger>
                <TabsTrigger value="status">Integration Status</TabsTrigger>
              </TabsList>
              
              <TabsContent value="overview">
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
                        name="Invoices Processed"
                        dot={{ r: 3 }}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </TabsContent>
              
              <TabsContent value="status">
                <div className="space-y-4">
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm text-left">
                      <thead className="text-xs text-gray-700 uppercase bg-gray-50 dark:bg-gray-800 dark:text-gray-400">
                        <tr>
                          <th scope="col" className="py-3 px-4">Status</th>
                          <th scope="col" className="py-3 px-4">Name</th>
                          <th scope="col" className="py-3 px-4">Organization</th>
                          <th scope="col" className="py-3 px-4">Last Validated</th>
                          <th scope="col" className="py-3 px-4">Last Result</th>
                        </tr>
                      </thead>
                      <tbody>
                        {metrics?.integration_statuses.map((integration, index) => (
                          <tr key={index} className="bg-white border-b dark:bg-gray-900 dark:border-gray-700">
                            <td className="py-3 px-4">
                              {getStatusIcon(integration)}
                            </td>
                            <td className="py-3 px-4 font-medium">
                              {integration.name}
                            </td>
                            <td className="py-3 px-4">
                              {integration.organization_id.substring(0, 8)}...
                            </td>
                            <td className="py-3 px-4">
                              {formatLastValidated(integration.last_validated)}
                            </td>
                            <td className="py-3 px-4">
                              {integration.last_validation_success === null ? (
                                <Badge variant="outline">Unknown</Badge>
                              ) : integration.last_validation_success ? (
                                <Badge variant="success">Success</Badge>
                              ) : (
                                <Badge variant="destructive">Failed</Badge>
                              )}
                            </td>
                          </tr>
                        ))}
                        
                        {(!metrics?.integration_statuses || metrics?.integration_statuses.length === 0) && (
                          <tr className="bg-white border-b dark:bg-gray-900 dark:border-gray-700">
                            <td colSpan={5} className="py-3 px-4 text-center text-muted-foreground">
                              No integration data available
                            </td>
                          </tr>
                        )}
                      </tbody>
                    </table>
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

export default OdooIntegrationMetricsCard;
