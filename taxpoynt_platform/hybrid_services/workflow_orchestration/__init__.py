"""
TaxPoynt Platform - Hybrid Services: Workflow Orchestration
End-to-end workflow orchestration for cross-role processes
"""

from .e2e_workflow_engine import (
    E2EWorkflowEngine,
    WorkflowType,
    WorkflowStatus,
    StepType,
    WorkflowContext,
    WorkflowStep,
    WorkflowDefinition,
    StepExecution,
    WorkflowExecution,
    create_workflow_engine
)

from .process_coordinator import (
    ProcessCoordinator,
    ProcessType,
    CoordinationStatus,
    ServiceRole,
    ProcessCoordinationRequest,
    ProcessCoordinationResponse,
    HandoffContext,
    FeedbackContext,
    ValidationContext,
    create_process_coordinator
)

from .state_machine import (
    WorkflowStateMachine,
    StateType,
    TransitionType,
    TransitionCondition,
    State,
    Transition,
    StateMachineDefinition,
    StateMachineInstance,
    StateTransitionEvent,
    create_state_machine
)

from .decision_engine import (
    DecisionEngine,
    DecisionType,
    RuleOperator,
    DecisionPriority,
    DecisionStatus,
    DecisionCondition,
    DecisionAction,
    DecisionRule,
    DecisionContext,
    DecisionResult,
    DecisionExecution,
    create_decision_engine
)

from .workflow_monitor import (
    WorkflowMonitor,
    AlertType,
    AlertSeverity,
    MonitoringStatus,
    WorkflowMetrics,
    SystemMetrics,
    WorkflowAlert,
    MonitoringRule,
    create_workflow_monitor
)

__version__ = "1.0.0"

__all__ = [
    # E2E Workflow Engine
    "E2EWorkflowEngine",
    "WorkflowType",
    "WorkflowStatus",
    "StepType",
    "WorkflowContext",
    "WorkflowStep",
    "WorkflowDefinition",
    "StepExecution",
    "WorkflowExecution",
    "create_workflow_engine",
    
    # Process Coordinator
    "ProcessCoordinator",
    "ProcessType",
    "CoordinationStatus",
    "ServiceRole",
    "ProcessCoordinationRequest",
    "ProcessCoordinationResponse",
    "HandoffContext",
    "FeedbackContext",
    "ValidationContext",
    "create_process_coordinator",
    
    # State Machine
    "WorkflowStateMachine",
    "StateType",
    "TransitionType",
    "TransitionCondition",
    "State",
    "Transition",
    "StateMachineDefinition",
    "StateMachineInstance",
    "StateTransitionEvent",
    "create_state_machine",
    
    # Decision Engine
    "DecisionEngine",
    "DecisionType",
    "RuleOperator",
    "DecisionPriority",
    "DecisionStatus",
    "DecisionCondition",
    "DecisionAction",
    "DecisionRule",
    "DecisionContext",
    "DecisionResult",
    "DecisionExecution",
    "create_decision_engine",
    
    # Workflow Monitor
    "WorkflowMonitor",
    "AlertType",
    "AlertSeverity",
    "MonitoringStatus",
    "WorkflowMetrics",
    "SystemMetrics",
    "WorkflowAlert",
    "MonitoringRule",
    "create_workflow_monitor"
]


class WorkflowOrchestrationService:
    """
    Comprehensive workflow orchestration service
    Coordinates end-to-end workflows across SI and APP roles
    """
    
    def __init__(self):
        """Initialize workflow orchestration service"""
        self.workflow_engine = create_workflow_engine()
        self.process_coordinator = create_process_coordinator()
        self.state_machine = create_state_machine()
        self.decision_engine = create_decision_engine()
        self.workflow_monitor = create_workflow_monitor()
        self.logger = __import__('logging').getLogger(__name__)
        
        # Service state
        self.is_initialized = False
        self.is_monitoring = False
    
    async def initialize(self):
        """Initialize the workflow orchestration service"""
        if self.is_initialized:
            return
        
        self.logger.info("Initializing workflow orchestration service")
        
        try:
            # Initialize monitoring
            await self.workflow_monitor.start_monitoring()
            self.is_monitoring = True
            
            # Register default workflows and state machines
            await self._register_default_workflows()
            await self._register_default_state_machines()
            await self._register_default_decision_rules()
            
            self.is_initialized = True
            self.logger.info("Workflow orchestration service initialized")
            
        except Exception as e:
            self.logger.error(f"Error initializing workflow orchestration service: {str(e)}")
            raise
    
    async def orchestrate_si_to_app_workflow(
        self,
        si_data: dict,
        validation_results: dict,
        certificates: list,
        metadata: dict
    ) -> dict:
        """
        Orchestrate SI to APP workflow
        
        Args:
            si_data: Data from SI processing
            validation_results: Validation results
            certificates: Digital certificates
            metadata: Process metadata
            
        Returns:
            Orchestration result
        """
        try:
            # Create workflow context
            context = WorkflowContext(
                workflow_id=f"si_to_app_{__import__('uuid').uuid4()}",
                execution_id=f"exec_{__import__('uuid').uuid4()}",
                workflow_type=WorkflowType.INVOICE_PROCESSING,
                initiator="si_service",
                tenant_id=metadata.get("tenant_id", "default"),
                metadata=metadata,
                variables={
                    "si_data": si_data,
                    "validation_results": validation_results,
                    "certificates": certificates
                },
                created_at=__import__('datetime').datetime.now(__import__('datetime').timezone.utc),
                updated_at=__import__('datetime').datetime.now(__import__('datetime').timezone.utc)
            )
            
            # Execute workflow
            execution = await self.workflow_engine.execute_workflow(
                workflow_id="si_to_app_processing",
                context=context
            )
            
            # Coordinate handoff
            handoff_context = await self.process_coordinator.initiate_si_to_app_handoff(
                si_process_id=context.execution_id,
                data_package=si_data,
                validation_results=validation_results,
                certificates=certificates,
                metadata=metadata
            )
            
            return {
                "workflow_execution": execution.to_dict(),
                "handoff_context": handoff_context.to_dict(),
                "status": "orchestrated",
                "timestamp": __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error orchestrating SI to APP workflow: {str(e)}")
            raise
    
    async def process_app_to_si_feedback(
        self,
        original_handoff_id: str,
        transmission_status: str,
        firs_response: dict,
        error_details: dict = None
    ) -> dict:
        """
        Process APP to SI feedback
        
        Args:
            original_handoff_id: Original handoff ID
            transmission_status: Transmission status
            firs_response: FIRS response
            error_details: Error details if any
            
        Returns:
            Feedback processing result
        """
        try:
            # Submit feedback
            feedback_context = await self.process_coordinator.submit_app_to_si_feedback(
                original_handoff_id=original_handoff_id,
                transmission_status=transmission_status,
                firs_response=firs_response,
                error_details=error_details
            )
            
            # Make decision on next steps
            decision_context = DecisionContext(
                context_id=f"feedback_{__import__('uuid').uuid4()}",
                source="app_feedback",
                data={
                    "transmission_status": transmission_status,
                    "firs_response": firs_response,
                    "error_details": error_details
                },
                metadata={"handoff_id": original_handoff_id},
                timestamp=__import__('datetime').datetime.now(__import__('datetime').timezone.utc)
            )
            
            decision_result = await self.decision_engine.make_decision(
                context=decision_context,
                decision_type=DecisionType.WORKFLOW_ROUTING
            )
            
            return {
                "feedback_context": feedback_context.to_dict(),
                "decision_result": decision_result.to_dict(),
                "status": "processed",
                "timestamp": __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error processing APP to SI feedback: {str(e)}")
            raise
    
    async def coordinate_cross_role_validation(
        self,
        validation_type: str,
        data_source: str,
        data: dict,
        validation_rules: list
    ) -> dict:
        """
        Coordinate cross-role validation
        
        Args:
            validation_type: Type of validation
            data_source: Source of data
            data: Data to validate
            validation_rules: Validation rules
            
        Returns:
            Validation result
        """
        try:
            # Map data source to service role
            service_role_map = {
                "si": ServiceRole.SI,
                "app": ServiceRole.APP,
                "core": ServiceRole.CORE,
                "hybrid": ServiceRole.HYBRID
            }
            
            source_role = service_role_map.get(data_source, ServiceRole.HYBRID)
            
            # Coordinate validation
            validation_context = await self.process_coordinator.coordinate_cross_role_validation(
                validation_type=validation_type,
                data_source=source_role,
                validation_rules=validation_rules,
                data=data
            )
            
            return {
                "validation_context": validation_context.to_dict(),
                "status": "validated",
                "timestamp": __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error coordinating cross-role validation: {str(e)}")
            raise
    
    async def get_workflow_status(self, execution_id: str) -> dict:
        """Get workflow execution status"""
        try:
            execution = await self.workflow_engine.get_execution_status(execution_id)
            
            if execution:
                return {
                    "execution": execution.to_dict(),
                    "found": True,
                    "timestamp": __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat()
                }
            else:
                return {
                    "execution": None,
                    "found": False,
                    "timestamp": __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat()
                }
                
        except Exception as e:
            self.logger.error(f"Error getting workflow status: {str(e)}")
            raise
    
    async def get_orchestration_metrics(self) -> dict:
        """Get orchestration metrics"""
        try:
            # Get system metrics
            system_metrics = await self.workflow_monitor.get_system_metrics()
            
            # Get workflow metrics
            workflow_metrics = await self.workflow_engine.get_workflow_metrics("si_to_app_processing")
            
            # Get active coordinations
            active_coordinations = await self.process_coordinator.list_active_coordinations()
            
            # Get active state machines
            active_state_machines = await self.state_machine.list_active_instances()
            
            # Get decision metrics
            decision_metrics = await self.decision_engine.get_decision_metrics()
            
            # Get active alerts
            active_alerts = await self.workflow_monitor.get_active_alerts()
            
            return {
                "system_metrics": system_metrics.to_dict(),
                "workflow_metrics": workflow_metrics,
                "active_coordinations": active_coordinations,
                "active_state_machines": active_state_machines,
                "decision_metrics": decision_metrics,
                "active_alerts": [alert.to_dict() for alert in active_alerts],
                "timestamp": __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting orchestration metrics: {str(e)}")
            raise
    
    async def _register_default_workflows(self):
        """Register default workflow definitions"""
        try:
            # SI to APP processing workflow
            si_to_app_workflow = WorkflowDefinition(
                workflow_id="si_to_app_processing",
                name="SI to APP Processing",
                description="End-to-end workflow for SI to APP processing",
                workflow_type=WorkflowType.INVOICE_PROCESSING,
                version="1.0.0",
                steps=[
                    WorkflowStep(
                        step_id="validate_si_data",
                        name="Validate SI Data",
                        step_type=StepType.VALIDATION,
                        service_role="si",
                        service_name="validation_service",
                        method_name="validate_invoice_data",
                        parameters={"data_source": "si"},
                        dependencies=[],
                        timeout=30,
                        retry_count=2,
                        retry_delay=5
                    ),
                    WorkflowStep(
                        step_id="prepare_transmission",
                        name="Prepare Transmission",
                        step_type=StepType.TRANSFORMATION,
                        service_role="app",
                        service_name="transmission_service",
                        method_name="prepare_transmission",
                        parameters={"format": "firs_format"},
                        dependencies=["validate_si_data"],
                        timeout=60,
                        retry_count=3,
                        retry_delay=10
                    ),
                    WorkflowStep(
                        step_id="transmit_to_firs",
                        name="Transmit to FIRS",
                        step_type=StepType.APP_TRANSMISSION,
                        service_role="app",
                        service_name="transmission_service",
                        method_name="transmit_to_firs",
                        parameters={"endpoint": "firs_api"},
                        dependencies=["prepare_transmission"],
                        timeout=120,
                        retry_count=3,
                        retry_delay=15
                    ),
                    WorkflowStep(
                        step_id="process_response",
                        name="Process FIRS Response",
                        step_type=StepType.SI_PROCESSING,
                        service_role="si",
                        service_name="irn_service",
                        method_name="process_firs_response",
                        parameters={"update_status": True},
                        dependencies=["transmit_to_firs"],
                        timeout=30,
                        retry_count=2,
                        retry_delay=5
                    )
                ],
                triggers=["si_processing_complete"],
                timeout=300,
                retry_policy={"max_retries": 3, "retry_delay": 30},
                rollback_policy={"enabled": True, "rollback_steps": ["process_response", "transmit_to_firs"]}
            )
            
            await self.workflow_engine.register_workflow(si_to_app_workflow)
            
        except Exception as e:
            self.logger.error(f"Error registering default workflows: {str(e)}")
            raise
    
    async def _register_default_state_machines(self):
        """Register default state machine definitions"""
        try:
            # Invoice processing state machine
            invoice_state_machine = StateMachineDefinition(
                machine_id="invoice_processing_states",
                name="Invoice Processing State Machine",
                description="State management for invoice processing workflow",
                initial_state="received",
                final_states=["completed", "failed", "cancelled"],
                states=[
                    State(
                        state_id="received",
                        name="Received",
                        description="Invoice received and queued",
                        state_type=StateType.INITIAL,
                        entry_actions=["log_receipt"],
                        exit_actions=["validate_format"]
                    ),
                    State(
                        state_id="processing",
                        name="Processing",
                        description="Invoice being processed",
                        state_type=StateType.PROCESSING,
                        entry_actions=["start_processing"],
                        exit_actions=["finalize_processing"]
                    ),
                    State(
                        state_id="transmitting",
                        name="Transmitting",
                        description="Transmitting to FIRS",
                        state_type=StateType.PROCESSING,
                        entry_actions=["prepare_transmission"],
                        exit_actions=["log_transmission"]
                    ),
                    State(
                        state_id="completed",
                        name="Completed",
                        description="Processing completed successfully",
                        state_type=StateType.FINAL,
                        entry_actions=["log_completion"],
                        exit_actions=[]
                    ),
                    State(
                        state_id="failed",
                        name="Failed",
                        description="Processing failed",
                        state_type=StateType.ERROR,
                        entry_actions=["log_failure"],
                        exit_actions=[]
                    )
                ],
                transitions=[
                    Transition(
                        transition_id="receive_to_process",
                        from_state="received",
                        to_state="processing",
                        condition=TransitionCondition.SUCCESS,
                        transition_type=TransitionType.AUTOMATIC,
                        actions=["start_processing_timer"]
                    ),
                    Transition(
                        transition_id="process_to_transmit",
                        from_state="processing",
                        to_state="transmitting",
                        condition=TransitionCondition.SUCCESS,
                        transition_type=TransitionType.AUTOMATIC,
                        actions=["prepare_transmission_data"]
                    ),
                    Transition(
                        transition_id="transmit_to_complete",
                        from_state="transmitting",
                        to_state="completed",
                        condition=TransitionCondition.SUCCESS,
                        transition_type=TransitionType.AUTOMATIC,
                        actions=["update_completion_status"]
                    ),
                    Transition(
                        transition_id="any_to_failed",
                        from_state="*",
                        to_state="failed",
                        condition=TransitionCondition.FAILURE,
                        transition_type=TransitionType.AUTOMATIC,
                        actions=["log_error_details"]
                    )
                ],
                global_timeout=3600,
                metadata={"category": "invoice_processing"}
            )
            
            await self.state_machine.register_state_machine(invoice_state_machine)
            
        except Exception as e:
            self.logger.error(f"Error registering default state machines: {str(e)}")
            raise
    
    async def _register_default_decision_rules(self):
        """Register default decision rules"""
        try:
            # High priority processing rule
            high_priority_rule = DecisionRule(
                rule_id="high_priority_processing",
                name="High Priority Processing",
                description="Route high priority invoices to fast processing",
                decision_type=DecisionType.WORKFLOW_ROUTING,
                priority=DecisionPriority.HIGH,
                conditions=[
                    DecisionCondition(
                        condition_id="check_priority",
                        field_path="metadata.priority",
                        operator=RuleOperator.EQUALS,
                        value="high",
                        description="Check if priority is high",
                        weight=1.0
                    )
                ],
                actions=[
                    DecisionAction(
                        action_id="route_to_fast_processing",
                        action_type="route_workflow",
                        parameters={"target_workflow": "fast_processing"},
                        description="Route to fast processing workflow"
                    )
                ],
                logical_operator="AND",
                enabled=True,
                metadata={"decision_logic": "route_to_fast_processing"}
            )
            
            await self.decision_engine.register_decision_rule(high_priority_rule)
            
            # Error handling rule
            error_handling_rule = DecisionRule(
                rule_id="error_handling",
                name="Error Handling",
                description="Handle processing errors",
                decision_type=DecisionType.ERROR_HANDLING,
                priority=DecisionPriority.CRITICAL,
                conditions=[
                    DecisionCondition(
                        condition_id="check_error_count",
                        field_path="error_details.count",
                        operator=RuleOperator.GREATER_THAN,
                        value=3,
                        description="Check if error count exceeds threshold",
                        weight=1.0
                    )
                ],
                actions=[
                    DecisionAction(
                        action_id="escalate_error",
                        action_type="escalate_error",
                        parameters={"escalation_level": "high"},
                        description="Escalate error to higher level"
                    )
                ],
                logical_operator="AND",
                enabled=True,
                metadata={"decision_logic": "escalate_error"}
            )
            
            await self.decision_engine.register_decision_rule(error_handling_rule)
            
        except Exception as e:
            self.logger.error(f"Error registering default decision rules: {str(e)}")
            raise
    
    async def health_check(self) -> dict:
        """Get service health status"""
        try:
            # Check individual component health
            engine_health = await self.workflow_engine.health_check()
            coordinator_health = await self.process_coordinator.health_check()
            state_machine_health = await self.state_machine.health_check()
            decision_engine_health = await self.decision_engine.health_check()
            monitor_health = await self.workflow_monitor.health_check()
            
            # Determine overall health
            overall_status = "healthy"
            component_statuses = [
                engine_health.get("status"),
                coordinator_health.get("status"),
                state_machine_health.get("status"),
                decision_engine_health.get("status"),
                monitor_health.get("status")
            ]
            
            if "error" in component_statuses:
                overall_status = "error"
            elif "degraded" in component_statuses:
                overall_status = "degraded"
            
            return {
                "status": overall_status,
                "service": "workflow_orchestration",
                "components": {
                    "workflow_engine": engine_health,
                    "process_coordinator": coordinator_health,
                    "state_machine": state_machine_health,
                    "decision_engine": decision_engine_health,
                    "workflow_monitor": monitor_health
                },
                "is_initialized": self.is_initialized,
                "is_monitoring": self.is_monitoring,
                "timestamp": __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error in health check: {str(e)}")
            return {
                "status": "error",
                "service": "workflow_orchestration",
                "error": str(e),
                "timestamp": __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat()
            }
    
    async def cleanup(self):
        """Cleanup service resources"""
        self.logger.info("Workflow orchestration service cleanup initiated")
        
        try:
            # Cleanup individual components
            await self.workflow_engine.cleanup()
            await self.process_coordinator.cleanup()
            await self.state_machine.cleanup()
            await self.decision_engine.cleanup()
            await self.workflow_monitor.cleanup()
            
            self.is_initialized = False
            self.is_monitoring = False
            
            self.logger.info("Workflow orchestration service cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}")


def create_workflow_orchestration_service() -> WorkflowOrchestrationService:
    """Create workflow orchestration service with all components"""
    return WorkflowOrchestrationService()


# Common workflow patterns
def get_common_workflow_patterns() -> dict:
    """Get common workflow patterns for reuse"""
    return {
        "si_to_app_processing": {
            "description": "Standard SI to APP processing workflow",
            "steps": ["validate", "transform", "transmit", "process_response"],
            "timeout": 300,
            "retry_policy": {"max_retries": 3, "retry_delay": 30}
        },
        "app_to_si_feedback": {
            "description": "APP to SI feedback workflow",
            "steps": ["receive_feedback", "validate_response", "update_status", "notify"],
            "timeout": 120,
            "retry_policy": {"max_retries": 2, "retry_delay": 15}
        },
        "cross_role_validation": {
            "description": "Cross-role validation workflow",
            "steps": ["collect_data", "apply_rules", "validate", "report"],
            "timeout": 180,
            "retry_policy": {"max_retries": 2, "retry_delay": 10}
        }
    }


# Workflow orchestration utilities
def create_workflow_context(
    workflow_type: str,
    initiator: str,
    data: dict,
    metadata: dict = None
) -> WorkflowContext:
    """Create workflow context with standard structure"""
    return WorkflowContext(
        workflow_id=f"{workflow_type}_{__import__('uuid').uuid4()}",
        execution_id=f"exec_{__import__('uuid').uuid4()}",
        workflow_type=WorkflowType(workflow_type),
        initiator=initiator,
        tenant_id=metadata.get("tenant_id", "default") if metadata else "default",
        metadata=metadata or {},
        variables=data,
        created_at=__import__('datetime').datetime.now(__import__('datetime').timezone.utc),
        updated_at=__import__('datetime').datetime.now(__import__('datetime').timezone.utc)
    )


def create_decision_context(
    source: str,
    data: dict,
    metadata: dict = None
) -> DecisionContext:
    """Create decision context with standard structure"""
    return DecisionContext(
        context_id=f"decision_{__import__('uuid').uuid4()}",
        source=source,
        data=data,
        metadata=metadata or {},
        timestamp=__import__('datetime').datetime.now(__import__('datetime').timezone.utc)
    )