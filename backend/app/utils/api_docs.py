"""
Utilities for standardizing API documentation across the TaxPoynt eInvoice application.

This module provides helper functions and constants to maintain consistent
API documentation for all endpoints, especially ERP integrations.
"""

from typing import Dict, List, Optional, Any, Union
from enum import Enum


class APIResponseStatus(str, Enum):
    """Standard response status values for API documentation."""
    SUCCESS = "success"
    ERROR = "error"


# Standard response models for documentation
STANDARD_RESPONSES = {
    200: {
        "description": "Successful response",
        "content": {
            "application/json": {
                "example": {
                    "success": True,
                    "message": "Operation completed successfully"
                }
            }
        }
    },
    400: {
        "description": "Bad request",
        "content": {
            "application/json": {
                "example": {
                    "success": False,
                    "error": "Invalid request parameters",
                    "details": "Additional error information"
                }
            }
        }
    },
    401: {
        "description": "Unauthorized",
        "content": {
            "application/json": {
                "example": {
                    "success": False,
                    "error": "Authentication required"
                }
            }
        }
    },
    403: {
        "description": "Forbidden",
        "content": {
            "application/json": {
                "example": {
                    "success": False,
                    "error": "Insufficient permissions to perform this action"
                }
            }
        }
    },
    404: {
        "description": "Not found",
        "content": {
            "application/json": {
                "example": {
                    "success": False,
                    "error": "Resource not found"
                }
            }
        }
    },
    500: {
        "description": "Internal server error",
        "content": {
            "application/json": {
                "example": {
                    "success": False,
                    "error": "An unexpected error occurred"
                }
            }
        }
    }
}


# Standard response descriptions for ERP integrations
ERP_INTEGRATION_RESPONSES = {
    **STANDARD_RESPONSES,
    409: {
        "description": "Conflict",
        "content": {
            "application/json": {
                "example": {
                    "success": False,
                    "error": "Integration already exists for this connection"
                }
            }
        }
    },
    503: {
        "description": "Service unavailable",
        "content": {
            "application/json": {
                "example": {
                    "success": False,
                    "error": "ERP system is currently unavailable"
                }
            }
        }
    }
}


def get_integration_example(integration_type: str) -> Dict[str, Any]:
    """
    Get example integration data for documentation based on integration type.
    
    Args:
        integration_type: The type of ERP integration (odoo, sap, etc.)
        
    Returns:
        Dictionary with example data
    """
    common_fields = {
        "id": "int-123456",
        "name": f"My {integration_type.title()} Integration",
        "status": "configured",
        "created_at": "2025-05-28T12:00:00Z",
        "last_sync": "2025-05-28T12:30:00Z",
    }
    
    if integration_type.lower() == "odoo":
        return {
            **common_fields,
            "integration_type": "odoo",
            "config": {
                "url": "https://example.odoo.com",
                "database": "example_db",
                "auth_method": "password",
            }
        }
    elif integration_type.lower() == "sap":
        return {
            **common_fields,
            "integration_type": "sap",
            "config": {
                "base_url": "https://example.sap.com/odata",
                "company_id": "1000",
                "auth_type": "basic",
            }
        }
    else:
        return {
            **common_fields,
            "integration_type": integration_type,
            "config": {
                "connection_details": "Configuration specific to this integration type"
            }
        }


def api_example_response(
    data: Optional[Dict[str, Any]] = None, 
    success: bool = True,
    message: Optional[str] = None,
    error: Optional[str] = None,
    status: str = APIResponseStatus.SUCCESS
) -> Dict[str, Any]:
    """
    Create a standardized example API response for documentation.
    
    Args:
        data: The example data to include in the response
        success: Whether the example represents a successful operation
        message: Optional success message
        error: Optional error message (for error examples)
        status: Response status (success/error)
        
    Returns:
        Standardized API response example
    """
    response = {
        "success": success,
        "status": status
    }
    
    if data:
        response["data"] = data
    
    if message and success:
        response["message"] = message
    
    if error and not success:
        response["error"] = error
    
    return response
