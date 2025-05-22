// @ts-check
const { test, expect } = require('@playwright/test');
const axios = require('axios');
require('dotenv').config();

/**
 * Real-time E2E tests for IRN Generation in TaxPoynt eInvoice
 * 
 * These tests validate:
 * 1. Single IRN generation
 * 2. IRN validation
 * 3. Batch IRN generation (if supported)
 */

// Test data
const TEST_USER = {
  email: process.env.TEST_USER_EMAIL || 'test@example.com',
  password: process.env.TEST_USER_PASSWORD || 'test-password'
};

// API endpoints
const API_BASE_URL = process.env.TEST_BACKEND_URL || 'http://localhost:8000/api/v1';
const LOGIN_ENDPOINT = `${API_BASE_URL}/auth/login`;
const IRN_GENERATE_ENDPOINT = `${API_BASE_URL}/irn/generate`;
const IRN_VALIDATE_ENDPOINT = `${API_BASE_URL}/irn/validate`;
const IRN_BATCH_ENDPOINT = `${API_BASE_URL}/irn/batch`;

// Test UBL document (simplified)
const TEST_UBL = `
<Invoice xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2" xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2" xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">
  <cbc:CustomizationID>urn:cen.eu:en16931:2017#compliant#urn:fdc:peppol.eu:2017:poacc:billing:3.0</cbc:CustomizationID>
  <cbc:ProfileID>urn:fdc:peppol.eu:2017:poacc:billing:01:1.0</cbc:ProfileID>
  <cbc:ID>INVOICE-TEST-001</cbc:ID>
  <cbc:IssueDate>2025-05-22</cbc:IssueDate>
  <cbc:DueDate>2025-06-22</cbc:DueDate>
  <cbc:InvoiceTypeCode>380</cbc:InvoiceTypeCode>
  <cbc:DocumentCurrencyCode>NGN</cbc:DocumentCurrencyCode>
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
test.describe('IRN Generation E2E Tests', () => {
  let authToken;
  let generatedIrn;

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

  // Test 1: Generate IRN for a single invoice
  test('should generate IRN for a single invoice', async () => {
    try {
      // @ts-ignore
      const response = await axios.post(IRN_GENERATE_ENDPOINT, {
        ubl_xml: TEST_UBL
      }, {
        headers: { Authorization: `Bearer ${authToken}` }
      });

      expect(response.status).toBe(200);
      expect(response.data).toHaveProperty('irn');
      
      // Store IRN for subsequent tests
      generatedIrn = response.data.irn;
      
      // Validate IRN format (assuming a specific format like UUID or similar)
      expect(generatedIrn).toBeTruthy();
      expect(typeof generatedIrn).toBe('string');
      
      console.log('Generated IRN:', generatedIrn);
    } catch (error) {
      console.error('IRN generation failed:', error.message);
      throw error;
    }
  });

  // Test 2: Validate the generated IRN
  test('should validate a previously generated IRN', async () => {
    // Skip if no IRN was generated
    test.skip(!generatedIrn, 'No IRN was generated in the previous test');
    
    try {
      // @ts-ignore
      const response = await axios.post(IRN_VALIDATE_ENDPOINT, {
        irn: generatedIrn
      }, {
        headers: { Authorization: `Bearer ${authToken}` }
      });

      expect(response.status).toBe(200);
      expect(response.data).toHaveProperty('valid');
      expect(response.data.valid).toBe(true);
      
      // Check if validation response contains invoice details
      expect(response.data).toHaveProperty('invoice_details');
      
      console.log('IRN validation successful:', response.data);
    } catch (error) {
      console.error('IRN validation failed:', error.message);
      throw error;
    }
  });

  // Test 3: Batch IRN generation (if supported)
  test('should generate IRNs in batch mode', async () => {
    // Create test batch data with multiple UBL documents
    const batchData = {
      invoices: [
        { id: 'BATCH-INV-001', ubl_xml: TEST_UBL },
        { id: 'BATCH-INV-002', ubl_xml: TEST_UBL.replace('INVOICE-TEST-001', 'INVOICE-TEST-002') }
      ]
    };
    
    try {
      // @ts-ignore
      const response = await axios.post(IRN_BATCH_ENDPOINT, batchData, {
        headers: { Authorization: `Bearer ${authToken}` }
      });

      expect(response.status).toBe(200);
      expect(response.data).toHaveProperty('results');
      expect(Array.isArray(response.data.results)).toBe(true);
      
      // Check batch processing results
      if (response.data.results.length > 0) {
        const firstResult = response.data.results[0];
        expect(firstResult).toHaveProperty('invoice_id');
        expect(firstResult).toHaveProperty('irn');
        expect(firstResult).toHaveProperty('status');
        
        console.log('Batch IRN generation results:', response.data.results);
      }
    } catch (error) {
      // If batch processing is not supported, this might fail with 404 or 501
      if (error.response && (error.response.status === 404 || error.response.status === 501)) {
        console.log('Batch IRN generation not supported - skipping test');
        test.skip(true, 'Batch IRN generation not supported');
      } else {
        console.error('Batch IRN generation failed:', error.message);
        throw error;
      }
    }
  });
});
