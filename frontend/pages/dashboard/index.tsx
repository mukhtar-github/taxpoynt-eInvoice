import { NextPage } from 'next';
import { Box, Container, Flex, Heading, Text } from '@chakra-ui/react';
import { useEffect, useState } from 'react';
import { useColorModeValue } from '@/components/ui/ChakraColorMode';
import { SimpleGrid } from '@/components/ui/ChakraGrid';
import { Link } from '@/components/ui/ChakraLink';
import DashboardLayout from '@/components/layouts/DashboardLayout';
import IntegrationStatusCard from '@/components/dashboard/IntegrationStatusCard';
import TransactionMetricsCard from '@/components/dashboard/TransactionMetricsCard';
import RecentTransactionsCard from '@/components/dashboard/RecentTransactionsCard';
import ErrorRateCard from '@/components/dashboard/ErrorRateCard';

// Mock data for POC phase
const mockIntegrations = [
  { id: '1', name: 'ERP Integration', client: 'ABC Corp', status: 'active', lastSynced: '2025-04-26T06:30:00Z' },
  { id: '2', name: 'Accounting System', client: 'XYZ Ltd', status: 'configured', lastSynced: null },
  { id: '3', name: 'POS Integration', client: 'Retail Co', status: 'error', lastSynced: '2025-04-25T14:22:00Z' },
];

const mockTransactions = {
  today: 124,
  week: 738,
  month: 2945,
  success: 95.8
};

const mockRecentTransactions = [
  { id: '1', type: 'irn_generation' as 'irn_generation', status: 'success' as 'success', integration: 'ERP Integration', timestamp: '2025-04-26T06:45:12Z' },
  { id: '2', type: 'validation' as 'validation', status: 'success' as 'success', integration: 'ERP Integration', timestamp: '2025-04-26T06:44:23Z' },
  { id: '3', type: 'submission' as 'submission', status: 'failed' as 'failed', integration: 'POS Integration', timestamp: '2025-04-26T06:22:58Z' },
  { id: '4', type: 'irn_generation' as 'irn_generation', status: 'success' as 'success', integration: 'ERP Integration', timestamp: '2025-04-26T06:18:42Z' },
  { id: '5', type: 'validation' as 'validation', status: 'success' as 'success', integration: 'ERP Integration', timestamp: '2025-04-26T06:15:19Z' },
];

const Dashboard: NextPage = () => {
  const [integrations, setIntegrations] = useState(mockIntegrations);
  const [transactions, setTransactions] = useState(mockTransactions);
  const [recentTransactions, setRecentTransactions] = useState(mockRecentTransactions);
  
  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');

  // In a real implementation, this would fetch data from the backend
  useEffect(() => {
    // Fetch dashboard data from API
    // Example: 
    // const fetchDashboardData = async () => {
    //   const response = await fetch('/api/dashboard/metrics');
    //   const data = await response.json();
    //   setIntegrations(data.integrations);
    //   setTransactions(data.transactions);
    //   setRecentTransactions(data.recentTransactions);
    // };
    //
    // fetchDashboardData();
  }, []);

  return (
    <DashboardLayout>
      <Container maxW="container.xl" py={8}>
        <Heading as="h1" size="xl" mb={6}>Dashboard</Heading>
        
        {/* Integration Status Section */}
        <Box mb={8}>
          <Flex justifyContent="space-between" alignItems="center" mb={4}>
            <Heading as="h2" size="md">Integration Status</Heading>
            <Link href="/integrations" color="blue.500" fontSize="sm">View All</Link>
          </Flex>
          <SimpleGrid columns={{ base: 1, md: 3 }} spacing={6}>
            <IntegrationStatusCard 
              count={integrations.filter(i => i.status === 'active').length} 
              status="Active" 
              colorScheme="green"
            />
            <IntegrationStatusCard 
              count={integrations.filter(i => i.status === 'configured').length}
              status="Configured" 
              colorScheme="blue"
            />
            <IntegrationStatusCard 
              count={integrations.filter(i => i.status === 'error').length}
              status="Error" 
              colorScheme="red"
            />
          </SimpleGrid>
        </Box>
        
        {/* Metrics Section */}
        <Box mb={8}>
          <Heading as="h2" size="md" mb={4}>Transaction Metrics</Heading>
          <SimpleGrid columns={{ base: 1, md: 4 }} spacing={6}>
            <TransactionMetricsCard 
              title="Today" 
              count={transactions.today} 
              icon="today"
            />
            <TransactionMetricsCard 
              title="This Week" 
              count={transactions.week} 
              icon="week"
            />
            <TransactionMetricsCard 
              title="This Month" 
              count={transactions.month} 
              icon="month"
            />
            <ErrorRateCard 
              successRate={transactions.success}
            />
          </SimpleGrid>
        </Box>
        
        {/* Recent Transactions Section */}
        <Box>
          <Heading as="h2" size="md" mb={4}>Recent Transactions</Heading>
          <Box 
            bg={bgColor} 
            borderRadius="lg" 
            border="1px" 
            borderColor={borderColor} 
            overflow="hidden"
          >
            <RecentTransactionsCard transactions={recentTransactions} />
          </Box>
        </Box>
      </Container>
    </DashboardLayout>
  );
};

export default Dashboard; 