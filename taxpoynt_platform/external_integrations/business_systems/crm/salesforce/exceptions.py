"""
Salesforce CRM Connector - Custom Exceptions
Exception classes for Salesforce CRM integration and error handling.
"""

from ....connector_framework import CRMConnectionError, CRMAuthenticationError, CRMDataError


class SalesforceConnectionError(CRMConnectionError):
    """Raised when Salesforce connection fails."""
    pass


class SalesforceAuthenticationError(CRMAuthenticationError):
    """Raised when Salesforce authentication fails."""
    pass


class SalesforceAPIError(Exception):
    """Raised when Salesforce API requests fail."""
    pass


class SalesforceDataError(CRMDataError):
    """Raised when Salesforce data operations fail."""
    pass


class SalesforceConfigurationError(Exception):
    """Raised when Salesforce configuration is invalid."""
    pass


class SalesforceRateLimitError(Exception):
    """Raised when Salesforce API rate limits are exceeded."""
    pass


class SalesforceValidationError(Exception):
    """Raised when Salesforce data validation fails."""
    pass


class SalesforceSOQLError(Exception):
    """Raised when SOQL query execution fails."""
    pass