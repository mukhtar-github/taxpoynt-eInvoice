import React, { useState, useEffect } from 'react';
import { NextPage } from 'next';
import Head from 'next/head';
import { useRouter } from 'next/router';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/Select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../components/ui/Tabs';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Loader2, RefreshCw, Activity, BarChart3, Layers, Clock } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useToast } from '../../components/ui/Toast';
import AppDashboardLayout from '../../components/layouts/AppDashboardLayout';
import RetryConfirmationDialog from '../../components/platform/transmission/RetryConfirmationDialog';
import TransmissionHealthStatus from '../../components/platform/transmission/TransmissionHealthStatus';
import TransmissionAnalytics from '../../components/platform/transmission/TransmissionAnalytics';
import BatchProcessingControls from '../../components/platform/transmission/BatchProcessingControls';
import { 
  TransmissionStatsCard,
  TransmissionTimelineChart,
  TransmissionListTable
} from '../../components/platform/transmission';
import transmissionApiService from '../../services/transmissionApiService';
// User data is now obtained from AuthContext

const timeRangeOptions = [
  { value: '24h', label: 'Last 24 Hours' },
  { value: '7d', label: 'Last 7 Days' },
  { value: '30d', label: 'Last 30 Days' },
  { value: 'all', label: 'All Time' }
];

const intervalOptions = [
  { value: 'hour', label: 'Hourly' },
  { value: 'day', label: 'Daily' },
  { value: 'week', label: 'Weekly' },
  { value: 'month', label: 'Monthly' }
];

/**
 * Transmission Dashboard - Platform Feature
 * 
 * This dashboard is part of the Platform functionality, which is separate from
 * the System Integration (SI) service. It allows tracking and management
 * of e-invoice transmissions between the Platform and regulatory authorities.
 */
const TransmissionDashboard: NextPage = () => {
  const router = useRouter();
  const { user, isAuthenticated, isLoading: authLoading } = useAuth();
  const toast = useToast();
  
  // State for tabs and UI
  const [activeTab, setActiveTab] = useState<string>('monitoring');
  
  // State for filters and data
  const [timeRange, setTimeRange] = useState<string>('7d');
  const [interval, setInterval] = useState<string>('day');
  const [loading, setLoading] = useState<boolean>(true);
  const [showRetryDialog, setShowRetryDialog] = useState<boolean>(false);
  const [selectedTransmission, setSelectedTransmission] = useState<string | null>(null);
  const [activeBatchTaskId, setActiveBatchTaskId] = useState<string | null>(null);
  const [isAdmin, setIsAdmin] = useState<boolean>(false);
  
  // State for metrics data
  const [statistics, setStatistics] = useState<any>(null);
  const [timeline, setTimeline] = useState<any>(null);
  const [recentTransmissions, setRecentTransmissions] = useState<any[]>([]);
  
  // Redirect to login if not authenticated
  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login');
    } else if (isAuthenticated) {
      // Check if user has admin privileges
      setIsAdmin(user?.role === 'admin' || false);
      loadDashboardData();
    }
  }, [isAuthenticated, authLoading, router]);
  
  // Reload data when timeRange or interval changes
  useEffect(() => {
    if (isAuthenticated && !authLoading) {
      loadTimeline();
    }
  }, [timeRange, interval, isAuthenticated, authLoading]);
  
  // Load dashboard data (stats, timeline, transmissions)
  const loadDashboardData = async () => {
    try {
      setLoading(true);
      await Promise.all([
        loadTransmissions(),
        loadStats(),
        loadTimeline()
      ]);
    } catch (error) {
      console.error('Error loading dashboard data:', error);
      toast({
        title: 'Data Loading Error',
        description: 'Failed to refresh transmission data',
        status: 'error'
      });
    } finally {
      setLoading(false);
    }
  };

  // Load transmission list
  const loadTransmissions = async () => {
    try {
      const { data, error } = await transmissionApiService.listTransmissions();
      if (error) {
        throw new Error(error);
      }
      setRecentTransmissions(data || []);
    } catch (error) {
      console.error('Error loading transmissions:', error);
    }
  };

  // Load transmission statistics
  const loadStats = async () => {
    try {
      const { data, error } = await transmissionApiService.getStatistics();
      if (error) {
        throw new Error(error);
      }
      setStatistics(data || null);
    } catch (error) {
      console.error('Error loading statistics:', error);
    }
  };

  // Load transmission timeline
  const loadTimeline = async () => {
    const { startDate, endDate } = getDateRange(timeRange);
    
    try {
      const { data, error } = await transmissionApiService.getTimeline(
        undefined, // organizationId
        startDate,
        endDate,
        interval as 'hour' | 'day' | 'week' | 'month'
      );
      
      if (error) {
        throw new Error(error);
      }
      
      setTimeline(data || null);
    } catch (error) {
      console.error('Error loading timeline:', error);
    }
  };

  // Convert time range to date objects
  const getDateRange = (range: string) => {
    const endDate = new Date();
    let startDate = new Date();
    
    switch (range) {
      case '24h':
        startDate.setHours(startDate.getHours() - 24);
        break;
      case '7d':
        startDate.setDate(startDate.getDate() - 7);
        break;
      case '30d':
        startDate.setDate(startDate.getDate() - 30);
        break;
      case 'all':
        // Set to distant past for "all time"
        startDate = new Date(2020, 0, 1);
        break;
    }
    
    return { startDate, endDate };
  };

  // Handle batch processing start
  const handleBatchStarted = (taskId: string) => {
    setActiveBatchTaskId(taskId);
    toast({
      title: 'Batch Processing Started',
      description: `Task ID: ${taskId}`,
      status: 'success'
    });
  };

  // Handle batch error
  const handleBatchError = (error: string) => {
    toast({
      title: 'Batch Processing Error',
      description: error,
      status: 'error'
    });
  };

  // Open retry dialog for a specific transmission
  const openRetryDialog = (id: string) => {
    setSelectedTransmission(id);
    setShowRetryDialog(true);
  };

  // Handle retry transmission with configurable parameters
  const handleRetryConfirm = async (maxRetries: number, retryDelay: number, force: boolean) => {
    if (!selectedTransmission) return;
    
    try {
      const retryResponse = await transmissionApiService.retryTransmission(
        selectedTransmission,
        maxRetries,
        retryDelay,
        force
      );
      
      if (retryResponse.error) {
        throw new Error(retryResponse.error);
      }
      
      // Refresh the data to show updated status
      await loadDashboardData();
      
      toast({
        title: "Transmission Retry Initiated",
        description: retryDelay > 0 
          ? `Retry scheduled with exponential backoff starting at ${retryDelay}s.`
          : "The system is attempting to resend the transmission immediately.",
        status: "success"
      });
    } catch (err) {
      console.error('Error retrying transmission:', err);
      toast({
        title: "Retry Failed",
        description: `Failed to retry the transmission: ${err instanceof Error ? err.message : 'Unknown error'}`,
        status: "error"
      });
    } finally {
      setShowRetryDialog(false);
      setSelectedTransmission(null);
    }
  };

  return (
    <>
      <Head>
        <title>Transmission Dashboard | TaxPoynt</title>
      </Head>
      <AppDashboardLayout>
        <div className="flex flex-col space-y-6">
          <div className="flex flex-col space-y-2">
            <h1 className="text-2xl font-semibold tracking-tight">Transmission Dashboard</h1>
            <p className="text-muted-foreground">
              Monitor and manage e-invoice transmissions between TaxPoynt and regulatory authorities
            </p>
          </div>
          
          {/* Main tabs */}
          <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
            <TabsList className="grid grid-cols-4 lg:w-[600px]">
              <TabsTrigger value="monitoring" className="flex items-center">
                <Activity className="h-4 w-4 mr-1.5" />
                Monitoring
              </TabsTrigger>
              <TabsTrigger value="analytics" className="flex items-center">
                <BarChart3 className="h-4 w-4 mr-1.5" />
                Analytics
              </TabsTrigger>
              <TabsTrigger value="batches" className="flex items-center">
                <Layers className="h-4 w-4 mr-1.5" />
                Batch Controls
              </TabsTrigger>
              <TabsTrigger value="history" className="flex items-center">
                <Clock className="h-4 w-4 mr-1.5" />
                History
              </TabsTrigger>
            </TabsList>
            
            {/* Monitoring Tab Content */}
            <TabsContent value="monitoring" className="space-y-6">
              {/* Controls and filters */}
              <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                <div className="flex items-center space-x-2">
                  <Select value={timeRange} onValueChange={setTimeRange}>
                    <SelectTrigger className="w-[180px]">
                      <SelectValue placeholder="Select time range" />
                    </SelectTrigger>
                    <SelectContent>
                      {timeRangeOptions.map(option => (
                        <SelectItem key={option.value} value={option.value}>
                          {option.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  
                  <Select value={interval} onValueChange={setInterval}>
                    <SelectTrigger className="w-[150px]">
                      <SelectValue placeholder="Select interval" />
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
                  variant="outline" 
                  onClick={loadDashboardData}
                  disabled={loading}
                >
                  {loading ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Loading
                    </>
                  ) : (
                    <>
                      <RefreshCw className="mr-2 h-4 w-4" />
                      Refresh
                    </>
                  )}
                </Button>
              </div>
              
              {/* Health Status Card */}
              <TransmissionHealthStatus refreshInterval={60000} />
              
              {/* Stats and timeline */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {statistics ? (
                  <>
                    {/* Main Stats Card */}
                    <TransmissionStatsCard 
                      stats={statistics} 
                      title="Transmission Statistics"
                    />
                    
                    {/* Success Rate Card */}
                    <Card className="border-l-4 border-l-cyan-500">
                      <CardHeader className="pb-2">
                        <CardTitle>Success Rate</CardTitle>
                        <CardDescription>Overall transmission success</CardDescription>
                      </CardHeader>
                      <CardContent className="pt-0">
                        <div className="relative h-36 flex items-center justify-center">
                          <div className="relative z-10 text-center">
                            <span className="text-3xl font-bold">
                              {Math.round(statistics.success_rate * 100)}%
                            </span>
                          </div>
                          <div 
                            className="absolute inset-0 rounded-full border-8 border-transparent border-t-primary"
                            style={{ 
                              transform: `rotate(${statistics.success_rate * 360}deg)`,
                              transition: 'transform 1s ease-out' 
                            }}
                          ></div>
                        </div>
                      </CardContent>
                    </Card>
                    
                    {/* Retry Statistics Card */}
                    <Card className="border-l-4 border-l-cyan-500">
                      <CardHeader>
                        <CardTitle>Retry Statistics</CardTitle>
                        <CardDescription>Retry information for transmissions</CardDescription>
                      </CardHeader>
                      <CardContent className="pb-6">
                        <div className="space-y-4">
                          <div>
                            <p className="text-sm font-medium">Average Retries</p>
                            <p className="text-2xl font-bold">{statistics.average_retries.toFixed(1)}</p>
                          </div>
                          <div>
                            <p className="text-sm font-medium">Transmissions in Retry</p>
                            <p className="text-2xl font-bold">{statistics.retrying}</p>
                          </div>
                          <div>
                            <p className="text-sm font-medium">Signed Transmissions</p>
                            <p className="text-2xl font-bold">{statistics.signed_transmissions}</p>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  </>
                ) : (
                  <Card className="col-span-full">
                    <CardContent className="p-6 text-center">
                      <p className="text-gray-500">No transmission data available</p>
                    </CardContent>
                  </Card>
                )}
                
                {/* Timeline Chart */}
                {timeline && (
                  <Card className="col-span-full border-l-4 border-l-cyan-500">
                    <CardHeader>
                      <CardTitle>Transmission Timeline</CardTitle>
                      <CardDescription>
                        Activity over {timeRange === '24h' ? 'the last 24 hours' : 
                          timeRange === '7d' ? 'the last 7 days' : 
                          timeRange === '30d' ? 'the last 30 days' : 
                          'all time'}
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <TransmissionTimelineChart data={timeline} />
                    </CardContent>
                  </Card>
                )}
              </div>
            </TabsContent>
            
            {/* Analytics Tab Content */}
            <TabsContent value="analytics" className="space-y-6">
              <TransmissionAnalytics 
                defaultTimeRange={timeRange}
              />
            </TabsContent>
            
            {/* Batch Controls Tab Content */}
            <TabsContent value="batches" className="space-y-6">
              <BatchProcessingControls 
                onBatchStarted={handleBatchStarted}
                onError={handleBatchError}
              />
            </TabsContent>
            
            {/* History Tab Content */}
            <TabsContent value="history" className="space-y-6">
              <Card className="border-l-4 border-l-cyan-500">
                <CardHeader>
                  <CardTitle>Recent Transmissions</CardTitle>
                  <CardDescription>Most recent transmission attempts</CardDescription>
                </CardHeader>
                <CardContent>
                  {recentTransmissions.length > 0 ? (
                    <TransmissionListTable
                      transmissions={recentTransmissions}
                      onRetry={openRetryDialog}
                      isLoading={loading}
                    />
                  ) : (
                    <div className="text-center py-8">
                      <p className="text-muted-foreground">No transmission history available</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </div>
      </AppDashboardLayout>
      
      {/* Retry Confirmation Dialog */}
      {showRetryDialog && selectedTransmission && (
        <RetryConfirmationDialog
          isOpen={showRetryDialog}
          onClose={() => setShowRetryDialog(false)}
          onConfirm={handleRetryConfirm}
          transmissionId={selectedTransmission} isLoading={false}        />
      )}
    </>
  );
};

export default TransmissionDashboard;