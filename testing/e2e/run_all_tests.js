/**
 * TaxPoynt eInvoice End-to-End Testing Suite
 * 
 * This script runs all end-to-end tests for the deployed environment,
 * focusing on Odoo integration, IRN generation, and FIRS submissions.
 */

const odooTests = require('./odoo_integration_test');
const irnTests = require('./irn_generation_test');
const firsTests = require('./firs_submission_test');
const fs = require('fs');
const path = require('path');

// Create results directory if it doesn't exist
const resultsDir = path.join(__dirname, 'results');
if (!fs.existsSync(resultsDir)) {
  fs.mkdirSync(resultsDir, { recursive: true });
}

// Create a test report file
const reportFile = path.join(resultsDir, `test_report_${new Date().toISOString().replace(/:/g, '-')}.txt`);

// Utility function to log to both console and report file
function log(message) {
  console.log(message);
  fs.appendFileSync(reportFile, message + '\n');
}

// Main test runner
async function runAllTests() {
  const startTime = new Date();
  
  log('===============================================================');
  log(`TaxPoynt eInvoice End-to-End Test Suite`);
  log(`Started: ${startTime.toISOString()}`);
  log(`Environment: ${process.env.NODE_ENV || 'development'}`);
  log('===============================================================\n');
  
  try {
    // Run Odoo integration tests
    log('\n=== Running Odoo Integration Tests ===\n');
    await odooTests.runOdooIntegrationTests();
    
    // Run IRN generation tests
    log('\n=== Running IRN Generation Tests ===\n');
    await irnTests.runIRNGenerationTests();
    
    // Run FIRS submission tests
    log('\n=== Running FIRS Submission Tests ===\n');
    await firsTests.runFIRSSubmissionTests();
    
    // Calculate execution time
    const endTime = new Date();
    const executionTime = (endTime - startTime) / 1000;
    
    log('\n===============================================================');
    log(`Test Suite Completed: ${endTime.toISOString()}`);
    log(`Total Execution Time: ${executionTime} seconds`);
    log('===============================================================');
    
    // Analyze results
    const results = analyzeResults();
    
    log('\n=== Test Results Summary ===');
    log(`Total Tests: ${results.total}`);
    log(`Passed: ${results.passed}`);
    log(`Failed: ${results.failed}`);
    log(`Success Rate: ${results.successRate.toFixed(2)}%`);
    
    if (results.failed > 0) {
      log('\nFailed Tests:');
      results.failedTests.forEach(test => {
        log(`- ${test.test} (${test.timestamp})`);
        log(`  Error: ${test.error}`);
      });
    }
    
  } catch (error) {
    log(`\nTest suite execution failed: ${error.message}`);
    log(error.stack);
  }
}

// Analyze all test results
function analyzeResults() {
  const results = {
    total: 0,
    passed: 0,
    failed: 0,
    successRate: 0,
    failedTests: []
  };
  
  try {
    // Read all result files
    const files = fs.readdirSync(resultsDir)
      .filter(file => file.endsWith('.json'));
    
    files.forEach(file => {
      try {
        const testResult = JSON.parse(
          fs.readFileSync(path.join(resultsDir, file), 'utf8')
        );
        
        results.total++;
        
        if (testResult.success) {
          results.passed++;
        } else {
          results.failed++;
          results.failedTests.push({
            test: testResult.test,
            timestamp: testResult.timestamp,
            error: testResult.error
          });
        }
      } catch (error) {
        console.error(`Error parsing result file ${file}:`, error);
      }
    });
    
    results.successRate = (results.passed / results.total) * 100;
  } catch (error) {
    console.error('Error analyzing results:', error);
  }
  
  return results;
}

// Run the tests if this file is executed directly
if (require.main === module) {
  runAllTests();
}

module.exports = {
  runAllTests
};
