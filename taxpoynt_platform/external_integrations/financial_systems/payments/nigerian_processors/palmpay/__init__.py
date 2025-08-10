"""
PalmPay Payment Processor Module
==============================

Comprehensive PalmPay integration for Nigerian mobile money and inter-bank transfer processing.
Provides NDPR-compliant data collection with AI-based transaction classification for 
e-invoicing compliance.

Key Features:
- Inter-bank transfer specialization
- Mobile money transaction processing
- Nigerian business income classification (AI + rule-based fallback)
- NDPR privacy protection with configurable levels
- Real-time webhook processing
- CBN mobile money compliance monitoring
- Universal Transaction Processor integration

Components:
- PalmPayConnector: Main integration interface with account discovery
- PalmPayConfig: Configuration management with environment support
- PalmPayTransaction: Transaction data models with privacy controls
- PalmPayCustomer: Customer data models with KYC compliance
- PalmPayAuthManager: Secure authentication and token management
- PalmPayPaymentProcessor: Core payment processing with classification
- PalmPayWebhookHandler: Webhook processing and validation

Usage:
    from taxpoynt_platform.external_integrations.financial_systems.payments.nigerian_processors.palmpay import (
        PalmPayConnector, PalmPayConfig
    )
    
    config = PalmPayConfig(
        api_key="your_api_key",
        secret_key="your_secret",
        environment="sandbox"
    )
    
    connector = PalmPayConnector(config)
    transactions = await connector.fetch_transactions(merchant_id)
"""

from .connector import PalmPayConnector, PalmPayConnectorConfig
from .models import PalmPayTransaction, PalmPayCustomer
from .auth import PalmPayAuthManager
from .payment_processor import PalmPayPaymentProcessor
from .webhook_handler import PalmPayWebhookHandler

__all__ = [
    'PalmPayConnector',
    'PalmPayConnectorConfig',
    'PalmPayTransaction',
    'PalmPayCustomer', 
    'PalmPayAuthManager',
    'PalmPayPaymentProcessor',
    'PalmPayWebhookHandler'
]

# Version info
__version__ = "1.0.0"
__author__ = "TaxPoynt Development Team"
__email__ = "info@taxpoynt.com"