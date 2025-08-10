"""
Custom Validator

Provides extensible custom validation rules for specialized requirements.
Allows users to define and execute custom validation logic beyond standard rules.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple, Callable, Union
from datetime import datetime
from decimal import Decimal
import json
import re
import importlib.util

logger = logging.getLogger(__name__)


class CustomValidationRule:
    """Represents a custom validation rule"""
    
    def __init__(
        self,
        rule_id: str,
        name: str,
        description: str,
        validator_function: Callable[[Dict[str, Any]], Tuple[bool, str]],
        conditions: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.rule_id = rule_id
        self.name = name
        self.description = description
        self.validator_function = validator_function
        self.conditions = conditions or {}
        self.metadata = metadata or {}
        self.enabled = True
        self.created_at = datetime.utcnow()


class CustomValidator:
    """
    Extensible custom validator for specialized validation requirements.
    Allows organizations to define their own validation rules and logic.
    """
    
    def __init__(self):
        self.custom_rules: Dict[str, CustomValidationRule] = {}
        self.rule_groups: Dict[str, List[str]] = {}
        self.execution_order: List[str] = []
        self.validation_context: Dict[str, Any] = {}
    
    def add_custom_rule(
        self,
        rule_id: str,
        name: str,
        description: str,
        validator_function: Callable[[Dict[str, Any]], Tuple[bool, str]],
        conditions: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        group: Optional[str] = None
    ) -> bool:
        """
        Add a custom validation rule.
        
        Args:
            rule_id: Unique identifier for the rule
            name: Human-readable name
            description: Rule description
            validator_function: Function that performs validation
            conditions: Conditions for when to apply the rule
            metadata: Additional rule metadata
            group: Optional rule group
            
        Returns:
            Success status
        """
        try:
            rule = CustomValidationRule(
                rule_id=rule_id,
                name=name,
                description=description,
                validator_function=validator_function,
                conditions=conditions,
                metadata=metadata
            )
            
            self.custom_rules[rule_id] = rule
            
            # Add to group if specified
            if group:
                if group not in self.rule_groups:
                    self.rule_groups[group] = []
                self.rule_groups[group].append(rule_id)
            
            # Add to execution order if not already present
            if rule_id not in self.execution_order:
                self.execution_order.append(rule_id)
            
            logger.info(f"Added custom validation rule: {rule_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding custom rule {rule_id}: {e}")
            return False
    
    def remove_custom_rule(self, rule_id: str) -> bool:
        """Remove a custom validation rule"""
        try:
            if rule_id in self.custom_rules:
                del self.custom_rules[rule_id]
                
                # Remove from execution order
                if rule_id in self.execution_order:
                    self.execution_order.remove(rule_id)
                
                # Remove from groups
                for group_rules in self.rule_groups.values():
                    if rule_id in group_rules:
                        group_rules.remove(rule_id)
                
                logger.info(f"Removed custom validation rule: {rule_id}")
                return True
            else:
                logger.warning(f"Custom rule not found: {rule_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error removing custom rule {rule_id}: {e}")
            return False
    
    def validate_with_custom_rules(
        self,
        data: Dict[str, Any],
        rule_group: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Validate data using custom rules.
        
        Args:
            data: Data to validate
            rule_group: Optional rule group to execute
            context: Additional validation context
            
        Returns:
            Tuple of (is_valid, validation_errors)
        """
        validation_errors = []
        
        try:
            # Update validation context
            if context:
                self.validation_context.update(context)
            
            # Determine which rules to execute
            rules_to_execute = self._get_rules_to_execute(rule_group)
            
            logger.info(f"Executing {len(rules_to_execute)} custom validation rules")
            
            for rule_id in rules_to_execute:
                rule = self.custom_rules.get(rule_id)
                if not rule or not rule.enabled:
                    continue
                
                try:
                    # Check if rule conditions are met
                    if not self._check_rule_conditions(rule, data):
                        logger.debug(f"Skipping rule {rule_id} - conditions not met")
                        continue
                    
                    # Execute the validator function
                    is_valid, error_message = rule.validator_function(data)
                    
                    if not is_valid:
                        validation_errors.append({
                            "rule_id": rule_id,
                            "rule_name": rule.name,
                            "rule_type": "custom",
                            "severity": rule.metadata.get("severity", "error"),
                            "message": error_message,
                            "description": rule.description,
                            "metadata": rule.metadata
                        })
                        
                        logger.warning(f"Custom rule violation: {rule_id} - {error_message}")
                
                except Exception as e:
                    logger.error(f"Error executing custom rule {rule_id}: {e}")
                    validation_errors.append({
                        "rule_id": rule_id,
                        "rule_name": rule.name,
                        "rule_type": "custom",
                        "severity": "error",
                        "message": f"Rule execution failed: {str(e)}",
                        "description": rule.description,
                        "metadata": {"execution_error": True}
                    })
            
            is_valid = not any(error["severity"] == "error" for error in validation_errors)
            return is_valid, validation_errors
            
        except Exception as e:
            logger.error(f"Error during custom validation: {e}")
            return False, [{
                "rule_id": "system_error",
                "rule_name": "System Error",
                "rule_type": "custom",
                "severity": "error",
                "message": f"Custom validation failed: {str(e)}",
                "description": "System error during custom validation"
            }]
    
    def load_rules_from_config(self, config_data: Dict[str, Any]) -> bool:
        """
        Load custom rules from configuration data.
        
        Args:
            config_data: Configuration containing rule definitions
            
        Returns:
            Success status
        """
        try:
            rules_config = config_data.get("custom_rules", [])
            
            for rule_config in rules_config:
                rule_id = rule_config.get("rule_id")
                if not rule_id:
                    logger.warning("Skipping rule without rule_id")
                    continue
                
                # Create validator function from config
                validator_function = self._create_validator_from_config(rule_config)
                if not validator_function:
                    logger.warning(f"Could not create validator for rule {rule_id}")
                    continue
                
                self.add_custom_rule(
                    rule_id=rule_id,
                    name=rule_config.get("name", rule_id),
                    description=rule_config.get("description", ""),
                    validator_function=validator_function,
                    conditions=rule_config.get("conditions"),
                    metadata=rule_config.get("metadata"),
                    group=rule_config.get("group")
                )
            
            logger.info(f"Loaded {len(rules_config)} custom rules from configuration")
            return True
            
        except Exception as e:
            logger.error(f"Error loading rules from config: {e}")
            return False
    
    def load_rules_from_file(self, file_path: str) -> bool:
        """
        Load custom rules from a JSON file.
        
        Args:
            file_path: Path to JSON configuration file
            
        Returns:
            Success status
        """
        try:
            with open(file_path, 'r') as f:
                config_data = json.load(f)
            
            return self.load_rules_from_config(config_data)
            
        except Exception as e:
            logger.error(f"Error loading rules from file {file_path}: {e}")
            return False
    
    def load_rule_from_python_module(self, module_path: str, rule_id: str) -> bool:
        """
        Load a custom rule from a Python module.
        
        Args:
            module_path: Path to Python module containing rule
            rule_id: ID for the rule
            
        Returns:
            Success status
        """
        try:
            spec = importlib.util.spec_from_file_location("custom_rule", module_path)
            if not spec or not spec.loader:
                logger.error(f"Could not load module from {module_path}")
                return False
            
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Look for validator function
            if hasattr(module, 'validate'):
                validator_function = module.validate
            else:
                logger.error(f"Module {module_path} must define a 'validate' function")
                return False
            
            # Get rule metadata
            name = getattr(module, 'RULE_NAME', rule_id)
            description = getattr(module, 'RULE_DESCRIPTION', f"Custom rule from {module_path}")
            metadata = getattr(module, 'RULE_METADATA', {})
            conditions = getattr(module, 'RULE_CONDITIONS', None)
            group = getattr(module, 'RULE_GROUP', None)
            
            return self.add_custom_rule(
                rule_id=rule_id,
                name=name,
                description=description,
                validator_function=validator_function,
                conditions=conditions,
                metadata=metadata,
                group=group
            )
            
        except Exception as e:
            logger.error(f"Error loading rule from module {module_path}: {e}")
            return False
    
    def enable_rule(self, rule_id: str) -> bool:
        """Enable a custom rule"""
        if rule_id in self.custom_rules:
            self.custom_rules[rule_id].enabled = True
            logger.info(f"Enabled custom rule: {rule_id}")
            return True
        return False
    
    def disable_rule(self, rule_id: str) -> bool:
        """Disable a custom rule"""
        if rule_id in self.custom_rules:
            self.custom_rules[rule_id].enabled = False
            logger.info(f"Disabled custom rule: {rule_id}")
            return True
        return False
    
    def set_execution_order(self, rule_ids: List[str]) -> bool:
        """Set the execution order for custom rules"""
        try:
            # Validate that all rule IDs exist
            missing_rules = [rule_id for rule_id in rule_ids if rule_id not in self.custom_rules]
            if missing_rules:
                logger.error(f"Cannot set execution order - missing rules: {missing_rules}")
                return False
            
            self.execution_order = rule_ids.copy()
            logger.info(f"Set custom rule execution order: {rule_ids}")
            return True
            
        except Exception as e:
            logger.error(f"Error setting execution order: {e}")
            return False
    
    def get_rule_summary(self) -> Dict[str, Any]:
        """Get summary of custom rules"""
        return {
            "total_rules": len(self.custom_rules),
            "enabled_rules": sum(1 for rule in self.custom_rules.values() if rule.enabled),
            "rule_groups": {group: len(rules) for group, rules in self.rule_groups.items()},
            "execution_order": self.execution_order.copy()
        }
    
    def export_rules_config(self) -> Dict[str, Any]:
        """Export custom rules as configuration"""
        rules_config = []
        
        for rule in self.custom_rules.values():
            rule_config = {
                "rule_id": rule.rule_id,
                "name": rule.name,
                "description": rule.description,
                "conditions": rule.conditions,
                "metadata": rule.metadata,
                "enabled": rule.enabled
            }
            
            # Find group for this rule
            for group, group_rules in self.rule_groups.items():
                if rule.rule_id in group_rules:
                    rule_config["group"] = group
                    break
            
            rules_config.append(rule_config)
        
        return {
            "custom_rules": rules_config,
            "execution_order": self.execution_order
        }
    
    def _get_rules_to_execute(self, rule_group: Optional[str] = None) -> List[str]:
        """Get list of rule IDs to execute"""
        if rule_group:
            # Execute only rules in the specified group
            group_rules = self.rule_groups.get(rule_group, [])
            # Maintain execution order for group rules
            return [rule_id for rule_id in self.execution_order if rule_id in group_rules]
        else:
            # Execute all rules in order
            return self.execution_order.copy()
    
    def _check_rule_conditions(self, rule: CustomValidationRule, data: Dict[str, Any]) -> bool:
        """Check if rule conditions are met"""
        if not rule.conditions:
            return True
        
        try:
            # Check document type condition
            if "document_type" in rule.conditions:
                required_type = rule.conditions["document_type"]
                actual_type = data.get("invoice_type_code") or data.get("firs_document_type")
                if actual_type != required_type:
                    return False
            
            # Check currency condition
            if "currency" in rule.conditions:
                required_currency = rule.conditions["currency"]
                actual_currency = data.get("currency_code")
                if actual_currency != required_currency:
                    return False
            
            # Check amount threshold condition
            if "min_amount" in rule.conditions:
                min_amount = float(rule.conditions["min_amount"])
                total_amount = float(data.get("legal_monetary_total", {}).get("tax_inclusive_amount", {}).get("value", 0))
                if total_amount < min_amount:
                    return False
            
            # Check custom condition expressions
            if "expression" in rule.conditions:
                # Simple expression evaluation (can be extended)
                expression = rule.conditions["expression"]
                return self._evaluate_condition_expression(expression, data)
            
            return True
            
        except Exception as e:
            logger.warning(f"Error checking conditions for rule {rule.rule_id}: {e}")
            return True  # Default to executing the rule if condition check fails
    
    def _evaluate_condition_expression(self, expression: str, data: Dict[str, Any]) -> bool:
        """Evaluate a simple condition expression"""
        try:
            # Simple expression parser for basic conditions
            # Format: "field operator value" (e.g., "currency_code == NGN")
            parts = expression.split()
            if len(parts) != 3:
                return True
            
            field_path, operator, expected_value = parts
            actual_value = self._get_nested_value(data, field_path)
            
            if operator == "==":
                return str(actual_value) == expected_value
            elif operator == "!=":
                return str(actual_value) != expected_value
            elif operator == ">":
                return float(actual_value) > float(expected_value)
            elif operator == "<":
                return float(actual_value) < float(expected_value)
            elif operator == ">=":
                return float(actual_value) >= float(expected_value)
            elif operator == "<=":
                return float(actual_value) <= float(expected_value)
            else:
                return True
                
        except Exception:
            return True
    
    def _get_nested_value(self, data: Dict[str, Any], path: str) -> Any:
        """Get nested value using dot notation"""
        try:
            value = data
            for key in path.split('.'):
                if isinstance(value, dict):
                    value = value.get(key)
                else:
                    return None
            return value
        except Exception:
            return None
    
    def _create_validator_from_config(self, rule_config: Dict[str, Any]) -> Optional[Callable]:
        """Create validator function from configuration"""
        try:
            validator_type = rule_config.get("validator_type")
            
            if validator_type == "field_required":
                field_path = rule_config.get("field_path")
                return lambda data: self._validate_field_required(data, field_path)
            
            elif validator_type == "field_format":
                field_path = rule_config.get("field_path")
                format_pattern = rule_config.get("format_pattern")
                return lambda data: self._validate_field_format(data, field_path, format_pattern)
            
            elif validator_type == "field_range":
                field_path = rule_config.get("field_path")
                min_value = rule_config.get("min_value")
                max_value = rule_config.get("max_value")
                return lambda data: self._validate_field_range(data, field_path, min_value, max_value)
            
            elif validator_type == "expression":
                expression = rule_config.get("expression")
                error_message = rule_config.get("error_message", "Expression validation failed")
                return lambda data: (self._evaluate_condition_expression(expression, data), error_message)
            
            else:
                logger.warning(f"Unknown validator type: {validator_type}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating validator from config: {e}")
            return None
    
    def _validate_field_required(self, data: Dict[str, Any], field_path: str) -> Tuple[bool, str]:
        """Validate that a field is present and not empty"""
        value = self._get_nested_value(data, field_path)
        if value is None or (isinstance(value, str) and not value.strip()):
            return False, f"Required field '{field_path}' is missing or empty"
        return True, ""
    
    def _validate_field_format(self, data: Dict[str, Any], field_path: str, pattern: str) -> Tuple[bool, str]:
        """Validate field format against regex pattern"""
        value = self._get_nested_value(data, field_path)
        if value is None:
            return True, ""  # Field not present, handled by required validation
        
        if not re.match(pattern, str(value)):
            return False, f"Field '{field_path}' format is invalid (expected pattern: {pattern})"
        return True, ""
    
    def _validate_field_range(self, data: Dict[str, Any], field_path: str, min_value: float, max_value: float) -> Tuple[bool, str]:
        """Validate field value is within specified range"""
        value = self._get_nested_value(data, field_path)
        if value is None:
            return True, ""  # Field not present, handled by required validation
        
        try:
            numeric_value = float(value)
            if numeric_value < min_value or numeric_value > max_value:
                return False, f"Field '{field_path}' value {numeric_value} is outside valid range [{min_value}, {max_value}]"
            return True, ""
        except (ValueError, TypeError):
            return False, f"Field '{field_path}' must be a numeric value"


# Global instance for easy access
custom_validator = CustomValidator()