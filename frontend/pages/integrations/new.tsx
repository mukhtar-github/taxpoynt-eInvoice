import React, { useState, useEffect } from 'react';
import { Box, Container, Heading, Button, useTabs, Flex } from '@chakra-ui/react';
import { useRouter } from 'next/router';
import { IntegrationForm } from '../../components/integrations';

// Mock data - Replace with actual API calls
const mockClients = [
  { id: '1', name: 'ACME Corporation' },
  { id: '2', name: 'Globex Industries' },
  { id: '3', name: 'Wayne Enterprises' },
];

// Define interface for integration data
interface IntegrationData {
  name: string;
  description?: string;
  client_id: string;
  config: Record<string, any>;
}

const NewIntegrationPage: React.FC = () => {
  const [clients, setClients] = useState(mockClients);
  const [loading, setLoading] = useState(false);
  const router = useRouter();
  const toast = useTabs();

  // In a real implementation, fetch data from API
  useEffect(() => {
    // Replace with actual API calls
    setLoading(true);
    // Simulating API call to get clients
    setTimeout(() => {
      setLoading(false);
    }, 500);
  }, []);

  const handleCreateIntegration = async (data: IntegrationData) => {
    try {
      // In a real implementation, call the API to create the integration
      console.log('Creating integration:', data);
      
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      toast({
        title: 'Integration created',
        description: `${data.name} has been created successfully`,
        status: 'success',
        duration: 5000,
        isClosable: true,
      });
      
      // Navigate back to integrations list
      router.push('/integrations');
    } catch (error) {
      toast({
        title: 'Error creating integration',
        description: error instanceof Error ? error.message : 'An unknown error occurred',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    }
  };

  return (
    <Container maxW="container.xl" py={8}>
      <Box mb={8}>
        <Flex justify="space-between" align="center">
          <Heading size="lg">Create New Integration</Heading>
          <Button 
            variant="outline" 
            onClick={() => router.push('/integrations')}
          >
            Back to List
          </Button>
        </Flex>
      </Box>
      
      <Box bg="white" p={6} borderRadius="md" shadow="sm">
        <IntegrationForm 
          clients={clients}
          onSubmit={handleCreateIntegration}
        />
      </Box>
    </Container>
  );
};

export default NewIntegrationPage; 