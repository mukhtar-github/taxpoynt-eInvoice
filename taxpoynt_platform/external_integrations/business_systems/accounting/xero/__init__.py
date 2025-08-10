"""
Xero Accounting Integration
Complete connector implementation for Xero accounting e-invoicing integration.
"""

from .connector import XeroConnector
from .auth import XeroAuthManager
from .rest_client import XeroRestClient
from .data_extractor import XeroDataExtractor
from .ubl_transformer import XeroUBLTransformer
from .exceptions import (
    XeroConnectionError,
    XeroAuthenticationError,
    XeroRateLimitError,
    XeroDataError,
    XeroValidationError,
    XeroTransformationError,
    XeroWebhookError,
    XeroOrganisationError,
    XeroInvoiceError,
    XeroContactError,
    XeroAccountError,
    XeroTaxError,
    create_xero_exception,
    handle_xero_api_error,
    XeroErrorHandler
)

# Main connector class
__all__ = [
    # Core connector
    "XeroConnector",
    
    # Component classes
    "XeroAuthManager",
    "XeroRestClient",
    "XeroDataExtractor", 
    "XeroUBLTransformer",
    
    # Exception classes
    "XeroConnectionError",
    "XeroAuthenticationError",
    "XeroRateLimitError",
    "XeroDataError",
    "XeroValidationError",
    "XeroTransformationError",
    "XeroWebhookError",
    "XeroOrganisationError",
    "XeroInvoiceError",
    "XeroContactError",
    "XeroAccountError",
    "XeroTaxError",
    
    # Utility functions
    "create_xero_exception",
    "handle_xero_api_error",
    "XeroErrorHandler"
]

# Connector metadata
CONNECTOR_INFO = {
    "name": "Xero",
    "version": "1.0.0",
    "description": "Complete Xero accounting integration for e-invoicing and FIRS compliance",
    "platform_type": "accounting",
    "supported_countries": ["NG", "NZ", "AU", "US", "GB", "CA"],
    "supported_currencies": ["NGN", "NZD", "AUD", "USD", "GBP", "CAD", "EUR"],
    "features": {
        "invoices": True,
        "credit_notes": True,
        "customers": True,
        "suppliers": True,
        "chart_of_accounts": True,
        "ubl_transformation": True,
        "multi_tenant": True,
        "oauth2": True,
        "incremental_sync": True,
        "multi_currency": True,
        "real_time_sync": False,  # No webhooks for accounting data
        "batch_operations": True,
        "tax_rates": True,
        "payments": True,
        "bank_transactions": True
    },
    "requirements": {
        "oauth2_app": True,
        "tenant_selection": True,
        "pkce_support": True,
        "openid_connect": True
    },
    "api_info": {
        "version": "2.0",
        "base_url": "https://api.xero.com/api.xro/2.0",
        "auth_url": "https://identity.xero.com/connect/authorize",
        "token_url": "https://identity.xero.com/connect/token",
        "connections_url": "https://api.xero.com/connections"
    },
    "rate_limits": {
        "calls_per_minute": 60,
        "calls_per_day": 5000,
        "concurrent_requests": 10,
        "burst_support": False
    }
}


def create_xero_connector(config: dict) -> XeroConnector:
    """
    Factory function to create Xero connector instance.
    
    Args:
        config: Connector configuration dictionary
        
    Returns:
        Configured Xero connector
        
    Example:
        config = {
            "client_id": "your_xero_app_client_id",
            "client_secret": "your_xero_app_client_secret", 
            "redirect_uri": "https://your-app.com/auth/callback",
            "tenant_id": "xero_tenant_id",  # Optional
            "auth_tokens": {
                "access_token": "oauth2_access_token",
                "refresh_token": "oauth2_refresh_token",
                "expires_at": "2024-12-31T23:59:59Z"
            }
        }
        connector = create_xero_connector(config)
    """
    return XeroConnector(config)


# Configuration validation helpers
def validate_xero_config(config: dict) -> tuple[bool, list[str]]:
    """
    Validate Xero connector configuration.
    
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
        "redirect_uri"
    ]
    
    for field in required_fields:
        if not config.get(field):
            errors.append(f"Missing required field: {field}")
    
    # Validate redirect URI format
    redirect_uri = config.get("redirect_uri", "")
    if redirect_uri and not redirect_uri.startswith(("http://", "https://")):
        errors.append("redirect_uri must be a valid HTTP/HTTPS URL")
    
    # Validate auth tokens if provided
    auth_tokens = config.get("auth_tokens", {})
    if auth_tokens:
        if not auth_tokens.get("access_token"):
            errors.append("Missing access_token in auth_tokens")
        if not auth_tokens.get("refresh_token"):
            errors.append("Missing refresh_token in auth_tokens")
    
    # Validate tenant_id format if provided
    tenant_id = config.get("tenant_id")
    if tenant_id and not isinstance(tenant_id, str):
        errors.append("tenant_id must be a string")
    
    return len(errors) == 0, errors


def get_oauth_requirements() -> dict:
    """
    Get OAuth2 setup requirements for Xero integration.
    
    Returns:
        Dictionary with OAuth2 setup information
    """
    return {
        "provider": "Xero",
        "oauth_version": "2.0",
        "scopes": [
            "accounting.transactions",
            "accounting.contacts",
            "accounting.settings", 
            "offline_access"
        ],
        "endpoints": {
            "discovery": "https://identity.xero.com/.well-known/openid_configuration",
            "authorization": "https://identity.xero.com/connect/authorize",
            "token": "https://identity.xero.com/connect/token",
            "connections": "https://api.xero.com/connections"
        },
        "required_parameters": {
            "client_id": "Your Xero app client ID",
            "client_secret": "Your Xero app client secret",
            "redirect_uri": "Your application redirect URI",
            "scope": "accounting.transactions accounting.contacts accounting.settings offline_access"
        },
        "callback_parameters": [
            "code",
            "state"
        ],
        "security_features": {
            "pkce": True,
            "state_parameter": True,
            "openid_connect": True
        },
        "multi_tenant": {
            "supported": True,
            "tenant_selection_required": True,
            "connections_endpoint": "https://api.xero.com/connections"
        },
        "setup_instructions": [
            "1. Create Xero app at https://developer.xero.com/myapps",
            "2. Configure OAuth2 redirect URIs",
            "3. Set appropriate scopes for accounting access",
            "4. Obtain client credentials",
            "5. Complete OAuth2 flow for each organization",
            "6. Handle multi-tenant organization selection"
        ]
    }


def get_supported_countries() -> dict:
    """
    Get supported countries and their specific requirements.
    
    Returns:
        Dictionary with country-specific information
    """
    return {
        "NG": {  # Nigeria
            "name": "Nigeria",
            "currency": "NGN",
            "vat_rate": 7.5,
            "tax_compliance": {
                "firs_integration": True,
                "tin_required": True,
                "vat_threshold": 25000000,  # NGN 25M annual turnover
                "ubl_version": "2.1"
            },
            "specific_requirements": [
                "TIN (Tax Identification Number) required",
                "FIRS e-invoicing compliance",
                "VAT registration for businesses above threshold"
            ]
        },
        "NZ": {  # New Zealand
            "name": "New Zealand", 
            "currency": "NZD",
            "vat_rate": 15.0,
            "tax_compliance": {
                "gst_required": True,
                "ird_number": True
            }
        },
        "AU": {  # Australia
            "name": "Australia",
            "currency": "AUD", 
            "vat_rate": 10.0,
            "tax_compliance": {
                "gst_required": True,
                "abn_required": True
            }
        },
        "US": {  # United States
            "name": "United States",
            "currency": "USD",
            "tax_compliance": {
                "sales_tax_varies": True,
                "ein_required": True
            }
        },
        "GB": {  # United Kingdom
            "name": "United Kingdom",
            "currency": "GBP",
            "vat_rate": 20.0,
            "tax_compliance": {
                "vat_required": True,
                "companies_house": True
            }
        },
        "CA": {  # Canada
            "name": "Canada",
            "currency": "CAD",
            "tax_compliance": {
                "gst_hst_required": True,
                "business_number": True
            }
        }
    }


def get_currency_support() -> dict:
    """
    Get supported currencies and conversion information.
    
    Returns:
        Dictionary with currency support information
    """
    return {
        "base_currencies": ["NGN", "NZD", "AUD", "USD", "GBP", "CAD", "EUR"],
        "multi_currency": {
            "supported": True,
            "automatic_conversion": True,
            "exchange_rates": "Xero provides rates",
            "base_currency_reporting": True
        },
        "nigerian_compliance": {
            "base_currency": "NGN",
            "foreign_currency_reporting": True,
            "exchange_rate_mandatory": True,
            "conversion_date_tracking": True
        },
        "conversion_features": {
            "historical_rates": True,
            "rate_locking": True,
            "gain_loss_tracking": True
        }
    }


def get_integration_patterns() -> dict:
    """
    Get recommended integration patterns for different use cases.
    
    Returns:
        Dictionary with integration pattern information
    """
    return {
        "real_time_sync": {
            "supported": False,
            "reason": "Xero doesn't provide webhooks for accounting data",
            "alternative": "Polling-based incremental sync"
        },
        "batch_processing": {
            "supported": True,
            "batch_size": 100,
            "recommended_frequency": "Every 15 minutes",
            "rate_limit_considerations": True
        },
        "incremental_sync": {
            "supported": True,
            "sync_method": "UpdatedDateUTC field",
            "recommended_interval": "15-30 minutes",
            "sync_types": ["invoices", "contacts", "accounts", "credit_notes"]
        },
        "multi_tenant": {
            "pattern": "Tenant per organization",
            "tenant_storage": "Required in configuration",
            "tenant_switching": "Per request basis",
            "concurrent_tenants": "Supported"
        },
        "error_handling": {
            "retry_strategy": "Exponential backoff",
            "rate_limit_handling": "Built-in queuing",
            "error_classification": "Automatic exception mapping",
            "logging": "Comprehensive audit trail"
        }
    }


def get_testing_requirements() -> dict:
    """
    Get testing and development requirements.
    
    Returns:
        Dictionary with testing information
    """
    return {
        "development_environment": {
            "demo_company": "Use Xero Demo Company",
            "sandbox": False,  # Xero uses demo company instead
            "test_data": "Pre-populated demo data available"
        },
        "oauth_testing": {
            "test_app": "Create separate app for testing",
            "localhost_redirect": "Supported for development",
            "token_expiry": "Test token refresh flows"
        },
        "api_testing": {
            "rate_limit_testing": "Test with actual limits",
            "error_simulation": "Use invalid data to test error handling",
            "multi_tenant_testing": "Test with multiple organizations"
        },
        "compliance_testing": {
            "nigerian_vat": "Test VAT calculations",
            "ubl_validation": "Validate UBL output",
            "firs_compliance": "Test FIRS submission format"
        }
    }


# Version and compatibility information
__version__ = "1.0.0"
__compatibility__ = {
    "xero_api": "2.0",
    "oauth_version": "2.0",
    "openid_connect": "1.0",
    "ubl_version": "2.1",
    "python_version": ">=3.8",
    "pkce_support": True
}

# Feature flags for different deployment environments
FEATURE_FLAGS = {
    "multi_currency_support": True,
    "batch_operations": True,
    "advanced_filtering": True,
    "tax_rate_sync": True,
    "payment_tracking": True,
    "bank_transaction_sync": True,
    "credit_note_support": True,
    "multi_tenant_support": True,
    "ubl_transformation": True,
    "firs_compliance": True,
    "nigerian_tax_rules": True
}

# Development and debugging helpers
DEBUG_INFO = {
    "common_issues": {
        "token_expiry": "Access tokens expire after 30 minutes",
        "tenant_selection": "Must select tenant for multi-org access",
        "rate_limits": "60 calls/minute, 5000/day per app",
        "scope_requirements": "Ensure accounting.transactions scope is granted"
    },
    "troubleshooting": {
        "connection_test": "Use test_connection() method",
        "auth_status": "Check get_auth_status() for token info",
        "rate_limits": "Monitor get_rate_limit_status()",
        "tenant_info": "Use get_available_tenants() for org list"
    }
}