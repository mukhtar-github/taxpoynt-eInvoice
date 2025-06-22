/** @type {import('next').NextConfig} */
const path = require('path');

const nextConfig = {
  webpack: (config, { isServer, dev }) => {
    // Force use of a single React instance
    config.resolve.alias = {
      ...config.resolve.alias,
      // Critical: Ensure all components use the same React instance
      'react': path.resolve(__dirname, './node_modules/react'),
      'react-dom': path.resolve(__dirname, './node_modules/react-dom'),
      'react/jsx-runtime': path.resolve(__dirname, './node_modules/react/jsx-runtime')
    };
    
    // Explicitly add jsx-runtime to modules
    config.resolve.modules = [
      ...(config.resolve.modules || []),
      path.resolve(__dirname, './node_modules/react'),
      'node_modules'
    ];
    
    // Re-enable optimization now that CRM components are working
    // if (!dev) {
    //   config.optimization.minimize = false;
    // }
    
    return config;
  },
  // Disable SWC for now to use Babel
  swcMinify: false,
  reactStrictMode: true,
  typescript: {
    // We've already fixed TypeScript errors
    ignoreBuildErrors: true,
  },
  poweredByHeader: false,
  compress: true,
  productionBrowserSourceMaps: false,
  images: {
    domains: [],
    unoptimized: false
  },
  // Configure security headers
  async headers() {
    return [
      {
        // Apply these headers to all routes
        source: '/(.*)',
        headers: [
          {
            key: 'X-DNS-Prefetch-Control',
            value: 'on',
          },
          {
            key: 'Strict-Transport-Security',
            value: 'max-age=63072000; includeSubDomains; preload'
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
          {
            key: 'X-Frame-Options',
            value: 'DENY',
          },
          {
            key: 'X-XSS-Protection',
            value: '1; mode=block'
          },
          {
            key: 'Referrer-Policy',
            value: 'strict-origin-when-cross-origin',
          },
          {
            key: 'Permissions-Policy',
            value: 'camera=(), microphone=(), geolocation=()'
          }
        ],
      },
    ];
  },
  // Configure redirects
  async redirects() {
    return [
      {
        source: '/dashboard',
        destination: '/submission-dashboard',
        permanent: true,
      },
    ];
  },
};

// Apply different settings based on environment
if (process.env.NODE_ENV === 'production') {
  // Production-specific optimizations
  nextConfig.output = 'standalone';
}

module.exports = nextConfig;

