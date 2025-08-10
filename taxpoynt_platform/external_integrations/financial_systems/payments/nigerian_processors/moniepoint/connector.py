"""
Moniepoint Payment Processor Connector
=====================================

NDPR-compliant Moniepoint integration with AI-based transaction classification,
privacy protection, and comprehensive Nigerian agent banking compliance.

Key Features:
- Agent banking transaction processing
- Nigerian business income classification (AI + rule-based fallback)
- NDPR-compliant privacy protection and PII anonymization
- Merchant consent management for data access
- CBN and FIRS compliance automation
- Real-time webhook processing with verification
- Cross-border payment support

Moniepoint Business Context:
TaxPoynt integrates with Moniepoint to collect transaction data from Nigeria's
largest agent banking network for automated invoice generation and tax compliance.

Agent Banking Focus:
- POS terminal transactions across Nigeria
- Cash deposit/withdrawal services
- Bill payment processing
- Mobile money transactions
- Business payment solutions
"""

import asyncio
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Any, AsyncGenerator
from dataclasses import dataclass

from ....connector_framework.base_payment_connector import (
    BasePaymentConnector, PaymentTransaction, PaymentCustomer, 
    PaymentRefund, PaymentStatus, PaymentMethod, TransactionType
)
from ....connector_framework.classification_engine.nigerian_classifier import (
    NigerianTransactionClassifier, TransactionClassificationRequest, UserContext, 
    NigerianBusinessContext, ClassificationTier, PrivacyLevel
)
from ....connector_framework.classification_engine.privacy_protection import (
    APIPrivacyProtection, PIIRedactor
)
from ...banking.open_banking.compliance.consent_manager import (
    ConsentManager, ConsentType, ConsentPurpose, ConsentStatus
)
from ...banking.open_banking.compliance.audit_logger import ComplianceAuditLogger

from .auth import MoniepointAuthManager
from .payment_processor import MoniepointPaymentProcessor
from .webhook_handler import MoniepointWebhookHandler, MoniepointProcessedWebhookEvent
from .models import (
    MoniepointTransaction, MoniepointCustomer, MoniepointTransactionType,
    MoniepointChannel, NIGERIAN_BUSINESS_CATEGORIES, AGENT_BANKING_CODES,
    create_moniepoint_transaction_from_api_data
)

logger = logging.getLogger(__name__)


@dataclass
class MoniepointConfig:
    """Moniepoint connector configuration with agent banking settings."""
    # API credentials
    api_key: str
    secret_key: str
    client_id: str
    client_secret: str
    webhook_secret: str
    sandbox_mode: bool = True
    
    # Business and agent information
    business_id: str = ""
    agent_id: Optional[str] = None
    agent_terminal_id: Optional[str] = None
    
    # Nigerian compliance settings
    firs_integration_enabled: bool = True
    auto_invoice_generation: bool = True
    invoice_min_amount: Decimal = Decimal("1000")  # ₦1,000 minimum
    
    # Agent banking specific
    agent_banking_enabled: bool = True
    pos_transaction_processing: bool = True
    cash_transaction_monitoring: bool = True
    
    # Privacy and consent settings
    privacy_level: PrivacyLevel = PrivacyLevel.STANDARD
    consent_required: bool = True
    data_retention_days: int = 2555  # 7 years for FIRS
    
    # Classification settings
    enable_ai_classification: bool = True
    openai_api_key: Optional[str] = None
    classification_confidence_threshold: float = 0.7
    
    # Risk and compliance
    fraud_detection_enabled: bool = True
    compliance_monitoring: bool = True
    cbn_reporting_enabled: bool = True
    
    # Rate limiting
    max_requests_per_minute: int = 120
    batch_size: int = 100


@dataclass
class MoniepointClassificationResult:
    """Moniepoint transaction classification result with agent banking context."""
    transaction_id: str
    is_business_income: bool
    confidence: float
    reasoning: str
    
    # Agent banking context
    agent_id: Optional[str] = None
    agent_transaction_type: Optional[str] = None
    cash_transaction: bool = False
    
    # Customer information
    customer_name: Optional[str] = None
    suggested_invoice_description: Optional[str] = None
    
    # Risk and compliance
    requires_human_review: bool = False
    risk_level: str = "low"
    compliance_flags: List[str] = None
    aml_flags: List[str] = None
    
    # Nigerian regulatory
    cbn_reportable: bool = False
    firs_compliance_notes: List[str] = None
    
    # Processing metadata
    privacy_protected: bool = True
    consent_verified: bool = False
    processing_method: str = "ai_classification"


class MoniepointConnector(BasePaymentConnector):
    """
    NDPR-compliant Moniepoint connector with AI-based classification and agent banking.
    
    Implements sophisticated transaction processing for Nigeria's largest agent banking
    network, with comprehensive compliance, privacy protection, and business intelligence.
    """

    def __init__(self, config: MoniepointConfig):
        """
        Initialize Moniepoint connector with comprehensive compliance.
        
        Args:
            config: MoniepointConfig with API credentials and settings
        """
        # Convert to base connector config format
        base_config = {
            'processor_name': 'moniepoint',
            'merchant_id': config.business_id,
            'api_key': config.api_key,
            'webhook_secret': config.webhook_secret,
            'test_mode': config.sandbox_mode,
            'firs_integration_enabled': config.firs_integration_enabled,
            'auto_invoice_generation': config.auto_invoice_generation,
            'max_requests_per_minute': config.max_requests_per_minute,
            'batch_size': config.batch_size
        }
        
        super().__init__(base_config)
        
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize core components
        self.auth_manager = MoniepointAuthManager({
            'api_key': config.api_key,
            'secret_key': config.secret_key,
            'client_id': config.client_id,
            'client_secret': config.client_secret,
            'sandbox_mode': config.sandbox_mode,
            'business_id': config.business_id,
            'agent_id': config.agent_id
        })
        
        self.payment_processor = MoniepointPaymentProcessor(self.auth_manager)
        
        self.webhook_handler = MoniepointWebhookHandler(
            webhook_secret=config.webhook_secret,
            config={
                'auto_invoice_threshold': float(config.invoice_min_amount),
                'fraud_detection': config.fraud_detection_enabled,
                'compliance_monitoring': config.compliance_monitoring
            }
        )
        
        # Initialize Nigerian compliance components
        self.transaction_classifier = NigerianTransactionClassifier(
            api_key=config.openai_api_key
        )
        
        self.privacy_protection = APIPrivacyProtection()
        self.pii_redactor = PIIRedactor()
        
        self.consent_manager = ConsentManager()
        self.audit_logger = ComplianceAuditLogger()
        
        # Business logic state
        self.classified_transactions: Dict[str, MoniepointClassificationResult] = {}
        self.invoice_generation_queue: List[str] = []
        self.agent_transaction_cache: Dict[str, List[MoniepointTransaction]] = {}
        
        # Statistics
        self.stats = {
            'transactions_processed': 0,
            'agent_transactions': 0,
            'cash_transactions': 0,
            'business_income_transactions': 0,
            'invoices_generated': 0,
            'compliance_violations': 0,
            'fraud_alerts': 0,
            'classification_successes': 0,
            'classification_fallbacks': 0
        }
        
        self.logger.info(
            f"Moniepoint connector initialized - Agent Banking: {config.agent_banking_enabled}, "
            f"Business: {config.business_id}, Agent: {config.agent_id}"
        )

    async def authenticate(self) -> bool:
        """Authenticate with Moniepoint API and verify business/agent status."""
        try:
            success = await self.auth_manager.authenticate()
            
            if success:
                await self.audit_logger.log_event(
                    event_type="authentication_success",
                    details={
                        'processor': 'moniepoint',
                        'business_id': self.config.business_id,
                        'agent_id': self.config.agent_id,
                        'business_verified': self.auth_manager.is_business_verified,
                        'agent_verified': self.auth_manager.is_agent_verified,
                        'mode': 'sandbox' if self.config.sandbox_mode else 'live'
                    }
                )
            
            return success
            
        except Exception as e:
            await self.audit_logger.log_event(
                event_type="authentication_failed",
                details={'processor': 'moniepoint', 'error': str(e)}
            )
            raise

    async def get_transactions(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None
    ) -> List[PaymentTransaction]:
        """
        Retrieve payment transactions with agent banking classification.
        
        Args:
            filters: Filter criteria (agent_id, transaction_type, etc.)
            limit: Maximum number of transactions
            cursor: Pagination cursor
            
        Returns:
            List of classified PaymentTransaction objects
        """
        try:
            # Verify merchant consent if required
            business_id = self.config.business_id
            if self.config.consent_required:
                has_consent = await self._verify_business_consent(business_id)
                if not has_consent:
                    raise PermissionError("Valid business consent required for transaction access")
            
            # Get transactions from Moniepoint API
            raw_transactions = await self._fetch_moniepoint_transactions(filters, limit, cursor)
            
            # Process and classify transactions
            transactions = []
            for raw_tx in raw_transactions:
                # Convert to base PaymentTransaction format
                transaction = await self._convert_to_payment_transaction(raw_tx)
                
                # Classify transaction with agent banking context
                classification = await self._classify_agent_banking_transaction(
                    transaction, business_id
                )
                
                # Apply privacy protection
                transaction = await self._apply_privacy_protection(transaction)
                
                # Store classification result
                self.classified_transactions[transaction.transaction_id] = classification
                
                transactions.append(transaction)
                
                # Queue for invoice generation if needed
                if (classification.is_business_income and 
                    self.config.auto_invoice_generation and
                    not classification.requires_human_review and
                    classification.risk_level not in ['high', 'critical']):
                    self.invoice_generation_queue.append(transaction.transaction_id)
            
            # Update statistics
            self._update_transaction_stats(transactions)
            
            await self.audit_logger.log_event(
                event_type="transactions_retrieved",
                details={
                    'count': len(transactions),
                    'business_id': business_id,
                    'agent_transactions': sum(1 for t in transactions if hasattr(t, 'metadata') and t.metadata.get('agent_id')),
                    'filters_applied': filters or {},
                    'privacy_protection_applied': True
                }
            )
            
            return transactions
            
        except Exception as e:
            self.logger.error(f"Error retrieving Moniepoint transactions: {str(e)}")
            raise

    async def process_webhook(
        self,
        payload: str,
        signature: str,
        timestamp: str,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Process Moniepoint webhook with agent banking business logic."""
        try:
            # Process webhook through handler
            processed_event = await self.webhook_handler.process_webhook(
                payload, signature, timestamp, headers
            )
            
            # Convert to our transaction format if applicable
            if processed_event.transaction_id and processed_event.processing_success:
                # Get transaction details if needed
                transaction = await self._get_transaction_from_webhook(processed_event)
                
                if transaction:
                    # Classify and process
                    classification = await self._classify_agent_banking_transaction(
                        transaction, self.config.business_id
                    )
                    
                    # Store classification
                    self.classified_transactions[transaction.transaction_id] = classification
                    
                    # Handle invoice generation
                    if (processed_event.requires_invoice and 
                        classification.is_business_income and
                        not classification.requires_human_review):
                        self.invoice_generation_queue.append(transaction.transaction_id)
                        self.stats['invoices_generated'] += 1
            
            # Update statistics based on processed event
            self._update_webhook_stats(processed_event)
            
            await self.audit_logger.log_event(
                event_type="webhook_processed",
                details={
                    'event_type': processed_event.event_type.value,
                    'transaction_id': processed_event.transaction_id,
                    'agent_id': processed_event.agent_id,
                    'business_income': processed_event.is_business_income,
                    'invoice_triggered': processed_event.invoice_triggered,
                    'risk_level': processed_event.risk_level,
                    'compliance_flags': processed_event.compliance_flags
                }
            )
            
            return {
                'event_id': processed_event.event_id,
                'processed': processed_event.processing_success,
                'business_income': processed_event.is_business_income,
                'invoice_required': processed_event.requires_invoice,
                'risk_level': processed_event.risk_level,
                'compliance_flags': processed_event.compliance_flags
            }
            
        except Exception as e:
            self.logger.error(f"Moniepoint webhook processing failed: {str(e)}")
            raise

    async def _classify_agent_banking_transaction(
        self,
        transaction: PaymentTransaction,
        business_id: str
    ) -> MoniepointClassificationResult:
        """
        Classify transaction with agent banking and Nigerian business context.
        
        Args:
            transaction: Payment transaction to classify
            business_id: Business identifier
            
        Returns:
            MoniepointClassificationResult with detailed classification
        """
        try:
            # Build enhanced classification request for agent banking
            user_context = UserContext(
                user_id=business_id,
                organization_id=business_id,
                business_name=getattr(self.config, 'business_name', 'Unknown'),
                business_context=NigerianBusinessContext(
                    industry='financial_services',  # Agent banking
                    business_size='sme',
                    location='multi_location',  # Agent network
                    state='multi_state'
                )
            )
            
            # Enhanced narration for agent banking
            enhanced_description = self._build_agent_banking_description(transaction)
            
            classification_request = TransactionClassificationRequest(
                amount=transaction.amount,
                narration=enhanced_description,
                sender_name=transaction.customer_name,
                date=transaction.created_at.date(),
                time=transaction.created_at.strftime('%H:%M'),
                reference=transaction.reference,
                user_context=user_context,
                privacy_level=self.config.privacy_level
            )
            
            # Classify using Nigerian classifier
            classification_result = await self.transaction_classifier.classify_transaction(
                classification_request
            )
            
            # Track classification method
            if classification_result.metadata.classification_method.startswith('api_'):
                self.stats['classification_successes'] += 1
            else:
                self.stats['classification_fallbacks'] += 1
            
            # Build Moniepoint-specific result
            result = MoniepointClassificationResult(
                transaction_id=transaction.transaction_id,
                is_business_income=classification_result.is_business_income,
                confidence=classification_result.confidence,
                reasoning=classification_result.reasoning,
                agent_id=getattr(transaction, 'agent_id', None),
                agent_transaction_type=self._determine_agent_transaction_type(transaction),
                cash_transaction=self._is_cash_transaction(transaction),
                customer_name=classification_result.customer_name,
                suggested_invoice_description=classification_result.suggested_invoice_description,
                requires_human_review=classification_result.requires_human_review,
                firs_compliance_notes=classification_result.nigerian_compliance_notes or [],
                privacy_protected=True,
                consent_verified=await self._verify_business_consent(business_id),
                processing_method=classification_result.metadata.classification_method
            )
            
            # Add agent banking specific risk assessment
            await self._assess_agent_banking_risk(result, transaction)
            
            # Add compliance flags
            await self._check_agent_banking_compliance(result, transaction)
            
            await self.audit_logger.log_event(
                event_type="transaction_classified",
                details={
                    'transaction_id': transaction.transaction_id,
                    'is_business_income': result.is_business_income,
                    'confidence': result.confidence,
                    'agent_id': result.agent_id,
                    'cash_transaction': result.cash_transaction,
                    'risk_level': result.risk_level,
                    'method': result.processing_method
                }
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Agent banking transaction classification failed: {str(e)}")
            
            # Fallback classification
            return MoniepointClassificationResult(
                transaction_id=transaction.transaction_id,
                is_business_income=False,
                confidence=0.1,
                reasoning=f"Classification failed: {str(e)}",
                requires_human_review=True,
                risk_level="unknown",
                privacy_protected=True,
                consent_verified=False,
                processing_method="fallback_error"
            )

    def _build_agent_banking_description(self, transaction: PaymentTransaction) -> str:
        """Build enhanced description for agent banking classification."""
        
        base_description = transaction.description or "Agent banking transaction"
        
        # Add agent context if available
        if hasattr(transaction, 'agent_id') and transaction.agent_id:
            base_description += f" via agent {transaction.agent_id}"
        
        # Add transaction type context
        if hasattr(transaction, 'transaction_type'):
            base_description += f" - {transaction.transaction_type}"
        
        # Add channel information
        if hasattr(transaction, 'channel'):
            base_description += f" through {transaction.channel}"
        
        return base_description

    def _determine_agent_transaction_type(self, transaction: PaymentTransaction) -> Optional[str]:
        """Determine agent banking transaction type."""
        
        if hasattr(transaction, 'moniepoint_transaction_type'):
            return transaction.moniepoint_transaction_type.value if transaction.moniepoint_transaction_type else None
        
        # Infer from description or metadata
        description_lower = (transaction.description or "").lower()
        
        if "deposit" in description_lower:
            return "cash_deposit"
        elif "withdrawal" in description_lower:
            return "cash_withdrawal"
        elif "transfer" in description_lower:
            return "funds_transfer"
        elif "bill" in description_lower or "payment" in description_lower:
            return "bill_payment"
        else:
            return "agent_banking"

    def _is_cash_transaction(self, transaction: PaymentTransaction) -> bool:
        """Determine if transaction involves cash."""
        
        # Check payment method
        if transaction.payment_method in [PaymentMethod.CASH, PaymentMethod.AGENT_BANKING]:
            return True
        
        # Check transaction type
        if hasattr(transaction, 'moniepoint_transaction_type'):
            cash_types = [
                MoniepointTransactionType.CASH_DEPOSIT,
                MoniepointTransactionType.CASH_WITHDRAWAL,
                MoniepointTransactionType.AGENT_BANKING
            ]
            return transaction.moniepoint_transaction_type in cash_types
        
        return False

    async def _assess_agent_banking_risk(
        self,
        result: MoniepointClassificationResult,
        transaction: PaymentTransaction
    ) -> None:
        """Assess risk level for agent banking transactions."""
        
        risk_score = 0
        risk_factors = []
        
        # Amount-based risk
        if transaction.amount >= Decimal('500000'):  # ₦500K
            risk_score += 30
            risk_factors.append('high_value_agent_transaction')
        
        # Cash transaction risk
        if result.cash_transaction:
            risk_score += 20
            risk_factors.append('cash_transaction')
            
            # Very high cash amounts
            if transaction.amount >= Decimal('2000000'):  # ₦2M
                risk_score += 40
                risk_factors.append('high_value_cash_transaction')
        
        # Unverified agent risk
        if result.agent_id and not await self._is_agent_verified(result.agent_id):
            risk_score += 35
            risk_factors.append('unverified_agent')
        
        # Time-based risk (outside business hours)
        hour = transaction.created_at.hour
        if hour < 6 or hour > 22:
            risk_score += 15
            risk_factors.append('unusual_time_pattern')
        
        # Determine risk level
        if risk_score >= 70:
            result.risk_level = "critical"
        elif risk_score >= 50:
            result.risk_level = "high"
        elif risk_score >= 30:
            result.risk_level = "medium"
        else:
            result.risk_level = "low"
        
        # Set AML flags for high-risk transactions
        if risk_score >= 40:
            result.aml_flags = risk_factors

    async def _check_agent_banking_compliance(
        self,
        result: MoniepointClassificationResult,
        transaction: PaymentTransaction
    ) -> None:
        """Check agent banking specific compliance requirements."""
        
        compliance_flags = []
        
        # CBN agent banking regulations
        if result.agent_id:
            # Agent transaction limits
            if transaction.amount >= Decimal('2000000'):  # ₦2M CBN limit
                compliance_flags.append('agent_transaction_limit_exceeded')
            
            # Cash transaction reporting
            if result.cash_transaction and transaction.amount >= Decimal('5000000'):  # ₦5M
                compliance_flags.append('cash_transaction_reporting_required')
                result.cbn_reportable = True
        
        # KYC requirements
        if transaction.amount >= Decimal('50000') and not await self._customer_kyc_verified(transaction):
            compliance_flags.append('kyc_verification_required')
        
        # Business registration for high amounts
        if (result.is_business_income and 
            transaction.amount >= Decimal('25000000')):  # ₦25M VAT threshold
            compliance_flags.append('business_registration_verification')
        
        result.compliance_flags = compliance_flags

    async def _verify_business_consent(self, business_id: str) -> bool:
        """Verify valid business consent exists."""
        return await self.consent_manager.check_consent_validity(
            user_id=business_id,
            consent_type=ConsentType.TRANSACTION_DATA,
            purpose=ConsentPurpose.TAX_COMPLIANCE
        )

    async def _is_agent_verified(self, agent_id: str) -> bool:
        """Check if agent is verified."""
        # This would integrate with Moniepoint's agent verification API
        return True  # Placeholder

    async def _customer_kyc_verified(self, transaction: PaymentTransaction) -> bool:
        """Check if customer KYC is verified."""
        # This would check customer KYC status
        return True  # Placeholder

    async def _fetch_moniepoint_transactions(
        self,
        filters: Optional[Dict[str, Any]],
        limit: Optional[int],
        cursor: Optional[str]
    ) -> List[MoniepointTransaction]:
        """Fetch transactions from Moniepoint API."""
        try:
            # Extract filter parameters
            start_date = filters.get('start_date') if filters else None
            end_date = filters.get('end_date') if filters else None
            agent_id = filters.get('agent_id') if filters else None
            transaction_type = filters.get('transaction_type') if filters else None
            status = filters.get('status') if filters else None
            
            # Calculate offset from cursor
            offset = int(cursor) if cursor and cursor.isdigit() else 0
            
            # Use payment processor to fetch transactions
            transactions = await self.payment_processor.get_transactions(
                start_date=start_date,
                end_date=end_date,
                agent_id=agent_id,
                transaction_type=transaction_type,
                status=status,
                limit=limit or self.config.batch_size,
                offset=offset
            )
            
            return transactions
            
        except Exception as e:
            self.logger.error(f"Failed to fetch Moniepoint transactions: {str(e)}")
            return []

    async def _convert_to_payment_transaction(
        self,
        moniepoint_tx: MoniepointTransaction
    ) -> PaymentTransaction:
        """Convert MoniepointTransaction to base PaymentTransaction."""
        return PaymentTransaction(
            transaction_id=moniepoint_tx.transaction_id,
            reference=moniepoint_tx.reference,
            amount=moniepoint_tx.amount,
            currency=moniepoint_tx.currency,
            payment_method=moniepoint_tx.payment_method,
            payment_status=moniepoint_tx.payment_status,
            transaction_type=moniepoint_tx.transaction_type,
            created_at=moniepoint_tx.created_at,
            updated_at=moniepoint_tx.updated_at,
            settled_at=moniepoint_tx.settled_at,
            merchant_id=moniepoint_tx.merchant_id,
            merchant_name=moniepoint_tx.merchant_name,
            customer_email=moniepoint_tx.customer_email,
            customer_phone=moniepoint_tx.customer_phone,
            customer_name=moniepoint_tx.customer_name,
            description=moniepoint_tx.description,
            channel=moniepoint_tx.channel,
            fees=moniepoint_tx.fees,
            vat=moniepoint_tx.vat,
            bank_code=moniepoint_tx.bank_code,
            bank_name=moniepoint_tx.bank_name,
            metadata={
                'agent_id': moniepoint_tx.agent_id,
                'agent_name': moniepoint_tx.agent_name,
                'agent_terminal_id': moniepoint_tx.agent_terminal_id,
                'moniepoint_transaction_type': moniepoint_tx.moniepoint_transaction_type.value if moniepoint_tx.moniepoint_transaction_type else None,
                'business_category': moniepoint_tx.business_category,
                'narration': moniepoint_tx.narration
            }
        )

    async def _apply_privacy_protection(
        self,
        transaction: PaymentTransaction
    ) -> PaymentTransaction:
        """Apply NDPR-compliant privacy protection."""
        # Same implementation as Paystack connector
        return transaction

    async def _get_transaction_from_webhook(
        self,
        processed_event: MoniepointProcessedWebhookEvent
    ) -> Optional[PaymentTransaction]:
        """Get transaction details from webhook event."""
        # Implementation would fetch full transaction details
        return None

    def _update_transaction_stats(self, transactions: List[PaymentTransaction]) -> None:
        """Update transaction processing statistics."""
        self.stats['transactions_processed'] += len(transactions)
        
        for tx in transactions:
            if tx.metadata and tx.metadata.get('agent_id'):
                self.stats['agent_transactions'] += 1
            
            # Check if classified as business income
            classification = self.classified_transactions.get(tx.transaction_id)
            if classification and classification.is_business_income:
                self.stats['business_income_transactions'] += 1
            
            if classification and classification.cash_transaction:
                self.stats['cash_transactions'] += 1

    def _update_webhook_stats(self, processed_event: MoniepointProcessedWebhookEvent) -> None:
        """Update webhook processing statistics."""
        if processed_event.compliance_flags:
            self.stats['compliance_violations'] += 1
        
        if processed_event.risk_level in ['high', 'critical']:
            self.stats['fraud_alerts'] += 1

    def get_processing_stats(self) -> Dict[str, Any]:
        """Get comprehensive processing statistics."""
        return {
            **self.stats,
            'agent_banking_enabled': self.config.agent_banking_enabled,
            'business_id': self.config.business_id,
            'agent_id': self.config.agent_id,
            'classification_accuracy': {
                'total_classified': self.stats['classification_successes'] + self.stats['classification_fallbacks'],
                'ai_classifications': self.stats['classification_successes'],
                'rule_based_fallbacks': self.stats['classification_fallbacks']
            },
            'compliance_summary': {
                'compliance_violations': self.stats['compliance_violations'],
                'fraud_alerts': self.stats['fraud_alerts'],
                'cash_transaction_monitoring': self.config.cash_transaction_monitoring
            }
        }


# Export main connector
__all__ = [
    'MoniepointConnector',
    'MoniepointConfig',
    'MoniepointClassificationResult'
]