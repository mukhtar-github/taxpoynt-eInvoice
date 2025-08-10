"""
PalmPay Webhook Handler
======================

Webhook processing for PalmPay transaction notifications with signature validation,
AI-based classification, and Universal Transaction Processor integration.

Specializes in inter-bank transfer and mobile money webhook events.
"""

import json
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

from .models import (
    PalmPayTransaction, PalmPayWebhookEvent, PalmPayTransactionType,
    PalmPayTransactionStatus, PalmPayCustomer
)
from .auth import PalmPayAuthManager
from .payment_processor import PalmPayPaymentProcessor, PalmPayConfig
from taxpoynt_platform.core_platform.monitoring.logging.service import LoggingService
from taxpoynt_platform.core_platform.transaction_processing.universal_processor import UniversalTransactionProcessor


class PalmPayWebhookEventType(Enum):
    """PalmPay webhook event types"""
    PAYMENT_NOTIFICATION = "payment.notification"
    TRANSACTION_STATUS_UPDATE = "transaction.status.update"
    TRANSFER_COMPLETED = "transfer.completed"
    TRANSFER_FAILED = "transfer.failed"
    CUSTOMER_KYC_UPDATE = "customer.kyc.update"
    WALLET_CREDITED = "wallet.credited"
    WALLET_DEBITED = "wallet.debited"
    REFUND_PROCESSED = "refund.processed"


@dataclass
class PalmPayWebhookConfig:
    """Configuration for PalmPay webhook processing"""
    secret_key: str
    validate_signatures: bool = True
    process_duplicates: bool = False
    enable_auto_retry: bool = True
    max_retry_attempts: int = 3
    enable_ai_classification: bool = True


class PalmPayWebhookHandler:
    """
    PalmPay webhook processor with Universal Transaction Processor integration
    
    Features:
    - Signature validation for security
    - Duplicate event detection
    - AI-based transaction classification
    - Universal Transaction Processor integration
    - Comprehensive error handling and retry logic
    """
    
    def __init__(
        self,
        config: PalmPayWebhookConfig,
        auth_manager: PalmPayAuthManager,
        payment_processor: PalmPayPaymentProcessor
    ):
        self.config = config
        self.auth_manager = auth_manager
        self.payment_processor = payment_processor
        
        # Initialize services
        self.logger = LoggingService().get_logger("palmpay_webhook")
        self.universal_processor = UniversalTransactionProcessor()
        
        # Event tracking
        self._processed_events = set()
        self._failed_events = {}
        
        # Event handlers mapping
        self._event_handlers = {
            PalmPayWebhookEventType.PAYMENT_NOTIFICATION: self._handle_payment_notification,
            PalmPayWebhookEventType.TRANSACTION_STATUS_UPDATE: self._handle_status_update,
            PalmPayWebhookEventType.TRANSFER_COMPLETED: self._handle_transfer_completed,
            PalmPayWebhookEventType.TRANSFER_FAILED: self._handle_transfer_failed,
            PalmPayWebhookEventType.CUSTOMER_KYC_UPDATE: self._handle_kyc_update,
            PalmPayWebhookEventType.WALLET_CREDITED: self._handle_wallet_credited,
            PalmPayWebhookEventType.WALLET_DEBITED: self._handle_wallet_debited,
            PalmPayWebhookEventType.REFUND_PROCESSED: self._handle_refund_processed
        }
    
    async def process_webhook(
        self,
        payload: str,
        headers: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Process incoming PalmPay webhook with full validation and processing
        """
        processing_start = datetime.utcnow()
        
        try:
            # Validate webhook signature
            if self.config.validate_signatures:
                is_valid = await self._validate_webhook_signature(payload, headers)
                if not is_valid:
                    self.logger.warning("Invalid webhook signature", extra={
                        'headers': {k: v for k, v in headers.items() if k.lower() not in ['authorization', 'signature']}
                    })
                    return {'status': 'error', 'message': 'Invalid signature'}
            
            # Parse webhook payload
            webhook_event = await self._parse_webhook_payload(payload, headers)
            if not webhook_event:
                return {'status': 'error', 'message': 'Invalid payload format'}
            
            # Check for duplicate events
            if await self._is_duplicate_event(webhook_event):
                if not self.config.process_duplicates:
                    self.logger.info("Duplicate webhook event ignored", extra={
                        'event_id': webhook_event.event_id,
                        'event_type': webhook_event.event_type
                    })
                    return {'status': 'ignored', 'message': 'Duplicate event'}
            
            # Process the webhook event
            result = await self._process_webhook_event(webhook_event)
            
            # Track processing time
            processing_time = (datetime.utcnow() - processing_start).total_seconds()
            
            self.logger.info("Webhook processed successfully", extra={
                'event_id': webhook_event.event_id,
                'event_type': webhook_event.event_type,
                'processing_time': processing_time
            })
            
            return {
                'status': 'success',
                'event_id': webhook_event.event_id,
                'processing_time': processing_time,
                'result': result
            }
            
        except Exception as e:
            self.logger.error("Webhook processing failed", extra={
                'error': str(e),
                'payload_preview': payload[:200] if payload else None
            })
            
            return {
                'status': 'error',
                'message': str(e),
                'processing_time': (datetime.utcnow() - processing_start).total_seconds()
            }
    
    async def _validate_webhook_signature(self, payload: str, headers: Dict[str, str]) -> bool:
        """
        Validate PalmPay webhook signature for security
        """
        try:
            signature = headers.get('X-PalmPay-Signature') or headers.get('x-palmpay-signature')
            timestamp = headers.get('X-PalmPay-Timestamp') or headers.get('x-palmpay-timestamp')
            
            if not signature or not timestamp:
                self.logger.warning("Missing signature or timestamp in webhook headers")
                return False
            
            return self.auth_manager.validate_webhook_signature(payload, signature, timestamp)
            
        except Exception as e:
            self.logger.error("Signature validation error", extra={'error': str(e)})
            return False
    
    async def _parse_webhook_payload(self, payload: str, headers: Dict[str, str]) -> Optional[PalmPayWebhookEvent]:
        """
        Parse webhook payload into structured event
        """
        try:
            data = json.loads(payload)
            
            return PalmPayWebhookEvent(
                event_id=data.get('event_id', f"palmpay_{datetime.utcnow().timestamp()}"),
                event_type=data.get('event_type', 'unknown'),
                timestamp=datetime.fromisoformat(data.get('timestamp', datetime.utcnow().isoformat())),
                data=data.get('data', {}),
                signature=headers.get('X-PalmPay-Signature')
            )
            
        except Exception as e:
            self.logger.error("Failed to parse webhook payload", extra={'error': str(e)})
            return None
    
    async def _is_duplicate_event(self, event: PalmPayWebhookEvent) -> bool:
        """
        Check if this webhook event has been processed before
        """
        event_key = f"{event.event_type}:{event.event_id}"
        
        if event_key in self._processed_events:
            return True
        
        # Add to processed events (with size limit)
        self._processed_events.add(event_key)
        if len(self._processed_events) > 10000:  # Keep last 10k events
            # Remove oldest 1000 events
            old_events = list(self._processed_events)[:1000]
            for old_event in old_events:
                self._processed_events.discard(old_event)
        
        return False
    
    async def _process_webhook_event(self, event: PalmPayWebhookEvent) -> Dict[str, Any]:
        """
        Route webhook event to appropriate handler
        """
        try:
            # Map event type
            event_type = self._map_event_type(event.event_type)
            
            # Get handler
            handler = self._event_handlers.get(event_type)
            if not handler:
                self.logger.warning("No handler for event type", extra={
                    'event_type': event.event_type,
                    'event_id': event.event_id
                })
                return {'status': 'unhandled', 'event_type': event.event_type}
            
            # Process event
            return await handler(event)
            
        except Exception as e:
            self.logger.error("Event processing failed", extra={
                'event_id': event.event_id,
                'event_type': event.event_type,
                'error': str(e)
            })
            
            # Track failed event for retry
            if self.config.enable_auto_retry:
                await self._schedule_retry(event, str(e))
            
            raise
    
    def _map_event_type(self, raw_event_type: str) -> PalmPayWebhookEventType:
        """Map raw event type to enum"""
        type_mapping = {
            'payment.notification': PalmPayWebhookEventType.PAYMENT_NOTIFICATION,
            'payment_notification': PalmPayWebhookEventType.PAYMENT_NOTIFICATION,
            'transaction.status.update': PalmPayWebhookEventType.TRANSACTION_STATUS_UPDATE,
            'transaction_status_update': PalmPayWebhookEventType.TRANSACTION_STATUS_UPDATE,
            'transfer.completed': PalmPayWebhookEventType.TRANSFER_COMPLETED,
            'transfer_completed': PalmPayWebhookEventType.TRANSFER_COMPLETED,
            'transfer.failed': PalmPayWebhookEventType.TRANSFER_FAILED,
            'transfer_failed': PalmPayWebhookEventType.TRANSFER_FAILED,
            'customer.kyc.update': PalmPayWebhookEventType.CUSTOMER_KYC_UPDATE,
            'wallet.credited': PalmPayWebhookEventType.WALLET_CREDITED,
            'wallet.debited': PalmPayWebhookEventType.WALLET_DEBITED,
            'refund.processed': PalmPayWebhookEventType.REFUND_PROCESSED
        }
        
        return type_mapping.get(raw_event_type, PalmPayWebhookEventType.PAYMENT_NOTIFICATION)
    
    async def _handle_payment_notification(self, event: PalmPayWebhookEvent) -> Dict[str, Any]:
        """
        Handle payment notification webhook - most common PalmPay event
        """
        transaction_data = event.data.get('transaction', {})
        
        if not transaction_data:
            raise ValueError("Missing transaction data in payment notification")
        
        # Create transaction object
        transaction = await self._create_transaction_from_webhook(transaction_data)
        
        # Apply AI classification if enabled
        if self.config.enable_ai_classification:
            transaction = await self.payment_processor._apply_ai_classification(transaction)
        
        # Send to Universal Transaction Processor
        await self._send_to_universal_processor(transaction, event)
        
        return {
            'transaction_id': transaction.transaction_id,
            'status': transaction.status.value,
            'amount': float(transaction.amount),
            'business_category': transaction.business_category
        }
    
    async def _handle_status_update(self, event: PalmPayWebhookEvent) -> Dict[str, Any]:
        """
        Handle transaction status update webhook
        """
        transaction_data = event.data.get('transaction', {})
        transaction_id = transaction_data.get('id') or event.data.get('transaction_id')
        new_status = transaction_data.get('status') or event.data.get('status')
        
        if not transaction_id or not new_status:
            raise ValueError("Missing transaction ID or status in update event")
        
        # Update transaction status in Universal Processor
        await self.universal_processor.update_transaction_status(
            processor='palmpay',
            transaction_id=transaction_id,
            new_status=new_status,
            webhook_data=event.data
        )
        
        return {
            'transaction_id': transaction_id,
            'new_status': new_status,
            'updated_at': event.timestamp.isoformat()
        }
    
    async def _handle_transfer_completed(self, event: PalmPayWebhookEvent) -> Dict[str, Any]:
        """
        Handle completed inter-bank transfer - PalmPay specialization
        """
        transfer_data = event.data.get('transfer', {})
        
        # Create specialized inter-bank transfer transaction
        transaction = await self._create_transfer_transaction(transfer_data, completed=True)
        
        # Apply AI classification
        if self.config.enable_ai_classification:
            transaction = await self.payment_processor._apply_ai_classification(transaction)
        
        # Send to Universal Transaction Processor
        await self._send_to_universal_processor(transaction, event)
        
        return {
            'transfer_id': transaction.transaction_id,
            'sender_bank': transaction.sender_bank,
            'receiver_bank': transaction.receiver_bank,
            'amount': float(transaction.amount),
            'status': 'completed'
        }
    
    async def _handle_transfer_failed(self, event: PalmPayWebhookEvent) -> Dict[str, Any]:
        """
        Handle failed inter-bank transfer
        """
        transfer_data = event.data.get('transfer', {})
        failure_reason = event.data.get('failure_reason', 'Unknown error')
        
        # Create failed transfer transaction
        transaction = await self._create_transfer_transaction(transfer_data, completed=False)
        transaction.status = PalmPayTransactionStatus.FAILED
        
        # Add failure metadata
        transaction.palmpay_metadata['failure_reason'] = failure_reason
        transaction.palmpay_metadata['failed_at'] = event.timestamp.isoformat()
        
        # Send to Universal Transaction Processor
        await self._send_to_universal_processor(transaction, event)
        
        return {
            'transfer_id': transaction.transaction_id,
            'status': 'failed',
            'failure_reason': failure_reason
        }
    
    async def _handle_kyc_update(self, event: PalmPayWebhookEvent) -> Dict[str, Any]:
        """
        Handle customer KYC status update
        """
        customer_data = event.data.get('customer', {})
        kyc_status = event.data.get('kyc_status')
        
        # Log KYC update for compliance tracking
        self.logger.info("Customer KYC status updated", extra={
            'customer_id': customer_data.get('id'),
            'kyc_status': kyc_status,
            'updated_at': event.timestamp.isoformat()
        })
        
        return {
            'customer_id': customer_data.get('id'),
            'kyc_status': kyc_status,
            'updated_at': event.timestamp.isoformat()
        }
    
    async def _handle_wallet_credited(self, event: PalmPayWebhookEvent) -> Dict[str, Any]:
        """
        Handle wallet credit notification
        """
        wallet_data = event.data.get('wallet', {})
        
        # Create wallet credit transaction
        transaction = await self._create_wallet_transaction(wallet_data, credit=True)
        
        # Send to Universal Transaction Processor
        await self._send_to_universal_processor(transaction, event)
        
        return {
            'wallet_id': wallet_data.get('id'),
            'amount': float(transaction.amount),
            'transaction_type': 'credit'
        }
    
    async def _handle_wallet_debited(self, event: PalmPayWebhookEvent) -> Dict[str, Any]:
        """
        Handle wallet debit notification
        """
        wallet_data = event.data.get('wallet', {})
        
        # Create wallet debit transaction
        transaction = await self._create_wallet_transaction(wallet_data, credit=False)
        
        # Send to Universal Transaction Processor
        await self._send_to_universal_processor(transaction, event)
        
        return {
            'wallet_id': wallet_data.get('id'),
            'amount': float(transaction.amount),
            'transaction_type': 'debit'
        }
    
    async def _handle_refund_processed(self, event: PalmPayWebhookEvent) -> Dict[str, Any]:
        """
        Handle refund processing notification
        """
        refund_data = event.data.get('refund', {})
        original_transaction_id = refund_data.get('original_transaction_id')
        
        # Create refund transaction
        transaction = await self._create_refund_transaction(refund_data)
        
        # Send to Universal Transaction Processor
        await self._send_to_universal_processor(transaction, event)
        
        return {
            'refund_id': transaction.transaction_id,
            'original_transaction_id': original_transaction_id,
            'amount': float(transaction.amount),
            'status': 'processed'
        }
    
    async def _create_transaction_from_webhook(self, transaction_data: Dict) -> PalmPayTransaction:
        """
        Create PalmPayTransaction from webhook data
        """
        return await self.payment_processor._create_transaction_from_raw(transaction_data)
    
    async def _create_transfer_transaction(self, transfer_data: Dict, completed: bool) -> PalmPayTransaction:
        """
        Create inter-bank transfer transaction from webhook data
        """
        from decimal import Decimal
        
        transaction = PalmPayTransaction(
            transaction_id=transfer_data.get('id', f"transfer_{datetime.utcnow().timestamp()}"),
            reference=transfer_data.get('reference', transfer_data.get('id')),
            amount=Decimal(str(transfer_data.get('amount', '0'))),
            currency=transfer_data.get('currency', 'NGN'),
            transaction_type=PalmPayTransactionType.INTER_BANK_TRANSFER,
            status=PalmPayTransactionStatus.SUCCESSFUL if completed else PalmPayTransactionStatus.PENDING,
            description=transfer_data.get('description', 'Inter-bank transfer'),
            sender_account=transfer_data.get('sender_account'),
            receiver_account=transfer_data.get('receiver_account'),
            sender_bank=transfer_data.get('sender_bank'),
            receiver_bank=transfer_data.get('receiver_bank'),
            session_id=transfer_data.get('session_id'),
            palmpay_metadata=transfer_data
        )
        
        return transaction
    
    async def _create_wallet_transaction(self, wallet_data: Dict, credit: bool) -> PalmPayTransaction:
        """
        Create wallet transaction from webhook data
        """
        from decimal import Decimal
        
        transaction = PalmPayTransaction(
            transaction_id=wallet_data.get('transaction_id', f"wallet_{datetime.utcnow().timestamp()}"),
            reference=wallet_data.get('reference', wallet_data.get('transaction_id')),
            amount=Decimal(str(wallet_data.get('amount', '0'))),
            currency=wallet_data.get('currency', 'NGN'),
            transaction_type=PalmPayTransactionType.CASH_IN if credit else PalmPayTransactionType.CASH_OUT,
            status=PalmPayTransactionStatus.SUCCESSFUL,
            description=f"Wallet {'credit' if credit else 'debit'}",
            customer_id=wallet_data.get('customer_id'),
            palmpay_metadata=wallet_data
        )
        
        return transaction
    
    async def _create_refund_transaction(self, refund_data: Dict) -> PalmPayTransaction:
        """
        Create refund transaction from webhook data
        """
        from decimal import Decimal
        
        transaction = PalmPayTransaction(
            transaction_id=refund_data.get('id', f"refund_{datetime.utcnow().timestamp()}"),
            reference=refund_data.get('reference', refund_data.get('id')),
            amount=Decimal(str(refund_data.get('amount', '0'))),
            currency=refund_data.get('currency', 'NGN'),
            transaction_type=PalmPayTransactionType.MONEY_TRANSFER,  # Refund as transfer
            status=PalmPayTransactionStatus.SUCCESSFUL,
            description=f"Refund for {refund_data.get('original_transaction_id')}",
            customer_id=refund_data.get('customer_id'),
            palmpay_metadata=refund_data
        )
        
        return transaction
    
    async def _send_to_universal_processor(self, transaction: PalmPayTransaction, event: PalmPayWebhookEvent):
        """
        Send processed transaction to Universal Transaction Processor
        """
        try:
            universal_data = transaction.to_universal_format()
            universal_data['webhook_event'] = {
                'event_id': event.event_id,
                'event_type': event.event_type,
                'timestamp': event.timestamp.isoformat()
            }
            
            await self.universal_processor.process_transaction(universal_data)
            
            self.logger.debug("Transaction sent to Universal Processor", extra={
                'transaction_id': transaction.transaction_id,
                'processor': 'palmpay'
            })
            
        except Exception as e:
            self.logger.error("Failed to send to Universal Processor", extra={
                'transaction_id': transaction.transaction_id,
                'error': str(e)
            })
            raise
    
    async def _schedule_retry(self, event: PalmPayWebhookEvent, error: str):
        """
        Schedule webhook event for retry
        """
        retry_key = f"{event.event_type}:{event.event_id}"
        
        if retry_key not in self._failed_events:
            self._failed_events[retry_key] = {
                'event': event,
                'attempts': 0,
                'last_error': error,
                'next_retry': datetime.utcnow()
            }
        
        retry_info = self._failed_events[retry_key]
        retry_info['attempts'] += 1
        retry_info['last_error'] = error
        
        if retry_info['attempts'] >= self.config.max_retry_attempts:
            self.logger.error("Max retry attempts exceeded", extra={
                'event_id': event.event_id,
                'attempts': retry_info['attempts']
            })
            del self._failed_events[retry_key]
        else:
            # Exponential backoff
            retry_delay = min(300, 30 * (2 ** retry_info['attempts']))  # Max 5 minutes
            retry_info['next_retry'] = datetime.utcnow() + timedelta(seconds=retry_delay)
            
            self.logger.info("Webhook scheduled for retry", extra={
                'event_id': event.event_id,
                'attempt': retry_info['attempts'],
                'next_retry': retry_info['next_retry'].isoformat()
            })
    
    async def process_retries(self):
        """
        Process failed webhook events that are ready for retry
        """
        current_time = datetime.utcnow()
        ready_for_retry = []
        
        for retry_key, retry_info in self._failed_events.items():
            if current_time >= retry_info['next_retry']:
                ready_for_retry.append(retry_key)
        
        for retry_key in ready_for_retry:
            retry_info = self._failed_events[retry_key]
            event = retry_info['event']
            
            try:
                self.logger.info("Retrying webhook event", extra={
                    'event_id': event.event_id,
                    'attempt': retry_info['attempts'] + 1
                })
                
                result = await self._process_webhook_event(event)
                
                # Success - remove from failed events
                del self._failed_events[retry_key]
                
                self.logger.info("Webhook retry successful", extra={
                    'event_id': event.event_id,
                    'final_attempt': retry_info['attempts'] + 1
                })
                
            except Exception as e:
                await self._schedule_retry(event, str(e))
    
    def get_webhook_statistics(self) -> Dict[str, Any]:
        """
        Get webhook processing statistics
        """
        return {
            'processed_events': len(self._processed_events),
            'failed_events': len(self._failed_events),
            'event_handlers': list(self._event_handlers.keys()),
            'configuration': {
                'validate_signatures': self.config.validate_signatures,
                'process_duplicates': self.config.process_duplicates,
                'enable_auto_retry': self.config.enable_auto_retry,
                'max_retry_attempts': self.config.max_retry_attempts
            }
        }


# Export for use in other modules
__all__ = [
    'PalmPayWebhookEventType',
    'PalmPayWebhookConfig',
    'PalmPayWebhookHandler'
]