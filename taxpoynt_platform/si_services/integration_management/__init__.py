"""
Integration Management Module

Comprehensive integration management for TaxPoynt SI services.
Provides connection management, authentication coordination, sync orchestration,
health monitoring, and failover management.
"""

from .connection_manager import (
    ConnectionManager,
    ConnectionConfig,
    ConnectionStatus,
    ConnectionState,
    SystemType,
    connection_manager,
    register_system,
    get_connection,
    test_system_connection
)

from .auth_coordinator import (
    AuthCoordinator,
    AuthCredentials,
    AuthToken,
    AuthStatus,
    AuthMethod,
    AuthState,
    OAuthHandler,
    auth_coordinator,
    register_system_credentials,
    authenticate_system,
    get_system_auth_token
)

from .sync_orchestrator import (
    SyncOrchestrator,
    SyncConfiguration,
    SyncExecution,
    SyncMapping,
    SyncFilter,
    SyncDirection,
    SyncStatus,
    ConflictResolution,
    SyncPriority,
    sync_orchestrator,
    register_sync_configuration,
    execute_synchronization
)

from .integration_health_monitor import (
    IntegrationHealthMonitor,
    HealthStatus,
    AlertSeverity,
    HealthThreshold,
    HealthMetric,
    Alert,
    integration_health_monitor
)

from .config_manager import (
    ConfigManager,
    config_manager
)

from .connection_tester import (
    ConnectionTester,
    connection_tester
)

from .metrics_collector import (
    MetricsCollector,
    metrics_collector
)

from .lifecycle_manager import (
    LifecycleManager,
    lifecycle_manager
)

from .dependency_injector import (
    IntegrationDependencyInjector,
    dependency_injector,
    configure_integration_dependencies,
    get_dependency_status,
    validate_dependencies
)

from .failover_manager import (
    FailoverManager,
    FailoverConfig,
    FailoverTarget,
    CircuitBreakerConfig,
    SystemStatus as FailoverSystemStatus,
    FailoverState,
    CircuitState,
    FailoverStrategy,
    RecoveryStrategy,
    failover_manager,
    register_system_failover,
    execute_with_system_failover,
    NoAvailableTargetsError,
    FailoverExhaustedException
)

__all__ = [
    # Connection Manager
    "ConnectionManager",
    "ConnectionConfig", 
    "ConnectionStatus",
    "ConnectionState",
    "SystemType",
    "connection_manager",
    "register_system",
    "get_connection",
    "test_system_connection",
    
    # Auth Coordinator
    "AuthCoordinator",
    "AuthCredentials",
    "AuthToken",
    "AuthStatus", 
    "AuthMethod",
    "AuthState",
    "OAuthHandler",
    "auth_coordinator",
    "register_system_credentials",
    "authenticate_system",
    "get_system_auth_token",
    
    # Sync Orchestrator
    "SyncOrchestrator",
    "SyncConfiguration",
    "SyncExecution",
    "SyncMapping",
    "SyncFilter",
    "SyncDirection",
    "SyncStatus",
    "ConflictResolution",
    "SyncPriority",
    "sync_orchestrator",
    "register_sync_configuration", 
    "execute_synchronization",
    
    # Integration Health Monitor
    "IntegrationHealthMonitor",
    "HealthStatus",
    "AlertSeverity",
    "HealthThreshold",
    "HealthMetric",
    "Alert",
    "integration_health_monitor",
    
    # Config Manager
    "ConfigManager",
    "config_manager",
    
    # Connection Tester
    "ConnectionTester", 
    "connection_tester",
    
    # Metrics Collector
    "MetricsCollector",
    "metrics_collector",
    
    # Lifecycle Manager
    "LifecycleManager",
    "lifecycle_manager",
    
    # Dependency Injector
    "IntegrationDependencyInjector",
    "dependency_injector", 
    "configure_integration_dependencies",
    "get_dependency_status",
    "validate_dependencies",
    
    # Failover Manager
    "FailoverManager",
    "FailoverConfig",
    "FailoverTarget",
    "CircuitBreakerConfig",
    "FailoverSystemStatus",
    "FailoverState",
    "CircuitState", 
    "FailoverStrategy",
    "RecoveryStrategy",
    "failover_manager",
    "register_system_failover",
    "execute_with_system_failover",
    "NoAvailableTargetsError",
    "FailoverExhaustedException"
]