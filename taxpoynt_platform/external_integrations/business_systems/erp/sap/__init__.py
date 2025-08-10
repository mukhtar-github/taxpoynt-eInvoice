"""
SAP ERP Connector Package
System Integrator (SI) role functionality for SAP ERP integration.

This package provides modular SAP ERP connectivity including:
- OData API connection and authentication (OAuth2, Basic)
- Data extraction from SAP billing and journal services
- FIRS format transformation
- Connection testing and validation
"""

from .connector import SAPConnector
from .exceptions import SAPODataError

__all__ = [
    "SAPConnector",
    "SAPODataError"
]