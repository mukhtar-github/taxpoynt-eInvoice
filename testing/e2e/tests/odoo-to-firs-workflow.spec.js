// @ts-check
const { test, expect } = require('@playwright/test');
const axios = require('axios');
require('dotenv').config({ path: process.env.ENV_FILE || '.env.test' });

/**
 * Complete Odoo to FIRS Workflow E2E Tests for TaxPoynt eInvoice
 * 
 * This test suite validates the entire invoice lifecycle:
 * 1. Fetching an invoice from Odoo
 * 2. Transforming it to UBL format with BIS Billing 3.0 mapping
 * 3. Generating an IRN
 * 4. Submitting to FIRS sandbox
 * 5. Checking submission status
 */

// Test data
const TEST_USER = {
  email: process.env.TEST_USER_EMAIL || 'test@example.com',
  password: process.env.TEST_USER_PASSWORD || 'test-password'
};

// API endpoint configuration - supports both local and production
const API_BASE_URL = process.env.TEST_BACKEND_URL || 'http://localhost:8000/api/v1';
const LOGIN_ENDPOINT = `${API_BASE_URL}/auth/login`;
const INVOICE_ENDPOINT = `${API_BASE_URL}/invoices`;
const UBL_TRANSFORM_ENDPOINT = `${API_BASE_URL}/transform/odoo`;
const IRN_GENERATE_ENDPOINT = `${API_BASE_URL}/irn/generate`;
const FIRS_SUBMIT_ENDPOINT = `${API_BASE_URL}/firs/submit`;
const FIRS_STATUS_CHECK_ENDPOINT = `${API_BASE_URL}/firs/status`;

// Rate limit handling
const RATE_LIMIT_DELAY = parseInt(process.env.TEST_RATE_LIMIT_DELAY || '1000', 10);

// Helper function to add delay between API calls to avoid rate limiting
async function delayBetweenRequests() {
  if (RATE_LIMIT_DELAY > 0) {
    console.log(`Adding delay of ${RATE_LIMIT_DELAY}ms to avoid rate limiting...`);
    return new Promise(resolve => setTimeout(resolve, RATE_LIMIT_DELAY));
  }
}

// Create axios instance with retry and timeout configuration
const apiClient = axios.create({
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
    'User-Agent': 'TaxPoynt-E2E-Test'
  }
});

// Add request interceptor for logging
apiClient.interceptors.request.use(request => {
  console.log(`Making request to: ${request.url}`);
  return request;
});

// Add response interceptor for rate limit handling
apiClient.interceptors.response.use(
  response => {
    // Check if we're approaching rate limits based on headers
    const remaining = parseInt(response.headers['x-ratelimit-remaining-ip'] || '1000', 10);
    if (remaining < 10) {
      console.warn(`Rate limit approaching: ${remaining} requests remaining`);
    }
    return response;
  },
  async error => {
    if (error.response && error.response.status === 429) {
      console.warn('Rate limit exceeded, retrying after delay...');
      await delayBetweenRequests();
      return apiClient(error.config);
    }
    return Promise.reject(error);
  }
);

// Test suite
test.describe('Odoo to FIRS Complete Workflow', () => {
  let authToken;
  let invoiceId;
  let ublXml;
  let generatedIrn;
  let submissionId;

  // Setup - authenticate before tests
  test.beforeAll(async () => {
    try {
      console.log(`Authenticating with API at ${API_BASE_URL}...`);
      const response = await apiClient.post(LOGIN_ENDPOINT, {
        email: TEST_USER.email,
        password: TEST_USER.password
      });

      authToken = response.data.token;
      console.log('Authentication successful');
      
      // Set auth token for all future requests
      apiClient.defaults.headers.common['Authorization'] = `Bearer ${authToken}`;
    } catch (error) {
      console.error('Authentication failed:', error.message);
      if (error.response) {
        console.error('Response:', error.response.data);
      }
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
        // Add delay before API call
        await delayBetweenRequests();
        
        // Get list of available invoices from Odoo
        const response = await apiClient.get(`${INVOICE_ENDPOINT}/odoo`);

        expect(response.status).toBe(200);
        expect(response.data).toHaveProperty('invoices');
        expect(Array.isArray(response.data.invoices)).toBe(true);
        
        if (response.data.invoices.length === 0) {
          test.skip(true, 'No invoices available from Odoo');
          return;
        }
        
        // Use the first invoice
        invoiceId = response.data.invoices[0].id;
        console.log(`Fetched invoice ID: ${invoiceId}`);
      }
      
      // Verify we have a valid invoice ID to work with
      expect(invoiceId).toBeTruthy();
    } catch (error) {
      console.error('Invoice fetch failed:', error.message);
      if (error.response) {
        console.error('Response:', error.response.data);
      }
      throw error;
    }
  });

  // Test 2: Transform invoice to UBL
  test('Step 2: Transform invoice to UBL with BIS Billing 3.0 mapping', async () => {
    // Skip if no invoice was found
    test.skip(!invoiceId, 'No invoice ID available from previous step');
    
    try {
      // Add delay before API call
      await delayBetweenRequests();
      
      const response = await apiClient.post(UBL_TRANSFORM_ENDPOINT, {
        invoice_id: invoiceId
      });

      expect(response.status).toBe(200);
      expect(response.data).toHaveProperty('ubl_xml');
      
      // Store UBL for subsequent tests
      ublXml = response.data.ubl_xml;
      
      // Validate UBL has essential BIS Billing 3.0 elements
      const requiredElements = [
        '<cbc:CustomizationID>urn:cen.eu:en16931:2017',
        '<cbc:ProfileID>urn:fdc:peppol.eu:2017:poacc:billing:01:1.0',
        '<cac:AccountingSupplierParty>',
        '<cac:AccountingCustomerParty>',
        '<cac:TaxTotal>',
        '<cac:LegalMonetaryTotal>',
        '<cac:InvoiceLine>'
      ];
      
      for (const element of requiredElements) {
        expect(ublXml.includes(element)).toBe(true);
      }
      
      console.log('UBL transformation successful with BIS Billing 3.0 mapping');
    } catch (error) {
      console.error('UBL transformation failed:', error.message);
      if (error.response) {
        console.error('Response:', error.response.data);
      }
      throw error;
    }
  });

  // Test 3: Generate IRN
  test('Step 3: Generate IRN for the transformed invoice', async () => {
    // Skip if no UBL was generated
    test.skip(!ublXml, 'No UBL available from previous step');
    
    try {
      // Add delay before API call
      await delayBetweenRequests();
      
      const response = await apiClient.post(IRN_GENERATE_ENDPOINT, {
        ubl_xml: ublXml
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
      if (error.response) {
        console.error('Response:', error.response.data);
      }
      throw error;
    }
  });

  // Test 4: Submit to FIRS
  test('Step 4: Submit invoice with IRN to FIRS sandbox', async () => {
    // Skip if no IRN was generated
    test.skip(!generatedIrn || !ublXml, 'No IRN or UBL available from previous steps');
    
    try {
      // Add delay before API call
      await delayBetweenRequests();
      
      // Add IRN to UBL XML
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
      
      const response = await apiClient.post(FIRS_SUBMIT_ENDPOINT, {
        ubl_xml: ublWithIrn,
        irn: generatedIrn,
        sandbox: true // Ensure we're using sandbox mode
      });

      expect(response.status).toBe(200);
      expect(response.data).toHaveProperty('submission_id');
      
      // Store submission ID for subsequent tests
      submissionId = response.data.submission_id;
      
      console.log('FIRS Submission successful. Submission ID:', submissionId);
    } catch (error) {
      console.error('FIRS submission failed:', error.message);
      if (error.response) {
        console.error('Response:', error.response.data);
      }
      throw error;
    }
  });

  // Test 5: Check submission status
  test('Step 5: Check FIRS submission status', async () => {
    // Skip if no submission was made
    test.skip(!submissionId, 'No submission ID available from previous step');
    
    try {
      // Add delay before API call
      await delayBetweenRequests();
      
      const response = await apiClient.get(`${FIRS_STATUS_CHECK_ENDPOINT}/${submissionId}`);

      expect(response.status).toBe(200);
      expect(response.data).toHaveProperty('status');
      
      // Status can be 'pending', 'processing', 'completed', or 'failed'
      const validStatuses = ['pending', 'processing', 'completed', 'failed'];
      expect(validStatuses).toContain(response.data.status);
      
      console.log('FIRS Submission Status:', response.data.status);
      
      // If we have additional status details, log them
      if (response.data.details) {
        console.log('Status Details:', response.data.details);
      }
    } catch (error) {
      console.error('Status check failed:', error.message);
      if (error.response) {
        console.error('Response:', error.response.data);
      }
      throw error;
    }
  });
});
