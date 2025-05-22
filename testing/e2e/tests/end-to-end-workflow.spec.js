// @ts-check
const { test, expect } = require('@playwright/test');
const axios = require('axios');
require('dotenv').config();

/**
 * Complete End-to-End Workflow Tests for TaxPoynt eInvoice
 * 
 * This test suite validates the entire invoice lifecycle:
 * 1. Fetching an invoice from Odoo
 * 2. Transforming it to UBL format
 * 3. Generating an IRN
 * 4. Submitting to FIRS
 * 5. Checking submission status
 */

// Test data
const TEST_USER = {
  email: process.env.TEST_USER_EMAIL || 'test@example.com',
  password: process.env.TEST_USER_PASSWORD || 'test-password'
};

// API endpoints
const API_BASE_URL = process.env.TEST_BACKEND_URL || 'http://localhost:8000/api/v1';
const LOGIN_ENDPOINT = `${API_BASE_URL}/auth/login`;
const INVOICE_ENDPOINT = `${API_BASE_URL}/invoices`;
const UBL_TRANSFORM_ENDPOINT = `${API_BASE_URL}/transform/odoo`;
const IRN_GENERATE_ENDPOINT = `${API_BASE_URL}/irn/generate`;
const FIRS_SUBMIT_ENDPOINT = `${API_BASE_URL}/firs/submit`;
const FIRS_STATUS_CHECK_ENDPOINT = `${API_BASE_URL}/firs/status`;

// Test suite
test.describe('Complete E2E Workflow Tests', () => {
  let authToken;
  let invoiceId;
  let ublXml;
  let generatedIrn;
  let submissionId;

  // Setup - authenticate before tests
  test.beforeAll(async () => {
    try {
      // @ts-ignore
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

  // Test 1: Fetch an invoice from Odoo
  test('Step 1: Fetch invoice from Odoo', async () => {
    try {
      // Try to use a specific invoice ID from environment or fetch the first available
      if (process.env.TEST_INVOICE_ID) {
        invoiceId = process.env.TEST_INVOICE_ID;
        console.log(`Using predefined invoice ID: ${invoiceId}`);
      } else {
        // Get list of available invoices from Odoo
        // @ts-ignore
        const response = await axios.get(`${INVOICE_ENDPOINT}/odoo`, {
          headers: { Authorization: `Bearer ${authToken}` }
        });

        expect(response.status).toBe(200);
        expect(response.data).toHaveProperty('invoices');
        expect(Array.isArray(response.data.invoices)).toBe(true);
        expect(response.data.invoices.length).toBeGreaterThan(0);
        
        // Use the first invoice
        invoiceId = response.data.invoices[0].id;
        console.log(`Fetched invoice ID: ${invoiceId}`);
      }
      
      // Verify we have a valid invoice ID to work with
      expect(invoiceId).toBeTruthy();
    } catch (error) {
      console.error('Invoice fetch failed:', error.message);
      throw error;
    }
  });

  // Test 2: Transform invoice to UBL
  test('Step 2: Transform invoice to UBL', async () => {
    // Skip if no invoice was found
    test.skip(!invoiceId, 'No invoice ID available from previous step');
    
    try {
      // @ts-ignore
      const response = await axios.post(UBL_TRANSFORM_ENDPOINT, {
        invoice_id: invoiceId
      }, {
        headers: { Authorization: `Bearer ${authToken}` }
      });

      expect(response.status).toBe(200);
      expect(response.data).toHaveProperty('ubl_xml');
      
      // Store UBL for subsequent tests
      ublXml = response.data.ubl_xml;
      
      // Validate UBL has essential elements
      const requiredElements = [
        '<cbc:CustomizationID>',
        '<cbc:ProfileID>',
        '<cac:AccountingSupplierParty>',
        '<cac:AccountingCustomerParty>',
        '<cac:TaxTotal>',
        '<cac:LegalMonetaryTotal>',
        '<cac:InvoiceLine>'
      ];
      
      for (const element of requiredElements) {
        expect(ublXml.includes(element)).toBe(true);
      }
      
      console.log('UBL transformation successful');
    } catch (error) {
      console.error('UBL transformation failed:', error.message);
      throw error;
    }
  });

  // Test 3: Generate IRN
  test('Step 3: Generate IRN for the transformed invoice', async () => {
    // Skip if no UBL was generated
    test.skip(!ublXml, 'No UBL available from previous step');
    
    try {
      // @ts-ignore
      const response = await axios.post(IRN_GENERATE_ENDPOINT, {
        ubl_xml: ublXml
      }, {
        headers: { Authorization: `Bearer ${authToken}` }
      });

      expect(response.status).toBe(200);
      expect(response.data).toHaveProperty('irn');
      
      // Store IRN for subsequent tests
      generatedIrn = response.data.irn;
      
      // Validate IRN format
      expect(generatedIrn).toBeTruthy();
      expect(typeof generatedIrn).toBe('string');
      
      console.log('Generated IRN:', generatedIrn);
    } catch (error) {
      console.error('IRN generation failed:', error.message);
      throw error;
    }
  });

  // Test 4: Submit to FIRS
  test('Step 4: Submit invoice with IRN to FIRS', async () => {
    // Skip if no IRN was generated
    test.skip(!generatedIrn || !ublXml, 'No IRN or UBL available from previous steps');
    
    try {
      // Add IRN to UBL XML - in a real implementation, the backend might handle this
      // Here we're simulating by using a simple string replacement for test purposes
      const ublWithIrn = ublXml.replace(
        '<cbc:ProfileID>',
        `<ext:UBLExtensions xmlns:ext="urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2">
          <ext:UBLExtension>
            <ext:ExtensionContent>
              <nig:NigerianExtension xmlns:nig="urn:firs:names:specification:ubl:schema:xsd:NigerianExtension-1">
                <nig:IRN>${generatedIrn}</nig:IRN>
              </nig:NigerianExtension>
            </ext:ExtensionContent>
          </ext:UBLExtension>
        </ext:UBLExtensions>
        <cbc:ProfileID>`
      );
      
      // @ts-ignore
      const response = await axios.post(FIRS_SUBMIT_ENDPOINT, {
        ubl_xml: ublWithIrn,
        irn: generatedIrn,
        sandbox: true // Ensure we're using sandbox mode
      }, {
        headers: { Authorization: `Bearer ${authToken}` }
      });

      expect(response.status).toBe(200);
      expect(response.data).toHaveProperty('submission_id');
      
      // Store submission ID for subsequent tests
      submissionId = response.data.submission_id;
      
      console.log('FIRS Submission successful. Submission ID:', submissionId);
    } catch (error) {
      console.error('FIRS submission failed:', error.message);
      throw error;
    }
  });

  // Test 5: Check submission status
  test('Step 5: Check FIRS submission status', async () => {
    // Skip if no submission was made
    test.skip(!submissionId, 'No submission ID available from previous step');
    
    try {
      // @ts-ignore
      const response = await axios.get(`${FIRS_STATUS_CHECK_ENDPOINT}/${submissionId}`, {
        headers: { Authorization: `Bearer ${authToken}` }
      });

      expect(response.status).toBe(200);
      expect(response.data).toHaveProperty('status');
      expect(response.data).toHaveProperty('submission_id');
      expect(response.data.submission_id).toBe(submissionId);
      
      // Status should be one of the expected values
      expect(['pending', 'processing', 'completed', 'failed']).toContain(response.data.status);
      
      console.log('Full end-to-end workflow completed successfully');
      console.log('Submission Status:', response.data.status);
    } catch (error) {
      console.error('Submission status check failed:', error.message);
      throw error;
    }
  });
});
