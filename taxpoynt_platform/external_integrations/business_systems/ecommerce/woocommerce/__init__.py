"""
WooCommerce E-commerce Integration Package
Comprehensive integration with WooCommerce e-commerce platform for TaxPoynt eInvoice platform.

This package provides complete WooCommerce e-commerce connectivity including:
- OAuth 1.0a and Basic authentication
- REST API client for comprehensive store operations
- Order data extraction with WordPress integration
- FIRS-compliant UBL BIS 3.0 invoice transformation
- Real-time webhook processing
- Plugin and extension compatibility
- Nigerian tax compliance (7.5% VAT)

Supported WooCommerce APIs:
- WooCommerce REST API v3 (wp-json/wc/v3)
- WordPress REST API integration
- Webhooks API (order events, customer events, product events)
- OAuth 1.0a API (recommended authentication)
- Basic Auth API (for HTTPS stores)

WordPress Integration Features:
- WordPress version compatibility checking
- Plugin detection and compatibility
- Theme integration support
- Custom post types and meta fields
- WordPress multisite support

Usage:
    from taxpoynt_platform.external_integrations.business_systems.ecommerce.woocommerce import (
        WooCommerceEcommerceConnector,
        WooCommerceAuthManager,
        WooCommerceRestClient,
        WooCommerceDataExtractor,
        WooCommerceOrderTransformer
    )
    
    # Initialize connector
    config = ConnectionConfig(
        store_id="your-store-domain",
        credentials={
            'store_url': 'https://your-store.com',
            'consumer_key': 'ck_your_consumer_key',
            'consumer_secret': 'cs_your_consumer_secret',
            'webhook_secret': 'your_webhook_secret',
            'use_oauth': True,  # True for OAuth 1.0a, False for Basic Auth
            'verify_ssl': True,
            'force_ssl': True,
            'api_version': 'wc/v3'
        }
    )
    
    connector = WooCommerceEcommerceConnector(config)
    
    # Connect and sync orders
    async with connector:
        sync_result = await connector.sync_orders()
        print(f"Synced {sync_result.orders_successful} orders")

Features:
- ✅ OAuth 1.0a Authentication (recommended for production)
- ✅ Basic Authentication support (for HTTPS stores)
- ✅ WordPress REST API integration
- ✅ Automatic rate limiting (60 requests/minute)
- ✅ Comprehensive error handling and retry logic
- ✅ Order synchronization with status filtering
- ✅ Real-time webhook processing
- ✅ Nigerian VAT compliance (7.5% VAT calculation)
- ✅ FIRS UBL BIS 3.0 invoice generation
- ✅ Product variation and bundle support
- ✅ Customer and product data extraction
- ✅ Pagination support for large datasets
- ✅ Batch order processing
- ✅ Webhook signature verification (HMAC-SHA256)
- ✅ WordPress plugin compatibility
- ✅ Multi-currency support
- ✅ Tax classes and rates integration

WooCommerce API Compatibility:
- WooCommerce REST API v3 (latest stable)
- WooCommerce REST API v2 (legacy support)
- WooCommerce REST API v1 (legacy support)
- WordPress REST API integration
- Custom WooCommerce extensions

API Endpoints Supported:
- /wp-json/wc/v3/system_status
- /wp-json/wc/v3/orders
- /wp-json/wc/v3/orders/{id}
- /wp-json/wc/v3/products
- /wp-json/wc/v3/products/{id}
- /wp-json/wc/v3/customers
- /wp-json/wc/v3/customers/{id}
- /wp-json/wc/v3/webhooks
- /wp-json/wc/v3/taxes
- /wp-json/wc/v3/taxes/classes
- /wp-json/wc/v3/products/categories
- /wp-json/wc/v3/products/tags
- /wp-json/wc/v3/settings

Nigerian E-commerce Features:
- Automatic 7.5% VAT calculation
- TIN validation and default handling
- Nigerian address formatting
- Naira (NGN) currency support
- FIRS-compliant invoice generation
- Nigerian business compliance

Authentication Methods:
- OAuth 1.0a (recommended for production)
- Basic Authentication (HTTPS required)
- Application Passwords (WordPress 5.6+)
- JWT Authentication (with plugins)

WordPress/WooCommerce Compatibility:
- WordPress 5.0+ (tested up to 6.4)
- WooCommerce 3.0+ (tested up to 8.5)
- PHP 7.4+ compatibility
- MySQL/MariaDB database support
- SSL/TLS encryption support
"""

from .connector import WooCommerceEcommerceConnector
from .auth import WooCommerceAuthManager
from .rest_client import WooCommerceRestClient
from .data_extractor import WooCommerceDataExtractor
from .order_transformer import WooCommerceOrderTransformer
from .exceptions import (
    WooCommerceConnectionError,
    WooCommerceAuthenticationError,
    WooCommerceAPIError,
    WooCommerceRateLimitError,
    WooCommerceValidationError,
    WooCommerceWebhookError,
    WooCommerceDataExtractionError,
    WooCommerceTransformationError,
    WooCommerceConfigurationError,
    WooCommerceProductError,
    WooCommerceCustomerError,
    WooCommercePluginError,
    WooCommerceWordPressError,
    create_woocommerce_exception
)

__all__ = [
    # Main connector
    'WooCommerceEcommerceConnector',
    
    # Core components
    'WooCommerceAuthManager',
    'WooCommerceRestClient',
    'WooCommerceDataExtractor',
    'WooCommerceOrderTransformer',
    
    # Exceptions
    'WooCommerceConnectionError',
    'WooCommerceAuthenticationError',
    'WooCommerceAPIError',
    'WooCommerceRateLimitError',
    'WooCommerceValidationError',
    'WooCommerceWebhookError',
    'WooCommerceDataExtractionError',
    'WooCommerceTransformationError',
    'WooCommerceConfigurationError',
    'WooCommerceProductError',
    'WooCommerceCustomerError',
    'WooCommercePluginError',
    'WooCommerceWordPressError',
    'create_woocommerce_exception'
]

# Package metadata
__version__ = '1.0.0'
__author__ = 'TaxPoynt Development Team'
__description__ = 'WooCommerce e-commerce integration for TaxPoynt eInvoice platform'

# WooCommerce-specific configuration
WOOCOMMERCE_CONFIG = {
    'api_version': 'wc/v3',
    'supported_api_versions': ['wc/v3', 'wc/v2', 'wc/v1'],
    'wordpress_integration': True,
    'base_endpoints': {
        'rest_api': '/wp-json/{version}',
        'system_status': '/system_status',
        'orders': '/orders',
        'products': '/products',
        'customers': '/customers',
        'webhooks': '/webhooks',
        'taxes': '/taxes',
        'settings': '/settings'
    },
    'rate_limits': {
        'requests_per_minute': 60,
        'burst_requests': 10,
        'retry_attempts': 3
    },
    'webhook_events': [
        'order.created',
        'order.updated',
        'order.deleted',
        'order.restored',
        'order.completed',
        'order.cancelled',
        'order.refunded',
        'customer.created',
        'customer.updated',
        'customer.deleted',
        'product.created',
        'product.updated',
        'product.deleted',
        'product.restored'
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

# WordPress compatibility matrix
WORDPRESS_COMPATIBILITY = {
    'minimum_wp_version': '5.0',
    'tested_up_to_wp': '6.4',
    'minimum_wc_version': '3.0',
    'tested_up_to_wc': '8.5',
    'php_requirements': {
        'minimum': '7.4',
        'recommended': '8.0'
    },
    'database_support': ['MySQL', 'MariaDB'],
    'ssl_required': True
}

# Order status mappings
ORDER_STATUS_MAPPINGS = {
    'wc_to_standard': {
        'pending': 'pending',
        'processing': 'processing',
        'on-hold': 'pending',
        'completed': 'delivered',
        'cancelled': 'cancelled',
        'refunded': 'refunded',
        'failed': 'failed',
        'trash': 'cancelled'
    },
    'standard_to_wc': {
        'pending': 'pending',
        'processing': 'processing',
        'shipped': 'processing',
        'delivered': 'completed',
        'cancelled': 'cancelled',
        'refunded': 'refunded',
        'failed': 'failed'
    }
}

# Payment method mappings
PAYMENT_METHOD_MAPPINGS = {
    'bacs': {
        'name': 'Direct Bank Transfer',
        'type': 'bank_transfer',
        'ubl_code': '30'
    },
    'cheque': {
        'name': 'Check Payment',
        'type': 'check',
        'ubl_code': '20'
    },
    'cod': {
        'name': 'Cash on Delivery',
        'type': 'cash',
        'ubl_code': '10'
    },
    'paypal': {
        'name': 'PayPal',
        'type': 'digital_wallet',
        'ubl_code': '42'
    },
    'stripe': {
        'name': 'Stripe',
        'type': 'credit_card',
        'ubl_code': '48'
    },
    'square': {
        'name': 'Square',
        'type': 'credit_card',
        'ubl_code': '48'
    },
    'razorpay': {
        'name': 'Razorpay',
        'type': 'credit_card',
        'ubl_code': '48'
    },
    'paystack': {
        'name': 'Paystack',
        'type': 'credit_card',
        'ubl_code': '48'
    },
    'flutterwave': {
        'name': 'Flutterwave',
        'type': 'credit_card',
        'ubl_code': '48'
    }
}

# Product classification mappings
PRODUCT_CLASSIFICATIONS = {
    'simple': {
        'type': 'Simple Product',
        'default_classification': '48000000-8'
    },
    'variable': {
        'type': 'Variable Product',
        'default_classification': '48000000-8'
    },
    'grouped': {
        'type': 'Grouped Product',
        'default_classification': '48000000-8'
    },
    'external': {
        'type': 'External/Affiliate Product',
        'default_classification': '48000000-8'
    },
    'subscription': {
        'type': 'Subscription Product',
        'default_classification': '77000000-0'
    },
    'bundle': {
        'type': 'Product Bundle',
        'default_classification': '48000000-8'
    }
}

# Plugin compatibility
PLUGIN_COMPATIBILITY = {
    'payment_gateways': [
        'woocommerce-gateway-stripe',
        'woocommerce-gateway-paypal',
        'woocommerce-square',
        'woocommerce-payments',
        'woocommerce-razorpay',
        'woocommerce-paystack'
    ],
    'shipping': [
        'woocommerce-shipping',
        'woocommerce-table-rate-shipping',
        'woocommerce-advanced-shipping'
    ],
    'taxation': [
        'woocommerce-tax',
        'woocommerce-eu-vat-assistant',
        'woocommerce-avatax'
    ],
    'subscriptions': [
        'woocommerce-subscriptions',
        'woocommerce-memberships'
    ],
    'inventory': [
        'woocommerce-stock-manager',
        'woocommerce-product-bundles'
    ]
}

# Feature matrix
FEATURES = {
    'authentication': {
        'oauth_1_0a': True,
        'basic_auth': True,
        'application_passwords': True,
        'jwt_auth': True,  # With plugin
        'webhook_verification': True,
        'ssl_verification': True
    },
    'data_extraction': {
        'orders': True,
        'customers': True,
        'products': True,
        'product_variations': True,
        'product_bundles': True,
        'categories': True,
        'tags': True,
        'taxes': True,
        'coupons': True,
        'refunds': True
    },
    'wordpress_integration': {
        'version_detection': True,
        'plugin_compatibility': True,
        'theme_integration': True,
        'custom_fields': True,
        'multisite_support': True,
        'user_roles': True
    },
    'real_time_processing': {
        'webhooks': True,
        'order_events': True,
        'customer_events': True,
        'product_events': True,
        'inventory_updates': True,
        'payment_notifications': True
    },
    'tax_compliance': {
        'nigerian_vat': True,
        'vat_inclusive_calculation': True,
        'tin_validation': True,
        'firs_compliance': True,
        'multi_currency': True,
        'tax_classes': True,
        'tax_rates': True
    },
    'integration': {
        'rest_api': True,
        'rate_limiting': True,
        'error_handling': True,
        'retry_logic': True,
        'health_monitoring': True,
        'batch_processing': True,
        'pagination': True,
        'filtering': True,
        'searching': True
    },
    'e_commerce_specific': {
        'order_lifecycle': True,
        'payment_processing': True,
        'inventory_tracking': True,
        'customer_management': True,
        'product_catalog': True,
        'product_variations': True,
        'shipping_fulfillment': True,
        'discount_handling': True,
        'subscription_support': True,
        'bundle_products': True,
        'digital_downloads': True
    }
}