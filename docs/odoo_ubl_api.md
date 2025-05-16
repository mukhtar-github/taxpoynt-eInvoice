# Odoo UBL API Documentation

This document provides comprehensive information about the Odoo UBL API endpoints, which enable testing and usage of the Odoo to BIS Billing 3.0 UBL mapping functionality.

## Overview

The Odoo UBL API provides endpoints for:
- Testing connections to Odoo servers
- Retrieving invoices from Odoo
- Mapping Odoo invoices to BIS Billing 3.0 UBL format
- Generating UBL XML documents
- Batch processing multiple invoices

These endpoints are specifically designed for testing the UBL mapping functionality with real Odoo connections.

## Base URL

All endpoints are prefixed with: `/api/v1/odoo-ubl`

## Authentication

All endpoints require authentication. The API supports:
- Bearer token authentication (JWT)
- API key authentication

Include one of the following headers with your requests:
- `Authorization: Bearer {token}`
- `X-API-Key: {api_key}`

## Endpoints

### Test Connection

Tests connectivity to an Odoo server and verifies UBL mapping capabilities.

```
GET /test-connection
```

#### Query Parameters

| Parameter | Type   | Required | Description                                   |
|-----------|--------|----------|-----------------------------------------------|
| host      | string | Yes      | Odoo host URL                                 |
| db        | string | Yes      | Odoo database name                            |
| user      | string | Yes      | Odoo username                                 |
| password  | string | No*      | Odoo password (use this or api_key)           |
| api_key   | string | No*      | Odoo API key (use this or password)           |

* At least one of `password` or `api_key` must be provided.

#### Response

```json
{
  "success": true,
  "message": "Connection successful",
  "data": {
    "odoo_version": "16.0",
    "user": "admin",
    "company_info": {
      "name": "Test Company Ltd",
      "vat": "NG987654321",
      "country_id": {"code": "NG", "name": "Nigeria"}
    }
  },
  "ubl_mapping_status": "available",
  "ubl_mapping_version": "BIS Billing 3.0",
  "ubl_schema_validation": true
}
```

### Get Invoices

Retrieves invoices from an Odoo server with UBL mapping capability information.

```
GET /invoices
```

#### Query Parameters

| Parameter     | Type    | Required | Default | Description                       |
|---------------|---------|----------|---------|-----------------------------------|
| host          | string  | Yes      |         | Odoo host URL                     |
| db            | string  | Yes      |         | Odoo database name                |
| user          | string  | Yes      |         | Odoo username                     |
| password      | string  | No*      |         | Odoo password                     |
| api_key       | string  | No*      |         | Odoo API key                      |
| from_date     | string  | No       |         | Start date (YYYY-MM-DD)           |
| to_date       | string  | No       |         | End date (YYYY-MM-DD)             |
| include_draft | boolean | No       | false   | Include draft invoices            |
| page          | integer | No       | 1       | Page number                       |
| page_size     | integer | No       | 10      | Number of items per page (max 100)|

* At least one of `password` or `api_key` must be provided.

#### Response

```json
{
  "status": "success",
  "data": [
    {
      "id": 1234,
      "number": "INV/2023/001",
      "date": "2023-05-31",
      "ubl_mapping_available": true,
      "ubl_endpoints": {
        "details": "/api/v1/odoo-ubl/invoices/1234",
        "ubl": "/api/v1/odoo-ubl/invoices/1234/ubl",
        "xml": "/api/v1/odoo-ubl/invoices/1234/ubl/xml"
      }
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 10,
    "total_pages": 1,
    "total_items": 1
  },
  "ubl_mapping": {
    "status": "available",
    "version": "BIS Billing 3.0"
  }
}
```

### Get Invoice Details

Retrieves details of a specific invoice from an Odoo server.

```
GET /invoices/{invoice_id}
```

#### Path Parameters

| Parameter  | Type    | Description       |
|------------|---------|-------------------|
| invoice_id | integer | Odoo invoice ID   |

#### Query Parameters

| Parameter | Type   | Required | Description                       |
|-----------|--------|----------|-----------------------------------|
| host      | string | Yes      | Odoo host URL                     |
| db        | string | Yes      | Odoo database name                |
| user      | string | Yes      | Odoo username                     |
| password  | string | No*      | Odoo password                     |
| api_key   | string | No*      | Odoo API key                      |

* At least one of `password` or `api_key` must be provided.

#### Response

```json
{
  "status": "success",
  "data": {
    "id": 1234,
    "number": "INV/2023/001",
    "date": "2023-05-31",
    "due_date": "2023-06-30",
    "partner_id": {
      "name": "Test Customer",
      "vat": "NG123456789"
    },
    "amount_untaxed": 1500.0,
    "amount_tax": 112.5,
    "amount_total": 1612.5
  },
  "ubl_mapping": {
    "available": true,
    "endpoints": {
      "ubl": "/api/v1/odoo-ubl/invoices/1234/ubl",
      "xml": "/api/v1/odoo-ubl/invoices/1234/ubl/xml"
    }
  }
}
```

### Map Invoice to UBL

Maps an Odoo invoice to BIS Billing 3.0 UBL format.

```
GET /invoices/{invoice_id}/ubl
```

#### Path Parameters

| Parameter  | Type    | Description     |
|------------|---------|-----------------|
| invoice_id | integer | Odoo invoice ID |

#### Query Parameters

| Parameter       | Type    | Required | Default | Description                       |
|-----------------|---------|----------|---------|-----------------------------------|
| host            | string  | Yes      |         | Odoo host URL                     |
| db              | string  | Yes      |         | Odoo database name                |
| user            | string  | Yes      |         | Odoo username                     |
| password        | string  | No*      |         | Odoo password                     |
| api_key         | string  | No*      |         | Odoo API key                      |
| validate_schema | boolean | No       | true    | Validate the UBL against schema   |

* At least one of `password` or `api_key` must be provided.

#### Response

```json
{
  "status": "success",
  "data": {
    "success": true,
    "ubl_id": "ubl_1234",
    "invoice_number": "INV/2023/001",
    "ubl_object": {
      "invoice_number": "INV/2023/001",
      "issue_date": "2023-05-31",
      "due_date": "2023-06-30",
      "monetary_total": {
        "tax_exclusive_amount": 1500.0,
        "tax_inclusive_amount": 1612.5,
        "payable_amount": 1612.5
      }
    },
    "validation": {
      "valid": true,
      "warnings": []
    }
  },
  "message": "Invoice successfully mapped to UBL format"
}
```

### Get UBL XML

Gets the UBL XML for an Odoo invoice.

```
GET /invoices/{invoice_id}/ubl/xml
```

#### Path Parameters

| Parameter  | Type    | Description     |
|------------|---------|-----------------|
| invoice_id | integer | Odoo invoice ID |

#### Query Parameters

| Parameter       | Type    | Required | Default | Description                       |
|-----------------|---------|----------|---------|-----------------------------------|
| host            | string  | Yes      |         | Odoo host URL                     |
| db              | string  | Yes      |         | Odoo database name                |
| user            | string  | Yes      |         | Odoo username                     |
| password        | string  | No*      |         | Odoo password                     |
| api_key         | string  | No*      |         | Odoo API key                      |
| validate_schema | boolean | No       | true    | Validate the UBL against schema   |

* At least one of `password` or `api_key` must be provided.

#### Response

Returns the XML content directly with:
- Content-Type: `application/xml`
- Content-Disposition: `attachment; filename=invoice_{id}_{timestamp}.xml`

### Batch Process Invoices

Batch processes multiple Odoo invoices, mapping them to UBL format.

```
POST /batch-process
```

#### Request Body

```json
{
  "host": "https://odoo.example.com",
  "db": "test_db",
  "user": "test_user",
  "password": "test_password",
  "from_date": "2023-01-01",
  "to_date": "2023-12-31",
  "include_draft": false,
  "page": 1,
  "page_size": 10
}
```

| Parameter     | Type    | Required | Default | Description                       |
|---------------|---------|----------|---------|-----------------------------------|
| host          | string  | Yes      |         | Odoo host URL                     |
| db            | string  | Yes      |         | Odoo database name                |
| user          | string  | Yes      |         | Odoo username                     |
| password      | string  | No*      |         | Odoo password                     |
| api_key       | string  | No*      |         | Odoo API key                      |
| from_date     | string  | No       |         | Start date (YYYY-MM-DD)           |
| to_date       | string  | No       |         | End date (YYYY-MM-DD)             |
| include_draft | boolean | No       | false   | Include draft invoices            |
| page          | integer | No       | 1       | Page number                       |
| page_size     | integer | No       | 10      | Number of items per page (max 100)|

* At least one of `password` or `api_key` must be provided.

#### Response

```json
{
  "status": "success",
  "processed_count": 2,
  "success_count": 2,
  "error_count": 0,
  "message": "Processed 2 invoices: 2 successful, 0 failed",
  "invoices": [
    {
      "invoice_id": 1234,
      "invoice_number": "INV/2023/001",
      "success": true,
      "errors": [],
      "warnings": [],
      "ubl_id": "ubl_1234"
    },
    {
      "invoice_id": 1235,
      "invoice_number": "INV/2023/002",
      "success": true,
      "errors": [],
      "warnings": [],
      "ubl_id": "ubl_1235"
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 10,
    "total_pages": 1,
    "total_items": 2
  }
}
```

## Error Responses

All endpoints follow a consistent error response format:

```json
{
  "status": "error",
  "message": "Error message",
  "code": "ERROR_CODE",
  "details": {
    "field": "Additional error information"
  }
}
```

### Common Error Codes

| Status Code | Error Code           | Description                               |
|-------------|----------------------|-------------------------------------------|
| 400         | INVALID_PARAMETERS   | Invalid or missing required parameters    |
| 401         | UNAUTHORIZED         | Authentication failed                     |
| 404         | INVOICE_NOT_FOUND    | Invoice not found                         |
| 422         | VALIDATION_ERROR     | UBL validation error                      |
| 500         | SERVER_ERROR         | Internal server error                     |
| 503         | ODOO_UNAVAILABLE     | Odoo server unavailable                   |

## Validation Errors

When mapping fails due to validation errors, the response will include detailed validation information:

```json
{
  "status": "error",
  "message": "Failed to map invoice to UBL format",
  "errors": [
    {
      "code": "MISSING_REQUIRED_FIELD",
      "field": "invoice_date",
      "message": "Invoice date is required"
    },
    {
      "code": "INVALID_FORMAT",
      "field": "vat",
      "message": "VAT number format is invalid"
    }
  ],
  "warnings": [
    {
      "code": "OPTIONAL_FIELD_MISSING",
      "field": "delivery_address",
      "message": "Delivery address is missing"
    }
  ]
}
```
