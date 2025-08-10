"""
Compliance Rule Engine
=====================
Universal rule processing engine that handles rule evaluation, conflict resolution,
and cross-framework rule harmonization.
"""

import logging
import re
import json
from typing import Dict, Any, List, Optional, Union, Tuple, Callable
from datetime import datetime, date
from decimal import Decimal
from enum import Enum

from .models import (
    ConflictResolutionStrategy, ValidationSeverity, RuleConflict
)
from ..orchestrator.models import (
    ComplianceFramework, ComplianceStatus, ComplianceRule, ValidationResult
)

logger = logging.getLogger(__name__)

class RuleType(str, Enum):
    """Types of compliance rules"""
    FORMAT = "format"
    CALCULATION = "calculation"
    BUSINESS_LOGIC = "business_logic"
    REFERENCE_DATA = "reference_data"
    CROSS_VALIDATION = "cross_validation"
    TEMPORAL = "temporal"

class RuleOperator(str, Enum):
    """Rule evaluation operators"""
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    GREATER_EQUAL = "greater_equal"
    LESS_EQUAL = "less_equal"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    MATCHES_REGEX = "matches_regex"
    IN_LIST = "in_list"
    NOT_IN_LIST = "not_in_list"
    IS_EMPTY = "is_empty"
    IS_NOT_EMPTY = "is_not_empty"
    LENGTH_EQUALS = "length_equals"
    LENGTH_BETWEEN = "length_between"

class ComplianceRuleEngine:
    """
    Universal rule engine for compliance validation
    """
    
    def __init__(self):
        """Initialize compliance rule engine"""
        self.logger = logging.getLogger(__name__)
        
        # Rule registry organized by framework
        self.rule_registry: Dict[ComplianceFramework, List[ComplianceRule]] = {}
        
        # Rule evaluation functions
        self.rule_evaluators = {
            RuleOperator.EQUALS: self._evaluate_equals,
            RuleOperator.NOT_EQUALS: self._evaluate_not_equals,
            RuleOperator.GREATER_THAN: self._evaluate_greater_than,
            RuleOperator.LESS_THAN: self._evaluate_less_than,
            RuleOperator.GREATER_EQUAL: self._evaluate_greater_equal,
            RuleOperator.LESS_EQUAL: self._evaluate_less_equal,
            RuleOperator.CONTAINS: self._evaluate_contains,
            RuleOperator.NOT_CONTAINS: self._evaluate_not_contains,
            RuleOperator.MATCHES_REGEX: self._evaluate_matches_regex,
            RuleOperator.IN_LIST: self._evaluate_in_list,
            RuleOperator.NOT_IN_LIST: self._evaluate_not_in_list,
            RuleOperator.IS_EMPTY: self._evaluate_is_empty,
            RuleOperator.IS_NOT_EMPTY: self._evaluate_is_not_empty,
            RuleOperator.LENGTH_EQUALS: self._evaluate_length_equals,
            RuleOperator.LENGTH_BETWEEN: self._evaluate_length_between
        }
        
        # Framework rule priorities (for conflict resolution)
        self.framework_priorities = {
            ComplianceFramework.FIRS: 1,
            ComplianceFramework.CAC: 2,
            ComplianceFramework.NITDA: 3,
            ComplianceFramework.ISO_27001: 4,
            ComplianceFramework.ISO_20022: 5,
            ComplianceFramework.UBL: 6,
            ComplianceFramework.PEPPOL: 7,
            ComplianceFramework.GDPR: 8,
            ComplianceFramework.NDPA: 9,
            ComplianceFramework.WCO_HS: 10,
            ComplianceFramework.LEI: 11
        }
        
        # Load built-in rules
        self._load_framework_rules()
        
        self.logger.info(f"Compliance Rule Engine initialized with {self._count_total_rules()} rules")
    
    def evaluate_rules(
        self,
        data: Dict[str, Any],
        framework: ComplianceFramework,
        context: Optional[Dict[str, Any]] = None
    ) -> List[ValidationResult]:
        """
        Evaluate all rules for a specific framework
        
        Args:
            data: Data to validate
            framework: Compliance framework
            context: Optional validation context
            
        Returns:
            List of ValidationResult objects
        """
        try:
            self.logger.debug(f"Evaluating rules for framework: {framework}")
            
            framework_rules = self.rule_registry.get(framework, [])
            if not framework_rules:
                self.logger.warning(f"No rules found for framework: {framework}")
                return []
            
            validation_results = []
            context = context or {}
            
            for rule in framework_rules:
                try:
                    result = self._evaluate_single_rule(rule, data, context)
                    validation_results.append(result)
                except Exception as e:
                    self.logger.error(f"Rule evaluation failed for {rule.rule_id}: {str(e)}")
                    # Create error result
                    error_result = ValidationResult(
                        rule_id=rule.rule_id,
                        framework=framework,
                        status=ComplianceStatus.ERROR,
                        severity=ValidationSeverity.HIGH,
                        validation_timestamp=datetime.now(),
                        validation_score=0.0,
                        issues_found=[f"Rule evaluation error: {str(e)}"],
                        recommendations=[f"Fix rule configuration for {rule.rule_id}"]
                    )
                    validation_results.append(error_result)
            
            self.logger.debug(f"Evaluated {len(validation_results)} rules for {framework}")
            return validation_results
            
        except Exception as e:
            self.logger.error(f"Framework rule evaluation failed for {framework}: {str(e)}")
            return []
    
    def detect_rule_conflicts(
        self,
        framework_results: Dict[ComplianceFramework, List[ValidationResult]]
    ) -> List[RuleConflict]:
        """
        Detect conflicts between rules across frameworks
        
        Args:
            framework_results: Validation results by framework
            
        Returns:
            List of detected rule conflicts
        """
        try:
            self.logger.debug("Detecting rule conflicts across frameworks")
            
            conflicts = []
            
            # Group results by data field
            field_results = self._group_results_by_field(framework_results)
            
            # Analyze each field for conflicts
            for field, results_by_framework in field_results.items():
                field_conflicts = self._analyze_field_conflicts(field, results_by_framework)
                conflicts.extend(field_conflicts)
            
            # Detect semantic conflicts
            semantic_conflicts = self._detect_semantic_conflicts(framework_results)
            conflicts.extend(semantic_conflicts)
            
            self.logger.debug(f"Detected {len(conflicts)} rule conflicts")
            return conflicts
            
        except Exception as e:
            self.logger.error(f"Rule conflict detection failed: {str(e)}")
            return []
    
    def resolve_conflicts(
        self,
        conflicts: List[RuleConflict],
        strategy: ConflictResolutionStrategy
    ) -> Dict[str, Any]:
        """
        Resolve rule conflicts using specified strategy
        
        Args:
            conflicts: List of conflicts to resolve
            strategy: Resolution strategy to use
            
        Returns:
            Dictionary with resolution results
        """
        try:
            self.logger.debug(f"Resolving {len(conflicts)} conflicts using strategy: {strategy}")
            
            resolution_results = {
                'resolved_conflicts': [],
                'unresolved_conflicts': [],
                'resolution_summary': {},
                'recommendations': []
            }
            
            for conflict in conflicts:
                try:
                    if strategy == ConflictResolutionStrategy.STRICT_PRECEDENCE:
                        resolution = self._resolve_by_severity(conflict)
                    elif strategy == ConflictResolutionStrategy.FRAMEWORK_PRIORITY:
                        resolution = self._resolve_by_framework_priority(conflict)
                    elif strategy == ConflictResolutionStrategy.LATEST_RULE:
                        resolution = self._resolve_by_latest_rule(conflict)
                    elif strategy == ConflictResolutionStrategy.AGGREGATE:
                        resolution = self._resolve_by_aggregation(conflict)
                    else:
                        resolution = self._mark_for_manual_resolution(conflict)
                    
                    if resolution['resolved']:
                        resolution_results['resolved_conflicts'].append(resolution)
                    else:
                        resolution_results['unresolved_conflicts'].append(conflict)
                        
                except Exception as e:
                    self.logger.error(f"Failed to resolve conflict {conflict.conflict_id}: {str(e)}")
                    resolution_results['unresolved_conflicts'].append(conflict)
            
            # Generate resolution summary
            resolution_results['resolution_summary'] = self._generate_resolution_summary(resolution_results)
            resolution_results['recommendations'] = self._generate_resolution_recommendations(resolution_results)
            
            return resolution_results
            
        except Exception as e:
            self.logger.error(f"Conflict resolution failed: {str(e)}")
            return {'resolved_conflicts': [], 'unresolved_conflicts': conflicts}
    
    def add_custom_rule(self, framework: ComplianceFramework, rule: ComplianceRule):
        """
        Add custom rule to framework
        
        Args:
            framework: Target framework
            rule: Custom rule to add
        """
        if framework not in self.rule_registry:
            self.rule_registry[framework] = []
        
        # Check for duplicate rule IDs
        existing_ids = [r.rule_id for r in self.rule_registry[framework]]
        if rule.rule_id in existing_ids:
            raise ValueError(f"Rule ID {rule.rule_id} already exists in framework {framework}")
        
        self.rule_registry[framework].append(rule)
        self.logger.info(f"Added custom rule {rule.rule_id} to framework {framework}")
    
    def remove_rule(self, framework: ComplianceFramework, rule_id: str) -> bool:
        """
        Remove rule from framework
        
        Args:
            framework: Target framework
            rule_id: Rule ID to remove
            
        Returns:
            True if rule was removed
        """
        if framework not in self.rule_registry:
            return False
        
        original_count = len(self.rule_registry[framework])
        self.rule_registry[framework] = [
            r for r in self.rule_registry[framework] if r.rule_id != rule_id
        ]
        
        removed = len(self.rule_registry[framework]) < original_count
        if removed:
            self.logger.info(f"Removed rule {rule_id} from framework {framework}")
        
        return removed
    
    def get_framework_rules(self, framework: ComplianceFramework) -> List[ComplianceRule]:
        """
        Get all rules for a framework
        
        Args:
            framework: Target framework
            
        Returns:
            List of rules for the framework
        """
        return self.rule_registry.get(framework, []).copy()
    
    def get_rule_statistics(self) -> Dict[str, Any]:
        """
        Get rule engine statistics
        
        Returns:
            Dictionary with rule statistics
        """
        stats = {
            'total_rules': self._count_total_rules(),
            'rules_by_framework': {},
            'rules_by_severity': {},
            'rules_by_category': {}
        }
        
        # Count by framework
        for framework, rules in self.rule_registry.items():
            stats['rules_by_framework'][framework.value] = len(rules)
        
        # Count by severity and category
        for rules in self.rule_registry.values():
            for rule in rules:
                # Severity stats
                severity = rule.severity.value
                if severity not in stats['rules_by_severity']:
                    stats['rules_by_severity'][severity] = 0
                stats['rules_by_severity'][severity] += 1
                
                # Category stats
                category = rule.rule_category
                if category not in stats['rules_by_category']:
                    stats['rules_by_category'][category] = 0
                stats['rules_by_category'][category] += 1
        
        return stats
    
    # Private helper methods
    
    def _evaluate_single_rule(
        self,
        rule: ComplianceRule,
        data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> ValidationResult:
        """Evaluate a single compliance rule"""
        
        try:
            # Extract rule parameters
            rule_params = rule.validation_parameters
            operator = rule_params.get('operator', 'equals')
            field_path = rule_params.get('field_path', '')
            expected_value = rule_params.get('expected_value')
            
            # Extract field value from data
            actual_value = self._extract_field_value(data, field_path)
            
            # Evaluate rule
            is_compliant = self._evaluate_rule_condition(
                actual_value, expected_value, operator, rule_params
            )
            
            # Create validation result
            status = ComplianceStatus.COMPLIANT if is_compliant else ComplianceStatus.NON_COMPLIANT
            score = 100.0 if is_compliant else 0.0
            
            issues = []
            recommendations = []
            
            if not is_compliant:
                issues.append(f"Rule {rule.rule_id} failed: {rule.rule_description}")
                recommendations.append(rule.remediation_guidance)
            
            return ValidationResult(
                rule_id=rule.rule_id,
                framework=rule.framework,
                status=status,
                severity=rule.severity,
                validation_timestamp=datetime.now(),
                validation_score=score,
                issues_found=issues,
                recommendations=recommendations
            )
            
        except Exception as e:
            self.logger.error(f"Single rule evaluation failed for {rule.rule_id}: {str(e)}")
            raise
    
    def _evaluate_rule_condition(
        self,
        actual_value: Any,
        expected_value: Any,
        operator: str,
        params: Dict[str, Any]
    ) -> bool:
        """Evaluate rule condition based on operator"""
        
        try:
            operator_enum = RuleOperator(operator)
            evaluator = self.rule_evaluators.get(operator_enum)
            
            if not evaluator:
                raise ValueError(f"Unknown operator: {operator}")
            
            return evaluator(actual_value, expected_value, params)
            
        except Exception as e:
            self.logger.error(f"Rule condition evaluation failed: {str(e)}")
            return False
    
    def _extract_field_value(self, data: Dict[str, Any], field_path: str) -> Any:
        """Extract field value using dot notation path"""
        if not field_path:
            return data
        
        try:
            keys = field_path.split('.')
            value = data
            
            for key in keys:
                if isinstance(value, dict):
                    value = value.get(key)
                elif isinstance(value, list) and key.isdigit():
                    index = int(key)
                    value = value[index] if 0 <= index < len(value) else None
                else:
                    return None
                
                if value is None:
                    break
            
            return value
            
        except Exception as e:
            self.logger.debug(f"Field extraction failed for path {field_path}: {str(e)}")
            return None
    
    # Rule evaluation functions
    
    def _evaluate_equals(self, actual: Any, expected: Any, params: Dict[str, Any]) -> bool:
        """Evaluate equals condition"""
        return actual == expected
    
    def _evaluate_not_equals(self, actual: Any, expected: Any, params: Dict[str, Any]) -> bool:
        """Evaluate not equals condition"""
        return actual != expected
    
    def _evaluate_greater_than(self, actual: Any, expected: Any, params: Dict[str, Any]) -> bool:
        """Evaluate greater than condition"""
        try:
            return float(actual) > float(expected)
        except (TypeError, ValueError):
            return False
    
    def _evaluate_less_than(self, actual: Any, expected: Any, params: Dict[str, Any]) -> bool:
        """Evaluate less than condition"""
        try:
            return float(actual) < float(expected)
        except (TypeError, ValueError):
            return False
    
    def _evaluate_greater_equal(self, actual: Any, expected: Any, params: Dict[str, Any]) -> bool:
        """Evaluate greater than or equal condition"""
        try:
            return float(actual) >= float(expected)
        except (TypeError, ValueError):
            return False
    
    def _evaluate_less_equal(self, actual: Any, expected: Any, params: Dict[str, Any]) -> bool:
        """Evaluate less than or equal condition"""
        try:
            return float(actual) <= float(expected)
        except (TypeError, ValueError):
            return False
    
    def _evaluate_contains(self, actual: Any, expected: Any, params: Dict[str, Any]) -> bool:
        """Evaluate contains condition"""
        try:
            return str(expected) in str(actual)
        except (TypeError, AttributeError):
            return False
    
    def _evaluate_not_contains(self, actual: Any, expected: Any, params: Dict[str, Any]) -> bool:
        """Evaluate not contains condition"""
        try:
            return str(expected) not in str(actual)
        except (TypeError, AttributeError):
            return False
    
    def _evaluate_matches_regex(self, actual: Any, expected: Any, params: Dict[str, Any]) -> bool:
        """Evaluate regex match condition"""
        try:
            pattern = str(expected)
            text = str(actual)
            return bool(re.match(pattern, text))
        except (TypeError, re.error):
            return False
    
    def _evaluate_in_list(self, actual: Any, expected: Any, params: Dict[str, Any]) -> bool:
        """Evaluate in list condition"""
        try:
            if isinstance(expected, list):
                return actual in expected
            return False
        except TypeError:
            return False
    
    def _evaluate_not_in_list(self, actual: Any, expected: Any, params: Dict[str, Any]) -> bool:
        """Evaluate not in list condition"""
        try:
            if isinstance(expected, list):
                return actual not in expected
            return True
        except TypeError:
            return False
    
    def _evaluate_is_empty(self, actual: Any, expected: Any, params: Dict[str, Any]) -> bool:
        """Evaluate is empty condition"""
        if actual is None:
            return True
        if isinstance(actual, (str, list, dict)):
            return len(actual) == 0
        return False
    
    def _evaluate_is_not_empty(self, actual: Any, expected: Any, params: Dict[str, Any]) -> bool:
        """Evaluate is not empty condition"""
        return not self._evaluate_is_empty(actual, expected, params)
    
    def _evaluate_length_equals(self, actual: Any, expected: Any, params: Dict[str, Any]) -> bool:
        """Evaluate length equals condition"""
        try:
            if hasattr(actual, '__len__'):
                return len(actual) == int(expected)
            return False
        except (TypeError, ValueError):
            return False
    
    def _evaluate_length_between(self, actual: Any, expected: Any, params: Dict[str, Any]) -> bool:
        """Evaluate length between condition"""
        try:
            if hasattr(actual, '__len__'):
                length = len(actual)
                min_length = params.get('min_length', 0)
                max_length = params.get('max_length', float('inf'))
                return min_length <= length <= max_length
            return False
        except (TypeError, ValueError):
            return False
    
    def _group_results_by_field(
        self,
        framework_results: Dict[ComplianceFramework, List[ValidationResult]]
    ) -> Dict[str, Dict[ComplianceFramework, List[ValidationResult]]]:
        """Group validation results by data field"""
        field_results = {}
        
        for framework, results in framework_results.items():
            for result in results:
                # Extract field from rule ID or use rule ID as field
                field = result.rule_id.split('_')[-1] if '_' in result.rule_id else result.rule_id
                
                if field not in field_results:
                    field_results[field] = {}
                
                if framework not in field_results[field]:
                    field_results[field][framework] = []
                
                field_results[field][framework].append(result)
        
        return field_results
    
    def _analyze_field_conflicts(
        self,
        field: str,
        results_by_framework: Dict[ComplianceFramework, List[ValidationResult]]
    ) -> List[RuleConflict]:
        """Analyze conflicts for a specific field"""
        conflicts = []
        
        if len(results_by_framework) < 2:
            return conflicts
        
        # Check for status conflicts
        frameworks = list(results_by_framework.keys())
        for i, framework1 in enumerate(frameworks):
            for framework2 in frameworks[i+1:]:
                results1 = results_by_framework[framework1]
                results2 = results_by_framework[framework2]
                
                # Check if there are conflicting statuses
                statuses1 = set(r.status for r in results1)
                statuses2 = set(r.status for r in results2)
                
                if statuses1 != statuses2:
                    conflict = RuleConflict(
                        conflicting_rules=[f"{framework1}_{field}", f"{framework2}_{field}"],
                        frameworks_involved=[framework1, framework2],
                        conflict_type="requirement",
                        conflict_description=f"Conflicting validation results for field {field}",
                        data_field=field,
                        resolution_strategy=ConflictResolutionStrategy.FRAMEWORK_PRIORITY,
                        resolution_result="Pending resolution",
                        business_impact="May require data format adjustment",
                        severity=ValidationSeverity.MEDIUM
                    )
                    conflicts.append(conflict)
        
        return conflicts
    
    def _detect_semantic_conflicts(
        self,
        framework_results: Dict[ComplianceFramework, List[ValidationResult]]
    ) -> List[RuleConflict]:
        """Detect semantic conflicts between frameworks"""
        conflicts = []
        
        # This would implement more sophisticated semantic conflict detection
        # For now, return empty list
        
        return conflicts
    
    def _resolve_by_severity(self, conflict: RuleConflict) -> Dict[str, Any]:
        """Resolve conflict by rule severity"""
        return {
            'resolved': True,
            'conflict_id': conflict.conflict_id,
            'resolution_method': 'severity',
            'winning_rule': conflict.conflicting_rules[0],  # Simplified
            'rationale': 'Higher severity rule takes precedence'
        }
    
    def _resolve_by_framework_priority(self, conflict: RuleConflict) -> Dict[str, Any]:
        """Resolve conflict by framework priority"""
        # Find framework with highest priority (lowest number)
        highest_priority_framework = min(
            conflict.frameworks_involved,
            key=lambda f: self.framework_priorities.get(f, 999)
        )
        
        return {
            'resolved': True,
            'conflict_id': conflict.conflict_id,
            'resolution_method': 'framework_priority',
            'winning_framework': highest_priority_framework,
            'rationale': f'Framework {highest_priority_framework} has higher priority'
        }
    
    def _resolve_by_latest_rule(self, conflict: RuleConflict) -> Dict[str, Any]:
        """Resolve conflict by latest rule"""
        return {
            'resolved': True,
            'conflict_id': conflict.conflict_id,
            'resolution_method': 'latest_rule',
            'winning_rule': conflict.conflicting_rules[-1],  # Assume last is latest
            'rationale': 'Most recent rule takes precedence'
        }
    
    def _resolve_by_aggregation(self, conflict: RuleConflict) -> Dict[str, Any]:
        """Resolve conflict by aggregating requirements"""
        return {
            'resolved': True,
            'conflict_id': conflict.conflict_id,
            'resolution_method': 'aggregation',
            'resolution': 'Combined requirements from all frameworks',
            'rationale': 'Aggregate all framework requirements'
        }
    
    def _mark_for_manual_resolution(self, conflict: RuleConflict) -> Dict[str, Any]:
        """Mark conflict for manual resolution"""
        return {
            'resolved': False,
            'conflict_id': conflict.conflict_id,
            'resolution_method': 'manual',
            'rationale': 'Requires manual review and resolution'
        }
    
    def _generate_resolution_summary(self, resolution_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate resolution summary"""
        total_conflicts = len(resolution_results['resolved_conflicts']) + len(resolution_results['unresolved_conflicts'])
        resolved_count = len(resolution_results['resolved_conflicts'])
        
        return {
            'total_conflicts': total_conflicts,
            'resolved_conflicts': resolved_count,
            'unresolved_conflicts': len(resolution_results['unresolved_conflicts']),
            'resolution_rate': (resolved_count / total_conflicts * 100) if total_conflicts > 0 else 100
        }
    
    def _generate_resolution_recommendations(self, resolution_results: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on resolution results"""
        recommendations = []
        
        if resolution_results['unresolved_conflicts']:
            recommendations.append("Review unresolved conflicts manually")
        
        if resolution_results['resolved_conflicts']:
            recommendations.append("Implement resolved conflict decisions in system configuration")
        
        recommendations.append("Regular review of rule conflicts to maintain compliance harmony")
        
        return recommendations
    
    def _count_total_rules(self) -> int:
        """Count total rules across all frameworks"""
        return sum(len(rules) for rules in self.rule_registry.values())
    
    def _load_framework_rules(self):
        """Load built-in rules for all frameworks"""
        # This would load rules from configuration files or database
        # For now, we'll add some basic rules for demonstration
        
        # FIRS rules
        self.rule_registry[ComplianceFramework.FIRS] = [
            ComplianceRule(
                rule_id="FIRS_TIN_FORMAT",
                framework=ComplianceFramework.FIRS,
                rule_name="TIN Format Validation",
                rule_description="Nigerian TIN must be 14 digits",
                rule_category="format",
                severity=ValidationSeverity.CRITICAL,
                validation_logic="TIN format validation",
                validation_parameters={
                    "operator": "matches_regex",
                    "field_path": "supplier_tin",
                    "expected_value": r"^\d{14}$"
                },
                regulatory_reference="FIRS TIN Guidelines",
                applicable_jurisdictions=["Nigeria"],
                effective_date=date(2020, 1, 1),
                business_impact="Invalid TIN prevents e-invoice submission",
                remediation_guidance="Ensure TIN is exactly 14 digits"
            )
        ]
        
        # CAC rules
        self.rule_registry[ComplianceFramework.CAC] = [
            ComplianceRule(
                rule_id="CAC_RC_FORMAT",
                framework=ComplianceFramework.CAC,
                rule_name="RC Number Format",
                rule_description="RC number must be 6-7 digits",
                rule_category="format",
                severity=ValidationSeverity.HIGH,
                validation_logic="RC number format validation",
                validation_parameters={
                    "operator": "matches_regex",
                    "field_path": "rc_number",
                    "expected_value": r"^\d{6,7}$"
                },
                regulatory_reference="CAC Registration Guidelines",
                applicable_jurisdictions=["Nigeria"],
                effective_date=date(2020, 1, 1),
                business_impact="Invalid RC number affects corporate verification",
                remediation_guidance="Verify RC number format with CAC"
            )
        ]
        
        self.logger.info(f"Loaded {self._count_total_rules()} built-in rules")