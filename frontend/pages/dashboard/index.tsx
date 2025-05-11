import { NextPage } from 'next';
import { useState, useEffect } from 'react';
import MainLayout from '../../components/layouts/MainLayout';
import { Container } from '../../components/ui/Container';
import { Typography } from '../../components/ui/Typography';
import { Card, CardContent, CardHeader, CardGrid, MetricCard } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { TransactionLogTable } from '../../components/ui/ResponsiveTable';
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
import Link from 'next/link';
import { AlertCircle, CheckCircle, Clock, RefreshCw } from 'lucide-react';

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
  const [isLoading, setIsLoading] = useState(false);
  
  // In a real implementation, this would fetch data from the backend
  useEffect(() => {
    // Simulating API call
    const fetchData = async () => {
      // In a real app, these would be separate API calls
      // const integrationsData = await api.get('/integrations');
      // const transactionsData = await api.get('/transactions/metrics');
      // const recentData = await api.get('/transactions/recent');
      
      // setIntegrations(integrationsData);
      // setTransactions(transactionsData);
      // setRecentTransactions(recentData);
    };
    
    fetchData();
  }, []);

  const handleRefresh = () => {
    setIsLoading(true);
    // Simulate API call delay
    setTimeout(() => {
      setIsLoading(false);
    }, 1000);
  };

  // Helper function to format dates
  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'Never';
    return new Date(dateString).toLocaleString();
  };

  return (
    <MainLayout title="Dashboard | Taxpoynt eInvoice">
      <Container padding="medium" className="py-6">
          <div className="flex flex-col md:flex-row justify-between items-center mb-6">
            <Typography.Heading level="h1">Dashboard</Typography.Heading>
            <Button 
              variant="outline" 
              size="sm" 
              className="mt-4 md:mt-0 flex items-center gap-2"
              onClick={handleRefresh}
              disabled={isLoading}
            >
              <RefreshCw size={16} className={isLoading ? "animate-spin" : ""} />
              Refresh Data
            </Button>
          </div>

          {/* Metric cards with consistent 24px spacing between cards */}
          <CardGrid columns={{ base: 1, md: 2, lg: 4 }} className="mb-8">
            <MetricCard
              title="Total Invoices (Today)"
              value={transactions.today.toString()}
            />
            <MetricCard
              title="Weekly Transactions"
              value={transactions.week.toString()}
            />
            <MetricCard
              title="Monthly Transactions"
              value={transactions.month.toString()}
            />
            <MetricCard
              title="Success Rate"
              value={`${transactions.success}%`}
              change={{
                value: "0.8%",
                type: "increase"
              }}
            />
          </CardGrid>
          
          {/* Main content cards with responsive layout */}
          <CardGrid columns={{ base: 1, lg: 2 }}>
            <Card>
              <CardHeader title="Integration Status" subtitle="Status of connected integrations" />
              <CardContent>
                {/* Responsive table with horizontal scroll */}
                <TableContainer>
                  <Table minWidth="600px">
                    <TableHeader>
                      <TableRow>
                        <TableHead>Integration</TableHead>
                        <TableHead>Client</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead>Last Synced</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {integrations.length === 0 ? (
                        <TableEmpty colSpan={4} message="No integrations found" />
                      ) : (
                        integrations.map(integration => (
                          <TableRow key={integration.id}>
                            <TableCell>{integration.name}</TableCell>
                            <TableCell>{integration.client}</TableCell>
                            <TableCell>
                              <Badge 
                                variant={
                                  integration.status === 'active' ? 'success' : 
                                  integration.status === 'error' ? 'destructive' : 
                                  'secondary'
                                }
                              >
                                {integration.status}
                              </Badge>
                            </TableCell>
                            <TableCell>{formatDate(integration.lastSynced)}</TableCell>
                          </TableRow>
                        ))
                      )}
                    </TableBody>
                  </Table>
                </TableContainer>
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader title="Transaction Metrics" subtitle="Weekly transaction volume" />
              <CardContent>
                <div className="h-64 flex items-center justify-center bg-background-alt rounded-md">
                  <Typography.Text variant="secondary">Chart placeholder - will display transaction metrics</Typography.Text>
                </div>
              </CardContent>
            </Card>
          </CardGrid>

          {/* Secondary content cards with responsive layout and proper spacing */}
          <CardGrid columns={{ base: 1, lg: 2 }} className="mt-6">
            <Card>
              <CardHeader title="Recent Transactions" subtitle="Latest system activity" />
              <CardContent>
                {/* Transaction log table with horizontal scroll capability */}
                <TransactionLogTable 
                  transactions={recentTransactions}
                  isLoading={isLoading}
                />
              </CardContent>
            </Card>

            <Card>
              <CardHeader title="Error Rate" subtitle="Daily error percentage" />
              <CardContent>
                <div className="h-64 flex items-center justify-center bg-background-alt rounded-md">
                  <Typography.Text variant="secondary">Chart placeholder - will display error rates</Typography.Text>
                </div>
              </CardContent>
            </Card>
          </CardGrid>
      </Container>
    </MainLayout>
  );
};

export default Dashboard; 