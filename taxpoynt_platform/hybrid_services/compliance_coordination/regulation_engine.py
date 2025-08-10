"""
Hybrid Service: Regulation Engine
Unified regulation enforcement across SI and APP roles
"""
import asyncio
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List, Union, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import re

from core_platform.database import get_db_session
from core_platform.models.compliance import Regulation, RegulationRule, ComplianceViolation
from core_platform.cache import CacheService
from core_platform.events import EventBus
from core_platform.monitoring import MetricsCollector
from core_platform.notifications import NotificationService

logger = logging.getLogger(__name__)


class RegulationType(str, Enum):
    """Types of regulations"""
    FIRS_EINVOICE = "firs_einvoice"
    DATA_PROTECTION = "data_protection"
    FINANCIAL_REPORTING = "financial_reporting"
    AUDIT_TRAIL = "audit_trail"
    CERTIFICATE_MANAGEMENT = "certificate_management"
    TRANSMISSION_SECURITY = "transmission_security"
    TAXPAYER_PRIVACY = "taxpayer_privacy"
    BUSINESS_RULES = "business_rules"


class RuleType(str, Enum):
    """Types of regulation rules"""
    MANDATORY = "mandatory"
    CONDITIONAL = "conditional"
    OPTIONAL = "optional"
    TECHNICAL = "technical"
    BUSINESS = "business"
    SECURITY = "security"


class ComplianceLevel(str, Enum):
    """Compliance requirement levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFORMATIONAL = "informational"


class ViolationSeverity(str, Enum):
    """Violation severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    WARNING = "warning"


class ServiceScope(str, Enum):
    """Service scope for regulation enforcement"""
    SI_ONLY = "si_only"
    APP_ONLY = "app_only"
    SI_AND_APP = "si_and_app"
    HYBRID = "hybrid"
    ALL = "all"


@dataclass
class RegulationRule:
    """Regulation rule definition"""
    rule_id: str
    regulation_type: RegulationType
    name: str
    description: str
    rule_type: RuleType
    compliance_level: ComplianceLevel
    service_scope: ServiceScope
    conditions: List[Dict[str, Any]]
    actions: List[Dict[str, Any]]
    validation_logic: str
    remediation_steps: List[str]
    enabled: bool = True
    effective_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ComplianceViolation:
    """Compliance violation record"""
    violation_id: str
    rule_id: str
    service_role: str
    service_name: str
    severity: ViolationSeverity
    message: str
    details: Dict[str, Any]
    context: Dict[str, Any]
    detected_at: datetime
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    resolved_by: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ComplianceResult:
    """Compliance check result"""
    check_id: str
    rule_id: str
    compliant: bool
    score: float
    violations: List[ComplianceViolation]
    recommendations: List[str]
    checked_at: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RegulationContext:
    """Context for regulation enforcement"""
    context_id: str
    service_role: str
    service_name: str
    operation: str
    data: Dict[str, Any]
    metadata: Dict[str, Any]
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class RegulationEngine:
    """Unified regulation enforcement engine"""
    
    def __init__(self):
        self.cache_service = CacheService()
        self.event_bus = EventBus()
        self.metrics_collector = MetricsCollector()
        self.notification_service = NotificationService()
        self.logger = logging.getLogger(__name__)
        
        # Regulation rules registry
        self.regulation_rules: Dict[str, RegulationRule] = {}
        
        # Custom validators
        self.custom_validators: Dict[str, Callable] = {}
        
        # Violation handlers
        self.violation_handlers: Dict[str, Callable] = {}
        
        # Active violations
        self.active_violations: Dict[str, ComplianceViolation] = {}
        
        # Compliance history
        self.compliance_history: List[ComplianceResult] = []
        
        # Initialize default regulations
        self._initialize_firs_regulations()
    
    async def register_regulation_rule(self, rule: RegulationRule) -> bool:
        """Register a regulation rule"""
        try:
            # Validate rule
            if not await self._validate_regulation_rule(rule):
                raise ValueError(f"Invalid regulation rule: {rule.rule_id}")
            
            # Store rule
            self.regulation_rules[rule.rule_id] = rule
            
            # Cache rule
            await self.cache_service.set(
                f"regulation_rule:{rule.rule_id}",
                rule.to_dict(),
                ttl=86400  # 24 hours
            )
            
            # Emit event
            await self.event_bus.emit("regulation_rule_registered", {
                "rule_id": rule.rule_id,
                "regulation_type": rule.regulation_type,
                "compliance_level": rule.compliance_level,
                "service_scope": rule.service_scope,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
            self.logger.info(f"Regulation rule registered: {rule.rule_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error registering regulation rule: {str(e)}")
            raise
    
    async def enforce_regulations(
        self,
        context: RegulationContext,
        regulation_types: Optional[List[RegulationType]] = None
    ) -> List[ComplianceResult]:
        """Enforce regulations for given context"""
        try:
            # Get applicable rules
            applicable_rules = await self._get_applicable_rules(context, regulation_types)
            
            if not applicable_rules:
                self.logger.info(f"No applicable rules for context: {context.context_id}")
                return []
            
            # Execute compliance checks
            compliance_results = []
            
            for rule in applicable_rules:
                result = await self._execute_compliance_check(rule, context)
                compliance_results.append(result)
                
                # Handle violations
                if result.violations:
                    await self._handle_violations(result.violations, context)
            
            # Store results
            await self._store_compliance_results(compliance_results)
            
            # Emit event
            await self.event_bus.emit("regulations_enforced", {
                "context_id": context.context_id,
                "service_role": context.service_role,
                "total_checks": len(compliance_results),
                "violations_found": sum(len(r.violations) for r in compliance_results),
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
            return compliance_results
            
        except Exception as e:
            self.logger.error(f"Error enforcing regulations: {str(e)}")
            raise
    
    async def check_compliance(
        self,
        rule_id: str,
        context: RegulationContext
    ) -> ComplianceResult:
        """Check compliance for a specific rule"""
        try:
            # Get rule
            rule = await self._get_regulation_rule(rule_id)
            if not rule:
                raise ValueError(f"Regulation rule not found: {rule_id}")
            
            # Execute compliance check
            result = await self._execute_compliance_check(rule, context)
            
            # Handle violations if any
            if result.violations:
                await self._handle_violations(result.violations, context)
            
            # Store result
            await self._store_compliance_results([result])
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error checking compliance: {str(e)}")
            raise
    
    async def get_compliance_status(
        self,
        service_role: Optional[str] = None,
        regulation_type: Optional[RegulationType] = None
    ) -> Dict[str, Any]:
        """Get overall compliance status"""
        try:
            # Filter compliance history
            filtered_results = self.compliance_history
            
            if service_role:
                # This would need to be implemented based on stored context
                pass
            
            if regulation_type:
                filtered_results = [
                    result for result in filtered_results
                    if self.regulation_rules.get(result.rule_id, {}).regulation_type == regulation_type
                ]
            
            # Calculate metrics
            total_checks = len(filtered_results)
            compliant_checks = len([r for r in filtered_results if r.compliant])
            violation_count = sum(len(r.violations) for r in filtered_results)
            
            compliance_rate = (compliant_checks / total_checks * 100) if total_checks > 0 else 0
            
            # Get active violations
            active_violations = len(self.active_violations)
            
            # Get violation breakdown by severity
            violation_breakdown = {}
            for violation in self.active_violations.values():
                severity = violation.severity
                violation_breakdown[severity] = violation_breakdown.get(severity, 0) + 1
            
            return {
                "total_checks": total_checks,
                "compliant_checks": compliant_checks,
                "violation_count": violation_count,
                "compliance_rate": compliance_rate,
                "active_violations": active_violations,
                "violation_breakdown": violation_breakdown,
                "service_role": service_role,
                "regulation_type": regulation_type,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting compliance status: {str(e)}")
            raise
    
    async def resolve_violation(
        self,
        violation_id: str,
        resolution_notes: str,
        resolved_by: str
    ) -> bool:
        """Resolve a compliance violation"""
        try:
            if violation_id not in self.active_violations:
                return False
            
            violation = self.active_violations[violation_id]
            violation.resolved_at = datetime.now(timezone.utc)
            violation.resolution_notes = resolution_notes
            violation.resolved_by = resolved_by
            
            # Remove from active violations
            del self.active_violations[violation_id]
            
            # Emit event
            await self.event_bus.emit("violation_resolved", {
                "violation_id": violation_id,
                "rule_id": violation.rule_id,
                "resolved_by": resolved_by,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
            self.logger.info(f"Violation resolved: {violation_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error resolving violation: {str(e)}")
            return False
    
    async def get_active_violations(
        self,
        service_role: Optional[str] = None,
        severity: Optional[ViolationSeverity] = None
    ) -> List[ComplianceViolation]:
        """Get active violations"""
        try:
            violations = list(self.active_violations.values())
            
            # Filter by service role
            if service_role:
                violations = [v for v in violations if v.service_role == service_role]
            
            # Filter by severity
            if severity:
                violations = [v for v in violations if v.severity == severity]
            
            return violations
            
        except Exception as e:
            self.logger.error(f"Error getting active violations: {str(e)}")
            return []
    
    async def get_regulation_rules(
        self,
        regulation_type: Optional[RegulationType] = None,
        service_scope: Optional[ServiceScope] = None
    ) -> List[RegulationRule]:
        """Get regulation rules"""
        try:
            rules = list(self.regulation_rules.values())
            
            # Filter by regulation type
            if regulation_type:
                rules = [r for r in rules if r.regulation_type == regulation_type]
            
            # Filter by service scope
            if service_scope:
                rules = [r for r in rules if r.service_scope == service_scope or r.service_scope == ServiceScope.ALL]
            
            return rules
            
        except Exception as e:
            self.logger.error(f"Error getting regulation rules: {str(e)}")
            return []
    
    async def update_regulation_rule(
        self,
        rule_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """Update a regulation rule"""
        try:
            if rule_id not in self.regulation_rules:
                return False
            
            rule = self.regulation_rules[rule_id]
            
            # Update fields
            for field, value in updates.items():
                if hasattr(rule, field):
                    setattr(rule, field, value)
            
            # Update cache
            await self.cache_service.set(
                f"regulation_rule:{rule_id}",
                rule.to_dict(),
                ttl=86400
            )
            
            # Emit event
            await self.event_bus.emit("regulation_rule_updated", {
                "rule_id": rule_id,
                "updates": updates,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating regulation rule: {str(e)}")
            return False
    
    async def disable_regulation_rule(self, rule_id: str) -> bool:
        """Disable a regulation rule"""
        try:
            return await self.update_regulation_rule(rule_id, {"enabled": False})
            
        except Exception as e:
            self.logger.error(f"Error disabling regulation rule: {str(e)}")
            return False
    
    async def enable_regulation_rule(self, rule_id: str) -> bool:
        """Enable a regulation rule"""
        try:
            return await self.update_regulation_rule(rule_id, {"enabled": True})
            
        except Exception as e:
            self.logger.error(f"Error enabling regulation rule: {str(e)}")
            return False
    
    # Handler registration methods
    
    def register_custom_validator(self, validator_name: str, validator: Callable) -> None:
        """Register a custom validator"""
        self.custom_validators[validator_name] = validator
    
    def register_violation_handler(self, handler_name: str, handler: Callable) -> None:
        """Register a violation handler"""
        self.violation_handlers[handler_name] = handler
    
    # Private helper methods
    
    async def _validate_regulation_rule(self, rule: RegulationRule) -> bool:
        """Validate regulation rule"""
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
            
            # Check effective date
            if rule.effective_date and rule.expiry_date:
                if rule.effective_date >= rule.expiry_date:
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating regulation rule: {str(e)}")
            return False
    
    async def _get_regulation_rule(self, rule_id: str) -> Optional[RegulationRule]:
        """Get regulation rule"""
        try:
            # Check cache first
            cached_rule = await self.cache_service.get(f"regulation_rule:{rule_id}")
            if cached_rule:
                return RegulationRule(**cached_rule)
            
            # Check registry
            return self.regulation_rules.get(rule_id)
            
        except Exception as e:
            self.logger.error(f"Error getting regulation rule: {str(e)}")
            return None
    
    async def _get_applicable_rules(
        self,
        context: RegulationContext,
        regulation_types: Optional[List[RegulationType]] = None
    ) -> List[RegulationRule]:
        """Get applicable regulation rules for context"""
        try:
            applicable_rules = []
            
            for rule in self.regulation_rules.values():
                # Check if rule is enabled
                if not rule.enabled:
                    continue
                
                # Check effective date
                now = datetime.now(timezone.utc)
                if rule.effective_date and now < rule.effective_date:
                    continue
                if rule.expiry_date and now > rule.expiry_date:
                    continue
                
                # Check regulation type filter
                if regulation_types and rule.regulation_type not in regulation_types:
                    continue
                
                # Check service scope
                if not await self._check_service_scope(rule, context):
                    continue
                
                applicable_rules.append(rule)
            
            # Sort by compliance level (critical first)
            level_order = {
                ComplianceLevel.CRITICAL: 0,
                ComplianceLevel.HIGH: 1,
                ComplianceLevel.MEDIUM: 2,
                ComplianceLevel.LOW: 3,
                ComplianceLevel.INFORMATIONAL: 4
            }
            
            applicable_rules.sort(key=lambda r: level_order.get(r.compliance_level, 5))
            
            return applicable_rules
            
        except Exception as e:
            self.logger.error(f"Error getting applicable rules: {str(e)}")
            return []
    
    async def _check_service_scope(self, rule: RegulationRule, context: RegulationContext) -> bool:
        """Check if rule applies to service scope"""
        try:
            if rule.service_scope == ServiceScope.ALL:
                return True
            elif rule.service_scope == ServiceScope.SI_ONLY:
                return context.service_role == "si"
            elif rule.service_scope == ServiceScope.APP_ONLY:
                return context.service_role == "app"
            elif rule.service_scope == ServiceScope.SI_AND_APP:
                return context.service_role in ["si", "app"]
            elif rule.service_scope == ServiceScope.HYBRID:
                return context.service_role == "hybrid"
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking service scope: {str(e)}")
            return False
    
    async def _execute_compliance_check(
        self,
        rule: RegulationRule,
        context: RegulationContext
    ) -> ComplianceResult:
        """Execute compliance check for rule"""
        check_id = str(uuid.uuid4())
        
        try:
            # Execute validation logic
            validation_result = await self._execute_validation_logic(rule, context)
            
            # Create violations if not compliant
            violations = []
            if not validation_result["compliant"]:
                violation = ComplianceViolation(
                    violation_id=str(uuid.uuid4()),
                    rule_id=rule.rule_id,
                    service_role=context.service_role,
                    service_name=context.service_name,
                    severity=self._map_compliance_level_to_severity(rule.compliance_level),
                    message=validation_result.get("message", "Compliance violation detected"),
                    details=validation_result.get("details", {}),
                    context=context.to_dict(),
                    detected_at=datetime.now(timezone.utc)
                )
                violations.append(violation)
            
            # Generate recommendations
            recommendations = await self._generate_recommendations(rule, validation_result)
            
            # Create result
            result = ComplianceResult(
                check_id=check_id,
                rule_id=rule.rule_id,
                compliant=validation_result["compliant"],
                score=validation_result.get("score", 1.0 if validation_result["compliant"] else 0.0),
                violations=violations,
                recommendations=recommendations,
                checked_at=datetime.now(timezone.utc)
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error executing compliance check: {str(e)}")
            
            # Return error result
            return ComplianceResult(
                check_id=check_id,
                rule_id=rule.rule_id,
                compliant=False,
                score=0.0,
                violations=[],
                recommendations=[f"Error executing compliance check: {str(e)}"],
                checked_at=datetime.now(timezone.utc)
            )
    
    async def _execute_validation_logic(
        self,
        rule: RegulationRule,
        context: RegulationContext
    ) -> Dict[str, Any]:
        """Execute validation logic"""
        try:
            # Check if custom validator exists
            if rule.validation_logic in self.custom_validators:
                validator = self.custom_validators[rule.validation_logic]
                if asyncio.iscoroutinefunction(validator):
                    return await validator(rule, context)
                else:
                    return validator(rule, context)
            
            # Default validation logic based on conditions
            return await self._evaluate_conditions(rule.conditions, context)
            
        except Exception as e:
            self.logger.error(f"Error executing validation logic: {str(e)}")
            return {
                "compliant": False,
                "score": 0.0,
                "message": f"Validation error: {str(e)}",
                "details": {"error": str(e)}
            }
    
    async def _evaluate_conditions(
        self,
        conditions: List[Dict[str, Any]],
        context: RegulationContext
    ) -> Dict[str, Any]:
        """Evaluate rule conditions"""
        try:
            results = []
            
            for condition in conditions:
                condition_result = await self._evaluate_condition(condition, context)
                results.append(condition_result)
            
            # All conditions must pass for compliance
            overall_compliant = all(r["passed"] for r in results)
            
            # Calculate score
            if results:
                score = sum(r["score"] for r in results) / len(results)
            else:
                score = 0.0
            
            return {
                "compliant": overall_compliant,
                "score": score,
                "condition_results": results,
                "message": "All conditions passed" if overall_compliant else "Some conditions failed"
            }
            
        except Exception as e:
            self.logger.error(f"Error evaluating conditions: {str(e)}")
            return {
                "compliant": False,
                "score": 0.0,
                "message": f"Condition evaluation error: {str(e)}",
                "details": {"error": str(e)}
            }
    
    async def _evaluate_condition(
        self,
        condition: Dict[str, Any],
        context: RegulationContext
    ) -> Dict[str, Any]:
        """Evaluate single condition"""
        try:
            condition_type = condition.get("type")
            
            if condition_type == "field_exists":
                field_path = condition.get("field")
                field_value = self._get_field_value(field_path, context.data)
                passed = field_value is not None
                
            elif condition_type == "field_equals":
                field_path = condition.get("field")
                expected_value = condition.get("value")
                field_value = self._get_field_value(field_path, context.data)
                passed = field_value == expected_value
                
            elif condition_type == "field_regex":
                field_path = condition.get("field")
                pattern = condition.get("pattern")
                field_value = self._get_field_value(field_path, context.data)
                passed = bool(re.match(pattern, str(field_value))) if field_value else False
                
            elif condition_type == "field_range":
                field_path = condition.get("field")
                min_value = condition.get("min")
                max_value = condition.get("max")
                field_value = self._get_field_value(field_path, context.data)
                passed = (min_value <= field_value <= max_value) if field_value is not None else False
                
            elif condition_type == "custom":
                validator_name = condition.get("validator")
                if validator_name in self.custom_validators:
                    validator = self.custom_validators[validator_name]
                    if asyncio.iscoroutinefunction(validator):
                        result = await validator(condition, context)
                    else:
                        result = validator(condition, context)
                    passed = result.get("passed", False)
                else:
                    passed = False
                    
            else:
                passed = False
            
            return {
                "condition_type": condition_type,
                "passed": passed,
                "score": 1.0 if passed else 0.0,
                "details": condition
            }
            
        except Exception as e:
            self.logger.error(f"Error evaluating condition: {str(e)}")
            return {
                "condition_type": condition.get("type", "unknown"),
                "passed": False,
                "score": 0.0,
                "error": str(e)
            }
    
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
    
    def _map_compliance_level_to_severity(self, compliance_level: ComplianceLevel) -> ViolationSeverity:
        """Map compliance level to violation severity"""
        mapping = {
            ComplianceLevel.CRITICAL: ViolationSeverity.CRITICAL,
            ComplianceLevel.HIGH: ViolationSeverity.HIGH,
            ComplianceLevel.MEDIUM: ViolationSeverity.MEDIUM,
            ComplianceLevel.LOW: ViolationSeverity.LOW,
            ComplianceLevel.INFORMATIONAL: ViolationSeverity.WARNING
        }
        return mapping.get(compliance_level, ViolationSeverity.MEDIUM)
    
    async def _generate_recommendations(
        self,
        rule: RegulationRule,
        validation_result: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations based on validation result"""
        try:
            recommendations = []
            
            if not validation_result["compliant"]:
                # Add remediation steps from rule
                recommendations.extend(rule.remediation_steps)
                
                # Add specific recommendations based on condition results
                condition_results = validation_result.get("condition_results", [])
                for condition_result in condition_results:
                    if not condition_result["passed"]:
                        condition_type = condition_result["condition_type"]
                        if condition_type == "field_exists":
                            recommendations.append("Ensure all required fields are provided")
                        elif condition_type == "field_equals":
                            recommendations.append("Verify field values match expected values")
                        elif condition_type == "field_regex":
                            recommendations.append("Ensure field values follow required format")
                        elif condition_type == "field_range":
                            recommendations.append("Verify field values are within acceptable range")
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Error generating recommendations: {str(e)}")
            return ["Review compliance requirements and correct any issues"]
    
    async def _handle_violations(
        self,
        violations: List[ComplianceViolation],
        context: RegulationContext
    ) -> None:
        """Handle compliance violations"""
        try:
            for violation in violations:
                # Add to active violations
                self.active_violations[violation.violation_id] = violation
                
                # Execute violation handler if available
                handler_name = f"handle_{violation.severity}"
                if handler_name in self.violation_handlers:
                    handler = self.violation_handlers[handler_name]
                    try:
                        if asyncio.iscoroutinefunction(handler):
                            await handler(violation, context)
                        else:
                            handler(violation, context)
                    except Exception as e:
                        self.logger.error(f"Error executing violation handler: {str(e)}")
                
                # Send notification for critical violations
                if violation.severity == ViolationSeverity.CRITICAL:
                    await self._send_violation_notification(violation)
                
                # Emit event
                await self.event_bus.emit("compliance_violation_detected", {
                    "violation_id": violation.violation_id,
                    "rule_id": violation.rule_id,
                    "service_role": violation.service_role,
                    "severity": violation.severity,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
                
        except Exception as e:
            self.logger.error(f"Error handling violations: {str(e)}")
    
    async def _send_violation_notification(self, violation: ComplianceViolation) -> None:
        """Send violation notification"""
        try:
            await self.notification_service.send_violation_alert(
                violation_id=violation.violation_id,
                rule_id=violation.rule_id,
                severity=violation.severity,
                message=violation.message,
                details=violation.details
            )
            
        except Exception as e:
            self.logger.error(f"Error sending violation notification: {str(e)}")
    
    async def _store_compliance_results(self, results: List[ComplianceResult]) -> None:
        """Store compliance results"""
        try:
            # Add to history
            self.compliance_history.extend(results)
            
            # Store in database
            with get_db_session() as db:
                for result in results:
                    db_result = ComplianceResult(
                        check_id=result.check_id,
                        rule_id=result.rule_id,
                        compliant=result.compliant,
                        score=result.score,
                        violations=[v.to_dict() for v in result.violations],
                        recommendations=result.recommendations,
                        checked_at=result.checked_at
                    )
                    db.add(db_result)
                db.commit()
            
            # Cache recent results
            for result in results:
                await self.cache_service.set(
                    f"compliance_result:{result.check_id}",
                    result.to_dict(),
                    ttl=3600  # 1 hour
                )
                
        except Exception as e:
            self.logger.error(f"Error storing compliance results: {str(e)}")
    
    def _initialize_firs_regulations(self):
        """Initialize FIRS e-invoice regulations"""
        try:
            # Invoice data structure regulation
            invoice_structure_rule = RegulationRule(
                rule_id="firs_invoice_structure",
                regulation_type=RegulationType.FIRS_EINVOICE,
                name="FIRS Invoice Structure",
                description="Mandatory invoice data structure for FIRS e-invoice",
                rule_type=RuleType.MANDATORY,
                compliance_level=ComplianceLevel.CRITICAL,
                service_scope=ServiceScope.SI_AND_APP,
                conditions=[
                    {
                        "type": "field_exists",
                        "field": "invoice_number"
                    },
                    {
                        "type": "field_exists",
                        "field": "invoice_date"
                    },
                    {
                        "type": "field_exists",
                        "field": "supplier_info"
                    },
                    {
                        "type": "field_exists",
                        "field": "customer_info"
                    },
                    {
                        "type": "field_exists",
                        "field": "line_items"
                    }
                ],
                actions=[
                    {
                        "type": "validate_structure",
                        "parameters": {"schema": "firs_invoice_schema"}
                    }
                ],
                validation_logic="validate_invoice_structure",
                remediation_steps=[
                    "Ensure all mandatory invoice fields are present",
                    "Verify invoice data follows FIRS schema",
                    "Check supplier and customer information completeness"
                ],
                enabled=True
            )
            
            # Digital certificate regulation
            certificate_rule = RegulationRule(
                rule_id="firs_certificate_requirement",
                regulation_type=RegulationType.CERTIFICATE_MANAGEMENT,
                name="FIRS Certificate Requirement",
                description="Valid digital certificate required for invoice signing",
                rule_type=RuleType.MANDATORY,
                compliance_level=ComplianceLevel.CRITICAL,
                service_scope=ServiceScope.SI_ONLY,
                conditions=[
                    {
                        "type": "field_exists",
                        "field": "certificate"
                    },
                    {
                        "type": "custom",
                        "validator": "validate_certificate_validity"
                    }
                ],
                actions=[
                    {
                        "type": "validate_certificate",
                        "parameters": {"check_expiry": True}
                    }
                ],
                validation_logic="validate_certificate",
                remediation_steps=[
                    "Ensure valid digital certificate is available",
                    "Check certificate expiry date",
                    "Verify certificate chain of trust"
                ],
                enabled=True
            )
            
            # Transmission security regulation
            transmission_security_rule = RegulationRule(
                rule_id="firs_transmission_security",
                regulation_type=RegulationType.TRANSMISSION_SECURITY,
                name="FIRS Transmission Security",
                description="Secure transmission requirements for FIRS API",
                rule_type=RuleType.MANDATORY,
                compliance_level=ComplianceLevel.HIGH,
                service_scope=ServiceScope.APP_ONLY,
                conditions=[
                    {
                        "type": "field_equals",
                        "field": "transmission.protocol",
                        "value": "https"
                    },
                    {
                        "type": "field_exists",
                        "field": "transmission.authentication"
                    }
                ],
                actions=[
                    {
                        "type": "validate_transmission_security",
                        "parameters": {"require_tls": True}
                    }
                ],
                validation_logic="validate_transmission_security",
                remediation_steps=[
                    "Use HTTPS for all API communications",
                    "Implement proper authentication mechanisms",
                    "Enable TLS encryption for data transmission"
                ],
                enabled=True
            )
            
            # Store default rules
            self.regulation_rules[invoice_structure_rule.rule_id] = invoice_structure_rule
            self.regulation_rules[certificate_rule.rule_id] = certificate_rule
            self.regulation_rules[transmission_security_rule.rule_id] = transmission_security_rule
            
        except Exception as e:
            self.logger.error(f"Error initializing FIRS regulations: {str(e)}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for regulation engine"""
        try:
            return {
                "status": "healthy",
                "service": "regulation_engine",
                "registered_rules": len(self.regulation_rules),
                "active_violations": len(self.active_violations),
                "custom_validators": len(self.custom_validators),
                "violation_handlers": len(self.violation_handlers),
                "compliance_history_size": len(self.compliance_history),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error in health check: {str(e)}")
            return {
                "status": "error",
                "service": "regulation_engine",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    async def cleanup(self) -> None:
        """Cleanup regulation engine resources"""
        try:
            # Clear registries
            self.regulation_rules.clear()
            self.custom_validators.clear()
            self.violation_handlers.clear()
            self.active_violations.clear()
            self.compliance_history.clear()
            
            self.logger.info("Regulation engine cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}")


def create_regulation_engine() -> RegulationEngine:
    """Create regulation engine instance"""
    return RegulationEngine()