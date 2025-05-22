import React, { useState, useEffect } from 'react';
import { NextPage } from 'next';
import Head from 'next/head';
import { useRouter } from 'next/router';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/Select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/Tabs';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/Card';
// Using Card component for error display instead of Alert
import { Button } from '../components/ui/Button';
import { Loader2, AlertTriangle, RefreshCw } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import DashboardLayout from '../components/layouts/DashboardLayout';
import SubmissionMetricsCard from '../components/dashboard/SubmissionMetricsCard';
import RetryMetricsCard from '../components/dashboard/RetryMetricsCard';
import {
  fetchSubmissionMetrics,
  fetchRetryMetrics,
  fetchOdooSubmissionMetrics,
  SubmissionMetrics,
  RetryMetrics
} from '../services/submissionDashboardService';

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

  // Fetch data based on selected filters
  const fetchDashboardData = async () => {
    setIsDataLoading(true);
    setError(null);
    
    try {
      // Fetch all data in parallel
      const [submissions, retries, odoo] = await Promise.all([
        fetchSubmissionMetrics(timeRange),
        fetchRetryMetrics(timeRange),
        fetchOdooSubmissionMetrics(timeRange)
      ]);
      
      setSubmissionMetrics(submissions);
      setRetryMetrics(retries);
      setOdooMetrics(odoo);
    } catch (err) {
      console.error('Error fetching dashboard data:', err);
      setError('Failed to load dashboard data. Please try again later.');
    } finally {
      setIsDataLoading(false);
    }
  };

  // Fetch data on initial load and when filters change
  useEffect(() => {
    fetchDashboardData();
  }, [timeRange]);

  // Handle refresh button click
  const handleRefresh = () => {
    fetchDashboardData();
  };

  // Show loading state while checking auth
  if (isLoading) {
    return (
      <>
        <Head>
          <title>Submission Dashboard | TaxPoynt eInvoice</title>
          <meta name="description" content="Monitor invoice submission metrics and retry status" />
        </Head>
        <div className="flex items-center justify-center min-h-screen">
          <Loader2 className="h-8 w-8 animate-spin text-primary mr-3" />
          <p>Loading dashboard...</p>
        </div>
      </>
    );
  }
  
  // If not authenticated, don't render dashboard content
  if (!isAuthenticated) {
    return null; // Will redirect via the useEffect
  }
  
  return (
    <>
      <Head>
        <title>Submission Dashboard | TaxPoynt eInvoice</title>
        <meta name="description" content="Monitor invoice submission metrics and retry status" />
      </Head>

      <DashboardLayout>
        <div className="container mx-auto px-4 py-6">
          <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-6 gap-4">
            <div>
              <h1 className="text-3xl font-bold tracking-tight">Submission Dashboard</h1>
              <p className="text-gray-500 dark:text-gray-400 mt-1">
                Monitor invoice submission metrics, status breakdowns, and retry analytics
              </p>
            </div>
            
            <div className="flex items-center gap-3">
              <Select
                value={timeRange}
                onValueChange={(value) => setTimeRange(value)}
              >
                <SelectTrigger className="w-[180px]">
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
              
              <Button 
                variant="outline" 
                onClick={handleRefresh} 
                disabled={isDataLoading}
              >
                {isDataLoading ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <RefreshCw className="mr-2 h-4 w-4" />
                )}
                Refresh
              </Button>
            </div>
          </div>

          {error && (
            <Card className="mb-6 border border-destructive bg-destructive/10">
              <CardContent className="flex items-start gap-3 p-4">
                <AlertTriangle className="h-5 w-5 text-destructive" />
                <div>
                  <CardTitle className="text-destructive">Error</CardTitle>
                  <CardDescription className="text-destructive-foreground">{error}</CardDescription>
                </div>
              </CardContent>
            </Card>
          )}

          <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
            <TabsList className="grid grid-cols-3 max-w-md mx-auto mb-6">
              <TabsTrigger value="overview">Overview</TabsTrigger>
              <TabsTrigger value="odoo">Odoo Integration</TabsTrigger>
              <TabsTrigger value="retries">Retry Analysis</TabsTrigger>
            </TabsList>

            <TabsContent value="overview" className="space-y-6">
              {isDataLoading ? (
                <div className="flex justify-center items-center h-64">
                  <Loader2 className="h-8 w-8 animate-spin text-primary" />
                </div>
              ) : submissionMetrics ? (
                <>
                  <SubmissionMetricsCard 
                    metrics={submissionMetrics} 
                    title="Invoice Submission Overview"
                    description="Comprehensive view of all invoice submissions across all integrations"
                  />
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <Card>
                      <CardHeader>
                        <CardTitle>Common Failure Reasons</CardTitle>
                        <CardDescription>Most frequent errors in failed submissions</CardDescription>
                      </CardHeader>
                      <CardContent>
                        {submissionMetrics.common_errors.length > 0 ? (
                          <div className="overflow-x-auto">
                            <table className="min-w-full bg-white dark:bg-gray-800 shadow rounded-lg">
                              <thead>
                                <tr className="border-b dark:border-gray-700">
                                  <th className="py-3 px-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Error Type</th>
                                  <th className="py-3 px-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Count</th>
                                  <th className="py-3 px-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Severity</th>
                                </tr>
                              </thead>
                              <tbody>
                                {submissionMetrics.common_errors.slice(0, 5).map((error, index) => (
                                  <tr key={index} className="border-b dark:border-gray-700">
                                    <td className="py-3 px-4">{error.error_type}</td>
                                    <td className="py-3 px-4">{error.count}</td>
                                    <td className="py-3 px-4">
                                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                                        error.severity === 'critical' ? 'bg-destructive text-destructive-foreground' :
                                        error.severity === 'high' ? 'bg-destructive/80 text-destructive-foreground' :
                                        error.severity === 'medium' ? 'bg-warning text-warning-foreground' :
                                        'bg-secondary text-secondary-foreground'
                                      }`}>
                                        {error.severity}
                                      </span>
                                    </td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        ) : (
                          <div className="text-center py-8">
                            <p>No errors recorded in this time period.</p>
                          </div>
                        )}
                      </CardContent>
                    </Card>
                    
                    <Card>
                      <CardHeader>
                        <CardTitle>System Health</CardTitle>
                        <CardDescription>Overall system health and performance metrics</CardDescription>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-4">
                          <div className="flex justify-between items-center p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                            <div>
                              <p className="text-sm text-gray-500">Success Rate</p>
                              <p className={`text-xl font-semibold ${
                                submissionMetrics.summary.success_rate >= 90 ? 'text-success' :
                                submissionMetrics.summary.success_rate >= 75 ? 'text-warning' :
                                'text-destructive'
                              }`}>
                                {submissionMetrics.summary.success_rate.toFixed(1)}%
                              </p>
                            </div>
                            <div className={`w-12 h-12 rounded-full flex items-center justify-center ${
                              submissionMetrics.summary.success_rate >= 90 ? 'bg-success/20 text-success' :
                              submissionMetrics.summary.success_rate >= 75 ? 'bg-warning/20 text-warning' :
                              'bg-destructive/20 text-destructive'
                            }`}>
                              {submissionMetrics.summary.success_rate >= 90 ? '👍' : 
                               submissionMetrics.summary.success_rate >= 75 ? '👌' : 
                               '👎'}
                            </div>
                          </div>
                          
                          <div className="flex justify-between items-center p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                            <div>
                              <p className="text-sm text-gray-500">Avg Processing Time</p>
                              <p className="text-xl font-semibold">
                                {(submissionMetrics.summary.avg_processing_time / 1000).toFixed(2)}s
                              </p>
                            </div>
                            <div className="w-12 h-12 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center">
                              ⏱️
                            </div>
                          </div>
                          
                          <div className="flex justify-between items-center p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                            <div>
                              <p className="text-sm text-gray-500">Failed Submissions</p>
                              <p className="text-xl font-semibold">
                                {submissionMetrics.summary.failed_count}
                              </p>
                            </div>
                            <Button 
                              variant="outline"
                              onClick={() => router.push('/retry-management/failed-submissions')}
                              className="text-xs"
                            >
                              View Details
                            </Button>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  </div>
                </>
              ) : (
                <div className="text-center py-12">
                  <p>No data available. Try changing the filters or refreshing the page.</p>
                </div>
              )}
            </TabsContent>

            <TabsContent value="odoo" className="space-y-6">
              {isDataLoading ? (
                <div className="flex justify-center items-center h-64">
                  <Loader2 className="h-8 w-8 animate-spin text-primary" />
                </div>
              ) : odooMetrics ? (
                <>
                  <SubmissionMetricsCard 
                    metrics={odooMetrics} 
                    title="Odoo Integration Metrics"
                    description="Detailed metrics for Odoo ERP integration submissions"
                  />
                  
                  <Card>
                    <CardHeader>
                      <CardTitle>Odoo Integration Analysis</CardTitle>
                      <CardDescription>Performance analysis of Odoo ERP integration</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                          <p className="text-sm text-gray-500">Total Odoo Submissions</p>
                          <p className="text-2xl font-bold">
                            {odooMetrics.odoo_metrics?.total_odoo_submissions || 0}
                          </p>
                        </div>
                        
                        <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                          <p className="text-sm text-gray-500">% of All Submissions</p>
                          <p className="text-2xl font-bold">
                            {(odooMetrics.odoo_metrics?.percentage_of_all_submissions || 0).toFixed(1)}%
                          </p>
                        </div>
                        
                        <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                          <p className="text-sm text-gray-500">Success Rate</p>
                          <p className={`text-2xl font-bold ${
                            odooMetrics.summary.success_rate >= 90 ? 'text-success' :
                            odooMetrics.summary.success_rate >= 75 ? 'text-warning' :
                            'text-destructive'
                          }`}>
                            {odooMetrics.summary.success_rate.toFixed(1)}%
                          </p>
                        </div>
                      </div>
                      
                      <div className="mt-6">
                        <h3 className="text-lg font-medium mb-3">UBL Transformation Performance</h3>
                        <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                          <p className="text-sm text-gray-500 mb-2">Common Transformation Issues</p>
                          {odooMetrics.common_errors.length > 0 ? (
                            <ul className="list-disc pl-5 space-y-1">
                              {odooMetrics.common_errors.slice(0, 3).map((error, index) => (
                                <li key={index} className="text-sm">
                                  {error.error_type} - {error.count} occurrences
                                </li>
                              ))}
                            </ul>
                          ) : (
                            <p className="text-sm">No transformation issues recorded.</p>
                          )}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </>
              ) : (
                <div className="text-center py-12">
                  <p>No Odoo integration data available. Try changing the filters or refreshing the page.</p>
                </div>
              )}
            </TabsContent>

            <TabsContent value="retries" className="space-y-6">
              {isDataLoading ? (
                <div className="flex justify-center items-center h-64">
                  <Loader2 className="h-8 w-8 animate-spin text-primary" />
                </div>
              ) : retryMetrics ? (
                <>
                  <RetryMetricsCard 
                    metrics={retryMetrics} 
                    title="Retry Analytics"
                    description="Performance metrics for the submission retry system"
                  />
                  
                  <Card>
                    <CardHeader>
                      <CardTitle>Retry System Health</CardTitle>
                      <CardDescription>Overall health and effectiveness of the retry system</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                          <div className="flex justify-between">
                            <div>
                              <h4 className="font-medium">Recovery Rate</h4>
                              <p className="text-gray-500 text-sm">Percentage of failed submissions recovered through retries</p>
                            </div>
                            <div className={`px-3 py-1 rounded-full text-sm font-medium ${
                              retryMetrics.metrics.success_rate >= 75 ? 'bg-green-100 text-green-700' :
                              retryMetrics.metrics.success_rate >= 50 ? 'bg-yellow-100 text-yellow-700' :
                              'bg-red-100 text-red-700'
                            }`}>
                              {retryMetrics.metrics.success_rate.toFixed(1)}%
                            </div>
                          </div>
                        </div>
                        
                        <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                          <div className="flex justify-between">
                            <div>
                              <h4 className="font-medium">Max Attempts Reached</h4>
                              <p className="text-gray-500 text-sm">Submissions that exhausted all retry attempts</p>
                            </div>
                            <div className="px-3 py-1 rounded-full text-sm font-medium bg-red-100 text-red-700">
                              {retryMetrics.metrics.max_attempts_reached_count} ({
                                ((retryMetrics.metrics.max_attempts_reached_count / retryMetrics.metrics.total_retries) * 100).toFixed(1)
                              }%)
                            </div>
                          </div>
                        </div>
                      </div>
                      
                      <div className="mt-6">
                        <h3 className="text-lg font-medium mb-3">Retry Actions</h3>
                        <div className="flex flex-col md:flex-row gap-4">
                          <Button 
                            variant="outline"
                            onClick={() => router.push('/retry-management/failed-submissions')}
                            className="flex-1"
                          >
                            View Failed Submissions
                          </Button>
                          
                          <Button 
                            variant="outline"
                            onClick={() => router.push('/retry-management/retry-config')}
                            className="flex-1"
                          >
                            Retry Configuration
                          </Button>
                        </div>
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
      </DashboardLayout>
    </>
  );
};

export default SubmissionDashboard;
