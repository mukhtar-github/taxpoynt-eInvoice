"""
Clover POS Integration Package
Comprehensive integration with Clover POS systems for TaxPoynt eInvoice platform.

This package provides complete Clover POS connectivity including:
- OAuth 2.0 authentication with automatic token refresh
- REST API client for both Clover production and sandbox environments
- Transaction data extraction with Nigerian market adaptations
- FIRS-compliant UBL BIS 3.0 invoice transformation
- Real-time webhook processing
- Multi-merchant and multi-location support

Supported Clover APIs:
- REST API v3 (Orders, Payments, Customers, Inventory)
- OAuth 2.0 Authorization (Production and Sandbox)
- Webhooks (Order and Payment events)

Nigerian Tax Compliance:
- Automatic 7.5% VAT calculation
- TIN validation and default handling
- Currency conversion to NGN
- FIRS-compliant invoice generation

Usage:
    from taxpoynt_platform.external_integrations.business_systems.pos.clover import (
        CloverPOSConnector,
        CloverAuthManager,
        CloverRestClient,
        CloverDataExtractor,
        CloverTransactionTransformer
    )
    
    # Initialize connector
    config = ConnectionConfig(
        merchant_id="your_merchant_id",
        credentials={
            'client_id': 'your_clover_app_id',
            'client_secret': 'your_clover_app_secret',
            'environment': 'sandbox'  # or 'production'
        }
    )
    
    connector = CloverPOSConnector(config)
    
    # Connect and sync transactions
    async with connector:
        sync_result = await connector.sync_transactions()
        print(f"Synced {sync_result.records_successful} transactions")

Features:
- ✅ OAuth 2.0 Authentication with token refresh
- ✅ Dual environment support (sandbox/production)
- ✅ Multi-merchant architecture
- ✅ Rate limiting with intelligent retry logic
- ✅ Comprehensive error handling
- ✅ Nigerian VAT compliance (7.5%)
- ✅ Currency conversion to NGN
- ✅ FIRS UBL BIS 3.0 invoice generation
- ✅ Real-time webhook processing
- ✅ Batch transaction synchronization
- ✅ Health monitoring and connection management

Clover POS System Compatibility:
- Clover Station (All generations)
- Clover Mini
- Clover Flex
- Clover Mobile
- Clover Go
- Clover Virtual Terminal
- Clover Online Ordering

API Endpoints Supported:
- /v3/merchants/{mId}/orders
- /v3/merchants/{mId}/payments
- /v3/merchants/{mId}/customers
- /v3/merchants/{mId}/items
- /v3/merchants/{mId}/inventory
- /v3/merchants/{mId}
- /oauth/token (Authentication)
"""

from .connector import CloverPOSConnector
from .auth import CloverAuthManager
from .rest_client import CloverRestClient
from .data_extractor import CloverDataExtractor
from .transaction_transformer import CloverTransactionTransformer
from .exceptions import (
    CloverConnectionError,
    CloverAuthenticationError,
    CloverAPIError,
    CloverRateLimitError,
    CloverValidationError,
    CloverWebhookError,
    create_clover_exception
)

__all__ = [
    # Main connector
    'CloverPOSConnector',
    
    # Core components
    'CloverAuthManager',
    'CloverRestClient',
    'CloverDataExtractor',
    'CloverTransactionTransformer',
    
    # Exceptions
    'CloverConnectionError',
    'CloverAuthenticationError',
    'CloverAPIError',
    'CloverRateLimitError',
    'CloverValidationError',
    'CloverWebhookError',
    'create_clover_exception'
]

# Package metadata
__version__ = '1.0.0'
__author__ = 'TaxPoynt Development Team'
__description__ = 'Clover POS integration for TaxPoynt eInvoice platform'

# Clover-specific configuration
CLOVER_CONFIG = {
    'api_version': 'v3',
    'supported_environments': ['sandbox', 'production'],
    'base_urls': {
        'sandbox': 'https://sandbox-dev.clover.com',
        'production': 'https://api.clover.com'
    },
    'oauth_urls': {
        'sandbox': 'https://sandbox-dev.clover.com/oauth',
        'production': 'https://www.clover.com/oauth'
    },
    'rate_limits': {
        'default': 1000,  # requests per hour per merchant
        'burst': 20      # requests per minute
    },
    'webhook_events': [
        'ORDER_CREATED',
        'ORDER_UPDATED',
        'ORDER_DELETED',
        'PAYMENT_CREATED',
        'PAYMENT_UPDATED',
        'PAYMENT_DELETED',
        'INVENTORY_UPDATED',
        'MERCHANT_UPDATED'
    ]
}

# Nigerian market compliance settings
NIGERIAN_COMPLIANCE = {
    'vat_rate': 0.075,  # 7.5% VAT
    'currency': 'NGN',
    'default_tin': '00000000-0001',
    'supported_payment_methods': [
        'cash',
        'credit_card',
        'debit_card',
        'bank_transfer',
        'mobile_money'
    ]
}

# Feature matrix
FEATURES = {
    'authentication': {
        'oauth2': True,
        'token_refresh': True,
        'multi_merchant': True,
        'sandbox_support': True
    },
    'data_extraction': {
        'orders': True,
        'payments': True,
        'customers': True,
        'inventory': True,
        'real_time': True,
        'batch_sync': True
    },
    'tax_compliance': {
        'nigerian_vat': True,
        'tin_validation': True,
        'currency_conversion': True,
        'firs_compliance': True
    },
    'integration': {
        'webhooks': True,
        'rest_api': True,
        'rate_limiting': True,
        'error_handling': True,
        'health_monitoring': True
    }
}