# TaxPoynt eInvoice End-to-End Testing Suite

This testing suite provides comprehensive end-to-end testing for the deployed TaxPoynt eInvoice environment, focusing on three critical integration areas:

1. **Odoo Integration Testing** - Verifies the Odoo to BIS Billing 3.0 UBL field mapping system
2. **IRN Generation Testing** - Validates the IRN generation and validation workflows
3. **FIRS Submission Testing** - Tests the submission flow to the FIRS API

## Prerequisites

Before running the tests, ensure you have:

1. Node.js 14.x or higher installed
2. Access to the deployed environment (frontend and backend)
3. Valid test user credentials
4. At least one configured Odoo instance
5. Access to FIRS sandbox environment

## Setup

1. Install dependencies:

```bash
cd testing/e2e
npm install
```

2. Configure environment variables:

```bash
cp .env.example .env
```

Edit the `.env` file with your specific environment details.

## Running Tests

### Run All Tests

```bash
npm test
```

This will execute all tests in sequence and generate a comprehensive report.

### Run Specific Test Suites

```bash
# Test Odoo integration
npm run test:odoo

# Test IRN generation
npm run test:irn

# Test FIRS submission
npm run test:firs
```

## Test Coverage

The test suite covers the following key functionality:

### Odoo Integration Tests

- Odoo connection status verification
- Invoice retrieval from Odoo
- UBL transformation using the OdooUBLTransformer
- Field mapping validation using OdooUBLValidator
- Testing of all required BIS Billing 3.0 fields

These tests build upon the existing Odoo to BIS Billing 3.0 UBL field mapping system which includes:

- OdooUBLValidator for validating mapped fields
- OdooUBLTransformer for transforming Odoo data to UBL XML
- Complete field mapping handling header information, supplier/customer details, line items, tax information, and monetary totals

### IRN Generation Tests

- Single IRN generation
- IRN validation
- Batch IRN generation
- IRN format verification

### FIRS Submission Tests

- FIRS API connectivity (sandbox)
- UBL document submission
- Submission status check
- End-to-end flow from Odoo to FIRS

These tests integrate with the existing FIRS API Testing Dashboard components:

- FIRSTestForm functionality
- FIRSStatusCheck validation
- FIRSBatchSubmit processes
- Security and authentication checks

## Manual Testing

In addition to the automated tests, a comprehensive manual testing checklist is provided in `manual_testing_checklist.md`. This checklist covers aspects that are difficult to automate and provides a structured approach to manual verification.

## Test Results

All test results are stored in the `results` directory. Each test run creates:

- Individual JSON files for each test case
- A comprehensive test report with success/failure details
- Sample data (UBL files, IRNs, submission IDs) for verification

## Integration Strategy Alignment

These tests are designed to align with the phased integration strategy:

1. **Phase 1 Focus**: Tests prioritize ERP systems (particularly Odoo) and accounting software integrations
2. **Future Expansion**: The testing framework is designed to accommodate additional integrations in later phases (e-commerce platforms, POS systems, etc.)

## Troubleshooting

If tests fail, check the following:

1. **Environment Variables**: Ensure all variables in `.env` are correctly set
2. **API Access**: Verify the test user has appropriate permissions
3. **Network Connectivity**: Confirm the test environment can access all required services
4. **Odoo Configuration**: Verify the Odoo instance is properly configured and accessible
5. **FIRS Sandbox**: Ensure the FIRS sandbox environment is operational

## Security Considerations

- All tests use the sandbox environment for FIRS submissions
- No production data is modified during testing
- Authentication is required for all API calls
- Sensitive information (API keys, passwords) should be stored only in the `.env` file

## Next Steps

After successful testing, consider:

1. Setting up automated CI/CD pipelines to run these tests automatically
2. Expanding test coverage for Phase 2 and Phase 3 integrations as they are implemented
3. Implementing performance and load testing for high-volume scenarios
