"""
Mono Open Banking Connector
===========================

Main connector class that orchestrates all Mono API interactions.
Provides a unified interface for account linking, transaction processing,
webhook handling, and automated invoice generation.

Key Features:
- Account linking and management
- Transaction data retrieval and analysis
- Real-time webhook processing
- Automated invoice generation triggers
- Nigerian banking compliance
- FIRS integration readiness
- Comprehensive error handling and retry logic

Architecture:
- Follows TaxPoynt connector patterns from backend/app/integrations/
- Integrates auth, transaction_fetcher, and webhook_handler
- Provides high-level business logic for e-invoicing workflows

Usage:
    async with MonoConnector(config) as connector:
        # Link account
        link_response = await connector.initiate_account_linking(...)
        
        # Get transactions
        transactions = await connector.get_account_transactions(...)
        
        # Process webhooks
        result = await connector.process_webhook(...)
"""

import asyncio
import logging
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Dict, Any, List, Optional, Tuple, AsyncGenerator
from dataclasses import dataclass

from .auth import MonoAuthHandler
from .transaction_fetcher import MonoTransactionFetcher, TransactionBatch, TransactionSummary
from .webhook_handler import MonoWebhookHandler, WebhookProcessingResult
from .models import (
    MonoAccountLinkingResponse,
    MonoTransaction,
    MonoAccount,
    MonoIncome,
    MonoTransactionType,
    MonoConnectionStatus,
    MonoBusinessAccount
)
from .exceptions import (
    MonoBaseException,
    MonoConnectionError,
    MonoAuthenticationError,
    MonoValidationError,
    MonoConfigurationError
)


logger = logging.getLogger(__name__)


@dataclass
class MonoConfig:
    """Mono connector configuration"""
    secret_key: str
    app_id: str
    environment: str = "sandbox"  # "sandbox" or "production"
    webhook_secret: Optional[str] = None
    enable_webhook_verification: bool = True
    max_concurrent_requests: int = 3
    default_transaction_limit: int = 50
    auto_invoice_generation: bool = False
    invoice_min_amount: Decimal = Decimal("1000")  # Minimum NGN for invoice generation


@dataclass
class AccountLinkingSession:
    """Account linking session data"""
    session_id: str
    customer_name: str
    customer_email: str
    mono_url: str
    reference: str
    created_at: datetime
    expires_at: datetime
    status: str = "pending"
    account_id: Optional[str] = None


@dataclass
class InvoiceGenerationTrigger:
    """Data for triggering invoice generation"""
    account_id: str
    transaction_id: str
    transaction_amount: Decimal
    transaction_narration: str
    customer_info: Dict[str, Any]
    business_info: Dict[str, Any]
    needs_firs_submission: bool = True


class MonoConnector:
    """
    Main Mono Open Banking connector.
    
    Provides unified access to Mono API features with business logic
    for e-invoicing, FIRS compliance, and Nigerian banking integration.
    """
    
    def __init__(self, config: MonoConfig):
        """
        Initialize Mono connector.
        
        Args:
            config: MonoConfig with API credentials and settings
        """
        self.config = config
        
        # Validate configuration
        self._validate_config()
        
        # Initialize components
        self.auth_handler = MonoAuthHandler(
            secret_key=config.secret_key,
            app_id=config.app_id,
            environment=config.environment,
            webhook_secret=config.webhook_secret
        )
        
        self.transaction_fetcher = MonoTransactionFetcher(
            secret_key=config.secret_key,
            base_url=f"https://api.withmono.com",
            max_concurrent_requests=config.max_concurrent_requests
        )
        
        self.webhook_handler = MonoWebhookHandler(
            webhook_secret=config.webhook_secret or "",
            enable_signature_verification=config.enable_webhook_verification
        )
        
        # Business logic state
        self.active_sessions: Dict[str, AccountLinkingSession] = {}
        self.connected_accounts: Dict[str, MonoAccount] = {}
        self.invoice_triggers: List[InvoiceGenerationTrigger] = []
        
        # Statistics
        self.stats = {
            "accounts_linked": 0,
            "transactions_processed": 0,
            "invoices_generated": 0,
            "webhooks_processed": 0,
            "errors_encountered": 0
        }
        
        # Register custom webhook handlers if auto-invoice is enabled
        if config.auto_invoice_generation:
            self._setup_auto_invoice_handlers()
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.auth_handler.__aenter__()
        await self.transaction_fetcher.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.auth_handler.__aexit__(exc_type, exc_val, exc_tb)
        await self.transaction_fetcher.__aexit__(exc_type, exc_val, exc_tb)
    
    def _validate_config(self):
        """Validate connector configuration"""
        if not self.config.secret_key:
            raise MonoConfigurationError("Mono secret key is required")
        
        if not self.config.app_id:
            raise MonoConfigurationError("Mono app ID is required")
        
        if self.config.environment not in ["sandbox", "production"]:
            raise MonoConfigurationError("Environment must be 'sandbox' or 'production'")
        
        if self.config.auto_invoice_generation and not self.config.webhook_secret:
            logger.warning("Auto-invoice generation enabled but webhook secret not provided")
    
    def _setup_auto_invoice_handlers(self):
        """Setup webhook handlers for automatic invoice generation"""
        from .models import MonoWebhookEventType
        
        # Register transaction created handler for auto-invoicing
        self.webhook_handler.register_handler(
            MonoWebhookEventType.TRANSACTION_CREATED,
            self._auto_invoice_transaction_handler
        )
    
    # Account Linking Methods
    async def initiate_account_linking(
        self,
        customer_name: str,
        customer_email: str,
        redirect_url: str,
        customer_id: Optional[str] = None,
        reference: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AccountLinkingSession:
        """
        Initiate account linking process.
        
        Args:
            customer_name: Customer's full name
            customer_email: Customer's email address
            redirect_url: HTTPS URL for post-authentication redirect
            customer_id: Optional customer identifier
            reference: Optional unique reference
            metadata: Optional additional metadata
            
        Returns:
            AccountLinkingSession with linking details
            
        Raises:
            MonoAuthenticationError: Authentication failed
            MonoValidationError: Invalid parameters
            MonoConnectionError: API connection issues
        """
        try:
            logger.info(f"Initiating account linking for {customer_email}")
            
            # Initiate linking with Mono
            linking_response = await self.auth_handler.initiate_account_linking(
                customer_name=customer_name,
                customer_email=customer_email,
                redirect_url=redirect_url,
                customer_id=customer_id,
                reference=reference,
                meta_data=metadata
            )
            
            # Create session record
            session = AccountLinkingSession(
                session_id=linking_response.id,
                customer_name=customer_name,
                customer_email=customer_email,
                mono_url=linking_response.mono_url,
                reference=reference or linking_response.customer,
                created_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(hours=1),  # 1-hour expiry
                status="pending"
            )
            
            # Store session
            self.active_sessions[session.session_id] = session
            
            logger.info(f"Account linking session created: {session.session_id}")
            return session
            
        except MonoBaseException:
            self.stats["errors_encountered"] += 1
            raise
        except Exception as e:
            self.stats["errors_encountered"] += 1
            logger.error(f"Unexpected error in account linking: {str(e)}", exc_info=True)
            raise MonoConnectionError(f"Account linking failed: {str(e)}")
    
    async def get_account_info(self, account_id: str) -> Optional[MonoAccount]:
        """
        Get account information.
        
        Args:
            account_id: Mono account identifier
            
        Returns:
            MonoAccount with account details or None if not found
        """
        try:
            # Check cache first
            if account_id in self.connected_accounts:
                return self.connected_accounts[account_id]
            
            # Get from API (would need to implement in auth_handler)
            status = await self.auth_handler.get_account_status(account_id)
            
            # For now, return a basic account structure
            # In a real implementation, you'd fetch full account details
            logger.info(f"Retrieved account info for: {account_id}")
            return None  # Placeholder
            
        except Exception as e:
            logger.error(f"Error getting account info: {str(e)}")
            return None
    
    # Transaction Methods
    async def get_account_transactions(
        self,
        account_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        transaction_type: Optional[MonoTransactionType] = None,
        limit: int = 50,
        page: int = 1
    ) -> TransactionBatch:
        """
        Get transactions for an account.
        
        Args:
            account_id: Mono account identifier
            start_date: Start date for filtering
            end_date: End date for filtering
            transaction_type: Filter by transaction type
            limit: Number of transactions per page  
            page: Page number
            
        Returns:
            TransactionBatch with transactions and metadata
        """
        try:
            batch = await self.transaction_fetcher.get_account_transactions(
                account_id=account_id,
                start_date=start_date,
                end_date=end_date,
                transaction_type=transaction_type,
                limit=limit,
                page=page
            )
            
            self.stats["transactions_processed"] += len(batch.transactions)
            
            # Check for invoice generation opportunities
            if self.config.auto_invoice_generation:
                await self._check_transactions_for_invoicing(batch.transactions, account_id)
            
            return batch
            
        except MonoBaseException:
            self.stats["errors_encountered"] += 1
            raise
    
    async def get_transaction_summary(
        self,
        account_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> TransactionSummary:
        """
        Get transaction summary and statistics.
        
        Args:
            account_id: Mono account identifier
            start_date: Start date for analysis
            end_date: End date for analysis
            
        Returns:
            TransactionSummary with aggregated data
        """
        return await self.transaction_fetcher.get_transaction_summary(
            account_id=account_id,
            start_date=start_date,
            end_date=end_date
        )
    
    async def stream_all_transactions(
        self,
        account_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        max_transactions: Optional[int] = None
    ) -> AsyncGenerator[MonoTransaction, None]:
        """
        Stream all transactions for an account.
        
        Args:
            account_id: Mono account identifier
            start_date: Start date for filtering
            end_date: End date for filtering
            max_transactions: Maximum number to retrieve
            
        Yields:
            MonoTransaction: Individual transaction records
        """
        async for transaction in self.transaction_fetcher.get_all_account_transactions(
            account_id=account_id,
            start_date=start_date,
            end_date=end_date,
            max_transactions=max_transactions
        ):
            self.stats["transactions_processed"] += 1
            
            # Check for invoice generation if enabled
            if self.config.auto_invoice_generation:
                await self._check_single_transaction_for_invoicing(transaction, account_id)
            
            yield transaction
    
    # Webhook Methods
    async def process_webhook(
        self,
        payload: str,
        signature: str,
        timestamp: str,
        headers: Optional[Dict[str, str]] = None
    ) -> WebhookProcessingResult:
        """
        Process incoming webhook.
        
        Args:
            payload: Raw webhook payload
            signature: Webhook signature
            timestamp: Request timestamp
            headers: HTTP headers
            
        Returns:
            WebhookProcessingResult with processing status
        """
        result = await self.webhook_handler.process_webhook(
            payload=payload,
            signature=signature,
            timestamp=timestamp,
            headers=headers
        )
        
        self.stats["webhooks_processed"] += 1
        
        if not result.success:
            self.stats["errors_encountered"] += 1
        
        return result
    
    # Invoice Generation Methods
    async def _check_transactions_for_invoicing(
        self,
        transactions: List[MonoTransaction],
        account_id: str
    ):
        """Check transactions for invoice generation opportunities"""
        for transaction in transactions:
            await self._check_single_transaction_for_invoicing(transaction, account_id)
    
    async def _check_single_transaction_for_invoicing(
        self,
        transaction: MonoTransaction,
        account_id: str
    ):
        """Check a single transaction for invoice generation"""
        # Only process credit transactions (money received)
        if transaction.type != MonoTransactionType.CREDIT:
            return
        
        # Check minimum amount
        if transaction.amount_naira < self.config.invoice_min_amount:
            return
        
        # Check for business-related indicators
        narration_lower = transaction.narration.lower()
        business_keywords = [
            "payment", "invoice", "service", "consultation", "project",
            "contract", "deposit", "installment", "fee", "subscription"
        ]
        
        has_business_keyword = any(keyword in narration_lower for keyword in business_keywords)
        is_round_amount = (transaction.amount_naira % 1000 == 0) or (transaction.amount_naira % 500 == 0)
        
        if has_business_keyword or is_round_amount:
            # Create invoice generation trigger
            trigger = InvoiceGenerationTrigger(
                account_id=account_id,
                transaction_id=transaction.id,
                transaction_amount=transaction.amount_naira,
                transaction_narration=transaction.narration,
                customer_info={},  # Would be populated from account data
                business_info={}   # Would be populated from business account settings
            )
            
            self.invoice_triggers.append(trigger)
            logger.info(f"Invoice generation triggered for transaction: {transaction.id}")
    
    async def _auto_invoice_transaction_handler(self, event) -> WebhookProcessingResult:
        """Handle transaction created webhook for auto-invoicing"""
        try:
            transaction_data = event.data
            account_id = event.account_id
            
            # Check if this transaction needs an invoice
            amount = transaction_data.get("amount", 0) / 100  # Convert kobo to Naira
            transaction_type = transaction_data.get("type")
            narration = transaction_data.get("narration", "")
            
            if (transaction_type == "credit" and 
                Decimal(str(amount)) >= self.config.invoice_min_amount and
                self._should_generate_invoice_from_webhook(transaction_data)):
                
                # Create invoice trigger
                trigger = InvoiceGenerationTrigger(
                    account_id=account_id,
                    transaction_id=transaction_data.get("id", ""),
                    transaction_amount=Decimal(str(amount)),
                    transaction_narration=narration,
                    customer_info={},
                    business_info={}
                )
                
                self.invoice_triggers.append(trigger)
                self.stats["invoices_generated"] += 1
                
                logger.info(f"Auto-invoice triggered for transaction: {trigger.transaction_id}")
            
            return WebhookProcessingResult(
                success=True,
                event_id=event.event_id,
                message="Transaction processed for auto-invoicing"
            )
            
        except Exception as e:
            logger.error(f"Auto-invoice handler error: {str(e)}")
            return WebhookProcessingResult(
                success=False,
                event_id=event.event_id,
                message=f"Auto-invoice failed: {str(e)}",
                should_retry=True
            )
    
    def _should_generate_invoice_from_webhook(self, transaction_data: Dict[str, Any]) -> bool:
        """Determine if webhook transaction should generate invoice"""
        narration = transaction_data.get("narration", "").lower()
        business_keywords = [
            "payment", "invoice", "service", "consultation", "project",
            "contract", "deposit", "installment", "fee", "subscription"
        ]
        
        has_business_keyword = any(keyword in narration for keyword in business_keywords)
        
        # Check for round amounts
        amount = transaction_data.get("amount", 0) / 100
        is_round_amount = (amount % 1000 == 0) or (amount % 500 == 0)
        
        return has_business_keyword or is_round_amount
    
    # Business Account Management
    async def create_business_account(
        self,
        account_id: str,
        business_info: Dict[str, Any]
    ) -> MonoBusinessAccount:
        """
        Create business account profile for invoice generation.
        
        Args:
            account_id: Mono account identifier
            business_info: Business registration information
            
        Returns:
            MonoBusinessAccount with business details
        """
        try:
            business_account = MonoBusinessAccount(
                account_id=account_id,
                business_name=business_info["business_name"],
                business_email=business_info["business_email"],
                business_phone=business_info["business_phone"],
                business_address=business_info["business_address"],
                tax_identification_number=business_info.get("tin"),
                cac_registration_number=business_info.get("cac_number"),
                business_type=business_info["business_type"]
            )
            
            logger.info(f"Business account created for: {business_account.business_name}")
            return business_account
            
        except Exception as e:
            logger.error(f"Error creating business account: {str(e)}")
            raise MonoValidationError(f"Business account creation failed: {str(e)}")
    
    # Statistics and Monitoring
    def get_stats(self) -> Dict[str, Any]:
        """Get connector statistics"""
        webhook_stats = self.webhook_handler.get_stats()
        
        return {
            **self.stats,
            "webhook_stats": webhook_stats,
            "active_sessions": len(self.active_sessions),
            "connected_accounts": len(self.connected_accounts),
            "pending_invoice_triggers": len(self.invoice_triggers),
            "config": {
                "environment": self.config.environment,
                "auto_invoice_enabled": self.config.auto_invoice_generation,
                "webhook_verification_enabled": self.config.enable_webhook_verification
            }
        }
    
    def get_pending_invoice_triggers(self) -> List[InvoiceGenerationTrigger]:
        """Get pending invoice generation triggers"""
        return self.invoice_triggers.copy()
    
    def clear_processed_triggers(self, trigger_ids: List[str]):
        """Clear processed invoice triggers"""
        # In a real implementation, you'd remove specific triggers by ID
        self.invoice_triggers.clear()
        logger.info(f"Cleared {len(trigger_ids)} processed invoice triggers")
    
    # Health Check
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on Mono connector"""
        try:
            # Test API connectivity (you'd implement this)
            api_healthy = True  # Placeholder
            
            return {
                "status": "healthy" if api_healthy else "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "api_connectivity": api_healthy,
                "stats": self.get_stats(),
                "components": {
                    "auth_handler": "operational",
                    "transaction_fetcher": "operational", 
                    "webhook_handler": "operational"
                }
            }
            
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }


# Export main connector
__all__ = [
    "MonoConnector",
    "MonoConfig",
    "AccountLinkingSession",
    "InvoiceGenerationTrigger"
]