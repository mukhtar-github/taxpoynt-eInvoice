"""
Moniepoint POS Integration Package
Comprehensive integration with Moniepoint POS systems for TaxPoynt eInvoice platform.

This package provides complete Moniepoint POS connectivity including:
- API key authentication and token management
- REST API client for production and sandbox environments
- Transaction data extraction with Nigerian banking integration
- FIRS-compliant UBL BIS 3.0 invoice transformation
- Real-time webhook processing
- NIP (Nigeria Instant Payment) support
- Multi-merchant and multi-terminal support

Supported Moniepoint APIs:
- Monnify API v1 (Transactions, Payments, Transfers, Virtual Accounts)
- Authentication API (Token-based authentication)
- Webhooks (Transaction and Settlement events)
- Banking Integration APIs (NIP, Account Verification)

Nigerian Market Integration:
- Automatic 7.5% VAT calculation (VAT-inclusive by default)
- TIN validation and default handling
- Nigerian banking system integration
- FIRS-compliant invoice generation
- CBN (Central Bank of Nigeria) compliance

Usage:
    from taxpoynt_platform.external_integrations.business_systems.pos.moniepoint import (
        MoniepointPOSConnector,
        MoniepointAuthManager,
        MoniepointRestClient,
        MoniepointDataExtractor,
        MoniepointTransactionTransformer
    )
    
    # Initialize connector
    config = ConnectionConfig(
        merchant_id="your_merchant_id",
        credentials={
            'api_key': 'your_moniepoint_api_key',
            'secret_key': 'your_moniepoint_secret_key',
            'merchant_id': 'your_merchant_id',
            'terminal_id': 'your_terminal_id',  # Optional
            'environment': 'sandbox'  # or 'production'
        }
    )
    
    connector = MoniepointPOSConnector(config)
    
    # Connect and sync transactions
    async with connector:
        sync_result = await connector.sync_transactions()
        print(f"Synced {sync_result.records_successful} transactions")

Features:
- ✅ API Key Authentication with token management
- ✅ Dual environment support (sandbox/production)
- ✅ Nigerian banking system integration
- ✅ Multi-merchant and multi-terminal architecture
- ✅ Comprehensive error handling
- ✅ Nigerian VAT compliance (7.5% VAT-inclusive)
- ✅ FIRS UBL BIS 3.0 invoice generation
- ✅ Real-time webhook processing
- ✅ Batch transaction synchronization
- ✅ NIP (Nigeria Instant Payment) support
- ✅ Virtual account management
- ✅ Account verification services

Moniepoint POS System Compatibility:
- Moniepoint POS Terminals (All models)
- Moniepoint Mobile POS
- Moniepoint Virtual Terminals
- Moniepoint Payment Gateway
- Moniepoint Agent Banking
- Moniepoint Business Banking

API Endpoints Supported:
- /api/v1/merchant/transactions
- /api/v1/merchant/{merchantId}
- /api/v1/transactions/{accountReference}
- /api/v1/bank-transfer/reserved-accounts
- /api/v1/disbursements/single
- /api/v1/disbursements/account/validate
- /api/v1/sdk/transactions/banks
- /api/v1/auth/login

Nigerian Banking Features:
- NIP (Nigeria Instant Payment) transactions
- Virtual account management
- Multi-bank support (Access, GTBank, UBA, Zenith, etc.)
- USSD payment integration
- QR code payments
- Card payment processing
- Mobile money integration
"""

from .connector import MoniepointPOSConnector
from .auth import MoniepointAuthManager
from .rest_client import MoniepointRestClient
from .data_extractor import MoniepointDataExtractor
from .transaction_transformer import MoniepointTransactionTransformer
from .exceptions import (
    MoniepointConnectionError,
    MoniepointAuthenticationError,
    MoniepointAPIError,
    MoniepointRateLimitError,
    MoniepointValidationError,
    MoniepointWebhookError,
    MoniepointDataExtractionError,
    MoniepointTransformationError,
    MoniepointConfigurationError,
    MoniepointNIPError,
    create_moniepoint_exception
)

__all__ = [
    # Main connector
    'MoniepointPOSConnector',
    
    # Core components
    'MoniepointAuthManager',
    'MoniepointRestClient',
    'MoniepointDataExtractor',
    'MoniepointTransactionTransformer',
    
    # Exceptions
    'MoniepointConnectionError',
    'MoniepointAuthenticationError',
    'MoniepointAPIError',
    'MoniepointRateLimitError',
    'MoniepointValidationError',
    'MoniepointWebhookError',
    'MoniepointDataExtractionError',
    'MoniepointTransformationError',
    'MoniepointConfigurationError',
    'MoniepointNIPError',
    'create_moniepoint_exception'
]

# Package metadata
__version__ = '1.0.0'
__author__ = 'TaxPoynt Development Team'
__description__ = 'Moniepoint POS integration for TaxPoynt eInvoice platform'

# Moniepoint-specific configuration
MONIEPOINT_CONFIG = {
    'api_version': 'v1',
    'supported_environments': ['sandbox', 'production'],
    'base_urls': {
        'sandbox': 'https://sandbox.monnify.com',
        'production': 'https://api.monnify.com'
    },
    'auth_endpoints': {
        'sandbox': 'https://sandbox.monnify.com/api/v1/auth/login',
        'production': 'https://api.monnify.com/api/v1/auth/login'
    },
    'rate_limits': {
        'default': 1000,  # requests per hour
        'burst': 100     # requests per minute
    },
    'webhook_events': [
        'TRANSACTION_COMPLETED',
        'PAYMENT_RECEIVED',
        'SUCCESSFUL_TRANSACTION',
        'FAILED_TRANSACTION',
        'SETTLEMENT_COMPLETED',
        'ACCOUNT_CREDITED',
        'TRANSFER_COMPLETED'
    ]
}

# Nigerian market compliance settings
NIGERIAN_COMPLIANCE = {
    'vat_rate': 0.075,  # 7.5% VAT
    'currency': 'NGN',
    'default_tin': '00000000-0001',
    'vat_inclusive_by_default': True,
    'supported_payment_methods': [
        'card',
        'bank_transfer',
        'ussd',
        'qr_code',
        'mobile_money',
        'nip',
        'cash'
    ]
}

# Nigerian banking integration settings
BANKING_INTEGRATION = {
    'nip_support': True,
    'virtual_accounts': True,
    'account_verification': True,
    'multi_bank_support': True,
    'supported_banks': [
        {'code': '044', 'name': 'Access Bank'},
        {'code': '014', 'name': 'Afribank Nigeria Plc'},
        {'code': '023', 'name': 'Citibank Nigeria Limited'},
        {'code': '050', 'name': 'Ecobank Nigeria Plc'},
        {'code': '011', 'name': 'First Bank of Nigeria Limited'},
        {'code': '214', 'name': 'First City Monument Bank Limited'},
        {'code': '070', 'name': 'Fidelity Bank Plc'},
        {'code': '058', 'name': 'Guaranty Trust Bank Plc'},
        {'code': '030', 'name': 'Heritage Banking Company Ltd.'},
        {'code': '082', 'name': 'Keystone Bank Limited'},
        {'code': '221', 'name': 'Stanbic IBTC Bank Plc'},
        {'code': '068', 'name': 'Standard Chartered Bank Nigeria Limited'},
        {'code': '032', 'name': 'Union Bank of Nigeria Plc'},
        {'code': '033', 'name': 'United Bank for Africa Plc'},
        {'code': '215', 'name': 'Unity Bank Plc'},
        {'code': '035', 'name': 'Wema Bank Plc'},
        {'code': '057', 'name': 'Zenith Bank Plc'}
    ]
}

# Feature matrix
FEATURES = {
    'authentication': {
        'api_key': True,
        'token_management': True,
        'multi_merchant': True,
        'multi_terminal': True,
        'sandbox_support': True
    },
    'data_extraction': {
        'transactions': True,
        'payments': True,
        'virtual_accounts': True,
        'settlements': True,
        'real_time': True,
        'batch_sync': True
    },
    'banking_features': {
        'nip_transactions': True,
        'account_verification': True,
        'bank_transfers': True,
        'virtual_accounts': True,
        'multi_bank_support': True,
        'ussd_integration': True
    },
    'payment_processing': {
        'card_payments': True,
        'bank_transfers': True,
        'ussd_payments': True,
        'qr_payments': True,
        'mobile_money': True,
        'cash_handling': True
    },
    'tax_compliance': {
        'nigerian_vat': True,
        'vat_inclusive_calculation': True,
        'tin_validation': True,
        'firs_compliance': True,
        'cbn_compliance': True
    },
    'integration': {
        'webhooks': True,
        'rest_api': True,
        'rate_limiting': True,
        'error_handling': True,
        'health_monitoring': True,
        'signature_validation': True
    }
}