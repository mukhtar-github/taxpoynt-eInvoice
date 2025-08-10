"""
Processed Transaction Model
===========================

Enhanced transaction model that includes validation results, duplicate detection,
and enrichment data from the transaction processing pipeline.

This represents a fully processed and validated banking transaction ready for
invoice generation and FIRS submission.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
from decimal import Decimal
from datetime import datetime

from ....connector_framework.base_banking_connector import BankTransaction
from .transaction_validator import ValidationResult
from .duplicate_detector import DuplicateResult


class ProcessingStatus(Enum):
    """Status of transaction processing."""
    PENDING = "pending"
    VALIDATED = "validated"
    DUPLICATE = "duplicate"
    ENRICHED = "enriched"
    CATEGORIZED = "categorized"
    READY_FOR_INVOICE = "ready_for_invoice"
    FAILED = "failed"


class TransactionRisk(Enum):
    """Risk level assessment for transaction."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ProcessingMetadata:
    """Metadata from transaction processing pipeline."""
    processing_timestamp: datetime
    processing_duration: float
    pipeline_version: str
    validation_passed: bool
    duplicate_detected: bool
    risk_level: TransactionRisk
    confidence_score: float
    processing_notes: List[str] = None


@dataclass
class EnrichmentData:
    """Additional data enriched during processing."""
    customer_matched: bool = False
    customer_confidence: float = 0.0
    customer_id: Optional[str] = None
    customer_name: Optional[str] = None
    customer_type: Optional[str] = None
    
    # Transaction categorization
    primary_category: Optional[str] = None
    sub_category: Optional[str] = None
    business_purpose: Optional[str] = None
    
    # Amount analysis
    amount_risk_flags: List[str] = None
    currency_converted: bool = False
    original_currency: Optional[str] = None
    
    # Pattern matching results
    transaction_patterns: List[str] = None
    merchant_identified: bool = False
    merchant_name: Optional[str] = None


@dataclass
class ProcessedTransaction:
    """
    Fully processed banking transaction with validation, enrichment, and metadata.
    
    This is the primary data structure used by invoice automation components.
    """
    
    # Original transaction data
    original_transaction: BankTransaction
    
    # Processing results
    validation_result: ValidationResult
    duplicate_result: DuplicateResult
    processing_metadata: ProcessingMetadata
    enrichment_data: EnrichmentData
    
    # Processed status
    status: ProcessingStatus
    
    # Computed properties for easy access
    @property
    def id(self) -> str:
        """Transaction ID."""
        return self.original_transaction.id
    
    @property
    def amount(self) -> Decimal:
        """Transaction amount."""
        return self.original_transaction.amount
    
    @property
    def date(self) -> datetime:
        """Transaction date."""
        return self.original_transaction.date
    
    @property
    def description(self) -> str:
        """Transaction description."""
        return self.original_transaction.description
    
    @property
    def account_number(self) -> str:
        """Account number."""
        return self.original_transaction.account_number
    
    @property
    def reference(self) -> str:
        """Transaction reference."""
        return self.original_transaction.reference
    
    @property
    def currency(self) -> str:
        """Transaction currency."""
        return self.original_transaction.currency
    
    @property
    def provider(self) -> str:
        """Banking provider."""
        return self.original_transaction.provider
    
    @property
    def category(self) -> str:
        """Transaction category (enriched if available)."""
        return (self.enrichment_data.primary_category or 
                self.original_transaction.category or 
                "unknown")
    
    # Helper methods
    
    def is_valid(self) -> bool:
        """Check if transaction passed validation."""
        return self.validation_result.is_valid
    
    def is_duplicate(self) -> bool:
        """Check if transaction is detected as duplicate."""
        return self.duplicate_result.is_duplicate
    
    def is_ready_for_invoice(self) -> bool:
        """Check if transaction is ready for invoice generation."""
        return (
            self.status == ProcessingStatus.READY_FOR_INVOICE and
            self.is_valid() and
            not self.is_duplicate() and
            self.processing_metadata.risk_level != TransactionRisk.CRITICAL
        )
    
    def get_customer_info(self) -> Dict[str, Any]:
        """Get enriched customer information."""
        return {
            'id': self.enrichment_data.customer_id,
            'name': self.enrichment_data.customer_name,
            'type': self.enrichment_data.customer_type,
            'matched': self.enrichment_data.customer_matched,
            'confidence': self.enrichment_data.customer_confidence
        }
    
    def get_risk_assessment(self) -> Dict[str, Any]:
        """Get risk assessment information."""
        return {
            'level': self.processing_metadata.risk_level,
            'confidence': self.processing_metadata.confidence_score,
            'flags': self.enrichment_data.amount_risk_flags or [],
            'validation_issues': len(self.validation_result.issues) if self.validation_result.issues else 0,
            'duplicate_matches': len(self.duplicate_result.matches) if self.duplicate_result.matches else 0
        }
    
    def get_categorization_info(self) -> Dict[str, Any]:
        """Get transaction categorization information."""
        return {
            'primary_category': self.enrichment_data.primary_category,
            'sub_category': self.enrichment_data.sub_category,
            'business_purpose': self.enrichment_data.business_purpose,
            'patterns': self.enrichment_data.transaction_patterns or [],
            'merchant_identified': self.enrichment_data.merchant_identified,
            'merchant_name': self.enrichment_data.merchant_name
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'id': self.id,
            'amount': str(self.amount),
            'date': self.date.isoformat(),
            'description': self.description,
            'account_number': self.account_number,
            'reference': self.reference,
            'currency': self.currency,
            'provider': self.provider,
            'category': self.category,
            'status': self.status.value,
            'is_valid': self.is_valid(),
            'is_duplicate': self.is_duplicate(),
            'is_ready_for_invoice': self.is_ready_for_invoice(),
            'customer_info': self.get_customer_info(),
            'risk_assessment': self.get_risk_assessment(),
            'categorization_info': self.get_categorization_info(),
            'processing_metadata': {
                'processing_timestamp': self.processing_metadata.processing_timestamp.isoformat(),
                'processing_duration': self.processing_metadata.processing_duration,
                'pipeline_version': self.processing_metadata.pipeline_version,
                'validation_passed': self.processing_metadata.validation_passed,
                'duplicate_detected': self.processing_metadata.duplicate_detected,
                'risk_level': self.processing_metadata.risk_level.value,
                'confidence_score': self.processing_metadata.confidence_score,
                'processing_notes': self.processing_metadata.processing_notes or []
            }
        }
    
    @classmethod
    def from_raw_transaction(
        cls,
        transaction: BankTransaction,
        validation_result: ValidationResult,
        duplicate_result: DuplicateResult,
        processing_duration: float = 0.0,
        pipeline_version: str = "1.0.0"
    ) -> 'ProcessedTransaction':
        """
        Create ProcessedTransaction from raw transaction and processing results.
        
        Args:
            transaction: Original bank transaction
            validation_result: Validation results
            duplicate_result: Duplicate detection results
            processing_duration: Time taken to process
            pipeline_version: Version of processing pipeline
            
        Returns:
            ProcessedTransaction instance
        """
        
        # Determine risk level
        risk_level = TransactionRisk.LOW
        if duplicate_result.is_duplicate:
            risk_level = TransactionRisk.HIGH
        elif not validation_result.is_valid:
            if validation_result.critical_count > 0:
                risk_level = TransactionRisk.CRITICAL
            elif validation_result.errors_count > 0:
                risk_level = TransactionRisk.HIGH
            elif validation_result.warnings_count > 2:
                risk_level = TransactionRisk.MEDIUM
        
        # Calculate confidence score
        confidence_score = 1.0
        if validation_result.issues:
            confidence_score -= (validation_result.critical_count * 0.3 + 
                               validation_result.errors_count * 0.2 + 
                               validation_result.warnings_count * 0.1)
        if duplicate_result.is_duplicate:
            confidence_score -= 0.5
        confidence_score = max(0.0, confidence_score)
        
        # Determine processing status
        if duplicate_result.is_duplicate:
            status = ProcessingStatus.DUPLICATE
        elif not validation_result.is_valid and validation_result.critical_count > 0:
            status = ProcessingStatus.FAILED
        elif validation_result.is_valid:
            status = ProcessingStatus.VALIDATED
        else:
            status = ProcessingStatus.PENDING
        
        # Create processing metadata
        processing_metadata = ProcessingMetadata(
            processing_timestamp=datetime.utcnow(),
            processing_duration=processing_duration,
            pipeline_version=pipeline_version,
            validation_passed=validation_result.is_valid,
            duplicate_detected=duplicate_result.is_duplicate,
            risk_level=risk_level,
            confidence_score=confidence_score,
            processing_notes=[]
        )
        
        # Create empty enrichment data (to be filled by enrichment pipeline)
        enrichment_data = EnrichmentData()
        
        return cls(
            original_transaction=transaction,
            validation_result=validation_result,
            duplicate_result=duplicate_result,
            processing_metadata=processing_metadata,
            enrichment_data=enrichment_data,
            status=status
        )


# Utility functions for working with processed transactions

def filter_ready_for_invoice(
    processed_transactions: List[ProcessedTransaction]
) -> List[ProcessedTransaction]:
    """Filter transactions that are ready for invoice generation."""
    return [tx for tx in processed_transactions if tx.is_ready_for_invoice()]


def group_by_customer(
    processed_transactions: List[ProcessedTransaction]
) -> Dict[str, List[ProcessedTransaction]]:
    """Group transactions by customer ID."""
    grouped = {}
    
    for tx in processed_transactions:
        customer_id = tx.enrichment_data.customer_id or "unknown"
        if customer_id not in grouped:
            grouped[customer_id] = []
        grouped[customer_id].append(tx)
    
    return grouped


def calculate_batch_statistics(
    processed_transactions: List[ProcessedTransaction]
) -> Dict[str, Any]:
    """Calculate statistics for a batch of processed transactions."""
    
    if not processed_transactions:
        return {}
    
    total_count = len(processed_transactions)
    valid_count = sum(1 for tx in processed_transactions if tx.is_valid())
    duplicate_count = sum(1 for tx in processed_transactions if tx.is_duplicate())
    ready_count = sum(1 for tx in processed_transactions if tx.is_ready_for_invoice())
    
    risk_breakdown = {}
    for risk_level in TransactionRisk:
        risk_breakdown[risk_level.value] = sum(
            1 for tx in processed_transactions 
            if tx.processing_metadata.risk_level == risk_level
        )
    
    total_amount = sum(tx.amount for tx in processed_transactions)
    average_confidence = sum(
        tx.processing_metadata.confidence_score for tx in processed_transactions
    ) / total_count
    
    return {
        'total_transactions': total_count,
        'valid_transactions': valid_count,
        'duplicate_transactions': duplicate_count,
        'ready_for_invoice': ready_count,
        'validation_rate': valid_count / total_count if total_count > 0 else 0,
        'duplicate_rate': duplicate_count / total_count if total_count > 0 else 0,
        'invoice_ready_rate': ready_count / total_count if total_count > 0 else 0,
        'risk_breakdown': risk_breakdown,
        'total_amount': str(total_amount),
        'average_confidence_score': average_confidence
    }