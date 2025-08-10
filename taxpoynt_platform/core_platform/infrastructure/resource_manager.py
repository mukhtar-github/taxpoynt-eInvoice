"""
Resource Manager - Core Platform Infrastructure
Comprehensive compute resource management system for the TaxPoynt platform.
Manages resource allocation, provisioning, monitoring, and optimization across all services.
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import psutil
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class ResourceType(Enum):
    CPU = "cpu"
    MEMORY = "memory"
    STORAGE = "storage"
    NETWORK = "network"
    GPU = "gpu"
    DATABASE = "database"
    CACHE = "cache"
    QUEUE = "queue"

class ResourceStatus(Enum):
    AVAILABLE = "available"
    ALLOCATED = "allocated"
    RESERVED = "reserved"
    OVERCOMMITTED = "overcommitted"
    FAILED = "failed"
    MAINTENANCE = "maintenance"

class ResourcePriority(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"
    BACKGROUND = "background"

class ServiceTier(Enum):
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"
    SCALE = "scale"

@dataclass
class ResourceQuota:
    resource_type: ResourceType
    limit: float
    used: float = 0.0
    reserved: float = 0.0
    unit: str = "units"
    soft_limit: Optional[float] = None
    burst_limit: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ResourceAllocation:
    id: str
    tenant_id: str
    service_id: str
    resource_type: ResourceType
    amount: float
    priority: ResourcePriority
    status: ResourceStatus
    allocated_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    tags: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ResourceNode:
    id: str
    name: str
    node_type: str
    region: str
    zone: str
    capacity: Dict[ResourceType, float]
    allocated: Dict[ResourceType, float] = field(default_factory=dict)
    reserved: Dict[ResourceType, float] = field(default_factory=dict)
    status: ResourceStatus = ResourceStatus.AVAILABLE
    labels: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    last_heartbeat: datetime = field(default_factory=datetime.utcnow)

@dataclass
class ResourcePolicy:
    id: str
    name: str
    tenant_id: Optional[str]
    service_type: Optional[str]
    tier: Optional[ServiceTier]
    quotas: Dict[ResourceType, ResourceQuota]
    priority: ResourcePriority
    auto_scaling: bool = True
    burst_allowed: bool = False
    preemptible: bool = False
    affinity_rules: List[str] = field(default_factory=list)
    anti_affinity_rules: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ResourceMetrics:
    timestamp: datetime
    node_id: str
    resource_type: ResourceType
    utilization: float
    available: float
    allocated: float
    reserved: float
    peak_utilization: float = 0.0
    avg_utilization: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

class ResourceProvider(ABC):
    @abstractmethod
    async def provision_resource(self, allocation: ResourceAllocation) -> bool:
        pass
    
    @abstractmethod
    async def deallocate_resource(self, allocation_id: str) -> bool:
        pass
    
    @abstractmethod
    async def get_resource_metrics(self, node_id: str) -> Dict[ResourceType, ResourceMetrics]:
        pass
    
    @abstractmethod
    async def scale_resource(self, allocation_id: str, new_amount: float) -> bool:
        pass

class ComputeProvider(ResourceProvider):
    async def provision_resource(self, allocation: ResourceAllocation) -> bool:
        try:
            if allocation.resource_type == ResourceType.CPU:
                return await self._provision_cpu(allocation)
            elif allocation.resource_type == ResourceType.MEMORY:
                return await self._provision_memory(allocation)
            else:
                logger.warning(f"Unsupported resource type: {allocation.resource_type}")
                return False
        except Exception as e:
            logger.error(f"Failed to provision compute resource: {e}")
            return False
    
    async def _provision_cpu(self, allocation: ResourceAllocation) -> bool:
        # Simulate CPU allocation
        logger.info(f"Provisioning {allocation.amount} CPU cores for {allocation.service_id}")
        # In real implementation, this would interact with container orchestrator
        return True
    
    async def _provision_memory(self, allocation: ResourceAllocation) -> bool:
        # Simulate memory allocation
        logger.info(f"Provisioning {allocation.amount}GB memory for {allocation.service_id}")
        # In real implementation, this would set memory limits
        return True
    
    async def deallocate_resource(self, allocation_id: str) -> bool:
        # Simulate resource deallocation
        logger.info(f"Deallocating resource: {allocation_id}")
        return True
    
    async def get_resource_metrics(self, node_id: str) -> Dict[ResourceType, ResourceMetrics]:
        # Get actual system metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        
        metrics = {
            ResourceType.CPU: ResourceMetrics(
                timestamp=datetime.utcnow(),
                node_id=node_id,
                resource_type=ResourceType.CPU,
                utilization=cpu_percent,
                available=100 - cpu_percent,
                allocated=cpu_percent,
                reserved=0.0
            ),
            ResourceType.MEMORY: ResourceMetrics(
                timestamp=datetime.utcnow(),
                node_id=node_id,
                resource_type=ResourceType.MEMORY,
                utilization=memory.percent,
                available=memory.available / (1024**3),  # GB
                allocated=memory.used / (1024**3),  # GB
                reserved=0.0
            )
        }
        
        return metrics
    
    async def scale_resource(self, allocation_id: str, new_amount: float) -> bool:
        logger.info(f"Scaling resource {allocation_id} to {new_amount}")
        return True

class DatabaseProvider(ResourceProvider):
    async def provision_resource(self, allocation: ResourceAllocation) -> bool:
        try:
            logger.info(f"Provisioning database resource for {allocation.service_id}")
            # Database provisioning logic would go here
            return True
        except Exception as e:
            logger.error(f"Failed to provision database resource: {e}")
            return False
    
    async def deallocate_resource(self, allocation_id: str) -> bool:
        logger.info(f"Deallocating database resource: {allocation_id}")
        return True
    
    async def get_resource_metrics(self, node_id: str) -> Dict[ResourceType, ResourceMetrics]:
        # Database metrics collection
        return {
            ResourceType.DATABASE: ResourceMetrics(
                timestamp=datetime.utcnow(),
                node_id=node_id,
                resource_type=ResourceType.DATABASE,
                utilization=75.0,  # Simulated
                available=25.0,
                allocated=75.0,
                reserved=0.0
            )
        }
    
    async def scale_resource(self, allocation_id: str, new_amount: float) -> bool:
        logger.info(f"Scaling database resource {allocation_id} to {new_amount}")
        return True

class CacheProvider(ResourceProvider):
    async def provision_resource(self, allocation: ResourceAllocation) -> bool:
        try:
            logger.info(f"Provisioning cache resource for {allocation.service_id}")
            # Cache provisioning logic would go here
            return True
        except Exception as e:
            logger.error(f"Failed to provision cache resource: {e}")
            return False
    
    async def deallocate_resource(self, allocation_id: str) -> bool:
        logger.info(f"Deallocating cache resource: {allocation_id}")
        return True
    
    async def get_resource_metrics(self, node_id: str) -> Dict[ResourceType, ResourceMetrics]:
        return {
            ResourceType.CACHE: ResourceMetrics(
                timestamp=datetime.utcnow(),
                node_id=node_id,
                resource_type=ResourceType.CACHE,
                utilization=60.0,  # Simulated
                available=40.0,
                allocated=60.0,
                reserved=0.0
            )
        }
    
    async def scale_resource(self, allocation_id: str, new_amount: float) -> bool:
        logger.info(f"Scaling cache resource {allocation_id} to {new_amount}")
        return True

class ResourceManager:
    def __init__(self):
        self.nodes: Dict[str, ResourceNode] = {}
        self.allocations: Dict[str, ResourceAllocation] = {}
        self.policies: Dict[str, ResourcePolicy] = {}
        self.providers: Dict[ResourceType, ResourceProvider] = {}
        self.quotas: Dict[str, Dict[ResourceType, ResourceQuota]] = {}
        self.metrics_history: List[ResourceMetrics] = []
        
        # Initialize providers
        self._initialize_providers()
        
        # Load default policies
        self._load_default_policies()
        
        # Initialize nodes
        self._initialize_nodes()
    
    def _initialize_providers(self):
        """Initialize resource providers"""
        self.providers = {
            ResourceType.CPU: ComputeProvider(),
            ResourceType.MEMORY: ComputeProvider(),
            ResourceType.DATABASE: DatabaseProvider(),
            ResourceType.CACHE: CacheProvider()
        }
    
    def _load_default_policies(self):
        """Load default resource policies for different service tiers"""
        default_policies = [
            ResourcePolicy(
                id="starter_policy",
                name="Starter Tier Policy",
                tier=ServiceTier.STARTER,
                quotas={
                    ResourceType.CPU: ResourceQuota(ResourceType.CPU, 2.0, unit="cores"),
                    ResourceType.MEMORY: ResourceQuota(ResourceType.MEMORY, 4.0, unit="GB"),
                    ResourceType.STORAGE: ResourceQuota(ResourceType.STORAGE, 20.0, unit="GB"),
                    ResourceType.DATABASE: ResourceQuota(ResourceType.DATABASE, 1.0, unit="instances")
                },
                priority=ResourcePriority.NORMAL,
                auto_scaling=False,
                burst_allowed=False
            ),
            ResourcePolicy(
                id="professional_policy",
                name="Professional Tier Policy",
                tier=ServiceTier.PROFESSIONAL,
                quotas={
                    ResourceType.CPU: ResourceQuota(ResourceType.CPU, 8.0, unit="cores", burst_limit=12.0),
                    ResourceType.MEMORY: ResourceQuota(ResourceType.MEMORY, 16.0, unit="GB", burst_limit=24.0),
                    ResourceType.STORAGE: ResourceQuota(ResourceType.STORAGE, 100.0, unit="GB"),
                    ResourceType.DATABASE: ResourceQuota(ResourceType.DATABASE, 2.0, unit="instances")
                },
                priority=ResourcePriority.HIGH,
                auto_scaling=True,
                burst_allowed=True
            ),
            ResourcePolicy(
                id="enterprise_policy",
                name="Enterprise Tier Policy",
                tier=ServiceTier.ENTERPRISE,
                quotas={
                    ResourceType.CPU: ResourceQuota(ResourceType.CPU, 32.0, unit="cores", burst_limit=48.0),
                    ResourceType.MEMORY: ResourceQuota(ResourceType.MEMORY, 64.0, unit="GB", burst_limit=96.0),
                    ResourceType.STORAGE: ResourceQuota(ResourceType.STORAGE, 500.0, unit="GB"),
                    ResourceType.DATABASE: ResourceQuota(ResourceType.DATABASE, 5.0, unit="instances")
                },
                priority=ResourcePriority.CRITICAL,
                auto_scaling=True,
                burst_allowed=True
            ),
            ResourcePolicy(
                id="scale_policy",
                name="Scale Tier Policy",
                tier=ServiceTier.SCALE,
                quotas={
                    ResourceType.CPU: ResourceQuota(ResourceType.CPU, 128.0, unit="cores", burst_limit=256.0),
                    ResourceType.MEMORY: ResourceQuota(ResourceType.MEMORY, 512.0, unit="GB", burst_limit=1024.0),
                    ResourceType.STORAGE: ResourceQuota(ResourceType.STORAGE, 2000.0, unit="GB"),
                    ResourceType.DATABASE: ResourceQuota(ResourceType.DATABASE, 20.0, unit="instances")
                },
                priority=ResourcePriority.CRITICAL,
                auto_scaling=True,
                burst_allowed=True
            )
        ]
        
        for policy in default_policies:
            self.policies[policy.id] = policy
    
    def _initialize_nodes(self):
        """Initialize resource nodes"""
        # Default local node
        local_node = ResourceNode(
            id="local_node_001",
            name="Local Development Node",
            node_type="development",
            region="local",
            zone="dev-zone-1",
            capacity={
                ResourceType.CPU: 16.0,
                ResourceType.MEMORY: 32.0,
                ResourceType.STORAGE: 1000.0,
                ResourceType.DATABASE: 10.0,
                ResourceType.CACHE: 8.0
            },
            labels={
                "environment": "development",
                "tier": "local"
            }
        )
        
        self.nodes[local_node.id] = local_node
    
    async def allocate_resource(self, tenant_id: str, service_id: str, resource_type: ResourceType, 
                              amount: float, priority: ResourcePriority = ResourcePriority.NORMAL,
                              metadata: Optional[Dict[str, Any]] = None) -> Optional[ResourceAllocation]:
        """Allocate a resource for a service"""
        try:
            # Check quotas
            if not await self._check_quota(tenant_id, resource_type, amount):
                logger.warning(f"Quota exceeded for tenant {tenant_id}, resource {resource_type.value}")
                return None
            
            # Find available node
            node = await self._find_available_node(resource_type, amount, priority)
            if not node:
                logger.warning(f"No available node for resource {resource_type.value}, amount {amount}")
                return None
            
            # Create allocation
            allocation_id = f"alloc_{int(time.time())}_{tenant_id}_{service_id}"
            allocation = ResourceAllocation(
                id=allocation_id,
                tenant_id=tenant_id,
                service_id=service_id,
                resource_type=resource_type,
                amount=amount,
                priority=priority,
                status=ResourceStatus.ALLOCATED,
                metadata=metadata or {}
            )
            
            # Provision resource
            if resource_type in self.providers:
                provider = self.providers[resource_type]
                if await provider.provision_resource(allocation):
                    # Update node allocation
                    if resource_type not in node.allocated:
                        node.allocated[resource_type] = 0.0
                    node.allocated[resource_type] += amount
                    
                    # Update quota usage
                    await self._update_quota_usage(tenant_id, resource_type, amount)
                    
                    # Store allocation
                    self.allocations[allocation_id] = allocation
                    
                    logger.info(f"Allocated resource: {allocation_id}")
                    return allocation
                else:
                    logger.error(f"Failed to provision resource: {allocation_id}")
                    return None
            else:
                logger.error(f"No provider for resource type: {resource_type.value}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to allocate resource: {e}")
            return None
    
    async def deallocate_resource(self, allocation_id: str) -> bool:
        """Deallocate a resource"""
        try:
            if allocation_id not in self.allocations:
                logger.warning(f"Allocation not found: {allocation_id}")
                return False
            
            allocation = self.allocations[allocation_id]
            
            # Deallocate from provider
            if allocation.resource_type in self.providers:
                provider = self.providers[allocation.resource_type]
                if await provider.deallocate_resource(allocation_id):
                    # Update node allocation
                    for node in self.nodes.values():
                        if allocation.resource_type in node.allocated:
                            if node.allocated[allocation.resource_type] >= allocation.amount:
                                node.allocated[allocation.resource_type] -= allocation.amount
                                break
                    
                    # Update quota usage
                    await self._update_quota_usage(allocation.tenant_id, allocation.resource_type, -allocation.amount)
                    
                    # Remove allocation
                    del self.allocations[allocation_id]
                    
                    logger.info(f"Deallocated resource: {allocation_id}")
                    return True
                else:
                    logger.error(f"Failed to deallocate resource: {allocation_id}")
                    return False
            else:
                logger.error(f"No provider for resource type: {allocation.resource_type.value}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to deallocate resource: {e}")
            return False
    
    async def _check_quota(self, tenant_id: str, resource_type: ResourceType, amount: float) -> bool:
        """Check if allocation would exceed quota"""
        try:
            if tenant_id not in self.quotas:
                # Get default quota based on tenant tier
                await self._initialize_tenant_quotas(tenant_id)
            
            tenant_quotas = self.quotas.get(tenant_id, {})
            if resource_type in tenant_quotas:
                quota = tenant_quotas[resource_type]
                if quota.used + amount > quota.limit:
                    # Check if burst is allowed
                    if quota.burst_limit and quota.used + amount <= quota.burst_limit:
                        return True
                    return False
            
            return True
        except Exception as e:
            logger.error(f"Failed to check quota: {e}")
            return False
    
    async def _initialize_tenant_quotas(self, tenant_id: str):
        """Initialize quotas for a tenant based on their tier"""
        try:
            # In real implementation, this would query tenant service tier
            # For now, use professional tier as default
            policy = self.policies.get("professional_policy")
            if policy:
                self.quotas[tenant_id] = policy.quotas.copy()
        except Exception as e:
            logger.error(f"Failed to initialize tenant quotas: {e}")
    
    async def _find_available_node(self, resource_type: ResourceType, amount: float, 
                                 priority: ResourcePriority) -> Optional[ResourceNode]:
        """Find an available node for resource allocation"""
        try:
            available_nodes = []
            
            for node in self.nodes.values():
                if node.status != ResourceStatus.AVAILABLE:
                    continue
                
                # Check capacity
                if resource_type in node.capacity:
                    allocated = node.allocated.get(resource_type, 0.0)
                    reserved = node.reserved.get(resource_type, 0.0)
                    available = node.capacity[resource_type] - allocated - reserved
                    
                    if available >= amount:
                        available_nodes.append((node, available))
            
            if not available_nodes:
                return None
            
            # Sort by available capacity (descending)
            available_nodes.sort(key=lambda x: x[1], reverse=True)
            
            # Return node with most available capacity
            return available_nodes[0][0]
            
        except Exception as e:
            logger.error(f"Failed to find available node: {e}")
            return None
    
    async def _update_quota_usage(self, tenant_id: str, resource_type: ResourceType, amount: float):
        """Update quota usage for a tenant"""
        try:
            if tenant_id not in self.quotas:
                await self._initialize_tenant_quotas(tenant_id)
            
            if tenant_id in self.quotas and resource_type in self.quotas[tenant_id]:
                quota = self.quotas[tenant_id][resource_type]
                quota.used = max(0.0, quota.used + amount)
                
        except Exception as e:
            logger.error(f"Failed to update quota usage: {e}")
    
    async def get_resource_utilization(self, node_id: Optional[str] = None) -> Dict[str, Any]:
        """Get resource utilization metrics"""
        try:
            utilization_data = {}
            
            nodes_to_check = [self.nodes[node_id]] if node_id and node_id in self.nodes else self.nodes.values()
            
            for node in nodes_to_check:
                node_utilization = {}
                
                for resource_type in node.capacity:
                    capacity = node.capacity[resource_type]
                    allocated = node.allocated.get(resource_type, 0.0)
                    reserved = node.reserved.get(resource_type, 0.0)
                    
                    utilization_percent = ((allocated + reserved) / capacity * 100) if capacity > 0 else 0
                    
                    node_utilization[resource_type.value] = {
                        'capacity': capacity,
                        'allocated': allocated,
                        'reserved': reserved,
                        'available': capacity - allocated - reserved,
                        'utilization_percent': utilization_percent
                    }
                
                utilization_data[node.id] = node_utilization
            
            return utilization_data
        except Exception as e:
            logger.error(f"Failed to get resource utilization: {e}")
            return {}
    
    async def get_tenant_usage(self, tenant_id: str) -> Dict[str, Any]:
        """Get resource usage for a specific tenant"""
        try:
            tenant_allocations = [
                allocation for allocation in self.allocations.values()
                if allocation.tenant_id == tenant_id
            ]
            
            usage_by_type = {}
            for allocation in tenant_allocations:
                resource_type = allocation.resource_type.value
                if resource_type not in usage_by_type:
                    usage_by_type[resource_type] = {
                        'total_allocated': 0.0,
                        'allocations': []
                    }
                
                usage_by_type[resource_type]['total_allocated'] += allocation.amount
                usage_by_type[resource_type]['allocations'].append({
                    'id': allocation.id,
                    'service_id': allocation.service_id,
                    'amount': allocation.amount,
                    'priority': allocation.priority.value,
                    'allocated_at': allocation.allocated_at.isoformat()
                })
            
            # Add quota information
            quotas = self.quotas.get(tenant_id, {})
            quota_info = {}
            for resource_type, quota in quotas.items():
                quota_info[resource_type.value] = {
                    'limit': quota.limit,
                    'used': quota.used,
                    'available': quota.limit - quota.used,
                    'utilization_percent': (quota.used / quota.limit * 100) if quota.limit > 0 else 0
                }
            
            return {
                'tenant_id': tenant_id,
                'usage_by_type': usage_by_type,
                'quotas': quota_info,
                'total_allocations': len(tenant_allocations)
            }
        except Exception as e:
            logger.error(f"Failed to get tenant usage: {e}")
            return {}
    
    async def optimize_resources(self) -> Dict[str, Any]:
        """Optimize resource allocation across nodes"""
        try:
            optimization_results = {
                'recommendations': [],
                'potential_savings': 0.0,
                'efficiency_improvements': []
            }
            
            # Analyze resource utilization
            utilization = await self.get_resource_utilization()
            
            for node_id, node_utilization in utilization.items():
                for resource_type, metrics in node_utilization.items():
                    utilization_percent = metrics['utilization_percent']
                    
                    # Identify underutilized resources
                    if utilization_percent < 20:
                        optimization_results['recommendations'].append({
                            'type': 'consolidation',
                            'node_id': node_id,
                            'resource_type': resource_type,
                            'message': f"Consider consolidating {resource_type} workloads from underutilized node {node_id}"
                        })
                    
                    # Identify overutilized resources
                    elif utilization_percent > 80:
                        optimization_results['recommendations'].append({
                            'type': 'scaling',
                            'node_id': node_id,
                            'resource_type': resource_type,
                            'message': f"Consider scaling out {resource_type} on node {node_id} due to high utilization"
                        })
            
            return optimization_results
        except Exception as e:
            logger.error(f"Failed to optimize resources: {e}")
            return {}
    
    async def start_monitoring(self, interval: int = 60):
        """Start continuous resource monitoring"""
        try:
            logger.info("Starting resource monitoring")
            
            while True:
                # Collect metrics from all nodes
                for node_id in self.nodes:
                    for resource_type, provider in self.providers.items():
                        try:
                            metrics = await provider.get_resource_metrics(node_id)
                            for metric in metrics.values():
                                self.metrics_history.append(metric)
                                
                                # Keep only last 1000 metrics to prevent memory bloat
                                if len(self.metrics_history) > 1000:
                                    self.metrics_history = self.metrics_history[-1000:]
                        except Exception as e:
                            logger.error(f"Failed to collect metrics for {node_id}/{resource_type.value}: {e}")
                
                # Check for optimization opportunities
                await self.optimize_resources()
                
                await asyncio.sleep(interval)
        except Exception as e:
            logger.error(f"Resource monitoring failed: {e}")
    
    def get_allocation_statistics(self) -> Dict[str, Any]:
        """Get resource allocation statistics"""
        try:
            total_allocations = len(self.allocations)
            
            # Allocations by type
            allocations_by_type = {}
            for allocation in self.allocations.values():
                resource_type = allocation.resource_type.value
                if resource_type not in allocations_by_type:
                    allocations_by_type[resource_type] = 0
                allocations_by_type[resource_type] += 1
            
            # Allocations by priority
            allocations_by_priority = {}
            for priority in ResourcePriority:
                allocations_by_priority[priority.value] = len([
                    a for a in self.allocations.values()
                    if a.priority == priority
                ])
            
            # Average allocation age
            now = datetime.utcnow()
            allocation_ages = [
                (now - allocation.allocated_at).total_seconds()
                for allocation in self.allocations.values()
            ]
            avg_age = sum(allocation_ages) / len(allocation_ages) if allocation_ages else 0
            
            return {
                'total_allocations': total_allocations,
                'allocations_by_type': allocations_by_type,
                'allocations_by_priority': allocations_by_priority,
                'average_allocation_age_seconds': avg_age,
                'total_nodes': len(self.nodes),
                'total_policies': len(self.policies)
            }
        except Exception as e:
            logger.error(f"Failed to get allocation statistics: {e}")
            return {}

# Global resource manager instance
resource_manager = ResourceManager()

async def initialize_resource_manager():
    """Initialize the resource manager"""
    try:
        logger.info("Resource manager initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize resource manager: {e}")
        return False

if __name__ == "__main__":
    async def main():
        await initialize_resource_manager()
        
        # Example usage
        allocation = await resource_manager.allocate_resource(
            tenant_id="tenant_001",
            service_id="einvoice_service",
            resource_type=ResourceType.CPU,
            amount=4.0,
            priority=ResourcePriority.HIGH
        )
        
        if allocation:
            print(f"Allocated resource: {allocation.id}")
            
            # Get utilization
            utilization = await resource_manager.get_resource_utilization()
            print(f"Resource utilization: {utilization}")
            
            # Get tenant usage
            usage = await resource_manager.get_tenant_usage("tenant_001")
            print(f"Tenant usage: {usage}")
            
            # Deallocate
            success = await resource_manager.deallocate_resource(allocation.id)
            print(f"Deallocation success: {success}")
    
    asyncio.run(main())