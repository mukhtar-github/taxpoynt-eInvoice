"""
Hybrid Service: Cross-Role Validator
Validates compliance across SI/APP boundaries
"""
import asyncio
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List, Union, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import hashlib

from core_platform.database import get_db_session
from core_platform.models.validation import ValidationResult, CrossRoleValidation, ValidationRule
from core_platform.cache import CacheService
from core_platform.events import EventBus
from core_platform.monitoring import MetricsCollector
from core_platform.notifications import NotificationService

logger = logging.getLogger(__name__)


class ValidationScope(str, Enum):
    """Validation scope"""
    SI_TO_APP = "si_to_app"
    APP_TO_SI = "app_to_si"
    BIDIRECTIONAL = "bidirectional"
    INTERNAL = "internal"


class ValidationPhase(str, Enum):
    """Validation phases"""
    PRE_PROCESSING = "pre_processing"
    PROCESSING = "processing"
    POST_PROCESSING = "post_processing"
    HANDOFF = "handoff"
    TRANSMISSION = "transmission"
    RESPONSE = "response"


class ValidationType(str, Enum):
    """Types of validation"""
    DATA_INTEGRITY = "data_integrity"
    SCHEMA_COMPLIANCE = "schema_compliance"
    BUSINESS_RULES = "business_rules"
    SECURITY_COMPLIANCE = "security_compliance"
    CERTIFICATE_VALIDATION = "certificate_validation"
    TRANSMISSION_VALIDATION = "transmission_validation"
    RESPONSE_VALIDATION = "response_validation"
    AUDIT_TRAIL = "audit_trail"


class ValidationSeverity(str, Enum):
    """Validation severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ValidationStatus(str, Enum):
    """Validation status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    SKIPPED = "skipped"


@dataclass
class ValidationRule:
    """Cross-role validation rule"""
    rule_id: str
    name: str
    description: str
    validation_type: ValidationType
    validation_scope: ValidationScope
    validation_phase: ValidationPhase
    severity: ValidationSeverity
    source_role: str
    target_role: str
    conditions: List[Dict[str, Any]]
    validation_logic: str
    error_message: str
    remediation_steps: List[str]
    enabled: bool = True
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ValidationContext:
    """Context for cross-role validation"""
    context_id: str
    source_role: str
    target_role: str
    validation_phase: ValidationPhase
    data: Dict[str, Any]
    metadata: Dict[str, Any]
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ValidationIssue:
    """Validation issue"""
    issue_id: str
    rule_id: str
    severity: ValidationSeverity
    message: str
    details: Dict[str, Any]
    field_path: Optional[str] = None
    actual_value: Optional[Any] = None
    expected_value: Optional[Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ValidationResult:
    """Cross-role validation result"""
    validation_id: str
    context: ValidationContext
    status: ValidationStatus
    rules_checked: List[str]
    issues: List[ValidationIssue]
    score: float
    execution_time: float
    validated_at: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DataIntegrityCheck:
    """Data integrity check result"""
    check_id: str
    source_hash: str
    target_hash: str
    integrity_verified: bool
    differences: List[Dict[str, Any]]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class CrossRoleValidator:
    """Cross-role validation service"""
    
    def __init__(self):
        self.cache_service = CacheService()
        self.event_bus = EventBus()
        self.metrics_collector = MetricsCollector()
        self.notification_service = NotificationService()
        self.logger = logging.getLogger(__name__)
        
        # Validation rules registry
        self.validation_rules: Dict[str, ValidationRule] = {}
        
        # Custom validators
        self.custom_validators: Dict[str, Any] = {}
        
        # Validation history
        self.validation_history: List[ValidationResult] = []
        
        # Schema registry
        self.schema_registry: Dict[str, Dict[str, Any]] = {}
        
        # Initialize default validation rules
        self._initialize_default_rules()
    
    async def register_validation_rule(self, rule: ValidationRule) -> bool:
        """Register a cross-role validation rule"""
        try:
            # Validate rule
            if not await self._validate_rule(rule):
                raise ValueError(f"Invalid validation rule: {rule.rule_id}")
            
            # Store rule
            self.validation_rules[rule.rule_id] = rule
            
            # Cache rule
            await self.cache_service.set(
                f"validation_rule:{rule.rule_id}",
                rule.to_dict(),
                ttl=86400  # 24 hours
            )
            
            # Emit event
            await self.event_bus.emit("validation_rule_registered", {
                "rule_id": rule.rule_id,
                "validation_type": rule.validation_type,
                "validation_scope": rule.validation_scope,
                "severity": rule.severity,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
            self.logger.info(f"Validation rule registered: {rule.rule_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error registering validation rule: {str(e)}")
            raise
    
    async def validate_cross_role_data(
        self,
        context: ValidationContext,
        validation_types: Optional[List[ValidationType]] = None,
        validation_phase: Optional[ValidationPhase] = None
    ) -> ValidationResult:
        """Validate data across roles"""
        validation_id = str(uuid.uuid4())
        start_time = datetime.now(timezone.utc)
        
        try:
            # Get applicable validation rules
            applicable_rules = await self._get_applicable_rules(
                context, validation_types, validation_phase
            )
            
            if not applicable_rules:
                self.logger.info(f"No applicable validation rules for context: {context.context_id}")
                return ValidationResult(
                    validation_id=validation_id,
                    context=context,
                    status=ValidationStatus.SKIPPED,
                    rules_checked=[],
                    issues=[],
                    score=1.0,
                    execution_time=0.0,
                    validated_at=start_time
                )
            
            # Execute validation rules
            all_issues = []
            checked_rules = []
            
            for rule in applicable_rules:
                try:
                    rule_issues = await self._execute_validation_rule(rule, context)
                    all_issues.extend(rule_issues)
                    checked_rules.append(rule.rule_id)
                    
                except Exception as e:
                    self.logger.error(f"Error executing validation rule {rule.rule_id}: {str(e)}")
                    # Create error issue
                    error_issue = ValidationIssue(
                        issue_id=str(uuid.uuid4()),
                        rule_id=rule.rule_id,
                        severity=ValidationSeverity.HIGH,
                        message=f"Validation rule execution failed: {str(e)}",
                        details={"error": str(e)}
                    )
                    all_issues.append(error_issue)
                    checked_rules.append(rule.rule_id)
            
            # Determine overall status
            if not all_issues:
                status = ValidationStatus.PASSED
            else:
                critical_issues = [i for i in all_issues if i.severity == ValidationSeverity.CRITICAL]
                if critical_issues:
                    status = ValidationStatus.FAILED
                else:
                    status = ValidationStatus.WARNING
            
            # Calculate score
            score = await self._calculate_validation_score(all_issues, applicable_rules)
            
            # Calculate execution time
            execution_time = (datetime.now(timezone.utc) - start_time).total_seconds()
            
            # Create validation result
            result = ValidationResult(
                validation_id=validation_id,
                context=context,
                status=status,
                rules_checked=checked_rules,
                issues=all_issues,
                score=score,
                execution_time=execution_time,
                validated_at=start_time
            )
            
            # Store result
            await self._store_validation_result(result)
            
            # Handle critical issues
            if status == ValidationStatus.FAILED:
                await self._handle_critical_issues(result)
            
            # Emit event
            await self.event_bus.emit("cross_role_validation_completed", {
                "validation_id": validation_id,
                "context_id": context.context_id,
                "status": status,
                "issues_count": len(all_issues),
                "execution_time": execution_time,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in cross-role validation: {str(e)}")
            
            # Create error result
            return ValidationResult(
                validation_id=validation_id,
                context=context,
                status=ValidationStatus.FAILED,
                rules_checked=[],
                issues=[ValidationIssue(
                    issue_id=str(uuid.uuid4()),
                    rule_id="system_error",
                    severity=ValidationSeverity.CRITICAL,
                    message=f"Validation system error: {str(e)}",
                    details={"error": str(e)}
                )],
                score=0.0,
                execution_time=(datetime.now(timezone.utc) - start_time).total_seconds(),
                validated_at=start_time
            )
    
    async def validate_si_to_app_handoff(
        self,
        si_data: Dict[str, Any],
        validation_results: Dict[str, Any],
        certificates: List[Dict[str, Any]],
        metadata: Dict[str, Any]
    ) -> ValidationResult:
        """Validate SI to APP handoff data"""
        try:
            # Create validation context
            context = ValidationContext(
                context_id=f"si_to_app_handoff_{uuid.uuid4()}",
                source_role="si",
                target_role="app",
                validation_phase=ValidationPhase.HANDOFF,
                data={
                    "si_data": si_data,
                    "validation_results": validation_results,
                    "certificates": certificates
                },
                metadata=metadata,
                timestamp=datetime.now(timezone.utc)
            )
            
            # Execute validation
            return await self.validate_cross_role_data(
                context,
                validation_types=[
                    ValidationType.DATA_INTEGRITY,
                    ValidationType.SCHEMA_COMPLIANCE,
                    ValidationType.CERTIFICATE_VALIDATION,
                    ValidationType.BUSINESS_RULES
                ],
                validation_phase=ValidationPhase.HANDOFF
            )
            
        except Exception as e:
            self.logger.error(f"Error validating SI to APP handoff: {str(e)}")
            raise
    
    async def validate_app_to_si_feedback(
        self,
        transmission_result: Dict[str, Any],
        firs_response: Dict[str, Any],
        original_context: Dict[str, Any]
    ) -> ValidationResult:
        """Validate APP to SI feedback data"""
        try:
            # Create validation context
            context = ValidationContext(
                context_id=f"app_to_si_feedback_{uuid.uuid4()}",
                source_role="app",
                target_role="si",
                validation_phase=ValidationPhase.RESPONSE,
                data={
                    "transmission_result": transmission_result,
                    "firs_response": firs_response,
                    "original_context": original_context
                },
                metadata={"feedback_type": "transmission_result"},
                timestamp=datetime.now(timezone.utc)
            )
            
            # Execute validation
            return await self.validate_cross_role_data(
                context,
                validation_types=[
                    ValidationType.RESPONSE_VALIDATION,
                    ValidationType.DATA_INTEGRITY,
                    ValidationType.AUDIT_TRAIL
                ],
                validation_phase=ValidationPhase.RESPONSE
            )
            
        except Exception as e:
            self.logger.error(f"Error validating APP to SI feedback: {str(e)}")
            raise
    
    async def validate_data_integrity(
        self,
        source_data: Dict[str, Any],
        target_data: Dict[str, Any],
        exclude_fields: Optional[List[str]] = None
    ) -> DataIntegrityCheck:
        """Validate data integrity between roles"""
        try:
            check_id = str(uuid.uuid4())
            
            # Prepare data for hashing (exclude fields that are expected to change)
            exclude_fields = exclude_fields or ['timestamp', 'processing_time', 'id', 'uuid']
            
            cleaned_source = self._clean_data_for_integrity_check(source_data, exclude_fields)
            cleaned_target = self._clean_data_for_integrity_check(target_data, exclude_fields)
            
            # Calculate hashes
            source_hash = self._calculate_data_hash(cleaned_source)
            target_hash = self._calculate_data_hash(cleaned_target)
            
            # Check integrity
            integrity_verified = source_hash == target_hash
            
            # Find differences if integrity check fails
            differences = []
            if not integrity_verified:
                differences = await self._find_data_differences(cleaned_source, cleaned_target)
            
            return DataIntegrityCheck(
                check_id=check_id,
                source_hash=source_hash,
                target_hash=target_hash,
                integrity_verified=integrity_verified,
                differences=differences
            )
            
        except Exception as e:
            self.logger.error(f"Error validating data integrity: {str(e)}")
            raise
    
    async def validate_schema_compliance(
        self,
        data: Dict[str, Any],
        schema_name: str,
        strict_mode: bool = True
    ) -> List[ValidationIssue]:
        """Validate schema compliance"""
        try:
            issues = []
            
            # Get schema
            schema = self.schema_registry.get(schema_name)
            if not schema:
                issues.append(ValidationIssue(
                    issue_id=str(uuid.uuid4()),
                    rule_id="schema_missing",
                    severity=ValidationSeverity.CRITICAL,
                    message=f"Schema not found: {schema_name}",
                    details={"schema_name": schema_name}
                ))
                return issues
            
            # Validate against schema
            schema_issues = await self._validate_against_schema(data, schema, strict_mode)
            issues.extend(schema_issues)
            
            return issues
            
        except Exception as e:
            self.logger.error(f"Error validating schema compliance: {str(e)}")
            raise
    
    async def validate_business_rules(
        self,
        data: Dict[str, Any],
        business_context: Dict[str, Any]
    ) -> List[ValidationIssue]:
        """Validate business rules"""
        try:
            issues = []
            
            # Get business rules for context
            business_rules = await self._get_business_rules(business_context)
            
            # Execute business rules
            for rule in business_rules:
                rule_issues = await self._execute_business_rule(rule, data, business_context)
                issues.extend(rule_issues)
            
            return issues
            
        except Exception as e:
            self.logger.error(f"Error validating business rules: {str(e)}")
            raise
    
    async def get_validation_history(
        self,
        context_id: Optional[str] = None,
        source_role: Optional[str] = None,
        target_role: Optional[str] = None,
        limit: int = 100
    ) -> List[ValidationResult]:
        """Get validation history"""
        try:
            filtered_history = self.validation_history
            
            # Filter by context_id
            if context_id:
                filtered_history = [
                    result for result in filtered_history
                    if result.context.context_id == context_id
                ]
            
            # Filter by source_role
            if source_role:
                filtered_history = [
                    result for result in filtered_history
                    if result.context.source_role == source_role
                ]
            
            # Filter by target_role
            if target_role:
                filtered_history = [
                    result for result in filtered_history
                    if result.context.target_role == target_role
                ]
            
            # Apply limit
            return filtered_history[-limit:]
            
        except Exception as e:
            self.logger.error(f"Error getting validation history: {str(e)}")
            return []
    
    async def get_validation_metrics(
        self,
        time_range: Optional[Tuple[datetime, datetime]] = None
    ) -> Dict[str, Any]:
        """Get validation metrics"""
        try:
            # Filter by time range
            filtered_results = self.validation_history
            if time_range:
                start_time, end_time = time_range
                filtered_results = [
                    result for result in filtered_results
                    if start_time <= result.validated_at <= end_time
                ]
            
            # Calculate metrics
            total_validations = len(filtered_results)
            passed_validations = len([r for r in filtered_results if r.status == ValidationStatus.PASSED])
            failed_validations = len([r for r in filtered_results if r.status == ValidationStatus.FAILED])
            warning_validations = len([r for r in filtered_results if r.status == ValidationStatus.WARNING])
            
            success_rate = (passed_validations / total_validations * 100) if total_validations > 0 else 0
            
            # Calculate average execution time
            execution_times = [r.execution_time for r in filtered_results]
            avg_execution_time = sum(execution_times) / len(execution_times) if execution_times else 0
            
            # Calculate average score
            scores = [r.score for r in filtered_results]
            avg_score = sum(scores) / len(scores) if scores else 0
            
            # Issue breakdown
            all_issues = []
            for result in filtered_results:
                all_issues.extend(result.issues)
            
            issue_breakdown = {}
            for issue in all_issues:
                severity = issue.severity
                issue_breakdown[severity] = issue_breakdown.get(severity, 0) + 1
            
            return {
                "total_validations": total_validations,
                "passed_validations": passed_validations,
                "failed_validations": failed_validations,
                "warning_validations": warning_validations,
                "success_rate": success_rate,
                "average_execution_time": avg_execution_time,
                "average_score": avg_score,
                "issue_breakdown": issue_breakdown,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting validation metrics: {str(e)}")
            raise
    
    async def register_schema(self, schema_name: str, schema: Dict[str, Any]) -> bool:
        """Register a validation schema"""
        try:
            self.schema_registry[schema_name] = schema
            
            # Cache schema
            await self.cache_service.set(
                f"validation_schema:{schema_name}",
                schema,
                ttl=86400  # 24 hours
            )
            
            self.logger.info(f"Schema registered: {schema_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error registering schema: {str(e)}")
            return False
    
    def register_custom_validator(self, validator_name: str, validator: Any) -> None:
        """Register a custom validator"""
        self.custom_validators[validator_name] = validator
    
    # Private helper methods
    
    async def _validate_rule(self, rule: ValidationRule) -> bool:
        """Validate validation rule"""
        try:
            # Check required fields
            if not rule.rule_id or not rule.name:
                return False
            
            # Check conditions
            if not rule.conditions:
                return False
            
            # Check validation logic
            if not rule.validation_logic:
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating rule: {str(e)}")
            return False
    
    async def _get_applicable_rules(
        self,
        context: ValidationContext,
        validation_types: Optional[List[ValidationType]] = None,
        validation_phase: Optional[ValidationPhase] = None
    ) -> List[ValidationRule]:
        """Get applicable validation rules"""
        try:
            applicable_rules = []
            
            for rule in self.validation_rules.values():
                # Check if rule is enabled
                if not rule.enabled:
                    continue
                
                # Check validation type filter
                if validation_types and rule.validation_type not in validation_types:
                    continue
                
                # Check validation phase filter
                if validation_phase and rule.validation_phase != validation_phase:
                    continue
                
                # Check scope
                if not await self._check_validation_scope(rule, context):
                    continue
                
                applicable_rules.append(rule)
            
            # Sort by severity (critical first)
            severity_order = {
                ValidationSeverity.CRITICAL: 0,
                ValidationSeverity.HIGH: 1,
                ValidationSeverity.MEDIUM: 2,
                ValidationSeverity.LOW: 3,
                ValidationSeverity.INFO: 4
            }
            
            applicable_rules.sort(key=lambda r: severity_order.get(r.severity, 5))
            
            return applicable_rules
            
        except Exception as e:
            self.logger.error(f"Error getting applicable rules: {str(e)}")
            return []
    
    async def _check_validation_scope(self, rule: ValidationRule, context: ValidationContext) -> bool:
        """Check if rule applies to validation scope"""
        try:
            if rule.validation_scope == ValidationScope.BIDIRECTIONAL:
                return True
            elif rule.validation_scope == ValidationScope.SI_TO_APP:
                return context.source_role == "si" and context.target_role == "app"
            elif rule.validation_scope == ValidationScope.APP_TO_SI:
                return context.source_role == "app" and context.target_role == "si"
            elif rule.validation_scope == ValidationScope.INTERNAL:
                return context.source_role == context.target_role
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking validation scope: {str(e)}")
            return False
    
    async def _execute_validation_rule(
        self,
        rule: ValidationRule,
        context: ValidationContext
    ) -> List[ValidationIssue]:
        """Execute validation rule"""
        try:
            # Check if custom validator exists
            if rule.validation_logic in self.custom_validators:
                validator = self.custom_validators[rule.validation_logic]
                if asyncio.iscoroutinefunction(validator):
                    return await validator(rule, context)
                else:
                    return validator(rule, context)
            
            # Default validation logic
            return await self._default_validation_logic(rule, context)
            
        except Exception as e:
            self.logger.error(f"Error executing validation rule: {str(e)}")
            return [ValidationIssue(
                issue_id=str(uuid.uuid4()),
                rule_id=rule.rule_id,
                severity=rule.severity,
                message=f"Rule execution failed: {str(e)}",
                details={"error": str(e)}
            )]
    
    async def _default_validation_logic(
        self,
        rule: ValidationRule,
        context: ValidationContext
    ) -> List[ValidationIssue]:
        """Default validation logic"""
        try:
            issues = []
            
            # Evaluate conditions
            for condition in rule.conditions:
                condition_issues = await self._evaluate_condition(condition, context, rule)
                issues.extend(condition_issues)
            
            return issues
            
        except Exception as e:
            self.logger.error(f"Error in default validation logic: {str(e)}")
            return [ValidationIssue(
                issue_id=str(uuid.uuid4()),
                rule_id=rule.rule_id,
                severity=rule.severity,
                message=f"Default validation failed: {str(e)}",
                details={"error": str(e)}
            )]
    
    async def _evaluate_condition(
        self,
        condition: Dict[str, Any],
        context: ValidationContext,
        rule: ValidationRule
    ) -> List[ValidationIssue]:
        """Evaluate validation condition"""
        try:
            condition_type = condition.get("type")
            issues = []
            
            if condition_type == "field_required":
                field_path = condition.get("field")
                if not self._get_field_value(field_path, context.data):
                    issues.append(ValidationIssue(
                        issue_id=str(uuid.uuid4()),
                        rule_id=rule.rule_id,
                        severity=rule.severity,
                        message=f"Required field missing: {field_path}",
                        details={"field_path": field_path},
                        field_path=field_path
                    ))
            
            elif condition_type == "field_format":
                field_path = condition.get("field")
                format_pattern = condition.get("pattern")
                field_value = self._get_field_value(field_path, context.data)
                
                if field_value and not re.match(format_pattern, str(field_value)):
                    issues.append(ValidationIssue(
                        issue_id=str(uuid.uuid4()),
                        rule_id=rule.rule_id,
                        severity=rule.severity,
                        message=f"Field format validation failed: {field_path}",
                        details={"field_path": field_path, "pattern": format_pattern},
                        field_path=field_path,
                        actual_value=field_value
                    ))
            
            elif condition_type == "field_equals":
                field_path = condition.get("field")
                expected_value = condition.get("value")
                field_value = self._get_field_value(field_path, context.data)
                
                if field_value != expected_value:
                    issues.append(ValidationIssue(
                        issue_id=str(uuid.uuid4()),
                        rule_id=rule.rule_id,
                        severity=rule.severity,
                        message=f"Field value mismatch: {field_path}",
                        details={"field_path": field_path},
                        field_path=field_path,
                        actual_value=field_value,
                        expected_value=expected_value
                    ))
            
            elif condition_type == "data_integrity":
                source_field = condition.get("source_field")
                target_field = condition.get("target_field")
                source_value = self._get_field_value(source_field, context.data)
                target_value = self._get_field_value(target_field, context.data)
                
                if source_value != target_value:
                    issues.append(ValidationIssue(
                        issue_id=str(uuid.uuid4()),
                        rule_id=rule.rule_id,
                        severity=rule.severity,
                        message=f"Data integrity violation: {source_field} != {target_field}",
                        details={"source_field": source_field, "target_field": target_field},
                        actual_value={"source": source_value, "target": target_value}
                    ))
            
            return issues
            
        except Exception as e:
            self.logger.error(f"Error evaluating condition: {str(e)}")
            return [ValidationIssue(
                issue_id=str(uuid.uuid4()),
                rule_id=rule.rule_id,
                severity=rule.severity,
                message=f"Condition evaluation failed: {str(e)}",
                details={"error": str(e)}
            )]
    
    def _get_field_value(self, field_path: str, data: Dict[str, Any]) -> Any:
        """Get field value using dot notation"""
        try:
            parts = field_path.split('.')
            value = data
            
            for part in parts:
                if isinstance(value, dict):
                    value = value.get(part)
                elif isinstance(value, list) and part.isdigit():
                    index = int(part)
                    value = value[index] if 0 <= index < len(value) else None
                else:
                    value = None
                    break
            
            return value
            
        except Exception as e:
            self.logger.error(f"Error getting field value: {str(e)}")
            return None
    
    async def _calculate_validation_score(
        self,
        issues: List[ValidationIssue],
        rules: List[ValidationRule]
    ) -> float:
        """Calculate validation score"""
        try:
            if not rules:
                return 1.0
            
            # Weight issues by severity
            severity_weights = {
                ValidationSeverity.CRITICAL: 1.0,
                ValidationSeverity.HIGH: 0.7,
                ValidationSeverity.MEDIUM: 0.4,
                ValidationSeverity.LOW: 0.2,
                ValidationSeverity.INFO: 0.1
            }
            
            total_deductions = 0.0
            for issue in issues:
                weight = severity_weights.get(issue.severity, 0.5)
                total_deductions += weight
            
            # Calculate score (0.0 to 1.0)
            max_possible_deductions = len(rules) * 1.0
            score = max(0.0, 1.0 - (total_deductions / max_possible_deductions))
            
            return score
            
        except Exception as e:
            self.logger.error(f"Error calculating validation score: {str(e)}")
            return 0.0
    
    def _clean_data_for_integrity_check(
        self,
        data: Dict[str, Any],
        exclude_fields: List[str]
    ) -> Dict[str, Any]:
        """Clean data for integrity check"""
        try:
            cleaned = {}
            
            for key, value in data.items():
                if key not in exclude_fields:
                    if isinstance(value, dict):
                        cleaned[key] = self._clean_data_for_integrity_check(value, exclude_fields)
                    elif isinstance(value, list):
                        cleaned[key] = [
                            self._clean_data_for_integrity_check(item, exclude_fields)
                            if isinstance(item, dict) else item
                            for item in value
                        ]
                    else:
                        cleaned[key] = value
            
            return cleaned
            
        except Exception as e:
            self.logger.error(f"Error cleaning data for integrity check: {str(e)}")
            return data
    
    def _calculate_data_hash(self, data: Dict[str, Any]) -> str:
        """Calculate hash of data"""
        try:
            # Convert to JSON string with sorted keys for consistent hashing
            json_string = json.dumps(data, sort_keys=True, default=str)
            return hashlib.sha256(json_string.encode()).hexdigest()
            
        except Exception as e:
            self.logger.error(f"Error calculating data hash: {str(e)}")
            return ""
    
    async def _find_data_differences(
        self,
        source_data: Dict[str, Any],
        target_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Find differences between source and target data"""
        try:
            differences = []
            
            # Find differences in source data
            for key, value in source_data.items():
                if key not in target_data:
                    differences.append({
                        "type": "missing_in_target",
                        "field": key,
                        "source_value": value
                    })
                elif target_data[key] != value:
                    differences.append({
                        "type": "value_mismatch",
                        "field": key,
                        "source_value": value,
                        "target_value": target_data[key]
                    })
            
            # Find fields only in target data
            for key, value in target_data.items():
                if key not in source_data:
                    differences.append({
                        "type": "missing_in_source",
                        "field": key,
                        "target_value": value
                    })
            
            return differences
            
        except Exception as e:
            self.logger.error(f"Error finding data differences: {str(e)}")
            return []
    
    async def _validate_against_schema(
        self,
        data: Dict[str, Any],
        schema: Dict[str, Any],
        strict_mode: bool
    ) -> List[ValidationIssue]:
        """Validate data against schema"""
        try:
            issues = []
            
            # Check required fields
            required_fields = schema.get("required", [])
            for field in required_fields:
                if field not in data:
                    issues.append(ValidationIssue(
                        issue_id=str(uuid.uuid4()),
                        rule_id="schema_validation",
                        severity=ValidationSeverity.HIGH,
                        message=f"Required field missing: {field}",
                        details={"field": field, "schema": schema.get("name", "unknown")},
                        field_path=field
                    ))
            
            # Check field types
            properties = schema.get("properties", {})
            for field, field_schema in properties.items():
                if field in data:
                    field_issues = await self._validate_field_against_schema(
                        field, data[field], field_schema, strict_mode
                    )
                    issues.extend(field_issues)
            
            # Check for unexpected fields in strict mode
            if strict_mode:
                allowed_fields = set(properties.keys())
                actual_fields = set(data.keys())
                unexpected_fields = actual_fields - allowed_fields
                
                for field in unexpected_fields:
                    issues.append(ValidationIssue(
                        issue_id=str(uuid.uuid4()),
                        rule_id="schema_validation",
                        severity=ValidationSeverity.MEDIUM,
                        message=f"Unexpected field: {field}",
                        details={"field": field, "schema": schema.get("name", "unknown")},
                        field_path=field
                    ))
            
            return issues
            
        except Exception as e:
            self.logger.error(f"Error validating against schema: {str(e)}")
            return []
    
    async def _validate_field_against_schema(
        self,
        field_name: str,
        field_value: Any,
        field_schema: Dict[str, Any],
        strict_mode: bool
    ) -> List[ValidationIssue]:
        """Validate field against schema"""
        try:
            issues = []
            
            # Check type
            expected_type = field_schema.get("type")
            if expected_type:
                actual_type = type(field_value).__name__
                type_mapping = {
                    "str": "string",
                    "int": "integer",
                    "float": "number",
                    "bool": "boolean",
                    "list": "array",
                    "dict": "object"
                }
                
                mapped_type = type_mapping.get(actual_type, actual_type)
                if mapped_type != expected_type:
                    issues.append(ValidationIssue(
                        issue_id=str(uuid.uuid4()),
                        rule_id="schema_validation",
                        severity=ValidationSeverity.MEDIUM,
                        message=f"Field type mismatch: {field_name}",
                        details={"field": field_name, "expected_type": expected_type, "actual_type": mapped_type},
                        field_path=field_name,
                        expected_value=expected_type,
                        actual_value=mapped_type
                    ))
            
            # Check format
            format_pattern = field_schema.get("format")
            if format_pattern and isinstance(field_value, str):
                if not re.match(format_pattern, field_value):
                    issues.append(ValidationIssue(
                        issue_id=str(uuid.uuid4()),
                        rule_id="schema_validation",
                        severity=ValidationSeverity.MEDIUM,
                        message=f"Field format validation failed: {field_name}",
                        details={"field": field_name, "format": format_pattern},
                        field_path=field_name,
                        actual_value=field_value
                    ))
            
            return issues
            
        except Exception as e:
            self.logger.error(f"Error validating field against schema: {str(e)}")
            return []
    
    async def _get_business_rules(self, business_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get business rules for context"""
        try:
            # This would typically fetch from a business rules engine
            # For now, return empty list
            return []
            
        except Exception as e:
            self.logger.error(f"Error getting business rules: {str(e)}")
            return []
    
    async def _execute_business_rule(
        self,
        rule: Dict[str, Any],
        data: Dict[str, Any],
        business_context: Dict[str, Any]
    ) -> List[ValidationIssue]:
        """Execute business rule"""
        try:
            # Business rule execution logic would go here
            return []
            
        except Exception as e:
            self.logger.error(f"Error executing business rule: {str(e)}")
            return []
    
    async def _store_validation_result(self, result: ValidationResult) -> None:
        """Store validation result"""
        try:
            # Add to history
            self.validation_history.append(result)
            
            # Store in database
            with get_db_session() as db:
                db_result = CrossRoleValidation(
                    validation_id=result.validation_id,
                    context=result.context.to_dict(),
                    status=result.status,
                    rules_checked=result.rules_checked,
                    issues=[issue.to_dict() for issue in result.issues],
                    score=result.score,
                    execution_time=result.execution_time,
                    validated_at=result.validated_at
                )
                db.add(db_result)
                db.commit()
            
            # Cache result
            await self.cache_service.set(
                f"validation_result:{result.validation_id}",
                result.to_dict(),
                ttl=3600  # 1 hour
            )
            
        except Exception as e:
            self.logger.error(f"Error storing validation result: {str(e)}")
    
    async def _handle_critical_issues(self, result: ValidationResult) -> None:
        """Handle critical validation issues"""
        try:
            critical_issues = [
                issue for issue in result.issues
                if issue.severity == ValidationSeverity.CRITICAL
            ]
            
            if critical_issues:
                # Send notification
                await self.notification_service.send_critical_validation_alert(
                    validation_id=result.validation_id,
                    context_id=result.context.context_id,
                    issues=critical_issues
                )
                
                # Emit event
                await self.event_bus.emit("critical_validation_issues", {
                    "validation_id": result.validation_id,
                    "context_id": result.context.context_id,
                    "critical_issues_count": len(critical_issues),
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
                
        except Exception as e:
            self.logger.error(f"Error handling critical issues: {str(e)}")
    
    def _initialize_default_rules(self):
        """Initialize default validation rules"""
        try:
            # SI to APP handoff validation
            si_to_app_rule = ValidationRule(
                rule_id="si_to_app_handoff_validation",
                name="SI to APP Handoff Validation",
                description="Validates data integrity during SI to APP handoff",
                validation_type=ValidationType.DATA_INTEGRITY,
                validation_scope=ValidationScope.SI_TO_APP,
                validation_phase=ValidationPhase.HANDOFF,
                severity=ValidationSeverity.CRITICAL,
                source_role="si",
                target_role="app",
                conditions=[
                    {
                        "type": "field_required",
                        "field": "si_data.invoice_number"
                    },
                    {
                        "type": "field_required",
                        "field": "si_data.irn"
                    },
                    {
                        "type": "field_required",
                        "field": "validation_results.schema_valid"
                    },
                    {
                        "type": "data_integrity",
                        "source_field": "si_data.total_amount",
                        "target_field": "validation_results.calculated_total"
                    }
                ],
                validation_logic="validate_si_to_app_handoff",
                error_message="SI to APP handoff validation failed",
                remediation_steps=[
                    "Verify all required fields are present",
                    "Check data integrity between SI and validation results",
                    "Ensure IRN is properly generated"
                ],
                enabled=True
            )
            
            # APP to SI feedback validation
            app_to_si_rule = ValidationRule(
                rule_id="app_to_si_feedback_validation",
                name="APP to SI Feedback Validation",
                description="Validates APP to SI feedback data",
                validation_type=ValidationType.RESPONSE_VALIDATION,
                validation_scope=ValidationScope.APP_TO_SI,
                validation_phase=ValidationPhase.RESPONSE,
                severity=ValidationSeverity.HIGH,
                source_role="app",
                target_role="si",
                conditions=[
                    {
                        "type": "field_required",
                        "field": "transmission_result.status"
                    },
                    {
                        "type": "field_required",
                        "field": "firs_response.response_code"
                    }
                ],
                validation_logic="validate_app_to_si_feedback",
                error_message="APP to SI feedback validation failed",
                remediation_steps=[
                    "Verify transmission result status is present",
                    "Check FIRS response code is included",
                    "Ensure feedback contains original context reference"
                ],
                enabled=True
            )
            
            # Certificate validation
            certificate_rule = ValidationRule(
                rule_id="certificate_validation",
                name="Certificate Validation",
                description="Validates digital certificates",
                validation_type=ValidationType.CERTIFICATE_VALIDATION,
                validation_scope=ValidationScope.BIDIRECTIONAL,
                validation_phase=ValidationPhase.PRE_PROCESSING,
                severity=ValidationSeverity.CRITICAL,
                source_role="any",
                target_role="any",
                conditions=[
                    {
                        "type": "field_required",
                        "field": "certificates"
                    },
                    {
                        "type": "custom",
                        "validator": "validate_certificate_chain"
                    }
                ],
                validation_logic="validate_certificates",
                error_message="Certificate validation failed",
                remediation_steps=[
                    "Ensure certificates are present",
                    "Verify certificate chain is valid",
                    "Check certificate expiry dates"
                ],
                enabled=True
            )
            
            # Store default rules
            self.validation_rules[si_to_app_rule.rule_id] = si_to_app_rule
            self.validation_rules[app_to_si_rule.rule_id] = app_to_si_rule
            self.validation_rules[certificate_rule.rule_id] = certificate_rule
            
        except Exception as e:
            self.logger.error(f"Error initializing default rules: {str(e)}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for cross-role validator"""
        try:
            return {
                "status": "healthy",
                "service": "cross_role_validator",
                "registered_rules": len(self.validation_rules),
                "registered_schemas": len(self.schema_registry),
                "custom_validators": len(self.custom_validators),
                "validation_history_size": len(self.validation_history),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error in health check: {str(e)}")
            return {
                "status": "error",
                "service": "cross_role_validator",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    async def cleanup(self) -> None:
        """Cleanup validator resources"""
        try:
            # Clear registries
            self.validation_rules.clear()
            self.custom_validators.clear()
            self.validation_history.clear()
            self.schema_registry.clear()
            
            self.logger.info("Cross-role validator cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}")


def create_cross_role_validator() -> CrossRoleValidator:
    """Create cross-role validator instance"""
    return CrossRoleValidator()