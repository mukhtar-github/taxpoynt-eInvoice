import React, { useState, useEffect } from 'react';
import { NextPage } from 'next';
import Head from 'next/head';
import { useRouter } from 'next/router';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/Select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../components/ui/Tabs';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Loader2, AlertTriangle, RefreshCw, Activity, BarChart3, RotateCw, Clock } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useToast } from '../../components/ui/Toast';
import AppDashboardLayout from '../../components/layouts/AppDashboardLayout';
import RetryConfirmationDialog from '../../components/app/transmission/RetryConfirmationDialog';
// Import APP-specific components from the app directory
import { 
  TransmissionStatsCard,
  TransmissionTimelineChart,
  TransmissionListTable
} from '../../components/app';
import transmissionApiService, { 
  TransmissionStatus, 
  TransmissionTimeline,
  TransmissionListItem
} from '../../services/transmissionApiService';

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
 * Transmission Dashboard - Access Point Provider (APP) Feature
 * 
 * This dashboard is part of the APP functionality, which is separate from
 * the System Integration (SI) service. It allows tracking and management
 * of e-invoice transmissions between the APP and regulatory authorities.
 */
const TransmissionDashboard: NextPage = () => {
  const router = useRouter();
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  const toast = useToast();
  
  // Redirect to login if not authenticated
  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/auth/login?redirect=' + encodeURIComponent(router.pathname));
    }
  }, [isAuthenticated, authLoading, router]);
  
  // State for filters and data
  const [timeRange, setTimeRange] = useState('24h');
  const [interval, setInterval] = useState('day');
  const [activeTab, setActiveTab] = useState('overview');
  const [isDataLoading, setIsDataLoading] = useState(true);
  const [isRetrying, setIsRetrying] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // State for metrics data
  const [statistics, setStatistics] = useState<TransmissionStatus | null>(null);
  const [timeline, setTimeline] = useState<TransmissionTimeline | null>(null);
  const [recentTransmissions, setRecentTransmissions] = useState<TransmissionListItem[]>([]);
  
  // Retry dialog state
  const [isRetryDialogOpen, setIsRetryDialogOpen] = useState(false);
  const [selectedTransmissionId, setSelectedTransmissionId] = useState<string | null>(null);
  
  // Convert time range to date objects
  const getDateRange = (range: string) => {
    const endDate = new Date();
    let startDate = new Date();
    
    switch(range) {
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
  
  // Load all dashboard data
  const loadDashboardData = async () => {
    setIsDataLoading(true);
    setError(null);
    
    try {
      const { startDate, endDate } = getDateRange(timeRange);
      
      // Load transmission statistics
      const statsResponse = await transmissionApiService.getStatistics(
        undefined, // organization ID - could filter by user.organizationId if needed
        startDate,
        endDate
      );
      
      if (statsResponse.error) {
        throw new Error(statsResponse.error);
      }
      
      setStatistics(statsResponse.data);
      
      // Load timeline data
      const timelineResponse = await transmissionApiService.getTimeline(
        undefined, // organization ID
        startDate,
        endDate,
        interval as 'hour' | 'day' | 'week' | 'month'
      );
      
      if (timelineResponse.error) {
        throw new Error(timelineResponse.error);
      }
      
      setTimeline(timelineResponse.data);
      
      // Load recent transmissions
      const recentResponse = await transmissionApiService.listTransmissions(
        undefined, // organization ID
        undefined, // certificate ID
        undefined, // submission ID
        undefined, // status
        0, // skip
        10 // limit - show top 10 recent transmissions
      );
      
      if (recentResponse.error) {
        throw new Error(recentResponse.error);
      }
      
      setRecentTransmissions(recentResponse.data || []);
      
    } catch (err: any) {
      setError(err.message || 'Failed to load transmission data');
      console.error('Dashboard data loading error:', err);
    } finally {
      setIsDataLoading(false);
    }
  };
  
  const refreshData = () => {
    loadDashboardData();
  };
  
  // Open retry dialog for a specific transmission
  const openRetryDialog = (id: string) => {
    setSelectedTransmissionId(id);
    setIsRetryDialogOpen(true);
  };
  
  // Handle retry transmission with configurable parameters
  const handleRetryConfirm = async (maxRetries: number, retryDelay: number, force: boolean) => {
    if (!selectedTransmissionId) return;
    
    setIsRetrying(true);
    try {
      const retryResponse = await transmissionApiService.retryTransmission(
        selectedTransmissionId,
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
      setIsRetrying(false);
      setIsRetryDialogOpen(false);
      setSelectedTransmissionId(null);
    }
  };
  
  // Load data on mount and when filters change
  useEffect(() => {
    if (isAuthenticated) {
      refreshData();
    }
  }, [isAuthenticated, timeRange, interval]);
  
  // Handle tab change
  const handleTabChange = (value: string) => {
    setActiveTab(value);
  };
  
  // Show loading state while authentication is in progress
  if (authLoading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }
  
  return (
    <AppDashboardLayout>
      <Head>
        <title>Transmission Dashboard | TaxPoynt eInvoice</title>
      </Head>
      
      <div className="container mx-auto py-6">
        <div className="mb-6 flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
          <h1 className="text-3xl font-bold tracking-tight">Transmission Dashboard</h1>
          
          <div className="flex items-center gap-4">
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
            
            <Button 
              variant="outline" 
              size="icon" 
              onClick={loadDashboardData}
              disabled={isDataLoading}
            >
              {isDataLoading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <RefreshCw className="h-4 w-4" />
              )}
              <span className="sr-only">Refresh data</span>
            </Button>
          </div>
        </div>
        
        {error && (
          <Card className="mb-6 border-red-200 bg-red-50">
            <CardContent className="pt-6">
              <div className="flex items-center gap-2 text-red-700">
                <AlertTriangle className="h-5 w-5" />
                <p>{error}</p>
              </div>
            </CardContent>
          </Card>
        )}
        
        <Tabs value={activeTab} onValueChange={handleTabChange} className="space-y-6">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="overview">
              <Activity className="mr-2 h-4 w-4" />
              Overview
            </TabsTrigger>
            <TabsTrigger value="timeline">
              <BarChart3 className="mr-2 h-4 w-4" />
              Timeline
            </TabsTrigger>
            <TabsTrigger value="transmissions">
              <Clock className="mr-2 h-4 w-4" />
              Recent Transmissions
            </TabsTrigger>
          </TabsList>
          
          {/* Overview Tab */}
          <TabsContent value="overview" className="space-y-6">
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
              {isDataLoading ? (
                Array(3).fill(0).map((_, i) => (
                  <Card key={i} className="overflow-hidden">
                    <CardHeader className="p-4">
                      <div className="h-5 w-3/4 animate-pulse rounded bg-gray-200"></div>
                    </CardHeader>
                    <CardContent className="p-4 pt-0">
                      <div className="h-40 animate-pulse rounded bg-gray-100"></div>
                    </CardContent>
                  </Card>
                ))
              ) : statistics ? (
                <>
                  <TransmissionStatsCard 
                    title="Transmission Status"
                    stats={statistics}
                  />
                  <Card>
                    <CardHeader>
                      <CardTitle>Success Rate</CardTitle>
                      <CardDescription>Overall transmission success rate</CardDescription>
                    </CardHeader>
                    <CardContent className="flex items-center justify-center pb-6">
                      <div className="relative h-36 w-36">
                        <div className="flex h-full w-full items-center justify-center rounded-full border-8 border-gray-100">
                          <div className="text-center">
                            <span className="text-3xl font-bold">
                              {Math.round(statistics.success_rate * 100)}%
                            </span>
                          </div>
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
                  <Card>
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
            </div>
          </TabsContent>
          
          {/* Timeline Tab */}
          <TabsContent value="timeline" className="space-y-6">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <div>
                  <CardTitle>Transmission Timeline</CardTitle>
                  <CardDescription>View transmission trends over time</CardDescription>
                </div>
                <Select value={interval} onValueChange={setInterval}>
                  <SelectTrigger className="w-[180px]">
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
              </CardHeader>
              <CardContent className="p-6">
                {isDataLoading ? (
                  <div className="h-80 animate-pulse rounded bg-gray-100"></div>
                ) : timeline && timeline.timeline.length > 0 ? (
                  <div className="h-80">
                    <TransmissionTimelineChart data={timeline} />
                  </div>
                ) : (
                  <div className="flex h-80 items-center justify-center">
                    <p className="text-gray-500">No timeline data available for selected period</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
          
          {/* Recent Transmissions Tab */}
          <TabsContent value="transmissions" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Recent Transmissions</CardTitle>
                <CardDescription>Most recent transmission attempts</CardDescription>
              </CardHeader>
              <CardContent>
                {isDataLoading ? (
                  <div className="h-96 animate-pulse rounded bg-gray-100"></div>
                ) : recentTransmissions && recentTransmissions.length > 0 ? (
                  <TransmissionListTable 
                    transmissions={recentTransmissions}
                    onViewDetails={(id) => router.push(`/dashboard/transmission/${id}`)}
                    onRetry={openRetryDialog}
                    isRetrying={isRetrying}
                  />
                ) : (
                  <div className="flex h-40 items-center justify-center">
                    <p className="text-gray-500">No recent transmissions found</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
      {/* Retry Confirmation Dialog */}
      {selectedTransmissionId && (
        <RetryConfirmationDialog
          isOpen={isRetryDialogOpen}
          onClose={() => {
            setIsRetryDialogOpen(false);
            setSelectedTransmissionId(null);
          }}
          onConfirm={handleRetryConfirm}
          transmissionId={selectedTransmissionId}
          isLoading={isRetrying}
        />
      )}
    </AppDashboardLayout>
  );
};

export default TransmissionDashboard;
