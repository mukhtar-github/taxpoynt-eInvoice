"""
ISO 20022 Financial Messaging Processor
=======================================
International financial messaging standard processor for structured financial data exchange.
Supports global financial messaging formats with Nigerian banking integration.

Components:
- iso20022_validator.py: Core ISO 20022 message validation
- message_processor.py: Financial message processing engine
- nigerian_banking_adapter.py: Nigerian banking system integration
- swift_integration.py: SWIFT network message handling
- models.py: ISO 20022 data models and structures

ISO 20022 Message Types:
- Payment Messages (pacs): Customer payments, bank-to-bank transfers
- Cash Management (camt): Account statements, transaction reporting
- Trade Finance (tsmt): Trade service management, letters of credit
- Securities (sese): Securities settlement, custody services
- Card Payments (casp): Card transaction processing

Nigerian Banking Features:
- CBN (Central Bank of Nigeria) compliance
- NIBSS (Nigeria Inter-Bank Settlement System) integration
- Naira transaction processing
- Nigerian bank code validation
- Local clearing and settlement support
"""

from .iso20022_validator import ISO20022Validator, ValidationResult
from .message_processor import MessageProcessor, ProcessingResult
from .models import (
    ISO20022Message, PaymentMessage, CashManagementMessage,
    MessageValidationError, NigerianBankingContext
)

__all__ = [
    'ISO20022Validator',
    'ValidationResult',
    'MessageProcessor',
    'ProcessingResult',
    'ISO20022Message',
    'PaymentMessage',
    'CashManagementMessage',
    'MessageValidationError',
    'NigerianBankingContext'
]