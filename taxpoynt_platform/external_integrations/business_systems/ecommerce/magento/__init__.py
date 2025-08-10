"""
Magento E-commerce Integration Package
Comprehensive integration with Magento/Adobe Commerce e-commerce platform for TaxPoynt eInvoice platform.

This package provides complete Magento e-commerce connectivity including:
- Integration token and Bearer authentication
- REST API client for comprehensive store operations
- Order data extraction with multi-store support
- FIRS-compliant UBL BIS 3.0 invoice transformation
- Real-time webhook processing
- Multi-store and Adobe Commerce support

Supported Magento Versions:
- Magento Open Source 2.3+
- Adobe Commerce 2.3+
- Adobe Commerce Cloud

Key Features:
- Multi-store architecture support
- Advanced search and filtering capabilities
- Nigerian tax compliance (7.5% VAT)
- Real-time order processing
- Comprehensive product catalog management
- Customer data integration
- Analytics and reporting

Usage Example:
    ```python
    from taxpoynt_platform.external_integrations.business_systems.ecommerce.magento import (
        MagentoEcommerceConnector,
        MagentoAuthManager,
        MagentoRESTClient
    )
    
    # Initialize connector
    config = {
        'base_url': 'https://your-magento-store.com',
        'auth_type': 'integration',
        'integration_token': 'your-integration-token',
        'store_id': 1,
        'webhook_secret': 'your-webhook-secret'
    }
    
    connector = MagentoEcommerceConnector(config)
    
    # Connect to store
    await connector.connect()
    
    # Get recent orders
    orders = await connector.get_orders(limit=10)
    
    # Transform order to UBL invoice
    if orders:
        invoice = await connector.transform_order_to_invoice(orders[0])
        print(f"Generated invoice for order {orders[0]['increment_id']}")
    
    # Process webhook
    webhook_result = await connector.process_webhook(
        'sales_order_save_after',
        {'entity_id': '123'}
    )
    ```

Configuration Options:
    base_url (str): Magento store base URL
    auth_type (str): Authentication type ('integration', 'bearer', 'customer')
    integration_token (str): Integration access token (recommended)
    username (str): Admin username (for bearer auth)
    password (str): Admin password (for bearer auth)
    store_id (int): Default store ID for multi-store operations
    webhook_secret (str): Secret for webhook signature verification
    rate_limit (dict): API rate limiting configuration
    transformer (dict): Invoice transformation settings

Nigerian Market Configuration:
    vat_rate (float): VAT rate (default: 0.075 for 7.5%)
    default_currency (str): Default currency (default: 'NGN')
    default_country (str): Default country code (default: 'NG')
    default_tin (str): Default TIN for missing tax IDs

Multi-Store Support:
    The connector supports Magento's multi-store architecture:
    - Store views for different languages/locales  
    - Websites for different domains/customer groups
    - Store groups for organizing related stores
    
    Store-specific operations can be performed by specifying store_id
    in method calls or configuring a default store_id.

Adobe Commerce Features:
    Enhanced support for Adobe Commerce (formerly Magento Commerce):
    - B2B functionality
    - Advanced catalog management
    - Staging and preview
    - Page Builder integration
    - Advanced reporting
    - Customer segmentation

Authentication Methods:
    1. Integration Token (Recommended):
       - Secure token-based authentication
       - Granular permission control
       - No password storage required
       
    2. Bearer Token:
       - Admin user credentials
       - Full API access
       - Token expiration handling
       
    3. Customer Token:
       - Customer-specific operations
       - Limited scope access
       - Customer account integration

API Capabilities:
    - Complete REST API v1 coverage
    - Advanced search criteria with filters
    - Batch operations for efficiency
    - Multi-store endpoint support
    - Rate limiting and retry logic
    - Comprehensive error handling

Webhook Support:
    Supported webhook events:
    - sales_order_save_after: Order creation/updates
    - customer_save_after: Customer creation/updates
    - catalog_product_save_after: Product creation/updates
    
    Features:
    - HMAC-SHA256 signature verification
    - Automatic invoice generation for eligible orders
    - Real-time data synchronization
    - Event-driven architecture

Error Handling:
    Custom exception hierarchy:
    - MagentoConnectionError: Connection issues
    - MagentoAuthenticationError: Auth failures
    - MagentoDataExtractionError: Data retrieval issues
    - MagentoTransformationError: Invoice transformation issues
    - MagentoAPIError: General API errors

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
    - Rate limiting compliance (300 requests/hour default)
    - Efficient pagination for large datasets
    - Caching for store configuration data
    - Batch operations where possible

Integration Notes:
    - Follows TaxPoynt eInvoice platform patterns
    - Implements BaseEcommerceConnector interface
    - Nigerian tax compliance built-in
    - UBL BIS 3.0 invoice generation
    - FIRS regulatory compliance

For detailed documentation and examples, see the individual module docstrings
and the TaxPoynt eInvoice platform documentation.
"""

from .connector import MagentoEcommerceConnector
from .auth import MagentoAuthManager
from .rest_client import MagentoRESTClient
from .data_extractor import MagentoDataExtractor
from .order_transformer import MagentoOrderTransformer
from .exceptions import (
    MagentoConnectionError,
    MagentoAuthenticationError,
    MagentoDataExtractionError,
    MagentoTransformationError,
    MagentoAPIError,
    MagentoOrderNotFoundError,
    MagentoCustomerNotFoundError,
    MagentoProductNotFoundError,
    MagentoStoreNotFoundError,
    MagentoRateLimitError,
    MagentoMultiStoreError,
    MagentoExtensionError
)

# Package metadata
__version__ = "1.0.0"
__author__ = "TaxPoynt Development Team"
__email__ = "dev@taxpoynt.com"
__description__ = "Magento/Adobe Commerce e-commerce integration for TaxPoynt eInvoice platform"

# Supported Magento versions
SUPPORTED_VERSIONS = [
    "2.3.x",
    "2.4.x",
    "Adobe Commerce 2.3.x",
    "Adobe Commerce 2.4.x",
    "Adobe Commerce Cloud"
]

# Default configuration
DEFAULT_CONFIG = {
    'auth_type': 'integration',
    'rate_limit': {
        'requests_per_hour': 300,
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
    }
}

# Export main classes and functions
__all__ = [
    # Main connector
    'MagentoEcommerceConnector',
    
    # Core components
    'MagentoAuthManager',
    'MagentoRESTClient', 
    'MagentoDataExtractor',
    'MagentoOrderTransformer',
    
    # Exceptions
    'MagentoConnectionError',
    'MagentoAuthenticationError',
    'MagentoDataExtractionError',
    'MagentoTransformationError',
    'MagentoAPIError',
    'MagentoOrderNotFoundError',
    'MagentoCustomerNotFoundError',
    'MagentoProductNotFoundError',
    'MagentoStoreNotFoundError',
    'MagentoRateLimitError',
    'MagentoMultiStoreError',
    'MagentoExtensionError',
    
    # Configuration
    'DEFAULT_CONFIG',
    'SUPPORTED_VERSIONS',
    
    # Metadata
    '__version__',
    '__author__',
    '__email__',
    '__description__'
]


def create_connector(config: dict) -> MagentoEcommerceConnector:
    """
    Factory function to create a Magento e-commerce connector.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Configured MagentoEcommerceConnector instance
        
    Example:
        ```python
        from taxpoynt_platform.external_integrations.business_systems.ecommerce.magento import (
            create_connector
        )
        
        config = {
            'base_url': 'https://your-magento-store.com',
            'auth_type': 'integration',
            'integration_token': 'your-token'
        }
        
        connector = create_connector(config)
        await connector.connect()
        ```
    """
    # Merge with default configuration
    merged_config = {**DEFAULT_CONFIG, **config}
    return MagentoEcommerceConnector(merged_config)


def get_supported_versions() -> list:
    """
    Get list of supported Magento versions.
    
    Returns:
        List of supported version strings
    """
    return SUPPORTED_VERSIONS.copy()


def validate_config(config: dict) -> dict:
    """
    Validate Magento connector configuration.
    
    Args:
        config: Configuration dictionary to validate
        
    Returns:
        Dictionary with validation results
        
    Example:
        ```python
        from taxpoynt_platform.external_integrations.business_systems.ecommerce.magento import (
            validate_config
        )
        
        config = {'base_url': 'https://store.com'}
        result = validate_config(config)
        
        if not result['valid']:
            print("Configuration errors:", result['errors'])
        ```
    """
    errors = []
    warnings = []
    
    # Required fields
    required_fields = ['base_url']
    for field in required_fields:
        if field not in config:
            errors.append(f"Missing required field: {field}")
    
    # Authentication validation
    auth_type = config.get('auth_type', 'integration')
    if auth_type == 'integration':
        if not config.get('integration_token'):
            errors.append("integration_token required for integration auth")
    elif auth_type == 'bearer':
        if not config.get('username') or not config.get('password'):
            errors.append("username and password required for bearer auth")
    
    # URL validation
    base_url = config.get('base_url', '')
    if base_url and not base_url.startswith(('http://', 'https://')):
        errors.append("base_url must start with http:// or https://")
    
    # TIN validation for Nigerian compliance
    transformer_config = config.get('transformer', {})
    default_tin = transformer_config.get('default_tin', DEFAULT_CONFIG['transformer']['default_tin'])
    if default_tin == DEFAULT_CONFIG['transformer']['default_tin']:
        warnings.append("Using default TIN - should be updated with actual TIN for compliance")
    
    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'warnings': warnings,
        'config': {**DEFAULT_CONFIG, **config}
    }