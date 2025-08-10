"""
Mono Open Banking Integration
=============================

Primary Open Banking provider integration for Nigerian financial institutions.
Mono provides access to account information, transaction history, and real-time
notifications from major Nigerian banks.

Features:
- Account linking and verification
- Transaction history retrieval  
- Real-time transaction webhooks
- Balance inquiries
- Account holder information
- NDPR-compliant data handling

API Documentation: https://docs.mono.co/
Supported Banks: Access, GTBank, Zenith, First Bank, UBA, Fidelity, FCMB, Sterling

Architecture:
- connector.py: Main Mono API integration
- auth.py: OAuth2/token-based authentication  
- transaction_fetcher.py: Transaction data retrieval
- webhook_handler.py: Real-time event processing
- models.py: Mono-specific data models
- exceptions.py: Mono-specific error handling

Follows existing TaxPoynt patterns from backend/app/integrations/
"""

from enum import Enum
from typing import Dict, Any


class MonoEnvironment(str, Enum):
    """Mono API environments"""
    SANDBOX = "sandbox"
    PRODUCTION = "production"


class MonoScope(str, Enum):
    """Mono API access scopes"""
    ACCOUNT_READ = "account:read"
    TRANSACTIONS_READ = "transactions:read" 
    IDENTITY_READ = "identity:read"
    BALANCE_READ = "balance:read"


class MonoEventType(str, Enum):
    """Mono webhook event types"""
    ACCOUNT_CONNECTED = "account.connected"
    ACCOUNT_UPDATE = "account.updated"
    TRANSACTION_CREATE = "transaction.created"
    TRANSACTION_UPDATE = "transaction.updated"
    ACCOUNT_REAUTHORIZATION_REQUIRED = "account.reauthorization_required"
    ACCOUNT_DISCONNECTED = "account.disconnected"


# Mono API configuration
MONO_CONFIG = {
    "base_urls": {
        MonoEnvironment.SANDBOX: "https://api.withmono.com/v1",
        MonoEnvironment.PRODUCTION: "https://api.withmono.com/v1"
    },
    "widget_urls": {
        MonoEnvironment.SANDBOX: "https://connect.mono.co/",
        MonoEnvironment.PRODUCTION: "https://connect.mono.co/"
    },
    "auth_scopes": [
        MonoScope.ACCOUNT_READ,
        MonoScope.TRANSACTIONS_READ,
        MonoScope.IDENTITY_READ,
        MonoScope.BALANCE_READ
    ],
    "webhook_timeout_seconds": 30,
    "max_retry_attempts": 3,
    "rate_limit_per_minute": 60,
    "max_transactions_per_request": 100
}

# Nigerian bank institutions supported by Mono
SUPPORTED_BANKS = {
    "mono_gtbank": {
        "name": "Guaranty Trust Bank",
        "code": "058",
        "mono_id": "gtbank",
        "supports_real_time": True
    },
    "mono_access": {
        "name": "Access Bank",
        "code": "044", 
        "mono_id": "access",
        "supports_real_time": True
    },
    "mono_zenith": {
        "name": "Zenith Bank",
        "code": "057",
        "mono_id": "zenith", 
        "supports_real_time": True
    },
    "mono_first_bank": {
        "name": "First Bank of Nigeria",
        "code": "011",
        "mono_id": "firstbank",
        "supports_real_time": True
    },
    "mono_uba": {
        "name": "United Bank for Africa",
        "code": "033",
        "mono_id": "uba",
        "supports_real_time": True
    },
    "mono_fidelity": {
        "name": "Fidelity Bank",
        "code": "070",
        "mono_id": "fidelity",
        "supports_real_time": False
    },
    "mono_fcmb": {
        "name": "First City Monument Bank",
        "code": "214",
        "mono_id": "fcmb",
        "supports_real_time": False
    },
    "mono_sterling": {
        "name": "Sterling Bank",
        "code": "232",
        "mono_id": "sterling",
        "supports_real_time": False
    }
}

# Export key components
__all__ = [
    "MonoEnvironment",
    "MonoScope", 
    "MonoEventType",
    "MONO_CONFIG",
    "SUPPORTED_BANKS"
]