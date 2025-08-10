"""
Transaction Processor
=====================

Integrated transaction processing pipeline that orchestrates all processing components.
Transforms raw banking transactions into fully processed, validated, and enriched transactions.

Features:
- Complete processing pipeline orchestration
- Multi-stage validation and enrichment
- Error handling and recovery
- Performance optimization
- Batch processing capabilities
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import asyncio
import logging

from ....connector_framework.base_banking_connector import BankTransaction
from .transaction_validator import TransactionValidator, ValidationResult
from .duplicate_detector import DuplicateDetector, DuplicateResult
from .amount_validator import AmountValidator, AmountValidationResult
from .business_rule_engine import BusinessRuleEngine, BusinessRuleEngineResult
from .pattern_matcher import PatternMatcher, PatternResult
from .processed_transaction import (
    ProcessedTransaction, ProcessingStatus, ProcessingMetadata, 
    EnrichmentData, TransactionRisk
)

logger = logging.getLogger(__name__)


class ProcessingStage(Enum):
    """Processing pipeline stages."""
    RAW_INPUT = "raw_input"
    VALIDATION = "validation"
    DUPLICATE_DETECTION = "duplicate_detection"
    AMOUNT_VALIDATION = "amount_validation"
    BUSINESS_RULES = "business_rules"
    PATTERN_MATCHING = "pattern_matching"
    ENRICHMENT = "enrichment"
    FINALIZATION = "finalization"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ProcessingConfig:
    """Configuration for transaction processing."""
    enable_validation: bool = True
    enable_duplicate_detection: bool = True
    enable_amount_validation: bool = True
    enable_business_rules: bool = True
    enable_pattern_matching: bool = True
    enable_customer_matching: bool = True
    
    fail_on_validation_errors: bool = False
    fail_on_duplicates: bool = True
    fail_on_business_rule_violations: bool = False
    fail_on_high_fraud_risk: bool = True
    
    max_processing_time: int = 30  # seconds
    enable_parallel_processing: bool = True
    batch_size: int = 100


@dataclass
class ProcessingResult:
    """Result of transaction processing pipeline."""
    transaction_id: str
    success: bool
    processed_transaction: Optional[ProcessedTransaction] = None
    processing_stage: ProcessingStage = ProcessingStage.RAW_INPUT
    processing_time: float = 0.0
    errors: List[str] = None
    warnings: List[str] = None
    stage_results: Dict[str, Any] = None


class TransactionProcessor:
    """
    Integrated transaction processor that orchestrates the complete processing pipeline.
    
    Coordinates all processing components to transform raw banking transactions
    into fully processed, validated, and enriched transactions ready for invoice generation.
    """
    
    def __init__(
        self,
        validator: TransactionValidator,
        duplicate_detector: DuplicateDetector,
        amount_validator: AmountValidator,
        business_rule_engine: BusinessRuleEngine,
        pattern_matcher: PatternMatcher,
        config: Optional[ProcessingConfig] = None
    ):
        self.validator = validator
        self.duplicate_detector = duplicate_detector
        self.amount_validator = amount_validator
        self.business_rule_engine = business_rule_engine
        self.pattern_matcher = pattern_matcher
        self.config = config or ProcessingConfig()
        
        # Processing pipeline version
        self.pipeline_version = "1.0.0"
        
        # Statistics
        self.stats = {
            'total_processed': 0,
            'successful_processed': 0,
            'failed_processed': 0,
            'stage_failures': {stage.value: 0 for stage in ProcessingStage},
            'average_processing_time': 0.0,
            'total_processing_time': 0.0
        }
    
    async def process_transaction(
        self,
        transaction: BankTransaction,
        historical_context: Optional[List[BankTransaction]] = None
    ) -> ProcessingResult:
        """
        Process a single banking transaction through the complete pipeline.
        
        Args:
            transaction: Raw banking transaction
            historical_context: Historical transactions for context
            
        Returns:
            ProcessingResult with processed transaction and metadata
        """
        start_time = datetime.utcnow()
        
        try:
            logger.info(f"Processing transaction: {transaction.id}")
            
            # Initialize result
            result = ProcessingResult(
                transaction_id=transaction.id,
                success=False,
                processing_stage=ProcessingStage.RAW_INPUT,
                errors=[],
                warnings=[],
                stage_results={}
            )
            
            # Stage 1: Validation
            if self.config.enable_validation:
                result.processing_stage = ProcessingStage.VALIDATION
                validation_result = await self.validator.validate_transaction(transaction)
                result.stage_results['validation'] = validation_result
                
                if not validation_result.is_valid and self.config.fail_on_validation_errors:
                    result.errors.append("Transaction validation failed")
                    result.processing_stage = ProcessingStage.FAILED
                    return result
            else:
                # Create dummy validation result
                validation_result = ValidationResult(
                    is_valid=True,
                    transaction_id=transaction.id,
                    issues=[],
                    validation_timestamp=start_time
                )
            
            # Stage 2: Duplicate Detection
            if self.config.enable_duplicate_detection:
                result.processing_stage = ProcessingStage.DUPLICATE_DETECTION
                duplicate_result = await self.duplicate_detector.check_duplicate(transaction)
                result.stage_results['duplicate_detection'] = duplicate_result
                
                if duplicate_result.is_duplicate and self.config.fail_on_duplicates:
                    result.errors.append("Duplicate transaction detected")
                    result.processing_stage = ProcessingStage.FAILED
                    return result
            else:
                # Create dummy duplicate result
                duplicate_result = DuplicateResult(
                    transaction_id=transaction.id,
                    is_duplicate=False,
                    detection_timestamp=start_time
                )
            
            # Stage 3: Amount Validation (Fraud Detection)
            if self.config.enable_amount_validation:
                result.processing_stage = ProcessingStage.AMOUNT_VALIDATION
                amount_result = await self.amount_validator.validate_amount(
                    transaction, historical_context
                )
                result.stage_results['amount_validation'] = amount_result
                
                if (not amount_result.is_valid or 
                    amount_result.risk_level.value in ['very_high', 'critical']) and \
                   self.config.fail_on_high_fraud_risk:
                    result.errors.append("High fraud risk detected")
                    result.processing_stage = ProcessingStage.FAILED
                    return result
            else:
                # Create dummy amount result
                from .amount_validator import AmountValidationResult, FraudRisk
                amount_result = AmountValidationResult(
                    transaction_id=transaction.id,
                    amount=transaction.amount,
                    is_valid=True,
                    risk_level=FraudRisk.LOW,
                    risk_score=0.1,
                    validation_timestamp=start_time
                )
            
            # Stage 4: Business Rules
            if self.config.enable_business_rules:
                result.processing_stage = ProcessingStage.BUSINESS_RULES
                business_rules_result = await self.business_rule_engine.evaluate_transaction(
                    transaction
                )
                result.stage_results['business_rules'] = business_rules_result
                
                if (business_rules_result.regulatory_violations or 
                    business_rules_result.critical_failures) and \
                   self.config.fail_on_business_rule_violations:
                    result.errors.append("Business rule violations detected")
                    result.processing_stage = ProcessingStage.FAILED
                    return result
            else:
                # Create dummy business rules result
                from .business_rule_engine import BusinessRuleEngineResult, RuleStatus
                business_rules_result = BusinessRuleEngineResult(
                    transaction_id=transaction.id,
                    overall_status=RuleStatus.PASSED,
                    rule_results=[],
                    regulatory_violations=[],
                    critical_failures=[],
                    warnings=[]
                )
            
            # Stage 5: Pattern Matching
            if self.config.enable_pattern_matching:
                result.processing_stage = ProcessingStage.PATTERN_MATCHING
                pattern_result = await self.pattern_matcher.match_patterns(
                    transaction, historical_context
                )
                result.stage_results['pattern_matching'] = pattern_result
            else:
                # Create dummy pattern result
                from .pattern_matcher import PatternResult, TransactionCategory
                pattern_result = PatternResult(
                    transaction_id=transaction.id,
                    primary_category=TransactionCategory.UNKNOWN,
                    confidence_score=0.0,
                    pattern_matches=[],
                    analysis_timestamp=start_time
                )
            
            # Stage 6: Enrichment and Integration
            result.processing_stage = ProcessingStage.ENRICHMENT
            processed_transaction = await self._create_processed_transaction(
                transaction,
                validation_result,
                duplicate_result,
                amount_result,
                business_rules_result,
                pattern_result,
                start_time
            )
            
            # Stage 7: Finalization
            result.processing_stage = ProcessingStage.FINALIZATION
            await self._finalize_processing(processed_transaction, result)
            
            # Success
            result.processed_transaction = processed_transaction
            result.success = True
            result.processing_stage = ProcessingStage.COMPLETED
            
            # Calculate processing time
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            result.processing_time = processing_time
            
            # Update statistics
            self._update_processing_stats(result)
            
            logger.info(f"Transaction processing completed: {transaction.id} - Time: {processing_time:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"Transaction processing failed: {transaction.id} - {e}")
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            error_result = ProcessingResult(
                transaction_id=transaction.id,
                success=False,
                processing_stage=ProcessingStage.FAILED,
                processing_time=processing_time,
                errors=[str(e)]
            )
            
            self._update_processing_stats(error_result)
            return error_result
    
    async def process_batch_transactions(
        self,
        transactions: List[BankTransaction],
        enable_parallel: Optional[bool] = None
    ) -> List[ProcessingResult]:
        """
        Process multiple transactions in batch.
        
        Args:
            transactions: List of raw banking transactions
            enable_parallel: Override parallel processing setting
            
        Returns:
            List of ProcessingResult objects
        """
        logger.info(f"Batch processing {len(transactions)} transactions")
        
        use_parallel = enable_parallel if enable_parallel is not None else self.config.enable_parallel_processing
        
        if use_parallel and len(transactions) > 1:
            return await self._process_batch_parallel(transactions)
        else:
            return await self._process_batch_sequential(transactions)
    
    async def _process_batch_parallel(
        self,
        transactions: List[BankTransaction]
    ) -> List[ProcessingResult]:
        """Process transactions in parallel batches."""
        
        batch_size = self.config.batch_size
        results = []
        
        # Process in chunks to avoid overwhelming the system
        for i in range(0, len(transactions), batch_size):
            batch = transactions[i:i + batch_size]
            logger.debug(f"Processing batch {i//batch_size + 1}: {len(batch)} transactions")
            
            # Create tasks for parallel processing
            tasks = []
            for j, transaction in enumerate(batch):
                # Use previous transactions as historical context
                historical_context = transactions[:i + j] if i + j > 0 else []
                task = self.process_transaction(transaction, historical_context)
                tasks.append(task)
            
            # Execute batch in parallel
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Handle exceptions
            for k, batch_result in enumerate(batch_results):
                if isinstance(batch_result, Exception):
                    logger.error(f"Batch processing failed for transaction: {batch[k].id} - {batch_result}")
                    error_result = ProcessingResult(
                        transaction_id=batch[k].id,
                        success=False,
                        processing_stage=ProcessingStage.FAILED,
                        errors=[str(batch_result)]
                    )
                    results.append(error_result)
                else:
                    results.append(batch_result)
        
        return results
    
    async def _process_batch_sequential(
        self,
        transactions: List[BankTransaction]
    ) -> List[ProcessingResult]:
        """Process transactions sequentially."""
        
        results = []
        
        for i, transaction in enumerate(transactions):
            # Use previous transactions as historical context
            historical_context = transactions[:i] if i > 0 else []
            
            result = await self.process_transaction(transaction, historical_context)
            results.append(result)
        
        return results
    
    async def _create_processed_transaction(
        self,
        transaction: BankTransaction,
        validation_result: ValidationResult,
        duplicate_result: DuplicateResult,
        amount_result: AmountValidationResult,
        business_rules_result: BusinessRuleEngineResult,
        pattern_result: PatternResult,
        start_time: datetime
    ) -> ProcessedTransaction:
        """Create processed transaction from all stage results."""
        
        # Calculate processing duration
        processing_duration = (datetime.utcnow() - start_time).total_seconds()
        
        # Create base processed transaction
        processed_tx = ProcessedTransaction.from_raw_transaction(
            transaction,
            validation_result,
            duplicate_result,
            processing_duration,
            self.pipeline_version
        )
        
        # Enrich with additional data
        await self._enrich_processed_transaction(
            processed_tx,
            amount_result,
            business_rules_result,
            pattern_result
        )
        
        return processed_tx
    
    async def _enrich_processed_transaction(
        self,
        processed_tx: ProcessedTransaction,
        amount_result: AmountValidationResult,
        business_rules_result: BusinessRuleEngineResult,
        pattern_result: PatternResult
    ):
        """Enrich processed transaction with additional data."""
        
        # Update risk level based on amount validation
        if amount_result.risk_level.value in ['high', 'very_high', 'critical']:
            if amount_result.risk_level.value == 'critical':
                processed_tx.processing_metadata.risk_level = TransactionRisk.CRITICAL
            elif amount_result.risk_level.value == 'very_high':
                processed_tx.processing_metadata.risk_level = TransactionRisk.HIGH
            else:
                processed_tx.processing_metadata.risk_level = TransactionRisk.MEDIUM
        
        # Update confidence score
        base_confidence = processed_tx.processing_metadata.confidence_score
        amount_confidence = 1.0 - amount_result.risk_score
        pattern_confidence = pattern_result.confidence_score
        
        # Weighted average confidence
        weights = [0.4, 0.3, 0.3]  # validation, amount, pattern
        confidences = [base_confidence, amount_confidence, pattern_confidence]
        
        weighted_confidence = sum(w * c for w, c in zip(weights, confidences))
        processed_tx.processing_metadata.confidence_score = min(weighted_confidence, 1.0)
        
        # Populate enrichment data
        enrichment = processed_tx.enrichment_data
        
        # Pattern matching results
        enrichment.primary_category = pattern_result.primary_category.value
        enrichment.business_purpose = pattern_result.business_purpose
        enrichment.merchant_identified = pattern_result.merchant_identified
        enrichment.merchant_name = pattern_result.merchant_name
        enrichment.transaction_patterns = pattern_result.pattern_flags
        
        # Amount validation results
        if amount_result.flags:
            enrichment.amount_risk_flags = [flag.value for flag in amount_result.flags]
        
        # Currency information
        enrichment.original_currency = processed_tx.original_transaction.currency
        enrichment.currency_converted = (
            processed_tx.original_transaction.currency and 
            processed_tx.original_transaction.currency.upper() != "NGN"
        )
        
        # Customer matching (would be integrated with actual customer matching system)
        if self.config.enable_customer_matching:
            customer_info = await self._match_customer(processed_tx, pattern_result)
            if customer_info:
                enrichment.customer_matched = True
                enrichment.customer_id = customer_info.get('id')
                enrichment.customer_name = customer_info.get('name')
                enrichment.customer_type = customer_info.get('type')
                enrichment.customer_confidence = customer_info.get('confidence', 0.0)
        
        # Determine final status
        processed_tx.status = self._determine_processing_status(
            processed_tx, business_rules_result
        )
    
    async def _match_customer(
        self,
        processed_tx: ProcessedTransaction,
        pattern_result: PatternResult
    ) -> Optional[Dict[str, Any]]:
        """Match customer information (simplified implementation)."""
        
        # This would integrate with actual customer matching system
        # For now, use pattern results and transaction data
        
        if pattern_result.merchant_identified:
            return {
                'id': f"merchant_{pattern_result.merchant_name}",
                'name': pattern_result.merchant_name,
                'type': 'merchant',
                'confidence': 0.8
            }
        
        # Check for customer indicators in description
        description = processed_tx.description or ""
        if any(keyword in description.lower() for keyword in ['salary', 'wage', 'staff']):
            return {
                'id': f"employee_{processed_tx.account_number}",
                'name': "Employee",
                'type': 'individual',
                'confidence': 0.6
            }
        
        return None
    
    def _determine_processing_status(
        self,
        processed_tx: ProcessedTransaction,
        business_rules_result: BusinessRuleEngineResult
    ) -> ProcessingStatus:
        """Determine final processing status."""
        
        if business_rules_result.regulatory_violations:
            return ProcessingStatus.FAILED
        
        if not processed_tx.is_valid() or processed_tx.is_duplicate():
            return ProcessingStatus.FAILED
        
        if processed_tx.processing_metadata.risk_level == TransactionRisk.CRITICAL:
            return ProcessingStatus.FAILED
        
        if processed_tx.enrichment_data.primary_category:
            return ProcessingStatus.READY_FOR_INVOICE
        
        return ProcessingStatus.ENRICHED
    
    async def _finalize_processing(
        self,
        processed_transaction: ProcessedTransaction,
        result: ProcessingResult
    ):
        """Finalize processing and add final validations."""
        
        # Add processing notes
        notes = []
        
        if processed_transaction.is_duplicate():
            notes.append("Duplicate transaction detected")
        
        if processed_transaction.processing_metadata.risk_level == TransactionRisk.HIGH:
            notes.append("High risk transaction - requires review")
        
        if processed_transaction.enrichment_data.merchant_identified:
            notes.append(f"Merchant identified: {processed_transaction.enrichment_data.merchant_name}")
        
        if processed_transaction.enrichment_data.customer_matched:
            notes.append("Customer successfully matched")
        
        processed_transaction.processing_metadata.processing_notes = notes
        
        # Add warnings to result
        if processed_transaction.processing_metadata.confidence_score < 0.5:
            result.warnings.append("Low confidence processing result")
        
        if processed_transaction.processing_metadata.risk_level in [TransactionRisk.MEDIUM, TransactionRisk.HIGH]:
            result.warnings.append("Transaction flagged for manual review")
    
    def _update_processing_stats(self, result: ProcessingResult):
        """Update processing statistics."""
        
        self.stats['total_processed'] += 1
        self.stats['total_processing_time'] += result.processing_time
        
        if result.success:
            self.stats['successful_processed'] += 1
        else:
            self.stats['failed_processed'] += 1
            self.stats['stage_failures'][result.processing_stage.value] += 1
        
        # Update average processing time
        self.stats['average_processing_time'] = (
            self.stats['total_processing_time'] / self.stats['total_processed']
        )
    
    def get_processing_statistics(self) -> Dict[str, Any]:
        """Get comprehensive processing statistics."""
        
        stats = self.stats.copy()
        
        if stats['total_processed'] > 0:
            stats['success_rate'] = stats['successful_processed'] / stats['total_processed']
            stats['failure_rate'] = stats['failed_processed'] / stats['total_processed']
        else:
            stats['success_rate'] = 0.0
            stats['failure_rate'] = 0.0
        
        # Add component statistics
        stats['component_stats'] = {
            'validator': self.validator.get_validation_statistics(),
            'duplicate_detector': self.duplicate_detector.get_detection_statistics(),
            'amount_validator': self.amount_validator.get_validation_statistics(),
            'business_rules': self.business_rule_engine.get_rule_statistics(),
            'pattern_matcher': self.pattern_matcher.get_pattern_statistics()
        }
        
        return stats
    
    def reset_statistics(self):
        """Reset all processing statistics."""
        
        self.stats = {
            'total_processed': 0,
            'successful_processed': 0,
            'failed_processed': 0,
            'stage_failures': {stage.value: 0 for stage in ProcessingStage},
            'average_processing_time': 0.0,
            'total_processing_time': 0.0
        }
        
        # Reset component statistics
        self.validator.reset_statistics()
        self.duplicate_detector.reset_statistics()
        self.amount_validator.reset_statistics()
        self.business_rule_engine.reset_statistics()
        self.pattern_matcher.reset_statistics()


def create_transaction_processor(
    validator: TransactionValidator,
    duplicate_detector: DuplicateDetector,
    amount_validator: AmountValidator,
    business_rule_engine: BusinessRuleEngine,
    pattern_matcher: PatternMatcher,
    config: Optional[ProcessingConfig] = None
) -> TransactionProcessor:
    """Factory function to create transaction processor."""
    return TransactionProcessor(
        validator,
        duplicate_detector,
        amount_validator,
        business_rule_engine,
        pattern_matcher,
        config
    )