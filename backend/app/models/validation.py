import uuid # type: ignore
from enum import Enum
from sqlalchemy import Column, String, Text, Boolean, TIMESTAMP, JSON, ForeignKey, UUID, Enum as SQLEnum, Integer # type: ignore
from sqlalchemy.sql import func # type: ignore  
from typing import List, Optional

from app.db.base_class import Base # type: ignore


class ValidationRuleType(str, Enum):
    """Types of validation rules."""
    SCHEMA = "schema"               # UBL schema validation
    BUSINESS_RULE = "business_rule" # Business logic validation
    FORMAT = "format"               # Format validation
    CALCULATION = "calculation"     # Calculation validation
    FIRS_REQUIREMENT = "firs_requirement" # FIRS-specific requirements


class ValidationRuleSeverity(str, Enum):
    """Severity levels for validation issues."""
    ERROR = "error"       # Validation error - fails validation
    WARNING = "warning"   # Warning - passes validation but with warnings
    INFO = "info"         # Informational - for reference only


class ValidationRuleSource(str, Enum):
    """Sources of validation rules."""
    SYSTEM = "system"     # System-defined rule (built-in)
    FIRS = "firs"         # FIRS-defined rule
    UBL = "ubl"           # UBL standard rule
    CUSTOM = "custom"     # User-defined rule


class ValidationRuleStatus(str, Enum):
    """Status of validation rules."""
    ACTIVE = "active"     # Rule is active and applied during validation
    DISABLED = "disabled" # Rule is disabled and not applied during validation
    DEPRECATED = "deprecated" # Rule is deprecated and should not be used


class ValidationRule(Base):
    """Base model for validation rules."""
    __tablename__ = "validation_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    rule_type = Column(SQLEnum(ValidationRuleType), nullable=False)
    field_path = Column(String(255), nullable=True)
    validation_logic = Column(JSON, nullable=False)
    error_message = Column(Text, nullable=False)
    severity = Column(SQLEnum(ValidationRuleSeverity), nullable=False, default=ValidationRuleSeverity.ERROR)
    source = Column(SQLEnum(ValidationRuleSource), nullable=False, default=ValidationRuleSource.SYSTEM)
    status = Column(SQLEnum(ValidationRuleStatus), nullable=False, default=ValidationRuleStatus.ACTIVE)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)
    created_by = Column(UUID(as_uuid=True), nullable=True)
    updated_by = Column(UUID(as_uuid=True), nullable=True)
    tags = Column(JSON, nullable=True)


class ValidationRecord(Base):
    """Record of invoice validation results."""
    __tablename__ = "validation_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    integration_id = Column(UUID(as_uuid=True), ForeignKey("integrations.id"), nullable=False)
    irn = Column(String(50), ForeignKey("irn_records.irn"), nullable=True)
    invoice_data = Column(JSON, nullable=False)
    is_valid = Column(Boolean, nullable=False)
    validation_time = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    issues = Column(JSON, nullable=True)  # List of validation errors and warnings
    external_id = Column(String(100), nullable=True)  # External invoice identifier
    validated_by = Column(UUID(as_uuid=True), nullable=True)  # User who initiated validation
    source = Column(String(50), nullable=True)  # Source of validation (e.g., "firs", "api", "odoo")
    duration_ms = Column(Integer, nullable=True)  # Validation execution time in milliseconds


class CustomValidationRule(Base):
    """User-defined or customized validation rules."""
    __tablename__ = "custom_validation_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    original_rule_id = Column(String(100), nullable=True)  # For overrides of system rules
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    rule_type = Column(SQLEnum(ValidationRuleType), nullable=False)
    field_path = Column(String(255), nullable=True)
    validator_definition = Column(JSON, nullable=False)  # Definition of the validation logic
    error_message = Column(Text, nullable=False)
    severity = Column(SQLEnum(ValidationRuleSeverity), nullable=False, default=ValidationRuleSeverity.ERROR)
    category = Column(String(50), nullable=True)  # For grouping rules
    status = Column(SQLEnum(ValidationRuleStatus), nullable=False, default=ValidationRuleStatus.ACTIVE)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)
    created_by = Column(UUID(as_uuid=True), nullable=True)
    updated_by = Column(UUID(as_uuid=True), nullable=True)


class ValidationRulePreset(Base):
    """Collection of validation rules as a preset."""
    __tablename__ = "validation_rule_presets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    preset_type = Column(String(50), nullable=False)  # e.g., "firs_nigeria", "ubl_basic"
    rules = Column(JSON, nullable=False)  # List of rule IDs
    is_default = Column(Boolean, default=False)  # Whether this is the default preset
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)
    created_by = Column(UUID(as_uuid=True), nullable=True)
    updated_by = Column(UUID(as_uuid=True), nullable=True)