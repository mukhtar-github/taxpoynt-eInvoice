import React, { useState, useEffect } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../ui/Tabs';
import { Card, CardContent, CardHeader, CardTitle } from '../../ui/Card';
import { Button } from '../../ui/Button';
import { Input } from '../../ui/Input';
import { Badge } from '../../ui/Badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../ui/Select';
import { 
  Activity, 
  BarChart3, 
  Clock, 
  AlertTriangle, 
  CheckCircle, 
  XCircle, 
  RefreshCw, 
  Search, 
  Calendar,
  Download,
  Filter,
  HelpCircle,
  Loader2,
  Bell
} from 'lucide-react';
import { useToast } from '../../ui/Toast';
import { useAuth } from '../../../context/AuthContext';
import TransmissionHealthStatus from './TransmissionHealthStatus';
import ContextualHelp from '../common/ContextualHelp';
import transmissionApiService from '../../../services/transmissionApiService';

interface TransmissionMonitoringDashboardProps {
  organizationId: string;
  refreshInterval?: number;
}

interface TransmissionMetric {
  id: string;
  name: string;
  value: number;
  change: number;
  status: 'positive' | 'negative' | 'neutral';
  icon: React.ReactNode;
}

interface TransmissionData {
  id: string;
  invoiceRef: string;
  customerName: string;
  amount: number;
  transmissionDate: string;
  status: 'success' | 'failed' | 'pending' | 'processing';
  retryCount: number;
  errorMessage?: string;
}

const TransmissionMonitoringDashboard: React.FC<TransmissionMonitoringDashboardProps> = ({ 
  organizationId,
  refreshInterval = 30000 
}) => {
  // State for various dashboard data
  const [metrics, setMetrics] = useState<TransmissionMetric[]>([]);
  const [transmissions, setTransmissions] = useState<TransmissionData[]>([]);
  const [filteredTransmissions, setFilteredTransmissions] = useState<TransmissionData[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [dateRange, setDateRange] = useState<string>('today');
  const [isAutoRefresh, setIsAutoRefresh] = useState<boolean>(true);
  const [refreshTimer, setRefreshTimer] = useState<NodeJS.Timeout | null>(null);
  
  const toast = useToast();
  const { user } = useAuth();
  
  // Check if user has admin permissions
  const isAdmin = user?.role === 'admin' || user?.role === 'org_admin';
  
  // Helper function to map API status to UI status
  const mapTransmissionStatus = (status: string): 'success' | 'failed' | 'pending' | 'processing' => {
    switch (status?.toLowerCase()) {
      case 'completed':
        return 'success';
      case 'failed':
        return 'failed';
      case 'pending':
        return 'pending';
      case 'in_progress':
      case 'retrying':
        return 'processing';
      default:
        return 'pending';
    }
  };

  // Help content for contextual help
  const monitoringHelp = {
    overview: "The Transmission Monitoring Dashboard provides real-time visibility into your e-invoice transmissions to FIRS.",
    metrics: "Key metrics show transmission performance and health over the selected time period.",
    filtering: "Use filters to narrow down transmissions by status, date range, or keyword search.",
    alerts: "System alerts notify you of potential issues that may affect transmission reliability."
  };
  
  useEffect(() => {
    fetchDashboardData();
    
    // Set up auto-refresh if enabled
    if (isAutoRefresh) {
      const timer = setInterval(() => {
        fetchDashboardData();
      }, refreshInterval);
      
      setRefreshTimer(timer);
    }
    
    return () => {
      if (refreshTimer) {
        clearInterval(refreshTimer);
      }
    };
  }, [organizationId, isAutoRefresh, refreshInterval, dateRange, filterStatus]);
  
  useEffect(() => {
    // Apply filters when search query or filter status changes
    applyFilters();
  }, [searchQuery, transmissions]);
  
  const fetchDashboardData = async () => {
    setLoading(true);
    
    try {
      // Fetch transmission statistics
      // Convert the dateRange string to appropriate Date objects
      let startDate: Date | undefined;
      let endDate: Date | undefined;
      
      // Create date range based on selected value
      const now = new Date();
      switch (dateRange) {
        case 'today':
          startDate = new Date(now.setHours(0, 0, 0, 0));
          endDate = new Date();
          break;
        case 'yesterday':
          startDate = new Date(now.setDate(now.getDate() - 1));
          startDate.setHours(0, 0, 0, 0);
          endDate = new Date(now.setHours(23, 59, 59, 999));
          break;
        case 'week':
          startDate = new Date(now.setDate(now.getDate() - 7));
          endDate = new Date();
          break;
        case 'month':
          startDate = new Date(now.setMonth(now.getMonth() - 1));
          endDate = new Date();
          break;
        default:
          startDate = new Date(now.setDate(now.getDate() - 7)); // Default to last 7 days
          endDate = new Date();
      }
      
      // Use proper parameter format - passing parameters directly instead of as an object
      const statsResponse = await transmissionApiService.getStatistics(
        organizationId,
        startDate,
        endDate
      );
      
      // Create metrics from statistics
      // statsResponse now directly contains the analytics data
      const newMetrics: TransmissionMetric[] = [
          {
            id: 'total',
            name: 'Total Transmissions',
            value: statsResponse.total || 0,
            change: statsResponse.totalChange || 0,
            status: statsResponse.totalChange > 0 ? 'positive' : 'neutral',
            icon: <Activity className="h-5 w-5 text-blue-500" />
          },
          {
            id: 'success',
            name: 'Successful',
            value: statsResponse.successful || 0,
            change: statsResponse.successfulChange || 0,
            status: statsResponse.successfulChange > 0 ? 'positive' : 'neutral',
            icon: <CheckCircle className="h-5 w-5 text-green-500" />
          },
          {
            id: 'failed',
            name: 'Failed',
            value: statsResponse.failed || 0,
            change: statsResponse.failedChange || 0,
            status: statsResponse.failedChange > 0 ? 'negative' : 'positive',
            icon: <XCircle className="h-5 w-5 text-red-500" />
          },
          {
            id: 'pending',
            name: 'Pending',
            value: statsResponse.pending || 0,
            change: statsResponse.pendingChange || 0,
            status: 'neutral',
            icon: <Clock className="h-5 w-5 text-yellow-500" />
          }
        ];
        
        setMetrics(newMetrics);
      
      // Fetch transmission list
      // Pass parameters individually in the correct order to match the API service method signature
      const transmissionsResponse = await transmissionApiService.listTransmissions(
        organizationId,
        undefined, // certificateId
        undefined, // submissionId
        filterStatus === 'all' ? undefined : filterStatus, // status
        0, // skip
        100, // limit
        // Additional options including date range filtering could go in options parameter
        { params: { date_range: dateRange } }
      );
      
      // The transmissionsResponse now has a data property that contains the array of items
      if (transmissionsResponse?.data) {
        setTransmissions(transmissionsResponse.data.map(item => ({
          id: item.id,
          invoiceRef: item.reference_id || '',
          customerName: 'N/A', // This info is not in the API response
          amount: 0, // This info is not in the API response
          transmissionDate: item.transmission_time || item.created_at || new Date().toISOString(),
          status: mapTransmissionStatus(item.status),
          retryCount: item.retry_count || 0,
          errorMessage: undefined // Error message may be in debug_info which we don't have here
        })));
      }
    } catch (err) {
      console.error('Error fetching dashboard data:', err);
      setError('Failed to load transmission data. Please try again.');
      toast({
        title: 'Error',
        description: 'Failed to load transmission dashboard data',
        status: 'error'
      });
    } finally {
      setLoading(false);
    }
  };
  
  const applyFilters = () => {
    let filtered = [...transmissions];
    
    // Apply search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(item => 
        item.invoiceRef.toLowerCase().includes(query) || 
        item.customerName.toLowerCase().includes(query) ||
        (item.errorMessage && item.errorMessage.toLowerCase().includes(query))
      );
    }
    
    setFilteredTransmissions(filtered);
  };
  
  const handleRefresh = () => {
    fetchDashboardData();
    toast({
      title: 'Refreshed',
      description: 'Dashboard data has been refreshed',
      status: 'info'
    });
  };
  
  const handleToggleAutoRefresh = () => {
    setIsAutoRefresh(!isAutoRefresh);
    
    if (isAutoRefresh && refreshTimer) {
      clearInterval(refreshTimer);
      setRefreshTimer(null);
    }
  };
  
  const handleRetryTransmission = async (transmissionId: string) => {
    try {
      // Pass transmissionId directly as a string, not as an object
      await transmissionApiService.retryTransmission(
        transmissionId
      );
      
      toast({
        title: 'Retry Initiated',
        description: 'Transmission retry has been initiated',
        status: 'success'
      });
      
      // Refresh data after a short delay to allow backend to process
      setTimeout(() => {
        fetchDashboardData();
      }, 1000);
    } catch (err) {
      console.error('Error retrying transmission:', err);
      toast({
        title: 'Error',
        description: 'Failed to retry transmission',
        status: 'error'
      });
    }
  };
  
  const formatAmount = (amount: number) => {
    return new Intl.NumberFormat('en-NG', { 
      style: 'currency', 
      currency: 'NGN' 
    }).format(amount);
  };
  
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString('en-NG', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };
  
  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'success':
        return <Badge className="bg-green-100 text-green-800">Success</Badge>;
      case 'failed':
        return <Badge className="bg-red-100 text-red-800">Failed</Badge>;
      case 'pending':
        return <Badge className="bg-yellow-100 text-yellow-800">Pending</Badge>;
      case 'processing':
        return <Badge className="bg-blue-100 text-blue-800">Processing</Badge>;
      default:
        return <Badge className="bg-gray-100 text-gray-800">{status}</Badge>;
    }
  };
  
  return (
    <div className="space-y-6">
      <Card className="border-l-4 border-l-cyan-500">
        <CardHeader className="pb-2">
          <div className="flex justify-between items-center">
            <div className="flex items-center">
              <Activity className="h-5 w-5 text-cyan-600 mr-2" />
              <CardTitle>Transmission Monitoring</CardTitle>
              <ContextualHelp content={monitoringHelp.overview}>
                <HelpCircle className="h-4 w-4 ml-2 text-gray-400" />
              </ContextualHelp>
            </div>
            <div className="flex items-center space-x-2">
              <Button
                variant={isAutoRefresh ? "default" : "outline"}
                size="sm"
                onClick={handleToggleAutoRefresh}
              >
                <Clock className="h-4 w-4 mr-1" />
                {isAutoRefresh ? "Auto-refresh On" : "Auto-refresh Off"}
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={handleRefresh}
                disabled={loading}
              >
                {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
                <span className="ml-1">Refresh</span>
              </Button>
            </div>
          </div>
        </CardHeader>
        
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            {metrics.map(metric => (
              <div key={metric.id} className="bg-white p-4 rounded-lg border shadow-sm">
                <div className="flex justify-between items-start">
                  <div>
                    <p className="text-sm text-gray-500">{metric.name}</p>
                    <h3 className="text-2xl font-bold mt-1">{metric.value.toLocaleString()}</h3>
                    <div className="flex items-center mt-1">
                      {metric.change !== 0 && (
                        <span className={`text-xs ${
                          metric.status === 'positive' ? 'text-green-600' : 
                          metric.status === 'negative' ? 'text-red-600' : 
                          'text-gray-600'
                        }`}>
                          {metric.change > 0 ? '+' : ''}{metric.change}%
                        </span>
                      )}
                      <span className="text-xs text-gray-500 ml-1">vs prev. period</span>
                    </div>
                  </div>
                  <div className="p-2 rounded-full bg-gray-50">{metric.icon}</div>
                </div>
              </div>
            ))}
          </div>
          
          <div className="mb-6">
            <TransmissionHealthStatus 
              refreshInterval={refreshInterval} 
              onRefresh={handleRefresh}
            />
          </div>
          
          <Tabs defaultValue="live">
            <div className="flex justify-between items-center mb-4">
              <TabsList>
                <TabsTrigger value="live">Live Monitor</TabsTrigger>
                <TabsTrigger value="analytics">Analytics</TabsTrigger>
                <TabsTrigger value="alerts">System Alerts</TabsTrigger>
              </TabsList>
              
              <div className="flex items-center space-x-2">
                <Select value={dateRange} onValueChange={setDateRange}>
                  <SelectTrigger className="w-32">
                    <Calendar className="h-4 w-4 mr-1" />
                    <SelectValue placeholder="Period" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="today">Today</SelectItem>
                    <SelectItem value="yesterday">Yesterday</SelectItem>
                    <SelectItem value="week">This Week</SelectItem>
                    <SelectItem value="month">This Month</SelectItem>
                  </SelectContent>
                </Select>
                
                <Select value={filterStatus} onValueChange={setFilterStatus}>
                  <SelectTrigger className="w-32">
                    <Filter className="h-4 w-4 mr-1" />
                    <SelectValue placeholder="Status" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Status</SelectItem>
                    <SelectItem value="success">Success</SelectItem>
                    <SelectItem value="failed">Failed</SelectItem>
                    <SelectItem value="pending">Pending</SelectItem>
                    <SelectItem value="processing">Processing</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            
            <div className="mb-4">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                <Input
                  placeholder="Search by invoice reference, customer name, or error message..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            
            <TabsContent value="live" className="space-y-4">
              {loading ? (
                <div className="flex justify-center items-center p-8">
                  <Loader2 className="h-8 w-8 animate-spin text-cyan-600" />
                </div>
              ) : filteredTransmissions.length > 0 ? (
                <div className="overflow-x-auto">
                  <table className="w-full border-collapse">
                    <thead>
                      <tr className="border-b">
                        <th className="py-3 px-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Invoice Ref</th>
                        <th className="py-3 px-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Customer</th>
                        <th className="py-3 px-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Amount</th>
                        <th className="py-3 px-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                        <th className="py-3 px-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                        <th className="py-3 px-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Retries</th>
                        <th className="py-3 px-4 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredTransmissions.map(item => (
                        <tr key={item.id} className="border-b hover:bg-gray-50">
                          <td className="py-4 px-4 text-sm">{item.invoiceRef}</td>
                          <td className="py-4 px-4 text-sm">{item.customerName}</td>
                          <td className="py-4 px-4 text-sm">{formatAmount(item.amount)}</td>
                          <td className="py-4 px-4 text-sm whitespace-nowrap">{formatDate(item.transmissionDate)}</td>
                          <td className="py-4 px-4 text-sm">{getStatusBadge(item.status)}</td>
                          <td className="py-4 px-4 text-sm text-center">{item.retryCount}</td>
                          <td className="py-4 px-4 text-sm text-right">
                            {item.status === 'failed' && (
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => handleRetryTransmission(item.id)}
                              >
                                <RefreshCw className="h-3 w-3 mr-1" />
                                Retry
                              </Button>
                            )}
                            {item.status === 'success' && (
                              <Button
                                variant="outline"
                                size="sm"
                              >
                                <Download className="h-3 w-3 mr-1" />
                                Receipt
                              </Button>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="text-center p-8 border border-dashed rounded-lg">
                  <Activity className="h-12 w-12 mx-auto text-gray-400 mb-2" />
                  <h3 className="text-lg font-medium text-gray-900">No Transmissions Found</h3>
                  <p className="text-gray-500 mt-1">
                    {searchQuery 
                      ? "No transmissions match your search criteria. Try a different search term or filter."
                      : "There are no transmissions to display for the selected time period and filters."}
                  </p>
                </div>
              )}
              
              {error && (
                <div className="bg-red-50 p-4 rounded-md border border-red-200">
                  <div className="flex items-start">
                    <div className="mr-3 mt-0.5">
                      <AlertTriangle className="h-5 w-5 text-red-600" />
                    </div>
                    <div>
                      <h4 className="text-sm font-medium text-red-800">Error Loading Data</h4>
                      <p className="text-sm text-red-700 mt-1">{error}</p>
                      <Button
                        variant="outline"
                        size="sm"
                        className="mt-3 text-xs"
                        onClick={handleRefresh}
                      >
                        <RefreshCw className="h-3 w-3 mr-1" />
                        Try Again
                      </Button>
                    </div>
                  </div>
                </div>
              )}
            </TabsContent>
            
            <TabsContent value="analytics">
              <div className="bg-white p-6 rounded-lg border shadow-sm">
                <h3 className="text-lg font-medium text-gray-900 mb-4">Transmission Analytics</h3>
                <div className="aspect-[2/1] bg-gray-100 rounded-md flex items-center justify-center">
                  <div className="text-center">
                    <BarChart3 className="h-12 w-12 mx-auto text-gray-400 mb-2" />
                    <p className="text-gray-500">Analytics visualization will appear here</p>
                  </div>
                </div>
                <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="p-4 bg-gray-50 rounded-md">
                    <p className="text-sm text-gray-500">Success Rate</p>
                    <h4 className="text-xl font-semibold mt-1">
                      {metrics.length > 0 && metrics[0].value > 0
                        ? `${Math.round((metrics[1].value / metrics[0].value) * 100)}%`
                        : '0%'}
                    </h4>
                  </div>
                  <div className="p-4 bg-gray-50 rounded-md">
                    <p className="text-sm text-gray-500">Avg. Response Time</p>
                    <h4 className="text-xl font-semibold mt-1">1.2s</h4>
                  </div>
                  <div className="p-4 bg-gray-50 rounded-md">
                    <p className="text-sm text-gray-500">Peak Hour</p>
                    <h4 className="text-xl font-semibold mt-1">14:00-15:00</h4>
                  </div>
                  <div className="p-4 bg-gray-50 rounded-md">
                    <p className="text-sm text-gray-500">Total Value</p>
                    <h4 className="text-xl font-semibold mt-1">₦4.2M</h4>
                  </div>
                </div>
              </div>
            </TabsContent>
            
            <TabsContent value="alerts">
              <div className="space-y-4">
                <div className="bg-yellow-50 p-4 rounded-md border border-yellow-200">
                  <div className="flex items-start">
                    <div className="mr-3 mt-0.5">
                      <AlertTriangle className="h-5 w-5 text-yellow-600" />
                    </div>
                    <div>
                      <h4 className="text-sm font-medium text-yellow-800">Performance Alert</h4>
                      <p className="text-sm text-yellow-700 mt-1">
                        Transmission response times have increased by 15% in the last hour.
                        This may indicate FIRS API performance degradation.
                      </p>
                      <p className="text-xs text-yellow-600 mt-2">
                        Detected: {new Date().toLocaleString()}
                      </p>
                    </div>
                  </div>
                </div>
                
                <div className="bg-green-50 p-4 rounded-md border border-green-200">
                  <div className="flex items-start">
                    <div className="mr-3 mt-0.5">
                      <CheckCircle className="h-5 w-5 text-green-600" />
                    </div>
                    <div>
                      <h4 className="text-sm font-medium text-green-800">System Healthy</h4>
                      <p className="text-sm text-green-700 mt-1">
                        All transmission services are operating normally.
                        Success rate is at 99.7% for the current period.
                      </p>
                      <p className="text-xs text-green-600 mt-2">
                        Last checked: {new Date().toLocaleString()}
                      </p>
                    </div>
                  </div>
                </div>
                
                {isAdmin && (
                  <div className="mt-6">
                    <Button variant="outline" size="sm">
                      <Bell className="h-4 w-4 mr-1" />
                      Configure Alert Settings
                    </Button>
                  </div>
                )}
              </div>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
};

export default TransmissionMonitoringDashboard;
