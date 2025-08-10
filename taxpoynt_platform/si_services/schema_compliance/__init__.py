"""
Schema Compliance Module

Comprehensive schema validation and compliance checking for TaxPoynt SI services.
Provides UBL validation, business rule checking, custom validation, and overall compliance verification.
"""

from .ubl_validator import (
    UBLValidator,
    ubl_validator
)

from .schema_transformer import (
    SchemaTransformer,
    schema_transformer
)

from .business_rule_engine import (
    BusinessRule,
    BusinessRuleEngine,
    business_rule_engine
)

from .custom_validator import (
    CustomValidationRule,
    CustomValidator,
    custom_validator
)

from .compliance_checker import (
    ComplianceLevel,
    ComplianceStatus,
    ComplianceChecker,
    compliance_checker
)

__all__ = [
    # UBL Validator
    "UBLValidator",
    "ubl_validator",
    
    # Schema Transformer
    "SchemaTransformer", 
    "schema_transformer",
    
    # Business Rule Engine
    "BusinessRule",
    "BusinessRuleEngine",
    "business_rule_engine",
    
    # Custom Validator
    "CustomValidationRule",
    "CustomValidator",
    "custom_validator",
    
    # Compliance Checker
    "ComplianceLevel",
    "ComplianceStatus", 
    "ComplianceChecker",
    "compliance_checker"
]


def configure_schema_compliance():
    """
    Configure dependencies between schema compliance components.
    Sets up the compliance checker with all validation components.
    """
    try:
        # Configure compliance checker with all validators
        compliance_checker.set_dependencies(
            ubl_validator=ubl_validator,
            schema_transformer=schema_transformer,
            business_rule_engine=business_rule_engine,
            custom_validator=custom_validator
        )
        
        return True
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error configuring schema compliance dependencies: {e}")
        return False


def get_compliance_status() -> dict:
    """
    Get the current status of schema compliance configuration.
    
    Returns:
        Dictionary with component availability and configuration status
    """
    return {
        "components": {
            "ubl_validator": bool(ubl_validator),
            "schema_transformer": bool(schema_transformer), 
            "business_rule_engine": bool(business_rule_engine),
            "custom_validator": bool(custom_validator),
            "compliance_checker": bool(compliance_checker)
        },
        "dependencies_configured": all([
            compliance_checker.ubl_validator,
            compliance_checker.schema_transformer,
            compliance_checker.business_rule_engine,
            compliance_checker.custom_validator
        ]),
        "summary": compliance_checker.get_compliance_summary() if compliance_checker else None
    }


# Auto-configure dependencies on import
configure_schema_compliance()