import { useState, useEffect } from 'react';
import CompanyDashboardLayout from '../../components/layouts/CompanyDashboardLayout';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { Typography } from '../../components/ui/Typography';
import { Spinner } from '../../components/ui/Spinner';
import { 
  BarChart2, 
  Database, 
  Package, 
  Users, 
  FileText, 
  ChevronRight,
  Zap,
  AlertCircle
} from 'lucide-react';
import Link from 'next/link';
import { useAuth } from '../../context/AuthContext';
import axios from 'axios';

// Types for ERP connection status
interface ERPConnection {
  type: string;
  status: 'connected' | 'disconnected' | 'pending';
  lastSync: string | null;
  url: string;
}

// Types for company dashboard summary
interface CompanyDashboardSummary {
  company: {
    name: string;
    logo_url: string | null;
  };
  erp: {
    connection: ERPConnection | null;
    invoice_count: number;
    customer_count: number;
    product_count: number;
  };
  recent_activity: Array<{
    id: string;
    type: 'invoice' | 'customer' | 'product';
    name: string;
    timestamp: string;
  }>;
}

// Mock data for the dashboard
const mockDashboardData: CompanyDashboardSummary = {
  company: {
    name: 'MT Garba Global Ventures',
    logo_url: null
  },
  erp: {
    connection: {
      type: 'odoo',
      status: 'connected',
      lastSync: '2025-05-26T15:30:00Z',
      url: 'https://mtgarba.odoo.com'
    },
    invoice_count: 543,
    customer_count: 128,
    product_count: 87
  },
  recent_activity: [
    { id: '1', type: 'invoice', name: 'INV-2025-0103', timestamp: '2025-05-26T16:45:00Z' },
    { id: '2', type: 'customer', name: 'Lagos State University', timestamp: '2025-05-26T14:22:00Z' },
    { id: '3', type: 'invoice', name: 'INV-2025-0102', timestamp: '2025-05-26T12:18:00Z' },
    { id: '4', type: 'product', name: 'Consulting Services', timestamp: '2025-05-26T09:45:00Z' },
    { id: '5', type: 'invoice', name: 'INV-2025-0101', timestamp: '2025-05-25T17:33:00Z' }
  ]
};

const CompanyDashboardHome = () => {
  const [dashboardData, setDashboardData] = useState<CompanyDashboardSummary | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { isAuthenticated } = useAuth();

  // Fetch dashboard data
  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        setIsLoading(true);
        setError(null);
        
        // In a real implementation, this would fetch from the API
        // For now, use mock data with a small delay to simulate API call
        await new Promise(resolve => setTimeout(resolve, 1000));
        setDashboardData(mockDashboardData);
      } catch (err) {
        console.error('Error fetching dashboard data:', err);
        setError('Failed to load dashboard data');
      } finally {
        setIsLoading(false);
      }
    };
    
    if (isAuthenticated) {
      fetchDashboardData();
    }
  }, [isAuthenticated]);

  // Format date
  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'Never';
    const date = new Date(dateString);
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
      hour12: true
    });
  };

  // Loading state
  if (isLoading) {
    return (
      <CompanyDashboardLayout title="Company Dashboard | TaxPoynt eInvoice">
        <div className="flex justify-center items-center h-64">
          <Spinner size="lg" />
          <span className="ml-3">Loading dashboard data...</span>
        </div>
      </CompanyDashboardLayout>
    );
  }

  // Error state
  if (error || !dashboardData) {
    return (
      <CompanyDashboardLayout title="Company Dashboard | TaxPoynt eInvoice">
        <div className="bg-red-50 border border-red-200 text-red-800 rounded-lg p-4 mb-6">
          <div className="flex items-center">
            <AlertCircle className="h-5 w-5 mr-2" />
            <Typography.Heading level="h3">Error Loading Dashboard</Typography.Heading>
          </div>
          <Typography.Text className="mt-2">
            {error || 'Unable to load dashboard data. Please try again later.'}
          </Typography.Text>
          <Button 
            variant="outline" 
            className="mt-3"
            onClick={() => window.location.reload()}
          >
            Retry
          </Button>
        </div>
      </CompanyDashboardLayout>
    );
  }

  return (
    <CompanyDashboardLayout title="Company Dashboard | TaxPoynt eInvoice">
      {/* Welcome section */}
      <div className="bg-gradient-to-r from-indigo-600 to-indigo-800 rounded-lg shadow-lg p-6 text-white mb-8">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between">
          <div>
            <Typography.Heading level="h1" className="text-white mb-2">
              Welcome to your dashboard
            </Typography.Heading>
            <Typography.Text className="text-indigo-100">
              Manage your invoices, customers, and ERP connections from one place
            </Typography.Text>
          </div>
          <div className="mt-4 md:mt-0">
            <Button 
              variant="default" 
              className="bg-white text-indigo-700 hover:bg-indigo-50"
              asChild
            >
              <Link href="/dashboard/erp-connection">
                {dashboardData.erp.connection ? 'Manage ERP Connection' : 'Connect ERP System'}
              </Link>
            </Button>
          </div>
        </div>
      </div>

      {/* ERP Connection Status */}
      <div className="mb-8">
        <div className="flex justify-between items-center mb-4">
          <Typography.Heading level="h2">
            ERP Connection
          </Typography.Heading>
          {dashboardData.erp.connection && (
            <Badge variant={dashboardData.erp.connection.status === 'connected' ? 'success' : 'warning'}>
              {dashboardData.erp.connection.status === 'connected' ? 'Connected' : 'Disconnected'}
            </Badge>
          )}
        </div>

        <Card>
          <CardContent className="p-6">
            {dashboardData.erp.connection ? (
              <div className="flex flex-col md:flex-row md:items-center md:justify-between">
                <div>
                  <div className="flex items-center">
                    <Database className="h-5 w-5 text-indigo-600 mr-2" />
                    <Typography.Heading level="h3" className="capitalize">
                      {dashboardData.erp.connection.type} Integration
                    </Typography.Heading>
                  </div>
                  <Typography.Text className="text-gray-500 mt-1">
                    URL: {dashboardData.erp.connection.url}
                  </Typography.Text>
                  <Typography.Text className="text-gray-500">
                    Last synchronized: {formatDate(dashboardData.erp.connection.lastSync)}
                  </Typography.Text>
                </div>
                <div className="mt-4 md:mt-0 space-x-2">
                  <Button variant="outline">
                    Sync Now
                  </Button>
                  <Button variant="default" asChild>
                    <Link href="/dashboard/erp-connection">
                      Manage
                    </Link>
                  </Button>
                </div>
              </div>
            ) : (
              <div className="text-center py-6">
                <Database className="h-12 w-12 text-gray-300 mx-auto mb-3" />
                <Typography.Heading level="h3" className="mb-2">
                  No ERP Connection
                </Typography.Heading>
                <Typography.Text className="text-gray-500 mb-4">
                  Connect your Odoo ERP system to manage invoices, customers, and products
                </Typography.Text>
                <Button asChild>
                  <Link href="/dashboard/erp-connection">
                    Connect ERP System
                  </Link>
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Data Overview */}
      <div className="mb-8">
        <Typography.Heading level="h2" className="mb-4">
          Data Overview
        </Typography.Heading>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card>
            <CardContent className="p-0">
              <Link href="/dashboard/invoices" className="block p-6 hover:bg-gray-50 transition-colors rounded-lg">
                <div className="flex justify-between items-start">
                  <div>
                    <div className="flex items-center">
                      <div className="bg-indigo-100 p-2 rounded-lg mr-3">
                        <FileText className="h-5 w-5 text-indigo-600" />
                      </div>
                      <Typography.Heading level="h3">
                        Invoices
                      </Typography.Heading>
                    </div>
                    <Typography.Heading level="h2" className="text-2xl font-bold mt-2">
                      {dashboardData.erp.invoice_count.toLocaleString()}
                    </Typography.Heading>
                  </div>
                  <ChevronRight className="h-5 w-5 text-gray-400" />
                </div>
              </Link>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-0">
              <Link href="/dashboard/customers" className="block p-6 hover:bg-gray-50 transition-colors rounded-lg">
                <div className="flex justify-between items-start">
                  <div>
                    <div className="flex items-center">
                      <div className="bg-emerald-100 p-2 rounded-lg mr-3">
                        <Users className="h-5 w-5 text-emerald-600" />
                      </div>
                      <Typography.Heading level="h3">
                        Customers
                      </Typography.Heading>
                    </div>
                    <Typography.Heading level="h2" className="text-2xl font-bold mt-2">
                      {dashboardData.erp.customer_count.toLocaleString()}
                    </Typography.Heading>
                  </div>
                  <ChevronRight className="h-5 w-5 text-gray-400" />
                </div>
              </Link>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-0">
              <Link href="/dashboard/products" className="block p-6 hover:bg-gray-50 transition-colors rounded-lg">
                <div className="flex justify-between items-start">
                  <div>
                    <div className="flex items-center">
                      <div className="bg-amber-100 p-2 rounded-lg mr-3">
                        <Package className="h-5 w-5 text-amber-600" />
                      </div>
                      <Typography.Heading level="h3">
                        Products
                      </Typography.Heading>
                    </div>
                    <Typography.Heading level="h2" className="text-2xl font-bold mt-2">
                      {dashboardData.erp.product_count.toLocaleString()}
                    </Typography.Heading>
                  </div>
                  <ChevronRight className="h-5 w-5 text-gray-400" />
                </div>
              </Link>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="mb-8">
        <div className="flex justify-between items-center mb-4">
          <Typography.Heading level="h2">
            Recent Activity
          </Typography.Heading>
          <Button variant="ghost" size="sm" asChild>
            <Link href="/dashboard/activity">
              View All
            </Link>
          </Button>
        </div>

        <Card>
          <CardContent className="p-0">
            <ul className="divide-y divide-gray-200">
              {dashboardData.recent_activity.map((activity) => (
                <li key={activity.id} className="p-4 hover:bg-gray-50">
                  <div className="flex items-center">
                    <div className={`p-2 rounded-full mr-3 ${
                      activity.type === 'invoice' ? 'bg-indigo-100' : 
                      activity.type === 'customer' ? 'bg-emerald-100' : 
                      'bg-amber-100'
                    }`}>
                      {activity.type === 'invoice' && <FileText className="h-4 w-4 text-indigo-600" />}
                      {activity.type === 'customer' && <Users className="h-4 w-4 text-emerald-600" />}
                      {activity.type === 'product' && <Package className="h-4 w-4 text-amber-600" />}
                    </div>
                    <div className="flex-1">
                      <Typography.Text className="font-medium">
                        {activity.name}
                      </Typography.Text>
                      <Typography.Text className="text-sm text-gray-500">
                        {activity.type.charAt(0).toUpperCase() + activity.type.slice(1)} • {formatDate(activity.timestamp)}
                      </Typography.Text>
                    </div>
                    <Button variant="ghost" size="icon" className="ml-2">
                      <ChevronRight className="h-4 w-4" />
                    </Button>
                  </div>
                </li>
              ))}

              {dashboardData.recent_activity.length === 0 && (
                <li className="py-8 px-4 text-center">
                  <Typography.Text className="text-gray-500">
                    No recent activity found
                  </Typography.Text>
                </li>
              )}
            </ul>
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <div>
        <Typography.Heading level="h2" className="mb-4">
          Quick Actions
        </Typography.Heading>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Button 
            variant="outline" 
            className="h-auto py-3 px-4 justify-start"
            asChild
          >
            <Link href="/dashboard/erp-connection/sync">
              <Zap className="h-4 w-4 mr-2" />
              Sync Data
            </Link>
          </Button>
          
          <Button 
            variant="outline" 
            className="h-auto py-3 px-4 justify-start"
            asChild
          >
            <Link href="/dashboard/invoices/new">
              <FileText className="h-4 w-4 mr-2" />
              Create Invoice
            </Link>
          </Button>
          
          <Button 
            variant="outline" 
            className="h-auto py-3 px-4 justify-start"
            asChild
          >
            <Link href="/dashboard/customers/new">
              <Users className="h-4 w-4 mr-2" />
              Add Customer
            </Link>
          </Button>
          
          <Button 
            variant="outline" 
            className="h-auto py-3 px-4 justify-start"
            asChild
          >
            <Link href="/dashboard/products/new">
              <Package className="h-4 w-4 mr-2" />
              Add Product
            </Link>
          </Button>
        </div>
      </div>
    </CompanyDashboardLayout>
  );
};

export default CompanyDashboardHome;
