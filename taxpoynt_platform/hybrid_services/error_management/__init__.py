"""
Error Management Hybrid Services Package

This package provides unified error handling services across the TaxPoynt platform,
coordinating error handling, recovery, escalation, and incident tracking between SI and APP roles.

Components:
- ErrorCoordinator: Coordinates error handling across SI and APP roles
- RecoveryOrchestrator: Orchestrates error recovery procedures
- EscalationManager: Manages error escalation workflows
- NotificationRouter: Routes error notifications to appropriate parties
- IncidentTracker: Tracks incidents and their resolution across roles
"""

from .error_coordinator import (
    ErrorCoordinator,
    ErrorType,
    ErrorSeverity,
    ErrorSource,
    ErrorStatus,
    RecoveryAction,
    ErrorContext,
    ErrorRecord,
    ErrorPattern,
    RecoveryPlan,
    create_error_coordinator
)

from .recovery_orchestrator import (
    RecoveryOrchestrator,
    RecoveryStrategy,
    RecoveryStatus,
    RecoveryPriority,
    ActionType,
    ActionStatus,
    RecoveryAction as RecoveryActionOrch,
    RecoverySession,
    RecoveryTemplate,
    RecoveryResult,
    create_recovery_orchestrator
)

from .escalation_manager import (
    EscalationManager,
    EscalationTrigger,
    EscalationStatus,
    EscalationLevel,
    EscalationSeverity,
    NotificationChannel,
    EscalationRule,
    EscalationPolicy,
    EscalationInstance,
    EscalationTarget,
    create_escalation_manager
)

from .notification_router import (
    NotificationRouter,
    NotificationChannel as NotificationRouterChannel,
    NotificationPriority,
    NotificationStatus,
    RoutingStrategy,
    DeliveryMode,
    NotificationTarget,
    NotificationRule,
    NotificationRequest,
    NotificationDelivery,
    NotificationTemplate,
    create_notification_router
)

from .incident_tracker import (
    IncidentTracker,
    IncidentStatus,
    IncidentSeverity,
    IncidentPriority,
    IncidentType,
    IncidentImpact,
    ResolutionType,
    IncidentMetrics,
    IncidentUpdate,
    Incident,
    IncidentResolution,
    IncidentTemplate,
    create_incident_tracker
)

__all__ = [
    # Error Coordinator
    "ErrorCoordinator",
    "ErrorType",
    "ErrorSeverity",
    "ErrorSource",
    "ErrorStatus",
    "RecoveryAction",
    "ErrorContext",
    "ErrorRecord",
    "ErrorPattern",
    "RecoveryPlan",
    "create_error_coordinator",
    
    # Recovery Orchestrator
    "RecoveryOrchestrator",
    "RecoveryStrategy",
    "RecoveryStatus",
    "RecoveryPriority",
    "ActionType",
    "ActionStatus",
    "RecoveryActionOrch",
    "RecoverySession",
    "RecoveryTemplate",
    "RecoveryResult",
    "create_recovery_orchestrator",
    
    # Escalation Manager
    "EscalationManager",
    "EscalationTrigger",
    "EscalationStatus",
    "EscalationLevel",
    "EscalationSeverity",
    "NotificationChannel",
    "EscalationRule",
    "EscalationPolicy",
    "EscalationInstance",
    "EscalationTarget",
    "create_escalation_manager",
    
    # Notification Router
    "NotificationRouter",
    "NotificationRouterChannel",
    "NotificationPriority",
    "NotificationStatus",
    "RoutingStrategy",
    "DeliveryMode",
    "NotificationTarget",
    "NotificationRule",
    "NotificationRequest",
    "NotificationDelivery",
    "NotificationTemplate",
    "create_notification_router",
    
    # Incident Tracker
    "IncidentTracker",
    "IncidentStatus",
    "IncidentSeverity",
    "IncidentPriority",
    "IncidentType",
    "IncidentImpact",
    "ResolutionType",
    "IncidentMetrics",
    "IncidentUpdate",
    "Incident",
    "IncidentResolution",
    "IncidentTemplate",
    "create_incident_tracker"
]

# Package version
__version__ = "1.0.0"

# Package metadata
__author__ = "TaxPoynt Platform Team"
__description__ = "Unified error handling services for TaxPoynt platform"
__license__ = "Proprietary"


# Convenience factory function to create all services
def create_error_management_services():
    """
    Create all error management services as a unified suite
    
    Returns:
        Dict containing all initialized services
    """
    return {
        "error_coordinator": create_error_coordinator(),
        "recovery_orchestrator": create_recovery_orchestrator(),
        "escalation_manager": create_escalation_manager(),
        "notification_router": create_notification_router(),
        "incident_tracker": create_incident_tracker()
    }


# Service initialization helper
async def initialize_error_management_services(services: dict = None):
    """
    Initialize all error management services
    
    Args:
        services: Optional dict of services to initialize. If None, creates all services.
    """
    if services is None:
        services = create_error_management_services()
    
    # Initialize services in dependency order
    initialization_order = [
        "notification_router",    # Base notification infrastructure
        "incident_tracker",       # Incident tracking foundation
        "error_coordinator",      # Core error coordination
        "escalation_manager",     # Escalation workflows
        "recovery_orchestrator"   # Recovery orchestration
    ]
    
    for service_name in initialization_order:
        if service_name in services:
            await services[service_name].initialize()
    
    return services


# Service cleanup helper
async def cleanup_error_management_services(services: dict):
    """
    Cleanup all error management services
    
    Args:
        services: Dict of services to cleanup
    """
    # Cleanup in reverse dependency order
    cleanup_order = [
        "recovery_orchestrator",
        "escalation_manager",
        "error_coordinator",
        "incident_tracker",
        "notification_router"
    ]
    
    for service_name in cleanup_order:
        if service_name in services:
            await services[service_name].cleanup()


# Health check aggregator
async def get_error_management_health(services: dict):
    """
    Get aggregated health status for all error management services
    
    Args:
        services: Dict of services to check
        
    Returns:
        Dict containing overall health status
    """
    health_results = {}
    overall_status = "healthy"
    critical_issues = []
    
    for service_name, service in services.items():
        try:
            health = await service.health_check()
            health_results[service_name] = health
            
            # Determine overall status (worst status wins)
            service_status = health.get("status", "unknown")
            if service_status == "error":
                overall_status = "error"
                critical_issues.append(f"{service_name}: {health.get('error', 'Unknown error')}")
            elif service_status == "degraded" and overall_status != "error":
                overall_status = "degraded"
                
        except Exception as e:
            health_results[service_name] = {
                "status": "error",
                "error": str(e)
            }
            overall_status = "error"
            critical_issues.append(f"{service_name}: {str(e)}")
    
    # Aggregate metrics
    aggregated_metrics = {
        "total_errors_handled": 0,
        "active_incidents": 0,
        "active_escalations": 0,
        "pending_recoveries": 0,
        "pending_notifications": 0
    }
    
    for service_name, health in health_results.items():
        metrics = health.get("metrics", {})
        
        if service_name == "error_coordinator":
            aggregated_metrics["total_errors_handled"] = metrics.get("total_errors_stored", 0)
        elif service_name == "incident_tracker":
            aggregated_metrics["active_incidents"] = metrics.get("open_incidents", 0)
        elif service_name == "escalation_manager":
            aggregated_metrics["active_escalations"] = metrics.get("active_escalations", 0)
        elif service_name == "recovery_orchestrator":
            aggregated_metrics["pending_recoveries"] = metrics.get("active_recoveries", 0)
        elif service_name == "notification_router":
            aggregated_metrics["pending_notifications"] = metrics.get("pending_deliveries", 0)
    
    return {
        "overall_status": overall_status,
        "services": health_results,
        "critical_issues": critical_issues,
        "aggregated_metrics": aggregated_metrics,
        "timestamp": f"{__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat()}"
    }


# Error handling workflow orchestrator
async def handle_platform_error(
    services: dict,
    error: Exception,
    context: dict,
    error_type: str = "system",
    severity: str = "medium"
):
    """
    Orchestrate platform-wide error handling workflow
    
    Args:
        services: Dict of error management services
        error: The exception that occurred
        context: Error context information
        error_type: Type of error
        severity: Severity level
        
    Returns:
        Dict containing workflow results
    """
    try:
        workflow_results = {
            "error_id": None,
            "incident_id": None,
            "escalation_id": None,
            "recovery_session_id": None,
            "notifications_sent": 0
        }
        
        # 1. Coordinate the error
        if "error_coordinator" in services:
            error_coordinator = services["error_coordinator"]
            
            # Create error context
            from .error_coordinator import ErrorContext, ErrorType, ErrorSeverity
            
            error_context = ErrorContext(
                context_id=str(__import__("uuid").uuid4()),
                user_id=context.get("user_id"),
                session_id=context.get("session_id"),
                request_id=context.get("request_id"),
                operation_name=context.get("operation_name", "unknown"),
                service_name=context.get("service_name", "unknown"),
                role=context.get("role", "unknown"),
                tenant_id=context.get("tenant_id"),
                trace_id=context.get("trace_id"),
                metadata=context.get("metadata", {})
            )
            
            error_id = await error_coordinator.handle_error(
                error=error,
                context=error_context,
                error_type=ErrorType(error_type),
                severity=ErrorSeverity(severity)
            )
            
            workflow_results["error_id"] = error_id
        
        # 2. Create incident if necessary
        if severity in ["critical", "high"] and "incident_tracker" in services:
            incident_tracker = services["incident_tracker"]
            
            from .incident_tracker import IncidentType, IncidentSeverity
            
            incident_id = await incident_tracker.create_incident(
                title=f"{error_type.title()} Error in {context.get('service_name', 'Unknown Service')}",
                description=f"Incident created for {severity} {error_type} error: {str(error)}",
                incident_type=IncidentType.OUTAGE if severity == "critical" else IncidentType.DEGRADATION,
                severity=IncidentSeverity.SEV1_CRITICAL if severity == "critical" else IncidentSeverity.SEV2_HIGH,
                reporter="platform_error_handler",
                affected_services=[context.get("service_name", "unknown")],
                context=context
            )
            
            workflow_results["incident_id"] = incident_id
            
            # Link error to incident
            if error_id and incident_id:
                await incident_tracker.link_error_to_incident(incident_id, error_id)
        
        # 3. Evaluate escalation
        if severity in ["critical", "high"] and "escalation_manager" in services:
            escalation_manager = services["escalation_manager"]
            
            escalation_id = await escalation_manager.evaluate_escalation(
                error_id=error_id or str(__import__("uuid").uuid4()),
                error_data={
                    "error_type": error_type,
                    "severity": severity,
                    "service_name": context.get("service_name"),
                    "occurred_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat()
                },
                context=context
            )
            
            workflow_results["escalation_id"] = escalation_id
        
        # 4. Initiate recovery if applicable
        if error_type in ["network", "timeout", "integration"] and "recovery_orchestrator" in services:
            recovery_orchestrator = services["recovery_orchestrator"]
            
            from .recovery_orchestrator import RecoveryStrategy, RecoveryPriority
            
            recovery_session_id = await recovery_orchestrator.create_recovery_session(
                error_id=error_id or str(__import__("uuid").uuid4()),
                error_type=error_type,
                error_context=context,
                strategy=RecoveryStrategy.EXPONENTIAL_BACKOFF,
                priority=RecoveryPriority.HIGH if severity in ["critical", "high"] else RecoveryPriority.MEDIUM
            )
            
            workflow_results["recovery_session_id"] = recovery_session_id
            
            # Execute recovery
            if recovery_session_id:
                recovery_result = await recovery_orchestrator.execute_recovery(recovery_session_id)
                workflow_results["recovery_success"] = recovery_result.success
        
        # 5. Route notifications
        if "notification_router" in services:
            notification_router = services["notification_router"]
            
            from .notification_router import NotificationPriority
            
            notification_request_id = await notification_router.route_notification(
                notification_type="platform_error",
                data={
                    "error_type": error_type,
                    "severity": severity,
                    "error_message": str(error),
                    "service_name": context.get("service_name"),
                    "error_id": error_id,
                    "incident_id": workflow_results["incident_id"],
                    "escalation_id": workflow_results["escalation_id"]
                },
                context=context,
                priority=NotificationPriority.IMMEDIATE if severity == "critical" else NotificationPriority.HIGH
            )
            
            workflow_results["notification_request_id"] = notification_request_id
        
        return workflow_results
        
    except Exception as e:
        # Log the meta-error
        __import__("logging").getLogger(__name__).error(f"Error in platform error handling workflow: {str(e)}")
        return {"error": str(e), "workflow_failed": True}


# Monitoring and metrics aggregator
async def get_error_management_metrics(services: dict, time_range_hours: int = 24):
    """
    Get aggregated metrics across all error management services
    
    Args:
        services: Dict of services to collect metrics from
        time_range_hours: Time range for metrics collection
        
    Returns:
        Dict containing aggregated metrics
    """
    try:
        metrics = {
            "time_range_hours": time_range_hours,
            "error_metrics": {},
            "incident_metrics": {},
            "escalation_metrics": {},
            "recovery_metrics": {},
            "notification_metrics": {},
            "overall_stats": {
                "total_errors": 0,
                "total_incidents": 0,
                "total_escalations": 0,
                "total_recoveries": 0,
                "total_notifications": 0,
                "avg_resolution_time_minutes": 0,
                "success_rates": {}
            }
        }
        
        # Collect metrics from each service
        if "error_coordinator" in services:
            error_summary = await services["error_coordinator"].get_error_summary(time_range_hours)
            metrics["error_metrics"] = error_summary
            metrics["overall_stats"]["total_errors"] = error_summary.get("total_errors", 0)
        
        if "incident_tracker" in services:
            incident_summary = await services["incident_tracker"].get_incidents_summary(time_range_hours)
            metrics["incident_metrics"] = incident_summary
            metrics["overall_stats"]["total_incidents"] = incident_summary.get("total_incidents", 0)
        
        if "escalation_manager" in services:
            escalation_summary = await services["escalation_manager"].get_escalation_summary(time_range_hours)
            metrics["escalation_metrics"] = escalation_summary
            metrics["overall_stats"]["total_escalations"] = escalation_summary.get("total_escalations", 0)
        
        if "recovery_orchestrator" in services:
            recovery_summary = await services["recovery_orchestrator"].get_recovery_summary(time_range_hours)
            metrics["recovery_metrics"] = recovery_summary
            metrics["overall_stats"]["total_recoveries"] = recovery_summary.get("total_sessions", 0)
        
        if "notification_router" in services:
            notification_summary = await services["notification_router"].get_delivery_summary(time_range_hours)
            metrics["notification_metrics"] = notification_summary
            metrics["overall_stats"]["total_notifications"] = notification_summary.get("total_deliveries", 0)
        
        # Calculate overall success rates
        metrics["overall_stats"]["success_rates"] = {
            "error_resolution_rate": metrics["error_metrics"].get("resolution_rate", 0),
            "incident_resolution_rate": (metrics["incident_metrics"].get("resolved_incidents", 0) / max(metrics["incident_metrics"].get("total_incidents", 1), 1)) * 100,
            "escalation_resolution_rate": metrics["escalation_metrics"].get("resolution_rate", 0),
            "recovery_success_rate": metrics["recovery_metrics"].get("success_rate", 0),
            "notification_delivery_rate": metrics["notification_metrics"].get("success_rate", 0)
        }
        
        return metrics
        
    except Exception as e:
        __import__("logging").getLogger(__name__).error(f"Error collecting error management metrics: {str(e)}")
        return {"error": str(e)}


# Configuration validator
def validate_error_management_config(config: dict) -> List[str]:
    """
    Validate error management configuration
    
    Args:
        config: Configuration dictionary
        
    Returns:
        List of validation errors
    """
    errors = []
    
    try:
        # Validate required sections
        required_sections = [
            "error_coordinator",
            "recovery_orchestrator", 
            "escalation_manager",
            "notification_router",
            "incident_tracker"
        ]
        
        for section in required_sections:
            if section not in config:
                errors.append(f"Missing required configuration section: {section}")
        
        # Validate escalation configuration
        if "escalation_manager" in config:
            escalation_config = config["escalation_manager"]
            
            if "sla_thresholds" not in escalation_config:
                errors.append("Missing SLA thresholds in escalation_manager configuration")
            
            if "notification_channels" not in escalation_config:
                errors.append("Missing notification channels in escalation_manager configuration")
        
        # Validate notification configuration
        if "notification_router" in config:
            notification_config = config["notification_router"]
            
            if "default_channels" not in notification_config:
                errors.append("Missing default channels in notification_router configuration")
                
            if "rate_limits" not in notification_config:
                errors.append("Missing rate limits in notification_router configuration")
        
        # Validate recovery configuration
        if "recovery_orchestrator" in config:
            recovery_config = config["recovery_orchestrator"]
            
            if "max_concurrent_recoveries" not in recovery_config:
                errors.append("Missing max_concurrent_recoveries in recovery_orchestrator configuration")
                
            if "recovery_timeout_minutes" not in recovery_config:
                errors.append("Missing recovery_timeout_minutes in recovery_orchestrator configuration")
        
    except Exception as e:
        errors.append(f"Configuration validation error: {str(e)}")
    
    return errors