"""
POS Systems Integration
Comprehensive suite of Point-of-Sale platform connectors for Nigerian e-invoicing compliance.
"""

from typing import Dict, List, Optional, Any, Type, Union
import logging

# Import all POS platform connectors
from .square import SquareConnector, create_square_connector
from .clover import CloverConnector, create_clover_connector  
from .toast import ToastConnector, create_toast_connector
from .lightspeed import LightspeedConnector, create_lightspeed_connector
from .shopify_pos import ShopifyPOSConnector, create_shopify_pos_connector
from .opay import OPayConnector, create_opay_connector
from .palmpay import PalmPayConnector, create_palmpay_connector
from .moniepoint import MoniepointConnector, create_moniepoint_connector

# Import base connector for type hints
from ...framework.pos.base_connector import BasePOSConnector


logger = logging.getLogger(__name__)


__version__ = "1.0.0"
__author__ = "TaxPoynt Development Team"
__email__ = "dev@taxpoynt.com"

# Package metadata
__title__ = "POS Systems Integration Suite"
__description__ = "Complete Point-of-Sale platform connectors for Nigerian e-invoicing compliance"
__url__ = "https://github.com/taxpoynt/taxpoynt-platform"
__license__ = "MIT"
__copyright__ = "Copyright 2024 TaxPoynt"


# Supported POS platforms
SUPPORTED_PLATFORMS = {
    "square": {
        "name": "Square POS",
        "connector_class": SquareConnector,
        "factory_function": create_square_connector,
        "vendor": "Block Inc.",
        "api_type": "REST",
        "authentication": "OAuth2 + Bearer Token",
        "supported_regions": ["US", "CA", "AU", "JP", "GB", "IE", "FR", "ES", "NG"],
        "supported_currencies": ["USD", "CAD", "AUD", "JPY", "GBP", "EUR", "NGN"],
        "features": {
            "multi_location": True,
            "real_time_sync": True,
            "webhook_support": True,
            "batch_operations": True,
            "inventory_management": True,
            "payment_processing": True,
            "customer_management": True,
            "employee_management": True,
            "reporting_analytics": True,
            "loyalty_programs": True,
            "gift_cards": True,
            "offline_mode": True
        },
        "compliance": {
            "firs_einvoicing": True,
            "ubl_2_1": True,
            "nigerian_vat": True,
            "pci_compliance": True,
            "receipt_generation": True
        }
    },
    
    "clover": {  
        "name": "Clover POS",
        "connector_class": CloverConnector,
        "factory_function": create_clover_connector,
        "vendor": "Fiserv Inc.",
        "api_type": "REST",
        "authentication": "OAuth2 + API Token",
        "supported_regions": ["US", "CA", "NG"],
        "supported_currencies": ["USD", "CAD", "NGN"],
        "features": {
            "multi_merchant": True,
            "real_time_sync": True,
            "webhook_support": True,
            "batch_operations": True,
            "inventory_tracking": True,
            "payment_gateway": True,
            "customer_database": True,
            "employee_roles": True,
            "sales_reporting": True,
            "app_marketplace": True,
            "hardware_integration": True,
            "table_service": True
        },
        "compliance": {
            "firs_einvoicing": True,
            "ubl_2_1": True,
            "nigerian_vat": True,
            "pci_dss": True,
            "receipt_printing": True
        }
    },
    
    "toast": {
        "name": "Toast POS",
        "connector_class": ToastConnector,
        "factory_function": create_toast_connector,
        "vendor": "Toast Inc.",
        "api_type": "REST",
        "authentication": "OAuth2 + Client Credentials",
        "supported_regions": ["US", "CA", "NG"],
        "supported_currencies": ["USD", "CAD", "NGN"],
        "features": {
            "multi_restaurant": True,
            "real_time_sync": True,
            "webhook_support": True,
            "batch_operations": True,
            "menu_management": True,
            "order_management": True,
            "payment_processing": True,
            "kitchen_display": True,
            "delivery_integration": True,
            "loyalty_programs": True,
            "restaurant_analytics": True,
            "staff_scheduling": True
        },
        "compliance": {
            "firs_einvoicing": True,
            "ubl_2_1": True,
            "nigerian_vat": True,
            "restaurant_compliance": True,
            "receipt_management": True
        }
    },
    
    "lightspeed": {
        "name": "Lightspeed Retail POS",
        "connector_class": LightspeedConnector,
        "factory_function": create_lightspeed_connector,
        "vendor": "Lightspeed Commerce Inc.",
        "api_type": "REST",
        "authentication": "OAuth2",
        "supported_regions": ["US", "CA", "EU", "AU", "NG"],
        "supported_currencies": ["USD", "CAD", "EUR", "GBP", "AUD", "NGN"],
        "features": {
            "multi_store": True,
            "real_time_sync": True,
            "webhook_support": True,
            "batch_operations": True,
            "advanced_inventory": True,
            "ecommerce_integration": True,
            "customer_profiles": True,
            "supplier_management": True,
            "reporting_suite": True,
            "omnichannel": True,
            "barcode_scanning": True,
            "purchase_orders": True
        },
        "compliance": {
            "firs_einvoicing": True,
            "ubl_2_1": True,
            "nigerian_vat": True,
            "retail_compliance": True,
            "receipt_generation": True
        }
    },
    
    "shopify_pos": {
        "name": "Shopify POS",
        "connector_class": ShopifyPOSConnector,
        "factory_function": create_shopify_pos_connector,
        "vendor": "Shopify Inc.",
        "api_type": "REST + GraphQL",
        "authentication": "OAuth2 + Private App",
        "supported_regions": ["US", "CA", "EU", "UK", "AU", "NG"],
        "supported_currencies": ["USD", "CAD", "EUR", "GBP", "AUD", "NGN"],
        "features": {
            "multi_location": True,
            "real_time_sync": True,
            "webhook_support": True,
            "batch_operations": True,
            "unified_inventory": True,
            "online_store_sync": True,
            "customer_sync": True,
            "staff_permissions": True,
            "sales_channels": True,
            "app_extensions": True,
            "mobile_pos": True,
            "omnichannel_retail": True
        },
        "compliance": {
            "firs_einvoicing": True,
            "ubl_2_1": True,
            "nigerian_vat": True,
            "omnichannel_compliance": True,
            "receipt_system": True
        }
    },
    
    "opay": {
        "name": "OPay POS",
        "connector_class": OPayConnector,
        "factory_function": create_opay_connector,
        "vendor": "Opera Limited",
        "api_type": "REST",
        "authentication": "API Key + Signature",
        "supported_regions": ["NG", "EG", "KE", "GH"],
        "supported_currencies": ["NGN", "EGP", "KES", "GHS"],
        "features": {
            "multi_agent": True,
            "real_time_sync": True,
            "webhook_support": True,
            "batch_operations": True,
            "mobile_money": True,
            "card_payments": True,
            "bank_transfers": True,
            "qr_payments": True,
            "transaction_history": True,
            "settlement_reports": True,
            "agent_management": True,
            "africa_focused": True
        },
        "compliance": {
            "firs_einvoicing": True,
            "ubl_2_1": True,
            "nigerian_vat": True,
            "cbn_compliance": True,
            "mobile_money_regulations": True
        }
    },
    
    "palmpay": {
        "name": "PalmPay POS",
        "connector_class": PalmPayConnector,
        "factory_function": create_palmpay_connector,
        "vendor": "PalmPay Limited",
        "api_type": "REST",
        "authentication": "API Key + HMAC",
        "supported_regions": ["NG", "GH", "KE", "TZ"],
        "supported_currencies": ["NGN", "GHS", "KES", "TZS"],
        "features": {
            "agent_network": True,
            "real_time_sync": True,
            "webhook_support": True,
            "batch_operations": True,
            "digital_payments": True,
            "pos_terminals": True,
            "mobile_wallet": True,
            "bill_payments": True,
            "airtime_topup": True,
            "merchant_services": True,
            "financial_services": True,
            "african_markets": True
        },
        "compliance": {
            "firs_einvoicing": True,
            "ubl_2_1": True,
            "nigerian_vat": True,
            "financial_regulations": True,
            "transaction_compliance": True
        }
    },
    
    "moniepoint": {
        "name": "Moniepoint POS",
        "connector_class": MoniepointConnector,
        "factory_function": create_moniepoint_connector,
        "vendor": "TeamApt Limited",
        "api_type": "REST",
        "authentication": "OAuth2 + API Key",
        "supported_regions": ["NG"],
        "supported_currencies": ["NGN"],
        "features": {
            "agent_banking": True,
            "real_time_sync": True,
            "webhook_support": True,
            "batch_operations": True,
            "card_acceptance": True,
            "bank_transfers": True,
            "cash_withdrawal": True,
            "bill_payments": True,
            "account_opening": True,
            "loan_disbursement": True,
            "merchant_acquiring": True,
            "nigeria_focused": True
        },
        "compliance": {
            "firs_einvoicing": True,
            "ubl_2_1": True,
            "nigerian_vat": True,
            "cbn_regulations": True,
            "banking_compliance": True
        }
    }
}


# Platform aliases for convenience
PLATFORM_ALIASES = {
    "sq": "square",
    "square_pos": "square",
    
    "clover_pos": "clover",
    
    "toast_pos": "toast",
    "toast_tab": "toast",
    
    "lightspeed_retail": "lightspeed",
    "ls": "lightspeed",
    
    "shopify_point_of_sale": "shopify_pos",
    "spos": "shopify_pos",
    
    "opay_pos": "opay",
    
    "palmpay_pos": "palmpay",
    "pp": "palmpay",
    
    "moniepoint_pos": "moniepoint",
    "mp": "moniepoint"
}


# Export main classes and functions
__all__ = [
    # Platform connectors
    "SquareConnector",
    "CloverConnector", 
    "ToastConnector",
    "LightspeedConnector",
    "ShopifyPOSConnector",
    "OPayConnector",
    "PalmPayConnector",
    "MoniepointConnector",
    
    # Factory functions
    "create_pos_connector",
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
    "POSPlatformError",
    "UnsupportedPlatformError",
    "ConfigurationError"
]


class POSPlatformError(Exception):
    """Base exception for POS platform errors."""
    pass


class UnsupportedPlatformError(POSPlatformError):
    """Raised when an unsupported platform is requested."""
    pass


class ConfigurationError(POSPlatformError):
    """Raised when platform configuration is invalid."""
    pass


def create_pos_connector(
    platform: str,
    config: Dict[str, Any],
    session=None
) -> BasePOSConnector:
    """
    Create a POS connector for the specified platform.
    
    Args:
        platform: Platform identifier (e.g., 'square', 'clover', 'toast')
        config: Platform-specific configuration
        session: Optional aiohttp session
        
    Returns:
        Configured POS connector instance
        
    Example:
        >>> config = {
        ...     "application_id": "your_app_id",
        ...     "access_token": "your_access_token",
        ...     "environment": "sandbox",
        ...     "location_id": "your_location_id"
        ... }
        >>> connector = create_pos_connector("square", config)
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
) -> BasePOSConnector:
    """
    Create POS connector from unified configuration.
    
    Args:
        config: Configuration dict with 'platform' field and platform-specific settings
        session: Optional aiohttp session
        
    Returns:
        Configured POS connector instance
    """
    if "platform" not in config:
        raise ConfigurationError("Configuration must include 'platform' field")
    
    platform = config.pop("platform")
    return create_pos_connector(platform, config, session)


def get_platform_connector(platform: str) -> Type[BasePOSConnector]:
    """Get connector class for specified platform."""
    platform = _normalize_platform_name(platform)
    
    if platform not in SUPPORTED_PLATFORMS:
        raise UnsupportedPlatformError(f"Platform '{platform}' is not supported")
    
    return SUPPORTED_PLATFORMS[platform]["connector_class"]


def get_connector_class(platform: str) -> Type[BasePOSConnector]:
    """Alias for get_platform_connector for backward compatibility."""
    return get_platform_connector(platform)


def list_supported_platforms() -> List[Dict[str, Any]]:
    """Get list of all supported POS platforms."""
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


def get_african_focused_platforms() -> List[str]:
    """Get list of platforms with specific focus on African markets."""
    return [
        platform_id
        for platform_id, info in SUPPORTED_PLATFORMS.items()
        if info["features"].get("africa_focused", False) or 
           info["features"].get("african_markets", False) or
           info["features"].get("nigeria_focused", False)
    ]


def get_mobile_payment_platforms() -> List[str]:
    """Get list of platforms that support mobile payment methods."""
    mobile_features = ["mobile_money", "mobile_wallet", "digital_payments", "qr_payments"]
    return [
        platform_id
        for platform_id, info in SUPPORTED_PLATFORMS.items()
        if any(info["features"].get(feature, False) for feature in mobile_features)
    ]


def get_omnichannel_platforms() -> List[str]:
    """Get list of platforms that support omnichannel retail."""
    omnichannel_features = ["omnichannel", "omnichannel_retail", "online_store_sync", "ecommerce_integration"]
    return [
        platform_id
        for platform_id, info in SUPPORTED_PLATFORMS.items()
        if any(info["features"].get(feature, False) for feature in omnichannel_features)
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
    "african_focused_count": len(get_african_focused_platforms()),
    "mobile_payment_count": len(get_mobile_payment_platforms()),
    "omnichannel_count": len(get_omnichannel_platforms())
}


# POS-specific utilities
def get_restaurant_pos_platforms() -> List[str]:
    """Get list of POS platforms designed for restaurants."""
    restaurant_features = ["table_service", "kitchen_display", "menu_management", "restaurant_analytics"]
    return [
        platform_id
        for platform_id, info in SUPPORTED_PLATFORMS.items()
        if any(info["features"].get(feature, False) for feature in restaurant_features)
    ]


def get_retail_pos_platforms() -> List[str]:
    """Get list of POS platforms designed for retail."""
    retail_features = ["advanced_inventory", "barcode_scanning", "purchase_orders", "supplier_management"]
    return [
        platform_id
        for platform_id, info in SUPPORTED_PLATFORMS.items()
        if any(info["features"].get(feature, False) for feature in retail_features)
    ]


def get_financial_services_platforms() -> List[str]:
    """Get list of POS platforms that offer financial services."""
    financial_features = ["agent_banking", "loan_disbursement", "account_opening", "financial_services"]
    return [
        platform_id
        for platform_id, info in SUPPORTED_PLATFORMS.items()
        if any(info["features"].get(feature, False) for feature in financial_features)
    ]


# Hardware compatibility information
HARDWARE_COMPATIBILITY = {
    "square": {
        "terminals": ["Square Terminal", "Square Register", "Square Stand"],
        "card_readers": ["Square Reader", "Square Contactless and Chip Reader"],
        "receipt_printers": ["Star TSP143IIIU", "Epson TM-m30"],
        "cash_drawers": ["APG Vasario 1616", "Star SMD2-1317"]
    },
    "clover": {
        "terminals": ["Clover Station", "Clover Mini", "Clover Flex", "Clover Go"],
        "card_readers": ["Built-in EMV", "Clover Go Card Reader"],
        "receipt_printers": ["Built-in thermal printer", "Star TSP650II"],
        "cash_drawers": ["APG Series 4000", "M-S Cash Drawer"]
    },
    "toast": {
        "terminals": ["Toast Flex", "Toast Go", "Kitchen Display System"],
        "card_readers": ["Integrated payment processing", "External EMV readers"],
        "receipt_printers": ["Star TSP143IIIU", "Epson TM-T88V"],
        "kitchen_displays": ["Toast KDS", "Tablet-based displays"]
    }
}