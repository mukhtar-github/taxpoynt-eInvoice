/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Exclude Cypress files from the build process
  typescript: {
    // Skip type checking of Cypress files during production builds
    ignoreBuildErrors: false,
    tsconfigPath: './tsconfig.json',
  },
}

module.exports = nextConfig

