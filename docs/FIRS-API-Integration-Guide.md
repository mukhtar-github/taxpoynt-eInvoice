# FIRS API Integration Guide

## Overview

This document provides comprehensive documentation for integrating with the Federal Inland Revenue Service (FIRS) e-Invoice API. It covers all available endpoints, authentication requirements, request/response formats, and implementation guidelines for the TaxPoynt eInvoice system.

> **Updated: May 21, 2025** - Added documentation for Odoo integration, new submission endpoints, performance monitoring, and testing UI.

## Base URL

- **Sandbox Environment**: `https://eivc-k6z6d.ondigitalocean.app`
- **Production Environment**: *(To be provided by FIRS)*

## Authentication

All API requests require authentication using API keys in the headers:

```
x-api-key: {{API_KEY}}
x-api-secret: {{API_SECRET}}
```

Some endpoints also require user authentication via a JWT token, which can be obtained using the authentication endpoint. This token is included in the `Authorization` header as a Bearer token.

### Authentication Endpoint

**POST** `/api/v1/utilities/authenticate`

#### Request Body

```json
{
  "email": "user_email@example.com",
  "password": "user_password"
}
```

#### Response

```json
{
  "status": "success",
  "message": "Authentication successful",
  "data": {
    "user_id": "user-id-string",
    "access_token": "jwt-token-string",
    "token_type": "Bearer",
    "expires_in": 3600,
    "issued_at": "2023-09-01T12:00:00Z",
    "user": {
      "id": "user-id-string",
      "email": "user_email@example.com",
      "name": "User Name",
      "role": "user-role"
    }
  }
}
```

## API Endpoints

### Health Check

**GET** `/api`

Checks if the API is operational.

#### Response

```json
{
  "healthy": true
}
```

### Entity Management

#### Search Entities

**GET** `/api/v1/entity`

Search for entities with pagination and filtering options.

##### Query Parameters

- `size`: Number of results per page (default: 20)
- `page`: Page number (default: 1)
- `sort_by`: Field to sort by (default: created_at)
- `sort_direction_desc`: Whether to sort descending (default: true)
- `reference`: Search by reference value

##### Response

```json
{
  "code": 200,
  "data": {
    "items": [
      {
        "id": "entity-id",
        "reference": "entity-reference",
        "name": "Entity Name",
        "tin": "TIN-number",
        "created_at": "2023-09-01T12:00:00Z"
      }
    ],
    "pagination": {
      "total_items": 100,
      "total_pages": 5,
      "current_page": 1,
      "size": 20
    }
  },
  "message": "Entities retrieved successfully"
}
```

#### Get Entity by ID

**GET** `/api/v1/entity/{ENTITY_ID}`

Retrieves a specific entity by its ID.

##### Path Parameters

- `ENTITY_ID`: The unique identifier of the entity

##### Response

```json
{
  "code": 200,
  "data": {
    "id": "entity-id",
    "reference": "entity-reference",
    "name": "Entity Name",
    "tin": "TIN-number",
    "email": "entity@example.com",
    "telephone": "+2348012345678",
    "business_description": "Entity business description",
    "address": {
      "street_name": "123 Main Street",
      "city_name": "Lagos",
      "postal_zone": "100001",
      "country": "NG"
    },
    "created_at": "2023-09-01T12:00:00Z"
  },
  "message": "Entity retrieved successfully"
}
```

### Party Management

#### Create Party

**POST** `/api/v1/invoice/party`

Creates a new business party in the system.

##### Request Body

```json
{
  "business_id": "business-uuid",
  "party_name": "Company Name",
  "postal_address_id": "address-uuid",
  "tin": "TIN-12345678",
  "email": "business@example.com",
  "telephone": "+2348012345678",
  "business_description": "Description of business activities"
}
```

Alternatively, instead of `postal_address_id`, you can provide address details directly:

```json
{
  "business_id": "business-uuid",
  "party_name": "Company Name",
  "tin": "TIN-12345678",
  "email": "business@example.com",
  "telephone": "+2348012345678",
  "business_description": "Description of business activities",
  "postal_address": {
    "street_name": "123 Main Street",
    "city_name": "Lagos",
    "postal_zone": "100001",
    "country": "NG"
  }
}
```

##### Response

```json
{
  "code": 201,
  "data": {
    "id": "party-uuid",
    "business_id": "business-uuid",
    "party_name": "Company Name",
    "tin": "TIN-12345678",
    "email": "business@example.com",
    "created_at": "2023-09-01T12:00:00Z"
  },
  "message": "Party created successfully"
}
```

#### Get Party by ID

**GET** `/api/v1/invoice/party/{PARTY_ID}`

Retrieves party details by ID.

##### Path Parameters

- `PARTY_ID`: The unique identifier of the party

##### Response

```json
{
  "code": 200,
  "data": {
    "id": "party-uuid",
    "business_id": "business-uuid",
    "party_name": "Company Name",
    "tin": "TIN-12345678",
    "email": "business@example.com",
    "telephone": "+2348012345678",
    "business_description": "Description of business activities",
    "postal_address": {
      "id": "address-uuid",
      "street_name": "123 Main Street",
      "city_name": "Lagos",
      "postal_zone": "100001",
      "country": "NG"
    },
    "created_at": "2023-09-01T12:00:00Z"
  },
  "message": "Party retrieved successfully"
}
```

### Invoice Management

#### Validate IRN

**POST** `/api/v1/invoice/irn/validate`

Validates an Invoice Reference Number (IRN).

##### Request Body

```json
{
  "business_id": "business-uuid",
  "invoice_reference": "INV001",
  "irn": "INV001-F3A3A0CF-20240619"
}
```

##### Response

```json
{
  "code": 200,
  "data": {
    "valid": true,
    "irn": "INV001-F3A3A0CF-20240619",
    "invoice_reference": "INV001",
    "business_id": "business-uuid"
  },
  "message": "IRN validation successful"
}
```

#### Validate Invoice

**POST** `/api/v1/invoice/validate`

Validates a complete invoice against FIRS rules without submitting it.

##### Request Body

*Complete invoice object following FIRS specification. See the example below.*

```json
{
  "business_id": "business-uuid",
  "irn": "ITW006-F3A3A0CF-20240703",
  "issue_date": "2024-05-14",
  "due_date": "2024-06-14",
  "issue_time": "17:59:04",
  "invoice_type_code": "396",
  "payment_status": "PENDING",
  "document_currency_code": "NGN",
  "accounting_supplier_party": {
    "party_name": "Supplier Company",
    "tin": "TIN-0099990001",
    "email": "supplier@example.com",
    "telephone": "+2348012345678",
    "postal_address": {
      "street_name": "123 Supplier Street",
      "city_name": "Lagos",
      "postal_zone": "100001",
      "country": "NG"
    }
  },
  "accounting_customer_party": {
    "party_name": "Customer Company",
    "tin": "TIN-000001",
    "email": "customer@example.com",
    "telephone": "+2348087654321",
    "postal_address": {
      "street_name": "456 Customer Avenue",
      "city_name": "Abuja",
      "postal_zone": "900001",
      "country": "NG"
    }
  },
  "legal_monetary_total": {
    "line_extension_amount": 340.50,
    "tax_exclusive_amount": 400,
    "tax_inclusive_amount": 430,
    "payable_amount": 430
  },
  "invoice_line": [
    {
      "hsn_code": "CC-001",
      "product_category": "Food and Beverages",
      "dicount_rate": 2.01,
      "dicount_amount": 3500,
      "fee_rate": 1.01,
      "fee_amount": 50,
      "invoiced_quantity": 15,
      "line_extension_amount": 30,
      "item": {
        "name": "Item Name",
        "description": "Item Description",
        "sellers_item_identification": "ITEM-001"
      },
      "price": {
        "price_amount": 10,
        "base_quantity": 3,
        "price_unit": "NGN per 1"
      }
    }
  ]
}
```

##### Response

```json
{
  "code": 200,
  "data": {
    "valid": true,
    "irn": "ITW006-F3A3A0CF-20240703",
    "validation_details": {
      "structure_valid": true,
      "tax_calculations_valid": true,
      "line_items_valid": true
    }
  },
  "message": "Invoice validation successful"
}
```

#### Sign Invoice

**POST** `/api/v1/invoice/sign`

Signs an invoice using FIRS API, generating a Cryptographic Stamp ID (CSID).

##### Request Body

*Complete invoice object following FIRS specification. Same format as Validate Invoice.*

##### Response

```json
{
  "code": 200,
  "data": {
    "irn": "ITW006-F3A3A0CF-20240703",
    "csid": "FIRS-CSID-123456789",
    "signed_at": "2023-09-01T12:00:00Z",
    "status": "SIGNED"
  },
  "message": "Invoice signed successfully"
}
```

#### Download Invoice

**GET** `/api/v1/invoice/download/{IRN}`

Downloads a signed invoice PDF.

##### Path Parameters

- `IRN`: The Invoice Reference Number

##### Response

```json
{
  "code": 200,
  "data": {
    "irn": "ITW006-F3A3A0CF-20240703",
    "pdf_content": "base64-encoded-pdf-data",
    "file_name": "Invoice-ITW006-F3A3A0CF-20240703.pdf"
  },
  "message": "Invoice downloaded successfully"
}
```

#### Confirm Invoice

**GET** `/api/v1/invoice/confirm/{IRN}`

Confirms an invoice in the FIRS system.

##### Path Parameters

- `IRN`: The Invoice Reference Number

##### Response

```json
{
  "code": 200,
  "data": {
    "irn": "ITW006-F3A3A0CF-20240703",
    "status": "CONFIRMED",
    "confirmed_at": "2023-09-01T12:00:00Z"
  },
  "message": "Invoice confirmed successfully"
}
```

#### Search Invoices

**GET** `/api/v1/invoice/{BUSINESS_ID}`

Searches for invoices for a specific business with pagination and filtering.

##### Path Parameters

- `BUSINESS_ID`: The business ID to search invoices for

##### Query Parameters

- `size`: Number of results per page (default: 20)
- `page`: Page number (default: 1)
- `sort_by`: Field to sort by (default: created_at)
- `sort_direction_desc`: Whether to sort descending (default: true)
- `irn`: Filter by IRN
- `payment_status`: Filter by payment status (e.g., "PENDING", "PAID")
- `invoice_type_code`: Filter by invoice type code
- `issue_date`: Filter by issue date
- `due_date`: Filter by due date

##### Response

```json
{
  "code": 200,
  "data": {
    "items": [
      {
        "irn": "ITW006-F3A3A0CF-20240703",
        "business_id": "business-uuid",
        "issue_date": "2024-05-14",
        "due_date": "2024-06-14",
        "invoice_type_code": "396",
        "payment_status": "PENDING",
        "document_currency_code": "NGN",
        "legal_monetary_total": {
          "payable_amount": 430
        },
        "status": "SIGNED",
        "created_at": "2023-09-01T12:00:00Z"
      }
    ],
    "pagination": {
      "total_items": 100,
      "total_pages": 5,
      "current_page": 1,
      "size": 20
    }
  },
  "message": "Invoices retrieved successfully"
}
```

#### Update Invoice

**PATCH** `/api/v1/invoice/update/{IRN}`

Updates an existing invoice.

##### Path Parameters

- `IRN`: The Invoice Reference Number

##### Request Body

*Partial invoice object with fields to update*

```json
{
  "payment_status": "PAID",
  "note": "Payment received on 2024-06-01"
}
```

##### Response

```json
{
  "code": 200,
  "data": {
    "irn": "ITW006-F3A3A0CF-20240703",
    "updated_fields": ["payment_status", "note"],
    "updated_at": "2023-09-01T12:00:00Z"
  },
  "message": "Invoice updated successfully"
}
```

### Reference Data

#### Get Countries

**GET** `/api/v1/invoice/resources/countries`

Returns a list of country codes.

##### Response

```json
{
  "code": 200,
  "data": [
    {
      "name": "Nigeria",
      "alpha_2": "NG",
      "alpha_3": "NGA",
      "country_code": "566"
    },
    {
      "name": "Ghana",
      "alpha_2": "GH",
      "alpha_3": "GHA",
      "country_code": "288"
    }
  ],
  "message": "Countries retrieved successfully"
}
```

#### Get Invoice Types

**GET** `/api/v1/invoice/resources/invoice-types`

Returns available invoice type codes.

##### Response

```json
{
  "code": 200,
  "data": [
    {
      "code": "380",
      "name": "Commercial Invoice"
    },
    {
      "code": "381",
      "name": "Credit Note"
    },
    {
      "code": "383",
      "name": "Debit Note"
    },
    {
      "code": "386",
      "name": "Prepayment Invoice"
    },
    {
      "code": "396",
      "name": "Factored Invoice"
    }
  ],
  "message": "Invoice types retrieved successfully"
}
```

#### Get Currencies

**GET** `/api/v1/invoice/resources/currencies`

Returns a list of currency codes.

##### Response

```json
{
  "code": 200,
  "data": [
    {
      "code": "NGN",
      "name": "Nigerian Naira"
    },
    {
      "code": "USD",
      "name": "US Dollar"
    },
    {
      "code": "EUR",
      "name": "Euro"
    }
  ],
  "message": "Currencies retrieved successfully"
}
```

#### Get VAT Exemptions

**GET** `/api/v1/invoice/resources/vat-exemptions`

Returns VAT exemption categories.

##### Response

```json
{
  "code": 200,
  "data": [
    {
      "id": "EXEMPT_GOODS",
      "name": "Exempt Goods",
      "description": "Goods specifically exempted by VAT law"
    },
    {
      "id": "ZERO_RATED",
      "name": "Zero Rated",
      "description": "Zero rated supplies"
    }
  ],
  "message": "VAT exemptions retrieved successfully"
}
```

## Error Handling

All API errors follow a consistent format:

```json
{
  "code": 400,
  "data": null,
  "message": "error has occurred",
  "error": {
    "id": "error-uuid",
    "handler": "handler_name",
    "public_message": "Error message for the client",
    "details": "Additional error details (optional)"
  }
}
```

Common error codes:

- `400` - Bad Request (invalid input)
- `401` - Unauthorized (authentication failed)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found
- `422` - Unprocessable Entity (validation failed)
- `500` - Internal Server Error

## Implementation Guidelines

### Security Considerations

1. **API Keys**: Store API keys securely in environment variables or a secure key management system.
2. **Token Management**: Refresh and store authentication tokens securely.
3. **Error Logging**: Log API errors for debugging but sanitize sensitive data.
4. **TLS**: Always use HTTPS connections.

### Performance Optimization

1. **Connection Pooling**: Reuse HTTP connections when making multiple API calls.
2. **Caching**: Cache reference data (countries, currencies, etc.) to reduce API calls.
3. **Rate Limiting**: Implement rate limiting to avoid hitting API rate limits.

### Testing

1. **Use Sandbox**: Test all integrations in the sandbox environment first.
2. **Test with Valid TIN**: For testing with the FIRS sandbox, use TIN `31569955-0001`.
3. **End-to-End Testing**: Test the complete invoice lifecycle (validate → sign → confirm).

## TaxPoynt Integration Components

### Odoo Integration with FIRS API

TaxPoynt provides a comprehensive integration between Odoo ERP and the FIRS e-Invoice API that follows our phased integration approach, prioritizing ERP systems first. The integration is built on three main components:

1. **OdooUBLTransformer**: Transforms Odoo invoice data to BIS Billing 3.0 UBL XML format
2. **FIRSConnector**: Connects the transformer output to the FIRS API with robust error handling
3. **FIRSService**: Handles direct FIRS API communication with sandbox/production environment support

#### API Endpoints for Odoo Integration

**1. Submit Odoo Invoice**

`POST /api/firs/submit-invoice`

Transforms and submits an Odoo invoice to the FIRS API.

**Request:**
```json
{
  "odoo_invoice": {
    "id": 12345,
    "name": "INV/2025/00001",
    "invoice_date": "2025-05-21",
    "currency_id": {"id": 1, "name": "NGN"},
    "amount_total": 1000.00,
    "amount_untaxed": 900.00,
    "amount_tax": 100.00,
    "partner_id": {
      "id": 1,
      "name": "Test Customer",
      "vat": "12345678901",
      "street": "Test Street",
      "city": "Test City"
    },
    "company_id": {
      "id": 1,
      "name": "Test Company",
      "vat": "98765432109"
    },
    "invoice_line_ids": [
      {
        "id": 1,
        "name": "Test Product",
        "quantity": 1.0,
        "price_unit": 900.00,
        "tax_ids": [{"id": 1, "name": "VAT 7.5%", "amount": 7.5}],
        "price_subtotal": 900.00,
        "price_total": 1000.00
      }
    ]
  },
  "company_info": {
    "id": 1,
    "name": "TaxPoynt Test Company Ltd",
    "vat": "98765432109",
    "street": "123 Company Street",
    "city": "Lagos",
    "state_id": {"id": 1, "name": "Lagos"},
    "country_id": {"id": 1, "name": "Nigeria"},
    "phone": "+234 1234567890",
    "email": "info@testcompany.com",
    "website": "https://testcompany.com",
    "company_registry": "RC123456",
    "currency_id": {"id": 1, "name": "NGN"}
  },
  "sandbox_mode": true
}
```

**Response:**
```json
{
  "success": true,
  "message": "Invoice submitted successfully",
  "submission_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "validation_issues": [],
  "firs_response": {
    "status": "PROCESSING",
    "timestamp": "2025-05-21T17:32:51+01:00"
  }
}
```

**2. Check Submission Status**

`GET /api/firs/submission-status/{submission_id}`

Checks the status of a submitted invoice.

**Query Parameters:**
- `use_sandbox` (optional): Boolean to override default sandbox setting

**Response:**
```json
{
  "submission_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "status": "COMPLETED",
  "timestamp": "2025-05-21T17:40:22+01:00",
  "message": "Invoice processed successfully",
  "details": {
    "irn": "NGN2025052100001",
    "issue_date": "2025-05-21",
    "processed_at": "2025-05-21T17:40:22+01:00"
  }
}
```

**3. Batch Submit Invoices**

`POST /api/firs/batch-submit`

Submits multiple Odoo invoices in a single batch operation.

**Request:**
Array of invoice submission objects as shown in the single submission example.

**Response:**
```json
{
  "success": true,
  "message": "Batch submitted successfully",
  "batch_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "invoice_count": 2,
  "success_count": 2,
  "failed_count": 0,
  "validation_issues": [],
  "firs_response": {
    "status": "PROCESSING",
    "timestamp": "2025-05-21T17:45:12+01:00"
  }
}
```

### Performance Monitoring

The TaxPoynt integration includes comprehensive monitoring of FIRS API interactions through the `FIRSAPIMonitor` component, which tracks:

- Request timing and performance metrics
- Error tracking and categorization
- Usage statistics for endpoints
- Rate limiting warnings

The monitoring data is available through internal endpoints and can be viewed in the admin dashboard.

### Testing UI

A testing UI is available at `/static/firs-test.html` that allows developers to:

- Submit Odoo invoices to the FIRS API
- Check submission status
- Submit batch operations
- Toggle between sandbox and production modes
- View detailed API responses

## Integration Examples

### Complete Invoice Example

Here's a complete example of an invoice object:

```json
{
  "business_id": "{{BUSINESS_ID}}",
  "irn": "ITW006-F3A3A0CF-20240703",
  "issue_date": "2024-05-14",
  "due_date": "2024-06-14",
  "issue_time": "17:59:04",
  "invoice_type_code": "396",
  "payment_status": "PENDING",
  "note": "This is a test invoice",
  "tax_point_date": "2024-05-14",
  "document_currency_code": "NGN",
  "tax_currency_code": "NGN",
  "accounting_cost": "2000 NGN",
  "buyer_reference": "PO-12345",
  "invoice_delivery_period": {
    "start_date": "2024-06-14",
    "end_date": "2024-06-16"
  },
  "order_reference": "ORD-67890",
  "billing_reference": [
    {
      "irn": "ITW001-E9E0C0D3-20240619",
      "issue_date": "2024-05-14"
    }
  ],
  "accounting_supplier_party": {
    "party_name": "Supplier Company Ltd",
    "tin": "TIN-0099990001",
    "email": "supplier@example.com",
    "telephone": "+2348012345678",
    "business_description": "Supplier of goods and services",
    "postal_address": {
      "street_name": "123 Supplier Street",
      "city_name": "Lagos",
      "postal_zone": "100001",
      "country": "NG"
    }
  },
  "accounting_customer_party": {
    "party_name": "Customer Company",
    "tin": "TIN-000001",
    "email": "customer@example.com",
    "telephone": "+2348087654321",
    "business_description": "Buyer of goods and services",
    "postal_address": {
      "street_name": "456 Customer Avenue",
      "city_name": "Abuja",
      "postal_zone": "900001",
      "country": "NG"
    }
  },
  "actual_delivery_date": "2024-05-14",
  "payment_means": [
    {
      "payment_means_code": "10",
      "payment_due_date": "2024-05-14"
    }
  ],
  "payment_terms_note": "Payment due within 30 days",
  "allowance_charge": [
    {
      "charge_indicator": true,
      "amount": 800.60
    },
    {
      "charge_indicator": false,
      "amount": 10
    }
  ],
  "tax_total": [
    {
      "tax_amount": 56.07,
      "tax_subtotal": [
        {
          "taxable_amount": 800,
          "tax_amount": 8,
          "tax_category": {
            "id": "LOCAL_SALES_TAX",
            "percent": 2.3
          }
        }
      ]
    }
  ],
  "legal_monetary_total": {
    "line_extension_amount": 340.50,
    "tax_exclusive_amount": 400,
    "tax_inclusive_amount": 430,
    "payable_amount": 430
  },
  "invoice_line": [
    {
      "hsn_code": "CC-001",
      "product_category": "Food and Beverages",
      "dicount_rate": 2.01,
      "dicount_amount": 3500,
      "fee_rate": 1.01,
      "fee_amount": 50,
      "invoiced_quantity": 15,
      "line_extension_amount": 30,
      "item": {
        "name": "Product A",
        "description": "High-quality product",
        "sellers_item_identification": "PROD-001"
      },
      "price": {
        "price_amount": 10,
        "base_quantity": 3,
        "price_unit": "NGN per 1"
      }
    },
    {
      "hsn_code": "VV-AX-001",
      "product_category": "Electronics",
      "dicount_rate": 2.01,
      "dicount_amount": 3500,
      "fee_rate": 1.01,
      "fee_amount": 50,
      "invoiced_quantity": 2,
      "line_extension_amount": 100,
      "item": {
        "name": "Product B",
        "description": "Electronic component",
        "sellers_item_identification": "PROD-002"
      },
      "price": {
        "price_amount": 20,
        "base_quantity": 5,
        "price_unit": "NGN per 1"
      }
    }
  ]
}
```

## Changelog

- **September 2023**: Initial documentation
- **May 2024**: Updated with path parameter changes and additional endpoints
