"""
Toast POS Integration Package
Comprehensive integration with Toast POS systems for TaxPoynt eInvoice platform.

This package provides complete Toast POS connectivity including:
- OAuth 2.0 authentication with automatic token refresh
- REST API client for production and sandbox environments
- Transaction data extraction with Nigerian market adaptations
- FIRS-compliant UBL BIS 3.0 invoice transformation
- Real-time webhook processing
- Multi-restaurant support

Supported Toast APIs:
- REST API v1 (Orders, Checks, Payments, Menu Items, Customers)
- OAuth 2.0 Authorization (Production and Sandbox)
- Webhooks (Order and Check events)

Nigerian Tax Compliance:
- Automatic 7.5% VAT calculation
- TIN validation and default handling
- Currency conversion to NGN
- FIRS-compliant invoice generation

Usage:
    from taxpoynt_platform.external_integrations.business_systems.pos.toast import (
        ToastPOSConnector,
        ToastAuthManager,
        ToastRestClient,
        ToastDataExtractor,
        ToastTransactionTransformer
    )
    
    # Initialize connector
    config = ConnectionConfig(
        restaurant_id="your_restaurant_guid",
        credentials={
            'client_id': 'your_toast_client_id',
            'client_secret': 'your_toast_client_secret',
            'environment': 'sandbox'  # or 'production'
        }
    )
    
    connector = ToastPOSConnector(config)
    
    # Connect and sync transactions
    async with connector:
        sync_result = await connector.sync_transactions()
        print(f"Synced {sync_result.records_successful} transactions")

Features:
- ✅ OAuth 2.0 Authentication with token refresh
- ✅ Dual environment support (sandbox/production)
- ✅ Multi-restaurant architecture
- ✅ Comprehensive error handling
- ✅ Nigerian VAT compliance (7.5%)
- ✅ Currency conversion to NGN
- ✅ FIRS UBL BIS 3.0 invoice generation
- ✅ Real-time webhook processing
- ✅ Batch transaction synchronization
- ✅ Health monitoring and connection management

Toast POS System Compatibility:
- Toast Point of Sale (All versions)
- Toast Kitchen Display System (KDS)
- Toast Online Ordering
- Toast Go (Mobile POS)
- Toast Delivery Services
- Toast Payroll & Team Management

API Endpoints Supported:
- /orders/v1/checks
- /orders/v1/orders
- /orders/v1/payments
- /config/v1/menuItems
- /customers/v1/customers
- /config/v1/restaurants
- /authentication/v1/authentication/login

Restaurant-Specific Features:
- Menu item categorization and modifiers
- Table and server tracking
- Dining option support (Dine In, Takeout, Delivery)
- Tip and gratuity handling
- Discount and promotion tracking
- Multi-location restaurant chains
"""

from .connector import ToastPOSConnector
from .auth import ToastAuthManager
from .rest_client import ToastRestClient
from .data_extractor import ToastDataExtractor
from .transaction_transformer import ToastTransactionTransformer
from .exceptions import (
    ToastConnectionError,
    ToastAuthenticationError,
    ToastAPIError,
    ToastRateLimitError,
    ToastValidationError,
    ToastWebhookError,
    ToastDataExtractionError,
    ToastTransformationError,
    ToastConfigurationError,
    create_toast_exception
)

__all__ = [
    # Main connector
    'ToastPOSConnector',
    
    # Core components
    'ToastAuthManager',
    'ToastRestClient',
    'ToastDataExtractor',
    'ToastTransactionTransformer',
    
    # Exceptions
    'ToastConnectionError',
    'ToastAuthenticationError',
    'ToastAPIError',
    'ToastRateLimitError',
    'ToastValidationError',
    'ToastWebhookError',
    'ToastDataExtractionError',
    'ToastTransformationError',
    'ToastConfigurationError',
    'create_toast_exception'
]

# Package metadata
__version__ = '1.0.0'
__author__ = 'TaxPoynt Development Team'
__description__ = 'Toast POS integration for TaxPoynt eInvoice platform'

# Toast-specific configuration
TOAST_CONFIG = {
    'api_version': 'v1',
    'supported_environments': ['sandbox', 'production'],
    'base_urls': {
        'sandbox': 'https://ws-sandbox-api.toasttab.com',
        'production': 'https://ws-api.toasttab.com'
    },
    'auth_endpoints': {
        'sandbox': 'https://ws-sandbox-api.toasttab.com/authentication/v1/authentication/login',
        'production': 'https://ws-api.toasttab.com/authentication/v1/authentication/login'
    },
    'rate_limits': {
        'default': 1000,  # requests per hour
        'burst': 50      # requests per minute
    },
    'webhook_events': [
        'ORDER_CREATED',
        'ORDER_MODIFIED',
        'ORDER_DELETED',
        'CHECK_CREATED',
        'CHECK_MODIFIED',
        'CHECK_DELETED',
        'PAYMENT_CREATED',
        'PAYMENT_MODIFIED',
        'RESTAURANT_UPDATED'
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
        'gift_card',
        'house_account',
        'loyalty_points',
        'external_payment'
    ]
}

# Restaurant industry specific settings
RESTAURANT_SETTINGS = {
    'item_categories': {
        'FOOD': 'food_beverage',
        'BEVERAGE': 'beverage',
        'ALCOHOL': 'alcoholic_beverage',
        'SERVICE': 'service',
        'MERCHANDISE': 'retail_merchandise'
    },
    'dining_options': [
        'DINE_IN',
        'TAKEOUT',
        'DELIVERY',
        'DRIVE_THRU',
        'CURBSIDE'
    ],
    'payment_processing': {
        'tip_handling': True,
        'gratuity_calculation': True,
        'split_checks': True,
        'refund_support': True
    }
}

# Feature matrix
FEATURES = {
    'authentication': {
        'oauth2': True,
        'token_refresh': True,
        'multi_restaurant': True,
        'sandbox_support': True
    },
    'data_extraction': {
        'checks': True,
        'orders': True,
        'payments': True,
        'menu_items': True,
        'customers': True,
        'real_time': True,
        'batch_sync': True
    },
    'restaurant_features': {
        'menu_modifiers': True,
        'table_tracking': True,
        'server_assignment': True,
        'dining_options': True,
        'tip_processing': True,
        'discount_handling': True
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