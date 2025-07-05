import React, { useEffect } from 'react';
import { useRouter } from 'next/router';
import Head from 'next/head';
import Link from 'next/link';
import { useAuth } from '../../context/AuthContext';
import MainLayout from '../../components/layouts/MainLayout';
import { EnhancedLoginForm } from '../../src/components/auth/EnhancedLoginForm';
import { ArrowLeft, Shield, Star, Zap } from 'lucide-react';

const EnhancedLoginPage: React.FC = () => {
  const { isAuthenticated } = useAuth();
  const router = useRouter();
  const { redirect, plan } = router.query;

  // If already authenticated, redirect
  useEffect(() => {
    if (isAuthenticated) {
      const redirectTo = redirect ? decodeURIComponent(redirect as string) : '/dashboard';
      router.push(redirectTo);
    }
  }, [isAuthenticated, redirect, router]);

  // If authenticated, don't render
  if (isAuthenticated) {
    return null;
  }

  const getContextualHeading = () => {
    if (plan) {
      return `Continue to ${plan} Plan`;
    }
    if (redirect) {
      return 'Sign in to continue';
    }
    return 'Welcome back to TaxPoynt';
  };

  const getContextualDescription = () => {
    if (plan) {
      return `Sign in to start your ${plan} plan free trial or create a new account`;
    }
    if (redirect) {
      return 'Please sign in to access the requested page';
    }
    return 'Sign in to your FIRS-compliant e-invoicing dashboard';
  };

  return (
    <MainLayout title={`Sign In${plan ? ` - ${plan} Plan` : ''} | TaxPoynt eInvoice`}>
      <Head>
        <meta 
          name="description" 
          content={`Sign in to your TaxPoynt eInvoice account${plan ? ` and continue with your ${plan} plan` : ''}. Access your FIRS-compliant e-invoicing dashboard.`}
        />
        <meta name="robots" content="noindex, follow" />
      </Head>

      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-green-50 py-12">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          {/* Header */}
          <div className="text-center mb-8">
            {/* Back Link */}
            {(plan || redirect) && (
              <Link 
                href={plan ? '/pricing' : '/'} 
                className="inline-flex items-center text-blue-600 hover:text-blue-700 text-sm font-medium mb-4"
              >
                <ArrowLeft className="mr-2 h-4 w-4" />
                {plan ? 'Back to Pricing' : 'Back to Home'}
              </Link>
            )}
            
            <h1 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              {getContextualHeading()}
            </h1>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              {getContextualDescription()}
            </p>
          </div>

          {/* Trust Indicators */}
          <div className="flex justify-center items-center space-x-8 mb-8 text-sm text-gray-600">
            <div className="flex items-center">
              <Shield className="h-4 w-4 text-green-600 mr-2" />
              <span>Bank-Grade Security</span>
            </div>
            <div className="flex items-center">
              <Star className="h-4 w-4 text-yellow-500 mr-2" />
              <span>FIRS Certified</span>
            </div>
            <div className="flex items-center">
              <Zap className="h-4 w-4 text-blue-600 mr-2" />
              <span>Instant Access</span>
            </div>
          </div>

          {/* Login Form */}
          <EnhancedLoginForm />

          {/* Help Section */}
          <div className="mt-12 text-center space-y-6">
            {/* Quick Help */}
            <div className="bg-white rounded-lg p-6 max-w-md mx-auto shadow-sm">
              <h3 className="font-semibold text-gray-900 mb-3">Need Help?</h3>
              <div className="space-y-2 text-sm text-gray-600">
                <div>
                  <Link href="/auth/forgot-password" className="text-blue-600 hover:underline">
                    Reset your password
                  </Link>
                </div>
                <div>
                  <Link href="/contact" className="text-blue-600 hover:underline">
                    Contact support
                  </Link>
                </div>
                <div>
                  <Link href="/demo" className="text-blue-600 hover:underline">
                    Schedule a demo
                  </Link>
                </div>
              </div>
            </div>

            {/* Footer Links */}
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

export default EnhancedLoginPage;