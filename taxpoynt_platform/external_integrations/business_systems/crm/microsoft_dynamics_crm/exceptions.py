"""
Microsoft Dynamics CRM Connector - Custom Exceptions
Exception classes for Microsoft Dynamics CRM integration and error handling.
"""

from ....connector_framework import CRMConnectionError, CRMAuthenticationError, CRMDataError


class DynamicsCRMConnectionError(CRMConnectionError):
    """Raised when Microsoft Dynamics CRM connection fails."""
    pass


class DynamicsCRMAuthenticationError(CRMAuthenticationError):
    """Raised when Microsoft Dynamics CRM authentication fails."""
    pass


class DynamicsCRMAPIError(CRMDataError):
    """Raised when Microsoft Dynamics CRM API request fails."""
    pass


class DynamicsCRMDataError(CRMDataError):
    """Raised when Microsoft Dynamics CRM data processing fails."""
    pass


class DynamicsCRMConfigurationError(Exception):
    """Raised when Microsoft Dynamics CRM configuration is invalid."""
    pass


class DynamicsCRMODataError(CRMDataError):
    """Raised when Microsoft Dynamics CRM OData query fails."""
    pass


class DynamicsCRMMetadataError(CRMDataError):
    """Raised when Microsoft Dynamics CRM metadata operation fails."""
    pass


class DynamicsCRMBatchError(CRMDataError):
    """Raised when Microsoft Dynamics CRM batch operation fails."""
    pass


class DynamicsCRMSecurityError(CRMAuthenticationError):
    """Raised when Microsoft Dynamics CRM security validation fails."""
    pass


class DynamicsCRMQuotaError(CRMDataError):
    """Raised when Microsoft Dynamics CRM API quota is exceeded."""
    pass


class DynamicsCRMVersionError(CRMDataError):
    """Raised when Microsoft Dynamics CRM version is incompatible."""
    pass