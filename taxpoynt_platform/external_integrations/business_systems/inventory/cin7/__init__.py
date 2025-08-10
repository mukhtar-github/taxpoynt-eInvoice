"""
Cin7 Inventory Integration Package
Complete integration with Cin7 inventory management system.
"""
from .connector import Cin7InventoryConnector
from .auth import Cin7AuthManager
from .rest_client import Cin7RestClient
from .data_extractor import Cin7DataExtractor
from .stock_transformer import Cin7StockTransformer
from .exceptions import (
    Cin7Exception,
    Cin7AuthenticationError,
    Cin7AuthorizationError,
    Cin7APIError,
    Cin7RateLimitError,
    Cin7ConnectionError,
    Cin7ConfigurationError,
    Cin7DataError,
    Cin7ProductNotFoundError,
    Cin7StockLocationNotFoundError,
    Cin7PurchaseOrderNotFoundError,
    Cin7SalesOrderNotFoundError,
    Cin7SupplierNotFoundError,
    Cin7ValidationError,
    Cin7TransformationError,
    Cin7SyncError,
    Cin7QuotaExceededError,
    Cin7MaintenanceError,
    Cin7DeprecationError,
    Cin7StockAdjustmentError,
    Cin7WarehouseError
)

__all__ = [
    # Main connector
    "Cin7InventoryConnector",
    
    # Core components
    "Cin7AuthManager",
    "Cin7RestClient", 
    "Cin7DataExtractor",
    "Cin7StockTransformer",
    
    # Exceptions
    "Cin7Exception",
    "Cin7AuthenticationError",
    "Cin7AuthorizationError",
    "Cin7APIError",
    "Cin7RateLimitError",
    "Cin7ConnectionError",
    "Cin7ConfigurationError",
    "Cin7DataError",
    "Cin7ProductNotFoundError",
    "Cin7StockLocationNotFoundError",
    "Cin7PurchaseOrderNotFoundError",
    "Cin7SalesOrderNotFoundError",
    "Cin7SupplierNotFoundError",
    "Cin7ValidationError",
    "Cin7TransformationError",
    "Cin7SyncError",
    "Cin7QuotaExceededError",
    "Cin7MaintenanceError",
    "Cin7DeprecationError",
    "Cin7StockAdjustmentError",
    "Cin7WarehouseError"
]

# Platform metadata
PLATFORM_INFO = {
    "name": "cin7",
    "display_name": "Cin7 Inventory Management",
    "description": "Cloud-based inventory management system with real-time stock tracking and multi-location support",
    "version": "1.3",
    "category": "inventory",
    "website": "https://www.cin7.com",
    "documentation": "https://support.cin7.com/hc/en-us/categories/115000216188-API",
    "supported_regions": ["Global"],
    "capabilities": [
        "product_management",
        "stock_tracking", 
        "multi_location",
        "purchase_orders",
        "sales_orders",
        "supplier_management",
        "stock_adjustments",
        "stock_transfers",
        "reporting",
        "real_time_sync",
        "api_webhooks"
    ],
    "authentication_methods": ["api_token"],
    "data_formats": ["json"],
    "rate_limits": {
        "requests_per_hour": 1000,
        "burst_limit": 10
    },
    "environments": {
        "sandbox": "https://sandbox.cin7.com",
        "production": "https://api.cin7.com"
    }
}


def create_cin7_connector(config: dict) -> Cin7InventoryConnector:
    """
    Create a Cin7 inventory connector instance.
    
    Args:
        config: Configuration dictionary containing:
            - api_username: Cin7 API username
            - api_token: Cin7 API token  
            - api_password: Cin7 API password
            - sandbox: Whether to use sandbox (default: True)
            - currency_code: Default currency (default: "NGN")
    
    Returns:
        Configured Cin7InventoryConnector instance
    
    Example:
        config = {
            "api_username": "your_username",
            "api_token": "your_token",
            "api_password": "your_password",
            "sandbox": True,
            "currency_code": "NGN"
        }
        connector = create_cin7_connector(config)
    """
    required_fields = ["api_username", "api_token", "api_password"]
    missing_fields = [field for field in required_fields if field not in config]
    
    if missing_fields:
        raise Cin7ConfigurationError(
            f"Missing required configuration fields: {', '.join(missing_fields)}"
        )
    
    return Cin7InventoryConnector(
        api_username=config["api_username"],
        api_token=config["api_token"],
        api_password=config["api_password"],
        sandbox=config.get("sandbox", True),
        currency_code=config.get("currency_code", "NGN")
    )


# Convenience functions
async def test_cin7_connection(config: dict) -> dict:
    """
    Test connection to Cin7 with given configuration.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Connection test results
    """
    connector = create_cin7_connector(config)
    
    try:
        await connector.connect()
        result = await connector.test_connection()
        await connector.disconnect()
        return result
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "platform": "cin7"
        }


def get_cin7_config_template() -> dict:
    """
    Get configuration template for Cin7 integration.
    
    Returns:
        Configuration template with required and optional fields
    """
    return {
        "api_username": {
            "required": True,
            "type": "string",
            "description": "Your Cin7 API username"
        },
        "api_token": {
            "required": True,
            "type": "string", 
            "description": "Your Cin7 API token",
            "sensitive": True
        },
        "api_password": {
            "required": True,
            "type": "string",
            "description": "Your Cin7 API password",
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


def validate_cin7_config(config: dict) -> dict:
    """
    Validate Cin7 configuration.
    
    Args:
        config: Configuration to validate
        
    Returns:
        Validation results
    """
    template = get_cin7_config_template()
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