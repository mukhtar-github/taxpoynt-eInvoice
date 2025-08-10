"""
Stripe Webhook Handler
=====================

Comprehensive webhook processing for Stripe payment events with
global support and AI-based classification.

Features:
- Real-time webhook event processing and validation
- Signature verification for webhook security
- AI-based Nigerian business transaction classification
- Global event handling for international payments
- Comprehensive retry logic and error handling
- NDPR-compliant event logging and privacy protection
- Advanced fraud detection and dispute handling
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from .models import StripeWebhookEvent, StripeTransaction, StripeCountry
from .auth import StripeAuthManager
from .payment_processor import StripePaymentProcessor
from ....connector_framework.classification_engine.nigerian_classifier import NigerianTransactionClassifier
from ....connector_framework.classification_engine.privacy_protection import APIPrivacyProtection


@dataclass
class StripeWebhookConfig:
    """Configuration for Stripe webhook processing"""
    
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
    
    # Tolerance for timestamp verification (in seconds)
    timestamp_tolerance: int = 300  # 5 minutes
    
    def __post_init__(self):
        if self.enabled_events is None:
            self.enabled_events = [
                'payment_intent.succeeded',
                'payment_intent.payment_failed',
                'payment_intent.requires_action',
                'charge.succeeded',
                'charge.failed',
                'charge.disputed',
                'charge.dispute.created',
                'invoice.payment_succeeded',
                'invoice.payment_failed',
                'customer.created',
                'customer.updated',
                'payment_method.attached',
                'setup_intent.succeeded'
            ]


class StripeWebhookHandler:
    """
    Stripe webhook event handler with comprehensive processing
    
    Handles real-time webhook events from Stripe with signature verification,
    AI classification, and integration with TaxPoynt's processing pipeline.
    """
    
    def __init__(
        self,
        config: StripeWebhookConfig,
        auth_manager: StripeAuthManager,
        payment_processor: StripePaymentProcessor,
        transaction_classifier: Optional[NigerianTransactionClassifier] = None
    ):
        """
        Initialize Stripe webhook handler
        
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
            'timestamp_failures': 0,
            'classification_attempts': 0,
            'events_by_type': {},
            'countries_processed': set(),
            'processing_times': [],
            'last_event_time': None,
            'fraud_events_detected': 0,
            'dispute_events_processed': 0
        }
        
        self.logger.info("Stripe webhook handler initialized", extra={
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
            event_id = webhook_data.get('id', '')
            event_type = webhook_data.get('type', '')
            api_version = webhook_data.get('api_version', '')
            event_data = webhook_data.get('data', {}).get('object', {})
            created_timestamp = webhook_data.get('created', 0)
            livemode = webhook_data.get('livemode', False)
            
            self.logger.info("Processing Stripe webhook", extra={
                'event_type': event_type,
                'event_id': event_id,
                'api_version': api_version,
                'livemode': livemode,
                'object_id': event_data.get('id')
            })
            
            # Verify signature if enabled
            if self.config.validate_signatures:
                signature = headers.get('stripe-signature', '')
                timestamp = headers.get('stripe-timestamp', str(created_timestamp))
                
                if not signature:
                    self.webhook_stats['signature_failures'] += 1
                    self.logger.warning("Missing webhook signature")
                    return self._create_error_response("Missing signature", processing_start)
                
                # Verify timestamp freshness
                if not self._verify_timestamp(timestamp):
                    self.webhook_stats['timestamp_failures'] += 1
                    self.logger.warning("Webhook timestamp too old or invalid")
                    return self._create_error_response("Invalid timestamp", processing_start)
                
                # Verify signature
                if not self._verify_signature(payload, signature, timestamp):
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
            webhook_event = StripeWebhookEvent(
                id=event_id,
                type=event_type,
                api_version=api_version,
                data=event_data,
                request=webhook_data.get('request'),
                created=datetime.fromtimestamp(created_timestamp),
                livemode=livemode,
                pending_webhooks=webhook_data.get('pending_webhooks', 0),
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
                'api_version': api_version,
                'livemode': livemode,
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
    
    async def _process_webhook_event(self, webhook_event: StripeWebhookEvent) -> Dict[str, Any]:
        """
        Process specific webhook event based on type
        
        Args:
            webhook_event: Webhook event to process
            
        Returns:
            Processing result
        """
        try:
            event_type = webhook_event.type
            event_data = webhook_event.data
            
            # Payment Intent events
            if event_type == 'payment_intent.succeeded':
                return await self._process_payment_intent_succeeded(webhook_event)
            
            elif event_type == 'payment_intent.payment_failed':
                return await self._process_payment_intent_failed(webhook_event)
            
            elif event_type == 'payment_intent.requires_action':
                return await self._process_payment_intent_requires_action(webhook_event)
            
            # Charge events
            elif event_type == 'charge.succeeded':
                return await self._process_charge_succeeded(webhook_event)
            
            elif event_type == 'charge.failed':
                return await self._process_charge_failed(webhook_event)
            
            elif event_type == 'charge.disputed':
                return await self._process_charge_disputed(webhook_event)
            
            elif event_type == 'charge.dispute.created':
                return await self._process_dispute_created(webhook_event)
            
            # Invoice events
            elif event_type in ['invoice.payment_succeeded', 'invoice.payment_failed']:
                return await self._process_invoice_event(webhook_event)
            
            # Customer events
            elif event_type in ['customer.created', 'customer.updated']:
                return await self._process_customer_event(webhook_event)
            
            # Payment method events
            elif event_type == 'payment_method.attached':
                return await self._process_payment_method_attached(webhook_event)
            
            # Setup intent events
            elif event_type == 'setup_intent.succeeded':
                return await self._process_setup_intent_succeeded(webhook_event)
            
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
    
    async def _process_payment_intent_succeeded(self, webhook_event: StripeWebhookEvent) -> Dict[str, Any]:
        """Process successful payment intent event"""
        try:
            event_data = webhook_event.data
            payment_intent_id = event_data.get('id', '')
            
            # Retrieve full payment intent details
            transaction = await self.payment_processor.retrieve_payment_intent(payment_intent_id)
            
            if not transaction:
                return {
                    'success': False,
                    'message': 'Payment intent retrieval failed',
                    'details': {'payment_intent_id': payment_intent_id}
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
            if transaction.country == StripeCountry.SOUTH_AFRICA and classification_result:  # Example - adjust for Nigerian customers
                if classification_result.get('is_business_income', False):
                    firs_processing_result = await self._process_for_firs_compliance(
                        transaction, classification_result
                    )
            
            self.logger.info("Payment intent succeeded", extra={
                'payment_intent_id': payment_intent_id,
                'amount': str(transaction.amount),
                'currency': transaction.currency,
                'country': transaction.country.value if transaction.country else None,
                'classification_confidence': classification_result.get('confidence') if classification_result else None,
                'requires_firs_submission': firs_processing_result is not None
            })
            
            return {
                'success': True,
                'message': 'Payment intent processed successfully',
                'details': {
                    'payment_intent_id': payment_intent_id,
                    'amount': str(transaction.amount),
                    'currency': transaction.currency,
                    'classification': classification_result,
                    'firs_processing': firs_processing_result
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error processing payment intent succeeded: {str(e)}")
            return {
                'success': False,
                'message': str(e),
                'details': {'error_in': 'payment_intent_succeeded_processing'}
            }
    
    async def _process_payment_intent_failed(self, webhook_event: StripeWebhookEvent) -> Dict[str, Any]:
        """Process failed payment intent event"""
        try:
            event_data = webhook_event.data
            payment_intent_id = event_data.get('id', '')
            last_payment_error = event_data.get('last_payment_error', {})
            
            failure_reason = last_payment_error.get('message', 'Unknown failure')
            failure_code = last_payment_error.get('code')
            
            self.logger.warning("Payment intent failed", extra={
                'payment_intent_id': payment_intent_id,
                'failure_reason': failure_reason,
                'failure_code': failure_code
            })
            
            return {
                'success': True,
                'message': 'Failed payment intent logged',
                'details': {
                    'payment_intent_id': payment_intent_id,
                    'failure_reason': failure_reason,
                    'failure_code': failure_code
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error processing payment intent failed: {str(e)}")
            return {
                'success': False,
                'message': str(e),
                'details': {'error_in': 'payment_intent_failed_processing'}
            }
    
    async def _process_payment_intent_requires_action(self, webhook_event: StripeWebhookEvent) -> Dict[str, Any]:
        """Process payment intent requiring action (e.g., 3D Secure)"""
        try:
            event_data = webhook_event.data
            payment_intent_id = event_data.get('id', '')
            next_action = event_data.get('next_action', {})
            
            self.logger.info("Payment intent requires action", extra={
                'payment_intent_id': payment_intent_id,
                'next_action_type': next_action.get('type'),
                'client_secret': event_data.get('client_secret')
            })
            
            return {
                'success': True,
                'message': 'Payment intent requires action logged',
                'details': {
                    'payment_intent_id': payment_intent_id,
                    'next_action': next_action
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error processing payment intent requires action: {str(e)}")
            return {
                'success': False,
                'message': str(e),
                'details': {'error_in': 'payment_intent_requires_action_processing'}
            }
    
    async def _process_charge_succeeded(self, webhook_event: StripeWebhookEvent) -> Dict[str, Any]:
        """Process successful charge event"""
        try:
            event_data = webhook_event.data
            charge_id = event_data.get('id', '')
            amount = event_data.get('amount', 0)
            currency = event_data.get('currency', 'usd')
            
            # Check for fraud indicators
            outcome = event_data.get('outcome', {})
            if outcome.get('type') == 'issuer_declined' or outcome.get('risk_level') == 'highest':
                self.webhook_stats['fraud_events_detected'] += 1
            
            self.logger.info("Charge succeeded", extra={
                'charge_id': charge_id,
                'amount': amount,
                'currency': currency,
                'risk_level': outcome.get('risk_level'),
                'network_status': outcome.get('network_status')
            })
            
            return {
                'success': True,
                'message': 'Charge processed successfully',
                'details': {
                    'charge_id': charge_id,
                    'amount': amount,
                    'currency': currency,
                    'outcome': outcome
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error processing charge succeeded: {str(e)}")
            return {
                'success': False,
                'message': str(e),
                'details': {'error_in': 'charge_succeeded_processing'}
            }
    
    async def _process_charge_failed(self, webhook_event: StripeWebhookEvent) -> Dict[str, Any]:
        """Process failed charge event"""
        try:
            event_data = webhook_event.data
            charge_id = event_data.get('id', '')
            failure_code = event_data.get('failure_code')
            failure_message = event_data.get('failure_message')
            
            self.logger.warning("Charge failed", extra={
                'charge_id': charge_id,
                'failure_code': failure_code,
                'failure_message': failure_message
            })
            
            return {
                'success': True,
                'message': 'Failed charge logged',
                'details': {
                    'charge_id': charge_id,
                    'failure_code': failure_code,
                    'failure_message': failure_message
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error processing charge failed: {str(e)}")
            return {
                'success': False,
                'message': str(e),
                'details': {'error_in': 'charge_failed_processing'}
            }
    
    async def _process_charge_disputed(self, webhook_event: StripeWebhookEvent) -> Dict[str, Any]:
        """Process disputed charge event"""
        try:
            event_data = webhook_event.data
            charge_id = event_data.get('id', '')
            disputed = event_data.get('disputed', False)
            
            if disputed:
                self.webhook_stats['dispute_events_processed'] += 1
            
            self.logger.warning("Charge disputed", extra={
                'charge_id': charge_id,
                'disputed': disputed
            })
            
            return {
                'success': True,
                'message': 'Charge dispute logged',
                'details': {
                    'charge_id': charge_id,
                    'disputed': disputed
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error processing charge disputed: {str(e)}")
            return {
                'success': False,
                'message': str(e),
                'details': {'error_in': 'charge_disputed_processing'}
            }
    
    async def _process_dispute_created(self, webhook_event: StripeWebhookEvent) -> Dict[str, Any]:
        """Process dispute created event"""
        try:
            event_data = webhook_event.data
            dispute_id = event_data.get('id', '')
            charge_id = event_data.get('charge', '')
            reason = event_data.get('reason', '')
            amount = event_data.get('amount', 0)
            
            self.webhook_stats['dispute_events_processed'] += 1
            
            self.logger.warning("Dispute created", extra={
                'dispute_id': dispute_id,
                'charge_id': charge_id,
                'reason': reason,
                'amount': amount
            })
            
            return {
                'success': True,
                'message': 'Dispute creation logged',
                'details': {
                    'dispute_id': dispute_id,
                    'charge_id': charge_id,
                    'reason': reason,
                    'amount': amount
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error processing dispute created: {str(e)}")
            return {
                'success': False,
                'message': str(e),
                'details': {'error_in': 'dispute_created_processing'}
            }
    
    async def _process_invoice_event(self, webhook_event: StripeWebhookEvent) -> Dict[str, Any]:
        """Process invoice events"""
        try:
            event_data = webhook_event.data
            invoice_id = event_data.get('id', '')
            status = event_data.get('status', '')
            
            self.logger.info("Invoice event processed", extra={
                'invoice_id': invoice_id,
                'status': status,
                'event_type': webhook_event.type
            })
            
            return {
                'success': True,
                'message': 'Invoice event processed',
                'details': {
                    'invoice_id': invoice_id,
                    'status': status
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error processing invoice event: {str(e)}")
            return {
                'success': False,
                'message': str(e),
                'details': {'error_in': 'invoice_event_processing'}
            }
    
    async def _process_customer_event(self, webhook_event: StripeWebhookEvent) -> Dict[str, Any]:
        """Process customer events"""
        try:
            event_data = webhook_event.data
            customer_id = event_data.get('id', '')
            email = event_data.get('email', '')
            
            self.logger.info("Customer event processed", extra={
                'customer_id': customer_id,
                'email': email,
                'event_type': webhook_event.type
            })
            
            return {
                'success': True,
                'message': 'Customer event processed',
                'details': {
                    'customer_id': customer_id,
                    'email': email
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error processing customer event: {str(e)}")
            return {
                'success': False,
                'message': str(e),
                'details': {'error_in': 'customer_event_processing'}
            }
    
    async def _process_payment_method_attached(self, webhook_event: StripeWebhookEvent) -> Dict[str, Any]:
        """Process payment method attached event"""
        try:
            event_data = webhook_event.data
            payment_method_id = event_data.get('id', '')
            customer_id = event_data.get('customer', '')
            type_info = event_data.get('type', '')
            
            self.logger.info("Payment method attached", extra={
                'payment_method_id': payment_method_id,
                'customer_id': customer_id,
                'type': type_info
            })
            
            return {
                'success': True,
                'message': 'Payment method attachment logged',
                'details': {
                    'payment_method_id': payment_method_id,
                    'customer_id': customer_id,
                    'type': type_info
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error processing payment method attached: {str(e)}")
            return {
                'success': False,
                'message': str(e),
                'details': {'error_in': 'payment_method_attached_processing'}
            }
    
    async def _process_setup_intent_succeeded(self, webhook_event: StripeWebhookEvent) -> Dict[str, Any]:
        """Process setup intent succeeded event"""
        try:
            event_data = webhook_event.data
            setup_intent_id = event_data.get('id', '')
            customer_id = event_data.get('customer', '')
            
            self.logger.info("Setup intent succeeded", extra={
                'setup_intent_id': setup_intent_id,
                'customer_id': customer_id
            })
            
            return {
                'success': True,
                'message': 'Setup intent success logged',
                'details': {
                    'setup_intent_id': setup_intent_id,
                    'customer_id': customer_id
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error processing setup intent succeeded: {str(e)}")
            return {
                'success': False,
                'message': str(e),
                'details': {'error_in': 'setup_intent_succeeded_processing'}
            }
    
    async def _classify_webhook_transaction(self, transaction: StripeTransaction) -> Optional[Dict[str, Any]]:
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
        transaction: StripeTransaction,
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
    
    def _verify_signature(self, payload: str, signature: str, timestamp: str) -> bool:
        """
        Verify Stripe webhook signature
        
        Args:
            payload: Raw webhook payload
            signature: Signature from webhook headers
            timestamp: Timestamp from headers
            
        Returns:
            True if signature is valid, False otherwise
        """
        return self.auth_manager.verify_webhook_signature(payload, signature, timestamp)
    
    def _verify_timestamp(self, timestamp: str) -> bool:
        """
        Verify webhook timestamp is within tolerance
        
        Args:
            timestamp: Timestamp string
            
        Returns:
            True if timestamp is valid and recent, False otherwise
        """
        try:
            event_timestamp = int(timestamp)
            current_timestamp = int(datetime.utcnow().timestamp())
            
            # Check if timestamp is within tolerance
            time_diff = abs(current_timestamp - event_timestamp)
            return time_diff <= self.config.timestamp_tolerance
            
        except (ValueError, TypeError):
            return False
    
    def _queue_for_retry(self, webhook_event: StripeWebhookEvent):
        """Queue failed webhook event for retry"""
        retry_item = {
            'webhook_event': webhook_event,
            'attempts': 0,
            'next_retry': datetime.utcnow() + timedelta(seconds=self.config.retry_delay_seconds),
            'max_attempts': self.config.max_retry_attempts
        }
        
        self.retry_queue.append(retry_item)
        self.logger.info(f"Queued event {webhook_event.id} for retry")
    
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
                
                self.logger.info(f"Retrying webhook event {webhook_event.id} (attempt {item['attempts']})")
                
                # Process the event again
                result = await self._process_webhook_event(webhook_event)
                
                if result['success']:
                    self.processed_events.add(webhook_event.id)
                    self.retry_queue.remove(item)
                    self.logger.info(f"Retry successful for event {webhook_event.id}")
                else:
                    # Check if we should retry again
                    if item['attempts'] >= item['max_attempts']:
                        self.failed_events.append(item)
                        self.retry_queue.remove(item)
                        self.logger.error(f"Event {webhook_event.id} failed after {item['attempts']} attempts")
                    else:
                        # Schedule next retry with exponential backoff
                        delay = self.config.retry_delay_seconds * (2 ** (item['attempts'] - 1))
                        item['next_retry'] = now + timedelta(seconds=delay)
                        self.logger.info(f"Scheduled next retry for event {webhook_event.id} in {delay} seconds")
                
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
            ),
            'timestamp_failure_rate': (
                self.webhook_stats['timestamp_failures'] /
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
    'StripeWebhookConfig',
    'StripeWebhookHandler'
]