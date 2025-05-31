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

/**
 * Transmission Detail Page - Access Point Provider (APP) Feature
 * 
 * This page displays detailed information about a specific transmission
 * as part of the APP functionality. It shows transmission metadata,
 * status history, response data, and debugging information.
 */
const TransmissionDetailPage: NextPage = () => {
  const router = useRouter();
  const { id } = router.query;
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  const toast = useToast();
  
  const [transmission, setTransmission] = useState<TransmissionDetail | null>(null);
  const [history, setHistory] = useState<HistoryEvent[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRetrying, setIsRetrying] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Redirect to login if not authenticated
  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/auth/login?redirect=' + encodeURIComponent(router.asPath));
    }
  }, [isAuthenticated, authLoading, router]);

  // Fetch transmission details
  useEffect(() => {
    const fetchTransmissionDetails = async () => {
      if (id && typeof id === 'string' && isAuthenticated) {
        setIsLoading(true);
        setError(null);
        
        try {
          // Fetch transmission details
          const transmissionResponse = await transmissionApiService.getTransmission(id);
          if (transmissionResponse.error) {
            throw new Error(transmissionResponse.error);
          }
          setTransmission(transmissionResponse.data);
          
          // Fetch transmission history
          const historyResponse = await transmissionApiService.getTransmissionHistory(id);
          if (historyResponse.error) {
            throw new Error(historyResponse.error);
          }
          if (historyResponse.data && historyResponse.data.history) {
            setHistory(historyResponse.data.history);
          } else {
            setHistory([]);
          }
        } catch (err) {
          console.error('Error fetching transmission details:', err);
          setError('Failed to load transmission details. Please try again.');
        } finally {
          setIsLoading(false);
        }
      }
    };

    fetchTransmissionDetails();
  }, [id, isAuthenticated]);

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

  const handleRetry = async () => {
    if (!transmission) return;
    
    setIsRetrying(true);
    try {
      const retryResponse = await transmissionApiService.retryTransmission(transmission.id);
      if (retryResponse.error) {
        throw new Error(retryResponse.error);
      }
      
      // Refetch the transmission data
      const updatedTransmissionResponse = await transmissionApiService.getTransmission(transmission.id);
      if (updatedTransmissionResponse.error) {
        throw new Error(updatedTransmissionResponse.error);
      }
      setTransmission(updatedTransmissionResponse.data);
      
      // Fetch updated history
      const updatedHistoryResponse = await transmissionApiService.getTransmissionHistory(transmission.id);
      if (updatedHistoryResponse.error) {
        throw new Error(updatedHistoryResponse.error);
      }
      if (updatedHistoryResponse.data && updatedHistoryResponse.data.history) {
        setHistory(updatedHistoryResponse.data.history);
      } else {
        setHistory([]);
      }
      
      toast({
        title: "Transmission Retry Initiated",
        description: "The system is attempting to resend the transmission.",
        status: "success"
      });
    } catch (err) {
      console.error('Error retrying transmission:', err);
      toast({
        title: "Retry Failed",
        description: "Failed to retry the transmission. Please try again.",
        status: "error"
      });
    } finally {
      setIsRetrying(false);
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
            {(transmission.status === 'failed' || transmission.status === 'canceled') && (
              <Button 
                onClick={handleRetry} 
                disabled={isRetrying}
              >
                {isRetrying ? (
                  <>
                    <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                    Retrying...
                  </>
                ) : (
                  <>
                    <RefreshCw className="h-4 w-4 mr-2" />
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
              <CardTitle>Transmission Stats</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <div>
                  <span className="text-sm font-medium">Attempts:</span>
                  <p>{transmission.retry_count + 1}</p>
                </div>
                <div>
                  <span className="text-sm font-medium">Last Attempt:</span>
                  <p>{transmission.last_retry_at ? formatDate(transmission.last_retry_at) : 'N/A'}</p>
                </div>
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
                                <span className="text-sm text-gray-500">{formatDate(event.timestamp)}</span>
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
          
          {/* Metadata Tab */}
          <TabsContent value="metadata">
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
