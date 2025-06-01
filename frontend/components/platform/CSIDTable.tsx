import React, { useState } from 'react';
import { format } from 'date-fns';
import { CSID, Certificate } from '../../types/app';
import apiService from '../../utils/apiService';
import { cn } from '../../utils/cn';

interface CSIDTableProps {
  csids: CSID[];
  certificates: Certificate[];
  onRefresh: () => void;
  className?: string;
}

const CSIDTable: React.FC<CSIDTableProps> = ({ 
  csids, 
  certificates,
  onRefresh,
  className = '' 
}) => {
  const [expandedCsidId, setExpandedCsidId] = useState<string | null>(null);
  const [loading, setLoading] = useState<{ [key: string]: boolean }>({});

  // Get certificate details for a given certificate ID
  const getCertificateDetails = (certificateId: string) => {
    const certificate = certificates.find(c => c.id === certificateId);
    return certificate ? `${certificate.subject} (${certificate.serial_number.slice(0, 8)}...)` : 'Unknown Certificate';
  };

  // Get status badge class
  const getStatusBadgeClass = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-green-100 text-green-800';
      case 'revoked':
        return 'bg-red-100 text-red-800';
      case 'expired':
        return 'bg-amber-100 text-amber-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  // Toggle expanded view for a CSID
  const toggleExpand = (csidId: string) => {
    if (expandedCsidId === csidId) {
      setExpandedCsidId(null);
    } else {
      setExpandedCsidId(csidId);
    }
  };

  // Handle CSID revocation
  const handleRevoke = async (csidId: string) => {
    if (confirm('Are you sure you want to revoke this CSID? This action cannot be undone.')) {
      try {
        setLoading(prev => ({ ...prev, [csidId]: true }));
        await apiService.post(`/api/v1/csids/${csidId}/revoke`, {
          reason: 'User requested revocation'
        });
        onRefresh();
      } catch (error) {
        console.error('Failed to revoke CSID:', error);
      } finally {
        setLoading(prev => ({ ...prev, [csidId]: false }));
      }
    }
  };

  // If there are no CSIDs, show a message
  if (csids.length === 0) {
    return (
      <div className={cn('text-center py-10', className)}>
        <p className="text-gray-600">No CSIDs found</p>
        <p className="text-sm text-gray-500 mt-2">
          CSIDs are automatically created when you receive a certificate and are used for secure transmissions
        </p>
      </div>
    );
  }

  return (
    <div className={cn('overflow-x-auto', className)}>
      <table className="min-w-full border-collapse">
        <thead className="bg-gray-50 text-left">
          <tr>
            <th className="px-4 py-3 text-sm font-medium text-gray-500">CSID</th>
            <th className="px-4 py-3 text-sm font-medium text-gray-500">Status</th>
            <th className="px-4 py-3 text-sm font-medium text-gray-500">Certificate</th>
            <th className="px-4 py-3 text-sm font-medium text-gray-500">Valid From</th>
            <th className="px-4 py-3 text-sm font-medium text-gray-500">Valid To</th>
            <th className="px-4 py-3 text-sm font-medium text-gray-500">Actions</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200 bg-white">
          {csids.map(csid => (
            <React.Fragment key={csid.id}>
              <tr className="text-sm text-gray-700 hover:bg-gray-50">
                <td className="px-4 py-3 font-mono">
                  {csid.csid_value.length > 16 
                    ? `${csid.csid_value.slice(0, 8)}...${csid.csid_value.slice(-8)}`
                    : csid.csid_value}
                </td>
                <td className="px-4 py-3">
                  <span className={cn('text-xs px-2 py-1 rounded-full', getStatusBadgeClass(csid.status))}>
                    {csid.status.charAt(0).toUpperCase() + csid.status.slice(1)}
                  </span>
                </td>
                <td className="px-4 py-3">
                  {getCertificateDetails(csid.certificate_id)}
                </td>
                <td className="px-4 py-3">
                  {format(new Date(csid.valid_from), 'dd MMM yyyy')}
                </td>
                <td className="px-4 py-3">
                  {format(new Date(csid.valid_to), 'dd MMM yyyy')}
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => toggleExpand(csid.id)}
                      className="text-blue-600 hover:text-blue-800 text-sm"
                    >
                      {expandedCsidId === csid.id ? 'Hide' : 'Details'}
                    </button>
                    
                    {csid.status === 'active' && (
                      <button
                        onClick={() => handleRevoke(csid.id)}
                        disabled={loading[csid.id]}
                        className="text-red-600 hover:text-red-800 text-sm disabled:opacity-50"
                      >
                        {loading[csid.id] ? 'Revoking...' : 'Revoke'}
                      </button>
                    )}
                    
                    <button
                      onClick={() => {
                        navigator.clipboard.writeText(csid.csid_value);
                      }}
                      className="text-gray-600 hover:text-gray-800 text-sm"
                      title="Copy CSID value"
                    >
                      Copy
                    </button>
                  </div>
                </td>
              </tr>
              
              {/* Expanded row for CSID details */}
              {expandedCsidId === csid.id && (
                <tr>
                  <td colSpan={6} className="px-4 py-3 bg-gray-50">
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <h4 className="font-medium text-gray-700">CSID Details</h4>
                        <div className="mt-2 space-y-1">
                          <p><span className="font-medium">ID:</span> <span className="font-mono">{csid.id}</span></p>
                          <p><span className="font-medium">CSID Value:</span> <span className="font-mono break-all">{csid.csid_value}</span></p>
                          <p><span className="font-medium">Status:</span> {csid.status.charAt(0).toUpperCase() + csid.status.slice(1)}</p>
                          <p><span className="font-medium">Created:</span> {format(new Date(csid.created_at), 'dd MMM yyyy HH:mm:ss')}</p>
                          <p><span className="font-medium">Last Updated:</span> {format(new Date(csid.updated_at), 'dd MMM yyyy HH:mm:ss')}</p>
                        </div>
                      </div>
                      <div>
                        <h4 className="font-medium text-gray-700">Validity Period</h4>
                        <div className="mt-2 space-y-1">
                          <p><span className="font-medium">Valid From:</span> {format(new Date(csid.valid_from), 'dd MMM yyyy HH:mm:ss')}</p>
                          <p><span className="font-medium">Valid To:</span> {format(new Date(csid.valid_to), 'dd MMM yyyy HH:mm:ss')}</p>
                          
                          {csid.status === 'revoked' && (
                            <>
                              <p><span className="font-medium">Revoked At:</span> {csid.revoked_at ? format(new Date(csid.revoked_at), 'dd MMM yyyy HH:mm:ss') : 'N/A'}</p>
                              <p><span className="font-medium">Revocation Reason:</span> {csid.revocation_reason || 'Not specified'}</p>
                            </>
                          )}
                        </div>
                        
                        {csid.metadata && Object.keys(csid.metadata).length > 0 && (
                          <div className="mt-4">
                            <h4 className="font-medium text-gray-700">Additional Information</h4>
                            <pre className="mt-2 bg-gray-100 p-2 rounded text-xs overflow-auto max-h-40">
                              {JSON.stringify(csid.metadata, null, 2)}
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

export default CSIDTable;
