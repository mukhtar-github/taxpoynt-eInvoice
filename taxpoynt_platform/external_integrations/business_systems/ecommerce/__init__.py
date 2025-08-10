"""
E-Commerce Systems Integration
Comprehensive suite of e-commerce platform connectors for Nigerian e-invoicing compliance.
"""

from typing import Dict, List, Optional, Any, Type, Union
import logging

# Import all e-commerce platform connectors
from .shopify import ShopifyConnector, create_shopify_connector
from .woocommerce import WooCommerceConnector, create_woocommerce_connector  
from .magento import MagentoConnector, create_magento_connector
from .bigcommerce import BigCommerceConnector, create_bigcommerce_connector
from .jumia import JumiaConnector, create_jumia_connector

# Import base connector for type hints
from ...framework.ecommerce.base_connector import BaseECommerceConnector


logger = logging.getLogger(__name__)


__version__ = "1.0.0"
__author__ = "TaxPoynt Development Team"
__email__ = "dev@taxpoynt.com"

# Package metadata
__title__ = "E-Commerce Systems Integration Suite"
__description__ = "Complete e-commerce platform connectors for Nigerian e-invoicing compliance"
__url__ = "https://github.com/taxpoynt/taxpoynt-platform"
__license__ = "MIT"
__copyright__ = "Copyright 2024 TaxPoynt"


# Supported e-commerce platforms
SUPPORTED_PLATFORMS = {
    "shopify": {
        "name": "Shopify",
        "connector_class": ShopifyConnector,
        "factory_function": create_shopify_connector,
        "vendor": "Shopify Inc.",
        "api_type": "REST + GraphQL",
        "authentication": "OAuth2 + API Key",
        "supported_regions": ["US", "CA", "EU", "UK", "AU", "NG"],
        "supported_currencies": ["USD", "EUR", "GBP", "CAD", "AUD", "NGN", "JPY"],
        "features": {
            "multi_store": True,
            "real_time_sync": True,
            "webhook_support": True,
            "batch_operations": True,
            "inventory_management": True,
            "order_management": True,
            "customer_management": True,
            "product_variants": True,
            "discount_codes": True,
            "shipping_zones": True,
            "payment_gateways": True,
            "app_extensions": True
        },
        "compliance": {
            "firs_einvoicing": True,
            "ubl_2_1": True,
            "nigerian_vat": True,
            "multi_currency": True,
            "tax_calculation": True
        }
    },
    
    "woocommerce": {  
        "name": "WooCommerce",
        "connector_class": WooCommerceConnector,
        "factory_function": create_woocommerce_connector,
        "vendor": "Automattic Inc.",
        "api_type": "REST",
        "authentication": "API Key + Secret",
        "supported_regions": ["Global", "NG"],
        "supported_currencies": ["USD", "EUR", "GBP", "NGN", "CAD", "AUD"],
        "features": {
            "multi_site": True,
            "real_time_sync": True,
            "webhook_support": True,
            "batch_operations": True,
            "inventory_tracking": True,
            "order_statuses": True,
            "customer_accounts": True,
            "product_categories": True,
            "coupon_system": True,
            "shipping_methods": True,
            "payment_methods": True,
            "plugin_extensions": True
        },
        "compliance": {
            "firs_einvoicing": True,
            "ubl_2_1": True,
            "nigerian_vat": True,
            "multi_currency": True,
            "tax_calculation": True
        }
    },
    
    "magento": {
        "name": "Magento Commerce",
        "connector_class": MagentoConnector,
        "factory_function": create_magento_connector,
        "vendor": "Adobe Inc.",
        "api_type": "REST + GraphQL",
        "authentication": "OAuth2 + Token",
        "supported_regions": ["US", "EU", "APAC", "NG"],
        "supported_currencies": ["USD", "EUR", "GBP", "NGN", "CAD", "AUD"],
        "features": {
            "multi_store": True,
            "real_time_sync": True,
            "webhook_support": True,
            "batch_operations": True,
            "advanced_inventory": True,
            "order_management": True,
            "customer_segmentation": True,
            "configurable_products": True,
            "price_rules": True,
            "advanced_shipping": True,
            "payment_integration": True,
            "b2b_features": True
        },
        "compliance": {
            "firs_einvoicing": True,
            "ubl_2_1": True,
            "nigerian_vat": True,
            "multi_currency": True,
            "tax_calculation": True
        }
    },
    
    "bigcommerce": {
        "name": "BigCommerce",
        "connector_class": BigCommerceConnector,
        "factory_function": create_bigcommerce_connector,
        "vendor": "BigCommerce Inc.",
        "api_type": "REST + GraphQL",
        "authentication": "OAuth2 + API Token",
        "supported_regions": ["US", "EU", "AU", "NG"],
        "supported_currencies": ["USD", "EUR", "GBP", "AUD", "NGN", "CAD"],
        "features": {
            "multi_store": True,
            "real_time_sync": True,
            "webhook_support": True,
            "batch_operations": True,
            "inventory_tracking": True,
            "order_processing": True,
            "customer_groups": True,
            "product_options": True,
            "promotional_tools": True,
            "shipping_calculator": True,
            "payment_methods": True,
            "headless_commerce": True
        },
        "compliance": {
            "firs_einvoicing": True,
            "ubl_2_1": True,
            "nigerian_vat": True,
            "multi_currency": True,
            "tax_calculation": True
        }
    },
    
    "jumia": {
        "name": "Jumia Marketplace",
        "connector_class": JumiaConnector,
        "factory_function": create_jumia_connector,
        "vendor": "Jumia Technologies",
        "api_type": "REST",
        "authentication": "API Key",
        "supported_regions": ["NG", "KE", "EG", "MA", "GH", "CI", "UG", "TN"],
        "supported_currencies": ["NGN", "KES", "EGP", "MAD", "GHS", "XOF", "UGX", "TND"],
        "features": {
            "marketplace_integration": True,
            "real_time_sync": True,
            "webhook_support": True,
            "batch_operations": True,
            "inventory_sync": True,
            "order_fulfillment": True,
            "seller_management": True,
            "product_catalog": True,
            "pricing_management": True,
            "logistics_integration": True,
            "payment_tracking": True,
            "africa_focused": True
        },
        "compliance": {
            "firs_einvoicing": True,
            "ubl_2_1": True,
            "nigerian_vat": True,
            "multi_currency": True,
            "african_tax_systems": True
        }
    }
}


# Platform aliases for convenience
PLATFORM_ALIASES = {
    "shopify_plus": "shopify",
    
    "woo": "woocommerce",
    "wordpress_commerce": "woocommerce",
    
    "magento2": "magento",
    "adobe_commerce": "magento",
    
    "bigcom": "bigcommerce",
    "bc": "bigcommerce",
    
    "jumia_marketplace": "jumia"
}


# Export main classes and functions
__all__ = [
    # Platform connectors
    "ShopifyConnector",
    "WooCommerceConnector", 
    "MagentoConnector",
    "BigCommerceConnector",
    "JumiaConnector",
    
    # Factory functions
    "create_ecommerce_connector",
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
    "ECommercePlatformError",
    "UnsupportedPlatformError",
    "ConfigurationError"
]


class ECommercePlatformError(Exception):
    """Base exception for e-commerce platform errors."""
    pass


class UnsupportedPlatformError(ECommercePlatformError):
    """Raised when an unsupported platform is requested."""
    pass


class ConfigurationError(ECommercePlatformError):
    """Raised when platform configuration is invalid."""
    pass


def create_ecommerce_connector(
    platform: str,
    config: Dict[str, Any],
    session=None
) -> BaseECommerceConnector:
    """
    Create an e-commerce connector for the specified platform.
    
    Args:
        platform: Platform identifier (e.g., 'shopify', 'woocommerce', 'magento')
        config: Platform-specific configuration
        session: Optional aiohttp session
        
    Returns:
        Configured e-commerce connector instance
        
    Example:
        >>> config = {
        ...     "shop_domain": "your-shop.myshopify.com",
        ...     "api_key": "your_api_key",
        ...     "api_secret": "your_api_secret",
        ...     "access_token": "your_access_token"
        ... }
        >>> connector = create_ecommerce_connector("shopify", config)
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
) -> BaseECommerceConnector:
    """
    Create e-commerce connector from unified configuration.
    
    Args:
        config: Configuration dict with 'platform' field and platform-specific settings
        session: Optional aiohttp session
        
    Returns:
        Configured e-commerce connector instance
    """
    if "platform" not in config:
        raise ConfigurationError("Configuration must include 'platform' field")
    
    platform = config.pop("platform")
    return create_ecommerce_connector(platform, config, session)


def get_platform_connector(platform: str) -> Type[BaseECommerceConnector]:
    """Get connector class for specified platform."""
    platform = _normalize_platform_name(platform)
    
    if platform not in SUPPORTED_PLATFORMS:
        raise UnsupportedPlatformError(f"Platform '{platform}' is not supported")
    
    return SUPPORTED_PLATFORMS[platform]["connector_class"]


def get_connector_class(platform: str) -> Type[BaseECommerceConnector]:
    """Alias for get_platform_connector for backward compatibility."""
    return get_platform_connector(platform)


def list_supported_platforms() -> List[Dict[str, Any]]:
    """Get list of all supported e-commerce platforms."""
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
        if region in info["supported_regions"] or "Global" in info["supported_regions"]
    ]


def get_firs_compliant_platforms() -> List[str]:
    """Get list of platforms that support FIRS e-invoicing compliance."""
    return [
        platform_id
        for platform_id, info in SUPPORTED_PLATFORMS.items()
        if info["compliance"].get("firs_einvoicing", False)
    ]


def get_african_focused_platforms() -> List[str]:
    """Get list of platforms with specific focus on African markets."""
    return [
        platform_id
        for platform_id, info in SUPPORTED_PLATFORMS.items()
        if info["features"].get("africa_focused", False) or 
           any(region in ["NG", "KE", "EG", "MA", "GH"] for region in info["supported_regions"])
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
    ]),
    "african_focused_count": len(get_african_focused_platforms())
}