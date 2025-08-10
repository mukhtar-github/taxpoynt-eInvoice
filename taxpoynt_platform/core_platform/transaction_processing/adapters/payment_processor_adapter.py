"""
Payment Processor Adapter for Universal Transaction Processing
============================================================

Adapter that bridges payment processor connectors to the Universal Transaction 
Processing pipeline. Transforms payment processor transactions into the universal 
format and ensures they follow the same quality gates as all other connector types.

This enables payment processors (Paystack, Moniepoint, OPay, PalmPay, etc.) to 
leverage the sophisticated transaction processing pipeline while maintaining 
their specialized payment processing features.

Key Features:
- Universal transaction format conversion
- Payment-specific enrichment preservation  
- Nigerian payment compliance integration
- AI classification integration
- Privacy protection compliance
- Webhook event transformation
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from decimal import Decimal

from ..connector_configs.connector_types import ConnectorType
from ..universal_transaction_processor import (
    UniversalTransactionProcessor, UniversalProcessingResult
)
from ..universal_processed_transaction import (
    UniversalProcessedTransaction, ProcessingStatus, TransactionRisk
)

# Import our payment connector framework
from ...external_integrations.connector_framework.base_payment_connector import (
    BasePaymentConnector, PaymentTransaction, PaymentWebhookEvent,
    PaymentStatus, PaymentMethod, TransactionType
)

logger = logging.getLogger(__name__)


@dataclass
class PaymentProcessorTransaction:
    """
    Universal representation of a payment processor transaction.
    
    This acts as the bridge between payment processor specific transactions
    and the universal transaction processing pipeline.
    """
    # Universal identifiers
    id: str
    transaction_id: str
    reference: str
    
    # Payment details  
    amount: Decimal
    currency: str
    payment_method: PaymentMethod
    payment_status: PaymentStatus
    transaction_type: TransactionType
    
    # Timestamps
    created_at: datetime
    updated_at: Optional[datetime] = None
    settled_at: Optional[datetime] = None
    
    # Merchant information
    merchant_id: str
    merchant_name: Optional[str] = None
    merchant_tin: Optional[str] = None
    
    # Customer information (privacy-protected)
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_name: Optional[str] = None
    
    # Transaction details
    description: Optional[str] = None
    channel: Optional[str] = None
    fees: Optional[Decimal] = None
    vat: Optional[Decimal] = None
    
    # Nigerian banking context
    bank_code: Optional[str] = None
    bank_name: Optional[str] = None
    
    # Payment processor specific
    processor_name: str
    processor_transaction_id: str
    gateway_response: Optional[str] = None
    ip_address: Optional[str] = None
    
    # Compliance and enrichment
    is_business_income: Optional[bool] = None
    classification_confidence: Optional[float] = None
    classification_reasoning: Optional[str] = None
    privacy_protected: bool = True
    consent_verified: bool = False
    
    # FIRS compliance
    invoice_generated: bool = False
    invoice_reference: Optional[str] = None
    irn_number: Optional[str] = None
    firs_submitted: bool = False
    
    # Additional metadata
    metadata: Optional[Dict[str, Any]] = None


class PaymentProcessorAdapter:
    """
    Adapter that integrates payment processor connectors with the Universal
    Transaction Processing pipeline.
    
    This allows payment processors to benefit from:
    - Unified fraud detection and risk assessment
    - Nigerian compliance validation
    - Cross-connector customer matching  
    - Consistent invoice generation standards
    - Advanced pattern recognition
    """

    def __init__(
        self,
        universal_processor: UniversalTransactionProcessor,
        processor_mapping: Optional[Dict[str, ConnectorType]] = None
    ):
        """
        Initialize payment processor adapter.
        
        Args:
            universal_processor: Universal transaction processor instance
            processor_mapping: Mapping of processor names to connector types
        """
        self.universal_processor = universal_processor
        self.logger = logging.getLogger(__name__)
        
        # Default processor mapping
        self.processor_mapping = processor_mapping or {
            'paystack': ConnectorType.PAYMENT_PAYSTACK,
            'flutterwave': ConnectorType.PAYMENT_FLUTTERWAVE,
            'moniepoint': ConnectorType.PAYMENT_MONIEPOINT,
            'opay': ConnectorType.PAYMENT_OPAY,
            'palmpay': ConnectorType.PAYMENT_PALMPAY,
            'interswitch': ConnectorType.PAYMENT_INTERSWITCH
        }
        
        # Processing statistics
        self.stats = {
            'total_processed': 0,
            'successful_processed': 0,
            'failed_processed': 0,
            'by_processor': {name: 0 for name in self.processor_mapping.keys()}
        }

    async def process_payment_transaction(
        self,
        payment_transaction: PaymentTransaction,
        processor_name: str,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> UniversalProcessingResult:
        """
        Process a payment transaction through the universal pipeline.
        
        Args:
            payment_transaction: Payment transaction from any processor connector
            processor_name: Name of the payment processor (paystack, moniepoint, etc.)
            additional_context: Additional processing context
            
        Returns:
            UniversalProcessingResult: Result of universal processing
        """
        try:
            self.logger.info(
                f"Processing {processor_name} payment transaction: {payment_transaction.transaction_id}"
            )
            
            # Get connector type
            connector_type = self.processor_mapping.get(processor_name.lower())
            if not connector_type:
                raise ValueError(f"Unknown payment processor: {processor_name}")
            
            # Convert to universal payment transaction format
            universal_payment_tx = self._convert_to_universal_payment_transaction(
                payment_transaction, processor_name
            )
            
            # Process through universal pipeline
            result = await self.universal_processor.process_transaction(
                transaction=universal_payment_tx,
                connector_type=connector_type,
                historical_context=additional_context.get('historical_context') if additional_context else None
            )
            
            # Enhance result with payment-specific metadata
            if result.success and result.processed_transaction:
                await self._enhance_with_payment_metadata(
                    result.processed_transaction,
                    payment_transaction,
                    processor_name
                )
            
            # Update statistics
            self._update_processing_stats(result, processor_name)
            
            self.logger.info(
                f"Completed {processor_name} payment processing: "
                f"{payment_transaction.transaction_id} - Success: {result.success}"
            )
            
            return result
            
        except Exception as e:
            self.logger.error(
                f"Payment processing failed for {processor_name}: "
                f"{payment_transaction.transaction_id} - {str(e)}"
            )
            
            # Create error result
            error_result = UniversalProcessingResult(
                transaction_id=payment_transaction.transaction_id,
                connector_type=self.processor_mapping.get(processor_name.lower()),
                success=False,
                errors=[str(e)]
            )
            
            self._update_processing_stats(error_result, processor_name)
            return error_result

    async def process_payment_batch(
        self,
        payment_transactions: List[PaymentTransaction],
        processor_name: str,
        enable_parallel: bool = True
    ) -> List[UniversalProcessingResult]:
        """
        Process multiple payment transactions in batch.
        
        Args:
            payment_transactions: List of payment transactions
            processor_name: Payment processor name
            enable_parallel: Enable parallel processing
            
        Returns:
            List of UniversalProcessingResult objects
        """
        self.logger.info(
            f"Batch processing {len(payment_transactions)} {processor_name} transactions"
        )
        
        if enable_parallel and len(payment_transactions) > 1:
            # Process in parallel
            tasks = [
                self.process_payment_transaction(tx, processor_name)
                for tx in payment_transactions
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Handle exceptions
            processed_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    error_result = UniversalProcessingResult(
                        transaction_id=payment_transactions[i].transaction_id,
                        connector_type=self.processor_mapping.get(processor_name.lower()),
                        success=False,
                        errors=[str(result)]
                    )
                    processed_results.append(error_result)
                else:
                    processed_results.append(result)
            
            return processed_results
        else:
            # Process sequentially
            results = []
            for tx in payment_transactions:
                result = await self.process_payment_transaction(tx, processor_name)
                results.append(result)
            return results

    async def process_webhook_event(
        self,
        webhook_event: PaymentWebhookEvent,
        processor_name: str
    ) -> Optional[UniversalProcessingResult]:
        """
        Process a payment webhook event through universal pipeline.
        
        Args:
            webhook_event: Payment webhook event
            processor_name: Payment processor name
            
        Returns:
            UniversalProcessingResult if transaction processing triggered
        """
        try:
            self.logger.info(
                f"Processing {processor_name} webhook: {webhook_event.event_type} "
                f"(Transaction: {webhook_event.transaction_id})"
            )
            
            # Only process successful payment events
            if not self._should_process_webhook_event(webhook_event):
                self.logger.debug(f"Webhook event not relevant for processing: {webhook_event.event_type}")
                return None
            
            # Create payment transaction from webhook data
            payment_transaction = self._create_transaction_from_webhook(webhook_event, processor_name)
            
            if payment_transaction:
                # Process through universal pipeline
                result = await self.process_payment_transaction(
                    payment_transaction, 
                    processor_name,
                    additional_context={'webhook_event': asdict(webhook_event)}
                )
                
                return result
            
            return None
            
        except Exception as e:
            self.logger.error(f"Webhook processing failed: {str(e)}")
            return None

    def _convert_to_universal_payment_transaction(
        self,
        payment_transaction: PaymentTransaction,
        processor_name: str
    ) -> PaymentProcessorTransaction:
        """Convert payment transaction to universal format."""
        
        return PaymentProcessorTransaction(
            id=payment_transaction.transaction_id,
            transaction_id=payment_transaction.transaction_id,
            reference=payment_transaction.reference,
            amount=payment_transaction.amount,
            currency=payment_transaction.currency,
            payment_method=payment_transaction.payment_method,
            payment_status=payment_transaction.payment_status,
            transaction_type=payment_transaction.transaction_type,
            created_at=payment_transaction.created_at,
            updated_at=payment_transaction.updated_at,
            settled_at=payment_transaction.settled_at,
            merchant_id=payment_transaction.merchant_id,
            merchant_name=payment_transaction.merchant_name,
            merchant_tin=payment_transaction.merchant_tin,
            customer_email=payment_transaction.customer_email,
            customer_phone=payment_transaction.customer_phone,
            customer_name=payment_transaction.customer_name,
            description=payment_transaction.description,
            channel=payment_transaction.channel,
            fees=payment_transaction.fees,
            vat=payment_transaction.vat,
            bank_code=payment_transaction.bank_code,
            bank_name=payment_transaction.bank_name,
            processor_name=processor_name,
            processor_transaction_id=payment_transaction.transaction_id,
            gateway_response=payment_transaction.gateway_response,
            ip_address=payment_transaction.ip_address,
            invoice_generated=payment_transaction.invoice_generated,
            invoice_reference=payment_transaction.invoice_reference,
            irn_number=payment_transaction.irn_number,
            firs_submitted=payment_transaction.firs_submitted,
            metadata=payment_transaction.metadata
        )

    async def _enhance_with_payment_metadata(
        self,
        processed_transaction: UniversalProcessedTransaction,
        original_payment_tx: PaymentTransaction,
        processor_name: str
    ) -> None:
        """Enhance processed transaction with payment-specific metadata."""
        
        # Add payment processor context
        if not processed_transaction.enrichment_data.metadata:
            processed_transaction.enrichment_data.metadata = {}
        
        processed_transaction.enrichment_data.metadata.update({
            'payment_processor': processor_name,
            'payment_method': original_payment_tx.payment_method.value,
            'payment_channel': original_payment_tx.channel,
            'settlement_status': 'settled' if original_payment_tx.settled_at else 'pending',
            'fees_charged': float(original_payment_tx.fees) if original_payment_tx.fees else 0.0,
            'vat_charged': float(original_payment_tx.vat) if original_payment_tx.vat else 0.0
        })
        
        # Add Nigerian payment context
        if original_payment_tx.bank_code:
            processed_transaction.enrichment_data.metadata['nigerian_bank_code'] = original_payment_tx.bank_code
            processed_transaction.enrichment_data.metadata['nigerian_bank_name'] = original_payment_tx.bank_name
        
        # Payment-specific risk factors
        risk_factors = []
        if original_payment_tx.payment_method.value in ['card', 'international_card']:
            risk_factors.append('card_payment')
        if original_payment_tx.amount > Decimal('1000000'):  # ₦1M threshold
            risk_factors.append('high_value_payment')
        if not original_payment_tx.settled_at:
            risk_factors.append('unsettled_payment')
        
        if risk_factors:
            processed_transaction.enrichment_data.metadata['payment_risk_factors'] = risk_factors

    def _should_process_webhook_event(self, webhook_event: PaymentWebhookEvent) -> bool:
        """Determine if webhook event should trigger transaction processing."""
        
        # Process successful payment events
        success_events = ['charge.success', 'transaction.success', 'payment.success']
        
        return (
            webhook_event.event_type in success_events and
            webhook_event.status == PaymentStatus.SUCCESS and
            webhook_event.transaction_id is not None
        )

    def _create_transaction_from_webhook(
        self,
        webhook_event: PaymentWebhookEvent,
        processor_name: str
    ) -> Optional[PaymentTransaction]:
        """Create payment transaction from webhook event data."""
        
        try:
            # Extract transaction data from webhook
            data = webhook_event.data or {}
            
            return PaymentTransaction(
                transaction_id=webhook_event.transaction_id,
                reference=webhook_event.reference or webhook_event.transaction_id,
                amount=Decimal(str(data.get('amount', 0))),
                currency=data.get('currency', 'NGN'),
                payment_method=PaymentMethod.UNKNOWN,  # Would need to parse from data
                payment_status=webhook_event.status,
                transaction_type=TransactionType.PAYMENT,
                created_at=webhook_event.timestamp,
                merchant_id=data.get('merchant_id', ''),
                description=data.get('description', f'{processor_name} payment'),
                metadata=data
            )
            
        except Exception as e:
            self.logger.error(f"Failed to create transaction from webhook: {str(e)}")
            return None

    def _update_processing_stats(self, result: UniversalProcessingResult, processor_name: str) -> None:
        """Update processing statistics."""
        
        self.stats['total_processed'] += 1
        self.stats['by_processor'][processor_name] += 1
        
        if result.success:
            self.stats['successful_processed'] += 1
        else:
            self.stats['failed_processed'] += 1

    def get_processing_statistics(self) -> Dict[str, Any]:
        """Get comprehensive processing statistics."""
        
        stats = self.stats.copy()
        
        if stats['total_processed'] > 0:
            stats['success_rate'] = stats['successful_processed'] / stats['total_processed']
            stats['failure_rate'] = stats['failed_processed'] / stats['total_processed']
        else:
            stats['success_rate'] = 0.0
            stats['failure_rate'] = 0.0
        
        return stats

    def register_processor(self, processor_name: str, connector_type: ConnectorType) -> None:
        """Register a new payment processor mapping."""
        
        self.processor_mapping[processor_name.lower()] = connector_type
        self.stats['by_processor'][processor_name.lower()] = 0
        
        self.logger.info(f"Registered payment processor: {processor_name} -> {connector_type.value}")


# Factory function for creating the adapter
def create_payment_processor_adapter(
    universal_processor: UniversalTransactionProcessor,
    custom_processor_mapping: Optional[Dict[str, ConnectorType]] = None
) -> PaymentProcessorAdapter:
    """
    Factory function to create payment processor adapter.
    
    Args:
        universal_processor: Universal transaction processor instance
        custom_processor_mapping: Custom processor name to connector type mapping
        
    Returns:
        PaymentProcessorAdapter instance
    """
    return PaymentProcessorAdapter(universal_processor, custom_processor_mapping)


# Export main classes
__all__ = [
    'PaymentProcessorAdapter',
    'PaymentProcessorTransaction', 
    'create_payment_processor_adapter'
]