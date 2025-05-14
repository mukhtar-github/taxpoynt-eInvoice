import React, { useEffect } from 'react';
import { useRouter } from 'next/router';
import MainLayout from '../components/layouts/MainLayout';
import { useAuth } from '../context/AuthContext';
import { Button } from '../components/ui/Button';
import { Typography } from '../components/ui/Typography';
import { Card, CardContent } from '../components/ui/Card';
import Image from 'next/image';
import Head from 'next/head';
import { ArrowRight, FileCheck, Clock, BarChart2, CheckCircle } from 'lucide-react';

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
        <title>Taxpoynt eInvoice | Automated Tax Compliance for Nigerian Businesses</title>
        <meta name="description" content="Transform your tax compliance with Nigeria's premier e-invoicing platform. Save time, eliminate errors, and stay compliant with FIRS regulations." />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.svg" type="image/svg+xml" />
        <link rel="alternate icon" href="/favicon.ico" type="image/png" />
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
                Transforming Tax Compliance for Nigerian Businesses
              </Typography.Heading>
              <Typography.Text size="lg" className="text-white/90 leading-relaxed max-w-xl">
                Automate your e-invoicing workflow, ensure FIRS compliance, and eliminate manual errors with our comprehensive platform designed specifically for Nigerian businesses.
              </Typography.Text>
              <div className="flex flex-col sm:flex-row gap-4 pt-4">
                <Button 
                  size="lg"
                  variant="default" 
                  className="bg-white text-primary-700 hover:bg-gray-100"
                  onClick={() => router.push('/auth/signup')}
                >
                  Start Your Free Trial
                </Button>
                <Button 
                  size="lg"
                  variant="outline" 
                  className="border-white text-white hover:bg-white/30 group bg-primary-700/50 backdrop-blur-sm shadow-md"
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
                      src="/logo.svg" 
                      alt="Taxpoynt eInvoice" 
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

        {/* Features Section */}
        <div className="py-16 bg-gray-50">
          <div className="container mx-auto px-4">
            <div className="text-center max-w-3xl mx-auto mb-12">
              <Typography.Heading level="h2" className="text-3xl font-bold mb-4">
                Why Choose Taxpoynt eInvoice?
              </Typography.Heading>
              <Typography.Text size="lg" className="text-gray-600">
                Our platform is designed to simplify tax compliance for Nigerian businesses of all sizes.
              </Typography.Text>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
              {[
                { 
                  icon: <FileCheck className="h-10 w-10 text-primary-600" />, 
                  title: 'FIRS Compliant', 
                  description: 'Generate IRNs that meet all FIRS requirements automatically.' 
                },
                { 
                  icon: <Clock className="h-10 w-10 text-primary-600" />, 
                  title: 'Save Time', 
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
          </div>
        </div>
      </MainLayout>
    </>
  );
};

export default Home; 