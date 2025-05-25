# Odoo to FIRS Integration Guide

## Overview

This document outlines the complete integration between Odoo ERP systems and the Federal Inland Revenue Service (FIRS) e-Invoicing platform through TaxPoynt eInvoice. This integration follows our ERP-first approach, prioritizing seamless connections with existing business systems while ensuring full compliance with FIRS requirements.

## ERP-First Integration Strategy

The TaxPoynt eInvoice system implements an ERP-first integration strategy, with a particular focus on Odoo as a primary supported ERP system. This approach:

1. Prioritizes data integrity between your ERP and e-invoicing submissions
2. Minimizes manual data entry and reconciliation work
3. Enables automatic status updates between systems
4. Ensures consistent IRN generation across all platforms

## Key Components

### 1. BIS Billing 3.0 UBL Field Mapping

The integration includes a comprehensive field mapping system with three main components:

* **OdooUBLValidator** - Validates mapped fields against BIS Billing 3.0 requirements
* **OdooUBLTransformer** - Transforms Odoo data to UBL XML format
* **Field Mapping Documentation** - Complete field mapping reference

All required invoice fields are handled, including:
- Header information
- Supplier/customer details
- Line items
- Tax information
- Monetary totals

### 2. IRN Generation Integration

The IRN (Invoice Reference Number) generation system has been enhanced to:

* Extract invoice numbers directly from Odoo
* Incorporate the FIRS-assigned Service ID (e.g., 94ND90NR)
* Apply the current date in YYYYMMDD format
* Assemble the components in the required format: `InvoiceNumber-ServiceID-YYYYMMDD`

For example: `INV001-94ND90NR-20250525`

### 3. UUID4 Business Identification

The integration now supports UUID4 format for business identification, ensuring:

* Unique global identifiers for each business entity
* Proper association between TIN (Tax Identification Number) and business ID
* Compliance with FIRS business entity requirements

## API Integration Points

### Connection API

**Endpoint:** `POST /api/v1/odoo/connect`

This API establishes a connection with your Odoo instance, authenticates, and retrieves available invoices.

**Request:**
```json
{
  "url": "https://your-odoo-instance.com",
  "database": "your_odoo_database",
  "username": "your_odoo_username",
  "password": "your_odoo_password",
  "options": {
    "include_draft_invoices": false,
    "start_date": "2025-01-01",
    "limit": 50
  }
}
```

**Response:**
```json
{
  "code": 200,
  "data": {
    "connection_id": "9e8d7c6b-5a4b-3c2d-1e0f-9a8b7c6d5e4f",
    "invoices_count": 12,
    "invoice_ids": ["INV/2025/0001", "INV/2025/0002", "INV/2025/0003", "..."]
  },
  "message": "Successfully connected to Odoo instance"
}
```

### Conversion and Submission API

**Endpoint:** `POST /api/v1/odoo/submit`

This API retrieves an invoice from Odoo, converts it to the FIRS UBL format, generates a valid IRN, and submits it to FIRS.

**Request:**
```json
{
  "connection_id": "9e8d7c6b-5a4b-3c2d-1e0f-9a8b7c6d5e4f",
  "invoice_id": "INV/2025/0001",
  "business_id": "4a4d0d3b-2392-46d4-b3b4-8f9cc00d9443", 
  "use_sandbox": true
}
```

**Response:**
```json
{
  "code": 200,
  "data": {
    "irn": "INV/2025/0001-94ND90NR-20250525",
    "submission_id": "5f3e9b1d-8c4e-4b0a-9f5d-8e7a3b1d4c2e",
    "status": "accepted",
    "odoo_status_update": "success"
  },
  "message": "Odoo invoice successfully submitted to FIRS"
}
```

## Frontend Integration Components

The TaxPoynt eInvoice frontend includes dedicated components for Odoo integration:

### 1. FIRSOdooConnect Component

The `FIRSOdooConnect.tsx` component provides a user interface for:
- Connecting to your Odoo instance
- Selecting invoices to submit
- Converting Odoo invoices to FIRS format
- Submitting to FIRS with proper IRN generation
- Viewing conversion and submission results

### 2. OdooIntegrationMetricsCard Component

The `OdooIntegrationMetricsCard.tsx` component displays metrics about your Odoo integration:
- Number of invoices synchronized
- Success/failure rates
- Recent submissions
- Integration health status

### 3. OdooIntegrationForm Component

The `OdooIntegrationForm.tsx` component allows configuration of your Odoo connection:
- Server URL
- Database credentials
- API authentication
- Synchronization options

## Testing and Validation

### Testing Your Integration

The TaxPoynt eInvoice platform includes testing tools to ensure proper integration:

1. **IRN Generation Testing**:
   - Validate IRN format compliance
   - Test with various invoice numbers
   - Ensure proper service ID incorporation

2. **Odoo Connection Testing**:
   - Verify connection to your Odoo instance
   - Test authentication and permissions
   - Check invoice retrieval functionality

3. **End-to-End Submission Testing**:
   - Convert Odoo invoices to FIRS format
   - Submit to FIRS sandbox environment
   - Validate responses and IRN generation

## Next Steps

To implement the Odoo to FIRS integration:

1. Configure your Odoo connection in the TaxPoynt eInvoice platform
2. Ensure your FIRS Service ID is correctly configured (currently set to: 94ND90NR)
3. Verify field mappings match your Odoo configuration
4. Run test submissions using the sandbox environment
5. Monitor submission results and fix any mapping issues
6. Switch to production mode after successful testing

## Troubleshooting Common Issues

### Missing or Invalid IRN

If you encounter issues with IRN generation:
- Verify your invoice numbers follow Odoo's standard format
- Ensure your Service ID is correctly configured
- Check that date formatting is correct in YYYYMMDD format

### Connection Failures

If you experience connection issues with Odoo:
- Verify network connectivity between TaxPoynt and your Odoo instance
- Confirm API credentials have sufficient permissions
- Check for any firewalls or security restrictions

### Field Mapping Problems

If invoice data is incorrectly mapped:
- Review the field mapping documentation
- Check for custom fields in your Odoo implementation
- Verify tax settings match Nigerian VAT requirements
