// @ts-check
const { test, expect } = require('@playwright/test');
const axios = require('axios');
require('dotenv').config();

/**
 * Real-time E2E tests for Odoo Integration in TaxPoynt eInvoice
 * 
 * These tests validate:
 * 1. Odoo connection status
 * 2. UBL transformation functionality
 * 3. Field mapping accuracy against BIS Billing 3.0 standards
 */

// Test data
const TEST_USER = {
  email: process.env.TEST_USER_EMAIL || 'test@example.com',
  password: process.env.TEST_USER_PASSWORD || 'test-password'
};

// API endpoints
const API_BASE_URL = process.env.TEST_BACKEND_URL || 'http://localhost:8000/api/v1';
const ODOO_STATUS_ENDPOINT = `${API_BASE_URL}/integration/status/odoo`;
const LOGIN_ENDPOINT = `${API_BASE_URL}/auth/login`;
const INVOICE_ENDPOINT = `${API_BASE_URL}/invoices`;
const UBL_TRANSFORM_ENDPOINT = `${API_BASE_URL}/transform/odoo`;

// Test suite
test.describe('Odoo Integration E2E Tests', () => {
  let authToken;

  // Setup - authenticate before tests
  test.beforeAll(async () => {
    try {
      const response = await axios.post(LOGIN_ENDPOINT, {
        email: TEST_USER.email,
        password: TEST_USER.password
      });

      authToken = response.data.token;
      console.log('Authentication successful');
    } catch (error) {
      console.error('Authentication failed:', error.message);
      throw error;
    }
  });

  // Test 1: Verify Odoo API status
  test('should check Odoo integration status', async () => {
    try {
      const response = await axios.get(ODOO_STATUS_ENDPOINT, {
        headers: { Authorization: `Bearer ${authToken}` }
      });

      expect(response.status).toBe(200);
      expect(response.data).toHaveProperty('status');
      
      // Log the actual status for visibility
      console.log('Odoo Integration Status:', response.data);
      
      // If we have active integrations, they should be operational
      if (response.data.active_integrations && response.data.active_integrations > 0) {
        expect(response.data.status).toBe('operational');
      }
    } catch (error) {
      console.error('Odoo status check failed:', error.message);
      throw error;
    }
  });

  // Test 2: Fetch invoice from Odoo
  test('should fetch an invoice from Odoo', async () => {
    try {
      // Get list of available invoices from Odoo
      const response = await axios.get(`${INVOICE_ENDPOINT}/odoo`, {
        headers: { Authorization: `Bearer ${authToken}` }
      });

      expect(response.status).toBe(200);
      expect(response.data).toHaveProperty('invoices');
      expect(Array.isArray(response.data.invoices)).toBe(true);
      
      // Log the available invoices count
      console.log(`Fetched ${response.data.invoices.length} invoices from Odoo`);
      
      // If we have invoices, the first one should have basic invoice properties
      if (response.data.invoices.length > 0) {
        const firstInvoice = response.data.invoices[0];
        expect(firstInvoice).toHaveProperty('id');
        expect(firstInvoice).toHaveProperty('invoice_number');
        console.log('Sample invoice:', firstInvoice.invoice_number);
      }
    } catch (error) {
      console.error('Invoice fetch failed:', error.message);
      throw error;
    }
  });

  // Test 3: Transform Odoo invoice to UBL
  test('should transform Odoo invoice to UBL format', async () => {
    try {
      // Use a specific invoice ID from environment or a default test ID
      const invoiceId = process.env.TEST_INVOICE_ID || 'INV-TEST-001';
      
      // Transform invoice to UBL
      const response = await axios.post(UBL_TRANSFORM_ENDPOINT, {
        invoice_id: invoiceId
      }, {
        headers: { Authorization: `Bearer ${authToken}` }
      });

      expect(response.status).toBe(200);
      expect(response.data).toHaveProperty('ubl_xml');
      
      // Validate UBL structure - check for essential BIS Billing 3.0 elements
      const ublXml = response.data.ubl_xml;
      
      // These are critical BIS Billing 3.0 UBL elements that must exist
      const requiredElements = [
        '<cbc:CustomizationID>',
        '<cbc:ProfileID>',
        '<cac:AccountingSupplierParty>',
        '<cac:AccountingCustomerParty>',
        '<cac:TaxTotal>',
        '<cac:LegalMonetaryTotal>',
        '<cac:InvoiceLine>'
      ];
      
      // Check each required element exists in the UBL XML
      for (const element of requiredElements) {
        expect(ublXml.includes(element)).toBe(true);
      }
      
      console.log('UBL transformation successful and validated against BIS Billing 3.0 requirements');
    } catch (error) {
      console.error('UBL transformation failed:', error.message);
      throw error;
    }
  });
});
