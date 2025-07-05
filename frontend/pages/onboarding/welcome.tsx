import React, { useEffect } from 'react';
import { useRouter } from 'next/router';
import Head from 'next/head';
import { useAuth } from '../../context/AuthContext';
import MainLayout from '../../components/layouts/MainLayout';
import { OnboardingWizard } from '../../src/components/onboarding/OnboardingWizard';

const OnboardingWelcomePage: React.FC = () => {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();

  // Redirect if not authenticated
  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/auth/enhanced-login?redirect=' + encodeURIComponent('/onboarding/welcome'));
    }
  }, [isAuthenticated, isLoading, router]);

  // Check if onboarding is already completed
  useEffect(() => {
    if (isAuthenticated) {
      const onboardingCompleted = localStorage.getItem('onboarding_completed');
      if (onboardingCompleted === 'true') {
        router.push('/dashboard');
      }
    }
  }, [isAuthenticated, router]);

  // Show loading or redirect
  if (isLoading || !isAuthenticated) {
    return (
      <MainLayout title="Setting up your account | TaxPoynt eInvoice">
        <div className="min-h-screen flex items-center justify-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      </MainLayout>
    );
  }

  return (
    <MainLayout title="Welcome & Setup | TaxPoynt eInvoice">
      <Head>
        <meta 
          name="description" 
          content="Complete your TaxPoynt eInvoice account setup. Configure your FIRS compliance settings and business information."
        />
        <meta name="robots" content="noindex, follow" />
      </Head>

      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-green-50 py-12">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          <OnboardingWizard />
        </div>
      </div>
    </MainLayout>
  );
};

export default OnboardingWelcomePage;