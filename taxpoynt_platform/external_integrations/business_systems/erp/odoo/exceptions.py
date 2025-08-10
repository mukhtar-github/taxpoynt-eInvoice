"""
Odoo Connector Exceptions
Custom exceptions for Odoo ERP connector operations.
"""


class OdooConnectorError(Exception):
    """Base exception for OdooConnector errors."""
    pass


class OdooConnectionError(OdooConnectorError):
    """Exception raised for connection errors."""
    pass


class OdooAuthenticationError(OdooConnectorError):
    """Exception raised for authentication errors."""
    pass


class OdooDataError(OdooConnectorError):
    """Exception raised for data retrieval errors."""
    pass