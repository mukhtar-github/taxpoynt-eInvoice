"""
Microsoft Dynamics Connector Exceptions
Custom exceptions for Microsoft Dynamics ERP connector operations.
"""


class DynamicsAPIError(Exception):
    """Exception raised for Microsoft Dynamics REST API-related errors."""
    pass


class DynamicsAuthenticationError(Exception):
    """Exception raised for Microsoft Dynamics authentication errors."""
    pass


class DynamicsDataError(Exception):
    """Exception raised for Microsoft Dynamics data extraction errors."""
    pass


class DynamicsConnectionError(Exception):
    """Exception raised for Microsoft Dynamics connection errors."""
    pass