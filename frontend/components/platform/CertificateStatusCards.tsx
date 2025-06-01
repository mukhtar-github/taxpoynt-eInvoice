import React, { useState, useEffect } from 'react';
import { Card, CardContent } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { cn } from '../../utils/cn';
import { CheckCircle, AlertCircle, Clock, ShieldAlert } from 'lucide-react';
import apiService from '../../utils/apiService';
import { isFeatureEnabled } from '../../config/featureFlags';

interface Certificate {
  id: string;
  organization_id: string;
  status: 'active' | 'expired' | 'revoked' | 'pending';
  valid_from: string;
  valid_to: string;
  subject_name: string;
  issuer_name: string;
  serial_number: string;
}

interface CertificateStatusCardsProps {
  organizationId: string;
  className?: string;
}

/**
 * Certificate Status Cards Component
 * 
 * Displays summary cards for certificate status including:
 * - Active certificates
 * - Expiring soon certificates
 * - Expired certificates
 */
const CertificateStatusCards: React.FC<CertificateStatusCardsProps> = ({ 
  organizationId,
  className = '' 
}) => {
  const [certificates, setCertificates] = useState<Certificate[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  
  // Only render if Platform certificate management features are enabled
  if (!isFeatureEnabled('APP_UI_ELEMENTS')) {
    return null;
  }
  
  useEffect(() => {
    const fetchCertificates = async () => {
      setLoading(true);
      setError(null);
      
      try {
        const response = await apiService.get(
          `/api/v1/certificates?organization_id=${organizationId}`
        );
        setCertificates(response.data);
      } catch (err: any) {
        console.error('Error fetching certificates:', err);
        setError(err.response?.data?.detail || 'Failed to load certificate data');
      } finally {
        setLoading(false);
      }
    };
    
    fetchCertificates();
  }, [organizationId]);
  
  // Certificate counts
  const activeCount = certificates.filter(cert => cert.status === 'active').length;
  
  const expiringCount = certificates.filter(cert => {
    if (cert.valid_to) {
      const expiryDate = new Date(cert.valid_to);
      const thirtyDaysFromNow = new Date();
      thirtyDaysFromNow.setDate(thirtyDaysFromNow.getDate() + 30);
      return expiryDate <= thirtyDaysFromNow && cert.status === 'active';
    }
    return false;
  }).length;
  
  const expiredCount = certificates.filter(cert => cert.status === 'expired').length;
  
  if (loading) {
    return (
      <div className={cn('grid grid-cols-1 md:grid-cols-3 gap-4', className)}>
        {[1, 2, 3].map(i => (
          <Card key={i} className="border border-gray-200 animate-pulse">
            <CardContent className="p-6">
              <div className="h-6 bg-gray-200 rounded w-24 mb-2"></div>
              <div className="h-10 bg-gray-200 rounded w-16"></div>
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }
  
  if (error) {
    return (
      <Card className={cn('border-l-4 border-red-500 bg-red-50', className)}>
        <CardContent className="p-6">
          <div className="flex items-center">
            <AlertCircle className="h-5 w-5 text-red-500 mr-2" />
            <span className="text-red-700">Error loading certificate data: {error}</span>
          </div>
        </CardContent>
      </Card>
    );
  }
  
  if (certificates.length === 0) {
    return (
      <Card className={cn('border-l-4 border-cyan-500 bg-cyan-50', className)}>
        <CardContent className="p-6">
          <div className="flex items-center mb-2">
            <ShieldAlert className="h-5 w-5 text-cyan-600 mr-2" />
            <span className="font-medium text-cyan-800">No Certificates Found</span>
          </div>
          <p className="text-sm text-cyan-700">
            You don't have any certificates configured yet. Set up your first certificate to enable secure transmissions.
          </p>
        </CardContent>
      </Card>
    );
  }
  
  return (
    <div className={cn('grid grid-cols-1 md:grid-cols-3 gap-4', className)}>
      {/* Active Certificates */}
      <Card className="border-l-4 border-green-500">
        <CardContent className="p-6">
          <div className="flex items-center mb-2">
            <CheckCircle className="h-5 w-5 text-green-500 mr-2" />
            <span className="text-sm font-medium text-gray-500">Active Certificates</span>
          </div>
          <div className="flex items-baseline">
            <span className="text-3xl font-bold text-green-600">{activeCount}</span>
            <span className="ml-2 text-sm text-gray-500">of {certificates.length} total</span>
          </div>
        </CardContent>
      </Card>
      
      {/* Expiring Soon */}
      <Card className="border-l-4 border-amber-500">
        <CardContent className="p-6">
          <div className="flex items-center mb-2">
            <Clock className="h-5 w-5 text-amber-500 mr-2" />
            <span className="text-sm font-medium text-gray-500">Expiring Soon</span>
          </div>
          <div className="flex items-baseline">
            <span className="text-3xl font-bold text-amber-600">{expiringCount}</span>
            <span className="ml-2 text-sm text-gray-500">in next 30 days</span>
          </div>
        </CardContent>
      </Card>
      
      {/* Expired */}
      <Card className="border-l-4 border-red-500">
        <CardContent className="p-6">
          <div className="flex items-center mb-2">
            <AlertCircle className="h-5 w-5 text-red-500 mr-2" />
            <span className="text-sm font-medium text-gray-500">Expired</span>
          </div>
          <div className="flex items-baseline">
            <span className="text-3xl font-bold text-red-600">{expiredCount}</span>
            <span className="ml-2 text-sm text-gray-500">need renewal</span>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default CertificateStatusCards;
