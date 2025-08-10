"""
OPay Webhook Handler
===================

Handles and validates OPay webhook events for real-time mobile money processing.
Implements signature verification and mobile wallet event processing with Nigerian
business compliance and regulatory requirements.

Features:
- HMAC signature verification
- Mobile money event classification
- Digital wallet transaction processing
- Business income detection for tax compliance
- Real-time fraud detection
- CBN regulatory compliance
- Automated invoice triggering
"""

import hashlib
import hmac
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

from .models import (
    OPayWebhookEvent, OPayTransactionType, OPayKYCLevel,
    NIGERIAN_MOBILE_MONEY_THRESHOLDS, KYC_TRANSACTION_LIMITS
)

logger = logging.getLogger(__name__)


class OPayEventType(Enum):
    """OPay webhook event types."""
    PAYMENT_SUCCESS = "payment.success"
    PAYMENT_FAILED = "payment.failed"
    TRANSFER_SUCCESS = "transfer.success"
    TRANSFER_FAILED = "transfer.failed"
    WALLET_CREDIT = "wallet.credit"
    WALLET_DEBIT = "wallet.debit"
    QR_PAYMENT_SUCCESS = "qr.payment.success"
    QR_PAYMENT_FAILED = "qr.payment.failed"
    BILL_PAYMENT_SUCCESS = "bill.payment.success"
    BILL_PAYMENT_FAILED = "bill.payment.failed"
    AIRTIME_PURCHASE_SUCCESS = "airtime.purchase.success"
    AIRTIME_PURCHASE_FAILED = "airtime.purchase.failed"
    SETTLEMENT_COMPLETED = "settlement.completed"
    SETTLEMENT_FAILED = "settlement.failed"
    REFUND_PROCESSED = "refund.processed"
    FRAUD_DETECTED = "fraud.detected"
    KYC_STATUS_CHANGE = "kyc.status.change"
    WALLET_STATUS_CHANGE = "wallet.status.change"
    MERCHANT_VERIFICATION = "merchant.verification"


@dataclass
class OPayProcessedWebhookEvent:
    """Processed webhook event with Nigerian mobile money context."""
    event_id: str
    event_type: OPayEventType
    processed_at: datetime
    transaction_id: Optional[str]
    wallet_id: Optional[str]
    
    # Mobile money intelligence
    is_business_income: bool
    requires_invoice: bool
    compliance_flags: List[str]
    risk_level: str  # low, medium, high, critical
    
    # Nigerian regulatory context
    cbn_reportable: bool
    firs_reportable: bool
    kyc_flags: List[str]
    aml_flags: List[str]
    
    # Mobile money specific
    mobile_money_transaction: bool
    wallet_transaction: bool
    qr_payment: bool
    bill_payment: bool
    
    # Processing results
    processing_success: bool
    processing_errors: List[str]
    invoice_triggered: bool
    
    # Original event data
    original_event: OPayWebhookEvent


class OPayWebhookHandler:
    """
    Handles OPay webhook events with Nigerian mobile money compliance.
    
    Features:
    - Mobile money event processing
    - Digital wallet transaction analysis
    - Business income classification
    - Fraud detection and risk assessment
    - CBN and FIRS compliance automation
    - Real-time invoice generation triggering
    """

    def __init__(self, webhook_secret: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize OPay webhook handler.
        
        Args:
            webhook_secret: Secret key for webhook signature verification
            config: Additional configuration options
        """
        self.webhook_secret = webhook_secret
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Processing configuration
        self.auto_invoice_threshold = self.config.get('auto_invoice_threshold', 1000)  # ₦1,000
        self.fraud_detection_enabled = self.config.get('fraud_detection', True)
        self.compliance_monitoring = self.config.get('compliance_monitoring', True)
        
        # Statistics tracking
        self.stats = {
            'webhooks_received': 0,
            'webhooks_verified': 0,
            'webhooks_rejected': 0,
            'events_processed': 0,
            'business_income_detected': 0,
            'invoices_triggered': 0,
            'fraud_alerts': 0,
            'compliance_violations': 0,
            'mobile_money_transactions': 0,
            'wallet_transactions': 0,
            'qr_payments': 0,
            'bill_payments': 0
        }
        
        # Business income event types (relevant for FIRS compliance)
        self.business_income_events = {
            OPayEventType.PAYMENT_SUCCESS,
            OPayEventType.QR_PAYMENT_SUCCESS,
            OPayEventType.TRANSFER_SUCCESS,
            OPayEventType.WALLET_CREDIT
        }
        
        # Events requiring CBN reporting
        self.cbn_reportable_events = {
            OPayEventType.PAYMENT_SUCCESS,
            OPayEventType.TRANSFER_SUCCESS,
            OPayEventType.WALLET_CREDIT,
            OPayEventType.WALLET_DEBIT,
            OPayEventType.FRAUD_DETECTED
        }

    async def verify_webhook_signature(self, payload: str, signature: str, timestamp: str) -> bool:
        """
        Verify OPay webhook signature using HMAC-SHA512.
        
        Args:
            payload: Raw webhook payload string
            signature: Signature from OPay headers
            timestamp: Request timestamp
            
        Returns:
            bool: True if signature is valid
        """
        try:
            self.stats['webhooks_received'] += 1
            
            if not payload or not signature or not timestamp:
                self.logger.warning("Missing payload, signature, or timestamp in webhook verification")
                self.stats['webhooks_rejected'] += 1
                return False
            
            # Create signature string (OPay format: timestamp + merchantId + payload)
            merchant_id = self.config.get('merchant_id', '')
            signature_string = f"{timestamp}{merchant_id}{payload}"
            
            # Compute expected signature using SHA512
            expected_signature = hmac.new(
                self.webhook_secret.encode('utf-8'),
                signature_string.encode('utf-8'),
                hashlib.sha512
            ).hexdigest()
            
            # Compare signatures (timing-safe comparison)
            is_valid = hmac.compare_digest(signature, expected_signature)
            
            if is_valid:
                self.stats['webhooks_verified'] += 1
                self.logger.debug("OPay webhook signature verified successfully")
            else:
                self.stats['webhooks_rejected'] += 1
                self.logger.warning("Invalid OPay webhook signature detected")
            
            return is_valid
            
        except Exception as e:
            self.logger.error(f"OPay webhook signature verification failed: {str(e)}")
            self.stats['webhooks_rejected'] += 1
            return False

    async def process_webhook(
        self,
        payload: str,
        signature: str,
        timestamp: str,
        headers: Optional[Dict[str, str]] = None
    ) -> OPayProcessedWebhookEvent:
        """
        Process and validate an OPay webhook event.
        
        Args:
            payload: Raw webhook payload
            signature: Webhook signature
            timestamp: Request timestamp
            headers: HTTP headers from webhook request
            
        Returns:
            OPayProcessedWebhookEvent: Processed webhook event
            
        Raises:
            ValueError: If webhook verification fails
            json.JSONDecodeError: If payload is invalid JSON
        """
        try:
            # Verify webhook signature
            if not await self.verify_webhook_signature(payload, signature, timestamp):
                raise ValueError("OPay webhook signature verification failed")
            
            # Parse payload
            webhook_data = json.loads(payload)
            
            # Extract event information
            event_type_str = webhook_data.get('eventType', '')
            try:
                event_type = OPayEventType(event_type_str)
            except ValueError:
                self.logger.warning(f"Unknown OPay event type: {event_type_str}")
                # Handle unknown events gracefully
                event_type = event_type_str
            
            # Build webhook event
            webhook_event = await self._build_webhook_event(
                webhook_data=webhook_data,
                event_type=event_type,
                payload=payload,
                signature_verified=True
            )
            
            # Process with Nigerian mobile money logic
            processed_event = await self._process_mobile_money_logic(webhook_event)
            
            self.stats['events_processed'] += 1
            
            self.logger.info(
                f"Processed OPay webhook: {event_type} "
                f"(Transaction: {webhook_event.transaction_id}, Wallet: {webhook_event.wallet_id})"
            )
            
            return processed_event
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in OPay webhook payload: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"OPay webhook processing failed: {str(e)}")
            raise

    async def _build_webhook_event(
        self,
        webhook_data: Dict[str, Any],
        event_type: OPayEventType,
        payload: str,
        signature_verified: bool
    ) -> OPayWebhookEvent:
        """Build structured webhook event from raw data."""
        
        data = webhook_data.get('data', {})
        
        # Extract common fields
        transaction_id = data.get('transactionId') or data.get('reference')
        wallet_id = data.get('walletId') or data.get('senderWalletId')
        
        # Create event object
        webhook_event = OPayWebhookEvent(
            event_id=webhook_data.get('eventId', ''),
            event_type=event_type.value if hasattr(event_type, 'value') else str(event_type),
            event_timestamp=datetime.utcnow(),
            transaction_id=str(transaction_id) if transaction_id else None,
            wallet_id=wallet_id,
            event_data=data,
            raw_payload=payload,
            verified=signature_verified,
            processed=False
        )
        
        return webhook_event

    async def _process_mobile_money_logic(
        self,
        webhook_event: OPayWebhookEvent
    ) -> OPayProcessedWebhookEvent:
        """Apply Nigerian mobile money logic and regulatory compliance."""
        
        try:
            # Initialize processed event
            processed_event = OPayProcessedWebhookEvent(
                event_id=webhook_event.event_id,
                event_type=OPayEventType(webhook_event.event_type),
                processed_at=datetime.utcnow(),
                transaction_id=webhook_event.transaction_id,
                wallet_id=webhook_event.wallet_id,
                is_business_income=False,
                requires_invoice=False,
                compliance_flags=[],
                risk_level="low",
                cbn_reportable=False,
                firs_reportable=False,
                kyc_flags=[],
                aml_flags=[],
                mobile_money_transaction=False,
                wallet_transaction=False,
                qr_payment=False,
                bill_payment=False,
                processing_success=True,
                processing_errors=[],
                invoice_triggered=False,
                original_event=webhook_event
            )
            
            # Classify transaction type
            await self._classify_mobile_money_transaction(processed_event, webhook_event)
            
            # Classify as business income
            await self._classify_business_income(processed_event, webhook_event)
            
            # Assess risk level
            await self._assess_mobile_money_risk(processed_event, webhook_event)
            
            # Check regulatory compliance
            await self._check_mobile_money_compliance(processed_event, webhook_event)
            
            # Determine if invoice should be triggered
            await self._evaluate_invoice_requirement(processed_event, webhook_event)
            
            # Update statistics
            self._update_event_stats(processed_event)
            
            return processed_event
            
        except Exception as e:
            self.logger.error(f"Mobile money logic processing failed: {str(e)}")
            
            # Return error state
            return OPayProcessedWebhookEvent(
                event_id=webhook_event.event_id,
                event_type=OPayEventType(webhook_event.event_type),
                processed_at=datetime.utcnow(),
                transaction_id=webhook_event.transaction_id,
                wallet_id=webhook_event.wallet_id,
                is_business_income=False,
                requires_invoice=False,
                compliance_flags=['processing_error'],
                risk_level="unknown",
                cbn_reportable=False,
                firs_reportable=False,
                kyc_flags=[],
                aml_flags=[],
                mobile_money_transaction=False,
                wallet_transaction=False,
                qr_payment=False,
                bill_payment=False,
                processing_success=False,
                processing_errors=[str(e)],
                invoice_triggered=False,
                original_event=webhook_event
            )

    async def _classify_mobile_money_transaction(
        self,
        processed_event: OPayProcessedWebhookEvent,
        webhook_event: OPayWebhookEvent
    ) -> None:
        """Classify mobile money transaction type."""
        
        event_type = processed_event.event_type
        data = webhook_event.event_data
        
        # Determine transaction categories
        if event_type in [OPayEventType.WALLET_CREDIT, OPayEventType.WALLET_DEBIT]:
            processed_event.wallet_transaction = True
            processed_event.mobile_money_transaction = True
            
        if event_type in [OPayEventType.QR_PAYMENT_SUCCESS, OPayEventType.QR_PAYMENT_FAILED]:
            processed_event.qr_payment = True
            processed_event.mobile_money_transaction = True
            
        if event_type in [OPayEventType.BILL_PAYMENT_SUCCESS, OPayEventType.BILL_PAYMENT_FAILED]:
            processed_event.bill_payment = True
            
        if event_type in [OPayEventType.PAYMENT_SUCCESS, OPayEventType.TRANSFER_SUCCESS]:
            processed_event.mobile_money_transaction = True

    async def _classify_business_income(
        self,
        processed_event: OPayProcessedWebhookEvent,
        webhook_event: OPayWebhookEvent
    ) -> None:
        """Classify if transaction represents business income."""
        
        event_type = processed_event.event_type
        data = webhook_event.event_data
        
        # Check if event type indicates business income
        if event_type in self.business_income_events:
            amount = data.get('amount', 0)
            transaction_type = data.get('transactionType', '')
            business_category = data.get('businessCategory', '')
            
            # QR payments are typically business income
            if processed_event.qr_payment and amount >= self.auto_invoice_threshold:
                processed_event.is_business_income = True
                
            # Wallet credits to business wallets
            if (processed_event.wallet_transaction and 
                event_type == OPayEventType.WALLET_CREDIT and
                data.get('walletType') == 'business_wallet'):
                processed_event.is_business_income = True
                
            # Merchant payments
            if any(term in transaction_type.lower() for term in ['merchant', 'business', 'pos']):
                processed_event.is_business_income = True
                
            # Business categories
            business_categories = [
                'retail', 'wholesale', 'services', 'technology',
                'hospitality', 'professional_services', 'fintech'
            ]
            
            if business_category in business_categories:
                processed_event.is_business_income = True

    async def _assess_mobile_money_risk(
        self,
        processed_event: OPayProcessedWebhookEvent,
        webhook_event: OPayWebhookEvent
    ) -> None:
        """Assess risk level for mobile money transactions."""
        
        if not self.fraud_detection_enabled:
            return
        
        data = webhook_event.event_data
        amount = data.get('amount', 0)
        
        risk_factors = []
        risk_score = 0
        
        # High value transaction risk
        if amount >= NIGERIAN_MOBILE_MONEY_THRESHOLDS['high_value_threshold']:
            risk_factors.append('high_value_mobile_money')
            risk_score += 35
        
        # KYC level vs transaction amount
        kyc_level = data.get('kycLevel', 'level_0')
        if kyc_level in ['level_0', 'level_1'] and amount >= 50000:  # ₦50K with low KYC
            risk_factors.append('low_kyc_high_amount')
            risk_score += 40
        
        # Velocity check
        if data.get('velocityCheck') == 'high':
            risk_factors.append('high_velocity_mobile_money')
            risk_score += 30
        
        # Cross-border transactions
        if data.get('crossBorder', False):
            risk_factors.append('cross_border_mobile_money')
            risk_score += 25
        
        # Unusual time patterns
        event_hour = webhook_event.event_timestamp.hour
        if event_hour < 6 or event_hour > 23:  # Outside typical business hours
            risk_factors.append('unusual_time_pattern')
            risk_score += 15
        
        # Multiple rapid wallet transactions
        if processed_event.wallet_transaction and data.get('transactionCountToday', 0) > 20:
            risk_factors.append('high_wallet_activity')
            risk_score += 20
        
        # Unverified wallet
        if not data.get('walletVerified', True):
            risk_factors.append('unverified_wallet')
            risk_score += 25
        
        # Determine risk level
        if risk_score >= 80:
            processed_event.risk_level = "critical"
        elif risk_score >= 60:
            processed_event.risk_level = "high"
        elif risk_score >= 35:
            processed_event.risk_level = "medium"
        else:
            processed_event.risk_level = "low"
        
        # Set AML flags for high-risk transactions
        if risk_score >= 50:
            processed_event.aml_flags = risk_factors

    async def _check_mobile_money_compliance(
        self,
        processed_event: OPayProcessedWebhookEvent,
        webhook_event: OPayWebhookEvent
    ) -> None:
        """Check CBN and FIRS mobile money compliance requirements."""
        
        if not self.compliance_monitoring:
            return
        
        event_type = processed_event.event_type
        data = webhook_event.event_data
        amount = data.get('amount', 0)
        
        # CBN reporting requirements
        if event_type in self.cbn_reportable_events:
            processed_event.cbn_reportable = True
            
            # High value mobile money reporting
            if amount >= 1000000:  # ₦1M CBN threshold
                processed_event.compliance_flags.append('cbn_high_value_mobile_money')
            
            # Cross-border mobile money
            if data.get('crossBorder', False):
                processed_event.compliance_flags.append('cbn_cross_border_mobile_money')
        
        # FIRS reporting requirements
        if processed_event.is_business_income:
            processed_event.firs_reportable = True
            
            # VAT compliance for high amounts
            if amount >= 25000000:  # ₦25M VAT threshold
                processed_event.compliance_flags.append('vat_registration_check_required')
        
        # KYC compliance checks
        kyc_level = data.get('kycLevel', 'level_0')
        if kyc_level in ['level_0', 'level_1']:
            # Check transaction limits for KYC level
            try:
                kyc_enum = OPayKYCLevel(kyc_level)
                kyc_limit = KYC_TRANSACTION_LIMITS.get(kyc_enum, 0)
                
                if amount > kyc_limit:
                    processed_event.kyc_flags.append('kyc_limit_exceeded')
                    processed_event.compliance_flags.append('kyc_upgrade_required')
            except ValueError:
                processed_event.kyc_flags.append('unknown_kyc_level')
        
        # Mobile money specific compliance
        if processed_event.mobile_money_transaction:
            # Daily transaction monitoring
            if data.get('dailyTransactionAmount', 0) >= 500000:  # ₦500K daily limit
                processed_event.compliance_flags.append('daily_mobile_money_limit_monitoring')
            
            # BVN verification requirement
            if not data.get('bvnVerified', False) and amount >= 50000:
                processed_event.compliance_flags.append('bvn_verification_required')

    async def _evaluate_invoice_requirement(
        self,
        processed_event: OPayProcessedWebhookEvent,
        webhook_event: OPayWebhookEvent
    ) -> None:
        """Determine if automatic invoice generation should be triggered."""
        
        # Business income check
        if not processed_event.is_business_income:
            return
        
        data = webhook_event.event_data
        amount = data.get('amount', 0)
        
        # Amount threshold check
        if amount < self.auto_invoice_threshold:
            return
        
        # Risk level check - don't auto-generate for high-risk transactions
        if processed_event.risk_level in ['high', 'critical']:
            return
        
        # Success event check
        success_events = [
            OPayEventType.PAYMENT_SUCCESS,
            OPayEventType.QR_PAYMENT_SUCCESS,
            OPayEventType.TRANSFER_SUCCESS,
            OPayEventType.WALLET_CREDIT
        ]
        
        if processed_event.event_type in success_events:
            processed_event.requires_invoice = True

    def _update_event_stats(self, processed_event: OPayProcessedWebhookEvent) -> None:
        """Update processing statistics based on event."""
        
        if processed_event.is_business_income:
            self.stats['business_income_detected'] += 1
        
        if processed_event.requires_invoice:
            self.stats['invoices_triggered'] += 1
            processed_event.invoice_triggered = True
        
        if processed_event.risk_level in ['high', 'critical']:
            self.stats['fraud_alerts'] += 1
        
        if processed_event.compliance_flags:
            self.stats['compliance_violations'] += 1
        
        if processed_event.mobile_money_transaction:
            self.stats['mobile_money_transactions'] += 1
        
        if processed_event.wallet_transaction:
            self.stats['wallet_transactions'] += 1
        
        if processed_event.qr_payment:
            self.stats['qr_payments'] += 1
        
        if processed_event.bill_payment:
            self.stats['bill_payments'] += 1

    def get_supported_events(self) -> List[str]:
        """Get list of supported webhook event types."""
        return [event.value for event in OPayEventType]

    def get_processing_stats(self) -> Dict[str, Any]:
        """Get comprehensive webhook processing statistics."""
        
        total_webhooks = self.stats['webhooks_received']
        verification_rate = (
            self.stats['webhooks_verified'] / max(1, total_webhooks) * 100
        )
        
        return {
            **self.stats,
            'verification_rate_percentage': verification_rate,
            'supported_event_types': len(OPayEventType),
            'business_income_event_types': len(self.business_income_events),
            'cbn_reportable_event_types': len(self.cbn_reportable_events),
            'fraud_detection_enabled': self.fraud_detection_enabled,
            'compliance_monitoring_enabled': self.compliance_monitoring
        }

    def reset_stats(self) -> None:
        """Reset processing statistics."""
        for key in self.stats:
            self.stats[key] = 0
        
        self.logger.info("OPay webhook handler statistics reset")


# Export main classes
__all__ = [
    'OPayWebhookHandler',
    'OPayProcessedWebhookEvent',
    'OPayEventType'
]