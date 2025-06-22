/**
 * System Integration (SI) Dashboard
 * 
 * Dedicated dashboard for users who want to manage ERP integrations,
 * invoices, customers, and products
 */

import React from 'react';
import { NextPage } from 'next';
import { useRouter } from 'next/router';
import Head from 'next/head';
import ProtectedRoute from '../../components/auth/ProtectedRoute';
import AppDashboardLayout from '../../components/layouts/AppDashboardLayout';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Badge } from '../../components/ui/Badge';
import { 
  Database,
  FileText,
  Users,
  Package,
  ArrowLeft,
  Activity,
  CheckCircle,
  AlertCircle
} from 'lucide-react';
import Link from 'next/link';

const SIDashboard: NextPage = () => {
  const router = useRouter();

  return (
    <>
      <Head>
        <title>System Integration (SI) Dashboard | TaxPoynt eInvoice</title>
        <meta name="description" content="Manage your ERP integrations, invoices, customers, and products" />
      </Head>
      
      <AppDashboardLayout>
        <div className="container mx-auto px-4 py-6">
          {/* Header with back navigation */}
          <div className="flex items-center gap-4 mb-6">
            <Button 
              variant="outline" 
              size="sm"
              onClick={() => router.push('/dashboard')}
              className="flex items-center gap-2"
            >
              <ArrowLeft className="w-4 h-4" />
              Back to Service Selection
            </Button>
            <div>
              <h1 className="text-2xl font-bold">System Integration (SI) Dashboard</h1>
              <p className="text-gray-600">Manage your ERP systems and business data</p>
            </div>
          </div>

          {/* Coming Soon Notice */}
          <Card className="mb-6 border-blue-200 bg-blue-50">
            <CardContent className="p-6">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-blue-100 rounded-lg">
                  <Database className="w-6 h-6 text-blue-600" />
                </div>
                <div>
                  <h3 className="font-semibold text-blue-900">SI Dashboard Implementation</h3>
                  <p className="text-blue-700 text-sm">
                    This dashboard will replace the existing company-home dashboard with improved
                    navigation and clearer focus on ERP integration services.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Temporary redirect to existing company dashboard */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Activity className="w-5 h-5" />
                Current Implementation
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-gray-600">
                While we finalize the new SI dashboard, you can access your ERP integration 
                features through the existing company dashboard.
              </p>
              
              <div className="flex items-center gap-4">
                <Button asChild>
                  <Link href="/dashboard/company-home">
                    Go to Company Dashboard
                  </Link>
                </Button>
                
                <div className="flex items-center gap-2 text-sm text-gray-500">
                  <CheckCircle className="w-4 h-4 text-green-500" />
                  <span>Temporary redirect</span>
                </div>
              </div>

              <div className="mt-6 p-4 bg-gray-50 rounded-lg">
                <h4 className="font-medium mb-2">What's coming in the new SI Dashboard:</h4>
                <ul className="text-sm text-gray-600 space-y-1">
                  <li>• Enhanced ERP connection management</li>
                  <li>• Real-time data synchronization status</li>
                  <li>• Improved invoice, customer, and product management</li>
                  <li>• Better integration with WebSocket real-time updates</li>
                  <li>• Cleaner separation from APP services</li>
                </ul>
              </div>
            </CardContent>
          </Card>
        </div>
      </AppDashboardLayout>
    </>
  );
};

// Wrap with ProtectedRoute
const ProtectedSIDashboard: NextPage = () => {
  return (
    <ProtectedRoute>
      <SIDashboard />
    </ProtectedRoute>
  );
};

export default ProtectedSIDashboard;