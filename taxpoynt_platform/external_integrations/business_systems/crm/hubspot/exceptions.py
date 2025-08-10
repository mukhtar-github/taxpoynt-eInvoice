"""
HubSpot CRM Connector - Custom Exceptions
Exception classes for HubSpot CRM integration and error handling.
"""

from ....connector_framework import CRMConnectionError, CRMAuthenticationError, CRMDataError


class HubSpotConnectionError(CRMConnectionError):
    """Raised when HubSpot connection fails."""
    pass


class HubSpotAuthenticationError(CRMAuthenticationError):
    """Raised when HubSpot authentication fails."""
    pass


class HubSpotAPIError(Exception):
    """Raised when HubSpot API requests fail."""
    pass


class HubSpotDataError(CRMDataError):
    """Raised when HubSpot data operations fail."""
    pass


class HubSpotConfigurationError(Exception):
    """Raised when HubSpot configuration is invalid."""
    pass


class HubSpotRateLimitError(Exception):
    """Raised when HubSpot API rate limits are exceeded."""
    pass


class HubSpotValidationError(Exception):
    """Raised when HubSpot data validation fails."""
    pass


class HubSpotWebhookError(Exception):
    """Raised when HubSpot webhook processing fails."""
    pass