"""
Network Coordinator - Core Platform Infrastructure
Comprehensive network configuration and management system for the TaxPoynt platform.
Manages network topology, routing, security, and connectivity across all services.
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import ipaddress
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class NetworkType(Enum):
    INTERNAL = "internal"
    EXTERNAL = "external"
    MANAGEMENT = "management"
    STORAGE = "storage"
    DATABASE = "database"
    CACHE = "cache"
    API_GATEWAY = "api_gateway"
    SERVICE_MESH = "service_mesh"

class NetworkProtocol(Enum):
    HTTP = "http"
    HTTPS = "https"
    TCP = "tcp"
    UDP = "udp"
    WEBSOCKET = "websocket"
    GRPC = "grpc"
    MQTT = "mqtt"

class TrafficType(Enum):
    NORTH_SOUTH = "north_south"  # Client to service
    EAST_WEST = "east_west"      # Service to service
    MANAGEMENT = "management"    # Administrative traffic
    MONITORING = "monitoring"    # Metrics and logs

class NetworkStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DEGRADED = "degraded"
    MAINTENANCE = "maintenance"
    FAILED = "failed"

class LoadBalancingMethod(Enum):
    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    IP_HASH = "ip_hash"
    LEAST_RESPONSE_TIME = "least_response_time"

@dataclass
class NetworkSegment:
    id: str
    name: str
    network_type: NetworkType
    cidr: str
    vlan_id: Optional[int] = None
    gateway: Optional[str] = None
    dns_servers: List[str] = field(default_factory=list)
    firewall_rules: List[str] = field(default_factory=list)
    status: NetworkStatus = NetworkStatus.ACTIVE
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class ServiceEndpoint:
    id: str
    service_id: str
    host: str
    port: int
    protocol: NetworkProtocol
    health_check_path: Optional[str] = None
    weight: int = 100
    status: NetworkStatus = NetworkStatus.ACTIVE
    metadata: Dict[str, Any] = field(default_factory=dict)
    last_health_check: Optional[datetime] = None

@dataclass
class LoadBalancer:
    id: str
    name: str
    frontend_host: str
    frontend_port: int
    protocol: NetworkProtocol
    method: LoadBalancingMethod
    backends: List[ServiceEndpoint] = field(default_factory=list)
    health_check_interval: int = 30
    timeout: int = 5
    max_retries: int = 3
    ssl_enabled: bool = False
    ssl_cert_path: Optional[str] = None
    status: NetworkStatus = NetworkStatus.ACTIVE
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class FirewallRule:
    id: str
    name: str
    source: str
    destination: str
    port: Optional[int] = None
    protocol: Optional[NetworkProtocol] = None
    action: str = "ALLOW"  # ALLOW, DENY, LOG
    priority: int = 100
    enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class NetworkRoute:
    id: str
    destination: str
    gateway: str
    interface: str
    metric: int = 100
    persistent: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class TrafficPolicy:
    id: str
    name: str
    source_patterns: List[str]
    destination_patterns: List[str]
    traffic_type: TrafficType
    rate_limit: Optional[int] = None  # requests per minute
    bandwidth_limit: Optional[int] = None  # Mbps
    priority: int = 100
    enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class NetworkMetrics:
    timestamp: datetime
    endpoint_id: str
    latency_ms: float
    throughput_mbps: float
    packet_loss_percent: float
    connection_count: int
    error_rate_percent: float
    bandwidth_utilization_percent: float
    metadata: Dict[str, Any] = field(default_factory=dict)

class NetworkProvider(ABC):
    @abstractmethod
    async def create_network_segment(self, segment: NetworkSegment) -> bool:
        pass
    
    @abstractmethod
    async def configure_load_balancer(self, load_balancer: LoadBalancer) -> bool:
        pass
    
    @abstractmethod
    async def apply_firewall_rules(self, rules: List[FirewallRule]) -> bool:
        pass
    
    @abstractmethod
    async def get_network_metrics(self, endpoint_id: str) -> Optional[NetworkMetrics]:
        pass

class CloudNetworkProvider(NetworkProvider):
    async def create_network_segment(self, segment: NetworkSegment) -> bool:
        try:
            logger.info(f"Creating network segment: {segment.name} ({segment.cidr})")
            # Cloud-specific network creation logic
            return True
        except Exception as e:
            logger.error(f"Failed to create network segment: {e}")
            return False
    
    async def configure_load_balancer(self, load_balancer: LoadBalancer) -> bool:
        try:
            logger.info(f"Configuring load balancer: {load_balancer.name}")
            # Cloud load balancer configuration
            return True
        except Exception as e:
            logger.error(f"Failed to configure load balancer: {e}")
            return False
    
    async def apply_firewall_rules(self, rules: List[FirewallRule]) -> bool:
        try:
            logger.info(f"Applying {len(rules)} firewall rules")
            # Cloud firewall rule application
            return True
        except Exception as e:
            logger.error(f"Failed to apply firewall rules: {e}")
            return False
    
    async def get_network_metrics(self, endpoint_id: str) -> Optional[NetworkMetrics]:
        try:
            # Simulate network metrics collection
            return NetworkMetrics(
                timestamp=datetime.utcnow(),
                endpoint_id=endpoint_id,
                latency_ms=25.5,
                throughput_mbps=150.0,
                packet_loss_percent=0.1,
                connection_count=45,
                error_rate_percent=0.2,
                bandwidth_utilization_percent=65.0
            )
        except Exception as e:
            logger.error(f"Failed to get network metrics: {e}")
            return None

class LocalNetworkProvider(NetworkProvider):
    async def create_network_segment(self, segment: NetworkSegment) -> bool:
        try:
            logger.info(f"Creating local network segment: {segment.name}")
            # Local network setup (Docker networks, etc.)
            return True
        except Exception as e:
            logger.error(f"Failed to create local network segment: {e}")
            return False
    
    async def configure_load_balancer(self, load_balancer: LoadBalancer) -> bool:
        try:
            logger.info(f"Configuring local load balancer: {load_balancer.name}")
            # Local load balancer setup (nginx, HAProxy, etc.)
            return True
        except Exception as e:
            logger.error(f"Failed to configure local load balancer: {e}")
            return False
    
    async def apply_firewall_rules(self, rules: List[FirewallRule]) -> bool:
        try:
            logger.info(f"Applying {len(rules)} local firewall rules")
            # Local firewall setup (iptables, etc.)
            return True
        except Exception as e:
            logger.error(f"Failed to apply local firewall rules: {e}")
            return False
    
    async def get_network_metrics(self, endpoint_id: str) -> Optional[NetworkMetrics]:
        try:
            # Simulate local network metrics
            return NetworkMetrics(
                timestamp=datetime.utcnow(),
                endpoint_id=endpoint_id,
                latency_ms=5.0,
                throughput_mbps=1000.0,
                packet_loss_percent=0.0,
                connection_count=25,
                error_rate_percent=0.0,
                bandwidth_utilization_percent=25.0
            )
        except Exception as e:
            logger.error(f"Failed to get local network metrics: {e}")
            return None

class NetworkCoordinator:
    def __init__(self):
        self.segments: Dict[str, NetworkSegment] = {}
        self.endpoints: Dict[str, ServiceEndpoint] = {}
        self.load_balancers: Dict[str, LoadBalancer] = {}
        self.firewall_rules: Dict[str, FirewallRule] = {}
        self.routes: Dict[str, NetworkRoute] = {}
        self.traffic_policies: Dict[str, TrafficPolicy] = {}
        self.providers: Dict[str, NetworkProvider] = {}
        self.metrics_history: List[NetworkMetrics] = []
        
        # Initialize providers
        self._initialize_providers()
        
        # Setup default network configuration
        self._setup_default_networks()
    
    def _initialize_providers(self):
        """Initialize network providers"""
        self.providers = {
            'cloud': CloudNetworkProvider(),
            'local': LocalNetworkProvider()
        }
    
    def _setup_default_networks(self):
        """Setup default network segments and configurations"""
        default_segments = [
            NetworkSegment(
                id="internal_network",
                name="Internal Services Network",
                network_type=NetworkType.INTERNAL,
                cidr="10.0.0.0/16",
                gateway="10.0.0.1",
                dns_servers=["10.0.0.2", "10.0.0.3"]
            ),
            NetworkSegment(
                id="external_network",
                name="External API Network",
                network_type=NetworkType.EXTERNAL,
                cidr="172.16.0.0/16",
                gateway="172.16.0.1"
            ),
            NetworkSegment(
                id="database_network",
                name="Database Network",
                network_type=NetworkType.DATABASE,
                cidr="10.1.0.0/16",
                gateway="10.1.0.1"
            ),
            NetworkSegment(
                id="cache_network",
                name="Cache Network",
                network_type=NetworkType.CACHE,
                cidr="10.2.0.0/16",
                gateway="10.2.0.1"
            )
        ]
        
        for segment in default_segments:
            self.segments[segment.id] = segment
        
        # Default firewall rules
        default_firewall_rules = [
            FirewallRule(
                id="allow_internal_http",
                name="Allow Internal HTTP",
                source="10.0.0.0/16",
                destination="10.0.0.0/16",
                port=80,
                protocol=NetworkProtocol.HTTP,
                action="ALLOW",
                priority=100
            ),
            FirewallRule(
                id="allow_internal_https",
                name="Allow Internal HTTPS",
                source="10.0.0.0/16",
                destination="10.0.0.0/16",
                port=443,
                protocol=NetworkProtocol.HTTPS,
                action="ALLOW",
                priority=100
            ),
            FirewallRule(
                id="allow_external_api",
                name="Allow External API Access",
                source="0.0.0.0/0",
                destination="172.16.0.0/16",
                port=443,
                protocol=NetworkProtocol.HTTPS,
                action="ALLOW",
                priority=200
            ),
            FirewallRule(
                id="deny_external_internal",
                name="Deny External to Internal",
                source="0.0.0.0/0",
                destination="10.0.0.0/16",
                action="DENY",
                priority=300
            )
        ]
        
        for rule in default_firewall_rules:
            self.firewall_rules[rule.id] = rule
    
    async def create_network_segment(self, segment_config: Dict[str, Any]) -> Optional[NetworkSegment]:
        """Create a new network segment"""
        try:
            segment = NetworkSegment(
                id=segment_config.get('id', f"segment_{int(time.time())}"),
                name=segment_config['name'],
                network_type=NetworkType(segment_config['network_type']),
                cidr=segment_config['cidr'],
                vlan_id=segment_config.get('vlan_id'),
                gateway=segment_config.get('gateway'),
                dns_servers=segment_config.get('dns_servers', []),
                metadata=segment_config.get('metadata', {})
            )
            
            # Validate CIDR
            try:
                ipaddress.IPv4Network(segment.cidr)
            except ValueError as e:
                logger.error(f"Invalid CIDR: {segment.cidr} - {e}")
                return None
            
            # Create segment using appropriate provider
            provider_name = segment_config.get('provider', 'local')
            if provider_name in self.providers:
                provider = self.providers[provider_name]
                if await provider.create_network_segment(segment):
                    self.segments[segment.id] = segment
                    logger.info(f"Created network segment: {segment.id}")
                    return segment
                else:
                    logger.error(f"Failed to create network segment with provider: {provider_name}")
                    return None
            else:
                logger.error(f"Unknown network provider: {provider_name}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to create network segment: {e}")
            return None
    
    async def register_service_endpoint(self, endpoint_config: Dict[str, Any]) -> Optional[ServiceEndpoint]:
        """Register a service endpoint"""
        try:
            endpoint = ServiceEndpoint(
                id=endpoint_config.get('id', f"endpoint_{int(time.time())}"),
                service_id=endpoint_config['service_id'],
                host=endpoint_config['host'],
                port=endpoint_config['port'],
                protocol=NetworkProtocol(endpoint_config.get('protocol', 'https')),
                health_check_path=endpoint_config.get('health_check_path'),
                weight=endpoint_config.get('weight', 100),
                metadata=endpoint_config.get('metadata', {})
            )
            
            self.endpoints[endpoint.id] = endpoint
            logger.info(f"Registered service endpoint: {endpoint.id}")
            return endpoint
            
        except Exception as e:
            logger.error(f"Failed to register service endpoint: {e}")
            return None
    
    async def create_load_balancer(self, lb_config: Dict[str, Any]) -> Optional[LoadBalancer]:
        """Create a load balancer"""
        try:
            load_balancer = LoadBalancer(
                id=lb_config.get('id', f"lb_{int(time.time())}"),
                name=lb_config['name'],
                frontend_host=lb_config['frontend_host'],
                frontend_port=lb_config['frontend_port'],
                protocol=NetworkProtocol(lb_config.get('protocol', 'https')),
                method=LoadBalancingMethod(lb_config.get('method', 'round_robin')),
                health_check_interval=lb_config.get('health_check_interval', 30),
                timeout=lb_config.get('timeout', 5),
                max_retries=lb_config.get('max_retries', 3),
                ssl_enabled=lb_config.get('ssl_enabled', False),
                ssl_cert_path=lb_config.get('ssl_cert_path'),
                metadata=lb_config.get('metadata', {})
            )
            
            # Add backend endpoints
            backend_ids = lb_config.get('backend_endpoint_ids', [])
            for endpoint_id in backend_ids:
                if endpoint_id in self.endpoints:
                    load_balancer.backends.append(self.endpoints[endpoint_id])
            
            # Configure load balancer using appropriate provider
            provider_name = lb_config.get('provider', 'local')
            if provider_name in self.providers:
                provider = self.providers[provider_name]
                if await provider.configure_load_balancer(load_balancer):
                    self.load_balancers[load_balancer.id] = load_balancer
                    logger.info(f"Created load balancer: {load_balancer.id}")
                    return load_balancer
                else:
                    logger.error(f"Failed to configure load balancer with provider: {provider_name}")
                    return None
            else:
                logger.error(f"Unknown network provider: {provider_name}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to create load balancer: {e}")
            return None
    
    async def add_firewall_rule(self, rule_config: Dict[str, Any]) -> Optional[FirewallRule]:
        """Add a firewall rule"""
        try:
            rule = FirewallRule(
                id=rule_config.get('id', f"rule_{int(time.time())}"),
                name=rule_config['name'],
                source=rule_config['source'],
                destination=rule_config['destination'],
                port=rule_config.get('port'),
                protocol=NetworkProtocol(rule_config['protocol']) if rule_config.get('protocol') else None,
                action=rule_config.get('action', 'ALLOW'),
                priority=rule_config.get('priority', 100),
                enabled=rule_config.get('enabled', True),
                metadata=rule_config.get('metadata', {})
            )
            
            self.firewall_rules[rule.id] = rule
            
            # Apply firewall rules
            await self._apply_firewall_rules()
            
            logger.info(f"Added firewall rule: {rule.id}")
            return rule
            
        except Exception as e:
            logger.error(f"Failed to add firewall rule: {e}")
            return None
    
    async def _apply_firewall_rules(self):
        """Apply all firewall rules to providers"""
        try:
            enabled_rules = [rule for rule in self.firewall_rules.values() if rule.enabled]
            
            for provider in self.providers.values():
                await provider.apply_firewall_rules(enabled_rules)
                
        except Exception as e:
            logger.error(f"Failed to apply firewall rules: {e}")
    
    async def add_traffic_policy(self, policy_config: Dict[str, Any]) -> Optional[TrafficPolicy]:
        """Add a traffic policy"""
        try:
            policy = TrafficPolicy(
                id=policy_config.get('id', f"policy_{int(time.time())}"),
                name=policy_config['name'],
                source_patterns=policy_config['source_patterns'],
                destination_patterns=policy_config['destination_patterns'],
                traffic_type=TrafficType(policy_config['traffic_type']),
                rate_limit=policy_config.get('rate_limit'),
                bandwidth_limit=policy_config.get('bandwidth_limit'),
                priority=policy_config.get('priority', 100),
                enabled=policy_config.get('enabled', True),
                metadata=policy_config.get('metadata', {})
            )
            
            self.traffic_policies[policy.id] = policy
            logger.info(f"Added traffic policy: {policy.id}")
            return policy
            
        except Exception as e:
            logger.error(f"Failed to add traffic policy: {e}")
            return None
    
    async def health_check_endpoints(self) -> Dict[str, bool]:
        """Perform health checks on all registered endpoints"""
        try:
            health_status = {}
            
            for endpoint_id, endpoint in self.endpoints.items():
                if endpoint.health_check_path:
                    # Simulate health check
                    is_healthy = await self._perform_health_check(endpoint)
                    health_status[endpoint_id] = is_healthy
                    
                    # Update endpoint status
                    endpoint.status = NetworkStatus.ACTIVE if is_healthy else NetworkStatus.FAILED
                    endpoint.last_health_check = datetime.utcnow()
                else:
                    # No health check path, assume healthy
                    health_status[endpoint_id] = True
            
            return health_status
            
        except Exception as e:
            logger.error(f"Failed to perform health checks: {e}")
            return {}
    
    async def _perform_health_check(self, endpoint: ServiceEndpoint) -> bool:
        """Perform health check on a specific endpoint"""
        try:
            # Simulate health check - in real implementation, this would make HTTP request
            # For now, simulate 95% uptime
            import random
            return random.random() > 0.05
            
        except Exception as e:
            logger.error(f"Health check failed for endpoint {endpoint.id}: {e}")
            return False
    
    async def get_network_topology(self) -> Dict[str, Any]:
        """Get network topology information"""
        try:
            topology = {
                'segments': {},
                'endpoints': {},
                'load_balancers': {},
                'connections': []
            }
            
            # Add segments
            for segment_id, segment in self.segments.items():
                topology['segments'][segment_id] = {
                    'name': segment.name,
                    'type': segment.network_type.value,
                    'cidr': segment.cidr,
                    'status': segment.status.value,
                    'gateway': segment.gateway
                }
            
            # Add endpoints
            for endpoint_id, endpoint in self.endpoints.items():
                topology['endpoints'][endpoint_id] = {
                    'service_id': endpoint.service_id,
                    'host': endpoint.host,
                    'port': endpoint.port,
                    'protocol': endpoint.protocol.value,
                    'status': endpoint.status.value,
                    'weight': endpoint.weight
                }
            
            # Add load balancers
            for lb_id, lb in self.load_balancers.items():
                topology['load_balancers'][lb_id] = {
                    'name': lb.name,
                    'frontend': f"{lb.frontend_host}:{lb.frontend_port}",
                    'protocol': lb.protocol.value,
                    'method': lb.method.value,
                    'backend_count': len(lb.backends),
                    'status': lb.status.value
                }
            
            # Add connections between load balancers and endpoints
            for lb in self.load_balancers.values():
                for backend in lb.backends:
                    topology['connections'].append({
                        'source': lb.id,
                        'target': backend.id,
                        'type': 'load_balancer_backend'
                    })
            
            return topology
            
        except Exception as e:
            logger.error(f"Failed to get network topology: {e}")
            return {}
    
    async def get_traffic_metrics(self) -> Dict[str, Any]:
        """Get traffic metrics across the network"""
        try:
            metrics = {
                'total_endpoints': len(self.endpoints),
                'active_endpoints': len([e for e in self.endpoints.values() if e.status == NetworkStatus.ACTIVE]),
                'total_load_balancers': len(self.load_balancers),
                'total_firewall_rules': len(self.firewall_rules),
                'enabled_firewall_rules': len([r for r in self.firewall_rules.values() if r.enabled]),
                'endpoint_metrics': {}
            }
            
            # Collect metrics from providers
            for endpoint_id in self.endpoints:
                for provider in self.providers.values():
                    try:
                        endpoint_metrics = await provider.get_network_metrics(endpoint_id)
                        if endpoint_metrics:
                            metrics['endpoint_metrics'][endpoint_id] = {
                                'latency_ms': endpoint_metrics.latency_ms,
                                'throughput_mbps': endpoint_metrics.throughput_mbps,
                                'packet_loss_percent': endpoint_metrics.packet_loss_percent,
                                'connection_count': endpoint_metrics.connection_count,
                                'error_rate_percent': endpoint_metrics.error_rate_percent,
                                'bandwidth_utilization_percent': endpoint_metrics.bandwidth_utilization_percent
                            }
                            
                            # Store in history
                            self.metrics_history.append(endpoint_metrics)
                            break
                    except Exception as e:
                        logger.error(f"Failed to get metrics for endpoint {endpoint_id}: {e}")
            
            # Keep only last 1000 metrics
            if len(self.metrics_history) > 1000:
                self.metrics_history = self.metrics_history[-1000:]
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to get traffic metrics: {e}")
            return {}
    
    async def optimize_traffic_routing(self) -> Dict[str, Any]:
        """Optimize traffic routing based on current metrics"""
        try:
            optimization_results = {
                'recommendations': [],
                'applied_optimizations': [],
                'performance_improvements': []
            }
            
            # Analyze load balancer performance
            for lb_id, lb in self.load_balancers.items():
                if len(lb.backends) > 1:
                    # Check backend health and performance
                    healthy_backends = [b for b in lb.backends if b.status == NetworkStatus.ACTIVE]
                    
                    if len(healthy_backends) < len(lb.backends):
                        optimization_results['recommendations'].append({
                            'type': 'backend_health',
                            'load_balancer_id': lb_id,
                            'message': f"Load balancer {lb.name} has unhealthy backends"
                        })
                    
                    # Suggest load balancing method optimization
                    if lb.method == LoadBalancingMethod.ROUND_ROBIN and len(healthy_backends) > 3:
                        optimization_results['recommendations'].append({
                            'type': 'load_balancing_method',
                            'load_balancer_id': lb_id,
                            'message': f"Consider using least_connections method for {lb.name} with {len(healthy_backends)} backends"
                        })
            
            # Analyze firewall rules
            enabled_rules = [r for r in self.firewall_rules.values() if r.enabled]
            if len(enabled_rules) > 50:
                optimization_results['recommendations'].append({
                    'type': 'firewall_optimization',
                    'message': f"Consider consolidating {len(enabled_rules)} firewall rules for better performance"
                })
            
            return optimization_results
            
        except Exception as e:
            logger.error(f"Failed to optimize traffic routing: {e}")
            return {}
    
    async def start_network_monitoring(self, interval: int = 60):
        """Start continuous network monitoring"""
        try:
            logger.info("Starting network monitoring")
            
            while True:
                # Perform health checks
                await self.health_check_endpoints()
                
                # Collect traffic metrics
                await self.get_traffic_metrics()
                
                # Check for optimization opportunities
                await self.optimize_traffic_routing()
                
                await asyncio.sleep(interval)
                
        except Exception as e:
            logger.error(f"Network monitoring failed: {e}")
    
    def get_network_statistics(self) -> Dict[str, Any]:
        """Get network configuration statistics"""
        try:
            return {
                'total_segments': len(self.segments),
                'segments_by_type': {
                    net_type.value: len([s for s in self.segments.values() if s.network_type == net_type])
                    for net_type in NetworkType
                },
                'total_endpoints': len(self.endpoints),
                'active_endpoints': len([e for e in self.endpoints.values() if e.status == NetworkStatus.ACTIVE]),
                'total_load_balancers': len(self.load_balancers),
                'active_load_balancers': len([lb for lb in self.load_balancers.values() if lb.status == NetworkStatus.ACTIVE]),
                'total_firewall_rules': len(self.firewall_rules),
                'enabled_firewall_rules': len([r for r in self.firewall_rules.values() if r.enabled]),
                'total_traffic_policies': len(self.traffic_policies),
                'enabled_traffic_policies': len([p for p in self.traffic_policies.values() if p.enabled]),
                'metrics_collected': len(self.metrics_history)
            }
        except Exception as e:
            logger.error(f"Failed to get network statistics: {e}")
            return {}

# Global network coordinator instance
network_coordinator = NetworkCoordinator()

async def initialize_network_coordinator():
    """Initialize the network coordinator"""
    try:
        logger.info("Network coordinator initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize network coordinator: {e}")
        return False

if __name__ == "__main__":
    async def main():
        await initialize_network_coordinator()
        
        # Example usage
        # Register service endpoint
        endpoint_config = {
            'service_id': 'einvoice_service',
            'host': '10.0.1.100',
            'port': 8080,
            'protocol': 'https',
            'health_check_path': '/health'
        }
        endpoint = await network_coordinator.register_service_endpoint(endpoint_config)
        
        if endpoint:
            print(f"Registered endpoint: {endpoint.id}")
            
            # Create load balancer
            lb_config = {
                'name': 'EInvoice API Load Balancer',
                'frontend_host': '0.0.0.0',
                'frontend_port': 443,
                'protocol': 'https',
                'method': 'round_robin',
                'backend_endpoint_ids': [endpoint.id]
            }
            lb = await network_coordinator.create_load_balancer(lb_config)
            
            if lb:
                print(f"Created load balancer: {lb.id}")
                
                # Get topology
                topology = await network_coordinator.get_network_topology()
                print(f"Network topology: {json.dumps(topology, indent=2)}")
                
                # Get metrics
                metrics = await network_coordinator.get_traffic_metrics()
                print(f"Traffic metrics: {json.dumps(metrics, indent=2)}")
    
    asyncio.run(main())