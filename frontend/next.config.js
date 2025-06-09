/** @type {import('next').NextConfig} */
const nextConfig = {
  webpack: (config) => {
    // Fix React dependency resolution issues with Radix UI
    config.resolve.alias = {
      ...config.resolve.alias,
      'react': require.resolve('react'),
      'react-dom': require.resolve('react-dom'),
      'react/jsx-runtime': require.resolve('react/jsx-runtime')
    };
    return config;
  },
  reactStrictMode: true,
  // Exclude Cypress files from the build process
  typescript: {
    // Skip type checking of Cypress files during production builds
    ignoreBuildErrors: false,
    tsconfigPath: './tsconfig.json',
  },
  poweredByHeader: false,
  compress: true,
  productionBrowserSourceMaps: false,
  swcMinify: true,
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

