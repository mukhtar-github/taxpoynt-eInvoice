# Square POS API Documentation

## Overview

This document provides comprehensive API documentation for the Square POS integration endpoints, webhook formats, and testing procedures.

## API Endpoints

### 1. OAuth Authentication

#### Initiate OAuth Flow
```http
GET /api/integrations/pos/square/oauth
```

**Parameters:**
- `organization_id` (required): Organization UUID
- `redirect_uri` (optional): Custom redirect URI

**Response:**
```json
{
  "authorization_url": "https://connect.squareup.com/oauth2/authorize?...",
  "state": "random_state_string"
}
```

#### OAuth Callback
```http
POST /api/integrations/pos/square/oauth/callback
```

**Request Body:**
```json
{
  "code": "oauth_authorization_code",
  "state": "state_parameter",
  "organization_id": "org_uuid"
}
```

**Response:**
```json
{
  "access_token": "encrypted_token",
  "merchant_id": "square_merchant_id",
  "expires_at": "2024-12-31T23:59:59Z"
}
```

### 2. Connection Management

#### Create Square Connection
```http
POST /api/integrations/pos/square/connect
```

**Request Body:**
```json
{
  "organization_id": "org_uuid",
  "connection_name": "Square POS - Main Location",
  "pos_type": "square",
  "credentials": {
    "access_token": "encrypted_token",
    "merchant_id": "merchant_id",
    "location_id": "location_id"
  },
  "webhook_config": {
    "webhook_url": "https://your-domain.com/webhook",
    "webhook_signature_key": "signature_key",
    "subscription_id": "subscription_id"
  }
}
```

**Response:**
```json
{
  "id": "connection_uuid",
  "status": "connected",
  "connection_name": "Square POS - Main Location",
  "created_at": "2024-01-15T10:30:00Z"
}
```

## Webhook Formats

### 1. Payment Created Webhook

```json
{
  "merchant_id": "ML4EG934WYEFS",
  "type": "payment.created",
  "event_id": "event_uuid",
  "created_at": "2024-01-15T10:30:00Z",
  "data": {
    "type": "payment",
    "id": "payment_id",
    "object": {
      "payment": {
        "id": "payment_123",
        "created_at": "2024-01-15T10:30:00Z",
        "updated_at": "2024-01-15T10:30:00Z",
        "amount_money": {
          "amount": 5000,
          "currency": "USD"
        },
        "status": "COMPLETED",
        "location_id": "location_123",
        "order_id": "order_123"
      }
    }
  }
}
```

### 2. Order Updated Webhook

```json
{
  "merchant_id": "ML4EG934WYEFS", 
  "type": "order.updated",
  "event_id": "event_uuid",
  "created_at": "2024-01-15T10:30:00Z",
  "data": {
    "type": "order",
    "id": "order_id",
    "object": {
      "order_updated": {
        "order_id": "order_123",
        "version": 2,
        "location_id": "location_123",
        "state": "COMPLETED"
      }
    }
  }
}
```

## Testing

### Running Tests

```bash
# Navigate to backend directory
cd /home/mukhtar-tanimu/taxpoynt-eInvoice/backend

# Run all POS integration tests
pytest app/tests/integrations/pos -v

# Run specific Square tests
pytest tests/integrations/pos/test_square_connector.py -v
pytest tests/integrations/pos/test_square_oauth.py -v
pytest tests/integrations/pos/test_square_webhooks.py -v
pytest tests/integrations/pos/test_square_transactions.py -v
```