"""
Data Synchronization Hybrid Services Package

This package provides cross-role data synchronization services for the TaxPoynt platform,
ensuring data consistency and conflict resolution between SI and APP roles.

Components:
- StateSync: Synchronizes state between SI and APP roles
- CacheCoordinator: Coordinates caching across different roles and levels
- ConsistencyManager: Ensures data consistency across the platform
- ConflictResolver: Resolves data conflicts in distributed synchronization
- SyncMonitor: Monitors synchronization health and performance
"""

from .state_synchronizer import (
    StateSynchronizer,
    SyncStrategy,
    SyncScope,
    SyncPriority,
    StateData,
    SyncRequest,
    SyncResult,
    SyncSession,
    create_state_synchronizer
)

from .cache_coordinator import (
    CacheCoordinator,
    CacheLevel,
    CacheStrategy,
    CacheOperation,
    CacheEntry,
    CachePolicy,
    create_cache_coordinator
)

from .consistency_manager import (
    ConsistencyManager,
    ConsistencyLevel,
    ConsistencyScope,
    ViolationType,
    ViolationSeverity,
    ResolutionStrategy,
    ConsistencyRule,
    DataSnapshot,
    ConsistencyViolation,
    ConsistencyCheck,
    create_consistency_manager
)

from .conflict_resolver import (
    ConflictResolver,
    ConflictType,
    ConflictSeverity,
    ResolutionMethod,
    ConflictStatus,
    ResolutionOutcome,
    ConflictData,
    Conflict,
    ConflictResolution,
    ConflictRule,
    MergeStrategy,
    create_conflict_resolver
)

from .sync_monitor import (
    SyncMonitor,
    SyncStatus,
    SyncIssueType,
    AlertSeverity,
    HealthLevel,
    SyncMetrics,
    SyncHealth,
    SyncAlert,
    SyncThreshold,
    create_sync_monitor
)

__all__ = [
    # State Synchronizer
    "StateSynchronizer",
    "SyncStrategy",
    "SyncScope", 
    "SyncPriority",
    "StateData",
    "SyncRequest",
    "SyncResult",
    "SyncSession",
    "create_state_synchronizer",
    
    # Cache Coordinator
    "CacheCoordinator",
    "CacheLevel",
    "CacheStrategy",
    "CacheOperation", 
    "CacheEntry",
    "CachePolicy",
    "create_cache_coordinator",
    
    # Consistency Manager
    "ConsistencyManager",
    "ConsistencyLevel",
    "ConsistencyScope",
    "ViolationType",
    "ViolationSeverity",
    "ResolutionStrategy",
    "ConsistencyRule",
    "DataSnapshot",
    "ConsistencyViolation",
    "ConsistencyCheck",
    "create_consistency_manager",
    
    # Conflict Resolver
    "ConflictResolver",
    "ConflictType",
    "ConflictSeverity",
    "ResolutionMethod",
    "ConflictStatus",
    "ResolutionOutcome",
    "ConflictData",
    "Conflict",
    "ConflictResolution",
    "ConflictRule",
    "MergeStrategy",
    "create_conflict_resolver",
    
    # Sync Monitor
    "SyncMonitor",
    "SyncStatus",
    "SyncIssueType",
    "AlertSeverity",
    "HealthLevel",
    "SyncMetrics",
    "SyncHealth",
    "SyncAlert",
    "SyncThreshold",
    "create_sync_monitor"
]

# Package version
__version__ = "1.0.0"

# Package metadata
__author__ = "TaxPoynt Platform Team"
__description__ = "Cross-role data synchronization services for TaxPoynt platform"
__license__ = "Proprietary"


# Convenience factory function to create all services
def create_data_synchronization_services():
    """
    Create all data synchronization services as a unified suite
    
    Returns:
        Dict containing all initialized services
    """
    return {
        "state_synchronizer": create_state_synchronizer(),
        "cache_coordinator": create_cache_coordinator(),
        "consistency_manager": create_consistency_manager(),
        "conflict_resolver": create_conflict_resolver(),
        "sync_monitor": create_sync_monitor()
    }


# Service initialization helper
async def initialize_data_synchronization_services(services: dict = None):
    """
    Initialize all data synchronization services
    
    Args:
        services: Optional dict of services to initialize. If None, creates all services.
    """
    if services is None:
        services = create_data_synchronization_services()
    
    # Initialize services in dependency order
    initialization_order = [
        "cache_coordinator",    # Base caching infrastructure
        "sync_monitor",        # Monitoring before sync operations
        "consistency_manager", # Consistency checking
        "conflict_resolver",   # Conflict resolution
        "state_synchronizer"   # Main synchronization
    ]
    
    for service_name in initialization_order:
        if service_name in services:
            await services[service_name].initialize()
    
    return services


# Service cleanup helper
async def cleanup_data_synchronization_services(services: dict):
    """
    Cleanup all data synchronization services
    
    Args:
        services: Dict of services to cleanup
    """
    # Cleanup in reverse dependency order
    cleanup_order = [
        "state_synchronizer",
        "conflict_resolver", 
        "consistency_manager",
        "sync_monitor",
        "cache_coordinator"
    ]
    
    for service_name in cleanup_order:
        if service_name in services:
            await services[service_name].cleanup()


# Health check aggregator
async def get_data_synchronization_health(services: dict):
    """
    Get aggregated health status for all data synchronization services
    
    Args:
        services: Dict of services to check
        
    Returns:
        Dict containing overall health status
    """
    health_results = {}
    overall_status = "healthy"
    
    for service_name, service in services.items():
        try:
            health = await service.health_check()
            health_results[service_name] = health
            
            # Determine overall status (worst status wins)
            if health.get("status") == "error":
                overall_status = "error"
            elif health.get("status") == "degraded" and overall_status != "error":
                overall_status = "degraded"
                
        except Exception as e:
            health_results[service_name] = {
                "status": "error",
                "error": str(e)
            }
            overall_status = "error"
    
    return {
        "overall_status": overall_status,
        "services": health_results,
        "timestamp": f"{__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat()}"
    }