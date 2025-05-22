/**
 * TaxPoynt eInvoice Manual Verification Script
 * 
 * This script provides a guided approach to manually verify the key components
 * of the deployed TaxPoynt eInvoice system.
 */

const readline = require('readline');
const fs = require('fs');
const path = require('path');

// Create the interface for user input
const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

// Create results directory if it doesn't exist
const resultsDir = path.join(__dirname, 'results');
if (!fs.existsSync(resultsDir)) {
  fs.mkdirSync(resultsDir, { recursive: true });
}

// Function to log test results
function logResult(component, status, notes) {
  const timestamp = new Date().toISOString();
  const result = {
    component,
    timestamp,
    status,
    notes
  };
  
  // Save to results file
  const filename = path.join(resultsDir, 
    `manual_verification_${component.toLowerCase().replace(/\s+/g, '_')}_${timestamp.replace(/:/g, '-')}.json`);
  
  fs.writeFileSync(filename, JSON.stringify(result, null, 2));
  
  console.log(`\nResult saved to ${filename}`);
}

// Function to prompt user with a yes/no question
function askYesNo(question) {
  return new Promise((resolve) => {
    rl.question(`${question} (y/n): `, (answer) => {
      resolve(answer.toLowerCase().startsWith('y'));
    });
  });
}

// Function to prompt user for text input
function askForInput(prompt) {
  return new Promise((resolve) => {
    rl.question(`${prompt}: `, (answer) => {
      resolve(answer);
    });
  });
}

// Function to run the Odoo integration verification
async function verifyOdooIntegration() {
  console.log('\n====== ODOO INTEGRATION VERIFICATION ======');
  console.log('This will guide you through verifying the Odoo integration in your deployed environment.');
  
  // Verify Odoo connection
  console.log('\n1. ODOO CONNECTION:');
  console.log('   Please navigate to your integration settings page in the TaxPoynt dashboard.');
  const connectionSuccess = await askYesNo('   Can you see your configured Odoo instances with status indicators?');
  
  // Verify UBL transformation
  console.log('\n2. UBL TRANSFORMATION:');
  console.log('   Please select an invoice from your Odoo integration page and click "Transform to UBL".');
  const transformationSuccess = await askYesNo('   Did the transformation complete successfully?');
  
  // Verify field mapping
  console.log('\n3. FIELD MAPPING:');
  console.log('   Examine the UBL output and check if all required BIS Billing 3.0 fields are present.');
  const fieldMappingSuccess = await askYesNo('   Are all required fields correctly mapped?');
  
  // Notes
  const notes = await askForInput('\nPlease provide any additional notes about the Odoo integration verification');
  
  // Log results
  const status = connectionSuccess && transformationSuccess && fieldMappingSuccess ? 'PASS' : 'FAIL';
  logResult('Odoo Integration', status, {
    connectionSuccess,
    transformationSuccess,
    fieldMappingSuccess,
    notes
  });
  
  return status === 'PASS';
}

// Function to run the IRN generation verification
async function verifyIRNGeneration() {
  console.log('\n====== IRN GENERATION VERIFICATION ======');
  console.log('This will guide you through verifying the IRN generation in your deployed environment.');
  
  // Verify single IRN generation
  console.log('\n1. SINGLE IRN GENERATION:');
  console.log('   Please navigate to the IRN generation page and generate an IRN for an invoice.');
  const singleIrnSuccess = await askYesNo('   Was the IRN generated successfully?');
  
  // Verify IRN validation
  console.log('\n2. IRN VALIDATION:');
  console.log('   Please navigate to the IRN validation page and validate the IRN you just generated.');
  const validationSuccess = await askYesNo('   Was the IRN validated successfully?');
  
  // Verify batch IRN generation (if applicable)
  console.log('\n3. BATCH IRN GENERATION (if applicable):');
  console.log('   If your system supports batch IRN generation, please test it.');
  const batchSupported = await askYesNo('   Does your system support batch IRN generation?');
  
  let batchSuccess = null;
  if (batchSupported) {
    batchSuccess = await askYesNo('   Was the batch IRN generation successful?');
  }
  
  // Notes
  const notes = await askForInput('\nPlease provide any additional notes about the IRN generation verification');
  
  // Log results
  const status = singleIrnSuccess && validationSuccess && (!batchSupported || batchSuccess) ? 'PASS' : 'FAIL';
  logResult('IRN Generation', status, {
    singleIrnSuccess,
    validationSuccess,
    batchSupported,
    batchSuccess,
    notes
  });
  
  return status === 'PASS';
}

// Function to run the FIRS submission verification
async function verifyFIRSSubmission() {
  console.log('\n====== FIRS SUBMISSION VERIFICATION ======');
  console.log('This will guide you through verifying the FIRS submission in your deployed environment.');
  
  // Verify FIRS API connectivity
  console.log('\n1. FIRS API CONNECTIVITY:');
  console.log('   Please navigate to the API Status dashboard.');
  const apiConnectivity = await askYesNo('   Is the FIRS API status shown as operational?');
  
  // Verify FIRS sandbox submission
  console.log('\n2. FIRS SANDBOX SUBMISSION:');
  console.log('   Please navigate to the FIRS testing dashboard and submit a test invoice to the sandbox environment.');
  const sandboxSubmission = await askYesNo('   Was the submission successful (received a submission ID)?');
  
  // Verify submission status check
  console.log('\n3. SUBMISSION STATUS CHECK:');
  console.log('   Please check the status of the submission you just made.');
  const statusCheck = await askYesNo('   Can you successfully check the submission status?');
  
  // Notes
  const notes = await askForInput('\nPlease provide any additional notes about the FIRS submission verification');
  
  // Log results
  const status = apiConnectivity && sandboxSubmission && statusCheck ? 'PASS' : 'FAIL';
  logResult('FIRS Submission', status, {
    apiConnectivity,
    sandboxSubmission,
    statusCheck,
    notes
  });
  
  return status === 'PASS';
}

// Function to run the end-to-end workflow verification
async function verifyEndToEndWorkflow() {
  console.log('\n====== END-TO-END WORKFLOW VERIFICATION ======');
  console.log('This will guide you through verifying the complete end-to-end workflow in your deployed environment.');
  
  console.log('\nPlease complete the following workflow:');
  console.log('1. Start with an invoice in Odoo');
  console.log('2. Retrieve the invoice in TaxPoynt');
  console.log('3. Transform to UBL');
  console.log('4. Generate IRN');
  console.log('5. Submit to FIRS sandbox');
  console.log('6. Check submission status');
  
  const workflowSuccess = await askYesNo('\nWere you able to complete the entire workflow successfully?');
  
  // Bottlenecks or issues
  const bottlenecks = await askForInput('Did you encounter any bottlenecks or issues during the workflow? If yes, please describe');
  
  // Performance
  const performance = await askForInput('How would you rate the performance of the end-to-end workflow? (Excellent/Good/Fair/Poor)');
  
  // Notes
  const notes = await askForInput('\nPlease provide any additional notes about the end-to-end workflow verification');
  
  // Log results
  const status = workflowSuccess ? 'PASS' : 'FAIL';
  logResult('End-to-End Workflow', status, {
    workflowSuccess,
    bottlenecks,
    performance,
    notes
  });
  
  return status === 'PASS';
}

// Main function to run the verification script
async function runVerification() {
  console.log('===============================================================');
  console.log('TaxPoynt eInvoice Manual Verification Script');
  console.log('===============================================================');
  console.log('This script will guide you through manually verifying the key components');
  console.log('of your deployed TaxPoynt eInvoice system.');
  console.log('\nThe verification will cover:');
  console.log('1. Odoo Integration and UBL Transformation');
  console.log('2. IRN Generation and Validation');
  console.log('3. FIRS Submission');
  console.log('4. End-to-End Workflow');
  
  const startVerification = await askYesNo('\nAre you ready to start the verification?');
  
  if (!startVerification) {
    console.log('\nVerification cancelled. Exiting...');
    rl.close();
    return;
  }
  
  // Run the verification steps
  const odooResult = await verifyOdooIntegration();
  const irnResult = await verifyIRNGeneration();
  const firsResult = await verifyFIRSSubmission();
  const workflowResult = await verifyEndToEndWorkflow();
  
  // Generate summary
  console.log('\n===============================================================');
  console.log('VERIFICATION SUMMARY');
  console.log('===============================================================');
  console.log(`Odoo Integration: ${odooResult ? 'PASS' : 'FAIL'}`);
  console.log(`IRN Generation: ${irnResult ? 'PASS' : 'FAIL'}`);
  console.log(`FIRS Submission: ${firsResult ? 'PASS' : 'FAIL'}`);
  console.log(`End-to-End Workflow: ${workflowResult ? 'PASS' : 'FAIL'}`);
  
  const overallStatus = odooResult && irnResult && firsResult && workflowResult ? 'PASS' : 'FAIL';
  console.log(`\nOverall Verification Status: ${overallStatus}`);
  
  // Save summary
  const summary = {
    timestamp: new Date().toISOString(),
    components: {
      odooIntegration: odooResult,
      irnGeneration: irnResult,
      firsSubmission: firsResult,
      endToEndWorkflow: workflowResult
    },
    overallStatus
  };
  
  const summaryFile = path.join(resultsDir, `verification_summary_${new Date().toISOString().replace(/:/g, '-')}.json`);
  fs.writeFileSync(summaryFile, JSON.stringify(summary, null, 2));
  console.log(`\nSummary saved to ${summaryFile}`);
  
  rl.close();
}

// Run the verification script
runVerification();
