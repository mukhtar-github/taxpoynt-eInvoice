"""
Sage Business Cloud Accounting Integration
Complete connector implementation for Sage Business Cloud Accounting e-invoicing integration.
"""

from .connector import SageConnector
from .auth import SageAuthManager
from .rest_client import SageRestClient
from .data_extractor import SageDataExtractor
from .ubl_transformer import SageUBLTransformer
from .exceptions import (
    SageConnectionError,
    SageAuthenticationError,
    SageRateLimitError,
    SageDataError,
    SageValidationError,
    SageTransformationError,
    SageWebhookError,
    SageBusinessError,
    SageInvoiceError,
    SageContactError,
    SageLedgerAccountError,
    SageTaxRateError,
    SageProductError,
    create_sage_exception,
    handle_sage_api_error,
    SageErrorHandler
)

# Main connector class
__all__ = [
    # Core connector
    "SageConnector",
    
    # Component classes
    "SageAuthManager",
    "SageRestClient",
    "SageDataExtractor",
    "SageUBLTransformer",
    
    # Exception classes
    "SageConnectionError",
    "SageAuthenticationError",
    "SageRateLimitError",
    "SageDataError",
    "SageValidationError",
    "SageTransformationError",
    "SageWebhookError",
    "SageBusinessError",
    "SageInvoiceError",
    "SageContactError",
    "SageLedgerAccountError",
    "SageTaxRateError",
    "SageProductError",
    
    # Utility functions
    "create_sage_exception",
    "handle_sage_api_error",
    "SageErrorHandler"
]

# Connector metadata
CONNECTOR_INFO = {
    "name": "Sage Business Cloud Accounting",
    "version": "1.0.0",
    "description": "Complete Sage Business Cloud Accounting integration for e-invoicing and FIRS compliance",
    "platform_type": "accounting",
    "supported_countries": ["NG", "GB", "US", "CA", "AU", "IE", "FR", "DE", "ES"],
    "supported_currencies": ["NGN", "GBP", "USD", "CAD", "AUD", "EUR"],
    "features": {
        "sales_invoices": True,
        "purchase_invoices": True,
        "credit_notes": True,
        "customers": True,
        "suppliers": True,
        "chart_of_accounts": True,
        "ubl_transformation": True,
        "multi_business": True,
        "oauth2": True,
        "incremental_sync": True,
        "multi_currency": True,
        "exchange_rates": True,
        "uk_vat_compliance": True,
        "nigerian_vat_compliance": True,
        "real_time_sync": False,  # No webhooks available
        "batch_operations": True,
        "tax_rates": True,
        "products": True,
        "pagination": True
    },
    "requirements": {
        "oauth2_app": True,
        "business_selection": True,
        "pkce_support": True
    },
    "api_info": {
        "version": "3.1",
        "base_url": "https://api.accounting.sage.com/v3.1",
        "auth_url": "https://www.sageone.com/oauth2/auth/central",
        "token_url": "https://www.sageone.com/oauth2/auth/central/token"
    },
    "rate_limits": {
        "calls_per_hour": 5000,
        "concurrent_requests": 10,
        "burst_support": False
    }
}


def create_sage_connector(config: dict) -> SageConnector:
    """
    Factory function to create Sage connector instance.
    
    Args:
        config: Connector configuration dictionary
        
    Returns:
        Configured Sage connector
        
    Example:
        config = {
            "client_id": "your_sage_app_client_id",
            "client_secret": "your_sage_app_client_secret",
            "redirect_uri": "https://your-app.com/auth/callback",
            "business_id": "sage_business_id",  # Optional
            "auth_tokens": {
                "access_token": "oauth2_access_token",
                "refresh_token": "oauth2_refresh_token",
                "expires_at": "2024-12-31T23:59:59Z"
            }
        }
        connector = create_sage_connector(config)
    """
    return SageConnector(config)


# Configuration validation helpers
def validate_sage_config(config: dict) -> tuple[bool, list[str]]:
    """
    Validate Sage connector configuration.
    
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
    
    # Validate business_id format if provided
    business_id = config.get("business_id")
    if business_id and not isinstance(business_id, str):
        errors.append("business_id must be a string")
    
    return len(errors) == 0, errors


def get_oauth_requirements() -> dict:
    """
    Get OAuth2 setup requirements for Sage Business Cloud Accounting integration.
    
    Returns:
        Dictionary with OAuth2 setup information
    """
    return {
        "provider": "Sage Business Cloud Accounting",
        "oauth_version": "2.0",
        "scopes": ["full_access"],
        "endpoints": {
            "authorization": "https://www.sageone.com/oauth2/auth/central",
            "token": "https://www.sageone.com/oauth2/auth/central/token"
        },
        "required_parameters": {
            "client_id": "Your Sage app client ID",
            "client_secret": "Your Sage app client secret",
            "redirect_uri": "Your application redirect URI",
            "scope": "full_access"
        },
        "callback_parameters": [
            "code",
            "state"
        ],
        "security_features": {
            "pkce": True,
            "state_parameter": True
        },
        "multi_business": {
            "supported": True,
            "business_selection_required": True,
            "business_switching": "Per session basis"
        },
        "setup_instructions": [
            "1. Create Sage app at https://developer.sage.com",
            "2. Configure OAuth2 redirect URIs",
            "3. Set scope to 'full_access' for accounting data",
            "4. Obtain client credentials",
            "5. Complete OAuth2 flow for each business",
            "6. Handle multi-business selection"
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
        "GB": {  # United Kingdom
            "name": "United Kingdom",
            "currency": "GBP",
            "vat_rates": [0, 5, 20],  # Zero, Reduced, Standard
            "tax_compliance": {
                "vat_required": True,
                "making_tax_digital": True,
                "companies_house": True
            },
            "specific_requirements": [
                "VAT registration required for businesses above £85,000 turnover",
                "Making Tax Digital compliance",
                "Companies House filing requirements"
            ]
        },
        "US": {  # United States
            "name": "United States",
            "currency": "USD",
            "tax_compliance": {
                "sales_tax_varies": True,
                "ein_required": True,
                "state_specific": True
            }
        },
        "CA": {  # Canada
            "name": "Canada",
            "currency": "CAD",
            "tax_compliance": {
                "gst_hst_required": True,
                "business_number": True,
                "provincial_tax": True
            }
        },
        "AU": {  # Australia
            "name": "Australia",
            "currency": "AUD",
            "vat_rate": 10.0,  # GST
            "tax_compliance": {
                "gst_required": True,
                "abn_required": True
            }
        },
        "IE": {  # Ireland
            "name": "Ireland",
            "currency": "EUR",
            "vat_rates": [0, 13.5, 23],  # Zero, Reduced, Standard
            "tax_compliance": {
                "vat_required": True,
                "revenue_online_service": True
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
        "base_currencies": ["NGN", "GBP", "USD", "CAD", "AUD", "EUR"],
        "multi_currency": {
            "supported": True,
            "automatic_conversion": True,
            "exchange_rates": "Sage provides rates and base currency amounts",
            "base_currency_reporting": True,
            "historical_rates": True
        },
        "nigerian_compliance": {
            "base_currency": "NGN",
            "foreign_currency_reporting": True,
            "exchange_rate_mandatory": True,
            "conversion_date_tracking": True,
            "sage_base_amounts": "Provided by Sage API"
        },
        "uk_compliance": {
            "base_currency": "GBP",
            "making_tax_digital": True,
            "vat_on_foreign_currency": True
        },
        "conversion_features": {
            "historical_rates": True,
            "rate_locking": True,
            "gain_loss_tracking": True,
            "sage_calculated_amounts": True
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
            "reason": "Sage doesn't provide webhooks",
            "alternative": "Polling-based incremental sync"
        },
        "batch_processing": {
            "supported": True,
            "batch_size": 200,  # Sage max items per page
            "recommended_frequency": "Every 30 minutes",
            "rate_limit_considerations": True,
            "pagination_required": True
        },
        "incremental_sync": {
            "supported": True,
            "sync_method": "Date-based filtering",
            "recommended_interval": "30-60 minutes",
            "sync_types": [
                "sales_invoices", 
                "purchase_invoices", 
                "contacts", 
                "credit_notes",
                "ledger_accounts",
                "products",
                "tax_rates"
            ]
        },
        "multi_business": {
            "pattern": "Business per session",
            "business_storage": "Required in configuration",
            "business_switching": "Per request basis",
            "concurrent_businesses": "Supported with separate sessions"
        },
        "error_handling": {
            "retry_strategy": "Exponential backoff",
            "rate_limit_handling": "Built-in queuing with hourly limits",
            "error_classification": "Automatic exception mapping",
            "logging": "Comprehensive audit trail"
        }
    }


def get_api_endpoints() -> dict:
    """
    Get comprehensive API endpoint information.
    
    Returns:
        Dictionary with API endpoint details
    """
    return {
        "base_url": "https://api.accounting.sage.com/v3.1",
        "business_scoped": True,
        "authentication": "OAuth2 Bearer token",
        "content_type": "application/json",
        "endpoints": {
            "sales_invoices": {
                "list": "GET /businesses/{business_id}/sales_invoices",
                "get": "GET /businesses/{business_id}/sales_invoices/{id}",
                "create": "POST /businesses/{business_id}/sales_invoices",
                "update": "PUT /businesses/{business_id}/sales_invoices/{id}",
                "pagination": True,
                "filters": ["from_date", "to_date", "search"]
            },
            "purchase_invoices": {
                "list": "GET /businesses/{business_id}/purchase_invoices",
                "get": "GET /businesses/{business_id}/purchase_invoices/{id}",
                "create": "POST /businesses/{business_id}/purchase_invoices",
                "update": "PUT /businesses/{business_id}/purchase_invoices/{id}",
                "pagination": True,
                "filters": ["from_date", "to_date", "search"]
            },
            "contacts": {
                "list": "GET /businesses/{business_id}/contacts",
                "get": "GET /businesses/{business_id}/contacts/{id}",
                "create": "POST /businesses/{business_id}/contacts",
                "update": "PUT /businesses/{business_id}/contacts/{id}",
                "pagination": True,
                "filters": ["contact_type", "search"]
            },
            "ledger_accounts": {
                "list": "GET /businesses/{business_id}/ledger_accounts",
                "get": "GET /businesses/{business_id}/ledger_accounts/{id}",
                "pagination": True,
                "filters": ["search"]
            },
            "tax_rates": {
                "list": "GET /businesses/{business_id}/tax_rates",
                "get": "GET /businesses/{business_id}/tax_rates/{id}",
                "pagination": True
            },
            "products": {
                "list": "GET /businesses/{business_id}/products",
                "get": "GET /businesses/{business_id}/products/{id}",
                "create": "POST /businesses/{business_id}/products",
                "update": "PUT /businesses/{business_id}/products/{id}",
                "pagination": True,
                "filters": ["product_type", "search"]
            },
            "sales_credit_notes": {
                "list": "GET /businesses/{business_id}/sales_credit_notes",
                "get": "GET /businesses/{business_id}/sales_credit_notes/{id}",
                "pagination": True,
                "filters": ["from_date", "to_date", "search"]
            }
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
            "sandbox": "No separate sandbox - use test business",
            "test_business": "Create test business in Sage",
            "test_data": "Create sample data for testing"
        },
        "oauth_testing": {
            "test_app": "Create separate app for testing",
            "localhost_redirect": "Supported for development",
            "token_expiry": "Test token refresh flows (1 hour expiry)"
        },
        "api_testing": {
            "rate_limit_testing": "Test with actual limits (5000/hour)",
            "error_simulation": "Use invalid data to test error handling",
            "multi_business_testing": "Test with multiple businesses",
            "pagination_testing": "Test with large datasets",
            "multi_currency_testing": "Test exchange rate handling"
        },
        "compliance_testing": {
            "uk_vat": "Test UK VAT rates (0%, 5%, 20%)",
            "nigerian_vat": "Test Nigerian VAT calculations (7.5%)",
            "ubl_validation": "Validate UBL output",
            "firs_compliance": "Test FIRS submission format",
            "multi_currency_compliance": "Test currency conversion"
        }
    }


# Version and compatibility information
__version__ = "1.0.0"
__compatibility__ = {
    "sage_api": "3.1",
    "oauth_version": "2.0",
    "ubl_version": "2.1",
    "python_version": ">=3.8",
    "pkce_support": True
}

# Feature flags for different deployment environments
FEATURE_FLAGS = {
    "multi_currency_support": True,
    "multi_business_support": True,
    "batch_operations": True,
    "advanced_filtering": True,
    "tax_rate_sync": True,
    "product_sync": True,
    "credit_note_support": True,
    "purchase_invoice_support": True,
    "ubl_transformation": True,
    "firs_compliance": True,
    "uk_vat_compliance": True,
    "nigerian_tax_rules": True,
    "exchange_rate_tracking": True,
    "sage_base_currency_amounts": True
}

# Development and debugging helpers
DEBUG_INFO = {
    "common_issues": {
        "token_expiry": "Access tokens expire after 1 hour",
        "business_selection": "Must select business for multi-business access",
        "rate_limits": "5000 calls/hour per business",
        "pagination": "Max 200 items per page",
        "scope_requirements": "Ensure 'full_access' scope is granted"
    },
    "troubleshooting": {
        "connection_test": "Use test_connection() method",
        "auth_status": "Check get_auth_status() for token info",
        "rate_limits": "Monitor get_rate_limit_status()",
        "business_info": "Use get_available_businesses() for business list",
        "api_responses": "Check Sage API documentation for response formats"
    }
}

# Sage-specific constants
SAGE_CONSTANTS = {
    "max_items_per_page": 200,
    "default_items_per_page": 20,
    "token_expiry_hours": 1,
    "rate_limit_per_hour": 5000,
    "supported_api_version": "3.1",
    "default_scope": "full_access",
    "pagination_required": True,
    "business_scoped_api": True
}