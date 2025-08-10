"""
Fishbowl Inventory Integration Package
Complete integration with Fishbowl inventory management system.
"""
from .connector import FishbowlInventoryConnector
from .auth import FishbowlAuthManager
from .rest_client import FishbowlXMLClient
from .data_extractor import FishbowlDataExtractor
from .stock_transformer import FishbowlStockTransformer
from .exceptions import (
    FishbowlException,
    FishbowlAuthenticationError,
    FishbowlAuthorizationError,
    FishbowlAPIError,
    FishbowlConnectionError,
    FishbowlConfigurationError,
    FishbowlDataError,
    FishbowlProductNotFoundError,
    FishbowlWarehouseNotFoundError,
    FishbowlInventoryNotFoundError,
    FishbowlWorkOrderNotFoundError,
    FishbowlPurchaseOrderNotFoundError,
    FishbowlSalesOrderNotFoundError,
    FishbowlVendorNotFoundError,
    FishbowlCustomerNotFoundError,
    FishbowlValidationError,
    FishbowlTransformationError,
    FishbowlSyncError,
    FishbowlDatabaseError,
    FishbowlXMLError,
    FishbowlSessionError,
    FishbowlInventoryAdjustmentError,
    FishbowlManufacturingError
)

__all__ = [
    # Main connector
    "FishbowlInventoryConnector",
    
    # Core components
    "FishbowlAuthManager",
    "FishbowlXMLClient",
    "FishbowlDataExtractor",
    "FishbowlStockTransformer",
    
    # Exceptions
    "FishbowlException",
    "FishbowlAuthenticationError",
    "FishbowlAuthorizationError",
    "FishbowlAPIError",
    "FishbowlConnectionError",
    "FishbowlConfigurationError",
    "FishbowlDataError",
    "FishbowlProductNotFoundError",
    "FishbowlWarehouseNotFoundError",
    "FishbowlInventoryNotFoundError",
    "FishbowlWorkOrderNotFoundError",
    "FishbowlPurchaseOrderNotFoundError",
    "FishbowlSalesOrderNotFoundError",
    "FishbowlVendorNotFoundError",
    "FishbowlCustomerNotFoundError",
    "FishbowlValidationError",
    "FishbowlTransformationError",
    "FishbowlSyncError",
    "FishbowlDatabaseError",
    "FishbowlXMLError",
    "FishbowlSessionError",
    "FishbowlInventoryAdjustmentError",
    "FishbowlManufacturingError"
]

# Platform metadata
PLATFORM_INFO = {
    "name": "fishbowl",
    "display_name": "Fishbowl Inventory Management",
    "description": "Manufacturing and warehouse management software with comprehensive inventory control and real-time reporting",
    "version": "2023.9",
    "category": "inventory",
    "website": "https://www.fishbowlinventory.com",
    "documentation": "https://www.fishbowlinventory.com/api-developer-resources/",
    "supported_regions": ["Global"],
    "capabilities": [
        "part_management",
        "inventory_tracking",
        "multi_location",
        "purchase_orders",
        "sales_orders",
        "work_orders",
        "manufacturing",
        "vendor_management",
        "customer_management",
        "reporting",
        "real_time_sync",
        "barcode_scanning",
        "cycle_counting",
        "lot_tracking",
        "serial_tracking"
    ],
    "authentication_methods": ["username_password"],
    "data_formats": ["xml"],
    "communication_protocol": "tcp",
    "default_port": 28192,
    "environments": {
        "production": "TCP connection to Fishbowl server"
    }
}


def create_fishbowl_connector(config: dict) -> FishbowlInventoryConnector:
    """
    Create a Fishbowl inventory connector instance.
    
    Args:
        config: Configuration dictionary containing:
            - server_host: Fishbowl server hostname/IP
            - server_port: Fishbowl server port (default: 28192)
            - username: Fishbowl username
            - password: Fishbowl password
            - app_name: Application name (default: "TaxPoynt")
            - app_description: Application description
            - currency_code: Default currency (default: "NGN")
    
    Returns:
        Configured FishbowlInventoryConnector instance
    
    Example:
        config = {
            "server_host": "192.168.1.100",
            "server_port": 28192,
            "username": "your_username",
            "password": "your_password",
            "currency_code": "NGN"
        }
        connector = create_fishbowl_connector(config)
    """
    required_fields = ["server_host", "server_port", "username", "password"]
    missing_fields = [field for field in required_fields if field not in config]
    
    if missing_fields:
        raise FishbowlConfigurationError(
            f"Missing required configuration fields: {', '.join(missing_fields)}"
        )
    
    return FishbowlInventoryConnector(
        server_host=config["server_host"],
        server_port=config["server_port"],
        username=config["username"],
        password=config["password"],
        app_name=config.get("app_name", "TaxPoynt"),
        app_description=config.get("app_description", "TaxPoynt E-Invoice Integration"),
        currency_code=config.get("currency_code", "NGN")
    )


# Convenience functions
async def test_fishbowl_connection(config: dict) -> dict:
    """
    Test connection to Fishbowl with given configuration.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Connection test results
    """
    connector = create_fishbowl_connector(config)
    
    try:
        await connector.connect()
        result = await connector.test_connection()
        await connector.disconnect()
        return result
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "platform": "fishbowl"
        }


def get_fishbowl_config_template() -> dict:
    """
    Get configuration template for Fishbowl integration.
    
    Returns:
        Configuration template with required and optional fields
    """
    return {
        "server_host": {
            "required": True,
            "type": "string",
            "description": "Fishbowl server hostname or IP address"
        },
        "server_port": {
            "required": True,
            "type": "integer",
            "default": 28192,
            "description": "Fishbowl server port (typically 28192)"
        },
        "username": {
            "required": True,
            "type": "string",
            "description": "Your Fishbowl username"
        },
        "password": {
            "required": True,
            "type": "string",
            "description": "Your Fishbowl password",
            "sensitive": True
        },
        "app_name": {
            "required": False,
            "type": "string",
            "default": "TaxPoynt",
            "description": "Application name for identification"
        },
        "app_description": {
            "required": False,
            "type": "string",
            "default": "TaxPoynt E-Invoice Integration",
            "description": "Application description"
        },
        "currency_code": {
            "required": False,
            "type": "string",
            "default": "NGN",
            "description": "Default currency code for transactions"
        }
    }


def validate_fishbowl_config(config: dict) -> dict:
    """
    Validate Fishbowl configuration.
    
    Args:
        config: Configuration to validate
        
    Returns:
        Validation results
    """
    template = get_fishbowl_config_template()
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
            elif expected_type == "integer" and not isinstance(actual_value, int):
                errors.append(f"Field '{field}' must be an integer")
    
    # Validate server port range
    if "server_port" in config:
        port = config["server_port"]
        if not (1 <= port <= 65535):
            errors.append("server_port must be between 1 and 65535")
    
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