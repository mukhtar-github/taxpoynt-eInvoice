"""
Lightspeed POS Connector Module

Complete Lightspeed POS integration for TaxPoynt eInvoice System.
Provides OAuth 2.0 authentication, transaction processing, and FIRS-compliant invoice generation
for both Lightspeed Retail (R-Series) and Restaurant (K-Series) systems.

Main Components:
- LightspeedPOSConnector: Main connector implementing BasePOSConnector interface
- LightspeedAuthenticator: OAuth 2.0 authentication management for both API types
- LightspeedRESTClient: Lightspeed API communication (Retail and Restaurant)
- LightspeedDataExtractor: Transaction and data extraction with Nigerian adaptations
- LightspeedTransactionTransformer: FIRS-compliant invoice transformation

Usage:
    from taxpoynt_platform.external_integrations.business_systems.pos.lightspeed import LightspeedPOSConnector
    
    # Lightspeed Retail configuration
    config = {
        'client_id': 'your_lightspeed_client_id',
        'client_secret': 'your_lightspeed_client_secret',
        'redirect_uri': 'your_oauth_redirect_uri',
        'api_type': 'retail',  # or 'restaurant'
        'scope': 'employee:all',
        'currency': 'NGN',
        'vat_rate': 0.075,
        'location_ids': ['shop_id_1', 'shop_id_2']
    }
    
    # Lightspeed Restaurant configuration
    config = {
        'client_id': 'your_lightspeed_client_id',
        'client_secret': 'your_lightspeed_client_secret',
        'redirect_uri': 'your_oauth_redirect_uri',
        'api_type': 'restaurant',
        'scope': 'read_orders write_orders',
        'currency': 'NGN',
        'vat_rate': 0.075
    }
    
    connector = LightspeedPOSConnector(config)
    await connector.authenticate()
    transactions = await connector.get_transactions()
"""

from .connector import LightspeedPOSConnector
from .auth import LightspeedAuthenticator
from .rest_client import LightspeedRESTClient
from .data_extractor import LightspeedDataExtractor
from .transaction_transformer import LightspeedTransactionTransformer
from .exceptions import (
    LightspeedError,
    LightspeedConnectionError,
    LightspeedAuthenticationError,
    LightspeedAPIError,
    LightspeedRateLimitError,
    LightspeedNotFoundError,
    LightspeedValidationError,
    LightspeedWebhookError,
    LightspeedSaleError,
    LightspeedCustomerError,
    LightspeedProductError,
    LightspeedInventoryError,
    LightspeedConfigurationError,
    LightspeedTimeoutError,
    LightspeedLocationError,
    create_lightspeed_exception
)

__all__ = [
    # Main connector
    'LightspeedPOSConnector',
    
    # Component classes
    'LightspeedAuthenticator',
    'LightspeedRESTClient',
    'LightspeedDataExtractor',
    'LightspeedTransactionTransformer',
    
    # Exception classes
    'LightspeedError',
    'LightspeedConnectionError',
    'LightspeedAuthenticationError',
    'LightspeedAPIError',
    'LightspeedRateLimitError',
    'LightspeedNotFoundError',
    'LightspeedValidationError',
    'LightspeedWebhookError',
    'LightspeedSaleError',
    'LightspeedCustomerError',
    'LightspeedProductError',
    'LightspeedInventoryError',
    'LightspeedConfigurationError',
    'LightspeedTimeoutError',
    'LightspeedLocationError',
    'create_lightspeed_exception'
]

# Connector metadata
__version__ = '1.0.0'
__author__ = 'TaxPoynt eInvoice Team'
__description__ = 'Lightspeed POS connector for Nigerian FIRS e-invoicing compliance'

# Supported features
SUPPORTED_FEATURES = [
    'oauth_authentication',
    'transaction_retrieval',
    'location_management',
    'payment_methods',
    'inventory_integration',
    'invoice_transformation',
    'firs_compliance',
    'nigerian_tax_handling',
    'multi_api_support',  # Both retail and restaurant APIs
    'customer_management',
    'product_management',
    'batch_processing',
    'transaction_sync',
    'daily_reporting',
    'multi_currency',
    'rate_limiting',
    'real_time_processing'
]

# Nigerian market compliance
NIGERIAN_COMPLIANCE = {
    'vat_rate': 0.075,  # 7.5% Nigerian VAT
    'supported_currencies': ['NGN', 'USD', 'EUR', 'GBP'],
    'tin_validation': True,
    'firs_integration': True,
    'ubl_bis_3_0': True,
    'default_customer_tin': '00000000-0001-0'
}

# Lightspeed-specific features
LIGHTSPEED_FEATURES = {
    'api_types': ['retail', 'restaurant'],
    'retail_api': {
        'base_url': 'https://api.lightspeedapp.com',
        'oauth_url': 'https://cloud.lightspeedapp.com/oauth',
        'supports': ['sales', 'customers', 'items', 'locations', 'registers']
    },
    'restaurant_api': {
        'base_url': 'https://api.ikentoo.com',
        'oauth_url': 'https://oauth.ikentoo.com',
        'supports': ['orders', 'customers', 'products', 'locations', 'terminals']
    },
    'authentication': {
        'method': 'oauth_2_0',
        'grant_type': 'authorization_code',
        'token_refresh': True,
        'scope_required': True
    },
    'rate_limiting': {
        'method': 'bucket_system',
        'requests_per_second': 2,
        'burst_capacity': 40,
        'retry_logic': True
    },
    'webhook_support': {
        'available': 'limited',
        'events': ['sale_created', 'sale_updated', 'customer_created'],
        'signature_verification': 'not_standard'
    }
}