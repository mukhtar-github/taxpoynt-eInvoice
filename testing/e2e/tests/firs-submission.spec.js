// @ts-check
const { test, expect } = require('@playwright/test');
const axios = require('axios');
require('dotenv').config();

/**
 * Real-time E2E tests for FIRS Submission in TaxPoynt eInvoice
 * 
 * These tests validate:
 * 1. FIRS API connectivity and status
 * 2. UBL document submission to FIRS sandbox
 * 3. Submission status tracking
 */

// Test data
const TEST_USER = {
  email: process.env.TEST_USER_EMAIL || 'test@example.com',
  password: process.env.TEST_USER_PASSWORD || 'test-password'
};

// API endpoints
const API_BASE_URL = process.env.TEST_BACKEND_URL || 'http://localhost:8000/api/v1';
const LOGIN_ENDPOINT = `${API_BASE_URL}/auth/login`;
const FIRS_STATUS_ENDPOINT = `${API_BASE_URL}/integration/status/firs`;
const FIRS_SUBMIT_ENDPOINT = `${API_BASE_URL}/firs/submit`;
const FIRS_STATUS_CHECK_ENDPOINT = `${API_BASE_URL}/firs/status`;

// Test IRN for submission (can be generated in real-time or hardcoded for testing)
const TEST_IRN = process.env.TEST_IRN || 'IRN12345678901234567890';

// Test UBL document with IRN (simplified)
const TEST_UBL_WITH_IRN = `
<Invoice xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2" xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2" xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">
  <cbc:CustomizationID>urn:cen.eu:en16931:2017#compliant#urn:fdc:peppol.eu:2017:poacc:billing:3.0</cbc:CustomizationID>
  <cbc:ProfileID>urn:fdc:peppol.eu:2017:poacc:billing:01:1.0</cbc:ProfileID>
  <cbc:ID>INVOICE-TEST-001</cbc:ID>
  <cbc:IssueDate>2025-05-22</cbc:IssueDate>
  <cbc:DueDate>2025-06-22</cbc:DueDate>
  <cbc:InvoiceTypeCode>380</cbc:InvoiceTypeCode>
  <cbc:DocumentCurrencyCode>NGN</cbc:DocumentCurrencyCode>
  <ext:UBLExtensions xmlns:ext="urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2">
    <ext:UBLExtension>
      <ext:ExtensionContent>
        <nig:NigerianExtension xmlns:nig="urn:firs:names:specification:ubl:schema:xsd:NigerianExtension-1">
          <nig:IRN>${TEST_IRN}</nig:IRN>
        </nig:NigerianExtension>
      </ext:ExtensionContent>
    </ext:UBLExtension>
  </ext:UBLExtensions>
  <cac:AccountingSupplierParty>
    <cac:Party>
      <cac:PartyName>
        <cbc:Name>Test Supplier Ltd</cbc:Name>
      </cac:PartyName>
      <cac:PostalAddress>
        <cbc:StreetName>123 Supplier Street</cbc:StreetName>
        <cbc:CityName>Lagos</cbc:CityName>
        <cbc:CountrySubentity>Lagos State</cbc:CountrySubentity>
        <cac:Country>
          <cbc:IdentificationCode>NG</cbc:IdentificationCode>
        </cac:Country>
      </cac:PostalAddress>
      <cac:PartyTaxScheme>
        <cbc:CompanyID>NG123456789</cbc:CompanyID>
        <cac:TaxScheme>
          <cbc:ID>VAT</cbc:ID>
        </cac:TaxScheme>
      </cac:PartyTaxScheme>
    </cac:Party>
  </cac:AccountingSupplierParty>
  <cac:AccountingCustomerParty>
    <cac:Party>
      <cac:PartyName>
        <cbc:Name>Test Customer Ltd</cbc:Name>
      </cac:PartyName>
      <cac:PostalAddress>
        <cbc:StreetName>456 Customer Avenue</cbc:StreetName>
        <cbc:CityName>Abuja</cbc:CityName>
        <cac:Country>
          <cbc:IdentificationCode>NG</cbc:IdentificationCode>
        </cac:Country>
      </cac:PostalAddress>
      <cac:PartyTaxScheme>
        <cbc:CompanyID>NG987654321</cbc:CompanyID>
        <cac:TaxScheme>
          <cbc:ID>VAT</cbc:ID>
        </cac:TaxScheme>
      </cac:PartyTaxScheme>
    </cac:Party>
  </cac:AccountingCustomerParty>
  <cac:TaxTotal>
    <cbc:TaxAmount currencyID="NGN">750.00</cbc:TaxAmount>
  </cac:TaxTotal>
  <cac:LegalMonetaryTotal>
    <cbc:LineExtensionAmount currencyID="NGN">5000.00</cbc:LineExtensionAmount>
    <cbc:TaxExclusiveAmount currencyID="NGN">5000.00</cbc:TaxExclusiveAmount>
    <cbc:TaxInclusiveAmount currencyID="NGN">5750.00</cbc:TaxInclusiveAmount>
    <cbc:PayableAmount currencyID="NGN">5750.00</cbc:PayableAmount>
  </cac:LegalMonetaryTotal>
  <cac:InvoiceLine>
    <cbc:ID>1</cbc:ID>
    <cbc:InvoicedQuantity unitCode="EA">10</cbc:InvoicedQuantity>
    <cbc:LineExtensionAmount currencyID="NGN">5000.00</cbc:LineExtensionAmount>
    <cac:Item>
      <cbc:Name>Test Product</cbc:Name>
      <cac:ClassifiedTaxCategory>
        <cbc:ID>S</cbc:ID>
        <cbc:Percent>15</cbc:Percent>
        <cac:TaxScheme>
          <cbc:ID>VAT</cbc:ID>
        </cac:TaxScheme>
      </cac:ClassifiedTaxCategory>
    </cac:Item>
    <cac:Price>
      <cbc:PriceAmount currencyID="NGN">500.00</cbc:PriceAmount>
    </cac:Price>
  </cac:InvoiceLine>
</Invoice>
`;

// Test suite
test.describe('FIRS Submission E2E Tests', () => {
  let authToken;
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

  // Test 1: Check FIRS API connectivity and status
  test('should check FIRS API connectivity status', async () => {
    try {
      // @ts-ignore
      const response = await axios.get(FIRS_STATUS_ENDPOINT, {
        headers: { Authorization: `Bearer ${authToken}` }
      });

      expect(response.status).toBe(200);
      expect(response.data).toHaveProperty('status');
      
      // Log the actual status for visibility
      console.log('FIRS API Status:', response.data);
      
      // FIRS API should be operational or in sandbox mode
      expect(['operational', 'sandbox']).toContain(response.data.status);
    } catch (error) {
      console.error('FIRS status check failed:', error.message);
      throw error;
    }
  });

  // Test 2: Submit invoice to FIRS sandbox
  test('should submit invoice to FIRS sandbox', async () => {
    try {
      // @ts-ignore
      const response = await axios.post(FIRS_SUBMIT_ENDPOINT, {
        ubl_xml: TEST_UBL_WITH_IRN,
        irn: TEST_IRN,
        sandbox: true // Ensure we're using sandbox mode
      }, {
        headers: { Authorization: `Bearer ${authToken}` }
      });

      expect(response.status).toBe(200);
      expect(response.data).toHaveProperty('submission_id');
      
      // Store submission ID for subsequent tests
      submissionId = response.data.submission_id;
      
      console.log('FIRS Submission successful. Submission ID:', submissionId);
      
      // Check additional response properties
      expect(response.data).toHaveProperty('timestamp');
      expect(response.data).toHaveProperty('status');
    } catch (error) {
      console.error('FIRS submission failed:', error.message);
      throw error;
    }
  });

  // Test 3: Check submission status
  test('should check submission status', async () => {
    // Skip if no submission was made
    test.skip(!submissionId, 'No submission was made in the previous test');
    
    try {
      // @ts-ignore
      const response = await axios.get(`${FIRS_STATUS_CHECK_ENDPOINT}/${submissionId}`, {
        headers: { Authorization: `Bearer ${authToken}` }
      });

      expect(response.status).toBe(200);
      expect(response.data).toHaveProperty('status');
      
      // Status should be one of the expected values
      expect(['pending', 'processing', 'completed', 'failed']).toContain(response.data.status);
      
      console.log('Submission Status:', response.data);
      
      // Check additional response properties
      expect(response.data).toHaveProperty('submission_id');
      expect(response.data).toHaveProperty('timestamp');
      expect(response.data).toHaveProperty('irn');
    } catch (error) {
      console.error('Submission status check failed:', error.message);
      throw error;
    }
  });
});
