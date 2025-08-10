"""
Jumia E-commerce Integration Package
Comprehensive integration with Jumia marketplace for TaxPoynt eInvoice platform.

This package provides complete Jumia marketplace connectivity including:
- API key and signature-based authentication
- Seller Center API client for comprehensive marketplace operations
- Order data extraction with African marketplace support
- FIRS-compliant UBL BIS 3.0 invoice transformation
- Real-time webhook processing
- Multi-country African marketplace support

Supported Jumia Marketplaces:
- Nigeria (jumia-ng) - Primary focus
- Kenya (jumia-ke)
- Uganda (jumia-ug)
- Ghana (jumia-gh)
- Côte d'Ivoire (jumia-ci)
- Senegal (jumia-sn)
- Morocco (jumia-ma)
- Tunisia (jumia-tn)
- Algeria (jumia-dz)
- Egypt (jumia-eg)

Key Features:
- African marketplace architecture support
- Regional API endpoints and authentication
- Nigerian tax compliance (7.5% VAT)
- Real-time order processing
- Comprehensive product catalog management
- Inventory and pricing management
- Shipment and fulfillment tracking
- Payment settlement integration
- Analytics and reporting

Usage Example:
    ```python
    from taxpoynt_platform.external_integrations.business_systems.ecommerce.jumia import (
        JumiaEcommerceConnector,
        JumiaAuthManager,
        JumiaRESTClient
    )
    
    # Initialize connector for Nigeria
    config = {
        'seller_id': 'your-seller-id',
        'api_key': 'your-api-key',
        'api_secret': 'your-api-secret',
        'country_code': 'NG',  # Nigeria
        'webhook_secret': 'your-webhook-secret',
        'sandbox': False
    }
    
    connector = JumiaEcommerceConnector(config)
    
    # Connect to marketplace
    await connector.connect()
    
    # Get recent orders
    orders = await connector.get_orders(limit=10)
    
    # Transform order to UBL invoice
    if orders:
        invoice = await connector.transform_order_to_invoice(orders[0])
        print(f"Generated invoice for order {orders[0]['order_number']}")
    
    # Process webhook
    webhook_result = await connector.process_webhook(
        'order.shipped',
        {'order_id': '12345'}
    )
    
    # Get marketplace analytics
    analytics = await connector.get_analytics()
    print(f"Total orders: {analytics['summary']['total_orders']}")
    ```

Configuration Options:
    seller_id (str): Jumia seller ID (required)
    api_key (str): Jumia API key (required)
    api_secret (str): Jumia API secret for signature generation (required)
    country_code (str): ISO country code for marketplace (default: 'NG')
    marketplace (str): Specific marketplace identifier (auto-detected)
    webhook_secret (str): Secret for webhook signature verification
    sandbox (bool): Use sandbox environment for testing (default: False)
    rate_limit (dict): API rate limiting configuration
    transformer (dict): Invoice transformation settings

Nigerian Market Configuration:
    vat_rate (float): VAT rate (default: 0.075 for 7.5%)
    default_currency (str): Default currency (default: 'NGN')
    default_country (str): Default country code (default: 'NG')
    default_tin (str): Default TIN for missing tax IDs
    seller_tin (str): Seller's Tax Identification Number
    seller_name (str): Seller business name
    seller_address (dict): Seller business address

African Marketplace Support:
    Jumia operates across 10+ African countries with localized:
    - Currency support (NGN, KES, UGX, GHS, etc.)
    - Language localization
    - Regional payment methods
    - Local fulfillment networks
    - Country-specific regulations
    
    The connector automatically handles regional differences
    based on the configured country_code.

Authentication Methods:
    1. API Key Authentication (Required):
       - Seller-specific API key and secret
       - HMAC-SHA256 signature generation
       - Timestamp-based request signing
       - Automatic signature rotation
       
    2. Webhook Verification:
       - HMAC-SHA256 signature verification
       - Timestamp validation
       - Payload integrity checking

API Capabilities:
    - Complete Jumia Seller Center API v3 coverage
    - Conservative rate limiting (60 requests/minute)
    - Comprehensive error handling with retry logic
    - Pagination support for large datasets
    - Regional marketplace endpoint routing
    - Multi-language response handling

Seller Operations:
    - Order management and status updates
    - Product catalog management (CRUD operations)
    - Inventory management and stock updates
    - Pricing management with bulk updates
    - Shipment creation and tracking
    - Returns and refunds processing
    - Payment settlement tracking
    - Quality control status monitoring
    - Performance analytics and reporting

Webhook Support:
    Supported webhook events:
    - order.created: New order placement
    - order.shipped: Order shipment notification
    - order.delivered: Delivery confirmation
    - order.returned: Return initiation
    - product.created: New product addition
    - product.updated: Product information changes
    - shipment.created: New shipment creation
    - shipment.updated: Shipment status changes
    
    Features:
    - HMAC-SHA256 signature verification
    - Timestamp validation for replay protection
    - Automatic invoice generation for eligible orders
    - Real-time inventory synchronization
    - Event-driven architecture

Error Handling:
    Custom exception hierarchy:
    - JumiaConnectionError: Connection issues
    - JumiaAuthenticationError: Auth failures
    - JumiaDataExtractionError: Data retrieval issues
    - JumiaTransformationError: Invoice transformation issues
    - JumiaAPIError: General API errors
    - JumiaRateLimitError: Rate limiting issues
    - JumiaMarketplaceError: Marketplace-specific errors
    - JumiaRegionalError: Regional operation errors

Dependencies:
    - aiohttp: Async HTTP client
    - python-dateutil: Date/time parsing
    - cryptography: Signature verification
    - pydantic: Data validation (optional)

Thread Safety:
    All components are designed for async/await usage and are thread-safe
    when used within the same event loop. Multiple connectors can be
    instantiated for different marketplaces simultaneously.

Performance Considerations:
    - Connection pooling for HTTP requests
    - Conservative rate limiting (60 requests/minute)
    - Efficient pagination for large datasets
    - Regional endpoint optimization
    - Caching for seller configuration data
    - Batch operations where possible

African E-commerce Features:
    - Multi-currency support (NGN, KES, UGX, etc.)
    - Local payment method integration
    - Regional fulfillment networks (JFS)
    - Cross-border logistics
    - Local language support
    - Cultural customization
    - Regional compliance handling

Nigerian Market Specialization:
    - 7.5% VAT compliance
    - Naira (NGN) currency handling
    - Lagos and Abuja logistics hubs
    - Local payment gateways (Paystack, Flutterwave)
    - FIRS tax regulation compliance
    - TIN validation and management
    - Nigerian address formatting

Integration Notes:
    - Follows TaxPoynt eInvoice platform patterns
    - Implements BaseEcommerceConnector interface
    - Nigerian tax compliance built-in
    - UBL BIS 3.0 invoice generation
    - FIRS regulatory compliance
    - Multi-marketplace transaction attribution

For detailed documentation and examples, see the individual module docstrings
and the TaxPoynt eInvoice platform documentation.
"""

from .connector import JumiaEcommerceConnector
from .auth import JumiaAuthManager
from .rest_client import JumiaRESTClient
from .data_extractor import JumiaDataExtractor
from .order_transformer import JumiaOrderTransformer
from .exceptions import (
    JumiaConnectionError,
    JumiaAuthenticationError,
    JumiaDataExtractionError,
    JumiaTransformationError,
    JumiaAPIError,
    JumiaOrderNotFoundError,
    JumiaProductNotFoundError,
    JumiaSellerNotFoundError,
    JumiaRateLimitError,
    JumiaMarketplaceError,
    JumiaInventoryError,
    JumiaFulfillmentError,
    JumiaPaymentError,
    JumiaCategoryError,
    JumiaRegionalError,
    JumiaComplianceError,
    get_marketplace_code,
    get_supported_countries,
    JUMIA_MARKETPLACES
)

# Package metadata
__version__ = "1.0.0"
__author__ = "TaxPoynt Development Team"
__email__ = "dev@taxpoynt.com"
__description__ = "Jumia marketplace integration for TaxPoynt eInvoice platform"

# Supported African countries and marketplaces
SUPPORTED_COUNTRIES = list(JUMIA_MARKETPLACES.keys())

# Default configuration
DEFAULT_CONFIG = {
    'country_code': 'NG',  # Default to Nigeria
    'sandbox': False,
    'rate_limit': {
        'requests_per_minute': 60,
        'burst_capacity': 5
    },
    'transformer': {
        'vat_rate': 0.075,
        'default_currency': 'NGN',
        'default_country': 'NG',
        'default_tin': '00000000-0001',
        'seller_name': 'Jumia Seller',
        'seller_address': {
            'street': 'Victoria Island',
            'city': 'Lagos',
            'postcode': '100001',
            'region': 'Lagos State',
            'country_id': 'NG'
        }
    },
    'webhook': {
        'timeout': 30,
        'retry_attempts': 3
    },
    'timeout': {
        'total': 60,
        'connect': 15,
        'read': 45
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
    'JumiaEcommerceConnector',
    
    # Core components
    'JumiaAuthManager',
    'JumiaRESTClient', 
    'JumiaDataExtractor',
    'JumiaOrderTransformer',
    
    # Exceptions
    'JumiaConnectionError',
    'JumiaAuthenticationError',
    'JumiaDataExtractionError',
    'JumiaTransformationError',
    'JumiaAPIError',
    'JumiaOrderNotFoundError',
    'JumiaProductNotFoundError',
    'JumiaSellerNotFoundError',
    'JumiaRateLimitError',
    'JumiaMarketplaceError',
    'JumiaInventoryError',
    'JumiaFulfillmentError',
    'JumiaPaymentError',
    'JumiaCategoryError',
    'JumiaRegionalError',
    'JumiaComplianceError',
    
    # Utility functions
    'get_marketplace_code',
    'get_supported_countries',
    
    # Configuration
    'DEFAULT_CONFIG',
    'SUPPORTED_COUNTRIES',
    'JUMIA_MARKETPLACES',
    
    # Metadata
    '__version__',
    '__author__',
    '__email__',
    '__description__'
]


def create_connector(config: dict) -> JumiaEcommerceConnector:
    """
    Factory function to create a Jumia e-commerce connector.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Configured JumiaEcommerceConnector instance
        
    Example:
        ```python
        from taxpoynt_platform.external_integrations.business_systems.ecommerce.jumia import (
            create_connector
        )
        
        config = {
            'seller_id': 'your-seller-id',
            'api_key': 'your-api-key',
            'api_secret': 'your-api-secret',
            'country_code': 'NG'
        }
        
        connector = create_connector(config)
        await connector.connect()
        ```
    """
    # Merge with default configuration
    merged_config = {**DEFAULT_CONFIG, **config}
    return JumiaEcommerceConnector(merged_config)


def validate_config(config: dict) -> dict:
    """
    Validate Jumia connector configuration.
    
    Args:
        config: Configuration dictionary to validate
        
    Returns:
        Dictionary with validation results
        
    Example:
        ```python
        from taxpoynt_platform.external_integrations.business_systems.ecommerce.jumia import (
            validate_config
        )
        
        config = {
            'seller_id': 'seller123',
            'api_key': 'key123',
            'api_secret': 'secret123'
        }
        result = validate_config(config)
        
        if not result['valid']:
            print("Configuration errors:", result['errors'])
        ```
    """
    errors = []
    warnings = []
    
    # Required fields
    required_fields = ['seller_id', 'api_key', 'api_secret']
    for field in required_fields:
        if field not in config:
            errors.append(f"Missing required field: {field}")
    
    # Country code validation
    country_code = config.get('country_code', 'NG')
    if country_code not in SUPPORTED_COUNTRIES:
        errors.append(f"Unsupported country code: {country_code}. Supported: {', '.join(SUPPORTED_COUNTRIES)}")
    
    # Seller ID validation
    seller_id = config.get('seller_id', '')
    if seller_id and not seller_id.strip():
        errors.append("seller_id cannot be empty")
    
    # API credentials validation
    api_key = config.get('api_key', '')
    api_secret = config.get('api_secret', '')
    
    if api_key and len(api_key) < 10:
        warnings.append("API key appears to be too short")
    
    if api_secret and len(api_secret) < 10:
        warnings.append("API secret appears to be too short")
    
    # TIN validation for Nigerian compliance
    transformer_config = config.get('transformer', {})
    seller_tin = transformer_config.get('seller_tin')
    if not seller_tin and country_code == 'NG':
        warnings.append("seller_tin not provided - required for Nigerian tax compliance")
    
    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'warnings': warnings,
        'config': {**DEFAULT_CONFIG, **config}
    }


def get_marketplace_info(country_code: str) -> dict:
    """
    Get marketplace information for a country.
    
    Args:
        country_code: ISO 3166-1 alpha-2 country code
        
    Returns:
        Dictionary with marketplace information
        
    Example:
        ```python
        from taxpoynt_platform.external_integrations.business_systems.ecommerce.jumia import (
            get_marketplace_info
        )
        
        info = get_marketplace_info('NG')
        print(f"Marketplace: {info['marketplace']}")
        print(f"Currency: {info['currency']}")
        ```
    """
    marketplace_info = {
        'NG': {
            'marketplace': 'jumia-ng',
            'name': 'Jumia Nigeria',
            'currency': 'NGN',
            'domain': 'jumia.com.ng',
            'language': 'en',
            'timezone': 'Africa/Lagos'
        },
        'KE': {
            'marketplace': 'jumia-ke',
            'name': 'Jumia Kenya',
            'currency': 'KES',
            'domain': 'jumia.co.ke',
            'language': 'en',
            'timezone': 'Africa/Nairobi'
        },
        'UG': {
            'marketplace': 'jumia-ug',
            'name': 'Jumia Uganda',
            'currency': 'UGX',
            'domain': 'jumia.co.ug',
            'language': 'en',
            'timezone': 'Africa/Kampala'
        },
        'GH': {
            'marketplace': 'jumia-gh',
            'name': 'Jumia Ghana',
            'currency': 'GHS',
            'domain': 'jumia.com.gh',
            'language': 'en',
            'timezone': 'Africa/Accra'
        },
        'CI': {
            'marketplace': 'jumia-ci',
            'name': 'Jumia Côte d\'Ivoire',
            'currency': 'XOF',
            'domain': 'jumia.ci',
            'language': 'fr',
            'timezone': 'Africa/Abidjan'
        },
        'SN': {
            'marketplace': 'jumia-sn',
            'name': 'Jumia Senegal',
            'currency': 'XOF',
            'domain': 'jumia.sn',
            'language': 'fr',
            'timezone': 'Africa/Dakar'
        },
        'MA': {
            'marketplace': 'jumia-ma',
            'name': 'Jumia Morocco',
            'currency': 'MAD',
            'domain': 'jumia.ma',
            'language': 'ar',
            'timezone': 'Africa/Casablanca'
        },
        'TN': {
            'marketplace': 'jumia-tn',
            'name': 'Jumia Tunisia',
            'currency': 'TND',
            'domain': 'jumia.com.tn',
            'language': 'ar',
            'timezone': 'Africa/Tunis'
        },
        'DZ': {
            'marketplace': 'jumia-dz',
            'name': 'Jumia Algeria',
            'currency': 'DZD',
            'domain': 'jumia.dz',
            'language': 'ar',
            'timezone': 'Africa/Algiers'
        },
        'EG': {
            'marketplace': 'jumia-eg',
            'name': 'Jumia Egypt',
            'currency': 'EGP',
            'domain': 'jumia.com.eg',
            'language': 'ar',
            'timezone': 'Africa/Cairo'
        }
    }
    
    return marketplace_info.get(country_code.upper(), {
        'marketplace': f'jumia-{country_code.lower()}',
        'name': f'Jumia {country_code.upper()}',
        'currency': 'USD',
        'domain': 'jumia.com',
        'language': 'en',
        'timezone': 'UTC'
    })