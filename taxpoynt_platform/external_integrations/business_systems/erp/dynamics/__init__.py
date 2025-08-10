"""
Microsoft Dynamics 365 ERP Connector Module
Provides integration with Microsoft Dynamics 365 Business Central for TaxPoynt eInvoice System.

This module implements OAuth 2.0 authentication, REST API communication,
and FIRS-compliant data transformation for Dynamics 365 integration.
"""

from .connector import DynamicsERPConnector
from .auth import DynamicsAuthenticator
from .rest_client import DynamicsRESTClient
from .data_extractor import DynamicsDataExtractor
from .firs_transformer import DynamicsFIRSTransformer
from .exceptions import (
    DynamicsAPIError,
    DynamicsAuthenticationError,
    DynamicsConnectionError,
    DynamicsDataError
)

__all__ = [
    'DynamicsERPConnector',
    'DynamicsAuthenticator',
    'DynamicsRESTClient',
    'DynamicsDataExtractor',
    'DynamicsFIRSTransformer',
    'DynamicsAPIError',
    'DynamicsAuthenticationError',
    'DynamicsConnectionError',
    'DynamicsDataError'
]