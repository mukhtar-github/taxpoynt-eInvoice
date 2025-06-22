# TaxPoynt CRM Integration API Documentation

## Overview

The TaxPoynt CRM Integration API provides comprehensive functionality for connecting Customer Relationship Management (CRM) systems to the e-invoicing platform. This API supports automatic invoice generation from CRM deals, real-time synchronization, and webhook-based event processing.

## Table of Contents

1. [Authentication](#authentication)
2. [Base URL](#base-url)
3. [Data Models](#data-models)
4. [CRM Connection Endpoints](#crm-connection-endpoints)
5. [Deal Management Endpoints](#deal-management-endpoints)
6. [Webhook Endpoints](#webhook-endpoints)
7. [Error Handling](#error-handling)
8. [Rate Limiting](#rate-limiting)
9. [Examples](#examples)

## Authentication

All API endpoints require authentication using JWT Bearer tokens.

```http
Authorization: Bearer {access_token}
```

## Base URL

```
Production: https://api.taxpoynt.com/api/v1/crm
Development: http://localhost:8000/api/v1/crm
```

## Data Models

### CRMConnection

Represents a connection to a CRM system.

```json
{
  "id": "uuid",
  "organization_id": "uuid",
  "crm_type": "hubspot | salesforce | pipedrive | zoho",
  "connection_name": "string",
  "credentials": {
    "client_id": "string",
    "client_secret": "encrypted_string",
    "refresh_token": "encrypted_string",
    "access_token": "encrypted_string"
  },
  "connection_settings": {
    "auto_sync": "boolean",
    "sync_frequency": "hourly | daily | weekly",
    "deal_stage_mapping": {
      "closedwon": "generate_invoice",
      "proposal": "create_draft"
    },
    "auto_generate_invoice_on_creation": "boolean",
    "default_currency": "NGN | USD | EUR | GBP",
    "webhook_events": ["deal.creation", "deal.propertyChange"]
  },
  "status": "pending | connecting | connected | failed | disconnected",
  "webhook_url": "string",
  "webhook_secret": "string",
  "last_sync": "datetime",
  "total_deals": "integer",
  "total_invoices": "integer",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### CRMDeal

Represents a deal from a CRM system.

```json
{
  "id": "uuid",
  "connection_id": "uuid",
  "external_deal_id": "string",
  "deal_title": "string",
  "deal_amount": "decimal_string",
  "deal_stage": "string",
  "deal_currency": "string",
  "customer_data": {
    "name": "string",
    "email": "string",
    "phone": "string",
    "company": "string",
    "address": {
      "street": "string",
      "city": "string",
      "state": "string",
      "country": "string",
      "postal_code": "string"
    }
  },
  "deal_data": {
    "source": "string",
    "owner": "string",
    "probability": "number",
    "expected_close_date": "datetime",
    "custom_fields": {}
  },
  "invoice_generated": "boolean",
  "invoice_data": {
    "invoice_number": "string",
    "invoice_id": "uuid",
    "generated_at": "datetime"
  },
  "created_at_source": "datetime",
  "updated_at_source": "datetime",
  "last_sync": "datetime",
  "sync_status": "success | failed | pending"
}
```

### DealProcessingRequest

Request payload for processing deals into invoices.

```json
{
  "action": "generate_invoice | create_draft | validate_only",
  "force_regenerate": "boolean",
  "invoice_settings": {
    "currency": "NGN | USD | EUR | GBP",
    "due_days": "integer",
    "tax_rate": "number",
    "line_items": [
      {
        "description": "string",
        "quantity": "number",
        "unit_price": "number",
        "tax_rate": "number"
      }
    ]
  }
}
```

### WebhookEvent

Represents a webhook event from CRM systems.

```json
{
  "eventId": "string",
  "subscriptionId": "string",
  "portalId": "integer",
  "appId": "integer",
  "occurredAt": "datetime",
  "subscriptionType": "string",
  "attemptNumber": "integer",
  "objectId": "string",
  "changeSource": "string",
  "changeFlag": "CREATED | UPDATED | DELETED",
  "propertyName": "string",
  "propertyValue": "string"
}
```

## CRM Connection Endpoints

### Create CRM Connection

Creates a new CRM connection for an organization.

```http
POST /api/v1/crm/{organization_id}/connections
```

**Request Body:**
```json
{
  "crm_type": "hubspot",
  "connection_name": "Main HubSpot Account",
  "credentials": {
    "client_id": "your_client_id",
    "client_secret": "your_client_secret",
    "authorization_code": "oauth_auth_code"
  },
  "connection_settings": {
    "auto_sync": true,
    "sync_frequency": "daily",
    "deal_stage_mapping": {
      "closedwon": "generate_invoice",
      "proposal": "create_draft"
    }
  }
}
```

**Response:** `201 Created`
```json
{
  "success": true,
  "data": {
    "connection": { /* CRMConnection object */ },
    "authentication_status": "success",
    "test_connection_result": {
      "success": true,
      "deals_accessible": true,
      "contacts_accessible": true
    }
  }
}
```

### Get CRM Connections

Retrieves all CRM connections for an organization.

```http
GET /api/v1/crm/{organization_id}/connections
```

**Query Parameters:**
- `status` (optional): Filter by connection status
- `crm_type` (optional): Filter by CRM type
- `page` (optional): Page number (default: 1)
- `page_size` (optional): Items per page (default: 20)

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "connections": [ /* Array of CRMConnection objects */ ],
    "pagination": {
      "page": 1,
      "page_size": 20,
      "total": 5,
      "pages": 1,
      "has_next": false,
      "has_prev": false
    }
  }
}
```

### Get CRM Connection

Retrieves a specific CRM connection.

```http
GET /api/v1/crm/{organization_id}/connections/{connection_id}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "connection": { /* CRMConnection object */ },
    "statistics": {
      "total_deals": 150,
      "invoices_generated": 45,
      "last_sync_duration": "00:02:15",
      "sync_success_rate": 98.5
    }
  }
}
```

### Update CRM Connection

Updates an existing CRM connection.

```http
PUT /api/v1/crm/{organization_id}/connections/{connection_id}
```

**Request Body:**
```json
{
  "connection_name": "Updated HubSpot Account",
  "connection_settings": {
    "auto_sync": false,
    "sync_frequency": "weekly"
  }
}
```

**Response:** `200 OK`

### Delete CRM Connection

Deletes a CRM connection and all associated data.

```http
DELETE /api/v1/crm/{organization_id}/connections/{connection_id}
```

**Response:** `204 No Content`

### Test CRM Connection

Tests the connectivity and authentication of a CRM connection.

```http
POST /api/v1/crm/{organization_id}/connections/{connection_id}/test
```

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "connection_status": "success",
    "authentication_valid": true,
    "api_accessible": true,
    "permissions": {
      "deals": "read",
      "contacts": "read",
      "webhooks": "write"
    },
    "test_results": {
      "deals_count": 150,
      "contacts_count": 500,
      "response_time_ms": 250
    }
  }
}
```

## Deal Management Endpoints

### Sync Deals

Synchronizes deals from the CRM system.

```http
POST /api/v1/crm/{organization_id}/connections/{connection_id}/sync
```

**Request Body (Optional):**
```json
{
  "days_back": 30,
  "force_full_sync": false,
  "filters": {
    "deal_stages": ["closedwon", "proposal"],
    "minimum_amount": 1000,
    "updated_since": "2023-12-01T00:00:00Z"
  }
}
```

**Response:** `202 Accepted`
```json
{
  "success": true,
  "data": {
    "sync_job_id": "uuid",
    "status": "queued",
    "estimated_duration": "00:05:00",
    "message": "Sync job has been queued for processing"
  }
}
```

### Get Deals

Retrieves deals from a CRM connection.

```http
GET /api/v1/crm/{organization_id}/connections/{connection_id}/deals
```

**Query Parameters:**
- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 20, max: 100)
- `deal_stage`: Filter by deal stage
- `invoice_generated`: Filter by invoice generation status
- `updated_since`: Filter by last update date
- `search`: Search in deal titles and customer names
- `sort_by`: Sort field (created_at, updated_at, amount)
- `sort_order`: Sort order (asc, desc)

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "deals": [ /* Array of CRMDeal objects */ ],
    "pagination": {
      "page": 1,
      "page_size": 20,
      "total": 150,
      "pages": 8,
      "has_next": true,
      "has_prev": false
    },
    "filters_applied": {
      "deal_stage": "closedwon",
      "invoice_generated": false
    }
  }
}
```

### Get Deal

Retrieves a specific deal.

```http
GET /api/v1/crm/{organization_id}/connections/{connection_id}/deals/{deal_id}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "deal": { /* CRMDeal object */ },
    "invoice_preview": {
      "invoice_number": "HUB-123456789",
      "amount": 50000.00,
      "currency": "NGN",
      "line_items": [ /* Array of line items */ ]
    }
  }
}
```

### Process Deal

Processes a deal (generates invoice, creates draft, etc.).

```http
POST /api/v1/crm/{organization_id}/connections/{connection_id}/deals/{deal_id}/process
```

**Request Body:**
```json
{
  "action": "generate_invoice",
  "force_regenerate": false,
  "invoice_settings": {
    "currency": "NGN",
    "due_days": 30,
    "tax_rate": 7.5
  }
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "processing_result": {
      "action": "generate_invoice",
      "status": "success",
      "invoice_id": "uuid",
      "invoice_number": "HUB-123456789",
      "processing_time_ms": 1500
    },
    "updated_deal": { /* Updated CRMDeal object */ }
  }
}
```

### Batch Process Deals

Processes multiple deals in a batch operation.

```http
POST /api/v1/crm/{organization_id}/connections/{connection_id}/deals/batch-process
```

**Request Body:**
```json
{
  "deal_ids": ["uuid1", "uuid2", "uuid3"],
  "action": "generate_invoice",
  "invoice_settings": {
    "currency": "NGN",
    "due_days": 30
  }
}
```

**Response:** `202 Accepted`
```json
{
  "success": true,
  "data": {
    "batch_job_id": "uuid",
    "status": "queued",
    "total_deals": 3,
    "estimated_duration": "00:01:30"
  }
}
```

### Get Batch Job Status

Retrieves the status of a batch processing job.

```http
GET /api/v1/crm/{organization_id}/batch-jobs/{job_id}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "job_id": "uuid",
    "status": "completed",
    "progress": {
      "total": 3,
      "processed": 3,
      "successful": 2,
      "failed": 1
    },
    "results": [
      {
        "deal_id": "uuid1",
        "status": "success",
        "invoice_id": "uuid"
      },
      {
        "deal_id": "uuid2",
        "status": "success",
        "invoice_id": "uuid"
      },
      {
        "deal_id": "uuid3",
        "status": "failed",
        "error": "Invalid customer data"
      }
    ],
    "completed_at": "2023-12-20T15:30:00Z"
  }
}
```

## Webhook Endpoints

### HubSpot Webhook

Receives and processes HubSpot webhook events.

```http
POST /api/v1/crm/webhook/hubspot/{connection_id}
```

**Headers:**
- `X-HubSpot-Signature`: Webhook signature for verification

**Request Body:**
```json
{
  "events": [
    {
      "eventId": "event-123",
      "subscriptionId": "sub-123",
      "portalId": 12345,
      "appId": 67890,
      "occurredAt": "2023-12-20T15:30:00Z",
      "subscriptionType": "deal.propertyChange",
      "attemptNumber": 1,
      "objectId": "123456789",
      "changeSource": "CRM_UI",
      "changeFlag": "UPDATED",
      "propertyName": "dealstage",
      "propertyValue": "closedwon"
    }
  ]
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "processed_events": 1,
    "failed_events": 0,
    "processing_results": [
      {
        "event_id": "event-123",
        "status": "processed",
        "action_taken": "invoice_generated",
        "invoice_id": "uuid"
      }
    ]
  }
}
```

### Salesforce Webhook

Receives and processes Salesforce webhook events.

```http
POST /api/v1/crm/webhook/salesforce/{connection_id}
```

*Similar structure to HubSpot webhook*

## Error Handling

### Error Response Format

All API errors follow a consistent format:

```json
{
  "success": false,
  "error": {
    "code": "AUTHENTICATION_FAILED",
    "message": "Invalid or expired access token",
    "details": {
      "field": "access_token",
      "reason": "Token has expired"
    },
    "timestamp": "2023-12-20T15:30:00Z",
    "request_id": "uuid"
  }
}
```

### Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `AUTHENTICATION_FAILED` | 401 | Invalid or expired authentication token |
| `AUTHORIZATION_DENIED` | 403 | Insufficient permissions for the operation |
| `RESOURCE_NOT_FOUND` | 404 | Requested resource does not exist |
| `VALIDATION_ERROR` | 422 | Request data validation failed |
| `RATE_LIMIT_EXCEEDED` | 429 | API rate limit exceeded |
| `INTEGRATION_ERROR` | 502 | Error communicating with CRM system |
| `SERVICE_UNAVAILABLE` | 503 | Service temporarily unavailable |

### CRM-Specific Error Codes

| Code | Description |
|------|-------------|
| `CRM_CONNECTION_FAILED` | Failed to connect to CRM system |
| `CRM_AUTHENTICATION_ERROR` | CRM authentication credentials invalid |
| `CRM_RATE_LIMIT` | CRM system rate limit exceeded |
| `CRM_DATA_INVALID` | Invalid data received from CRM |
| `DEAL_NOT_FOUND` | Specified deal not found in CRM |
| `WEBHOOK_VERIFICATION_FAILED` | Webhook signature verification failed |

## Rate Limiting

### Limits

- **General API**: 1000 requests per hour per organization
- **Sync Operations**: 10 requests per hour per connection
- **Webhook Endpoints**: 10000 requests per hour per connection

### Rate Limit Headers

```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1703097600
X-RateLimit-Window: 3600
```

### Rate Limit Exceeded Response

```json
{
  "success": false,
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded. Try again in 3600 seconds.",
    "details": {
      "limit": 1000,
      "remaining": 0,
      "reset_at": "2023-12-20T16:00:00Z"
    }
  }
}
```

## Examples

### Complete HubSpot Integration Flow

#### 1. Create Connection

```bash
curl -X POST "https://api.taxpoynt.com/api/v1/crm/{org_id}/connections" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "crm_type": "hubspot",
    "connection_name": "Primary HubSpot",
    "credentials": {
      "client_id": "your_client_id",
      "client_secret": "your_client_secret",
      "authorization_code": "oauth_code"
    },
    "connection_settings": {
      "auto_sync": true,
      "deal_stage_mapping": {
        "closedwon": "generate_invoice"
      }
    }
  }'
```

#### 2. Sync Deals

```bash
curl -X POST "https://api.taxpoynt.com/api/v1/crm/{org_id}/connections/{conn_id}/sync" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "days_back": 30,
    "filters": {
      "deal_stages": ["closedwon"]
    }
  }'
```

#### 3. Get Deals

```bash
curl -X GET "https://api.taxpoynt.com/api/v1/crm/{org_id}/connections/{conn_id}/deals?deal_stage=closedwon&invoice_generated=false" \
  -H "Authorization: Bearer {token}"
```

#### 4. Process Deal

```bash
curl -X POST "https://api.taxpoynt.com/api/v1/crm/{org_id}/connections/{conn_id}/deals/{deal_id}/process" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "generate_invoice",
    "invoice_settings": {
      "currency": "NGN",
      "due_days": 30
    }
  }'
```

### Webhook Setup Example

#### 1. Configure Webhook in HubSpot

- URL: `https://api.taxpoynt.com/api/v1/crm/webhook/hubspot/{connection_id}`
- Events: `deal.creation`, `deal.propertyChange`
- Secret: Use the `webhook_secret` from your connection

#### 2. Handle Webhook Events

The webhook endpoint will automatically process events according to your connection settings and deal stage mappings.

## SDKs and Libraries

### Python SDK

```python
from taxpoynt_crm import TaxPoyntCRM

# Initialize client
client = TaxPoyntCRM(
    api_key="your_api_key",
    base_url="https://api.taxpoynt.com"
)

# Create connection
connection = client.connections.create(
    organization_id="org_id",
    crm_type="hubspot",
    connection_name="My HubSpot",
    credentials={
        "client_id": "client_id",
        "client_secret": "client_secret"
    }
)

# Sync deals
sync_job = client.deals.sync(
    organization_id="org_id",
    connection_id=connection.id,
    days_back=30
)

# Process deal
result = client.deals.process(
    organization_id="org_id",
    connection_id=connection.id,
    deal_id="deal_id",
    action="generate_invoice"
)
```

### JavaScript SDK

```javascript
import { TaxPoyntCRM } from '@taxpoynt/crm-sdk';

// Initialize client
const client = new TaxPoyntCRM({
  apiKey: 'your_api_key',
  baseUrl: 'https://api.taxpoynt.com'
});

// Create connection
const connection = await client.connections.create({
  organizationId: 'org_id',
  crmType: 'hubspot',
  connectionName: 'My HubSpot',
  credentials: {
    clientId: 'client_id',
    clientSecret: 'client_secret'
  }
});

// Sync deals
const syncJob = await client.deals.sync({
  organizationId: 'org_id',
  connectionId: connection.id,
  daysBack: 30
});

// Process deal
const result = await client.deals.process({
  organizationId: 'org_id',
  connectionId: connection.id,
  dealId: 'deal_id',
  action: 'generate_invoice'
});
```

## Changelog

### v1.2.0 (2023-12-20)
- Added batch processing endpoints
- Enhanced webhook event handling
- Improved error reporting
- Added deal filtering options

### v1.1.0 (2023-11-15)
- Added Salesforce integration support
- Enhanced rate limiting
- Added webhook signature verification
- Improved pagination

### v1.0.0 (2023-10-01)
- Initial release
- HubSpot integration support
- Basic deal management
- Invoice generation from deals

## Support

For API support and questions:
- Email: api-support@taxpoynt.com
- Documentation: https://docs.taxpoynt.com/crm-api
- Status Page: https://status.taxpoynt.com