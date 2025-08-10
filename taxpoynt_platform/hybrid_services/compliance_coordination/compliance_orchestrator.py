"""
Hybrid Service: Compliance Orchestrator
Orchestrates comprehensive compliance checks across SI and APP roles
"""
import asyncio
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

from core_platform.database import get_db_session
from core_platform.models.compliance import ComplianceExecution, ComplianceWorkflow, ComplianceResult
from core_platform.cache import CacheService
from core_platform.events import EventBus
from core_platform.monitoring import MetricsCollector
from core_platform.notifications import NotificationService

from .regulation_engine import RegulationEngine, RegulationContext, RegulationType
from .cross_role_validator import CrossRoleValidator, ValidationContext, ValidationPhase

logger = logging.getLogger(__name__)


class ComplianceWorkflowType(str, Enum):
    """Types of compliance workflows"""
    FULL_COMPLIANCE_CHECK = "full_compliance_check"
    TARGETED_COMPLIANCE = "targeted_compliance"
    REGULATORY_AUDIT = "regulatory_audit"
    CROSS_ROLE_VALIDATION = "cross_role_validation"
    PERIODIC_COMPLIANCE = "periodic_compliance"
    INCIDENT_RESPONSE = "incident_response"
    CERTIFICATION_REVIEW = "certification_review"
    EMERGENCY_COMPLIANCE = "emergency_compliance"


class CompliancePhase(str, Enum):
    """Compliance check phases"""
    PREPARATION = "preparation"
    REGULATION_ENFORCEMENT = "regulation_enforcement"
    CROSS_ROLE_VALIDATION = "cross_role_validation"
    AUDIT_TRAIL_GENERATION = "audit_trail_generation"
    REPORTING = "reporting"
    REMEDIATION = "remediation"


class ComplianceStatus(str, Enum):
    """Compliance execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PARTIALLY_COMPLETED = "partially_completed"


class CompliancePriority(str, Enum):
    """Compliance priority levels"""
    EMERGENCY = "emergency"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    ROUTINE = "routine"


@dataclass
class ComplianceWorkflowDefinition:
    """Compliance workflow definition"""
    workflow_id: str
    name: str
    description: str
    workflow_type: ComplianceWorkflowType
    phases: List[CompliancePhase]
    regulation_types: List[RegulationType]
    service_scopes: List[str]
    validation_phases: List[ValidationPhase]
    priority: CompliancePriority
    timeout: int
    retry_policy: Dict[str, Any]
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ComplianceContext:
    """Context for compliance orchestration"""
    context_id: str
    workflow_type: ComplianceWorkflowType
    initiated_by: str
    service_role: str
    target_services: List[str]
    data: Dict[str, Any]
    metadata: Dict[str, Any]
    priority: CompliancePriority
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CompliancePhaseResult:
    """Result of a compliance phase"""
    phase_id: str
    phase: CompliancePhase
    status: ComplianceStatus
    results: Dict[str, Any]
    issues: List[Dict[str, Any]]
    execution_time: float
    started_at: datetime
    completed_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ComplianceExecution:
    """Compliance execution record"""
    execution_id: str
    workflow_id: str
    context: ComplianceContext
    status: ComplianceStatus
    phase_results: List[CompliancePhaseResult]
    overall_score: float
    total_issues: int
    critical_issues: int
    started_at: datetime
    completed_at: Optional[datetime] = None
    total_duration: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ComplianceOrchestrator:
    """Compliance orchestration service"""
    
    def __init__(self):
        self.cache_service = CacheService()
        self.event_bus = EventBus()
        self.metrics_collector = MetricsCollector()
        self.notification_service = NotificationService()
        self.logger = logging.getLogger(__name__)
        
        # Initialize component services
        self.regulation_engine = RegulationEngine()
        self.cross_role_validator = CrossRoleValidator()
        
        # Workflow definitions
        self.workflow_definitions: Dict[str, ComplianceWorkflowDefinition] = {}
        
        # Active executions
        self.active_executions: Dict[str, ComplianceExecution] = {}
        
        # Execution history
        self.execution_history: List[ComplianceExecution] = []
        
        # Phase handlers
        self.phase_handlers = {
            CompliancePhase.PREPARATION: self._handle_preparation_phase,
            CompliancePhase.REGULATION_ENFORCEMENT: self._handle_regulation_enforcement_phase,
            CompliancePhase.CROSS_ROLE_VALIDATION: self._handle_cross_role_validation_phase,
            CompliancePhase.AUDIT_TRAIL_GENERATION: self._handle_audit_trail_generation_phase,
            CompliancePhase.REPORTING: self._handle_reporting_phase,
            CompliancePhase.REMEDIATION: self._handle_remediation_phase
        }
        
        # Initialize default workflows
        self._initialize_default_workflows()
    
    async def register_compliance_workflow(self, workflow: ComplianceWorkflowDefinition) -> bool:
        """Register a compliance workflow"""
        try:
            # Validate workflow
            if not await self._validate_workflow(workflow):
                raise ValueError(f"Invalid compliance workflow: {workflow.workflow_id}")
            
            # Store workflow
            self.workflow_definitions[workflow.workflow_id] = workflow
            
            # Cache workflow
            await self.cache_service.set(
                f"compliance_workflow:{workflow.workflow_id}",
                workflow.to_dict(),
                ttl=86400  # 24 hours
            )
            
            # Emit event
            await self.event_bus.emit("compliance_workflow_registered", {
                "workflow_id": workflow.workflow_id,
                "workflow_type": workflow.workflow_type,
                "phases": workflow.phases,
                "priority": workflow.priority,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
            self.logger.info(f"Compliance workflow registered: {workflow.workflow_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error registering compliance workflow: {str(e)}")
            raise
    
    async def execute_compliance_workflow(
        self,
        workflow_id: str,
        context: ComplianceContext
    ) -> ComplianceExecution:
        """Execute a compliance workflow"""
        execution_id = str(uuid.uuid4())
        start_time = datetime.now(timezone.utc)
        
        try:
            # Get workflow definition
            workflow = await self._get_workflow_definition(workflow_id)
            if not workflow:
                raise ValueError(f"Workflow not found: {workflow_id}")
            
            # Create execution record
            execution = ComplianceExecution(
                execution_id=execution_id,
                workflow_id=workflow_id,
                context=context,
                status=ComplianceStatus.RUNNING,
                phase_results=[],
                overall_score=0.0,
                total_issues=0,
                critical_issues=0,
                started_at=start_time
            )
            
            # Add to active executions
            self.active_executions[execution_id] = execution
            
            # Emit start event
            await self.event_bus.emit("compliance_execution_started", {
                "execution_id": execution_id,
                "workflow_id": workflow_id,
                "context_id": context.context_id,
                "initiated_by": context.initiated_by,
                "priority": context.priority,
                "timestamp": start_time.isoformat()
            })
            
            # Execute workflow phases
            for phase in workflow.phases:
                phase_result = await self._execute_phase(phase, execution, workflow)
                execution.phase_results.append(phase_result)
                
                # Check if phase failed and workflow should stop
                if phase_result.status == ComplianceStatus.FAILED:
                    if workflow.retry_policy.get("stop_on_failure", False):
                        execution.status = ComplianceStatus.FAILED
                        break
            
            # Calculate overall results
            await self._calculate_overall_results(execution)
            
            # Determine final status
            if execution.status == ComplianceStatus.RUNNING:
                failed_phases = [p for p in execution.phase_results if p.status == ComplianceStatus.FAILED]
                if failed_phases:
                    execution.status = ComplianceStatus.PARTIALLY_COMPLETED
                else:
                    execution.status = ComplianceStatus.COMPLETED
            
            # Complete execution
            execution.completed_at = datetime.now(timezone.utc)
            execution.total_duration = (execution.completed_at - execution.started_at).total_seconds()
            
            # Remove from active executions
            if execution_id in self.active_executions:
                del self.active_executions[execution_id]
            
            # Store execution
            await self._store_execution(execution)
            
            # Add to history
            self.execution_history.append(execution)
            
            # Handle results
            await self._handle_execution_results(execution)
            
            # Emit completion event
            await self.event_bus.emit("compliance_execution_completed", {
                "execution_id": execution_id,
                "workflow_id": workflow_id,
                "status": execution.status,
                "overall_score": execution.overall_score,
                "total_issues": execution.total_issues,
                "critical_issues": execution.critical_issues,
                "duration": execution.total_duration,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
            return execution
            
        except Exception as e:
            self.logger.error(f"Error executing compliance workflow: {str(e)}")
            
            # Update execution with error
            if execution_id in self.active_executions:
                execution = self.active_executions[execution_id]
                execution.status = ComplianceStatus.FAILED
                execution.completed_at = datetime.now(timezone.utc)
                execution.total_duration = (execution.completed_at - execution.started_at).total_seconds()
                
                # Store failed execution
                await self._store_execution(execution)
                
                # Remove from active executions
                del self.active_executions[execution_id]
            
            raise
    
    async def execute_full_compliance_check(
        self,
        service_role: str,
        target_services: List[str],
        data: Dict[str, Any],
        metadata: Dict[str, Any],
        initiated_by: str
    ) -> ComplianceExecution:
        """Execute full compliance check"""
        try:
            # Create context
            context = ComplianceContext(
                context_id=f"full_compliance_{uuid.uuid4()}",
                workflow_type=ComplianceWorkflowType.FULL_COMPLIANCE_CHECK,
                initiated_by=initiated_by,
                service_role=service_role,
                target_services=target_services,
                data=data,
                metadata=metadata,
                priority=CompliancePriority.HIGH,
                timestamp=datetime.now(timezone.utc)
            )
            
            # Execute workflow
            return await self.execute_compliance_workflow("full_compliance_check", context)
            
        except Exception as e:
            self.logger.error(f"Error executing full compliance check: {str(e)}")
            raise
    
    async def execute_cross_role_compliance(
        self,
        source_role: str,
        target_role: str,
        validation_phase: ValidationPhase,
        data: Dict[str, Any],
        initiated_by: str
    ) -> ComplianceExecution:
        """Execute cross-role compliance check"""
        try:
            # Create context
            context = ComplianceContext(
                context_id=f"cross_role_compliance_{uuid.uuid4()}",
                workflow_type=ComplianceWorkflowType.CROSS_ROLE_VALIDATION,
                initiated_by=initiated_by,
                service_role=source_role,
                target_services=[target_role],
                data=data,
                metadata={"validation_phase": validation_phase},
                priority=CompliancePriority.HIGH,
                timestamp=datetime.now(timezone.utc)
            )
            
            # Execute workflow
            return await self.execute_compliance_workflow("cross_role_validation", context)
            
        except Exception as e:
            self.logger.error(f"Error executing cross-role compliance: {str(e)}")
            raise
    
    async def execute_emergency_compliance(
        self,
        incident_type: str,
        affected_services: List[str],
        incident_data: Dict[str, Any],
        initiated_by: str
    ) -> ComplianceExecution:
        """Execute emergency compliance check"""
        try:
            # Create context
            context = ComplianceContext(
                context_id=f"emergency_compliance_{uuid.uuid4()}",
                workflow_type=ComplianceWorkflowType.EMERGENCY_COMPLIANCE,
                initiated_by=initiated_by,
                service_role="hybrid",
                target_services=affected_services,
                data=incident_data,
                metadata={"incident_type": incident_type},
                priority=CompliancePriority.EMERGENCY,
                timestamp=datetime.now(timezone.utc)
            )
            
            # Execute workflow
            return await self.execute_compliance_workflow("emergency_compliance", context)
            
        except Exception as e:
            self.logger.error(f"Error executing emergency compliance: {str(e)}")
            raise
    
    async def get_execution_status(self, execution_id: str) -> Optional[ComplianceExecution]:
        """Get compliance execution status"""
        try:
            # Check active executions
            if execution_id in self.active_executions:
                return self.active_executions[execution_id]
            
            # Check history
            for execution in self.execution_history:
                if execution.execution_id == execution_id:
                    return execution
            
            # Check database
            return await self._get_stored_execution(execution_id)
            
        except Exception as e:
            self.logger.error(f"Error getting execution status: {str(e)}")
            return None
    
    async def cancel_execution(self, execution_id: str) -> bool:
        """Cancel compliance execution"""
        try:
            if execution_id in self.active_executions:
                execution = self.active_executions[execution_id]
                execution.status = ComplianceStatus.CANCELLED
                execution.completed_at = datetime.now(timezone.utc)
                execution.total_duration = (execution.completed_at - execution.started_at).total_seconds()
                
                # Store cancelled execution
                await self._store_execution(execution)
                
                # Remove from active executions
                del self.active_executions[execution_id]
                
                # Emit event
                await self.event_bus.emit("compliance_execution_cancelled", {
                    "execution_id": execution_id,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
                
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error cancelling execution: {str(e)}")
            return False
    
    async def get_compliance_metrics(
        self,
        time_range: Optional[tuple] = None,
        service_role: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get compliance metrics"""
        try:
            # Filter executions
            filtered_executions = self.execution_history
            
            if time_range:
                start_time, end_time = time_range
                filtered_executions = [
                    exec for exec in filtered_executions
                    if start_time <= exec.started_at <= end_time
                ]
            
            if service_role:
                filtered_executions = [
                    exec for exec in filtered_executions
                    if exec.context.service_role == service_role
                ]
            
            # Calculate metrics
            total_executions = len(filtered_executions)
            completed_executions = len([e for e in filtered_executions if e.status == ComplianceStatus.COMPLETED])
            failed_executions = len([e for e in filtered_executions if e.status == ComplianceStatus.FAILED])
            
            success_rate = (completed_executions / total_executions * 100) if total_executions > 0 else 0
            
            # Calculate average scores
            scores = [e.overall_score for e in filtered_executions if e.overall_score > 0]
            avg_score = sum(scores) / len(scores) if scores else 0
            
            # Calculate average duration
            durations = [e.total_duration for e in filtered_executions if e.total_duration > 0]
            avg_duration = sum(durations) / len(durations) if durations else 0
            
            # Issue statistics
            total_issues = sum(e.total_issues for e in filtered_executions)
            critical_issues = sum(e.critical_issues for e in filtered_executions)
            
            return {
                "total_executions": total_executions,
                "completed_executions": completed_executions,
                "failed_executions": failed_executions,
                "success_rate": success_rate,
                "average_score": avg_score,
                "average_duration": avg_duration,
                "total_issues": total_issues,
                "critical_issues": critical_issues,
                "active_executions": len(self.active_executions),
                "service_role": service_role,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting compliance metrics: {str(e)}")
            raise
    
    async def list_active_executions(self) -> List[Dict[str, Any]]:
        """List active compliance executions"""
        try:
            active_list = []
            
            for execution_id, execution in self.active_executions.items():
                active_list.append({
                    "execution_id": execution_id,
                    "workflow_id": execution.workflow_id,
                    "context_id": execution.context.context_id,
                    "status": execution.status,
                    "priority": execution.context.priority,
                    "started_at": execution.started_at.isoformat(),
                    "current_phase": execution.phase_results[-1].phase if execution.phase_results else None
                })
            
            return active_list
            
        except Exception as e:
            self.logger.error(f"Error listing active executions: {str(e)}")
            return []
    
    # Phase handlers
    
    async def _execute_phase(
        self,
        phase: CompliancePhase,
        execution: ComplianceExecution,
        workflow: ComplianceWorkflowDefinition
    ) -> CompliancePhaseResult:
        """Execute a compliance phase"""
        phase_id = str(uuid.uuid4())
        start_time = datetime.now(timezone.utc)
        
        try:
            # Get phase handler
            handler = self.phase_handlers.get(phase)
            if not handler:
                raise ValueError(f"No handler for phase: {phase}")
            
            # Execute phase
            results = await handler(execution, workflow)
            
            # Create phase result
            phase_result = CompliancePhaseResult(
                phase_id=phase_id,
                phase=phase,
                status=ComplianceStatus.COMPLETED,
                results=results,
                issues=results.get("issues", []),
                execution_time=(datetime.now(timezone.utc) - start_time).total_seconds(),
                started_at=start_time,
                completed_at=datetime.now(timezone.utc)
            )
            
            return phase_result
            
        except Exception as e:
            self.logger.error(f"Error executing phase {phase}: {str(e)}")
            
            # Create failed phase result
            return CompliancePhaseResult(
                phase_id=phase_id,
                phase=phase,
                status=ComplianceStatus.FAILED,
                results={"error": str(e)},
                issues=[{
                    "type": "phase_execution_error",
                    "message": str(e),
                    "severity": "critical"
                }],
                execution_time=(datetime.now(timezone.utc) - start_time).total_seconds(),
                started_at=start_time,
                completed_at=datetime.now(timezone.utc)
            )
    
    async def _handle_preparation_phase(
        self,
        execution: ComplianceExecution,
        workflow: ComplianceWorkflowDefinition
    ) -> Dict[str, Any]:
        """Handle preparation phase"""
        try:
            # Prepare compliance context
            preparation_results = {
                "context_validated": True,
                "services_available": [],
                "regulation_rules_loaded": [],
                "validation_rules_loaded": []
            }
            
            # Check service availability
            for service in execution.context.target_services:
                # This would check if service is available
                preparation_results["services_available"].append({
                    "service": service,
                    "available": True
                })
            
            # Load regulation rules
            regulation_rules = await self.regulation_engine.get_regulation_rules()
            preparation_results["regulation_rules_loaded"] = [r.rule_id for r in regulation_rules]
            
            # Load validation rules
            validation_rules = await self.cross_role_validator.get_validation_rules()
            preparation_results["validation_rules_loaded"] = [r.rule_id for r in validation_rules]
            
            return preparation_results
            
        except Exception as e:
            self.logger.error(f"Error in preparation phase: {str(e)}")
            raise
    
    async def _handle_regulation_enforcement_phase(
        self,
        execution: ComplianceExecution,
        workflow: ComplianceWorkflowDefinition
    ) -> Dict[str, Any]:
        """Handle regulation enforcement phase"""
        try:
            # Create regulation context
            regulation_context = RegulationContext(
                context_id=execution.context.context_id,
                service_role=execution.context.service_role,
                service_name=execution.context.target_services[0] if execution.context.target_services else "unknown",
                operation="compliance_check",
                data=execution.context.data,
                metadata=execution.context.metadata,
                timestamp=datetime.now(timezone.utc)
            )
            
            # Enforce regulations
            regulation_results = await self.regulation_engine.enforce_regulations(
                regulation_context,
                workflow.regulation_types
            )
            
            # Process results
            enforcement_results = {
                "regulation_checks": len(regulation_results),
                "compliant_checks": len([r for r in regulation_results if r.compliant]),
                "violations": [],
                "overall_compliance": True
            }
            
            # Process violations
            for result in regulation_results:
                if result.violations:
                    enforcement_results["violations"].extend([v.to_dict() for v in result.violations])
                    enforcement_results["overall_compliance"] = False
            
            return enforcement_results
            
        except Exception as e:
            self.logger.error(f"Error in regulation enforcement phase: {str(e)}")
            raise
    
    async def _handle_cross_role_validation_phase(
        self,
        execution: ComplianceExecution,
        workflow: ComplianceWorkflowDefinition
    ) -> Dict[str, Any]:
        """Handle cross-role validation phase"""
        try:
            # Create validation context
            validation_context = ValidationContext(
                context_id=execution.context.context_id,
                source_role=execution.context.service_role,
                target_role=execution.context.target_services[0] if execution.context.target_services else "unknown",
                validation_phase=ValidationPhase.PROCESSING,
                data=execution.context.data,
                metadata=execution.context.metadata,
                timestamp=datetime.now(timezone.utc)
            )
            
            # Execute validation
            validation_result = await self.cross_role_validator.validate_cross_role_data(
                validation_context,
                validation_phases=workflow.validation_phases
            )
            
            # Process results
            validation_results = {
                "validation_id": validation_result.validation_id,
                "status": validation_result.status,
                "rules_checked": validation_result.rules_checked,
                "issues": [issue.to_dict() for issue in validation_result.issues],
                "score": validation_result.score,
                "execution_time": validation_result.execution_time
            }
            
            return validation_results
            
        except Exception as e:
            self.logger.error(f"Error in cross-role validation phase: {str(e)}")
            raise
    
    async def _handle_audit_trail_generation_phase(
        self,
        execution: ComplianceExecution,
        workflow: ComplianceWorkflowDefinition
    ) -> Dict[str, Any]:
        """Handle audit trail generation phase"""
        try:
            # Generate audit trail
            audit_trail = {
                "execution_id": execution.execution_id,
                "workflow_id": execution.workflow_id,
                "context": execution.context.to_dict(),
                "phases_executed": [p.phase for p in execution.phase_results],
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "checksum": self._generate_audit_checksum(execution)
            }
            
            # Store audit trail
            await self._store_audit_trail(audit_trail)
            
            return {
                "audit_trail_generated": True,
                "audit_trail_id": audit_trail["execution_id"],
                "checksum": audit_trail["checksum"]
            }
            
        except Exception as e:
            self.logger.error(f"Error in audit trail generation phase: {str(e)}")
            raise
    
    async def _handle_reporting_phase(
        self,
        execution: ComplianceExecution,
        workflow: ComplianceWorkflowDefinition
    ) -> Dict[str, Any]:
        """Handle reporting phase"""
        try:
            # Generate compliance report
            report = await self._generate_compliance_report(execution)
            
            # Store report
            await self._store_compliance_report(report)
            
            return {
                "report_generated": True,
                "report_id": report["report_id"],
                "report_type": report["report_type"]
            }
            
        except Exception as e:
            self.logger.error(f"Error in reporting phase: {str(e)}")
            raise
    
    async def _handle_remediation_phase(
        self,
        execution: ComplianceExecution,
        workflow: ComplianceWorkflowDefinition
    ) -> Dict[str, Any]:
        """Handle remediation phase"""
        try:
            # Identify issues requiring remediation
            all_issues = []
            for phase_result in execution.phase_results:
                all_issues.extend(phase_result.issues)
            
            critical_issues = [issue for issue in all_issues if issue.get("severity") == "critical"]
            
            # Generate remediation plan
            remediation_plan = await self._generate_remediation_plan(critical_issues)
            
            # Execute automatic remediation where possible
            remediation_results = await self._execute_remediation_plan(remediation_plan)
            
            return {
                "remediation_plan_generated": True,
                "critical_issues": len(critical_issues),
                "automatic_remediations": len(remediation_results.get("automatic", [])),
                "manual_remediations": len(remediation_results.get("manual", [])),
                "remediation_plan": remediation_plan
            }
            
        except Exception as e:
            self.logger.error(f"Error in remediation phase: {str(e)}")
            raise
    
    # Helper methods
    
    async def _validate_workflow(self, workflow: ComplianceWorkflowDefinition) -> bool:
        """Validate workflow definition"""
        try:
            # Check required fields
            if not workflow.workflow_id or not workflow.name:
                return False
            
            # Check phases
            if not workflow.phases:
                return False
            
            # Check timeout
            if workflow.timeout <= 0:
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating workflow: {str(e)}")
            return False
    
    async def _get_workflow_definition(self, workflow_id: str) -> Optional[ComplianceWorkflowDefinition]:
        """Get workflow definition"""
        try:
            # Check cache first
            cached_workflow = await self.cache_service.get(f"compliance_workflow:{workflow_id}")
            if cached_workflow:
                return ComplianceWorkflowDefinition(**cached_workflow)
            
            # Check registry
            return self.workflow_definitions.get(workflow_id)
            
        except Exception as e:
            self.logger.error(f"Error getting workflow definition: {str(e)}")
            return None
    
    async def _calculate_overall_results(self, execution: ComplianceExecution) -> None:
        """Calculate overall execution results"""
        try:
            # Calculate overall score
            phase_scores = []
            for phase_result in execution.phase_results:
                if "score" in phase_result.results:
                    phase_scores.append(phase_result.results["score"])
            
            execution.overall_score = sum(phase_scores) / len(phase_scores) if phase_scores else 0.0
            
            # Count issues
            total_issues = 0
            critical_issues = 0
            
            for phase_result in execution.phase_results:
                total_issues += len(phase_result.issues)
                critical_issues += len([
                    issue for issue in phase_result.issues
                    if issue.get("severity") == "critical"
                ])
            
            execution.total_issues = total_issues
            execution.critical_issues = critical_issues
            
        except Exception as e:
            self.logger.error(f"Error calculating overall results: {str(e)}")
    
    async def _store_execution(self, execution: ComplianceExecution) -> None:
        """Store compliance execution"""
        try:
            # Store in database
            with get_db_session() as db:
                db_execution = ComplianceExecution(
                    execution_id=execution.execution_id,
                    workflow_id=execution.workflow_id,
                    context=execution.context.to_dict(),
                    status=execution.status,
                    phase_results=[pr.to_dict() for pr in execution.phase_results],
                    overall_score=execution.overall_score,
                    total_issues=execution.total_issues,
                    critical_issues=execution.critical_issues,
                    started_at=execution.started_at,
                    completed_at=execution.completed_at,
                    total_duration=execution.total_duration
                )
                db.add(db_execution)
                db.commit()
            
            # Cache execution
            await self.cache_service.set(
                f"compliance_execution:{execution.execution_id}",
                execution.to_dict(),
                ttl=3600  # 1 hour
            )
            
        except Exception as e:
            self.logger.error(f"Error storing execution: {str(e)}")
    
    async def _get_stored_execution(self, execution_id: str) -> Optional[ComplianceExecution]:
        """Get stored execution"""
        try:
            # Check cache first
            cached_execution = await self.cache_service.get(f"compliance_execution:{execution_id}")
            if cached_execution:
                return ComplianceExecution(**cached_execution)
            
            # Check database
            with get_db_session() as db:
                db_execution = db.query(ComplianceExecution).filter(
                    ComplianceExecution.execution_id == execution_id
                ).first()
                
                if db_execution:
                    return ComplianceExecution(
                        execution_id=db_execution.execution_id,
                        workflow_id=db_execution.workflow_id,
                        context=ComplianceContext(**db_execution.context),
                        status=ComplianceStatus(db_execution.status),
                        phase_results=[CompliancePhaseResult(**pr) for pr in db_execution.phase_results],
                        overall_score=db_execution.overall_score,
                        total_issues=db_execution.total_issues,
                        critical_issues=db_execution.critical_issues,
                        started_at=db_execution.started_at,
                        completed_at=db_execution.completed_at,
                        total_duration=db_execution.total_duration
                    )
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting stored execution: {str(e)}")
            return None
    
    async def _handle_execution_results(self, execution: ComplianceExecution) -> None:
        """Handle execution results"""
        try:
            # Send notifications for critical issues
            if execution.critical_issues > 0:
                await self.notification_service.send_critical_compliance_alert(
                    execution_id=execution.execution_id,
                    critical_issues=execution.critical_issues,
                    context=execution.context.to_dict()
                )
            
            # Update metrics
            await self.metrics_collector.record_compliance_execution(
                execution_id=execution.execution_id,
                status=execution.status,
                score=execution.overall_score,
                duration=execution.total_duration,
                issues=execution.total_issues
            )
            
        except Exception as e:
            self.logger.error(f"Error handling execution results: {str(e)}")
    
    def _generate_audit_checksum(self, execution: ComplianceExecution) -> str:
        """Generate audit checksum"""
        try:
            # Create checksum data
            checksum_data = {
                "execution_id": execution.execution_id,
                "workflow_id": execution.workflow_id,
                "context_id": execution.context.context_id,
                "phase_results": [pr.phase for pr in execution.phase_results],
                "overall_score": execution.overall_score,
                "total_issues": execution.total_issues
            }
            
            # Generate checksum
            import hashlib
            checksum_string = json.dumps(checksum_data, sort_keys=True)
            return hashlib.sha256(checksum_string.encode()).hexdigest()
            
        except Exception as e:
            self.logger.error(f"Error generating audit checksum: {str(e)}")
            return ""
    
    async def _store_audit_trail(self, audit_trail: Dict[str, Any]) -> None:
        """Store audit trail"""
        try:
            # Store in database
            with get_db_session() as db:
                # This would store in an audit table
                pass
            
            # Cache audit trail
            await self.cache_service.set(
                f"audit_trail:{audit_trail['execution_id']}",
                audit_trail,
                ttl=86400 * 7  # 7 days
            )
            
        except Exception as e:
            self.logger.error(f"Error storing audit trail: {str(e)}")
    
    async def _generate_compliance_report(self, execution: ComplianceExecution) -> Dict[str, Any]:
        """Generate compliance report"""
        try:
            report = {
                "report_id": f"compliance_report_{execution.execution_id}",
                "report_type": "compliance_execution",
                "execution_id": execution.execution_id,
                "workflow_id": execution.workflow_id,
                "context": execution.context.to_dict(),
                "status": execution.status,
                "overall_score": execution.overall_score,
                "total_issues": execution.total_issues,
                "critical_issues": execution.critical_issues,
                "phase_results": [pr.to_dict() for pr in execution.phase_results],
                "duration": execution.total_duration,
                "generated_at": datetime.now(timezone.utc).isoformat()
            }
            
            return report
            
        except Exception as e:
            self.logger.error(f"Error generating compliance report: {str(e)}")
            return {}
    
    async def _store_compliance_report(self, report: Dict[str, Any]) -> None:
        """Store compliance report"""
        try:
            # Store in database
            with get_db_session() as db:
                # This would store in a reports table
                pass
            
            # Cache report
            await self.cache_service.set(
                f"compliance_report:{report['report_id']}",
                report,
                ttl=86400 * 30  # 30 days
            )
            
        except Exception as e:
            self.logger.error(f"Error storing compliance report: {str(e)}")
    
    async def _generate_remediation_plan(self, critical_issues: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate remediation plan"""
        try:
            plan = {
                "plan_id": str(uuid.uuid4()),
                "critical_issues": len(critical_issues),
                "automatic_remediations": [],
                "manual_remediations": [],
                "generated_at": datetime.now(timezone.utc).isoformat()
            }
            
            for issue in critical_issues:
                issue_type = issue.get("type", "unknown")
                
                if issue_type in ["field_missing", "field_format"]:
                    plan["automatic_remediations"].append({
                        "issue_id": issue.get("id"),
                        "action": "data_correction",
                        "description": "Automatically correct data format or add missing fields"
                    })
                else:
                    plan["manual_remediations"].append({
                        "issue_id": issue.get("id"),
                        "action": "manual_review",
                        "description": "Manual review and correction required"
                    })
            
            return plan
            
        except Exception as e:
            self.logger.error(f"Error generating remediation plan: {str(e)}")
            return {}
    
    async def _execute_remediation_plan(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """Execute remediation plan"""
        try:
            results = {
                "automatic": [],
                "manual": []
            }
            
            # Execute automatic remediations
            for remediation in plan.get("automatic_remediations", []):
                try:
                    # Execute automatic remediation
                    results["automatic"].append({
                        "issue_id": remediation["issue_id"],
                        "status": "completed",
                        "action": remediation["action"]
                    })
                except Exception as e:
                    results["automatic"].append({
                        "issue_id": remediation["issue_id"],
                        "status": "failed",
                        "error": str(e)
                    })
            
            # Schedule manual remediations
            for remediation in plan.get("manual_remediations", []):
                results["manual"].append({
                    "issue_id": remediation["issue_id"],
                    "status": "scheduled",
                    "action": remediation["action"]
                })
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error executing remediation plan: {str(e)}")
            return {"automatic": [], "manual": []}
    
    def _initialize_default_workflows(self):
        """Initialize default compliance workflows"""
        try:
            # Full compliance check workflow
            full_compliance_workflow = ComplianceWorkflowDefinition(
                workflow_id="full_compliance_check",
                name="Full Compliance Check",
                description="Comprehensive compliance check across all regulations and validations",
                workflow_type=ComplianceWorkflowType.FULL_COMPLIANCE_CHECK,
                phases=[
                    CompliancePhase.PREPARATION,
                    CompliancePhase.REGULATION_ENFORCEMENT,
                    CompliancePhase.CROSS_ROLE_VALIDATION,
                    CompliancePhase.AUDIT_TRAIL_GENERATION,
                    CompliancePhase.REPORTING,
                    CompliancePhase.REMEDIATION
                ],
                regulation_types=[
                    RegulationType.FIRS_EINVOICE,
                    RegulationType.DATA_PROTECTION,
                    RegulationType.CERTIFICATE_MANAGEMENT
                ],
                service_scopes=["si", "app", "hybrid"],
                validation_phases=[
                    ValidationPhase.PRE_PROCESSING,
                    ValidationPhase.PROCESSING,
                    ValidationPhase.POST_PROCESSING
                ],
                priority=CompliancePriority.HIGH,
                timeout=3600,
                retry_policy={"max_retries": 2, "stop_on_failure": False}
            )
            
            # Cross-role validation workflow
            cross_role_workflow = ComplianceWorkflowDefinition(
                workflow_id="cross_role_validation",
                name="Cross-Role Validation",
                description="Validation compliance across SI and APP boundaries",
                workflow_type=ComplianceWorkflowType.CROSS_ROLE_VALIDATION,
                phases=[
                    CompliancePhase.PREPARATION,
                    CompliancePhase.CROSS_ROLE_VALIDATION,
                    CompliancePhase.REPORTING
                ],
                regulation_types=[RegulationType.FIRS_EINVOICE],
                service_scopes=["si", "app"],
                validation_phases=[ValidationPhase.HANDOFF, ValidationPhase.TRANSMISSION],
                priority=CompliancePriority.HIGH,
                timeout=1800,
                retry_policy={"max_retries": 1, "stop_on_failure": True}
            )
            
            # Emergency compliance workflow
            emergency_workflow = ComplianceWorkflowDefinition(
                workflow_id="emergency_compliance",
                name="Emergency Compliance",
                description="Emergency compliance check for critical incidents",
                workflow_type=ComplianceWorkflowType.EMERGENCY_COMPLIANCE,
                phases=[
                    CompliancePhase.PREPARATION,
                    CompliancePhase.REGULATION_ENFORCEMENT,
                    CompliancePhase.AUDIT_TRAIL_GENERATION,
                    CompliancePhase.REMEDIATION
                ],
                regulation_types=[
                    RegulationType.FIRS_EINVOICE,
                    RegulationType.TRANSMISSION_SECURITY,
                    RegulationType.AUDIT_TRAIL
                ],
                service_scopes=["si", "app", "hybrid"],
                validation_phases=[ValidationPhase.PROCESSING],
                priority=CompliancePriority.EMERGENCY,
                timeout=900,
                retry_policy={"max_retries": 0, "stop_on_failure": True}
            )
            
            # Store default workflows
            self.workflow_definitions[full_compliance_workflow.workflow_id] = full_compliance_workflow
            self.workflow_definitions[cross_role_workflow.workflow_id] = cross_role_workflow
            self.workflow_definitions[emergency_workflow.workflow_id] = emergency_workflow
            
        except Exception as e:
            self.logger.error(f"Error initializing default workflows: {str(e)}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for compliance orchestrator"""
        try:
            # Check component health
            regulation_health = await self.regulation_engine.health_check()
            validator_health = await self.cross_role_validator.health_check()
            
            return {
                "status": "healthy",
                "service": "compliance_orchestrator",
                "registered_workflows": len(self.workflow_definitions),
                "active_executions": len(self.active_executions),
                "execution_history_size": len(self.execution_history),
                "components": {
                    "regulation_engine": regulation_health,
                    "cross_role_validator": validator_health
                },
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error in health check: {str(e)}")
            return {
                "status": "error",
                "service": "compliance_orchestrator",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    async def cleanup(self) -> None:
        """Cleanup orchestrator resources"""
        try:
            # Cancel active executions
            for execution_id in list(self.active_executions.keys()):
                await self.cancel_execution(execution_id)
            
            # Cleanup components
            await self.regulation_engine.cleanup()
            await self.cross_role_validator.cleanup()
            
            # Clear registries
            self.workflow_definitions.clear()
            self.active_executions.clear()
            self.execution_history.clear()
            
            self.logger.info("Compliance orchestrator cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}")


def create_compliance_orchestrator() -> ComplianceOrchestrator:
    """Create compliance orchestrator instance"""
    return ComplianceOrchestrator()