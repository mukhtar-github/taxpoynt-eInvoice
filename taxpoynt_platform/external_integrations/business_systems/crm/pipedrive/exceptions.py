"""
Pipedrive CRM Connector - Custom Exceptions
Exception classes for Pipedrive CRM integration and error handling.
"""

from ....connector_framework import CRMConnectionError, CRMAuthenticationError, CRMDataError


class PipedriveConnectionError(CRMConnectionError):
    """Raised when Pipedrive connection fails."""
    pass


class PipedriveAuthenticationError(CRMAuthenticationError):
    """Raised when Pipedrive authentication fails."""
    pass


class PipedriveAPIError(CRMDataError):
    """Raised when Pipedrive API request fails."""
    pass


class PipedriveDataError(CRMDataError):
    """Raised when Pipedrive data processing fails."""
    pass


class PipedriveConfigurationError(Exception):
    """Raised when Pipedrive configuration is invalid."""
    pass


class PipedriveQuotaError(CRMDataError):
    """Raised when Pipedrive API quota is exceeded."""
    pass


class PipedrivePermissionError(CRMAuthenticationError):
    """Raised when Pipedrive permission is denied."""
    pass


class PipedriveValidationError(CRMDataError):
    """Raised when Pipedrive data validation fails."""
    pass


class PipedriveWebhookError(CRMDataError):
    """Raised when Pipedrive webhook operation fails."""
    pass


class PipedriveFileError(CRMDataError):
    """Raised when Pipedrive file operation fails."""
    pass


class PipedriveFilterError(CRMDataError):
    """Raised when Pipedrive filter operation fails."""
    pass