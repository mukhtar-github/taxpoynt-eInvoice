"""
PalmPay POS Integration Package
Comprehensive integration with PalmPay POS systems for TaxPoynt eInvoice platform.

This package provides complete PalmPay POS connectivity including:
- Signature-based authentication and API access management
- REST API client for production and sandbox environments
- Transaction data extraction with Nigerian mobile money integration
- FIRS-compliant UBL BIS 3.0 invoice transformation
- Real-time webhook processing
- Mobile wallet and payment processing support
- Agent network integration
- Multi-terminal and multi-merchant support

Supported PalmPay APIs:
- Payment API v1 (Transactions, Payments, Wallet Operations)
- Merchant API (Merchant Info, Balance, Payment Methods)
- POS Terminal API (Terminal transactions and management)
- Agent Network API (Agent transactions and management)
- Mobile Money API (Mobile money transactions)
- Webhooks (Payment and Transaction events)

Nigerian Mobile Money Integration:
- Automatic 7.5% VAT calculation (VAT-inclusive by default)
- TIN validation and default handling
- Nigerian mobile payment services integration
- FIRS-compliant invoice generation
- CBN (Central Bank of Nigeria) compliance
- Agent network transaction support

Usage:
    from taxpoynt_platform.external_integrations.business_systems.pos.palmpay import (
        PalmPayPOSConnector,
        PalmPayAuthManager,
        PalmPayRestClient,
        PalmPayDataExtractor,
        PalmPayTransactionTransformer
    )
    
    # Initialize connector
    config = ConnectionConfig(
        merchant_id="your_merchant_id",
        credentials={
            'app_id': 'your_palmpay_app_id',
            'app_key': 'your_palmpay_app_key',
            'merchant_id': 'your_merchant_id',
            'terminal_id': 'your_terminal_id',
            'environment': 'sandbox'  # or 'production'
        }
    )
    
    connector = PalmPayPOSConnector(config)
    
    # Connect and sync transactions
    async with connector:
        sync_result = await connector.sync_transactions()
        print(f"Synced {sync_result.records_successful} transactions")

Features:
- ✅ Signature-based Authentication with HMAC SHA-256
- ✅ Dual environment support (sandbox/production)
- ✅ Nigerian mobile money system integration
- ✅ Agent network transaction processing
- ✅ Multi-terminal and multi-merchant architecture
- ✅ Comprehensive error handling
- ✅ Nigerian VAT compliance (7.5% VAT-inclusive)
- ✅ FIRS UBL BIS 3.0 invoice generation
- ✅ Real-time webhook processing
- ✅ Batch transaction synchronization
- ✅ Mobile wallet and payment processing
- ✅ POS terminal management
- ✅ Payment method diversification

PalmPay POS System Compatibility:
- PalmPay POS Terminals (All models)
- PalmPay Mobile Wallet
- PalmPay Agent Network
- PalmPay Business Dashboard
- PalmPay Payment Gateway
- PalmPay QR Code Payments
- PalmPay USSD Services
- PalmPay Bank Transfer Integration

API Endpoints Supported:
- /api/v1/merchant/info
- /api/v1/transaction/query
- /api/v1/transaction/detail
- /api/v1/agent/transactions
- /api/v1/mobilemoney/transactions
- /api/v1/payment/create
- /api/v1/payment/status
- /api/v1/balance/query
- /api/v1/agent/info

Nigerian Mobile Money Features:
- PalmPay Wallet transactions
- Multi-network mobile money support
- USSD payment integration
- QR code payment processing
- Bank transfer integration
- Agent network transactions
- Mobile airtime and data purchases
- Bill payment services
"""

from .connector import PalmPayPOSConnector
from .auth import PalmPayAuthManager
from .rest_client import PalmPayRestClient
from .data_extractor import PalmPayDataExtractor
from .transaction_transformer import PalmPayTransactionTransformer
from .exceptions import (
    PalmPayConnectionError,
    PalmPayAuthenticationError,
    PalmPayAPIError,
    PalmPayRateLimitError,
    PalmPayValidationError,
    PalmPayWebhookError,
    PalmPayDataExtractionError,
    PalmPayTransformationError,
    PalmPayConfigurationError,
    PalmPayMobileMoneyError,
    create_palmpay_exception
)

__all__ = [
    # Main connector
    'PalmPayPOSConnector',
    
    # Core components
    'PalmPayAuthManager',
    'PalmPayRestClient',
    'PalmPayDataExtractor',
    'PalmPayTransactionTransformer',
    
    # Exceptions
    'PalmPayConnectionError',
    'PalmPayAuthenticationError',
    'PalmPayAPIError',
    'PalmPayRateLimitError',
    'PalmPayValidationError',
    'PalmPayWebhookError',
    'PalmPayDataExtractionError',
    'PalmPayTransformationError',
    'PalmPayConfigurationError',
    'PalmPayMobileMoneyError',
    'create_palmpay_exception'
]

# Package metadata
__version__ = '1.0.0'
__author__ = 'TaxPoynt Development Team'
__description__ = 'PalmPay POS integration for TaxPoynt eInvoice platform'

# PalmPay-specific configuration
PALMPAY_CONFIG = {
    'api_version': 'v1',
    'supported_environments': ['sandbox', 'production'],
    'base_urls': {
        'sandbox': 'https://openapi-uat.palmpay.com',
        'production': 'https://openapi.palmpay.com'
    },
    'signature_algorithm': 'SHA256',
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
        'REFUND_PROCESSED',
        'AGENT_TRANSACTION_COMPLETED'
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
        'pos_terminal',
        'agent_network'
    ]
}

# Mobile money integration settings
MOBILE_MONEY_INTEGRATION = {
    'palmpay_wallet_support': True,
    'multi_network_support': True,
    'ussd_integration': True,
    'qr_code_payments': True,
    'agent_network': True,
    'supported_services': [
        {'service': 'PalmPay Wallet', 'code': 'PALMPAY_WALLET'},
        {'service': 'MTN Mobile Money', 'code': 'MTN_MOMO'},
        {'service': 'Airtel Money', 'code': 'AIRTEL_MONEY'},
        {'service': 'Glo Mobile Money', 'code': 'GLO_MOBILE_MONEY'},
        {'service': '9mobile Mobile Money', 'code': '9MOBILE_MONEY'}
    ]
}

# Agent network integration settings
AGENT_NETWORK_INTEGRATION = {
    'agent_transaction_support': True,
    'multi_agent_support': True,
    'agent_commission_tracking': True,
    'agent_location_support': True,
    'supported_agent_types': [
        {'type': 'PalmPay Agent', 'code': 'PALMPAY_AGENT'},
        {'type': 'Banking Agent', 'code': 'BANKING_AGENT'},
        {'type': 'Mobile Money Agent', 'code': 'MOMO_AGENT'},
        {'type': 'Retail Agent', 'code': 'RETAIL_AGENT'}
    ]
}

# Business categories for PalmPay transactions
BUSINESS_CATEGORIES = {
    'payment_types': [
        'service_payment',
        'goods_purchase',
        'financial_service',
        'telecommunications',
        'utility_payment',
        'mobile_payment',
        'wallet_transfer',
        'agent_commission',
        'agent_network_payment'
    ],
    'transaction_types': [
        'PAYMENT',
        'TRANSFER',
        'PURCHASE',
        'REFUND',
        'WITHDRAWAL',
        'DEPOSIT',
        'BILL_PAYMENT',
        'AIRTIME_PURCHASE',
        'AGENT_TRANSACTION'
    ]
}

# Feature matrix
FEATURES = {
    'authentication': {
        'signature_based': True,
        'hmac_sha256': True,
        'multi_merchant': True,
        'multi_terminal': True,
        'sandbox_support': True
    },
    'data_extraction': {
        'merchant_transactions': True,
        'pos_transactions': True,
        'wallet_transactions': True,
        'agent_transactions': True,
        'mobile_money_transactions': True,
        'payment_history': True,
        'real_time': True,
        'batch_sync': True
    },
    'mobile_money_features': {
        'palmpay_wallet': True,
        'multi_network_support': True,
        'ussd_payments': True,
        'qr_code_payments': True,
        'agent_transactions': True,
        'bill_payments': True
    },
    'agent_network_features': {
        'agent_transactions': True,
        'multi_agent_support': True,
        'commission_tracking': True,
        'location_support': True,
        'agent_info_retrieval': True
    },
    'payment_processing': {
        'wallet_payments': True,
        'card_payments': True,
        'bank_transfers': True,
        'ussd_payments': True,
        'qr_payments': True,
        'agent_payments': True,
        'mobile_money_payments': True
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