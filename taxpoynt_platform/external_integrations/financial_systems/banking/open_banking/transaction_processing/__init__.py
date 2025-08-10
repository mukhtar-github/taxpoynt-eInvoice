"""
Transaction Processing Package
==============================

Comprehensive transaction analysis and processing for Open Banking data.
Validates, cleanses, and enriches banking transaction data before invoice generation.

Key Components:
- transaction_validator.py: Validates transaction data integrity
- duplicate_detector.py: Prevents duplicate transaction processing
- amount_validator.py: Amount validation and fraud detection
- business_rule_engine.py: Nigerian business logic rules
- pattern_matcher.py: Transaction pattern recognition and categorization

Features:
- Multi-level validation pipeline
- Fraud detection and prevention
- Nigerian compliance rules
- Smart categorization
- Data enrichment
"""

# Core processing components
from .transaction_validator import (
    TransactionValidator,
    ValidationResult,
    ValidationRule,
    ValidationSeverity,
    create_validator
)

from .duplicate_detector import (
    DuplicateDetector,
    DuplicateResult,
    DuplicateStrategy,
    DetectionRule,
    create_duplicate_detector
)

from .amount_validator import (
    AmountValidator,
    AmountValidationResult,
    FraudRisk,
    AmountThreshold,
    create_amount_validator
)

from .business_rule_engine import (
    BusinessRuleEngine,
    BusinessRule,
    RuleResult,
    RuleType,
    NigerianBusinessRules,
    create_business_rule_engine
)

from .pattern_matcher import (
    PatternMatcher,
    PatternResult,
    TransactionCategory,
    PatternRule,
    create_pattern_matcher
)

# Amount validation
from .amount_validator import (
    AmountValidator,
    AmountValidationResult,
    FraudRisk,
    AmountThreshold,
    create_amount_validator
)

# Business rule engine
from .business_rule_engine import (
    BusinessRuleEngine,
    BusinessRule,
    RuleResult,
    RuleType,
    NigerianBusinessRules,
    create_business_rule_engine
)

# Pattern matcher
from .pattern_matcher import (
    PatternMatcher,
    PatternResult,
    TransactionCategory,
    PatternRule,
    create_pattern_matcher
)

# Processed transaction model
from .processed_transaction import (
    ProcessedTransaction,
    ProcessingStatus,
    ProcessingMetadata,
    EnrichmentData,
    TransactionRisk,
    filter_ready_for_invoice,
    group_by_customer,
    calculate_batch_statistics
)

# Integrated processing pipeline
from .transaction_processor import (
    TransactionProcessor,
    ProcessingResult,
    ProcessingConfig,
    ProcessingStage,
    create_transaction_processor
)

# Package metadata
__version__ = "1.0.0"
__author__ = "TaxPoynt Platform Team"
__description__ = "Transaction Processing for Open Banking Integration"

# Export all public classes
__all__ = [
    # Validation
    "TransactionValidator",
    "ValidationResult", 
    "ValidationRule",
    "ValidationSeverity",
    "create_validator",
    
    # Duplicate detection
    "DuplicateDetector",
    "DuplicateResult",
    "DuplicateStrategy", 
    "DetectionRule",
    "create_duplicate_detector",
    
    # Amount validation
    "AmountValidator",
    "AmountValidationResult",
    "FraudRisk",
    "AmountThreshold",
    "create_amount_validator",
    
    # Business rules
    "BusinessRuleEngine",
    "BusinessRule",
    "RuleResult",
    "RuleType", 
    "NigerianBusinessRules",
    "create_business_rule_engine",
    
    # Pattern matching
    "PatternMatcher",
    "PatternResult",
    "TransactionCategory",
    "PatternRule",
    "create_pattern_matcher",
    
    # Amount validation
    "AmountValidator",
    "AmountValidationResult",
    "FraudRisk",
    "AmountThreshold",
    "create_amount_validator",
    
    # Business rules
    "BusinessRuleEngine",
    "BusinessRule",
    "RuleResult",
    "RuleType", 
    "NigerianBusinessRules",
    "create_business_rule_engine",
    
    # Pattern matching
    "PatternMatcher",
    "PatternResult",
    "TransactionCategory",
    "PatternRule",
    "create_pattern_matcher",
    
    # Processed transaction model
    "ProcessedTransaction",
    "ProcessingStatus",
    "ProcessingMetadata",
    "EnrichmentData",
    "TransactionRisk",
    "filter_ready_for_invoice",
    "group_by_customer",
    "calculate_batch_statistics",
    
    # Integrated processor
    "TransactionProcessor",
    "ProcessingResult",
    "ProcessingConfig",
    "ProcessingStage",
    "create_transaction_processor",
]


# Factory function for complete processing pipeline
def create_complete_processing_pipeline(
    validation_rules=None,
    duplicate_strategy=DuplicateStrategy.HASH_BASED,
    fraud_thresholds=None,
    business_rules=None,
    pattern_rules=None
):
    """
    Create complete transaction processing pipeline.
    
    Args:
        validation_rules: Custom validation rules
        duplicate_strategy: Duplicate detection strategy
        fraud_thresholds: Fraud detection thresholds
        business_rules: Custom business rules
        pattern_rules: Custom pattern matching rules
        
    Returns:
        Configured TransactionProcessor instance
    """
    
    # Create individual components
    validator = create_validator(validation_rules)
    duplicate_detector = create_duplicate_detector(duplicate_strategy)
    amount_validator = create_amount_validator(fraud_thresholds)
    rule_engine = create_business_rule_engine(business_rules)
    pattern_matcher = create_pattern_matcher(pattern_rules)
    
    # Create integrated processor
    processor = create_transaction_processor(
        validator=validator,
        duplicate_detector=duplicate_detector,
        amount_validator=amount_validator,
        rule_engine=rule_engine,
        pattern_matcher=pattern_matcher
    )
    
    return processor