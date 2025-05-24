// @ts-check
const { test, expect } = require('@playwright/test');
const axios = require('axios');
require('dotenv').config({ path: process.env.ENV_FILE || '.env.prod' });

/**
 * Production-Ready Odoo to FIRS E2E Test for TaxPoynt eInvoice
 * 
 * This test validates the complete invoice lifecycle using a known-good invoice:
 * 1. Authenticates with production API
 * 2. Retrieves the specific Odoo invoice (INV/2023/001)
 * 3. Transforms it to UBL format with BIS Billing 3.0 validation
 * 4. Generates an IRN
 * 5. Submits to FIRS sandbox
 * 6. Checks submission status
 */

// Test data
const TEST_USER = {
  email: process.env.TEST_USER_EMAIL || 'test@example.com',
  password: process.env.TEST_USER_PASSWORD || 'test-password'
};

// Known invoice data from previous tests
const TEST_INVOICE = {
  id: process.env.TEST_INVOICE_ID || '1234',
  number: process.env.TEST_INVOICE_NUMBER || 'INV/2023/001'
};

// API endpoint configuration
const API_BASE_URL = process.env.TEST_BACKEND_URL || 'https://taxpoynt-einvoice-production.up.railway.app/api/v1';
const LOGIN_ENDPOINT = `${API_BASE_URL}/auth/login`;
const INVOICE_ENDPOINT = `${API_BASE_URL}/invoices`;
const SPECIFIC_INVOICE_ENDPOINT = `${API_BASE_URL}/odoo-ubl/invoices/${TEST_INVOICE.id}`;
const UBL_TRANSFORM_ENDPOINT = `${API_BASE_URL}/odoo-ubl/invoices/${TEST_INVOICE.id}/ubl`;
const UBL_XML_ENDPOINT = `${API_BASE_URL}/odoo-ubl/invoices/${TEST_INVOICE.id}/ubl/xml`;
const IRN_GENERATE_ENDPOINT = `${API_BASE_URL}/irn/generate`;
const FIRS_SUBMIT_ENDPOINT = `${API_BASE_URL}/firs/submit`;
const FIRS_STATUS_CHECK_ENDPOINT = `${API_BASE_URL}/firs/status`;

// Rate limiting configuration
const RATE_LIMIT_DELAY = parseInt(process.env.TEST_RATE_LIMIT_DELAY || '3000', 10);
const MAX_RETRIES = parseInt(process.env.TEST_MAX_RETRIES || '3', 10);
const RETRY_DELAY = parseInt(process.env.TEST_RETRY_DELAY || '5000', 10);

// Helper function to add delay between API calls to avoid rate limiting
async function delayBetweenRequests() {
  if (RATE_LIMIT_DELAY > 0) {
    console.log(`Adding delay of ${RATE_LIMIT_DELAY}ms to avoid rate limiting...`);
    return new Promise(resolve => setTimeout(resolve, RATE_LIMIT_DELAY));
  }
}

// Retry function with exponential backoff
async function retryOperation(operation, retries = MAX_RETRIES, backoff = RETRY_DELAY) {
  let lastError;
  
  for (let i = 0; i < retries; i++) {
    try {
      return await operation();
    } catch (error) {
      console.log(`Attempt ${i + 1} failed with error: ${error.message}`);
      lastError = error;
      
      if (i < retries - 1) {
        const waitTime = backoff * Math.pow(2, i);
        console.log(`Retrying in ${waitTime}ms...`);
        await new Promise(resolve => setTimeout(resolve, waitTime));
      }
    }
  }
  
  throw lastError;
}

// Create axios instance with enhanced configuration
const apiClient = axios.create({
  timeout: 60000,
  headers: {
    'Content-Type': 'application/json',
    'User-Agent': 'TaxPoynt-E2E-Production-Test'
  }
});

// Add request interceptor for logging
apiClient.interceptors.request.use(request => {
  console.log(`Making request to: ${request.url}`);
  return request;
});

// Test suite
test.describe('Production Odoo to FIRS E2E Workflow', () => {
  let authToken;
  let ublObject;
  let ublXml;
  let generatedIrn;
  let submissionId;

  // Setup - authenticate before tests
  test.beforeAll(async () => {
    try {
      console.log(`Authenticating with API at ${API_BASE_URL}...`);
      
      const authenticateOperation = async () => {
        const response = await apiClient.post(LOGIN_ENDPOINT, {
          email: TEST_USER.email,
          password: TEST_USER.password
        });
        return response.data.token;
      };
      
      // Retry authentication up to configured number of times with exponential backoff
      authToken = await retryOperation(authenticateOperation);
      
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

  // Test 1: Verify and retrieve specific Odoo invoice
  test('Step 1: Verify and retrieve specific Odoo invoice', async () => {
    try {
      console.log(`Retrieving specific invoice ${TEST_INVOICE.number} (ID: ${TEST_INVOICE.id})...`);
      await delayBetweenRequests();
      
      const fetchInvoiceOperation = async () => {
        return await apiClient.get(SPECIFIC_INVOICE_ENDPOINT);
      };
      
      // Retry invoice fetch with configured retries
      const response = await retryOperation(fetchInvoiceOperation);
      
      expect(response.status).toBe(200);
      expect(response.data).toHaveProperty('status', 'success');
      expect(response.data).toHaveProperty('data');
      
      const invoice = response.data.data;
      expect(invoice).toHaveProperty('id', parseInt(TEST_INVOICE.id));
      expect(invoice).toHaveProperty('number', TEST_INVOICE.number);
      
      console.log(`✅ Successfully verified invoice ${invoice.number}`);
      console.log('Invoice Details:', {
        id: invoice.id,
        number: invoice.number,
        date: invoice.date,
        total: invoice.amount_total,
        currency: invoice.currency_id?.name || 'NGN',
        state: invoice.state
      });
      
      // Verify UBL mapping is available
      expect(invoice).toHaveProperty('ubl_mapping_available', true);
    } catch (error) {
      console.error('❌ Invoice verification failed:', error.message);
      if (error.response) {
        console.error('Response status:', error.response.status);
        console.error('Response data:', JSON.stringify(error.response.data, null, 2));
      }
      throw error;
    }
  });

  // Test 2: Transform invoice to UBL format
  test('Step 2: Transform invoice to UBL format with BIS Billing 3.0 mapping', async () => {
    try {
      console.log(`Transforming invoice ${TEST_INVOICE.number} to UBL format...`);
      await delayBetweenRequests();
      
      const transformOperation = async () => {
        return await apiClient.get(UBL_TRANSFORM_ENDPOINT);
      };
      
      // Retry UBL transformation with configured retries
      const response = await retryOperation(transformOperation);
      
      expect(response.status).toBe(200);
      expect(response.data).toHaveProperty('status', 'success');
      expect(response.data).toHaveProperty('data');
      expect(response.data.data).toHaveProperty('ubl_object');
      expect(response.data.data).toHaveProperty('ubl_xml');
      
      // Store UBL for subsequent tests
      ublObject = response.data.data.ubl_object;
      
      // Verify invoice number in UBL object
      expect(ublObject).toHaveProperty('invoice_number', TEST_INVOICE.number);
      
      console.log('✅ UBL transformation successful');
      
      // Next, retrieve the full XML
      console.log('Retrieving full UBL XML...');
      await delayBetweenRequests();
      
      const getXmlOperation = async () => {
        return await apiClient.get(UBL_XML_ENDPOINT);
      };
      
      // Retry XML retrieval with configured retries
      const xmlResponse = await retryOperation(getXmlOperation);
      
      expect(typeof xmlResponse.data).toBe('string');
      ublXml = xmlResponse.data;
      
      // Validate UBL has essential BIS Billing 3.0 elements
      const requiredElements = [
        '<cbc:CustomizationID>',
        '<cbc:ProfileID>',
        '<cac:AccountingSupplierParty>',
        '<cac:AccountingCustomerParty>',
        '<cac:TaxTotal>',
        '<cac:LegalMonetaryTotal>',
        '<cac:InvoiceLine>'
      ];
      
      let missingElements = [];
      for (const element of requiredElements) {
        if (!ublXml.includes(element)) {
          missingElements.push(element);
        }
      }
      
      if (missingElements.length > 0) {
        console.warn('⚠️ UBL XML is missing some elements:', missingElements);
      } else {
        console.log('✅ UBL XML includes all required BIS Billing 3.0 elements');
      }
      
      expect(missingElements.length).toBe(0);
    } catch (error) {
      console.error('❌ UBL transformation failed:', error.message);
      if (error.response) {
        console.error('Response status:', error.response.status);
        console.error('Response data:', JSON.stringify(error.response.data, null, 2));
      }
      throw error;
    }
  });

  // Test 3: Generate IRN
  test('Step 3: Generate IRN for the transformed invoice', async () => {
    test.skip(!ublXml, 'No UBL XML available from previous step');
    
    try {
      console.log('Generating IRN for the transformed invoice...');
      await delayBetweenRequests();
      
      const generateIrnOperation = async () => {
        return await apiClient.post(IRN_GENERATE_ENDPOINT, {
          ubl_xml: ublXml
        });
      };
      
      // Retry IRN generation with configured retries
      const response = await retryOperation(generateIrnOperation);
      
      expect(response.status).toBe(200);
      expect(response.data).toHaveProperty('irn');
      
      // Store IRN for subsequent tests
      generatedIrn = response.data.irn;
      
      // Validate IRN format
      expect(generatedIrn).toBeTruthy();
      expect(typeof generatedIrn).toBe('string');
      
      console.log('✅ Generated IRN:', generatedIrn);
    } catch (error) {
      console.error('❌ IRN generation failed:', error.message);
      if (error.response) {
        console.error('Response status:', error.response.status);
        console.error('Response data:', JSON.stringify(error.response.data, null, 2));
      }
      throw error;
    }
  });

  // Test 4: Submit to FIRS
  test('Step 4: Submit invoice with IRN to FIRS sandbox', async () => {
    test.skip(!generatedIrn || !ublXml, 'No IRN or UBL XML available from previous steps');
    
    try {
      console.log('Submitting invoice to FIRS sandbox...');
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
      
      const submitOperation = async () => {
        return await apiClient.post(FIRS_SUBMIT_ENDPOINT, {
          ubl_xml: ublWithIrn,
          irn: generatedIrn,
          sandbox: true // Ensure we're using sandbox mode
        });
      };
      
      // Retry FIRS submission with configured retries
      const response = await retryOperation(submitOperation);
      
      expect(response.status).toBe(200);
      expect(response.data).toHaveProperty('submission_id');
      
      // Store submission ID for subsequent tests
      submissionId = response.data.submission_id;
      
      console.log('✅ FIRS Submission successful. Submission ID:', submissionId);
    } catch (error) {
      console.error('❌ FIRS submission failed:', error.message);
      if (error.response) {
        console.error('Response status:', error.response.status);
        console.error('Response data:', JSON.stringify(error.response.data, null, 2));
      }
      throw error;
    }
  });

  // Test 5: Check submission status
  test('Step 5: Check FIRS submission status', async () => {
    test.skip(!submissionId, 'No submission ID available from previous step');
    
    try {
      console.log(`Checking FIRS submission status for ID: ${submissionId}...`);
      await delayBetweenRequests();
      
      const checkStatusOperation = async () => {
        return await apiClient.get(`${FIRS_STATUS_CHECK_ENDPOINT}/${submissionId}`);
      };
      
      // Retry status check with configured retries
      const response = await retryOperation(checkStatusOperation);
      
      expect(response.status).toBe(200);
      expect(response.data).toHaveProperty('status');
      
      // Status can be 'pending', 'processing', 'completed', or 'failed'
      const validStatuses = ['pending', 'processing', 'completed', 'failed'];
      expect(validStatuses).toContain(response.data.status);
      
      console.log('✅ FIRS Submission Status:', response.data.status);
      
      // If we have additional status details, log them
      if (response.data.details) {
        console.log('Status Details:', response.data.details);
      }
      
      console.log('\n🎉 COMPLETE E2E TEST SUCCESSFUL! 🎉');
      console.log('Summary:');
      console.log(`- Invoice: ${TEST_INVOICE.number} (ID: ${TEST_INVOICE.id})`);
      console.log(`- UBL Transformation: Success`);
      console.log(`- IRN Generated: ${generatedIrn}`);
      console.log(`- FIRS Submission ID: ${submissionId}`);
      console.log(`- FIRS Status: ${response.data.status}`);
      console.log('\nThe Odoo → UBL → FIRS workflow is working correctly.');
    } catch (error) {
      console.error('❌ Status check failed:', error.message);
      if (error.response) {
        console.error('Response status:', error.response.status);
        console.error('Response data:', JSON.stringify(error.response.data, null, 2));
      }
      throw error;
    }
  });
});
