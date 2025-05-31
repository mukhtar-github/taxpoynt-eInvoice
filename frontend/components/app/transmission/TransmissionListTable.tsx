import React from 'react';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../ui/Table';
import { TransmissionListItem } from '../../../services/transmissionApiService';
import { Badge } from '../../ui/Badge';
import { Button } from '../../ui/Button';
import { useRouter } from 'next/router';
import { 
  CheckCircle2, 
  XCircle, 
  Clock, 
  AlertCircle, 
  RotateCw, 
  Ban,
  ExternalLink,
  RefreshCw
} from 'lucide-react';

interface TransmissionListTableProps {
  transmissions: TransmissionListItem[];
  onRetry?: (id: string) => void;
  onViewDetails?: (id: string) => void;
  isLoading?: boolean;
}

const TransmissionListTable: React.FC<TransmissionListTableProps> = ({ 
  transmissions, 
  onRetry,
  onViewDetails,
  isLoading = false
}) => {
  const router = useRouter();

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

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleString();
  };
  
  const viewDetails = (id: string) => {
    if (onViewDetails) {
      onViewDetails(id);
    } else {
      router.push(`/dashboard/transmission/${id}`);
    }
  };

  const handleRetry = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (onRetry) {
      onRetry(id);
    }
  };

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-60">
        <RefreshCw className="h-8 w-8 animate-spin text-gray-400" />
      </div>
    );
  }

  return (
    <div className="rounded-md border">
      <Table>
        <TableHead>
          <TableRow>
            <TableHeader>ID</TableHeader>
            <TableHeader>Organization</TableHeader>
            <TableHeader>Status</TableHeader>
            <TableHeader>Transmission Time</TableHeader>
            <TableHeader>Retry Count</TableHeader>
            <TableHeader className="text-right">Actions</TableHeader>
          </TableRow>
        </TableHead>
        <TableBody>
          {transmissions.length === 0 ? (
            <TableRow>
              <TableCell colSpan={6} className="text-center py-6 text-gray-500">
                No transmissions found
              </TableCell>
            </TableRow>
          ) : (
            transmissions.map((transmission) => (
              <TableRow 
                key={transmission.id} 
                className="cursor-pointer hover:bg-gray-50"
                onClick={() => viewDetails(transmission.id)}
              >
                <TableCell className="font-medium">{transmission.id.substring(0, 8)}...</TableCell>
                <TableCell>{transmission.organization_id.substring(0, 8)}...</TableCell>
                <TableCell>{getStatusBadge(transmission.status)}</TableCell>
                <TableCell>{formatDate(transmission.transmission_time)}</TableCell>
                <TableCell>{transmission.retry_count}</TableCell>
                <TableCell className="text-right">
                  <div className="flex justify-end gap-2">
                    <Button 
                      variant="outline" 
                      size="sm"
                      onClick={() => viewDetails(transmission.id)}
                    >
                      <ExternalLink className="h-4 w-4 mr-1" />
                      Details
                    </Button>
                    {(transmission.status === 'failed' || transmission.status === 'canceled') && onRetry && (
                      <Button 
                        variant="outline" 
                        size="sm"
                        onClick={(e) => handleRetry(transmission.id, e)}
                      >
                        <RefreshCw className="h-4 w-4 mr-1" />
                        Retry
                      </Button>
                    )}
                  </div>
                </TableCell>
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>
    </div>
  );
};

export default TransmissionListTable;
