/**
 * IRN Generation End-to-End Test
 * 
 * This script tests the IRN (Invoice Reference Number) generation process
 * in the deployed environment.
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

// Test IRN generation
async function testIRNGeneration(token) {
  try {
    // Create a test invoice payload for IRN generation
    const invoicePayload = {
      supplier: {
        name: "Test Supplier Ltd",
        tax_id: "12345678901",
        address: {
          street: "123 Test Street",
          city: "Test City",
          state: "Test State",
          postal_code: "12345",
          country: "NG"
        }
      },
      customer: {
        name: "Test Customer Ltd",
        tax_id: "09876543210",
        address: {
          street: "456 Customer Street",
          city: "Customer City",
          state: "Customer State",
          postal_code: "54321",
          country: "NG"
        }
      },
      invoice: {
        number: `TEST-${Date.now()}`,
        issue_date: new Date().toISOString().split('T')[0],
        due_date: new Date(Date.now() + 30*24*60*60*1000).toISOString().split('T')[0],
        currency: "NGN",
        total_amount: 1000.00,
        tax_amount: 75.00
      }
    };
    
    const response = await axios.post(
      `${config.urls.backend}/irn/generate`,
      invoicePayload,
      {
        headers: { Authorization: `Bearer ${token}` }
      }
    );
    
    assert.strictEqual(response.status, 200, 'Status code should be 200');
    assert.ok(response.data.irn, 'Should return an IRN');
    assert.ok(response.data.timestamp, 'Should return a timestamp');
    
    // Save generated IRN details for later tests
    fs.writeFileSync(
      path.join(resultsDir, 'irn_generation_result.json'),
      JSON.stringify(response.data, null, 2)
    );
    
    return logResult('IRN Generation Test', true, { 
      irn: response.data.irn,
      timestamp: response.data.timestamp,
      invoiceNumber: invoicePayload.invoice.number
    });
  } catch (error) {
    return logResult('IRN Generation Test', false, { 
      error: error.message,
      stack: error.stack
    });
  }
}

// Test IRN validation
async function testIRNValidation(token) {
  try {
    // First, generate a new IRN
    const genResponse = await axios.post(
      `${config.urls.backend}/irn/generate`,
      {
        supplier: {
          name: "Validation Test Supplier",
          tax_id: "12345678901"
        },
        customer: {
          name: "Validation Test Customer",
          tax_id: "09876543210"
        },
        invoice: {
          number: `VALIDATE-${Date.now()}`,
          issue_date: new Date().toISOString().split('T')[0],
          total_amount: 2000.00
        }
      },
      {
        headers: { Authorization: `Bearer ${token}` }
      }
    );
    
    const irn = genResponse.data.irn;
    
    // Now validate the IRN
    const response = await axios.post(
      `${config.urls.backend}/irn/validate`,
      { irn },
      {
        headers: { Authorization: `Bearer ${token}` }
      }
    );
    
    assert.strictEqual(response.status, 200, 'Status code should be 200');
    assert.ok(response.data.valid, 'IRN should be valid');
    assert.ok(response.data.details, 'Should return validation details');
    
    return logResult('IRN Validation Test', true, { 
      irn,
      valid: response.data.valid,
      details: response.data.details
    });
  } catch (error) {
    return logResult('IRN Validation Test', false, { 
      error: error.message,
      stack: error.stack
    });
  }
}

// Test IRN batch generation
async function testIRNBatchGeneration(token) {
  try {
    // Create multiple test invoices
    const invoices = Array(3).fill().map((_, i) => ({
      supplier: {
        name: "Batch Test Supplier",
        tax_id: "12345678901"
      },
      customer: {
        name: "Batch Test Customer",
        tax_id: "09876543210"
      },
      invoice: {
        number: `BATCH-${Date.now()}-${i}`,
        issue_date: new Date().toISOString().split('T')[0],
        total_amount: 1000.00 * (i + 1)
      }
    }));
    
    const response = await axios.post(
      `${config.urls.backend}/bulk-irn/generate`,
      { invoices },
      {
        headers: { Authorization: `Bearer ${token}` }
      }
    );
    
    assert.strictEqual(response.status, 200, 'Status code should be 200');
    assert.ok(Array.isArray(response.data.results), 'Should return results array');
    assert.strictEqual(response.data.results.length, invoices.length, 
      'Should return same number of results as invoices');
    
    const allSuccessful = response.data.results.every(r => r.success && r.irn);
    assert.ok(allSuccessful, 'All IRNs should be generated successfully');
    
    return logResult('IRN Batch Generation Test', true, { 
      batchSize: invoices.length,
      successful: response.data.results.filter(r => r.success).length,
      failed: response.data.results.filter(r => !r.success).length
    });
  } catch (error) {
    return logResult('IRN Batch Generation Test', false, { 
      error: error.message,
      stack: error.stack
    });
  }
}

// Run all IRN generation tests
async function runIRNGenerationTests() {
  console.log('Starting IRN Generation Tests...');
  
  try {
    // Authenticate
    const token = await authenticate();
    console.log('Authentication successful');
    
    // Run tests
    await testIRNGeneration(token);
    await testIRNValidation(token);
    await testIRNBatchGeneration(token);
    
    console.log('IRN Generation Tests completed');
  } catch (error) {
    console.error('Test suite failed:', error);
  }
}

// Run the tests if this file is executed directly
if (require.main === module) {
  runIRNGenerationTests();
}

module.exports = {
  runIRNGenerationTests,
  testIRNGeneration,
  testIRNValidation,
  testIRNBatchGeneration
};
