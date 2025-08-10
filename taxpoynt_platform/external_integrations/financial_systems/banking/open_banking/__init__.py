"""
Open Banking Integration Framework
==================================

Nigerian Open Banking implementation supporting multiple providers:
- Mono (Primary Provider)
- Stitch (Enterprise Provider)
- Unified Banking Interface

Provides standardized access to:
- Account information
- Transaction history
- Real-time transaction notifications
- Balance inquiries
- Account verification

Compliance Features:
- NDPR (Nigerian Data Protection Regulation) compliance
- PCI DSS standards
- CBN (Central Bank of Nigeria) guidelines
- 7-year data retention as per FIRS requirements

Based on existing payment connector patterns for consistency.
"""

from enum import Enum
from typing import Dict, Any, List, Optional
from datetime import datetime
from decimal import Decimal


class OpenBankingProvider(str, Enum):
    """Supported Open Banking providers in Nigeria"""
    MONO = "mono"
    STITCH = "stitch" 
    UNIFIED = "unified"  # Multi-provider interface


class ConsentScope(str, Enum):
    """Data access consent scopes per CBN guidelines"""
    ACCOUNT_INFO = "account_info"
    TRANSACTIONS = "transactions"
    BALANCE = "balance"
    IDENTITY = "identity"
    OFFLINE_ACCESS = "offline_access"


class ConsentStatus(str, Enum):
    """Consent lifecycle status"""
    PENDING = "pending"
    AUTHORIZED = "authorized"
    EXPIRED = "expired"
    REVOKED = "revoked"
    REJECTED = "rejected"


class DataCategory(str, Enum):
    """CBN data categorization for consent"""
    BASIC = "basic"          # Account number, name
    DETAILED = "detailed"    # Transaction history
    SENSITIVE = "sensitive"  # Income analysis, spending patterns


class RetentionPeriod(str, Enum):
    """Data retention periods per Nigerian regulations"""
    IMMEDIATE = "immediate"   # Delete immediately after use
    TAX_COMPLIANCE = "7_years"  # FIRS requirement
    REGULATORY = "10_years"   # CBN requirement
    INDEFINITE = "indefinite" # Customer consent based


# Nigerian Open Banking Limits (CBN Guidelines)
TRANSACTION_LIMITS = {
    "daily_inquiry_limit": 50,      # API calls per day per customer
    "monthly_transaction_limit": 1000,  # Transactions per month
    "data_retention_days": 2555,    # 7 years in days
    "consent_validity_days": 90,    # Maximum consent period
    "session_timeout_minutes": 15,  # Session timeout
}

# Standard Nigerian account verification requirements
ACCOUNT_VERIFICATION_REQUIREMENTS = {
    "bvn_required": True,
    "phone_verification": True,
    "email_verification": False,  # Optional
    "address_verification": False,  # Optional for basic accounts
    "minimum_balance": 0,  # No minimum for verification
}

# Export key components
__all__ = [
    "OpenBankingProvider",
    "ConsentScope",
    "ConsentStatus", 
    "DataCategory",
    "RetentionPeriod",
    "TRANSACTION_LIMITS",
    "ACCOUNT_VERIFICATION_REQUIREMENTS"
]