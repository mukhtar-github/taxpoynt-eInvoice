"""
Paystack Payment Processor Connector
===================================

NDPR-compliant Paystack integration with AI-based transaction classification,
privacy protection, and comprehensive Nigerian business pattern recognition.

Key Features:
- Nigerian transaction classification (AI + rule-based fallback)
- NDPR-compliant privacy protection and PII anonymization
- Merchant consent management for data access
- FIRS compliance and automated invoice generation
- Comprehensive audit trails and compliance logging
- Nigerian banking standards integration
- Real-time webhook processing with verification

TaxPoynt Role: Data collector for FIRS compliance, NOT payment processing.
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

from .auth import PaystackAuthManager
from .payment_processor import PaystackPaymentProcessor
from .webhook_handler import PaystackWebhookHandler
from .models import PaystackTransaction, PaystackCustomer, PaystackRefund

logger = logging.getLogger(__name__)


@dataclass
class PaystackConfig:
    """Paystack connector configuration with compliance settings."""
    secret_key: str
    public_key: str
    webhook_secret: str
    test_mode: bool = True
    merchant_email: str = ""
    
    # Nigerian compliance settings
    firs_integration_enabled: bool = True
    auto_invoice_generation: bool = True
    invoice_min_amount: Decimal = Decimal("1000")  # ₦1,000 minimum
    
    # Privacy and consent settings
    privacy_level: PrivacyLevel = PrivacyLevel.STANDARD
    consent_required: bool = True
    data_retention_days: int = 2555  # 7 years for FIRS
    
    # Classification settings
    enable_ai_classification: bool = True
    openai_api_key: Optional[str] = None
    classification_confidence_threshold: float = 0.7
    
    # Rate limiting
    max_requests_per_minute: int = 100
    batch_size: int = 50


@dataclass
class PaymentClassificationResult:
    """Payment transaction classification result."""
    transaction_id: str
    is_business_income: bool
    confidence: float
    reasoning: str
    customer_name: Optional[str] = None
    suggested_invoice_description: Optional[str] = None
    requires_human_review: bool = False
    firs_compliance_notes: List[str] = None
    privacy_protected: bool = True
    consent_verified: bool = False


@dataclass
class MerchantConsentSession:
    """Merchant consent session for payment data access."""
    session_id: str
    merchant_id: str
    merchant_email: str
    consent_type: ConsentType
    status: ConsentStatus
    created_at: datetime
    expires_at: datetime
    data_categories: List[str]
    processing_purposes: List[str]


class PaystackConnector(BasePaymentConnector):
    """
    NDPR-compliant Paystack connector with AI-based classification.
    
    Implements sophisticated transaction classification, privacy protection,
    and consent management following TaxPoynt's proven patterns from
    open banking integration.
    """

    def __init__(self, config: PaystackConfig):
        """
        Initialize Paystack connector with comprehensive compliance.
        
        Args:
            config: PaystackConfig with API credentials and compliance settings
        """
        # Convert to base connector config format
        base_config = {
            'processor_name': 'paystack',
            'merchant_id': config.merchant_email,
            'api_key': config.secret_key,
            'public_key': config.public_key,
            'webhook_secret': config.webhook_secret,
            'test_mode': config.test_mode,
            'firs_integration_enabled': config.firs_integration_enabled,
            'auto_invoice_generation': config.auto_invoice_generation,
            'max_requests_per_minute': config.max_requests_per_minute,
            'batch_size': config.batch_size
        }
        
        super().__init__(base_config)
        
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize core components
        self.auth_manager = PaystackAuthManager({
            'secret_key': config.secret_key,
            'public_key': config.public_key,
            'test_mode': config.test_mode,
            'merchant_email': config.merchant_email
        })
        
        self.payment_processor = PaystackPaymentProcessor(self.auth_manager)
        self.webhook_handler = PaystackWebhookHandler(config.webhook_secret)
        
        # Initialize Nigerian compliance components
        self.transaction_classifier = NigerianTransactionClassifier(
            api_key=config.openai_api_key
        )
        
        self.privacy_protection = APIPrivacyProtection()
        self.pii_redactor = PIIRedactor()
        
        self.consent_manager = ConsentManager()
        self.audit_logger = ComplianceAuditLogger()
        
        # Business logic state
        self.active_consent_sessions: Dict[str, MerchantConsentSession] = {}
        self.classified_transactions: Dict[str, PaymentClassificationResult] = {}
        self.invoice_generation_queue: List[str] = []
        
        # Statistics
        self.stats = {
            'transactions_processed': 0,
            'transactions_classified': 0,
            'invoices_generated': 0,
            'consent_requests': 0,
            'privacy_violations_detected': 0,
            'api_classification_used': 0,
            'rule_based_fallback_used': 0
        }
        
        self.logger.info(f"Paystack connector initialized with Nigerian compliance features")

    async def authenticate(self) -> bool:
        """Authenticate with Paystack API."""
        try:
            success = await self.auth_manager.authenticate()
            
            if success:
                await self.audit_logger.log_event(
                    event_type="authentication_success",
                    details={
                        'processor': 'paystack',
                        'merchant_id': self.config.merchant_email,
                        'mode': 'test' if self.config.test_mode else 'live'
                    }
                )
            
            return success
            
        except Exception as e:
            await self.audit_logger.log_event(
                event_type="authentication_failed",
                details={'processor': 'paystack', 'error': str(e)}
            )
            raise

    async def request_merchant_consent(
        self,
        merchant_id: str,
        merchant_email: str,
        data_categories: List[str],
        processing_purposes: List[str],
        context: Optional[Dict[str, Any]] = None
    ) -> MerchantConsentSession:
        """
        Request consent from merchant for payment data access.
        
        Args:
            merchant_id: Merchant identifier
            merchant_email: Merchant email
            data_categories: Categories of data to be processed
            processing_purposes: Purposes for data processing
            context: Additional context (IP, user agent, etc.)
            
        Returns:
            MerchantConsentSession with consent details
        """
        try:
            # Request consent using consent manager
            consent_record = await self.consent_manager.request_consent(
                user_id=merchant_id,
                consent_type=ConsentType.TRANSACTION_DATA,
                purpose=ConsentPurpose.TAX_COMPLIANCE,
                data_categories=data_categories,
                retention_period=self.config.data_retention_days,
                third_parties=['openai_api'] if self.config.enable_ai_classification else [],
                context=context
            )
            
            # Create session
            session = MerchantConsentSession(
                session_id=consent_record.consent_id,
                merchant_id=merchant_id,
                merchant_email=merchant_email,
                consent_type=ConsentType.TRANSACTION_DATA,
                status=ConsentStatus.PENDING,
                created_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(hours=1),
                data_categories=data_categories,
                processing_purposes=processing_purposes
            )
            
            self.active_consent_sessions[session.session_id] = session
            self.stats['consent_requests'] += 1
            
            await self.audit_logger.log_event(
                event_type="consent_requested",
                details={
                    'merchant_id': merchant_id,
                    'session_id': session.session_id,
                    'data_categories': data_categories,
                    'purposes': processing_purposes
                }
            )
            
            self.logger.info(f"Consent requested for merchant: {merchant_email}")
            return session
            
        except Exception as e:
            self.logger.error(f"Failed to request merchant consent: {str(e)}")
            raise

    async def grant_merchant_consent(
        self,
        session_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Grant merchant consent for data processing.
        
        Args:
            session_id: Consent session identifier
            context: Additional context
            
        Returns:
            True if consent granted successfully
        """
        try:
            # Grant consent
            consent_record = await self.consent_manager.grant_consent(
                consent_id=session_id,
                context=context
            )
            
            # Update session
            if session_id in self.active_consent_sessions:
                session = self.active_consent_sessions[session_id]
                session.status = ConsentStatus.GRANTED
            
            await self.audit_logger.log_event(
                event_type="consent_granted",
                details={
                    'session_id': session_id,
                    'merchant_id': consent_record.user_id
                }
            )
            
            self.logger.info(f"Consent granted for session: {session_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to grant consent: {str(e)}")
            return False

    async def verify_merchant_consent(
        self,
        merchant_id: str,
        consent_type: ConsentType = ConsentType.TRANSACTION_DATA,
        purpose: ConsentPurpose = ConsentPurpose.TAX_COMPLIANCE
    ) -> bool:
        """
        Verify valid merchant consent exists.
        
        Args:
            merchant_id: Merchant identifier
            consent_type: Type of consent required
            purpose: Purpose of data processing
            
        Returns:
            True if valid consent exists
        """
        return await self.consent_manager.check_consent_validity(
            user_id=merchant_id,
            consent_type=consent_type,
            purpose=purpose
        )

    async def get_transactions(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None
    ) -> List[PaymentTransaction]:
        """
        Retrieve payment transactions with classification and privacy protection.
        
        Args:
            filters: Filter criteria
            limit: Maximum number of transactions
            cursor: Pagination cursor
            
        Returns:
            List of classified PaymentTransaction objects
        """
        try:
            # Verify merchant consent if required
            merchant_id = self.config.merchant_email
            if self.config.consent_required:
                has_consent = await self.verify_merchant_consent(merchant_id)
                if not has_consent:
                    raise PermissionError("Valid merchant consent required for transaction access")
            
            # Get transactions from Paystack
            raw_transactions = await self.payment_processor.get_transactions(
                start_date=filters.get('start_date') if filters else None,
                end_date=filters.get('end_date') if filters else None,
                status=filters.get('status') if filters else None,
                limit=limit or self.config.batch_size
            )
            
            # Convert to base PaymentTransaction format
            transactions = []
            for raw_tx in raw_transactions:
                transaction = await self._convert_to_payment_transaction(raw_tx)
                
                # Classify transaction for business income
                classification = await self._classify_transaction(transaction, merchant_id)
                
                # Apply privacy protection
                transaction = await self._apply_privacy_protection(transaction)
                
                # Store classification result
                self.classified_transactions[transaction.transaction_id] = classification
                
                transactions.append(transaction)
                
                # Queue for invoice generation if needed
                if (classification.is_business_income and 
                    self.config.auto_invoice_generation and
                    not classification.requires_human_review):
                    self.invoice_generation_queue.append(transaction.transaction_id)
            
            self.stats['transactions_processed'] += len(transactions)
            
            await self.audit_logger.log_event(
                event_type="transactions_retrieved",
                details={
                    'count': len(transactions),
                    'merchant_id': merchant_id,
                    'filters_applied': filters or {},
                    'privacy_protection_applied': True
                }
            )
            
            return transactions
            
        except Exception as e:
            self.logger.error(f"Error retrieving transactions: {str(e)}")
            raise

    async def _classify_transaction(
        self,
        transaction: PaymentTransaction,
        merchant_id: str
    ) -> PaymentClassificationResult:
        """
        Classify transaction using Nigerian business pattern recognition.
        
        Args:
            transaction: Payment transaction to classify
            merchant_id: Merchant identifier
            
        Returns:
            PaymentClassificationResult with classification details
        """
        try:
            # Build classification request
            user_context = UserContext(
                user_id=merchant_id,
                organization_id=merchant_id,
                business_name=getattr(self.config, 'business_name', 'Unknown'),
                business_context=NigerianBusinessContext(
                    industry='technology',  # Could be configured
                    business_size='sme',
                    location='lagos',
                    state='lagos'
                )
            )
            
            classification_request = TransactionClassificationRequest(
                amount=transaction.amount,
                narration=transaction.description or 'Payment received',
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
            
            # Track classification method used
            if classification_result.metadata.classification_method.startswith('api_'):
                self.stats['api_classification_used'] += 1
            else:
                self.stats['rule_based_fallback_used'] += 1
            
            self.stats['transactions_classified'] += 1
            
            # Convert to our result format
            result = PaymentClassificationResult(
                transaction_id=transaction.transaction_id,
                is_business_income=classification_result.is_business_income,
                confidence=classification_result.confidence,
                reasoning=classification_result.reasoning,
                customer_name=classification_result.customer_name,
                suggested_invoice_description=classification_result.suggested_invoice_description,
                requires_human_review=classification_result.requires_human_review,
                firs_compliance_notes=classification_result.nigerian_compliance_notes or [],
                privacy_protected=True,
                consent_verified=await self.verify_merchant_consent(merchant_id)
            )
            
            await self.audit_logger.log_event(
                event_type="transaction_classified",
                details={
                    'transaction_id': transaction.transaction_id,
                    'is_business_income': result.is_business_income,
                    'confidence': result.confidence,
                    'method': classification_result.metadata.classification_method,
                    'privacy_level': self.config.privacy_level.value
                }
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Transaction classification failed: {str(e)}")
            
            # Fallback classification
            return PaymentClassificationResult(
                transaction_id=transaction.transaction_id,
                is_business_income=False,
                confidence=0.1,
                reasoning=f"Classification failed: {str(e)}",
                requires_human_review=True,
                privacy_protected=True,
                consent_verified=False
            )

    async def _apply_privacy_protection(
        self,
        transaction: PaymentTransaction
    ) -> PaymentTransaction:
        """
        Apply NDPR-compliant privacy protection to transaction data.
        
        Args:
            transaction: Original transaction
            
        Returns:
            Privacy-protected transaction
        """
        try:
            # Detect and redact PII in description
            if transaction.description:
                redacted_description, redaction_report = self.pii_redactor.redact_pii(
                    transaction.description
                )
                
                if redaction_report:
                    self.stats['privacy_violations_detected'] += len(redaction_report)
                    
                    await self.audit_logger.log_event(
                        event_type="pii_detected_and_redacted",
                        details={
                            'transaction_id': transaction.transaction_id,
                            'redactions': redaction_report
                        }
                    )
                
                transaction.description = redacted_description
            
            # Redact sensitive customer information based on privacy level
            if self.config.privacy_level in [PrivacyLevel.HIGH, PrivacyLevel.MAXIMUM]:
                if transaction.customer_email:
                    transaction.customer_email = self._anonymize_email(transaction.customer_email)
                if transaction.customer_phone:
                    transaction.customer_phone = '[PHONE]'
                if transaction.customer_name and self.config.privacy_level == PrivacyLevel.MAXIMUM:
                    transaction.customer_name = '[NAME]'
            
            return transaction
            
        except Exception as e:
            self.logger.error(f"Privacy protection failed: {str(e)}")
            return transaction

    def _anonymize_email(self, email: str) -> str:
        """Anonymize email address while preserving domain for business analysis."""
        try:
            local, domain = email.split('@')
            return f"[EMAIL]@{domain}"
        except:
            return '[EMAIL]'

    async def _convert_to_payment_transaction(
        self,
        paystack_tx: PaystackTransaction
    ) -> PaymentTransaction:
        """Convert PaystackTransaction to base PaymentTransaction."""
        return PaymentTransaction(
            transaction_id=paystack_tx.transaction_id,
            reference=paystack_tx.reference,
            amount=paystack_tx.amount,
            currency=paystack_tx.currency,
            payment_method=paystack_tx.payment_method,
            payment_status=paystack_tx.payment_status,
            transaction_type=paystack_tx.transaction_type,
            created_at=paystack_tx.created_at,
            updated_at=paystack_tx.updated_at,
            settled_at=paystack_tx.settled_at,
            
            # Merchant info
            merchant_id=paystack_tx.merchant_id,
            merchant_name=paystack_tx.merchant_name,
            merchant_tin=paystack_tx.merchant_tin,
            
            # Customer info
            customer_email=paystack_tx.customer_email,
            customer_phone=paystack_tx.customer_phone,
            customer_name=paystack_tx.customer_name,
            
            # Transaction details
            description=paystack_tx.description,
            channel=paystack_tx.channel,
            fees=paystack_tx.fees,
            vat=paystack_tx.vat,
            
            # Nigerian compliance
            bank_code=paystack_tx.bank_code,
            bank_name=paystack_tx.bank_name,
            
            # FIRS fields
            invoice_generated=paystack_tx.invoice_generated,
            invoice_reference=paystack_tx.invoice_reference,
            irn_number=paystack_tx.irn_number,
            firs_submitted=paystack_tx.firs_submitted,
            
            # Metadata
            gateway_response=paystack_tx.gateway_response,
            ip_address=paystack_tx.ip_address,
            metadata=paystack_tx.metadata
        )

    async def get_transaction_by_id(self, transaction_id: str) -> Optional[PaymentTransaction]:
        """Get specific transaction by ID with classification."""
        try:
            paystack_tx = await self.payment_processor.get_transaction_by_id(transaction_id)
            if not paystack_tx:
                return None
                
            transaction = await self._convert_to_payment_transaction(paystack_tx)
            
            # Get cached classification or classify
            if transaction_id in self.classified_transactions:
                classification = self.classified_transactions[transaction_id]
            else:
                classification = await self._classify_transaction(
                    transaction, 
                    self.config.merchant_email
                )
                self.classified_transactions[transaction_id] = classification
            
            return await self._apply_privacy_protection(transaction)
            
        except Exception as e:
            self.logger.error(f"Error retrieving transaction {transaction_id}: {str(e)}")
            return None

    async def get_transaction_by_reference(self, reference: str) -> Optional[PaymentTransaction]:
        """Get specific transaction by reference."""
        try:
            paystack_tx = await self.payment_processor.verify_transaction(reference)
            if not paystack_tx:
                return None
                
            return await self._convert_to_payment_transaction(paystack_tx)
            
        except Exception as e:
            self.logger.error(f"Error retrieving transaction by reference {reference}: {str(e)}")
            return None

    async def process_webhook(self, webhook_data: Dict[str, Any]) -> PaymentWebhookEvent:
        """Process Paystack webhook with classification and privacy protection."""
        try:
            # Verify webhook signature
            verified = await self.webhook_handler.verify_webhook(
                webhook_data.get('payload', ''),
                webhook_data.get('signature', '')
            )
            
            if not verified:
                raise ValueError("Webhook signature verification failed")
            
            # Extract transaction data
            event_data = webhook_data.get('data', {})
            transaction_id = str(event_data.get('id', ''))
            reference = event_data.get('reference', '')
            
            # Process based on event type
            event_type = webhook_data.get('event', '')
            if event_type in ['charge.success', 'transaction.success']:
                # Get full transaction details
                transaction = await self.get_transaction_by_id(transaction_id)
                
                if transaction and self.config.auto_invoice_generation:
                    # Check if needs invoice generation
                    classification = self.classified_transactions.get(transaction_id)
                    if (classification and 
                        classification.is_business_income and 
                        not classification.requires_human_review):
                        self.invoice_generation_queue.append(transaction_id)
                        self.stats['invoices_generated'] += 1
            
            await self.audit_logger.log_event(
                event_type="webhook_processed",
                details={
                    'event_type': event_type,
                    'transaction_id': transaction_id,
                    'reference': reference,
                    'verified': verified
                }
            )
            
            return PaymentWebhookEvent(
                event_type=event_type,
                event_id=webhook_data.get('id', ''),
                timestamp=datetime.utcnow(),
                transaction_id=transaction_id,
                reference=reference,
                status=PaymentStatus.SUCCESS if 'success' in event_type else PaymentStatus.PENDING,
                data=event_data,
                source='paystack',
                verified=verified,
                processed=True
            )
            
        except Exception as e:
            self.logger.error(f"Webhook processing failed: {str(e)}")
            raise

    async def verify_webhook_signature(self, payload: str, signature: str) -> bool:
        """Verify Paystack webhook signature."""
        return await self.webhook_handler.verify_webhook(payload, signature)

    async def get_settlements(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None
    ) -> List[SettlementInfo]:
        """Get settlement information from Paystack."""
        try:
            settlements = await self.payment_processor.get_settlements(
                start_date=filters.get('start_date') if filters else None,
                end_date=filters.get('end_date') if filters else None,
                limit=limit
            )
            
            # Convert to base format (implementation needed)
            return []  # Placeholder
            
        except Exception as e:
            self.logger.error(f"Error retrieving settlements: {str(e)}")
            return []

    async def transform_transaction_to_invoice(
        self,
        transaction_id: str,
        transformation_options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Transform classified transaction to FIRS-compliant invoice."""
        try:
            # Get transaction and classification
            transaction = await self.get_transaction_by_id(transaction_id)
            classification = self.classified_transactions.get(transaction_id)
            
            if not transaction or not classification:
                raise ValueError(f"Transaction or classification not found: {transaction_id}")
            
            if not classification.is_business_income:
                raise ValueError(f"Transaction not classified as business income: {transaction_id}")
            
            # Build FIRS-compliant invoice
            invoice_data = {
                'invoice_header': {
                    'invoice_id': f"INV-{transaction.reference}",
                    'invoice_date': transaction.created_at.isoformat(),
                    'due_date': (transaction.created_at + timedelta(days=30)).isoformat(),
                    'currency': transaction.currency,
                    'exchange_rate': 1.0
                },
                'supplier': {
                    'name': transformation_options.get('supplier_name', 'Unknown Business'),
                    'tin': transformation_options.get('supplier_tin'),
                    'address': transformation_options.get('supplier_address'),
                    'email': self.config.merchant_email
                },
                'customer': {
                    'name': classification.customer_name or transaction.customer_name or 'Unknown Customer',
                    'email': transaction.customer_email,
                    'phone': transaction.customer_phone
                },
                'line_items': [{
                    'description': classification.suggested_invoice_description or transaction.description,
                    'quantity': 1,
                    'unit_price': float(transaction.amount),
                    'total': float(transaction.amount),
                    'vat_rate': 0.075,  # 7.5% Nigerian VAT
                    'vat_amount': float(transaction.amount) * 0.075
                }],
                'totals': {
                    'subtotal': float(transaction.amount),
                    'vat_total': float(transaction.amount) * 0.075,
                    'total': float(transaction.amount) * 1.075
                },
                'payment_info': {
                    'payment_method': transaction.payment_method.value,
                    'payment_reference': transaction.reference,
                    'payment_date': transaction.created_at.isoformat(),
                    'payment_status': 'completed'
                },
                'firs_compliance': {
                    'irn_required': True,
                    'vat_applicable': True,
                    'classification_confidence': classification.confidence,
                    'business_income_verified': classification.is_business_income,
                    'compliance_notes': classification.firs_compliance_notes
                }
            }
            
            await self.audit_logger.log_event(
                event_type="invoice_generated",
                details={
                    'transaction_id': transaction_id,
                    'invoice_id': invoice_data['invoice_header']['invoice_id'],
                    'amount': float(transaction.amount),
                    'classification_confidence': classification.confidence
                }
            )
            
            return invoice_data
            
        except Exception as e:
            self.logger.error(f"Invoice transformation failed: {str(e)}")
            raise

    def get_processing_stats(self) -> Dict[str, Any]:
        """Get comprehensive processing statistics."""
        return {
            **self.stats,
            'classification_accuracy': {
                'total_classified': self.stats['transactions_classified'],
                'api_classifications': self.stats['api_classification_used'],
                'rule_based_fallbacks': self.stats['rule_based_fallback_used'],
                'api_usage_percentage': (
                    self.stats['api_classification_used'] / 
                    max(1, self.stats['transactions_classified']) * 100
                )
            },
            'privacy_compliance': {
                'pii_violations_detected': self.stats['privacy_violations_detected'],
                'privacy_level': self.config.privacy_level.value,
                'consent_compliance': self.config.consent_required
            },
            'firs_compliance': {
                'auto_invoice_enabled': self.config.auto_invoice_generation,
                'invoices_generated': self.stats['invoices_generated'],
                'pending_invoices': len(self.invoice_generation_queue)
            }
        }

    async def get_classification_cost_summary(self) -> Dict[str, Any]:
        """Get AI classification cost summary."""
        return self.transaction_classifier.get_cost_summary()

    def get_pending_invoice_queue(self) -> List[str]:
        """Get pending invoice generation queue."""
        return self.invoice_generation_queue.copy()

    def clear_processed_invoices(self, transaction_ids: List[str]) -> None:
        """Clear processed invoices from queue."""
        for tx_id in transaction_ids:
            if tx_id in self.invoice_generation_queue:
                self.invoice_generation_queue.remove(tx_id)
        
        self.logger.info(f"Cleared {len(transaction_ids)} processed invoices from queue")


# Export main connector
__all__ = [
    'PaystackConnector',
    'PaystackConfig', 
    'PaymentClassificationResult',
    'MerchantConsentSession'
]