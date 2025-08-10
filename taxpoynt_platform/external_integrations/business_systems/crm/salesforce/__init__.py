"""
Salesforce CRM Connector Module
Provides integration with Salesforce CRM for TaxPoynt eInvoice System.

This module implements OAuth 2.0/JWT authentication, REST API communication,
SOQL querying, and deal-to-invoice transformation for Salesforce integration.
"""

from .connector import SalesforceCRMConnector
from .auth import SalesforceAuthenticator
from .rest_client import SalesforceRESTClient
from .data_extractor import SalesforceDataExtractor
from .deal_transformer import SalesforceDealTransformer
from .exceptions import (
    SalesforceAPIError,
    SalesforceAuthenticationError,
    SalesforceConnectionError,
    SalesforceDataError,
    SalesforceConfigurationError,
    SalesforceRateLimitError,
    SalesforceValidationError,
    SalesforceSOQLError
)

__all__ = [
    'SalesforceCRMConnector',
    'SalesforceAuthenticator',
    'SalesforceRESTClient',
    'SalesforceDataExtractor',
    'SalesforceDealTransformer',
    'SalesforceAPIError',
    'SalesforceAuthenticationError',
    'SalesforceConnectionError',
    'SalesforceDataError',
    'SalesforceConfigurationError',
    'SalesforceRateLimitError',
    'SalesforceValidationError',
    'SalesforceSOQLError'
]