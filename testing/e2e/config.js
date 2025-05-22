/**
 * End-to-End Testing Configuration
 * 
 * This file contains configuration for testing the deployed TaxPoynt eInvoice environment
 */

module.exports = {
  // Base URLs for testing different environments
  urls: {
    // Replace with your actual deployment URLs
    frontend: process.env.TEST_FRONTEND_URL || 'https://taxpoynt.com',
    backend: process.env.TEST_BACKEND_URL || 'https://api.taxpoynt.com/api/v1',
    // FIRS sandbox API for testing
    firsSandbox: 'https://eivc-k6z6d.ondigitalocean.app/api/v1'
  },
  
  // Test user credentials
  testUser: {
    email: process.env.TEST_USER_EMAIL || 'test@example.com',
    password: process.env.TEST_USER_PASSWORD || 'your-test-password'
  },
  
  // Odoo test configuration
  odooTest: {
    url: process.env.TEST_ODOO_URL || 'https://taxpoyntcom2.odoo.com/odoo',
    database: process.env.TEST_ODOO_DB || 'odoo_test',
    username: process.env.TEST_ODOO_USER || 'admin',
    password: process.env.TEST_ODOO_PASSWORD || 'admin',
    // Sample invoice ID to use for testing
    testInvoiceId: process.env.TEST_INVOICE_ID || '12345'
  },
  
  // FIRS test configuration
  firsTest: {
    apiKey: process.env.TEST_FIRS_API_KEY || 'your-test-api-key',
    clientId: process.env.TEST_FIRS_CLIENT_ID || 'your-test-client-id',
    clientSecret: process.env.TEST_FIRS_CLIENT_SECRET || 'your-test-client-secret',
    useSandbox: true // Always use sandbox for automated tests
  },
  
  // Test timeouts
  timeouts: {
    defaultWait: 5000, // 5 seconds
    longOperation: 30000, // 30 seconds for longer operations
    pageLoad: 10000 // 10 seconds for page loads
  }
};
