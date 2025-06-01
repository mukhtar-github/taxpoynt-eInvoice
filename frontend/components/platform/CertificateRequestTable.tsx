import React, { useState } from 'react';
import { format } from 'date-fns';
import { CertificateRequest } from '../../types/app';
import apiService from '../../utils/apiService';
import { cn } from '../../utils/cn';

interface CertificateRequestTableProps {
  requests: CertificateRequest[];
  onRefresh: () => void;
  className?: string;
}

const CertificateRequestTable: React.FC<CertificateRequestTableProps> = ({ 
  requests, 
  onRefresh,
  className = '' 
}) => {
  const [expandedRequestId, setExpandedRequestId] = useState<string | null>(null);
  const [loading, setLoading] = useState<{ [key: string]: boolean }>({});

  // Get status badge class for visual indicator
  const getStatusBadgeClass = (status: string) => {
    switch (status) {
      case 'pending':
        return 'bg-yellow-100 text-yellow-800';
      case 'approved':
        return 'bg-blue-100 text-blue-800';
      case 'issued':
        return 'bg-green-100 text-green-800';
      case 'rejected':
        return 'bg-red-100 text-red-800';
      case 'canceled':
        return 'bg-gray-100 text-gray-800';
      case 'error':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  // Get request type display name
  const getRequestTypeDisplay = (type: string) => {
    switch (type) {
      case 'new':
        return 'New Certificate';
      case 'renewal':
        return 'Certificate Renewal';
      case 'replacement':
        return 'Certificate Replacement';
      case 'revocation':
        return 'Certificate Revocation';
      default:
        return type.charAt(0).toUpperCase() + type.slice(1);
    }
  };
  
  // Cancel a certificate request
  const handleCancel = async (requestId: string) => {
    if (confirm('Are you sure you want to cancel this certificate request?')) {
      try {
        setLoading(prev => ({ ...prev, [requestId]: true }));
        await apiService.post(`/api/v1/certificate-requests/${requestId}/cancel`);
        onRefresh();
      } catch (error) {
        console.error('Failed to cancel certificate request:', error);
      } finally {
        setLoading(prev => ({ ...prev, [requestId]: false }));
      }
    }
  };
  
  // Toggle expanded view for a request
  const toggleExpand = (requestId: string) => {
    if (expandedRequestId === requestId) {
      setExpandedRequestId(null);
    } else {
      setExpandedRequestId(requestId);
    }
  };

  // If there are no requests, show a message
  if (requests.length === 0) {
    return (
      <div className={cn('text-center py-10', className)}>
        <p className="text-gray-600">No certificate requests found</p>
      </div>
    );
  }

  return (
    <div className={cn('overflow-x-auto', className)}>
      <table className="min-w-full border-collapse">
        <thead className="bg-gray-50 text-left">
          <tr>
            <th className="px-4 py-3 text-sm font-medium text-gray-500">Type</th>
            <th className="px-4 py-3 text-sm font-medium text-gray-500">Status</th>
            <th className="px-4 py-3 text-sm font-medium text-gray-500">Subject</th>
            <th className="px-4 py-3 text-sm font-medium text-gray-500">Created</th>
            <th className="px-4 py-3 text-sm font-medium text-gray-500">Updated</th>
            <th className="px-4 py-3 text-sm font-medium text-gray-500">Actions</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200 bg-white">
          {requests.map(request => (
            <React.Fragment key={request.id}>
              <tr className="text-sm text-gray-700 hover:bg-gray-50">
                <td className="px-4 py-3">
                  <span className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded-full">
                    {getRequestTypeDisplay(request.request_type)}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <span className={cn('text-xs px-2 py-1 rounded-full', getStatusBadgeClass(request.status))}>
                    {request.status.charAt(0).toUpperCase() + request.status.slice(1)}
                  </span>
                </td>
                <td className="px-4 py-3">
                  {request.subject_info?.common_name || 'N/A'}
                </td>
                <td className="px-4 py-3">
                  {format(new Date(request.created_at), 'dd MMM yyyy')}
                </td>
                <td className="px-4 py-3">
                  {format(new Date(request.updated_at), 'dd MMM yyyy')}
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => toggleExpand(request.id)}
                      className="text-blue-600 hover:text-blue-800 text-sm"
                    >
                      {expandedRequestId === request.id ? 'Hide' : 'Details'}
                    </button>
                    
                    {request.status === 'pending' && (
                      <button
                        onClick={() => handleCancel(request.id)}
                        disabled={loading[request.id]}
                        className="text-red-600 hover:text-red-800 text-sm disabled:opacity-50"
                      >
                        {loading[request.id] ? 'Cancelling...' : 'Cancel'}
                      </button>
                    )}
                  </div>
                </td>
              </tr>
              
              {/* Expanded row for request details */}
              {expandedRequestId === request.id && (
                <tr>
                  <td colSpan={6} className="px-4 py-3 bg-gray-50">
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <h4 className="font-medium text-gray-700">Subject Information</h4>
                        <div className="mt-2 space-y-1">
                          <p><span className="font-medium">Common Name:</span> {request.subject_info.common_name}</p>
                          <p><span className="font-medium">Organization:</span> {request.subject_info.organization}</p>
                          {request.subject_info.organizational_unit && (
                            <p><span className="font-medium">Organizational Unit:</span> {request.subject_info.organizational_unit}</p>
                          )}
                          <p><span className="font-medium">Country:</span> {request.subject_info.country}</p>
                          {request.subject_info.state && (
                            <p><span className="font-medium">State/Province:</span> {request.subject_info.state}</p>
                          )}
                          {request.subject_info.locality && (
                            <p><span className="font-medium">Locality:</span> {request.subject_info.locality}</p>
                          )}
                          {request.subject_info.email && (
                            <p><span className="font-medium">Email:</span> {request.subject_info.email}</p>
                          )}
                        </div>
                      </div>
                      <div>
                        <h4 className="font-medium text-gray-700">Certificate Details</h4>
                        <div className="mt-2 space-y-1">
                          <p>
                            <span className="font-medium">Certificate Type:</span>{' '}
                            {request.certificate_type.charAt(0).toUpperCase() + request.certificate_type.slice(1)}
                          </p>
                          <p><span className="font-medium">Key Size:</span> {request.key_size} bits</p>
                          <p><span className="font-medium">Key Algorithm:</span> {request.key_algorithm}</p>
                          {request.comment && (
                            <p><span className="font-medium">Comment:</span> {request.comment}</p>
                          )}
                          {request.certificate_id && (
                            <p>
                              <span className="font-medium">Certificate ID:</span>{' '}
                              <span className="font-mono text-xs">{request.certificate_id}</span>
                            </p>
                          )}
                        </div>
                        {request.metadata && Object.keys(request.metadata).length > 0 && (
                          <div className="mt-4">
                            <h4 className="font-medium text-gray-700">Additional Information</h4>
                            <pre className="mt-2 bg-gray-100 p-2 rounded text-xs overflow-auto max-h-40">
                              {JSON.stringify(request.metadata, null, 2)}
                            </pre>
                          </div>
                        )}
                      </div>
                    </div>
                  </td>
                </tr>
              )}
            </React.Fragment>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default CertificateRequestTable;
