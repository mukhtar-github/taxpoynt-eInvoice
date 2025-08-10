"""
Inventory Management Systems Integration
Comprehensive suite of inventory platform connectors for Nigerian e-invoicing compliance.
"""

from typing import Dict, List, Optional, Any, Type, Union
import logging

# Import inventory platform connectors (will be implemented)
try:
    from .cin7 import Cin7Connector, create_cin7_connector
    CIN7_AVAILABLE = True
except ImportError:
    CIN7_AVAILABLE = False
    logger.warning("Cin7 connector not available")

try:
    from .fishbowl import FishbowlConnector, create_fishbowl_connector
    FISHBOWL_AVAILABLE = True
except ImportError:
    FISHBOWL_AVAILABLE = False
    logger.warning("Fishbowl connector not available")

try:
    from .tradegecko import TradeGeckoConnector, create_tradegecko_connector
    TRADEGECKO_AVAILABLE = True
except ImportError:
    TRADEGECKO_AVAILABLE = False
    logger.warning("TradeGecko connector not available")

try:
    from .unleashed import UnleashedConnector, create_unleashed_connector
    UNLEASHED_AVAILABLE = True
except ImportError:
    UNLEASHED_AVAILABLE = False
    logger.warning("Unleashed connector not available")

# Import base connector for type hints
from ...connector_framework.base_inventory_connector import BaseInventoryConnector


logger = logging.getLogger(__name__)


__version__ = "1.0.0"
__author__ = "TaxPoynt Development Team"
__email__ = "dev@taxpoynt.com"

# Package metadata
__title__ = "Inventory Management Systems Integration Suite"
__description__ = "Complete inventory platform connectors for Nigerian e-invoicing compliance"
__url__ = "https://github.com/taxpoynt/taxpoynt-platform"
__license__ = "MIT"
__copyright__ = "Copyright 2024 TaxPoynt"


# Supported inventory platforms
SUPPORTED_PLATFORMS = {
    "cin7": {
        "name": "Cin7 Core",
        "connector_class": Cin7Connector if CIN7_AVAILABLE else None,
        "factory_function": create_cin7_connector if CIN7_AVAILABLE else None,
        "vendor": "Cin7 Limited",
        "api_type": "REST",
        "authentication": "API Token + Basic Auth",
        "supported_regions": ["Global", "US", "AU", "UK", "NG"],
        "supported_currencies": ["USD", "AUD", "GBP", "EUR", "NGN", "CAD"],
        "features": {
            "multi_warehouse": True,
            "real_time_sync": True,
            "webhook_support": True,
            "batch_operations": True,
            "advanced_inventory": True,
            "purchase_management": True,
            "sales_management": True,
            "supplier_management": True,
            "stock_movements": True,
            "barcode_support": True,
            "lot_tracking": True,
            "serial_tracking": True,
            "kitting_assembly": True,
            "landed_costs": True
        },
        "compliance": {
            "firs_einvoicing": True,
            "ubl_2_1": True,
            "nigerian_vat": True,
            "stock_valuation": True,
            "audit_trails": True
        },
        "available": CIN7_AVAILABLE
    },
    
    "fishbowl": {  
        "name": "Fishbowl Inventory",
        "connector_class": FishbowlConnector if FISHBOWL_AVAILABLE else None,
        "factory_function": create_fishbowl_connector if FISHBOWL_AVAILABLE else None,
        "vendor": "Fishbowl Inc.",
        "api_type": "REST + XML",
        "authentication": "API Key + Session",
        "supported_regions": ["US", "CA", "NG"],
        "supported_currencies": ["USD", "CAD", "NGN"],
        "features": {
            "quickbooks_integration": True,
            "real_time_sync": True,
            "webhook_support": False,
            "batch_operations": True,
            "manufacturing": True,
            "work_orders": True,
            "bill_of_materials": True,
            "cycle_counting": True,
            "pick_pack_ship": True,
            "barcode_scanning": True,
            "lot_serial_tracking": True,
            "multi_location": True,
            "landed_costs": True,
            "drop_shipping": True
        },
        "compliance": {
            "firs_einvoicing": True,
            "ubl_2_1": True,
            "nigerian_vat": True,
            "quickbooks_sync": True,
            "manufacturing_compliance": True
        },
        "available": FISHBOWL_AVAILABLE
    },
    
    "tradegecko": {
        "name": "QuickBooks Commerce (TradeGecko)",
        "connector_class": TradeGeckoConnector if TRADEGECKO_AVAILABLE else None,
        "factory_function": create_tradegecko_connector if TRADEGECKO_AVAILABLE else None,
        "vendor": "Intuit Inc.",
        "api_type": "REST",
        "authentication": "OAuth2",
        "supported_regions": ["US", "UK", "AU", "SG", "NG"],
        "supported_currencies": ["USD", "GBP", "AUD", "SGD", "NGN", "EUR"],
        "features": {
            "multi_channel": True,
            "real_time_sync": True,
            "webhook_support": True,
            "batch_operations": True,
            "ecommerce_integration": True,
            "b2b_wholesale": True,
            "order_management": True,
            "fulfillment": True,
            "reporting_analytics": True,
            "variant_management": True,
            "pricing_rules": True,
            "customer_portal": True,
            "mobile_app": True,
            "integrations_marketplace": True
        },
        "compliance": {
            "firs_einvoicing": True,
            "ubl_2_1": True,
            "nigerian_vat": True,
            "multi_channel_compliance": True,
            "quickbooks_integration": True
        },
        "available": TRADEGECKO_AVAILABLE
    },
    
    "unleashed": {
        "name": "Unleashed Software",
        "connector_class": UnleashedConnector if UNLEASHED_AVAILABLE else None,
        "factory_function": create_unleashed_connector if UNLEASHED_AVAILABLE else None,
        "vendor": "Unleashed Software Limited",
        "api_type": "REST",
        "authentication": "API Key + HMAC",
        "supported_regions": ["US", "UK", "AU", "NZ", "NG"],
        "supported_currencies": ["USD", "GBP", "AUD", "NZD", "NGN", "EUR"],
        "features": {
            "cloud_based": True,
            "real_time_sync": True,
            "webhook_support": True,
            "batch_operations": True,
            "manufacturing": True,
            "assembly_disassembly": True,
            "multi_warehouse": True,
            "purchase_planning": True,
            "sales_analytics": True,
            "batch_lot_tracking": True,
            "expiry_date_tracking": True,
            "landed_cost_tracking": True,
            "stock_forecasting": True,
            "mobile_stocktaking": True
        },
        "compliance": {
            "firs_einvoicing": True,
            "ubl_2_1": True,
            "nigerian_vat": True,
            "gst_compliance": True,
            "cloud_security": True
        },
        "available": UNLEASHED_AVAILABLE
    }
}


# Platform aliases for convenience
PLATFORM_ALIASES = {
    "cin7_core": "cin7",
    "cin7_omni": "cin7",
    
    "fishbowl_inventory": "fishbowl",
    "fb": "fishbowl",
    
    "quickbooks_commerce": "tradegecko",
    "qb_commerce": "tradegecko",
    "tg": "tradegecko",
    
    "unleashed_software": "unleashed",
    "us": "unleashed"
}


# Export main classes and functions
__all__ = [
    # Platform connectors (available ones)
    "Cin7Connector" if CIN7_AVAILABLE else None,
    "FishbowlConnector" if FISHBOWL_AVAILABLE else None, 
    "TradeGeckoConnector" if TRADEGECKO_AVAILABLE else None,
    "UnleashedConnector" if UNLEASHED_AVAILABLE else None,
    
    # Factory functions
    "create_inventory_connector",
    "create_connector_from_config",
    "get_platform_connector",
    
    # Utility functions
    "list_supported_platforms",
    "list_available_platforms",
    "get_platform_info",
    "validate_platform_config",
    "get_connector_class",
    
    # Platform registry
    "SUPPORTED_PLATFORMS",
    "PLATFORM_ALIASES",
    
    # Exception classes
    "InventoryPlatformError",
    "UnsupportedPlatformError",
    "ConfigurationError",
    "PlatformNotAvailableError"
]

# Remove None values from __all__
__all__ = [item for item in __all__ if item is not None]


class InventoryPlatformError(Exception):
    """Base exception for inventory platform errors."""
    pass


class UnsupportedPlatformError(InventoryPlatformError):
    """Raised when an unsupported platform is requested."""
    pass


class ConfigurationError(InventoryPlatformError):
    """Raised when platform configuration is invalid."""
    pass


class PlatformNotAvailableError(InventoryPlatformError):
    """Raised when a platform is supported but not currently available."""
    pass


def create_inventory_connector(
    platform: str,
    config: Dict[str, Any],
    session=None
) -> BaseInventoryConnector:
    """
    Create an inventory connector for the specified platform.
    
    Args:
        platform: Platform identifier (e.g., 'cin7', 'fishbowl', 'unleashed')
        config: Platform-specific configuration
        session: Optional aiohttp session
        
    Returns:
        Configured inventory connector instance
        
    Example:
        >>> config = {
        ...     "api_username": "your_username",
        ...     "api_token": "your_api_token",
        ...     "api_password": "your_password",
        ...     "sandbox": True
        ... }
        >>> connector = create_inventory_connector("cin7", config)
    """
    # Normalize platform name
    platform = _normalize_platform_name(platform)
    
    if platform not in SUPPORTED_PLATFORMS:
        raise UnsupportedPlatformError(f"Platform '{platform}' is not supported")
    
    platform_info = SUPPORTED_PLATFORMS[platform]
    
    if not platform_info["available"]:
        raise PlatformNotAvailableError(f"Platform '{platform}' is not currently available. Check dependencies.")
    
    factory_function = platform_info["factory_function"]
    
    try:
        return factory_function(**config, session=session)
    except Exception as e:
        raise ConfigurationError(f"Failed to create {platform} connector: {str(e)}")


def create_connector_from_config(
    config: Dict[str, Any],
    session=None
) -> BaseInventoryConnector:
    """
    Create inventory connector from unified configuration.
    
    Args:
        config: Configuration dict with 'platform' field and platform-specific settings
        session: Optional aiohttp session
        
    Returns:
        Configured inventory connector instance
    """
    if "platform" not in config:
        raise ConfigurationError("Configuration must include 'platform' field")
    
    platform = config.pop("platform")
    return create_inventory_connector(platform, config, session)


def get_platform_connector(platform: str) -> Type[BaseInventoryConnector]:
    """Get connector class for specified platform."""
    platform = _normalize_platform_name(platform)
    
    if platform not in SUPPORTED_PLATFORMS:
        raise UnsupportedPlatformError(f"Platform '{platform}' is not supported")
    
    platform_info = SUPPORTED_PLATFORMS[platform]
    
    if not platform_info["available"]:
        raise PlatformNotAvailableError(f"Platform '{platform}' is not currently available")
    
    return platform_info["connector_class"]


def get_connector_class(platform: str) -> Type[BaseInventoryConnector]:
    """Alias for get_platform_connector for backward compatibility."""
    return get_platform_connector(platform)


def list_supported_platforms() -> List[Dict[str, Any]]:
    """Get list of all supported inventory platforms."""
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
            "compliance": info["compliance"],
            "available": info["available"]
        }
        for platform_id, info in SUPPORTED_PLATFORMS.items()
    ]


def list_available_platforms() -> List[Dict[str, Any]]:
    """Get list of currently available inventory platforms."""
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
            "compliance": info["compliance"],
            "available": info["available"]
        }
        for platform_id, info in SUPPORTED_PLATFORMS.items()
        if info["available"]
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
        if info["compliance"].get("firs_einvoicing", False) and info["available"]
    ]


def get_manufacturing_platforms() -> List[str]:
    """Get list of platforms that support manufacturing features."""
    manufacturing_features = ["manufacturing", "work_orders", "bill_of_materials", "assembly_disassembly"]
    return [
        platform_id
        for platform_id, info in SUPPORTED_PLATFORMS.items()
        if any(info["features"].get(feature, False) for feature in manufacturing_features) and info["available"]
    ]


def get_multi_warehouse_platforms() -> List[str]:
    """Get list of platforms that support multi-warehouse operations."""
    return [
        platform_id
        for platform_id, info in SUPPORTED_PLATFORMS.items()
        if info["features"].get("multi_warehouse", False) and info["available"]
    ]


def get_ecommerce_integrated_platforms() -> List[str]:
    """Get list of platforms with e-commerce integration."""
    ecommerce_features = ["ecommerce_integration", "multi_channel", "b2b_wholesale"]
    return [
        platform_id
        for platform_id, info in SUPPORTED_PLATFORMS.items()
        if any(info["features"].get(feature, False) for feature in ecommerce_features) and info["available"]
    ]


# Integration statistics
INTEGRATION_STATS = {
    "total_platforms": len(SUPPORTED_PLATFORMS),
    "available_platforms": len([p for p in SUPPORTED_PLATFORMS.values() if p["available"]]),
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
        if p["features"].get("webhook_support", False) and p["available"]
    ]),
    "manufacturing_count": len(get_manufacturing_platforms()),
    "multi_warehouse_count": len(get_multi_warehouse_platforms()),
    "ecommerce_integrated_count": len(get_ecommerce_integrated_platforms())
}


# Inventory-specific utilities
def get_lot_tracking_platforms() -> List[str]:
    """Get list of platforms that support lot/batch tracking."""
    lot_features = ["lot_tracking", "batch_lot_tracking", "serial_tracking"]
    return [
        platform_id
        for platform_id, info in SUPPORTED_PLATFORMS.items()
        if any(info["features"].get(feature, False) for feature in lot_features) and info["available"]
    ]


def get_barcode_platforms() -> List[str]:
    """Get list of platforms that support barcode operations."""
    barcode_features = ["barcode_support", "barcode_scanning", "mobile_stocktaking"]
    return [
        platform_id
        for platform_id, info in SUPPORTED_PLATFORMS.items()
        if any(info["features"].get(feature, False) for feature in barcode_features) and info["available"]
    ]


def get_cloud_based_platforms() -> List[str]:
    """Get list of cloud-based inventory platforms."""
    return [
        platform_id
        for platform_id, info in SUPPORTED_PLATFORMS.items()
        if info["features"].get("cloud_based", True) and info["available"]  # Most modern platforms are cloud-based
    ]


# Integration examples and documentation
INTEGRATION_EXAMPLES = {
    "basic_setup": '''
# Basic inventory integration setup
from taxpoynt_platform.external_integrations.business_systems.inventory import create_inventory_connector

async def setup_inventory_integration():
    # Check available platforms
    from taxpoynt_platform.external_integrations.business_systems.inventory import list_available_platforms
    available = list_available_platforms()
    print(f"Available platforms: {[p['name'] for p in available]}")
    
    # Create Cin7 connector
    connector = create_inventory_connector("cin7", {
        "api_username": "your_username",
        "api_token": "your_api_token", 
        "api_password": "your_password",
        "sandbox": True
    })
    
    async with connector:
        # Test connection
        test_result = await connector.test_connection()
        if test_result["success"]:
            print("Successfully connected to inventory system")
        
        return connector
''',
    
    "stock_management": '''
# Stock level management
async def manage_stock_levels(connector):
    # Get current stock levels
    stock_levels = await connector.get_stock_levels()
    
    # Check for low stock
    low_stock = await connector.get_low_stock_report(threshold=10)
    
    # Adjust stock for a product
    adjustment = await connector.adjust_stock(
        product_id="PROD123",
        quantity=50,
        warehouse_id="WH001",
        reason="Stock replenishment",
        reference="ADJ001"
    )
    
    # Transfer stock between locations
    transfer = await connector.transfer_stock(
        product_id="PROD123",
        quantity=25,
        from_location="WH001",
        to_location="WH002",
        reference="TRF001"
    )
    
    return {
        "stock_levels": len(stock_levels),
        "low_stock_items": len(low_stock),
        "adjustment_id": adjustment.get("id"),
        "transfer_id": transfer.get("id")
    }
''',
    
    "purchase_order_management": '''
# Purchase order operations
async def manage_purchase_orders(connector):
    # Get recent purchase orders
    from datetime import datetime, timedelta
    since_date = datetime.utcnow() - timedelta(days=30)
    
    purchase_orders = await connector.get_purchase_orders(
        modified_since=since_date,
        status="open"
    )
    
    # Create new purchase order
    new_po = await connector.create_purchase_order({
        "supplier_id": "SUP001",
        "reference": "PO-2024-001",
        "line_items": [
            {
                "product_id": "PROD123",
                "quantity": 100,
                "unit_cost": 25.50
            }
        ],
        "delivery_date": "2024-08-01"
    })
    
    return {
        "existing_orders": len(purchase_orders),
        "new_order_id": new_po.get("id")
    }
''',
    
    "firs_compliance": '''
# FIRS e-invoicing compliance
async def generate_stock_invoices(connector):
    # Get stock movements for the month
    from datetime import datetime, timedelta
    
    month_start = datetime.utcnow().replace(day=1)
    month_end = datetime.utcnow()
    
    # Get inventory data for period
    period_data = await connector.get_inventory_for_period(
        start_date=month_start,
        end_date=month_end
    )
    
    # Generate invoices for significant stock movements
    invoices = []
    for movement in period_data["movements"]:
        if abs(movement.get("quantity", 0)) > 100:  # Significant movements
            try:
                invoice = await connector.generate_stock_movement_invoice(
                    movement_id=movement["id"],
                    invoice_type="stock_movement"
                )
                invoices.append(invoice)
            except NotImplementedError:
                # Some connectors may not implement this yet
                pass
    
    return {
        "period": f"{month_start.date()} to {month_end.date()}",
        "total_movements": len(period_data["movements"]),
        "invoices_generated": len(invoices)
    }
'''
}


# Platform-specific configuration templates
CONFIGURATION_TEMPLATES = {
    "cin7": {
        "required_fields": ["api_username", "api_token", "api_password"],
        "optional_fields": ["sandbox"],
        "example": {
            "api_username": "your_cin7_username",
            "api_token": "your_cin7_api_token",
            "api_password": "your_cin7_password",
            "sandbox": True
        }
    },
    "fishbowl": {
        "required_fields": ["server_host", "server_port", "username", "password"],
        "optional_fields": ["database_name", "timeout"],
        "example": {
            "server_host": "localhost",
            "server_port": 28192,
            "username": "your_fishbowl_user",
            "password": "your_fishbowl_password",
            "database_name": "your_database"
        }
    },
    "tradegecko": {
        "required_fields": ["client_id", "client_secret", "redirect_uri"],
        "optional_fields": ["sandbox"],
        "example": {
            "client_id": "your_tradegecko_client_id",
            "client_secret": "your_tradegecko_secret",
            "redirect_uri": "https://your-app.com/callback",
            "sandbox": True
        }
    },
    "unleashed": {
        "required_fields": ["api_id", "api_key"],
        "optional_fields": ["base_url"],
        "example": {
            "api_id": "your_unleashed_api_id",
            "api_key": "your_unleashed_api_key",
            "base_url": "https://api.unleashedsoftware.com"
        }
    }
}