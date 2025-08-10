"""
Pipedrive CRM Connector Module
Provides integration with Pipedrive CRM for TaxPoynt eInvoice System.
This module implements API token/OAuth 2.0 authentication, Pipedrive API v1 communication,
deal management, and deal-to-invoice transformation for Pipedrive CRM integration.
"""

from .connector import PipedriveCRMConnector
from .auth import PipedriveAuthenticator
from .rest_client import PipedriveRestClient
from .data_extractor import PipedriveDataExtractor
from .deal_transformer import PipedriveDealTransformer
from .exceptions import (
    PipedriveConnectionError,
    PipedriveAuthenticationError,
    PipedriveAPIError,
    PipedriveDataError,
    PipedriveConfigurationError,
    PipedriveQuotaError,
    PipedrivePermissionError,
    PipedriveValidationError,
    PipedriveWebhookError,
    PipedriveFileError,
    PipedriveFilterError
)

__all__ = [
    'PipedriveCRMConnector',
    'PipedriveAuthenticator',
    'PipedriveRestClient',
    'PipedriveDataExtractor',
    'PipedriveDealTransformer',
    'PipedriveConnectionError',
    'PipedriveAuthenticationError',
    'PipedriveAPIError',
    'PipedriveDataError',
    'PipedriveConfigurationError',
    'PipedriveQuotaError',
    'PipedrivePermissionError',
    'PipedriveValidationError',
    'PipedriveWebhookError',
    'PipedriveFileError',
    'PipedriveFilterError'
]