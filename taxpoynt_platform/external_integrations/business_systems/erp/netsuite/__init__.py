"""
NetSuite ERP Connector Module
Provides integration with NetSuite ERP for TaxPoynt eInvoice System.

This module implements OAuth 1.0a authentication, REST API communication,
SuiteQL querying, and FIRS-compliant data transformation for NetSuite integration.
"""

from .connector import NetSuiteERPConnector
from .auth import NetSuiteAuthenticator
from .rest_client import NetSuiteRESTClient
from .data_extractor import NetSuiteDataExtractor
from .firs_transformer import NetSuiteFIRSTransformer
from .exceptions import (
    NetSuiteAPIError,
    NetSuiteAuthenticationError,
    NetSuiteConnectionError,
    NetSuiteDataError,
    NetSuiteConfigurationError,
    NetSuiteRateLimitError,
    NetSuiteValidationError
)

__all__ = [
    'NetSuiteERPConnector',
    'NetSuiteAuthenticator',
    'NetSuiteRESTClient',
    'NetSuiteDataExtractor',
    'NetSuiteFIRSTransformer',
    'NetSuiteAPIError',
    'NetSuiteAuthenticationError',
    'NetSuiteConnectionError',
    'NetSuiteDataError',
    'NetSuiteConfigurationError',
    'NetSuiteRateLimitError',
    'NetSuiteValidationError'
]