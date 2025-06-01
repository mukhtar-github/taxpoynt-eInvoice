import React, { useState, useEffect } from 'react';
import { useToast } from '@/components/ui/Toast';
import { Button } from '@/components/ui/Button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/Table';
import { Modal, ModalHeader, ModalBody, ModalFooter } from '@/components/ui/Modal';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/Alert';
import { Loader2, RefreshCw, Shield, CheckCircle, XCircle, Clock, ArrowUpRight } from 'lucide-react';
import axios from 'axios';

// Types for transmission data
interface TransmissionRecord {
  id: string;
  status: string;
  organization_id: string;
  transmission_time: string;
  destination: string;
  retry_count: number;
  last_retry_time?: string;
  destination_endpoint?: string;
  certificate_id?: string;
}

interface TransmissionStatus {
  transmission_id: string;
  status: string;
  last_updated: string;
  retry_count?: number;
  retry_history?: any[];
  verification_status?: string;
  firs_status?: any;
  error?: string;
}

interface TransmissionReceipt {
  receipt_id: string;
  transmission_id: string;
  timestamp: string;
  verification_status: string;
  receipt_data: any;
}

interface SecureTransmissionManagerProps {
  organizationId: string;
}

const SecureTransmissionManager: React.FC<SecureTransmissionManagerProps> = ({ organizationId }) => {
  const toast = useToast();
  const [transmissions, setTransmissions] = useState<TransmissionRecord[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [selectedTransmission, setSelectedTransmission] = useState<TransmissionRecord | null>(null);
  const [detailsOpen, setDetailsOpen] = useState<boolean>(false);
  const [receiptOpen, setReceiptOpen] = useState<boolean>(false);
  const [statusDetails, setStatusDetails] = useState<TransmissionStatus | null>(null);
  const [receiptDetails, setReceiptDetails] = useState<TransmissionReceipt | null>(null);
  const [statusLoading, setStatusLoading] = useState<boolean>(false);
  const [retryLoading, setRetryLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch transmissions on component mount
  useEffect(() => {
    fetchTransmissions();
  }, [organizationId]);

  // Function to fetch transmissions from API
  const fetchTransmissions = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`/api/v1/transmissions?organization_id=${organizationId}`, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      });
      
      setTransmissions(response.data);
    } catch (err) {
      if (axios.isAxiosError(err)) {
        const errorMsg = err.response?.data?.detail || 'Failed to fetch transmissions';
        setError(errorMsg);
        toast({
          title: 'Error',
          description: errorMsg,
          status: 'error',
        });
      } else {
        setError('An unexpected error occurred');
        toast({
          title: 'Error',
          description: 'An unexpected error occurred while fetching transmissions',
          status: 'error',
        });
      }
    } finally {
      setLoading(false);
    }
  };

  // Function to check transmission status
  const checkTransmissionStatus = async (transmissionId: string) => {
    setStatusLoading(true);
    
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`/api/v1/transmissions/${transmissionId}/status`, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      });
      
      setStatusDetails(response.data);
      setDetailsOpen(true);
    } catch (err) {
      if (axios.isAxiosError(err)) {
        const errorMsg = err.response?.data?.detail || 'Failed to fetch transmission status';
        toast({
          title: 'Error',
          description: errorMsg,
          status: 'error',
        });
      } else {
        toast({
          title: 'Error',
          description: 'An unexpected error occurred while fetching status',
          status: 'error',
        });
      }
    } finally {
      setStatusLoading(false);
    }
  };

  // Function to retry transmission
  const retryTransmission = async (transmissionId: string) => {
    setRetryLoading(true);
    
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(`/api/v1/transmissions/${transmissionId}/retry`, {}, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      });
      
      toast({
        title: 'Success',
        description: 'Transmission retry initiated successfully',
        status: 'success',
      });
      
      // Update the status in our list
      setTransmissions(prevTransmissions => 
        prevTransmissions.map(t => 
          t.id === transmissionId ? { ...t, status: 'retrying' } : t
        )
      );
      
      // If details modal is open, fetch updated status
      if (detailsOpen && selectedTransmission?.id === transmissionId) {
        await checkTransmissionStatus(transmissionId);
      }
    } catch (err) {
      if (axios.isAxiosError(err)) {
        const errorMsg = err.response?.data?.detail || 'Failed to retry transmission';
        toast({
          title: 'Error',
          description: errorMsg,
          status: 'error',
        });
      } else {
        toast({
          title: 'Error',
          description: 'An unexpected error occurred while retrying',
          status: 'error',
        });
      }
    } finally {
      setRetryLoading(false);
    }
  };

  // Function to fetch receipt
  const fetchReceipt = async (transmissionId: string) => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`/api/v1/transmissions/${transmissionId}/receipt`, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      });
      
      setReceiptDetails(response.data);
      setReceiptOpen(true);
    } catch (err) {
      if (axios.isAxiosError(err)) {
        const errorMsg = err.response?.data?.detail || 'No receipt available for this transmission';
        toast({
          title: 'Information',
          description: errorMsg,
          status: 'info',
        });
      } else {
        toast({
          title: 'Error',
          description: 'An unexpected error occurred while fetching receipt',
          status: 'error',
        });
      }
    }
  };

  // Function to get status badge color
  const getStatusBadge = (status: string) => {
    switch(status.toLowerCase()) {
      case 'completed':
        return <Badge className="bg-green-500"><CheckCircle className="w-3 h-3 mr-1" /> {status}</Badge>;
      case 'failed':
        return <Badge className="bg-red-500"><XCircle className="w-3 h-3 mr-1" /> {status}</Badge>;
      case 'pending':
        return <Badge className="bg-yellow-500"><Clock className="w-3 h-3 mr-1" /> {status}</Badge>;
      case 'in_progress':
        return <Badge className="bg-blue-500"><Loader2 className="w-3 h-3 mr-1 animate-spin" /> {status}</Badge>;
      case 'retrying':
        return <Badge className="bg-purple-500"><RefreshCw className="w-3 h-3 mr-1" /> {status}</Badge>;
      default:
        return <Badge>{status}</Badge>;
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold">Secure Transmissions</h2>
          <p className="text-gray-500">Manage and monitor secure FIRS transmissions</p>
        </div>
        <div className="flex gap-2">
          <Button 
            variant="outline" 
            onClick={fetchTransmissions}
            disabled={loading}
          >
            {loading ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <RefreshCw className="h-4 w-4 mr-2" />}
            Refresh
          </Button>
        </div>
      </div>

      <Card className="border-l-4 border-cyan-500">
        <CardHeader>
          <div className="flex justify-between items-center">
            <div>
              <CardTitle>Transmission Records</CardTitle>
              <CardDescription>Secure data transmissions to FIRS</CardDescription>
            </div>
            <Badge variant="outline" className="border-cyan-500 text-cyan-500">
              <Shield className="w-3 h-3 mr-1" /> Platform
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          {error && (
            <Alert variant="error" className="mb-4">
              <AlertTitle>Error</AlertTitle>
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {loading ? (
            <div className="flex justify-center items-center py-8">
              <Loader2 className="h-8 w-8 animate-spin text-cyan-500" />
            </div>
          ) : transmissions.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              No transmission records found
            </div>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>ID</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Destination</TableHead>
                    <TableHead>Transmitted</TableHead>
                    <TableHead>Retries</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {transmissions.map((transmission) => (
                    <TableRow key={transmission.id}>
                      <TableCell className="font-mono text-xs">{transmission.id.substring(0, 8)}...</TableCell>
                      <TableCell>{getStatusBadge(transmission.status)}</TableCell>
                      <TableCell>{transmission.destination}</TableCell>
                      <TableCell>{new Date(transmission.transmission_time).toLocaleString()}</TableCell>
                      <TableCell>{transmission.retry_count}</TableCell>
                      <TableCell className="text-right">
                        <div className="flex justify-end gap-2">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => {
                              setSelectedTransmission(transmission);
                              checkTransmissionStatus(transmission.id);
                            }}
                            disabled={statusLoading && selectedTransmission?.id === transmission.id}
                          >
                            {statusLoading && selectedTransmission?.id === transmission.id ? (
                              <Loader2 className="h-4 w-4 mr-1 animate-spin" />
                            ) : (
                              <ArrowUpRight className="h-4 w-4 mr-1" />
                            )}
                            Details
                          </Button>
                          
                          {transmission.status === 'completed' && (
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => {
                                setSelectedTransmission(transmission);
                                fetchReceipt(transmission.id);
                              }}
                            >
                              <CheckCircle className="h-4 w-4 mr-1" />
                              Receipt
                            </Button>
                          )}
                          
                          {(transmission.status === 'failed' || transmission.status === 'pending') && (
                            <Button
                              size="sm"
                              variant="outline"
                              className="border-red-500 text-red-500 hover:bg-red-50"
                              onClick={() => retryTransmission(transmission.id)}
                              disabled={retryLoading && selectedTransmission?.id === transmission.id}
                            >
                              {retryLoading && selectedTransmission?.id === transmission.id ? (
                                <Loader2 className="h-4 w-4 mr-1 animate-spin" />
                              ) : (
                                <RefreshCw className="h-4 w-4 mr-1" />
                              )}
                              Retry
                            </Button>
                          )}
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Status Details Modal */}
      {selectedTransmission && (
        <Modal isOpen={detailsOpen} onClose={() => setDetailsOpen(false)} size="lg">
            <ModalHeader>
              <h3 className="text-lg font-semibold">Transmission Details</h3>
            </ModalHeader>
            <ModalBody>
              {statusDetails ? (
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm text-gray-500">Transmission ID</p>
                      <p className="font-mono text-xs">{statusDetails.transmission_id}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500">Status</p>
                      <p>{getStatusBadge(statusDetails.status)}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500">Last Updated</p>
                      <p>{new Date(statusDetails.last_updated).toLocaleString()}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500">Retry Count</p>
                      <p>{statusDetails.retry_count || 0}</p>
                    </div>
                  </div>

                  {statusDetails.firs_status && (
                    <div className="mt-4">
                      <h4 className="text-md font-semibold mb-2">FIRS Status</h4>
                      <Card>
                        <CardContent className="p-4">
                          <pre className="text-xs overflow-auto bg-gray-50 p-2 rounded">
                            {JSON.stringify(statusDetails.firs_status, null, 2)}
                          </pre>
                        </CardContent>
                      </Card>
                    </div>
                  )}

                  {statusDetails.retry_history && statusDetails.retry_history.length > 0 && (
                    <div className="mt-4">
                      <h4 className="text-md font-semibold mb-2">Retry History</h4>
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>Attempt</TableHead>
                            <TableHead>Time</TableHead>
                            <TableHead>Status</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {statusDetails.retry_history.map((retry, index) => (
                            <TableRow key={index}>
                              <TableCell>{retry.attempt}</TableCell>
                              <TableCell>{new Date(retry.timestamp).toLocaleString()}</TableCell>
                              <TableCell>{retry.status}</TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </div>
                  )}

                  {statusDetails.error && (
                    <Alert variant="error" className="mt-4">
                      <AlertTitle>Error</AlertTitle>
                      <AlertDescription>{statusDetails.error}</AlertDescription>
                    </Alert>
                  )}
                </div>
              ) : (
                <div className="flex justify-center items-center py-8">
                  <Loader2 className="h-8 w-8 animate-spin text-cyan-500" />
                </div>
              )}
            </ModalBody>
            <ModalFooter>
              {selectedTransmission.status === 'failed' && (
                <Button 
                  variant="outline" 
                  className="border-red-500 text-red-500 hover:bg-red-50 mr-2"
                  onClick={() => retryTransmission(selectedTransmission.id)}
                  disabled={retryLoading}
                >
                  {retryLoading ? (
                    <Loader2 className="h-4 w-4 mr-1 animate-spin" />
                  ) : (
                    <RefreshCw className="h-4 w-4 mr-1" />
                  )}
                  Retry Transmission
                </Button>
              )}
              <Button variant="outline" onClick={() => setDetailsOpen(false)}>
                Close
              </Button>
            </ModalFooter>
        </Modal>
      )}

      {/* Receipt Modal */}
      {selectedTransmission && (
        <Modal isOpen={receiptOpen} onClose={() => setReceiptOpen(false)} size="lg">
            <ModalHeader>
              <h3 className="text-lg font-semibold">Transmission Receipt</h3>
            </ModalHeader>
            <ModalBody>
              {receiptDetails ? (
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm text-gray-500">Receipt ID</p>
                      <p className="font-mono text-xs">{receiptDetails.receipt_id}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500">Verification</p>
                      <p>{receiptDetails.verification_status === 'verified' ? (
                        <Badge className="bg-green-500"><CheckCircle className="w-3 h-3 mr-1" />Verified</Badge>
                      ) : (
                        <Badge>{receiptDetails.verification_status}</Badge>
                      )}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500">Timestamp</p>
                      <p>{new Date(receiptDetails.timestamp).toLocaleString()}</p>
                    </div>
                  </div>

                  <div className="mt-4">
                    <h4 className="text-md font-semibold mb-2">Receipt Data</h4>
                    <Card>
                      <CardContent className="p-4">
                        <pre className="text-xs overflow-auto bg-gray-50 p-2 rounded">
                          {JSON.stringify(receiptDetails.receipt_data, null, 2)}
                        </pre>
                      </CardContent>
                    </Card>
                  </div>
                </div>
              ) : (
                <div className="flex justify-center items-center py-8">
                  <Loader2 className="h-8 w-8 animate-spin text-cyan-500" />
                </div>
              )}
            </ModalBody>
            <ModalFooter>
              <Button variant="outline" onClick={() => setReceiptOpen(false)}>
                Close
              </Button>
            </ModalFooter>
        </Modal>
      )}
    </div>
  );
};

export default SecureTransmissionManager;
