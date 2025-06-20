import { NextPage } from 'next';
import { useState, useEffect } from 'react';
import ProtectedRoute from '../../components/auth/ProtectedRoute';
import CompanyDashboardLayout from '../../components/layouts/CompanyDashboardLayout';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../components/ui/Card';
import { EnhancedMetricCard, MetricCardGrid } from '../../components/dashboard/EnhancedMetricCard';
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
  Users,
  FileText,
  CheckCircle
} from 'lucide-react';
import EnhancedDashboard from '../../components/dashboard/EnhancedDashboard';
import { useAuth } from '../../context/AuthContext';
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
  const { user } = useAuth();
  
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
        <title>TaxPoynt | Dashboard</title>
      </Head>
      <CompanyDashboardLayout title="Dashboard Overview | Taxpoynt eInvoice" description="View your company's e-invoicing performance and metrics">
        <div className="p-8 bg-gradient-to-b from-slate-50 to-white">
          {/* Hero section with logo and navigation */}
          <div className="flex flex-col space-y-4 md:space-y-0 md:flex-row md:justify-between md:items-center mb-8 bg-gradient-to-r from-blue-600 to-indigo-700 rounded-lg shadow-lg p-6 text-white">
            <div className="flex items-center">
              <div className="mr-4 bg-white p-2 rounded-lg shadow-md flex items-center justify-center" style={{ width: '44px', height: '44px' }}>
                {/* Using SVG directly instead of external image to prevent shakiness */}
                <svg width="32" height="32" viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M32 0C14.327 0 0 14.327 0 32C0 49.673 14.327 64 32 64C49.673 64 64 49.673 64 32C64 14.327 49.673 0 32 0ZM32 12C38.627 12 44 17.373 44 24C44 30.627 38.627 36 32 36C25.373 36 20 30.627 20 24C20 17.373 25.373 12 32 12ZM32 56C24.36 56 17.56 52.36 13.6 46.64C13.8 39.32 27.2 35.2 32 35.2C36.76 35.2 50.2 39.32 50.4 46.64C46.44 52.36 39.64 56 32 56Z" fill="#4F46E5"/>
                </svg>
              </div>
              <div>
                <Typography.Heading level="h1" className="text-white">TaxPoynt Dashboard</Typography.Heading>
                <p className="text-blue-100 text-sm">Monitor your e-Invoice performance metrics</p>
              </div>
            </div>
            <div className="flex space-x-3">
              <Link href="/firs-test?dev=true" passHref>
                <Button 
                  variant="secondary" 
                  size="sm" 
                  className="flex items-center gap-2 bg-white/10 hover:bg-white/20 text-white border-white/20"
                  onClick={(e) => {
                    // Set dev mode in local storage to ensure persistence
                    if (typeof window !== 'undefined') {
                      // Set authentication tokens if needed for development
                      localStorage.setItem('dev_mode', 'true');
                      localStorage.setItem('auth_token', 'temp_dev_token_' + Date.now());
                      localStorage.setItem('user_permissions', JSON.stringify(['firs_api_access', 'dashboard_access']));
                    }
                  }}
                >
                  <FileBarChart size={16} />
                  FIRS Testing Dashboard
                </Button>
              </Link>
              <Button 
                variant="outline" 
                className="bg-blue-500 hover:bg-blue-600 text-white border-blue-400 hover:border-blue-500 font-medium"
                onClick={handleRefresh}
                disabled={isLoading}
              >
                {isLoading ? (
                  <>
                    <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                    Refreshing...
                  </>
                ) : (
                  <>
                    <RefreshCw className="h-4 w-4 mr-2" />
                    Refresh
                  </>
                )}
              </Button>
            </div>
          </div>

          {/* Enhanced metric cards with animations and mobile-first design */}
          <MetricCardGrid className="mb-8">
            <EnhancedMetricCard
              title="Total Invoices (Today)"
              value={summary?.irn_summary?.total_irns || 1245}
              previousValue={summary?.irn_summary?.total_irns ? Math.floor(summary.irn_summary.total_irns * 0.92) : 1145}
              icon={<FileText className="w-6 h-6" />}
              countUp={true}
              animationDuration={2000}
              onClick={() => window.location.href = '/dashboard/metrics'}
            />
            
            <EnhancedMetricCard
              title="Weekly Transactions"
              value={summary?.odoo_summary?.total_invoices || 1028}
              previousValue={summary?.odoo_summary?.total_invoices ? Math.floor(summary.odoo_summary.total_invoices * 0.88) : 905}
              icon={<BarChart3 className="w-6 h-6" />}
              countUp={true}
              animationDuration={2200}
              onClick={() => window.location.href = '/dashboard/integrations'}
            />
            
            <EnhancedMetricCard
              title="Monthly Transactions"
              value={summary?.system_summary?.total_requests || 2456}
              previousValue={summary?.system_summary?.total_requests ? Math.floor(summary.system_summary.total_requests * 0.85) : 2088}
              icon={<LineChart className="w-6 h-6" />}
              countUp={true}
              animationDuration={2400}
              onClick={() => window.location.href = '/dashboard/metrics'}
            />
            
            <EnhancedMetricCard
              title="Success Rate"
              value={summary?.validation_summary?.success_rate || 94.6}
              previousValue={summary?.validation_summary?.success_rate ? summary.validation_summary.success_rate - 0.8 : 93.8}
              suffix="%"
              precision={1}
              icon={<CheckCircle className="w-6 h-6" />}
              countUp={true}
              animationDuration={1800}
              onClick={() => window.location.href = '/dashboard/validation-stats'}
            />
          </MetricCardGrid>
          
          {/* Enhanced Dashboard with Platform Components */}
          <EnhancedDashboard organizationId={(user as any)?.organization_id || ''} />
          
          {/* Main content cards with modern styling */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-white rounded-lg shadow-lg border border-gray-100 overflow-hidden transition-all duration-300 hover:shadow-xl">
              <div className="border-b border-gray-100 p-5">
                <h3 className="text-lg font-bold text-gray-800">Integration Status</h3>
                <p className="text-sm text-gray-500">Status of connected integrations</p>
              </div>
              <div className="p-5">
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
              </div>
            </div>
            
            <div className="bg-white rounded-lg shadow-lg border border-gray-100 overflow-hidden transition-all duration-300 hover:shadow-xl">
              <div className="border-b border-gray-100 p-5">
                <h3 className="text-lg font-bold text-gray-800">Transaction Metrics</h3>
                <p className="text-sm text-gray-500">Weekly transaction volume</p>
              </div>
              <div className="p-5">
                <div className="h-64 flex items-center justify-center bg-background-alt rounded-md">
                  <Typography.Text variant="secondary">Chart placeholder - will display transaction metrics</Typography.Text>
                </div>
              </div>
            </div>
          </div>

          {/* Secondary content cards with modern styling */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
            <div className="bg-white rounded-lg shadow-lg border border-gray-100 overflow-hidden transition-all duration-300 hover:shadow-xl">
              <div className="border-b border-gray-100 p-5">
                <h3 className="text-lg font-bold text-gray-800">Recent Transactions</h3>
                <p className="text-sm text-gray-500">Latest system activity</p>
              </div>
              <div className="p-5">
                {/* Transaction log table with horizontal scroll capability */}
                <TransactionLogTable 
                  transactions={[]}
                  isLoading={isLoading}
                />
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-lg border border-gray-100 overflow-hidden transition-all duration-300 hover:shadow-xl">
              <div className="border-b border-gray-100 p-5">
                <h3 className="text-lg font-bold text-gray-800">Error Rate</h3>
                <p className="text-sm text-gray-500">Daily error percentage</p>
              </div>
              <div className="p-5">
                <div className="h-64 flex items-center justify-center bg-background-alt rounded-md">
                  <Typography.Text variant="secondary">Chart placeholder - will display error rates</Typography.Text>
                </div>
              </div>
            </div>
          </div>
          
          {/* Workflow visualization section */}
          <div className="mt-10 px-4 py-8 bg-white rounded-lg shadow-lg border border-gray-200">
            <h2 className="text-2xl font-bold text-gray-800 mb-6 text-center">Complete E2E eInvoice Workflow</h2>
            <div className="flex flex-col md:flex-row justify-between items-center max-w-4xl mx-auto">
              <div className="flex flex-col items-center p-4 transition-all duration-300 transform hover:scale-105">
                <div className="bg-blue-100 p-4 rounded-full mb-3">
                  <svg className="h-8 w-8 text-blue-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M20 7h-7m0 0v7m0-7l-3-3m-3-3H4m0 0v7m0-7l3-3" />
                  </svg>
                </div>
                <h3 className="font-bold text-lg text-center">Odoo Integration</h3>
                <p className="text-gray-600 text-center text-sm mt-2">Fetch invoice data from Odoo</p>
              </div>
              
              <div className="hidden md:block text-blue-500">
                <svg className="h-8 w-8" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M5 12h14M12 5l7 7-7 7" />
                </svg>
              </div>
              
              <div className="flex flex-col items-center p-4 transition-all duration-300 transform hover:scale-105">
                <div className="bg-indigo-100 p-4 rounded-full mb-3">
                  <svg className="h-8 w-8 text-indigo-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M14 3v4a1 1 0 001 1h4" />
                    <path d="M17 21H7a2 2 0 01-2-2V5a2 2 0 012-2h7l5 5v11a2 2 0 01-2 2z" />
                  </svg>
                </div>
                <h3 className="font-bold text-lg text-center">UBL Transformation</h3>
                <p className="text-gray-600 text-center text-sm mt-2">Convert to BIS Billing 3.0 format</p>
              </div>
              
              <div className="hidden md:block text-blue-500">
                <svg className="h-8 w-8" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M5 12h14M12 5l7 7-7 7" />
                </svg>
              </div>
              
              <div className="flex flex-col items-center p-4 transition-all duration-300 transform hover:scale-105">
                <div className="bg-green-100 p-4 rounded-full mb-3">
                  <svg className="h-8 w-8 text-green-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <h3 className="font-bold text-lg text-center">FIRS Submission</h3>
                <p className="text-gray-600 text-center text-sm mt-2">Submit to FIRS & check status</p>
              </div>
            </div>
          </div>
        </div>
      </CompanyDashboardLayout>
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