# Odoo Integration Implementation

## Overview

This document summarizes the implementation of the Odoo integration for TaxPoynt eInvoice. The integration provides robust connectivity with Odoo ERP systems to facilitate invoice data retrieval and electronic invoice generation.

## Key Components

### 1. Complete OdooRPC Connector Implementation

A comprehensive `OdooConnector` class in `app/services/odoo_connector.py` that handles:
- Authentication with both password and API key support
- Connection state management with auto-reconnection
- Exception handling with specific error types
- Reusable methods for data retrieval

### 2. Authentication with Odoo Instances

The connector implements flexible authentication handling:
- Support for both password and API key authentication methods
- Secure connection management
- Session timeout detection and reconnection logic
- Proper error reporting

### 3. Invoice Data Retrieval Functions

Enhanced invoice retrieval with:
- Comprehensive invoice data including line items and customer details
- Support for filtering by date range and status
- Attachment retrieval capabilities
- Detailed invoice metadata

### 4. Error Handling for Connection Issues

Implemented robust error handling with:
- Custom exception types (`OdooConnectionError`, `OdooAuthenticationError`, `OdooDataError`)
- Detailed error messages
- Automatic reconnection for common errors
- Consistent error response format

### 5. Pagination Support for Large Datasets

Added pagination capabilities with:
- Configurable page size and page number
- Total count and page calculation
- Previous/next page information
- Metadata for client-side pagination UI

## Additional Improvements

- Added search functionality for invoices with various criteria
- Added partner/customer retrieval capabilities
- Improved IRN generation with proper invoice data handling
- Enhanced test connection function with detailed capability reporting

## Implementation Details

The implementation maintains backward compatibility with the existing codebase. It follows best practices for error handling, separation of concerns, and provides a solid foundation for further Odoo integration features.

## Usage Examples

### Connecting to Odoo

```python
from app.services.odoo_connector import OdooConnector
from app.schemas.integration import OdooConfig, OdooAuthMethod

# Configure connection
config = OdooConfig(
    url="https://odoo.example.com",
    database="production_db",
    username="apiuser",
    auth_method=OdooAuthMethod.PASSWORD,
    password="secure_password"
)

# Create connector
connector = OdooConnector(config)

# Authenticate
connector.authenticate()

# Get user info
user_info = connector.get_user_info()
print(f"Connected as: {user_info['name']}")
```

### Retrieving Invoices with Pagination

```python
from datetime import datetime, timedelta
from app.services.odoo_service import fetch_odoo_invoices

# Fetch invoices from the last 30 days
from_date = datetime.utcnow() - timedelta(days=30)
result = fetch_odoo_invoices(
    config=config,
    from_date=from_date,
    include_draft=False,
    page=1,
    page_size=20
)

print(f"Found {result['total']} invoices")
for invoice in result['invoices']:
    print(f"Invoice: {invoice['invoice_number']} - {invoice['amount_total']} {invoice['currency']['name']}")

# Navigate to next page if available
if result['has_next']:
    next_page = result['next_page']
    # Get next page...
```

### Searching for Invoices

```python
from app.services.odoo_service import search_odoo_invoices

# Search for invoices
search_result = search_odoo_invoices(
    config=config,
    search_term="ACME Corporation",
    page=1,
    page_size=10
)

print(f"Found {search_result['total']} matching invoices")
```

### Generating IRN for Odoo Invoice

```python
from app.services.odoo_service import generate_irn_for_odoo_invoice

# Generate IRN
irn_result = generate_irn_for_odoo_invoice(
    config=config,
    invoice_id=12345,
    integration_id="integration_uuid",
    service_id="TAXPNT",
    user_id="user_uuid"
)

if irn_result['success']:
    print(f"IRN generated: {irn_result['irn']}")
else:
    print(f"Error: {irn_result['error']}")
```
