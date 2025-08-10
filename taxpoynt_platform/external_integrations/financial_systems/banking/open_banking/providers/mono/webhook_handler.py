"""
Mono Webhook Handler
===================

Handles real-time webhook events from Mono Open Banking API.
Processes account updates, transaction notifications, and connection status changes.

Webhook Events:
- account.connected: New account linked
- account.updated: Account information updated
- transaction.created: New transaction received
- transaction.updated: Transaction information updated
- account.reauthorization_required: Account needs reauth
- account.disconnected: Account unlinked

Features:
- Signature verification for security
- Event deduplication
- Retry handling
- Nigerian banking compliance
- Automated invoice generation triggers
- Real-time notification dispatch

Architecture consistent with backend/app/utils/webhook_verification.py patterns.
"""

import asyncio
import hashlib
import hmac
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable, Set
from dataclasses import dataclass
from enum import Enum

from pydantic import ValidationError

from .models import (
    MonoWebhookPayload,
    MonoWebhookEventType,
    MonoTransaction,
    MonoAccount,
    MonoWebhookVerification
)
from .exceptions import (
    MonoWebhookError,
    MonoWebhookSignatureError,
    MonoInvalidEventError,
    MonoValidationError
)


logger = logging.getLogger(__name__)


class WebhookProcessingStatus(str, Enum):
    """Webhook processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    IGNORED = "ignored"


@dataclass
class WebhookEvent:
    """Processed webhook event with metadata"""
    event_id: str
    event_type: MonoWebhookEventType
    account_id: str
    data: Dict[str, Any]
    timestamp: datetime
    processing_status: WebhookProcessingStatus
    retry_count: int = 0
    error_message: Optional[str] = None
    processed_at: Optional[datetime] = None


@dataclass
class WebhookProcessingResult:
    """Result of webhook processing"""
    success: bool
    event_id: str
    message: str
    data: Optional[Dict[str, Any]] = None
    should_retry: bool = False
    retry_delay_seconds: int = 60


class MonoWebhookHandler:
    """
    Handles Mono webhook events with security, deduplication, and processing.
    
    Provides comprehensive webhook event processing with Nigerian banking
    compliance and automated invoice generation capabilities.
    """
    
    def __init__(
        self,
        webhook_secret: str,
        max_event_age_minutes: int = 15,
        enable_signature_verification: bool = True,
        max_retry_attempts: int = 3
    ):
        """
        Initialize webhook handler.
        
        Args:
            webhook_secret: Secret for webhook signature verification
            max_event_age_minutes: Maximum age of webhook events to accept
            enable_signature_verification: Whether to verify webhook signatures
            max_retry_attempts: Maximum retry attempts for failed processing
        """
        self.webhook_secret = webhook_secret
        self.max_event_age_minutes = max_event_age_minutes
        self.enable_signature_verification = enable_signature_verification
        self.max_retry_attempts = max_retry_attempts
        
        # Event handlers registry
        self.event_handlers: Dict[MonoWebhookEventType, List[Callable]] = {}
        
        # Event deduplication (in-memory, would use Redis in production)
        self.processed_events: Set[str] = set()
        self.event_timestamps: Dict[str, datetime] = {}
        
        # Processing statistics
        self.stats = {
            "total_events": 0,
            "successful_events": 0,
            "failed_events": 0,
            "ignored_events": 0,
            "signature_failures": 0
        }
        
        # Register default handlers
        self._register_default_handlers()
    
    def _register_default_handlers(self):
        """Register default event handlers"""
        self.register_handler(MonoWebhookEventType.ACCOUNT_CONNECTED, self._handle_account_connected)
        self.register_handler(MonoWebhookEventType.ACCOUNT_UPDATED, self._handle_account_updated)
        self.register_handler(MonoWebhookEventType.TRANSACTION_CREATED, self._handle_transaction_created)
        self.register_handler(MonoWebhookEventType.TRANSACTION_UPDATED, self._handle_transaction_updated)
        self.register_handler(MonoWebhookEventType.ACCOUNT_REAUTHORIZATION_REQUIRED, self._handle_reauth_required)
        self.register_handler(MonoWebhookEventType.ACCOUNT_DISCONNECTED, self._handle_account_disconnected)
    
    def register_handler(
        self,
        event_type: MonoWebhookEventType,
        handler: Callable[[WebhookEvent], WebhookProcessingResult]
    ):
        """
        Register a custom event handler.
        
        Args:
            event_type: Type of event to handle
            handler: Async function to handle the event
        """
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        
        self.event_handlers[event_type].append(handler)
        logger.info(f"Registered handler for event type: {event_type}")
    
    def verify_webhook_signature(
        self,
        payload: str,
        signature: str,
        timestamp: str
    ) -> bool:
        """
        Verify Mono webhook signature for security.
        
        Args:
            payload: Raw webhook payload string
            signature: Signature from webhook headers
            timestamp: Timestamp from webhook headers
            
        Returns:
            bool: True if signature is valid
        """
        if not self.enable_signature_verification:
            return True
        
        if not self.webhook_secret:
            logger.warning("Webhook secret not configured, skipping verification")
            return True
        
        try:
            # Mono webhook signature verification
            # Format may vary - adjust based on Mono's actual implementation
            expected_signature = hmac.new(
                self.webhook_secret.encode('utf-8'),
                f"{timestamp}.{payload}".encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            # Handle different signature formats
            signature_clean = signature.replace('sha256=', '') if signature.startswith('sha256=') else signature
            
            is_valid = hmac.compare_digest(signature_clean, expected_signature)
            
            if not is_valid:
                self.stats["signature_failures"] += 1
                logger.warning("Webhook signature verification failed")
            
            return is_valid
            
        except Exception as e:
            logger.error(f"Webhook signature verification error: {str(e)}")
            self.stats["signature_failures"] += 1
            return False
    
    def _is_event_too_old(self, timestamp: datetime) -> bool:
        """Check if webhook event is too old to process"""
        age_minutes = (datetime.utcnow() - timestamp).total_seconds() / 60
        return age_minutes > self.max_event_age_minutes
    
    def _is_duplicate_event(self, event_id: str) -> bool:
        """Check if event has already been processed"""
        return event_id in self.processed_events
    
    def _mark_event_processed(self, event_id: str):
        """Mark event as processed for deduplication"""
        self.processed_events.add(event_id)
        self.event_timestamps[event_id] = datetime.utcnow()
        
        # Clean up old events (keep only last hour)
        cutoff_time = datetime.utcnow() - timedelta(hours=1)
        old_events = [
            eid for eid, ts in self.event_timestamps.items()
            if ts < cutoff_time
        ]
        for eid in old_events:
            self.processed_events.discard(eid)
            self.event_timestamps.pop(eid, None)
    
    async def process_webhook(
        self,
        payload: str,
        signature: str,
        timestamp: str,
        headers: Optional[Dict[str, str]] = None
    ) -> WebhookProcessingResult:
        """
        Process incoming webhook payload.
        
        Args:
            payload: Raw webhook payload string
            signature: Webhook signature for verification
            timestamp: Request timestamp
            headers: Optional HTTP headers
            
        Returns:
            WebhookProcessingResult with processing status
        """
        try:
            self.stats["total_events"] += 1
            
            # Verify webhook signature
            if not self.verify_webhook_signature(payload, signature, timestamp):
                raise MonoWebhookSignatureError("Webhook signature verification failed")
            
            # Parse webhook payload
            try:
                payload_data = json.loads(payload)
                webhook_payload = MonoWebhookPayload(**payload_data)
            except (json.JSONDecodeError, ValidationError) as e:
                raise MonoInvalidEventError(
                    event_type="unknown",
                    message=f"Invalid webhook payload format: {str(e)}"
                )
            
            # Generate event ID for deduplication
            event_id = self._generate_event_id(webhook_payload)
            
            # Check for duplicate events
            if self._is_duplicate_event(event_id):
                self.stats["ignored_events"] += 1
                return WebhookProcessingResult(
                    success=True,
                    event_id=event_id,
                    message="Duplicate event ignored"
                )
            
            # Check event age
            if self._is_event_too_old(webhook_payload.timestamp):
                self.stats["ignored_events"] += 1
                return WebhookProcessingResult(
                    success=True,
                    event_id=event_id,
                    message="Event too old, ignored"
                )
            
            # Create webhook event
            webhook_event = WebhookEvent(
                event_id=event_id,
                event_type=webhook_payload.event,
                account_id=webhook_payload.account,
                data=webhook_payload.data,
                timestamp=webhook_payload.timestamp,
                processing_status=WebhookProcessingStatus.PENDING
            )
            
            # Process the event
            result = await self._process_event(webhook_event)
            
            # Mark as processed if successful
            if result.success:
                self._mark_event_processed(event_id)
                self.stats["successful_events"] += 1
            else:
                self.stats["failed_events"] += 1
            
            return result
            
        except MonoWebhookError as e:
            logger.error(f"Webhook processing error: {str(e)}")
            self.stats["failed_events"] += 1
            return WebhookProcessingResult(
                success=False,
                event_id="unknown",
                message=str(e),
                should_retry=False
            )
        except Exception as e:
            logger.error(f"Unexpected webhook processing error: {str(e)}", exc_info=True)
            self.stats["failed_events"] += 1
            return WebhookProcessingResult(
                success=False,
                event_id="unknown",
                message=f"Unexpected error: {str(e)}",
                should_retry=True
            )
    
    def _generate_event_id(self, webhook_payload: MonoWebhookPayload) -> str:
        """Generate unique event ID for deduplication"""
        # Combine event type, account, timestamp, and data hash
        data_hash = hashlib.md5(json.dumps(webhook_payload.data, sort_keys=True).encode()).hexdigest()[:8]
        timestamp_str = webhook_payload.timestamp.strftime("%Y%m%d%H%M%S")
        return f"{webhook_payload.event}_{webhook_payload.account}_{timestamp_str}_{data_hash}"
    
    async def _process_event(self, event: WebhookEvent) -> WebhookProcessingResult:
        """
        Process a webhook event using registered handlers.
        
        Args:
            event: WebhookEvent to process
            
        Returns:
            WebhookProcessingResult with processing outcome
        """
        event.processing_status = WebhookProcessingStatus.PROCESSING
        
        try:
            handlers = self.event_handlers.get(event.event_type, [])
            
            if not handlers:
                logger.warning(f"No handlers registered for event type: {event.event_type}")
                return WebhookProcessingResult(
                    success=True,
                    event_id=event.event_id,
                    message=f"No handlers for event type: {event.event_type}"
                )
            
            # Execute all handlers for this event type
            results = []
            for handler in handlers:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        result = await handler(event)
                    else:
                        result = handler(event)
                    results.append(result)
                except Exception as e:
                    logger.error(f"Handler error for {event.event_type}: {str(e)}", exc_info=True)
                    results.append(WebhookProcessingResult(
                        success=False,
                        event_id=event.event_id,
                        message=f"Handler failed: {str(e)}",
                        should_retry=True
                    ))
            
            # Determine overall success
            all_successful = all(r.success for r in results)
            any_retry_needed = any(r.should_retry for r in results)
            
            event.processing_status = WebhookProcessingStatus.COMPLETED if all_successful else WebhookProcessingStatus.FAILED
            event.processed_at = datetime.utcnow()
            
            return WebhookProcessingResult(
                success=all_successful,
                event_id=event.event_id,
                message=f"Processed {len(handlers)} handlers, {len([r for r in results if r.success])} successful",
                should_retry=any_retry_needed and not all_successful
            )
            
        except Exception as e:
            event.processing_status = WebhookProcessingStatus.FAILED
            event.error_message = str(e)
            logger.error(f"Event processing failed: {str(e)}", exc_info=True)
            
            return WebhookProcessingResult(
                success=False,
                event_id=event.event_id,
                message=f"Processing failed: {str(e)}",
                should_retry=True
            )
    
    # Default event handlers
    async def _handle_account_connected(self, event: WebhookEvent) -> WebhookProcessingResult:
        """Handle account connection events"""
        try:
            account_data = event.data
            account_id = event.account_id
            
            logger.info(f"Account connected: {account_id}")
            
            # Here you would typically:
            # 1. Update account status in database
            # 2. Trigger initial transaction sync
            # 3. Send notification to user
            # 4. Set up automated invoice monitoring
            
            return WebhookProcessingResult(
                success=True,
                event_id=event.event_id,
                message=f"Account connected successfully: {account_id}",
                data={"account_id": account_id, "status": "connected"}
            )
            
        except Exception as e:
            logger.error(f"Error handling account connected: {str(e)}")
            return WebhookProcessingResult(
                success=False,
                event_id=event.event_id,
                message=f"Failed to handle account connection: {str(e)}",
                should_retry=True
            )
    
    async def _handle_account_updated(self, event: WebhookEvent) -> WebhookProcessingResult:
        """Handle account update events"""
        try:
            account_id = event.account_id
            
            logger.info(f"Account updated: {account_id}")
            
            # Update account information in database
            # Refresh cached account data
            
            return WebhookProcessingResult(
                success=True,
                event_id=event.event_id,
                message=f"Account updated: {account_id}"
            )
            
        except Exception as e:
            return WebhookProcessingResult(
                success=False,
                event_id=event.event_id,
                message=f"Failed to handle account update: {str(e)}",
                should_retry=True
            )
    
    async def _handle_transaction_created(self, event: WebhookEvent) -> WebhookProcessingResult:
        """Handle new transaction events - critical for invoice generation"""
        try:
            account_id = event.account_id
            transaction_data = event.data
            
            logger.info(f"New transaction for account {account_id}: {transaction_data.get('id', 'unknown')}")
            
            # This is where automated invoice generation would be triggered
            # 1. Parse transaction data
            # 2. Check if transaction meets invoice criteria
            # 3. Generate invoice if needed
            # 4. Submit to FIRS if required
            # 5. Send notifications
            
            # For now, just log the transaction
            transaction_id = transaction_data.get("id")
            amount = transaction_data.get("amount", 0)
            transaction_type = transaction_data.get("type")
            narration = transaction_data.get("narration", "")
            
            # Check if this looks like a business transaction that needs invoicing
            needs_invoice = self._should_generate_invoice(transaction_data)
            
            result_data = {
                "account_id": account_id,
                "transaction_id": transaction_id,
                "amount": amount,
                "type": transaction_type,
                "narration": narration,
                "needs_invoice": needs_invoice
            }
            
            return WebhookProcessingResult(
                success=True,
                event_id=event.event_id,
                message=f"Transaction processed: {transaction_id}",
                data=result_data
            )
            
        except Exception as e:
            logger.error(f"Error handling transaction created: {str(e)}")
            return WebhookProcessingResult(
                success=False,
                event_id=event.event_id,
                message=f"Failed to handle new transaction: {str(e)}",
                should_retry=True
            )
    
    async def _handle_transaction_updated(self, event: WebhookEvent) -> WebhookProcessingResult:
        """Handle transaction update events"""
        try:
            account_id = event.account_id
            transaction_data = event.data
            
            logger.info(f"Transaction updated for account {account_id}")
            
            return WebhookProcessingResult(
                success=True,
                event_id=event.event_id,
                message="Transaction update processed"
            )
            
        except Exception as e:
            return WebhookProcessingResult(
                success=False,
                event_id=event.event_id,
                message=f"Failed to handle transaction update: {str(e)}",
                should_retry=True
            )
    
    async def _handle_reauth_required(self, event: WebhookEvent) -> WebhookProcessingResult:
        """Handle reauthorization required events"""
        try:
            account_id = event.account_id
            
            logger.warning(f"Reauthorization required for account: {account_id}")
            
            # 1. Update account status to require reauth
            # 2. Send notification to user
            # 3. Pause automated processes for this account
            
            return WebhookProcessingResult(
                success=True,
                event_id=event.event_id,
                message=f"Reauthorization flagged for account: {account_id}",
                data={"account_id": account_id, "status": "reauth_required"}
            )
            
        except Exception as e:
            return WebhookProcessingResult(
                success=False,
                event_id=event.event_id,
                message=f"Failed to handle reauth required: {str(e)}",
                should_retry=True
            )
    
    async def _handle_account_disconnected(self, event: WebhookEvent) -> WebhookProcessingResult:
        """Handle account disconnection events"""
        try:
            account_id = event.account_id
            
            logger.info(f"Account disconnected: {account_id}")
            
            # 1. Update account status
            # 2. Stop automated processes
            # 3. Archive transaction data per retention policy
            # 4. Send notification
            
            return WebhookProcessingResult(
                success=True,
                event_id=event.event_id,
                message=f"Account disconnected: {account_id}",
                data={"account_id": account_id, "status": "disconnected"}
            )
            
        except Exception as e:
            return WebhookProcessingResult(
                success=False,
                event_id=event.event_id,
                message=f"Failed to handle account disconnect: {str(e)}",
                should_retry=True
            )
    
    def _should_generate_invoice(self, transaction_data: Dict[str, Any]) -> bool:
        """
        Determine if a transaction should trigger invoice generation.
        
        Args:
            transaction_data: Transaction data from webhook
            
        Returns:
            bool: True if invoice should be generated
        """
        # Only consider credit transactions (money received)
        if transaction_data.get("type") != "credit":
            return False
        
        # Check minimum amount (e.g., NGN 1,000)
        amount = transaction_data.get("amount", 0)
        if amount < 100000:  # 1000 NGN in kobo
            return False
        
        # Check for business-related keywords
        narration = transaction_data.get("narration", "").lower()
        business_keywords = [
            "payment", "invoice", "service", "consultation", "project",
            "contract", "deposit", "installment", "fee", "subscription"
        ]
        
        has_business_keyword = any(keyword in narration for keyword in business_keywords)
        
        # Check for round amounts (often business transactions)
        amount_naira = amount / 100
        is_round_amount = (amount_naira % 1000 == 0) or (amount_naira % 500 == 0)
        
        return has_business_keyword or is_round_amount
    
    def get_stats(self) -> Dict[str, Any]:
        """Get webhook processing statistics"""
        return {
            **self.stats,
            "success_rate": (
                self.stats["successful_events"] / max(self.stats["total_events"], 1) * 100
            ),
            "processed_events_cache_size": len(self.processed_events)
        }


# Export webhook handler
__all__ = [
    "MonoWebhookHandler",
    "WebhookEvent",
    "WebhookProcessingResult",
    "WebhookProcessingStatus"
]