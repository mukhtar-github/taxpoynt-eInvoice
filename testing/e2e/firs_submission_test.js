/**
 * FIRS Submission End-to-End Test
 * 
 * This script tests the FIRS submission process in the deployed environment,
 * focusing on the integration between Odoo, UBL transformation, and FIRS API.
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

// Test FIRS API connectivity
async function testFIRSAPIConnection(token) {
  try {
    const response = await axios.get(
      `${config.urls.backend}/integration-status/firs`,
      {
        headers: { Authorization: `Bearer ${token}` }
      }
    );
    
    assert.strictEqual(response.status, 200, 'Status code should be 200');
    assert.ok(response.data.status, 'Should return API status');
    
    // Check sandbox environment
    assert.ok(
      response.data.sandbox_available, 
      'FIRS sandbox environment should be available'
    );
    
    return logResult('FIRS API Connection Test', true, { 
      status: response.data.status,
      sandboxAvailable: response.data.sandbox_available,
      productionAvailable: response.data.production_available || false
    });
  } catch (error) {
    return logResult('FIRS API Connection Test', false, { 
      error: error.message,
      stack: error.stack
    });
  }
}

// Test UBL-to-FIRS submission
async function testUBLSubmission(token) {
  try {
    let ublContent;
    
    // Try to read a UBL sample from previous tests
    try {
      ublContent = fs.readFileSync(
        path.join(resultsDir, 'odoo_ubl_sample.xml'), 
        'utf8'
      );
    } catch (error) {
      // If no sample exists, generate one by transforming an Odoo invoice
      const transformResponse = await axios.post(
        `${config.urls.backend}/odoo-ubl/transform`, 
        {
          invoice_id: config.odooTest.testInvoiceId,
          validate: true
        },
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      
      ublContent = transformResponse.data.ubl;
    }
    
    // Submit the UBL to FIRS
    const response = await axios.post(
      `${config.urls.backend}/firs/submit-ubl`,
      {
        ubl: ublContent,
        use_sandbox: true
      },
      {
        headers: { Authorization: `Bearer ${token}` }
      }
    );
    
    assert.strictEqual(response.status, 200, 'Status code should be 200');
    assert.ok(response.data.submission_id, 'Should return a submission ID');
    
    // Save submission details for status check test
    fs.writeFileSync(
      path.join(resultsDir, 'firs_submission_result.json'),
      JSON.stringify(response.data, null, 2)
    );
    
    return logResult('FIRS UBL Submission Test', true, { 
      submissionId: response.data.submission_id,
      timestamp: response.data.timestamp,
      sandbox: true
    });
  } catch (error) {
    return logResult('FIRS UBL Submission Test', false, { 
      error: error.message,
      stack: error.stack
    });
  }
}

// Test submission status check
async function testSubmissionStatusCheck(token) {
  try {
    let submissionId;
    
    // Try to read submission ID from previous test
    try {
      const submissionData = JSON.parse(
        fs.readFileSync(
          path.join(resultsDir, 'firs_submission_result.json'), 
          'utf8'
        )
      );
      submissionId = submissionData.submission_id;
    } catch (error) {
      // If no submission exists, throw error
      throw new Error('No previous submission found. Run UBL submission test first.');
    }
    
    // Check submission status
    const response = await axios.get(
      `${config.urls.backend}/firs/status/${submissionId}?sandbox=true`,
      {
        headers: { Authorization: `Bearer ${token}` }
      }
    );
    
    assert.strictEqual(response.status, 200, 'Status code should be 200');
    assert.ok(response.data.status, 'Should return submission status');
    
    return logResult('FIRS Submission Status Check Test', true, { 
      submissionId,
      status: response.data.status,
      details: response.data.details || {}
    });
  } catch (error) {
    return logResult('FIRS Submission Status Check Test', false, { 
      error: error.message,
      stack: error.stack
    });
  }
}

// Test end-to-end Odoo to FIRS flow
async function testOdooToFIRSFlow(token) {
  try {
    // 1. Get invoice from Odoo
    const odooResponse = await axios.get(
      `${config.urls.backend}/odoo-ubl/invoice/${config.odooTest.testInvoiceId}`, 
      {
        headers: { Authorization: `Bearer ${token}` }
      }
    );
    
    const invoice = odooResponse.data.invoice;
    
    // 2. Transform to UBL
    const ublResponse = await axios.post(
      `${config.urls.backend}/odoo-ubl/transform`, 
      {
        invoice_id: config.odooTest.testInvoiceId,
        validate: true
      },
      {
        headers: { Authorization: `Bearer ${token}` }
      }
    );
    
    const ubl = ublResponse.data.ubl;
    
    // 3. Generate IRN
    const irnResponse = await axios.post(
      `${config.urls.backend}/irn/generate`,
      {
        supplier: {
          name: invoice.supplier_name || "Test Supplier",
          tax_id: invoice.supplier_tax_id || "12345678901"
        },
        customer: {
          name: invoice.customer_name || "Test Customer",
          tax_id: invoice.customer_tax_id || "09876543210"
        },
        invoice: {
          number: invoice.number || `TEST-${Date.now()}`,
          issue_date: invoice.date || new Date().toISOString().split('T')[0],
          total_amount: invoice.amount_total || 1000.00
        }
      },
      {
        headers: { Authorization: `Bearer ${token}` }
      }
    );
    
    const irn = irnResponse.data.irn;
    
    // 4. Submit to FIRS with IRN
    const firsResponse = await axios.post(
      `${config.urls.backend}/firs/submit-ubl`,
      {
        ubl,
        irn,
        use_sandbox: true
      },
      {
        headers: { Authorization: `Bearer ${token}` }
      }
    );
    
    const submissionId = firsResponse.data.submission_id;
    
    // 5. Check submission metrics
    const metricsResponse = await axios.get(
      `${config.urls.backend}/submission-dashboard/metrics?time_range=24h`,
      {
        headers: { Authorization: `Bearer ${token}` }
      }
    );
    
    // Save full flow details
    fs.writeFileSync(
      path.join(resultsDir, 'odoo_to_firs_flow.json'),
      JSON.stringify({
        invoice: odooResponse.data,
        ubl: { size: ubl.length, sample: ubl.substring(0, 500) + '...' },
        irn: irnResponse.data,
        submission: firsResponse.data,
        metrics: metricsResponse.data
      }, null, 2)
    );
    
    return logResult('End-to-End Odoo to FIRS Flow Test', true, { 
      invoiceId: config.odooTest.testInvoiceId,
      invoiceNumber: invoice.number,
      irn,
      submissionId,
      timestamp: firsResponse.data.timestamp
    });
  } catch (error) {
    return logResult('End-to-End Odoo to FIRS Flow Test', false, { 
      error: error.message,
      stack: error.stack
    });
  }
}

// Run all FIRS submission tests
async function runFIRSSubmissionTests() {
  console.log('Starting FIRS Submission Tests...');
  
  try {
    // Authenticate
    const token = await authenticate();
    console.log('Authentication successful');
    
    // Run tests
    await testFIRSAPIConnection(token);
    await testUBLSubmission(token);
    await testSubmissionStatusCheck(token);
    await testOdooToFIRSFlow(token);
    
    console.log('FIRS Submission Tests completed');
  } catch (error) {
    console.error('Test suite failed:', error);
  }
}

// Run the tests if this file is executed directly
if (require.main === module) {
  runFIRSSubmissionTests();
}

module.exports = {
  runFIRSSubmissionTests,
  testFIRSAPIConnection,
  testUBLSubmission,
  testSubmissionStatusCheck,
  testOdooToFIRSFlow
};
