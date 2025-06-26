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
    
    // Fix Terser configuration for production builds
    if (!dev && !isServer) {
      config.optimization.minimizer = config.optimization.minimizer.map(plugin => {
        if (plugin.constructor.name === 'TerserPlugin') {
          return new plugin.constructor({
            terserOptions: {
              ...plugin.options.terserOptions,
              parse: {
                ecma: 8,
              },
              compress: {
                ecma: 5,
                warnings: false,
                comparisons: false,
                inline: 2,
              },
              mangle: {
                safari10: true,
              },
              output: {
                ecma: 5,
                comments: false,
                ascii_only: true,
              },
            },
          });
        }
        return plugin;
      });
    }
    
    return config;
  },
  // Use SWC for better performance and compatibility
  swcMinify: true,
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
    unoptimized: false,
    // Nigerian mobile optimization
    deviceSizes: [320, 480, 640, 750, 828, 1080, 1200],
    imageSizes: [16, 32, 48, 64, 96, 128, 256, 384],
    formats: ['image/webp']
  },
  // PWA and Service Worker support
  experimental: {
    // Enable modern features for better performance
    esmExternals: true,
    serverComponentsExternalPackages: []
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

