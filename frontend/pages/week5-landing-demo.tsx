import React, { useEffect } from 'react';
import { useRouter } from 'next/router';
import Head from 'next/head';
import { useAuth } from '../context/AuthContext';
import MainLayout from '../components/layouts/MainLayout';
import { EnhancedHero, ValuePropositions, CallToAction } from '../components/landing';
import { Card, CardContent } from '../components/ui/Card';
import { Typography } from '../components/ui/Typography';
import { Button } from '../components/ui/Button';
import { 
  Shield, 
  GitMerge, 
  FileCheck, 
  Lock, 
  ShieldCheck,
  Database,
  Server,
  HardDrive,
  Layers,
  Users,
  Award,
  BookOpen,
  CheckCircle,
  ArrowRight,
  Play,
  Star
} from 'lucide-react';

const Week5LandingDemo: React.FC = () => {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();

  // Redirect authenticated users to dashboard
  useEffect(() => {
    if (isAuthenticated && !isLoading) {
      router.push('/dashboard');
    }
  }, [isAuthenticated, isLoading, router]);

  return (
    <>
      <Head>
        <title>Week 5: Enhanced Business Landing Page | TaxPoynt E-Invoice</title>
        <meta name="description" content="Week 5 UI/UX improvements: Modern hero section with gradient backgrounds, scroll-triggered animations, and optimized conversion flows." />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/icons/logo.svg" type="image/svg+xml" />
      </Head>

      <div className="min-h-screen bg-white">
        
        {/* Enhanced Header Navigation */}
        <header className="fixed top-0 left-0 right-0 z-50 bg-white/95 backdrop-blur-md border-b border-gray-200/50">
          <div className="container mx-auto px-4">
            <div className="flex items-center justify-between h-16">
              
              {/* Logo */}
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-gradient-to-r from-primary-600 to-primary-700 rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold text-lg">T</span>
                </div>
                <span className="text-xl font-bold text-gray-900">TaxPoynt</span>
                <span className="text-sm bg-cyan-100 text-cyan-800 px-2 py-1 rounded-full font-medium">
                  Week 5 Demo
                </span>
              </div>

              {/* Navigation */}
              <nav className="hidden md:flex items-center space-x-8">
                <a href="#features" className="text-gray-600 hover:text-primary-600 font-medium transition-colors">
                  Features
                </a>
                <a href="#integrations" className="text-gray-600 hover:text-primary-600 font-medium transition-colors">
                  Integrations
                </a>
                <a href="#pricing" className="text-gray-600 hover:text-primary-600 font-medium transition-colors">
                  Pricing
                </a>
              </nav>

              {/* CTA Buttons */}
              <div className="flex items-center space-x-3">
                <Button variant="ghost" onClick={() => router.push('/auth/login')}>
                  Sign In
                </Button>
                <Button onClick={() => router.push('/auth/signup')}>
                  Get Started
                </Button>
              </div>
            </div>
          </div>
        </header>

        {/* Enhanced Hero Section */}
        <EnhancedHero className="pt-16" />

        {/* Dual Certification Section */}
        <section className="py-16 bg-gradient-to-r from-gray-50 to-gray-100 border-y border-gray-200">
          <div className="container mx-auto px-4">
            <div className="text-center mb-12">
              <Typography.Heading level="h2" className="text-3xl font-bold mb-4">
                Dual Certification Advantage
              </Typography.Heading>
              <Typography.Text size="lg" className="text-gray-600 max-w-2xl mx-auto">
                We're one of the few solutions offering both System Integrator and Access Point Provider certifications for complete e-invoicing compliance.
              </Typography.Text>
            </div>

            <div className="flex flex-col md:flex-row items-center justify-center gap-8 max-w-4xl mx-auto">
              
              {/* SI Certification */}
              <div className="bg-white p-8 rounded-2xl shadow-lg border border-gray-200 flex-1 max-w-sm transform hover:scale-105 transition-transform duration-300">
                <div className="text-center">
                  <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <GitMerge className="h-8 w-8 text-blue-700" />
                  </div>
                  <Typography.Text className="text-gray-500 text-sm font-medium">CERTIFIED</Typography.Text>
                  <Typography.Heading level="h3" className="text-xl font-bold text-blue-800 mb-3">
                    System Integrator (SI)
                  </Typography.Heading>
                  <Typography.Text className="text-gray-600 text-sm">
                    Direct integration with ERP systems, automated invoice generation, and seamless data flow.
                  </Typography.Text>
                </div>
              </div>
              
              {/* Plus Symbol */}
              <div className="flex items-center justify-center w-12 h-12 bg-gray-200 rounded-full">
                <Typography.Text className="text-2xl font-bold text-gray-400">+</Typography.Text>
              </div>
              
              {/* APP Certification */}
              <div className="bg-white p-8 rounded-2xl shadow-lg border border-cyan-200 flex-1 max-w-sm transform hover:scale-105 transition-transform duration-300 ring-2 ring-cyan-100">
                <div className="text-center">
                  <div className="w-16 h-16 bg-cyan-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <Shield className="h-8 w-8 text-cyan-700" />
                  </div>
                  <Typography.Text className="text-cyan-600 text-sm font-medium">CERTIFIED</Typography.Text>
                  <Typography.Heading level="h3" className="text-xl font-bold text-cyan-800 mb-3">
                    Access Point Provider (APP)
                  </Typography.Heading>
                  <Typography.Text className="text-gray-600 text-sm">
                    Secure transmission to FIRS, certificate management, and compliance validation.
                  </Typography.Text>
                </div>
              </div>
            </div>

            <div className="text-center mt-8">
              <div className="inline-flex items-center space-x-2 bg-green-100 text-green-800 px-4 py-2 rounded-full">
                <CheckCircle className="h-4 w-4" />
                <span className="font-medium text-sm">Complete E-Invoicing Solution</span>
              </div>
            </div>
          </div>
        </section>

        {/* Value Propositions Section */}
        <ValuePropositions />

        {/* Systems Integration Showcase */}
        <section id="integrations" className="py-20 bg-white">
          <div className="container mx-auto px-4">
            <div className="text-center max-w-4xl mx-auto mb-16">
              <Typography.Heading level="h2" className="text-4xl font-bold mb-6">
                Seamless ERP Integration
              </Typography.Heading>
              <Typography.Text size="lg" className="text-gray-600">
                Connect with your existing business systems in minutes. Our platform integrates with all major ERP, CRM, and accounting software.
              </Typography.Text>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-8">
              {[
                { 
                  icon: <Database className="h-12 w-12 text-blue-600" />,
                  name: 'SAP', 
                  description: 'Enterprise-grade integration with SAP ERP systems',
                  badges: ['UBL 2.1', 'PEPPOL', 'API'],
                  status: 'Production Ready'
                },
                { 
                  icon: <Server className="h-12 w-12 text-orange-600" />,
                  name: 'Odoo', 
                  description: 'Complete Odoo integration for SME businesses',
                  badges: ['UBL 2.1', 'REST API'],
                  status: 'Production Ready'
                },
                { 
                  icon: <HardDrive className="h-12 w-12 text-red-600" />,
                  name: 'Oracle', 
                  description: 'Secure Oracle ERP integration with data validation',
                  badges: ['UBL 2.1', 'PEPPOL', 'SOAP'],
                  status: 'Production Ready'
                },
                { 
                  icon: <GitMerge className="h-12 w-12 text-blue-500" />,
                  name: 'Microsoft Dynamics', 
                  description: 'Full Dynamics 365 compatibility and bi-directional sync',
                  badges: ['UBL 2.1', 'PEPPOL', 'Graph API'],
                  status: 'Production Ready'
                },
                { 
                  icon: <Layers className="h-12 w-12 text-green-600" />,
                  name: 'QuickBooks', 
                  description: 'Simple QuickBooks integration for small businesses',
                  badges: ['UBL 2.1', 'API'],
                  status: 'Production Ready'
                },
              ].map((integration, index) => (
                <Card key={index} className="group hover:shadow-xl transition-all duration-300 border-2 hover:border-primary-200">
                  <CardContent className="p-6 text-center">
                    <div className="mb-4 group-hover:scale-110 transition-transform duration-300">
                      {integration.icon}
                    </div>
                    <Typography.Heading level="h3" className="text-lg font-bold mb-2">
                      {integration.name}
                    </Typography.Heading>
                    <Typography.Text className="text-gray-600 text-sm mb-4">
                      {integration.description}
                    </Typography.Text>
                    
                    <div className="flex flex-wrap gap-1 justify-center mb-3">
                      {integration.badges.map((badge, i) => (
                        <span key={i} className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-50 text-blue-700 border border-blue-100">
                          {badge}
                        </span>
                      ))}
                    </div>
                    
                    <div className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-green-50 text-green-700 border border-green-100">
                      <div className="w-2 h-2 bg-green-500 rounded-full mr-2"></div>
                      {integration.status}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>

            <div className="text-center mt-12">
              <Button size="lg" variant="outline" className="group">
                View All Integrations
                <ArrowRight className="ml-2 h-4 w-4 group-hover:translate-x-1 transition-transform" />
              </Button>
            </div>
          </div>
        </section>

        {/* APP Capabilities Section */}
        <section id="app-capabilities" className="py-20 bg-gradient-to-b from-cyan-50 to-white">
          <div className="container mx-auto px-4">
            <div className="text-center max-w-3xl mx-auto mb-16">
              <div className="inline-block bg-cyan-100 text-cyan-800 px-4 py-2 rounded-full mb-6">
                <span className="font-medium">NEW: Access Point Provider Certification</span>
              </div>
              <Typography.Heading level="h2" className="text-4xl font-bold mb-6">
                Secure E-Invoice Transmission
              </Typography.Heading>
              <Typography.Text size="lg" className="text-gray-600">
                As a certified Access Point Provider, we handle the secure submission of your e-invoices directly to FIRS, ensuring compliance and validation at every step.
              </Typography.Text>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              {[
                { 
                  icon: <ShieldCheck className="h-12 w-12 text-cyan-600" />,
                  name: 'Certificate Management', 
                  description: 'Automatic handling of digital certificates required for e-invoice validation and submission. We manage the entire certificate lifecycle.',
                  features: ['Auto-renewal', 'Validation', 'Backup systems']
                },
                { 
                  icon: <Lock className="h-12 w-12 text-cyan-600" />,
                  name: 'Secure Transmission', 
                  description: 'End-to-end encrypted transmission of invoices to FIRS with complete audit trail and delivery confirmation.',
                  features: ['256-bit encryption', 'Audit logs', 'Real-time status']
                },
                { 
                  icon: <FileCheck className="h-12 w-12 text-cyan-600" />,
                  name: 'Validation & Verification', 
                  description: 'Real-time validation ensures all invoices meet FIRS requirements before submission, preventing rejections.',
                  features: ['Pre-validation', 'Error detection', 'Compliance check']
                },
              ].map((feature, index) => (
                <Card key={index} className="border-l-4 border-cyan-500 shadow-lg hover:shadow-xl transition-shadow group">
                  <CardContent className="p-8">
                    <div className="mb-6 group-hover:scale-110 transition-transform duration-300">{feature.icon}</div>
                    <Typography.Heading level="h3" className="text-xl font-bold mb-4">
                      {feature.name}
                    </Typography.Heading>
                    <Typography.Text className="text-gray-600 mb-6">
                      {feature.description}
                    </Typography.Text>
                    <ul className="space-y-2">
                      {feature.features.map((item, i) => (
                        <li key={i} className="flex items-center space-x-2">
                          <CheckCircle className="h-4 w-4 text-green-500" />
                          <span className="text-sm text-gray-600">{item}</span>
                        </li>
                      ))}
                    </ul>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        </section>

        {/* Success Stories Section */}
        <section className="py-20 bg-gray-50">
          <div className="container mx-auto px-4">
            <div className="text-center mb-16">
              <Typography.Heading level="h2" className="text-4xl font-bold mb-6">
                Trusted by Leading Nigerian Businesses
              </Typography.Heading>
              <Typography.Text size="lg" className="text-gray-600">
                See how companies across Nigeria are transforming their e-invoicing processes
              </Typography.Text>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              {[
                {
                  company: "TechCorp Nigeria",
                  industry: "Technology",
                  testimonial: "TaxPoynt reduced our invoice processing time by 90%. What used to take our accounting team hours now happens automatically.",
                  author: "Adebayo Ogundimu",
                  role: "CFO",
                  metrics: "90% time reduction",
                  rating: 5
                },
                {
                  company: "Lagos Manufacturing Ltd",
                  industry: "Manufacturing", 
                  testimonial: "The seamless SAP integration meant we didn't have to change our existing processes. FIRS compliance became effortless.",
                  author: "Fatima Aliyu",
                  role: "Operations Director",
                  metrics: "100% FIRS compliance",
                  rating: 5
                },
                {
                  company: "Abuja Trading Co",
                  industry: "Trading",
                  testimonial: "Customer support is exceptional. They helped us set up everything in under an hour and we've been running smoothly ever since.",
                  author: "Chidi Okwu",
                  role: "Business Owner",
                  metrics: "1 hour setup time",
                  rating: 5
                }
              ].map((story, index) => (
                <Card key={index} className="bg-white shadow-lg hover:shadow-xl transition-shadow">
                  <CardContent className="p-8">
                    <div className="flex items-center space-x-1 mb-4">
                      {[...Array(story.rating)].map((_, i) => (
                        <Star key={i} className="h-4 w-4 fill-yellow-400 text-yellow-400" />
                      ))}
                    </div>
                    
                    <Typography.Text className="text-gray-700 italic mb-6 leading-relaxed">
                      "{story.testimonial}"
                    </Typography.Text>
                    
                    <div className="border-t pt-6">
                      <div className="flex items-center justify-between mb-4">
                        <div>
                          <div className="font-semibold text-gray-900">{story.author}</div>
                          <div className="text-sm text-gray-500">{story.role}</div>
                        </div>
                        <div className="text-right">
                          <div className="font-bold text-primary-600">{story.metrics}</div>
                          <div className="text-xs text-gray-500">Key Result</div>
                        </div>
                      </div>
                      <div className="text-sm text-gray-600">
                        <strong>{story.company}</strong> • {story.industry}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        </section>

        {/* Enhanced Call-to-Action */}
        <CallToAction 
          title="Ready to Transform Your E-Invoicing?"
          description="Join hundreds of Nigerian businesses already saving time and ensuring compliance with TaxPoynt. Get started in minutes with our guided setup process."
          trackingId="landing-bottom"
          showStats={true}
          showTestimonial={true}
        />

        {/* Footer */}
        <footer className="bg-gray-900 text-white py-12">
          <div className="container mx-auto px-4">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
              
              {/* Company Info */}
              <div className="space-y-4">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 bg-gradient-to-r from-primary-600 to-primary-700 rounded-lg flex items-center justify-center">
                    <span className="text-white font-bold text-lg">T</span>
                  </div>
                  <span className="text-xl font-bold">TaxPoynt</span>
                </div>
                <Typography.Text className="text-gray-300 text-sm">
                  Nigeria's premier e-invoicing platform with dual SI and APP certifications.
                </Typography.Text>
                <div className="flex items-center space-x-2">
                  <Shield className="h-4 w-4 text-green-400" />
                  <span className="text-sm text-gray-300">FIRS Certified</span>
                </div>
              </div>

              {/* Quick Links */}
              <div>
                <Typography.Heading level="h4" className="font-semibold mb-4">Product</Typography.Heading>
                <div className="space-y-2">
                  <a href="#" className="block text-gray-300 hover:text-white text-sm transition-colors">Features</a>
                  <a href="#" className="block text-gray-300 hover:text-white text-sm transition-colors">Integrations</a>
                  <a href="#" className="block text-gray-300 hover:text-white text-sm transition-colors">Pricing</a>
                  <a href="#" className="block text-gray-300 hover:text-white text-sm transition-colors">API Docs</a>
                </div>
              </div>

              <div>
                <Typography.Heading level="h4" className="font-semibold mb-4">Company</Typography.Heading>
                <div className="space-y-2">
                  <a href="#" className="block text-gray-300 hover:text-white text-sm transition-colors">About</a>
                  <a href="#" className="block text-gray-300 hover:text-white text-sm transition-colors">Blog</a>
                  <a href="#" className="block text-gray-300 hover:text-white text-sm transition-colors">Careers</a>
                  <a href="#" className="block text-gray-300 hover:text-white text-sm transition-colors">Contact</a>
                </div>
              </div>

              <div>
                <Typography.Heading level="h4" className="font-semibold mb-4">Support</Typography.Heading>
                <div className="space-y-2">
                  <a href="#" className="block text-gray-300 hover:text-white text-sm transition-colors">Documentation</a>
                  <a href="#" className="block text-gray-300 hover:text-white text-sm transition-colors">Help Center</a>
                  <a href="#" className="block text-gray-300 hover:text-white text-sm transition-colors">Status</a>
                  <a href="#" className="block text-gray-300 hover:text-white text-sm transition-colors">Security</a>
                </div>
              </div>
            </div>

            <div className="border-t border-gray-800 mt-12 pt-8 flex flex-col md:flex-row justify-between items-center">
              <Typography.Text className="text-gray-400 text-sm">
                © 2025 TaxPoynt. All rights reserved.
              </Typography.Text>
              
              <div className="flex items-center space-x-6 mt-4 md:mt-0">
                <a href="#" className="text-gray-400 hover:text-white text-sm transition-colors">Privacy Policy</a>
                <a href="#" className="text-gray-400 hover:text-white text-sm transition-colors">Terms of Service</a>
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                  <span className="text-gray-400 text-sm">All systems operational</span>
                </div>
              </div>
            </div>
          </div>
        </footer>
      </div>
    </>
  );
};

export default Week5LandingDemo;