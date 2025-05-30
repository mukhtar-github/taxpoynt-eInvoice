import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import * as Tabs from '@radix-ui/react-tabs';
import { isFeatureEnabled } from '../../config/featureFlags';
import apiService from '../../utils/apiService';
import CertificateCard from 'components/app/CertificateCard';
import CertificateRequestTable from 'components/app/CertificateRequestTable';
import CertificateRequestWizard from 'components/app/CertificateRequestWizard';
import CSIDTable from 'components/app/CSIDTable';
import { Certificate, CertificateRequest, CSID } from '../../types/app';
import { cn } from '../../utils/cn';

interface CertificateManagementDashboardProps {
  organizationId: string;
  className?: string;
}

const CertificateManagementDashboard: React.FC<CertificateManagementDashboardProps> = ({ 
  organizationId,
  className = '' 
}) => {
  // State for certificates, requests, and CSIDs
  const [certificates, setCertificates] = useState<Certificate[]>([]);
  const [requests, setRequests] = useState<CertificateRequest[]>([]);
  const [csids, setCSIDs] = useState<CSID[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [isWizardOpen, setIsWizardOpen] = useState<boolean>(false);
  const router = useRouter();
  
  // Only render if APP certificate management features are enabled
  if (!isFeatureEnabled('APP_UI_ELEMENTS')) {
    return null;
  }
  
  // Fetch data on component mount
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);
      
      try {
        // Fetch certificates
        const certificatesResponse = await apiService.get(
          `/api/v1/certificates?organization_id=${organizationId}`
        );
        setCertificates(certificatesResponse.data);
        
        // Fetch certificate requests
        const requestsResponse = await apiService.get(
          `/api/v1/certificate-requests?organization_id=${organizationId}`
        );
        setRequests(requestsResponse.data);
        
        // Fetch CSIDs
        const csidsResponse = await apiService.get(
          `/api/v1/csids?organization_id=${organizationId}`
        );
        setCSIDs(csidsResponse.data);
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Error fetching certificate data');
      } finally {
        setLoading(false);
      }
    };
    
    fetchData();
  }, [organizationId]);
  
  // Certificate status counts
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
  
  // Handle new certificate request
  const handleNewRequest = () => {
    setIsWizardOpen(true);
  };
  
  // Handle refresh data
  const handleRefresh = () => {
    router.reload();
  };
  
  // Render loading state
  if (loading) {
    return (
      <div className={cn('p-4', className)}>
        <h2 className="text-xl font-semibold">Certificate Management</h2>
        <p className="mt-2">Loading certificate data...</p>
      </div>
    );
  }
  
  // Render error state
  if (error) {
    return (
      <div className={cn('p-4', className)}>
        <h2 className="text-xl font-semibold">Certificate Management</h2>
        <p className="mt-2 text-red-500">{error}</p>
        <button 
          className="mt-4 bg-blue-600 text-white py-2 px-4 rounded hover:bg-blue-700"
          onClick={handleRefresh}
        >
          Retry
        </button>
      </div>
    );
  }
  
  return (
    <div className={cn('certificate-management-dashboard p-4', className)}>
      {/* Dashboard Header */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-xl font-semibold">Certificate Management</h2>
          <p className="mt-1 text-sm text-gray-600">
            Manage your organization's certificates and signing identifiers
          </p>
        </div>
        <button
          className="bg-blue-600 text-white py-2 px-4 rounded hover:bg-blue-700"
          onClick={handleNewRequest}
        >
          Request New Certificate
        </button>
      </div>
      
      {/* Status Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="p-4 border border-gray-200 rounded bg-white">
          <span className="text-sm text-gray-500">Total Certificates</span>
          <h3 className="text-2xl font-bold">{certificates.length}</h3>
        </div>
        <div className="p-4 border border-gray-200 rounded bg-white">
          <span className="text-sm text-gray-500">Active</span>
          <h3 className="text-2xl font-bold text-green-600">{activeCount}</h3>
        </div>
        <div className="p-4 border border-gray-200 rounded bg-white">
          <span className="text-sm text-gray-500">Expiring Soon</span>
          <h3 className="text-2xl font-bold text-orange-500">{expiringCount}</h3>
        </div>
        <div className="p-4 border border-gray-200 rounded bg-white">
          <span className="text-sm text-gray-500">Expired</span>
          <h3 className="text-2xl font-bold text-red-600">{expiredCount}</h3>
        </div>
      </div>
      
      {/* Tabs for Different Sections */}
      <Tabs.Root defaultValue="certificates" className="w-full">
        <Tabs.List className="flex border-b border-gray-200 mb-4">
          <Tabs.Trigger 
            value="certificates"
            className="px-4 py-2 border-b-2 border-transparent data-[state=active]:border-blue-600 data-[state=active]:text-blue-600"
          >
            Certificates
          </Tabs.Trigger>
          <Tabs.Trigger 
            value="requests"
            className="px-4 py-2 border-b-2 border-transparent data-[state=active]:border-blue-600 data-[state=active]:text-blue-600 flex items-center"
          >
            Requests
            {requests.length > 0 && (
              <span className="ml-2 bg-blue-100 text-blue-800 text-xs font-medium px-2.5 py-0.5 rounded">
                {requests.length}
              </span>
            )}
          </Tabs.Trigger>
          <Tabs.Trigger 
            value="csids"
            className="px-4 py-2 border-b-2 border-transparent data-[state=active]:border-blue-600 data-[state=active]:text-blue-600"
          >
            CSIDs
          </Tabs.Trigger>
        </Tabs.List>
        
        <Tabs.Content value="certificates">
          {certificates.length === 0 ? (
            <div className="text-center py-10">
              <p className="mb-4">No certificates found for this organization</p>
              <button 
                className="bg-blue-600 text-white py-2 px-4 rounded hover:bg-blue-700"
                onClick={handleNewRequest}
              >
                Request Your First Certificate
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {certificates.map(certificate => (
                <CertificateCard 
                  key={certificate.id} 
                  certificate={certificate} 
                  onRefresh={handleRefresh}
                />
              ))}
            </div>
          )}
        </Tabs.Content>
        
        <Tabs.Content value="requests">
          <CertificateRequestTable 
            requests={requests} 
            onRefresh={handleRefresh}
          />
        </Tabs.Content>
        
        <Tabs.Content value="csids">
          <CSIDTable 
            csids={csids} 
            certificates={certificates}
            onRefresh={handleRefresh}
          />
        </Tabs.Content>
      </Tabs.Root>
      
      {/* Certificate Request Wizard */}
      {isWizardOpen && (
        <CertificateRequestWizard 
          isOpen={isWizardOpen} 
          onClose={() => setIsWizardOpen(false)} 
          organizationId={organizationId}
          onRequestComplete={handleRefresh}
        />
      )}
    </div>
  );
};

export default CertificateManagementDashboard;
