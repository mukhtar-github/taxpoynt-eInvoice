"""
Open Banking Providers
======================

Provider-specific implementations for Nigerian Open Banking services.

Supported Providers:
- Mono: Primary provider for individual and SME accounts
- Stitch: Enterprise-grade provider for large corporations
- Unified Banking: Multi-provider aggregation layer

Each provider follows the same interface pattern but implements
provider-specific authentication, data formats, and API patterns.

Architecture Consistency:
- Based on existing connector patterns from backend/app/integrations/
- Follows the same auth, connector, exceptions pattern
- Maintains webhook verification standards
"""

from enum import Enum
from typing import Dict, Any, Optional
from datetime import datetime


class ProviderCapability(str, Enum):
    """Capabilities that providers may support"""
    ACCOUNT_INFO = "account_info"
    TRANSACTION_HISTORY = "transaction_history" 
    REAL_TIME_NOTIFICATIONS = "real_time_notifications"
    BALANCE_INQUIRY = "balance_inquiry"
    ACCOUNT_VERIFICATION = "account_verification"
    BULK_OPERATIONS = "bulk_operations"
    WEBHOOK_SUPPORT = "webhook_support"
    RATE_LIMITING = "rate_limiting"
    SANDBOX_MODE = "sandbox_mode"


class ProviderTier(str, Enum):
    """Provider service tiers"""
    BASIC = "basic"        # Individual accounts, limited features
    PROFESSIONAL = "professional"  # SME accounts, enhanced features  
    ENTERPRISE = "enterprise"      # Corporate accounts, full features
    DEVELOPER = "developer"        # Sandbox/testing tier


# Provider feature matrix
PROVIDER_CAPABILITIES = {
    "mono": {
        "supported_capabilities": [
            ProviderCapability.ACCOUNT_INFO,
            ProviderCapability.TRANSACTION_HISTORY,
            ProviderCapability.REAL_TIME_NOTIFICATIONS,
            ProviderCapability.BALANCE_INQUIRY,
            ProviderCapability.WEBHOOK_SUPPORT,
            ProviderCapability.SANDBOX_MODE
        ],
        "tiers": [ProviderTier.BASIC, ProviderTier.PROFESSIONAL],
        "max_accounts_per_request": 5,
        "rate_limit_per_minute": 60,
        "webhook_retry_attempts": 3,
        "data_retention_days": 365
    },
    "stitch": {
        "supported_capabilities": [
            ProviderCapability.ACCOUNT_INFO,
            ProviderCapability.TRANSACTION_HISTORY, 
            ProviderCapability.REAL_TIME_NOTIFICATIONS,
            ProviderCapability.BALANCE_INQUIRY,
            ProviderCapability.ACCOUNT_VERIFICATION,
            ProviderCapability.BULK_OPERATIONS,
            ProviderCapability.WEBHOOK_SUPPORT,
            ProviderCapability.RATE_LIMITING,
            ProviderCapability.SANDBOX_MODE
        ],
        "tiers": [ProviderTier.PROFESSIONAL, ProviderTier.ENTERPRISE],
        "max_accounts_per_request": 50,
        "rate_limit_per_minute": 300,
        "webhook_retry_attempts": 5,
        "data_retention_days": 2555  # 7 years
    },
    "unified": {
        "supported_capabilities": [
            # Unified supports all capabilities through aggregation
            capability for capability in ProviderCapability
        ],
        "tiers": [tier for tier in ProviderTier],
        "max_accounts_per_request": 100,  # Aggregated limit
        "rate_limit_per_minute": 500,     # Combined limit
        "webhook_retry_attempts": 5,
        "data_retention_days": 2555
    }
}

# Nigerian bank coverage by provider
BANK_COVERAGE = {
    "mono": [
        "access_bank", "gtbank", "zenith_bank", "first_bank", 
        "uba", "fidelity_bank", "fcmb", "sterling_bank"
    ],
    "stitch": [
        "access_bank", "gtbank", "zenith_bank", "first_bank",
        "uba", "stanbic_ibtc", "standard_chartered", "ecobank",
        "union_bank", "wema_bank", "polaris_bank"
    ],
    "unified": [
        # Unified provides access to all banks through provider aggregation
        "all_supported_banks"
    ]
}

# Export key components
__all__ = [
    "ProviderCapability",
    "ProviderTier",
    "PROVIDER_CAPABILITIES", 
    "BANK_COVERAGE"
]