import React from 'react';
import { Badge } from '../../ui/Badge';
import { Card, CardContent } from '../../ui/Card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../ui/Table';
import { Alert, AlertDescription, AlertTitle } from '../../ui/Alert';
import { CheckCircle, XCircle, Clock, Loader2, RefreshCw, AlertCircle } from 'lucide-react';

interface TransmissionDetailsProps {
  status: {
    transmission_id: string;
    status: string;
    last_updated: string;
    retry_count?: number;
    retry_history?: any[];
    verification_status?: string;
    firs_status?: any;
    error?: string;
  };
}

const TransmissionDetails: React.FC<TransmissionDetailsProps> = ({ status }) => {
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
      <div className="grid grid-cols-2 gap-4">
        <div>
          <p className="text-sm text-gray-500">Transmission ID</p>
          <p className="font-mono text-xs">{status.transmission_id}</p>
        </div>
        <div>
          <p className="text-sm text-gray-500">Status</p>
          <p>{getStatusBadge(status.status)}</p>
        </div>
        <div>
          <p className="text-sm text-gray-500">Last Updated</p>
          <p>{new Date(status.last_updated).toLocaleString()}</p>
        </div>
        <div>
          <p className="text-sm text-gray-500">Retry Count</p>
          <p>{status.retry_count || 0}</p>
        </div>
        {status.verification_status && (
          <div>
            <p className="text-sm text-gray-500">Verification Status</p>
            <p>{status.verification_status === 'verified' ? (
              <Badge className="bg-green-500"><CheckCircle className="w-3 h-3 mr-1" />Verified</Badge>
            ) : (
              <Badge>{status.verification_status}</Badge>
            )}</p>
          </div>
        )}
      </div>

      {status.firs_status && (
        <div className="mt-4">
          <h4 className="text-md font-semibold mb-2">FIRS Status</h4>
          <Card>
            <CardContent className="p-4">
              <pre className="text-xs overflow-auto bg-gray-50 p-2 rounded">
                {JSON.stringify(status.firs_status, null, 2)}
              </pre>
            </CardContent>
          </Card>
        </div>
      )}

      {status.retry_history && status.retry_history.length > 0 && (
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
              {status.retry_history.map((retry, index) => (
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

      {status.error && (
        <Alert variant="error" className="mt-4">
          <AlertCircle className="h-4 w-4 mr-2" />
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>{status.error}</AlertDescription>
        </Alert>
      )}
    </div>
  );
};

export default TransmissionDetails;
