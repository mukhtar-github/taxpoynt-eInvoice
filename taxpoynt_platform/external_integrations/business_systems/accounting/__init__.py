"""
Accounting Systems Integration
Comprehensive suite of accounting platform connectors for Nigerian e-invoicing compliance.
"""

from typing import Dict, List, Optional, Any, Type, Union
import logging

# Import all accounting platform connectors
from .quickbooks import QuickBooksConnector, create_quickbooks_connector
from .xero import XeroConnector, create_xero_connector  
from .sage import SageConnector, create_sage_connector
from .wave import WaveConnector, create_wave_connector
from .freshbooks import FreshBooksConnector, create_freshbooks_connector

# Import base connector for type hints
from ...framework.accounting.base_connector import BaseAccountingConnector

# Import common exceptions
from .quickbooks.exceptions import QuickBooksException
from .xero.exceptions import XeroException
from .sage.exceptions import SageException
from .wave.exceptions import WaveException
from .freshbooks.exceptions import FreshBooksException


logger = logging.getLogger(__name__)


__version__ = "1.0.0"
__author__ = "TaxPoynt Development Team"
__email__ = "dev@taxpoynt.com"

# Package metadata
__title__ = "Accounting Systems Integration Suite"
__description__ = "Complete accounting platform connectors for Nigerian e-invoicing compliance"
__url__ = "https://github.com/taxpoynt/taxpoynt-platform"
__license__ = "MIT"
__copyright__ = "Copyright 2024 TaxPoynt"


# Supported accounting platforms
SUPPORTED_PLATFORMS = {
    "quickbooks": {
        "name": "QuickBooks Online",
        "connector_class": QuickBooksConnector,
        "factory_function": create_quickbooks_connector,
        "vendor": "Intuit Inc.",
        "api_type": "REST",
        "authentication": "OAuth2",
        "supported_regions": ["US", "CA", "UK", "AU", "NG"],
        "supported_currencies": ["USD", "CAD", "GBP", "AUD", "NGN", "EUR"],
        "features": {
            "multi_company": True,
            "real_time_sync": True,
            "webhook_support": True,
            "batch_operations": True,
            "custom_fields": True,
            "attachments": True,
            "inventory_tracking": True,
            "project_tracking": True,
            "time_tracking": True
        },
        "rate_limits": {
            "requests_per_minute": 500,
            "burst_limit": 100
        },
        "compliance": {
            "firs_einvoicing": True,
            "ubl_2_1": True,
            "nigerian_vat": True,
            "multi_currency": True
        }
    },
    
    "xero": {  
        "name": "Xero",
        "connector_class": XeroConnector,
        "factory_function": create_xero_connector,
        "vendor": "Xero Limited",
        "api_type": "REST",
        "authentication": "OAuth2 + PKCE + OpenID Connect",
        "supported_regions": ["US", "UK", "AU", "NZ", "NG"],
        "supported_currencies": ["USD", "GBP", "AUD", "NZD", "NGN", "EUR", "CAD"],
        "features": {
            "multi_tenant": True,
            "real_time_sync": True,
            "webhook_support": True,
            "batch_operations": True,
            "custom_fields": False,
            "attachments": True,
            "inventory_tracking": True,
            "project_tracking": True,
            "payroll_integration": True
        },
        "rate_limits": {
            "requests_per_minute": 60,
            "daily_limit": 5000
        },
        "compliance": {
            "firs_einvoicing": True,
            "ubl_2_1": True,
            "nigerian_vat": True,
            "multi_currency": True
        }
    },
    
    "sage": {
        "name": "Sage Business Cloud Accounting",
        "connector_class": SageConnector,
        "factory_function": create_sage_connector,
        "vendor": "Sage Group plc",
        "api_type": "REST",
        "authentication": "OAuth2",
        "supported_regions": ["UK", "IE", "US", "CA", "ES", "FR", "DE", "NG"],
        "supported_currencies": ["GBP", "EUR", "USD", "CAD", "NGN"],
        "features": {
            "multi_business": True,
            "real_time_sync": True,
            "webhook_support": True,
            "batch_operations": True,
            "custom_fields": True,
            "attachments": True,
            "inventory_tracking": True,
            "multi_currency": True,
            "advanced_reporting": True
        },
        "rate_limits": {
            "requests_per_minute": 300,
            "requests_per_hour": 5000
        },
        "compliance": {
            "firs_einvoicing": True,
            "ubl_2_1": True,
            "nigerian_vat": True,
            "multi_currency": True,
            "uk_mtd": True
        }
    },
    
    "wave": {
        "name": "Wave Accounting",
        "connector_class": WaveConnector,
        "factory_function": create_wave_connector,
        "vendor": "Wave Financial Inc.",
        "api_type": "GraphQL",
        "authentication": "OAuth2 + PKCE",
        "supported_regions": ["US", "CA", "NG"],
        "supported_currencies": ["USD", "CAD", "NGN", "EUR", "GBP"],
        "features": {
            "multi_business": True,
            "real_time_sync": True,
            "webhook_support": True,
            "batch_operations": True,
            "custom_fields": False,
            "attachments": False,
            "inventory_tracking": False,
            "receipt_scanning": True,
            "payment_processing": True
        },
        "rate_limits": {
            "requests_per_minute": 60,
            "burst_limit": 10
        },
        "compliance": {
            "firs_einvoicing": True,
            "ubl_2_1": True,
            "nigerian_vat": True,
            "multi_currency": True
        }
    },
    
    "freshbooks": {
        "name": "FreshBooks",
        "connector_class": FreshBooksConnector,
        "factory_function": create_freshbooks_connector,
        "vendor": "FreshBooks Inc.",
        "api_type": "REST",
        "authentication": "OAuth2",
        "supported_regions": ["US", "CA", "EU", "NG"],
        "supported_currencies": ["USD", "CAD", "EUR", "GBP", "NGN", "AUD", "NZD"],
        "features": {
            "multi_account": True,
            "real_time_sync": True,
            "webhook_support": True,
            "batch_operations": True,
            "custom_fields": True,
            "attachments": True,
            "time_tracking": True,
            "expense_tracking": True,
            "project_management": True,
            "client_portal": True
        },
        "rate_limits": {
            "requests_per_minute": 300,
            "burst_limit": 20
        },
        "compliance": {
            "firs_einvoicing": True,
            "ubl_2_1": True,
            "nigerian_vat": True,
            "multi_currency": True
        }
    }
}


# Platform aliases for convenience
PLATFORM_ALIASES = {
    "qbo": "quickbooks",
    "quickbooks_online": "quickbooks",
    "intuit": "quickbooks",
    
    "xero_accounting": "xero",
    
    "sage_business_cloud": "sage",
    "sage_accounting": "sage",
    
    "wave_accounting": "wave",
    "waveapps": "wave",
    
    "freshbooks_classic": "freshbooks",
    "fb": "freshbooks"
}


# Export main classes and functions
__all__ = [
    # Platform connectors
    "QuickBooksConnector",
    "XeroConnector", 
    "SageConnector",
    "WaveConnector",
    "FreshBooksConnector",
    
    # Factory functions
    "create_accounting_connector",
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
    "AccountingPlatformError",
    "UnsupportedPlatformError",
    "ConfigurationError"
]


class AccountingPlatformError(Exception):
    """Base exception for accounting platform errors."""
    pass


class UnsupportedPlatformError(AccountingPlatformError):
    """Raised when an unsupported platform is requested."""
    pass


class ConfigurationError(AccountingPlatformError):
    """Raised when platform configuration is invalid."""
    pass


def create_accounting_connector(
    platform: str,
    config: Dict[str, Any],
    session=None
) -> BaseAccountingConnector:
    """
    Create an accounting connector for the specified platform.
    
    Args:
        platform: Platform identifier (e.g., 'quickbooks', 'xero', 'sage')
        config: Platform-specific configuration
        session: Optional aiohttp session
        
    Returns:
        Configured accounting connector instance
        
    Raises:
        UnsupportedPlatformError: If platform is not supported
        ConfigurationError: If configuration is invalid
        
    Example:
        >>> config = {
        ...     "client_id": "your_client_id",
        ...     "client_secret": "your_client_secret",
        ...     "redirect_uri": "https://your-app.com/callback",
        ...     "sandbox": True
        ... }
        >>> connector = create_accounting_connector("quickbooks", config)
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
) -> BaseAccountingConnector:
    """
    Create accounting connector from unified configuration.
    
    Args:
        config: Configuration dict with 'platform' field and platform-specific settings
        session: Optional aiohttp session
        
    Returns:
        Configured accounting connector instance
        
    Config format:
        {
            "platform": "quickbooks",
            "client_id": "client_id",
            "client_secret": "client_secret",
            "redirect_uri": "https://app.com/callback",
            "sandbox": true
        }
        
    Example:
        >>> config = {
        ...     "platform": "xero",
        ...     "client_id": "xero_client_id",
        ...     "client_secret": "xero_client_secret",
        ...     "redirect_uri": "https://app.com/callback",
        ...     "sandbox": True
        ... }
        >>> connector = create_connector_from_config(config)
    """
    if "platform" not in config:
        raise ConfigurationError("Configuration must include 'platform' field")
    
    platform = config.pop("platform")
    return create_accounting_connector(platform, config, session)


def get_platform_connector(platform: str) -> Type[BaseAccountingConnector]:
    """
    Get connector class for specified platform.
    
    Args:
        platform: Platform identifier
        
    Returns:
        Connector class
        
    Example:
        >>> connector_class = get_platform_connector("quickbooks")
        >>> connector = connector_class(client_id="...", ...)
    """
    platform = _normalize_platform_name(platform)
    
    if platform not in SUPPORTED_PLATFORMS:
        raise UnsupportedPlatformError(f"Platform '{platform}' is not supported")
    
    return SUPPORTED_PLATFORMS[platform]["connector_class"]


def get_connector_class(platform: str) -> Type[BaseAccountingConnector]:
    """Alias for get_platform_connector for backward compatibility."""
    return get_platform_connector(platform)


def list_supported_platforms() -> List[Dict[str, Any]]:
    """
    Get list of all supported accounting platforms.
    
    Returns:
        List of platform information dictionaries
        
    Example:
        >>> platforms = list_supported_platforms()
        >>> for platform in platforms:
        ...     print(f"{platform['name']} - {platform['vendor']}")
    """
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
    """
    Get detailed information about a specific platform.
    
    Args:
        platform: Platform identifier
        
    Returns:
        Platform information dictionary
        
    Example:
        >>> info = get_platform_info("quickbooks")
        >>> print(f"Rate limit: {info['rate_limits']['requests_per_minute']}/min")
    """
    platform = _normalize_platform_name(platform)
    
    if platform not in SUPPORTED_PLATFORMS:
        raise UnsupportedPlatformError(f"Platform '{platform}' is not supported")
    
    return SUPPORTED_PLATFORMS[platform].copy()


def validate_platform_config(platform: str, config: Dict[str, Any]) -> List[str]:
    """
    Validate configuration for specified platform.
    
    Args:
        platform: Platform identifier
        config: Configuration to validate
        
    Returns:
        List of validation errors (empty if valid)
        
    Example:
        >>> errors = validate_platform_config("quickbooks", config)
        >>> if errors:
        ...     print(f"Configuration errors: {errors}")
    """
    platform = _normalize_platform_name(platform)
    
    if platform not in SUPPORTED_PLATFORMS:
        return [f"Platform '{platform}' is not supported"]
    
    errors = []
    
    # Common required fields for OAuth2
    required_fields = ["client_id", "client_secret", "redirect_uri"]
    
    for field in required_fields:
        if field not in config:
            errors.append(f"Missing required field: {field}")
        elif not config[field]:
            errors.append(f"Empty value for required field: {field}")
    
    # Validate redirect URI format
    if "redirect_uri" in config:
        redirect_uri = config["redirect_uri"]
        if not redirect_uri.startswith(("http://", "https://")):
            errors.append("Redirect URI must start with http:// or https://")
    
    # Validate sandbox setting if present
    if "sandbox" in config and not isinstance(config["sandbox"], bool):
        errors.append("Sandbox setting must be boolean")
    
    return errors


def get_platforms_by_region(region: str) -> List[str]:
    """
    Get list of platforms supported in a specific region.
    
    Args:
        region: Region code (e.g., 'US', 'NG', 'UK')
        
    Returns:
        List of platform identifiers
        
    Example:
        >>> ng_platforms = get_platforms_by_region("NG")
        >>> print(f"Platforms in Nigeria: {ng_platforms}")
    """
    return [
        platform_id
        for platform_id, info in SUPPORTED_PLATFORMS.items()
        if region in info["supported_regions"]
    ]


def get_platforms_by_currency(currency: str) -> List[str]:
    """
    Get list of platforms that support a specific currency.
    
    Args:
        currency: Currency code (e.g., 'NGN', 'USD', 'EUR')
        
    Returns:
        List of platform identifiers
        
    Example:
        >>> ngn_platforms = get_platforms_by_currency("NGN")
        >>> print(f"Platforms supporting NGN: {ngn_platforms}")
    """
    return [
        platform_id
        for platform_id, info in SUPPORTED_PLATFORMS.items()
        if currency in info["supported_currencies"]
    ]


def get_platforms_with_feature(feature: str) -> List[str]:
    """
    Get list of platforms that support a specific feature.
    
    Args:
        feature: Feature name (e.g., 'webhook_support', 'multi_currency')
        
    Returns:
        List of platform identifiers
        
    Example:
        >>> webhook_platforms = get_platforms_with_feature("webhook_support")
        >>> print(f"Platforms with webhooks: {webhook_platforms}")
    """
    return [
        platform_id
        for platform_id, info in SUPPORTED_PLATFORMS.items()
        if info["features"].get(feature, False)
    ]


def get_firs_compliant_platforms() -> List[str]:
    """
    Get list of platforms that support FIRS e-invoicing compliance.
    
    Returns:
        List of platform identifiers
        
    Example:
        >>> firs_platforms = get_firs_compliant_platforms()
        >>> print(f"FIRS compliant platforms: {firs_platforms}")
    """
    return [
        platform_id
        for platform_id, info in SUPPORTED_PLATFORMS.items()
        if info["compliance"].get("firs_einvoicing", False)
    ]


def _normalize_platform_name(platform: str) -> str:
    """Normalize platform name using aliases."""
    platform = platform.lower().strip()
    return PLATFORM_ALIASES.get(platform, platform)


# Platform comparison utilities
def compare_platforms(platforms: List[str]) -> Dict[str, Any]:
    """
    Compare features and capabilities across multiple platforms.
    
    Args:
        platforms: List of platform identifiers to compare
        
    Returns:
        Comparison matrix
        
    Example:
        >>> comparison = compare_platforms(["quickbooks", "xero", "sage"])
        >>> print(comparison["feature_matrix"])
    """
    normalized_platforms = [_normalize_platform_name(p) for p in platforms]
    
    # Validate all platforms are supported
    unsupported = [p for p in normalized_platforms if p not in SUPPORTED_PLATFORMS]
    if unsupported:
        raise UnsupportedPlatformError(f"Unsupported platforms: {unsupported}")
    
    # Collect all unique features
    all_features = set()
    for platform in normalized_platforms:
        all_features.update(SUPPORTED_PLATFORMS[platform]["features"].keys())
    
    # Build feature matrix
    feature_matrix = {}
    for feature in sorted(all_features):
        feature_matrix[feature] = {
            platform: SUPPORTED_PLATFORMS[platform]["features"].get(feature, False)
            for platform in normalized_platforms
        }
    
    # Build summary
    summary = {
        "platforms": normalized_platforms,
        "platform_count": len(normalized_platforms),
        "feature_matrix": feature_matrix,
        "common_features": [
            feature for feature, support in feature_matrix.items()
            if all(support.values())
        ],
        "unique_features": {
            platform: [
                feature for feature, support in feature_matrix.items()
                if support[platform] and not all(
                    support[p] for p in normalized_platforms if p != platform
                )
            ]
            for platform in normalized_platforms
        }
    }
    
    return summary


# Integration health check
async def health_check_all_platforms(configs: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """
    Perform health check on all configured platforms.
    
    Args:
        configs: Dictionary of platform configs {platform_id: config}
        
    Returns:
        Health check results for all platforms
        
    Example:
        >>> configs = {
        ...     "quickbooks": {"client_id": "...", "client_secret": "...", ...},
        ...     "xero": {"client_id": "...", "client_secret": "...", ...}
        ... }
        >>> results = await health_check_all_platforms(configs)
    """
    results = {}
    
    for platform_id, config in configs.items():
        try:
            connector = create_accounting_connector(platform_id, config)
            
            async with connector:
                # Perform basic connectivity test
                if hasattr(connector, 'test_connection'):
                    test_result = await connector.test_connection()
                    results[platform_id] = {
                        "status": "healthy" if test_result.get("success") else "unhealthy",
                        "details": test_result,
                        "error": None
                    }
                else:
                    results[platform_id] = {
                        "status": "unknown",
                        "details": "Health check not implemented",
                        "error": None
                    }
                    
        except Exception as e:
            logger.error(f"Health check failed for {platform_id}: {e}")
            results[platform_id] = {
                "status": "unhealthy", 
                "details": None,
                "error": str(e)
            }
    
    return results


# Batch operations across platforms
class MultiPlatformConnector:
    """
    Wrapper for managing multiple accounting platform connectors simultaneously.
    
    Useful for scenarios where you need to sync data across multiple platforms
    or provide unified access to multiple accounting systems.
    """
    
    def __init__(self, configs: Dict[str, Dict[str, Any]]):
        """
        Initialize multi-platform connector.
        
        Args:
            configs: Dictionary of platform configs {platform_id: config}
        """
        self.configs = configs
        self.connectors: Dict[str, BaseAccountingConnector] = {}
        
        # Initialize all connectors
        for platform_id, config in configs.items():
            self.connectors[platform_id] = create_accounting_connector(platform_id, config)
    
    async def __aenter__(self):
        """Async context manager entry."""
        for connector in self.connectors.values():
            await connector.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        for connector in self.connectors.values():
            await connector.__aexit__(exc_type, exc_val, exc_tb)
    
    def get_connector(self, platform: str) -> BaseAccountingConnector:
        """Get connector for specific platform."""
        platform = _normalize_platform_name(platform)
        if platform not in self.connectors:
            raise UnsupportedPlatformError(f"Platform '{platform}' not configured")
        return self.connectors[platform]
    
    def list_platforms(self) -> List[str]:
        """Get list of configured platforms."""
        return list(self.connectors.keys())
    
    async def health_check_all(self) -> Dict[str, Any]:
        """Perform health check on all connectors."""
        return await health_check_all_platforms(self.configs)


# Statistics and analytics
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
    "webhook_enabled_count": len(get_platforms_with_feature("webhook_support")),
    "multi_entity_count": len([
        p for p in SUPPORTED_PLATFORMS.values()
        if p["features"].get("multi_company") or 
           p["features"].get("multi_tenant") or 
           p["features"].get("multi_business") or
           p["features"].get("multi_account")
    ])
}