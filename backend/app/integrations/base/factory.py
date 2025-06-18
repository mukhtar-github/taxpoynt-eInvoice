"""
Factory and utility functions for creating integration connectors.

This module provides utilities to create and configure integration
connectors based on connection configuration.
"""

import importlib
import logging
from typing import Dict, Any, Optional, Type

from app.integrations.base.connector import BaseConnector
from app.integrations.base.errors import IntegrationError

logger = logging.getLogger(__name__)


def create_connector(
    integration_type: str,
    platform_name: str,
    config: Dict[str, Any]
) -> BaseConnector:
    """
    Create an integration connector for the specified platform.
    
    Args:
        integration_type: Type of integration (crm, pos, erp)
        platform_name: Name of the platform (hubspot, square, etc.)
        config: Configuration for the connector
        
    Returns:
        Instantiated connector for the specified platform
        
    Raises:
        IntegrationError: If connector could not be created
    """
    try:
        # Derive the module path based on the integration type and platform
        module_path = f"app.integrations.{integration_type.lower()}.{platform_name.lower()}.connector"
        
        # Import the module
        module = importlib.import_module(module_path)
        
        # Look for a class that ends with "Connector"
        connector_class = None
        for attr_name in dir(module):
            if attr_name.endswith("Connector") and attr_name != "BaseConnector":
                connector_class = getattr(module, attr_name)
                break
                
        if not connector_class:
            raise IntegrationError(
                f"No connector class found in {module_path}",
                error_code="CONNECTOR_NOT_FOUND"
            )
            
        # Create and return the connector instance
        logger.info(f"Creating {integration_type}/{platform_name} connector")
        return connector_class(config)
        
    except ImportError as e:
        logger.error(f"Failed to import connector module: {str(e)}")
        raise IntegrationError(
            f"Integration for {integration_type}/{platform_name} is not supported",
            error_code="INTEGRATION_NOT_SUPPORTED",
            details={"error": str(e)}
        )
    except Exception as e:
        logger.error(f"Failed to create connector: {str(e)}", exc_info=True)
        raise IntegrationError(
            f"Failed to create connector for {integration_type}/{platform_name}: {str(e)}",
            error_code="CONNECTOR_CREATION_ERROR",
            details={"error": str(e)}
        )


def get_available_integrations(integration_type: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
    """
    Get available integrations and their capabilities.
    
    Args:
        integration_type: Optional filter for integration type
        
    Returns:
        Dict of available integrations with capabilities
    """
    # Define the available integrations and their capabilities
    available_integrations = {
        "crm": {
            "hubspot": {
                "name": "HubSpot",
                "description": "HubSpot CRM integration",
                "auth_methods": ["oauth2"],
                "features": ["deals", "contacts", "companies"],
                "status": "available",
            },
            "salesforce": {
                "name": "Salesforce",
                "description": "Salesforce CRM integration",
                "auth_methods": ["oauth2"],
                "features": ["opportunities", "accounts", "contacts"],
                "status": "planned",
            },
            "pipedrive": {
                "name": "Pipedrive",
                "description": "Pipedrive CRM integration",
                "auth_methods": ["api_key"],
                "features": ["deals", "persons", "organizations"],
                "status": "planned",
            }
        },
        "pos": {
            "square": {
                "name": "Square",
                "description": "Square POS integration",
                "auth_methods": ["oauth2"],
                "features": ["transactions", "customers", "items"],
                "status": "planned",
            },
            "toast": {
                "name": "Toast",
                "description": "Toast POS integration",
                "auth_methods": ["oauth2"],
                "features": ["orders", "customers", "menu-items"],
                "status": "planned",
            },
            "lightspeed": {
                "name": "Lightspeed",
                "description": "Lightspeed POS integration",
                "auth_methods": ["oauth2", "api_key"],
                "features": ["sales", "customers", "inventory"],
                "status": "planned",
            }
        },
        "erp": {
            "odoo": {
                "name": "Odoo",
                "description": "Odoo ERP integration",
                "auth_methods": ["basic", "api_key"],
                "features": ["invoices", "contacts", "products"],
                "status": "available",
            }
        }
    }
    
    # Filter by integration type if specified
    if integration_type:
        if integration_type in available_integrations:
            return {integration_type: available_integrations[integration_type]}
        return {}
    
    return available_integrations
