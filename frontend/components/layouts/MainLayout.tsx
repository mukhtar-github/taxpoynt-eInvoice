import React, { ReactNode } from 'react';
import Head from 'next/head';
import { useRouter } from 'next/router';
import MainNav from '../ui/MainNav';
import { cn } from '../../utils/cn';
import { useAuth } from '../../context/AuthContext';
import { Button } from '../ui/Button';
import { Typography } from '../ui/Typography';

interface MainLayoutProps {
  children: ReactNode;
  title?: string;
  description?: string;
  showNav?: boolean;
  className?: string;
}

/**
 * MainLayout Component
 * 
 * Main layout component that includes the navigation and provides a consistent
 * layout structure for the application. This replaces the previous Chakra UI
 * version with Tailwind CSS styling.
 */
const MainLayout: React.FC<MainLayoutProps> = ({
  children,
  title = 'Taxpoynt eInvoice | Automated Tax Compliance for Nigerian Businesses',
  description = 'Transform your tax compliance with Nigeria\'s premier e-invoicing platform. Save time, eliminate errors, and stay compliant with FIRS regulations.',
  showNav = true,
  className
}) => {
  const { isAuthenticated, user, logout } = useAuth();
  const router = useRouter();
  return (
    <>
      <Head>
        <title>{title}</title>
        <meta name="description" content={description} />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.svg" type="image/svg+xml" />
        <link rel="alternate icon" href="/favicon.ico" type="image/png" />
      </Head>

      <div className="min-h-screen bg-background flex flex-col">
        {showNav && (
          <MainNav 
            title="Taxpoynt eInvoice"
            userInfo={isAuthenticated ? {
              name: user?.name || '',
              email: user?.email || '',
            } : undefined}
            authButtons={!isAuthenticated ? (
              <div className="flex items-center space-x-4">
                <Button 
                  variant="ghost"
                  onClick={() => router.push('/auth/login')}
                >
                  Log In
                </Button>
                <Button 
                  variant="default"
                  onClick={() => router.push('/auth/signup')}
                >
                  Sign Up
                </Button>
              </div>
            ) : undefined}
            onLogout={logout}
          />
        )}

        <main className={cn("flex-1", className)}>
          {children}
        </main>
        
        {/* Hero section for homepage - only show on homepage when not authenticated */}
        {!isAuthenticated && router.pathname === '/' && (
          <div className="bg-gradient-to-r from-primary-600 to-primary-800 text-white relative">
            {/* Add overlay for better text visibility */}
            <div className="absolute inset-0 bg-black bg-opacity-25 z-0"></div>
            <div className="container mx-auto px-4 py-16 md:py-24 relative z-10">
              <div className="max-w-3xl mx-auto text-center">
                <Typography.Heading level="h1" className="text-3xl md:text-5xl font-bold mb-6 text-white drop-shadow-md">
                  Tax Compliance Made Effortless
                </Typography.Heading>
                <Typography.Text size="lg" className="mb-8 text-white drop-shadow-sm">
                  Taxpoynt delivers real-time e-invoicing that meets FIRS standards while saving you precious time.
                  Say goodbye to tax compliance headaches and hello to automated precision.
                </Typography.Text>
                <div className="flex flex-col sm:flex-row gap-4 justify-center">
                  <Button 
                    size="lg" 
                    variant="default" 
                    className="bg-white text-primary-700 hover:bg-gray-100 shadow-md font-semibold"
                    onClick={() => router.push('/auth/signup')}
                  >
                    Start Your Free Trial
                  </Button>
                  <Button 
                    size="lg" 
                    variant="outline" 
                    className="border-white text-white hover:bg-white/30 bg-primary-700/50 backdrop-blur-sm shadow-md font-semibold text-shadow-sm"
                    onClick={() => router.push('/features')}
                  >
                    See How It Works
                  </Button>
                </div>
                
                <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-8 text-left">
                  <div className="bg-white/10 p-6 rounded-lg">
                    <Typography.Heading level="h3" className="text-xl font-semibold mb-2">FIRS Compliant</Typography.Heading>
                    <Typography.Text>100% adherence to all e-invoicing regulations with automatic updates</Typography.Text>
                  </div>
                  <div className="bg-white/10 p-6 rounded-lg">
                    <Typography.Heading level="h3" className="text-xl font-semibold mb-2">Time-Saving</Typography.Heading>
                    <Typography.Text>Reduce invoice processing time by up to 80% with automation</Typography.Text>
                  </div>
                  <div className="bg-white/10 p-6 rounded-lg">
                    <Typography.Heading level="h3" className="text-xl font-semibold mb-2">Error-Free</Typography.Heading>
                    <Typography.Text>Eliminate manual calculation errors and compliance risks</Typography.Text>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
        
        {/* Footer - Different versions for public pages and authenticated users */}
        {!isAuthenticated && !router.pathname.startsWith('/dashboard') ? (
          <footer className="bg-gray-50 dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 py-12">
            <div className="container mx-auto px-4">
              <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
                <div className="md:col-span-2">
                  <Typography.Heading level="h3" className="text-xl font-bold mb-4">Taxpoynt eInvoice</Typography.Heading>
                  <Typography.Text variant="secondary" className="max-w-md mb-6">
                    Nigeria's leading e-invoicing platform that streamlines tax compliance for businesses of all sizes.
                    Certified by FIRS and trusted by thousands of companies across Nigeria.
                  </Typography.Text>
                  <div className="flex space-x-4">
                    <a href="#" aria-label="Twitter" className="text-gray-400 hover:text-primary">
                      <svg className="h-6 w-6" fill="currentColor" viewBox="0 0 24 24"><path d="M8.29 20.251c7.547 0 11.675-6.253 11.675-11.675 0-.178 0-.355-.012-.53A8.348 8.348 0 0022 5.92a8.19 8.19 0 01-2.357.646 4.118 4.118 0 001.804-2.27 8.224 8.224 0 01-2.605.996 4.107 4.107 0 00-6.993 3.743 11.65 11.65 0 01-8.457-4.287 4.106 4.106 0 001.27 5.477A4.072 4.072 0 012.8 9.713v.052a4.105 4.105 0 003.292 4.022 4.095 4.095 0 01-1.853.07 4.108 4.108 0 003.834 2.85A8.233 8.233 0 012 18.407a11.616 11.616 0 006.29 1.84"></path></svg>
                    </a>
                    <a href="#" aria-label="LinkedIn" className="text-gray-400 hover:text-primary">
                      <svg className="h-6 w-6" fill="currentColor" viewBox="0 0 24 24"><path d="M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.239 5-5v-14c0-2.761-2.238-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.79-1.75-1.764s.784-1.764 1.75-1.764 1.75.79 1.75 1.764-.783 1.764-1.75 1.764zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z"></path></svg>
                    </a>
                  </div>
                </div>
                <div>
                  <Typography.Heading level="h3" className="text-lg font-semibold mb-4">Resources</Typography.Heading>
                  <ul className="space-y-2">
                    <li><a href="#" className="hover:text-primary">Documentation</a></li>
                    <li><a href="#" className="hover:text-primary">API Reference</a></li>
                    <li><a href="#" className="hover:text-primary">Support Center</a></li>
                    <li><a href="#" className="hover:text-primary">FIRS Guidelines</a></li>
                  </ul>
                </div>
                <div>
                  <Typography.Heading level="h3" className="text-lg font-semibold mb-4">Company</Typography.Heading>
                  <ul className="space-y-2">
                    <li><a href="#" className="hover:text-primary">About Us</a></li>
                    <li><a href="#" className="hover:text-primary">Careers</a></li>
                    <li><a href="#" className="hover:text-primary">Blog</a></li>
                    <li><a href="#" className="hover:text-primary">Contact</a></li>
                  </ul>
                  <Typography.Text variant="secondary" className="mt-6">
                    <strong>Email:</strong> support@taxpoynt.com<br />
                    <strong>Address:</strong> Abuja, Nigeria
                  </Typography.Text>
                </div>
              </div>
              <div className="border-t border-gray-200 dark:border-gray-700 mt-8 pt-6 flex flex-col md:flex-row justify-between items-center gap-4">
                <Typography.Text variant="secondary" className="text-sm">
                  {'©'} {Number(new Date().getFullYear())} Taxpoynt Technologies Ltd. All rights reserved. FIRS Certified Provider.
                </Typography.Text>
                <div className="text-sm text-gray-500">
                  <a href="#" className="hover:text-primary mr-6">Privacy Policy</a>
                  <a href="#" className="hover:text-primary">Terms of Service</a>
                </div>
              </div>
            </div>
          </footer>
        ) : (
          <footer className="py-6 bg-background border-t border-border">
            <div className="container mx-auto px-4">
              <div className="flex flex-col md:flex-row justify-between items-center">
                <div className="mb-4 md:mb-0">
                  <p className="text-sm text-text-secondary">
                    {'©'} {Number(new Date().getFullYear())} Taxpoynt eInvoice. All rights reserved.
                  </p>
                </div>
                
                <div className="flex space-x-6">
                  <a 
                    href="#"
                    className="text-sm text-text-secondary hover:text-primary"
                  >
                    Privacy Policy
                  </a>
                  <a 
                    href="#"
                    className="text-sm text-text-secondary hover:text-primary"
                  >
                    Terms of Service
                  </a>
                  <a 
                    href="#"
                    className="text-sm text-text-secondary hover:text-primary"
                  >
                    Support
                  </a>
                </div>
              </div>
            </div>
          </footer>
        )}
      </div>
    </>
  );
};

export default MainLayout;
