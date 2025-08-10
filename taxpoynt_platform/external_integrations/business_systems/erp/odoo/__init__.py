"""
Odoo ERP Connector Package
System Integrator (SI) role functionality for Odoo ERP integration.

This package provides modular Odoo ERP connectivity including:
- Connection management and authentication
- Data extraction (invoices, customers, products, partners)
- FIRS format transformation
- Connection testing and validation
"""

from .connector import OdooConnector
from .exceptions import (
    OdooConnectorError,
    OdooConnectionError,
    OdooAuthenticationError,
    OdooDataError
)

__all__ = [
    "OdooConnector",
    "OdooConnectorError",
    "OdooConnectionError", 
    "OdooAuthenticationError",
    "OdooDataError"
]