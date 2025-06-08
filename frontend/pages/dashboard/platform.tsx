import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../components/ui/Tabs';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Badge } from '../../components/ui/Badge';
import { 
  Layers,
  Shield,
  Activity,
  FileText,
  Bell,
  Settings,
  HelpCircle,
  ChevronRight
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import AppDashboardLayout from '../../components/layouts/AppDashboardLayout';
import CertificateManagementInterface from '../../components/platform/certificate/CertificateManagementInterface';
import TransmissionMonitoringDashboard from '../../components/platform/transmission/TransmissionMonitoringDashboard';
import ComplianceSummaryVisualization from '../../components/platform/compliance/ComplianceSummaryVisualization';
import ContextualHelp from '../../components/platform/common/ContextualHelp';


// Help content for platform dashboard
const platformHelp = {
  overview: "The Platform Dashboard provides a centralized view of all your e-invoicing platform functionality.",
  certificate: "Manage digital certificates required for signing electronic invoices in compliance with FIRS regulations.",
  transmission: "Monitor and manage the transmission of e-invoices to FIRS, including statistics and error handling.",
  compliance: "Track your compliance status with FIRS regulations and identify areas for improvement."
};

const PlatformDashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState<string>('overview');
  const [organizationId, setOrganizationId] = useState<string>('');
  const router = useRouter();
  const { user, isLoading } = useAuth();

  
  useEffect(() => {
    // If user exists, we'll use their ID as the organization ID for now
    // In a real implementation, you might fetch the organization ID from an API
    if (user && user.id) {
      setOrganizationId(user.id);
    }
    
    // Check if tab is specified in URL
    if (router.query.tab && typeof router.query.tab === 'string') {
      setActiveTab(router.query.tab);
    }
  }, [user, router.query]);
  
  // Handle tab change
  const handleTabChange = (value: string) => {
    setActiveTab(value);
    
    // Update URL without reloading the page
    router.push(
      {
        pathname: router.pathname,
        query: { ...router.query, tab: value },
      },
      undefined,
      { shallow: true }
    );
  };
  
  if (isLoading) {
    return (
      <AppDashboardLayout>
        <div className="flex justify-center items-center h-96">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-cyan-500"></div>
        </div>
      </AppDashboardLayout>
    );
  }
  
  if (!user || !organizationId) {
    return (
      <AppDashboardLayout>
        <div className="text-center p-8">
          <h2 className="text-xl font-semibold text-gray-800">Authentication Required</h2>
          <p className="mt-2 text-gray-600">Please log in to access the Platform Dashboard.</p>
          <Button 
            className="mt-4"
            onClick={() => router.push('/auth/login')}
          >
            Go to Login
          </Button>
        </div>
      </AppDashboardLayout>
    );
  }
  
  return (
    <AppDashboardLayout>
      <div className="container mx-auto px-4 py-6">
        <div className="mb-6">
          <div className="flex justify-between items-center">
            <div className="flex items-center">
              <Layers className="h-6 w-6 text-cyan-600 mr-2" />
              <h1 className="text-2xl font-bold text-gray-900">Platform Dashboard</h1>
              <Badge className="ml-3 bg-cyan-100 text-cyan-800">Platform</Badge>
              <ContextualHelp content={platformHelp.overview}>
                <HelpCircle className="h-4 w-4 ml-2 text-gray-400" />
              </ContextualHelp>
            </div>
            <div className="flex space-x-2">
              <Button variant="outline" size="sm">
                <Bell className="h-4 w-4 mr-1" />
                Notifications
              </Button>
              <Button variant="outline" size="sm">
                <Settings className="h-4 w-4 mr-1" />
                Settings
              </Button>
            </div>
          </div>
          <p className="text-gray-500 mt-1">
            Manage certificates, monitor transmissions, and ensure compliance with FIRS regulations.
          </p>
        </div>
        
        <Tabs value={activeTab} onValueChange={handleTabChange}>
          <TabsList className="grid grid-cols-4 mb-8">
            <TabsTrigger value="overview">
              <Layers className="h-4 w-4 mr-2" />
              Overview
            </TabsTrigger>
            <TabsTrigger value="certificates">
              <Shield className="h-4 w-4 mr-2" />
              Certificates
            </TabsTrigger>
            <TabsTrigger value="transmission">
              <Activity className="h-4 w-4 mr-2" />
              Transmission
            </TabsTrigger>
            <TabsTrigger value="compliance">
              <FileText className="h-4 w-4 mr-2" />
              Compliance
            </TabsTrigger>
          </TabsList>
          
          <TabsContent value="overview" className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {/* Certificate Management Card */}
              <Card className="relative overflow-hidden border-l-4 border-l-cyan-500">
                <CardHeader className="pb-2">
                  <CardTitle className="flex items-center">
                    <Shield className="h-5 w-5 text-cyan-600 mr-2" />
                    Certificate Management
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-gray-500 mb-4">
                    Manage digital certificates for e-invoice signing compliant with FIRS regulations.
                  </p>
                  <div className="flex justify-between items-center">
                    <Button 
                      variant="outline" 
                      size="sm"
                      onClick={() => handleTabChange('certificates')}
                    >
                      View Certificates
                      <ChevronRight className="h-4 w-4 ml-1" />
                    </Button>
                    <Badge className="bg-green-100 text-green-800">Active</Badge>
                  </div>
                </CardContent>
              </Card>
              
              {/* Transmission Monitoring Card */}
              <Card className="relative overflow-hidden border-l-4 border-l-cyan-500">
                <CardHeader className="pb-2">
                  <CardTitle className="flex items-center">
                    <Activity className="h-5 w-5 text-cyan-600 mr-2" />
                    Transmission Monitoring
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-gray-500 mb-4">
                    Monitor e-invoice transmissions to FIRS, track status, and handle errors.
                  </p>
                  <div className="flex justify-between items-center">
                    <Button 
                      variant="outline" 
                      size="sm"
                      onClick={() => handleTabChange('transmission')}
                    >
                      View Transmissions
                      <ChevronRight className="h-4 w-4 ml-1" />
                    </Button>
                    <Badge className="bg-blue-100 text-blue-800">Active</Badge>
                  </div>
                </CardContent>
              </Card>
              
              {/* Compliance Summary Card */}
              <Card className="relative overflow-hidden border-l-4 border-l-cyan-500">
                <CardHeader className="pb-2">
                  <CardTitle className="flex items-center">
                    <FileText className="h-5 w-5 text-cyan-600 mr-2" />
                    Compliance Summary
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-gray-500 mb-4">
                    Track compliance with FIRS regulations and get recommendations for improvement.
                  </p>
                  <div className="flex justify-between items-center">
                    <Button 
                      variant="outline" 
                      size="sm"
                      onClick={() => handleTabChange('compliance')}
                    >
                      View Compliance
                      <ChevronRight className="h-4 w-4 ml-1" />
                    </Button>
                    <Badge className="bg-yellow-100 text-yellow-800">85%</Badge>
                  </div>
                </CardContent>
              </Card>
            </div>
            
            {/* Quick Overview Dashboard */}
            <Card>
              <CardHeader>
                <CardTitle>Platform Health Overview</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="bg-white p-4 rounded-lg border shadow-sm">
                    <div className="flex justify-between items-start">
                      <div>
                        <p className="text-sm text-gray-500">Certificate Status</p>
                        <h3 className="text-2xl font-bold mt-1">Active</h3>
                        <p className="text-xs text-gray-500 mt-1">Valid until Jan 15, 2026</p>
                      </div>
                      <div className="p-2 rounded-full bg-green-100">
                        <Shield className="h-5 w-5 text-green-600" />
                      </div>
                    </div>
                  </div>
                  
                  <div className="bg-white p-4 rounded-lg border shadow-sm">
                    <div className="flex justify-between items-start">
                      <div>
                        <p className="text-sm text-gray-500">Transmission Rate</p>
                        <h3 className="text-2xl font-bold mt-1">98.2%</h3>
                        <p className="text-xs text-gray-500 mt-1">Last 24 hours</p>
                      </div>
                      <div className="p-2 rounded-full bg-blue-100">
                        <Activity className="h-5 w-5 text-blue-600" />
                      </div>
                    </div>
                  </div>
                  
                  <div className="bg-white p-4 rounded-lg border shadow-sm">
                    <div className="flex justify-between items-start">
                      <div>
                        <p className="text-sm text-gray-500">Compliance Score</p>
                        <h3 className="text-2xl font-bold mt-1">85%</h3>
                        <p className="text-xs text-gray-500 mt-1">2 issues need attention</p>
                      </div>
                      <div className="p-2 rounded-full bg-yellow-100">
                        <FileText className="h-5 w-5 text-yellow-600" />
                      </div>
                    </div>
                  </div>
                </div>
                
                <div className="mt-4 p-4 bg-cyan-50 rounded-md border border-cyan-200">
                  <div className="flex items-start">
                    <Bell className="h-5 w-5 text-cyan-600 mr-3 mt-0.5" />
                    <div>
                      <h4 className="text-sm font-medium text-cyan-800">Important Platform Notices</h4>
                      <p className="text-sm text-cyan-700 mt-1">
                        FIRS has announced changes to the e-invoicing API that will take effect on July 1, 2025.
                        An update to your certificates will be required before this date.
                      </p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
          
          <TabsContent value="certificates">
            <CertificateManagementInterface organizationId={organizationId} />
          </TabsContent>
          
          <TabsContent value="transmission">
            <TransmissionMonitoringDashboard organizationId={organizationId} />
          </TabsContent>
          
          <TabsContent value="compliance">
            <ComplianceSummaryVisualization organizationId={organizationId} />
          </TabsContent>
        </Tabs>
      </div>
    </AppDashboardLayout>
  );
};

export default PlatformDashboard;
