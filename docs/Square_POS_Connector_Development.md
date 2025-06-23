# Square POS Connector Development - Implementation Guide

## Overview

This document provides a comprehensive overview of the Square POS Connector Development implementation, which enhances the TaxPoynt platform with official Square SDK integration, OAuth authentication, and FIRS compliance capabilities.

## Implementation Summary

The Square POS connector has been successfully enhanced with enterprise-ready features including official SDK integration, OAuth flow, and FIRS compliance capabilities for Nigerian e-invoicing requirements.

## 1. Official Square Python SDK Integration ✅

### Features Implemented
- **Square SDK Dependency**: Added `squareup>=21.0.0.20231030` to project requirements
- **API Client Management**: Replaced manual HTTP requests with official Square SDK calls
- **Enhanced Error Handling**: Implemented Square-specific exception handling with `ApiException`
- **Dedicated API Clients**: Separate clients for locations, orders, payments, customers, catalog, and webhooks

### Technical Details
```python
# Initialize Square client with official SDK
self.client = Client(
    access_token=self.access_token,
    environment=self.environment
)

# Get API clients
self.locations_api = self.client.locations
self.orders_api = self.client.orders
self.payments_api = self.client.payments
self.customers_api = self.client.customers
self.catalog_api = self.client.catalog
self.webhooks_api = self.client.webhook_subscriptions
```

### Benefits
- **Reliability**: Official SDK with Square-maintained updates
- **Type Safety**: Better error handling and response validation
- **Future-Proof**: Automatic API version updates and deprecation handling
- **Performance**: Optimized connection management and retry logic

## 2. Square OAuth Implementation ✅

### File: `/backend/app/integrations/pos/square/oauth.py`

### Features Implemented
- **Complete OAuth 2.0 Flow**: Authorization URL generation, token exchange, and refresh
- **CSRF Protection**: State parameter validation for security
- **Token Management**: Automatic token refresh and expiration handling
- **Scope Management**: Required permissions for POS integration

### OAuth Flow Process
1. **Authorization URL Generation**
```python
oauth_manager = SquareOAuthManager(config)
auth_data = await oauth_manager.initiate_oauth_flow(user_id)
# Returns: {"authorization_url": "...", "state": "..."}
```

2. **Token Exchange**
```python
token_info = await oauth_manager.complete_oauth_flow(code, state, user_id)
# Returns: access_token, refresh_token, expires_at, merchant_id
```

3. **Token Refresh**
```python
new_token = await oauth_flow.refresh_access_token(refresh_token)
```

### Required Scopes
- `PAYMENTS_READ` - Read payment information
- `PAYMENTS_WRITE` - Create payments (if needed)
- `ORDERS_READ` - Read order information
- `ORDERS_WRITE` - Create/update orders (if needed)
- `CUSTOMERS_READ` - Read customer information
- `INVENTORY_READ` - Read inventory information
- `MERCHANT_PROFILE_READ` - Read merchant profile
- `ITEMS_READ` - Read catalog items
- `WEBHOOK_SUBSCRIPTION_MANAGEMENT` - Manage webhook subscriptions

### Security Features
- **State Validation**: CSRF protection with secure random states
- **Token Expiration**: 5-minute buffer before token expiry
- **Secure Storage**: Encrypted token storage recommendations
- **URL Validation**: HTTPS-only webhook URLs

## 3. Enhanced Webhook Signature Verification ✅

### Square Webhook Verification Process
Following Square's official specifications:

1. **Combine notification URL + request body**
2. **Create HMAC-SHA1 hash** using webhook signature key
3. **Base64 encode** the hash
4. **Compare** with provided signature using constant-time comparison

### Implementation
```python
async def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
    notification_url = self.webhook_url or ""
    request_body = payload.decode('utf-8')
    
    # Step 1: Combine notification URL with request body
    string_to_sign = notification_url + request_body
    
    # Step 2: Create HMAC-SHA1 hash
    computed_hash = hmac.new(
        self.webhook_signature_key.encode('utf-8'),
        string_to_sign.encode('utf-8'),
        hashlib.sha1
    ).digest()
    
    # Step 3: Base64 encode the hash
    computed_signature = base64.b64encode(computed_hash).decode('utf-8')
    
    # Step 4: Compare signatures using constant-time comparison
    return hmac.compare_digest(signature, computed_signature)
```

### Security Features
- **Constant-time comparison**: Prevents timing attacks
- **Detailed logging**: Security event tracking
- **Error handling**: Graceful failure with logging
- **Synchronous variant**: For non-async contexts

## 4. FIRS Invoice Transformation ✅

### File: `/backend/app/integrations/pos/square/firs_transformer.py`

### Features Implemented
- **Complete Square-to-FIRS transformation**: Convert Square transactions to FIRS-compliant invoices
- **Currency conversion**: USD to NGN with configurable exchange rates
- **Nigerian VAT calculation**: 7.5% VAT with proper rounding
- **FIRS validation**: Comprehensive validation against FIRS requirements

### Transformation Process

#### 1. Transaction Processing
```python
firs_invoice = transformer.transform_transaction_to_firs_invoice(
    transaction, location, customer_info
)
```

#### 2. Currency Conversion
```python
# Convert USD to NGN (configurable exchange rate)
line_extension_amount = Decimal(str(transaction.amount)) * conversion_rate
tax_amount = line_extension_amount * Decimal("0.075")  # 7.5% VAT
```

#### 3. IRN Generation
```python
# Format: InvoiceNumber-ServiceID-YYYYMMDD
invoice_number = f"SQ{transaction_id[:10]}"
irn = f"{invoice_number}-{service_id}-{date.strftime('%Y%m%d')}"
```

### FIRS Compliance Features

#### Required Fields Validation
- `business_id` - TaxPoynt business UUID
- `irn` - Invoice Reference Number
- `issue_date` - Invoice issuance date
- `invoice_type_code` - FIRS invoice type (380 for Commercial Invoice)
- `document_currency_code` - Currency (NGN)
- `accounting_supplier_party` - Seller information
- `accounting_customer_party` - Buyer information
- `legal_monetary_total` - Financial totals
- `invoice_line` - Items or services

#### Business Rule Validation
- **IRN Format**: `InvoiceNumber-ServiceID-YYYYMMDD`
- **TIN Format**: `12345678-0001`
- **Monetary Totals**: Proper tax calculations and relationships
- **Date Validation**: ISO format and logical date relationships

#### Tax Calculation
```python
# Nigerian VAT (7.5%)
tax_rate = Decimal("7.5") / Decimal("100")
tax_amount = line_extension_amount * tax_rate
tax_inclusive_amount = line_extension_amount + tax_amount
```

### Validation Engine
```python
validation_result = transformer.validate_firs_invoice(firs_invoice)
# Returns: {"valid": bool, "errors": [], "warnings": []}
```

## 5. Enhanced Connector Features ✅

### FIRS Invoice Generation
```python
# Generate FIRS invoice from Square transaction
firs_invoice = await connector.generate_firs_invoice(transaction, customer_info)

# Process transaction with automatic invoice generation
result = await connector.process_transaction_with_firs_invoice(
    transaction_data, auto_generate_invoice=True
)
```

### Customer Integration
```python
# Retrieve customer details from Square
customer_info = await connector._get_customer_details(customer_id)
```

### Error Handling
- **Comprehensive logging**: Detailed error tracking and debugging
- **Graceful degradation**: Continue processing even if FIRS generation fails
- **Validation errors**: Clear error messages for validation failures

## Technical Architecture

### File Structure
```
backend/app/integrations/pos/square/
├── __init__.py              # Package exports
├── connector.py             # Main Square connector with SDK integration
├── models.py                # Square-specific data models
├── oauth.py                 # OAuth 2.0 authentication flow
└── firs_transformer.py      # FIRS invoice transformation
```

### Dependencies
```txt
squareup>=21.0.0.20231030    # Official Square Python SDK
```

### Configuration
```python
connection_config = {
    "access_token": "...",
    "application_id": "...",
    "environment": "sandbox|production",
    "webhook_signature_key": "...",
    "location_id": "...",
    "firs_config": {
        "business_id": "...",
        "service_id": "...",
        "tin": "...",
        "business_name": "...",
        "default_currency": "NGN",
        "tax_rate": 7.5
    }
}
```

## Usage Examples

### 1. Initialize Connector
```python
from app.integrations.pos.square import SquarePOSConnector

connector = SquarePOSConnector(connection_config)
await connector.authenticate()
```

### 2. OAuth Flow
```python
from app.integrations.pos.square import SquareOAuthManager

oauth_manager = SquareOAuthManager(oauth_config)

# Start OAuth flow
auth_data = await oauth_manager.initiate_oauth_flow(user_id)
# Redirect user to auth_data["authorization_url"]

# Complete OAuth flow (from callback)
token_info = await oauth_manager.complete_oauth_flow(code, state, user_id)
```

### 3. Process Webhook
```python
# Verify webhook signature
is_valid = await connector.verify_webhook_signature(payload, signature)

if is_valid:
    # Process webhook event
    result = await connector.handle_webhook_event(webhook_data)
```

### 4. Generate FIRS Invoice
```python
# Get transaction
transaction = await connector.get_transaction_by_id(transaction_id)

# Generate FIRS invoice
firs_invoice = await connector.generate_firs_invoice(transaction)

# Validate invoice
validation_result = connector.firs_transformer.validate_firs_invoice(firs_invoice)
```

## Security Considerations

### 1. OAuth Security
- **State validation**: CSRF protection with secure random states
- **Token storage**: Encrypt tokens before database storage
- **Scope limitation**: Request only necessary permissions
- **Token rotation**: Implement automatic token refresh

### 2. Webhook Security
- **Signature verification**: Always verify Square webhook signatures
- **HTTPS only**: Webhook URLs must use HTTPS
- **IP whitelisting**: Consider implementing Square IP range validation
- **Rate limiting**: Implement webhook endpoint rate limiting

### 3. Data Protection
- **PII handling**: Proper handling of customer personal information
- **Data encryption**: Encrypt sensitive data at rest
- **Access logging**: Log all API access for audit purposes
- **Error sanitization**: Don't expose sensitive data in error messages

## Testing Strategy

### 1. Unit Tests
- **OAuth flow testing**: Test authorization URL generation, token exchange
- **Webhook verification**: Test signature validation with known good/bad signatures
- **FIRS transformation**: Test transaction-to-invoice conversion
- **Validation engine**: Test FIRS compliance validation

### 2. Integration Tests
- **Square API integration**: Test with Square sandbox environment
- **End-to-end flow**: Test complete transaction processing
- **Error scenarios**: Test error handling and recovery

### 3. Production Testing
- **Sandbox environment**: Use Square sandbox for development
- **Webhook testing**: Test webhook endpoints with Square webhook testing tools
- **Performance testing**: Load testing for high-volume merchants

## Production Deployment

### 1. Environment Configuration
```bash
# Required environment variables
SQUARE_ACCESS_TOKEN=...
SQUARE_APPLICATION_ID=...
SQUARE_WEBHOOK_SIGNATURE_KEY=...
SQUARE_ENVIRONMENT=production
```

### 2. Database Setup
- **Token storage**: Encrypted token storage table
- **Transaction logging**: Audit trail for all Square transactions
- **FIRS invoice storage**: Store generated invoices for compliance

### 3. Monitoring
- **API rate limits**: Monitor Square API usage
- **Webhook delivery**: Track webhook processing success rates
- **FIRS compliance**: Monitor invoice generation and validation rates
- **Error tracking**: Comprehensive error monitoring and alerting

## Compliance and Certification

### FIRS Compliance
- **Invoice format**: Complies with FIRS e-invoicing specifications
- **Tax calculations**: Accurate Nigerian VAT calculations
- **Validation rules**: Implements all FIRS validation requirements
- **IRN generation**: Proper Invoice Reference Number format

### Square Compliance
- **Official SDK**: Uses Square-approved integration methods
- **OAuth 2.0**: Follows Square OAuth best practices
- **Webhook security**: Implements Square webhook security requirements
- **API versioning**: Supports latest Square API version

## Support and Maintenance

### 1. Documentation
- **API documentation**: Comprehensive API reference
- **Integration guide**: Step-by-step integration instructions
- **Troubleshooting**: Common issues and solutions

### 2. Updates
- **SDK updates**: Regular Square SDK updates
- **API version**: Monitor Square API version changes
- **FIRS updates**: Track FIRS specification changes

### 3. Support Channels
- **Error logging**: Comprehensive error tracking
- **Debug mode**: Detailed logging for development
- **Performance monitoring**: API performance tracking

## Conclusion

The Square POS Connector Development implementation provides a comprehensive, enterprise-ready solution for Square POS integration with full FIRS compliance. The implementation includes:

- **Official Square SDK integration** with proper error handling
- **Complete OAuth 2.0 authentication flow** with security best practices
- **FIRS-compliant invoice transformation** with validation
- **Enhanced webhook processing** with proper signature verification
- **Production-ready features** including monitoring, logging, and error handling

This implementation ensures reliable, secure, and compliant integration between Square POS systems and the TaxPoynt e-invoicing platform, meeting all Nigerian FIRS requirements for electronic invoicing.