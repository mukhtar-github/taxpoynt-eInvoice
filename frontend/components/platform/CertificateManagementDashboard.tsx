import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import * as Tabs from '@radix-ui/react-tabs';
import { Shield, Bell, History, Lock, CheckSquare, RefreshCw } from 'lucide-react';
import { Badge } from '../ui/Badge';
import { isFeatureEnabled } from '../../config/featureFlags';
import apiService from '../../utils/apiService';
import CertificateCard from 'components/platform/CertificateCard';
import CertificateRequestTable from 'components/platform/CertificateRequestTable';
import CertificateRequestWizard from 'components/platform/CertificateRequestWizard';
import CSIDTable from 'components/platform/CSIDTable';
import CertificateTimeline from 'components/platform/CertificateTimeline';
import CertificateExpiryWarnings from 'components/platform/CertificateExpiryWarnings';
import CertificateRevocationDialog from 'components/platform/CertificateRevocationDialog';
import CertificateBackupRestore from 'components/platform/CertificateBackupRestore';
import CertificateChainValidation from 'components/platform/CertificateChainValidation';
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
  const [isRevocationDialogOpen, setIsRevocationDialogOpen] = useState<boolean>(false);
  const [selectedCertificate, setSelectedCertificate] = useState<Certificate | null>(null);
  const [activeTab, setActiveTab] = useState<string>('certificates');
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
  
  // Handle certificate revocation
  const handleRevokeCertificate = (certificate: Certificate) => {
    setSelectedCertificate(certificate);
    setIsRevocationDialogOpen(true);
  };
  
  // Handle tab change
  const handleTabChange = (value: string) => {
    setActiveTab(value);
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
    <div className={cn('certificate-management-dashboard p-4 border-l-4 border-cyan-500', className)}>
      {/* Dashboard Header */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-xl font-semibold flex items-center">
            <Shield className="h-5 w-5 mr-2 text-cyan-500" />
            Certificate Management
            <Badge className="ml-2 bg-cyan-100 text-cyan-800 hover:bg-cyan-200">Platform</Badge>
          </h2>
          <p className="mt-1 text-sm text-gray-600">
            Manage your organization's certificates and signing identifiers
          </p>
        </div>
        <div className="flex space-x-2">
          <button
            className="flex items-center bg-gray-100 text-gray-700 py-2 px-3 rounded hover:bg-gray-200"
            onClick={handleRefresh}
          >
            <RefreshCw className="h-4 w-4 mr-1" />
            Refresh
          </button>
          <button
            className="flex items-center bg-cyan-600 text-white py-2 px-4 rounded hover:bg-cyan-700"
            onClick={handleNewRequest}
          >
            <Lock className="h-4 w-4 mr-1" />
            Request New Certificate
          </button>
        </div>
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
      <Tabs.Root defaultValue="certificates" className="w-full" onValueChange={handleTabChange}>
        <Tabs.List className="flex border-b border-gray-200 mb-4 overflow-x-auto">
          <Tabs.Trigger 
            value="certificates"
            className="px-4 py-2 border-b-2 border-transparent data-[state=active]:border-cyan-600 data-[state=active]:text-cyan-600 whitespace-nowrap"
          >
            Certificates
          </Tabs.Trigger>
          <Tabs.Trigger 
            value="requests"
            className="px-4 py-2 border-b-2 border-transparent data-[state=active]:border-cyan-600 data-[state=active]:text-cyan-600 flex items-center whitespace-nowrap"
          >
            Requests
            {requests.length > 0 && (
              <span className="ml-2 bg-cyan-100 text-cyan-800 text-xs font-medium px-2.5 py-0.5 rounded">
                {requests.length}
              </span>
            )}
          </Tabs.Trigger>
          <Tabs.Trigger 
            value="csids"
            className="px-4 py-2 border-b-2 border-transparent data-[state=active]:border-cyan-600 data-[state=active]:text-cyan-600 whitespace-nowrap"
          >
            CSIDs
          </Tabs.Trigger>
          <Tabs.Trigger 
            value="timeline"
            className="px-4 py-2 border-b-2 border-transparent data-[state=active]:border-cyan-600 data-[state=active]:text-cyan-600 flex items-center whitespace-nowrap"
          >
            <History className="h-4 w-4 mr-1" />
            Timeline
          </Tabs.Trigger>
          <Tabs.Trigger 
            value="expiry-warnings"
            className="px-4 py-2 border-b-2 border-transparent data-[state=active]:border-cyan-600 data-[state=active]:text-cyan-600 flex items-center whitespace-nowrap"
          >
            <Bell className="h-4 w-4 mr-1" />
            Expiry Warnings
          </Tabs.Trigger>
          <Tabs.Trigger 
            value="backup-restore"
            className="px-4 py-2 border-b-2 border-transparent data-[state=active]:border-cyan-600 data-[state=active]:text-cyan-600 flex items-center whitespace-nowrap"
          >
            <Lock className="h-4 w-4 mr-1" />
            Backup & Restore
          </Tabs.Trigger>
          <Tabs.Trigger 
            value="validation"
            className="px-4 py-2 border-b-2 border-transparent data-[state=active]:border-cyan-600 data-[state=active]:text-cyan-600 flex items-center whitespace-nowrap"
          >
            <CheckSquare className="h-4 w-4 mr-1" />
            Chain Validation
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
                  onRevoke={() => handleRevokeCertificate(certificate)}
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
        
        {/* Certificate Timeline Tab */}
        <Tabs.Content value="timeline">
          <CertificateTimeline 
            certificate={certificates[0]}
            events={certificates.map(cert => {
              // Map CertificateStatus to valid CertificateEvent.eventType values
              let eventType: 'created' | 'activated' | 'renewed' | 'revoked' | 'expired' | 'backed_up' | 'restored' | 'validated';
              
              switch(cert.status) {
                case 'active':
                  eventType = 'activated';
                  break;
                case 'pending':
                  eventType = 'created';
                  break;
                case 'expired':
                  eventType = 'expired';
                  break;
                case 'revoked':
                  eventType = 'revoked';
                  break;
                default:
                  eventType = 'created'; // Fallback value
              }
              
              return {
                id: cert.id,
                certificateId: cert.id,
                eventType: eventType,
                timestamp: new Date(cert.valid_from).toISOString(), // Convert to string as expected by CertificateEvent
              };
            })}
            className="mt-4"
          />
        </Tabs.Content>
        
        {/* Certificate Expiry Warnings Tab */}
        <Tabs.Content value="expiry-warnings">
          <CertificateExpiryWarnings 
            certificates={certificates}
            organizationId={organizationId}
            className="mt-4"
          />
        </Tabs.Content>
        
        {/* Certificate Backup & Restore Tab */}
        <Tabs.Content value="backup-restore">
          <CertificateBackupRestore 
            certificates={certificates}
            organizationId={organizationId}
            onBackupComplete={handleRefresh}
            onRestoreComplete={handleRefresh}
            className="mt-4"
          />
        </Tabs.Content>
        
        {/* Certificate Chain Validation Tab */}
        <Tabs.Content value="validation">
          <CertificateChainValidation 
            organizationId={organizationId}
            className="mt-4"
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
      
      {/* Certificate Revocation Dialog */}
      {isRevocationDialogOpen && selectedCertificate && (
        <CertificateRevocationDialog
          isOpen={isRevocationDialogOpen}
          onClose={() => setIsRevocationDialogOpen(false)}
          certificate={selectedCertificate}
          onRevoked={handleRefresh}
        />
      )}
    </div>
  );
};

export default CertificateManagementDashboard;
