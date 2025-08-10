"""
HubSpot CRM Connector Module
Provides integration with HubSpot CRM for TaxPoynt eInvoice System.

This module implements OAuth 2.0/API key authentication, REST API communication,
deal management, and deal-to-invoice transformation for HubSpot integration.
"""

from .connector import HubSpotCRMConnector
from .auth import HubSpotAuthenticator
from .rest_client import HubSpotRESTClient
from .data_extractor import HubSpotDataExtractor
from .deal_transformer import HubSpotDealTransformer
from .exceptions import (
    HubSpotAPIError,
    HubSpotAuthenticationError,
    HubSpotConnectionError,
    HubSpotDataError,
    HubSpotConfigurationError,
    HubSpotRateLimitError,
    HubSpotValidationError,
    HubSpotWebhookError
)

__all__ = [
    'HubSpotCRMConnector',
    'HubSpotAuthenticator',
    'HubSpotRESTClient',
    'HubSpotDataExtractor',
    'HubSpotDealTransformer',
    'HubSpotAPIError',
    'HubSpotAuthenticationError',
    'HubSpotConnectionError',
    'HubSpotDataError',
    'HubSpotConfigurationError',
    'HubSpotRateLimitError',
    'HubSpotValidationError',
    'HubSpotWebhookError'
]