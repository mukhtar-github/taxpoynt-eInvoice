"""
NetSuite ERP Connector - Custom Exceptions
Exception classes for NetSuite ERP integration and error handling.
"""

from ....connector_framework import ERPConnectionError, ERPAuthenticationError, ERPDataError


class NetSuiteConnectionError(ERPConnectionError):
    """Raised when NetSuite connection fails."""
    pass


class NetSuiteAuthenticationError(ERPAuthenticationError):
    """Raised when NetSuite authentication fails."""
    pass


class NetSuiteAPIError(Exception):
    """Raised when NetSuite API requests fail."""
    pass


class NetSuiteDataError(ERPDataError):
    """Raised when NetSuite data operations fail."""
    pass


class NetSuiteConfigurationError(Exception):
    """Raised when NetSuite configuration is invalid."""
    pass


class NetSuiteRateLimitError(Exception):
    """Raised when NetSuite API rate limits are exceeded."""
    pass


class NetSuiteValidationError(Exception):
    """Raised when NetSuite data validation fails."""
    pass