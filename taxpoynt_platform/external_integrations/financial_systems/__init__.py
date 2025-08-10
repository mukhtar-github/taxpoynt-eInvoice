"""
Financial Systems Integration
============================

Comprehensive integration framework for Nigerian financial systems including:
- Open Banking providers (Mono, Stitch)
- USSD banking services
- NIBSS integration
- BVN validation services

This package provides unified access to financial transaction data, automated
invoice generation, and FIRS-compliant financial reporting.

Architecture aligned with existing TaxPoynt patterns:
- Base connector patterns from backend/app/integrations/payments/base.py
- Webhook verification from backend/app/utils/webhook_verification.py
- USSD models from backend/app/integrations/ussd/models.py
"""

__version__ = "1.0.0"
__author__ = "TaxPoynt Platform Team"

# Core financial system types
from enum import Enum


class FinancialSystemType(str, Enum):
    """Types of financial systems supported"""
    OPEN_BANKING = "open_banking"
    USSD_GATEWAY = "ussd_gateway"
    NIBSS_INTEGRATION = "nibss_integration"
    BVN_VALIDATION = "bvn_validation"


class TransactionType(str, Enum):
    """Nigerian transaction types for e-invoicing"""
    CREDIT = "credit"  # Money received
    DEBIT = "debit"    # Money sent
    TRANSFER = "transfer"
    PAYMENT = "payment"
    REFUND = "refund"
    REVERSAL = "reversal"


class NigerianBankCode(str, Enum):
    """Major Nigerian banks with their codes"""
    ACCESS_BANK = "044"
    DIAMOND_BANK = "063"
    ECOBANK = "050"
    FIDELITY_BANK = "070"
    FIRST_BANK = "011"
    FIRST_CITY_MONUMENT_BANK = "214"
    GUARANTY_TRUST_BANK = "058"
    HERITAGE_BANK = "030"
    KEYSTONE_BANK = "082"
    POLARIS_BANK = "076"
    STANBIC_IBTC = "221"
    STANDARD_CHARTERED = "068"
    STERLING_BANK = "232"
    UNION_BANK = "032"
    UNITED_BANK_FOR_AFRICA = "033"
    UNITY_BANK = "215"
    WEMA_BANK = "035"
    ZENITH_BANK = "057"


# Export key components for easy access
__all__ = [
    "FinancialSystemType",
    "TransactionType", 
    "NigerianBankCode"
]