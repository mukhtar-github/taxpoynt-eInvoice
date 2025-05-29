import React, { useState, useEffect } from 'react';
import { NextPage } from 'next';
import Head from 'next/head';
import { useRouter } from 'next/router';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/Select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../components/ui/Tabs';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/Card';
// Using Card component for error display instead of Alert
import { Button } from '../../components/ui/Button';
import { Loader2, AlertTriangle, RefreshCw } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import AppDashboardLayout from '../../components/layouts/AppDashboardLayout';
import SubmissionMetricsCard from '../../components/dashboard/SubmissionMetricsCard';
import RetryMetricsCard from '../../components/dashboard/RetryMetricsCard';
import ApiStatusOverview from '../../components/dashboard/ApiStatusOverview';
import {
  fetchSubmissionMetrics,
  fetchRetryMetrics,
  fetchOdooSubmissionMetrics,
  SubmissionMetrics,
  RetryMetrics
} from '../../services/submissionDashboardService';

const timeRangeOptions = [
  { value: '24h', label: 'Last 24 Hours' },
  { value: '7d', label: 'Last 7 Days' },
  { value: '30d', label: 'Last 30 Days' },
  { value: 'all', label: 'All Time' }
];

const SubmissionDashboard: NextPage = () => {
  const router = useRouter();
  const { isAuthenticated, isLoading } = useAuth();
  
  // Redirect to login if not authenticated
  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/auth/login?redirect=' + encodeURIComponent(router.pathname));
    }
  }, [isAuthenticated, isLoading, router]);
  
  // State for filters and data
  const [timeRange, setTimeRange] = useState('24h');
  const [activeTab, setActiveTab] = useState('overview');
  const [isDataLoading, setIsDataLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // State for metrics data
  const [submissionMetrics, setSubmissionMetrics] = useState<SubmissionMetrics | null>(null);
  const [retryMetrics, setRetryMetrics] = useState<RetryMetrics | null>(null);
  const [odooMetrics, setOdooMetrics] = useState<SubmissionMetrics | null>(null);

  // Create safe default data to prevent undefined errors
  const defaultSubmissionMetrics: SubmissionMetrics = {
    timestamp: new Date().toISOString(),
    summary: {
      total_submissions: 0,
      success_count: 0,
      failed_count: 0,
      pending_count: 0,
      success_rate: 0,
      avg_processing_time: 0,
      common_errors: []
    },
    status_breakdown: [],
    hourly_submissions: [],
    daily_submissions: [],
    common_errors: [],
    time_range: '24h'
  };
  
  const defaultRetryMetrics: RetryMetrics = {
    timestamp: new Date().toISOString(),
    metrics: {
      total_retries: 0,
      success_count: 0,
      failed_count: 0,
      pending_count: 0,
      success_rate: 0,
      avg_attempts: 0,
      max_attempts_reached_count: 0
    },
    retry_breakdown_by_status: [],
    retry_breakdown_by_severity: [],
    time_range: '24h'
  };



  // Create a function to fetch all dashboard data
  const fetchDashboardData = async () => {
    setIsDataLoading(true);
    setError(null);
    
    try {
      // Use Promise.allSettled to fetch all metrics with enhanced error handling
      const [submissionResult, retryResult, odooResult] = await Promise.allSettled([
        fetchSubmissionMetrics(timeRange).catch(err => {
          console.log('Submission metrics error:', err);
          return defaultSubmissionMetrics;
        }),
        fetchRetryMetrics(timeRange).catch(err => {
          console.log('Retry metrics error:', err);
          return defaultRetryMetrics;
        }),
        fetchOdooSubmissionMetrics(timeRange).catch(err => {
          console.log('Odoo metrics error:', err);
          return defaultSubmissionMetrics;
        })
      ]);
      
      // Safely process results, ensuring we always have default data if needed
      setSubmissionMetrics(
        submissionResult.status === 'fulfilled' ? 
          submissionResult.value || defaultSubmissionMetrics : 
          defaultSubmissionMetrics
      );
      
      setRetryMetrics(
        retryResult.status === 'fulfilled' ? 
          retryResult.value || defaultRetryMetrics : 
          defaultRetryMetrics
      );
      
      setOdooMetrics(
        odooResult.status === 'fulfilled' ? 
          odooResult.value || defaultSubmissionMetrics : 
          defaultSubmissionMetrics
      );
    } catch (err) {
      console.error('Error fetching dashboard data:', err);
      setError('Unable to fetch dashboard data. Please try again later.');
    } finally {
      setIsDataLoading(false);
    }
  };

  // Call the fetch function when component mounts or filters change
  useEffect(() => {
    fetchDashboardData();
  }, [timeRange]);

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin" />
        <span className="ml-2">Loading...</span>
      </div>
    );
  }

  // If not authenticated, don't render anything (will redirect)
  if (!isAuthenticated) {
    return null;
  }

  return (
    <>
      <Head>
        <title>Submission Dashboard | TaxPoynt eInvoice</title>
        <meta name="description" content="Monitor e-invoice submission metrics and status" />
      </Head>

      <AppDashboardLayout>
        <div className="space-y-6">
          {/* Header with filters */}
          <div className="flex flex-col md:flex-row items-start md:items-center justify-between space-y-4 md:space-y-0">
            <div>
              <h1 className="text-2xl font-bold tracking-tight">Submission Dashboard</h1>
              <p className="text-sm text-gray-500">Monitor your e-invoice submission metrics and status</p>
            </div>
            
            <div className="flex items-center space-x-4">
              <div className="w-[150px]">
                <Select
                  value={timeRange}
                  onValueChange={(value) => setTimeRange(value)}
                >
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="Select time range" />
                  </SelectTrigger>
                  <SelectContent>
                    {timeRangeOptions.map((option) => (
                      <SelectItem key={option.value} value={option.value}>
                        {option.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              
              <Button 
                variant="outline"
                size="icon"
                onClick={() => fetchDashboardData()}
                disabled={isDataLoading}
                title="Refresh data"
              >
                {isDataLoading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <RefreshCw className="h-4 w-4" />
                )}
              </Button>
            </div>
          </div>

          {/* Error display */}
          {error && (
            <Card className="border-red-300 shadow-sm">
              <CardContent className="flex items-center space-x-2 p-4">
                <AlertTriangle className="h-5 w-5 text-red-500" />
                <p className="text-sm text-red-800">{error}</p>
              </CardContent>
            </Card>
          )}
          
          {/* Dashboard content */}
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList>
              <TabsTrigger value="overview">Overview</TabsTrigger>
              <TabsTrigger value="odoo">Odoo</TabsTrigger>
              <TabsTrigger value="retry">Retry Metrics</TabsTrigger>
            </TabsList>
            
            <TabsContent value="overview" className="space-y-4">
              {/* API Status */}
              <ApiStatusOverview />
              
              {/* Submission Metrics */}
              {submissionMetrics ? (
                <SubmissionMetricsCard metrics={submissionMetrics} isLoading={isDataLoading} />
              ) : (
                <div className="text-center py-12">
                  <p>No submission metrics available. Try changing the filters or refreshing the page.</p>
                </div>
              )}
            </TabsContent>
            
            <TabsContent value="odoo" className="space-y-4">
              {odooMetrics ? (
                <>
                  <Card>
                    <CardHeader>
                      <CardTitle>Odoo Integration Metrics</CardTitle>
                      <CardDescription>
                        Submission metrics for invoices from Odoo
                      </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div className="bg-white rounded-lg p-4 shadow-sm border">
                          <p className="text-sm font-medium text-gray-500">Total Submissions</p>
                          <p className="text-3xl font-bold">{odooMetrics.summary.total_submissions}</p>
                        </div>
                        
                        <div className="bg-white rounded-lg p-4 shadow-sm border">
                          <p className="text-sm font-medium text-gray-500">Success Rate</p>
                          <p className="text-3xl font-bold">{odooMetrics.summary.success_rate}%</p>
                        </div>
                        
                        <div className="bg-white rounded-lg p-4 shadow-sm border">
                          <p className="text-sm font-medium text-gray-500">Average Processing Time</p>
                          <p className="text-3xl font-bold">{odooMetrics.summary.avg_processing_time}s</p>
                        </div>
                      </div>
                      
                      <div className="flex space-x-4 justify-end mt-4">
                        <Button
                          onClick={() => router.push('/dashboard/integrations')}
                        >
                          Manage Integrations
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                </>
              ) : (
                <div className="text-center py-12">
                  <p>No Odoo metrics available. Try changing the filters or refreshing the page.</p>
                </div>
              )}
            </TabsContent>
            
            <TabsContent value="retry" className="space-y-4">
              {retryMetrics ? (
                <>
                  <Card>
                    <CardHeader>
                      <CardTitle>Retry Metrics</CardTitle>
                      <CardDescription>
                        Statistics for failed submission retry attempts
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <RetryMetricsCard metrics={retryMetrics} isLoading={isDataLoading} />
                      
                      <div className="flex space-x-4 justify-end mt-6">
                        <Button 
                          variant="outline"
                          onClick={() => router.push('/dashboard/retry-queue')}
                          className="flex-1"
                        >
                          View Retry Queue
                        </Button>
                        
                        <Button 
                          variant="outline"
                          onClick={() => router.push('/dashboard/retry-config')}
                          className="flex-1"
                        >
                          Retry Configuration
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                </>
              ) : (
                <div className="text-center py-12">
                  <p>No retry metrics available. Try changing the filters or refreshing the page.</p>
                </div>
              )}
            </TabsContent>
          </Tabs>
        </div>
      </AppDashboardLayout>
    </>
  );
};

export default SubmissionDashboard;
