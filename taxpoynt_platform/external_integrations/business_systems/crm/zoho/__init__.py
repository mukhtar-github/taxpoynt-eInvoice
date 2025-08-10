"""
Zoho CRM Connector Module
Provides integration with Zoho CRM for TaxPoynt eInvoice System.
This module implements OAuth 2.0 authentication, CRM API v2 communication,
deal management, and deal-to-invoice transformation for Zoho CRM integration.
"""

from .connector import ZohoCRMConnector
from .auth import ZohoCRMAuthenticator
from .rest_client import ZohoCRMRestClient
from .data_extractor import ZohoCRMDataExtractor
from .deal_transformer import ZohoCRMDealTransformer
from .exceptions import (
    ZohoCRMConnectionError,
    ZohoCRMAuthenticationError,
    ZohoCRMAPIError,
    ZohoCRMDataError,
    ZohoCRMConfigurationError,
    ZohoCRMQuotaError,
    ZohoCRMPermissionError,
    ZohoCRMValidationError,
    ZohoCRMBulkError,
    ZohoCRMWebhookError,
    ZohoCRMFileError
)

__all__ = [
    'ZohoCRMConnector',
    'ZohoCRMAuthenticator',
    'ZohoCRMRestClient',
    'ZohoCRMDataExtractor',
    'ZohoCRMDealTransformer',
    'ZohoCRMConnectionError',
    'ZohoCRMAuthenticationError',
    'ZohoCRMAPIError',
    'ZohoCRMDataError',
    'ZohoCRMConfigurationError',
    'ZohoCRMQuotaError',
    'ZohoCRMPermissionError',
    'ZohoCRMValidationError',
    'ZohoCRMBulkError',
    'ZohoCRMWebhookError',
    'ZohoCRMFileError'
]