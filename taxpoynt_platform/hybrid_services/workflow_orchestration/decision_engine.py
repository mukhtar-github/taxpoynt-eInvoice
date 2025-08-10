"""
Hybrid Service: Decision Engine
Automated decision making for workflows and cross-role processes
"""
import asyncio
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List, Union, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import operator
import re

from core_platform.database import get_db_session
from core_platform.models.decision import DecisionRule, DecisionExecution, DecisionContext
from core_platform.cache import CacheService
from core_platform.events import EventBus
from core_platform.monitoring import MetricsCollector
from core_platform.notifications import NotificationService

logger = logging.getLogger(__name__)


class DecisionType(str, Enum):
    """Decision types"""
    RULE_BASED = "rule_based"
    THRESHOLD_BASED = "threshold_based"
    PATTERN_MATCHING = "pattern_matching"
    RISK_ASSESSMENT = "risk_assessment"
    WORKFLOW_ROUTING = "workflow_routing"
    RESOURCE_ALLOCATION = "resource_allocation"
    ERROR_HANDLING = "error_handling"
    COMPLIANCE_CHECK = "compliance_check"


class RuleOperator(str, Enum):
    """Rule operators"""
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    GREATER_EQUAL = "greater_equal"
    LESS_EQUAL = "less_equal"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    REGEX_MATCH = "regex_match"
    IN_LIST = "in_list"
    NOT_IN_LIST = "not_in_list"


class DecisionPriority(str, Enum):
    """Decision priority levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class DecisionStatus(str, Enum):
    """Decision execution status"""
    PENDING = "pending"
    EVALUATING = "evaluating"
    COMPLETED = "completed"
    FAILED = "failed"
    OVERRIDDEN = "overridden"


@dataclass
class DecisionCondition:
    """Decision condition"""
    condition_id: str
    field_path: str
    operator: RuleOperator
    value: Any
    description: str
    weight: float = 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DecisionAction:
    """Decision action"""
    action_id: str
    action_type: str
    parameters: Dict[str, Any]
    description: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DecisionRule:
    """Decision rule definition"""
    rule_id: str
    name: str
    description: str
    decision_type: DecisionType
    priority: DecisionPriority
    conditions: List[DecisionCondition]
    actions: List[DecisionAction]
    logical_operator: str  # "AND", "OR"
    enabled: bool = True
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DecisionContext:
    """Decision context"""
    context_id: str
    source: str
    data: Dict[str, Any]
    metadata: Dict[str, Any]
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DecisionResult:
    """Decision result"""
    decision_id: str
    rule_id: str
    context_id: str
    decision: str
    confidence: float
    actions: List[DecisionAction]
    reasoning: str
    executed_at: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DecisionExecution:
    """Decision execution record"""
    execution_id: str
    decision_id: str
    status: DecisionStatus
    input_context: DecisionContext
    decision_result: Optional[DecisionResult]
    error: Optional[str]
    started_at: datetime
    completed_at: Optional[datetime]
    duration: float
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class DecisionEngine:
    """Automated decision making engine"""
    
    def __init__(self):
        self.cache_service = CacheService()
        self.event_bus = EventBus()
        self.metrics_collector = MetricsCollector()
        self.notification_service = NotificationService()
        self.logger = logging.getLogger(__name__)
        
        # Decision rules registry
        self.decision_rules: Dict[str, DecisionRule] = {}
        
        # Custom evaluators
        self.custom_evaluators: Dict[str, Callable] = {}
        
        # Action handlers
        self.action_handlers: Dict[str, Callable] = {}
        
        # Decision history
        self.decision_history: List[DecisionExecution] = []
        
        # Operator mapping
        self.operators = {
            RuleOperator.EQUALS: operator.eq,
            RuleOperator.NOT_EQUALS: operator.ne,
            RuleOperator.GREATER_THAN: operator.gt,
            RuleOperator.LESS_THAN: operator.lt,
            RuleOperator.GREATER_EQUAL: operator.ge,
            RuleOperator.LESS_EQUAL: operator.le
        }
    
    async def register_decision_rule(self, rule: DecisionRule) -> bool:
        """Register a decision rule"""
        try:
            # Validate rule
            if not await self._validate_decision_rule(rule):
                raise ValueError(f"Invalid decision rule: {rule.rule_id}")
            
            # Store rule
            self.decision_rules[rule.rule_id] = rule
            
            # Cache rule
            await self.cache_service.set(
                f"decision_rule:{rule.rule_id}",
                rule.to_dict(),
                ttl=86400  # 24 hours
            )
            
            # Emit event
            await self.event_bus.emit("decision_rule_registered", {
                "rule_id": rule.rule_id,
                "name": rule.name,
                "decision_type": rule.decision_type,
                "priority": rule.priority,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
            self.logger.info(f"Decision rule registered: {rule.rule_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error registering decision rule: {str(e)}")
            raise
    
    async def make_decision(
        self,
        context: DecisionContext,
        decision_type: Optional[DecisionType] = None,
        rule_ids: Optional[List[str]] = None
    ) -> DecisionResult:
        """Make a decision based on context"""
        execution_id = str(uuid.uuid4())
        decision_id = str(uuid.uuid4())
        
        try:
            # Create execution record
            execution = DecisionExecution(
                execution_id=execution_id,
                decision_id=decision_id,
                status=DecisionStatus.EVALUATING,
                input_context=context,
                decision_result=None,
                error=None,
                started_at=datetime.now(timezone.utc),
                completed_at=None,
                duration=0.0
            )
            
            # Get applicable rules
            applicable_rules = await self._get_applicable_rules(
                context, decision_type, rule_ids
            )
            
            if not applicable_rules:
                raise ValueError("No applicable decision rules found")
            
            # Evaluate rules
            rule_results = []
            for rule in applicable_rules:
                rule_result = await self._evaluate_rule(rule, context)
                if rule_result["matched"]:
                    rule_results.append((rule, rule_result))
            
            # Select best rule (highest priority and confidence)
            if not rule_results:
                raise ValueError("No rules matched the input context")
            
            best_rule, best_result = self._select_best_rule(rule_results)
            
            # Create decision result
            decision_result = DecisionResult(
                decision_id=decision_id,
                rule_id=best_rule.rule_id,
                context_id=context.context_id,
                decision=best_result["decision"],
                confidence=best_result["confidence"],
                actions=best_rule.actions,
                reasoning=best_result["reasoning"],
                executed_at=datetime.now(timezone.utc)
            )
            
            # Execute actions
            await self._execute_decision_actions(decision_result.actions, context)
            
            # Update execution
            execution.decision_result = decision_result
            execution.status = DecisionStatus.COMPLETED
            execution.completed_at = datetime.now(timezone.utc)
            execution.duration = (
                execution.completed_at - execution.started_at
            ).total_seconds()
            
            # Store execution
            await self._store_decision_execution(execution)
            
            # Add to history
            self.decision_history.append(execution)
            
            # Emit event
            await self.event_bus.emit("decision_made", {
                "decision_id": decision_id,
                "rule_id": best_rule.rule_id,
                "decision": decision_result.decision,
                "confidence": decision_result.confidence,
                "context_id": context.context_id,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
            return decision_result
            
        except Exception as e:
            self.logger.error(f"Error making decision: {str(e)}")
            
            # Update execution with error
            execution.status = DecisionStatus.FAILED
            execution.error = str(e)
            execution.completed_at = datetime.now(timezone.utc)
            execution.duration = (
                execution.completed_at - execution.started_at
            ).total_seconds()
            
            # Store failed execution
            await self._store_decision_execution(execution)
            
            raise
    
    async def evaluate_conditions(
        self,
        conditions: List[DecisionCondition],
        context: DecisionContext,
        logical_operator: str = "AND"
    ) -> Dict[str, Any]:
        """Evaluate a set of conditions"""
        try:
            results = []
            
            for condition in conditions:
                condition_result = await self._evaluate_condition(condition, context)
                results.append(condition_result)
            
            # Apply logical operator
            if logical_operator == "AND":
                overall_result = all(r["matched"] for r in results)
            elif logical_operator == "OR":
                overall_result = any(r["matched"] for r in results)
            else:
                raise ValueError(f"Unsupported logical operator: {logical_operator}")
            
            # Calculate confidence
            if results:
                confidence = sum(r["confidence"] for r in results) / len(results)
            else:
                confidence = 0.0
            
            return {
                "matched": overall_result,
                "confidence": confidence,
                "condition_results": results,
                "logical_operator": logical_operator
            }
            
        except Exception as e:
            self.logger.error(f"Error evaluating conditions: {str(e)}")
            raise
    
    async def get_decision_history(
        self,
        context_id: Optional[str] = None,
        rule_id: Optional[str] = None,
        limit: int = 100
    ) -> List[DecisionExecution]:
        """Get decision history"""
        try:
            filtered_history = self.decision_history
            
            # Filter by context_id
            if context_id:
                filtered_history = [
                    exec for exec in filtered_history
                    if exec.input_context.context_id == context_id
                ]
            
            # Filter by rule_id
            if rule_id:
                filtered_history = [
                    exec for exec in filtered_history
                    if exec.decision_result and exec.decision_result.rule_id == rule_id
                ]
            
            # Apply limit
            return filtered_history[-limit:]
            
        except Exception as e:
            self.logger.error(f"Error getting decision history: {str(e)}")
            return []
    
    async def get_decision_metrics(self, rule_id: Optional[str] = None) -> Dict[str, Any]:
        """Get decision metrics"""
        try:
            filtered_executions = self.decision_history
            
            if rule_id:
                filtered_executions = [
                    exec for exec in filtered_executions
                    if exec.decision_result and exec.decision_result.rule_id == rule_id
                ]
            
            total_decisions = len(filtered_executions)
            successful_decisions = len([
                exec for exec in filtered_executions
                if exec.status == DecisionStatus.COMPLETED
            ])
            failed_decisions = len([
                exec for exec in filtered_executions
                if exec.status == DecisionStatus.FAILED
            ])
            
            # Calculate success rate
            success_rate = (successful_decisions / total_decisions * 100) if total_decisions > 0 else 0
            
            # Calculate average confidence
            confidences = [
                exec.decision_result.confidence
                for exec in filtered_executions
                if exec.decision_result
            ]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            # Calculate average duration
            durations = [exec.duration for exec in filtered_executions]
            avg_duration = sum(durations) / len(durations) if durations else 0
            
            return {
                "total_decisions": total_decisions,
                "successful_decisions": successful_decisions,
                "failed_decisions": failed_decisions,
                "success_rate": success_rate,
                "average_confidence": avg_confidence,
                "average_duration": avg_duration,
                "rule_id": rule_id,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting decision metrics: {str(e)}")
            raise
    
    async def override_decision(
        self,
        decision_id: str,
        new_decision: str,
        reason: str,
        override_by: str
    ) -> bool:
        """Override a previous decision"""
        try:
            # Find original execution
            original_execution = next(
                (exec for exec in self.decision_history if exec.decision_id == decision_id),
                None
            )
            
            if not original_execution:
                return False
            
            # Create override execution
            override_execution = DecisionExecution(
                execution_id=str(uuid.uuid4()),
                decision_id=decision_id,
                status=DecisionStatus.OVERRIDDEN,
                input_context=original_execution.input_context,
                decision_result=DecisionResult(
                    decision_id=decision_id,
                    rule_id="manual_override",
                    context_id=original_execution.input_context.context_id,
                    decision=new_decision,
                    confidence=1.0,
                    actions=[],
                    reasoning=f"Manual override: {reason}",
                    executed_at=datetime.now(timezone.utc)
                ),
                error=None,
                started_at=datetime.now(timezone.utc),
                completed_at=datetime.now(timezone.utc),
                duration=0.0
            )
            
            # Store override
            await self._store_decision_execution(override_execution)
            
            # Add to history
            self.decision_history.append(override_execution)
            
            # Emit event
            await self.event_bus.emit("decision_overridden", {
                "original_decision_id": decision_id,
                "new_decision": new_decision,
                "reason": reason,
                "override_by": override_by,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error overriding decision: {str(e)}")
            return False
    
    # Handler registration methods
    
    def register_custom_evaluator(self, evaluator_name: str, evaluator: Callable) -> None:
        """Register a custom condition evaluator"""
        self.custom_evaluators[evaluator_name] = evaluator
    
    def register_action_handler(self, action_type: str, handler: Callable) -> None:
        """Register an action handler"""
        self.action_handlers[action_type] = handler
    
    # Private helper methods
    
    async def _validate_decision_rule(self, rule: DecisionRule) -> bool:
        """Validate decision rule"""
        try:
            # Check required fields
            if not rule.rule_id or not rule.name:
                return False
            
            # Check conditions
            if not rule.conditions:
                return False
            
            # Check actions
            if not rule.actions:
                return False
            
            # Check logical operator
            if rule.logical_operator not in ["AND", "OR"]:
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating decision rule: {str(e)}")
            return False
    
    async def _get_applicable_rules(
        self,
        context: DecisionContext,
        decision_type: Optional[DecisionType] = None,
        rule_ids: Optional[List[str]] = None
    ) -> List[DecisionRule]:
        """Get applicable decision rules"""
        try:
            applicable_rules = []
            
            for rule in self.decision_rules.values():
                # Check if rule is enabled
                if not rule.enabled:
                    continue
                
                # Check validity period
                now = datetime.now(timezone.utc)
                if rule.valid_from and now < rule.valid_from:
                    continue
                if rule.valid_until and now > rule.valid_until:
                    continue
                
                # Check decision type filter
                if decision_type and rule.decision_type != decision_type:
                    continue
                
                # Check rule ID filter
                if rule_ids and rule.rule_id not in rule_ids:
                    continue
                
                applicable_rules.append(rule)
            
            # Sort by priority
            priority_order = {
                DecisionPriority.CRITICAL: 0,
                DecisionPriority.HIGH: 1,
                DecisionPriority.MEDIUM: 2,
                DecisionPriority.LOW: 3
            }
            
            applicable_rules.sort(key=lambda r: priority_order.get(r.priority, 4))
            
            return applicable_rules
            
        except Exception as e:
            self.logger.error(f"Error getting applicable rules: {str(e)}")
            return []
    
    async def _evaluate_rule(self, rule: DecisionRule, context: DecisionContext) -> Dict[str, Any]:
        """Evaluate a decision rule"""
        try:
            # Evaluate conditions
            condition_result = await self.evaluate_conditions(
                rule.conditions, context, rule.logical_operator
            )
            
            if not condition_result["matched"]:
                return {
                    "matched": False,
                    "confidence": 0.0,
                    "decision": None,
                    "reasoning": "Conditions not met"
                }
            
            # Determine decision
            decision = await self._determine_decision(rule, context, condition_result)
            
            return {
                "matched": True,
                "confidence": condition_result["confidence"],
                "decision": decision,
                "reasoning": f"Rule {rule.rule_id} matched with {condition_result['confidence']:.2f} confidence"
            }
            
        except Exception as e:
            self.logger.error(f"Error evaluating rule: {str(e)}")
            return {
                "matched": False,
                "confidence": 0.0,
                "decision": None,
                "reasoning": f"Error: {str(e)}"
            }
    
    async def _evaluate_condition(
        self,
        condition: DecisionCondition,
        context: DecisionContext
    ) -> Dict[str, Any]:
        """Evaluate a single condition"""
        try:
            # Get field value
            field_value = await self._get_field_value(condition.field_path, context)
            
            # Evaluate condition
            matched = await self._apply_operator(
                condition.operator, field_value, condition.value
            )
            
            # Calculate confidence based on match and weight
            confidence = condition.weight if matched else 0.0
            
            return {
                "condition_id": condition.condition_id,
                "matched": matched,
                "confidence": confidence,
                "field_value": field_value,
                "expected_value": condition.value,
                "operator": condition.operator
            }
            
        except Exception as e:
            self.logger.error(f"Error evaluating condition: {str(e)}")
            return {
                "condition_id": condition.condition_id,
                "matched": False,
                "confidence": 0.0,
                "error": str(e)
            }
    
    async def _get_field_value(self, field_path: str, context: DecisionContext) -> Any:
        """Get field value from context using dot notation"""
        try:
            parts = field_path.split('.')
            value = context.data
            
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
    
    async def _apply_operator(self, operator: RuleOperator, field_value: Any, expected_value: Any) -> bool:
        """Apply operator to compare values"""
        try:
            if operator in self.operators:
                return self.operators[operator](field_value, expected_value)
            
            elif operator == RuleOperator.CONTAINS:
                return expected_value in str(field_value) if field_value else False
            
            elif operator == RuleOperator.NOT_CONTAINS:
                return expected_value not in str(field_value) if field_value else True
            
            elif operator == RuleOperator.STARTS_WITH:
                return str(field_value).startswith(str(expected_value)) if field_value else False
            
            elif operator == RuleOperator.ENDS_WITH:
                return str(field_value).endswith(str(expected_value)) if field_value else False
            
            elif operator == RuleOperator.REGEX_MATCH:
                return bool(re.match(str(expected_value), str(field_value))) if field_value else False
            
            elif operator == RuleOperator.IN_LIST:
                return field_value in expected_value if isinstance(expected_value, list) else False
            
            elif operator == RuleOperator.NOT_IN_LIST:
                return field_value not in expected_value if isinstance(expected_value, list) else True
            
            else:
                raise ValueError(f"Unsupported operator: {operator}")
                
        except Exception as e:
            self.logger.error(f"Error applying operator: {str(e)}")
            return False
    
    async def _determine_decision(
        self,
        rule: DecisionRule,
        context: DecisionContext,
        condition_result: Dict[str, Any]
    ) -> str:
        """Determine decision based on rule and context"""
        try:
            # Check if rule has custom decision logic
            if rule.metadata and "decision_logic" in rule.metadata:
                decision_logic = rule.metadata["decision_logic"]
                
                # Use custom evaluator if available
                if decision_logic in self.custom_evaluators:
                    evaluator = self.custom_evaluators[decision_logic]
                    if asyncio.iscoroutinefunction(evaluator):
                        return await evaluator(rule, context, condition_result)
                    else:
                        return evaluator(rule, context, condition_result)
            
            # Default decision logic based on rule type
            if rule.decision_type == DecisionType.THRESHOLD_BASED:
                return "approve" if condition_result["confidence"] >= 0.8 else "reject"
            
            elif rule.decision_type == DecisionType.RISK_ASSESSMENT:
                if condition_result["confidence"] >= 0.9:
                    return "low_risk"
                elif condition_result["confidence"] >= 0.7:
                    return "medium_risk"
                else:
                    return "high_risk"
            
            elif rule.decision_type == DecisionType.WORKFLOW_ROUTING:
                return rule.metadata.get("target_workflow", "default") if rule.metadata else "default"
            
            else:
                return "approve"  # Default decision
                
        except Exception as e:
            self.logger.error(f"Error determining decision: {str(e)}")
            return "error"
    
    def _select_best_rule(self, rule_results: List) -> tuple:
        """Select the best rule from matching rules"""
        try:
            # Sort by priority and confidence
            priority_order = {
                DecisionPriority.CRITICAL: 0,
                DecisionPriority.HIGH: 1,
                DecisionPriority.MEDIUM: 2,
                DecisionPriority.LOW: 3
            }
            
            def sort_key(item):
                rule, result = item
                return (priority_order.get(rule.priority, 4), -result["confidence"])
            
            sorted_results = sorted(rule_results, key=sort_key)
            return sorted_results[0]
            
        except Exception as e:
            self.logger.error(f"Error selecting best rule: {str(e)}")
            return rule_results[0] if rule_results else (None, None)
    
    async def _execute_decision_actions(
        self,
        actions: List[DecisionAction],
        context: DecisionContext
    ) -> None:
        """Execute decision actions"""
        try:
            for action in actions:
                handler = self.action_handlers.get(action.action_type)
                if not handler:
                    self.logger.warning(f"Action handler not found: {action.action_type}")
                    continue
                
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(action, context)
                    else:
                        handler(action, context)
                        
                except Exception as e:
                    self.logger.error(f"Error executing action {action.action_id}: {str(e)}")
                    
        except Exception as e:
            self.logger.error(f"Error executing decision actions: {str(e)}")
    
    async def _store_decision_execution(self, execution: DecisionExecution) -> None:
        """Store decision execution"""
        try:
            # Store in database
            with get_db_session() as db:
                db_execution = DecisionExecution(
                    execution_id=execution.execution_id,
                    decision_id=execution.decision_id,
                    status=execution.status,
                    input_context=execution.input_context.to_dict(),
                    decision_result=execution.decision_result.to_dict() if execution.decision_result else None,
                    error=execution.error,
                    started_at=execution.started_at,
                    completed_at=execution.completed_at,
                    duration=execution.duration
                )
                db.add(db_execution)
                db.commit()
            
            # Cache execution
            await self.cache_service.set(
                f"decision_execution:{execution.execution_id}",
                execution.to_dict(),
                ttl=3600  # 1 hour
            )
            
        except Exception as e:
            self.logger.error(f"Error storing decision execution: {str(e)}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for decision engine"""
        try:
            return {
                "status": "healthy",
                "service": "decision_engine",
                "registered_rules": len(self.decision_rules),
                "custom_evaluators": len(self.custom_evaluators),
                "action_handlers": len(self.action_handlers),
                "decision_history_size": len(self.decision_history),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error in health check: {str(e)}")
            return {
                "status": "error",
                "service": "decision_engine",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    async def cleanup(self) -> None:
        """Cleanup decision engine resources"""
        try:
            # Clear registries
            self.decision_rules.clear()
            self.custom_evaluators.clear()
            self.action_handlers.clear()
            self.decision_history.clear()
            
            self.logger.info("Decision engine cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}")


def create_decision_engine() -> DecisionEngine:
    """Create decision engine instance"""
    return DecisionEngine()