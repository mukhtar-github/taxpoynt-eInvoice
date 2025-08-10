"""
Interswitch Payment Processor Module
===================================

Comprehensive Interswitch integration for Nigerian interbank transaction processing.
Provides NDPR-compliant data collection with AI-based transaction classification for 
e-invoicing compliance.

Key Features:
- Interbank transaction specialization (NIBSS integration)
- Real-time transaction processing
- Nigerian business income classification (AI + rule-based fallback)
- NDPR privacy protection with configurable levels
- Real-time webhook processing
- CBN interbank compliance monitoring
- Universal Transaction Processor integration

Components:
- InterswitchConnector: Main integration interface with account discovery
- InterswitchConfig: Configuration management with environment support
- InterswitchTransaction: Transaction data models with privacy controls
- InterswitchCustomer: Customer data models with KYC compliance
- InterswitchAuthManager: Secure authentication and token management
- InterswitchPaymentProcessor: Core payment processing with classification
- InterswitchWebhookHandler: Webhook processing and validation

Usage:
    from taxpoynt_platform.external_integrations.financial_systems.payments.nigerian_processors.interswitch import (
        InterswitchConnector, InterswitchConfig
    )
    
    config = InterswitchConfig(
        client_id="your_client_id",
        client_secret="your_secret",
        environment="sandbox"
    )
    
    connector = InterswitchConnector(config)
    transactions = await connector.fetch_transactions(merchant_id)
"""

from .connector import InterswitchConnector, InterswitchConnectorConfig
from .models import InterswitchTransaction, InterswitchCustomer, NIGERIAN_BANKS
from .auth import InterswitchAuthManager
from .payment_processor import InterswitchPaymentProcessor
from .webhook_handler import InterswitchWebhookHandler

__all__ = [
    'InterswitchConnector',
    'InterswitchConnectorConfig',
    'InterswitchTransaction',
    'InterswitchCustomer',
    'NIGERIAN_BANKS',
    'InterswitchAuthManager',
    'InterswitchPaymentProcessor',
    'InterswitchWebhookHandler'
]

# Version info
__version__ = "1.0.0"
__author__ = "TaxPoynt Development Team"
__email__ = "info@taxpoynt.com"