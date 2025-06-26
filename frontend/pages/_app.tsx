import React, { useEffect } from 'react';
import type { AppProps } from 'next/app';
import { ToastProvider } from '../components/ui/Toast';
import { AuthProvider } from '../context/AuthContext';
import { TransmissionProvider } from '../context/TransmissionContext';
import '../styles/globals.css';

/**
 * Main application component
 * 
 * This has been migrated from Chakra UI to use Tailwind CSS
 * The theme is now controlled through Tailwind configuration
 */
function MyApp({ Component, pageProps }: AppProps) {
  useEffect(() => {
    // Register service worker for PWA functionality
    if ('serviceWorker' in navigator && process.env.NODE_ENV === 'production') {
      navigator.serviceWorker.register('/sw.js')
        .then((registration) => {
          console.log('Service Worker registered successfully:', registration);
        })
        .catch((error) => {
          console.log('Service Worker registration failed:', error);
        });
    }
    
    // Add PWA manifest link
    const link = document.createElement('link');
    link.rel = 'manifest';
    link.href = '/manifest.json';
    document.head.appendChild(link);
    
    // Add theme color meta tag
    const themeColor = document.createElement('meta');
    themeColor.name = 'theme-color';
    themeColor.content = '#16a34a';
    document.head.appendChild(themeColor);
    
    return () => {
      // Cleanup if needed
      document.head.removeChild(link);
      document.head.removeChild(themeColor);
    };
  }, []);

  return (
    <ToastProvider position="top-right">
      <AuthProvider>
        <TransmissionProvider>
          <div className="min-h-screen bg-background font-body text-text-primary">
            <Component {...pageProps} />
          </div>
        </TransmissionProvider>
      </AuthProvider>
    </ToastProvider>
  );
}

export default MyApp;