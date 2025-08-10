"""
Shopify POS Connector Module

Complete Shopify POS integration for TaxPoynt eInvoice System.
Provides OAuth 2.0 and private app authentication, order/transaction processing, and FIRS-compliant invoice generation.

Main Components:
- ShopifyPOSConnector: Main connector implementing BasePOSConnector interface
- ShopifyAuthenticator: OAuth 2.0 and private app authentication management
- ShopifyRESTClient: Shopify Admin API communication (REST and GraphQL)
- ShopifyDataExtractor: Order/transaction and data extraction
- ShopifyTransactionTransformer: FIRS-compliant invoice transformation

Usage:
    from taxpoynt_platform.external_integrations.business_systems.pos.shopify_pos import ShopifyPOSConnector
    
    # OAuth 2.0 configuration
    config = {
        'shop_domain': 'your-shop.myshopify.com',
        'api_key': 'your_shopify_api_key',
        'api_secret': 'your_shopify_api_secret',
        'webhook_secret': 'your_webhook_secret',
        'currency': 'NGN',
        'vat_rate': 0.075,
        'pos_location_ids': ['location_1', 'location_2'],
        'include_online_orders': False
    }
    
    # Private App configuration
    config = {
        'shop_domain': 'your-shop.myshopify.com',
        'private_app': True,
        'access_token': 'your_private_app_access_token',
        'webhook_secret': 'your_webhook_secret',
        'currency': 'NGN',
        'vat_rate': 0.075
    }
    
    connector = ShopifyPOSConnector(config)
    await connector.authenticate()
    transactions = await connector.get_transactions()
"""

from .connector import ShopifyPOSConnector
from .auth import ShopifyAuthenticator
from .rest_client import ShopifyRESTClient
from .data_extractor import ShopifyDataExtractor
from .transaction_transformer import ShopifyTransactionTransformer
from .exceptions import (
    ShopifyError,
    ShopifyConnectionError,
    ShopifyAuthenticationError,
    ShopifyAPIError,
    ShopifyRateLimitError,
    ShopifyNotFoundError,
    ShopifyValidationError,
    ShopifyWebhookError,
    ShopifyOrderError,
    ShopifyCustomerError,
    ShopifyProductError,
    ShopifyInventoryError,
    ShopifyConfigurationError,
    ShopifyTimeoutError,
    ShopifyLocationError,
    create_shopify_exception
)

__all__ = [
    # Main connector
    'ShopifyPOSConnector',
    
    # Component classes
    'ShopifyAuthenticator',
    'ShopifyRESTClient',
    'ShopifyDataExtractor',
    'ShopifyTransactionTransformer',
    
    # Exception classes
    'ShopifyError',
    'ShopifyConnectionError',
    'ShopifyAuthenticationError',
    'ShopifyAPIError',
    'ShopifyRateLimitError',
    'ShopifyNotFoundError',
    'ShopifyValidationError',
    'ShopifyWebhookError',
    'ShopifyOrderError',
    'ShopifyCustomerError',
    'ShopifyProductError',
    'ShopifyInventoryError',
    'ShopifyConfigurationError',
    'ShopifyTimeoutError',
    'ShopifyLocationError',
    'create_shopify_exception'
]

# Connector metadata
__version__ = '1.0.0'
__author__ = 'TaxPoynt eInvoice Team'
__description__ = 'Shopify POS connector for Nigerian FIRS e-invoicing compliance'

# Supported features
SUPPORTED_FEATURES = [
    'oauth_authentication',
    'private_app_authentication',
    'transaction_retrieval',
    'webhook_processing',
    'webhook_signature_verification',
    'location_management',
    'payment_methods',
    'invoice_transformation',
    'firs_compliance',
    'nigerian_tax_handling',
    'order_management',
    'customer_management',
    'product_management',
    'inventory_integration',
    'multi_currency_support',
    'gift_card_support',
    'discount_support',
    'graphql_api',
    'batch_processing',
    'real_time_webhooks',
    'customizations_support',
    'shipping_integration',
    'transaction_sync',
    'daily_reporting'
]

# Nigerian market compliance
NIGERIAN_COMPLIANCE = {
    'vat_rate': 0.075,  # 7.5% Nigerian VAT
    'supported_currencies': ['NGN', 'USD', 'CAD', 'EUR', 'GBP'],
    'tin_validation': True,
    'firs_integration': True,
    'ubl_bis_3_0': True,
    'default_customer_tin': '00000000-0001-0'
}

# Shopify-specific features
SHOPIFY_FEATURES = {
    'admin_api_version': '2023-10',
    'supports_pos_orders': True,
    'supports_online_orders': True,
    'webhook_events': [
        'orders/create',
        'orders/updated', 
        'orders/paid',
        'orders/cancelled',
        'orders/fulfilled',
        'orders/partially_fulfilled',
        'customers/create',
        'customers/update',
        'products/create',
        'products/update'
    ],
    'authentication_methods': ['oauth_2_0', 'private_app'],
    'api_types': ['rest', 'graphql'],
    'rate_limiting': {
        'call_limit': True,
        'bucket_system': True,
        'retry_after_header': True
    }
}