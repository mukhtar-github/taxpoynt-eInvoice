"""
Validation rule management service for FIRS e-invoice requirements.

This module provides functionality for managing validation rules for invoice validation,
with particular focus on Nigerian FIRS e-invoice requirements.
"""
import logging
import uuid
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.validation import (
    ValidationRule, 
    CustomValidationRule, 
    ValidationRulePreset,
    ValidationRuleType,
    ValidationRuleSeverity,
    ValidationRuleStatus,
    ValidationRuleSource
)
from app.schemas.validation_management import (
    ValidationRuleCreate,
    ValidationRuleUpdate,
    ValidationRuleResponse,
    ValidatorPresetCreate
)
from app.services.invoice_validation_service import validation_engine

logger = logging.getLogger(__name__)


class ValidationRuleService:
    """
    Service for managing validation rules.
    
    This service provides functionality for creating, updating, and managing
    validation rules, with special focus on FIRS e-invoice requirements.
    """
    
    def __init__(self, db: Session):
        """Initialize the validation rule service."""
        self.db = db
    
    def get_rule_by_id(self, rule_id: Union[str, uuid.UUID]) -> Optional[Union[ValidationRule, CustomValidationRule]]:
        """
        Get a validation rule by ID.
        
        Args:
            rule_id: ID of the rule to retrieve
            
        Returns:
            ValidationRule or CustomValidationRule if found, None otherwise
        """
        # Try system rules first
        if isinstance(rule_id, str) and not rule_id.startswith(("custom-", "preset-")):
            # This might be a built-in rule ID like "FIRS-REQ-001"
            rule = self.db.query(ValidationRule).filter(
                ValidationRule.id.astext == rule_id
            ).first()
            return rule
            
        # Try custom rules
        rule = self.db.query(CustomValidationRule).filter(
            CustomValidationRule.id == rule_id
        ).first()
        
        return rule
    
    def create_rule(self, rule_data: ValidationRuleCreate, user_id: Optional[uuid.UUID] = None) -> ValidationRuleResponse:
        """
        Create a new validation rule.
        
        Args:
            rule_data: Rule data to create
            user_id: ID of user creating the rule
            
        Returns:
            Created rule
            
        Raises:
            HTTPException: If rule creation fails
        """
        try:
            # Create new rule
            rule = CustomValidationRule(
                id=uuid.uuid4(),
                name=rule_data.name,
                description=rule_data.description,
                rule_type=rule_data.rule_type,
                field_path=rule_data.field_path,
                validator_definition=rule_data.validation_logic,
                error_message=rule_data.error_message,
                severity=rule_data.severity,
                category="custom",
                status=ValidationRuleStatus.ACTIVE,
                created_by=user_id,
                created_at=datetime.utcnow()
            )
            
            self.db.add(rule)
            self.db.commit()
            self.db.refresh(rule)
            
            # Convert to response model
            response = ValidationRuleResponse(
                id=rule.id,
                name=rule.name,
                description=rule.description,
                rule_type=rule.rule_type,
                field_path=rule.field_path,
                validation_logic=rule.validator_definition,
                error_message=rule.error_message,
                severity=rule.severity,
                created_at=rule.created_at,
                updated_at=rule.updated_at or rule.created_at,
                active=rule.status == ValidationRuleStatus.ACTIVE
            )
            
            logger.info(f"Created new validation rule: {rule.name} ({rule.id})")
            return response
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating validation rule: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating validation rule: {str(e)}"
            )
    
    def update_rule(
        self, 
        rule_id: Union[str, uuid.UUID],
        rule_data: ValidationRuleUpdate,
        user_id: Optional[uuid.UUID] = None
    ) -> ValidationRuleResponse:
        """
        Update an existing validation rule.
        
        Args:
            rule_id: ID of the rule to update
            rule_data: Updated rule data
            user_id: ID of user updating the rule
            
        Returns:
            Updated rule
            
        Raises:
            HTTPException: If rule update fails
        """
        rule = self.get_rule_by_id(rule_id)
        if not rule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Validation rule with ID {rule_id} not found"
            )
            
        try:
            # Handle built-in rules differently
            is_builtin = isinstance(rule, ValidationRule)
            
            if is_builtin:
                # For built-in rules, create a custom rule that overrides it
                custom_rule = CustomValidationRule(
                    id=uuid.uuid4(),
                    original_rule_id=str(rule_id),
                    name=rule_data.name or rule.name,
                    description=rule_data.description or rule.description,
                    rule_type=rule_data.rule_type or rule.rule_type,
                    field_path=rule_data.field_path or rule.field_path,
                    validator_definition=rule_data.validation_logic or rule.validation_logic,
                    error_message=rule_data.error_message or rule.error_message,
                    severity=rule_data.severity or rule.severity,
                    category="override",
                    status=ValidationRuleStatus.ACTIVE if rule_data.active is None or rule_data.active else ValidationRuleStatus.DISABLED,
                    created_by=user_id,
                    created_at=datetime.utcnow()
                )
                
                self.db.add(custom_rule)
                self.db.commit()
                self.db.refresh(custom_rule)
                
                rule = custom_rule
            else:
                # Update custom rule
                if rule_data.name is not None:
                    rule.name = rule_data.name
                if rule_data.description is not None:
                    rule.description = rule_data.description
                if rule_data.rule_type is not None:
                    rule.rule_type = rule_data.rule_type
                if rule_data.field_path is not None:
                    rule.field_path = rule_data.field_path
                if rule_data.validation_logic is not None:
                    rule.validator_definition = rule_data.validation_logic
                if rule_data.error_message is not None:
                    rule.error_message = rule_data.error_message
                if rule_data.severity is not None:
                    rule.severity = rule_data.severity
                if rule_data.active is not None:
                    rule.status = ValidationRuleStatus.ACTIVE if rule_data.active else ValidationRuleStatus.DISABLED
                    
                rule.updated_by = user_id
                rule.updated_at = datetime.utcnow()
                
                self.db.commit()
                self.db.refresh(rule)
            
            # Convert to response model
            response = ValidationRuleResponse(
                id=rule.id,
                name=rule.name,
                description=rule.description,
                rule_type=rule.rule_type,
                field_path=rule.field_path,
                validation_logic=rule.validator_definition,
                error_message=rule.error_message,
                severity=rule.severity,
                created_at=rule.created_at,
                updated_at=rule.updated_at or rule.created_at,
                active=rule.status == ValidationRuleStatus.ACTIVE
            )
            
            logger.info(f"Updated validation rule: {rule.name} ({rule.id})")
            return response
            
        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating validation rule: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error updating validation rule: {str(e)}"
            )
    
    def delete_rule(self, rule_id: Union[str, uuid.UUID]) -> bool:
        """
        Delete a validation rule.
        
        Args:
            rule_id: ID of the rule to delete
            
        Returns:
            True if rule was deleted, False otherwise
            
        Raises:
            HTTPException: If rule deletion fails
        """
        rule = self.get_rule_by_id(rule_id)
        if not rule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Validation rule with ID {rule_id} not found"
            )
            
        # We can only delete custom rules
        if isinstance(rule, ValidationRule):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete built-in validation rules, use disable_rule instead"
            )
            
        try:
            self.db.delete(rule)
            self.db.commit()
            
            logger.info(f"Deleted validation rule: {rule.name} ({rule.id})")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting validation rule: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error deleting validation rule: {str(e)}"
            )
    
    def disable_rule(
        self, 
        rule_id: Union[str, uuid.UUID], 
        user_id: Optional[uuid.UUID] = None
    ) -> bool:
        """
        Disable a validation rule.
        
        Args:
            rule_id: ID of the rule to disable
            user_id: ID of user disabling the rule
            
        Returns:
            True if rule was disabled, False otherwise
            
        Raises:
            HTTPException: If rule disabling fails
        """
        rule = self.get_rule_by_id(rule_id)
        if not rule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Validation rule with ID {rule_id} not found"
            )
            
        try:
            # Handle built-in rules differently
            is_builtin = isinstance(rule, ValidationRule)
            
            if is_builtin:
                # For built-in rules, create a disabled custom rule that overrides it
                custom_rule = CustomValidationRule(
                    id=uuid.uuid4(),
                    original_rule_id=str(rule_id),
                    name=f"DISABLED: {rule.name}",
                    description=rule.description,
                    rule_type=rule.rule_type,
                    field_path=rule.field_path,
                    validator_definition=rule.validation_logic,
                    error_message=rule.error_message,
                    severity=rule.severity,
                    category="override",
                    status=ValidationRuleStatus.DISABLED,
                    created_by=user_id,
                    created_at=datetime.utcnow()
                )
                
                self.db.add(custom_rule)
                self.db.commit()
            else:
                # Update custom rule status
                rule.status = ValidationRuleStatus.DISABLED
                rule.updated_by = user_id
                rule.updated_at = datetime.utcnow()
                
                self.db.commit()
            
            logger.info(f"Disabled validation rule: {rule.name} ({rule_id})")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error disabling validation rule: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error disabling validation rule: {str(e)}"
            )
    
    def enable_rule(
        self, 
        rule_id: Union[str, uuid.UUID], 
        user_id: Optional[uuid.UUID] = None
    ) -> bool:
        """
        Enable a validation rule.
        
        Args:
            rule_id: ID of the rule to enable
            user_id: ID of user enabling the rule
            
        Returns:
            True if rule was enabled, False otherwise
            
        Raises:
            HTTPException: If rule enabling fails
        """
        rule = self.get_rule_by_id(rule_id)
        if not rule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Validation rule with ID {rule_id} not found"
            )
            
        try:
            # Handle built-in rules differently
            is_builtin = isinstance(rule, ValidationRule)
            
            if is_builtin:
                # For built-in rules, remove any disabling override
                disabled_rule = self.db.query(CustomValidationRule).filter(
                    CustomValidationRule.original_rule_id == str(rule_id),
                    CustomValidationRule.status == ValidationRuleStatus.DISABLED
                ).first()
                
                if disabled_rule:
                    self.db.delete(disabled_rule)
                    self.db.commit()
            else:
                # Update custom rule status
                rule.status = ValidationRuleStatus.ACTIVE
                rule.updated_by = user_id
                rule.updated_at = datetime.utcnow()
                
                self.db.commit()
            
            logger.info(f"Enabled validation rule: {rule.name or 'Unknown'} ({rule_id})")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error enabling validation rule: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error enabling validation rule: {str(e)}"
            )
    
    def list_rules(
        self, 
        skip: int = 0, 
        limit: int = 100, 
        include_disabled: bool = False,
        category: Optional[str] = None,
        rule_type: Optional[ValidationRuleType] = None,
        source: Optional[ValidationRuleSource] = None
    ) -> Tuple[List[ValidationRuleResponse], int]:
        """
        List validation rules.
        
        Args:
            skip: Number of rules to skip
            limit: Maximum number of rules to return
            include_disabled: Include disabled rules in results
            category: Filter by rule category
            rule_type: Filter by rule type
            source: Filter by rule source
            
        Returns:
            Tuple of (rules, total_count)
            
        Raises:
            HTTPException: If rule listing fails
        """
        try:
            # Get system rules from the database
            system_query = self.db.query(ValidationRule)
            
            # Apply filters
            if not include_disabled:
                system_query = system_query.filter(ValidationRule.status == ValidationRuleStatus.ACTIVE.value)
            if category:
                # For system rules, use tags to check category
                system_query = system_query.filter(ValidationRule.tags.contains({"category": category}))
            if rule_type:
                system_query = system_query.filter(ValidationRule.rule_type == rule_type)
            if source:
                system_query = system_query.filter(ValidationRule.source == source)
                
            # Get custom rules
            custom_query = self.db.query(CustomValidationRule)
            
            # Apply filters to custom rules
            if not include_disabled:
                custom_query = custom_query.filter(CustomValidationRule.status == ValidationRuleStatus.ACTIVE.value)
            if category:
                custom_query = custom_query.filter(CustomValidationRule.category == category)
            if rule_type:
                custom_query = custom_query.filter(CustomValidationRule.rule_type == rule_type)
                
            # Check which built-in rules are disabled by custom rules
            disabled_rule_ids = set()
            if not include_disabled:
                disabled_overrides = self.db.query(CustomValidationRule).filter(
                    CustomValidationRule.status == ValidationRuleStatus.DISABLED,
                    CustomValidationRule.original_rule_id.isnot(None)
                ).all()
                
                disabled_rule_ids = {r.original_rule_id for r in disabled_overrides}
                
            # Get system rules, filtering out disabled ones
            system_rules = system_query.all()
            filtered_system_rules = [r for r in system_rules if str(r.id) not in disabled_rule_ids]
            
            # Get custom rules
            custom_rules = custom_query.filter(CustomValidationRule.original_rule_id.is_(None)).all()
            
            # Combine rules
            combined_rules = filtered_system_rules + custom_rules
            total_count = len(combined_rules)
            
            # Apply pagination
            paginated_rules = combined_rules[skip:skip+limit]
            
            # Convert to response models
            rule_responses = []
            for rule in paginated_rules:
                is_custom = isinstance(rule, CustomValidationRule)
                
                validation_logic = rule.validator_definition if is_custom else rule.validation_logic
                
                rule_responses.append(ValidationRuleResponse(
                    id=rule.id,
                    name=rule.name,
                    description=rule.description,
                    rule_type=rule.rule_type,
                    field_path=rule.field_path,
                    validation_logic=validation_logic,
                    error_message=rule.error_message,
                    severity=rule.severity,
                    created_at=rule.created_at,
                    updated_at=rule.updated_at or rule.created_at,
                    active=rule.status == ValidationRuleStatus.ACTIVE
                ))
            
            return rule_responses, total_count
            
        except Exception as e:
            logger.error(f"Error listing validation rules: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error listing validation rules: {str(e)}"
            )
    
    def create_rule_preset(
        self, 
        preset_data: ValidatorPresetCreate, 
        user_id: Optional[uuid.UUID] = None
    ) -> ValidationRulePreset:
        """
        Create a validation rule preset.
        
        Args:
            preset_data: Preset data to create
            user_id: ID of user creating the preset
            
        Returns:
            Created preset
            
        Raises:
            HTTPException: If preset creation fails
        """
        try:
            # Check that all rules exist
            for rule_id in preset_data.rules:
                rule = self.get_rule_by_id(rule_id)
                if not rule:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Validation rule with ID {rule_id} not found"
                    )
            
            # Create preset
            preset = ValidationRulePreset(
                id=uuid.uuid4(),
                name=preset_data.name,
                description=preset_data.description,
                preset_type=preset_data.preset_type,
                rules=[str(rule_id) for rule_id in preset_data.rules],
                created_by=user_id,
                created_at=datetime.utcnow()
            )
            
            self.db.add(preset)
            self.db.commit()
            self.db.refresh(preset)
            
            logger.info(f"Created validation rule preset: {preset.name} ({preset.id})")
            return preset
            
        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating validation rule preset: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating validation rule preset: {str(e)}"
            )
    
    def create_firs_validator_preset(self, user_id: Optional[uuid.UUID] = None) -> ValidationRulePreset:
        """
        Create a validator preset with all FIRS-specific rules.
        
        Args:
            user_id: ID of user creating the preset
            
        Returns:
            Created preset
            
        Raises:
            HTTPException: If preset creation fails
        """
        try:
            # Get all FIRS rules
            rules, _ = self.list_rules(
                limit=1000, 
                include_disabled=False,
                source=ValidationRuleSource.FIRS
            )
            
            # Create preset data
            preset_data = ValidatorPresetCreate(
                name="FIRS Nigeria e-Invoice Requirements",
                description="Complete set of validation rules for Nigerian FIRS e-Invoice compliance",
                preset_type="firs_nigeria",
                rules=[rule.id for rule in rules]
            )
            
            # Create preset
            return self.create_rule_preset(preset_data, user_id)
            
        except Exception as e:
            logger.error(f"Error creating FIRS validator preset: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating FIRS validator preset: {str(e)}"
            )


# Factory function to create validation rule service
def get_validation_rule_service(db: Session) -> ValidationRuleService:
    """Get validation rule service."""
    return ValidationRuleService(db)
