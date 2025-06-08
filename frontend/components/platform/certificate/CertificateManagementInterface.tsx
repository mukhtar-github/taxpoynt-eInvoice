import React, { useState, useEffect } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../ui/Tabs';
import { Card, CardContent, CardHeader, CardTitle } from '../../ui/Card';
import { Button } from '../../ui/Button';
import { Badge } from '../../ui/Badge';
import { Input } from '../../ui/Input';
import { 
  Shield, 
  FileKey, 
  RefreshCw, 
  Download, 
  Upload, 
  Clock, 
  AlertTriangle, 
  Check, 
  Loader2, 
  HelpCircle
} from 'lucide-react';
import { useToast } from '../../ui/Toast';
import { useAuth } from '../../../context/AuthContext';
import ContextualHelp from '../common/ContextualHelp';
import CertificateCard from '../CertificateCard';
import CertificateRequestWizard from '../CertificateRequestWizard';
import CertificateRevocationDialog from '../CertificateRevocationDialog';
import apiService from '../../../utils/apiService';
import { Certificate, CertificateRequest } from '../../../types/app';

interface CertificateManagementInterfaceProps {
  organizationId: string;
}

const CertificateManagementInterface: React.FC<CertificateManagementInterfaceProps> = ({ organizationId }) => {
  const [certificates, setCertificates] = useState<Certificate[]>([]);
  const [requests, setRequests] = useState<CertificateRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isWizardOpen, setIsWizardOpen] = useState(false);
  const [isRevocationDialogOpen, setIsRevocationDialogOpen] = useState(false);
  const [selectedCertificate, setSelectedCertificate] = useState<Certificate | null>(null);
  const [filterValue, setFilterValue] = useState('');
  const toast = useToast();
  const { user } = useAuth();
  
  // Check if user has admin permissions
  const isAdmin = user?.role === 'admin' || user?.role === 'org_admin';
  
  // Certificate management help text
  const certificateHelp = {
    overview: "Digital certificates are used to securely sign your electronic invoices and ensure compliance with FIRS regulations.",
    activation: "New certificates must be activated with FIRS before they can be used for invoice signing.",
    renewal: "Certificates should be renewed 30 days before expiration to ensure continuity of service.",
    backup: "Regular backup of certificates is recommended to prevent loss of signing capabilities."
  };
  
  useEffect(() => {
    fetchCertificates();
    fetchCertificateRequests();
  }, [organizationId]);
  
  const fetchCertificates = async () => {
    setLoading(true);
    try {
      const response = await apiService.get(`/api/v1/organizations/${organizationId}/certificates`);
      if (response.data) {
        setCertificates(response.data);
      }
    } catch (err) {
      console.error('Error fetching certificates:', err);
      setError('Failed to load certificates. Please try again.');
      toast({
        title: 'Error',
        description: 'Failed to load certificates',
        status: 'error'
      });
    } finally {
      setLoading(false);
    }
  };
  
  const fetchCertificateRequests = async () => {
    try {
      const response = await apiService.get(`/api/v1/organizations/${organizationId}/certificate-requests`);
      if (response.data) {
        setRequests(response.data);
      }
    } catch (err) {
      console.error('Error fetching certificate requests:', err);
    }
  };
  
  const handleRefresh = () => {
    fetchCertificates();
    fetchCertificateRequests();
    toast({
      title: 'Refreshed',
      description: 'Certificate data has been refreshed',
      status: 'info'
    });
  };
  
  const handleNewCertificateRequest = () => {
    setIsWizardOpen(true);
  };
  
  const handleRevokeCertificate = (certificate: Certificate) => {
    setSelectedCertificate(certificate);
    setIsRevocationDialogOpen(true);
  };
  
  const handleWizardComplete = () => {
    setIsWizardOpen(false);
    fetchCertificateRequests();
    toast({
      title: 'Success',
      description: 'Certificate request submitted successfully',
      status: 'success'
    });
  };
  
  const handleRevocationComplete = () => {
    setIsRevocationDialogOpen(false);
    fetchCertificates();
    toast({
      title: 'Certificate Revoked',
      description: 'The certificate has been revoked successfully',
      status: 'success'
    });
  };
  
  const filterCertificates = () => {
    if (!filterValue) return certificates;
    
    return certificates.filter(cert => 
      cert.subject.toLowerCase().includes(filterValue.toLowerCase()) ||
      cert.serial_number.toLowerCase().includes(filterValue.toLowerCase()) ||
      cert.status.toLowerCase().includes(filterValue.toLowerCase())
    );
  };
  
  const getStatusBadge = (status: string) => {
    switch (status.toLowerCase()) {
      case 'active':
        return <Badge className="bg-green-100 text-green-800">Active</Badge>;
      case 'expired':
        return <Badge className="bg-red-100 text-red-800">Expired</Badge>;
      case 'revoked':
        return <Badge className="bg-gray-100 text-gray-800">Revoked</Badge>;
      case 'pending':
        return <Badge className="bg-yellow-100 text-yellow-800">Pending</Badge>;
      default:
        return <Badge className="bg-blue-100 text-blue-800">{status}</Badge>;
    }
  };
  
  return (
    <div className="space-y-6">
      <Card className="border-l-4 border-l-cyan-500">
        <CardHeader className="pb-2">
          <div className="flex justify-between items-center">
            <div className="flex items-center">
              <Shield className="h-5 w-5 text-cyan-600 mr-2" />
              <CardTitle>Certificate Management</CardTitle>
              <ContextualHelp content={certificateHelp.overview}>
                <HelpCircle className="h-4 w-4 ml-2 text-gray-400" />
              </ContextualHelp>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={handleRefresh}
              disabled={loading}
            >
              {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
              <span className="ml-1">Refresh</span>
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="active">
            <div className="flex justify-between items-center mb-4">
              <TabsList>
                <TabsTrigger value="active">Active Certificates</TabsTrigger>
                <TabsTrigger value="requests">Certificate Requests</TabsTrigger>
                <TabsTrigger value="expired">Expired & Revoked</TabsTrigger>
              </TabsList>
              
              {isAdmin && (
                <Button onClick={handleNewCertificateRequest} className="bg-cyan-600 hover:bg-cyan-700">
                  <FileKey className="h-4 w-4 mr-2" />
                  Request New Certificate
                </Button>
              )}
            </div>
            
            <div className="mb-4">
              <Input
                placeholder="Filter certificates..."
                value={filterValue}
                onChange={(e) => setFilterValue(e.target.value)}
                className="max-w-md"
              />
            </div>
            
            <TabsContent value="active" className="space-y-4">
              {loading ? (
                <div className="flex justify-center items-center p-8">
                  <Loader2 className="h-8 w-8 animate-spin text-cyan-600" />
                </div>
              ) : filterCertificates().filter(cert => cert.status.toLowerCase() === 'active').length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {filterCertificates()
                    .filter(cert => cert.status.toLowerCase() === 'active')
                    .map(certificate => (
                      <CertificateCard
                        key={certificate.id}
                        certificate={certificate}
                        onRevoke={isAdmin ? () => handleRevokeCertificate(certificate) : undefined} onRefresh={function (): void {
                          throw new Error('Function not implemented.');
                        } }                      />
                    ))}
                </div>
              ) : (
                <div className="text-center p-8 border border-dashed rounded-lg">
                  <Shield className="h-12 w-12 mx-auto text-gray-400 mb-2" />
                  <h3 className="text-lg font-medium text-gray-900">No Active Certificates</h3>
                  <p className="text-gray-500 mt-1">
                    {isAdmin 
                      ? "You don't have any active certificates. Request a new certificate to start signing invoices."
                      : "There are no active certificates. Contact your administrator to request new certificates."}
                  </p>
                  {isAdmin && (
                    <Button 
                      onClick={handleNewCertificateRequest} 
                      className="mt-4 bg-cyan-600 hover:bg-cyan-700"
                    >
                      Request Certificate
                    </Button>
                  )}
                </div>
              )}
              
              <div className="bg-cyan-50 p-4 rounded-md border border-cyan-200 mt-4">
                <div className="flex items-start">
                  <div className="mr-3 mt-0.5">
                    <AlertTriangle className="h-5 w-5 text-cyan-600" />
                  </div>
                  <div>
                    <h4 className="text-sm font-medium text-cyan-800">Important Information</h4>
                    <p className="text-sm text-cyan-700 mt-1">
                      Digital certificates are crucial for e-invoice compliance. Ensure certificates are
                      kept secure and backed up regularly. Certificates typically expire after 12 months.
                    </p>
                    <div className="flex gap-4 mt-3">
                      <Button variant="outline" size="sm" className="text-xs">
                        <Download className="h-3 w-3 mr-1" /> Backup Certificates
                      </Button>
                      <Button variant="outline" size="sm" className="text-xs">
                        <Clock className="h-3 w-3 mr-1" /> View Certificate Timeline
                      </Button>
                    </div>
                  </div>
                </div>
              </div>
            </TabsContent>
            
            <TabsContent value="requests">
              {requests.length > 0 ? (
                <div className="space-y-4">
                  {requests.map(request => (
                    <div key={request.id} className="border rounded-lg p-4">
                      <div className="flex justify-between items-start">
                        <div>
                          <h3 className="font-medium">{request.subject}</h3>
                          <p className="text-sm text-gray-500 mt-1">
                            Requested: {new Date(request.requestDate).toLocaleDateString()}
                          </p>
                          <div className="mt-2">
                            {getStatusBadge(request.status)}
                          </div>
                        </div>
                        <div className="flex space-x-2">
                          {request.status.toLowerCase() === 'pending' && isAdmin && (
                            <Button size="sm" variant="outline">Check Status</Button>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center p-8 border border-dashed rounded-lg">
                  <FileKey className="h-12 w-12 mx-auto text-gray-400 mb-2" />
                  <h3 className="text-lg font-medium text-gray-900">No Certificate Requests</h3>
                  <p className="text-gray-500 mt-1">
                    There are no pending certificate requests at this time.
                  </p>
                </div>
              )}
            </TabsContent>
            
            <TabsContent value="expired">
              {filterCertificates().filter(cert => 
                ['expired', 'revoked'].includes(cert.status.toLowerCase())
              ).length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {filterCertificates()
                    .filter(cert => ['expired', 'revoked'].includes(cert.status.toLowerCase()))
                    .map(certificate => (
                      <CertificateCard
                        key={certificate.id}
                        certificate={certificate} onRefresh={function (): void {
                          throw new Error('Function not implemented.');
                        } }                      />
                    ))}
                </div>
              ) : (
                <div className="text-center p-8 border border-dashed rounded-lg">
                  <Clock className="h-12 w-12 mx-auto text-gray-400 mb-2" />
                  <h3 className="text-lg font-medium text-gray-900">No Expired Certificates</h3>
                  <p className="text-gray-500 mt-1">
                    You don't have any expired or revoked certificates.
                  </p>
                </div>
              )}
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
      
      {isWizardOpen && (
        <CertificateRequestWizard
          isOpen={isWizardOpen}
          organizationId={organizationId}
          onRequestComplete={handleWizardComplete}
          onClose={() => setIsWizardOpen(false)}
        />
      )}
      
      {isRevocationDialogOpen && selectedCertificate && (
        <CertificateRevocationDialog
          certificate={selectedCertificate}
          isOpen={isRevocationDialogOpen}
          onRevoked={handleRevocationComplete}
          onClose={() => setIsRevocationDialogOpen(false)}
        />
      )}
    </div>
  );
};

export default CertificateManagementInterface;
