"""
Moniepoint Webhook Handler
=========================

Handles and validates Moniepoint webhook events for real-time payment processing.
Implements signature verification and agent banking event processing with Nigerian
business compliance and regulatory requirements.

Features:
- HMAC signature verification
- Agent banking event classification
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

from .models import MoniepointWebhookEvent, MoniepointTransactionType, NIGERIAN_RISK_THRESHOLDS

logger = logging.getLogger(__name__)


class MoniepointEventType(Enum):
    """Moniepoint webhook event types."""
    PAYMENT_SUCCESS = "payment.success"
    PAYMENT_FAILED = "payment.failed"
    TRANSFER_SUCCESS = "transfer.success"
    TRANSFER_FAILED = "transfer.failed"
    AGENT_DEPOSIT = "agent.deposit"
    AGENT_WITHDRAWAL = "agent.withdrawal"
    AGENT_TRANSFER = "agent.transfer"
    BILL_PAYMENT_SUCCESS = "bill_payment.success"
    BILL_PAYMENT_FAILED = "bill_payment.failed"
    SETTLEMENT_COMPLETED = "settlement.completed"
    SETTLEMENT_FAILED = "settlement.failed"
    REFUND_PROCESSED = "refund.processed"
    COMPLIANCE_ALERT = "compliance.alert"
    FRAUD_DETECTED = "fraud.detected"
    AGENT_STATUS_CHANGE = "agent.status_change"
    BUSINESS_VERIFICATION = "business.verification"


@dataclass
class MoniepointProcessedWebhookEvent:
    """Processed webhook event with Nigerian business context."""
    event_id: str
    event_type: MoniepointEventType
    processed_at: datetime
    transaction_id: Optional[str]
    agent_id: Optional[str]
    
    # Business intelligence
    is_business_income: bool
    requires_invoice: bool
    compliance_flags: List[str]
    risk_level: str  # low, medium, high, critical
    
    # Nigerian regulatory context
    cbn_reportable: bool
    firs_reportable: bool
    aml_flags: List[str]
    
    # Processing results
    processing_success: bool
    processing_errors: List[str]
    invoice_triggered: bool
    
    # Original event data
    original_event: MoniepointWebhookEvent


class MoniepointWebhookHandler:
    """
    Handles Moniepoint webhook events with Nigerian regulatory compliance.
    
    Features:
    - Agent banking event processing
    - Business income classification
    - Fraud detection and risk assessment
    - CBN and FIRS compliance automation
    - Real-time invoice generation triggering
    """

    def __init__(self, webhook_secret: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Moniepoint webhook handler.
        
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
            'agent_transactions': 0
        }
        
        # Business income event types (relevant for FIRS compliance)
        self.business_income_events = {
            MoniepointEventType.PAYMENT_SUCCESS,
            MoniepointEventType.TRANSFER_SUCCESS,
            MoniepointEventType.AGENT_DEPOSIT,
            MoniepointEventType.BILL_PAYMENT_SUCCESS
        }
        
        # Events requiring CBN reporting
        self.cbn_reportable_events = {
            MoniepointEventType.PAYMENT_SUCCESS,
            MoniepointEventType.TRANSFER_SUCCESS,
            MoniepointEventType.AGENT_DEPOSIT,
            MoniepointEventType.AGENT_WITHDRAWAL,
            MoniepointEventType.FRAUD_DETECTED
        }

    async def verify_webhook_signature(self, payload: str, signature: str, timestamp: str) -> bool:
        """
        Verify Moniepoint webhook signature using HMAC-SHA256.
        
        Args:
            payload: Raw webhook payload string
            signature: Signature from Moniepoint headers
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
            
            # Create signature string (timestamp + payload)
            signature_string = f"{timestamp}{payload}"
            
            # Compute expected signature
            expected_signature = hmac.new(
                self.webhook_secret.encode('utf-8'),
                signature_string.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            # Compare signatures (timing-safe comparison)
            is_valid = hmac.compare_digest(signature, expected_signature)
            
            if is_valid:
                self.stats['webhooks_verified'] += 1
                self.logger.debug("Moniepoint webhook signature verified successfully")
            else:
                self.stats['webhooks_rejected'] += 1
                self.logger.warning("Invalid Moniepoint webhook signature detected")
            
            return is_valid
            
        except Exception as e:
            self.logger.error(f"Moniepoint webhook signature verification failed: {str(e)}")
            self.stats['webhooks_rejected'] += 1
            return False

    async def process_webhook(
        self,
        payload: str,
        signature: str,
        timestamp: str,
        headers: Optional[Dict[str, str]] = None
    ) -> MoniepointProcessedWebhookEvent:
        """
        Process and validate a Moniepoint webhook event.
        
        Args:
            payload: Raw webhook payload
            signature: Webhook signature
            timestamp: Request timestamp
            headers: HTTP headers from webhook request
            
        Returns:
            MoniepointProcessedWebhookEvent: Processed webhook event
            
        Raises:
            ValueError: If webhook verification fails
            json.JSONDecodeError: If payload is invalid JSON
        """
        try:
            # Verify webhook signature
            if not await self.verify_webhook_signature(payload, signature, timestamp):
                raise ValueError("Moniepoint webhook signature verification failed")
            
            # Parse payload
            webhook_data = json.loads(payload)
            
            # Extract event information
            event_type_str = webhook_data.get('event', '')
            try:
                event_type = MoniepointEventType(event_type_str)
            except ValueError:
                self.logger.warning(f"Unknown Moniepoint event type: {event_type_str}")
                # Handle unknown events gracefully
                event_type = event_type_str
            
            # Build webhook event
            webhook_event = await self._build_webhook_event(
                webhook_data=webhook_data,
                event_type=event_type,
                payload=payload,
                signature_verified=True
            )
            
            # Process with Nigerian business logic
            processed_event = await self._process_nigerian_business_logic(webhook_event)
            
            self.stats['events_processed'] += 1
            
            self.logger.info(
                f"Processed Moniepoint webhook: {event_type} "
                f"(Transaction: {webhook_event.transaction_id}, Agent: {webhook_event.agent_id})"
            )
            
            return processed_event
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in Moniepoint webhook payload: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Moniepoint webhook processing failed: {str(e)}")
            raise

    async def _build_webhook_event(
        self,
        webhook_data: Dict[str, Any],
        event_type: MoniepointEventType,
        payload: str,
        signature_verified: bool
    ) -> MoniepointWebhookEvent:
        """Build structured webhook event from raw data."""
        
        data = webhook_data.get('data', {})
        
        # Extract common fields
        transaction_id = data.get('transaction_id') or data.get('id')
        agent_id = data.get('agent_id')
        
        # Create event object
        webhook_event = MoniepointWebhookEvent(
            event_id=webhook_data.get('id', ''),
            event_type=event_type.value if hasattr(event_type, 'value') else str(event_type),
            event_timestamp=datetime.utcnow(),
            transaction_id=str(transaction_id) if transaction_id else None,
            agent_id=agent_id,
            event_data=data,
            raw_payload=payload,
            verified=signature_verified,
            processed=False
        )
        
        return webhook_event

    async def _process_nigerian_business_logic(
        self,
        webhook_event: MoniepointWebhookEvent
    ) -> MoniepointProcessedWebhookEvent:
        """Apply Nigerian business logic and regulatory compliance."""
        
        try:
            # Initialize processed event
            processed_event = MoniepointProcessedWebhookEvent(
                event_id=webhook_event.event_id,
                event_type=MoniepointEventType(webhook_event.event_type),
                processed_at=datetime.utcnow(),
                transaction_id=webhook_event.transaction_id,
                agent_id=webhook_event.agent_id,
                is_business_income=False,
                requires_invoice=False,
                compliance_flags=[],
                risk_level="low",
                cbn_reportable=False,
                firs_reportable=False,
                aml_flags=[],
                processing_success=True,
                processing_errors=[],
                invoice_triggered=False,
                original_event=webhook_event
            )
            
            # Classify as business income
            await self._classify_business_income(processed_event, webhook_event)
            
            # Assess risk level
            await self._assess_transaction_risk(processed_event, webhook_event)
            
            # Check regulatory compliance
            await self._check_regulatory_compliance(processed_event, webhook_event)
            
            # Determine if invoice should be triggered
            await self._evaluate_invoice_requirement(processed_event, webhook_event)
            
            # Agent banking specific processing
            if webhook_event.agent_id:
                await self._process_agent_banking_logic(processed_event, webhook_event)
                self.stats['agent_transactions'] += 1
            
            # Update statistics
            if processed_event.is_business_income:
                self.stats['business_income_detected'] += 1
            
            if processed_event.requires_invoice:
                self.stats['invoices_triggered'] += 1
                processed_event.invoice_triggered = True
            
            if processed_event.risk_level in ['high', 'critical']:
                self.stats['fraud_alerts'] += 1
            
            if processed_event.compliance_flags:
                self.stats['compliance_violations'] += 1
            
            return processed_event
            
        except Exception as e:
            self.logger.error(f"Nigerian business logic processing failed: {str(e)}")
            
            # Return error state
            return MoniepointProcessedWebhookEvent(
                event_id=webhook_event.event_id,
                event_type=MoniepointEventType(webhook_event.event_type),
                processed_at=datetime.utcnow(),
                transaction_id=webhook_event.transaction_id,
                agent_id=webhook_event.agent_id,
                is_business_income=False,
                requires_invoice=False,
                compliance_flags=['processing_error'],
                risk_level="unknown",
                cbn_reportable=False,
                firs_reportable=False,
                aml_flags=[],
                processing_success=False,
                processing_errors=[str(e)],
                invoice_triggered=False,
                original_event=webhook_event
            )

    async def _classify_business_income(
        self,
        processed_event: MoniepointProcessedWebhookEvent,
        webhook_event: MoniepointWebhookEvent
    ) -> None:
        """Classify if transaction represents business income."""
        
        event_type = processed_event.event_type
        data = webhook_event.event_data
        
        # Check if event type indicates business income
        if event_type in self.business_income_events:
            # Additional checks for business income classification
            amount = data.get('amount', 0)
            transaction_type = data.get('transaction_type', '')
            business_category = data.get('business_category', '')
            
            # Agent banking transactions are often business income
            if webhook_event.agent_id and amount >= self.auto_invoice_threshold:
                processed_event.is_business_income = True
                
            # Specific business transaction types
            business_transaction_types = [
                'business_payment', 'pos_payment', 'merchant_payment',
                'service_payment', 'goods_payment'
            ]
            
            if transaction_type in business_transaction_types:
                processed_event.is_business_income = True
                
            # Business categories that indicate income
            business_categories = [
                'retail', 'wholesale', 'manufacturing', 'services',
                'technology', 'hospitality', 'professional_services'
            ]
            
            if business_category in business_categories:
                processed_event.is_business_income = True

    async def _assess_transaction_risk(
        self,
        processed_event: MoniepointProcessedWebhookEvent,
        webhook_event: MoniepointWebhookEvent
    ) -> None:
        """Assess transaction risk level using Nigerian risk parameters."""
        
        if not self.fraud_detection_enabled:
            return
        
        data = webhook_event.event_data
        amount = data.get('amount', 0)
        
        risk_factors = []
        risk_score = 0
        
        # High value transaction risk
        if amount >= NIGERIAN_RISK_THRESHOLDS['high_value_threshold']:
            risk_factors.append('high_value_transaction')
            risk_score += 30
        
        # Cross-border transaction risk
        if data.get('cross_border', False):
            risk_factors.append('cross_border_transaction')
            risk_score += 25
        
        # Agent banking specific risks
        if webhook_event.agent_id:
            # Check agent daily limits
            if amount >= NIGERIAN_RISK_THRESHOLDS['agent_daily_limit']:
                risk_factors.append('agent_limit_exceeded')
                risk_score += 40
            
            # Unusual agent transaction patterns
            if data.get('transaction_count_today', 0) > 50:
                risk_factors.append('high_velocity_agent')
                risk_score += 20
        
        # Cash transaction reporting threshold
        if (amount >= NIGERIAN_RISK_THRESHOLDS['cash_transaction_reporting_threshold'] and
            data.get('payment_method') == 'cash'):
            risk_factors.append('cash_reporting_threshold')
            risk_score += 35
        
        # Unusual time patterns
        event_hour = webhook_event.event_timestamp.hour
        if event_hour < 6 or event_hour > 22:  # Outside business hours
            risk_factors.append('unusual_time_pattern')
            risk_score += 10
        
        # Determine risk level
        if risk_score >= 70:
            processed_event.risk_level = "critical"
        elif risk_score >= 50:
            processed_event.risk_level = "high"
        elif risk_score >= 30:
            processed_event.risk_level = "medium"
        else:
            processed_event.risk_level = "low"
        
        # Add AML flags for high-risk transactions
        if risk_score >= 50:
            processed_event.aml_flags = risk_factors

    async def _check_regulatory_compliance(
        self,
        processed_event: MoniepointProcessedWebhookEvent,
        webhook_event: MoniepointWebhookEvent
    ) -> None:
        """Check CBN and FIRS regulatory compliance requirements."""
        
        if not self.compliance_monitoring:
            return
        
        event_type = processed_event.event_type
        data = webhook_event.event_data
        amount = data.get('amount', 0)
        
        # CBN reporting requirements
        if event_type in self.cbn_reportable_events:
            processed_event.cbn_reportable = True
            
            # Additional CBN compliance checks
            if amount >= 5000000:  # ₦5M CBN threshold
                processed_event.compliance_flags.append('cbn_large_transaction_reporting')
            
            if data.get('cross_border', False):
                processed_event.compliance_flags.append('cbn_foreign_exchange_reporting')
        
        # FIRS reporting requirements
        if processed_event.is_business_income:
            processed_event.firs_reportable = True
            
            # VAT compliance check
            if amount >= 25000000:  # ₦25M VAT registration threshold
                processed_event.compliance_flags.append('vat_registration_required')
        
        # Agent banking compliance
        if webhook_event.agent_id:
            # Agent banking transaction limits
            if amount >= 2000000:  # ₦2M agent limit
                processed_event.compliance_flags.append('agent_transaction_limit_check')
            
            # KYC requirements
            if data.get('customer_kyc_level', 1) < 2 and amount >= 50000:
                processed_event.compliance_flags.append('kyc_upgrade_required')

    async def _evaluate_invoice_requirement(
        self,
        processed_event: MoniepointProcessedWebhookEvent,
        webhook_event: MoniepointWebhookEvent
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
            MoniepointEventType.PAYMENT_SUCCESS,
            MoniepointEventType.TRANSFER_SUCCESS,
            MoniepointEventType.AGENT_DEPOSIT
        ]
        
        if processed_event.event_type in success_events:
            processed_event.requires_invoice = True

    async def _process_agent_banking_logic(
        self,
        processed_event: MoniepointProcessedWebhookEvent,
        webhook_event: MoniepointWebhookEvent
    ) -> None:
        """Process agent banking specific logic and compliance."""
        
        data = webhook_event.event_data
        
        # Agent transaction classification
        agent_transaction_types = {
            'cash_deposit': MoniepointTransactionType.CASH_DEPOSIT,
            'cash_withdrawal': MoniepointTransactionType.CASH_WITHDRAWAL,
            'funds_transfer': MoniepointTransactionType.FUNDS_TRANSFER,
            'bill_payment': MoniepointTransactionType.BILL_PAYMENT
        }
        
        transaction_type = data.get('transaction_type', '')
        if transaction_type in agent_transaction_types:
            # Additional compliance for agent transactions
            if data.get('amount', 0) >= 1000000:  # ₦1M threshold
                processed_event.compliance_flags.append('agent_large_transaction_monitoring')
        
        # Agent verification status
        agent_verified = data.get('agent_verified', False)
        if not agent_verified:
            processed_event.compliance_flags.append('unverified_agent_transaction')
            processed_event.risk_level = "high"

    def get_supported_events(self) -> List[str]:
        """Get list of supported webhook event types."""
        return [event.value for event in MoniepointEventType]

    def get_processing_stats(self) -> Dict[str, Any]:
        """Get comprehensive webhook processing statistics."""
        
        total_webhooks = self.stats['webhooks_received']
        verification_rate = (
            self.stats['webhooks_verified'] / max(1, total_webhooks) * 100
        )
        
        return {
            **self.stats,
            'verification_rate_percentage': verification_rate,
            'supported_event_types': len(MoniepointEventType),
            'business_income_event_types': len(self.business_income_events),
            'cbn_reportable_event_types': len(self.cbn_reportable_events),
            'fraud_detection_enabled': self.fraud_detection_enabled,
            'compliance_monitoring_enabled': self.compliance_monitoring
        }

    def reset_stats(self) -> None:
        """Reset processing statistics."""
        for key in self.stats:
            self.stats[key] = 0
        
        self.logger.info("Moniepoint webhook handler statistics reset")


# Export main classes
__all__ = [
    'MoniepointWebhookHandler',
    'MoniepointProcessedWebhookEvent',
    'MoniepointEventType'
]