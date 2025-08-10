"""
Oracle Connector Exceptions
Custom exceptions for Oracle ERP Cloud connector operations.
"""


class OracleAPIError(Exception):
    """Exception raised for Oracle REST API-related errors."""
    pass


class OracleAuthenticationError(Exception):
    """Exception raised for Oracle authentication errors."""
    pass


class OracleDataError(Exception):
    """Exception raised for Oracle data extraction errors."""
    pass


class OracleConnectionError(Exception):
    """Exception raised for Oracle connection errors."""
    pass