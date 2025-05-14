import { NextPage } from 'next';
import { useState, useEffect } from 'react';
import ProtectedRoute from '../../components/auth/ProtectedRoute';
import DashboardLayout from '../../components/layouts/DashboardLayout';
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardGrid, MetricCard } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { Table, TableContainer, TableHeader, TableRow, TableHead, TableBody, TableCell, TableEmpty } from '../../components/ui/Table';
import Link from 'next/link';
import { 
  BarChart3, 
  LineChart, 
  Activity, 
  Server, 
  FileBarChart,
  ShieldCheck,
  Layers,
  Settings,
  RefreshCw,
  TrendingUp,
  Users
} from 'lucide-react';
import Head from 'next/head';
import { fetchDashboardSummary } from '../../services/dashboardService';
import axios, { AxiosError } from 'axios';
import { TransactionLogTable } from '@/components/ui/ResponsiveTable';
import Typography from '@/components/ui/Typography';

// Dashboard module definitions for navigation
const dashboardModules = [
  { 
    id: 'overview', 
    name: 'Dashboard Overview', 
    description: 'Summary of all system components and metrics',
    icon: <Activity className="h-8 w-8" />,
    path: '/dashboard',
    color: 'bg-blue-50 dark:bg-blue-950'
  },
  { 
    id: 'metrics', 
    name: 'Detailed Metrics', 
    description: 'In-depth analytics and performance metrics',
    icon: <BarChart3 className="h-8 w-8" />,
    path: '/dashboard/metrics',
    color: 'bg-emerald-50 dark:bg-emerald-950'
  },
  { 
    id: 'irn', 
    name: 'IRN Monitoring', 
    description: 'Invoice Reference Number generation tracking',
    icon: <FileBarChart className="h-8 w-8" />,
    path: '/dashboard/irn-monitoring',
    color: 'bg-indigo-50 dark:bg-indigo-950'
  },
  { 
    id: 'validation', 
    name: 'Validation Statistics', 
    description: 'Invoice validation success rates and errors',
    icon: <ShieldCheck className="h-8 w-8" />,
    path: '/dashboard/validation-stats',
    color: 'bg-violet-50 dark:bg-violet-950'
  },
  { 
    id: 'integration', 
    name: 'Integration Status', 
    description: 'Status of Odoo and other system integrations',
    icon: <Layers className="h-8 w-8" />,
    path: '/dashboard/integration-status',
    color: 'bg-amber-50 dark:bg-amber-950'
  },
  { 
    id: 'system', 
    name: 'System Health', 
    description: 'API performance and infrastructure health metrics',
    icon: <Server className="h-8 w-8" />,
    path: '/dashboard/system-health',
    color: 'bg-rose-50 dark:bg-rose-950'
  },
  { 
    id: 'b2b', 
    name: 'B2B vs B2C Analytics', 
    description: 'Comparison of business vs consumer invoices',
    icon: <Users className="h-8 w-8" />,
    path: '/dashboard/b2b-vs-b2c',
    color: 'bg-purple-50 dark:bg-purple-950'
  }
];

// Interface for the dashboard summary
interface DashboardSummaryData {
  timestamp: string;
  irn_summary: {
    total_irns: number;
    active_irns: number;
    unused_irns: number;
    expired_irns: number;
  };
  validation_summary: {
    total_validations: number;
    success_rate: number;
    common_errors: Array<{
      error_code: string;
      count: number;
      percentage: number;
    }>;
  };
  b2b_vs_b2c_summary: {
    b2b_percentage: number;
    b2c_percentage: number;
    b2b_success_rate: number;
    b2c_success_rate: number;
  };
  odoo_summary: {
    active_integrations: number;
    total_invoices: number;
    success_rate: number;
  };
  system_summary: {
    total_requests: number;
    error_rate: number;
    avg_response_time: number;
  };
}

const DashboardHub: NextPage = () => {
  const [summary, setSummary] = useState<DashboardSummaryData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Fetch dashboard summary if available
  useEffect(() => {
    const fetchSummary = async () => {
      try {
        setIsLoading(true);
        setError(null);
        const data = await fetchDashboardSummary();
        setSummary(data);
      } catch (err) {
        console.error('Error fetching dashboard summary', err);
        // Properly handle and display the error message
        if (axios.isAxiosError(err)) {
          const axiosError = err as AxiosError;
          setError((axiosError.response?.data as any)?.detail || 'Failed to load dashboard data');
        } else {
          setError('Failed to load dashboard data');
        }
      } finally {
        setIsLoading(false);
      }
    };
    
    fetchSummary();
  }, []);
  
  const handleRefresh = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const data = await fetchDashboardSummary();
      setSummary(data);
    } catch (err) {
      console.error('Error refreshing dashboard data', err);
      if (axios.isAxiosError(err)) {
        const axiosError = err as AxiosError;
        setError((axiosError.response?.data as any)?.detail || 'Failed to refresh dashboard data');
      } else {
        setError('Failed to refresh dashboard data');
      }
    } finally {
      setIsLoading(false);
    }
  };

  // Helper function to format dates
  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'Never';
    return new Date(dateString).toLocaleString();
  };

  return (
    <>
      <Head>
        <title>FIRS e-Invoice | Dashboard Navigation</title>
      </Head>
      <DashboardLayout>
        <div className="p-8">
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
              value={summary?.irn_summary.total_irns.toString() || '0'}
            />
            <MetricCard
              title="Weekly Transactions"
              value={summary?.odoo_summary.total_invoices.toString() || '0'}
            />
            <MetricCard
              title="Monthly Transactions"
              value={summary?.system_summary.total_requests.toString() || '0'}
            />
            <MetricCard
              title="Success Rate"
              value={`${summary?.validation_summary.success_rate}%`}
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
                      {summary?.odoo_summary?.active_integrations === 0 ? (
                        <TableEmpty colSpan={4} message="No integrations found" />
                      ) : (
                        Array.from({ length: summary?.odoo_summary?.active_integrations ?? 0 }, (_, index) => (
                          <TableRow key={index}>
                            <TableCell>Integration {index + 1}</TableCell>
                            <TableCell>Client {index + 1}</TableCell>
                            <TableCell>
                              <Badge 
                                variant={
                                  (summary?.odoo_summary?.success_rate ?? 0) > 0.5 ? 'success' : 
                                  (summary?.odoo_summary?.success_rate ?? 0) < 0.5 ? 'destructive' : 
                                  'secondary'
                                }
                              >
                                {(summary?.odoo_summary?.success_rate ?? 0) > 0.5 ? 'Active' : 
                                (summary?.odoo_summary?.success_rate ?? 0) < 0.5 ? 'Error' : 
                                'Unknown'}
                              </Badge>
                            </TableCell>
                            <TableCell>{formatDate(summary?.timestamp ?? null)}</TableCell>
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
                  transactions={[]}
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
        </div>
      </DashboardLayout>
    </>
  );
};

// Wrap the component with the ProtectedRoute component
const ProtectedDashboardHub: NextPage = () => {
  return (
    <ProtectedRoute>
      <DashboardHub />
    </ProtectedRoute>
  );
};

export default ProtectedDashboardHub;