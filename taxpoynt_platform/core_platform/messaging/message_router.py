"""
Core Platform: Message Router
Manages role-based message routing between SI and APP services
"""
import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Set, Union, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import fnmatch

from .event_bus import Event, EventBus, EventScope, EventPriority, get_event_bus

logger = logging.getLogger(__name__)


class ServiceRole(str, Enum):
    """Service roles in the platform"""
    SYSTEM_INTEGRATOR = "si"
    ACCESS_POINT_PROVIDER = "app"
    HYBRID = "hybrid"
    CORE = "core"


class RoutingStrategy(str, Enum):
    """Message routing strategies"""
    BROADCAST = "broadcast"         # Send to all matching targets
    ROUND_ROBIN = "round_robin"     # Distribute among targets
    PRIORITY = "priority"           # Send to highest priority target
    FAILOVER = "failover"          # Try targets in order until success
    LOAD_BALANCED = "load_balanced" # Route based on load metrics


class MessageType(str, Enum):
    """Types of messages in the system"""
    EVENT = "event"
    COMMAND = "command"
    QUERY = "query"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    ALERT = "alert"


@dataclass
class RoutingRule:
    """Message routing rule definition"""
    rule_id: str
    name: str
    description: str
    source_pattern: str         # Pattern for source services
    target_pattern: str         # Pattern for target services
    message_pattern: str        # Pattern for message types
    source_role: Optional[ServiceRole] = None
    target_role: Optional[ServiceRole] = None
    strategy: RoutingStrategy = RoutingStrategy.BROADCAST
    priority: int = 0
    conditions: Dict[str, Any] = None
    transformations: List[str] = None
    filters: Dict[str, Any] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.conditions is None:
            self.conditions = {}
        if self.transformations is None:
            self.transformations = []
        if self.filters is None:
            self.filters = {}
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ServiceEndpoint:
    """Service endpoint for message routing"""
    endpoint_id: str
    service_name: str
    service_role: ServiceRole
    endpoint_url: Optional[str] = None
    callback: Optional[Callable] = None
    priority: int = 0
    active: bool = True
    load_factor: float = 1.0
    last_activity: datetime = None
    health_status: str = "healthy"
    tags: List[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.last_activity is None:
            self.last_activity = datetime.now(timezone.utc)
        if self.tags is None:
            self.tags = []
        if self.metadata is None:
            self.metadata = {}


@dataclass
class RoutingContext:
    """Context for message routing"""
    source_service: str
    source_role: ServiceRole
    target_services: List[str] = None
    target_role: Optional[ServiceRole] = None
    tenant_id: Optional[str] = None
    correlation_id: Optional[str] = None
    routing_metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.target_services is None:
            self.target_services = []
        if self.routing_metadata is None:
            self.routing_metadata = {}


@dataclass
class RoutedMessage:
    """Message with routing information"""
    message_id: str
    message_type: MessageType
    payload: Dict[str, Any]
    routing_context: RoutingContext
    timestamp: datetime
    priority: EventPriority = EventPriority.NORMAL
    expiry: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3
    route_history: List[str] = None
    
    def __post_init__(self):
        if self.route_history is None:
            self.route_history = []


class MessageRouter:
    """
    Message Router for TaxPoynt Platform
    
    Handles role-based message routing between:
    - SI (System Integrator) services
    - APP (Access Point Provider) services  
    - Hybrid services
    - Core platform services
    
    Features:
    - Role-based routing rules
    - Multiple routing strategies
    - Service discovery and health tracking
    - Message transformation and filtering
    - Load balancing and failover
    """
    
    def __init__(self, event_bus: Optional[EventBus] = None):
        """Initialize the message router"""
        self.event_bus = event_bus or get_event_bus()
        
        # Routing infrastructure
        self.routing_rules: Dict[str, RoutingRule] = {}
        self.service_endpoints: Dict[str, ServiceEndpoint] = {}
        self.role_mappings: Dict[ServiceRole, List[str]] = {
            role: [] for role in ServiceRole
        }
        
        # Routing state
        self.routing_table: Dict[str, List[str]] = {}
        self.active_routes: Dict[str, RoutedMessage] = {}
        self.load_metrics: Dict[str, Dict[str, float]] = {}
        
        # Round-robin tracking
        self.round_robin_state: Dict[str, int] = {}
        
        # Message transformers and filters
        self.transformers: Dict[str, Callable] = {}
        self.filters: Dict[str, Callable] = {}
        
        # Statistics
        self.routing_stats = {
            "messages_routed": 0,
            "routing_failures": 0,
            "successful_deliveries": 0,
            "failed_deliveries": 0,
            "transformation_count": 0,
            "filter_drops": 0
        }
        
        self.logger = logging.getLogger(__name__)
        self.is_initialized = False
    
    async def initialize(self):
        """Initialize the message router"""
        if self.is_initialized:
            return
        
        self.logger.info("Initializing Message Router")
        
        # Set up default routing rules
        await self._setup_default_rules()
        
        # Register with event bus
        await self._register_event_handlers()
        
        # Start monitoring tasks
        asyncio.create_task(self._health_monitoring_loop())
        asyncio.create_task(self._load_balancing_loop())
        
        self.is_initialized = True
        self.logger.info("Message Router initialized")
    
    async def register_service(
        self,
        service_name: str,
        service_role: ServiceRole,
        endpoint_url: Optional[str] = None,
        callback: Optional[Callable] = None,
        priority: int = 0,
        tags: List[str] = None,
        metadata: Dict[str, Any] = None
    ) -> str:
        """Register a service endpoint for routing"""
        try:
            endpoint_id = f"{service_role.value}_{service_name}_{uuid.uuid4().hex[:8]}"
            
            endpoint = ServiceEndpoint(
                endpoint_id=endpoint_id,
                service_name=service_name,
                service_role=service_role,
                endpoint_url=endpoint_url,
                callback=callback,
                priority=priority,
                tags=tags or [],
                metadata=metadata or {}
            )
            
            self.service_endpoints[endpoint_id] = endpoint
            self.role_mappings[service_role].append(endpoint_id)
            
            # Initialize load metrics
            self.load_metrics[endpoint_id] = {
                "requests_per_minute": 0.0,
                "average_response_time": 0.0,
                "error_rate": 0.0,
                "active_connections": 0
            }
            
            self.logger.info(f"Service registered: {service_name} ({service_role.value}) -> {endpoint_id}")
            
            # Emit service registration event
            await self.event_bus.emit(
                event_type="service.registered",
                payload={
                    "endpoint_id": endpoint_id,
                    "service_name": service_name,
                    "service_role": service_role.value,
                    "endpoint_url": endpoint_url
                },
                source="message_router",
                scope=EventScope.GLOBAL
            )
            
            return endpoint_id
            
        except Exception as e:
            self.logger.error(f"Error registering service: {str(e)}")
            raise
    
    async def unregister_service(self, endpoint_id: str) -> bool:
        """Unregister a service endpoint"""
        try:
            if endpoint_id in self.service_endpoints:
                endpoint = self.service_endpoints[endpoint_id]
                
                # Remove from role mappings
                if endpoint_id in self.role_mappings[endpoint.service_role]:
                    self.role_mappings[endpoint.service_role].remove(endpoint_id)
                
                # Clean up metrics
                if endpoint_id in self.load_metrics:
                    del self.load_metrics[endpoint_id]
                
                # Remove endpoint
                del self.service_endpoints[endpoint_id]
                
                self.logger.info(f"Service unregistered: {endpoint_id}")
                
                # Emit service unregistration event
                await self.event_bus.emit(
                    event_type="service.unregistered",
                    payload={
                        "endpoint_id": endpoint_id,
                        "service_name": endpoint.service_name,
                        "service_role": endpoint.service_role.value
                    },
                    source="message_router",
                    scope=EventScope.GLOBAL
                )
                
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error unregistering service: {str(e)}")
            return False
    
    async def add_routing_rule(self, rule: RoutingRule):
        """Add a routing rule"""
        try:
            self.routing_rules[rule.rule_id] = rule
            
            # Rebuild routing table
            await self._rebuild_routing_table()
            
            self.logger.info(f"Routing rule added: {rule.name}")
            
        except Exception as e:
            self.logger.error(f"Error adding routing rule: {str(e)}")
            raise
    
    async def remove_routing_rule(self, rule_id: str) -> bool:
        """Remove a routing rule"""
        try:
            if rule_id in self.routing_rules:
                rule = self.routing_rules[rule_id]
                del self.routing_rules[rule_id]
                
                # Rebuild routing table
                await self._rebuild_routing_table()
                
                self.logger.info(f"Routing rule removed: {rule.name}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error removing routing rule: {str(e)}")
            return False
    
    async def route_message(
        self,
        message_type: MessageType,
        payload: Dict[str, Any],
        routing_context: RoutingContext,
        priority: EventPriority = EventPriority.NORMAL,
        expiry: Optional[datetime] = None
    ) -> str:
        """Route a message based on context and rules"""
        try:
            message = RoutedMessage(
                message_id=str(uuid.uuid4()),
                message_type=message_type,
                payload=payload,
                routing_context=routing_context,
                timestamp=datetime.now(timezone.utc),
                priority=priority,
                expiry=expiry
            )
            
            # Store active route
            self.active_routes[message.message_id] = message
            
            # Find applicable routing rules
            applicable_rules = await self._find_applicable_rules(message)
            
            if not applicable_rules:
                self.logger.warning(f"No routing rules found for message {message.message_id}")
                self.routing_stats["routing_failures"] += 1
                return message.message_id
            
            # Execute routing for each rule
            for rule in applicable_rules:
                await self._execute_routing_rule(message, rule)
            
            self.routing_stats["messages_routed"] += 1
            
            return message.message_id
            
        except Exception as e:
            self.logger.error(f"Error routing message: {str(e)}")
            self.routing_stats["routing_failures"] += 1
            raise
    
    async def route_to_role(
        self,
        target_role: ServiceRole,
        message_type: MessageType,
        payload: Dict[str, Any],
        source_service: str,
        source_role: ServiceRole,
        strategy: RoutingStrategy = RoutingStrategy.BROADCAST,
        tenant_id: Optional[str] = None
    ) -> str:
        """Route message to all services of a specific role"""
        routing_context = RoutingContext(
            source_service=source_service,
            source_role=source_role,
            target_role=target_role,
            tenant_id=tenant_id
        )
        
        # Create temporary rule for this routing
        temp_rule = RoutingRule(
            rule_id=f"temp_role_route_{uuid.uuid4().hex[:8]}",
            name=f"Route to {target_role.value}",
            description=f"Temporary rule to route to {target_role.value} services",
            source_pattern="*",
            target_pattern="*",
            message_pattern="*",
            source_role=source_role,
            target_role=target_role,
            strategy=strategy
        )
        
        message = RoutedMessage(
            message_id=str(uuid.uuid4()),
            message_type=message_type,
            payload=payload,
            routing_context=routing_context,
            timestamp=datetime.now(timezone.utc)
        )
        
        await self._execute_routing_rule(message, temp_rule)
        
        return message.message_id
    
    async def route_to_service(
        self,
        target_service: str,
        message_type: MessageType,
        payload: Dict[str, Any],
        source_service: str,
        source_role: ServiceRole,
        tenant_id: Optional[str] = None
    ) -> str:
        """Route message to a specific service"""
        routing_context = RoutingContext(
            source_service=source_service,
            source_role=source_role,
            target_services=[target_service],
            tenant_id=tenant_id
        )
        
        return await self.route_message(
            message_type=message_type,
            payload=payload,
            routing_context=routing_context
        )
    
    async def _setup_default_rules(self):
        """Set up default routing rules"""
        default_rules = [
            # SI to APP communication
            RoutingRule(
                rule_id="si_to_app_default",
                name="SI to APP Default Route",
                description="Route SI service messages to APP services",
                source_pattern="*",
                target_pattern="*",
                message_pattern="*",
                source_role=ServiceRole.SYSTEM_INTEGRATOR,
                target_role=ServiceRole.ACCESS_POINT_PROVIDER,
                strategy=RoutingStrategy.BROADCAST
            ),
            
            # APP to SI communication
            RoutingRule(
                rule_id="app_to_si_default",
                name="APP to SI Default Route",
                description="Route APP service messages to SI services",
                source_pattern="*",
                target_pattern="*",
                message_pattern="*",
                source_role=ServiceRole.ACCESS_POINT_PROVIDER,
                target_role=ServiceRole.SYSTEM_INTEGRATOR,
                strategy=RoutingStrategy.LOAD_BALANCED
            ),
            
            # Hybrid service communication
            RoutingRule(
                rule_id="hybrid_broadcast",
                name="Hybrid Service Broadcast",
                description="Broadcast hybrid service messages to all roles",
                source_pattern="*",
                target_pattern="*",
                message_pattern="*",
                source_role=ServiceRole.HYBRID,
                strategy=RoutingStrategy.BROADCAST
            ),
            
            # Core platform communication
            RoutingRule(
                rule_id="core_priority",
                name="Core Platform Priority Route",
                description="Priority routing for core platform messages",
                source_pattern="*",
                target_pattern="*",
                message_pattern="*",
                source_role=ServiceRole.CORE,
                strategy=RoutingStrategy.PRIORITY,
                priority=100
            ),
            
            # Emergency/Alert routing
            RoutingRule(
                rule_id="alert_broadcast",
                name="Alert Broadcast",
                description="Broadcast alert messages to all services",
                source_pattern="*",
                target_pattern="*",
                message_pattern="alert.*",
                strategy=RoutingStrategy.BROADCAST,
                priority=200
            )
        ]
        
        for rule in default_rules:
            await self.add_routing_rule(rule)
    
    async def _find_applicable_rules(self, message: RoutedMessage) -> List[RoutingRule]:
        """Find routing rules applicable to a message"""
        applicable_rules = []
        
        for rule in self.routing_rules.values():
            if await self._rule_matches_message(rule, message):
                applicable_rules.append(rule)
        
        # Sort by priority (highest first)
        applicable_rules.sort(key=lambda r: r.priority, reverse=True)
        
        return applicable_rules
    
    async def _rule_matches_message(self, rule: RoutingRule, message: RoutedMessage) -> bool:
        """Check if a routing rule matches a message"""
        try:
            context = message.routing_context
            
            # Check source role
            if rule.source_role and rule.source_role != context.source_role:
                return False
            
            # Check target role
            if rule.target_role and context.target_role and rule.target_role != context.target_role:
                return False
            
            # Check source pattern
            if not self._pattern_matches(rule.source_pattern, context.source_service):
                return False
            
            # Check message pattern
            if not self._pattern_matches(rule.message_pattern, message.message_type.value):
                return False
            
            # Check conditions
            if rule.conditions:
                if not await self._evaluate_conditions(rule.conditions, message):
                    return False
            
            # Check filters
            if rule.filters:
                if not await self._apply_filters(rule.filters, message):
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error matching rule {rule.rule_id}: {str(e)}")
            return False
    
    async def _execute_routing_rule(self, message: RoutedMessage, rule: RoutingRule):
        """Execute a routing rule for a message"""
        try:
            # Find target endpoints
            target_endpoints = await self._find_target_endpoints(message, rule)
            
            if not target_endpoints:
                self.logger.warning(f"No target endpoints found for rule {rule.rule_id}")
                return
            
            # Apply transformations
            transformed_payload = await self._apply_transformations(
                message.payload, rule.transformations
            )
            
            # Route based on strategy
            if rule.strategy == RoutingStrategy.BROADCAST:
                await self._broadcast_message(message, target_endpoints, transformed_payload)
            elif rule.strategy == RoutingStrategy.ROUND_ROBIN:
                await self._round_robin_message(message, target_endpoints, transformed_payload, rule.rule_id)
            elif rule.strategy == RoutingStrategy.PRIORITY:
                await self._priority_message(message, target_endpoints, transformed_payload)
            elif rule.strategy == RoutingStrategy.LOAD_BALANCED:
                await self._load_balanced_message(message, target_endpoints, transformed_payload)
            elif rule.strategy == RoutingStrategy.FAILOVER:
                await self._failover_message(message, target_endpoints, transformed_payload)
            
        except Exception as e:
            self.logger.error(f"Error executing routing rule {rule.rule_id}: {str(e)}")
    
    async def _find_target_endpoints(self, message: RoutedMessage, rule: RoutingRule) -> List[ServiceEndpoint]:
        """Find target endpoints for a message based on routing rule"""
        target_endpoints = []
        context = message.routing_context
        
        # If specific target services are specified
        if context.target_services:
            for service_name in context.target_services:
                for endpoint in self.service_endpoints.values():
                    if (endpoint.service_name == service_name and 
                        endpoint.active and
                        self._pattern_matches(rule.target_pattern, endpoint.service_name)):
                        
                        # Check role compatibility
                        if rule.target_role and endpoint.service_role != rule.target_role:
                            continue
                        
                        target_endpoints.append(endpoint)
        
        # If target role is specified
        elif rule.target_role:
            for endpoint_id in self.role_mappings.get(rule.target_role, []):
                if endpoint_id in self.service_endpoints:
                    endpoint = self.service_endpoints[endpoint_id]
                    if (endpoint.active and
                        self._pattern_matches(rule.target_pattern, endpoint.service_name)):
                        target_endpoints.append(endpoint)
        
        # Otherwise, find all matching endpoints
        else:
            for endpoint in self.service_endpoints.values():
                if (endpoint.active and
                    self._pattern_matches(rule.target_pattern, endpoint.service_name)):
                    target_endpoints.append(endpoint)
        
        return target_endpoints
    
    async def _broadcast_message(
        self, 
        message: RoutedMessage, 
        endpoints: List[ServiceEndpoint], 
        payload: Dict[str, Any]
    ):
        """Broadcast message to all endpoints"""
        delivery_tasks = []
        
        for endpoint in endpoints:
            task = asyncio.create_task(
                self._deliver_message(message, endpoint, payload)
            )
            delivery_tasks.append(task)
        
        # Wait for all deliveries
        if delivery_tasks:
            results = await asyncio.gather(*delivery_tasks, return_exceptions=True)
            
            # Update statistics
            successful = sum(1 for r in results if r is True)
            failed = len(results) - successful
            
            self.routing_stats["successful_deliveries"] += successful
            self.routing_stats["failed_deliveries"] += failed
    
    async def _round_robin_message(
        self, 
        message: RoutedMessage, 
        endpoints: List[ServiceEndpoint], 
        payload: Dict[str, Any],
        rule_id: str
    ):
        """Route message using round-robin strategy"""
        if not endpoints:
            return
        
        # Get current round-robin index
        current_index = self.round_robin_state.get(rule_id, 0)
        
        # Select endpoint
        selected_endpoint = endpoints[current_index % len(endpoints)]
        
        # Update round-robin state
        self.round_robin_state[rule_id] = (current_index + 1) % len(endpoints)
        
        # Deliver message
        success = await self._deliver_message(message, selected_endpoint, payload)
        
        if success:
            self.routing_stats["successful_deliveries"] += 1
        else:
            self.routing_stats["failed_deliveries"] += 1
    
    async def _priority_message(
        self, 
        message: RoutedMessage, 
        endpoints: List[ServiceEndpoint], 
        payload: Dict[str, Any]
    ):
        """Route message to highest priority endpoint"""
        if not endpoints:
            return
        
        # Sort by priority (highest first)
        sorted_endpoints = sorted(endpoints, key=lambda e: e.priority, reverse=True)
        
        # Try highest priority endpoints until success
        for endpoint in sorted_endpoints:
            success = await self._deliver_message(message, endpoint, payload)
            
            if success:
                self.routing_stats["successful_deliveries"] += 1
                break
        else:
            self.routing_stats["failed_deliveries"] += 1
    
    async def _load_balanced_message(
        self, 
        message: RoutedMessage, 
        endpoints: List[ServiceEndpoint], 
        payload: Dict[str, Any]
    ):
        """Route message using load balancing"""
        if not endpoints:
            return
        
        # Calculate load scores for each endpoint
        endpoint_scores = []
        for endpoint in endpoints:
            load_metrics = self.load_metrics.get(endpoint.endpoint_id, {})
            
            # Calculate composite load score (lower is better)
            load_score = (
                load_metrics.get("requests_per_minute", 0) * 0.4 +
                load_metrics.get("average_response_time", 0) * 0.3 +
                load_metrics.get("error_rate", 0) * 100 * 0.2 +
                load_metrics.get("active_connections", 0) * 0.1
            ) / endpoint.load_factor
            
            endpoint_scores.append((endpoint, load_score))
        
        # Sort by load score (lowest first)
        endpoint_scores.sort(key=lambda x: x[1])
        
        # Select endpoint with lowest load
        selected_endpoint = endpoint_scores[0][0]
        
        # Deliver message
        success = await self._deliver_message(message, selected_endpoint, payload)
        
        if success:
            self.routing_stats["successful_deliveries"] += 1
        else:
            self.routing_stats["failed_deliveries"] += 1
    
    async def _failover_message(
        self, 
        message: RoutedMessage, 
        endpoints: List[ServiceEndpoint], 
        payload: Dict[str, Any]
    ):
        """Route message with failover strategy"""
        if not endpoints:
            return
        
        # Sort by priority and health status
        sorted_endpoints = sorted(
            endpoints, 
            key=lambda e: (e.priority, e.health_status == "healthy"), 
            reverse=True
        )
        
        # Try endpoints in order until success
        for endpoint in sorted_endpoints:
            success = await self._deliver_message(message, endpoint, payload)
            
            if success:
                self.routing_stats["successful_deliveries"] += 1
                return
        
        # All endpoints failed
        self.routing_stats["failed_deliveries"] += 1
    
    async def _deliver_message(
        self, 
        message: RoutedMessage, 
        endpoint: ServiceEndpoint, 
        payload: Dict[str, Any]
    ) -> bool:
        """Deliver message to a specific endpoint"""
        try:
            # Update route history
            message.route_history.append(endpoint.endpoint_id)
            
            # Prepare delivery payload
            delivery_payload = {
                "message_id": message.message_id,
                "message_type": message.message_type.value,
                "payload": payload,
                "source_service": message.routing_context.source_service,
                "source_role": message.routing_context.source_role.value,
                "target_service": endpoint.service_name,
                "timestamp": message.timestamp.isoformat(),
                "correlation_id": message.routing_context.correlation_id,
                "tenant_id": message.routing_context.tenant_id
            }
            
            # Deliver via callback if available
            if endpoint.callback:
                if asyncio.iscoroutinefunction(endpoint.callback):
                    result = await endpoint.callback(delivery_payload)
                else:
                    result = endpoint.callback(delivery_payload)
                
                # Update endpoint activity
                endpoint.last_activity = datetime.now(timezone.utc)
                
                return bool(result)
            
            # Deliver via event bus
            await self.event_bus.emit(
                event_type=f"message.{message.message_type.value}",
                payload=delivery_payload,
                source="message_router",
                scope=self._role_to_scope(endpoint.service_role),
                priority=message.priority
            )
            
            # Update endpoint activity
            endpoint.last_activity = datetime.now(timezone.utc)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error delivering message to {endpoint.endpoint_id}: {str(e)}")
            
            # Update endpoint health
            endpoint.health_status = "unhealthy"
            
            return False
    
    def _pattern_matches(self, pattern: str, text: str) -> bool:
        """Check if pattern matches text"""
        if pattern == "*":
            return True
        if pattern == text:
            return True
        
        # Simple glob pattern matching
        if "*" in pattern or "?" in pattern:
            return fnmatch.fnmatch(text, pattern)
        
        return False
    
    def _role_to_scope(self, role: ServiceRole) -> EventScope:
        """Convert service role to event scope"""
        role_scope_mapping = {
            ServiceRole.SYSTEM_INTEGRATOR: EventScope.SI_SERVICES,
            ServiceRole.ACCESS_POINT_PROVIDER: EventScope.APP_SERVICES,
            ServiceRole.HYBRID: EventScope.HYBRID,
            ServiceRole.CORE: EventScope.GLOBAL
        }
        return role_scope_mapping.get(role, EventScope.GLOBAL)
    
    async def _apply_transformations(
        self, 
        payload: Dict[str, Any], 
        transformations: List[str]
    ) -> Dict[str, Any]:
        """Apply message transformations"""
        if not transformations:
            return payload
        
        transformed_payload = payload.copy()
        
        for transformation in transformations:
            if transformation in self.transformers:
                try:
                    transformer = self.transformers[transformation]
                    transformed_payload = await transformer(transformed_payload)
                    self.routing_stats["transformation_count"] += 1
                except Exception as e:
                    self.logger.error(f"Error applying transformation {transformation}: {str(e)}")
        
        return transformed_payload
    
    async def _apply_filters(self, filters: Dict[str, Any], message: RoutedMessage) -> bool:
        """Apply message filters"""
        for filter_name, filter_config in filters.items():
            if filter_name in self.filters:
                try:
                    filter_func = self.filters[filter_name]
                    if not await filter_func(message, filter_config):
                        self.routing_stats["filter_drops"] += 1
                        return False
                except Exception as e:
                    self.logger.error(f"Error applying filter {filter_name}: {str(e)}")
                    return False
        
        return True
    
    async def _evaluate_conditions(self, conditions: Dict[str, Any], message: RoutedMessage) -> bool:
        """Evaluate routing conditions"""
        # Implement condition evaluation logic
        # This is a simplified version
        for condition_key, condition_value in conditions.items():
            if condition_key == "tenant_id":
                if message.routing_context.tenant_id != condition_value:
                    return False
            elif condition_key == "message_type":
                if message.message_type.value != condition_value:
                    return False
        
        return True
    
    async def _rebuild_routing_table(self):
        """Rebuild the routing table based on current rules and endpoints"""
        self.routing_table.clear()
        
        # This is a simplified implementation
        # In practice, you might want to precompute routing paths
        for rule in self.routing_rules.values():
            key = f"{rule.source_role}_{rule.target_role}_{rule.strategy}"
            if key not in self.routing_table:
                self.routing_table[key] = []
            self.routing_table[key].append(rule.rule_id)
    
    async def _register_event_handlers(self):
        """Register event handlers with the event bus"""
        await self.event_bus.subscribe(
            event_pattern="service.health.*",
            callback=self._handle_service_health_event,
            subscriber="message_router"
        )
        
        await self.event_bus.subscribe(
            event_pattern="service.load.*",
            callback=self._handle_service_load_event,
            subscriber="message_router"
        )
    
    async def _handle_service_health_event(self, event: Event):
        """Handle service health events"""
        try:
            endpoint_id = event.payload.get("endpoint_id")
            health_status = event.payload.get("health_status", "unknown")
            
            if endpoint_id in self.service_endpoints:
                self.service_endpoints[endpoint_id].health_status = health_status
                
        except Exception as e:
            self.logger.error(f"Error handling service health event: {str(e)}")
    
    async def _handle_service_load_event(self, event: Event):
        """Handle service load events"""
        try:
            endpoint_id = event.payload.get("endpoint_id")
            load_metrics = event.payload.get("load_metrics", {})
            
            if endpoint_id in self.load_metrics:
                self.load_metrics[endpoint_id].update(load_metrics)
                
        except Exception as e:
            self.logger.error(f"Error handling service load event: {str(e)}")
    
    async def _health_monitoring_loop(self):
        """Monitor service health"""
        while True:
            try:
                await asyncio.sleep(30)  # Check every 30 seconds
                
                current_time = datetime.now(timezone.utc)
                
                for endpoint in self.service_endpoints.values():
                    # Check if endpoint has been inactive
                    if current_time - endpoint.last_activity > timedelta(minutes=5):
                        if endpoint.health_status == "healthy":
                            endpoint.health_status = "stale"
                        elif endpoint.health_status == "stale":
                            endpoint.health_status = "unhealthy"
                            endpoint.active = False
                
            except Exception as e:
                self.logger.error(f"Error in health monitoring: {str(e)}")
    
    async def _load_balancing_loop(self):
        """Update load balancing metrics"""
        while True:
            try:
                await asyncio.sleep(60)  # Update every minute
                
                # Reset metrics for next period
                for endpoint_id in self.load_metrics:
                    metrics = self.load_metrics[endpoint_id]
                    metrics["requests_per_minute"] = 0.0
                
            except Exception as e:
                self.logger.error(f"Error in load balancing loop: {str(e)}")
    
    async def get_routing_stats(self) -> Dict[str, Any]:
        """Get routing statistics"""
        return {
            "routing_stats": self.routing_stats.copy(),
            "service_endpoints": len(self.service_endpoints),
            "active_endpoints": sum(1 for e in self.service_endpoints.values() if e.active),
            "routing_rules": len(self.routing_rules),
            "active_routes": len(self.active_routes),
            "role_mappings": {
                role.value: len(endpoints) 
                for role, endpoints in self.role_mappings.items()
            }
        }
    
    async def get_service_health(self) -> Dict[str, Any]:
        """Get service health status"""
        health_summary = {}
        
        for endpoint in self.service_endpoints.values():
            role = endpoint.service_role.value
            if role not in health_summary:
                health_summary[role] = {
                    "healthy": 0,
                    "unhealthy": 0,
                    "stale": 0,
                    "total": 0
                }
            
            health_summary[role][endpoint.health_status] += 1
            health_summary[role]["total"] += 1
        
        return health_summary


# Global message router instance
_global_message_router: Optional[MessageRouter] = None


def get_message_router() -> MessageRouter:
    """Get global message router instance"""
    global _global_message_router
    if _global_message_router is None:
        _global_message_router = MessageRouter()
    return _global_message_router


async def initialize_message_router(event_bus: Optional[EventBus] = None) -> MessageRouter:
    """Initialize and start the global message router"""
    global _global_message_router
    _global_message_router = MessageRouter(event_bus)
    await _global_message_router.initialize()
    return _global_message_router