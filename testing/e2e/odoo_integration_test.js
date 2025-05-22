/**
 * Odoo Integration End-to-End Test
 * 
 * This script tests the Odoo integration in the deployed environment,
 * focusing on UBL transformation and field mapping.
 */

const axios = require('axios');
const assert = require('assert');
const config = require('./config');
const fs = require('fs');
const path = require('path');

// Create results directory if it doesn't exist
const resultsDir = path.join(__dirname, 'results');
if (!fs.existsSync(resultsDir)) {
  fs.mkdirSync(resultsDir, { recursive: true });
}

// Utility function to log test results
function logResult(testName, success, details = {}) {
  const timestamp = new Date().toISOString();
  const result = {
    test: testName,
    timestamp,
    success,
    ...details
  };
  
  console.log(`[${timestamp}] ${testName}: ${success ? 'PASSED' : 'FAILED'}`);
  if (!success) {
    console.error(details.error || 'Test failed without specific error');
  }
  
  // Save result to file
  fs.writeFileSync(
    path.join(resultsDir, `${testName.replace(/\s+/g, '_')}_${timestamp}.json`),
    JSON.stringify(result, null, 2)
  );
  
  return success;
}

// Authenticate and get token
async function authenticate() {
  try {
    const response = await axios.post(`${config.urls.backend}/auth/login`, {
      email: config.testUser.email,
      password: config.testUser.password
    });
    
    return response.data.access_token;
  } catch (error) {
    throw new Error(`Authentication failed: ${error.message}`);
  }
}

// Test Odoo connection status
async function testOdooConnectionStatus(token) {
  try {
    const response = await axios.get(`${config.urls.backend}/integration-status/odoo`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    
    assert.strictEqual(response.status, 200, 'Status code should be 200');
    assert.ok(response.data.integrations && response.data.integrations.length > 0, 
      'Should return at least one Odoo integration');
    
    // Find any operational integrations
    const operational = response.data.integrations.some(i => i.status === 'operational');
    assert.ok(operational, 'At least one Odoo integration should be operational');
    
    return logResult('Odoo Connection Status Test', true, { 
      integrations: response.data.integrations.length,
      operational
    });
  } catch (error) {
    return logResult('Odoo Connection Status Test', false, { 
      error: error.message,
      stack: error.stack
    });
  }
}

// Test Odoo invoice retrieval
async function testOdooInvoiceRetrieval(token) {
  try {
    const response = await axios.get(
      `${config.urls.backend}/odoo-ubl/invoice/${config.odooTest.testInvoiceId}`, 
      {
        headers: { Authorization: `Bearer ${token}` }
      }
    );
    
    assert.strictEqual(response.status, 200, 'Status code should be 200');
    assert.ok(response.data.invoice, 'Should return invoice data');
    assert.ok(response.data.invoice.id, 'Invoice should have an ID');
    
    // Save invoice data for later tests
    fs.writeFileSync(
      path.join(resultsDir, 'odoo_invoice_sample.json'),
      JSON.stringify(response.data.invoice, null, 2)
    );
    
    return logResult('Odoo Invoice Retrieval Test', true, { 
      invoiceId: response.data.invoice.id,
      invoiceNumber: response.data.invoice.number || 'N/A'
    });
  } catch (error) {
    return logResult('Odoo Invoice Retrieval Test', false, { 
      error: error.message,
      stack: error.stack
    });
  }
}

// Test UBL transformation
async function testUBLTransformation(token) {
  try {
    const response = await axios.post(
      `${config.urls.backend}/odoo-ubl/transform`, 
      {
        invoice_id: config.odooTest.testInvoiceId,
        validate: true
      },
      {
        headers: { Authorization: `Bearer ${token}` }
      }
    );
    
    assert.strictEqual(response.status, 200, 'Status code should be 200');
    assert.ok(response.data.ubl, 'Should return UBL data');
    
    // Basic validation of UBL structure
    const ubl = response.data.ubl;
    assert.ok(ubl.includes('<Invoice'), 'UBL should contain Invoice tag');
    assert.ok(ubl.includes('<cbc:ID'), 'UBL should contain ID tag');
    assert.ok(ubl.includes('<cac:AccountingSupplierParty'), 'UBL should contain supplier information');
    assert.ok(ubl.includes('<cac:AccountingCustomerParty'), 'UBL should contain customer information');
    
    // Save UBL for later inspection
    fs.writeFileSync(
      path.join(resultsDir, 'odoo_ubl_sample.xml'),
      ubl
    );
    
    return logResult('UBL Transformation Test', true, {
      ublSize: ubl.length,
      validation: response.data.validation || {}
    });
  } catch (error) {
    return logResult('UBL Transformation Test', false, { 
      error: error.message,
      stack: error.stack
    });
  }
}

// Test field mapping validation
async function testFieldMappingValidation(token) {
  try {
    const response = await axios.post(
      `${config.urls.backend}/odoo-ubl/validate-mapping`, 
      {
        invoice_id: config.odooTest.testInvoiceId
      },
      {
        headers: { Authorization: `Bearer ${token}` }
      }
    );
    
    assert.strictEqual(response.status, 200, 'Status code should be 200');
    assert.ok(response.data.mapping_validation, 'Should return mapping validation results');
    
    // Check for required fields
    const validation = response.data.mapping_validation;
    const requiredFields = [
      'InvoiceNumber', 'IssueDate', 'DueDate', 
      'SupplierName', 'SupplierTaxID', 'CustomerName'
    ];
    
    requiredFields.forEach(field => {
      assert.ok(
        validation.fields.some(f => f.name === field && f.status === 'mapped'),
        `Required field ${field} should be mapped`
      );
    });
    
    return logResult('Field Mapping Validation Test', true, {
      mappedFields: validation.fields.filter(f => f.status === 'mapped').length,
      unmappedFields: validation.fields.filter(f => f.status === 'unmapped').length,
      validationSuccess: validation.success
    });
  } catch (error) {
    return logResult('Field Mapping Validation Test', false, { 
      error: error.message,
      stack: error.stack
    });
  }
}

// Run all Odoo integration tests
async function runOdooIntegrationTests() {
  console.log('Starting Odoo Integration Tests...');
  
  try {
    // Authenticate
    const token = await authenticate();
    console.log('Authentication successful');
    
    // Run tests
    await testOdooConnectionStatus(token);
    await testOdooInvoiceRetrieval(token);
    await testUBLTransformation(token);
    await testFieldMappingValidation(token);
    
    console.log('Odoo Integration Tests completed');
  } catch (error) {
    console.error('Test suite failed:', error);
  }
}

// Run the tests if this file is executed directly
if (require.main === module) {
  runOdooIntegrationTests();
}

module.exports = {
  runOdooIntegrationTests,
  testOdooConnectionStatus,
  testOdooInvoiceRetrieval,
  testUBLTransformation,
  testFieldMappingValidation
};
