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
  Globe,
  ShieldCheck,
  Lock,
  Award,
  BookOpen,
  Users,
  FileText,
  Lightbulb,
  GraduationCap
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
                Complete E-Invoicing Solution: From Integration to Transmission
              </Typography.Heading>
              <Typography.Text size="lg" className="text-white/90 leading-relaxed max-w-xl">
                Our dual-certified platform offers both System Integration and Platform capabilities, automating your entire e-invoicing workflow from ERP integration to secure FIRS submission.
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
                  onClick={() => {
                    // Smooth scroll to the Platform capabilities section
                    const appSection = document.getElementById('app-capabilities');
                    if (appSection) {
                      appSection.scrollIntoView({ behavior: 'smooth' });
                    }
                  }}
                >
                  Explore Platform Features <ArrowRight className="ml-2 h-4 w-4 group-hover:translate-x-1 transition-transform" />
                </Button>
              </div>
            </div>
            <div className="hidden lg:flex justify-end">
              <div className="relative w-full max-w-xl h-96 bg-white/10 rounded-lg overflow-hidden backdrop-blur-sm border-2 border-white/20 shadow-2xl">
                {/* Dashboard Screenshot */}
                <div className="absolute inset-0 bg-gradient-to-br from-white/5 to-transparent">
                  <div className="relative h-full w-full overflow-hidden">
                    {/* Create a browser window frame effect */}
                    <div className="h-6 bg-gray-800 flex items-center px-2">
                      <div className="flex space-x-1.5">
                        <div className="w-2.5 h-2.5 rounded-full bg-red-500"></div>
                        <div className="w-2.5 h-2.5 rounded-full bg-yellow-500"></div>
                        <div className="w-2.5 h-2.5 rounded-full bg-green-500"></div>
                      </div>
                    </div>
                    {/* Dashboard screenshot fills the frame */}
                    <div className="h-[calc(100%-24px)] w-full">
                      <Image 
                        src="/icons/dashboard-screenshot.webp" 
                        alt="TaxPoynt E-Invoice Dashboard" 
                        width={600} 
                        height={400}
                        className="w-full h-full object-cover object-top" 
                      />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Dual Certification Highlight */}
        <div className="bg-gradient-to-r from-gray-50 to-gray-100 border-y border-gray-200 py-8">
          <div className="container mx-auto px-4">
            <div className="flex flex-col md:flex-row items-center justify-center gap-8">
              <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200 flex items-center">
                <div className="p-3 rounded-full bg-blue-100 mr-4">
                  <GitMerge className="h-8 w-8 text-blue-700" />
                </div>
                <div>
                  <Typography.Text className="text-gray-500 text-sm">Certified</Typography.Text>
                  <Typography.Heading level="h3" className="text-lg font-semibold">
                    System Integrator (SI)
                  </Typography.Heading>
                </div>
              </div>
              
              <div className="flex items-center">
                <Typography.Text className="text-xl font-bold px-4 text-gray-400">+</Typography.Text>
              </div>
              
              <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200 flex items-center">
                <div className="p-3 rounded-full bg-cyan-100 mr-4">
                  <Shield className="h-8 w-8 text-cyan-700" />
                </div>
                <div>
                  <Typography.Text className="text-gray-500 text-sm">Certified</Typography.Text>
                  <Typography.Heading level="h3" className="text-lg font-semibold">
                    Access Point Provider (Platform)
                  </Typography.Heading>
                </div>
              </div>
            </div>
            
            <div className="text-center mt-6">
              <Typography.Text className="text-gray-600">
                One of the few solutions offering both certifications for complete e-invoicing compliance
              </Typography.Text>
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

        {/* APP Capabilities Section */}
        <div id="app-capabilities" className="py-16 bg-white">
          <div className="container mx-auto px-4">
            <div className="text-center max-w-3xl mx-auto mb-10">
              <div className="inline-block bg-cyan-100 text-cyan-800 px-4 py-2 rounded-full mb-4">
                <span className="font-medium">Platform Certified</span>
              </div>
              <Typography.Heading level="h2" className="text-3xl font-bold mb-4">
                Secure E-Invoice Transmission
              </Typography.Heading>
              <Typography.Text size="lg" className="text-gray-600 mb-4">
                As a certified Access Point Provider, we handle the secure submission of your e-invoices directly to FIRS, ensuring compliance and validation at every step.
              </Typography.Text>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              {[
                { 
                  icon: <ShieldCheck className="h-12 w-12 text-cyan-600" />,
                  name: 'Certificate Management', 
                  description: 'Automatic handling of digital certificates required for e-invoice validation and submission.' 
                },
                { 
                  icon: <Lock className="h-12 w-12 text-cyan-600" />,
                  name: 'Secure Transmission', 
                  description: 'Encrypted, compliant transmission of invoices to FIRS with complete audit trail.' 
                },
                { 
                  icon: <FileCheck className="h-12 w-12 text-cyan-600" />,
                  name: 'Validation & Verification', 
                  description: 'Real-time validation ensures all invoices meet FIRS requirements before submission.' 
                },
              ].map((feature, index) => (
                <Card key={index} className="platform-card shadow-sm hover:shadow-md transition-shadow h-full">
                  <CardContent className="pt-6">
                    <div className="mb-4">{feature.icon}</div>
                    <Typography.Heading level="h3" className="text-xl font-semibold mb-2">
                      {feature.name}
                    </Typography.Heading>
                    <Typography.Text className="text-gray-600">
                      {feature.description}
                    </Typography.Text>
                  </CardContent>
                </Card>
              ))}
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
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-8 mb-16">
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
                { 
                  icon: <ShieldCheck className="h-10 w-10 text-cyan-600" />, 
                  title: 'End-to-End Solution', 
                  description: 'Complete e-invoicing solution from integration to secure FIRS transmission.' 
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

        {/* Case Studies Section */}
        <div className="py-16 bg-gray-50">
          <div className="container mx-auto px-4">
            <div className="text-center max-w-3xl mx-auto mb-12">
              <Typography.Heading level="h2" className="text-3xl font-bold mb-4">
                Success Stories
              </Typography.Heading>
              <Typography.Text size="lg" className="text-gray-600">
                See how businesses are benefiting from our combined System Integration and Platform solution
              </Typography.Text>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 mb-8">
              {/* Case Study 1 */}
              <Card className="overflow-hidden h-full shadow-md hover:shadow-lg transition-shadow">
                <div className="h-48 bg-gray-200 relative">
                  <div className="absolute inset-0 flex items-center justify-center bg-gradient-to-r from-primary-600 to-primary-700">
                    <Users className="h-12 w-12 text-white opacity-70" />
                  </div>
                </div>
                <CardContent className="p-6">
                  <div className="flex items-center justify-between mb-4">
                    <Typography.Heading level="h3" className="text-xl font-bold">
                      XYZ Manufacturing
                    </Typography.Heading>
                    <span className="bg-green-100 text-green-800 text-xs px-2 py-1 rounded-full font-medium">Manufacturing</span>
                  </div>
                  <Typography.Text className="mb-4">
                    Reduced invoice processing time by 85% and eliminated all compliance errors with our dual-certified solution. Their monthly tax filing now completes in just hours instead of days.
                  </Typography.Text>
                  <div className="flex flex-wrap gap-2 mb-4">
                    <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-blue-50 text-blue-700">SI Integration</span>
                    <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-cyan-50 text-cyan-700">Platform Certified</span>
                  </div>
                  <Button variant="outline" size="sm" className="w-full mt-2">
                    Read Full Story
                  </Button>
                </CardContent>
              </Card>

              {/* Case Study 2 */}
              <Card className="overflow-hidden h-full shadow-md hover:shadow-lg transition-shadow">
                <div className="h-48 bg-gray-200 relative">
                  <div className="absolute inset-0 flex items-center justify-center bg-gradient-to-r from-cyan-600 to-cyan-700">
                    <FileText className="h-12 w-12 text-white opacity-70" />
                  </div>
                </div>
                <CardContent className="p-6">
                  <div className="flex items-center justify-between mb-4">
                    <Typography.Heading level="h3" className="text-xl font-bold">
                      ABC Financial Services
                    </Typography.Heading>
                    <span className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded-full font-medium">Finance</span>
                  </div>
                  <Typography.Text className="mb-4">
                    Achieved 100% FIRS compliance rate with our platform's automated validation and secure transmission. Their audit preparation time decreased by 70% thanks to comprehensive reporting.
                  </Typography.Text>
                  <div className="flex flex-wrap gap-2 mb-4">
                    <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-blue-50 text-blue-700">Odoo Integration</span>
                    <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-cyan-50 text-cyan-700">Platform Security</span>
                  </div>
                  <Button variant="outline" size="sm" className="w-full mt-2">
                    Read Full Story
                  </Button>
                </CardContent>
              </Card>

              {/* Case Study 3 */}
              <Card className="overflow-hidden h-full shadow-md hover:shadow-lg transition-shadow">
                <div className="h-48 bg-gray-200 relative">
                  <div className="absolute inset-0 flex items-center justify-center bg-gradient-to-r from-gray-700 to-gray-800">
                    <ShieldCheck className="h-12 w-12 text-white opacity-70" />
                  </div>
                </div>
                <CardContent className="p-6">
                  <div className="flex items-center justify-between mb-4">
                    <Typography.Heading level="h3" className="text-xl font-bold">
                      Global Retail Corp
                    </Typography.Heading>
                    <span className="bg-purple-100 text-purple-800 text-xs px-2 py-1 rounded-full font-medium">Retail</span>
                  </div>
                  <Typography.Text className="mb-4">
                    Seamlessly connected multiple ERPs to our platform for centralized e-invoice management. Cryptographic stamping and automated validation streamlined operations across 12 locations.
                  </Typography.Text>
                  <div className="flex flex-wrap gap-2 mb-4">
                    <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-blue-50 text-blue-700">Multi-ERP</span>
                    <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-cyan-50 text-cyan-700">Platform Analytics</span>
                  </div>
                  <Button variant="outline" size="sm" className="w-full mt-2">
                    Read Full Story
                  </Button>
                </CardContent>
              </Card>
            </div>

            <div className="text-center mt-8">
              <Button
                variant="outline"
                size="lg"
                className="bg-white border-primary-600 text-primary-700 hover:bg-primary-50"
              >
                View All Case Studies
              </Button>
            </div>
          </div>
        </div>

        {/* Educational Resources Section */}
        <div className="py-16 bg-white">
          <div className="container mx-auto px-4">
            <div className="text-center max-w-3xl mx-auto mb-12">
              <Typography.Heading level="h2" className="text-3xl font-bold mb-4">
                Educational Resources
              </Typography.Heading>
              <Typography.Text size="lg" className="text-gray-600">
                Learn more about our Platform functionality and how it complements our System Integration capabilities
              </Typography.Text>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {/* Resource 1 */}
              <Card className="overflow-hidden h-full shadow-sm hover:shadow-md transition-shadow border-t-4 border-t-cyan-500">
                <CardContent className="p-6">
                  <div className="mb-4">
                    <BookOpen className="h-8 w-8 text-cyan-600" />
                  </div>
                  <Typography.Heading level="h3" className="text-lg font-semibold mb-2">
                    Platform Certification Guide
                  </Typography.Heading>
                  <Typography.Text className="text-gray-600 mb-4">
                    Understanding the requirements and benefits of FIRS Access Point Provider certification.
                  </Typography.Text>
                  <Button variant="link" className="text-cyan-600 p-0 h-auto font-medium">
                    Read Guide <ArrowRight className="ml-1 h-4 w-4" />
                  </Button>
                </CardContent>
              </Card>

              {/* Resource 2 */}
              <Card className="overflow-hidden h-full shadow-sm hover:shadow-md transition-shadow border-t-4 border-t-cyan-500">
                <CardContent className="p-6">
                  <div className="mb-4">
                    <Lightbulb className="h-8 w-8 text-cyan-600" />
                  </div>
                  <Typography.Heading level="h3" className="text-lg font-semibold mb-2">
                    Cryptographic Stamping Explained
                  </Typography.Heading>
                  <Typography.Text className="text-gray-600 mb-4">
                    How our Platform securely stamps and validates your e-invoices for FIRS compliance.
                  </Typography.Text>
                  <Button variant="link" className="text-cyan-600 p-0 h-auto font-medium">
                    Learn More <ArrowRight className="ml-1 h-4 w-4" />
                  </Button>
                </CardContent>
              </Card>

              {/* Resource 3 */}
              <Card className="overflow-hidden h-full shadow-sm hover:shadow-md transition-shadow border-t-4 border-t-cyan-500">
                <CardContent className="p-6">
                  <div className="mb-4">
                    <Award className="h-8 w-8 text-cyan-600" />
                  </div>
                  <Typography.Heading level="h3" className="text-lg font-semibold mb-2">
                    Certificate Management Best Practices
                  </Typography.Heading>
                  <Typography.Text className="text-gray-600 mb-4">
                    Guidelines for maintaining and renewing your digital certificates for e-invoicing.
                  </Typography.Text>
                  <Button variant="link" className="text-cyan-600 p-0 h-auto font-medium">
                    View Guide <ArrowRight className="ml-1 h-4 w-4" />
                  </Button>
                </CardContent>
              </Card>

              {/* Resource 4 */}
              <Card className="overflow-hidden h-full shadow-sm hover:shadow-md transition-shadow border-t-4 border-t-cyan-500">
                <CardContent className="p-6">
                  <div className="mb-4">
                    <GraduationCap className="h-8 w-8 text-cyan-600" />
                  </div>
                  <Typography.Heading level="h3" className="text-lg font-semibold mb-2">
                    Platform & SI Integration Tutorial
                  </Typography.Heading>
                  <Typography.Text className="text-gray-600 mb-4">
                    Step-by-step guide to leveraging our combined solution for maximum e-invoicing efficiency.
                  </Typography.Text>
                  <Button variant="link" className="text-cyan-600 p-0 h-auto font-medium">
                    Start Tutorial <ArrowRight className="ml-1 h-4 w-4" />
                  </Button>
                </CardContent>
              </Card>
            </div>

            <div className="mt-10 bg-gradient-to-r from-cyan-50 to-blue-50 rounded-lg p-6 border border-cyan-100">
              <div className="flex flex-col md:flex-row gap-6 items-center">
                <div className="md:w-3/4">
                  <Typography.Heading level="h3" className="text-xl font-bold mb-2">
                    Expert Platform Implementation Support
                  </Typography.Heading>
                  <Typography.Text className="text-gray-700">
                    Need help understanding how our Platform functionality can transform your e-invoicing workflow? Our experts are ready to guide you through every step of the implementation process.
                  </Typography.Text>
                </div>
                <div className="md:w-1/4 flex justify-center">
                  <Button className="bg-cyan-600 hover:bg-cyan-700 text-white">
                    Schedule Consultation
                  </Button>
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