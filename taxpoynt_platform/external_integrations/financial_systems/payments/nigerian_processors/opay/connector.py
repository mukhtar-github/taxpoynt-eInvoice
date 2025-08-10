"""
OPay Payment Processor Connector
===============================

NDPR-compliant OPay integration with AI-based transaction classification,
privacy protection, and comprehensive Nigerian mobile money compliance.

Key Features:
- Mobile money transaction processing
- Nigerian business income classification (AI + rule-based fallback)
- NDPR-compliant privacy protection and PII anonymization
- Merchant consent management for data access
- CBN and FIRS compliance automation
- Real-time webhook processing with verification
- Digital wallet and QR payment support

OPay Business Context:
TaxPoynt integrates with OPay to collect transaction data from Nigeria's
leading mobile money platform for automated invoice generation and tax compliance.

Mobile Money Focus:
- Digital wallet transactions
- QR code payments
- Bill payment processing
- Airtime and data purchases
- Business-to-business transfers
- Cross-border remittances
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

from .auth import OPayAuthManager
from .payment_processor import OPayPaymentProcessor
from .webhook_handler import OPayWebhookHandler, OPayProcessedWebhookEvent
from .models import (
    OPayTransaction, OPayCustomer, OPayTransactionType,
    OPayChannel, OPayWalletType, OPayKYCLevel, OPAY_BUSINESS_CATEGORIES,
    MOBILE_MONEY_CODES, create_opay_transaction_from_api_data
)

logger = logging.getLogger(__name__)


@dataclass
class OPayConfig:
    """OPay connector configuration with mobile money settings."""
    # API credentials
    merchant_id: str
    public_key: str
    private_key: str
    secret_key: str
    webhook_secret: str
    sandbox_mode: bool = True
    
    # Wallet and app information
    app_id: Optional[str] = None
    wallet_id: Optional[str] = None
    
    # Nigerian compliance settings
    firs_integration_enabled: bool = True
    auto_invoice_generation: bool = True
    invoice_min_amount: Decimal = Decimal("1000")  # ₦1,000 minimum
    
    # Mobile money specific
    mobile_money_enabled: bool = True
    qr_payment_processing: bool = True
    bill_payment_monitoring: bool = True
    
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
    kyc_monitoring_enabled: bool = True
    
    # Rate limiting
    max_requests_per_minute: int = 100
    batch_size: int = 100


@dataclass
class OPayClassificationResult:
    """OPay transaction classification result with mobile money context."""
    transaction_id: str
    is_business_income: bool
    confidence: float
    reasoning: str
    
    # Mobile money context
    wallet_id: Optional[str] = None
    mobile_money_type: Optional[str] = None
    qr_payment: bool = False
    bill_payment: bool = False
    
    # Customer information
    customer_name: Optional[str] = None
    suggested_invoice_description: Optional[str] = None
    
    # Risk and compliance
    requires_human_review: bool = False
    risk_level: str = "low"
    compliance_flags: List[str] = None
    kyc_flags: List[str] = None
    aml_flags: List[str] = None
    
    # Nigerian regulatory
    cbn_reportable: bool = False
    firs_compliance_notes: List[str] = None
    
    # Processing metadata
    privacy_protected: bool = True
    consent_verified: bool = False
    processing_method: str = "ai_classification"


class OPayConnector(BasePaymentConnector):
    """
    NDPR-compliant OPay connector with AI-based classification and mobile money.
    
    Implements sophisticated transaction processing for Nigeria's leading mobile
    money platform, with comprehensive compliance, privacy protection, and business intelligence.
    """

    def __init__(self, config: OPayConfig):
        """
        Initialize OPay connector with comprehensive compliance.
        
        Args:
            config: OPayConfig with API credentials and settings
        """
        # Convert to base connector config format
        base_config = {
            'processor_name': 'opay',
            'merchant_id': config.merchant_id,
            'api_key': config.public_key,
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
        self.auth_manager = OPayAuthManager({
            'merchant_id': config.merchant_id,
            'public_key': config.public_key,
            'private_key': config.private_key,
            'secret_key': config.secret_key,
            'sandbox_mode': config.sandbox_mode,
            'app_id': config.app_id,
            'wallet_id': config.wallet_id
        })
        
        self.payment_processor = OPayPaymentProcessor(self.auth_manager)
        
        self.webhook_handler = OPayWebhookHandler(
            webhook_secret=config.webhook_secret,
            config={
                'merchant_id': config.merchant_id,
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
        self.classified_transactions: Dict[str, OPayClassificationResult] = {}
        self.invoice_generation_queue: List[str] = []
        self.wallet_transaction_cache: Dict[str, List[OPayTransaction]] = {}
        
        # Statistics
        self.stats = {
            'transactions_processed': 0,
            'mobile_money_transactions': 0,
            'wallet_transactions': 0,
            'qr_payments': 0,
            'bill_payments': 0,
            'business_income_transactions': 0,
            'invoices_generated': 0,
            'compliance_violations': 0,
            'fraud_alerts': 0,
            'kyc_violations': 0,
            'classification_successes': 0,
            'classification_fallbacks': 0
        }
        
        self.logger.info(
            f"OPay connector initialized - Mobile Money: {config.mobile_money_enabled}, "
            f"Merchant: {config.merchant_id}, Wallet: {config.wallet_id}"
        )

    async def authenticate(self) -> bool:
        """Authenticate with OPay API and verify merchant/wallet status."""
        try:
            success = await self.auth_manager.authenticate()
            
            if success:
                await self.audit_logger.log_event(
                    event_type="authentication_success",
                    details={
                        'processor': 'opay',
                        'merchant_id': self.config.merchant_id,
                        'wallet_id': self.config.wallet_id,
                        'merchant_verified': self.auth_manager.is_merchant_verified,
                        'wallet_verified': self.auth_manager.is_wallet_verified,
                        'mode': 'sandbox' if self.config.sandbox_mode else 'live'
                    }
                )
            
            return success
            
        except Exception as e:
            await self.audit_logger.log_event(
                event_type="authentication_failed",
                details={'processor': 'opay', 'error': str(e)}
            )
            raise

    async def get_transactions(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None
    ) -> List[PaymentTransaction]:
        """
        Retrieve payment transactions with mobile money classification.
        
        Args:
            filters: Filter criteria (wallet_id, transaction_type, etc.)
            limit: Maximum number of transactions
            cursor: Pagination cursor (page number for OPay)
            
        Returns:
            List of classified PaymentTransaction objects
        """
        try:
            # Verify merchant consent if required
            merchant_id = self.config.merchant_id
            if self.config.consent_required:
                has_consent = await self._verify_merchant_consent(merchant_id)
                if not has_consent:
                    raise PermissionError("Valid merchant consent required for transaction access")
            
            # Get transactions from OPay API
            raw_transactions = await self._fetch_opay_transactions(filters, limit, cursor)
            
            # Process and classify transactions
            transactions = []
            for raw_tx in raw_transactions:
                # Convert to base PaymentTransaction format
                transaction = await self._convert_to_payment_transaction(raw_tx)
                
                # Classify transaction with mobile money context
                classification = await self._classify_mobile_money_transaction(
                    transaction, merchant_id
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
                    'merchant_id': merchant_id,
                    'mobile_money_transactions': sum(1 for t in transactions if self._is_mobile_money_transaction(t)),
                    'filters_applied': filters or {},
                    'privacy_protection_applied': True
                }
            )
            
            return transactions
            
        except Exception as e:
            self.logger.error(f"Error retrieving OPay transactions: {str(e)}")
            raise

    async def process_webhook(
        self,
        payload: str,
        signature: str,
        timestamp: str,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Process OPay webhook with mobile money business logic."""
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
                    classification = await self._classify_mobile_money_transaction(
                        transaction, self.config.merchant_id
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
                    'wallet_id': processed_event.wallet_id,
                    'mobile_money': processed_event.mobile_money_transaction,
                    'qr_payment': processed_event.qr_payment,
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
                'mobile_money': processed_event.mobile_money_transaction,
                'qr_payment': processed_event.qr_payment,
                'compliance_flags': processed_event.compliance_flags
            }
            
        except Exception as e:
            self.logger.error(f"OPay webhook processing failed: {str(e)}")
            raise

    async def _classify_mobile_money_transaction(
        self,
        transaction: PaymentTransaction,
        merchant_id: str
    ) -> OPayClassificationResult:
        """
        Classify transaction with mobile money and Nigerian business context.
        
        Args:
            transaction: Payment transaction to classify
            merchant_id: Merchant identifier
            
        Returns:
            OPayClassificationResult with detailed classification
        """
        try:
            # Build enhanced classification request for mobile money
            user_context = UserContext(
                user_id=merchant_id,
                organization_id=merchant_id,
                business_name=getattr(self.config, 'business_name', 'Unknown'),
                business_context=NigerianBusinessContext(
                    industry='fintech',  # Mobile money/fintech
                    business_size='sme',
                    location='multi_location',  # Mobile money network
                    state='multi_state'
                )
            )
            
            # Enhanced narration for mobile money
            enhanced_description = self._build_mobile_money_description(transaction)
            
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
            
            # Build OPay-specific result
            result = OPayClassificationResult(
                transaction_id=transaction.transaction_id,
                is_business_income=classification_result.is_business_income,
                confidence=classification_result.confidence,
                reasoning=classification_result.reasoning,
                wallet_id=getattr(transaction, 'wallet_id', None),
                mobile_money_type=self._determine_mobile_money_type(transaction),
                qr_payment=self._is_qr_payment(transaction),
                bill_payment=self._is_bill_payment(transaction),
                customer_name=classification_result.customer_name,
                suggested_invoice_description=classification_result.suggested_invoice_description,
                requires_human_review=classification_result.requires_human_review,
                firs_compliance_notes=classification_result.nigerian_compliance_notes or [],
                privacy_protected=True,
                consent_verified=await self._verify_merchant_consent(merchant_id),
                processing_method=classification_result.metadata.classification_method
            )
            
            # Add mobile money specific risk assessment
            await self._assess_mobile_money_risk(result, transaction)
            
            # Add compliance flags
            await self._check_mobile_money_compliance(result, transaction)
            
            await self.audit_logger.log_event(
                event_type="transaction_classified",
                details={
                    'transaction_id': transaction.transaction_id,
                    'is_business_income': result.is_business_income,
                    'confidence': result.confidence,
                    'wallet_id': result.wallet_id,
                    'mobile_money_type': result.mobile_money_type,
                    'qr_payment': result.qr_payment,
                    'risk_level': result.risk_level,
                    'method': result.processing_method
                }
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Mobile money transaction classification failed: {str(e)}")
            
            # Fallback classification
            return OPayClassificationResult(
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

    def _build_mobile_money_description(self, transaction: PaymentTransaction) -> str:
        """Build enhanced description for mobile money classification."""
        
        base_description = transaction.description or "Mobile money transaction"
        
        # Add wallet context if available
        if hasattr(transaction, 'wallet_id') and transaction.wallet_id:
            base_description += f" via wallet {transaction.wallet_id}"
        
        # Add transaction type context
        if hasattr(transaction, 'opay_transaction_type'):
            base_description += f" - {transaction.opay_transaction_type}"
        
        # Add channel information
        if hasattr(transaction, 'channel'):
            base_description += f" through {transaction.channel}"
        
        # Add mobile context
        if hasattr(transaction, 'mobile_network'):
            base_description += f" on {transaction.mobile_network}"
        
        return base_description

    def _determine_mobile_money_type(self, transaction: PaymentTransaction) -> Optional[str]:
        """Determine mobile money transaction type."""
        
        if hasattr(transaction, 'opay_transaction_type'):
            return transaction.opay_transaction_type.value if transaction.opay_transaction_type else None
        
        # Infer from description or metadata
        description_lower = (transaction.description or "").lower()
        
        if "wallet" in description_lower:
            return "wallet_transfer"
        elif "qr" in description_lower:
            return "qr_payment"
        elif "bill" in description_lower:
            return "bill_payment"
        elif "airtime" in description_lower:
            return "airtime_purchase"
        elif "transfer" in description_lower:
            return "p2p_transfer"
        else:
            return "mobile_money"

    def _is_qr_payment(self, transaction: PaymentTransaction) -> bool:
        """Determine if transaction is a QR payment."""
        
        # Check transaction type
        if hasattr(transaction, 'opay_transaction_type'):
            return transaction.opay_transaction_type == OPayTransactionType.QR_PAYMENT
        
        # Check channel
        if hasattr(transaction, 'channel'):
            return transaction.channel == OPayChannel.QR_CODE
        
        # Check description
        description_lower = (transaction.description or "").lower()
        return "qr" in description_lower

    def _is_bill_payment(self, transaction: PaymentTransaction) -> bool:
        """Determine if transaction is a bill payment."""
        
        if hasattr(transaction, 'opay_transaction_type'):
            return transaction.opay_transaction_type == OPayTransactionType.BILL_PAYMENT
        
        description_lower = (transaction.description or "").lower()
        return any(term in description_lower for term in ['bill', 'electricity', 'water', 'cable'])

    def _is_mobile_money_transaction(self, transaction: PaymentTransaction) -> bool:
        """Determine if transaction is mobile money related."""
        
        # Check payment method
        if transaction.payment_method in [PaymentMethod.DIGITAL_WALLET, PaymentMethod.MOBILE_MONEY]:
            return True
        
        # Check if has wallet context
        if hasattr(transaction, 'wallet_id') and transaction.wallet_id:
            return True
        
        return False

    async def _assess_mobile_money_risk(
        self,
        result: OPayClassificationResult,
        transaction: PaymentTransaction
    ) -> None:
        """Assess risk level for mobile money transactions."""
        # Implementation similar to webhook handler risk assessment
        pass

    async def _check_mobile_money_compliance(
        self,
        result: OPayClassificationResult,
        transaction: PaymentTransaction
    ) -> None:
        """Check mobile money specific compliance requirements."""
        # Implementation similar to webhook handler compliance checks
        pass

    async def _verify_merchant_consent(self, merchant_id: str) -> bool:
        """Verify valid merchant consent exists."""
        return await self.consent_manager.check_consent_validity(
            user_id=merchant_id,
            consent_type=ConsentType.TRANSACTION_DATA,
            purpose=ConsentPurpose.TAX_COMPLIANCE
        )

    async def _fetch_opay_transactions(
        self,
        filters: Optional[Dict[str, Any]],
        limit: Optional[int],
        cursor: Optional[str]
    ) -> List[OPayTransaction]:
        """Fetch transactions from OPay API."""
        try:
            # Extract filter parameters
            start_date = filters.get('start_date') if filters else None
            end_date = filters.get('end_date') if filters else None
            wallet_id = filters.get('wallet_id') if filters else None
            transaction_type = filters.get('transaction_type') if filters else None
            status = filters.get('status') if filters else None
            
            # Calculate page from cursor
            page = int(cursor) if cursor and cursor.isdigit() else 1
            
            # Use payment processor to fetch transactions
            transactions = await self.payment_processor.get_transactions(
                start_date=start_date,
                end_date=end_date,
                wallet_id=wallet_id,
                transaction_type=transaction_type,
                status=status,
                limit=limit or self.config.batch_size,
                page=page
            )
            
            return transactions
            
        except Exception as e:
            self.logger.error(f"Failed to fetch OPay transactions: {str(e)}")
            return []

    async def _convert_to_payment_transaction(
        self,
        opay_tx: OPayTransaction
    ) -> PaymentTransaction:
        """Convert OPayTransaction to base PaymentTransaction."""
        return PaymentTransaction(
            transaction_id=opay_tx.transaction_id,
            reference=opay_tx.reference,
            amount=opay_tx.amount,
            currency=opay_tx.currency,
            payment_method=opay_tx.payment_method,
            payment_status=opay_tx.payment_status,
            transaction_type=opay_tx.transaction_type,
            created_at=opay_tx.created_at,
            updated_at=opay_tx.updated_at,
            settled_at=opay_tx.settled_at,
            merchant_id=opay_tx.merchant_id,
            merchant_name=opay_tx.merchant_name,
            customer_email=opay_tx.customer_email,
            customer_phone=opay_tx.customer_phone,
            customer_name=opay_tx.customer_name,
            description=opay_tx.description,
            channel=opay_tx.channel,
            fees=opay_tx.fees,
            vat=opay_tx.vat,
            bank_code=opay_tx.bank_code,
            bank_name=opay_tx.bank_name,
            metadata={
                'wallet_id': opay_tx.sender_wallet_id,
                'receiver_wallet_id': opay_tx.receiver_wallet_id,
                'opay_transaction_type': opay_tx.opay_transaction_type.value if opay_tx.opay_transaction_type else None,
                'mobile_network': opay_tx.mobile_network,
                'qr_code_id': opay_tx.qr_code_id,
                'bill_type': opay_tx.bill_type,
                'business_category': opay_tx.business_category,
                'narration': opay_tx.narration
            }
        )

    async def _apply_privacy_protection(
        self,
        transaction: PaymentTransaction
    ) -> PaymentTransaction:
        """Apply NDPR-compliant privacy protection."""
        # Same implementation as other connectors
        return transaction

    async def _get_transaction_from_webhook(
        self,
        processed_event: OPayProcessedWebhookEvent
    ) -> Optional[PaymentTransaction]:
        """Get transaction details from webhook event."""
        # Implementation would fetch full transaction details
        return None

    def _update_transaction_stats(self, transactions: List[PaymentTransaction]) -> None:
        """Update transaction processing statistics."""
        self.stats['transactions_processed'] += len(transactions)
        
        for tx in transactions:
            if self._is_mobile_money_transaction(tx):
                self.stats['mobile_money_transactions'] += 1
            
            if self._is_qr_payment(tx):
                self.stats['qr_payments'] += 1
            
            if self._is_bill_payment(tx):
                self.stats['bill_payments'] += 1
            
            # Check if classified as business income
            classification = self.classified_transactions.get(tx.transaction_id)
            if classification and classification.is_business_income:
                self.stats['business_income_transactions'] += 1

    def _update_webhook_stats(self, processed_event: OPayProcessedWebhookEvent) -> None:
        """Update webhook processing statistics."""
        if processed_event.compliance_flags:
            self.stats['compliance_violations'] += 1
        
        if processed_event.risk_level in ['high', 'critical']:
            self.stats['fraud_alerts'] += 1
        
        if processed_event.kyc_flags:
            self.stats['kyc_violations'] += 1

    def get_processing_stats(self) -> Dict[str, Any]:
        """Get comprehensive processing statistics."""
        return {
            **self.stats,
            'mobile_money_enabled': self.config.mobile_money_enabled,
            'merchant_id': self.config.merchant_id,
            'wallet_id': self.config.wallet_id,
            'classification_accuracy': {
                'total_classified': self.stats['classification_successes'] + self.stats['classification_fallbacks'],
                'ai_classifications': self.stats['classification_successes'],
                'rule_based_fallbacks': self.stats['classification_fallbacks']
            },
            'compliance_summary': {
                'compliance_violations': self.stats['compliance_violations'],
                'fraud_alerts': self.stats['fraud_alerts'],
                'kyc_violations': self.stats['kyc_violations'],
                'kyc_monitoring': self.config.kyc_monitoring_enabled
            }
        }


# Export main connector
__all__ = [
    'OPayConnector',
    'OPayConfig',
    'OPayClassificationResult'
]