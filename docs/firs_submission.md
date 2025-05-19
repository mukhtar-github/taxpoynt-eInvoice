# FIRS Invoice Submission Implementation

This document outlines the implementation of the FIRS (Federal Inland Revenue Service) submission functionality in the TaxPoynt eInvoice system.

## Overview

The FIRS submission module enables secure and reliable submission of e-invoices to the FIRS API. It supports both JSON and UBL XML formats, with special handling for BIS Billing 3.0 compliant documents.

### Features

- Authentication with FIRS API
- Single and batch invoice submission
- UBL XML invoice submission
- Submission status tracking
- Validation before submission
- Comprehensive error handling

## Architecture

The implementation follows a layered architecture:

1. **API Layer**: FastAPI routes for client interaction
2. **Service Layer**: Core business logic for FIRS API communication
3. **Model Layer**: Data structures for requests and responses

### Component Diagram

```
┌─────────────┐     ┌──────────────────┐     ┌──────────────┐
│ API Routes  │────▶│ FIRS Service     │────▶│  FIRS API    │
└─────────────┘     └──────────────────┘     └──────────────┘
       ▲                     │                       │
       │                     ▼                       │
┌─────────────┐     ┌──────────────────┐            │
│ Client App  │     │ UBL Transformer  │◀───────────┘
└─────────────┘     └──────────────────┘
```

## Authentication

The FIRS API uses OAuth2 Bearer token authentication. The implementation includes:

- Automatic token acquisition
- Token refresh handling
- Token expiry management

```python
# Example authentication flow
await firs_service.authenticate()
# Token is automatically refreshed when needed
```

## Submission Endpoints

### 1. Single Invoice Submission

Submits a single invoice in FIRS-compliant JSON format.

**Endpoint:** `POST /api/v1/firs/submission/invoice`

**Request:**
```json
{
  "invoice_number": "INV-2025-0001",
  "issue_date": "2025-05-16",
  "supplier": {
    "name": "Supplier Company Ltd",
    "tax_id": "1234567890"
  },
  "customer": {
    "name": "Customer Company Ltd",
    "tax_id": "0987654321"
  },
  "items": [
    {
      "description": "Product A",
      "quantity": 2,
      "unit_price": 100.00,
      "tax_rate": 7.5,
      "line_extension_amount": 200.00,
      "tax_amount": 15.00
    }
  ],
  "tax_total": 15.00,
  "invoice_total": 215.00
}
```

**Response:**
```json
{
  "success": true,
  "message": "Invoice submitted successfully",
  "submission_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "status": "SUBMITTED",
  "details": {
    "received_at": "2025-05-16T09:45:12Z",
    "expected_completion": "2025-05-16T09:50:12Z"
  }
}
```

### 2. Batch Submission

Submits multiple invoices in a single request.

**Endpoint:** `POST /api/v1/firs/submission/batch`

**Request:**
```json
[
  {
    "invoice_number": "INV-2025-0001",
    "issue_date": "2025-05-16",
    "...": "..."
  },
  {
    "invoice_number": "INV-2025-0002",
    "issue_date": "2025-05-16",
    "...": "..."
  }
]
```

**Response:**
```json
{
  "success": true,
  "message": "Batch of 2 invoices submitted successfully",
  "submission_id": "3b1f8b40-9a2e-4a8c-b0f3-7d4c5e6f7g8h",
  "status": "BATCH_SUBMITTED",
  "details": {
    "received_at": "2025-05-16T09:45:12Z",
    "invoice_count": 2,
    "expected_completion": "2025-05-16T09:55:12Z"
  }
}
```

### 3. UBL XML Submission

Submits an invoice in UBL XML format, compatible with BIS Billing 3.0.

**Endpoint:** `POST /api/v1/firs/submission/ubl`

**Request:**
- `ubl_file`: UBL XML file upload
- `invoice_type`: Type of invoice (standard, credit_note, etc.)

**Response:**
```json
{
  "success": true,
  "message": "UBL invoice submitted successfully",
  "submission_id": "7d8c9b0a-1e2f-3g4h-5i6j-7k8l9m0n1o2p",
  "status": "UBL_SUBMITTED",
  "details": {
    "received_at": "2025-05-16T09:45:12Z",
    "format": "UBL2.1",
    "profile": "BIS3.0"
  }
}
```

### 4. Status Checking

Checks the status of a previously submitted invoice.

**Endpoint:** `GET /api/v1/firs/submission/status/{submission_id}`

**Response:**
```json
{
  "submission_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "status": "PROCESSING",
  "timestamp": "2025-05-16T09:47:23Z",
  "message": "Invoice is being processed",
  "details": {
    "progress": 65,
    "steps_completed": ["validation", "signature_verification"],
    "steps_pending": ["fiscal_analysis", "confirmation"]
  }
}
```

## Error Handling

The implementation includes comprehensive error handling:

### 1. Validation Errors

```json
{
  "success": false,
  "message": "Invoice validation failed",
  "errors": [
    {
      "field": "tax_total",
      "message": "Tax total does not match sum of line tax amounts"
    },
    {
      "field": "supplier.tax_id",
      "message": "Invalid tax ID format"
    }
  ]
}
```

### 2. Authentication Errors

```json
{
  "detail": "FIRS API authentication failed: Invalid credentials"
}
```

### 3. Submission Errors

```json
{
  "success": false,
  "message": "Submission failed with status code 400",
  "errors": [
    {
      "code": "DUPLICATE_INVOICE",
      "message": "An invoice with the same number has already been submitted"
    }
  ],
  "details": {
    "status_code": 400
  }
}
```

## UBL Integration

The system integrates with the existing Odoo to BIS Billing 3.0 UBL mapping system, allowing for:

1. Transformation of Odoo invoices to UBL format
2. Validation against BIS Billing 3.0 requirements
3. Submission to FIRS with proper metadata

## Sandbox Environment

For testing purposes, the system supports a sandbox environment:

```python
# Example sandbox configuration in settings.py
FIRS_SANDBOX_API_URL = "https://sandbox.firs.gov.ng/api"
FIRS_SANDBOX_API_KEY = "sandbox_key"
FIRS_SANDBOX_API_SECRET = "sandbox_secret"
```

## Security Considerations

1. **API Credentials**: Stored securely in environment variables
2. **Access Control**: Proper authentication and authorization for submission endpoints
3. **Data Validation**: Input validation before submission to prevent injection attacks
4. **Logging**: Detailed logging of submission activity for audit purposes

## Configuration

The FIRS submission functionality can be configured via environment variables:

```
# FIRS API Configuration
FIRS_API_URL=https://api.firs.gov.ng
FIRS_API_KEY=your_api_key
FIRS_API_SECRET=your_api_secret

# Sandbox Configuration
FIRS_SANDBOX_API_URL=https://sandbox.firs.gov.ng/api
FIRS_SANDBOX_API_KEY=your_sandbox_key
FIRS_SANDBOX_API_SECRET=your_sandbox_secret

# Submission Settings
FIRS_SUBMISSION_TIMEOUT=30
FIRS_RETRY_ATTEMPTS=3
```

## Usage Examples

### Example 1: Submitting a Single Invoice

```python
from app.services.firs_service import firs_service

async def submit_invoice_example():
    invoice_data = {
        "invoice_number": "INV-2025-0001",
        "issue_date": "2025-05-16",
        "supplier": {
            "name": "Supplier Company Ltd",
            "tax_id": "1234567890"
        },
        # ... other invoice data
    }
    
    result = await firs_service.submit_invoice(invoice_data)
    
    if result.success:
        print(f"Invoice submitted successfully. Submission ID: {result.submission_id}")
    else:
        print(f"Submission failed: {result.message}")
        if result.errors:
            for error in result.errors:
                print(f"- {error.get('field', 'General')}: {error.get('message')}")
```

### Example 2: Checking Submission Status

```python
from app.services.firs_service import firs_service

async def check_status_example(submission_id):
    try:
        status = await firs_service.check_submission_status(submission_id)
        print(f"Status: {status.status}")
        print(f"Message: {status.message}")
        print(f"Timestamp: {status.timestamp}")
        
        if status.status == "COMPLETED":
            print("Invoice successfully processed by FIRS")
        elif status.status == "FAILED":
            print(f"Processing failed: {status.details.get('error_message')}")
        else:
            print("Invoice is still being processed")
            
    except Exception as e:
        print(f"Error checking status: {str(e)}")
```

## Future Enhancements

1. **Webhook Support**: Implement webhook callbacks for asynchronous status updates
2. **Bulk Status Checking**: Add endpoint for checking multiple submission statuses
3. **Retry Mechanism**: Automatic retry for failed submissions
4. **Reporting Dashboard**: Visual dashboard for submission statistics
5. **Advanced Validation**: Enhanced pre-submission validation rules

## Troubleshooting

Common issues and solutions:

1. **Authentication Failures**
   - Check API credentials
   - Verify network connectivity to FIRS API
   - Check token expiration and refresh logic

2. **Submission Errors**
   - Validate invoice format before submission
   - Check for required fields
   - Verify tax calculations match line items

3. **Status Check Failures**
   - Verify submission ID format
   - Check if submission exists
   - Ensure adequate permissions

## Conclusion

The FIRS submission functionality provides a robust and secure way to submit e-invoices to the FIRS API, supporting both JSON and UBL XML formats. The implementation adheres to FIRS specifications and integrates seamlessly with the existing Odoo to BIS Billing 3.0 UBL mapping system.
