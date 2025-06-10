# TaxPoynt CRM & POS Integration - Architectural Approach

## Architecture Overview

The CRM and POS integration architecture will extend the existing TaxPoynt eInvoice platform, maintaining consistency with established patterns while addressing new requirements specific to CRM and POS systems.

## Design Principles

1. **Reuse, Don't Reinvent**: Leverage existing architecture patterns and components wherever possible
2. **Separation of Concerns**: Maintain clear boundaries between system components
3. **Scalability First**: Design for high-volume POS transactions from the beginning
4. **Unified Experience**: Consistent API and UI experiences across integration types
5. **Security by Design**: Ensure secure handling of credentials and data at all stages

## High-Level Architecture

```
                              ┌─────────────────────────────┐
                              │                             │
                              │   TaxPoynt Core Platform    │
                              │                             │
                              └─────────────────┬───────────┘
                                                │
                     ┌──────────────────────────┼──────────────────────────┐
                     │                          │                          │
          ┌──────────▼──────────┐    ┌──────────▼──────────┐    ┌──────────▼──────────┐
          │                     │    │                     │    │                     │
          │  ERP Integration    │    │  CRM Integration    │    │  POS Integration    │
          │                     │    │                     │    │                     │
          └──────────┬──────────┘    └──────────┬──────────┘    └──────────┬──────────┘
                     │                          │                          │
          ┌──────────▼──────────┐    ┌──────────▼──────────┐    ┌──────────▼──────────┐
          │                     │    │                     │    │                     │
          │   Odoo, SAP, etc.   │    │ HubSpot, Salesforce │    │  Square, Toast, etc.│
          │                     │    │                     │    │                     │
          └─────────────────────┘    └─────────────────────┘    └─────────────────────┘
```

## Component Architecture

### 1. Integration Framework Extensions

```
/backend/app/
├── integrations/
│   ├── base/                # Base classes and shared functionality
│   │   ├── connector.py     # Base connector class
│   │   ├── auth.py          # Authentication handler
│   │   └── monitor.py       # Health monitoring
│   │
│   ├── erp/                 # Existing ERP integrations
│   │   └── odoo/            # Odoo connector
│   │
│   ├── crm/                 # New CRM connectors
│   │   ├── hubspot/         # HubSpot implementation
│   │   ├── salesforce/      # Salesforce implementation
│   │   └── pipedrive/       # Pipedrive implementation
│   │
│   └── pos/                 # New POS connectors
│       ├── square/          # Square POS implementation
│       ├── toast/           # Toast POS implementation
│       └── lightspeed/      # Lightspeed POS implementation
```

### 2. Database Schema Extensions

```sql
-- CRM Connection Tables
CREATE TABLE crm_connections (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    organization_id UUID REFERENCES organizations(id),
    crm_type VARCHAR(50) NOT NULL,
    connection_name VARCHAR(255),
    credentials_encrypted TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE crm_deals (
    id UUID PRIMARY KEY,
    crm_connection_id UUID REFERENCES crm_connections(id),
    external_deal_id VARCHAR(255),
    deal_title VARCHAR(255),
    deal_amount DECIMAL(15,2),
    customer_data JSONB,
    deal_stage VARCHAR(100),
    expected_close_date TIMESTAMP,
    invoice_generated BOOLEAN DEFAULT FALSE,
    invoice_id UUID REFERENCES invoices(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- POS Connection Tables
CREATE TABLE pos_connections (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    organization_id UUID REFERENCES organizations(id),
    pos_type VARCHAR(50) NOT NULL,
    location_name VARCHAR(255),
    credentials_encrypted TEXT,
    webhook_url VARCHAR(500),
    webhook_secret VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE pos_transactions (
    id UUID PRIMARY KEY,
    pos_connection_id UUID REFERENCES pos_connections(id),
    external_transaction_id VARCHAR(255),
    transaction_amount DECIMAL(15,2),
    tax_amount DECIMAL(15,2),
    items JSONB,
    customer_data JSONB,
    transaction_timestamp TIMESTAMP,
    invoice_generated BOOLEAN DEFAULT FALSE,
    invoice_transmitted BOOLEAN DEFAULT FALSE,
    invoice_id UUID REFERENCES invoices(id),
    processing_errors JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
) PARTITION BY RANGE (transaction_timestamp);

-- Create monthly partitions for high-volume transaction data
CREATE TABLE pos_transactions_y2025m01 PARTITION OF pos_transactions
    FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');
```

### 3. Queue System Architecture

The system will utilize a multi-level queue to handle different processing priorities:

```
┌───────────────────────┐     ┌───────────────────────┐     ┌───────────────────────┐
│                       │     │                       │     │                       │
│ High-Priority Queue   │     │ Standard Queue        │     │ Batch Processing      │
│ (POS Transactions)    │     │ (CRM Deals)           │     │ (Historical Data)     │
│                       │     │                       │     │                       │
└───────────┬───────────┘     └───────────┬───────────┘     └───────────┬───────────┘
            │                             │                             │
            ▼                             ▼                             ▼
┌───────────────────────┐     ┌───────────────────────┐     ┌───────────────────────┐
│                       │     │                       │     │                       │
│ Workers (5-10)        │     │ Workers (3-5)         │     │ Workers (1-3)         │
│ <2s SLA              │     │ <30s SLA             │     │ No strict SLA         │
│                       │     │                       │     │                       │
└───────────┬───────────┘     └───────────┬───────────┘     └───────────┬───────────┘
            │                             │                             │
            └─────────────────────────────┼─────────────────────────────┘
                                          │
                                          ▼
                             ┌───────────────────────┐
                             │                       │
                             │ Invoice Processing    │
                             │ & Transmission        │
                             │                       │
                             └───────────────────────┘
```

### 4. API Layer Extensions

```python
# FastAPI Router Extensions
router = APIRouter(prefix="/integrations", tags=["integrations"])

# CRM Routes
router.include_router(
    crm_router,
    prefix="/crm",
    tags=["crm-integrations"],
)

# POS Routes
router.include_router(
    pos_router,
    prefix="/pos",
    tags=["pos-integrations"],
)

# CRM-specific routes
crm_router.add_api_route(
    "/{platform}/connect",
    connect_crm_platform,
    methods=["POST"],
    response_model=CRMConnection,
)

# POS-specific routes
pos_router.add_api_route(
    "/{platform}/connect",
    connect_pos_platform,
    methods=["POST"],
    response_model=POSConnection,
)
```

## Security Architecture

### 1. Authentication & Authorization

- OAuth 2.0 flows for all CRM and POS platforms
- Credential encryption using Fernet with key rotation
- Scope-limited API access tokens
- Webhook signature verification for all incoming webhooks

### 2. Credential Management

```python
class SecureCredentialManager:
    """Securely manage integration credentials"""
    
    def encrypt_credentials(self, credentials: dict) -> str:
        """Encrypt credentials for storage"""
        # Uses Fernet symmetric encryption with key rotation
        
    def decrypt_credentials(self, encrypted_data: str) -> dict:
        """Decrypt credentials for use"""
        # Decrypts credentials when needed for API calls
        
    def rotate_encryption_keys(self):
        """Rotate encryption keys periodically"""
        # Implements key rotation schedule
```

## Performance Considerations

### 1. Database Optimizations

- Table partitioning for high-volume POS transaction tables
- Strategic indexing for frequently queried fields
- Read replicas for analytics and reporting queries
- Periodic aggregation of historical data

### 2. Caching Strategy

- Redis caching for frequently accessed CRM data
- Local memory caching for configuration data
- Distributed caching for shared application state

### 3. Rate Limiting & Throttling

- Implement platform-specific rate limit handling
- Adaptive throttling based on API response headers
- Circuit breakers for failing external services

## Monitoring & Observability

The integration will extend the existing monitoring system with:

- Detailed transaction timing metrics
- Integration-specific health checks
- Custom dashboards for CRM and POS systems
- Real-time alerting for processing delays

## Frontend Architecture

The frontend will follow the existing component structure with new integration-specific components:

```
/frontend/components/
├── integrations/
│   ├── common/            # Shared integration components
│   ├── erp/               # ERP integration components
│   ├── crm/               # New CRM components
│   │   ├── HubSpotConnector.tsx
│   │   ├── CRMDashboard.tsx
│   │   ├── DealsList.tsx
│   │   └── CRMSettings.tsx
│   │
│   └── pos/               # New POS components
│       ├── SquareConnector.tsx
│       ├── POSDashboard.tsx
│       ├── TransactionsList.tsx
│       └── RealTimeMonitor.tsx
```

This architecture provides a solid foundation for the CRM and POS integration while maintaining consistency with the existing TaxPoynt platform architecture.
