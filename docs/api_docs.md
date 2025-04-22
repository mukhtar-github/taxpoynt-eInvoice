### API Documentation
This documents the APIs for interaction, ensuring clarity for developers. It includes:
- **API Endpoints**: Key endpoints like POST /auth/login, POST /integrations, and GET /integrations/{id} are detailed, reflecting the need for authentication and integration management.
- **Request/Response Structures**: Sample payloads like login requests with email and password, and integration creation with client_id and configuration, are provided, aligning with FastAPI's automatic documentation.
- **Authentication Methods**: Uses JWT tokens in Authorization headers, ensuring secure access, as per the authentication details in the thinking trace.
- **Sample Payloads**: Examples like JSON objects for login and integration creation are included, facilitating implementation.

## API Endpoints

### Authentication and Authorization

#### User Management
- `POST /auth/register` - Register a new user account
- `POST /auth/login` - Authenticate user and receive JWT token
- `POST /auth/refresh` - Refresh JWT token
- `POST /auth/password/reset-request` - Request password reset
- `POST /auth/password/reset` - Reset password with token
- `GET /auth/verify/{token}` - Verify email address
- `GET /users/me` - Get current user profile
- `PATCH /users/me` - Update current user profile
- `POST /auth/logout` - Invalidate current token

#### Organization Management
- `POST /organizations` - Create a new organization
- `GET /organizations/{id}` - Get organization details
- `PATCH /organizations/{id}` - Update organization
- `GET /organizations/{id}/users` - List users in organization
- `POST /organizations/{id}/users` - Invite user to organization
- `DELETE /organizations/{id}/users/{user_id}` - Remove user from organization

#### API Keys
- `GET /api-keys` - List API keys for current user
- `POST /api-keys` - Generate new API key
- `DELETE /api-keys/{id}` - Revoke an API key

### Integration Configuration

#### Client Management
- `GET /clients` - List all clients for current organization
- `POST /clients` - Create a new client
- `GET /clients/{id}` - Get client details
- `PATCH /clients/{id}` - Update client
- `DELETE /clients/{id}` - Delete client

#### Integration Management
- `GET /integrations` - List all integrations
- `POST /integrations` - Create a new integration
- `GET /integrations/{id}` - Get integration details
- `PATCH /integrations/{id}` - Update integration configuration
- `DELETE /integrations/{id}` - Delete integration
- `POST /integrations/{id}/test` - Test integration connection
- `GET /integrations/{id}/status` - Check integration status
- `POST /integrations/{id}/clone` - Clone existing integration
- `GET /integrations/{id}/history` - View configuration change history
- `POST /integrations/import` - Import integration configuration
- `GET /integrations/{id}/export` - Export integration configuration

### Invoice Reference Number (IRN)

- `POST /irn/generate` - Generate a single IRN
- `POST /irn/generate-batch` - Generate multiple IRNs in batch
- `GET /irn/{irn}` - Validate and get IRN details
- `GET /irn` - List IRNs with filtering options
- `POST /irn/{irn}/status` - Update IRN status (used, unused, expired)
- `GET /irn/metrics` - Get IRN usage metrics

### Invoice Validation

- `POST /validate/invoice` - Validate single invoice
- `POST /validate/invoices` - Validate batch of invoices
- `GET /validation/rules` - List active validation rules
- `POST /validation/test` - Test invoice against specific rules
- `GET /validation/errors` - List common validation errors

### FIRS System Resources

- `GET /resources/currencies` - Get list of available currencies
- `GET /resources/invoice-types` - Get list of invoice types
- `GET /resources/payment-means` - Get list of payment methods
- `GET /resources/hs-codes` - Get list of product codes
- `GET /resources/services-codes` - Get list of service codes
- `GET /resources/tax-categories` - Get list of tax categories
- `GET /resources/vat-exemptions` - Get list of VAT exemptions

### QR Code and Signing

- `GET /crypto/keys` - Download cryptographic keys
- `POST /invoice/sign` - Sign an invoice and generate QR code
- `POST /invoice/verify` - Verify a signed invoice

### Monitoring and Reporting

- `GET /dashboard/metrics` - Get dashboard metrics overview
- `GET /dashboard/transactions` - Get transaction history
- `GET /dashboard/errors` - Get error logs
- `GET /dashboard/performance` - Get performance metrics
- `POST /reports/generate` - Generate custom report
- `GET /reports` - List available reports
- `GET /reports/{id}` - Get specific report

## Request/Response Examples

### Authentication

#### Register User
```json
// Request
POST /auth/register
{
  "email": "user@example.com",
  "password": "secure_password",
  "first_name": "John",
  "last_name": "Doe",
  "company_name": "Integration Co."
}

// Response
{
  "user_id": "e12d3a45-6789-0b1c-d2e3-f456789abcde",
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "created_at": "2023-06-01T12:00:00Z"
}
```

#### Login
```json
// Request
POST /auth/login
{
  "email": "user@example.com",
  "password": "secure_password"
}

// Response
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### Integration Configuration

#### Create Integration
```json
// Request
POST /integrations
{
  "client_id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "ERP System Integration",
  "description": "Connect client ERP to FIRS",
  "config": {
    "api_url": "https://erp.client.com/api",
    "auth_method": "api_key",
    "api_key": "client_api_key_here",
    "schedule": "daily",
    "timezone": "Africa/Lagos"
  }
}

// Response
{
  "integration_id": "b5ce3a45-6789-0b1c-d2e3-f456789abcde",
  "client_id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "ERP System Integration",
  "status": "configured",
  "created_at": "2023-06-01T14:30:00Z"
}
```

### IRN Generation

#### Generate IRN
```json
// Request
POST /irn/generate
{
  "integration_id": "b5ce3a45-6789-0b1c-d2e3-f456789abcde",
  "invoice_number": "INV001",
  "timestamp": "20240611"
}

// Response
{
  "irn": "INV001-94ND90NR-20240611",
  "status": "unused",
  "generated_at": "2024-06-11T10:15:00Z",
  "valid_until": "2024-06-18T23:59:59Z"
}
```

### Invoice Validation

#### Validate Invoice
```json
// Request
POST /validate/invoice
{
  "business_id": "bb99420d-d6bb-422c-b371-b9f6d6009aae",
  "irn": "INV001-94ND90NR-20240611",
  "issue_date": "2024-06-11",
  "due_date": "2024-07-11",
  "issue_time": "17:59:04",
  "invoice_type_code": "381",
  "payment_status": "PENDING",
  "note": "This is a commercial invoice",
  "document_currency_code": "NGN",
  "accounting_supplier_party": {
    "party_name": "ABC Company Ltd",
    "postal_address": {
      "tin": "12345678-0001",
      "email": "business@email.com",
      "telephone": "+23480254099000",
      "business_description": "Sales of IT equipment",
      "street_name": "123 Lagos Street, Abuja",
      "city_name": "Abuja",
      "postal_zone": "900001",
      "country": "NG"
    }
  },
  "accounting_customer_party": {
    "party_name": "XYZ Corporation",
    "postal_address": {
      "tin": "87654321-0001",
      "email": "buyer@email.com",
      "telephone": "+23480254099001",
      "business_description": "IT Consulting",
      "street_name": "456 Abuja Road, Lagos",
      "city_name": "Lagos",
      "postal_zone": "100001",
      "country": "NG"
    }
  },
  "legal_monetary_total": {
    "line_extension_amount": 40000.00,
    "tax_exclusive_amount": 40000.00,
    "tax_inclusive_amount": 43000.00,
    "payable_amount": 43000.00
  },
  "invoice_line": [
    {
      "hsn_code": "8471.30",
      "product_category": "Electronics",
      "invoiced_quantity": 10,
      "line_extension_amount": 40000.00,
      "item": {
        "name": "Laptop Computers",
        "description": "15-inch Business Laptops",
        "sellers_item_identification": "LP-2024-001"
      },
      "price": {
        "price_amount": 4000.00,
        "base_quantity": 1,
        "price_unit": "NGN per 1"
      }
    }
  ]
}

// Response
{
  "code": 201,
  "data": {
    "ok": true
  }
}
```

### FIRS Resources

#### Get Currencies
```json
// Request
GET /resources/currencies

// Response
[
  {
    "symbol": "₦",
    "name": "Nigerian Naira",
    "symbol_native": "₦",
    "decimal_digits": 2,
    "rounding": 0,
    "code": "NGN",
    "name_plural": "Nigerian nairas"
  },
  {
    "symbol": "$",
    "name": "US Dollar",
    "symbol_native": "$",
    "decimal_digits": 2,
    "rounding": 0,
    "code": "USD",
    "name_plural": "US dollars"
  }
]
```

#### Get Invoice Types
```json
// Request
GET /resources/invoice-types

// Response
[
  {
    "code": "380",
    "value": "Credit Note"
  },
  {
    "code": "381",
    "value": "Commercial Invoice"
  },
  {
    "code": "384",
    "value": "Debit Note"
  }
]
```

## Authentication Methods

### Internal API Authentication

All internal API endpoints require authentication using JWT tokens:

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

Alternatively, API keys can be used for server-to-server integration:

```
X-API-Key: api_key_here
```

### FIRS API Authentication

For communication with the FIRS e-invoicing API, you must include both the API key and secret key in the request headers:

```
X-API-KEY: your_firs_api_key
X-SECRET-KEY: your_firs_secret_key
```

These credentials are assigned to each taxpayer upon successful business enablement.

## Rate Limiting

The API implements rate limiting to protect against abuse:

- Authentication endpoints: 10 requests per minute per IP
- Standard endpoints: 60 requests per minute per user
- Batch operations: 10 requests per minute per user
