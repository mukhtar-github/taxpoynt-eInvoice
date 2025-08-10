"""
Stitch Open Banking Integration
===============================

Enterprise-grade open banking provider integration for large corporations.
Stitch provides enhanced enterprise features including bulk operations,
advanced webhook capabilities, and comprehensive audit trails.

Key Enterprise Features:
- Multi-account management for corporate entities
- Bulk transaction processing and reporting
- Advanced authentication with OAuth 2.0 + client certificates
- Enhanced webhook verification and retry logic
- Comprehensive audit trails and compliance reporting
- 7-year data retention for regulatory compliance
- Higher rate limits for enterprise operations

Components:
- StitchBankingConnector: Main connector orchestrating all operations
- StitchAuthHandler: Enterprise authentication with OAuth 2.0
- StitchTransactionFetcher: Bulk transaction processing
- StitchWebhookHandler: Enterprise webhook management
- StitchModels: Enterprise data models and schemas
- StitchExceptions: Stitch-specific error handling

Usage:
    from .connector import StitchBankingConnector
    
    config = {
        'client_id': 'your_client_id',
        'client_secret': 'your_client_secret',
        'environment': 'production',  # or 'sandbox'
        'webhook_secret': 'webhook_verification_secret',
        'enterprise_tier': True
    }
    
    async with StitchBankingConnector(config) as connector:
        accounts = await connector.get_enterprise_accounts()
        transactions = await connector.bulk_fetch_transactions(account_ids)
"""

from .connector import StitchBankingConnector
from .auth import StitchAuthHandler
from .transaction_fetcher import StitchTransactionFetcher
from .webhook_handler import StitchWebhookHandler
from .models import (
    StitchAccount,
    StitchTransaction,
    StitchWebhookEvent,
    StitchAccountLinkingResponse,
    StitchBulkOperationResult,
    StitchTransactionType,
    StitchAccountType
)
from .exceptions import (
    StitchAPIError,
    StitchAuthenticationError,
    StitchRateLimitError,
    StitchWebhookError,
    StitchBulkOperationError
)

__all__ = [
    'StitchBankingConnector',
    'StitchAuthHandler', 
    'StitchTransactionFetcher',
    'StitchWebhookHandler',
    'StitchAccount',
    'StitchTransaction',
    'StitchWebhookEvent',
    'StitchAccountLinkingResponse',
    'StitchBulkOperationResult',
    'StitchTransactionType',
    'StitchAccountType',
    'StitchAPIError',
    'StitchAuthenticationError',
    'StitchRateLimitError',
    'StitchWebhookError',
    'StitchBulkOperationError'
]