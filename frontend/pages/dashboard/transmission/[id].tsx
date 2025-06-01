import React, { useState, useEffect } from 'react';
import { NextPage } from 'next';
import { useRouter } from 'next/router';
import Head from 'next/head';
import { useToast } from '../../../components/ui/Toast';
import { useAuth } from '../../../context/AuthContext';
import AppDashboardLayout from '../../../components/layouts/AppDashboardLayout';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../../components/ui/Card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../../components/ui/Tabs';
import { Badge } from '../../../components/ui/Badge';
import { Button } from '../../../components/ui/Button';
import { 
  CheckCircle2, 
  XCircle, 
  Clock, 
  AlertCircle, 
  RotateCw, 
  Ban,
  ArrowLeft, 
  RefreshCw,
  ExternalLink,
  Info,
  FileJson,
  History,
  AlertTriangle
} from 'lucide-react';
import transmissionApiService, { TransmissionDetail, TransmissionHistory, HistoryEvent } from '../../../services/transmissionApiService';
import RetryConfirmationDialog from '../../../components/platform/transmission/RetryConfirmationDialog';
import { formatDateTime } from '@/utils/formatters';

/**
 * Transmission Detail Page - Access Point Provider (APP) Feature
 * 
 * This page displays detailed information about a specific transmission
 * as part of the APP functionality. It shows transmission metadata,
 * status history, response data, and debugging information.
 */
const TransmissionDetailPage: NextPage = () => {
  const router = useRouter();
  const { id: queryId } = router.query;
  const id = Array.isArray(queryId) ? queryId[0] : queryId;
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  const toast = useToast();
  
  const [transmission, setTransmission] = useState<TransmissionDetail | null>(null);
  const [history, setHistory] = useState<HistoryEvent[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Retry dialog state
  const [isRetryDialogOpen, setIsRetryDialogOpen] = useState(false);
  const [isRetrying, setIsRetrying] = useState(false);

  // Redirect to login if not authenticated
  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/auth/login?redirect=' + encodeURIComponent(router.asPath));
    }
  }, [isAuthenticated, authLoading, router]);

  // Load transmission data - used for initial load and refreshing after actions
  const loadTransmissionData = async () => {
    try {
      if (!id) {
        setIsLoading(false);
        setError("No transmission ID provided");
        return;
      }
      
      setIsLoading(true);
      setError(null);
      
      // Fetch transmission details
      const transmissionResponse = await transmissionApiService.getTransmission(id as string);
      if (transmissionResponse.error) {
        throw new Error(transmissionResponse.error);
      }
      setTransmission(transmissionResponse.data);
      
      // Fetch transmission history
      const historyResponse = await transmissionApiService.getTransmissionHistory(id as string);
      if (historyResponse.error) {
        throw new Error(historyResponse.error);
      }
      if (historyResponse.data && historyResponse.data.history) {
        setHistory(historyResponse.data.history);
      } else {
        setHistory([]);
      }
    } catch (err) {
      console.error('Error loading transmission details:', err);
      setError('Failed to load transmission details. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };
  
  // Fetch transmission details
  useEffect(() => {
    if (id && isAuthenticated && !authLoading) {
      setIsLoading(true);
      setError(null);
      loadTransmissionData();
    }
  }, [id, isAuthenticated, authLoading]);

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'pending':
        return <Badge variant="outline" className="bg-amber-100 text-amber-800"><Clock className="h-3 w-3 mr-1" /> Pending</Badge>;
      case 'in_progress':
        return <Badge variant="outline" className="bg-blue-100 text-blue-800"><AlertCircle className="h-3 w-3 mr-1" /> In Progress</Badge>;
      case 'completed':
        return <Badge variant="outline" className="bg-green-100 text-green-800"><CheckCircle2 className="h-3 w-3 mr-1" /> Completed</Badge>;
      case 'failed':
        return <Badge variant="outline" className="bg-red-100 text-red-800"><XCircle className="h-3 w-3 mr-1" /> Failed</Badge>;
      case 'retrying':
        return <Badge variant="outline" className="bg-purple-100 text-purple-800"><RotateCw className="h-3 w-3 mr-1" /> Retrying</Badge>;
      case 'canceled':
        return <Badge variant="outline" className="bg-gray-100 text-gray-800"><Ban className="h-3 w-3 mr-1" /> Canceled</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  const formatDate = (dateStr?: string) => {
    if (!dateStr) return 'N/A';
    const date = new Date(dateStr);
    return date.toLocaleString();
  };

  // Handle retry action with configurable parameters
  const handleRetryConfirm = async (maxRetries: number, retryDelay: number, force: boolean) => {
    if (!id) return;
    
    try {
      setIsRetrying(true);
      const retryResponse = await transmissionApiService.retryTransmission(
        id as string,
        maxRetries,
        retryDelay,
        force
      );
      
      if (retryResponse.error) {
        throw new Error(retryResponse.error);
      }
      
      // Refresh the data
      await loadTransmissionData();
      
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
    }
  };

  const goBack = () => {
    router.push('/dashboard/transmission');
  };

  if (authLoading || (!transmission && isLoading)) {
    return (
      <AppDashboardLayout>
        <div className="flex justify-center items-center min-h-screen">
          <RefreshCw className="h-8 w-8 animate-spin text-gray-400" />
        </div>
      </AppDashboardLayout>
    );
  }

  if (error) {
    return (
      <AppDashboardLayout>
        <div className="p-6">
          <Card>
            <CardContent className="pt-6">
              <div className="flex flex-col items-center justify-center py-10">
                <AlertTriangle className="h-10 w-10 text-red-500 mb-4" />
                <h2 className="text-xl font-semibold mb-2">Error Loading Transmission</h2>
                <p className="text-gray-500 mb-4">{error}</p>
                <div className="flex gap-3">
                  <Button onClick={goBack}>
                    <ArrowLeft className="h-4 w-4 mr-2" />
                    Return to Dashboard
                  </Button>
                  <Button variant="outline" onClick={() => window.location.reload()}>
                    <RefreshCw className="h-4 w-4 mr-2" />
                    Retry
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </AppDashboardLayout>
    );
  }

  if (!transmission) {
    return (
      <AppDashboardLayout>
        <div className="p-6">
          <Card>
            <CardContent className="pt-6">
              <div className="flex flex-col items-center justify-center py-10">
                <Info className="h-10 w-10 text-amber-500 mb-4" />
                <h2 className="text-xl font-semibold mb-2">Transmission Not Found</h2>
                <p className="text-gray-500 mb-4">The requested transmission could not be found.</p>
                <Button onClick={goBack}>
                  <ArrowLeft className="h-4 w-4 mr-2" />
                  Return to Dashboard
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </AppDashboardLayout>
    );
  }

  return (
    <AppDashboardLayout>
      <Head>
        <title>Transmission Details | TaxPoynt e-Invoice</title>
      </Head>
      
      <div className="p-6">
        {/* Header with back button */}
        <div className="flex flex-col md:flex-row md:items-center justify-between mb-6">
          <div>
            <Button variant="ghost" onClick={goBack}>
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Transmissions
            </Button>
            <h1 className="text-2xl font-bold mt-2">Transmission Details</h1>
            <p className="text-gray-500">ID: {transmission.id}</p>
          </div>
          
          <div className="mt-4 md:mt-0">
            {(transmission.status === 'failed' || transmission.status === 'pending' || transmission.status === 'canceled') && (
              <Button
                variant="outline"
                size="sm"
                disabled={isRetrying}
                onClick={() => setIsRetryDialogOpen(true)}
                className="ml-auto"
              >
                {isRetrying ? (
                  <>
                    <RotateCw className="mr-2 h-4 w-4 animate-spin" />
                    Retrying...
                  </>
                ) : (
                  <>
                    <RotateCw className="mr-2 h-4 w-4" />
                    Retry Transmission
                  </>
                )}
              </Button>
            )}
          </div>
        </div>
        
        {/* Basic Info Card */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
          <Card>
            <CardHeader>
              <CardTitle>Transmission Status</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-col items-center justify-center">
                <div className="mb-4">
                  {getStatusBadge(transmission.status)}
                </div>
                <p className="text-sm text-gray-500">
                  Last Updated: {transmission.updated_at ? formatDate(transmission.updated_at) : 'N/A'}
                </p>
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader>
              <CardTitle>Invoice Information</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <div>
                  <span className="text-sm font-medium">Reference:</span>
                  <p>{transmission.invoice_reference || 'N/A'}</p>
                </div>
                <div>
                  <span className="text-sm font-medium">Created:</span>
                  <p>{transmission.created_at ? formatDate(transmission.created_at) : 'N/A'}</p>
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader>
              <CardTitle>Retry Stats</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <div>
                  <span className="text-sm font-medium">Total Attempts:</span>
                  <p>{transmission.retry_count + 1}</p>
                </div>
                <div>
                  <span className="text-sm font-medium">Last Retry:</span>
                  <p>{transmission.last_retry_time ? formatDateTime(transmission.last_retry_time) : 'N/A'}</p>
                </div>
                {transmission.status === 'retrying' && (
                  <div>
                    <span className="text-sm font-medium text-amber-600">Status:</span>
                    <p className="text-amber-600">Waiting for next retry attempt</p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
        
        {/* Tabs for Details, History, etc. */}
        <Tabs defaultValue="history" className="mt-6">
          <TabsList>
            <TabsTrigger value="history">
              <History className="h-4 w-4 mr-2" />
              History
            </TabsTrigger>
            <TabsTrigger value="retries">
              <RotateCw className="h-4 w-4 mr-2" />
              Retry History
            </TabsTrigger>
            <TabsTrigger value="metadata">
              <Info className="h-4 w-4 mr-2" />
              Metadata
            </TabsTrigger>
            <TabsTrigger value="response">
              <ExternalLink className="h-4 w-4 mr-2" />
              Response Data
            </TabsTrigger>
            <TabsTrigger value="debug">
              <FileJson className="h-4 w-4 mr-2" />
              Debug Info
            </TabsTrigger>
          </TabsList>
          
          {/* History Tab */}
          <TabsContent value="history">
            <Card>
              <CardHeader>
                <CardTitle>Transmission History</CardTitle>
                <CardDescription>
                  Timeline of events for this transmission
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-6">
                  {history.length === 0 ? (
                    <p className="text-center text-gray-500 py-4">No history records found</p>
                  ) : (
                    <div className="relative">
                      <div className="absolute h-full w-px bg-gray-200 left-2.5 top-0 z-0"></div>
                      <ul className="space-y-4 relative z-10">
                        {history.map((event, index) => (
                          <li key={index} className="flex items-start gap-4">
                            <div className="rounded-full h-5 w-5 bg-white border-2 border-gray-300 mt-1"></div>
                            <div className="flex-1">
                              <div className="flex flex-col sm:flex-row sm:items-center justify-between mb-1">
                                <div className="flex items-center">
                                  <h4 className="font-medium">{event.event}</h4>
                                  <div className="ml-2">
                                    {getStatusBadge(event.status)}
                                  </div>
                                </div>
                                <span className="text-sm text-gray-500">{formatDateTime(event.timestamp)}</span>
                              </div>
                              {event.details && (
                                <p className="text-sm text-gray-600">{event.details}</p>
                              )}
                            </div>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </TabsContent>
          
          {/* Retry History Tab */}
          <TabsContent value="retries" className="mt-2">
            <div className="p-4 bg-white rounded-md shadow-sm overflow-x-auto">
              <h3 className="text-lg font-medium mb-4">Retry Information</h3>
              
              {/* Basic retry information */}
              <dl className="grid grid-cols-1 gap-x-4 gap-y-6 sm:grid-cols-2 mb-6">
                <div>
                  <dt className="text-sm font-medium text-gray-500">Total Attempts</dt>
                  <dd className="mt-1 text-sm text-gray-900">{transmission.retry_count + 1}</dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500">Last Retry Time</dt>
                  <dd className="mt-1 text-sm text-gray-900">
                    {transmission.last_retry_time ? formatDateTime(transmission.last_retry_time) : 'Never'}
                  </dd>
                </div>
                {transmission.status === 'retrying' && (
                  <div className="col-span-2">
                    <dt className="text-sm font-medium text-amber-600">Current Status</dt>
                    <dd className="mt-1 text-sm text-amber-600">
                      <Clock className="inline-block h-4 w-4 mr-1" />
                      Waiting for next retry attempt
                    </dd>
                  </div>
                )}
              </dl>
              
              {/* Retry History Table */}
              {transmission.transmission_metadata?.retry_history && transmission.transmission_metadata.retry_history.length > 0 ? (
                <div>
                  <h4 className="text-md font-medium mb-2">Retry History</h4>
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead>
                        <tr>
                          <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Attempt</th>
                          <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Time</th>
                          <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Delay (s)</th>
                          <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Initiator</th>
                          <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Result</th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {transmission.transmission_metadata.retry_history.map((retry: any, index: number) => (
                          <tr key={index} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                            <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-900">{retry.attempt}</td>
                            <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-900">{formatDateTime(retry.timestamp)}</td>
                            <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-900">{retry.delay || 0}</td>
                            <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-900">{retry.initiator || 'System'}</td>
                            <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-900">
                              {retry.success ? (
                                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                                  <CheckCircle2 className="h-3 w-3 mr-1" /> Success
                                </span>
                              ) : (
                                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                                  <XCircle className="h-3 w-3 mr-1" /> Failed
                                </span>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              ) : (
                <p className="text-center text-gray-500 py-4">No retry history available</p>
              )}
              
              {/* Retry Strategy Information */}
              {transmission.transmission_metadata?.retry_strategy && (
                <div className="mt-6 pt-4 border-t border-gray-200">
                  <h4 className="text-md font-medium mb-2">Retry Strategy</h4>
                  <dl className="grid grid-cols-1 gap-x-4 gap-y-2 sm:grid-cols-3">
                    <div>
                      <dt className="text-sm font-medium text-gray-500">Max Retries</dt>
                      <dd className="text-sm text-gray-900">{transmission.transmission_metadata.retry_strategy.max_retries || 3}</dd>
                    </div>
                    <div>
                      <dt className="text-sm font-medium text-gray-500">Base Delay (s)</dt>
                      <dd className="text-sm text-gray-900">{transmission.transmission_metadata.retry_strategy.retry_delay || 0}</dd>
                    </div>
                    <div>
                      <dt className="text-sm font-medium text-gray-500">Backoff Type</dt>
                      <dd className="text-sm text-gray-900">Exponential</dd>
                    </div>
                  </dl>
                </div>
              )}
            </div>
          </TabsContent>
          
          {/* Metadata Tab */}
          <TabsContent value="metadata" className="mt-2">
            <Card>
              <CardHeader>
                <CardTitle>Transmission Metadata</CardTitle>
                <CardDescription>
                  Additional information about this transmission
                </CardDescription>
              </CardHeader>
              <CardContent>
                <pre className="bg-gray-100 p-4 rounded-lg overflow-auto max-h-96 text-sm">
                  {transmission.metadata ? JSON.stringify(transmission.metadata, null, 2) : 'No metadata available'}
                </pre>
              </CardContent>
            </Card>
          </TabsContent>
          
          {/* Response Data Tab */}
          <TabsContent value="response">
            <Card>
              <CardHeader>
                <CardTitle>Response Data</CardTitle>
                <CardDescription>
                  Data received from the API endpoint
                </CardDescription>
              </CardHeader>
              <CardContent>
                <pre className="bg-gray-100 p-4 rounded-lg overflow-auto max-h-96 text-sm">
                  {transmission.response_data ? JSON.stringify(transmission.response_data, null, 2) : 'No response data available'}
                </pre>
              </CardContent>
            </Card>
          </TabsContent>
          
          {/* Debug Info Tab */}
          <TabsContent value="debug">
            <Card>
              <CardHeader>
                <CardTitle>Debug Information</CardTitle>
                <CardDescription>
                  Technical details for troubleshooting
                </CardDescription>
              </CardHeader>
              <CardContent>
                <pre className="bg-gray-100 p-4 rounded-lg overflow-auto max-h-96 text-sm">
                  {transmission.debug_info ? JSON.stringify(transmission.debug_info, null, 2) : 'No debug information available'}
                </pre>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </AppDashboardLayout>
  );
};

export default TransmissionDetailPage;
