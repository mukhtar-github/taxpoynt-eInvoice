import React from 'react';
import type { AppProps } from 'next/app';
import '../styles/globals.css';

/**
 * Main application component
 * 
 * This has been migrated from Chakra UI to use Tailwind CSS
 * The theme is now controlled through Tailwind configuration
 */
function MyApp({ Component, pageProps }: AppProps) {
  return (
    <div className="min-h-screen bg-background font-body text-text-primary">
      <Component {...pageProps} />
    </div>
  );
}

export default MyApp;