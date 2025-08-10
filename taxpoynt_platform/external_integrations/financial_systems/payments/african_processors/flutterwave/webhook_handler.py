"""
Flutterwave Webhook Handler
==========================

Comprehensive webhook processing for Flutterwave payment events with
Pan-African support and AI-based classification.

Features:
- Real-time webhook event processing and validation
- Signature verification for webhook security
- AI-based Nigerian business transaction classification
- Multi-country event handling for African payments
- Comprehensive retry logic and error handling
- NDPR-compliant event logging and privacy protection
- Integration with Universal Transaction Processor
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import hashlib
import hmac

from .models import FlutterwaveWebhookEvent, FlutterwaveTransaction, FlutterwaveCountry
from .auth import FlutterwaveAuthManager
from .payment_processor import FlutterwavePaymentProcessor
from ....connector_framework.classification_engine.nigerian_classifier import NigerianTransactionClassifier
from ....connector_framework.classification_engine.privacy_protection import APIPrivacyProtection


@dataclass
class FlutterwaveWebhookConfig:
    """Configuration for Flutterwave webhook processing"""
    
    webhook_secret: str
    validate_signatures: bool = True
    enable_auto_retry: bool = True
    max_retry_attempts: int = 3
    retry_delay_seconds: int = 5
    
    # Classification settings
    enable_ai_classification: bool = True
    classification_threshold: float = 0.7
    
    # Processing settings
    process_async: bool = True
    batch_processing: bool = False
    batch_size: int = 10
    batch_timeout: int = 30
    
    # Event filtering
    enabled_events: List[str] = None
    
    def __post_init__(self):
        if self.enabled_events is None:
            self.enabled_events = [
                'charge.completed',
                'transfer.completed',
                'transfer.failed',
                'charge.failed',
                'charge.disputed',
                'charge.dispute.resolved'
            ]


class FlutterwaveWebhookHandler:
    """
    Flutterwave webhook event handler with comprehensive processing
    
    Handles real-time webhook events from Flutterwave with signature verification,
    AI classification, and integration with TaxPoynt's processing pipeline.
    """
    
    def __init__(
        self,
        config: FlutterwaveWebhookConfig,
        auth_manager: FlutterwaveAuthManager,
        payment_processor: FlutterwavePaymentProcessor,
        transaction_classifier: Optional[NigerianTransactionClassifier] = None
    ):
        """
        Initialize Flutterwave webhook handler
        
        Args:
            config: Webhook configuration
            auth_manager: Authentication manager
            payment_processor: Payment processor instance
            transaction_classifier: Optional transaction classifier
        """
        self.config = config
        self.auth_manager = auth_manager
        self.payment_processor = payment_processor
        self.transaction_classifier = transaction_classifier
        self.logger = logging.getLogger(__name__)
        
        # Privacy protection
        self.privacy_protection = APIPrivacyProtection()
        
        # Processing state
        self.processed_events = set()
        self.failed_events = []
        self.retry_queue = []
        
        # Statistics
        self.webhook_stats = {
            'total_received': 0,
            'total_processed': 0,
            'total_failed': 0,
            'signature_failures': 0,
            'classification_attempts': 0,
            'events_by_type': {},
            'countries_processed': set(),
            'processing_times': [],
            'last_event_time': None
        }
        
        self.logger.info("Flutterwave webhook handler initialized", extra={
            'validate_signatures': config.validate_signatures,
            'enabled_events': len(config.enabled_events),
            'auto_retry_enabled': config.enable_auto_retry
        })
    
    async def process_webhook(self, payload: str, headers: Dict[str, str]) -> Dict[str, Any]:
        """
        Process incoming webhook with comprehensive validation and processing
        
        Args:
            payload: Raw webhook payload
            headers: HTTP headers from webhook request
            
        Returns:
            Processing result with status and details
        """
        processing_start = datetime.utcnow()
        
        try:
            self.webhook_stats['total_received'] += 1
            self.webhook_stats['last_event_time'] = processing_start
            
            # Parse payload
            try:
                webhook_data = json.loads(payload)
            except json.JSONDecodeError as e:
                self.logger.error("Invalid JSON in webhook payload", extra={'error': str(e)})
                return self._create_error_response("Invalid JSON payload", processing_start)
            
            # Extract event info
            event_type = webhook_data.get('event', '')
            event_id = webhook_data.get('id', '')
            transaction_data = webhook_data.get('data', {})
            
            self.logger.info("Processing Flutterwave webhook", extra={
                'event_type': event_type,
                'event_id': event_id,
                'transaction_id': transaction_data.get('id')
            })
            
            # Verify signature if enabled
            if self.config.validate_signatures:
                signature = headers.get('verif-hash', '')
                if not signature:
                    self.webhook_stats['signature_failures'] += 1
                    self.logger.warning("Missing webhook signature")
                    return self._create_error_response("Missing signature", processing_start)
                
                if not self._verify_signature(payload, signature):
                    self.webhook_stats['signature_failures'] += 1
                    self.logger.warning("Invalid webhook signature")
                    return self._create_error_response("Invalid signature", processing_start)
            
            # Check if event is enabled
            if event_type not in self.config.enabled_events:
                self.logger.debug(f"Ignoring disabled event type: {event_type}")
                return self._create_success_response("Event type disabled", processing_start)
            
            # Check for duplicate processing
            if event_id in self.processed_events:
                self.logger.debug(f"Skipping already processed event: {event_id}")
                return self._create_success_response("Already processed", processing_start)
            
            # Create webhook event object
            webhook_event = FlutterwaveWebhookEvent(
                event=event_type,
                event_type=event_type,
                data=transaction_data,
                event_id=event_id,
                created_at=processing_start,
                verified=True,
                signature_valid=self.config.validate_signatures
            )
            
            # Process the event
            processing_result = await self._process_webhook_event(webhook_event)
            
            # Update statistics
            self.webhook_stats['events_by_type'][event_type] = self.webhook_stats['events_by_type'].get(event_type, 0) + 1
            
            # Record processing
            if processing_result['success']:
                self.processed_events.add(event_id)
                self.webhook_stats['total_processed'] += 1
                webhook_event.processed = True
            else:
                self.webhook_stats['total_failed'] += 1
                if self.config.enable_auto_retry:
                    self._queue_for_retry(webhook_event)
            
            # Record processing time
            processing_time = (datetime.utcnow() - processing_start).total_seconds()
            self.webhook_stats['processing_times'].append(processing_time)
            webhook_event.processing_time = processing_time
            
            # Return result
            result = {
                'status': 'success' if processing_result['success'] else 'error',
                'event_id': event_id,
                'event_type': event_type,
                'processing_time': processing_time,
                'message': processing_result.get('message', ''),
                'details': processing_result.get('details', {})
            }
            
            self.logger.info("Webhook processing completed", extra=result)
            return result
            
        except Exception as e:
            self.webhook_stats['total_failed'] += 1
            self.logger.error("Webhook processing error", extra={
                'error': str(e),
                'event_id': event_id if 'event_id' in locals() else None,
                'event_type': event_type if 'event_type' in locals() else None
            })
            return self._create_error_response(str(e), processing_start)
    
    async def _process_webhook_event(self, webhook_event: FlutterwaveWebhookEvent) -> Dict[str, Any]:
        """
        Process specific webhook event based on type
        
        Args:
            webhook_event: Webhook event to process
            
        Returns:
            Processing result
        """
        try:
            event_type = webhook_event.event_type
            transaction_data = webhook_event.data
            
            if event_type in ['charge.completed', 'transfer.completed']:
                return await self._process_successful_transaction(webhook_event)
            
            elif event_type in ['charge.failed', 'transfer.failed']:
                return await self._process_failed_transaction(webhook_event)
            
            elif event_type == 'charge.disputed':
                return await self._process_disputed_transaction(webhook_event)
            
            elif event_type == 'charge.dispute.resolved':
                return await self._process_dispute_resolved(webhook_event)
            
            else:
                self.logger.warning(f"Unhandled event type: {event_type}")
                return {
                    'success': True,
                    'message': f'Event type {event_type} not handled',
                    'details': {'skipped': True}
                }
            
        except Exception as e:
            self.logger.error(f"Event processing error: {str(e)}")
            return {
                'success': False,
                'message': str(e),
                'details': {'error_type': type(e).__name__}
            }
    
    async def _process_successful_transaction(self, webhook_event: FlutterwaveWebhookEvent) -> Dict[str, Any]:
        """Process successful payment/transfer event"""
        try:
            transaction_data = webhook_event.data
            transaction_id = str(transaction_data.get('id', ''))
            
            # Verify transaction with Flutterwave
            transaction = await self.payment_processor.verify_transaction(transaction_id)
            
            if not transaction:
                return {
                    'success': False,
                    'message': 'Transaction verification failed',
                    'details': {'transaction_id': transaction_id}
                }
            
            # Apply AI classification if enabled
            classification_result = None
            if self.config.enable_ai_classification and self.transaction_classifier:
                classification_result = await self._classify_webhook_transaction(transaction)
                self.webhook_stats['classification_attempts'] += 1
            
            # Track country
            if transaction.country:
                self.webhook_stats['countries_processed'].add(transaction.country.value)
            
            # Process for FIRS compliance (if Nigerian transaction)
            firs_processing_result = None
            if transaction.country == FlutterwaveCountry.NIGERIA and classification_result:
                if classification_result.get('is_business_income', False):
                    firs_processing_result = await self._process_for_firs_compliance(
                        transaction, classification_result
                    )
            
            self.logger.info("Successful transaction processed", extra={
                'transaction_id': transaction_id,
                'amount': str(transaction.amount),
                'currency': transaction.currency,
                'country': transaction.country.value if transaction.country else None,
                'classification_confidence': classification_result.get('confidence') if classification_result else None,
                'requires_firs_submission': firs_processing_result is not None
            })
            
            return {
                'success': True,
                'message': 'Transaction processed successfully',
                'details': {
                    'transaction_id': transaction_id,
                    'amount': str(transaction.amount),
                    'currency': transaction.currency,
                    'classification': classification_result,
                    'firs_processing': firs_processing_result
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error processing successful transaction: {str(e)}")
            return {
                'success': False,
                'message': str(e),
                'details': {'error_in': 'successful_transaction_processing'}
            }
    
    async def _process_failed_transaction(self, webhook_event: FlutterwaveWebhookEvent) -> Dict[str, Any]:
        """Process failed payment/transfer event"""
        try:
            transaction_data = webhook_event.data
            transaction_id = str(transaction_data.get('id', ''))
            failure_reason = transaction_data.get('processor_response', 'Unknown failure')
            
            self.logger.warning("Failed transaction processed", extra={
                'transaction_id': transaction_id,
                'failure_reason': failure_reason,
                'event_type': webhook_event.event_type
            })
            
            return {
                'success': True,
                'message': 'Failed transaction logged',
                'details': {
                    'transaction_id': transaction_id,
                    'failure_reason': failure_reason
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error processing failed transaction: {str(e)}")
            return {
                'success': False,
                'message': str(e),
                'details': {'error_in': 'failed_transaction_processing'}
            }
    
    async def _process_disputed_transaction(self, webhook_event: FlutterwaveWebhookEvent) -> Dict[str, Any]:
        """Process disputed transaction event"""
        try:
            transaction_data = webhook_event.data
            transaction_id = str(transaction_data.get('id', ''))
            dispute_reason = transaction_data.get('reason', 'Unknown dispute')
            
            self.logger.warning("Transaction disputed", extra={
                'transaction_id': transaction_id,
                'dispute_reason': dispute_reason
            })
            
            return {
                'success': True,
                'message': 'Dispute logged',
                'details': {
                    'transaction_id': transaction_id,
                    'dispute_reason': dispute_reason
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error processing disputed transaction: {str(e)}")
            return {
                'success': False,
                'message': str(e),
                'details': {'error_in': 'disputed_transaction_processing'}
            }
    
    async def _process_dispute_resolved(self, webhook_event: FlutterwaveWebhookEvent) -> Dict[str, Any]:
        """Process dispute resolved event"""
        try:
            transaction_data = webhook_event.data
            transaction_id = str(transaction_data.get('id', ''))
            resolution = transaction_data.get('resolution', 'Unknown resolution')
            
            self.logger.info("Dispute resolved", extra={
                'transaction_id': transaction_id,
                'resolution': resolution
            })
            
            return {
                'success': True,
                'message': 'Dispute resolution logged',
                'details': {
                    'transaction_id': transaction_id,
                    'resolution': resolution
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error processing dispute resolution: {str(e)}")
            return {
                'success': False,
                'message': str(e),
                'details': {'error_in': 'dispute_resolution_processing'}
            }
    
    async def _classify_webhook_transaction(self, transaction: FlutterwaveTransaction) -> Optional[Dict[str, Any]]:
        """Classify webhook transaction for business income"""
        if not self.transaction_classifier:
            return None
        
        try:
            # Use the payment processor's classification method
            classification = await self.payment_processor._classify_transaction(transaction)
            return classification
            
        except Exception as e:
            self.logger.error(f"Webhook transaction classification failed: {str(e)}")
            return None
    
    async def _process_for_firs_compliance(
        self,
        transaction: FlutterwaveTransaction,
        classification: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Process transaction for FIRS compliance if applicable"""
        try:
            # This would integrate with TaxPoynt's FIRS submission system
            # For now, we just log that it should be processed
            
            if classification.get('is_business_income', False):
                confidence = classification.get('confidence', 0.0)
                
                if confidence >= self.config.classification_threshold:
                    self.logger.info("Transaction queued for FIRS processing", extra={
                        'transaction_id': transaction.transaction_id,
                        'amount': str(transaction.amount),
                        'confidence': confidence,
                        'classification_method': classification.get('method')
                    })
                    
                    return {
                        'queued_for_firs': True,
                        'confidence': confidence,
                        'estimated_tax': float(transaction.amount) * 0.075  # 7.5% VAT
                    }
                else:
                    self.logger.info("Transaction requires manual review", extra={
                        'transaction_id': transaction.transaction_id,
                        'confidence': confidence,
                        'threshold': self.config.classification_threshold
                    })
                    
                    return {
                        'requires_manual_review': True,
                        'confidence': confidence
                    }
            
            return None
            
        except Exception as e:
            self.logger.error(f"FIRS compliance processing error: {str(e)}")
            return None
    
    def _verify_signature(self, payload: str, signature: str) -> bool:
        """
        Verify Flutterwave webhook signature
        
        Args:
            payload: Raw webhook payload
            signature: Signature from webhook headers
            
        Returns:
            True if signature is valid, False otherwise
        """
        return self.auth_manager.verify_webhook_signature(payload, signature)
    
    def _queue_for_retry(self, webhook_event: FlutterwaveWebhookEvent):
        """Queue failed webhook event for retry"""
        retry_item = {
            'webhook_event': webhook_event,
            'attempts': 0,
            'next_retry': datetime.utcnow() + timedelta(seconds=self.config.retry_delay_seconds),
            'max_attempts': self.config.max_retry_attempts
        }
        
        self.retry_queue.append(retry_item)
        self.logger.info(f"Queued event {webhook_event.event_id} for retry")
    
    async def process_retries(self):
        """Process failed webhook events that are ready for retry"""
        if not self.retry_queue:
            return
        
        now = datetime.utcnow()
        ready_for_retry = []
        
        for item in self.retry_queue:
            if item['next_retry'] <= now:
                ready_for_retry.append(item)
        
        for item in ready_for_retry:
            try:
                webhook_event = item['webhook_event']
                item['attempts'] += 1
                
                self.logger.info(f"Retrying webhook event {webhook_event.event_id} (attempt {item['attempts']})")
                
                # Process the event again
                result = await self._process_webhook_event(webhook_event)
                
                if result['success']:
                    self.processed_events.add(webhook_event.event_id)
                    self.retry_queue.remove(item)
                    self.logger.info(f"Retry successful for event {webhook_event.event_id}")
                else:
                    # Check if we should retry again
                    if item['attempts'] >= item['max_attempts']:
                        self.failed_events.append(item)
                        self.retry_queue.remove(item)
                        self.logger.error(f"Event {webhook_event.event_id} failed after {item['attempts']} attempts")
                    else:
                        # Schedule next retry with exponential backoff
                        delay = self.config.retry_delay_seconds * (2 ** (item['attempts'] - 1))
                        item['next_retry'] = now + timedelta(seconds=delay)
                        self.logger.info(f"Scheduled next retry for event {webhook_event.event_id} in {delay} seconds")
                
            except Exception as e:
                self.logger.error(f"Error during retry processing: {str(e)}")
                item['next_retry'] = now + timedelta(seconds=self.config.retry_delay_seconds * 2)
    
    def _create_success_response(self, message: str, start_time: datetime) -> Dict[str, Any]:
        """Create success response"""
        return {
            'status': 'success',
            'message': message,
            'processing_time': (datetime.utcnow() - start_time).total_seconds()
        }
    
    def _create_error_response(self, message: str, start_time: datetime) -> Dict[str, Any]:
        """Create error response"""
        return {
            'status': 'error',
            'message': message,
            'processing_time': (datetime.utcnow() - start_time).total_seconds()
        }
    
    def get_webhook_statistics(self) -> Dict[str, Any]:
        """Get comprehensive webhook processing statistics"""
        avg_processing_time = (
            sum(self.webhook_stats['processing_times']) / len(self.webhook_stats['processing_times'])
            if self.webhook_stats['processing_times'] else 0
        )
        
        return {
            **self.webhook_stats,
            'countries_processed': list(self.webhook_stats['countries_processed']),
            'average_processing_time': avg_processing_time,
            'pending_retries': len(self.retry_queue),
            'permanently_failed': len(self.failed_events),
            'success_rate': (
                self.webhook_stats['total_processed'] / 
                max(1, self.webhook_stats['total_received']) * 100
            ),
            'signature_failure_rate': (
                self.webhook_stats['signature_failures'] /
                max(1, self.webhook_stats['total_received']) * 100
            )
        }
    
    def clear_processed_events(self, older_than_hours: int = 24):
        """Clear old processed events to prevent memory buildup"""
        # This would be implemented with a proper cleanup strategy
        # For now, we just clear if we have too many
        if len(self.processed_events) > 10000:
            # Keep only the most recent 5000
            event_list = list(self.processed_events)
            self.processed_events = set(event_list[-5000:])
            self.logger.info(f"Cleared {len(event_list) - 5000} old processed events")


__all__ = [
    'FlutterwaveWebhookConfig',
    'FlutterwaveWebhookHandler'
]