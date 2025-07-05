import React, { useEffect } from 'react';
import { useRouter } from 'next/router';
import Head from 'next/head';
import Link from 'next/link';
import { useAuth } from '../../context/AuthContext';
import MainLayout from '../../components/layouts/MainLayout';
import { StreamlinedRegistrationForm } from '../../src/components/auth/StreamlinedRegistrationForm';
import { ArrowLeft, Star, Shield, Zap } from 'lucide-react';

const EnhancedSignupPage: React.FC = () => {
  const { isAuthenticated } = useAuth();
  const router = useRouter();
  const { plan } = router.query;

  // If already authenticated, redirect to dashboard
  useEffect(() => {
    if (isAuthenticated) {
      router.push('/dashboard');
    }
  }, [isAuthenticated, router]);

  // If not authenticated, prevent rendering
  if (isAuthenticated) {
    return null;
  }

  const getPlanDisplayName = (planName?: string) => {
    if (!planName) return '';
    const planNames = {
      starter: 'Starter',
      business: 'Business',
      enterprise: 'Enterprise'
    };
    return planNames[planName.toLowerCase() as keyof typeof planNames] || planName;
  };

  return (
    <MainLayout title={`Create Account${plan ? ` - ${getPlanDisplayName(plan as string)} Plan` : ''} | TaxPoynt eInvoice`}>
      <Head>
        <meta 
          name="description" 
          content={`Create your TaxPoynt eInvoice account${plan ? ` and start your ${getPlanDisplayName(plan as string)} plan free trial` : ''}. FIRS-compliant e-invoicing for Nigerian businesses.`}
        />
        <meta name="robots" content="noindex, follow" />
      </Head>

      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-green-50 py-12">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          {/* Header */}
          <div className="text-center mb-8">
            <Link 
              href="/pricing" 
              className="inline-flex items-center text-blue-600 hover:text-blue-700 text-sm font-medium mb-4"
            >
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back to Pricing
            </Link>
            
            <h1 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              {plan ? `Join TaxPoynt with ${getPlanDisplayName(plan as string)}` : 'Join TaxPoynt eInvoice'}
            </h1>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              Start your journey to FIRS compliance with Nigeria's leading e-invoicing platform.
              {plan && ' Your 14-day free trial starts immediately.'}
            </p>
          </div>

          {/* Trust Indicators */}
          <div className="flex justify-center items-center space-x-8 mb-8 text-sm text-gray-600">
            <div className="flex items-center">
              <Shield className="h-4 w-4 text-green-600 mr-2" />
              <span>FIRS Certified</span>
            </div>
            <div className="flex items-center">
              <Star className="h-4 w-4 text-yellow-500 mr-2" />
              <span>5,000+ Happy Users</span>
            </div>
            <div className="flex items-center">
              <Zap className="h-4 w-4 text-blue-600 mr-2" />
              <span>Setup in 5 Minutes</span>
            </div>
          </div>

          {/* Registration Form */}
          <StreamlinedRegistrationForm />

          {/* Footer Links */}
          <div className="text-center mt-12 space-y-4">
            <div className="text-sm text-gray-500">
              Need help? Contact our{' '}
              <Link href="/contact" className="text-blue-600 hover:underline">
                support team
              </Link>
              {' '}or{' '}
              <Link href="/demo" className="text-blue-600 hover:underline">
                schedule a demo
              </Link>
            </div>
            
            <div className="flex justify-center space-x-6 text-sm text-gray-400">
              <Link href="/terms" className="hover:text-gray-600">Terms</Link>
              <Link href="/privacy" className="hover:text-gray-600">Privacy</Link>
              <Link href="/security" className="hover:text-gray-600">Security</Link>
              <Link href="/support" className="hover:text-gray-600">Support</Link>
            </div>
          </div>
        </div>
      </div>
    </MainLayout>
  );
};

export default EnhancedSignupPage;