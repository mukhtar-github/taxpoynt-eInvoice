import React, { useEffect } from 'react';
import { useRouter } from 'next/router';
import Head from 'next/head';
import { useAuth } from '../context/AuthContext';
import MainLayout from '../components/layouts/MainLayout';
import { 
  FeatureShowcase, 
  BenefitsVisualization, 
  PlatformCapabilities, 
  IntegrationEcosystem 
} from '../components/landing';
import { Typography } from '../components/ui/Typography';
import { Card, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { 
  Zap, 
  Award, 
  Settings, 
  Globe,
  ArrowRight,
  CheckCircle,
  Star,
  Users,
  TrendingUp
} from 'lucide-react';

const Day3Day4FeatureShowcaseDemo: React.FC = () => {
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
        <title>Day 3-4: Feature Showcase System | TaxPoynt E-Invoice</title>
        <meta name="description" content="Day 3-4 Feature Showcase System: Feature cards grid, benefits visualization, platform capabilities with progressive disclosure, and integration ecosystem preview." />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/icons/logo.svg" type="image/svg+xml" />
      </Head>

      <div className="min-h-screen bg-white">
        
        {/* Enhanced Header */}
        <header className="bg-gradient-to-r from-gray-900 via-blue-900 to-purple-900 text-white py-16">
          <div className="container mx-auto px-4">
            <div className="max-w-4xl mx-auto text-center">
              
              {/* Demo Badge */}
              <div className="inline-flex items-center space-x-2 bg-white/10 backdrop-blur-md border border-white/20 rounded-full px-4 py-2 mb-6">
                <Zap className="h-4 w-4 text-yellow-400" />
                <span className="font-medium text-sm">Day 3-4 Implementation Demo</span>
              </div>

              {/* Title */}
              <Typography.Heading level="h1" className="text-4xl md:text-6xl font-bold mb-6 leading-tight">
                Feature Showcase System
              </Typography.Heading>

              {/* Subtitle */}
              <Typography.Text size="lg" className="text-white/90 leading-relaxed mb-8 max-w-3xl mx-auto">
                Experience our comprehensive feature showcase system with interactive cards, benefits visualization, 
                platform capabilities with progressive disclosure, and integration ecosystem preview.
              </Typography.Text>

              {/* Feature Highlights */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
                <div className="bg-white/10 backdrop-blur-sm rounded-lg p-4 border border-white/20">
                  <Zap className="h-8 w-8 text-yellow-400 mb-3 mx-auto" />
                  <div className="text-sm font-medium">Feature Cards Grid</div>
                  <div className="text-xs text-white/70">Interactive hover animations</div>
                </div>
                <div className="bg-white/10 backdrop-blur-sm rounded-lg p-4 border border-white/20">
                  <Award className="h-8 w-8 text-green-400 mb-3 mx-auto" />
                  <div className="text-sm font-medium">Benefits Visualization</div>
                  <div className="text-xs text-white/70">Icons & micro-interactions</div>
                </div>
                <div className="bg-white/10 backdrop-blur-sm rounded-lg p-4 border border-white/20">
                  <Settings className="h-8 w-8 text-blue-400 mb-3 mx-auto" />
                  <div className="text-sm font-medium">Platform Capabilities</div>
                  <div className="text-xs text-white/70">Progressive disclosure</div>
                </div>
                <div className="bg-white/10 backdrop-blur-sm rounded-lg p-4 border border-white/20">
                  <Globe className="h-8 w-8 text-purple-400 mb-3 mx-auto" />
                  <div className="text-sm font-medium">Integration Ecosystem</div>
                  <div className="text-xs text-white/70">Interactive preview</div>
                </div>
              </div>

              {/* CTA */}
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <Button 
                  size="lg"
                  className="bg-white text-gray-900 hover:bg-gray-100 font-bold shadow-xl"
                  onClick={() => {
                    const featureSection = document.getElementById('feature-showcase');
                    if (featureSection) {
                      featureSection.scrollIntoView({ behavior: 'smooth' });
                    }
                  }}
                >
                  Explore Features
                  <ArrowRight className="ml-2 h-5 w-5" />
                </Button>
                
                <Button 
                  size="lg"
                  variant="outline" 
                  className="border-white/30 text-white hover:bg-white/10 backdrop-blur-sm"
                  onClick={() => router.push('/auth/signup')}
                >
                  Start Free Trial
                </Button>
              </div>
            </div>
          </div>
        </header>

        {/* Navigation Bar */}
        <nav className="sticky top-0 z-50 bg-white/95 backdrop-blur-md border-b border-gray-200">
          <div className="container mx-auto px-4">
            <div className="flex items-center justify-between h-16">
              
              {/* Logo */}
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 bg-gradient-to-r from-primary-600 to-primary-700 rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold">T</span>
                </div>
                <span className="font-bold text-gray-900">TaxPoynt</span>
                <span className="text-sm bg-blue-100 text-blue-800 px-2 py-1 rounded-full font-medium">
                  Day 3-4 Demo
                </span>
              </div>

              {/* Quick Navigation */}
              <div className="hidden md:flex items-center space-x-6">
                <a 
                  href="#feature-showcase" 
                  className="text-gray-600 hover:text-primary-600 font-medium transition-colors"
                >
                  Features
                </a>
                <a 
                  href="#benefits" 
                  className="text-gray-600 hover:text-primary-600 font-medium transition-colors"
                >
                  Benefits
                </a>
                <a 
                  href="#capabilities" 
                  className="text-gray-600 hover:text-primary-600 font-medium transition-colors"
                >
                  Capabilities
                </a>
                <a 
                  href="#integrations" 
                  className="text-gray-600 hover:text-primary-600 font-medium transition-colors"
                >
                  Integrations
                </a>
              </div>

              <Button onClick={() => router.push('/auth/signup')}>
                Get Started
              </Button>
            </div>
          </div>
        </nav>

        {/* Feature Showcase Section */}
        <section id="feature-showcase">
          <FeatureShowcase 
            showCategories={true}
            maxFeatures={9} // Show 9 features for demo
          />
        </section>

        {/* Separator */}
        <div className="bg-gradient-to-r from-primary-50 to-cyan-50 py-12">
          <div className="container mx-auto px-4 text-center">
            <div className="max-w-3xl mx-auto">
              <Typography.Heading level="h3" className="text-2xl font-bold mb-4">
                Comprehensive Business Impact
              </Typography.Heading>
              <Typography.Text size="lg" className="text-gray-600">
                See how our platform delivers measurable benefits across all aspects of your e-invoicing operations.
              </Typography.Text>
            </div>
          </div>
        </div>

        {/* Benefits Visualization Section */}
        <section id="benefits">
          <BenefitsVisualization 
            showMetrics={true}
          />
        </section>

        {/* Separator */}
        <div className="bg-gradient-to-r from-blue-50 to-purple-50 py-12">
          <div className="container mx-auto px-4 text-center">
            <div className="max-w-3xl mx-auto">
              <Typography.Heading level="h3" className="text-2xl font-bold mb-4">
                Technical Excellence & Innovation
              </Typography.Heading>
              <Typography.Text size="lg" className="text-gray-600">
                Explore the advanced technical capabilities that power our enterprise-grade e-invoicing platform.
              </Typography.Text>
            </div>
          </div>
        </div>

        {/* Platform Capabilities Section */}
        <section id="capabilities">
          <PlatformCapabilities 
            defaultExpanded={['data-processing']} // Start with one expanded for demo
          />
        </section>

        {/* Separator */}
        <div className="bg-gradient-to-r from-purple-50 to-pink-50 py-12">
          <div className="container mx-auto px-4 text-center">
            <div className="max-w-3xl mx-auto">
              <Typography.Heading level="h3" className="text-2xl font-bold mb-4">
                Seamless System Integrations
              </Typography.Heading>
              <Typography.Text size="lg" className="text-gray-600">
                Connect with your existing business systems through our comprehensive integration ecosystem.
              </Typography.Text>
            </div>
          </div>
        </div>

        {/* Integration Ecosystem Section */}
        <section id="integrations">
          <IntegrationEcosystem 
            showFilters={true}
            maxIntegrations={12} // Show 12 integrations for demo
          />
        </section>

        {/* Summary Section */}
        <section className="py-20 bg-gradient-to-r from-gray-900 via-blue-900 to-purple-900 text-white">
          <div className="container mx-auto px-4">
            <div className="max-w-4xl mx-auto text-center">
              
              <Typography.Heading level="h2" className="text-3xl md:text-4xl font-bold mb-6">
                Day 3-4 Implementation Complete
              </Typography.Heading>
              
              <Typography.Text size="lg" className="text-white/90 leading-relaxed mb-12">
                Experience the full Feature Showcase System with interactive cards, comprehensive benefits visualization, 
                progressive disclosure capabilities, and our complete integration ecosystem.
              </Typography.Text>

              {/* Implementation Stats */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-12">
                <div className="text-center">
                  <div className="text-3xl font-bold mb-2 text-yellow-400">9+</div>
                  <div className="text-white/80">Feature Categories</div>
                </div>
                <div className="text-center">
                  <div className="text-3xl font-bold mb-2 text-green-400">6</div>
                  <div className="text-white/80">Benefit Metrics</div>
                </div>
                <div className="text-center">
                  <div className="text-3xl font-bold mb-2 text-blue-400">6</div>
                  <div className="text-white/80">Platform Capabilities</div>
                </div>
                <div className="text-center">
                  <div className="text-3xl font-bold mb-2 text-purple-400">10+</div>
                  <div className="text-white/80">System Integrations</div>
                </div>
              </div>

              {/* Key Features Achieved */}
              <div className="bg-white/10 backdrop-blur-md rounded-2xl p-8 mb-12 border border-white/20">
                <Typography.Heading level="h3" className="text-xl font-bold mb-6">
                  Key Features Implemented
                </Typography.Heading>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-left">
                  <div className="space-y-3">
                    <div className="flex items-center space-x-3">
                      <CheckCircle className="h-5 w-5 text-green-400" />
                      <span>Feature Cards Grid with hover animations</span>
                    </div>
                    <div className="flex items-center space-x-3">
                      <CheckCircle className="h-5 w-5 text-green-400" />
                      <span>Category filtering and search</span>
                    </div>
                    <div className="flex items-center space-x-3">
                      <CheckCircle className="h-5 w-5 text-green-400" />
                      <span>Progressive disclosure for detailed features</span>
                    </div>
                    <div className="flex items-center space-x-3">
                      <CheckCircle className="h-5 w-5 text-green-400" />
                      <span>Animated counters and metrics</span>
                    </div>
                  </div>
                  
                  <div className="space-y-3">
                    <div className="flex items-center space-x-3">
                      <CheckCircle className="h-5 w-5 text-green-400" />
                      <span>Benefits visualization with micro-interactions</span>
                    </div>
                    <div className="flex items-center space-x-3">
                      <CheckCircle className="h-5 w-5 text-green-400" />
                      <span>Platform capabilities overview</span>
                    </div>
                    <div className="flex items-center space-x-3">
                      <CheckCircle className="h-5 w-5 text-green-400" />
                      <span>Integration ecosystem with filters</span>
                    </div>
                    <div className="flex items-center space-x-3">
                      <CheckCircle className="h-5 w-5 text-green-400" />
                      <span>Scroll-triggered animations</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Final CTA */}
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <Button 
                  size="lg"
                  className="bg-white text-gray-900 hover:bg-gray-100 font-bold shadow-xl"
                  onClick={() => router.push('/auth/signup')}
                >
                  Experience the Platform
                  <ArrowRight className="ml-2 h-5 w-5" />
                </Button>
                
                <Button 
                  size="lg"
                  variant="outline" 
                  className="border-white/30 text-white hover:bg-white/10 backdrop-blur-sm"
                  onClick={() => router.push('/')}
                >
                  View Main Landing Page
                </Button>
              </div>
            </div>
          </div>
        </section>

        {/* Footer */}
        <footer className="bg-gray-900 text-white py-12">
          <div className="container mx-auto px-4">
            <div className="text-center">
              <div className="flex items-center justify-center space-x-3 mb-4">
                <div className="w-8 h-8 bg-gradient-to-r from-primary-600 to-primary-700 rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold">T</span>
                </div>
                <span className="text-xl font-bold">TaxPoynt</span>
              </div>
              
              <Typography.Text className="text-gray-300 mb-4">
                Day 3-4: Feature Showcase System Implementation Demo
              </Typography.Text>
              
              <div className="flex items-center justify-center space-x-6">
                <div className="flex items-center space-x-2">
                  <Star className="h-4 w-4 text-yellow-400" />
                  <span className="text-sm text-gray-300">Interactive Features</span>
                </div>
                <div className="flex items-center space-x-2">
                  <Users className="h-4 w-4 text-blue-400" />
                  <span className="text-sm text-gray-300">User-Centric Design</span>
                </div>
                <div className="flex items-center space-x-2">
                  <TrendingUp className="h-4 w-4 text-green-400" />
                  <span className="text-sm text-gray-300">Performance Optimized</span>
                </div>
              </div>
            </div>
          </div>
        </footer>
      </div>
    </>
  );
};

export default Day3Day4FeatureShowcaseDemo;