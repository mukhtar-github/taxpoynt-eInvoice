import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Flex,
  Heading,
  Badge,
  Text,
  Spinner,
} from '@chakra-ui/react';
import {
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalFooter,
  ModalBody,
  ModalCloseButton,
  useDisclosure
} from '../../components/ui/ChakraModal';
import { Table, Thead, Tbody, Tr, Th, Td } from '../../components/ui/ChakraTable';
import { Button, IconButton, useToast } from '../../components/ui/ChakraButton';
import { FiEdit2, FiTrash2, FiPlus, FiPlay } from 'react-icons/fi';
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
];

const mockIntegrations = [
  {
    id: '1',
    name: 'ERP System Integration',
    client_id: '1',
    client_name: 'ACME Corporation',
    status: 'configured',
    last_tested: null,
  },
  {
    id: '2',
    name: 'Accounting Software Integration',
    client_id: '2',
    client_name: 'Globex Industries',
    status: 'active',
    last_tested: '2023-06-15T10:30:00Z',
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
  const { isOpen, onOpen, onClose } = useDisclosure();
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
    onClose();
    
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
    onOpen();
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
    <Container maxW="container.xl" py={8}>
      <Flex justify="space-between" align="center" mb={8}>
        <Heading size="lg">Integrations</Heading>
        <Button 
          leftIcon={<FiPlus />} 
          colorScheme="blue"
          onClick={() => {
            setSelectedIntegration(null);
            onOpen();
          }}
        >
          Create Integration
        </Button>
      </Flex>

      {loading ? (
        <Flex justify="center" my={10}>
          <Spinner size="xl" />
        </Flex>
      ) : integrations.length === 0 ? (
        <Box 
          p={10} 
          textAlign="center" 
          borderWidth={1} 
          borderRadius="md"
          borderStyle="dashed"
        >
          <Text fontSize="lg" mb={6}>No integrations found</Text>
          <Button 
            leftIcon={<FiPlus />} 
            colorScheme="blue"
            onClick={() => {
              setSelectedIntegration(null);
              onOpen();
            }}
          >
            Create Your First Integration
          </Button>
        </Box>
      ) : (
        <Table variant="simple">
          <Thead>
            <Tr>
              <Th>Name</Th>
              <Th>Client</Th>
              <Th>Status</Th>
              <Th>Last Tested</Th>
              <Th>Actions</Th>
            </Tr>
          </Thead>
          <Tbody>
            {integrations.map((integration) => (
              <Tr key={integration.id}>
                <Td fontWeight="medium">{integration.name}</Td>
                <Td>{integration.client_name}</Td>
                <Td>
                  <Badge 
                    colorScheme={
                      integration.status === 'active' ? 'green' :
                      integration.status === 'configured' ? 'blue' :
                      integration.status === 'failed' ? 'red' : 'gray'
                    }
                  >
                    {integration.status}
                  </Badge>
                </Td>
                <Td>
                  {integration.last_tested 
                    ? new Date(integration.last_tested).toLocaleString() 
                    : 'Never'}
                </Td>
                <Td>
                  <Flex>
                    <IconButton
                      aria-label="Test integration"
                      icon={<FiPlay />}
                      size="sm"
                      colorScheme="green"
                      variant="ghost"
                      mr={2}
                      onClick={() => handleTestIntegration(integration.id)}
                    />
                    <IconButton
                      aria-label="Edit integration"
                      icon={<FiEdit2 />}
                      size="sm"
                      colorScheme="blue"
                      variant="ghost"
                      mr={2}
                      onClick={() => handleEditIntegration(integration)}
                    />
                    <IconButton
                      aria-label="Delete integration"
                      icon={<FiTrash2 />}
                      size="sm"
                      colorScheme="red"
                      variant="ghost"
                      onClick={() => handleDeleteIntegration(integration.id)}
                    />
                  </Flex>
                </Td>
              </Tr>
            ))}
          </Tbody>
        </Table>
      )}

      {/* Integration Form Modal */}
      <Modal isOpen={isOpen} onClose={onClose} size="xl">
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>
            {selectedIntegration ? 'Edit Integration' : 'Create Integration'}
          </ModalHeader>
          <ModalCloseButton onClick={onClose} />
          <ModalBody>
            <IntegrationForm 
              clients={clients}
              onSubmit={handleCreateIntegration}
              initialData={convertIntegrationToFormData(selectedIntegration)}
            />
          </ModalBody>
        </ModalContent>
      </Modal>
    </Container>
  );
};

export default IntegrationsPage; 