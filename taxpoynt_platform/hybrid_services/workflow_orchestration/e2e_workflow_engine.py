"""
Hybrid Service: End-to-End Workflow Engine
Orchestrates SI → APP workflows and cross-role processes
"""
import asyncio
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List, Union, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

from core_platform.database import get_db_session
from core_platform.models.workflow import WorkflowExecution, WorkflowStep, WorkflowState
from core_platform.cache import CacheService
from core_platform.events import EventBus
from core_platform.monitoring import MetricsCollector
from core_platform.notifications import NotificationService

logger = logging.getLogger(__name__)


class WorkflowType(str, Enum):
    """Workflow types"""
    INVOICE_PROCESSING = "invoice_processing"
    TAXPAYER_ONBOARDING = "taxpayer_onboarding"
    COMPLIANCE_CHECK = "compliance_check"
    CERTIFICATE_RENEWAL = "certificate_renewal"
    DATA_SYNCHRONIZATION = "data_synchronization"
    ERROR_RECOVERY = "error_recovery"
    AUDIT_TRAIL = "audit_trail"
    SYSTEM_INTEGRATION = "system_integration"


class WorkflowStatus(str, Enum):
    """Workflow execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"
    RETRYING = "retrying"


class StepType(str, Enum):
    """Workflow step types"""
    SI_PROCESSING = "si_processing"
    APP_TRANSMISSION = "app_transmission"
    VALIDATION = "validation"
    TRANSFORMATION = "transformation"
    NOTIFICATION = "notification"
    DECISION = "decision"
    PARALLEL = "parallel"
    SEQUENTIAL = "sequential"
    RETRY = "retry"
    ROLLBACK = "rollback"


@dataclass
class WorkflowContext:
    """Workflow execution context"""
    workflow_id: str
    execution_id: str
    workflow_type: WorkflowType
    initiator: str
    tenant_id: str
    metadata: Dict[str, Any]
    variables: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class WorkflowStep:
    """Workflow step definition"""
    step_id: str
    name: str
    step_type: StepType
    service_role: str  # 'si', 'app', 'core', 'hybrid'
    service_name: str
    method_name: str
    parameters: Dict[str, Any]
    dependencies: List[str]
    timeout: int
    retry_count: int
    retry_delay: int
    rollback_method: Optional[str] = None
    condition: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class WorkflowDefinition:
    """Workflow definition"""
    workflow_id: str
    name: str
    description: str
    workflow_type: WorkflowType
    version: str
    steps: List[WorkflowStep]
    triggers: List[str]
    timeout: int
    retry_policy: Dict[str, Any]
    rollback_policy: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class StepExecution:
    """Step execution result"""
    step_id: str
    status: WorkflowStatus
    started_at: datetime
    completed_at: Optional[datetime]
    result: Optional[Dict[str, Any]]
    error: Optional[str]
    retry_count: int
    duration: float
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class WorkflowExecution:
    """Workflow execution result"""
    execution_id: str
    workflow_id: str
    status: WorkflowStatus
    context: WorkflowContext
    steps: List[StepExecution]
    started_at: datetime
    completed_at: Optional[datetime]
    total_duration: float
    error: Optional[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class E2EWorkflowEngine:
    """End-to-end workflow orchestration engine"""
    
    def __init__(self):
        self.cache_service = CacheService()
        self.event_bus = EventBus()
        self.metrics_collector = MetricsCollector()
        self.notification_service = NotificationService()
        self.logger = logging.getLogger(__name__)
        
        # Workflow definitions registry
        self.workflow_definitions: Dict[str, WorkflowDefinition] = {}
        
        # Service registry for dynamic service lookup
        self.service_registry: Dict[str, Dict[str, Any]] = {}
        
        # Running executions
        self.running_executions: Dict[str, WorkflowExecution] = {}
        
    async def register_workflow(self, definition: WorkflowDefinition) -> bool:
        """Register a workflow definition"""
        try:
            # Validate workflow definition
            if not await self._validate_workflow_definition(definition):
                raise ValueError(f"Invalid workflow definition: {definition.workflow_id}")
            
            # Store in registry
            self.workflow_definitions[definition.workflow_id] = definition
            
            # Cache definition
            await self.cache_service.set(
                f"workflow_definition:{definition.workflow_id}",
                definition.to_dict(),
                ttl=86400  # 24 hours
            )
            
            # Emit event
            await self.event_bus.emit("workflow_registered", {
                "workflow_id": definition.workflow_id,
                "workflow_type": definition.workflow_type,
                "version": definition.version,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
            self.logger.info(f"Workflow registered: {definition.workflow_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error registering workflow: {str(e)}")
            raise
    
    async def execute_workflow(
        self,
        workflow_id: str,
        context: WorkflowContext,
        parameters: Optional[Dict[str, Any]] = None
    ) -> WorkflowExecution:
        """Execute a workflow"""
        execution_id = str(uuid.uuid4())
        
        try:
            # Get workflow definition
            definition = await self._get_workflow_definition(workflow_id)
            if not definition:
                raise ValueError(f"Workflow not found: {workflow_id}")
            
            # Create execution context
            execution = WorkflowExecution(
                execution_id=execution_id,
                workflow_id=workflow_id,
                status=WorkflowStatus.RUNNING,
                context=context,
                steps=[],
                started_at=datetime.now(timezone.utc),
                completed_at=None,
                total_duration=0.0,
                error=None
            )
            
            # Add to running executions
            self.running_executions[execution_id] = execution
            
            # Update context with parameters
            if parameters:
                context.variables.update(parameters)
            
            # Emit start event
            await self.event_bus.emit("workflow_execution_started", {
                "execution_id": execution_id,
                "workflow_id": workflow_id,
                "context": context.to_dict(),
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
            # Execute workflow steps
            execution = await self._execute_workflow_steps(execution, definition)
            
            # Calculate total duration
            if execution.completed_at:
                execution.total_duration = (
                    execution.completed_at - execution.started_at
                ).total_seconds()
            
            # Remove from running executions
            if execution_id in self.running_executions:
                del self.running_executions[execution_id]
            
            # Store execution result
            await self._store_execution_result(execution)
            
            # Emit completion event
            await self.event_bus.emit("workflow_execution_completed", {
                "execution_id": execution_id,
                "workflow_id": workflow_id,
                "status": execution.status,
                "duration": execution.total_duration,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
            return execution
            
        except Exception as e:
            self.logger.error(f"Error executing workflow: {str(e)}")
            
            # Update execution with error
            if execution_id in self.running_executions:
                execution = self.running_executions[execution_id]
                execution.status = WorkflowStatus.FAILED
                execution.error = str(e)
                execution.completed_at = datetime.now(timezone.utc)
                
                # Store failed execution
                await self._store_execution_result(execution)
                
                # Remove from running executions
                del self.running_executions[execution_id]
            
            raise
    
    async def cancel_workflow(self, execution_id: str) -> bool:
        """Cancel a running workflow"""
        try:
            if execution_id not in self.running_executions:
                return False
            
            execution = self.running_executions[execution_id]
            execution.status = WorkflowStatus.CANCELLED
            execution.completed_at = datetime.now(timezone.utc)
            
            # Store cancelled execution
            await self._store_execution_result(execution)
            
            # Remove from running executions
            del self.running_executions[execution_id]
            
            # Emit cancellation event
            await self.event_bus.emit("workflow_execution_cancelled", {
                "execution_id": execution_id,
                "workflow_id": execution.workflow_id,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error cancelling workflow: {str(e)}")
            raise
    
    async def pause_workflow(self, execution_id: str) -> bool:
        """Pause a running workflow"""
        try:
            if execution_id not in self.running_executions:
                return False
            
            execution = self.running_executions[execution_id]
            execution.status = WorkflowStatus.PAUSED
            
            # Emit pause event
            await self.event_bus.emit("workflow_execution_paused", {
                "execution_id": execution_id,
                "workflow_id": execution.workflow_id,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error pausing workflow: {str(e)}")
            raise
    
    async def resume_workflow(self, execution_id: str) -> bool:
        """Resume a paused workflow"""
        try:
            if execution_id not in self.running_executions:
                return False
            
            execution = self.running_executions[execution_id]
            if execution.status != WorkflowStatus.PAUSED:
                return False
            
            execution.status = WorkflowStatus.RUNNING
            
            # Emit resume event
            await self.event_bus.emit("workflow_execution_resumed", {
                "execution_id": execution_id,
                "workflow_id": execution.workflow_id,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error resuming workflow: {str(e)}")
            raise
    
    async def get_execution_status(self, execution_id: str) -> Optional[WorkflowExecution]:
        """Get workflow execution status"""
        try:
            # Check running executions first
            if execution_id in self.running_executions:
                return self.running_executions[execution_id]
            
            # Check stored executions
            return await self._get_stored_execution(execution_id)
            
        except Exception as e:
            self.logger.error(f"Error getting execution status: {str(e)}")
            raise
    
    async def get_workflow_metrics(self, workflow_id: str) -> Dict[str, Any]:
        """Get workflow execution metrics"""
        try:
            with get_db_session() as db:
                # Get execution statistics
                total_executions = db.query(WorkflowExecution).filter(
                    WorkflowExecution.workflow_id == workflow_id
                ).count()
                
                successful_executions = db.query(WorkflowExecution).filter(
                    WorkflowExecution.workflow_id == workflow_id,
                    WorkflowExecution.status == WorkflowStatus.COMPLETED
                ).count()
                
                failed_executions = db.query(WorkflowExecution).filter(
                    WorkflowExecution.workflow_id == workflow_id,
                    WorkflowExecution.status == WorkflowStatus.FAILED
                ).count()
                
                # Calculate success rate
                success_rate = (successful_executions / total_executions * 100) if total_executions > 0 else 0
                
                # Get average duration
                avg_duration = await self._calculate_average_duration(db, workflow_id)
                
                # Get recent executions
                recent_executions = await self._get_recent_executions(db, workflow_id, limit=10)
                
                return {
                    "workflow_id": workflow_id,
                    "total_executions": total_executions,
                    "successful_executions": successful_executions,
                    "failed_executions": failed_executions,
                    "success_rate": success_rate,
                    "average_duration": avg_duration,
                    "recent_executions": recent_executions,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                
        except Exception as e:
            self.logger.error(f"Error getting workflow metrics: {str(e)}")
            raise
    
    async def list_running_workflows(self) -> List[Dict[str, Any]]:
        """List all running workflows"""
        try:
            running_workflows = []
            
            for execution_id, execution in self.running_executions.items():
                running_workflows.append({
                    "execution_id": execution_id,
                    "workflow_id": execution.workflow_id,
                    "status": execution.status,
                    "started_at": execution.started_at.isoformat(),
                    "context": execution.context.to_dict()
                })
            
            return running_workflows
            
        except Exception as e:
            self.logger.error(f"Error listing running workflows: {str(e)}")
            raise
    
    # Private helper methods
    
    async def _validate_workflow_definition(self, definition: WorkflowDefinition) -> bool:
        """Validate workflow definition"""
        try:
            # Check required fields
            if not definition.workflow_id or not definition.name:
                return False
            
            # Check steps
            if not definition.steps:
                return False
            
            # Validate step dependencies
            step_ids = {step.step_id for step in definition.steps}
            for step in definition.steps:
                for dep in step.dependencies:
                    if dep not in step_ids:
                        return False
            
            # Check for circular dependencies
            if self._has_circular_dependencies(definition.steps):
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating workflow definition: {str(e)}")
            return False
    
    def _has_circular_dependencies(self, steps: List[WorkflowStep]) -> bool:
        """Check for circular dependencies in workflow steps"""
        visited = set()
        rec_stack = set()
        
        def visit(step_id: str, step_deps: Dict[str, List[str]]) -> bool:
            if step_id in rec_stack:
                return True
            if step_id in visited:
                return False
            
            visited.add(step_id)
            rec_stack.add(step_id)
            
            for dep in step_deps.get(step_id, []):
                if visit(dep, step_deps):
                    return True
            
            rec_stack.remove(step_id)
            return False
        
        # Build dependency map
        step_deps = {step.step_id: step.dependencies for step in steps}
        
        # Check each step
        for step in steps:
            if step.step_id not in visited:
                if visit(step.step_id, step_deps):
                    return True
        
        return False
    
    async def _get_workflow_definition(self, workflow_id: str) -> Optional[WorkflowDefinition]:
        """Get workflow definition"""
        try:
            # Check cache first
            cached_def = await self.cache_service.get(f"workflow_definition:{workflow_id}")
            if cached_def:
                return WorkflowDefinition(**cached_def)
            
            # Check registry
            if workflow_id in self.workflow_definitions:
                return self.workflow_definitions[workflow_id]
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting workflow definition: {str(e)}")
            return None
    
    async def _execute_workflow_steps(
        self,
        execution: WorkflowExecution,
        definition: WorkflowDefinition
    ) -> WorkflowExecution:
        """Execute workflow steps"""
        try:
            # Build step execution plan
            execution_plan = self._build_execution_plan(definition.steps)
            
            # Execute steps according to plan
            for step_batch in execution_plan:
                if execution.status == WorkflowStatus.PAUSED:
                    # Wait for resume
                    while execution.status == WorkflowStatus.PAUSED:
                        await asyncio.sleep(1)
                
                if execution.status == WorkflowStatus.CANCELLED:
                    break
                
                # Execute steps in parallel within batch
                batch_tasks = []
                for step in step_batch:
                    task = asyncio.create_task(
                        self._execute_step(execution, step)
                    )
                    batch_tasks.append(task)
                
                # Wait for batch completion
                batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
                
                # Check for failures
                for i, result in enumerate(batch_results):
                    if isinstance(result, Exception):
                        execution.status = WorkflowStatus.FAILED
                        execution.error = str(result)
                        execution.completed_at = datetime.now(timezone.utc)
                        return execution
                    
                    execution.steps.append(result)
            
            # Mark as completed if successful
            if execution.status == WorkflowStatus.RUNNING:
                execution.status = WorkflowStatus.COMPLETED
                execution.completed_at = datetime.now(timezone.utc)
            
            return execution
            
        except Exception as e:
            self.logger.error(f"Error executing workflow steps: {str(e)}")
            execution.status = WorkflowStatus.FAILED
            execution.error = str(e)
            execution.completed_at = datetime.now(timezone.utc)
            return execution
    
    def _build_execution_plan(self, steps: List[WorkflowStep]) -> List[List[WorkflowStep]]:
        """Build step execution plan considering dependencies"""
        plan = []
        remaining_steps = steps.copy()
        executed_steps = set()
        
        while remaining_steps:
            # Find steps that can be executed (all dependencies met)
            ready_steps = []
            for step in remaining_steps:
                if all(dep in executed_steps for dep in step.dependencies):
                    ready_steps.append(step)
            
            if not ready_steps:
                raise ValueError("Circular dependency detected in workflow steps")
            
            # Add ready steps to plan
            plan.append(ready_steps)
            
            # Mark steps as executed
            for step in ready_steps:
                executed_steps.add(step.step_id)
                remaining_steps.remove(step)
        
        return plan
    
    async def _execute_step(
        self,
        execution: WorkflowExecution,
        step: WorkflowStep
    ) -> StepExecution:
        """Execute a single workflow step"""
        step_execution = StepExecution(
            step_id=step.step_id,
            status=WorkflowStatus.RUNNING,
            started_at=datetime.now(timezone.utc),
            completed_at=None,
            result=None,
            error=None,
            retry_count=0,
            duration=0.0
        )
        
        try:
            # Check condition if specified
            if step.condition and not await self._evaluate_condition(step.condition, execution.context):
                step_execution.status = WorkflowStatus.COMPLETED
                step_execution.completed_at = datetime.now(timezone.utc)
                step_execution.result = {"skipped": True, "reason": "condition_not_met"}
                return step_execution
            
            # Execute step with retry logic
            for attempt in range(step.retry_count + 1):
                try:
                    step_execution.retry_count = attempt
                    
                    # Execute step
                    result = await self._call_service_method(
                        step.service_role,
                        step.service_name,
                        step.method_name,
                        step.parameters,
                        execution.context
                    )
                    
                    # Success
                    step_execution.status = WorkflowStatus.COMPLETED
                    step_execution.result = result
                    step_execution.completed_at = datetime.now(timezone.utc)
                    step_execution.duration = (
                        step_execution.completed_at - step_execution.started_at
                    ).total_seconds()
                    
                    return step_execution
                    
                except Exception as e:
                    self.logger.warning(f"Step {step.step_id} attempt {attempt + 1} failed: {str(e)}")
                    
                    if attempt < step.retry_count:
                        # Wait before retry
                        await asyncio.sleep(step.retry_delay)
                    else:
                        # Final failure
                        step_execution.status = WorkflowStatus.FAILED
                        step_execution.error = str(e)
                        step_execution.completed_at = datetime.now(timezone.utc)
                        step_execution.duration = (
                            step_execution.completed_at - step_execution.started_at
                        ).total_seconds()
                        
                        return step_execution
            
        except Exception as e:
            self.logger.error(f"Error executing step {step.step_id}: {str(e)}")
            step_execution.status = WorkflowStatus.FAILED
            step_execution.error = str(e)
            step_execution.completed_at = datetime.now(timezone.utc)
            step_execution.duration = (
                step_execution.completed_at - step_execution.started_at
            ).total_seconds()
            
            return step_execution
    
    async def _call_service_method(
        self,
        service_role: str,
        service_name: str,
        method_name: str,
        parameters: Dict[str, Any],
        context: WorkflowContext
    ) -> Dict[str, Any]:
        """Call service method dynamically"""
        try:
            # Get service instance
            service = await self._get_service_instance(service_role, service_name)
            
            # Get method
            method = getattr(service, method_name)
            
            # Prepare parameters with context
            call_params = parameters.copy()
            call_params['context'] = context
            
            # Call method
            if asyncio.iscoroutinefunction(method):
                result = await method(**call_params)
            else:
                result = method(**call_params)
            
            return {"success": True, "result": result}
            
        except Exception as e:
            self.logger.error(f"Error calling service method: {str(e)}")
            raise
    
    async def _get_service_instance(self, service_role: str, service_name: str) -> Any:
        """Get service instance from registry"""
        try:
            # This would integrate with the actual service registry
            # For now, return a mock service
            return MockService()
            
        except Exception as e:
            self.logger.error(f"Error getting service instance: {str(e)}")
            raise
    
    async def _evaluate_condition(self, condition: str, context: WorkflowContext) -> bool:
        """Evaluate step condition"""
        try:
            # Simple condition evaluation
            # In production, this would use a more robust expression evaluator
            return eval(condition, {"context": context})
            
        except Exception as e:
            self.logger.error(f"Error evaluating condition: {str(e)}")
            return False
    
    async def _store_execution_result(self, execution: WorkflowExecution) -> None:
        """Store workflow execution result"""
        try:
            # Store in database
            with get_db_session() as db:
                db_execution = WorkflowExecution(
                    execution_id=execution.execution_id,
                    workflow_id=execution.workflow_id,
                    status=execution.status,
                    context=execution.context.to_dict(),
                    steps=[step.to_dict() for step in execution.steps],
                    started_at=execution.started_at,
                    completed_at=execution.completed_at,
                    total_duration=execution.total_duration,
                    error=execution.error
                )
                db.add(db_execution)
                db.commit()
            
            # Cache recent result
            await self.cache_service.set(
                f"workflow_execution:{execution.execution_id}",
                execution.to_dict(),
                ttl=86400  # 24 hours
            )
            
        except Exception as e:
            self.logger.error(f"Error storing execution result: {str(e)}")
            raise
    
    async def _get_stored_execution(self, execution_id: str) -> Optional[WorkflowExecution]:
        """Get stored workflow execution"""
        try:
            # Check cache first
            cached_execution = await self.cache_service.get(f"workflow_execution:{execution_id}")
            if cached_execution:
                return WorkflowExecution(**cached_execution)
            
            # Check database
            with get_db_session() as db:
                db_execution = db.query(WorkflowExecution).filter(
                    WorkflowExecution.execution_id == execution_id
                ).first()
                
                if db_execution:
                    return WorkflowExecution(
                        execution_id=db_execution.execution_id,
                        workflow_id=db_execution.workflow_id,
                        status=WorkflowStatus(db_execution.status),
                        context=WorkflowContext(**db_execution.context),
                        steps=[StepExecution(**step) for step in db_execution.steps],
                        started_at=db_execution.started_at,
                        completed_at=db_execution.completed_at,
                        total_duration=db_execution.total_duration,
                        error=db_execution.error
                    )
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting stored execution: {str(e)}")
            return None
    
    async def _calculate_average_duration(self, db, workflow_id: str) -> float:
        """Calculate average workflow duration"""
        try:
            from sqlalchemy import func
            
            result = db.query(func.avg(WorkflowExecution.total_duration)).filter(
                WorkflowExecution.workflow_id == workflow_id,
                WorkflowExecution.status == WorkflowStatus.COMPLETED
            ).scalar()
            
            return result or 0.0
            
        except Exception as e:
            self.logger.error(f"Error calculating average duration: {str(e)}")
            return 0.0
    
    async def _get_recent_executions(self, db, workflow_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent workflow executions"""
        try:
            executions = db.query(WorkflowExecution).filter(
                WorkflowExecution.workflow_id == workflow_id
            ).order_by(WorkflowExecution.started_at.desc()).limit(limit).all()
            
            return [
                {
                    "execution_id": exec.execution_id,
                    "status": exec.status,
                    "started_at": exec.started_at.isoformat(),
                    "completed_at": exec.completed_at.isoformat() if exec.completed_at else None,
                    "duration": exec.total_duration
                }
                for exec in executions
            ]
            
        except Exception as e:
            self.logger.error(f"Error getting recent executions: {str(e)}")
            return []
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for workflow engine"""
        try:
            return {
                "status": "healthy",
                "service": "e2e_workflow_engine",
                "registered_workflows": len(self.workflow_definitions),
                "running_executions": len(self.running_executions),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error in health check: {str(e)}")
            return {
                "status": "error",
                "service": "e2e_workflow_engine",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    async def cleanup(self) -> None:
        """Cleanup workflow engine resources"""
        try:
            # Cancel all running executions
            for execution_id in list(self.running_executions.keys()):
                await self.cancel_workflow(execution_id)
            
            # Clear registries
            self.workflow_definitions.clear()
            self.service_registry.clear()
            self.running_executions.clear()
            
            self.logger.info("Workflow engine cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}")


class MockService:
    """Mock service for testing"""
    
    async def process_data(self, data: Any, context: WorkflowContext) -> Dict[str, Any]:
        """Mock data processing"""
        return {"processed": True, "data": data}
    
    async def validate_input(self, input_data: Any, context: WorkflowContext) -> Dict[str, Any]:
        """Mock input validation"""
        return {"valid": True, "input": input_data}
    
    async def send_notification(self, message: str, context: WorkflowContext) -> Dict[str, Any]:
        """Mock notification sending"""
        return {"sent": True, "message": message}


def create_workflow_engine() -> E2EWorkflowEngine:
    """Create workflow engine instance"""
    return E2EWorkflowEngine()