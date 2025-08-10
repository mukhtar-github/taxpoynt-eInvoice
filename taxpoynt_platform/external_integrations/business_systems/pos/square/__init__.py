"""
Square POS Connector Module

Complete Square POS integration for TaxPoynt eInvoice System.
Provides OAuth 2.0 authentication, transaction processing, and FIRS-compliant invoice generation.

Main Components:
- SquarePOSConnector: Main connector implementing BasePOSConnector interface
- SquareAuthenticator: OAuth 2.0 authentication management
- SquareRESTClient: Square API communication
- SquareDataExtractor: Transaction and data extraction
- SquareTransactionTransformer: FIRS-compliant invoice transformation

Usage:
    from taxpoynt_platform.external_integrations.business_systems.pos.square import SquarePOSConnector
    
    config = {
        'application_id': 'your_square_application_id',
        'application_secret': 'your_square_application_secret',
        'sandbox': True,
        'webhook_signature_key': 'your_webhook_key',
        'currency': 'NGN',
        'vat_rate': 0.075
    }
    
    connector = SquarePOSConnector(config)
    await connector.authenticate()
    transactions = await connector.get_transactions()
"""

from .connector import SquarePOSConnector
from .auth import SquareAuthenticator
from .rest_client import SquareRESTClient
from .data_extractor import SquareDataExtractor
from .transaction_transformer import SquareTransactionTransformer
from .exceptions import (
    SquareError,
    SquareConnectionError,
    SquareAuthenticationError,
    SquareAPIError,
    SquareRateLimitError,
    SquareNotFoundError,
    SquareValidationError,
    SquareWebhookError,
    SquarePaymentError,
    SquareOrderError,
    SquareInventoryError,
    SquareConfigurationError,
    SquareTimeoutError,
    create_square_exception
)

__all__ = [
    # Main connector
    'SquarePOSConnector',
    
    # Component classes
    'SquareAuthenticator',
    'SquareRESTClient',
    'SquareDataExtractor',
    'SquareTransactionTransformer',
    
    # Exception classes
    'SquareError',
    'SquareConnectionError',
    'SquareAuthenticationError',
    'SquareAPIError',
    'SquareRateLimitError',
    'SquareNotFoundError',
    'SquareValidationError',
    'SquareWebhookError',
    'SquarePaymentError',
    'SquareOrderError',
    'SquareInventoryError',
    'SquareConfigurationError',
    'SquareTimeoutError',
    'create_square_exception'
]

# Connector metadata
__version__ = '1.0.0'
__author__ = 'TaxPoynt eInvoice Team'
__description__ = 'Square POS connector for Nigerian FIRS e-invoicing compliance'

# Supported features
SUPPORTED_FEATURES = [
    'oauth_authentication',
    'transaction_retrieval',
    'webhook_processing',
    'location_management',
    'payment_methods',
    'invoice_transformation',
    'firs_compliance',
    'nigerian_tax_handling',
    'daily_reporting',
    'transaction_sync',
    'multi_currency',
    'real_time_processing',
    'inventory_integration',
    'customer_management',
    'order_management'
]

# Nigerian market compliance
NIGERIAN_COMPLIANCE = {
    'vat_rate': 0.075,  # 7.5% Nigerian VAT
    'supported_currencies': ['NGN', 'USD'],
    'tin_validation': True,
    'firs_integration': True,
    'ubl_bis_3_0': True,
    'default_customer_tin': '00000000-0001-0'
}