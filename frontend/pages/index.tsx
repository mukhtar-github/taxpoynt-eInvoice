import React, { useEffect } from 'react';
import { useRouter } from 'next/router';
import MainLayout from '../components/layouts/MainLayout';
import { useAuth } from '../context/AuthContext';
import { Button } from '../components/ui/Button';
import { Typography } from '../components/ui/Typography';
import { Card, CardContent } from '../components/ui/Card';
import Head from 'next/head';
import { 
  EnhancedHero, 
  ValuePropositions, 
  CallToAction, 
  FeatureShowcase, 
  BenefitsVisualization, 
  PlatformCapabilities, 
  IntegrationEcosystem,
  TrustBadges,
  SecurityIndicators,
  TestimonialsCarousel,
  UsageStatistics,
  SuccessStories
} from '../components/landing';
import { 
  ArrowRight, 
  FileCheck, 
  Database,
  Server,
  HardDrive,
  GitMerge,
  Layers,
  Shield,
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
        <title>Taxpoynt E-Invoice | Advanced E-Invoicing Platform with Comprehensive Features & Integrations</title>
        <meta name="description" content="Nigeria's most advanced e-invoicing platform with interactive features showcase, comprehensive benefits visualization, and seamless system integrations. FIRS certified APP solution." />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        {/* Using consistent favicon implementation from MainLayout */}
        <link rel="icon" href="/icons/logo.svg" type="image/svg+xml" />
        <link rel="apple-touch-icon" href="/icons/logo.svg" />
        <link rel="manifest" href="/site.webmanifest" />
      </Head>
      <MainLayout>
        {/* Enhanced Hero Section with Week 5 Improvements */}
        <EnhancedHero />

        {/* Day 5: Trust & Social Proof Section */}
        <div className="py-8 bg-gradient-to-r from-blue-50 to-cyan-50 border-y border-blue-200">
          <div className="container mx-auto px-4">
            <div className="text-center mb-8">
              <Typography.Heading level="h2" className="text-2xl font-bold text-gray-900 mb-2">
                Trusted by Thousands of Nigerian Businesses
              </Typography.Heading>
              <Typography.Text className="text-gray-600">
                Join the growing community of businesses achieving FIRS compliance effortlessly
              </Typography.Text>
            </div>
            
            {/* Trust Badges */}
            <TrustBadges 
              variant="inline" 
              animated={true}
              showFIRSBadges={true}
              showSecurityBadges={true}
            />
            
            {/* Usage Statistics */}
            <div className="mt-12">
              <UsageStatistics 
                layout="hero"
                animated={true}
                theme="light"
              />
            </div>
          </div>
        </div>

        {/* Security Status Banner */}
        <div className="bg-white border-b border-gray-200 py-4">
          <div className="container mx-auto px-4">
            <SecurityIndicators 
              layout="banner"
              animated={true}
            />
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
                  <Typography.Text className="text-gray-500 text-sm font-medium">CERTIFIED</Typography.Text>
                  <Typography.Heading level="h3" className="text-lg font-bold text-cyan-800">
                    Access Point Provider (APP)
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

        {/* Feature Showcase System - Day 3-4 Enhancement */}
        <FeatureShowcase 
          showCategories={true}
          maxFeatures={6}
        />

        {/* APP Capabilities Section - Enhanced & Prominent */}
        <div id="app-capabilities" className="py-16 bg-gradient-to-r from-cyan-50 to-white border-t-4 border-cyan-500">
          <div className="container mx-auto px-4">
            <div className="text-center max-w-3xl mx-auto mb-10">
              <div className="inline-block bg-cyan-600 text-white px-4 py-2 rounded-full mb-4 shadow-md">
                <span className="font-semibold">APP Certified</span>
              </div>
              <Typography.Heading level="h2" className="text-3xl font-bold mb-4 text-cyan-800">
                Access Point Provider Excellence
              </Typography.Heading>
              <Typography.Text size="lg" className="text-gray-700 mb-6">
                As Nigeria's premier certified Access Point Provider (APP), we handle the complete e-invoice lifecycle—from secure cryptographic stamping to validated FIRS submission—with enterprise-grade security and real-time tracking.
              </Typography.Text>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              {[
                { 
                  icon: <ShieldCheck className="h-12 w-12 text-cyan-600" />,
                  name: 'Certificate Management', 
                  description: 'Comprehensive digital certificate lifecycle management with automated renewal alerts, secure storage, and instant deployment for seamless e-invoice authentication.' 
                },
                { 
                  icon: <Lock className="h-12 w-12 text-cyan-600" />,
                  name: 'Secure Transmission', 
                  description: 'Enterprise-grade encrypted transmission with FIRS-compliant protocols, full audit trails, and guaranteed delivery confirmation for every invoice.' 
                },
                { 
                  icon: <FileCheck className="h-12 w-12 text-cyan-600" />,
                  name: 'Cryptographic Stamping', 
                  description: 'Advanced QR code stamping with tamper-evident digital signatures that ensure invoice authenticity and compliance with Nigerian tax regulations.' 
                },
              ].map((feature, index) => (
                <Card key={index} className="shadow-sm hover:shadow-md transition-shadow h-full border-l-4 border-cyan-500 bg-cyan-50/50">                   
                  <CardContent className="pt-6">
                    <div className="absolute top-3 right-3">
                      <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-cyan-100 text-cyan-800 border border-cyan-200">
                        APP
                      </span>
                    </div>
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
            
            {/* Add APP-specific call-to-action */}
            <div className="text-center mt-8">
              <Button
                size="lg"
                variant="default"
                className="bg-cyan-600 hover:bg-cyan-700 text-white shadow-lg font-medium"
                onClick={() => router.push("/auth/signup?focus=app")}
              >
                Start Using Access Point Provider
              </Button>
              
              <div className="mt-3">
                <Typography.Text size="sm" className="text-gray-600">
                  Fully FIRS-compliant with enterprise-level security
                </Typography.Text>
              </div>
            </div>
            </div>
          </div>
        </div>

        {/* Enhanced Value Propositions Section - Week 5 */}
        <ValuePropositions />

        {/* Benefits Visualization - Day 3-4 Enhancement */}
        <BenefitsVisualization 
          showMetrics={true}
        />

        {/* Customer Testimonials Section */}
        <div className="py-16 bg-gradient-to-b from-white to-gray-50">
          <div className="container mx-auto px-4">
            <div className="text-center max-w-3xl mx-auto mb-12">
              <Typography.Heading level="h2" className="text-3xl font-bold mb-4 text-gray-900">
                What Our Customers Say
              </Typography.Heading>
              <Typography.Text size="lg" className="text-gray-600">
                Real experiences from businesses that have transformed their e-invoicing with TaxPoynt
              </Typography.Text>
            </div>
            
            <TestimonialsCarousel 
              autoPlay={true}
              interval={6000}
              showMetrics={true}
              showRating={true}
              layout="single"
              animated={true}
            />
          </div>
        </div>

        {/* Platform Capabilities Overview - Day 3-4 Enhancement */}
        <PlatformCapabilities 
          defaultExpanded={['data-processing']}
        />

        {/* Success Stories Section - Enhanced with Day 5 Component */}
        <div className="py-16 bg-gradient-to-r from-cyan-50 to-white">
          <div className="container mx-auto px-4">
            <div className="text-center max-w-3xl mx-auto mb-12">
              <div className="inline-block bg-cyan-100 text-cyan-800 px-4 py-2 rounded-full mb-4">
                <span className="font-semibold">Success Stories</span>
              </div>
              <Typography.Heading level="h2" className="text-3xl font-bold mb-4 text-gray-800">
                Real Results from Real Businesses
              </Typography.Heading>
              <Typography.Text size="lg" className="text-gray-700">
                See how organizations across Nigeria are transforming their e-invoicing operations with TaxPoynt
              </Typography.Text>
            </div>

            <SuccessStories 
              showFilters={true}
              layout="grid"
              maxStories={6}
              animated={true}
            />
          </div>
        </div>

        {/* Integration Ecosystem Preview - Day 3-4 Enhancement */}
        <IntegrationEcosystem 
          showFilters={true}
          maxIntegrations={8}
        />

        {/* Security & Trust Section - Day 5 Enhancement */}
        <div className="py-16 bg-gradient-to-b from-gray-50 to-white">
          <div className="container mx-auto px-4">
            <div className="text-center max-w-3xl mx-auto mb-12">
              <Typography.Heading level="h2" className="text-3xl font-bold mb-4 text-gray-900">
                Enterprise-Grade Security & Reliability
              </Typography.Heading>
              <Typography.Text size="lg" className="text-gray-600">
                Your data security and system reliability are our top priorities. See how we protect your business.
              </Typography.Text>
            </div>
            
            <SecurityIndicators 
              showRealTimeStatus={true}
              showSecurityMetrics={true}
              showUptime={true}
              animated={true}
              layout="detailed"
            />
          </div>
        </div>

        {/* Trust Badges & Certifications */}
        <div className="py-16 bg-white border-t border-gray-200">
          <div className="container mx-auto px-4">
            <div className="text-center max-w-3xl mx-auto mb-12">
              <Typography.Heading level="h2" className="text-3xl font-bold mb-4 text-gray-900">
                Certifications & Compliance
              </Typography.Heading>
              <Typography.Text size="lg" className="text-gray-600">
                Our comprehensive certifications ensure your e-invoicing meets all regulatory requirements
              </Typography.Text>
            </div>
            
            <TrustBadges 
              variant="horizontal"
              animated={true}
              showFIRSBadges={true}
              showSecurityBadges={true}
              showCertifications={true}
            />
          </div>
        </div>

        {/* APP Educational Resources Section */}
        <div className="py-16 bg-gradient-to-b from-white to-cyan-50">
          <div className="container mx-auto px-4">
            <div className="text-center max-w-3xl mx-auto mb-12">
              <div className="inline-block bg-cyan-100 text-cyan-800 px-4 py-2 rounded-full mb-4">
                <span className="font-semibold">APP Resources</span>
              </div>
              <Typography.Heading level="h2" className="text-3xl font-bold mb-4">
                Access Point Provider Knowledge Center
              </Typography.Heading>
              <Typography.Text size="lg" className="text-gray-700">
                Learn more about our APP capabilities and how our certified e-invoice transmission solutions can transform your business
              </Typography.Text>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {/* Resource 1 */}
              <Card className="overflow-hidden h-full shadow-sm hover:shadow-md transition-shadow border-t-4 border-t-cyan-500">
                <CardContent className="p-6 relative">
                  <span className="absolute top-3 right-3 inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-cyan-100 text-cyan-800 border border-cyan-200">
                    APP
                  </span>
                  <div className="mb-4">
                    <BookOpen className="h-8 w-8 text-cyan-600" />
                  </div>
                  <Typography.Heading level="h3" className="text-lg font-semibold mb-2">
                    APP Certification Guide
                  </Typography.Heading>
                  <Typography.Text className="text-gray-600 mb-4">
                    Complete guide to FIRS Access Point Provider certification requirements and compliance benefits.
                  </Typography.Text>
                  <Button variant="link" className="text-cyan-600 p-0 h-auto font-medium">
                    Read Guide <ArrowRight className="ml-1 h-4 w-4" />
                  </Button>
                </CardContent>
              </Card>

              {/* Resource 2 */}
              <Card className="overflow-hidden h-full shadow-sm hover:shadow-md transition-shadow border-t-4 border-t-cyan-500">
                <CardContent className="p-6 relative">
                  <span className="absolute top-3 right-3 inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-cyan-100 text-cyan-800 border border-cyan-200">
                    APP
                  </span>
                  <div className="mb-4">
                    <Lightbulb className="h-8 w-8 text-cyan-600" />
                  </div>
                  <Typography.Heading level="h3" className="text-lg font-semibold mb-2">
                    Cryptographic Stamping Explained
                  </Typography.Heading>
                  <Typography.Text className="text-gray-600 mb-4">
                    How our APP solution securely stamps and validates your e-invoices for FIRS compliance and authenticity verification.
                  </Typography.Text>
                  <Button variant="link" className="text-cyan-600 p-0 h-auto font-medium">
                    Learn More <ArrowRight className="ml-1 h-4 w-4" />
                  </Button>
                </CardContent>
              </Card>

              {/* Resource 3 */}
              <Card className="overflow-hidden h-full shadow-sm hover:shadow-md transition-shadow border-t-4 border-t-cyan-500">
                <CardContent className="p-6 relative">
                  <span className="absolute top-3 right-3 inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-cyan-100 text-cyan-800 border border-cyan-200">
                    APP
                  </span>
                  <div className="mb-4">
                    <Award className="h-8 w-8 text-cyan-600" />
                  </div>
                  <Typography.Heading level="h3" className="text-lg font-semibold mb-2">
                    APP Certificate Lifecycle Management
                  </Typography.Heading>
                  <Typography.Text className="text-gray-600 mb-4">
                    Expert guidelines for maintaining, renewing and maximizing security of your APP digital certificates.
                  </Typography.Text>
                  <Button variant="link" className="text-cyan-600 p-0 h-auto font-medium">
                    View Guide <ArrowRight className="ml-1 h-4 w-4" />
                  </Button>
                </CardContent>
              </Card>

              {/* Resource 4 */}
              <Card className="overflow-hidden h-full shadow-sm hover:shadow-md transition-shadow border-t-4 border-t-cyan-500">
                <CardContent className="p-6 relative">
                  <span className="absolute top-3 right-3 inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-cyan-100 text-cyan-800 border border-cyan-200">
                    APP
                  </span>
                  <div className="mb-4">
                    <GraduationCap className="h-8 w-8 text-cyan-600" />
                  </div>
                  <Typography.Heading level="h3" className="text-lg font-semibold mb-2">
                    APP Integration Masterclass
                  </Typography.Heading>
                  <Typography.Text className="text-gray-600 mb-4">
                    Complete APP implementation guide with best practices for secure e-invoice transmission and compliance.
                  </Typography.Text>
                  <Button variant="link" className="text-cyan-600 p-0 h-auto font-medium">
                    Start Tutorial <ArrowRight className="ml-1 h-4 w-4" />
                  </Button>
                </CardContent>
              </Card>
            </div>

            <div className="mt-10 bg-gradient-to-r from-cyan-50 to-cyan-100 rounded-lg p-6 border-2 border-cyan-200">
              <div className="flex flex-col md:flex-row gap-6 items-center">
                <div className="md:w-3/4">
                  <div className="flex items-center mb-2">
                    <span className="inline-flex items-center px-2 py-1 mr-3 rounded text-xs font-medium bg-cyan-100 text-cyan-800 border border-cyan-200">
                      APP
                    </span>
                    <Typography.Heading level="h3" className="text-xl font-bold">
                      Expert APP Implementation Support
                    </Typography.Heading>
                  </div>
                  <Typography.Text className="text-gray-700">
                    Need help leveraging our APP capabilities for your e-invoicing compliance needs? Our certified experts are ready to guide you through every step of the implementation and certification process.
                  </Typography.Text>
                </div>
                <div className="md:w-1/4 flex justify-center">
                  <Button className="bg-cyan-600 hover:bg-cyan-700 text-white shadow-sm">
                    Schedule APP Consultation
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Enhanced Call-to-Action Section - Week 5 */}
        <CallToAction 
          title="Ready to Transform Your E-Invoicing?"
          description="Join hundreds of Nigerian businesses already saving time and ensuring compliance with TaxPoynt. Get started in minutes with our guided setup process."
          trackingId="landing-main"
          showStats={true}
          showTestimonial={true}
        />
      </MainLayout>
    </>
  );
};

export default Home; 