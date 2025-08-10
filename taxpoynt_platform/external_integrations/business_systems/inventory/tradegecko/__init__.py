"""
TradeGecko Inventory Integration Package
Complete integration with TradeGecko inventory management system.
"""
from .connector import TradeGeckoInventoryConnector
from .auth import TradeGeckoAuthManager
from .rest_client import TradeGeckoRestClient
from .data_extractor import TradeGeckoDataExtractor
from .stock_transformer import TradeGeckoStockTransformer
from .exceptions import (
    TradeGeckoException,
    TradeGeckoAuthenticationError,
    TradeGeckoAuthorizationError,
    TradeGeckoAPIError,
    TradeGeckoRateLimitError,
    TradeGeckoConnectionError,
    TradeGeckoConfigurationError,
    TradeGeckoDataError,
    TradeGeckoProductNotFoundError,
    TradeGeckoVariantNotFoundError,
    TradeGeckoLocationNotFoundError,
    TradeGeckoOrderNotFoundError,
    TradeGeckoPurchaseOrderNotFoundError,
    TradeGeckoSupplierNotFoundError,
    TradeGeckoCustomerNotFoundError,
    TradeGeckoValidationError,
    TradeGeckoTransformationError,
    TradeGeckoSyncError,
    TradeGeckoQuotaExceededError,
    TradeGeckoMaintenanceError,
    TradeGeckoDeprecationError,
    TradeGeckoStockAdjustmentError,
    TradeGeckoFulfillmentError,
    TradeGeckoChannelError
)

__all__ = [
    # Main connector
    "TradeGeckoInventoryConnector",
    
    # Core components
    "TradeGeckoAuthManager",
    "TradeGeckoRestClient",
    "TradeGeckoDataExtractor", 
    "TradeGeckoStockTransformer",
    
    # Exceptions
    "TradeGeckoException",
    "TradeGeckoAuthenticationError",
    "TradeGeckoAuthorizationError",
    "TradeGeckoAPIError",
    "TradeGeckoRateLimitError",
    "TradeGeckoConnectionError",
    "TradeGeckoConfigurationError",
    "TradeGeckoDataError",
    "TradeGeckoProductNotFoundError",
    "TradeGeckoVariantNotFoundError",
    "TradeGeckoLocationNotFoundError",
    "TradeGeckoOrderNotFoundError",
    "TradeGeckoPurchaseOrderNotFoundError",
    "TradeGeckoSupplierNotFoundError",
    "TradeGeckoCustomerNotFoundError",
    "TradeGeckoValidationError",
    "TradeGeckoTransformationError",
    "TradeGeckoSyncError",
    "TradeGeckoQuotaExceededError",
    "TradeGeckoMaintenanceError",
    "TradeGeckoDeprecationError",
    "TradeGeckoStockAdjustmentError",
    "TradeGeckoFulfillmentError",
    "TradeGeckoChannelError"
]

# Platform metadata
PLATFORM_INFO = {
    "name": "tradegecko",
    "display_name": "TradeGecko Inventory Management",
    "description": "Cloud-based inventory and order management platform with multi-channel sales support and advanced product variants",
    "version": "v1",
    "category": "inventory",
    "website": "https://www.tradegecko.com",
    "documentation": "https://developer.tradegecko.com/",
    "supported_regions": ["Global"],
    "capabilities": [
        "product_management",
        "variant_tracking",
        "stock_tracking",
        "multi_location",
        "purchase_orders",
        "sales_orders",
        "supplier_management",
        "customer_management",
        "multi_channel",
        "fulfillment",
        "stock_adjustments",
        "stock_movements",
        "reporting",
        "real_time_sync",
        "webhooks"
    ],
    "authentication_methods": ["oauth2"],
    "data_formats": ["json"],
    "rate_limits": {
        "requests_per_minute": 300,
        "burst_limit": 20
    },
    "environments": {
        "sandbox": "https://api.tradegecko.com",
        "production": "https://api.tradegecko.com"
    }
}


def create_tradegecko_connector(config: dict) -> TradeGeckoInventoryConnector:
    """
    Create a TradeGecko inventory connector instance.
    
    Args:
        config: Configuration dictionary containing:
            - access_token: TradeGecko API access token
            - sandbox: Whether to use sandbox (default: True)
            - currency_code: Default currency (default: "NGN")
    
    Returns:
        Configured TradeGeckoInventoryConnector instance
    
    Example:
        config = {
            "access_token": "your_access_token",
            "sandbox": True,
            "currency_code": "NGN"
        }
        connector = create_tradegecko_connector(config)
    """
    required_fields = ["access_token"]
    missing_fields = [field for field in required_fields if field not in config]
    
    if missing_fields:
        raise TradeGeckoConfigurationError(
            f"Missing required configuration fields: {', '.join(missing_fields)}"
        )
    
    return TradeGeckoInventoryConnector(
        access_token=config["access_token"],
        sandbox=config.get("sandbox", True),
        currency_code=config.get("currency_code", "NGN")
    )


# Convenience functions
async def test_tradegecko_connection(config: dict) -> dict:
    """
    Test connection to TradeGecko with given configuration.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Connection test results
    """
    connector = create_tradegecko_connector(config)
    
    try:
        await connector.connect()
        result = await connector.test_connection()
        await connector.disconnect()
        return result
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "platform": "tradegecko"
        }


def get_tradegecko_config_template() -> dict:
    """
    Get configuration template for TradeGecko integration.
    
    Returns:
        Configuration template with required and optional fields
    """
    return {
        "access_token": {
            "required": True,
            "type": "string",
            "description": "Your TradeGecko API access token",
            "sensitive": True
        },
        "sandbox": {
            "required": False,
            "type": "boolean",
            "default": True,
            "description": "Whether to use sandbox environment"
        },
        "currency_code": {
            "required": False,
            "type": "string",
            "default": "NGN",
            "description": "Default currency code for transactions"
        }
    }


def validate_tradegecko_config(config: dict) -> dict:
    """
    Validate TradeGecko configuration.
    
    Args:
        config: Configuration to validate
        
    Returns:
        Validation results
    """
    template = get_tradegecko_config_template()
    errors = []
    warnings = []
    
    # Check required fields
    for field, specs in template.items():
        if specs["required"] and field not in config:
            errors.append(f"Missing required field: {field}")
        elif field in config:
            # Validate field types
            expected_type = specs["type"]
            actual_value = config[field]
            
            if expected_type == "string" and not isinstance(actual_value, str):
                errors.append(f"Field '{field}' must be a string")
            elif expected_type == "boolean" and not isinstance(actual_value, bool):
                errors.append(f"Field '{field}' must be a boolean")
    
    # Validate access token format (basic check)
    if "access_token" in config:
        token = config["access_token"]
        if len(token) < 20:
            warnings.append("Access token appears to be too short")
    
    # Check for unknown fields
    known_fields = set(template.keys())
    provided_fields = set(config.keys())
    unknown_fields = provided_fields - known_fields
    
    if unknown_fields:
        warnings.append(f"Unknown configuration fields: {', '.join(unknown_fields)}")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }