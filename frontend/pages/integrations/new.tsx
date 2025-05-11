import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import MainLayout from '../../components/layouts/MainLayout';
import { Container } from '../../components/ui/Container';
import { Typography } from '../../components/ui/Typography';
import { Button } from '../../components/ui/Button';
import { Card, CardContent } from '../../components/ui/Card';
import { useToast } from '../../components/ui/Toast';
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
  const toast = useToast();

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
      });
      
      // Navigate back to integrations list
      router.push('/integrations');
    } catch (error) {
      toast({
        title: 'Error creating integration',
        description: error instanceof Error ? error.message : 'An unknown error occurred',
        status: 'error',
        duration: 5000,
      });
    }
  };

  return (
    <MainLayout title="Create Integration | Taxpoynt eInvoice">
      <Container maxWidth="xl" padding="medium">
        <div className="mb-6">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <Typography.Heading level="h1">Create New Integration</Typography.Heading>
            <Button 
              variant="outline" 
              className="mt-4 md:mt-0"
              onClick={() => router.push('/integrations')}
            >
              Back to List
            </Button>
          </div>
        </div>
        
        <Card>
          <CardContent>
            <IntegrationForm 
              clients={clients}
              onSubmit={handleCreateIntegration}
            />
          </CardContent>
        </Card>
      </Container>
    </MainLayout>
  );
};

export default NewIntegrationPage; 