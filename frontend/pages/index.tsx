import React, { useEffect } from 'react';
import { useRouter } from 'next/router';
import MainLayout from '../components/layouts/MainLayout';
import { useAuth } from '../context/AuthContext';
import { Button } from '../components/ui/Button';
import { Typography } from '../components/ui/Typography';
import { Card, CardContent } from '../components/ui/Card';
import Image from 'next/image';
import Head from 'next/head';
import { 
  ArrowRight, 
  FileCheck, 
  Clock, 
  BarChart2, 
  CheckCircle,
  Database,
  Server,
  HardDrive,
  GitMerge,
  Layers,
  Shield,
  Globe
} from 'lucide-react';

const Home: React.FC = () => {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();

  // Redirect authenticated users to dashboard
  useEffect(() => {
    if (isAuthenticated && !isLoading) {
      router.push('/dashboard');
    }
  }, [isAuthenticated, isLoading, router]);

  // For unauthenticated users, just show the MainLayout with hero section
  return (
    <>
      <Head>
        <title>Taxpoynt E-Invoice | Automated Tax Compliance for Nigerian Businesses</title>
        <meta name="description" content="Transform your tax compliance with Nigeria's premier e-invoicing platform. Save time, eliminate errors, and stay compliant with FIRS regulations." />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        {/* Using consistent favicon implementation from MainLayout */}
        <link rel="icon" href="/icons/logo.svg" type="image/svg+xml" />
        <link rel="apple-touch-icon" href="/icons/logo.svg" />
        <link rel="manifest" href="/site.webmanifest" />
      </Head>
      <MainLayout>
        {/* Hero Section - Enhanced with image and better layout */}
        <div className="bg-gradient-to-r from-primary-600 to-primary-800 text-white py-16 md:py-24 relative">
          {/* Add a subtle overlay pattern for better text readability */}
          <div className="absolute inset-0 bg-black bg-opacity-20 z-0"></div>
          <div className="container mx-auto px-4 grid grid-cols-1 lg:grid-cols-2 gap-12 items-center relative z-10">
            <div className="space-y-6">
              <div className="inline-block bg-primary-500 bg-opacity-30 px-4 py-2 rounded-full">
                <span className="text-white font-medium">FIRS Compliant E-Invoicing</span>
              </div>
              <Typography.Heading level="h1" className="text-4xl md:text-6xl font-bold text-white drop-shadow-md">
                Transforming Tax Compliance Through ERP Integration
              </Typography.Heading>
              <Typography.Text size="lg" className="text-white/90 leading-relaxed max-w-xl">
                Automate your e-invoicing workflow through seamless ERP systems integration, ensure FIRS compliance, and eliminate manual errors with our platform designed specifically for Nigerian businesses.
              </Typography.Text>
              <div className="flex flex-col sm:flex-row gap-4 pt-4">
                <Button 
                  size="lg"
                  variant="default" 
                  className="bg-white text-primary-700 hover:bg-gray-100 font-bold shadow-lg tracking-wide border-2 border-white text-shadow-sm"
                  onClick={() => router.push('/auth/signup')}
                >
                  Start Your Free Trial
                </Button>
                <Button 
                  size="lg"
                  variant="outline" 
                  className="border-white text-white hover:bg-white/30 group bg-primary-700/50 backdrop-blur-sm shadow-md font-semibold text-shadow-sm"
                  onClick={() => router.push('/documentation')}
                >
                  Learn More <ArrowRight className="ml-2 h-4 w-4 group-hover:translate-x-1 transition-transform" />
                </Button>
              </div>
            </div>
            <div className="hidden lg:flex justify-end">
              <div className="relative w-full max-w-lg h-96 bg-white/10 rounded-lg overflow-hidden backdrop-blur-sm">
                <div className="absolute inset-0 bg-gradient-to-br from-white/10 to-transparent">
                  <div className="relative h-full flex items-center justify-center">
                    <Image 
                      src="/icons/logo.svg" 
                      alt="Taxpoynt E-Invoice" 
                      width={150} 
                      height={150} 
                      className="drop-shadow-xl" 
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Systems Integration Section */}
        <div className="py-16 bg-gray-50">
          <div className="container mx-auto px-4">
            <div className="text-center max-w-3xl mx-auto mb-10">
              <Typography.Heading level="h2" className="text-3xl font-bold mb-4">
                Seamless Systems Integration
              </Typography.Heading>
              <Typography.Text size="lg" className="text-gray-600 mb-4">
                Our platform connects directly with your existing business systems, enabling automatic e-invoice generation and submission without disrupting your workflow.
              </Typography.Text>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-8">
              {[
                { 
                  icon: <Database className="h-10 w-10 text-primary-600" />,
                  name: 'SAP', 
                  description: 'Direct integration with SAP ERP for automated invoice synchronization and real-time reporting.' 
                },
                { 
                  icon: <Server className="h-10 w-10 text-primary-600" />,
                  name: 'Odoo', 
                  description: 'Seamless Odoo integration for small to medium businesses needing end-to-end e-invoicing.' 
                },
                { 
                  icon: <HardDrive className="h-10 w-10 text-primary-600" />,
                  name: 'Oracle', 
                  description: 'Enterprise-grade Oracle ERP integration with secure data transmission and validation.' 
                },
                { 
                  icon: <GitMerge className="h-10 w-10 text-primary-600" />,
                  name: 'Microsoft Dynamics', 
                  description: 'Full Microsoft Dynamics 365 compatibility with bi-directional data flow.' 
                },
                { 
                  icon: <Layers className="h-10 w-10 text-primary-600" />,
                  name: 'QuickBooks', 
                  description: 'Quick and easy QuickBooks integration for small businesses and accountants.' 
                },
              ].map((integration, index) => (
                <Card key={index} className="border-none shadow-sm hover:shadow-md transition-shadow h-full">
                  <CardContent className="pt-6">
                    <div className="flex items-center mb-4">
                      <div className="mr-3">{integration.icon}</div>
                      <Typography.Heading level="h3" className="text-xl font-semibold">
                        {integration.name}
                      </Typography.Heading>
                    </div>
                    <Typography.Text className="text-gray-600">
                      {integration.description}
                    </Typography.Text>
                    
                    {/* Technical Standards Badges - Subtle indication of compatibility */}
                    <div className="flex flex-wrap gap-1.5 mt-4 mb-1">
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-50 text-blue-700 border border-blue-100">
                        UBL 2.1
                      </span>
                      {integration.name === 'SAP' || integration.name === 'Oracle' || integration.name === 'Microsoft Dynamics' ? (
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-50 text-green-700 border border-green-100">
                          PEPPOL
                        </span>
                      ) : null}
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-purple-50 text-purple-700 border border-purple-100">
                        API
                      </span>
                    </div>
                    
                    <div className="mt-2">
                      <Typography.Text className="text-sm text-primary-600 font-medium">
                        Integration Ready
                      </Typography.Text>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
            
            <div className="mt-10 text-center">
              <Button
                size="lg"
                variant="outline"
                className="bg-white text-primary-700 border-primary-600 hover:bg-primary-50 font-semibold"
                onClick={() => router.push('/integrations')}
              >
                Explore All Integrations
              </Button>
            </div>
          </div>
        </div>

        {/* Why Choose Section - Enhanced with technical standards value */}
        <div className="py-16 bg-white">
          <div className="container mx-auto px-4">
            <div className="text-center max-w-3xl mx-auto mb-10">
              <Typography.Heading level="h2" className="text-3xl font-bold mb-4">
                Why Choose Taxpoynt E-Invoice?
              </Typography.Heading>
              <Typography.Text size="lg" className="text-gray-600">
                Our platform combines business efficiency with enterprise-grade technical standards to future-proof your tax compliance.
              </Typography.Text>
            </div>
            
            {/* Business Benefits */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8 mb-16">
              {[
                { 
                  icon: <FileCheck className="h-10 w-10 text-primary-600" />, 
                  title: 'FIRS Compliant', 
                  description: 'Generate IRNs that meet all FIRS requirements automatically.' 
                },
                { 
                  icon: <Clock className="h-10 w-10 text-primary-600" />, 
                  title: 'Saves Time', 
                  description: 'Reduce manual processing time by up to 90% with our automated systems.' 
                },
                { 
                  icon: <BarChart2 className="h-10 w-10 text-primary-600" />, 
                  title: 'Real-Time Analytics', 
                  description: 'Track compliance metrics and monitor your invoice status in real-time.' 
                },
                { 
                  icon: <CheckCircle className="h-10 w-10 text-primary-600" />, 
                  title: 'Error Prevention', 
                  description: 'Built-in validation catches errors before they become costly problems.' 
                },
              ].map((feature, index) => (
                <Card key={index} className="border-none shadow-sm hover:shadow-md transition-shadow">
                  <CardContent className="pt-6">
                    <div className="mb-4">{feature.icon}</div>
                    <Typography.Heading level="h3" className="text-xl font-semibold mb-2">
                      {feature.title}
                    </Typography.Heading>
                    <Typography.Text className="text-gray-600">
                      {feature.description}
                    </Typography.Text>
                  </CardContent>
                </Card>
              ))}
            </div>
            
            {/* Technical Standards Value Section */}
            <div className="max-w-4xl mx-auto">
              <div className="text-center mb-8">
                <Typography.Heading level="h3" className="text-2xl font-bold mb-2">
                  Enterprise Standards That Matter
                </Typography.Heading>
                <Typography.Text size="lg" className="text-gray-600">
                  Our adherence to global technical standards delivers tangible business value
                </Typography.Text>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                <div className="bg-blue-50 rounded-lg p-6 border border-blue-100">
                  <div className="flex items-center mb-4">
                    <Shield className="h-8 w-8 text-primary-600 mr-3" />
                    <Typography.Heading level="h4" className="text-lg font-semibold">
                      Risk Reduction & Compliance
                    </Typography.Heading>
                  </div>
                  <ul className="space-y-2 pl-11">
                    <li className="text-gray-700 list-disc">
                      <span className="font-medium">UBL 2.1 Compliance</span>: Ensures your e-invoices meet both FIRS requirements and global standards
                    </li>
                    <li className="text-gray-700 list-disc">
                      <span className="font-medium">QR Verification</span>: Protects against fraud and simplifies invoice validation
                    </li>
                  </ul>
                </div>
                
                <div className="bg-green-50 rounded-lg p-6 border border-green-100">
                  <div className="flex items-center mb-4">
                    <Globe className="h-8 w-8 text-primary-600 mr-3" />
                    <Typography.Heading level="h4" className="text-lg font-semibold">
                      Future-Proof Investment
                    </Typography.Heading>
                  </div>
                  <ul className="space-y-2 pl-11">
                    <li className="text-gray-700 list-disc">
                      <span className="font-medium">PEPPOL Compatibility</span>: Prepares Nigerian businesses for international trade documentation
                    </li>
                    <li className="text-gray-700 list-disc">
                      <span className="font-medium">API-First Design</span>: Ensures seamless integration with any current or future business system
                    </li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </div>
      </MainLayout>
    </>
  );
};

export default Home; 