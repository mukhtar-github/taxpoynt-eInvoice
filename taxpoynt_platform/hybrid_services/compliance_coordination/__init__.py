"""
TaxPoynt Platform - Hybrid Services: Compliance Coordination
Unified compliance enforcement across SI and APP roles
"""

from .regulation_engine import (
    RegulationEngine,
    RegulationType,
    RuleType,
    ComplianceLevel,
    ViolationSeverity,
    ServiceScope,
    RegulationRule,
    ComplianceViolation,
    ComplianceResult,
    RegulationContext,
    create_regulation_engine
)

from .cross_role_validator import (
    CrossRoleValidator,
    ValidationScope,
    ValidationPhase,
    ValidationType,
    ValidationSeverity,
    ValidationStatus,
    ValidationRule,
    ValidationContext,
    ValidationIssue,
    ValidationResult,
    DataIntegrityCheck,
    create_cross_role_validator
)

from .compliance_orchestrator import (
    ComplianceOrchestrator,
    ComplianceWorkflowType,
    CompliancePhase,
    ComplianceStatus,
    CompliancePriority,
    ComplianceWorkflowDefinition,
    ComplianceContext,
    CompliancePhaseResult,
    ComplianceExecution,
    create_compliance_orchestrator
)

from .audit_coordinator import (
    AuditCoordinator,
    AuditType,
    AuditScope,
    AuditStatus,
    AuditPriority,
    EventType,
    AuditEvent,
    AuditTrail,
    AuditSession,
    AuditFinding,
    AuditReport,
    create_audit_coordinator
)

from .regulatory_tracker import (
    RegulatoryTracker,
    RegulatorySource,
    ChangeType,
    ImpactLevel,
    ChangeStatus,
    NotificationStatus,
    RegulatoryChange,
    RegulatorySubscription,
    RegulatoryNotification,
    ComplianceGap,
    ComplianceStatus,
    create_regulatory_tracker
)

__version__ = "1.0.0"

__all__ = [
    # Regulation Engine
    "RegulationEngine",
    "RegulationType",
    "RuleType",
    "ComplianceLevel",
    "ViolationSeverity",
    "ServiceScope",
    "RegulationRule",
    "ComplianceViolation",
    "ComplianceResult",
    "RegulationContext",
    "create_regulation_engine",
    
    # Cross-Role Validator
    "CrossRoleValidator",
    "ValidationScope",
    "ValidationPhase",
    "ValidationType",
    "ValidationSeverity",
    "ValidationStatus",
    "ValidationRule",
    "ValidationContext",
    "ValidationIssue",
    "ValidationResult",
    "DataIntegrityCheck",
    "create_cross_role_validator",
    
    # Compliance Orchestrator
    "ComplianceOrchestrator",
    "ComplianceWorkflowType",
    "CompliancePhase",
    "ComplianceStatus",
    "CompliancePriority",
    "ComplianceWorkflowDefinition",
    "ComplianceContext",
    "CompliancePhaseResult",
    "ComplianceExecution",
    "create_compliance_orchestrator",
    
    # Audit Coordinator
    "AuditCoordinator",
    "AuditType",
    "AuditScope",
    "AuditStatus",
    "AuditPriority",
    "EventType",
    "AuditEvent",
    "AuditTrail",
    "AuditSession",
    "AuditFinding",
    "AuditReport",
    "create_audit_coordinator",
    
    # Regulatory Tracker
    "RegulatoryTracker",
    "RegulatorySource",
    "ChangeType",
    "ImpactLevel",
    "ChangeStatus",
    "NotificationStatus",
    "RegulatoryChange",
    "RegulatorySubscription",
    "RegulatoryNotification",
    "ComplianceGap",
    "ComplianceStatus",
    "create_regulatory_tracker"
]


class ComplianceCoordinationService:
    """
    Comprehensive compliance coordination service
    Unified compliance enforcement across SI and APP roles
    """
    
    def __init__(self):
        """Initialize compliance coordination service"""
        self.regulation_engine = create_regulation_engine()
        self.cross_role_validator = create_cross_role_validator()
        self.compliance_orchestrator = create_compliance_orchestrator()
        self.audit_coordinator = create_audit_coordinator()
        self.regulatory_tracker = create_regulatory_tracker()
        self.logger = __import__('logging').getLogger(__name__)
        
        # Service state
        self.is_initialized = False
        self.is_monitoring = False
    
    async def initialize(self):
        """Initialize the compliance coordination service"""
        if self.is_initialized:
            return
        
        self.logger.info("Initializing compliance coordination service")
        
        try:
            # Start regulatory monitoring
            await self.regulatory_tracker.start_monitoring()
            self.is_monitoring = True
            
            # Register default audit session for compliance
            await self._initiate_default_audit_session()
            
            # Initialize cross-service integration
            await self._setup_cross_service_integration()
            
            self.is_initialized = True
            self.logger.info("Compliance coordination service initialized")
            
        except Exception as e:
            self.logger.error(f"Error initializing compliance coordination service: {str(e)}")
            raise
    
    async def execute_comprehensive_compliance_check(
        self,
        service_role: str,
        target_services: list,
        data: dict,
        metadata: dict,
        initiated_by: str
    ) -> dict:
        """
        Execute comprehensive compliance check across all components
        
        Args:
            service_role: Role of the service being checked
            target_services: List of target services
            data: Data to be checked
            metadata: Additional metadata
            initiated_by: User/system initiating the check
            
        Returns:
            Comprehensive compliance results
        """
        try:
            # Create compliance context
            compliance_context = ComplianceContext(
                context_id=f"comprehensive_check_{__import__('uuid').uuid4()}",
                workflow_type=ComplianceWorkflowType.FULL_COMPLIANCE_CHECK,
                initiated_by=initiated_by,
                service_role=service_role,
                target_services=target_services,
                data=data,
                metadata=metadata,
                priority=CompliancePriority.HIGH,
                timestamp=__import__('datetime').datetime.now(__import__('datetime').timezone.utc)
            )
            
            # Execute compliance orchestration
            compliance_execution = await self.compliance_orchestrator.execute_compliance_workflow(
                "full_compliance_check",
                compliance_context
            )
            
            # Initiate audit session
            audit_session = await self.audit_coordinator.initiate_audit_session(
                audit_type=AuditType.COMPLIANCE_AUDIT,
                audit_scope=AuditScope.CROSS_ROLE,
                initiated_by=initiated_by,
                target_services=target_services,
                objectives=[
                    "Verify compliance with regulations",
                    "Validate cross-role data integrity",
                    "Document compliance status"
                ],
                priority=AuditPriority.HIGH
            )
            
            # Log audit events for compliance check
            await self.audit_coordinator.log_audit_event(
                event_type=EventType.COMPLIANCE_CHECK,
                service_role=service_role,
                service_name="compliance_coordination",
                action="comprehensive_compliance_check",
                resource=f"compliance_check:{compliance_context.context_id}",
                details={
                    "target_services": target_services,
                    "compliance_execution_id": compliance_execution.execution_id,
                    "audit_session_id": audit_session.session_id
                },
                user_id=initiated_by,
                session_id=audit_session.session_id
            )
            
            return {
                "compliance_execution": compliance_execution.to_dict(),
                "audit_session": audit_session.to_dict(),
                "status": "completed",
                "timestamp": __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error executing comprehensive compliance check: {str(e)}")
            raise
    
    async def validate_cross_role_handoff(
        self,
        source_role: str,
        target_role: str,
        handoff_data: dict,
        validation_phase: str = "handoff"
    ) -> dict:
        """
        Validate cross-role handoff with compliance enforcement
        
        Args:
            source_role: Source service role
            target_role: Target service role
            handoff_data: Data being handed off
            validation_phase: Phase of validation
            
        Returns:
            Validation results with compliance status
        """
        try:
            # Create validation context
            validation_context = ValidationContext(
                context_id=f"cross_role_handoff_{__import__('uuid').uuid4()}",
                source_role=source_role,
                target_role=target_role,
                validation_phase=ValidationPhase(validation_phase),
                data=handoff_data,
                metadata={"handoff_type": "cross_role"},
                timestamp=__import__('datetime').datetime.now(__import__('datetime').timezone.utc)
            )
            
            # Execute cross-role validation
            validation_result = await self.cross_role_validator.validate_cross_role_data(
                validation_context,
                validation_types=[
                    ValidationType.DATA_INTEGRITY,
                    ValidationType.SCHEMA_COMPLIANCE,
                    ValidationType.BUSINESS_RULES
                ]
            )
            
            # Create regulation context
            regulation_context = RegulationContext(
                context_id=validation_context.context_id,
                service_role=source_role,
                service_name=target_role,
                operation="cross_role_handoff",
                data=handoff_data,
                metadata={"target_role": target_role},
                timestamp=__import__('datetime').datetime.now(__import__('datetime').timezone.utc)
            )
            
            # Enforce regulations
            regulation_results = await self.regulation_engine.enforce_regulations(
                regulation_context,
                [RegulationType.FIRS_EINVOICE, RegulationType.DATA_PROTECTION]
            )
            
            return {
                "validation_result": validation_result.to_dict(),
                "regulation_results": [r.to_dict() for r in regulation_results],
                "overall_status": "passed" if validation_result.status == ValidationStatus.PASSED else "failed",
                "timestamp": __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error validating cross-role handoff: {str(e)}")
            raise
    
    async def track_regulatory_compliance(
        self,
        service_name: str,
        regulation_sources: list = None
    ) -> dict:
        """
        Track regulatory compliance for a service
        
        Args:
            service_name: Name of the service
            regulation_sources: List of regulatory sources to track
            
        Returns:
            Compliance tracking results
        """
        try:
            # Get regulatory changes
            regulatory_changes = await self.regulatory_tracker.get_regulatory_changes(
                source=regulation_sources[0] if regulation_sources else None,
                limit=50
            )
            
            # Get compliance status
            compliance_status = await self.regulatory_tracker.get_compliance_status(
                service_name=service_name
            )
            
            # Check upcoming deadlines
            upcoming_deadlines = await self.regulatory_tracker.check_compliance_deadlines(
                days_ahead=60
            )
            
            # Generate compliance report
            compliance_report = await self.regulatory_tracker.generate_compliance_report(
                service_name=service_name,
                report_type="detailed"
            )
            
            return {
                "service_name": service_name,
                "regulatory_changes": [c.to_dict() for c in regulatory_changes],
                "compliance_status": [s.to_dict() for s in compliance_status],
                "upcoming_deadlines": upcoming_deadlines,
                "compliance_report": compliance_report,
                "timestamp": __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error tracking regulatory compliance: {str(e)}")
            raise
    
    async def initiate_compliance_audit(
        self,
        audit_type: str,
        audit_scope: str,
        target_services: list,
        initiated_by: str,
        objectives: list = None
    ) -> dict:
        """
        Initiate compliance audit
        
        Args:
            audit_type: Type of audit
            audit_scope: Scope of audit
            target_services: Services to audit
            initiated_by: User initiating audit
            objectives: Audit objectives
            
        Returns:
            Audit initiation results
        """
        try:
            # Initiate audit session
            audit_session = await self.audit_coordinator.initiate_audit_session(
                audit_type=AuditType(audit_type),
                audit_scope=AuditScope(audit_scope),
                initiated_by=initiated_by,
                target_services=target_services,
                objectives=objectives or ["Verify compliance with regulations"],
                priority=AuditPriority.HIGH
            )
            
            # Create compliance context for audit
            compliance_context = ComplianceContext(
                context_id=f"audit_compliance_{audit_session.session_id}",
                workflow_type=ComplianceWorkflowType.REGULATORY_AUDIT,
                initiated_by=initiated_by,
                service_role="hybrid",
                target_services=target_services,
                data={"audit_session_id": audit_session.session_id},
                metadata={"audit_type": audit_type, "audit_scope": audit_scope},
                priority=CompliancePriority.HIGH,
                timestamp=__import__('datetime').datetime.now(__import__('datetime').timezone.utc)
            )
            
            # Execute compliance workflow for audit
            compliance_execution = await self.compliance_orchestrator.execute_compliance_workflow(
                "regulatory_audit",
                compliance_context
            )
            
            return {
                "audit_session": audit_session.to_dict(),
                "compliance_execution": compliance_execution.to_dict(),
                "status": "initiated",
                "timestamp": __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error initiating compliance audit: {str(e)}")
            raise
    
    async def get_compliance_dashboard(self) -> dict:
        """Get comprehensive compliance dashboard"""
        try:
            # Get compliance orchestrator metrics
            compliance_metrics = await self.compliance_orchestrator.get_compliance_metrics()
            
            # Get validation metrics
            validation_metrics = await self.cross_role_validator.get_validation_metrics()
            
            # Get audit metrics
            audit_metrics = await self.audit_coordinator.get_audit_metrics()
            
            # Get regulatory metrics
            regulatory_metrics = await self.regulatory_tracker.get_regulatory_metrics()
            
            # Get regulation engine compliance status
            regulation_status = await self.regulation_engine.get_compliance_status()
            
            # Get active sessions and executions
            active_audits = await self.audit_coordinator.list_active_sessions()
            active_executions = await self.compliance_orchestrator.list_active_executions()
            
            return {
                "compliance_overview": {
                    "total_compliance_checks": compliance_metrics.get("total_executions", 0),
                    "success_rate": compliance_metrics.get("success_rate", 0),
                    "active_executions": len(active_executions),
                    "critical_issues": compliance_metrics.get("critical_issues", 0)
                },
                "validation_overview": {
                    "total_validations": validation_metrics.get("total_validations", 0),
                    "validation_success_rate": validation_metrics.get("success_rate", 0),
                    "cross_role_issues": validation_metrics.get("violation_count", 0)
                },
                "audit_overview": {
                    "total_audits": audit_metrics.get("total_sessions", 0),
                    "audit_success_rate": audit_metrics.get("success_rate", 0),
                    "active_audits": len(active_audits),
                    "total_findings": audit_metrics.get("total_findings", 0)
                },
                "regulatory_overview": {
                    "total_regulatory_changes": regulatory_metrics.get("total_regulatory_changes", 0),
                    "pending_notifications": regulatory_metrics.get("pending_notifications", 0),
                    "average_compliance": regulatory_metrics.get("average_compliance_percentage", 0)
                },
                "regulation_enforcement": {
                    "total_checks": regulation_status.get("total_checks", 0),
                    "compliance_rate": regulation_status.get("compliance_rate", 0),
                    "active_violations": regulation_status.get("active_violations", 0)
                },
                "active_sessions": {
                    "compliance_executions": active_executions,
                    "audit_sessions": active_audits
                },
                "timestamp": __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting compliance dashboard: {str(e)}")
            raise
    
    async def handle_regulatory_change_notification(
        self,
        change_data: dict,
        source: str = "external"
    ) -> dict:
        """
        Handle regulatory change notification
        
        Args:
            change_data: Regulatory change data
            source: Source of the change
            
        Returns:
            Processing results
        """
        try:
            # Create regulatory change
            regulatory_change = RegulatoryChange(
                change_id=change_data.get("id", str(__import__('uuid').uuid4())),
                source=RegulatorySource(source),
                change_type=ChangeType(change_data.get("type", "regulation_update")),
                title=change_data.get("title", ""),
                description=change_data.get("description", ""),
                impact_level=ImpactLevel(change_data.get("impact_level", "medium")),
                status=ChangeStatus(change_data.get("status", "effective")),
                affected_services=change_data.get("affected_services", []),
                compliance_deadline=__import__('datetime').datetime.fromisoformat(change_data["compliance_deadline"]) if change_data.get("compliance_deadline") else None,
                effective_date=__import__('datetime').datetime.fromisoformat(change_data.get("effective_date", __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat())),
                published_date=__import__('datetime').datetime.fromisoformat(change_data.get("published_date", __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat())),
                reference_number=change_data.get("reference_number"),
                document_url=change_data.get("document_url"),
                details=change_data.get("details", {}),
                metadata=change_data.get("metadata", {})
            )
            
            # Register the change
            await self.regulatory_tracker.register_regulatory_change(regulatory_change)
            
            # If critical, initiate emergency compliance check
            if regulatory_change.impact_level == ImpactLevel.CRITICAL:
                await self.compliance_orchestrator.execute_emergency_compliance(
                    incident_type="critical_regulatory_change",
                    affected_services=regulatory_change.affected_services,
                    incident_data=regulatory_change.to_dict(),
                    initiated_by="system"
                )
            
            return {
                "regulatory_change": regulatory_change.to_dict(),
                "status": "processed",
                "actions_taken": [
                    "Regulatory change registered",
                    "Subscribers notified",
                    "Compliance gaps identified"
                ],
                "timestamp": __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error handling regulatory change notification: {str(e)}")
            raise
    
    async def _initiate_default_audit_session(self):
        """Initiate default audit session for system compliance"""
        try:
            await self.audit_coordinator.initiate_audit_session(
                audit_type=AuditType.COMPLIANCE_AUDIT,
                audit_scope=AuditScope.SYSTEM_WIDE,
                initiated_by="system",
                target_services=["si_services", "app_services", "hybrid_services"],
                objectives=[
                    "Monitor system-wide compliance",
                    "Track regulatory adherence",
                    "Generate compliance audit trail"
                ],
                priority=AuditPriority.ROUTINE
            )
            
        except Exception as e:
            self.logger.error(f"Error initiating default audit session: {str(e)}")
    
    async def _setup_cross_service_integration(self):
        """Setup integration between compliance components"""
        try:
            # Register custom validators in cross-role validator
            self.cross_role_validator.register_custom_validator(
                "regulation_compliance",
                self._validate_regulation_compliance
            )
            
            # Register audit event handler
            await self.audit_coordinator.log_audit_event(
                event_type=EventType.SYSTEM_CONFIGURATION,
                service_role="hybrid",
                service_name="compliance_coordination",
                action="service_integration_setup",
                resource="compliance_coordination_service",
                details={"integration_status": "completed"},
                user_id="system"
            )
            
        except Exception as e:
            self.logger.error(f"Error setting up cross-service integration: {str(e)}")
    
    async def _validate_regulation_compliance(self, rule, context):
        """Custom validator for regulation compliance"""
        try:
            # Create regulation context from validation context
            regulation_context = RegulationContext(
                context_id=context.context_id,
                service_role=context.source_role,
                service_name=context.target_role,
                operation="validation_compliance_check",
                data=context.data,
                metadata=context.metadata,
                timestamp=context.timestamp
            )
            
            # Check regulation compliance
            regulation_results = await self.regulation_engine.enforce_regulations(
                regulation_context,
                [RegulationType.FIRS_EINVOICE]
            )
            
            # Return validation result
            violations = []
            for result in regulation_results:
                violations.extend(result.violations)
            
            return {
                "passed": len(violations) == 0,
                "violations": [v.to_dict() for v in violations],
                "regulation_results": [r.to_dict() for r in regulation_results]
            }
            
        except Exception as e:
            self.logger.error(f"Error in regulation compliance validation: {str(e)}")
            return {"passed": False, "error": str(e)}
    
    async def health_check(self) -> dict:
        """Get service health status"""
        try:
            # Check individual component health
            regulation_health = await self.regulation_engine.health_check()
            validator_health = await self.cross_role_validator.health_check()
            orchestrator_health = await self.compliance_orchestrator.health_check()
            audit_health = await self.audit_coordinator.health_check()
            tracker_health = await self.regulatory_tracker.health_check()
            
            # Determine overall health
            overall_status = "healthy"
            component_statuses = [
                regulation_health.get("status"),
                validator_health.get("status"),
                orchestrator_health.get("status"),
                audit_health.get("status"),
                tracker_health.get("status")
            ]
            
            if "error" in component_statuses:
                overall_status = "error"
            elif "degraded" in component_statuses:
                overall_status = "degraded"
            
            return {
                "status": overall_status,
                "service": "compliance_coordination",
                "components": {
                    "regulation_engine": regulation_health,
                    "cross_role_validator": validator_health,
                    "compliance_orchestrator": orchestrator_health,
                    "audit_coordinator": audit_health,
                    "regulatory_tracker": tracker_health
                },
                "is_initialized": self.is_initialized,
                "is_monitoring": self.is_monitoring,
                "timestamp": __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error in health check: {str(e)}")
            return {
                "status": "error",
                "service": "compliance_coordination",
                "error": str(e),
                "timestamp": __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat()
            }
    
    async def cleanup(self):
        """Cleanup service resources"""
        self.logger.info("Compliance coordination service cleanup initiated")
        
        try:
            # Cleanup individual components
            await self.regulation_engine.cleanup()
            await self.cross_role_validator.cleanup()
            await self.compliance_orchestrator.cleanup()
            await self.audit_coordinator.cleanup()
            await self.regulatory_tracker.cleanup()
            
            self.is_initialized = False
            self.is_monitoring = False
            
            self.logger.info("Compliance coordination service cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}")


def create_compliance_coordination_service() -> ComplianceCoordinationService:
    """Create compliance coordination service with all components"""
    return ComplianceCoordinationService()


# Common compliance patterns
def get_common_compliance_patterns() -> dict:
    """Get common compliance patterns for reuse"""
    return {
        "firs_einvoice_compliance": {
            "description": "Standard FIRS e-invoice compliance check",
            "regulations": ["firs_einvoice", "certificate_management"],
            "validations": ["data_integrity", "schema_compliance"],
            "audit_requirements": True
        },
        "cross_role_handoff_compliance": {
            "description": "Cross-role handoff compliance validation",
            "regulations": ["data_protection", "audit_trail"],
            "validations": ["data_integrity", "business_rules"],
            "audit_requirements": True
        },
        "regulatory_change_compliance": {
            "description": "Compliance check for regulatory changes",
            "regulations": ["all_applicable"],
            "validations": ["comprehensive"],
            "audit_requirements": True
        }
    }


# Compliance utilities
def create_compliance_context(
    workflow_type: str,
    service_role: str,
    target_services: list,
    data: dict,
    metadata: dict = None
) -> ComplianceContext:
    """Create compliance context with standard structure"""
    return ComplianceContext(
        context_id=f"{workflow_type}_{__import__('uuid').uuid4()}",
        workflow_type=ComplianceWorkflowType(workflow_type),
        initiated_by="system",
        service_role=service_role,
        target_services=target_services,
        data=data,
        metadata=metadata or {},
        priority=CompliancePriority.MEDIUM,
        timestamp=__import__('datetime').datetime.now(__import__('datetime').timezone.utc)
    )


def create_regulation_context(
    service_role: str,
    operation: str,
    data: dict,
    metadata: dict = None
) -> RegulationContext:
    """Create regulation context with standard structure"""
    return RegulationContext(
        context_id=f"regulation_{__import__('uuid').uuid4()}",
        service_role=service_role,
        service_name="compliance_service",
        operation=operation,
        data=data,
        metadata=metadata or {},
        timestamp=__import__('datetime').datetime.now(__import__('datetime').timezone.utc)
    )


def create_validation_context(
    source_role: str,
    target_role: str,
    validation_phase: str,
    data: dict,
    metadata: dict = None
) -> ValidationContext:
    """Create validation context with standard structure"""
    return ValidationContext(
        context_id=f"validation_{__import__('uuid').uuid4()}",
        source_role=source_role,
        target_role=target_role,
        validation_phase=ValidationPhase(validation_phase),
        data=data,
        metadata=metadata or {},
        timestamp=__import__('datetime').datetime.now(__import__('datetime').timezone.utc)
    )