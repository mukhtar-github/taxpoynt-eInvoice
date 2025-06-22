/**
 * Access Point Provider (APP) Dashboard
 * 
 * Dedicated dashboard for users who want to manage certificates,
 * compliance, transmission, and digital signatures
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
  Shield,
  FileText,
  Activity,
  Settings,
  ArrowLeft,
  CheckCircle,
  AlertCircle
} from 'lucide-react';
import Link from 'next/link';

const APPDashboard: NextPage = () => {
  const router = useRouter();

  return (
    <>
      <Head>
        <title>Access Point Provider (APP) Dashboard | TaxPoynt eInvoice</title>
        <meta name="description" content="Manage certificates, compliance, transmission, and digital signatures" />
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
              <h1 className="text-2xl font-bold">Access Point Provider (APP) Dashboard</h1>
              <p className="text-gray-600">Manage certificates, compliance & secure transmission</p>
            </div>
          </div>

          {/* Coming Soon Notice */}
          <Card className="mb-6 border-cyan-200 bg-cyan-50">
            <CardContent className="p-6">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-cyan-100 rounded-lg">
                  <Shield className="w-6 h-6 text-cyan-600" />
                </div>
                <div>
                  <h3 className="font-semibold text-cyan-900">APP Dashboard Implementation</h3>
                  <p className="text-cyan-700 text-sm">
                    This dashboard will replace the existing platform dashboard with improved
                    navigation and clearer focus on Access Point Provider services.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Temporary redirect to existing platform dashboard */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Activity className="w-5 h-5" />
                Current Implementation
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-gray-600">
                While we finalize the new APP dashboard, you can access your certificate management,
                transmission monitoring, and compliance features through the existing platform dashboard.
              </p>
              
              <div className="flex items-center gap-4">
                <Button asChild>
                  <Link href="/dashboard/platform">
                    Go to Platform Dashboard
                  </Link>
                </Button>
                
                <div className="flex items-center gap-2 text-sm text-gray-500">
                  <CheckCircle className="w-4 h-4 text-green-500" />
                  <span>Temporary redirect</span>
                </div>
              </div>

              <div className="mt-6 p-4 bg-gray-50 rounded-lg">
                <h4 className="font-medium mb-2">What's coming in the new APP Dashboard:</h4>
                <ul className="text-sm text-gray-600 space-y-1">
                  <li>• Unified certificate lifecycle management</li>
                  <li>• Real-time transmission monitoring with WebSocket updates</li>
                  <li>• Enhanced compliance tracking and reporting</li>
                  <li>• Improved digital signature management</li>
                  <li>• Better integration with FIRS APIs</li>
                  <li>• Cleaner separation from SI services</li>
                </ul>
              </div>
              
              <div className="mt-4 p-4 bg-blue-50 rounded-lg border border-blue-200">
                <div className="flex items-start gap-2">
                  <AlertCircle className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" />
                  <div>
                    <h4 className="font-medium text-blue-900">Important Note</h4>
                    <p className="text-sm text-blue-700 mt-1">
                      In our codebase, we use "platform" to avoid conflicts with the reserved "app" directory name.
                      However, in the user interface, we maintain the "Access Point Provider (APP)" terminology 
                      that users are familiar with.
                    </p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </AppDashboardLayout>
    </>
  );
};

// Wrap with ProtectedRoute
const ProtectedAPPDashboard: NextPage = () => {
  return (
    <ProtectedRoute>
      <APPDashboard />
    </ProtectedRoute>
  );
};

export default ProtectedAPPDashboard;