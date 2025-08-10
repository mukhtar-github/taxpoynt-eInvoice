"""
Unleashed Inventory Integration Package
Complete integration with Unleashed inventory management system.
"""
from .connector import UnleashedInventoryConnector
from .auth import UnleashedAuthManager
from .rest_client import UnleashedRestClient
from .data_extractor import UnleashedDataExtractor
from .stock_transformer import UnleashedStockTransformer
from .exceptions import (
    UnleashedException,
    UnleashedAuthenticationError,
    UnleashedAuthorizationError,
    UnleashedAPIError,
    UnleashedRateLimitError,
    UnleashedConnectionError,
    UnleashedConfigurationError,
    UnleashedDataError,
    UnleashedProductNotFoundError,
    UnleashedWarehouseNotFoundError,
    UnleashedStockOnHandNotFoundError,
    UnleashedPurchaseOrderNotFoundError,
    UnleashedSalesOrderNotFoundError,
    UnleashedSupplierNotFoundError,
    UnleashedCustomerNotFoundError,
    UnleashedValidationError,
    UnleashedTransformationError,
    UnleashedSyncError,
    UnleashedQuotaExceededError,
    UnleashedMaintenanceError,
    UnleashedDeprecationError,
    UnleashedStockAdjustmentError,
    UnleashedTransactionError,
    UnleashedReportError
)

__all__ = [
    # Main connector
    "UnleashedInventoryConnector",
    
    # Core components
    "UnleashedAuthManager",
    "UnleashedRestClient",
    "UnleashedDataExtractor",
    "UnleashedStockTransformer",
    
    # Exceptions
    "UnleashedException",
    "UnleashedAuthenticationError",
    "UnleashedAuthorizationError",
    "UnleashedAPIError",
    "UnleashedRateLimitError",
    "UnleashedConnectionError",
    "UnleashedConfigurationError",
    "UnleashedDataError",
    "UnleashedProductNotFoundError",
    "UnleashedWarehouseNotFoundError",
    "UnleashedStockOnHandNotFoundError",
    "UnleashedPurchaseOrderNotFoundError",
    "UnleashedSalesOrderNotFoundError",
    "UnleashedSupplierNotFoundError",
    "UnleashedCustomerNotFoundError",
    "UnleashedValidationError",
    "UnleashedTransformationError",
    "UnleashedSyncError",
    "UnleashedQuotaExceededError",
    "UnleashedMaintenanceError",
    "UnleashedDeprecationError",
    "UnleashedStockAdjustmentError",
    "UnleashedTransactionError",
    "UnleashedReportError"
]

# Platform metadata
PLATFORM_INFO = {
    "name": "unleashed",
    "display_name": "Unleashed Inventory Management",
    "description": "Cloud-based inventory and business management software with comprehensive product tracking and multi-warehouse support",
    "version": "API v1",
    "category": "inventory",
    "website": "https://www.unleashedsoftware.com",
    "documentation": "https://apidocs.unleashedsoftware.com/",
    "supported_regions": ["Global"],
    "capabilities": [
        "product_management",
        "stock_tracking",
        "multi_warehouse",
        "purchase_orders",
        "sales_orders",
        "supplier_management",
        "customer_management",
        "stock_adjustments",
        "stock_movements",
        "assembly_management",
        "manufacturing",
        "reporting",
        "real_time_sync",
        "barcode_support",
        "serial_tracking",
        "batch_tracking"
    ],
    "authentication_methods": ["hmac_signature"],
    "data_formats": ["json"],
    "rate_limits": {
        "requests_per_hour": 1000,
        "burst_limit": 10
    },
    "environments": {
        "production": "https://api.unleashedsoftware.com"
    }
}


def create_unleashed_connector(config: dict) -> UnleashedInventoryConnector:
    """
    Create an Unleashed inventory connector instance.
    
    Args:
        config: Configuration dictionary containing:
            - api_id: Unleashed API ID
            - api_key: Unleashed API key
            - currency_code: Default currency (default: "NGN")
    
    Returns:
        Configured UnleashedInventoryConnector instance
    
    Example:
        config = {
            "api_id": "your_api_id",
            "api_key": "your_api_key",
            "currency_code": "NGN"
        }
        connector = create_unleashed_connector(config)
    """
    required_fields = ["api_id", "api_key"]
    missing_fields = [field for field in required_fields if field not in config]
    
    if missing_fields:
        raise UnleashedConfigurationError(
            f"Missing required configuration fields: {', '.join(missing_fields)}"
        )
    
    return UnleashedInventoryConnector(
        api_id=config["api_id"],
        api_key=config["api_key"],
        currency_code=config.get("currency_code", "NGN")
    )


# Convenience functions
async def test_unleashed_connection(config: dict) -> dict:
    """
    Test connection to Unleashed with given configuration.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Connection test results
    """
    connector = create_unleashed_connector(config)
    
    try:
        await connector.connect()
        result = await connector.test_connection()
        await connector.disconnect()
        return result
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "platform": "unleashed"
        }


def get_unleashed_config_template() -> dict:
    """
    Get configuration template for Unleashed integration.
    
    Returns:
        Configuration template with required and optional fields
    """
    return {
        "api_id": {
            "required": True,
            "type": "string",
            "description": "Your Unleashed API ID",
            "sensitive": True
        },
        "api_key": {
            "required": True,
            "type": "string",
            "description": "Your Unleashed API key",
            "sensitive": True
        },
        "currency_code": {
            "required": False,
            "type": "string",
            "default": "NGN",
            "description": "Default currency code for transactions"
        }
    }


def validate_unleashed_config(config: dict) -> dict:
    """
    Validate Unleashed configuration.
    
    Args:
        config: Configuration to validate
        
    Returns:
        Validation results
    """
    template = get_unleashed_config_template()
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
    
    # Validate API credentials format (basic checks)
    if "api_id" in config:
        api_id = config["api_id"]
        if len(api_id) < 10:
            warnings.append("API ID appears to be too short")
    
    if "api_key" in config:
        api_key = config["api_key"]
        if len(api_key) < 20:
            warnings.append("API key appears to be too short")
    
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