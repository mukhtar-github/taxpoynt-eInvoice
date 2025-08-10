"""
FreshBooks Integration
Complete connector implementation for FreshBooks e-invoicing integration.
"""
from .connector import FreshBooksConnector
from .auth import FreshBooksAuthManager
from .rest_client import FreshBooksRestClient
from .data_extractor import FreshBooksDataExtractor
from .ubl_transformer import FreshBooksUBLTransformer
from .exceptions import (
    FreshBooksException,
    FreshBooksAuthenticationError,
    FreshBooksAuthorizationError,
    FreshBooksAPIError,
    FreshBooksRateLimitError,
    FreshBooksConnectionError,
    FreshBooksConfigurationError,
    FreshBooksDataError,
    FreshBooksAccountNotFoundError,
    FreshBooksClientNotFoundError,
    FreshBooksInvoiceNotFoundError,
    FreshBooksItemNotFoundError,
    FreshBooksValidationError,
    FreshBooksTransformationError,
    FreshBooksSyncError,
    FreshBooksQuotaExceededError,
    FreshBooksMaintenanceError,
    FreshBooksDeprecationError,
    FreshBooksWebhookError,
    FreshBooksPermissionError
)


__version__ = "1.0.0"
__author__ = "TaxPoynt Development Team"
__email__ = "dev@taxpoynt.com"

# Package metadata
__title__ = "FreshBooks Integration"
__description__ = "Complete FreshBooks connector for Nigerian e-invoicing compliance"
__url__ = "https://github.com/taxpoynt/taxpoynt-platform"
__license__ = "MIT"
__copyright__ = "Copyright 2024 TaxPoynt"

# Export main classes
__all__ = [
    # Main connector
    "FreshBooksConnector",
    
    # Core components
    "FreshBooksAuthManager",
    "FreshBooksRestClient", 
    "FreshBooksDataExtractor",
    "FreshBooksUBLTransformer",
    
    # Exceptions
    "FreshBooksException",
    "FreshBooksAuthenticationError",
    "FreshBooksAuthorizationError",
    "FreshBooksAPIError",
    "FreshBooksRateLimitError",
    "FreshBooksConnectionError",
    "FreshBooksConfigurationError",
    "FreshBooksDataError",
    "FreshBooksAccountNotFoundError",
    "FreshBooksClientNotFoundError",
    "FreshBooksInvoiceNotFoundError",
    "FreshBooksItemNotFoundError",
    "FreshBooksValidationError",
    "FreshBooksTransformationError",
    "FreshBooksSyncError",
    "FreshBooksQuotaExceededError",
    "FreshBooksMaintenanceError",
    "FreshBooksDeprecationError",
    "FreshBooksWebhookError",
    "FreshBooksPermissionError",
    
    # Factory functions
    "create_freshbooks_connector",
    "create_freshbooks_connector_from_config",
    
    # Utility functions
    "validate_freshbooks_config",
    "get_freshbooks_oauth_scopes",
    "is_freshbooks_webhook_valid"
]


def create_freshbooks_connector(
    client_id: str,
    client_secret: str,
    redirect_uri: str,
    sandbox: bool = True,
    session=None
) -> FreshBooksConnector:
    """
    Create a new FreshBooks connector instance.
    
    Args:
        client_id: FreshBooks application client ID
        client_secret: FreshBooks application client secret  
        redirect_uri: OAuth2 redirect URI
        sandbox: Whether to use sandbox environment
        session: Optional aiohttp session
        
    Returns:
        Configured FreshBooks connector
        
    Example:
        >>> connector = create_freshbooks_connector(
        ...     client_id="your_client_id",
        ...     client_secret="your_client_secret",
        ...     redirect_uri="https://your-app.com/callback",
        ...     sandbox=True
        ... )
        >>> 
        >>> # Start OAuth flow
        >>> auth_url, state = connector.get_authorization_url()
        >>> print(f"Visit: {auth_url}")
        >>> 
        >>> # After user authorization
        >>> await connector.authenticate_with_code(auth_code, state)
        >>> 
        >>> # Get account info and invoices
        >>> account_info = await connector.get_account_info()
        >>> invoices = await connector.get_invoices()
    """
    return FreshBooksConnector(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        sandbox=sandbox,
        session=session
    )


def create_freshbooks_connector_from_config(config: dict, session=None) -> FreshBooksConnector:
    """
    Create FreshBooks connector from configuration dictionary.
    
    Args:
        config: Configuration dictionary containing FreshBooks settings
        session: Optional aiohttp session
        
    Returns:
        Configured FreshBooks connector
        
    Config format:
        {
            "client_id": "freshbooks_client_id",
            "client_secret": "freshbooks_client_secret", 
            "redirect_uri": "https://your-app.com/callback",
            "sandbox": true,
            "account_id": "optional_default_account_id"
        }
        
    Example:
        >>> config = {
        ...     "client_id": "your_client_id",
        ...     "client_secret": "your_client_secret",
        ...     "redirect_uri": "https://your-app.com/callback",
        ...     "sandbox": True
        ... }
        >>> connector = create_freshbooks_connector_from_config(config)
    """
    validate_freshbooks_config(config)
    
    return FreshBooksConnector(
        client_id=config["client_id"],
        client_secret=config["client_secret"], 
        redirect_uri=config["redirect_uri"],
        sandbox=config.get("sandbox", True),
        session=session
    )


def validate_freshbooks_config(config: dict) -> None:
    """
    Validate FreshBooks configuration dictionary.
    
    Args:
        config: Configuration dictionary to validate
        
    Raises:
        FreshBooksConfigurationError: If configuration is invalid
        
    Example:
        >>> config = {"client_id": "id", "client_secret": "secret", "redirect_uri": "https://app.com/cb"}
        >>> validate_freshbooks_config(config)  # No exception = valid
    """
    required_fields = ["client_id", "client_secret", "redirect_uri"]
    
    for field in required_fields:
        if field not in config:
            raise FreshBooksConfigurationError(f"Missing required field: {field}")
        if not config[field]:
            raise FreshBooksConfigurationError(f"Empty value for required field: {field}")
    
    # Validate redirect URI format
    redirect_uri = config["redirect_uri"]
    if not redirect_uri.startswith(("http://", "https://")):
        raise FreshBooksConfigurationError("Redirect URI must start with http:// or https://")
    
    # Validate sandbox setting
    if "sandbox" in config and not isinstance(config["sandbox"], bool):
        raise FreshBooksConfigurationError("Sandbox setting must be boolean")


def get_freshbooks_oauth_scopes() -> list:
    """
    Get list of OAuth2 scopes required for FreshBooks integration.
    
    Returns:
        List of required OAuth2 scopes
        
    Example:
        >>> scopes = get_freshbooks_oauth_scopes()
        >>> print(scopes)
        ['user:profile:read', 'user:clients:read', 'user:clients:write', ...]
    """
    return [
        "user:profile:read",
        "user:clients:read", 
        "user:clients:write",
        "user:items:read",
        "user:items:write", 
        "user:invoices:read",
        "user:invoices:write",
        "user:payments:read"
    ]


def is_freshbooks_webhook_valid(payload: bytes, signature: str, secret: str) -> bool:
    """
    Validate FreshBooks webhook signature.
    
    Args:
        payload: Raw webhook payload bytes
        signature: Webhook signature from headers
        secret: Webhook secret for validation
        
    Returns:
        True if signature is valid
        
    Example:
        >>> is_valid = is_freshbooks_webhook_valid(payload, signature, webhook_secret)
        >>> if is_valid:
        ...     process_webhook(payload)
    """
    import hmac
    import hashlib
    
    try:
        # FreshBooks uses HMAC-SHA256 for webhook signatures
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
    "name": "FreshBooks",
    "type": "accounting",
    "vendor": "FreshBooks Inc.",
    "api_version": "v1",
    "api_type": "REST",
    "authentication": "OAuth2",
    "documentation": "https://www.freshbooks.com/api",
    "supported_regions": ["US", "CA", "EU", "NG"],
    "supported_currencies": ["USD", "CAD", "EUR", "GBP", "NGN", "AUD", "NZD"],
    "rate_limits": {
        "requests_per_minute": 300,
        "burst_limit": 20
    },
    "features": {
        "multi_account": True,
        "real_time_sync": True, 
        "webhook_support": True,
        "batch_operations": True,
        "custom_fields": True,
        "file_attachments": True,
        "time_tracking": True,
        "expense_tracking": True,
        "project_management": True
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
        "hst_provinces": ["ON", "NB", "NL", "NS", "PE"],
        "tax_identifier": "GST/HST",
        "einvoice_required": False,
        "firs_compliance": False
    },
    "GB": {
        "name": "United Kingdom",
        "currency": "GBP",
        "vat_rate": 20.0,
        "tax_identifier": "VAT",
        "einvoice_required": False,
        "firs_compliance": False
    }
}


# Line item types and their UBL mappings
LINE_ITEM_TYPES = {
    0: {
        "name": "item",
        "description": "Product or service item",
        "ubl_unit_code": "EA",
        "supports_inventory": True
    },
    1: {
        "name": "time", 
        "description": "Time tracking entry",
        "ubl_unit_code": "HUR",
        "supports_inventory": False
    },
    2: {
        "name": "expense",
        "description": "Expense reimbursement",
        "ubl_unit_code": "EA", 
        "supports_inventory": False
    }
}


# Integration examples and documentation
INTEGRATION_EXAMPLES = {
    "basic_setup": '''
# Basic FreshBooks integration setup
from taxpoynt_platform.external_integrations.business_systems.accounting.freshbooks import create_freshbooks_connector

async def setup_freshbooks_integration():
    connector = create_freshbooks_connector(
        client_id="your_freshbooks_client_id",
        client_secret="your_freshbooks_client_secret",
        redirect_uri="https://your-app.com/oauth/callback",
        sandbox=True  # Use False for production
    )
    
    # Get authorization URL
    auth_url, state = connector.get_authorization_url()
    print(f"Please visit: {auth_url}")
    
    # After user authorization, exchange code for tokens
    auth_code = input("Enter authorization code: ")
    await connector.authenticate_with_code(auth_code, state)
    
    return connector
''',
    
    "invoice_extraction": '''
# Extract and convert invoices to UBL
async def extract_invoices_for_einvoicing(connector, account_id=None):
    # Get account info if not provided
    if not account_id:
        account_info = await connector.get_account_info()
        account_id = account_info["id"]
    
    # Get recent invoices
    from datetime import datetime, timedelta
    since_date = datetime.utcnow() - timedelta(days=30)
    
    invoices = await connector.get_invoices(
        account_id=account_id,
        updated_since=since_date,
        status_filter="sent"  # Only sent invoices
    )
    
    # Convert to UBL format for FIRS submission
    ubl_invoices = []
    for invoice in invoices:
        ubl_invoice = await connector.convert_invoice_to_ubl(
            invoice_id=invoice["id"],
            account_id=account_id,
            include_client_details=True
        )
        ubl_invoices.append(ubl_invoice)
    
    return ubl_invoices
''',
    
    "batch_processing": '''
# Batch process multiple invoices
async def batch_process_invoices(connector, invoice_ids, account_id=None):
    ubl_invoices = await connector.batch_convert_invoices_to_ubl(
        invoice_ids=invoice_ids,
        account_id=account_id,
        include_client_details=True
    )
    
    # Process UBL invoices for FIRS submission
    for ubl_invoice in ubl_invoices:
        # Submit to FIRS e-invoicing API
        # await submit_to_firs(ubl_invoice)
        pass
    
    return len(ubl_invoices)
''',
    
    "client_management": '''
# Create clients and invoices
async def create_client_and_invoice(connector, account_id=None):
    # Create a new client
    client_data = {
        "organization": "ACME Corporation",
        "email": "billing@acme.com",
        "s_street": "123 Business Street",
        "s_city": "Lagos",
        "s_country": "Nigeria",
        "currency_code": "NGN"
    }
    
    client = await connector.create_client(client_data, account_id)
    
    # Create an invoice for the client
    invoice_data = {
        "clientid": client["client"]["id"],
        "lines": [
            {
                "name": "Consulting Services",
                "description": "IT consulting services",
                "qty": 10,
                "unit_cost": {"amount": "5000.00"},
                "type": 0  # Item type
            }
        ],
        "currency_code": "NGN"
    }
    
    invoice = await connector.create_invoice(invoice_data, account_id)
    return client, invoice
''',
    
    "error_handling": '''
# Comprehensive error handling
from taxpoynt_platform.external_integrations.business_systems.accounting.freshbooks import (
    FreshBooksException, FreshBooksAuthenticationError, FreshBooksRateLimitError
)

async def robust_freshbooks_integration():
    try:
        connector = create_freshbooks_connector(...)
        
        # Test connection
        test_result = await connector.test_connection()
        if not test_result["success"]:
            raise FreshBooksConnectionError(f"Connection failed: {test_result['error']}")
        
        # Your integration logic here
        
    except FreshBooksAuthenticationError as e:
        logger.error(f"Authentication failed: {e}")
        # Redirect to re-authorization
        
    except FreshBooksRateLimitError as e:
        logger.warning(f"Rate limited, retry after {e.retry_after} seconds")
        await asyncio.sleep(e.retry_after)
        
    except FreshBooksException as e:
        logger.error(f"FreshBooks integration error: {e}")
        # Handle other FreshBooks-specific errors
        
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
        "freshbooks-test-credentials",
        "sandbox-environment-access"
    ],
    "mock_data": "tests/fixtures/freshbooks_mock_data.json",
    "test_config": {
        "sandbox_base_url": "https://api.freshbooks.com",
        "test_account_id": "test_account_123",
        "test_redirect_uri": "http://localhost:8000/callback"
    }
}


# Troubleshooting guide
TROUBLESHOOTING = {
    "authentication_failed": {
        "symptoms": ["401 Unauthorized", "Invalid token", "Token expired"],
        "solutions": [
            "Verify client credentials are correct",
            "Check redirect URI matches FreshBooks app configuration", 
            "Ensure OAuth scopes include required permissions",
            "Refresh tokens if expired",
            "Check if account has multiple businesses"
        ]
    },
    "rate_limit_exceeded": {
        "symptoms": ["429 Too Many Requests", "Rate limit error"],
        "solutions": [
            "Implement exponential backoff retry logic",
            "Reduce request frequency to stay under 300/minute",
            "Use batch operations where possible",
            "Monitor rate limit headers",
            "Consider upgrading FreshBooks plan for higher limits"
        ]
    },
    "account_access_issues": {
        "symptoms": ["Account not found", "Permission denied"],
        "solutions": [
            "Verify account ID is correct and accessible",
            "Check OAuth scopes match required permissions",
            "Ensure user has admin access to the account",
            "Verify account is active and not suspended"
        ]
    },
    "data_sync_issues": {
        "symptoms": ["Missing data", "Stale data", "Sync errors"],
        "solutions": [
            "Use updated_since parameter for incremental sync",
            "Handle pagination properly for large datasets", 
            "Check for deleted items (vis_state = 1)",
            "Implement proper error handling for partial failures"
        ]
    }
}


# Webhook event types
WEBHOOK_EVENTS = {
    "invoice.create": "New invoice created",
    "invoice.update": "Invoice updated", 
    "invoice.delete": "Invoice deleted",
    "client.create": "New client created",
    "client.update": "Client updated",
    "client.delete": "Client deleted",
    "payment.create": "New payment received",
    "payment.update": "Payment updated",
    "expense.create": "New expense created",
    "estimate.create": "New estimate created",
    "project.create": "New project created"
}