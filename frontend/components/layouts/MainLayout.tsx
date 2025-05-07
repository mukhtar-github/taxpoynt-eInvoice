import React, { ReactNode } from 'react';
import Head from 'next/head';
import MainNav from '../ui/MainNav';
import { cn } from '../../utils/cn';

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
  title = 'Taxpoynt eInvoice',
  description = 'eInvoice management system for Nigerian businesses',
  showNav = true,
  className
}) => {
  return (
    <>
      <Head>
        <title>{title}</title>
        <meta name="description" content={description} />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <div className="min-h-screen bg-background flex flex-col">
        {showNav && (
          <MainNav 
            title="Taxpoynt eInvoice"
            onLogout={() => {
              // Placeholder for logout functionality
              console.log('Logout clicked');
            }}
          />
        )}

        <main className={cn("flex-1", className)}>
          {children}
        </main>

        <footer className="py-6 bg-background border-t border-border">
          <div className="container mx-auto px-4">
            <div className="flex flex-col md:flex-row justify-between items-center">
              <div className="mb-4 md:mb-0">
                <p className="text-sm text-text-secondary">
                  © {new Date().getFullYear()} Taxpoynt eInvoice. All rights reserved.
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
      </div>
    </>
  );
};

export default MainLayout;
