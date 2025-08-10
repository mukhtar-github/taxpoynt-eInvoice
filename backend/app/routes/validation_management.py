"""
API routes for validation rule management.

This module provides API endpoints for managing validation rules,
particularly focused on FIRS e-invoice specifications.
"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.models.organization import Organization
from app.models.validation import ValidationRuleType, ValidationRuleSource, ValidationRuleSeverity
from app.schemas.validation_management import (
    ValidationRuleCreate,
    ValidationRuleUpdate,
    ValidationRuleResponse,
    ValidationRuleList,
    ValidationRuleImport,
    ValidationRuleTesting,
    ValidationRuleTestResult,
    ValidatorPresetCreate,
    ValidatorPresetResponse
)
from app.services.firs_app.data_validation_service import get_validation_rule_service
from app.dependencies.auth import get_current_user, get_current_organization

router = APIRouter(prefix="/validation-rules", tags=["validation-rules"])


@router.get("", response_model=ValidationRuleList)
def list_validation_rules(
    skip: int = 0,
    limit: int = 100,
    include_disabled: bool = False,
    category: Optional[str] = None,
    rule_type: Optional[ValidationRuleType] = None,
    source: Optional[ValidationRuleSource] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List validation rules with filtering and pagination.
    
    This endpoint returns a list of validation rules that can be filtered
    by various criteria like rule type, category, and source.
    """
    validation_rule_service = get_validation_rule_service(db)
    rules, total_count = validation_rule_service.list_rules(
        skip=skip, 
        limit=limit, 
        include_disabled=include_disabled,
        category=category,
        rule_type=rule_type,
        source=source
    )
    
    return ValidationRuleList(total=total_count, items=rules)


@router.post("", response_model=ValidationRuleResponse)
def create_validation_rule(
    rule: ValidationRuleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_organization: Organization = Depends(get_current_organization)
):
    """
    Create a new validation rule.
    
    This endpoint allows creating custom validation rules for invoice validation.
    These can be tailored to specific business needs beyond standard FIRS requirements.
    """
    validation_rule_service = get_validation_rule_service(db)
    return validation_rule_service.create_rule(rule, current_user.id)


@router.get("/{rule_id}", response_model=ValidationRuleResponse)
def get_validation_rule(
    rule_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific validation rule by ID.
    
    This endpoint returns detailed information about a specific validation rule,
    including its definition, severity, and status.
    """
    validation_rule_service = get_validation_rule_service(db)
    rule = validation_rule_service.get_rule_by_id(rule_id)
    
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Validation rule with ID {rule_id} not found"
        )
    
    # Convert to response model
    is_custom = hasattr(rule, "validator_definition")
    
    return ValidationRuleResponse(
        id=rule.id,
        name=rule.name,
        description=rule.description,
        rule_type=rule.rule_type,
        field_path=rule.field_path,
        validation_logic=rule.validator_definition if is_custom else rule.validation_logic,
        error_message=rule.error_message,
        severity=rule.severity,
        created_at=rule.created_at,
        updated_at=rule.updated_at or rule.created_at,
        active=rule.status == "active"
    )


@router.put("/{rule_id}", response_model=ValidationRuleResponse)
def update_validation_rule(
    rule_id: UUID,
    rule_update: ValidationRuleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update an existing validation rule.
    
    This endpoint allows modifying existing validation rules, whether they are
    custom rules or overrides of system rules.
    """
    validation_rule_service = get_validation_rule_service(db)
    return validation_rule_service.update_rule(rule_id, rule_update, current_user.id)


@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_validation_rule(
    rule_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a validation rule.
    
    This endpoint allows deleting custom validation rules. Built-in rules 
    cannot be deleted but can be disabled.
    """
    validation_rule_service = get_validation_rule_service(db)
    validation_rule_service.delete_rule(rule_id)
    return None


@router.post("/{rule_id}/disable", status_code=status.HTTP_200_OK)
def disable_validation_rule(
    rule_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Disable a validation rule.
    
    This endpoint allows disabling a validation rule without deleting it.
    This can be used for both custom and built-in rules.
    """
    validation_rule_service = get_validation_rule_service(db)
    validation_rule_service.disable_rule(rule_id, current_user.id)
    return {"status": "success", "message": f"Validation rule {rule_id} disabled"}


@router.post("/{rule_id}/enable", status_code=status.HTTP_200_OK)
def enable_validation_rule(
    rule_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Enable a validation rule.
    
    This endpoint allows re-enabling a previously disabled validation rule.
    This can be used for both custom and built-in rules.
    """
    validation_rule_service = get_validation_rule_service(db)
    validation_rule_service.enable_rule(rule_id, current_user.id)
    return {"status": "success", "message": f"Validation rule {rule_id} enabled"}


@router.post("/test", response_model=ValidationRuleTestResult)
def test_validation_rule(
    test_data: ValidationRuleTesting,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Test a validation rule with sample data.
    
    This endpoint allows testing how a validation rule would behave
    with specific invoice data without performing actual validation.
    """
    import time
    
    validation_rule_service = get_validation_rule_service(db)
    rule = validation_rule_service.get_rule_by_id(test_data.rule_id)
    
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Validation rule with ID {test_data.rule_id} not found"
        )
    
    # Create test logic based on rule type
    is_custom = hasattr(rule, "validator_definition")
    validation_logic = rule.validator_definition if is_custom else rule.validation_logic
    
    from app.services.invoice_validation_service import validation_engine
    
    start_time = time.time()
    
    try:
        # Convert test data to object with attribute access
        class DotDict:
            def __init__(self, data):
                for key, value in data.items():
                    if isinstance(value, dict):
                        setattr(self, key, DotDict(value))
                    else:
                        setattr(self, key, value)

        test_obj = DotDict(test_data.test_data)
        
        # Find and execute validator
        validator_func = None
        
        if is_custom:
            # Custom rule, create validator function
            from app.services.validation_rule_manager import ValidationRuleManager
            manager = ValidationRuleManager(db, validation_engine)
            validator_func = manager._rule_validator_from_definition(validation_logic)
        else:
            # System rule, find rule in validation engine
            for rule_def in validation_engine.rules:
                if str(rule_def.get('id')) == str(rule.id):
                    validator_func = rule_def.get('validator')
                    break
        
        if not validator_func:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not find validator function for rule"
            )
        
        result = validator_func(test_obj)
        end_time = time.time()
        
        return ValidationRuleTestResult(
            rule_id=rule.id,
            rule_name=rule.name,
            passed=bool(result),
            message="Validation passed" if result else rule.error_message,
            execution_time_ms=round((end_time - start_time) * 1000, 2)
        )
    
    except Exception as e:
        end_time = time.time()
        return ValidationRuleTestResult(
            rule_id=rule.id,
            rule_name=rule.name,
            passed=False,
            message=f"Error executing validation: {str(e)}",
            execution_time_ms=round((end_time - start_time) * 1000, 2)
        )


@router.post("/import", response_model=ValidationRuleList)
def import_validation_rules(
    rule_import: ValidationRuleImport,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Import multiple validation rules.
    
    This endpoint allows bulk importing of validation rules, which is useful
    for setting up a new environment or synchronizing rules between systems.
    """
    validation_rule_service = get_validation_rule_service(db)
    
    created_rules = []
    for rule_data in rule_import.rules:
        try:
            rule = validation_rule_service.create_rule(rule_data, current_user.id)
            created_rules.append(rule)
        except Exception as e:
            # Continue with other rules even if one fails
            continue
    
    return ValidationRuleList(total=len(created_rules), items=created_rules)


@router.post("/presets", response_model=ValidatorPresetResponse)
def create_validator_preset(
    preset: ValidatorPresetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a validation rule preset.
    
    This endpoint allows creating named collections of validation rules that
    can be applied together for different validation scenarios.
    """
    validation_rule_service = get_validation_rule_service(db)
    preset_obj = validation_rule_service.create_rule_preset(preset, current_user.id)
    
    return ValidatorPresetResponse(
        id=preset_obj.id,
        name=preset_obj.name,
        description=preset_obj.description,
        preset_type=preset_obj.preset_type,
        rules_count=len(preset_obj.rules),
        created_at=preset_obj.created_at,
        updated_at=preset_obj.updated_at or preset_obj.created_at,
        active=True
    )


@router.post("/presets/firs", response_model=ValidatorPresetResponse)
def create_firs_validator_preset(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a preset with all FIRS validation rules.
    
    This is a convenience endpoint that automatically creates a preset
    containing all the validation rules required for FIRS e-invoice compliance.
    """
    validation_rule_service = get_validation_rule_service(db)
    preset = validation_rule_service.create_firs_validator_preset(current_user.id)
    
    return ValidatorPresetResponse(
        id=preset.id,
        name=preset.name,
        description=preset.description,
        preset_type=preset.preset_type,
        rules_count=len(preset.rules),
        created_at=preset.created_at,
        updated_at=preset.updated_at or preset.created_at,
        active=True
    )
