"""
QuickBooks Online Accounting Integration
Complete connector implementation for QuickBooks Online e-invoicing integration.
"""

from .connector import QuickBooksConnector
from .auth import QuickBooksAuthManager
from .rest_client import QuickBooksRestClient
from .data_extractor import QuickBooksDataExtractor
from .ubl_transformer import QuickBooksUBLTransformer
from .exceptions import (
    QuickBooksConnectionError,
    QuickBooksAuthenticationError,
    QuickBooksRateLimitError,
    QuickBooksDataError,
    QuickBooksValidationError,
    QuickBooksTransformationError,
    QuickBooksWebhookError
)

# Main connector class
__all__ = [
    # Core connector
    "QuickBooksConnector",
    
    # Component classes
    "QuickBooksAuthManager",
    "QuickBooksRestClient", 
    "QuickBooksDataExtractor",
    "QuickBooksUBLTransformer",
    
    # Exception classes
    "QuickBooksConnectionError",
    "QuickBooksAuthenticationError", 
    "QuickBooksRateLimitError",
    "QuickBooksDataError",
    "QuickBooksValidationError",
    "QuickBooksTransformationError",
    "QuickBooksWebhookError"
]

# Connector metadata
CONNECTOR_INFO = {
    "name": "QuickBooks Online",
    "version": "1.0.0",
    "description": "Complete QuickBooks Online integration for e-invoicing and FIRS compliance",
    "platform_type": "accounting",
    "supported_countries": ["NG", "US", "CA", "GB", "AU"],
    "supported_currencies": ["NGN", "USD", "CAD", "GBP", "AUD"],
    "features": {
        "invoices": True,
        "credit_notes": True,
        "customers": True,
        "items": True,
        "chart_of_accounts": True,
        "ubl_transformation": True,
        "webhooks": True,
        "oauth2": True,
        "incremental_sync": True,
        "real_time_sync": True
    },
    "requirements": {
        "oauth2_app": True,
        "webhook_endpoint": True,
        "ssl_certificate": True,
        "company_id": True
    }
}


def create_quickbooks_connector(config: dict) -> QuickBooksConnector:
    """
    Factory function to create QuickBooks connector instance.
    
    Args:
        config: Connector configuration dictionary
        
    Returns:
        Configured QuickBooks connector
        
    Example:
        config = {
            "client_id": "your_app_client_id",
            "client_secret": "your_app_client_secret",
            "company_id": "quickbooks_company_id",
            "sandbox": True,
            "webhook_verifier_token": "webhook_token",
            "auth_tokens": {
                "access_token": "oauth2_access_token",
                "refresh_token": "oauth2_refresh_token",
                "expires_at": "2024-12-31T23:59:59Z"
            }
        }
        connector = create_quickbooks_connector(config)
    """
    return QuickBooksConnector(config)


# Configuration validation helpers
def validate_quickbooks_config(config: dict) -> tuple[bool, list[str]]:
    """
    Validate QuickBooks connector configuration.
    
    Args:
        config: Configuration dictionary to validate
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    # Required fields
    required_fields = [
        "client_id",
        "client_secret", 
        "company_id"
    ]
    
    for field in required_fields:
        if not config.get(field):
            errors.append(f"Missing required field: {field}")
    
    # Validate auth tokens if provided
    auth_tokens = config.get("auth_tokens", {})
    if auth_tokens:
        if not auth_tokens.get("access_token"):
            errors.append("Missing access_token in auth_tokens")
        if not auth_tokens.get("refresh_token"):
            errors.append("Missing refresh_token in auth_tokens")
    
    # Validate webhook config if provided
    if config.get("webhooks_enabled") and not config.get("webhook_verifier_token"):
        errors.append("webhook_verifier_token required when webhooks are enabled")
    
    return len(errors) == 0, errors


def get_oauth_requirements() -> dict:
    """
    Get OAuth2 setup requirements for QuickBooks integration.
    
    Returns:
        Dictionary with OAuth2 setup information
    """
    return {
        "provider": "Intuit QuickBooks",
        "oauth_version": "2.0",
        "scopes": ["com.intuit.quickbooks.accounting"],
        "endpoints": {
            "discovery": "https://appcenter.intuit.com/connect/oauth2",
            "authorization": "https://appcenter.intuit.com/connect/oauth2",
            "token": "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer"
        },
        "required_parameters": {
            "client_id": "Your QuickBooks app client ID",
            "client_secret": "Your QuickBooks app client secret",
            "redirect_uri": "Your application redirect URI",
            "scope": "com.intuit.quickbooks.accounting"
        },
        "callback_parameters": [
            "code",
            "realmId", 
            "state"
        ],
        "setup_instructions": [
            "1. Create QuickBooks app at https://developer.intuit.com",
            "2. Configure OAuth2 redirect URIs",
            "3. Enable webhooks endpoint (optional)",
            "4. Obtain client credentials",
            "5. Complete OAuth2 flow to get company authorization"
        ]
    }


def get_webhook_requirements() -> dict:
    """
    Get webhook setup requirements for QuickBooks integration.
    
    Returns:
        Dictionary with webhook setup information
    """
    return {
        "endpoint_url": "Your HTTPS webhook endpoint URL",
        "supported_events": [
            "Invoice Create/Update/Delete",
            "Customer Create/Update/Delete", 
            "Item Create/Update/Delete",
            "Payment Create/Update/Delete"
        ],
        "verification": {
            "method": "signature_verification",
            "requires": "webhook_verifier_token"
        },
        "payload_format": "JSON",
        "retry_policy": "Exponential backoff",
        "requirements": [
            "HTTPS endpoint required",
            "Valid SSL certificate",
            "Response within 30 seconds",
            "Return 200 status for successful processing"
        ],
        "setup_instructions": [
            "1. Implement HTTPS webhook endpoint",
            "2. Configure webhook URL in QuickBooks app",
            "3. Set webhook verifier token",
            "4. Implement signature verification",
            "5. Test webhook delivery"
        ]
    }


# Version and compatibility information
__version__ = "1.0.0"
__compatibility__ = {
    "quickbooks_api": "v3",
    "oauth_version": "2.0",
    "ubl_version": "2.1",
    "python_version": ">=3.8"
}