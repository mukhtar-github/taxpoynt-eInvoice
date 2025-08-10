"""
Microsoft Dynamics CRM Connector Module
Provides integration with Microsoft Dynamics CRM for TaxPoynt eInvoice System.
This module implements multi-flow OAuth 2.0 authentication, Web API communication,
OData queries, and deal-to-invoice transformation for Dynamics CRM integration.
"""

from .connector import MicrosoftDynamicsCRMConnector
from .auth import DynamicsCRMAuthenticator
from .rest_client import DynamicsCRMRestClient
from .data_extractor import DynamicsCRMDataExtractor
from .deal_transformer import DynamicsCRMDealTransformer
from .exceptions import (
    DynamicsCRMConnectionError,
    DynamicsCRMAuthenticationError,
    DynamicsCRMAPIError,
    DynamicsCRMDataError,
    DynamicsCRMConfigurationError,
    DynamicsCRMODataError,
    DynamicsCRMMetadataError,
    DynamicsCRMBatchError,
    DynamicsCRMSecurityError,
    DynamicsCRMQuotaError,
    DynamicsCRMVersionError
)

__all__ = [
    'MicrosoftDynamicsCRMConnector',
    'DynamicsCRMAuthenticator',
    'DynamicsCRMRestClient', 
    'DynamicsCRMDataExtractor',
    'DynamicsCRMDealTransformer',
    'DynamicsCRMConnectionError',
    'DynamicsCRMAuthenticationError',
    'DynamicsCRMAPIError',
    'DynamicsCRMDataError',
    'DynamicsCRMConfigurationError',
    'DynamicsCRMODataError',
    'DynamicsCRMMetadataError',
    'DynamicsCRMBatchError',
    'DynamicsCRMSecurityError',
    'DynamicsCRMQuotaError',
    'DynamicsCRMVersionError'
]