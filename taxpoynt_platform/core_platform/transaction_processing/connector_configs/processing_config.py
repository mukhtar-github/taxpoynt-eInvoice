"""
Processing Configuration System
===============================

Connector-specific processing configurations that define how transactions
from different business systems should be processed, validated, and enriched.

Each connector type has unique characteristics that require tailored processing
approaches while maintaining consistent quality and compliance standards.

This configuration system enables the universal transaction processor to
intelligently adapt its behavior based on the source system characteristics.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

from .connector_types import ConnectorType, get_connector_characteristics


class ProcessingProfile(Enum):
    """Pre-defined processing profiles for different system types."""
    ENTERPRISE_ERP = "enterprise_erp"           # High-trust, structured data
    SMALL_BUSINESS = "small_business"           # Medium-trust, good structure
    CUSTOMER_FACING = "customer_facing"         # Variable trust, needs validation
    FINANCIAL_DATA = "financial_data"           # High-risk, needs fraud detection


@dataclass
class ConnectorProcessingConfig:
    """
    Comprehensive processing configuration for a specific connector type.
    
    This configuration defines how the universal transaction processor should
    handle transactions from a specific business system type.
    """
    
    # Basic identification
    connector_type: ConnectorType
    profile: ProcessingProfile
    
    # Processing stage controls
    enable_validation: bool = True
    enable_duplicate_detection: bool = True
    enable_amount_validation: bool = True
    enable_business_rules: bool = True
    enable_pattern_matching: bool = True
    enable_customer_matching: bool = True
    
    # Error handling behavior
    fail_on_validation_errors: bool = False
    fail_on_duplicates: bool = True
    fail_on_business_rule_violations: bool = False
    fail_on_high_fraud_risk: bool = True
    
    # Performance settings
    max_processing_time: int = 30  # seconds
    enable_parallel_processing: bool = True
    batch_size: int = 100
    
    # Quality thresholds
    minimum_confidence_threshold: float = 0.6
    maximum_risk_tolerance: str = "medium"  # low, medium, high
    
    # Confidence calculation weights [validation, amount, pattern]
    confidence_weights: List[float] = field(default_factory=lambda: [0.4, 0.3, 0.3])
    
    # Nigerian compliance requirements
    compliance_rules: List[str] = field(default_factory=list)
    
    # Connector-specific settings
    connector_specific_settings: Dict[str, Any] = field(default_factory=dict)
    
    # Processing optimizations
    skip_low_value_fraud_detection: bool = False
    low_value_threshold: float = 1000.0  # NGN
    
    # Enrichment preferences
    prioritize_customer_matching: bool = True
    enable_merchant_identification: bool = True
    enable_category_prediction: bool = True
    
    # Monitoring and logging
    enable_detailed_logging: bool = False
    log_performance_metrics: bool = True
    alert_on_processing_failures: bool = True


def create_enterprise_erp_config(connector_type: ConnectorType) -> ConnectorProcessingConfig:
    """Create configuration for enterprise ERP systems (SAP, Oracle, etc.)."""
    characteristics = get_connector_characteristics(connector_type)
    
    return ConnectorProcessingConfig(
        connector_type=connector_type,
        profile=ProcessingProfile.ENTERPRISE_ERP,
        
        # ERP data is highly structured and trusted
        enable_validation=True,
        enable_duplicate_detection=True,
        enable_amount_validation=False,  # ERP amounts are trusted
        enable_business_rules=True,
        enable_pattern_matching=True,
        enable_customer_matching=True,
        
        # ERP systems have good data quality - don't fail on minor issues
        fail_on_validation_errors=False,
        fail_on_duplicates=False,  # ERP might legitimately have similar transactions
        fail_on_business_rule_violations=True,  # Compliance is critical
        fail_on_high_fraud_risk=False,  # ERP is trusted
        
        # Performance optimized for batch processing
        max_processing_time=60,
        enable_parallel_processing=True,
        batch_size=500,  # ERP can handle large batches
        
        # High confidence in ERP data
        minimum_confidence_threshold=0.8,
        maximum_risk_tolerance="low",
        confidence_weights=[0.3, 0.1, 0.6],  # Trust pattern matching over amount validation
        
        # Nigerian business compliance
        compliance_rules=characteristics.nigerian_compliance_requirements,
        
        # ERP-specific optimizations
        connector_specific_settings={
            "trust_invoice_numbers": True,
            "validate_customer_codes": True,
            "enforce_accounting_standards": True,
            "require_cost_center_mapping": True,
            "enable_multi_currency": True
        },
        
        # Skip unnecessary checks for trusted systems
        skip_low_value_fraud_detection=True,
        low_value_threshold=5000.0,
        
        # Focus on business intelligence
        prioritize_customer_matching=True,
        enable_merchant_identification=False,  # Not applicable for ERP
        enable_category_prediction=True,
        
        # Enterprise monitoring
        enable_detailed_logging=True,
        log_performance_metrics=True,
        alert_on_processing_failures=True
    )


def create_small_business_config(connector_type: ConnectorType) -> ConnectorProcessingConfig:
    """Create configuration for small business systems (Odoo, QuickBooks, etc.)."""
    characteristics = get_connector_characteristics(connector_type)
    
    return ConnectorProcessingConfig(
        connector_type=connector_type,
        profile=ProcessingProfile.SMALL_BUSINESS,
        
        # Moderate validation for small business systems
        enable_validation=True,
        enable_duplicate_detection=True,
        enable_amount_validation=True,  # Some validation needed
        enable_business_rules=True,
        enable_pattern_matching=True,
        enable_customer_matching=True,
        
        # Balanced error handling
        fail_on_validation_errors=False,
        fail_on_duplicates=False,
        fail_on_business_rule_violations=True,
        fail_on_high_fraud_risk=False,
        
        # Standard performance settings
        max_processing_time=45,
        enable_parallel_processing=True,
        batch_size=200,
        
        # Moderate confidence requirements
        minimum_confidence_threshold=0.7,
        maximum_risk_tolerance="medium",
        confidence_weights=[0.4, 0.2, 0.4],
        
        # SME compliance requirements
        compliance_rules=characteristics.nigerian_compliance_requirements,
        
        # Small business optimizations
        connector_specific_settings={
            "flexible_data_formats": True,
            "auto_correct_minor_errors": True,
            "simplified_reporting": True,
            "sme_tax_rules": True
        },
        
        # Moderate fraud detection
        skip_low_value_fraud_detection=True,
        low_value_threshold=2000.0,
        
        # Comprehensive enrichment
        prioritize_customer_matching=True,
        enable_merchant_identification=True,
        enable_category_prediction=True,
        
        # Standard monitoring
        enable_detailed_logging=False,
        log_performance_metrics=True,
        alert_on_processing_failures=True
    )


def create_customer_facing_config(connector_type: ConnectorType) -> ConnectorProcessingConfig:
    """Create configuration for customer-facing systems (POS, E-commerce, CRM)."""
    characteristics = get_connector_characteristics(connector_type)
    
    return ConnectorProcessingConfig(
        connector_type=connector_type,
        profile=ProcessingProfile.CUSTOMER_FACING,
        
        # Full validation for customer-facing systems
        enable_validation=True,
        enable_duplicate_detection=True,
        enable_amount_validation=True,
        enable_business_rules=True,
        enable_pattern_matching=True,
        enable_customer_matching=True,
        
        # Strict error handling for customer data
        fail_on_validation_errors=False,
        fail_on_duplicates=False,  # Customers might make similar purchases
        fail_on_business_rule_violations=False,
        fail_on_high_fraud_risk=True,  # Important for customer-facing
        
        # Standard performance
        max_processing_time=30,
        enable_parallel_processing=True,
        batch_size=150,
        
        # Moderate confidence with customer data variability
        minimum_confidence_threshold=0.6,
        maximum_risk_tolerance="medium",
        confidence_weights=[0.4, 0.4, 0.2],  # Balance validation and amount checks
        
        # Customer protection compliance
        compliance_rules=characteristics.nigerian_compliance_requirements,
        
        # Customer-specific settings
        connector_specific_settings={
            "customer_data_validation": True,
            "receipt_generation": True,
            "consumer_protection": True,
            "payment_method_tracking": True
        },
        
        # Enable fraud detection
        skip_low_value_fraud_detection=False,
        low_value_threshold=500.0,
        
        # Customer-focused enrichment
        prioritize_customer_matching=True,
        enable_merchant_identification=True,
        enable_category_prediction=True,
        
        # Customer service monitoring
        enable_detailed_logging=False,
        log_performance_metrics=True,
        alert_on_processing_failures=True
    )


def create_financial_data_config(connector_type: ConnectorType) -> ConnectorProcessingConfig:
    """Create configuration for financial data sources (Banking, Open Banking)."""
    characteristics = get_connector_characteristics(connector_type)
    
    return ConnectorProcessingConfig(
        connector_type=connector_type,
        profile=ProcessingProfile.FINANCIAL_DATA,
        
        # Maximum validation for financial data
        enable_validation=True,
        enable_duplicate_detection=True,
        enable_amount_validation=True,
        enable_business_rules=True,
        enable_pattern_matching=True,
        enable_customer_matching=True,
        
        # Strict financial compliance
        fail_on_validation_errors=False,  # Financial data can be messy
        fail_on_duplicates=True,  # Critical for financial transactions
        fail_on_business_rule_violations=True,
        fail_on_high_fraud_risk=True,
        
        # Conservative performance for accuracy
        max_processing_time=90,
        enable_parallel_processing=True,
        batch_size=50,  # Smaller batches for accuracy
        
        # High standards for financial data
        minimum_confidence_threshold=0.8,
        maximum_risk_tolerance="low",
        confidence_weights=[0.3, 0.5, 0.2],  # Emphasize amount validation
        
        # Financial compliance requirements
        compliance_rules=characteristics.nigerian_compliance_requirements,
        
        # Financial-specific settings
        connector_specific_settings={
            "enhanced_fraud_detection": True,
            "regulatory_reporting": True,
            "transaction_monitoring": True,
            "anti_money_laundering": True,
            "know_your_customer": True
        },
        
        # No skipping for financial data
        skip_low_value_fraud_detection=False,
        low_value_threshold=100.0,  # Very low threshold
        
        # Comprehensive financial enrichment
        prioritize_customer_matching=True,
        enable_merchant_identification=True,
        enable_category_prediction=True,
        
        # Enhanced monitoring for financial data
        enable_detailed_logging=True,
        log_performance_metrics=True,
        alert_on_processing_failures=True
    )


def get_default_processing_configs() -> Dict[ConnectorType, ConnectorProcessingConfig]:
    """Get default processing configurations for all supported connector types."""
    
    configs = {}
    
    # Enterprise ERP Systems
    enterprise_erp_connectors = [
        ConnectorType.ERP_SAP,
        ConnectorType.ERP_ORACLE,
        ConnectorType.ERP_MICROSOFT_DYNAMICS,
        ConnectorType.ERP_NETSUITE
    ]
    
    for connector_type in enterprise_erp_connectors:
        configs[connector_type] = create_enterprise_erp_config(connector_type)
    
    # Small Business Systems
    small_business_connectors = [
        ConnectorType.ERP_ODOO,
        ConnectorType.ERP_SAGE,
        ConnectorType.ACCOUNTING_QUICKBOOKS,
        ConnectorType.ACCOUNTING_XERO,
        ConnectorType.ACCOUNTING_WAVE,
        ConnectorType.ACCOUNTING_FRESHBOOKS,
        ConnectorType.ACCOUNTING_SAGE
    ]
    
    for connector_type in small_business_connectors:
        configs[connector_type] = create_small_business_config(connector_type)
    
    # Customer-Facing Systems  
    customer_facing_connectors = [
        ConnectorType.CRM_SALESFORCE,
        ConnectorType.CRM_HUBSPOT,
        ConnectorType.CRM_MICROSOFT_DYNAMICS_CRM,
        ConnectorType.CRM_ZOHO,
        ConnectorType.CRM_PIPEDRIVE,
        ConnectorType.POS_RETAIL,
        ConnectorType.POS_HOSPITALITY,
        ConnectorType.POS_ECOMMERCE,
        ConnectorType.ECOMMERCE_SHOPIFY,
        ConnectorType.ECOMMERCE_WOOCOMMERCE,
        ConnectorType.ECOMMERCE_MAGENTO,
        ConnectorType.ECOMMERCE_JUMIA,
        ConnectorType.ECOMMERCE_BIGCOMMERCE,
        ConnectorType.INVENTORY_FISHBOWL,
        ConnectorType.INVENTORY_CIN7
    ]
    
    for connector_type in customer_facing_connectors:
        configs[connector_type] = create_customer_facing_config(connector_type)
    
    # Financial Data Sources
    financial_data_connectors = [
        ConnectorType.BANKING_OPEN_BANKING
    ]
    
    for connector_type in financial_data_connectors:
        configs[connector_type] = create_financial_data_config(connector_type)
    
    return configs


def get_processing_config(
    connector_type: ConnectorType,
    custom_overrides: Optional[Dict[str, Any]] = None
) -> ConnectorProcessingConfig:
    """
    Get processing configuration for a connector type with optional overrides.
    
    Args:
        connector_type: Type of connector
        custom_overrides: Optional configuration overrides
        
    Returns:
        Processing configuration for the connector type
    """
    default_configs = get_default_processing_configs()
    config = default_configs.get(connector_type)
    
    if not config:
        # Create a default configuration for unknown connector types
        config = create_small_business_config(connector_type)
    
    # Apply custom overrides if provided
    if custom_overrides:
        for key, value in custom_overrides.items():
            if hasattr(config, key):
                setattr(config, key, value)
            else:
                # Add to connector-specific settings
                config.connector_specific_settings[key] = value
    
    return config


def validate_processing_config(config: ConnectorProcessingConfig) -> List[str]:
    """
    Validate a processing configuration for consistency and correctness.
    
    Args:
        config: Configuration to validate
        
    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []
    
    # Validate confidence weights
    if len(config.confidence_weights) != 3:
        errors.append("Confidence weights must have exactly 3 values [validation, amount, pattern]")
    elif abs(sum(config.confidence_weights) - 1.0) > 0.01:
        errors.append("Confidence weights must sum to 1.0")
    
    # Validate thresholds
    if not (0.0 <= config.minimum_confidence_threshold <= 1.0):
        errors.append("Minimum confidence threshold must be between 0.0 and 1.0")
    
    if config.max_processing_time <= 0:
        errors.append("Max processing time must be positive")
    
    if config.batch_size <= 0:
        errors.append("Batch size must be positive")
    
    if config.low_value_threshold < 0:
        errors.append("Low value threshold cannot be negative")
    
    # Validate risk tolerance
    valid_risk_levels = ["low", "medium", "high"]
    if config.maximum_risk_tolerance not in valid_risk_levels:
        errors.append(f"Maximum risk tolerance must be one of: {valid_risk_levels}")
    
    # Logic consistency checks
    if not config.enable_amount_validation and config.fail_on_high_fraud_risk:
        errors.append("Cannot fail on high fraud risk without amount validation enabled")
    
    if not config.enable_duplicate_detection and config.fail_on_duplicates:
        errors.append("Cannot fail on duplicates without duplicate detection enabled")
    
    return errors


def create_custom_config(
    connector_type: ConnectorType,
    base_profile: ProcessingProfile,
    **overrides
) -> ConnectorProcessingConfig:
    """
    Create a custom processing configuration based on a profile with overrides.
    
    Args:
        connector_type: Type of connector
        base_profile: Base processing profile to start with
        **overrides: Configuration overrides
        
    Returns:
        Custom processing configuration
    """
    # Create base configuration based on profile
    if base_profile == ProcessingProfile.ENTERPRISE_ERP:
        base_config = create_enterprise_erp_config(connector_type)
    elif base_profile == ProcessingProfile.SMALL_BUSINESS:
        base_config = create_small_business_config(connector_type)
    elif base_profile == ProcessingProfile.CUSTOMER_FACING:
        base_config = create_customer_facing_config(connector_type)
    elif base_profile == ProcessingProfile.FINANCIAL_DATA:
        base_config = create_financial_data_config(connector_type)
    else:
        raise ValueError(f"Unknown processing profile: {base_profile}")
    
    # Apply overrides
    for key, value in overrides.items():
        if hasattr(base_config, key):
            setattr(base_config, key, value)
        else:
            base_config.connector_specific_settings[key] = value
    
    # Validate the custom configuration
    validation_errors = validate_processing_config(base_config)
    if validation_errors:
        raise ValueError(f"Invalid configuration: {'; '.join(validation_errors)}")
    
    return base_config