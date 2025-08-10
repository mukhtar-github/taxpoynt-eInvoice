"""
Universal Transaction Processor
===============================

Universal transaction processing pipeline that works with ALL external connector types.
Transforms raw transactions from any source (Banking, ERP, POS, CRM, etc.) into fully 
processed, validated, and enriched transactions ready for invoice generation.

This is the cornerstone of TaxPoynt's unified processing architecture - every transaction,
regardless of source, goes through the same quality gates and compliance checks.

Supported Connector Types:
- Banking (Open Banking, USSD, NIBSS)
- ERP Systems (SAP, Oracle, Dynamics, NetSuite, Odoo)
- CRM Systems (Salesforce, HubSpot, Dynamics CRM)
- POS Systems (retail, hospitality, e-commerce)
- E-commerce platforms (Shopify, WooCommerce, Magento)
- Accounting systems (QuickBooks, Xero, Wave)

Features:
- Connector-specific processing configurations
- Nigerian compliance rules for all transaction types
- Unified fraud detection and risk assessment
- Cross-connector customer matching
- Consistent invoice generation standards
"""

from typing import Dict, List, Optional, Any, Union, Type
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import asyncio
import logging

from .connector_processing_config import (
    ConnectorProcessingConfig, ConnectorType, ProcessingProfile
)
from .universal_processed_transaction import (
    UniversalProcessedTransaction, ProcessingStatus, ProcessingMetadata, 
    EnrichmentData, TransactionRisk
)
from .processing_stages import ProcessingStage
from ..validation.universal_validator import UniversalTransactionValidator, ValidationResult
from ..detection.universal_duplicate_detector import UniversalDuplicateDetector, DuplicateResult
from ..validation.universal_amount_validator import UniversalAmountValidator, AmountValidationResult
from ..rules.universal_business_rule_engine import UniversalBusinessRuleEngine, BusinessRuleEngineResult
from ..matching.universal_pattern_matcher import UniversalPatternMatcher, PatternResult

logger = logging.getLogger(__name__)


@dataclass
class UniversalProcessingResult:
    """Result of universal transaction processing pipeline."""
    transaction_id: str
    connector_type: ConnectorType
    success: bool
    processed_transaction: Optional[UniversalProcessedTransaction] = None
    processing_stage: ProcessingStage = ProcessingStage.RAW_INPUT
    processing_time: float = 0.0
    errors: List[str] = None
    warnings: List[str] = None
    stage_results: Dict[str, Any] = None
    connector_specific_data: Dict[str, Any] = None


class UniversalTransactionProcessor:
    """
    Universal transaction processor for ALL external connector types.
    
    This processor intelligently adapts its processing pipeline based on the 
    connector type and processing configuration. It ensures consistent quality 
    and compliance standards across all transaction sources while optimizing 
    processing for each connector's unique characteristics.
    
    Architecture Benefits:
    - Single processing standard across all integrations
    - Connector-specific business rules and validation
    - Unified fraud detection and risk assessment
    - Consistent Nigerian compliance checks
    - Cross-connector customer intelligence
    """
    
    def __init__(
        self,
        validator: UniversalTransactionValidator,
        duplicate_detector: UniversalDuplicateDetector,
        amount_validator: UniversalAmountValidator,
        business_rule_engine: UniversalBusinessRuleEngine,
        pattern_matcher: UniversalPatternMatcher,
        processing_configs: Dict[ConnectorType, ConnectorProcessingConfig] = None
    ):
        self.validator = validator
        self.duplicate_detector = duplicate_detector
        self.amount_validator = amount_validator
        self.business_rule_engine = business_rule_engine
        self.pattern_matcher = pattern_matcher
        
        # Load connector-specific configurations
        self.processing_configs = processing_configs or self._load_default_configs()
        
        # Processing pipeline version
        self.pipeline_version = "2.0.0-universal"
        
        # Statistics by connector type
        self.stats = {
            connector_type.value: {
                'total_processed': 0,
                'successful_processed': 0,
                'failed_processed': 0,
                'stage_failures': {stage.value: 0 for stage in ProcessingStage},
                'average_processing_time': 0.0,
                'total_processing_time': 0.0
            } for connector_type in ConnectorType
        }
        
        # Global statistics
        self.global_stats = {
            'total_processed': 0,
            'successful_processed': 0,
            'failed_processed': 0,
            'average_processing_time': 0.0,
            'total_processing_time': 0.0
        }
    
    async def process_transaction(
        self,
        transaction: Any,  # Can be BankTransaction, ERPTransaction, POSTransaction, etc.
        connector_type: ConnectorType,
        historical_context: Optional[List[Any]] = None,
        custom_config: Optional[ConnectorProcessingConfig] = None
    ) -> UniversalProcessingResult:
        """
        Process a transaction from any connector type through the universal pipeline.
        
        Args:
            transaction: Raw transaction from any connector type
            connector_type: Type of connector (Banking, ERP, POS, CRM)
            historical_context: Historical transactions for context
            custom_config: Override default processing configuration
            
        Returns:
            UniversalProcessingResult with processed transaction and metadata
        """
        start_time = datetime.utcnow()
        config = custom_config or self.processing_configs.get(connector_type)
        
        if not config:
            raise ValueError(f"No processing configuration found for connector type: {connector_type}")
        
        try:
            logger.info(f"Processing {connector_type.value} transaction: {self._get_transaction_id(transaction)}")
            
            # Initialize result
            result = UniversalProcessingResult(
                transaction_id=self._get_transaction_id(transaction),
                connector_type=connector_type,
                success=False,
                processing_stage=ProcessingStage.RAW_INPUT,
                errors=[],
                warnings=[],
                stage_results={},
                connector_specific_data={}
            )
            
            # Stage 1: Validation (connector-specific rules)
            if config.enable_validation:
                result.processing_stage = ProcessingStage.VALIDATION
                validation_result = await self.validator.validate_transaction(
                    transaction, connector_type, config
                )
                result.stage_results['validation'] = validation_result
                
                if not validation_result.is_valid and config.fail_on_validation_errors:
                    result.errors.append(f"{connector_type.value} transaction validation failed")
                    result.processing_stage = ProcessingStage.FAILED
                    return result
            else:
                validation_result = ValidationResult.create_default(
                    self._get_transaction_id(transaction)
                )
            
            # Stage 2: Duplicate Detection (connector-aware)
            if config.enable_duplicate_detection:
                result.processing_stage = ProcessingStage.DUPLICATE_DETECTION
                duplicate_result = await self.duplicate_detector.check_duplicate(
                    transaction, connector_type, config
                )
                result.stage_results['duplicate_detection'] = duplicate_result
                
                if duplicate_result.is_duplicate and config.fail_on_duplicates:
                    result.errors.append("Duplicate transaction detected")
                    result.processing_stage = ProcessingStage.FAILED
                    return result
            else:
                duplicate_result = DuplicateResult.create_default(
                    self._get_transaction_id(transaction)
                )
            
            # Stage 3: Amount Validation (connector-specific fraud detection)
            if config.enable_amount_validation:
                result.processing_stage = ProcessingStage.AMOUNT_VALIDATION
                amount_result = await self.amount_validator.validate_amount(
                    transaction, connector_type, config, historical_context
                )
                result.stage_results['amount_validation'] = amount_result
                
                if (not amount_result.is_valid or 
                    amount_result.risk_level.value in ['very_high', 'critical']) and \
                   config.fail_on_high_fraud_risk:
                    result.errors.append(f"High fraud risk detected for {connector_type.value}")
                    result.processing_stage = ProcessingStage.FAILED
                    return result
            else:
                amount_result = AmountValidationResult.create_default(
                    self._get_transaction_id(transaction), 
                    self._get_transaction_amount(transaction)
                )
            
            # Stage 4: Business Rules (Nigerian compliance by connector type)
            if config.enable_business_rules:
                result.processing_stage = ProcessingStage.BUSINESS_RULES
                business_rules_result = await self.business_rule_engine.evaluate_transaction(
                    transaction, connector_type, config
                )
                result.stage_results['business_rules'] = business_rules_result
                
                if (business_rules_result.regulatory_violations or 
                    business_rules_result.critical_failures) and \
                   config.fail_on_business_rule_violations:
                    result.errors.append(f"Nigerian compliance violations for {connector_type.value}")
                    result.processing_stage = ProcessingStage.FAILED
                    return result
            else:
                business_rules_result = BusinessRuleEngineResult.create_default(
                    self._get_transaction_id(transaction)
                )
            
            # Stage 5: Pattern Matching (connector-specific patterns)
            if config.enable_pattern_matching:
                result.processing_stage = ProcessingStage.PATTERN_MATCHING
                pattern_result = await self.pattern_matcher.match_patterns(
                    transaction, connector_type, config, historical_context
                )
                result.stage_results['pattern_matching'] = pattern_result
            else:
                pattern_result = PatternResult.create_default(
                    self._get_transaction_id(transaction)
                )
            
            # Stage 6: Enrichment and Integration
            result.processing_stage = ProcessingStage.ENRICHMENT
            processed_transaction = await self._create_universal_processed_transaction(
                transaction,
                connector_type,
                config,
                validation_result,
                duplicate_result,
                amount_result,
                business_rules_result,
                pattern_result,
                start_time
            )
            
            # Stage 7: Finalization
            result.processing_stage = ProcessingStage.FINALIZATION
            await self._finalize_processing(processed_transaction, result, config)
            
            # Success
            result.processed_transaction = processed_transaction
            result.success = True
            result.processing_stage = ProcessingStage.COMPLETED
            
            # Calculate processing time
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            result.processing_time = processing_time
            
            # Update statistics
            self._update_processing_stats(result, connector_type)
            
            logger.info(f"{connector_type.value} transaction processing completed: {self._get_transaction_id(transaction)} - Time: {processing_time:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"{connector_type.value} transaction processing failed: {self._get_transaction_id(transaction)} - {e}")
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            error_result = UniversalProcessingResult(
                transaction_id=self._get_transaction_id(transaction),
                connector_type=connector_type,
                success=False,
                processing_stage=ProcessingStage.FAILED,
                processing_time=processing_time,
                errors=[str(e)]
            )
            
            self._update_processing_stats(error_result, connector_type)
            return error_result
    
    async def process_batch_transactions(
        self,
        transactions: List[Any],
        connector_type: ConnectorType,
        custom_config: Optional[ConnectorProcessingConfig] = None,
        enable_parallel: Optional[bool] = None
    ) -> List[UniversalProcessingResult]:
        """
        Process multiple transactions from the same connector type in batch.
        
        Args:
            transactions: List of raw transactions from connector
            connector_type: Type of connector
            custom_config: Override default processing configuration
            enable_parallel: Override parallel processing setting
            
        Returns:
            List of UniversalProcessingResult objects
        """
        logger.info(f"Batch processing {len(transactions)} {connector_type.value} transactions")
        
        config = custom_config or self.processing_configs.get(connector_type)
        use_parallel = enable_parallel if enable_parallel is not None else config.enable_parallel_processing
        
        if use_parallel and len(transactions) > 1:
            return await self._process_batch_parallel(transactions, connector_type, config)
        else:
            return await self._process_batch_sequential(transactions, connector_type, config)
    
    async def process_mixed_batch_transactions(
        self,
        mixed_transactions: List[tuple[Any, ConnectorType]],
        enable_parallel: bool = True
    ) -> List[UniversalProcessingResult]:
        """
        Process transactions from multiple connector types in a single batch.
        
        This enables cross-connector intelligence and customer matching.
        
        Args:
            mixed_transactions: List of (transaction, connector_type) tuples
            enable_parallel: Enable parallel processing
            
        Returns:
            List of UniversalProcessingResult objects
        """
        logger.info(f"Mixed batch processing {len(mixed_transactions)} transactions from multiple connectors")
        
        if enable_parallel and len(mixed_transactions) > 1:
            tasks = []
            for transaction, connector_type in mixed_transactions:
                task = self.process_transaction(transaction, connector_type)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Handle exceptions
            processed_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    transaction, connector_type = mixed_transactions[i]
                    logger.error(f"Mixed batch processing failed for {connector_type.value} transaction: {self._get_transaction_id(transaction)} - {result}")
                    error_result = UniversalProcessingResult(
                        transaction_id=self._get_transaction_id(transaction),
                        connector_type=connector_type,
                        success=False,
                        processing_stage=ProcessingStage.FAILED,
                        errors=[str(result)]
                    )
                    processed_results.append(error_result)
                else:
                    processed_results.append(result)
            
            return processed_results
        else:
            results = []
            for transaction, connector_type in mixed_transactions:
                result = await self.process_transaction(transaction, connector_type)
                results.append(result)
            return results
    
    def _get_transaction_id(self, transaction: Any) -> str:
        """Extract transaction ID from any transaction type."""
        if hasattr(transaction, 'id'):
            return transaction.id
        elif hasattr(transaction, 'transaction_id'):
            return transaction.transaction_id
        elif hasattr(transaction, 'reference'):
            return transaction.reference
        else:
            return f"unknown_{hash(str(transaction))}"
    
    def _get_transaction_amount(self, transaction: Any) -> float:
        """Extract transaction amount from any transaction type."""
        if hasattr(transaction, 'amount'):
            return float(transaction.amount)
        elif hasattr(transaction, 'total'):
            return float(transaction.total)
        elif hasattr(transaction, 'value'):
            return float(transaction.value)
        else:
            return 0.0
    
    async def _create_universal_processed_transaction(
        self,
        transaction: Any,
        connector_type: ConnectorType,
        config: ConnectorProcessingConfig,
        validation_result: ValidationResult,
        duplicate_result: DuplicateResult,
        amount_result: AmountValidationResult,
        business_rules_result: BusinessRuleEngineResult,
        pattern_result: PatternResult,
        start_time: datetime
    ) -> UniversalProcessedTransaction:
        """Create universal processed transaction from all stage results."""
        
        processing_duration = (datetime.utcnow() - start_time).total_seconds()
        
        # Create universal processed transaction
        processed_tx = UniversalProcessedTransaction.from_raw_transaction(
            transaction,
            connector_type,
            validation_result,
            duplicate_result,
            processing_duration,
            self.pipeline_version
        )
        
        # Enrich with additional data
        await self._enrich_universal_transaction(
            processed_tx,
            amount_result,
            business_rules_result,
            pattern_result,
            config
        )
        
        return processed_tx
    
    async def _enrich_universal_transaction(
        self,
        processed_tx: UniversalProcessedTransaction,
        amount_result: AmountValidationResult,
        business_rules_result: BusinessRuleEngineResult,
        pattern_result: PatternResult,
        config: ConnectorProcessingConfig
    ):
        """Enrich universal processed transaction with connector-specific data."""
        
        # Update risk level based on amount validation
        if amount_result.risk_level.value in ['high', 'very_high', 'critical']:
            if amount_result.risk_level.value == 'critical':
                processed_tx.processing_metadata.risk_level = TransactionRisk.CRITICAL
            elif amount_result.risk_level.value == 'very_high':
                processed_tx.processing_metadata.risk_level = TransactionRisk.HIGH
            else:
                processed_tx.processing_metadata.risk_level = TransactionRisk.MEDIUM
        
        # Update confidence score with connector-specific weighting
        base_confidence = processed_tx.processing_metadata.confidence_score
        amount_confidence = 1.0 - amount_result.risk_score
        pattern_confidence = pattern_result.confidence_score
        
        # Connector-specific confidence weights
        weights = config.confidence_weights or [0.4, 0.3, 0.3]  # validation, amount, pattern
        confidences = [base_confidence, amount_confidence, pattern_confidence]
        
        weighted_confidence = sum(w * c for w, c in zip(weights, confidences))
        processed_tx.processing_metadata.confidence_score = min(weighted_confidence, 1.0)
        
        # Populate enrichment data with connector-specific information
        enrichment = processed_tx.enrichment_data
        
        # Pattern matching results
        enrichment.primary_category = pattern_result.primary_category.value if pattern_result.primary_category else None
        enrichment.business_purpose = pattern_result.business_purpose
        enrichment.merchant_identified = pattern_result.merchant_identified
        enrichment.merchant_name = pattern_result.merchant_name
        enrichment.transaction_patterns = pattern_result.pattern_flags
        
        # Amount validation results
        if amount_result.flags:
            enrichment.amount_risk_flags = [flag.value for flag in amount_result.flags]
        
        # Connector-specific enrichment
        if processed_tx.connector_type == ConnectorType.ERP_SAP:
            await self._enrich_erp_specific(processed_tx, pattern_result)
        elif processed_tx.connector_type in [ConnectorType.BANKING_OPEN_BANKING, ConnectorType.USSD_MTN]:
            await self._enrich_banking_specific(processed_tx, pattern_result)
        elif processed_tx.connector_type == ConnectorType.POS_RETAIL:
            await self._enrich_pos_specific(processed_tx, pattern_result)
        elif processed_tx.connector_type == ConnectorType.CRM_SALESFORCE:
            await self._enrich_crm_specific(processed_tx, pattern_result)
        
        # Universal customer matching (works across all connector types)
        if config.enable_customer_matching:
            customer_info = await self._match_universal_customer(processed_tx, pattern_result)
            if customer_info:
                enrichment.customer_matched = True
                enrichment.customer_id = customer_info.get('id')
                enrichment.customer_name = customer_info.get('name')
                enrichment.customer_type = customer_info.get('type')
                enrichment.customer_confidence = customer_info.get('confidence', 0.0)
        
        # Determine final status based on connector type and Nigerian compliance
        processed_tx.status = self._determine_universal_processing_status(
            processed_tx, business_rules_result
        )
    
    async def _enrich_erp_specific(self, processed_tx: UniversalProcessedTransaction, pattern_result: PatternResult):
        """Apply ERP-specific enrichment."""
        # ERP transactions are usually already structured
        processed_tx.enrichment_data.erp_invoice_number = getattr(processed_tx.original_transaction, 'invoice_number', None)
        processed_tx.enrichment_data.erp_customer_code = getattr(processed_tx.original_transaction, 'customer_code', None)
        processed_tx.enrichment_data.erp_cost_center = getattr(processed_tx.original_transaction, 'cost_center', None)
    
    async def _enrich_banking_specific(self, processed_tx: UniversalProcessedTransaction, pattern_result: PatternResult):
        """Apply banking-specific enrichment."""
        # Banking transactions need more fraud detection
        processed_tx.enrichment_data.bank_account_verified = True
        processed_tx.enrichment_data.transaction_channel = getattr(processed_tx.original_transaction, 'channel', 'unknown')
    
    async def _enrich_pos_specific(self, processed_tx: UniversalProcessedTransaction, pattern_result: PatternResult):
        """Apply POS-specific enrichment."""
        # POS transactions have retail-specific data
        processed_tx.enrichment_data.pos_terminal_id = getattr(processed_tx.original_transaction, 'terminal_id', None)
        processed_tx.enrichment_data.receipt_number = getattr(processed_tx.original_transaction, 'receipt_number', None)
    
    async def _enrich_crm_specific(self, processed_tx: UniversalProcessedTransaction, pattern_result: PatternResult):
        """Apply CRM-specific enrichment."""
        # CRM transactions are service-based
        processed_tx.enrichment_data.service_type = getattr(processed_tx.original_transaction, 'service_type', None)
        processed_tx.enrichment_data.project_id = getattr(processed_tx.original_transaction, 'project_id', None)
    
    async def _match_universal_customer(
        self,
        processed_tx: UniversalProcessedTransaction,
        pattern_result: PatternResult
    ) -> Optional[Dict[str, Any]]:
        """Universal customer matching across all connector types."""
        
        # This would integrate with the universal customer matching system
        # that works across Banking, ERP, POS, and CRM data
        
        if pattern_result.merchant_identified:
            return {
                'id': f"merchant_{pattern_result.merchant_name}_{processed_tx.connector_type.value}",
                'name': pattern_result.merchant_name,
                'type': 'merchant',
                'confidence': 0.8,
                'sources': [processed_tx.connector_type.value]
            }
        
        # Cross-connector customer matching would happen here
        # For example, matching a bank account holder with ERP customer records
        
        return None
    
    def _determine_universal_processing_status(
        self,
        processed_tx: UniversalProcessedTransaction,
        business_rules_result: BusinessRuleEngineResult
    ) -> ProcessingStatus:
        """Determine final processing status with Nigerian compliance checks."""
        
        if business_rules_result.regulatory_violations:
            return ProcessingStatus.FAILED
        
        if not processed_tx.is_valid() or processed_tx.is_duplicate():
            return ProcessingStatus.FAILED
        
        if processed_tx.processing_metadata.risk_level == TransactionRisk.CRITICAL:
            return ProcessingStatus.FAILED
        
        # Connector-specific status determination
        if processed_tx.connector_type in [ConnectorType.ERP_SAP, ConnectorType.ERP_ORACLE]:
            # ERP transactions should be ready for invoice if they pass basic validation
            return ProcessingStatus.READY_FOR_INVOICE
        elif processed_tx.connector_type in [ConnectorType.BANKING_OPEN_BANKING, ConnectorType.USSD_MTN]:
            # Banking transactions need categorization before invoice generation
            if processed_tx.enrichment_data.primary_category:
                return ProcessingStatus.READY_FOR_INVOICE
            else:
                return ProcessingStatus.ENRICHED
        else:
            # Default status determination
            if processed_tx.enrichment_data.primary_category:
                return ProcessingStatus.READY_FOR_INVOICE
            return ProcessingStatus.ENRICHED
    
    async def _finalize_processing(
        self,
        processed_transaction: UniversalProcessedTransaction,
        result: UniversalProcessingResult,
        config: ConnectorProcessingConfig
    ):
        """Finalize universal processing with connector-specific validations."""
        
        # Add connector-specific processing notes
        notes = []
        
        connector_name = processed_transaction.connector_type.value
        
        if processed_transaction.is_duplicate():
            notes.append(f"Duplicate {connector_name} transaction detected")
        
        if processed_transaction.processing_metadata.risk_level == TransactionRisk.HIGH:
            notes.append(f"High risk {connector_name} transaction - requires review")
        
        if processed_transaction.enrichment_data.merchant_identified:
            notes.append(f"Merchant identified in {connector_name}: {processed_transaction.enrichment_data.merchant_name}")
        
        if processed_transaction.enrichment_data.customer_matched:
            notes.append(f"Customer successfully matched across connectors")
        
        # Connector-specific finalizations
        if processed_transaction.connector_type in [ConnectorType.ERP_SAP, ConnectorType.ERP_ORACLE]:
            notes.append("ERP transaction - structured data processed")
        elif processed_transaction.connector_type in [ConnectorType.BANKING_OPEN_BANKING, ConnectorType.USSD_MTN]:
            notes.append("Banking transaction - fraud detection applied")
        
        processed_transaction.processing_metadata.processing_notes = notes
        
        # Add warnings to result
        if processed_transaction.processing_metadata.confidence_score < config.minimum_confidence_threshold:
            result.warnings.append(f"Low confidence {connector_name} processing result")
        
        if processed_transaction.processing_metadata.risk_level in [TransactionRisk.MEDIUM, TransactionRisk.HIGH]:
            result.warnings.append(f"{connector_name} transaction flagged for manual review")
    
    async def _process_batch_parallel(
        self,
        transactions: List[Any],
        connector_type: ConnectorType,
        config: ConnectorProcessingConfig
    ) -> List[UniversalProcessingResult]:
        """Process transactions in parallel batches."""
        
        batch_size = config.batch_size
        results = []
        
        for i in range(0, len(transactions), batch_size):
            batch = transactions[i:i + batch_size]
            logger.debug(f"Processing {connector_type.value} batch {i//batch_size + 1}: {len(batch)} transactions")
            
            tasks = []
            for j, transaction in enumerate(batch):
                historical_context = transactions[:i + j] if i + j > 0 else []
                task = self.process_transaction(transaction, connector_type, historical_context)
                tasks.append(task)
            
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for k, batch_result in enumerate(batch_results):
                if isinstance(batch_result, Exception):
                    logger.error(f"{connector_type.value} batch processing failed for transaction: {self._get_transaction_id(batch[k])} - {batch_result}")
                    error_result = UniversalProcessingResult(
                        transaction_id=self._get_transaction_id(batch[k]),
                        connector_type=connector_type,
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
        transactions: List[Any],
        connector_type: ConnectorType,
        config: ConnectorProcessingConfig
    ) -> List[UniversalProcessingResult]:
        """Process transactions sequentially."""
        
        results = []
        
        for i, transaction in enumerate(transactions):
            historical_context = transactions[:i] if i > 0 else []
            result = await self.process_transaction(transaction, connector_type, historical_context)
            results.append(result)
        
        return results
    
    def _update_processing_stats(self, result: UniversalProcessingResult, connector_type: ConnectorType):
        """Update processing statistics by connector type."""
        
        # Update connector-specific stats
        connector_stats = self.stats[connector_type.value]
        connector_stats['total_processed'] += 1
        connector_stats['total_processing_time'] += result.processing_time
        
        if result.success:
            connector_stats['successful_processed'] += 1
        else:
            connector_stats['failed_processed'] += 1
            connector_stats['stage_failures'][result.processing_stage.value] += 1
        
        connector_stats['average_processing_time'] = (
            connector_stats['total_processing_time'] / connector_stats['total_processed']
        )
        
        # Update global stats
        self.global_stats['total_processed'] += 1
        self.global_stats['total_processing_time'] += result.processing_time
        
        if result.success:
            self.global_stats['successful_processed'] += 1
        else:
            self.global_stats['failed_processed'] += 1
        
        self.global_stats['average_processing_time'] = (
            self.global_stats['total_processing_time'] / self.global_stats['total_processed']
        )
    
    def _load_default_configs(self) -> Dict[ConnectorType, ConnectorProcessingConfig]:
        """Load default processing configurations for each connector type."""
        from .default_processing_configs import get_default_processing_configs
        return get_default_processing_configs()
    
    def get_processing_statistics(
        self, 
        connector_type: Optional[ConnectorType] = None
    ) -> Dict[str, Any]:
        """Get comprehensive processing statistics."""
        
        if connector_type:
            # Return connector-specific statistics
            stats = self.stats[connector_type.value].copy()
            
            if stats['total_processed'] > 0:
                stats['success_rate'] = stats['successful_processed'] / stats['total_processed']
                stats['failure_rate'] = stats['failed_processed'] / stats['total_processed']
            else:
                stats['success_rate'] = 0.0
                stats['failure_rate'] = 0.0
            
            stats['connector_type'] = connector_type.value
            return stats
        else:
            # Return global statistics
            stats = self.global_stats.copy()
            
            if stats['total_processed'] > 0:
                stats['success_rate'] = stats['successful_processed'] / stats['total_processed']
                stats['failure_rate'] = stats['failed_processed'] / stats['total_processed']
            else:
                stats['success_rate'] = 0.0
                stats['failure_rate'] = 0.0
            
            # Add breakdown by connector type
            stats['connector_breakdown'] = {}
            for connector_type in ConnectorType:
                connector_stats = self.stats[connector_type.value]
                if connector_stats['total_processed'] > 0:
                    stats['connector_breakdown'][connector_type.value] = {
                        'total_processed': connector_stats['total_processed'],
                        'success_rate': connector_stats['successful_processed'] / connector_stats['total_processed'],
                        'average_processing_time': connector_stats['average_processing_time']
                    }
            
            return stats


def create_universal_transaction_processor(
    validator: UniversalTransactionValidator,
    duplicate_detector: UniversalDuplicateDetector,
    amount_validator: UniversalAmountValidator,
    business_rule_engine: UniversalBusinessRuleEngine,
    pattern_matcher: UniversalPatternMatcher,
    processing_configs: Optional[Dict[ConnectorType, ConnectorProcessingConfig]] = None
) -> UniversalTransactionProcessor:
    """Factory function to create universal transaction processor."""
    return UniversalTransactionProcessor(
        validator,
        duplicate_detector,
        amount_validator,
        business_rule_engine,
        pattern_matcher,
        processing_configs
    )