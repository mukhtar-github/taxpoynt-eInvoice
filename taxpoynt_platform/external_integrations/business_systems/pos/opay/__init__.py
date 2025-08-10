"""
OPay POS Integration Package
Comprehensive integration with OPay POS systems for TaxPoynt eInvoice platform.

This package provides complete OPay POS connectivity including:
- Signature-based authentication and API access management
- REST API client for production and sandbox environments
- Transaction data extraction with Nigerian mobile money integration
- FIRS-compliant UBL BIS 3.0 invoice transformation
- Real-time webhook processing
- Mobile wallet and payment processing support
- Multi-terminal and multi-merchant support

Supported OPay APIs:
- Payment API v3 (Transactions, Payments, Wallet Operations)
- Merchant API (Merchant Info, Balance, Payment Methods)
- POS Terminal API (Terminal transactions and management)
- Webhooks (Payment and Transaction events)
- Mobile Money Integration APIs

Nigerian Mobile Money Integration:
- Automatic 7.5% VAT calculation (VAT-inclusive by default)
- TIN validation and default handling
- Nigerian mobile money services integration
- FIRS-compliant invoice generation
- CBN (Central Bank of Nigeria) compliance

Usage:
    from taxpoynt_platform.external_integrations.business_systems.pos.opay import (
        OPayPOSConnector,
        OPayAuthManager,
        OPayRestClient,
        OPayDataExtractor,
        OPayTransactionTransformer
    )
    
    # Initialize connector
    config = ConnectionConfig(
        merchant_id="your_merchant_id",
        credentials={
            'public_key': 'your_opay_public_key',
            'private_key': 'your_opay_private_key',
            'merchant_id': 'your_merchant_id',
            'environment': 'sandbox'  # or 'production'
        }
    )
    
    connector = OPayPOSConnector(config)
    
    # Connect and sync transactions
    async with connector:
        sync_result = await connector.sync_transactions()
        print(f"Synced {sync_result.records_successful} transactions")

Features:
- ✅ Signature-based Authentication with HMAC SHA-512
- ✅ Dual environment support (sandbox/production)
- ✅ Nigerian mobile money system integration
- ✅ Multi-terminal and multi-merchant architecture
- ✅ Comprehensive error handling
- ✅ Nigerian VAT compliance (7.5% VAT-inclusive)
- ✅ FIRS UBL BIS 3.0 invoice generation
- ✅ Real-time webhook processing
- ✅ Batch transaction synchronization
- ✅ Mobile wallet and payment processing
- ✅ POS terminal management
- ✅ Payment method diversification

OPay POS System Compatibility:
- OPay POS Terminals (All models)
- OPay Mobile Wallet
- OPay Agent Network
- OPay Business Dashboard
- OPay Payment Gateway
- OPay QR Code Payments
- OPay USSD Services
- OPay Bank Transfer Integration

API Endpoints Supported:
- /api/v3/merchant/transactions
- /api/v3/merchant/info
- /api/v3/merchant/balance
- /api/v3/pos/transactions
- /api/v3/wallet/transactions
- /api/v3/payment/initialize
- /api/v3/payment/status
- /api/v3/payment/methods
- /api/v3/transaction/status

Nigerian Mobile Money Features:
- OPay Wallet transactions
- Multi-network mobile money support
- USSD payment integration
- QR code payment processing
- Bank transfer integration
- Agent network transactions
- Mobile airtime and data purchases
- Bill payment services
"""

from .connector import OPayPOSConnector
from .auth import OPayAuthManager
from .rest_client import OPayRestClient
from .data_extractor import OPayDataExtractor
from .transaction_transformer import OPayTransactionTransformer
from .exceptions import (
    OPayConnectionError,
    OPayAuthenticationError,
    OPayAPIError,
    OPayRateLimitError,
    OPayValidationError,
    OPayWebhookError,
    OPayDataExtractionError,
    OPayTransformationError,
    OPayConfigurationError,
    OPayWalletError,
    create_opay_exception
)

__all__ = [
    # Main connector
    'OPayPOSConnector',
    
    # Core components
    'OPayAuthManager',
    'OPayRestClient',
    'OPayDataExtractor',
    'OPayTransactionTransformer',
    
    # Exceptions
    'OPayConnectionError',
    'OPayAuthenticationError',
    'OPayAPIError',
    'OPayRateLimitError',
    'OPayValidationError',
    'OPayWebhookError',
    'OPayDataExtractionError',
    'OPayTransformationError',
    'OPayConfigurationError',
    'OPayWalletError',
    'create_opay_exception'
]

# Package metadata
__version__ = '1.0.0'
__author__ = 'TaxPoynt Development Team'
__description__ = 'OPay POS integration for TaxPoynt eInvoice platform'

# OPay-specific configuration
OPAY_CONFIG = {
    'api_version': 'v3',
    'supported_environments': ['sandbox', 'production'],
    'base_urls': {
        'sandbox': 'https://sandboxapi.opayweb.com',
        'production': 'https://liveapi.opayweb.com'
    },
    'signature_algorithm': 'SHA512',
    'rate_limits': {
        'default': 1000,  # requests per hour
        'burst': 50      # requests per minute
    },
    'webhook_events': [
        'PAYMENT_SUCCESS',
        'PAYMENT_FAILED',
        'TRANSACTION_COMPLETED',
        'ORDER_PAID',
        'ORDER_CANCELLED',
        'WALLET_CREDITED',
        'WALLET_DEBITED',
        'TRANSFER_COMPLETED',
        'REFUND_PROCESSED'
    ]
}

# Nigerian market compliance settings
NIGERIAN_COMPLIANCE = {
    'vat_rate': 0.075,  # 7.5% VAT
    'currency': 'NGN',
    'default_tin': '00000000-0001',
    'vat_inclusive_by_default': True,
    'supported_payment_methods': [
        'mobile_wallet',
        'debit_card',
        'bank_transfer',
        'ussd',
        'qr_code',
        'mobile_money',
        'cash',
        'pos_terminal'
    ]
}

# Mobile money integration settings
MOBILE_MONEY_INTEGRATION = {
    'opay_wallet_support': True,
    'multi_network_support': True,
    'ussd_integration': True,
    'qr_code_payments': True,
    'agent_network': True,
    'supported_services': [
        {'service': 'OPay Wallet', 'code': 'OPAY_WALLET'},
        {'service': 'MTN Mobile Money', 'code': 'MTN_MOMO'},
        {'service': 'Airtel Money', 'code': 'AIRTEL_MONEY'},
        {'service': 'Glo Mobile Money', 'code': 'GLO_MOBILE_MONEY'},
        {'service': '9mobile Mobile Money', 'code': '9MOBILE_MONEY'}
    ]
}

# Business categories for OPay transactions
BUSINESS_CATEGORIES = {
    'payment_types': [
        'service_payment',
        'goods_purchase',
        'financial_service',
        'telecommunications',
        'utility_payment',
        'mobile_payment',
        'wallet_transfer',
        'agent_commission'
    ],
    'transaction_types': [
        'PAYMENT',
        'TRANSFER',
        'PURCHASE',
        'REFUND',
        'WITHDRAWAL',
        'DEPOSIT',
        'BILL_PAYMENT',
        'AIRTIME_PURCHASE'
    ]
}

# Feature matrix
FEATURES = {
    'authentication': {
        'signature_based': True,
        'hmac_sha512': True,
        'multi_merchant': True,
        'multi_terminal': True,
        'sandbox_support': True
    },
    'data_extraction': {
        'merchant_transactions': True,
        'pos_transactions': True,
        'wallet_transactions': True,
        'payment_history': True,
        'real_time': True,
        'batch_sync': True
    },
    'mobile_money_features': {
        'opay_wallet': True,
        'multi_network_support': True,
        'ussd_payments': True,
        'qr_code_payments': True,
        'agent_transactions': True,
        'bill_payments': True
    },
    'payment_processing': {
        'wallet_payments': True,
        'card_payments': True,
        'bank_transfers': True,
        'ussd_payments': True,
        'qr_payments': True,
        'agent_payments': True
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