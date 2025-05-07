import { NextPage } from 'next';
import { useState, useEffect } from 'react';
import MainLayout from '../../components/layouts/MainLayout';
import { Container } from '../../components/ui/Grid';
import { Typography } from '../../components/ui/Typography';
import { Card, CardContent, CardHeader, MetricCard } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
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
      <Container>
        <div className="py-6">
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

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
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
          </div>
          
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader title="Integration Status" subtitle="Status of connected integrations" />
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="w-full border-collapse text-sm">
                    <thead>
                      <tr className="border-b-2 border-border">
                        <th className="text-left p-3 font-semibold">Integration</th>
                        <th className="text-left p-3 font-semibold">Client</th>
                        <th className="text-left p-3 font-semibold">Status</th>
                        <th className="text-left p-3 font-semibold">Last Synced</th>
                      </tr>
                    </thead>
                    <tbody>
                      {integrations.map(integration => (
                        <tr key={integration.id} className="border-b border-border">
                          <td className="p-3">{integration.name}</td>
                          <td className="p-3">{integration.client}</td>
                          <td className="p-3">
                            <Badge 
                              variant={
                                integration.status === 'active' ? 'success' : 
                                integration.status === 'error' ? 'destructive' : 
                                'secondary'
                              }
                            >
                              {integration.status}
                            </Badge>
                          </td>
                          <td className="p-3">{formatDate(integration.lastSynced)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
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
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
            <Card>
              <CardHeader title="Recent Transactions" subtitle="Latest system activity" />
              <CardContent>
                <div className="space-y-4">
                  {recentTransactions.map(transaction => (
                    <div key={transaction.id} className="flex justify-between items-center p-3 bg-background-alt rounded-md">
                      <div>
                        <Typography.Text weight="medium">
                          {transaction.type === 'irn_generation' ? 'IRN Generation' : 
                           transaction.type === 'validation' ? 'Validation' : 
                           'Submission'}
                        </Typography.Text>
                        <Typography.Text variant="secondary" size="sm">
                          {transaction.integration} - {formatDate(transaction.timestamp)}
                        </Typography.Text>
                      </div>
                      <div>
                        {transaction.status === 'success' ? (
                          <Badge variant="success" className="flex items-center gap-1">
                            <CheckCircle size={14} />
                            <span>Success</span>
                          </Badge>
                        ) : transaction.status === 'failed' ? (
                          <Badge variant="destructive" className="flex items-center gap-1">
                            <AlertCircle size={14} />
                            <span>Failed</span>
                          </Badge>
                        ) : (
                          <Badge variant="secondary" className="flex items-center gap-1">
                            <Clock size={14} />
                            <span>Pending</span>
                          </Badge>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
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
          </div>
        </div>
      </Container>
    </MainLayout>
  );
};

export default Dashboard; 