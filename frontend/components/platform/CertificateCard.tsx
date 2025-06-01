import React, { useState } from 'react';
import { format } from 'date-fns';
import { Download, XCircle, ChevronDown, ChevronUp } from 'lucide-react';
import { Card, CardContent } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';
import { Certificate } from '../../types/app';
import apiService from '../../utils/apiService';
import { cn } from '../../utils/cn';

interface CertificateCardProps {
  certificate: Certificate;
  onRefresh: () => void;
  onRevoke?: (certificate: Certificate) => void;
  className?: string;
}

const CertificateCard: React.FC<CertificateCardProps> = ({ 
  certificate, 
  onRefresh,
  onRevoke,
  className = '' 
}) => {
  const [isExpanded, setIsExpanded] = useState<boolean>(false);
  const [isDownloading, setIsDownloading] = useState<boolean>(false);
  const [isRevoking, setIsRevoking] = useState<boolean>(false);

  // Calculate days until expiry
  const validTo = new Date(certificate.valid_to);
  const today = new Date();
  const daysUntilExpiry = Math.floor((validTo.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));
  
  // Get status class for visual indicator
  const getStatusClass = () => {
    switch (certificate.status) {
      case 'active':
        if (daysUntilExpiry <= 30) return 'bg-orange-500';
        return 'bg-green-600';
      case 'expired':
        return 'bg-red-600';
      case 'revoked':
        return 'bg-red-800';
      default:
        return 'bg-gray-500';
    }
  };

  // Format certificate expiry detail
  const getExpiryDetail = () => {
    if (certificate.status === 'expired') {
      return `Expired on ${format(new Date(certificate.valid_to), 'dd MMM yyyy')}`;
    } else if (certificate.status === 'revoked') {
      return 'Revoked';
    } else if (daysUntilExpiry <= 0) {
      return 'Expired today';
    } else if (daysUntilExpiry === 1) {
      return 'Expires tomorrow';
    } else if (daysUntilExpiry <= 30) {
      return `Expires in ${daysUntilExpiry} days`;
    } else {
      return `Expires on ${format(new Date(certificate.valid_to), 'dd MMM yyyy')}`;
    }
  };
  
  // Get certificate type display name
  const getCertificateTypeDisplay = (type: string) => {
    switch (type) {
      case 'access_point':
        return 'Access Point';
      case 'authentication':
        return 'Authentication';
      case 'signing':
        return 'Signing';
      default:
        return type.charAt(0).toUpperCase() + type.slice(1);
    }
  };
  
  // Download certificate
  const handleDownload = async () => {
    try {
      setIsDownloading(true);
      const response = await apiService.get(`/api/v1/certificates/${certificate.id}/download`, {
        responseType: 'blob'
      });
      
      // Create a blob URL and trigger download
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `certificate-${certificate.id}.pem`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      console.error('Failed to download certificate:', error);
    } finally {
      setIsDownloading(false);
    }
  };
  
  // Revoke certificate
  const handleRevoke = () => {
    if (onRevoke) {
      onRevoke(certificate);
    }
  };

  return (
    <Card className={cn('border-l-4 border-cyan-500 overflow-hidden shadow-sm', className)}>
      <CardContent className="p-4">
        {/* Status and Type Header */}
        <div className="flex justify-between items-center">
          <div className="flex items-center">
            <div className={cn('w-3 h-3 rounded-full mr-2', getStatusClass())} />
            <span className="text-sm">
              {certificate.status.charAt(0).toUpperCase() + certificate.status.slice(1)}
            </span>
          </div>
          <Badge className="bg-cyan-100 text-cyan-800 hover:bg-cyan-200">
            {getCertificateTypeDisplay(certificate.certificate_type)}
          </Badge>
        </div>
        
        {/* Certificate Subject */}
        <h3 className="text-lg font-medium mt-2 truncate" title={certificate.subject}>
          {certificate.subject}
        </h3>
        
        {/* Expiry Information */}
        <p className="text-sm text-gray-600 mt-1">
          {getExpiryDetail()}
        </p>
        
        {/* Basic Information */}
        <div className="mt-3 space-y-1 text-sm">
          <p className="text-gray-600">
            <span className="font-medium">Serial:</span>{' '}
            <span className="font-mono text-xs">
              {certificate.serial_number.slice(0, 8)}...{certificate.serial_number.slice(-8)}
            </span>
          </p>
          <p className="text-gray-600">
            <span className="font-medium">Issued by:</span>{' '}
            {certificate.issuer.length > 30 
              ? `${certificate.issuer.slice(0, 30)}...` 
              : certificate.issuer}
          </p>
          <p className="text-gray-600">
            <span className="font-medium">Issued:</span>{' '}
            {format(new Date(certificate.valid_from), 'dd MMM yyyy')}
          </p>
        </div>
        
        {/* Actions */}
        <div className="mt-4 pt-3 border-t border-gray-100 flex justify-between items-center">
          <Button
            onClick={() => setIsExpanded(!isExpanded)}
            variant="ghost"
            size="sm"
            className="text-sm flex items-center text-gray-600 hover:text-cyan-600 mr-3 p-0 h-auto"
          >
            {isExpanded ? (
              <>
                <ChevronUp className="h-4 w-4 mr-1" />
                Hide Details
              </>
            ) : (
              <>
                <ChevronDown className="h-4 w-4 mr-1" />
                Show Details
              </>
            )}
          </Button>
          
          <div className="flex">
            <Button
              onClick={handleDownload}
              disabled={isDownloading || certificate.status !== 'active'}
              variant="outline"
              size="sm"
              className="text-sm flex items-center text-cyan-600 hover:text-cyan-800 mr-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Download className="h-4 w-4 mr-1" />
              {isDownloading ? 'Downloading...' : 'Download'}
            </Button>
            
            {certificate.status === 'active' && (
              <Button
                onClick={handleRevoke}
                disabled={isRevoking}
                variant="outline"
                size="sm"
                className="text-sm flex items-center text-red-600 hover:text-red-800 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <XCircle className="h-4 w-4 mr-1" />
                {isRevoking ? 'Revoking...' : 'Revoke'}
              </Button>
            )}
          </div>
        </div>
      </CardContent>
      
      {/* Expanded Details */}
      {isExpanded && (
        <CardContent className="px-4 pb-4 border-t border-gray-100 pt-3 mt-0 text-sm bg-gray-50">
          <div className="space-y-2">
            <div>
              <p className="font-medium">Subject</p>
              <p className="font-mono text-xs break-all mt-1 text-gray-600">
                {certificate.subject}
              </p>
            </div>
            <div>
              <p className="font-medium">Issuer</p>
              <p className="font-mono text-xs break-all mt-1 text-gray-600">
                {certificate.issuer}
              </p>
            </div>
            <div>
              <p className="font-medium">Fingerprint</p>
              <p className="font-mono text-xs break-all mt-1 text-gray-600">
                {certificate.fingerprint}
              </p>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="font-medium">Valid From</p>
                <p className="text-gray-600">
                  {format(new Date(certificate.valid_from), 'dd MMM yyyy HH:mm')}
                </p>
              </div>
              <div>
                <p className="font-medium">Valid To</p>
                <p className="text-gray-600">
                  {format(new Date(certificate.valid_to), 'dd MMM yyyy HH:mm')}
                </p>
              </div>
            </div>
            {certificate.metadata && (
              <div>
                <p className="font-medium">Additional Information</p>
                <pre className="bg-gray-50 p-2 rounded mt-1 overflow-auto text-xs">
                  {JSON.stringify(certificate.metadata, null, 2)}
                </pre>
              </div>
            )}
          </div>
        </CardContent>
      )}
    </Card>
  );
};

export default CertificateCard;
