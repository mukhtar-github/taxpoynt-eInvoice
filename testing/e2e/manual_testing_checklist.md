# TaxPoynt eInvoice Manual Testing Checklist

This document provides a comprehensive checklist for manually testing the TaxPoynt eInvoice system in the deployed environment. Use this checklist alongside the automated tests to ensure full coverage of all critical functionality.

## Prerequisites

- Access to deployed frontend (https://taxpoyn.com)
- Valid admin user credentials
- Access to at least one configured Odoo instance
- Access to FIRS sandbox environment

## Odoo Integration Testing

### Odoo Connection

- [ ] **Login to TaxPoynt Dashboard**
  - Verify you can successfully log in
  - Verify you're redirected to the dashboard

- [ ] **Navigate to Integration Settings**
  - Verify all configured Odoo instances are listed
  - Verify connection status indicators are accurate

- [ ] **Test Connection Feature**
  - Click "Test Connection" for each Odoo instance
  - Verify you receive appropriate success/failure messages
  - Verify connection details (URL, database) are correctly displayed

### Odoo Invoice Retrieval

- [ ] **Navigate to Odoo Integration Dashboard**
  - Verify the list of recent invoices loads correctly
  - Verify invoice details (number, date, amount) are displayed accurately

- [ ] **Search for Specific Invoice**
  - Search for an invoice by number
  - Verify correct invoice is found and displayed

- [ ] **View Invoice Details**
  - Select an invoice to view details
  - Verify all invoice fields are correctly populated from Odoo
  - Verify line items are displayed accurately

### UBL Transformation

- [ ] **Transform Invoice to UBL**
  - Select "Transform to UBL" for a specific invoice
  - Verify transformation completes without errors
  - Verify UBL preview is displayed

- [ ] **Validate UBL Structure**
  - Review the UBL XML structure
  - Verify all required BIS Billing 3.0 fields are present
  - Verify supplier and customer information is correctly mapped

- [ ] **Download UBL File**
  - Download the UBL file
  - Open in a text editor and verify the content is valid XML
  - Verify the file follows BIS Billing 3.0 standards

### Field Mapping Validation

- [ ] **Check Field Mapping Status**
  - Navigate to field mapping status page
  - Verify all required fields show as mapped
  - Identify any unmapped fields

- [ ] **Test Missing Field Handling**
  - If possible, select an invoice with known missing fields
  - Verify the system correctly identifies and reports missing fields
  - Verify appropriate warnings/errors are displayed

## IRN Generation Testing

### Single IRN Generation

- [ ] **Navigate to IRN Generation Page**
  - Verify the form loads correctly
  - Verify all required fields are present

- [ ] **Generate IRN for Invoice**
  - Complete the form with valid invoice details
  - Submit the form
  - Verify IRN is generated and displayed
  - Verify IRN format is correct (matches expected pattern)

- [ ] **Test Input Validation**
  - Try submitting with missing required fields
  - Verify appropriate validation messages are displayed
  - Try submitting with invalid data
  - Verify the system properly validates the input

### IRN Validation

- [ ] **Navigate to IRN Validation Page**
  - Verify the form loads correctly

- [ ] **Validate Valid IRN**
  - Enter a previously generated IRN
  - Verify the system confirms it as valid
  - Verify associated invoice details are displayed

- [ ] **Validate Invalid IRN**
  - Enter an invalid or non-existent IRN
  - Verify the system correctly identifies it as invalid
  - Verify appropriate error messages are displayed

### Batch IRN Generation

- [ ] **Navigate to Batch IRN Generation**
  - Verify the interface loads correctly

- [ ] **Upload Batch File**
  - Prepare a CSV file with multiple invoices
  - Upload the file
  - Verify the system processes all invoices
  - Verify IRNs are generated for all valid entries
  - Verify appropriate errors for invalid entries

## FIRS Submission Testing

### FIRS API Connectivity

- [ ] **Check FIRS API Status**
  - Navigate to API Status dashboard
  - Verify FIRS API status is displayed (operational/degraded/error)
  - Verify sandbox availability is correctly shown

### UBL Submission

- [ ] **Navigate to FIRS Submission Page**
  - Verify the form loads correctly

- [ ] **Submit UBL Document**
  - Upload or select a previously generated UBL document
  - Choose sandbox environment
  - Submit the document
  - Verify submission ID is returned
  - Verify submission is tracked in the system

### Submission Status Check

- [ ] **Check Submission Status**
  - Navigate to submission status page
  - Enter a previous submission ID
  - Verify status is correctly displayed
  - Verify detailed information is shown (timestamp, result)

### End-to-End Flow

- [ ] **Complete Full Submission Flow**
  - Start with an invoice in Odoo
  - Retrieve the invoice in TaxPoynt
  - Transform to UBL
  - Generate IRN
  - Submit to FIRS sandbox
  - Check submission status
  - Verify all steps complete successfully

## Dashboard Metrics Testing

### Submission Dashboard

- [ ] **Navigate to Submission Dashboard**
  - Verify the dashboard loads correctly
  - Verify all metrics cards are displayed

- [ ] **Check Time Range Filtering**
  - Test different time ranges (24h, 7d, 30d, all)
  - Verify metrics update accordingly
  - Verify charts and graphs reflect the selected time range

### Error Analysis

- [ ] **Review Error Metrics**
  - Check the error breakdown section
  - Verify error types are categorized correctly
  - Verify count and percentage are displayed accurately

### Integration-Specific Metrics

- [ ] **Check Odoo Integration Metrics**
  - Navigate to Odoo-specific metrics
  - Verify success rates and processing times are displayed
  - Verify metrics match expected values based on test submissions

## Security Testing

### Authentication

- [ ] **Test Session Expiration**
  - Login and remain inactive for the session timeout period
  - Verify you're automatically logged out or prompted to re-authenticate
  - Verify sensitive operations require re-authentication

- [ ] **Test Unauthorized Access**
  - Attempt to access protected routes when logged out
  - Verify you're redirected to login page
  - Verify API calls return appropriate authentication errors

### API Security

- [ ] **Test API Authentication**
  - Attempt API calls without authentication
  - Verify appropriate 401/403 responses
  - Test with invalid tokens
  - Verify proper error responses

## Final Verification

- [ ] **Check Notification System**
  - Verify success/error notifications are displayed appropriately
  - Verify critical errors are prominently displayed

- [ ] **Verify Responsive Design**
  - Test the application on different screen sizes
  - Verify UI adapts appropriately to mobile and tablet sizes

- [ ] **Cross-Browser Testing**
  - Test in multiple browsers (Chrome, Firefox, Safari, Edge)
  - Verify functionality works consistently across browsers

## Issue Reporting

For any issues found during manual testing:

1. Take screenshots of the issue
2. Document the exact steps to reproduce
3. Note the environment details (browser, device)
4. Record any error messages displayed
5. Log the issue in the project tracking system

---

## Testing Log

| Test Date | Tester | Environment | Results Summary | Issues Found |
|-----------|--------|-------------|-----------------|--------------|
|           |        |             |                 |              |
|           |        |             |                 |              |
|           |        |             |                 |              |
