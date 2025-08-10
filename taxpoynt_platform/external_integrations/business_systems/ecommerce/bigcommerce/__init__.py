"""
BigCommerce E-commerce Integration Package
Comprehensive integration with BigCommerce e-commerce platform for TaxPoynt eInvoice platform.

This package provides complete BigCommerce e-commerce connectivity including:
- OAuth2 and API token authentication
- REST API client for comprehensive store operations
- Order data extraction with multi-channel support
- FIRS-compliant UBL BIS 3.0 invoice transformation
- Real-time webhook processing
- Multi-channel and headless commerce support

Supported BigCommerce Features:
- BigCommerce SaaS platform
- Multi-channel selling
- Headless commerce
- BigCommerce for WordPress
- Channel management
- Advanced product variations
- Multi-storefront operations

Key Features:
- Multi-channel architecture support
- Advanced API filtering and pagination
- Nigerian tax compliance (7.5% VAT)
- Real-time order processing
- Comprehensive product catalog management
- Customer data integration with addresses
- Analytics and reporting
- Webhook signature verification

Usage Example:
    ```python
    from taxpoynt_platform.external_integrations.business_systems.ecommerce.bigcommerce import (
        BigCommerceEcommerceConnector,
        BigCommerceAuthManager,
        BigCommerceRESTClient
    )
    
    # Initialize connector
    config = {
        'store_hash': 'your-store-hash',
        'auth_type': 'api_token',
        'api_token': 'your-api-token',
        'webhook_secret': 'your-webhook-secret',
        'channel_id': 1  # Optional: default channel
    }
    
    connector = BigCommerceEcommerceConnector(config)
    
    # Connect to store
    await connector.connect()
    
    # Get recent orders
    orders = await connector.get_orders(limit=10)
    
    # Transform order to UBL invoice
    if orders:
        invoice = await connector.transform_order_to_invoice(orders[0])
        print(f"Generated invoice for order {orders[0]['id']}")
    
    # Process webhook
    webhook_result = await connector.process_webhook(
        'store/order/created',
        {'order_id': 123}
    )
    
    # Get multi-channel data
    channels = await connector.get_channels()
    for channel in channels:
        print(f"Channel: {channel['name']} - Type: {channel['type']}")
    ```

Configuration Options:
    store_hash (str): BigCommerce store hash (required)
    auth_type (str): Authentication type ('api_token', 'oauth2', 'store_token')
    api_token (str): API access token (recommended for server-to-server)
    client_id (str): OAuth2 client ID (for oauth2 auth)
    client_secret (str): OAuth2 client secret (for oauth2 auth)
    access_token (str): OAuth2 access token (for oauth2 auth)
    store_token (str): Store-specific API token (for store_token auth)
    webhook_secret (str): Secret for webhook signature verification
    channel_id (int): Default channel ID for multi-channel operations
    rate_limit (dict): API rate limiting configuration
    transformer (dict): Invoice transformation settings

Nigerian Market Configuration:
    vat_rate (float): VAT rate (default: 0.075 for 7.5%)
    default_currency (str): Default currency (default: 'NGN')
    default_country (str): Default country code (default: 'NG')
    default_tin (str): Default TIN for missing tax IDs

Multi-Channel Support:
    BigCommerce's multi-channel architecture allows selling across:
    - Online storefronts
    - Marketplaces (Amazon, eBay, Facebook, Instagram)
    - Social media platforms
    - Point of sale systems
    - Custom applications via API
    
    The connector supports channel-specific operations and can filter
    data by channel for accurate attribution and reporting.

Authentication Methods:
    1. API Token (Recommended):
       - Store-level API token with granular scopes
       - X-Auth-Token header authentication
       - No expiration, revocable from admin panel
       
    2. OAuth2 Apps:
       - Public app authentication flow
       - X-Auth-Client and X-Auth-Token headers
       - Suitable for third-party applications
       
    3. Store Token:
       - Legacy store-specific tokens
       - Backward compatibility support

API Capabilities:
    - Complete BigCommerce REST API v3 coverage
    - Advanced filtering with field operators
    - Efficient pagination with limit/page parameters
    - Multi-channel endpoint support
    - Rate limiting compliance (5 req/sec)
    - Comprehensive error handling and retry logic

Webhook Support:
    Supported webhook events:
    - store/order/created: New order creation
    - store/order/updated: Order status changes
    - store/order/statusUpdated: Order status specific updates
    - store/customer/created: New customer registration
    - store/customer/updated: Customer profile changes
    - store/product/created: New product addition
    - store/product/updated: Product information changes
    - store/product/inventory/updated: Stock level changes
    
    Features:
    - Signature verification with webhook secret
    - Automatic invoice generation for eligible orders
    - Real-time data synchronization
    - Event-driven architecture
    - Multi-channel webhook support

Error Handling:
    Custom exception hierarchy:
    - BigCommerceConnectionError: Connection issues
    - BigCommerceAuthenticationError: Auth failures
    - BigCommerceDataExtractionError: Data retrieval issues
    - BigCommerceTransformationError: Invoice transformation issues
    - BigCommerceAPIError: General API errors
    - BigCommerceRateLimitError: Rate limiting issues
    - BigCommerceChannelError: Multi-channel operation errors

Dependencies:
    - aiohttp: Async HTTP client
    - python-dateutil: Date/time parsing
    - cryptography: Signature verification
    - pydantic: Data validation (optional)

Thread Safety:
    All components are designed for async/await usage and are thread-safe
    when used within the same event loop. Multiple connectors can be
    instantiated for different stores simultaneously.

Performance Considerations:
    - Connection pooling for HTTP requests
    - Rate limiting compliance (5 requests/second)
    - Efficient pagination for large datasets
    - Caching for store configuration data
    - Batch operations where possible
    - Multi-channel data optimization

BigCommerce-Specific Features:
    - Product variants and modifiers
    - Custom fields and meta data
    - Advanced tax rules
    - Shipping zones and methods
    - Coupon and discount management
    - Gift certificate support
    - Abandoned cart recovery
    - Customer groups and pricing

Integration Notes:
    - Follows TaxPoynt eInvoice platform patterns
    - Implements BaseEcommerceConnector interface
    - Nigerian tax compliance built-in
    - UBL BIS 3.0 invoice generation
    - FIRS regulatory compliance
    - Multi-channel transaction attribution

For detailed documentation and examples, see the individual module docstrings
and the TaxPoynt eInvoice platform documentation.
"""

from .connector import BigCommerceEcommerceConnector
from .auth import BigCommerceAuthManager
from .rest_client import BigCommerceRESTClient
from .data_extractor import BigCommerceDataExtractor
from .order_transformer import BigCommerceOrderTransformer
from .exceptions import (
    BigCommerceConnectionError,
    BigCommerceAuthenticationError,
    BigCommerceDataExtractionError,
    BigCommerceTransformationError,
    BigCommerceAPIError,
    BigCommerceOrderNotFoundError,
    BigCommerceCustomerNotFoundError,
    BigCommerceProductNotFoundError,
    BigCommerceStoreNotFoundError,
    BigCommerceRateLimitError,
    BigCommerceWebhookError,
    BigCommerceChannelError,
    BigCommerceAppError,
    BigCommerceScriptError,
    BigCommerceCheckoutError,
    BigCommerceMultiChannelError
)

# Package metadata
__version__ = "1.0.0"
__author__ = "TaxPoynt Development Team"
__email__ = "dev@taxpoynt.com"
__description__ = "BigCommerce e-commerce integration for TaxPoynt eInvoice platform"

# Supported BigCommerce features
SUPPORTED_FEATURES = [
    "Multi-channel selling",
    "Headless commerce",
    "Advanced product variants",
    "Customer groups",
    "Tax rules and zones",
    "Shipping calculations",
    "Coupon management",
    "Gift certificates",
    "Custom fields",
    "Webhook notifications",
    "OAuth2 authentication",
    "API token authentication"
]

# Default configuration
DEFAULT_CONFIG = {
    'auth_type': 'api_token',
    'rate_limit': {
        'requests_per_second': 5,
        'burst_capacity': 10
    },
    'transformer': {
        'vat_rate': 0.075,
        'default_currency': 'NGN',
        'default_country': 'NG',
        'default_tin': '00000000-0001'
    },
    'webhook': {
        'timeout': 30,
        'retry_attempts': 3
    },
    'timeout': {
        'total': 30,
        'connect': 10,
        'read': 20
    },
    'retry': {
        'max_retries': 3,
        'backoff_factor': 2,
        'retry_statuses': [429, 500, 502, 503, 504]
    }
}

# Export main classes and functions
__all__ = [
    # Main connector
    'BigCommerceEcommerceConnector',
    
    # Core components
    'BigCommerceAuthManager',
    'BigCommerceRESTClient', 
    'BigCommerceDataExtractor',
    'BigCommerceOrderTransformer',
    
    # Exceptions
    'BigCommerceConnectionError',
    'BigCommerceAuthenticationError',
    'BigCommerceDataExtractionError',
    'BigCommerceTransformationError',
    'BigCommerceAPIError',
    'BigCommerceOrderNotFoundError',
    'BigCommerceCustomerNotFoundError',
    'BigCommerceProductNotFoundError',
    'BigCommerceStoreNotFoundError',
    'BigCommerceRateLimitError',
    'BigCommerceWebhookError',
    'BigCommerceChannelError',
    'BigCommerceAppError',
    'BigCommerceScriptError',
    'BigCommerceCheckoutError',
    'BigCommerceMultiChannelError',
    
    # Configuration
    'DEFAULT_CONFIG',
    'SUPPORTED_FEATURES',
    
    # Metadata
    '__version__',
    '__author__',
    '__email__',
    '__description__'
]


def create_connector(config: dict) -> BigCommerceEcommerceConnector:
    """
    Factory function to create a BigCommerce e-commerce connector.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Configured BigCommerceEcommerceConnector instance
        
    Example:
        ```python
        from taxpoynt_platform.external_integrations.business_systems.ecommerce.bigcommerce import (
            create_connector
        )
        
        config = {
            'store_hash': 'your-store-hash',
            'auth_type': 'api_token',
            'api_token': 'your-token'
        }
        
        connector = create_connector(config)
        await connector.connect()
        ```
    """
    # Merge with default configuration
    merged_config = {**DEFAULT_CONFIG, **config}
    return BigCommerceEcommerceConnector(merged_config)


def get_supported_features() -> list:
    """
    Get list of supported BigCommerce features.
    
    Returns:
        List of supported feature strings
    """
    return SUPPORTED_FEATURES.copy()


def validate_config(config: dict) -> dict:
    """
    Validate BigCommerce connector configuration.
    
    Args:
        config: Configuration dictionary to validate
        
    Returns:
        Dictionary with validation results
        
    Example:
        ```python
        from taxpoynt_platform.external_integrations.business_systems.ecommerce.bigcommerce import (
            validate_config
        )
        
        config = {'store_hash': 'abc123'}
        result = validate_config(config)
        
        if not result['valid']:
            print("Configuration errors:", result['errors'])
        ```
    """
    errors = []
    warnings = []
    
    # Required fields
    required_fields = ['store_hash']
    for field in required_fields:
        if field not in config:
            errors.append(f"Missing required field: {field}")
    
    # Authentication validation
    auth_type = config.get('auth_type', 'api_token')
    if auth_type == 'api_token':
        if not config.get('api_token'):
            errors.append("api_token required for api_token auth")
    elif auth_type == 'oauth2':
        if not config.get('client_id') or not config.get('access_token'):
            errors.append("client_id and access_token required for oauth2 auth")
    elif auth_type == 'store_token':
        if not config.get('store_token'):
            errors.append("store_token required for store_token auth")
    
    # Store hash validation
    store_hash = config.get('store_hash', '')
    if store_hash and not store_hash.replace('-', '').replace('_', '').isalnum():
        warnings.append("Store hash format appears invalid - should be alphanumeric with hyphens/underscores")
    
    # TIN validation for Nigerian compliance
    transformer_config = config.get('transformer', {})
    default_tin = transformer_config.get('default_tin', DEFAULT_CONFIG['transformer']['default_tin'])
    if default_tin == DEFAULT_CONFIG['transformer']['default_tin']:
        warnings.append("Using default TIN - should be updated with actual TIN for compliance")
    
    # Channel ID validation
    channel_id = config.get('channel_id')
    if channel_id is not None:
        try:
            int(channel_id)
        except (ValueError, TypeError):
            errors.append("channel_id must be a valid integer")
    
    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'warnings': warnings,
        'config': {**DEFAULT_CONFIG, **config}
    }


def generate_oauth_url(client_id: str, redirect_uri: str, scope: str = None, state: str = None) -> str:
    """
    Generate OAuth2 authorization URL for BigCommerce app installation.
    
    Args:
        client_id: OAuth2 client ID
        redirect_uri: OAuth2 redirect URI
        scope: Requested permissions scope
        state: Optional state parameter for CSRF protection
        
    Returns:
        OAuth2 authorization URL
        
    Example:
        ```python
        from taxpoynt_platform.external_integrations.business_systems.ecommerce.bigcommerce import (
            generate_oauth_url
        )
        
        url = generate_oauth_url(
            client_id='your-client-id',
            redirect_uri='https://yourapp.com/auth/callback',
            scope='store_v2_orders store_v2_products',
            state='random-state-string'
        )
        
        print(f"Install app at: {url}")
        ```
    """
    from urllib.parse import urlencode
    
    default_scope = "store_v2_orders store_v2_products store_v2_customers"
    
    params = {
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'response_type': 'code',
        'scope': scope or default_scope
    }
    
    if state:
        params['state'] = state
    
    base_url = "https://login.bigcommerce.com/oauth2/authorize"
    return f"{base_url}?{urlencode(params)}"