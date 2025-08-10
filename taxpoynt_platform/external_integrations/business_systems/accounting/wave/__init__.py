"""
Wave Accounting Integration
Complete connector implementation for Wave Accounting e-invoicing integration.
"""
from .connector import WaveConnector
from .auth import WaveAuthManager
from .rest_client import WaveRestClient
from .data_extractor import WaveDataExtractor
from .ubl_transformer import WaveUBLTransformer
from .exceptions import (
    WaveException,
    WaveAuthenticationError,
    WaveAuthorizationError,
    WaveAPIError,
    WaveRateLimitError,
    WaveConnectionError,
    WaveConfigurationError,
    WaveDataError,
    WaveBusinessNotFoundError,
    WaveCustomerNotFoundError,
    WaveInvoiceNotFoundError,
    WaveProductNotFoundError,
    WaveValidationError,
    WaveTransformationError,
    WaveSyncError,
    WaveQuotaExceededError,
    WaveMaintenanceError,
    WaveDeprecationError
)


__version__ = "1.0.0"
__author__ = "TaxPoynt Development Team"
__email__ = "dev@taxpoynt.com"

# Package metadata
__title__ = "Wave Accounting Integration"
__description__ = "Complete Wave Accounting connector for Nigerian e-invoicing compliance"
__url__ = "https://github.com/taxpoynt/taxpoynt-platform"
__license__ = "MIT"
__copyright__ = "Copyright 2024 TaxPoynt"

# Export main classes
__all__ = [
    # Main connector
    "WaveConnector",
    
    # Core components
    "WaveAuthManager",
    "WaveRestClient", 
    "WaveDataExtractor",
    "WaveUBLTransformer",
    
    # Exceptions
    "WaveException",
    "WaveAuthenticationError",
    "WaveAuthorizationError",
    "WaveAPIError",
    "WaveRateLimitError",
    "WaveConnectionError",
    "WaveConfigurationError",
    "WaveDataError",
    "WaveBusinessNotFoundError",
    "WaveCustomerNotFoundError",
    "WaveInvoiceNotFoundError",
    "WaveProductNotFoundError",
    "WaveValidationError",
    "WaveTransformationError",
    "WaveSyncError",
    "WaveQuotaExceededError",
    "WaveMaintenanceError",
    "WaveDeprecationError",
    
    # Factory functions
    "create_wave_connector",
    "create_wave_connector_from_config",
    
    # Utility functions
    "validate_wave_config",
    "get_wave_oauth_scopes",
    "is_wave_webhook_valid"
]


def create_wave_connector(
    client_id: str,
    client_secret: str,
    redirect_uri: str,
    sandbox: bool = True,
    session=None
) -> WaveConnector:
    """
    Create a new Wave connector instance.
    
    Args:
        client_id: Wave application client ID
        client_secret: Wave application client secret  
        redirect_uri: OAuth2 redirect URI
        sandbox: Whether to use sandbox environment
        session: Optional aiohttp session
        
    Returns:
        Configured Wave connector
        
    Example:
        >>> connector = create_wave_connector(
        ...     client_id="your_client_id",
        ...     client_secret="your_client_secret",
        ...     redirect_uri="https://your-app.com/callback",
        ...     sandbox=True
        ... )
        >>> 
        >>> # Start OAuth flow
        >>> auth_url, verifier, state = connector.get_authorization_url()
        >>> print(f"Visit: {auth_url}")
        >>> 
        >>> # After user authorization
        >>> await connector.authenticate_with_code(auth_code, verifier, state)
        >>> 
        >>> # Select business and get invoices
        >>> businesses = await connector.list_businesses()
        >>> await connector.select_business(businesses[0]["id"])
        >>> invoices = await connector.get_invoices()
    """
    return WaveConnector(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        sandbox=sandbox,
        session=session
    )


def create_wave_connector_from_config(config: dict, session=None) -> WaveConnector:
    """
    Create Wave connector from configuration dictionary.
    
    Args:
        config: Configuration dictionary containing Wave settings
        session: Optional aiohttp session
        
    Returns:
        Configured Wave connector
        
    Config format:
        {
            "client_id": "wave_client_id",
            "client_secret": "wave_client_secret", 
            "redirect_uri": "https://your-app.com/callback",
            "sandbox": true,
            "business_id": "optional_default_business_id"
        }
        
    Example:
        >>> config = {
        ...     "client_id": "your_client_id",
        ...     "client_secret": "your_client_secret",
        ...     "redirect_uri": "https://your-app.com/callback",
        ...     "sandbox": True
        ... }
        >>> connector = create_wave_connector_from_config(config)
    """
    validate_wave_config(config)
    
    return WaveConnector(
        client_id=config["client_id"],
        client_secret=config["client_secret"], 
        redirect_uri=config["redirect_uri"],
        sandbox=config.get("sandbox", True),
        session=session
    )


def validate_wave_config(config: dict) -> None:
    """
    Validate Wave configuration dictionary.
    
    Args:
        config: Configuration dictionary to validate
        
    Raises:
        WaveConfigurationError: If configuration is invalid
        
    Example:
        >>> config = {"client_id": "id", "client_secret": "secret", "redirect_uri": "https://app.com/cb"}
        >>> validate_wave_config(config)  # No exception = valid
    """
    required_fields = ["client_id", "client_secret", "redirect_uri"]
    
    for field in required_fields:
        if field not in config:
            raise WaveConfigurationError(f"Missing required field: {field}")
        if not config[field]:
            raise WaveConfigurationError(f"Empty value for required field: {field}")
    
    # Validate redirect URI format
    redirect_uri = config["redirect_uri"]
    if not redirect_uri.startswith(("http://", "https://")):
        raise WaveConfigurationError("Redirect URI must start with http:// or https://")
    
    # Validate sandbox setting
    if "sandbox" in config and not isinstance(config["sandbox"], bool):
        raise WaveConfigurationError("Sandbox setting must be boolean")


def get_wave_oauth_scopes() -> list:
    """
    Get list of OAuth2 scopes required for Wave integration.
    
    Returns:
        List of required OAuth2 scopes
        
    Example:
        >>> scopes = get_wave_oauth_scopes()
        >>> print(scopes)
        ['businesses.read', 'customers.read', 'customers.write', ...]
    """
    return [
        "businesses.read",
        "customers.read", 
        "customers.write",
        "products.read",
        "products.write", 
        "invoices.read",
        "invoices.write",
        "sales.read"
    ]


def is_wave_webhook_valid(payload: bytes, signature: str, secret: str) -> bool:
    """
    Validate Wave webhook signature.
    
    Args:
        payload: Raw webhook payload bytes
        signature: Webhook signature from headers
        secret: Webhook secret for validation
        
    Returns:
        True if signature is valid
        
    Example:
        >>> is_valid = is_wave_webhook_valid(payload, signature, webhook_secret)
        >>> if is_valid:
        ...     process_webhook(payload)
    """
    import hmac
    import hashlib
    
    try:
        # Wave uses HMAC-SHA256 for webhook signatures
        expected_signature = hmac.new(
            secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        # Remove 'sha256=' prefix if present
        if signature.startswith("sha256="):
            signature = signature[7:]
        
        return hmac.compare_digest(expected_signature, signature)
    except Exception:
        return False


# Platform information
PLATFORM_INFO = {
    "name": "Wave Accounting",
    "type": "accounting",
    "vendor": "Wave Financial Inc.",
    "api_version": "2023-01",
    "api_type": "GraphQL",
    "authentication": "OAuth2 + PKCE",
    "documentation": "https://developer.waveapps.com/hc/en-us",
    "supported_regions": ["US", "CA", "NG"],
    "supported_currencies": ["USD", "CAD", "NGN", "EUR", "GBP"],
    "rate_limits": {
        "requests_per_minute": 60,
        "burst_limit": 10
    },
    "features": {
        "multi_business": True,
        "real_time_sync": True, 
        "webhook_support": True,
        "batch_operations": True,
        "custom_fields": False,
        "file_attachments": False
    },
    "compliance": {
        "firs_einvoicing": True,
        "ubl_2_1": True,
        "nigerian_vat": True,
        "multi_currency": True
    }
}


# Supported countries and their tax configurations
SUPPORTED_COUNTRIES = {
    "NG": {
        "name": "Nigeria",
        "currency": "NGN",
        "vat_rate": 7.5,
        "tax_identifier": "TIN",
        "einvoice_required": True,
        "firs_compliance": True
    },
    "US": {
        "name": "United States", 
        "currency": "USD",
        "sales_tax": "varies_by_state",
        "tax_identifier": "EIN",
        "einvoice_required": False,
        "firs_compliance": False
    },
    "CA": {
        "name": "Canada",
        "currency": "CAD", 
        "gst_rate": 5.0,
        "tax_identifier": "GST/HST",
        "einvoice_required": False,
        "firs_compliance": False
    }
}


# Integration examples and documentation
INTEGRATION_EXAMPLES = {
    "basic_setup": '''
# Basic Wave integration setup
from taxpoynt_platform.external_integrations.business_systems.accounting.wave import create_wave_connector

async def setup_wave_integration():
    connector = create_wave_connector(
        client_id="your_wave_client_id",
        client_secret="your_wave_client_secret",
        redirect_uri="https://your-app.com/oauth/callback",
        sandbox=True  # Use False for production
    )
    
    # Get authorization URL
    auth_url, code_verifier, state = connector.get_authorization_url()
    print(f"Please visit: {auth_url}")
    
    # After user authorization, exchange code for tokens
    auth_code = input("Enter authorization code: ")
    await connector.authenticate_with_code(auth_code, code_verifier, state)
    
    return connector
''',
    
    "invoice_extraction": '''
# Extract and convert invoices to UBL
async def extract_invoices_for_einvoicing(connector, business_id):
    # Select business
    await connector.select_business(business_id)
    
    # Get recent invoices
    from datetime import datetime, timedelta
    since_date = datetime.utcnow() - timedelta(days=30)
    
    invoices = await connector.get_invoices(
        modified_since=since_date,
        status_filter="SENT"  # Only sent invoices
    )
    
    # Convert to UBL format for FIRS submission
    ubl_invoices = []
    for invoice in invoices:
        ubl_invoice = await connector.convert_invoice_to_ubl(
            invoice_id=invoice["id"],
            include_customer_details=True
        )
        ubl_invoices.append(ubl_invoice)
    
    return ubl_invoices
''',
    
    "batch_processing": '''
# Batch process multiple invoices
async def batch_process_invoices(connector, invoice_ids):
    ubl_invoices = await connector.batch_convert_invoices_to_ubl(
        invoice_ids=invoice_ids,
        include_customer_details=True
    )
    
    # Process UBL invoices for FIRS submission
    for ubl_invoice in ubl_invoices:
        # Submit to FIRS e-invoicing API
        # await submit_to_firs(ubl_invoice)
        pass
    
    return len(ubl_invoices)
''',
    
    "error_handling": '''
# Comprehensive error handling
from taxpoynt_platform.external_integrations.business_systems.accounting.wave import (
    WaveException, WaveAuthenticationError, WaveRateLimitError
)

async def robust_wave_integration():
    try:
        connector = create_wave_connector(...)
        
        # Test connection
        test_result = await connector.test_connection()
        if not test_result["success"]:
            raise WaveConnectionError(f"Connection failed: {test_result['error']}")
        
        # Your integration logic here
        
    except WaveAuthenticationError as e:
        logger.error(f"Authentication failed: {e}")
        # Redirect to re-authorization
        
    except WaveRateLimitError as e:
        logger.warning(f"Rate limited, retry after {e.retry_after} seconds")
        await asyncio.sleep(e.retry_after)
        
    except WaveException as e:
        logger.error(f"Wave integration error: {e}")
        # Handle other Wave-specific errors
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise
'''
}


# Testing and development utilities
TESTING_REQUIREMENTS = {
    "unit_tests": [
        "pytest>=7.0.0",
        "pytest-asyncio>=0.21.0", 
        "aioresponses>=0.7.4",
        "factory-boy>=3.2.1"
    ],
    "integration_tests": [
        "wave-test-credentials",
        "sandbox-environment-access"
    ],
    "mock_data": "tests/fixtures/wave_mock_data.json",
    "test_config": {
        "sandbox_base_url": "https://gql.waveapps.com",
        "test_business_id": "test_business_123",
        "test_redirect_uri": "http://localhost:8000/callback"
    }
}


# Troubleshooting guide
TROUBLESHOOTING = {
    "authentication_failed": {
        "symptoms": ["401 Unauthorized", "Invalid token", "Token expired"],
        "solutions": [
            "Verify client credentials are correct",
            "Check redirect URI matches Wave app configuration", 
            "Ensure OAuth scopes include required permissions",
            "Refresh tokens if expired"
        ]
    },
    "rate_limit_exceeded": {
        "symptoms": ["429 Too Many Requests", "Rate limit error"],
        "solutions": [
            "Implement exponential backoff retry logic",
            "Reduce request frequency",
            "Use batch operations where possible",
            "Monitor rate limit headers"
        ]
    },
    "graphql_errors": {
        "symptoms": ["GraphQL query errors", "Field not found"],
        "solutions": [
            "Check Wave API documentation for schema changes",
            "Verify query syntax and field names",
            "Ensure business has required data",
            "Handle partial data gracefully"
        ]
    }
}