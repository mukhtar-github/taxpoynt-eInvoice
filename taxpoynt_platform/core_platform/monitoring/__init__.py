"""
Core Platform Monitoring - Observability System

Comprehensive observability suite for the TaxPoynt platform providing:
- Metrics aggregation across all services
- Health orchestration and monitoring
- Centralized alerting and incident management
- Distributed tracing for request flows
- Centralized logging and analysis

This package provides unified observability across:
- SI Services (ERP integrations, certificate management, etc.)
- APP Services (FIRS communication, taxpayer management, etc.)
- Hybrid Services (analytics, billing, workflow orchestration, etc.)
- Core Platform (authentication, data management, messaging, etc.)
- External Integrations (business systems, regulatory systems, etc.)
"""

from .metrics_aggregator import (
    MetricsAggregator,
    MetricPoint,
    AggregatedMetric,
    MetricSource,
    MetricCollector,
    ServiceRole,
    MetricType,
    AggregationMethod,
    SIMetricsCollector,
    HealthMonitorCollector,
    metrics_aggregator,
    setup_metrics_aggregation,
    shutdown_metrics_aggregation
)

from .health_orchestrator import (
    HealthOrchestrator,
    HealthCheck,
    HealthResult,
    ServiceHealth,
    HealthStatus,
    CheckType,
    CheckPriority,
    health_orchestrator,
    check_service_connectivity,
    check_database_connectivity,
    check_memory_usage,
    setup_default_health_checks,
    shutdown_health_orchestration
)

from .alert_manager import (
    AlertManager,
    Alert,
    AlertRule,
    EscalationPolicy,
    NotificationTemplate,
    NotificationEndpoint,
    AlertSeverity,
    AlertStatus,
    NotificationChannel,
    EscalationLevel,
    AlertCorrelationEngine,
    alert_manager,
    setup_default_alert_rules,
    shutdown_alert_management
)

from .trace_collector import (
    TraceCollector,
    Span,
    Trace,
    SpanContext,
    SamplingRule,
    SpanKind,
    SpanStatus,
    trace_collector,
    trace_function,
    setup_default_sampling_rules,
    shutdown_trace_collection
)

from .log_aggregator import (
    LogAggregator,
    LogEntry,
    LogPattern,
    LogMetric,
    LogAlert,
    LogLevel,
    LogFormat,
    PlatformLogHandler,
    log_aggregator,
    setup_default_log_patterns,
    shutdown_log_aggregation
)

# Global instances for easy access
__all__ = [
    # Metrics Aggregation
    'MetricsAggregator',
    'MetricPoint',
    'AggregatedMetric',
    'MetricSource',
    'MetricCollector',
    'ServiceRole',
    'MetricType',
    'AggregationMethod',
    'SIMetricsCollector',
    'HealthMonitorCollector',
    'metrics_aggregator',
    'setup_metrics_aggregation',
    'shutdown_metrics_aggregation',
    
    # Health Orchestration
    'HealthOrchestrator',
    'HealthCheck',
    'HealthResult',
    'ServiceHealth',
    'HealthStatus',
    'CheckType',
    'CheckPriority',
    'health_orchestrator',
    'check_service_connectivity',
    'check_database_connectivity',
    'check_memory_usage',
    'setup_default_health_checks',
    'shutdown_health_orchestration',
    
    # Alert Management
    'AlertManager',
    'Alert',
    'AlertRule',
    'EscalationPolicy',
    'NotificationTemplate',
    'NotificationEndpoint',
    'AlertSeverity',
    'AlertStatus',
    'NotificationChannel',
    'EscalationLevel',
    'AlertCorrelationEngine',
    'alert_manager',
    'setup_default_alert_rules',
    'shutdown_alert_management',
    
    # Distributed Tracing
    'TraceCollector',
    'Span',
    'Trace',
    'SpanContext',
    'SamplingRule',
    'SpanKind',
    'SpanStatus',
    'trace_collector',
    'trace_function',
    'setup_default_sampling_rules',
    'shutdown_trace_collection',
    
    # Log Aggregation
    'LogAggregator',
    'LogEntry',
    'LogPattern',
    'LogMetric',
    'LogAlert',
    'LogLevel',
    'LogFormat',
    'PlatformLogHandler',
    'log_aggregator',
    'setup_default_log_patterns',
    'shutdown_log_aggregation',
    
    # Convenience functions
    'setup_platform_observability',
    'shutdown_platform_observability',
    'get_platform_observability_health'
]


# Convenience functions for platform-wide observability management
async def setup_platform_observability():
    """
    Setup complete platform observability system.
    
    Initializes all observability components:
    - Metrics aggregation
    - Health orchestration  
    - Alert management
    - Distributed tracing
    - Log aggregation
    
    Also sets up default rules, patterns, and configurations.
    """
    # Setup metrics aggregation
    await setup_metrics_aggregation()
    
    # Setup health orchestration
    await setup_default_health_checks()
    await health_orchestrator.start_orchestration()
    
    # Setup alert management
    await setup_default_alert_rules()
    await alert_manager.start_alert_processing()
    
    # Setup distributed tracing
    await setup_default_sampling_rules()
    await trace_collector.start_trace_processing()
    
    # Setup log aggregation
    await setup_default_log_patterns()
    await log_aggregator.start_log_processing()
    
    # Wire dependencies
    _setup_component_dependencies()
    
    print("✅ TaxPoynt Platform Observability System initialized successfully!")
    print("📊 Metrics Aggregation: Active")
    print("🔍 Health Orchestration: Active") 
    print("🚨 Alert Management: Active")
    print("🔗 Distributed Tracing: Active")
    print("📝 Log Aggregation: Active")


async def shutdown_platform_observability():
    """
    Shutdown complete platform observability system.
    
    Gracefully shuts down all observability components and cleans up resources.
    """
    # Shutdown in reverse order
    await shutdown_log_aggregation()
    await shutdown_trace_collection()
    await shutdown_alert_management()
    await shutdown_health_orchestration()
    await shutdown_metrics_aggregation()
    
    print("✅ TaxPoynt Platform Observability System shutdown completed!")


def get_platform_observability_health() -> dict:
    """
    Get comprehensive health status of the observability platform.
    
    Returns:
        dict: Health status of all observability components
    """
    return {
        "timestamp": metrics_aggregator.collection_stats.get("last_collection"),
        "components": {
            "metrics_aggregator": metrics_aggregator.get_aggregator_health(),
            "health_orchestrator": health_orchestrator.get_orchestrator_health(),
            "alert_manager": alert_manager.get_alert_manager_health(),
            "trace_collector": trace_collector.get_trace_collector_health(),
            "log_aggregator": log_aggregator.get_log_aggregator_health()
        },
        "overall_status": _calculate_overall_observability_health()
    }


def _setup_component_dependencies():
    """Setup dependencies between observability components"""
    # Inject metrics aggregator into other components
    health_orchestrator.set_metrics_aggregator(metrics_aggregator)
    alert_manager.set_metrics_aggregator(metrics_aggregator)
    trace_collector.set_metrics_aggregator(metrics_aggregator)
    log_aggregator.set_metrics_aggregator(metrics_aggregator)
    
    # Inject alert manager into other components
    health_orchestrator.set_alert_manager(alert_manager)
    log_aggregator.set_alert_manager(alert_manager)
    
    # Inject trace collector into log aggregator
    log_aggregator.set_trace_collector(trace_collector)
    
    # Setup cross-component event handlers
    _setup_cross_component_handlers()


def _setup_cross_component_handlers():
    """Setup event handlers between components"""
    # Health orchestrator -> Alert manager
    async def health_failure_handler(health_check, result):
        if result.status in ['critical', 'warning']:
            await alert_manager.trigger_alert({
                "title": f"Health Check Failed: {health_check.name}",
                "description": result.message,
                "service_name": health_check.service_name,
                "service_role": health_check.service_role,
                "severity": "critical" if result.status == "critical" else "warning",
                "source": "health_orchestrator",
                "check_id": health_check.check_id,
                "timestamp": result.timestamp
            })
    
    health_orchestrator.add_check_failure_handler(health_failure_handler)
    
    # Trace collector -> Metrics aggregator (additional metrics)
    async def trace_metrics_handler(trace):
        if trace.error_count > 0:
            await metrics_aggregator.collect_metric_point(
                name="trace_errors_total",
                value=trace.error_count,
                service_role="cross_platform",
                service_name="distributed_tracing",
                tags={"trace_id": trace.trace_id}
            )
    
    trace_collector.add_trace_finished_handler(trace_metrics_handler)
    
    # Log aggregator -> Alert manager (critical logs)
    async def critical_log_handler(log_entry):
        if log_entry.level.value == "critical":
            await alert_manager.trigger_alert({
                "title": f"Critical Log: {log_entry.service_name}",
                "description": log_entry.message,
                "service_name": log_entry.service_name,
                "service_role": log_entry.service_role,
                "severity": "critical",
                "source": "log_aggregator",
                "log_id": log_entry.log_id,
                "timestamp": log_entry.timestamp
            })
    
    log_aggregator.add_log_received_handler(critical_log_handler)


def _calculate_overall_observability_health() -> str:
    """Calculate overall health of the observability system"""
    try:
        # Get health from all components
        components_health = [
            metrics_aggregator.get_aggregator_health()["status"],
            health_orchestrator.get_orchestrator_health()["status"],
            alert_manager.get_alert_manager_health()["status"],
            trace_collector.get_trace_collector_health()["status"],
            log_aggregator.get_log_aggregator_health()["status"]
        ]
        
        # Count healthy components
        healthy_count = sum(1 for status in components_health if status in ["healthy", "running"])
        total_count = len(components_health)
        
        if healthy_count == total_count:
            return "healthy"
        elif healthy_count >= total_count * 0.8:  # 80% healthy
            return "degraded"
        else:
            return "critical"
            
    except Exception:
        return "unknown"


# Service role mapping for easy access
SERVICE_ROLES = {
    "si_services": ServiceRole.SI_SERVICES,
    "app_services": ServiceRole.APP_SERVICES,
    "hybrid_services": ServiceRole.HYBRID_SERVICES,
    "core_platform": ServiceRole.CORE_PLATFORM,
    "external_integrations": ServiceRole.EXTERNAL_INTEGRATIONS
}

# Common metric types for easy access
METRIC_TYPES = {
    "counter": MetricType.COUNTER,
    "gauge": MetricType.GAUGE,
    "histogram": MetricType.HISTOGRAM,
    "timer": MetricType.TIMER,
    "distribution": MetricType.DISTRIBUTION
}

# Common log levels for easy access  
LOG_LEVELS = {
    "trace": LogLevel.TRACE,
    "debug": LogLevel.DEBUG,
    "info": LogLevel.INFO,
    "warning": LogLevel.WARNING,
    "error": LogLevel.ERROR,
    "critical": LogLevel.CRITICAL
}

# Alert severities for easy access
ALERT_SEVERITIES = {
    "info": AlertSeverity.INFO,
    "warning": AlertSeverity.WARNING,
    "error": AlertSeverity.ERROR,
    "critical": AlertSeverity.CRITICAL
}

# Health statuses for easy access
HEALTH_STATUSES = {
    "healthy": HealthStatus.HEALTHY,
    "warning": HealthStatus.WARNING,
    "critical": HealthStatus.CRITICAL,
    "unknown": HealthStatus.UNKNOWN,
    "maintenance": HealthStatus.MAINTENANCE
}

# Check types for easy access
CHECK_TYPES = {
    "connectivity": CheckType.CONNECTIVITY,
    "performance": CheckType.PERFORMANCE,
    "resource": CheckType.RESOURCE,
    "dependency": CheckType.DEPENDENCY,
    "functional": CheckType.FUNCTIONAL,
    "security": CheckType.SECURITY
}

# Span kinds for easy access
SPAN_KINDS = {
    "server": SpanKind.SERVER,
    "client": SpanKind.CLIENT,
    "producer": SpanKind.PRODUCER,
    "consumer": SpanKind.CONSUMER,
    "internal": SpanKind.INTERNAL
}