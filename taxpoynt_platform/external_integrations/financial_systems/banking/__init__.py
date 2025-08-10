"""
Banking Systems Integration
===========================

Core banking integration framework for Nigerian financial institutions.
Provides unified access to transaction data, account information, and
real-time banking services through various channels.

Supported Banking Channels:
- Open Banking (Mono, Stitch)
- USSD Banking Services
- NIBSS Inter-bank System
- BVN Validation Services

Based on existing TaxPoynt payment patterns for consistency.
"""

from enum import Enum
from typing import Dict, Any, Optional
from datetime import datetime
from decimal import Decimal


class BankingChannel(str, Enum):
    """Banking integration channels"""
    OPEN_BANKING = "open_banking"
    USSD = "ussd"
    NIBSS = "nibss"
    BVN = "bvn"


class AccountType(str, Enum):
    """Nigerian bank account types"""
    SAVINGS = "savings"
    CURRENT = "current"
    DOMICILIARY = "domiciliary"
    FIXED_DEPOSIT = "fixed_deposit"
    CORPORATE = "corporate"


class TransactionChannel(str, Enum):
    """Transaction channels in Nigerian banking"""
    MOBILE_APP = "mobile_app"
    USSD = "ussd"
    WEB = "web"
    ATM = "atm"
    POS = "pos"
    BRANCH = "branch"
    ONLINE_TRANSFER = "online_transfer"


class TransactionStatus(str, Enum):
    """Transaction processing status"""
    PENDING = "pending"
    SUCCESSFUL = "successful"
    FAILED = "failed"
    REVERSED = "reversed"
    PROCESSING = "processing"


# Common Nigerian banking data structures
NIGERIAN_BANK_HOLIDAYS = [
    "01-01",  # New Year's Day
    "04-14",  # Good Friday (varies)
    "04-17",  # Easter Monday (varies)
    "05-01",  # Workers' Day
    "06-12",  # Democracy Day
    "10-01",  # Independence Day
    "12-25",  # Christmas Day
    "12-26",  # Boxing Day
]

USSD_CODES = {
    "access_bank": "*901#",
    "gtbank": "*737#",
    "zenith_bank": "*966#",
    "first_bank": "*894#",
    "uba": "*919#",
    "fidelity_bank": "*770#",
    "union_bank": "*826#",
    "sterling_bank": "*822#",
    "stanbic_ibtc": "*909#",
    "fcmb": "*329#",
}

# Export key components
__all__ = [
    "BankingChannel",
    "AccountType", 
    "TransactionChannel",
    "TransactionStatus",
    "NIGERIAN_BANK_HOLIDAYS",
    "USSD_CODES"
]