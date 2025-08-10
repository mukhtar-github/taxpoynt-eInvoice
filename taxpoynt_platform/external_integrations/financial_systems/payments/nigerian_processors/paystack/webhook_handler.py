"""
Paystack Webhook Handler
=======================

Handles and validates Paystack webhook events for real-time payment processing.
Implements signature verification and event processing for Nigerian business compliance.
"""

import hashlib
import hmac
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class PaystackEventType(Enum):
    """Paystack webhook event types."""
    CHARGE_SUCCESS = "charge.success"
    TRANSACTION_SUCCESS = "transaction.success"
    TRANSFER_SUCCESS = "transfer.success"
    TRANSFER_FAILED = "transfer.failed"
    TRANSFER_REVERSED = "transfer.reversed"
    CUSTOMERIDENTIFICATION_SUCCESS = "customeridentification.success"
    CUSTOMERIDENTIFICATION_FAILED = "customeridentification.failed"
    DEDICATED_ACCOUNT_ASSIGN_SUCCESS = "dedicatedaccount.assign.success"
    DEDICATED_ACCOUNT_ASSIGN_FAILED = "dedicatedaccount.assign.failed"
    INVOICE_CREATE = "invoice.create"
    INVOICE_PAYMENT_FAILED = "invoice.payment_failed"
    INVOICE_UPDATE = "invoice.update"
    SUBSCRIPTION_CREATE = "subscription.create"
    SUBSCRIPTION_DISABLE = "subscription.disable"
    SUBSCRIPTION_EXPIRY_REMINDER = "subscription.expiry_reminder"


@dataclass
class PaystackWebhookEvent:
    """Structured representation of a Paystack webhook event."""
    event_id: str
    event_type: PaystackEventType
    created_at: datetime
    data: Dict[str, Any]
    raw_payload: str
    signature_verified: bool
    
    # Nigerian business context
    transaction_id: Optional[str] = None
    transaction_reference: Optional[str] = None
    customer_email: Optional[str] = None
    amount: Optional[float] = None
    currency: str = "NGN"
    
    # Processing metadata
    processed_at: Optional[datetime] = None
    processing_status: str = "pending"
    business_income_relevant: bool = False
    requires_invoice: bool = False


class PaystackWebhookHandler:
    """
    Handles Paystack webhook events with signature verification and business logic.
    
    Features:
    - HMAC-SHA512 signature verification
    - Event type classification
    - Nigerian business income detection
    - Automatic invoice triggering
    - Comprehensive audit logging
    """

    def __init__(self, webhook_secret: str):
        """
        Initialize Paystack webhook handler.
        
        Args:
            webhook_secret: Secret key for webhook signature verification
        """
        self.webhook_secret = webhook_secret
        self.logger = logging.getLogger(__name__)
        
        # Statistics tracking
        self.stats = {
            'webhooks_received': 0,
            'webhooks_verified': 0,
            'webhooks_rejected': 0,
            'events_processed': 0,
            'business_income_detected': 0,
            'invoices_triggered': 0
        }
        
        # Business income event types (relevant for FIRS compliance)
        self.business_income_events = {
            PaystackEventType.CHARGE_SUCCESS,
            PaystackEventType.TRANSACTION_SUCCESS,
            PaystackEventType.TRANSFER_SUCCESS
        }

    async def verify_webhook(self, payload: str, signature: str) -> bool:
        """
        Verify Paystack webhook signature using HMAC-SHA512.
        
        Args:
            payload: Raw webhook payload string
            signature: Signature from Paystack headers
            
        Returns:
            bool: True if signature is valid
        """
        try:
            self.stats['webhooks_received'] += 1
            
            if not payload or not signature:
                self.logger.warning("Missing payload or signature in webhook verification")
                self.stats['webhooks_rejected'] += 1
                return False
            
            # Compute expected signature
            expected_signature = hmac.new(
                self.webhook_secret.encode('utf-8'),
                payload.encode('utf-8'),
                hashlib.sha512
            ).hexdigest()
            
            # Compare signatures (timing-safe comparison)
            is_valid = hmac.compare_digest(signature, expected_signature)
            
            if is_valid:
                self.stats['webhooks_verified'] += 1
                self.logger.debug("Webhook signature verified successfully")
            else:
                self.stats['webhooks_rejected'] += 1
                self.logger.warning("Invalid webhook signature detected")
            
            return is_valid
            
        except Exception as e:
            self.logger.error(f"Webhook signature verification failed: {str(e)}")
            self.stats['webhooks_rejected'] += 1
            return False

    async def process_webhook(
        self,
        payload: str,
        signature: str,
        headers: Optional[Dict[str, str]] = None
    ) -> PaystackWebhookEvent:
        """
        Process and validate a Paystack webhook event.
        
        Args:
            payload: Raw webhook payload
            signature: Webhook signature
            headers: HTTP headers from webhook request
            
        Returns:
            PaystackWebhookEvent: Processed webhook event
            
        Raises:
            ValueError: If webhook verification fails
            json.JSONDecodeError: If payload is invalid JSON
        """
        try:
            # Verify webhook signature
            if not await self.verify_webhook(payload, signature):
                raise ValueError("Webhook signature verification failed")
            
            # Parse payload
            webhook_data = json.loads(payload)
            
            # Extract event information
            event_type_str = webhook_data.get('event', '')
            try:
                event_type = PaystackEventType(event_type_str)
            except ValueError:
                self.logger.warning(f"Unknown Paystack event type: {event_type_str}")
                # Create a generic event type for unknown events
                event_type = event_type_str
            
            # Build webhook event
            webhook_event = await self._build_webhook_event(
                webhook_data=webhook_data,
                event_type=event_type,
                payload=payload,
                signature_verified=True
            )
            
            # Process business logic
            await self._process_business_logic(webhook_event)
            
            self.stats['events_processed'] += 1
            
            self.logger.info(
                f"Processed Paystack webhook: {event_type} "
                f"(Transaction: {webhook_event.transaction_reference})"
            )
            
            return webhook_event
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in webhook payload: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Webhook processing failed: {str(e)}")
            raise

    async def _build_webhook_event(
        self,
        webhook_data: Dict[str, Any],
        event_type: PaystackEventType,
        payload: str,
        signature_verified: bool
    ) -> PaystackWebhookEvent:
        """
        Build structured webhook event from raw data.
        
        Args:
            webhook_data: Parsed webhook JSON data
            event_type: Classified event type
            payload: Raw payload string
            signature_verified: Whether signature was verified
            
        Returns:
            PaystackWebhookEvent: Structured event object
        """
        data = webhook_data.get('data', {})
        
        # Extract common transaction fields
        transaction_id = None
        transaction_reference = None
        customer_email = None
        amount = None
        
        # Different event types have different data structures
        if hasattr(event_type, 'value') and 'charge' in event_type.value:
            # Charge events
            transaction_id = str(data.get('id', ''))
            transaction_reference = data.get('reference', '')
            customer_email = data.get('customer', {}).get('email', '')
            amount = data.get('amount', 0) / 100.0  # Paystack amounts in kobo
            
        elif hasattr(event_type, 'value') and 'transaction' in event_type.value:
            # Transaction events
            transaction_id = str(data.get('id', ''))
            transaction_reference = data.get('reference', '')
            customer_email = data.get('customer', {}).get('email', '')
            amount = data.get('amount', 0) / 100.0
            
        elif hasattr(event_type, 'value') and 'transfer' in event_type.value:
            # Transfer events
            transaction_id = str(data.get('id', ''))
            transaction_reference = data.get('reference', '')
            amount = data.get('amount', 0) / 100.0
        
        # Create event object
        webhook_event = PaystackWebhookEvent(
            event_id=webhook_data.get('id', ''),
            event_type=event_type,
            created_at=datetime.utcnow(),
            data=data,
            raw_payload=payload,
            signature_verified=signature_verified,
            transaction_id=transaction_id,
            transaction_reference=transaction_reference,
            customer_email=customer_email,
            amount=amount,
            currency=data.get('currency', 'NGN'),
            processed_at=datetime.utcnow(),
            processing_status="processing"
        )
        
        return webhook_event

    async def _process_business_logic(self, webhook_event: PaystackWebhookEvent) -> None:
        """
        Apply Nigerian business logic to webhook event.
        
        Args:
            webhook_event: Webhook event to process
        """
        try:
            # Check if event is relevant for business income (FIRS compliance)
            if webhook_event.event_type in self.business_income_events:
                webhook_event.business_income_relevant = True
                self.stats['business_income_detected'] += 1
                
                # Check if invoice generation should be triggered
                if await self._should_trigger_invoice(webhook_event):
                    webhook_event.requires_invoice = True
                    self.stats['invoices_triggered'] += 1
                    
                    self.logger.info(
                        f"Invoice generation triggered for transaction: "
                        f"{webhook_event.transaction_reference}"
                    )
            
            # Update processing status
            webhook_event.processing_status = "completed"
            
        except Exception as e:
            webhook_event.processing_status = "failed"
            self.logger.error(f"Business logic processing failed: {str(e)}")

    async def _should_trigger_invoice(self, webhook_event: PaystackWebhookEvent) -> bool:
        """
        Determine if invoice generation should be triggered.
        
        Args:
            webhook_event: Webhook event to evaluate
            
        Returns:
            bool: True if invoice should be generated
        """
        # Business rules for invoice generation
        if not webhook_event.amount or webhook_event.amount < 1000:  # Minimum ₦1,000
            return False
        
        # Success events that represent completed payments
        success_events = {
            PaystackEventType.CHARGE_SUCCESS,
            PaystackEventType.TRANSACTION_SUCCESS
        }
        
        if webhook_event.event_type not in success_events:
            return False
        
        # Must have valid transaction reference
        if not webhook_event.transaction_reference:
            return False
        
        return True

    def get_supported_events(self) -> List[str]:
        """
        Get list of supported webhook event types.
        
        Returns:
            List of supported event type strings
        """
        return [event.value for event in PaystackEventType]

    def get_processing_stats(self) -> Dict[str, Any]:
        """
        Get webhook processing statistics.
        
        Returns:
            Dictionary containing processing statistics
        """
        total_webhooks = self.stats['webhooks_received']
        verification_rate = (
            self.stats['webhooks_verified'] / max(1, total_webhooks) * 100
        )
        
        return {
            **self.stats,
            'verification_rate_percentage': verification_rate,
            'supported_event_types': len(PaystackEventType),
            'business_income_event_types': len(self.business_income_events)
        }

    async def validate_webhook_config(self) -> Dict[str, Any]:
        """
        Validate webhook configuration and connectivity.
        
        Returns:
            Dictionary containing validation results
        """
        validation_result = {
            'webhook_secret_configured': bool(self.webhook_secret),
            'webhook_secret_length': len(self.webhook_secret) if self.webhook_secret else 0,
            'supported_events': self.get_supported_events(),
            'business_income_events': [e.value for e in self.business_income_events],
            'validation_timestamp': datetime.utcnow().isoformat()
        }
        
        # Validate webhook secret strength
        if self.webhook_secret:
            validation_result['webhook_secret_strength'] = (
                'strong' if len(self.webhook_secret) >= 32 else 'weak'
            )
        else:
            validation_result['webhook_secret_strength'] = 'missing'
        
        return validation_result

    def reset_stats(self) -> None:
        """Reset processing statistics."""
        self.stats = {
            'webhooks_received': 0,
            'webhooks_verified': 0,
            'webhooks_rejected': 0,
            'events_processed': 0,
            'business_income_detected': 0,
            'invoices_triggered': 0
        }
        
        self.logger.info("Webhook handler statistics reset")


# Export main classes
__all__ = [
    'PaystackWebhookHandler',
    'PaystackWebhookEvent',
    'PaystackEventType'
]