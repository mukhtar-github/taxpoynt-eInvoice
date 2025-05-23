"""
Schemas for validation rule management.

This module provides Pydantic models for managing validation rules,
including creating, updating, and disabling FIRS validation rules.
"""
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field, validator
from uuid import UUID


class RuleType(str, Enum):
    """Types of validation rules."""
    SCHEMA = "schema"               # UBL schema validation
    BUSINESS_RULE = "business_rule" # Business logic validation
    FORMAT = "format"               # Format validation
    CALCULATION = "calculation"     # Calculation validation
    FIRS_REQUIREMENT = "firs_requirement" # FIRS-specific requirements


class RuleSeverity(str, Enum):
    """Severity levels for validation issues."""
    ERROR = "error"       # Validation error - fails validation
    WARNING = "warning"   # Warning - passes validation but with warnings
    INFO = "info"         # Informational - for reference only


class ValidationLogicType(str, Enum):
    """Types of validation logic."""
    FIELD_PRESENCE = "field_presence"   # Field must be present
    FIELD_FORMAT = "field_format"       # Field must match a specific format
    FIELD_COMPARISON = "field_comparison" # Compare fields
    CALCULATION = "calculation"         # Calculation validation
    CONDITION = "condition"             # Conditional validation
    CUSTOM_CODE = "custom_code"         # Custom validation code


class ValidationRuleCreate(BaseModel):
    """Schema for creating a validation rule."""
    name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    rule_type: RuleType
    field_path: Optional[str] = Field(None, max_length=255)
    validation_logic: Dict[str, Any] = Field(...)
    error_message: str = Field(..., min_length=5, max_length=500)
    severity: RuleSeverity = RuleSeverity.ERROR

    @validator("validation_logic")
    def validate_logic(cls, v):
        """Validate that the logic format matches the required structure."""
        if "type" not in v:
            raise ValueError("Validation logic must include a 'type' field")
        
        logic_type = v["type"]
        
        # Validate specific logic types
        if logic_type == ValidationLogicType.FIELD_PRESENCE:
            if "field" not in v:
                raise ValueError("Field presence validation must include a 'field' path")
                
        elif logic_type == ValidationLogicType.FIELD_FORMAT:
            if "field" not in v or "pattern" not in v:
                raise ValueError("Field format validation must include 'field' and 'pattern'")
                
        elif logic_type == ValidationLogicType.FIELD_COMPARISON:
            if "field" not in v or "comparison" not in v or "value" not in v:
                raise ValueError("Field comparison must include 'field', 'comparison', and 'value'")
                
        elif logic_type == ValidationLogicType.CALCULATION:
            if "expression" not in v:
                raise ValueError("Calculation validation must include an 'expression'")
                
        elif logic_type == ValidationLogicType.CONDITION:
            if "condition" not in v:
                raise ValueError("Conditional validation must include a 'condition'")
                
        elif logic_type == ValidationLogicType.CUSTOM_CODE:
            if "code" not in v:
                raise ValueError("Custom code validation must include 'code'")
        
        return v


class ValidationRuleUpdate(BaseModel):
    """Schema for updating a validation rule."""
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    rule_type: Optional[RuleType] = None
    field_path: Optional[str] = Field(None, max_length=255)
    validation_logic: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = Field(None, min_length=5, max_length=500)
    severity: Optional[RuleSeverity] = None
    active: Optional[bool] = None


class ValidationRuleResponse(BaseModel):
    """Schema for validation rule response."""
    id: UUID
    name: str
    description: Optional[str] = None
    rule_type: RuleType
    field_path: Optional[str] = None
    validation_logic: Dict[str, Any]
    error_message: str
    severity: RuleSeverity
    created_at: datetime
    updated_at: datetime
    active: bool

    class Config:
        from_attributes = True


class ValidationRuleList(BaseModel):
    """Schema for list of validation rules."""
    total: int
    items: List[ValidationRuleResponse]


class ValidationRuleImport(BaseModel):
    """Schema for importing validation rules."""
    rules: List[ValidationRuleCreate]


class ValidatorPresetType(str, Enum):
    """Types of validator presets."""
    FIRS_NIGERIA = "firs_nigeria"   # Nigerian FIRS e-invoice requirements
    UBL_BASIC = "ubl_basic"         # Basic UBL requirements
    UBL_EXTENDED = "ubl_extended"   # Extended UBL requirements
    CUSTOM = "custom"               # Custom validator preset


class ValidatorPresetCreate(BaseModel):
    """Schema for creating a validator preset."""
    name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    preset_type: ValidatorPresetType
    rules: List[UUID] = Field(..., min_items=1)


class ValidatorPresetResponse(BaseModel):
    """Schema for validator preset response."""
    id: UUID
    name: str
    description: Optional[str] = None
    preset_type: ValidatorPresetType
    rules_count: int
    created_at: datetime
    updated_at: datetime
    active: bool

    class Config:
        from_attributes = True


class ValidationRuleTesting(BaseModel):
    """Schema for testing a validation rule."""
    rule_id: UUID
    test_data: Dict[str, Any]
    
    
class ValidationRuleTestResult(BaseModel):
    """Schema for validation rule test result."""
    rule_id: UUID
    rule_name: str
    passed: bool
    message: Optional[str] = None
    execution_time_ms: float
