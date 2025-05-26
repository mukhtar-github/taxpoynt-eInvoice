# FIRS e-Invoicing Integration - User Guide

## Introduction

This guide explains how to use the FIRS e-invoicing integration features in TaxPoynt eInvoice. It covers configuration, usage, and troubleshooting for Odoo users and system administrators.

## Table of Contents

1. [Configuration](#configuration)
2. [IRN Generation](#irn-generation)
3. [Using Reference Data](#using-reference-data)
4. [Creating FIRS-Compliant Invoices](#creating-firs-compliant-invoices)
5. [FIRS Testing Dashboard](#firs-testing-dashboard)
6. [Troubleshooting](#troubleshooting)

## Configuration

### Prerequisites

Before using the FIRS e-invoicing integration, you need:

1. **FIRS Business Registration**:
   - Registered business with FIRS
   - Valid Service ID (e.g., "94ND90NR")
   - API credentials (API Key and Secret)

2. **Environment Variables**:
   - Set the following environment variables:

```bash
# FIRS API Configuration
FIRS_API_URL=https://eivc-k6z6d.ondigitalocean.app
FIRS_API_KEY=your-api-key
FIRS_API_SECRET=your-api-secret

# Business Information
BUSINESS_NAME=Your Company Name
BUSINESS_TIN=your-tin-number
BUSINESS_SERVICE_ID=your-service-id
```

### Configuration Steps

1. **Login to TaxPoynt Admin**:
   - Navigate to Settings > Integrations > FIRS API

2. **Enter API Credentials**:
   - API Key
   - API Secret
   - Service ID

3. **Set Business Information**:
   - Business Name
   - TIN
   - Contact Information

4. **Test Connection**:
   - Click "Test Connection" to verify your credentials

## IRN Generation

The Invoice Reference Number (IRN) is a unique identifier required by FIRS for each invoice.

### Automatic IRN Generation

IRNs are automatically generated when:
- An invoice is created in Odoo
- An invoice is imported from an external system
- An invoice is manually created in the TaxPoynt dashboard

### IRN Format

The IRN follows the format: `InvoiceNumber-ServiceID-YYYYMMDD`

Example: `INV001-94ND90NR-20250526`

### Manual IRN Generation

If you need to manually generate an IRN:

1. Navigate to Tools > FIRS Tools > Generate IRN
2. Enter the invoice number
3. Select the invoice date
4. Click "Generate"

The system will validate the IRN format and display the result.

## Using Reference Data

TaxPoynt eInvoice automatically retrieves and uses FIRS reference data to ensure compliance.

### Available Reference Data

1. **Currency Codes**:
   - 118 currencies supported by FIRS
   - Default: NGN (Nigerian Naira)

2. **Invoice Types**:
   - 20 invoice types supported by FIRS
   - Common types:
     - 380: Commercial Invoice
     - 381: Credit Note
     - 384: Corrected Invoice

3. **VAT Exemption Codes**:
   - 236 exemption codes for specific products/services
   - Used when an item is VAT-exempt

### Using Reference Data in Odoo

The system automatically maps Odoo fields to FIRS reference data:

1. **Currency**:
   - Odoo's `currency_id` is mapped to FIRS currency code
   - Select a supported currency in Odoo

2. **Invoice Type**:
   - Odoo's invoice type is mapped to FIRS invoice type code
   - Regular invoices map to code 380
   - Credit notes map to code 381

## Creating FIRS-Compliant Invoices

### From Odoo

When creating invoices in Odoo:

1. **Fill Required Fields**:
   - Customer information (name, TIN, address)
   - Invoice lines with proper VAT/tax settings
   - Currency (must be supported by FIRS)

2. **Validate Invoice**:
   - Odoo validation triggers TaxPoynt validation
   - System will flag any compliance issues

3. **FIRS Submission Status**:
   - An additional tab shows FIRS submission status
   - IRN is displayed on the invoice

### From TaxPoynt Dashboard

1. **Create New Invoice**:
   - Click "New Invoice" in the TaxPoynt dashboard
   - Fill in the invoice details
   - Select customer from registered parties

2. **Add Line Items**:
   - Add products/services
   - Set quantity, price, and VAT rate
   - System calculates totals

3. **Validate and Submit**:
   - Click "Validate" to check FIRS compliance
   - Click "Submit to FIRS" when ready

## FIRS Testing Dashboard

The FIRS Testing Dashboard allows you to test API functionality without affecting production data.

### Accessing the Dashboard

1. Navigate to Tools > FIRS Testing Dashboard
2. Login with your admin credentials

### Dashboard Features

1. **Status Check**:
   - Test API connectivity
   - Verify credentials

2. **Entity Lookup**:
   - Search for registered businesses by TIN

3. **IRN Generation and Validation**:
   - Test IRN generation
   - Validate existing IRNs

4. **Invoice Validation**:
   - Test invoice payloads
   - View validation results

5. **Batch Testing**:
   - Upload multiple invoices
   - Validate in batch

### Sandbox vs. Production

- Toggle between sandbox and production environments
- Clearly marked to prevent accidental production submissions
- Sandbox test data does not affect real FIRS submissions

## Troubleshooting

### Common Issues and Solutions

1. **"Invalid IRN Format" Error**:
   - **Issue**: The IRN doesn't follow FIRS requirements
   - **Solution**: Ensure invoice numbers are alphanumeric and Service ID is correct

2. **"Currency Not Supported" Error**:
   - **Issue**: The invoice uses a currency not recognized by FIRS
   - **Solution**: Check supported currencies in the dashboard and use only those

3. **"Invalid VAT Rate" Error**:
   - **Issue**: The VAT rate doesn't match FIRS requirements
   - **Solution**: Use standard 7.5% VAT or a valid exemption code

4. **Connection Issues**:
   - **Issue**: Cannot connect to FIRS API
   - **Solution**: 
     - Verify internet connection
     - Check API credentials in settings
     - Ensure FIRS services are operational

### Getting Help

If you encounter issues not covered in this guide:

1. **Check System Status**:
   - Tools > FIRS Testing Dashboard > System Status

2. **View Logs**:
   - Admin > System > Logs > FIRS API Logs

3. **Contact Support**:
   - Email: support@taxpoynt.com
   - Include error messages and screenshots

### Planned Updates

The following features are currently in development:

1. Enhanced entity lookup with cached results
2. Batch submission optimization
3. Additional validation rules based on FIRS updates

Check the "Updates" section in the dashboard for the latest information on upcoming features.
