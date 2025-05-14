import React from 'react';
import type { AppProps } from 'next/app';
import { ToastProvider } from '../components/ui/Toast';
import { AuthProvider } from '../context/AuthContext';
import '../styles/globals.css';

/**
 * Main application component
 * 
 * This has been migrated from Chakra UI to use Tailwind CSS
 * The theme is now controlled through Tailwind configuration
 */
function MyApp({ Component, pageProps }: AppProps) {
  return (
    <ToastProvider position="top-right">
      <AuthProvider>
        <div className="min-h-screen bg-background font-body text-text-primary">
          <Component {...pageProps} />
        </div>
      </AuthProvider>
    </ToastProvider>
  );
}

export default MyApp;