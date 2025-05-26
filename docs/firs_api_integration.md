# FIRS API Integration - Technical Documentation

## Overview

This document outlines the FIRS API integration implemented in the TaxPoynt eInvoice system. It focuses on the working endpoints and functionality that has been successfully implemented and tested, while also documenting known limitations and requirements for full integration.

## Table of Contents

1. [Working Endpoints](#working-endpoints)
2. [IRN Generation and Validation](#irn-generation-and-validation)
3. [Invoice Data Structure](#invoice-data-structure)
4. [Authentication Requirements](#authentication-requirements)
5. [Integration with Odoo](#integration-with-odoo)
6. [Known Limitations](#known-limitations)
7. [Troubleshooting](#troubleshooting)

## Working Endpoints

The following FIRS API endpoints have been successfully tested and integrated:

### Reference Data Endpoints

| Endpoint | Method | Description | Status |
|----------|--------|-------------|--------|
| `/api/v1/invoice/resources/currencies` | GET | Retrieves available currency codes (118 currencies) | ✅ Working |
| `/api/v1/invoice/resources/invoice-types` | GET | Retrieves available invoice type codes (20 types) | ✅ Working |
| `/api/v1/invoice/resources/vat-exemptions` | GET | Retrieves VAT exemption codes (236 exemptions) | ✅ Working |
| `/api/v1/invoice/resources/countries` | GET | Retrieves country codes (249 countries) | ✅ Working |
| `/api/v1/invoice/resources/services-codes` | GET | Retrieves service codes (419 codes) | ✅ Working |

### Example Request

```python
headers = {
    "accept": "*/*",
    "x-api-key": FIRS_API_KEY,
    "x-api-secret": FIRS_API_SECRET,
    "x-timestamp": timestamp,
    "x-request-id": request_id,
    "x-certificate": FIRS_CERTIFICATE_B64,
    "Content-Type": "application/json"
}

response = requests.get(
    "https://eivc-k6z6d.ondigitalocean.app/api/v1/invoice/resources/currencies", 
    headers=headers
)
```

### Example Response

```json
{
  "code": 200,
  "data": [
    {
      "code": "USD",
      "symbol": "$",
      "name": "US Dollar",
      "decimal_digits": 2
    },
    {
      "code": "NGN",
      "symbol": "₦",
      "name": "Nigerian Naira",
      "decimal_digits": 2
    },
    // Additional currencies...
  ]
}
```

## IRN Generation and Validation

The IRN (Invoice Reference Number) is a critical component of the FIRS e-invoicing system. TaxPoynt eInvoice implements IRN generation and validation according to FIRS specifications.

### IRN Format

The IRN follows the format: `InvoiceNumber-ServiceID-YYYYMMDD`

- **InvoiceNumber**: Alphanumeric identifier from the accounting system
- **ServiceID**: 8-character FIRS-assigned Service ID (e.g., `94ND90NR`)
- **YYYYMMDD**: Date in format YYYYMMDD (e.g., `20250526`)

Example: `INV001-94ND90NR-20250526`

### IRN Generation Implementation

```python
def generate_irn(invoice_number: str, invoice_date: Optional[datetime.datetime] = None) -> str:
    """
    Generate IRN according to FIRS specifications: InvoiceNumber-ServiceID-YYYYMMDD.
    """
    if not invoice_number:
        raise ValueError("Invoice number is required for IRN generation")
    
    # Validate invoice number (alphanumeric only)
    if not all(c.isalnum() for c in invoice_number):
        raise ValueError("Invoice number must contain only alphanumeric characters")
    
    # Use provided date or current date
    if invoice_date is None:
        invoice_date = datetime.datetime.now()
        
    # Format date as YYYYMMDD
    date_str = invoice_date.strftime("%Y%m%d")
    
    # Construct IRN
    return f"{invoice_number}-{BUSINESS_SERVICE_ID}-{date_str}"
```

### IRN Validation Implementation

IRN validation ensures that the IRN follows the FIRS format requirements:

```python
def validate_irn(irn: str) -> Tuple[bool, Optional[str]]:
    """
    Validate that an IRN follows the FIRS format requirements.
    """
    # Check overall format with regex
    pattern = re.compile(r'^[a-zA-Z0-9]+-[a-zA-Z0-9]{8}-\d{8}$')
    if not pattern.match(irn):
        return False, "Invalid IRN format"
    
    # Split and validate components
    parts = irn.split('-')
    if len(parts) != 3:
        return False, "IRN must have three components separated by hyphens"
    
    invoice_number, service_id, timestamp = parts
    
    # Validate invoice number
    if not all(c.isalnum() for c in invoice_number):
        return False, "Invoice number must contain only alphanumeric characters"
    
    # Validate service ID
    if len(service_id) != 8 or not all(c.isalnum() for c in service_id):
        return False, "Service ID must be exactly 8 alphanumeric characters"
    
    # Validate timestamp
    if not timestamp.isdigit() or len(timestamp) != 8:
        return False, "Timestamp must be 8 digits in YYYYMMDD format"
    
    # Check if date is valid
    try:
        year = int(timestamp[0:4])
        month = int(timestamp[4:6])
        day = int(timestamp[6:8])
        date = datetime.datetime(year, month, day)
        
        # Ensure date isn't in the future
        if date > datetime.datetime.now():
            return False, "IRN date cannot be in the future"
    except ValueError:
        return False, "Invalid date in IRN"
    
    return True, None
```

## Invoice Data Structure

The FIRS API requires a specific invoice data structure for validation and submission. The following JSON structure is used for invoice-related API endpoints:

```json
{
  "business_id": "71fcdd6f-3027-487b-ae38-4830b99f1cf5",
  "invoice_reference": "INV001",
  "irn": "INV001-94ND90NR-20250526",
  "invoice_date": "2025-05-26",
  "invoice_type_code": "380",
  "supplier": {
    "id": "71fcdd6f-3027-487b-ae38-4830b99f1cf5",
    "tin": "31569955-0001",
    "name": "MT GARBA GLOBAL VENTURES",
    "address": "123 Tax Avenue, Lagos",
    "email": "info@taxpoynt.com"
  },
  "customer": {
    "id": "212a597c-f04a-459b-b14c-1875921d8ce1",
    "tin": "98765432-0001",
    "name": "Sample Customer Ltd",
    "address": "456 Customer Street, Abuja",
    "email": "customer@example.com"
  },
  "invoice_items": [
    {
      "id": "ITEM001",
      "name": "Consulting Services",
      "quantity": 1,
      "unit_price": 50000.00,
      "total_amount": 50000.00,
      "vat_amount": 7500.00,
      "vat_rate": 7.5
    }
  ],
  "total_amount": 50000.00,
  "vat_amount": 7500.00,
  "currency_code": "NGN"
}
```

### Key Fields

| Field | Description | Validation |
|-------|-------------|------------|
| `business_id` | UUID format business ID | Must be valid UUID4 format |
| `invoice_reference` | Invoice number from accounting system | Alphanumeric |
| `irn` | Invoice Reference Number | Format: InvoiceNumber-ServiceID-YYYYMMDD |
| `invoice_date` | Invoice issue date | Format: YYYY-MM-DD |
| `invoice_type_code` | Type of invoice | Must be valid code from invoice-types endpoint |
| `supplier`/`customer` | Party information | Must include id, tin, name |
| `invoice_items` | Line items | Array of items with quantity, price, tax info |
| `currency_code` | Invoice currency | Must be valid code from currencies endpoint |

## Authentication Requirements

The FIRS API uses a multi-layer authentication approach:

1. **API Key/Secret Authentication**: Basic headers included in all requests
2. **Certificate-Based Authentication**: For secured endpoints
3. **Business ID Verification**: Entity-related operations require proper business registration

### Required Headers

```python
headers = {
    "accept": "*/*",
    "x-api-key": FIRS_API_KEY,
    "x-api-secret": FIRS_API_SECRET,
    "x-timestamp": timestamp,
    "x-request-id": request_id,
    "x-certificate": FIRS_CERTIFICATE_B64,
    "Content-Type": "application/json"
}
```

### Authentication Flow

For protected endpoints, the following authentication flow is required:

1. Authenticate with email/password to obtain access token
2. Include token in Authorization header for subsequent requests
3. Include certificate in x-certificate header

```python
def authenticate(email: str, password: str) -> Dict[str, Any]:
    """Authenticate with FIRS API and get access token."""
    url = f"{FIRS_API_URL}/api/v1/utilities/authenticate"
    payload = {
        "email": email,
        "password": password,
        "business_tin": BUSINESS_TIN,
        "service_id": BUSINESS_SERVICE_ID,
        "request_id": request_id,
        "timestamp": timestamp
    }
    
    response = requests.post(url, json=payload, headers=get_default_headers())
    
    if response.status_code == 200:
        auth_data = response.json()
        if "data" in auth_data and "access_token" in auth_data["data"]:
            access_token = auth_data["data"]["access_token"]
            return {"success": True, "token": access_token}
    
    return {"success": False, "error": "Authentication failed"}
```

## Integration with Odoo

The TaxPoynt eInvoice system integrates with Odoo ERP using a comprehensive field mapping system that transforms Odoo invoice data to the FIRS-required format.

### Odoo to FIRS Field Mapping

| Odoo Field | FIRS Field | Transformation |
|------------|------------|----------------|
| `name` | `invoice_reference` | Direct mapping |
| `invoice_date` | `invoice_date` | Format as YYYY-MM-DD |
| `partner_id.name` | `customer.name` | Direct mapping |
| `partner_id.vat` | `customer.tin` | Extract TIN from VAT field |
| `company_id.name` | `supplier.name` | Direct mapping |
| `company_id.vat` | `supplier.tin` | Extract TIN from VAT field |
| `invoice_line_ids` | `invoice_items` | Transform each line item |
| `currency_id.name` | `currency_code` | Map to ISO code |

### Integration Process

1. Fetch invoice data from Odoo
2. Transform data to FIRS format using OdooUBLTransformer
3. Generate IRN for the invoice
4. Validate invoice data against FIRS reference data
5. Submit invoice to FIRS API (when authentication is resolved)

## Known Limitations

The current implementation has the following limitations:

1. **Entity Lookup**: The FIRS API endpoints for entity lookup require proper business registration and authentication, which is pending resolution.

2. **Invoice Submission**: The actual submission of invoices to FIRS is not yet implemented due to authentication requirements.

3. **UUID Mapping**: The mapping between Service ID (312577) and the UUID format required by the API needs to be confirmed with FIRS.

## Troubleshooting

### Common Issues

1. **"Invalid UUID length" Error**
   - **Cause**: Using Service ID directly instead of UUID format
   - **Solution**: Convert Service ID to proper UUID format before API calls

2. **"Access denied" Error**
   - **Cause**: Missing or invalid authentication
   - **Solution**: Authenticate first and include token in subsequent requests

3. **"This business does not exist" Error**
   - **Cause**: Business not registered with FIRS or incorrect Business ID
   - **Solution**: Verify business registration status with FIRS

### Diagnostic Tools

Use the provided diagnostic tools to troubleshoot API issues:

1. `firs_api_tester_v1.py`: Tests basic reference data endpoints
2. `firs_api_tester_v2.py`: Tests additional endpoints including invoice validation
3. `phase2_demo.py`: Demonstrates working functionality for IRN generation and validation
