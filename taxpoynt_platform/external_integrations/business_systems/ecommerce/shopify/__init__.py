"""
Shopify E-commerce Integration Package
Comprehensive integration with Shopify e-commerce platform for TaxPoynt eInvoice platform.

This package provides complete Shopify e-commerce connectivity including:
- OAuth 2.0 and private app authentication
- REST API client for comprehensive store operations
- Order data extraction and customer management
- FIRS-compliant UBL BIS 3.0 invoice transformation
- Real-time webhook processing
- Multi-store support
- Nigerian tax compliance (7.5% VAT)

Supported Shopify APIs:
- Admin REST API (2023-10 and later versions)
- GraphQL Admin API (partial support)
- Webhooks API (order events, payment events)
- OAuth 2.0 API (public app authentication)
- Private App API (password authentication)

E-commerce Features:
- Complete order lifecycle management
- Product catalog synchronization
- Customer data management
- Multi-currency support
- Payment gateway integration
- Inventory and fulfillment tracking

Usage:
    from taxpoynt_platform.external_integrations.business_systems.ecommerce.shopify import (
        ShopifyEcommerceConnector,
        ShopifyAuthManager,
        ShopifyRestClient,
        ShopifyDataExtractor,
        ShopifyOrderTransformer
    )
    
    # Initialize connector
    config = ConnectionConfig(
        store_id="your_shop_name",
        credentials={
            'shop_name': 'your-shop-name',  # Without .myshopify.com
            'api_key': 'your_shopify_api_key',
            'api_secret': 'your_shopify_api_secret',
            'access_token': 'your_access_token',  # For private apps or post-OAuth
            'webhook_secret': 'your_webhook_secret',
            'private_app': False,  # True for private apps
            'api_version': '2023-10',
            'scopes': ['read_orders', 'read_products', 'read_customers'],
            'redirect_uri': 'https://your-app.com/auth/callback'
        }
    )
    
    connector = ShopifyEcommerceConnector(config)
    
    # Connect and sync orders
    async with connector:
        sync_result = await connector.sync_orders()
        print(f"Synced {sync_result.orders_successful} orders")

Features:
- ✅ OAuth 2.0 Authentication with CSRF protection
- ✅ Private app authentication support
- ✅ Automatic rate limiting (2 calls/second with burst)
- ✅ Comprehensive error handling and retry logic
- ✅ Order synchronization with date range filtering
- ✅ Real-time webhook processing
- ✅ Nigerian VAT compliance (7.5% VAT calculation)
- ✅ FIRS UBL BIS 3.0 invoice generation
- ✅ Multi-store and multi-currency support
- ✅ Product and customer data extraction
- ✅ Pagination support for large datasets
- ✅ Batch order processing
- ✅ Webhook signature verification
- ✅ Health monitoring and connection testing

Shopify API Compatibility:
- Shopify REST Admin API v2023-10 (latest stable)
- Shopify REST Admin API v2023-07
- Shopify REST Admin API v2023-04
- Shopify REST Admin API v2023-01
- Legacy API versions (limited support)

API Endpoints Supported:
- /admin/api/2023-10/shop.json
- /admin/api/2023-10/orders.json
- /admin/api/2023-10/orders/{id}.json
- /admin/api/2023-10/products.json
- /admin/api/2023-10/products/{id}.json
- /admin/api/2023-10/customers.json
- /admin/api/2023-10/customers/{id}.json
- /admin/api/2023-10/locations.json
- /admin/api/2023-10/inventory_levels.json
- /admin/api/2023-10/webhooks.json
- /admin/oauth/authorize (OAuth flow)
- /admin/oauth/access_token (token exchange)

Nigerian E-commerce Features:
- Automatic 7.5% VAT calculation
- TIN validation and default handling
- Lagos State default addressing
- Naira (NGN) currency support
- FIRS-compliant invoice generation
- Nigerian business compliance

Authentication Methods:
- OAuth 2.0 (recommended for public apps)
- Private App Passwords (for server-to-server)
- Custom App authentication
- Partner app authentication
"""

from .connector import ShopifyEcommerceConnector
from .auth import ShopifyAuthManager
from .rest_client import ShopifyRestClient
from .data_extractor import ShopifyDataExtractor
from .order_transformer import ShopifyOrderTransformer
from .exceptions import (
    ShopifyConnectionError,
    ShopifyAuthenticationError,
    ShopifyAPIError,
    ShopifyRateLimitError,
    ShopifyValidationError,
    ShopifyWebhookError,
    ShopifyDataExtractionError,
    ShopifyTransformationError,
    ShopifyConfigurationError,
    ShopifyProductError,
    ShopifyCustomerError,
    ShopifyInventoryError,
    create_shopify_exception
)

__all__ = [
    # Main connector
    'ShopifyEcommerceConnector',
    
    # Core components
    'ShopifyAuthManager',
    'ShopifyRestClient',
    'ShopifyDataExtractor',
    'ShopifyOrderTransformer',
    
    # Exceptions
    'ShopifyConnectionError',
    'ShopifyAuthenticationError',
    'ShopifyAPIError',
    'ShopifyRateLimitError',
    'ShopifyValidationError',
    'ShopifyWebhookError',
    'ShopifyDataExtractionError',
    'ShopifyTransformationError',
    'ShopifyConfigurationError',
    'ShopifyProductError',
    'ShopifyCustomerError',
    'ShopifyInventoryError',
    'create_shopify_exception'
]

# Package metadata
__version__ = '1.0.0'
__author__ = 'TaxPoynt Development Team'
__description__ = 'Shopify e-commerce integration for TaxPoynt eInvoice platform'

# Shopify-specific configuration
SHOPIFY_CONFIG = {
    'api_version': '2023-10',
    'supported_api_versions': [
        '2023-10', '2023-07', '2023-04', '2023-01',
        '2022-10', '2022-07', '2022-04', '2022-01'
    ],
    'base_urls': {
        'admin_api': 'https://{shop}.myshopify.com/admin/api/{version}',
        'oauth': 'https://{shop}.myshopify.com/admin/oauth',
        'storefront': 'https://{shop}.myshopify.com'
    },
    'rate_limits': {
        'rest_api': {
            'calls_per_second': 2,
            'burst_bucket_size': 40,
            'leak_rate': 2  # calls per second
        },
        'graphql_api': {
            'cost_per_second': 1000,
            'restore_rate': 50,
            'maximum_cost': 1000
        }
    },
    'webhook_events': [
        'orders/create',
        'orders/updated',
        'orders/paid',
        'orders/cancelled',
        'orders/fulfilled',
        'orders/partially_fulfilled',
        'orders/refunded',
        'order_transactions/create',
        'customers/create',
        'customers/updated',
        'products/create',
        'products/updated',
        'inventory_levels/update'
    ]
}

# Nigerian market compliance settings
NIGERIAN_COMPLIANCE = {
    'vat_rate': 0.075,  # 7.5% VAT
    'currency': 'NGN',
    'default_tin': '00000000-0001',
    'vat_inclusive_by_default': True,
    'default_location': {
        'country': 'Nigeria',
        'country_code': 'NG',
        'state': 'Lagos State',
        'city': 'Lagos',
        'postal_code': '100001'
    }
}

# OAuth scopes for different access levels
OAUTH_SCOPES = {
    'basic': [
        'read_orders',
        'read_products',
        'read_customers'
    ],
    'standard': [
        'read_orders',
        'read_products',
        'read_customers',
        'read_inventory',
        'read_locations',
        'read_fulfillments'
    ],
    'advanced': [
        'read_orders',
        'write_orders',
        'read_products',
        'write_products',
        'read_customers',
        'write_customers',
        'read_inventory',
        'write_inventory',
        'read_locations',
        'read_fulfillments',
        'write_fulfillments',
        'read_shipping',
        'write_shipping',
        'read_analytics'
    ],
    'full_access': [
        'read_all_orders',
        'write_orders',
        'read_products',
        'write_products',
        'read_customers',
        'write_customers',
        'read_inventory',
        'write_inventory',
        'read_locations',
        'write_locations',
        'read_fulfillments',
        'write_fulfillments',
        'read_shipping',
        'write_shipping',
        'read_analytics',
        'read_reports',
        'write_script_tags',
        'read_themes',
        'write_themes'
    ]
}

# Product categories for classification
PRODUCT_CATEGORIES = {
    'physical_goods': [
        'apparel', 'clothing', 'shoes', 'bags', 'jewelry',
        'electronics', 'books', 'home', 'toys', 'sports',
        'health', 'beauty', 'food', 'automotive'
    ],
    'digital_goods': [
        'digital', 'software', 'ebooks', 'music', 'videos',
        'courses', 'subscriptions', 'memberships'
    ],
    'services': [
        'consultation', 'training', 'support', 'maintenance',
        'installation', 'repair', 'customization'
    ],
    'gift_cards': [
        'gift_card', 'voucher', 'credit', 'store_credit'
    ]
}

# Payment gateway mappings
PAYMENT_GATEWAYS = {
    'shopify_payments': {
        'name': 'Shopify Payments',
        'type': 'credit_card',
        'ubl_code': '48'
    },
    'stripe': {
        'name': 'Stripe',
        'type': 'credit_card',
        'ubl_code': '48'
    },
    'paypal': {
        'name': 'PayPal',
        'type': 'digital_wallet',
        'ubl_code': '42'
    },
    'square': {
        'name': 'Square',
        'type': 'credit_card',
        'ubl_code': '48'
    },
    'authorize_net': {
        'name': 'Authorize.Net',
        'type': 'credit_card',
        'ubl_code': '48'
    },
    'braintree': {
        'name': 'Braintree',
        'type': 'credit_card',
        'ubl_code': '48'
    },
    'manual': {
        'name': 'Manual Payment',
        'type': 'cash',
        'ubl_code': '10'
    },
    'bank_transfer': {
        'name': 'Bank Transfer',
        'type': 'bank_transfer',
        'ubl_code': '30'
    }
}

# Feature matrix
FEATURES = {
    'authentication': {
        'oauth_2_0': True,
        'private_app': True,
        'custom_app': True,
        'partner_app': True,
        'webhook_verification': True,
        'app_proxy_verification': True
    },
    'data_extraction': {
        'orders': True,
        'customers': True,
        'products': True,
        'inventory': True,
        'fulfillments': True,
        'transactions': True,
        'refunds': True,
        'analytics': True
    },
    'real_time_processing': {
        'webhooks': True,
        'order_events': True,
        'payment_events': True,
        'inventory_updates': True,
        'customer_updates': True,
        'product_updates': True
    },
    'tax_compliance': {
        'nigerian_vat': True,
        'vat_inclusive_calculation': True,
        'tin_validation': True,
        'firs_compliance': True,
        'multi_currency': True
    },
    'integration': {
        'rest_api': True,
        'graphql_api': False,  # Future enhancement
        'rate_limiting': True,
        'error_handling': True,
        'retry_logic': True,
        'health_monitoring': True,
        'batch_processing': True,
        'pagination': True
    },
    'e_commerce_specific': {
        'order_lifecycle': True,
        'payment_processing': True,
        'inventory_tracking': True,
        'customer_management': True,
        'product_catalog': True,
        'shipping_fulfillment': True,
        'discount_handling': True,
        'multi_variant_products': True
    }
}