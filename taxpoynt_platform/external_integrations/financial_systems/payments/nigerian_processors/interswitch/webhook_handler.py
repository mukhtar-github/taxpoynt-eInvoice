"""
Interswitch Webhook Handler
==========================

Webhook processing for Interswitch transaction notifications with signature validation,
AI-based classification, and Universal Transaction Processor integration.

Specializes in interbank transfer and NIBSS infrastructure webhook events.
"""

import json
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

from .models import (
    InterswitchTransaction, InterswitchWebhookEvent, InterswitchTransactionType,
    InterswitchTransactionStatus, InterswitchCustomer
)
from .auth import InterswitchAuthManager
from .payment_processor import InterswitchPaymentProcessor, InterswitchConfig
from taxpoynt_platform.core_platform.monitoring.logging.service import LoggingService
from taxpoynt_platform.core_platform.transaction_processing.universal_processor import UniversalTransactionProcessor


class InterswitchWebhookEventType(Enum):
    """Interswitch webhook event types"""
    TRANSACTION_NOTIFICATION = "transaction.notification"
    TRANSACTION_STATUS_UPDATE = "transaction.status.update"
    INTERBANK_TRANSFER_COMPLETED = "interbank.transfer.completed"
    INTERBANK_TRANSFER_FAILED = "interbank.transfer.failed"
    NIBSS_NIP_NOTIFICATION = "nibss.nip.notification"
    RTGS_NOTIFICATION = "rtgs.notification"
    ACH_NOTIFICATION = "ach.notification"
    SETTLEMENT_NOTIFICATION = "settlement.notification"
    REVERSAL_NOTIFICATION = "reversal.notification"
    ACCOUNT_INQUIRY_RESPONSE = "account.inquiry.response"


@dataclass
class InterswitchWebhookConfig:
    """Configuration for Interswitch webhook processing"""
    client_secret: str
    validate_signatures: bool = True
    process_duplicates: bool = False
    enable_auto_retry: bool = True
    max_retry_attempts: int = 3
    enable_ai_classification: bool = True


class InterswitchWebhookHandler:
    """
    Interswitch webhook processor with Universal Transaction Processor integration
    
    Features:
    - Signature validation for security
    - Duplicate event detection
    - AI-based transaction classification
    - Universal Transaction Processor integration
    - Comprehensive error handling and retry logic
    """
    
    def __init__(
        self,
        config: InterswitchWebhookConfig,
        auth_manager: InterswitchAuthManager,
        payment_processor: InterswitchPaymentProcessor
    ):
        self.config = config
        self.auth_manager = auth_manager
        self.payment_processor = payment_processor
        
        # Initialize services
        self.logger = LoggingService().get_logger("interswitch_webhook")
        self.universal_processor = UniversalTransactionProcessor()
        
        # Event tracking
        self._processed_events = set()
        self._failed_events = {}
        
        # Event handlers mapping
        self._event_handlers = {
            InterswitchWebhookEventType.TRANSACTION_NOTIFICATION: self._handle_transaction_notification,
            InterswitchWebhookEventType.TRANSACTION_STATUS_UPDATE: self._handle_status_update,
            InterswitchWebhookEventType.INTERBANK_TRANSFER_COMPLETED: self._handle_interbank_completed,
            InterswitchWebhookEventType.INTERBANK_TRANSFER_FAILED: self._handle_interbank_failed,
            InterswitchWebhookEventType.NIBSS_NIP_NOTIFICATION: self._handle_nibss_nip,
            InterswitchWebhookEventType.RTGS_NOTIFICATION: self._handle_rtgs_notification,
            InterswitchWebhookEventType.ACH_NOTIFICATION: self._handle_ach_notification,
            InterswitchWebhookEventType.SETTLEMENT_NOTIFICATION: self._handle_settlement_notification,
            InterswitchWebhookEventType.REVERSAL_NOTIFICATION: self._handle_reversal_notification,
            InterswitchWebhookEventType.ACCOUNT_INQUIRY_RESPONSE: self._handle_account_inquiry
        }
    
    async def process_webhook(
        self,
        payload: str,
        headers: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Process incoming Interswitch webhook with full validation and processing
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
        Validate Interswitch webhook signature for security
        """
        try:
            signature = headers.get('X-Interswitch-Signature') or headers.get('x-interswitch-signature')
            timestamp = headers.get('X-Interswitch-Timestamp') or headers.get('x-interswitch-timestamp')
            
            if not signature or not timestamp:
                self.logger.warning("Missing signature or timestamp in webhook headers")
                return False
            
            return self.auth_manager.validate_webhook_signature(payload, signature, timestamp)
            
        except Exception as e:
            self.logger.error("Signature validation error", extra={'error': str(e)})
            return False
    
    async def _parse_webhook_payload(self, payload: str, headers: Dict[str, str]) -> Optional[InterswitchWebhookEvent]:
        """
        Parse webhook payload into structured event
        """
        try:
            data = json.loads(payload)
            
            return InterswitchWebhookEvent(
                event_id=data.get('event_id', f"interswitch_{datetime.utcnow().timestamp()}"),
                event_type=data.get('event_type', 'unknown'),
                timestamp=datetime.fromisoformat(data.get('timestamp', datetime.utcnow().isoformat())),
                data=data.get('data', {}),
                signature=headers.get('X-Interswitch-Signature')
            )
            
        except Exception as e:
            self.logger.error("Failed to parse webhook payload", extra={'error': str(e)})
            return None
    
    async def _is_duplicate_event(self, event: InterswitchWebhookEvent) -> bool:
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
    
    async def _process_webhook_event(self, event: InterswitchWebhookEvent) -> Dict[str, Any]:
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
    
    def _map_event_type(self, raw_event_type: str) -> InterswitchWebhookEventType:
        """Map raw event type to enum"""
        type_mapping = {
            'transaction.notification': InterswitchWebhookEventType.TRANSACTION_NOTIFICATION,
            'transaction_notification': InterswitchWebhookEventType.TRANSACTION_NOTIFICATION,
            'transaction.status.update': InterswitchWebhookEventType.TRANSACTION_STATUS_UPDATE,
            'transaction_status_update': InterswitchWebhookEventType.TRANSACTION_STATUS_UPDATE,
            'interbank.transfer.completed': InterswitchWebhookEventType.INTERBANK_TRANSFER_COMPLETED,
            'interbank_transfer_completed': InterswitchWebhookEventType.INTERBANK_TRANSFER_COMPLETED,
            'interbank.transfer.failed': InterswitchWebhookEventType.INTERBANK_TRANSFER_FAILED,
            'interbank_transfer_failed': InterswitchWebhookEventType.INTERBANK_TRANSFER_FAILED,
            'nibss.nip.notification': InterswitchWebhookEventType.NIBSS_NIP_NOTIFICATION,
            'nibss_nip_notification': InterswitchWebhookEventType.NIBSS_NIP_NOTIFICATION,
            'rtgs.notification': InterswitchWebhookEventType.RTGS_NOTIFICATION,
            'rtgs_notification': InterswitchWebhookEventType.RTGS_NOTIFICATION,
            'ach.notification': InterswitchWebhookEventType.ACH_NOTIFICATION,
            'ach_notification': InterswitchWebhookEventType.ACH_NOTIFICATION,
            'settlement.notification': InterswitchWebhookEventType.SETTLEMENT_NOTIFICATION,
            'reversal.notification': InterswitchWebhookEventType.REVERSAL_NOTIFICATION,
            'account.inquiry.response': InterswitchWebhookEventType.ACCOUNT_INQUIRY_RESPONSE
        }
        
        return type_mapping.get(raw_event_type, InterswitchWebhookEventType.TRANSACTION_NOTIFICATION)
    
    async def _handle_transaction_notification(self, event: InterswitchWebhookEvent) -> Dict[str, Any]:
        """
        Handle general transaction notification webhook
        """
        transaction_data = event.data.get('transaction', {})
        
        if not transaction_data:
            raise ValueError("Missing transaction data in notification")
        
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
    
    async def _handle_status_update(self, event: InterswitchWebhookEvent) -> Dict[str, Any]:
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
            processor='interswitch',
            transaction_id=transaction_id,
            new_status=new_status,
            webhook_data=event.data
        )
        
        return {
            'transaction_id': transaction_id,
            'new_status': new_status,
            'updated_at': event.timestamp.isoformat()
        }
    
    async def _handle_interbank_completed(self, event: InterswitchWebhookEvent) -> Dict[str, Any]:
        """
        Handle completed interbank transfer - Interswitch specialization
        """
        transfer_data = event.data.get('transfer', {})
        
        # Create specialized interbank transfer transaction
        transaction = await self._create_interbank_transaction(transfer_data, completed=True)
        
        # Apply AI classification
        if self.config.enable_ai_classification:
            transaction = await self.payment_processor._apply_ai_classification(transaction)
        
        # Send to Universal Transaction Processor
        await self._send_to_universal_processor(transaction, event)
        
        return {
            'transfer_id': transaction.transaction_id,
            'originating_bank': transaction.originating_bank_name,
            'destination_bank': transaction.destination_bank_name,
            'amount': float(transaction.amount),
            'status': 'completed',
            'settlement_id': transaction.settlement_id
        }
    
    async def _handle_interbank_failed(self, event: InterswitchWebhookEvent) -> Dict[str, Any]:
        """
        Handle failed interbank transfer
        """
        transfer_data = event.data.get('transfer', {})
        failure_reason = event.data.get('failure_reason', 'Unknown error')
        
        # Create failed transfer transaction
        transaction = await self._create_interbank_transaction(transfer_data, completed=False)
        transaction.status = InterswitchTransactionStatus.FAILED
        
        # Add failure metadata
        transaction.interswitch_metadata['failure_reason'] = failure_reason
        transaction.interswitch_metadata['failed_at'] = event.timestamp.isoformat()
        
        # Send to Universal Transaction Processor
        await self._send_to_universal_processor(transaction, event)
        
        return {
            'transfer_id': transaction.transaction_id,
            'status': 'failed',
            'failure_reason': failure_reason
        }
    
    async def _handle_nibss_nip(self, event: InterswitchWebhookEvent) -> Dict[str, Any]:
        """
        Handle NIBSS NIP (Instant Payment) notification
        """
        nip_data = event.data.get('nip_transaction', {})
        
        # Create NIP transaction
        transaction = await self._create_nip_transaction(nip_data)
        
        # Apply AI classification
        if self.config.enable_ai_classification:
            transaction = await self.payment_processor._apply_ai_classification(transaction)
        
        # Send to Universal Transaction Processor
        await self._send_to_universal_processor(transaction, event)
        
        return {
            'nip_transaction_id': transaction.transaction_id,
            'nip_session_id': transaction.nip_session_id,
            'amount': float(transaction.amount),
            'status': transaction.status.value
        }
    
    async def _handle_rtgs_notification(self, event: InterswitchWebhookEvent) -> Dict[str, Any]:
        """
        Handle RTGS (Real Time Gross Settlement) notification
        """
        rtgs_data = event.data.get('rtgs_transaction', {})
        
        # Create RTGS transaction
        transaction = await self._create_rtgs_transaction(rtgs_data)
        
        # Apply AI classification
        if self.config.enable_ai_classification:
            transaction = await self.payment_processor._apply_ai_classification(transaction)
        
        # Send to Universal Transaction Processor
        await self._send_to_universal_processor(transaction, event)
        
        return {
            'rtgs_transaction_id': transaction.transaction_id,
            'settlement_id': transaction.settlement_id,
            'amount': float(transaction.amount),
            'value_date': transaction.value_date.isoformat() if transaction.value_date else None
        }
    
    async def _handle_ach_notification(self, event: InterswitchWebhookEvent) -> Dict[str, Any]:
        """
        Handle ACH (Automated Clearing House) notification
        """
        ach_data = event.data.get('ach_transaction', {})
        
        # Create ACH transaction
        transaction = await self._create_ach_transaction(ach_data)
        
        # Apply AI classification
        if self.config.enable_ai_classification:
            transaction = await self.payment_processor._apply_ai_classification(transaction)
        
        # Send to Universal Transaction Processor
        await self._send_to_universal_processor(transaction, event)
        
        return {
            'ach_transaction_id': transaction.transaction_id,
            'settlement_date': transaction.settlement_date.isoformat() if transaction.settlement_date else None,
            'amount': float(transaction.amount)
        }
    
    async def _handle_settlement_notification(self, event: InterswitchWebhookEvent) -> Dict[str, Any]:
        """
        Handle settlement notification
        """
        settlement_data = event.data.get('settlement', {})
        
        # Log settlement information for reconciliation
        self.logger.info("Settlement notification received", extra={
            'settlement_id': settlement_data.get('settlement_id'),
            'settlement_amount': settlement_data.get('total_amount'),
            'transaction_count': settlement_data.get('transaction_count'),
            'settlement_date': settlement_data.get('settlement_date')
        })
        
        return {
            'settlement_id': settlement_data.get('settlement_id'),
            'total_amount': settlement_data.get('total_amount'),
            'transaction_count': settlement_data.get('transaction_count'),
            'settlement_date': settlement_data.get('settlement_date')
        }
    
    async def _handle_reversal_notification(self, event: InterswitchWebhookEvent) -> Dict[str, Any]:
        """
        Handle transaction reversal notification
        """
        reversal_data = event.data.get('reversal', {})
        original_transaction_id = reversal_data.get('original_transaction_id')
        
        # Create reversal transaction
        transaction = await self._create_reversal_transaction(reversal_data)
        
        # Send to Universal Transaction Processor
        await self._send_to_universal_processor(transaction, event)
        
        return {
            'reversal_id': transaction.transaction_id,
            'original_transaction_id': original_transaction_id,
            'amount': float(transaction.amount),
            'status': 'reversed'
        }
    
    async def _handle_account_inquiry(self, event: InterswitchWebhookEvent) -> Dict[str, Any]:
        """
        Handle account inquiry response
        """
        inquiry_data = event.data.get('inquiry', {})
        
        # Log account inquiry result
        self.logger.info("Account inquiry response", extra={
            'account_number': inquiry_data.get('account_number', '')[-4:],  # Only last 4 digits
            'bank_code': inquiry_data.get('bank_code'),
            'account_name': inquiry_data.get('account_name'),
            'inquiry_successful': inquiry_data.get('successful', False)
        })
        
        return {
            'account_number': inquiry_data.get('account_number'),
            'bank_code': inquiry_data.get('bank_code'),
            'account_name': inquiry_data.get('account_name'),
            'successful': inquiry_data.get('successful', False)
        }
    
    async def _create_transaction_from_webhook(self, transaction_data: Dict) -> InterswitchTransaction:
        """
        Create InterswitchTransaction from webhook data
        """
        return await self.payment_processor._create_transaction_from_raw(transaction_data)
    
    async def _create_interbank_transaction(self, transfer_data: Dict, completed: bool) -> InterswitchTransaction:
        """
        Create interbank transfer transaction from webhook data
        """
        from decimal import Decimal
        
        transaction = InterswitchTransaction(
            transaction_id=transfer_data.get('id', f"interbank_{datetime.utcnow().timestamp()}"),
            reference=transfer_data.get('reference', transfer_data.get('id')),
            amount=Decimal(str(transfer_data.get('amount', '0'))),
            currency=transfer_data.get('currency', 'NGN'),
            transaction_type=InterswitchTransactionType.INTERBANK_TRANSFER,
            status=InterswitchTransactionStatus.COMPLETED if completed else InterswitchTransactionStatus.PENDING,
            description=transfer_data.get('description', 'Interbank transfer'),
            originating_bank_code=transfer_data.get('originating_bank_code'),
            destination_bank_code=transfer_data.get('destination_bank_code'),
            originating_account=transfer_data.get('originating_account'),
            destination_account=transfer_data.get('destination_account'),
            originating_bank_name=transfer_data.get('originating_bank_name'),
            destination_bank_name=transfer_data.get('destination_bank_name'),
            settlement_id=transfer_data.get('settlement_id'),
            interswitch_metadata=transfer_data
        )
        
        return transaction
    
    async def _create_nip_transaction(self, nip_data: Dict) -> InterswitchTransaction:
        """
        Create NIBSS NIP transaction from webhook data
        """
        from decimal import Decimal
        
        transaction = InterswitchTransaction(
            transaction_id=nip_data.get('id', f"nip_{datetime.utcnow().timestamp()}"),
            reference=nip_data.get('reference', nip_data.get('id')),
            amount=Decimal(str(nip_data.get('amount', '0'))),
            currency=nip_data.get('currency', 'NGN'),
            transaction_type=InterswitchTransactionType.NIBSS_INSTANT_PAYMENT,
            status=InterswitchTransactionStatus.SUCCESSFUL,
            description=nip_data.get('description', 'NIBSS Instant Payment'),
            originating_bank_code=nip_data.get('originating_bank_code'),
            destination_bank_code=nip_data.get('destination_bank_code'),
            originating_account=nip_data.get('originating_account'),
            destination_account=nip_data.get('destination_account'),
            nip_session_id=nip_data.get('nip_session_id'),
            nibss_session_id=nip_data.get('nibss_session_id'),
            interswitch_metadata=nip_data
        )
        
        return transaction
    
    async def _create_rtgs_transaction(self, rtgs_data: Dict) -> InterswitchTransaction:
        """
        Create RTGS transaction from webhook data
        """
        from decimal import Decimal
        
        transaction = InterswitchTransaction(
            transaction_id=rtgs_data.get('id', f"rtgs_{datetime.utcnow().timestamp()}"),
            reference=rtgs_data.get('reference', rtgs_data.get('id')),
            amount=Decimal(str(rtgs_data.get('amount', '0'))),
            currency=rtgs_data.get('currency', 'NGN'),
            transaction_type=InterswitchTransactionType.RTGS_TRANSFER,
            status=InterswitchTransactionStatus.SETTLED,
            description=rtgs_data.get('description', 'RTGS Transfer'),
            originating_bank_code=rtgs_data.get('originating_bank_code'),
            destination_bank_code=rtgs_data.get('destination_bank_code'),
            originating_account=rtgs_data.get('originating_account'),
            destination_account=rtgs_data.get('destination_account'),
            settlement_id=rtgs_data.get('settlement_id'),
            value_date=datetime.fromisoformat(rtgs_data['value_date']) if rtgs_data.get('value_date') else None,
            settlement_date=datetime.fromisoformat(rtgs_data['settlement_date']) if rtgs_data.get('settlement_date') else None,
            interswitch_metadata=rtgs_data
        )
        
        return transaction
    
    async def _create_ach_transaction(self, ach_data: Dict) -> InterswitchTransaction:
        """
        Create ACH transaction from webhook data
        """
        from decimal import Decimal
        
        transaction = InterswitchTransaction(
            transaction_id=ach_data.get('id', f"ach_{datetime.utcnow().timestamp()}"),
            reference=ach_data.get('reference', ach_data.get('id')),
            amount=Decimal(str(ach_data.get('amount', '0'))),
            currency=ach_data.get('currency', 'NGN'),
            transaction_type=InterswitchTransactionType.ACH_TRANSFER,
            status=InterswitchTransactionStatus.SETTLED,
            description=ach_data.get('description', 'ACH Transfer'),
            originating_bank_code=ach_data.get('originating_bank_code'),
            destination_bank_code=ach_data.get('destination_bank_code'),
            originating_account=ach_data.get('originating_account'),
            destination_account=ach_data.get('destination_account'),
            settlement_date=datetime.fromisoformat(ach_data['settlement_date']) if ach_data.get('settlement_date') else None,
            interswitch_metadata=ach_data
        )
        
        return transaction
    
    async def _create_reversal_transaction(self, reversal_data: Dict) -> InterswitchTransaction:
        """
        Create reversal transaction from webhook data
        """
        from decimal import Decimal
        
        transaction = InterswitchTransaction(
            transaction_id=reversal_data.get('id', f"reversal_{datetime.utcnow().timestamp()}"),
            reference=reversal_data.get('reference', reversal_data.get('id')),
            amount=Decimal(str(reversal_data.get('amount', '0'))),
            currency=reversal_data.get('currency', 'NGN'),
            transaction_type=InterswitchTransactionType.INTERBANK_TRANSFER,  # Reversal as transfer
            status=InterswitchTransactionStatus.REVERSED,
            description=f"Reversal for {reversal_data.get('original_transaction_id')}",
            originating_bank_code=reversal_data.get('originating_bank_code'),
            destination_bank_code=reversal_data.get('destination_bank_code'),
            interswitch_metadata=reversal_data
        )
        
        return transaction
    
    async def _send_to_universal_processor(self, transaction: InterswitchTransaction, event: InterswitchWebhookEvent):
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
                'processor': 'interswitch'
            })
            
        except Exception as e:
            self.logger.error("Failed to send to Universal Processor", extra={
                'transaction_id': transaction.transaction_id,
                'error': str(e)
            })
            raise
    
    async def _schedule_retry(self, event: InterswitchWebhookEvent, error: str):
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
    'InterswitchWebhookEventType',
    'InterswitchWebhookConfig',
    'InterswitchWebhookHandler'
]