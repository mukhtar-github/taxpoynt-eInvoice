import React, { useState, useEffect } from 'react';
import DashboardLayout from '../../components/layouts/DashboardLayout';
import ProtectedRoute from '../../components/auth/ProtectedRoute';
import { Container } from '../../components/ui/Container';
import { Typography } from '../../components/ui/Typography';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { Card, CardHeader, CardContent } from '../../components/ui/Card';
import { 
  Table, 
  TableContainer, 
  TableHeader, 
  TableBody, 
  TableHead, 
  TableRow, 
  TableCell, 
  TableEmpty 
} from '../../components/ui/Table';
import { Spinner } from '../../components/ui/Spinner';
import {
  Modal,
  ModalHeader,
  ModalBody,
} from '../../components/ui/Modal';
import { useToast } from '../../components/ui/Toast';
import { Edit2 as FiEdit2, Trash2 as FiTrash2, Plus as FiPlus, Play as FiPlay } from 'lucide-react';
import { useRouter } from 'next/router';
import { IntegrationForm } from '../../components/integrations';

// Interface for integration form data
interface IntegrationFormData {
  name: string;
  description: string;
  client_id: string;
  config: Record<string, any>;
}

// Interface for integration object
interface Integration {
  id: string;
  name: string;
  client_id: string;
  client_name: string;
  status: 'active' | 'configured' | 'failed' | string;
  last_tested: string | null;
}

// Mock data - Replace with actual API calls
const mockClients = [
  { id: '1', name: 'ACME Corporation' },
  { id: '2', name: 'Globex Industries' },
  { id: '3', name: 'Wayne Enterprises' },
  { id: '4', name: 'First Bank Nigeria' },
  { id: '5', name: 'Dangote Group' },
];

const mockIntegrations = [
  {
    id: '1',
    name: 'SAP ERP Integration',
    client_id: '1',
    client_name: 'ACME Corporation',
    status: 'active',
    last_tested: '2025-05-10T14:30:00Z',
    description: 'Direct integration with SAP ERP for automated invoice synchronization and real-time reporting.'
  },
  {
    id: '2',
    name: 'Odoo Integration',
    client_id: '2',
    client_name: 'Globex Industries',
    status: 'active',
    last_tested: '2025-05-12T09:15:00Z',
    description: 'Seamless Odoo integration for small to medium businesses needing end-to-end e-invoicing.'
  },
  {
    id: '3',
    name: 'Oracle ERP Integration',
    client_id: '3',
    client_name: 'Wayne Enterprises',
    status: 'configured',
    last_tested: '2025-05-13T16:45:00Z',
    description: 'Enterprise-grade Oracle ERP integration with secure data transmission and validation.'
  },
  {
    id: '4',
    name: 'Microsoft Dynamics Integration',
    client_id: '4',
    client_name: 'First Bank Nigeria',
    status: 'active',
    last_tested: '2025-05-14T11:20:00Z',
    description: 'Full Microsoft Dynamics 365 compatibility with bi-directional data flow.'
  },
  {
    id: '5',
    name: 'QuickBooks Integration',
    client_id: '5',
    client_name: 'Dangote Group',
    status: 'configured',
    last_tested: null,
    description: 'Quick and easy QuickBooks integration for small businesses and accountants.'
  },
];

// Function to convert Integration to IntegrationFormData for compatibility
const convertIntegrationToFormData = (integration: Integration | null): Partial<IntegrationFormData> | undefined => {
  if (!integration) return undefined;
  
  return {
    name: integration.name,
    client_id: integration.client_id,
    description: '', // Add any default values for missing fields
    config: {} // Add a default empty config or retrieve it from somewhere
  };
};

const IntegrationsPage: React.FC = () => {
  const [integrations, setIntegrations] = useState<Integration[]>(mockIntegrations);
  const [clients, setClients] = useState(mockClients);
  const [loading, setLoading] = useState(false);
  const [selectedIntegration, setSelectedIntegration] = useState<Integration | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  
  const openModal = () => setIsModalOpen(true);
  const closeModal = () => setIsModalOpen(false);
  const router = useRouter();
  const toast = useToast();

  // In a real implementation, fetch data from API
  useEffect(() => {
    // Replace with actual API calls
    setLoading(true);
    // Simulating API call
    setTimeout(() => {
      setLoading(false);
    }, 500);
  }, []);

  const handleCreateIntegration = async (data: IntegrationFormData) => {
    // In a real implementation, call the API to create the integration
    console.log('Creating integration:', data);
    
    // Mock implementation
    const newIntegration = {
      id: `${integrations.length + 1}`,
      name: data.name,
      client_id: data.client_id,
      client_name: clients.find(c => c.id === data.client_id)?.name || 'Unknown Client',
      status: 'configured',
      last_tested: null,
    };
    
    setIntegrations([...integrations, newIntegration]);
    closeModal();
    
    toast({
      title: 'Integration created',
      description: `${data.name} has been created successfully`,
      status: 'success',
      duration: 5000,
      isClosable: true,
    });
  };

  const handleEditIntegration = (integration: Integration) => {
    setSelectedIntegration(integration);
    open();
  };

  const handleDeleteIntegration = (id: string) => {
    // In a real implementation, call the API to delete the integration
    setIntegrations(integrations.filter(i => i.id !== id));
    
    toast({
      title: 'Integration deleted',
      description: 'The integration has been deleted successfully',
      status: 'success',
      duration: 5000,
      isClosable: true,
    });
  };

  const handleTestIntegration = (id: string) => {
    // In a real implementation, call the API to test the integration
    toast({
      title: 'Testing integration',
      description: 'Integration test started',
      status: 'info',
      duration: 3000,
      isClosable: true,
    });
    
    // Simulate a successful test after 2 seconds
    setTimeout(() => {
      toast({
        title: 'Test successful',
        description: 'Integration tested successfully',
        status: 'success',
        duration: 5000,
        isClosable: true,
      });
    }, 2000);
  };

  return (
    <DashboardLayout>
      <Container maxWidth="xl" padding="medium">
        <div className="flex flex-col md:flex-row justify-between items-center mb-6">
        <Typography.Heading level="h1">Integrations</Typography.Heading>
        <Button 
          variant="default"
          className="mt-4 md:mt-0 flex items-center gap-2"
          onClick={() => {
            setSelectedIntegration(null);
            openModal();
          }}
        >
          <FiPlus className="h-4 w-4" aria-hidden="true" />
          Create Integration
        </Button>
      </div>

      {loading ? (
        <div className="my-10">
          <Spinner size="xl" center />
        </div>
      ) : integrations.length === 0 ? (
        <Card className="p-8 text-center border border-dashed">
          <CardContent>
            <Typography.Text size="lg" className="mb-6">No integrations found</Typography.Text>
            <Button 
              variant="default"
              className="flex items-center gap-2 mx-auto"
              onClick={() => {
                setSelectedIntegration(null);
                openModal();
              }}
            >
              <FiPlus className="h-4 w-4" aria-hidden="true" />
              Create Your First Integration
            </Button>
          </CardContent>
        </Card>
      ) : (
        <TableContainer variant="card">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Client</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Last Tested</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {integrations.map((integration) => (
                <TableRow key={integration.id}>
                  <TableCell className="font-medium">{integration.name}</TableCell>
                  <TableCell>{integration.client_name}</TableCell>
                  <TableCell>
                    <Badge 
                      variant={
                        integration.status === 'active' ? 'success' :
                        integration.status === 'configured' ? 'default' :
                        integration.status === 'failed' ? 'destructive' : 'secondary'
                      }
                    >
                      {integration.status}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    {integration.last_tested 
                      ? new Date(integration.last_tested).toLocaleString() 
                      : 'Never'}
                  </TableCell>
                  <TableCell>
                    <div className="flex space-x-2">
                      <Button
                        aria-label="Test integration"
                        variant="ghost"
                        size="icon"
                        className="text-success-dark hover:text-success hover:bg-success-light"
                        onClick={() => handleTestIntegration(integration.id)}
                      >
                        <FiPlay className="h-4 w-4" />
                      </Button>
                      <Button
                        aria-label="Edit integration"
                        variant="ghost"
                        size="icon"
                        className="text-primary hover:bg-primary-light"
                        onClick={() => {
                          handleEditIntegration(integration);
                          openModal();
                        }}
                      >
                        <FiEdit2 className="h-4 w-4" />
                      </Button>
                      <Button
                        aria-label="Delete integration"
                        variant="ghost"
                        size="icon"
                        className="text-error-dark hover:text-error hover:bg-error-light"
                        onClick={() => handleDeleteIntegration(integration.id)}
                      >
                        <FiTrash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      {/* Integration Form Modal */}
      <Modal isOpen={isModalOpen} onClose={closeModal} size="xl">
        <ModalHeader>
          {selectedIntegration ? 'Edit Integration' : 'Create Integration'}
        </ModalHeader>
        <ModalBody>
          <IntegrationForm 
            clients={clients}
            onSubmit={handleCreateIntegration}
            initialData={convertIntegrationToFormData(selectedIntegration)}
          />
        </ModalBody>
      </Modal>
      </Container>
    </DashboardLayout>
  );
};

// Wrap the component with ProtectedRoute
const ProtectedIntegrationsPage = () => {
  return (
    <ProtectedRoute>
      <IntegrationsPage />
    </ProtectedRoute>
  );
};

export default ProtectedIntegrationsPage;