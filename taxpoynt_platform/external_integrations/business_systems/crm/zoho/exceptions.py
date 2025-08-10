"""
Zoho CRM Connector - Custom Exceptions
Exception classes for Zoho CRM integration and error handling.
"""

from ....connector_framework import CRMConnectionError, CRMAuthenticationError, CRMDataError


class ZohoCRMConnectionError(CRMConnectionError):
    """Raised when Zoho CRM connection fails."""
    pass


class ZohoCRMAuthenticationError(CRMAuthenticationError):
    """Raised when Zoho CRM authentication fails."""
    pass


class ZohoCRMAPIError(CRMDataError):
    """Raised when Zoho CRM API request fails."""
    pass


class ZohoCRMDataError(CRMDataError):
    """Raised when Zoho CRM data processing fails."""
    pass


class ZohoCRMConfigurationError(Exception):
    """Raised when Zoho CRM configuration is invalid."""
    pass


class ZohoCRMQuotaError(CRMDataError):
    """Raised when Zoho CRM API quota is exceeded."""
    pass


class ZohoCRMPermissionError(CRMAuthenticationError):
    """Raised when Zoho CRM permission is denied."""
    pass


class ZohoCRMValidationError(CRMDataError):
    """Raised when Zoho CRM data validation fails."""
    pass


class ZohoCRMBulkError(CRMDataError):
    """Raised when Zoho CRM bulk operation fails."""
    pass


class ZohoCRMWebhookError(CRMDataError):
    """Raised when Zoho CRM webhook operation fails."""
    pass


class ZohoCRMFileError(CRMDataError):
    """Raised when Zoho CRM file operation fails."""
    pass