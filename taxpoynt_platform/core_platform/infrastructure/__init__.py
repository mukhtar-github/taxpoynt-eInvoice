"""
Core Platform Infrastructure Package
Comprehensive infrastructure management and orchestration for the TaxPoynt platform.
Provides unified infrastructure management across all platform roles and services.
"""

from .resource_manager import (
    ResourceManager,
    ResourceAllocation,
    ResourceNode,
    ResourcePolicy,
    ResourceQuota,
    ResourceType,
    ResourceStatus,
    ResourcePriority,
    ServiceTier,
    resource_manager,
    initialize_resource_manager
)

from .network_coordinator import (
    NetworkCoordinator,
    NetworkSegment,
    ServiceEndpoint,
    LoadBalancer,
    FirewallRule,
    TrafficPolicy,
    NetworkType,
    NetworkProtocol,
    NetworkStatus,
    LoadBalancingMethod,
    TrafficType,
    network_coordinator,
    initialize_network_coordinator
)

from .storage_orchestrator import (
    StorageOrchestrator,
    StorageVolume,
    BackupPolicy,
    BackupJob,
    LifecycleRule,
    StorageQuota,
    StorageType,
    StorageClass,
    StorageStatus,
    ReplicationStrategy,
    BackupType,
    storage_orchestrator,
    initialize_storage_orchestrator
)

from .deployment_manager import (
    DeploymentManager,
    Deployment,
    DeploymentConfig,
    Environment,
    ServiceSpec,
    DeploymentStrategy,
    DeploymentStatus,
    EnvironmentType,
    ServiceType,
    deployment_manager,
    initialize_deployment_manager
)

from .scaling_controller import (
    ScalingController,
    ScalingPolicy,
    ScalingRule,
    ScalingAction,
    PredictiveModel,
    ScalingDirection,
    ScalingTrigger,
    ScalingStrategy,
    ScalingStatus,
    scaling_controller,
    initialize_scaling_controller
)

__all__ = [
    # Resource Manager
    'ResourceManager',
    'ResourceAllocation',
    'ResourceNode',
    'ResourcePolicy',
    'ResourceQuota',
    'ResourceType',
    'ResourceStatus',
    'ResourcePriority',
    'ServiceTier',
    'resource_manager',
    'initialize_resource_manager',
    
    # Network Coordinator
    'NetworkCoordinator',
    'NetworkSegment',
    'ServiceEndpoint',
    'LoadBalancer',
    'FirewallRule',
    'TrafficPolicy',
    'NetworkType',
    'NetworkProtocol',
    'NetworkStatus',
    'LoadBalancingMethod',
    'TrafficType',
    'network_coordinator',
    'initialize_network_coordinator',
    
    # Storage Orchestrator
    'StorageOrchestrator',
    'StorageVolume',
    'BackupPolicy',
    'BackupJob',
    'LifecycleRule',
    'StorageQuota',
    'StorageType',
    'StorageClass',
    'StorageStatus',
    'ReplicationStrategy',
    'BackupType',
    'storage_orchestrator',
    'initialize_storage_orchestrator',
    
    # Deployment Manager
    'DeploymentManager',
    'Deployment',
    'DeploymentConfig',
    'Environment',
    'ServiceSpec',
    'DeploymentStrategy',
    'DeploymentStatus',
    'EnvironmentType',
    'ServiceType',
    'deployment_manager',
    'initialize_deployment_manager',
    
    # Scaling Controller
    'ScalingController',
    'ScalingPolicy',
    'ScalingRule',
    'ScalingAction',
    'PredictiveModel',
    'ScalingDirection',
    'ScalingTrigger',
    'ScalingStrategy',
    'ScalingStatus',
    'scaling_controller',
    'initialize_scaling_controller'
]

async def initialize_infrastructure_management():
    """
    Initialize all infrastructure management components.
    This function should be called during platform startup.
    """
    success = True
    
    # Initialize resource manager
    if not await initialize_resource_manager():
        success = False
    
    # Initialize network coordinator
    if not await initialize_network_coordinator():
        success = False
    
    # Initialize storage orchestrator
    if not await initialize_storage_orchestrator():
        success = False
    
    # Initialize deployment manager
    if not await initialize_deployment_manager():
        success = False
    
    # Initialize scaling controller
    if not await initialize_scaling_controller():
        success = False
    
    return success