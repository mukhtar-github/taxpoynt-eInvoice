"""
CRM Systems Integration
Comprehensive suite of CRM platform connectors for Nigerian e-invoicing compliance.
"""

from typing import Dict, List, Optional, Any, Type, Union
import logging

# Import all CRM platform connectors
from .salesforce import SalesforceConnector, create_salesforce_connector
from .hubspot import HubSpotConnector, create_hubspot_connector  
from .zoho import ZohoCRMConnector, create_zoho_crm_connector
from .pipedrive import PipedriveConnector, create_pipedrive_connector
from .microsoft_dynamics import MicrosoftDynamicsConnector, create_microsoft_dynamics_connector

# Import base connector for type hints
from ...framework.crm.base_connector import BaseCRMConnector


logger = logging.getLogger(__name__)


__version__ = "1.0.0"
__author__ = "TaxPoynt Development Team"
__email__ = "dev@taxpoynt.com"

# Package metadata
__title__ = "CRM Systems Integration Suite"
__description__ = "Complete CRM platform connectors for Nigerian e-invoicing compliance"
__url__ = "https://github.com/taxpoynt/taxpoynt-platform"
__license__ = "MIT"
__copyright__ = "Copyright 2024 TaxPoynt"


# Supported CRM platforms
SUPPORTED_PLATFORMS = {
    "salesforce": {
        "name": "Salesforce",
        "connector_class": SalesforceConnector,
        "factory_function": create_salesforce_connector,
        "vendor": "Salesforce Inc.",
        "api_type": "REST",
        "authentication": "OAuth2",
        "supported_regions": ["US", "EU", "APAC", "NG"],
        "supported_currencies": ["USD", "EUR", "GBP", "NGN", "CAD", "AUD"],
        "features": {
            "multi_org": True,
            "real_time_sync": True,
            "webhook_support": True,
            "batch_operations": True,
            "custom_fields": True,
            "workflow_automation": True,
            "advanced_reporting": True,
            "lead_management": True,
            "opportunity_tracking": True,
            "contact_management": True
        },
        "compliance": {
            "firs_einvoicing": True,
            "ubl_2_1": True,
            "nigerian_vat": True
        }
    },
    
    "hubspot": {  
        "name": "HubSpot CRM",
        "connector_class": HubSpotConnector,
        "factory_function": create_hubspot_connector,
        "vendor": "HubSpot Inc.",
        "api_type": "REST",
        "authentication": "OAuth2",
        "supported_regions": ["US", "EU", "APAC", "NG"],
        "supported_currencies": ["USD", "EUR", "GBP", "NGN", "CAD", "JPY"],
        "features": {
            "multi_portal": True,
            "real_time_sync": True,
            "webhook_support": True,
            "batch_operations": True,
            "custom_properties": True,
            "marketing_automation": True,
            "sales_pipeline": True,
            "contact_scoring": True,
            "deal_tracking": True,
            "email_integration": True
        },
        "compliance": {
            "firs_einvoicing": True,
            "ubl_2_1": True,
            "nigerian_vat": True
        }
    },
    
    "zoho": {
        "name": "Zoho CRM",
        "connector_class": ZohoCRMConnector,
        "factory_function": create_zoho_crm_connector,
        "vendor": "Zoho Corporation",
        "api_type": "REST",
        "authentication": "OAuth2",
        "supported_regions": ["US", "EU", "IN", "AU", "NG"],
        "supported_currencies": ["USD", "EUR", "GBP", "INR", "NGN", "AUD"],
        "features": {
            "multi_org": True,
            "real_time_sync": True,
            "webhook_support": True,
            "batch_operations": True,
            "custom_fields": True,
            "workflow_rules": True,
            "territory_management": True,
            "forecast_management": True,
            "inventory_management": True,
            "vendor_management": True
        },
        "compliance": {
            "firs_einvoicing": True,
            "ubl_2_1": True,
            "nigerian_vat": True
        }
    },
    
    "pipedrive": {
        "name": "Pipedrive",
        "connector_class": PipedriveConnector,
        "factory_function": create_pipedrive_connector,
        "vendor": "Pipedrive Inc.",
        "api_type": "REST",
        "authentication": "API Key + OAuth2",
        "supported_regions": ["US", "EU", "NG"],
        "supported_currencies": ["USD", "EUR", "GBP", "NGN"],
        "features": {
            "multi_company": False,
            "real_time_sync": True,
            "webhook_support": True,
            "batch_operations": True,
            "custom_fields": True,
            "pipeline_management": True,
            "activity_tracking": True,
            "email_sync": True,
            "deal_rotting": True,
            "sales_reporting": True
        },
        "compliance": {
            "firs_einvoicing": True,
            "ubl_2_1": True,
            "nigerian_vat": True
        }
    },
    
    "microsoft_dynamics": {
        "name": "Microsoft Dynamics 365 CRM",
        "connector_class": MicrosoftDynamicsConnector,
        "factory_function": create_microsoft_dynamics_connector,
        "vendor": "Microsoft Corporation",
        "api_type": "REST (Web API)",
        "authentication": "OAuth2 + Azure AD",
        "supported_regions": ["US", "EU", "APAC", "NG"],
        "supported_currencies": ["USD", "EUR", "GBP", "NGN", "CAD", "AUD"],
        "features": {
            "multi_tenant": True,
            "real_time_sync": True,
            "webhook_support": True,
            "batch_operations": True,
            "custom_entities": True,
            "business_process_flows": True,
            "power_platform_integration": True,
            "ai_insights": True,
            "unified_interface": True,
            "mobile_app": True
        },
        "compliance": {
            "firs_einvoicing": True,
            "ubl_2_1": True,
            "nigerian_vat": True
        }
    }
}


# Platform aliases for convenience
PLATFORM_ALIASES = {
    "sf": "salesforce",
    "sfdc": "salesforce",
    
    "hs": "hubspot",
    "hubspot_crm": "hubspot",
    
    "zoho_crm": "zoho",
    "zcrm": "zoho",
    
    "pd": "pipedrive",
    
    "dynamics": "microsoft_dynamics",
    "dynamics_365": "microsoft_dynamics",
    "d365": "microsoft_dynamics",
    "msft_dynamics": "microsoft_dynamics"
}


# Export main classes and functions
__all__ = [
    # Platform connectors
    "SalesforceConnector",
    "HubSpotConnector", 
    "ZohoCRMConnector",
    "PipedriveConnector",
    "MicrosoftDynamicsConnector",
    
    # Factory functions
    "create_crm_connector",
    "create_connector_from_config",
    "get_platform_connector",
    
    # Utility functions
    "list_supported_platforms",
    "get_platform_info",
    "validate_platform_config",
    "get_connector_class",
    
    # Platform registry
    "SUPPORTED_PLATFORMS",
    "PLATFORM_ALIASES",
    
    # Exception classes
    "CRMPlatformError",
    "UnsupportedPlatformError",
    "ConfigurationError"
]


class CRMPlatformError(Exception):
    """Base exception for CRM platform errors."""
    pass


class UnsupportedPlatformError(CRMPlatformError):
    """Raised when an unsupported platform is requested."""
    pass


class ConfigurationError(CRMPlatformError):
    """Raised when platform configuration is invalid."""
    pass


def create_crm_connector(
    platform: str,
    config: Dict[str, Any],
    session=None
) -> BaseCRMConnector:
    """
    Create a CRM connector for the specified platform.
    
    Args:
        platform: Platform identifier (e.g., 'salesforce', 'hubspot', 'zoho')
        config: Platform-specific configuration
        session: Optional aiohttp session
        
    Returns:
        Configured CRM connector instance
        
    Example:
        >>> config = {
        ...     "client_id": "your_client_id",
        ...     "client_secret": "your_client_secret",
        ...     "redirect_uri": "https://your-app.com/callback",
        ...     "sandbox": True
        ... }
        >>> connector = create_crm_connector("salesforce", config)
    """
    # Normalize platform name
    platform = _normalize_platform_name(platform)
    
    if platform not in SUPPORTED_PLATFORMS:
        raise UnsupportedPlatformError(f"Platform '{platform}' is not supported")
    
    platform_info = SUPPORTED_PLATFORMS[platform]
    factory_function = platform_info["factory_function"]
    
    try:
        return factory_function(**config, session=session)
    except Exception as e:
        raise ConfigurationError(f"Failed to create {platform} connector: {str(e)}")


def create_connector_from_config(
    config: Dict[str, Any],
    session=None
) -> BaseCRMConnector:
    """
    Create CRM connector from unified configuration.
    
    Args:
        config: Configuration dict with 'platform' field and platform-specific settings
        session: Optional aiohttp session
        
    Returns:
        Configured CRM connector instance
    """
    if "platform" not in config:
        raise ConfigurationError("Configuration must include 'platform' field")
    
    platform = config.pop("platform")
    return create_crm_connector(platform, config, session)


def get_platform_connector(platform: str) -> Type[BaseCRMConnector]:
    """Get connector class for specified platform."""
    platform = _normalize_platform_name(platform)
    
    if platform not in SUPPORTED_PLATFORMS:
        raise UnsupportedPlatformError(f"Platform '{platform}' is not supported")
    
    return SUPPORTED_PLATFORMS[platform]["connector_class"]


def get_connector_class(platform: str) -> Type[BaseCRMConnector]:
    """Alias for get_platform_connector for backward compatibility."""
    return get_platform_connector(platform)


def list_supported_platforms() -> List[Dict[str, Any]]:
    """Get list of all supported CRM platforms."""
    return [
        {
            "id": platform_id,
            "name": info["name"],
            "vendor": info["vendor"],
            "api_type": info["api_type"],
            "authentication": info["authentication"],
            "supported_regions": info["supported_regions"],
            "supported_currencies": info["supported_currencies"],
            "features": info["features"],
            "compliance": info["compliance"]
        }
        for platform_id, info in SUPPORTED_PLATFORMS.items()
    ]


def get_platform_info(platform: str) -> Dict[str, Any]:
    """Get detailed information about a specific platform."""
    platform = _normalize_platform_name(platform)
    
    if platform not in SUPPORTED_PLATFORMS:
        raise UnsupportedPlatformError(f"Platform '{platform}' is not supported")
    
    return SUPPORTED_PLATFORMS[platform].copy()


def _normalize_platform_name(platform: str) -> str:
    """Normalize platform name using aliases."""
    platform = platform.lower().strip()
    return PLATFORM_ALIASES.get(platform, platform)


def get_platforms_by_region(region: str) -> List[str]:
    """Get list of platforms supported in a specific region."""
    return [
        platform_id
        for platform_id, info in SUPPORTED_PLATFORMS.items()
        if region in info["supported_regions"]
    ]


def get_firs_compliant_platforms() -> List[str]:
    """Get list of platforms that support FIRS e-invoicing compliance."""
    return [
        platform_id
        for platform_id, info in SUPPORTED_PLATFORMS.items()
        if info["compliance"].get("firs_einvoicing", False)
    ]


# Integration statistics
INTEGRATION_STATS = {
    "total_platforms": len(SUPPORTED_PLATFORMS),
    "total_vendors": len(set(info["vendor"] for info in SUPPORTED_PLATFORMS.values())),
    "supported_regions": list(set().union(*[
        info["supported_regions"] for info in SUPPORTED_PLATFORMS.values()
    ])),
    "supported_currencies": list(set().union(*[
        info["supported_currencies"] for info in SUPPORTED_PLATFORMS.values()
    ])),
    "firs_compliant_count": len(get_firs_compliant_platforms()),
    "webhook_enabled_count": len([
        p for p in SUPPORTED_PLATFORMS.values()
        if p["features"].get("webhook_support", False)
    ])
}