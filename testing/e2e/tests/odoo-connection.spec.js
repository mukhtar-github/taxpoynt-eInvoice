// @ts-check
const { test, expect } = require('@playwright/test');
const axios = require('axios');
require('dotenv').config({ path: process.env.ENV_FILE || '.env.test' });

/**
 * Odoo Connection Test for TaxPoynt eInvoice
 * 
 * This test validates:
 * 1. API authentication
 * 2. Odoo connectivity status
 * 3. Lists available invoices for testing
 */

// Test data
const TEST_USER = {
  email: process.env.TEST_USER_EMAIL || 'test@example.com',
  password: process.env.TEST_USER_PASSWORD || 'test-password'
};

// API endpoint configuration
const API_BASE_URL = process.env.TEST_BACKEND_URL || 'http://localhost:8000/api/v1';
const LOGIN_ENDPOINT = `${API_BASE_URL}/auth/login`;
const ODOO_STATUS_ENDPOINT = `${API_BASE_URL}/integration/status/odoo`;
const INVOICE_ENDPOINT = `${API_BASE_URL}/invoices`;

// Create axios instance with extended timeout for potentially slow connections
const apiClient = axios.create({
  timeout: 60000,
  headers: {
    'Content-Type': 'application/json',
    'User-Agent': 'TaxPoynt-E2E-Test-OdooConnection'
  }
});

// Test suite
test.describe('Odoo Connection Verification', () => {
  let authToken;

  // Setup - authenticate before tests
  test.beforeAll(async () => {
    try {
      console.log(`Authenticating with API at ${API_BASE_URL}...`);
      const response = await apiClient.post(LOGIN_ENDPOINT, {
        email: TEST_USER.email,
        password: TEST_USER.password
      });

      authToken = response.data.token;
      console.log('Authentication successful ✅');
      
      // Set auth token for all future requests
      apiClient.defaults.headers.common['Authorization'] = `Bearer ${authToken}`;
    } catch (error) {
      console.error('❌ Authentication failed:', error.message);
      if (error.response) {
        console.error('Response status:', error.response.status);
        console.error('Response data:', JSON.stringify(error.response.data, null, 2));
      }
      throw error;
    }
  });

  // Test 1: Verify Odoo connection status
  test('Verify Odoo integration status', async () => {
    try {
      console.log(`Checking Odoo integration status at ${ODOO_STATUS_ENDPOINT}...`);
      const response = await apiClient.get(ODOO_STATUS_ENDPOINT);

      expect(response.status).toBe(200);
      expect(response.data).toHaveProperty('status');
      
      console.log('Odoo Integration Status:', response.data);
      
      // Verify Odoo is operational or has active integrations
      if (response.data.active_integrations && response.data.active_integrations > 0) {
        console.log(`✅ Found ${response.data.active_integrations} active Odoo integrations`);
        expect(response.data.status).toBe('operational');
      } else {
        console.warn('⚠️ No active Odoo integrations found');
      }
    } catch (error) {
      console.error('❌ Odoo status check failed:', error.message);
      if (error.response) {
        console.error('Response status:', error.response.status);
        console.error('Response data:', JSON.stringify(error.response.data, null, 2));
      }
      throw error;
    }
  });

  // Test 2: List available invoices from Odoo
  test('List available invoices from Odoo', async () => {
    try {
      console.log(`Fetching invoices from Odoo via ${INVOICE_ENDPOINT}/odoo...`);
      const response = await apiClient.get(`${INVOICE_ENDPOINT}/odoo`);

      expect(response.status).toBe(200);
      expect(response.data).toHaveProperty('invoices');
      expect(Array.isArray(response.data.invoices)).toBe(true);
      
      const invoices = response.data.invoices;
      console.log(`✅ Successfully fetched ${invoices.length} invoices from Odoo`);
      
      // Display the invoices for selection in testing
      if (invoices.length > 0) {
        console.log('\nAvailable Invoices for Testing:');
        console.log('--------------------------------');
        invoices.forEach((invoice, index) => {
          console.log(`${index + 1}. ID: ${invoice.id} | Number: ${invoice.invoice_number || 'N/A'} | Date: ${invoice.date || 'N/A'} | Amount: ${invoice.amount_total || 'N/A'}`);
        });
        console.log('\nUse these invoice IDs in your .env.test file for TEST_INVOICE_ID');
      } else {
        console.warn('⚠️ No invoices found in Odoo');
      }
    } catch (error) {
      console.error('❌ Invoice fetch failed:', error.message);
      if (error.response) {
        console.error('Response status:', error.response.status);
        console.error('Response data:', JSON.stringify(error.response.data, null, 2));
      }
      throw error;
    }
  });
});
