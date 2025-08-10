"""
Processing Stage Definitions
============================

Comprehensive definition of processing pipeline stages and their configurations
for different connector types. Each stage represents a specific processing step
in the universal transaction processing pipeline.

The processing pipeline is designed to be flexible and connector-aware, allowing
different business systems to follow optimized processing paths while maintaining
consistent quality and compliance standards.

Pipeline Architecture:
Raw Transaction → Validation → Duplicate Detection → Amount Validation → 
Business Rules → Pattern Matching → Enrichment → Finalization → Completed
"""

from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod

from ..connector_configs.connector_types import ConnectorType, ConnectorCategory


class ProcessingStage(Enum):
    """Enumeration of all processing pipeline stages."""
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


class StageExecutionMode(Enum):
    """Execution modes for processing stages."""
    REQUIRED = "required"        # Stage must be executed and must pass
    OPTIONAL = "optional"        # Stage will be executed but failure won't stop pipeline
    CONDITIONAL = "conditional"   # Stage execution depends on transaction properties
    SKIP = "skip"               # Stage will be skipped for this connector type


class StageFailureAction(Enum):
    """Actions to take when a stage fails."""
    FAIL_PIPELINE = "fail_pipeline"      # Stop processing and mark as failed
    CONTINUE_WITH_WARNING = "continue"   # Continue processing but add warning
    RETRY_WITH_DEFAULTS = "retry"        # Retry with default values
    MANUAL_REVIEW = "manual_review"      # Flag for manual review


@dataclass
class StageConfiguration:
    """Configuration for a specific processing stage."""
    stage: ProcessingStage
    execution_mode: StageExecutionMode
    failure_action: StageFailureAction
    timeout_seconds: int = 10
    retry_attempts: int = 0
    dependencies: Set[ProcessingStage] = field(default_factory=set)
    connector_specific_settings: Dict[str, Any] = field(default_factory=dict)
    
    # Quality thresholds
    minimum_quality_threshold: float = 0.0
    warning_threshold: float = 0.5
    
    # Performance settings
    enable_caching: bool = True
    cache_ttl_seconds: int = 300
    enable_parallel_execution: bool = False


@dataclass
class ProcessingPipeline:
    """Complete processing pipeline configuration for a connector type."""
    connector_type: ConnectorType
    pipeline_name: str
    pipeline_version: str = "1.0.0"
    
    # Stage configurations in execution order
    stage_configs: Dict[ProcessingStage, StageConfiguration] = field(default_factory=dict)
    
    # Pipeline-level settings
    max_total_processing_time: int = 120  # seconds
    enable_stage_parallelization: bool = False
    failure_recovery_enabled: bool = True
    
    # Monitoring and logging
    detailed_logging: bool = False
    performance_tracking: bool = True
    alert_on_stage_failures: bool = True
    
    def get_execution_order(self) -> List[ProcessingStage]:
        """Get the execution order of stages based on dependencies."""
        ordered_stages = []
        remaining_stages = set(self.stage_configs.keys())
        
        while remaining_stages:
            # Find stages with no unresolved dependencies
            ready_stages = []
            for stage in remaining_stages:
                config = self.stage_configs[stage]
                if config.dependencies.issubset(set(ordered_stages)):
                    ready_stages.append(stage)
            
            if not ready_stages:
                # Circular dependency or invalid configuration
                raise ValueError("Circular dependency detected in pipeline stages")
            
            # Add ready stages to execution order
            # Sort by stage enum order for consistency
            ready_stages.sort(key=lambda x: list(ProcessingStage).index(x))
            ordered_stages.extend(ready_stages)
            remaining_stages -= set(ready_stages)
        
        return ordered_stages
    
    def is_stage_enabled(self, stage: ProcessingStage) -> bool:
        """Check if a stage is enabled for this pipeline."""
        config = self.stage_configs.get(stage)
        return config is not None and config.execution_mode != StageExecutionMode.SKIP
    
    def get_critical_stages(self) -> List[ProcessingStage]:
        """Get stages that are critical for pipeline success."""
        return [
            stage for stage, config in self.stage_configs.items()
            if config.execution_mode == StageExecutionMode.REQUIRED
        ]


class PipelineProfileBuilder:
    """Builder class for creating processing pipeline profiles."""
    
    @staticmethod
    def create_enterprise_erp_pipeline(connector_type: ConnectorType) -> ProcessingPipeline:
        """Create processing pipeline for enterprise ERP systems."""
        pipeline = ProcessingPipeline(
            connector_type=connector_type,
            pipeline_name=f"Enterprise ERP Pipeline - {connector_type.value}",
            max_total_processing_time=180,  # ERP can handle longer processing
            enable_stage_parallelization=True,
            detailed_logging=True
        )
        
        # Raw Input (always first)
        pipeline.stage_configs[ProcessingStage.RAW_INPUT] = StageConfiguration(
            stage=ProcessingStage.RAW_INPUT,
            execution_mode=StageExecutionMode.REQUIRED,
            failure_action=StageFailureAction.FAIL_PIPELINE,
            timeout_seconds=5
        )
        
        # Validation (trust ERP data quality)
        pipeline.stage_configs[ProcessingStage.VALIDATION] = StageConfiguration(
            stage=ProcessingStage.VALIDATION,
            execution_mode=StageExecutionMode.REQUIRED,
            failure_action=StageFailureAction.CONTINUE_WITH_WARNING,
            timeout_seconds=15,
            dependencies={ProcessingStage.RAW_INPUT},
            connector_specific_settings={
                "validate_erp_structure": True,
                "require_account_codes": True,
                "validate_cost_centers": True,
                "strict_data_types": True
            }
        )
        
        # Duplicate Detection (less critical for ERP)
        pipeline.stage_configs[ProcessingStage.DUPLICATE_DETECTION] = StageConfiguration(
            stage=ProcessingStage.DUPLICATE_DETECTION,
            execution_mode=StageExecutionMode.OPTIONAL,
            failure_action=StageFailureAction.CONTINUE_WITH_WARNING,
            timeout_seconds=20,
            dependencies={ProcessingStage.VALIDATION},
            connector_specific_settings={
                "erp_duplicate_window_hours": 24,
                "check_invoice_numbers": True,
                "check_po_numbers": True
            }
        )
        
        # Amount Validation (skip for trusted ERP)
        pipeline.stage_configs[ProcessingStage.AMOUNT_VALIDATION] = StageConfiguration(
            stage=ProcessingStage.AMOUNT_VALIDATION,
            execution_mode=StageExecutionMode.SKIP,
            failure_action=StageFailureAction.CONTINUE_WITH_WARNING,
            timeout_seconds=10
        )
        
        # Business Rules (critical for compliance)
        pipeline.stage_configs[ProcessingStage.BUSINESS_RULES] = StageConfiguration(
            stage=ProcessingStage.BUSINESS_RULES,
            execution_mode=StageExecutionMode.REQUIRED,
            failure_action=StageFailureAction.FAIL_PIPELINE,
            timeout_seconds=30,
            dependencies={ProcessingStage.VALIDATION},
            connector_specific_settings={
                "enforce_nigerian_accounting_standards": True,
                "validate_tax_compliance": True,
                "check_audit_requirements": True
            }
        )
        
        # Pattern Matching (important for categorization)
        pipeline.stage_configs[ProcessingStage.PATTERN_MATCHING] = StageConfiguration(
            stage=ProcessingStage.PATTERN_MATCHING,
            execution_mode=StageExecutionMode.REQUIRED,
            failure_action=StageFailureAction.CONTINUE_WITH_WARNING,
            timeout_seconds=25,
            dependencies={ProcessingStage.BUSINESS_RULES},
            connector_specific_settings={
                "use_erp_categories": True,
                "enable_account_code_matching": True,
                "business_unit_classification": True
            }
        )
        
        # Enrichment
        pipeline.stage_configs[ProcessingStage.ENRICHMENT] = StageConfiguration(
            stage=ProcessingStage.ENRICHMENT,
            execution_mode=StageExecutionMode.REQUIRED,
            failure_action=StageFailureAction.CONTINUE_WITH_WARNING,
            timeout_seconds=20,
            dependencies={ProcessingStage.PATTERN_MATCHING, ProcessingStage.DUPLICATE_DETECTION},
            connector_specific_settings={
                "enrich_customer_data": True,
                "add_erp_metadata": True,
                "calculate_enterprise_metrics": True
            }
        )
        
        # Finalization
        pipeline.stage_configs[ProcessingStage.FINALIZATION] = StageConfiguration(
            stage=ProcessingStage.FINALIZATION,
            execution_mode=StageExecutionMode.REQUIRED,
            failure_action=StageFailureAction.FAIL_PIPELINE,
            timeout_seconds=10,
            dependencies={ProcessingStage.ENRICHMENT}
        )
        
        return pipeline
    
    @staticmethod
    def create_small_business_pipeline(connector_type: ConnectorType) -> ProcessingPipeline:
        """Create processing pipeline for small business systems."""
        pipeline = ProcessingPipeline(
            connector_type=connector_type,
            pipeline_name=f"Small Business Pipeline - {connector_type.value}",
            max_total_processing_time=90,
            enable_stage_parallelization=True,
            detailed_logging=False
        )
        
        # Raw Input
        pipeline.stage_configs[ProcessingStage.RAW_INPUT] = StageConfiguration(
            stage=ProcessingStage.RAW_INPUT,
            execution_mode=StageExecutionMode.REQUIRED,
            failure_action=StageFailureAction.FAIL_PIPELINE,
            timeout_seconds=5
        )
        
        # Validation (moderate validation)
        pipeline.stage_configs[ProcessingStage.VALIDATION] = StageConfiguration(
            stage=ProcessingStage.VALIDATION,
            execution_mode=StageExecutionMode.REQUIRED,
            failure_action=StageFailureAction.RETRY_WITH_DEFAULTS,
            timeout_seconds=10,
            retry_attempts=1,
            dependencies={ProcessingStage.RAW_INPUT},
            connector_specific_settings={
                "flexible_validation": True,
                "auto_correct_minor_errors": True,
                "sme_business_rules": True
            }
        )
        
        # Duplicate Detection
        pipeline.stage_configs[ProcessingStage.DUPLICATE_DETECTION] = StageConfiguration(
            stage=ProcessingStage.DUPLICATE_DETECTION,
            execution_mode=StageExecutionMode.REQUIRED,
            failure_action=StageFailureAction.CONTINUE_WITH_WARNING,
            timeout_seconds=15,
            dependencies={ProcessingStage.VALIDATION},
            connector_specific_settings={
                "sme_duplicate_window_hours": 12,
                "fuzzy_matching_enabled": True
            }
        )
        
        # Amount Validation (moderate fraud detection)
        pipeline.stage_configs[ProcessingStage.AMOUNT_VALIDATION] = StageConfiguration(
            stage=ProcessingStage.AMOUNT_VALIDATION,
            execution_mode=StageExecutionMode.OPTIONAL,
            failure_action=StageFailureAction.CONTINUE_WITH_WARNING,
            timeout_seconds=15,
            dependencies={ProcessingStage.VALIDATION},
            connector_specific_settings={
                "sme_fraud_thresholds": True,
                "moderate_risk_tolerance": True
            }
        )
        
        # Business Rules
        pipeline.stage_configs[ProcessingStage.BUSINESS_RULES] = StageConfiguration(
            stage=ProcessingStage.BUSINESS_RULES,
            execution_mode=StageExecutionMode.REQUIRED,
            failure_action=StageFailureAction.CONTINUE_WITH_WARNING,
            timeout_seconds=20,
            dependencies={ProcessingStage.VALIDATION},
            connector_specific_settings={
                "sme_compliance_rules": True,
                "simplified_tax_validation": True
            }
        )
        
        # Pattern Matching
        pipeline.stage_configs[ProcessingStage.PATTERN_MATCHING] = StageConfiguration(
            stage=ProcessingStage.PATTERN_MATCHING,
            execution_mode=StageExecutionMode.REQUIRED,
            failure_action=StageFailureAction.CONTINUE_WITH_WARNING,
            timeout_seconds=15,
            dependencies={ProcessingStage.BUSINESS_RULES},
            connector_specific_settings={
                "sme_pattern_library": True,
                "simplified_categorization": True
            }
        )
        
        # Enrichment
        pipeline.stage_configs[ProcessingStage.ENRICHMENT] = StageConfiguration(
            stage=ProcessingStage.ENRICHMENT,
            execution_mode=StageExecutionMode.REQUIRED,
            failure_action=StageFailureAction.CONTINUE_WITH_WARNING,
            timeout_seconds=15,
            dependencies={ProcessingStage.PATTERN_MATCHING, ProcessingStage.DUPLICATE_DETECTION},
            connector_specific_settings={
                "basic_enrichment": True,
                "sme_customer_matching": True
            }
        )
        
        # Finalization
        pipeline.stage_configs[ProcessingStage.FINALIZATION] = StageConfiguration(
            stage=ProcessingStage.FINALIZATION,
            execution_mode=StageExecutionMode.REQUIRED,
            failure_action=StageFailureAction.FAIL_PIPELINE,
            timeout_seconds=5,
            dependencies={ProcessingStage.ENRICHMENT}
        )
        
        return pipeline
    
    @staticmethod
    def create_customer_facing_pipeline(connector_type: ConnectorType) -> ProcessingPipeline:
        """Create processing pipeline for customer-facing systems (POS, E-commerce)."""
        pipeline = ProcessingPipeline(
            connector_type=connector_type,
            pipeline_name=f"Customer Facing Pipeline - {connector_type.value}",
            max_total_processing_time=60,
            enable_stage_parallelization=True,
            alert_on_stage_failures=True
        )
        
        # Raw Input
        pipeline.stage_configs[ProcessingStage.RAW_INPUT] = StageConfiguration(
            stage=ProcessingStage.RAW_INPUT,
            execution_mode=StageExecutionMode.REQUIRED,
            failure_action=StageFailureAction.FAIL_PIPELINE,
            timeout_seconds=5
        )
        
        # Validation (strict for customer data)
        pipeline.stage_configs[ProcessingStage.VALIDATION] = StageConfiguration(
            stage=ProcessingStage.VALIDATION,
            execution_mode=StageExecutionMode.REQUIRED,
            failure_action=StageFailureAction.RETRY_WITH_DEFAULTS,
            timeout_seconds=10,
            retry_attempts=2,
            dependencies={ProcessingStage.RAW_INPUT},
            connector_specific_settings={
                "customer_data_validation": True,
                "receipt_validation": True,
                "payment_method_validation": True
            }
        )
        
        # Duplicate Detection (important for customer transactions)
        pipeline.stage_configs[ProcessingStage.DUPLICATE_DETECTION] = StageConfiguration(
            stage=ProcessingStage.DUPLICATE_DETECTION,
            execution_mode=StageExecutionMode.REQUIRED,
            failure_action=StageFailureAction.CONTINUE_WITH_WARNING,
            timeout_seconds=10,
            dependencies={ProcessingStage.VALIDATION},
            connector_specific_settings={
                "customer_duplicate_window_hours": 4,
                "check_receipt_numbers": True,
                "customer_behavior_analysis": True
            }
        )
        
        # Amount Validation (fraud detection for customer transactions)
        pipeline.stage_configs[ProcessingStage.AMOUNT_VALIDATION] = StageConfiguration(
            stage=ProcessingStage.AMOUNT_VALIDATION,
            execution_mode=StageExecutionMode.REQUIRED,
            failure_action=StageFailureAction.MANUAL_REVIEW,
            timeout_seconds=15,
            dependencies={ProcessingStage.VALIDATION},
            connector_specific_settings={
                "customer_fraud_detection": True,
                "unusual_amount_flagging": True,
                "payment_pattern_analysis": True
            }
        )
        
        # Business Rules (consumer protection)
        pipeline.stage_configs[ProcessingStage.BUSINESS_RULES] = StageConfiguration(
            stage=ProcessingStage.BUSINESS_RULES,
            execution_mode=StageExecutionMode.REQUIRED,
            failure_action=StageFailureAction.CONTINUE_WITH_WARNING,
            timeout_seconds=15,
            dependencies={ProcessingStage.VALIDATION},
            connector_specific_settings={
                "consumer_protection_rules": True,
                "receipt_completeness_check": True,
                "refund_policy_validation": True
            }
        )
        
        # Pattern Matching (customer behavior patterns)
        pipeline.stage_configs[ProcessingStage.PATTERN_MATCHING] = StageConfiguration(
            stage=ProcessingStage.PATTERN_MATCHING,
            execution_mode=StageExecutionMode.REQUIRED,
            failure_action=StageFailureAction.CONTINUE_WITH_WARNING,
            timeout_seconds=12,
            dependencies={ProcessingStage.BUSINESS_RULES, ProcessingStage.AMOUNT_VALIDATION},
            connector_specific_settings={
                "customer_pattern_recognition": True,
                "product_categorization": True,
                "seasonal_pattern_analysis": True
            }
        )
        
        # Enrichment (customer insights)
        pipeline.stage_configs[ProcessingStage.ENRICHMENT] = StageConfiguration(
            stage=ProcessingStage.ENRICHMENT,
            execution_mode=StageExecutionMode.REQUIRED,
            failure_action=StageFailureAction.CONTINUE_WITH_WARNING,
            timeout_seconds=15,
            dependencies={ProcessingStage.PATTERN_MATCHING, ProcessingStage.DUPLICATE_DETECTION},
            connector_specific_settings={
                "customer_enrichment": True,
                "loyalty_data_integration": True,
                "demographic_enrichment": True
            }
        )
        
        # Finalization
        pipeline.stage_configs[ProcessingStage.FINALIZATION] = StageConfiguration(
            stage=ProcessingStage.FINALIZATION,
            execution_mode=StageExecutionMode.REQUIRED,
            failure_action=StageFailureAction.FAIL_PIPELINE,
            timeout_seconds=8,
            dependencies={ProcessingStage.ENRICHMENT}
        )
        
        return pipeline
    
    @staticmethod
    def create_financial_data_pipeline(connector_type: ConnectorType) -> ProcessingPipeline:
        """Create processing pipeline for financial data sources (Banking)."""
        pipeline = ProcessingPipeline(
            connector_type=connector_type,
            pipeline_name=f"Financial Data Pipeline - {connector_type.value}",
            max_total_processing_time=150,
            enable_stage_parallelization=False,  # Sequential for accuracy
            detailed_logging=True,
            alert_on_stage_failures=True
        )
        
        # Raw Input
        pipeline.stage_configs[ProcessingStage.RAW_INPUT] = StageConfiguration(
            stage=ProcessingStage.RAW_INPUT,
            execution_mode=StageExecutionMode.REQUIRED,
            failure_action=StageFailureAction.FAIL_PIPELINE,
            timeout_seconds=10
        )
        
        # Validation (thorough financial validation)
        pipeline.stage_configs[ProcessingStage.VALIDATION] = StageConfiguration(
            stage=ProcessingStage.VALIDATION,
            execution_mode=StageExecutionMode.REQUIRED,
            failure_action=StageFailureAction.RETRY_WITH_DEFAULTS,
            timeout_seconds=20,
            retry_attempts=2,
            dependencies={ProcessingStage.RAW_INPUT},
            connector_specific_settings={
                "financial_data_validation": True,
                "bank_reference_validation": True,
                "account_number_validation": True,
                "transaction_integrity_check": True
            }
        )
        
        # Duplicate Detection (critical for financial data)
        pipeline.stage_configs[ProcessingStage.DUPLICATE_DETECTION] = StageConfiguration(
            stage=ProcessingStage.DUPLICATE_DETECTION,
            execution_mode=StageExecutionMode.REQUIRED,
            failure_action=StageFailureAction.FAIL_PIPELINE,
            timeout_seconds=25,
            dependencies={ProcessingStage.VALIDATION},
            connector_specific_settings={
                "financial_duplicate_window_hours": 72,
                "exact_amount_matching": True,
                "bank_reference_matching": True,
                "cross_account_duplicate_check": True
            }
        )
        
        # Amount Validation (comprehensive fraud detection)
        pipeline.stage_configs[ProcessingStage.AMOUNT_VALIDATION] = StageConfiguration(
            stage=ProcessingStage.AMOUNT_VALIDATION,
            execution_mode=StageExecutionMode.REQUIRED,
            failure_action=StageFailureAction.MANUAL_REVIEW,
            timeout_seconds=30,
            dependencies={ProcessingStage.VALIDATION},
            connector_specific_settings={
                "comprehensive_fraud_detection": True,
                "velocity_checks": True,
                "amount_pattern_analysis": True,
                "suspicious_timing_detection": True,
                "large_transaction_flagging": True
            }
        )
        
        # Business Rules (financial regulations)
        pipeline.stage_configs[ProcessingStage.BUSINESS_RULES] = StageConfiguration(
            stage=ProcessingStage.BUSINESS_RULES,
            execution_mode=StageExecutionMode.REQUIRED,
            failure_action=StageFailureAction.FAIL_PIPELINE,
            timeout_seconds=25,
            dependencies={ProcessingStage.VALIDATION},
            connector_specific_settings={
                "cbn_compliance_rules": True,
                "anti_money_laundering_check": True,
                "foreign_exchange_validation": True,
                "regulatory_reporting_requirements": True
            }
        )
        
        # Pattern Matching (financial patterns)
        pipeline.stage_configs[ProcessingStage.PATTERN_MATCHING] = StageConfiguration(
            stage=ProcessingStage.PATTERN_MATCHING,
            execution_mode=StageExecutionMode.REQUIRED,
            failure_action=StageFailureAction.CONTINUE_WITH_WARNING,
            timeout_seconds=20,
            dependencies={ProcessingStage.BUSINESS_RULES, ProcessingStage.AMOUNT_VALIDATION},
            connector_specific_settings={
                "financial_pattern_recognition": True,
                "merchant_identification": True,
                "transaction_categorization": True,
                "behavioral_analysis": True
            }
        )
        
        # Enrichment (financial intelligence)
        pipeline.stage_configs[ProcessingStage.ENRICHMENT] = StageConfiguration(
            stage=ProcessingStage.ENRICHMENT,
            execution_mode=StageExecutionMode.REQUIRED,
            failure_action=StageFailureAction.CONTINUE_WITH_WARNING,
            timeout_seconds=25,
            dependencies={ProcessingStage.PATTERN_MATCHING, ProcessingStage.DUPLICATE_DETECTION},
            connector_specific_settings={
                "financial_enrichment": True,
                "counterparty_identification": True,
                "risk_scoring": True,
                "regulatory_classification": True
            }
        )
        
        # Finalization
        pipeline.stage_configs[ProcessingStage.FINALIZATION] = StageConfiguration(
            stage=ProcessingStage.FINALIZATION,
            execution_mode=StageExecutionMode.REQUIRED,
            failure_action=StageFailureAction.FAIL_PIPELINE,
            timeout_seconds=10,
            dependencies={ProcessingStage.ENRICHMENT}
        )
        
        return pipeline


def get_default_pipeline_for_connector(connector_type: ConnectorType) -> ProcessingPipeline:
    """Get the default processing pipeline for a specific connector type."""
    
    # Determine connector category
    if connector_type.value.startswith('erp_') and connector_type in [
        ConnectorType.ERP_SAP, ConnectorType.ERP_ORACLE, 
        ConnectorType.ERP_MICROSOFT_DYNAMICS, ConnectorType.ERP_NETSUITE
    ]:
        return PipelineProfileBuilder.create_enterprise_erp_pipeline(connector_type)
    
    elif (connector_type.value.startswith('erp_') or 
          connector_type.value.startswith('accounting_')):
        return PipelineProfileBuilder.create_small_business_pipeline(connector_type)
    
    elif (connector_type.value.startswith('pos_') or 
          connector_type.value.startswith('ecommerce_') or
          connector_type.value.startswith('crm_')):
        return PipelineProfileBuilder.create_customer_facing_pipeline(connector_type)
    
    elif connector_type.value.startswith('banking_'):
        return PipelineProfileBuilder.create_financial_data_pipeline(connector_type)
    
    else:
        # Default to small business pipeline for unknown types
        return PipelineProfileBuilder.create_small_business_pipeline(connector_type)


def get_all_default_pipelines() -> Dict[ConnectorType, ProcessingPipeline]:
    """Get default processing pipelines for all supported connector types."""
    pipelines = {}
    
    for connector_type in ConnectorType:
        pipelines[connector_type] = get_default_pipeline_for_connector(connector_type)
    
    return pipelines


def validate_pipeline_configuration(pipeline: ProcessingPipeline) -> List[str]:
    """
    Validate a processing pipeline configuration for consistency and correctness.
    
    Args:
        pipeline: Pipeline configuration to validate
        
    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []
    
    # Check that required stages are present
    required_stages = {
        ProcessingStage.RAW_INPUT,
        ProcessingStage.VALIDATION,
        ProcessingStage.FINALIZATION
    }
    
    missing_required = required_stages - set(pipeline.stage_configs.keys())
    if missing_required:
        errors.append(f"Missing required stages: {missing_required}")
    
    # Validate dependencies
    try:
        execution_order = pipeline.get_execution_order()
    except ValueError as e:
        errors.append(str(e))
    
    # Check for reasonable timeouts
    total_timeout = sum(config.timeout_seconds for config in pipeline.stage_configs.values())
    if total_timeout > pipeline.max_total_processing_time:
        errors.append(f"Sum of stage timeouts ({total_timeout}s) exceeds max processing time ({pipeline.max_total_processing_time}s)")
    
    # Validate individual stage configurations
    for stage, config in pipeline.stage_configs.items():
        if config.timeout_seconds <= 0:
            errors.append(f"Stage {stage.value} has invalid timeout: {config.timeout_seconds}")
        
        if config.retry_attempts < 0:
            errors.append(f"Stage {stage.value} has invalid retry attempts: {config.retry_attempts}")
    
    return errors