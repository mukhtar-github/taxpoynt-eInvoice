"""
Core Platform: Pub-Sub Coordinator
Advanced publish-subscribe coordination for event-driven architecture
"""
import asyncio
import json
import logging
import uuid
import fnmatch
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Set, Union, Callable, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from collections import defaultdict
import weakref

from .event_bus import Event, EventBus, EventScope, EventPriority, get_event_bus
from .message_router import ServiceRole

logger = logging.getLogger(__name__)


class SubscriptionType(str, Enum):
    """Types of subscriptions"""
    PERSISTENT = "persistent"       # Survives restarts
    TEMPORARY = "temporary"         # Session-based
    DURABLE = "durable"            # Guaranteed delivery
    EPHEMERAL = "ephemeral"        # Best effort delivery


class DeliveryMode(str, Enum):
    """Message delivery modes"""
    AT_MOST_ONCE = "at_most_once"     # Fire and forget
    AT_LEAST_ONCE = "at_least_once"   # Guaranteed delivery (may duplicate)
    EXACTLY_ONCE = "exactly_once"     # Exactly once delivery


class TopicType(str, Enum):
    """Types of topics"""
    BROADCAST = "broadcast"         # All subscribers receive message
    ROUND_ROBIN = "round_robin"     # Distribute among subscribers
    PRIORITY = "priority"           # Highest priority subscriber gets message
    LOAD_BALANCED = "load_balanced" # Load-based distribution


@dataclass
class Topic:
    """Pub-Sub topic definition"""
    topic_id: str
    name: str
    description: str
    topic_type: TopicType = TopicType.BROADCAST
    scope: EventScope = EventScope.GLOBAL
    service_role: Optional[ServiceRole] = None
    retention_policy: Optional[timedelta] = None
    max_subscribers: Optional[int] = None
    allow_wildcards: bool = True
    filters: Dict[str, Any] = None
    metadata: Dict[str, Any] = None
    created_at: datetime = None
    
    def __post_init__(self):
        if self.filters is None:
            self.filters = {}
        if self.metadata is None:
            self.metadata = {}
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)


@dataclass
class Subscription:
    """Subscription to a topic"""
    subscription_id: str
    subscriber_id: str
    topic_pattern: str
    callback: Callable
    subscription_type: SubscriptionType = SubscriptionType.TEMPORARY
    delivery_mode: DeliveryMode = DeliveryMode.AT_MOST_ONCE
    priority: int = 0
    filters: Dict[str, Any] = None
    transform_rules: List[str] = None
    retry_policy: Dict[str, Any] = None
    created_at: datetime = None
    last_activity: datetime = None
    message_count: int = 0
    error_count: int = 0
    active: bool = True
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.filters is None:
            self.filters = {}
        if self.transform_rules is None:
            self.transform_rules = []
        if self.retry_policy is None:
            self.retry_policy = {"max_retries": 3, "backoff_factor": 2.0}
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)
        if self.last_activity is None:
            self.last_activity = self.created_at
        if self.metadata is None:
            self.metadata = {}


@dataclass
class Publication:
    """Published message"""
    publication_id: str
    topic: str
    payload: Dict[str, Any]
    publisher_id: str
    priority: EventPriority = EventPriority.NORMAL
    delivery_mode: DeliveryMode = DeliveryMode.AT_MOST_ONCE
    expiry: Optional[datetime] = None
    correlation_id: Optional[str] = None
    tenant_id: Optional[str] = None
    headers: Dict[str, Any] = None
    published_at: datetime = None
    
    def __post_init__(self):
        if self.headers is None:
            self.headers = {}
        if self.published_at is None:
            self.published_at = datetime.now(timezone.utc)


@dataclass
class DeliveryReceipt:
    """Delivery receipt for tracking"""
    receipt_id: str
    publication_id: str
    subscription_id: str
    delivery_status: str  # delivered, failed, retry
    delivery_time: datetime = None
    retry_count: int = 0
    error_message: Optional[str] = None
    
    def __post_init__(self):
        if self.delivery_time is None:
            self.delivery_time = datetime.now(timezone.utc)


class PubSubCoordinator:
    """
    Pub-Sub Coordinator for TaxPoynt Platform
    
    Advanced publish-subscribe system with:
    - Topic-based message routing
    - Multiple delivery guarantees
    - Subscription filtering and transformation
    - Dead letter handling
    - Message replay capabilities
    - Cross-service coordination
    """
    
    def __init__(self, event_bus: Optional[EventBus] = None):
        """Initialize the pub-sub coordinator"""
        self.event_bus = event_bus or get_event_bus()
        
        # Topic and subscription management
        self.topics: Dict[str, Topic] = {}
        self.subscriptions: Dict[str, Subscription] = {}
        self.topic_subscriptions: Dict[str, Set[str]] = defaultdict(set)
        self.subscriber_subscriptions: Dict[str, Set[str]] = defaultdict(set)
        
        # Message tracking
        self.publications: Dict[str, Publication] = {}
        self.delivery_receipts: Dict[str, DeliveryReceipt] = {}
        self.message_history: Dict[str, List[Publication]] = defaultdict(list)
        
        # Delivery guarantees
        self.pending_deliveries: Dict[str, Publication] = {}
        self.failed_deliveries: Dict[str, Publication] = {}
        self.retry_queue: List[Tuple[datetime, Publication, Subscription]] = []
        
        # Pattern matching cache
        self.pattern_cache: Dict[str, List[str]] = {}
        self.cache_expiry = datetime.now(timezone.utc)
        
        # Transformers and filters
        self.message_transformers: Dict[str, Callable] = {}
        self.message_filters: Dict[str, Callable] = {}
        
        # Round-robin state for load balancing
        self.round_robin_state: Dict[str, int] = {}
        
        # Statistics
        self.stats = {
            "topics_created": 0,
            "subscriptions_created": 0,
            "messages_published": 0,
            "messages_delivered": 0,
            "delivery_failures": 0,
            "retries_attempted": 0
        }
        
        # Weak references for cleanup
        self.callback_refs = weakref.WeakValueDictionary()
        
        self.logger = logging.getLogger(__name__)
        self.is_initialized = False
        self.is_running = False
    
    async def initialize(self):
        """Initialize the pub-sub coordinator"""
        if self.is_initialized:
            return
        
        self.logger.info("Initializing Pub-Sub Coordinator")
        
        # Set up default topics
        await self._setup_default_topics()
        
        # Register with event bus
        await self._register_event_handlers()
        
        # Setup built-in transformers and filters
        await self._setup_transformers_and_filters()
        
        self.is_initialized = True
        self.logger.info("Pub-Sub Coordinator initialized")
    
    async def start(self):
        """Start the pub-sub coordinator"""
        if not self.is_initialized:
            await self.initialize()
        
        if self.is_running:
            return
        
        self.is_running = True
        self.logger.info("Starting Pub-Sub Coordinator")
        
        # Start background tasks
        asyncio.create_task(self._retry_processor())
        asyncio.create_task(self._cleanup_task())
        asyncio.create_task(self._metrics_task())
        
        self.logger.info("Pub-Sub Coordinator started")
    
    async def stop(self):
        """Stop the pub-sub coordinator"""
        if not self.is_running:
            return
        
        self.logger.info("Stopping Pub-Sub Coordinator")
        self.is_running = False
        
        # Process remaining retries
        await self._process_retry_queue(force=True)
        
        self.logger.info("Pub-Sub Coordinator stopped")
    
    async def create_topic(self, topic: Topic) -> bool:
        """Create a new topic"""
        try:
            if topic.topic_id in self.topics:
                self.logger.warning(f"Topic already exists: {topic.topic_id}")
                return False
            
            self.topics[topic.topic_id] = topic
            self.topic_subscriptions[topic.topic_id] = set()
            
            self.stats["topics_created"] += 1
            
            self.logger.info(f"Topic created: {topic.name} ({topic.topic_id})")
            
            # Emit topic created event
            await self.event_bus.emit(
                event_type="pubsub.topic.created",
                payload={
                    "topic_id": topic.topic_id,
                    "name": topic.name,
                    "topic_type": topic.topic_type.value,
                    "scope": topic.scope.value
                },
                source="pubsub_coordinator",
                scope=EventScope.GLOBAL
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error creating topic: {str(e)}")
            return False
    
    async def delete_topic(self, topic_id: str, force: bool = False) -> bool:
        """Delete a topic"""
        try:
            if topic_id not in self.topics:
                return False
            
            # Check for active subscriptions
            if not force and self.topic_subscriptions[topic_id]:
                self.logger.warning(f"Cannot delete topic with active subscriptions: {topic_id}")
                return False
            
            # Remove all subscriptions
            for sub_id in list(self.topic_subscriptions[topic_id]):
                await self.unsubscribe(sub_id)
            
            # Remove topic
            topic = self.topics[topic_id]
            del self.topics[topic_id]
            del self.topic_subscriptions[topic_id]
            
            # Clear pattern cache
            self._clear_pattern_cache()
            
            self.logger.info(f"Topic deleted: {topic.name} ({topic_id})")
            
            # Emit topic deleted event
            await self.event_bus.emit(
                event_type="pubsub.topic.deleted",
                payload={"topic_id": topic_id, "name": topic.name},
                source="pubsub_coordinator",
                scope=EventScope.GLOBAL
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error deleting topic {topic_id}: {str(e)}")
            return False
    
    async def subscribe(
        self,
        subscriber_id: str,
        topic_pattern: str,
        callback: Callable,
        subscription_type: SubscriptionType = SubscriptionType.TEMPORARY,
        delivery_mode: DeliveryMode = DeliveryMode.AT_MOST_ONCE,
        priority: int = 0,
        filters: Dict[str, Any] = None,
        transform_rules: List[str] = None
    ) -> str:
        """Subscribe to topics matching a pattern"""
        try:
            subscription_id = str(uuid.uuid4())
            
            subscription = Subscription(
                subscription_id=subscription_id,
                subscriber_id=subscriber_id,
                topic_pattern=topic_pattern,
                callback=callback,
                subscription_type=subscription_type,
                delivery_mode=delivery_mode,
                priority=priority,
                filters=filters or {},
                transform_rules=transform_rules or []
            )
            
            # Store subscription
            self.subscriptions[subscription_id] = subscription
            self.subscriber_subscriptions[subscriber_id].add(subscription_id)
            
            # Map to matching topics
            await self._map_subscription_to_topics(subscription)
            
            # Store weak reference to callback
            self.callback_refs[subscription_id] = callback
            
            self.stats["subscriptions_created"] += 1
            
            self.logger.info(f"Subscription created: {subscriber_id} -> {topic_pattern}")
            
            # Emit subscription created event
            await self.event_bus.emit(
                event_type="pubsub.subscription.created",
                payload={
                    "subscription_id": subscription_id,
                    "subscriber_id": subscriber_id,
                    "topic_pattern": topic_pattern,
                    "delivery_mode": delivery_mode.value
                },
                source="pubsub_coordinator",
                scope=EventScope.GLOBAL
            )
            
            return subscription_id
            
        except Exception as e:
            self.logger.error(f"Error creating subscription: {str(e)}")
            raise
    
    async def unsubscribe(self, subscription_id: str) -> bool:
        """Unsubscribe from topics"""
        try:
            if subscription_id not in self.subscriptions:
                return False
            
            subscription = self.subscriptions[subscription_id]
            
            # Remove from topic mappings
            for topic_id in list(self.topic_subscriptions.keys()):
                if subscription_id in self.topic_subscriptions[topic_id]:
                    self.topic_subscriptions[topic_id].remove(subscription_id)
            
            # Remove from subscriber mappings
            if subscription.subscriber_id in self.subscriber_subscriptions:
                self.subscriber_subscriptions[subscription.subscriber_id].discard(subscription_id)
                
                # Clean up empty subscriber entries
                if not self.subscriber_subscriptions[subscription.subscriber_id]:
                    del self.subscriber_subscriptions[subscription.subscriber_id]
            
            # Remove subscription
            del self.subscriptions[subscription_id]
            
            # Remove weak reference
            if subscription_id in self.callback_refs:
                del self.callback_refs[subscription_id]
            
            self.logger.info(f"Subscription removed: {subscription_id}")
            
            # Emit subscription removed event
            await self.event_bus.emit(
                event_type="pubsub.subscription.removed",
                payload={
                    "subscription_id": subscription_id,
                    "subscriber_id": subscription.subscriber_id
                },
                source="pubsub_coordinator",
                scope=EventScope.GLOBAL
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error unsubscribing {subscription_id}: {str(e)}")
            return False
    
    async def publish(
        self,
        topic: str,
        payload: Dict[str, Any],
        publisher_id: str,
        priority: EventPriority = EventPriority.NORMAL,
        delivery_mode: DeliveryMode = DeliveryMode.AT_MOST_ONCE,
        expiry: Optional[datetime] = None,
        correlation_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        headers: Dict[str, Any] = None
    ) -> str:
        """Publish a message to a topic"""
        try:
            publication = Publication(
                publication_id=str(uuid.uuid4()),
                topic=topic,
                payload=payload,
                publisher_id=publisher_id,
                priority=priority,
                delivery_mode=delivery_mode,
                expiry=expiry,
                correlation_id=correlation_id,
                tenant_id=tenant_id,
                headers=headers or {}
            )
            
            # Store publication
            self.publications[publication.publication_id] = publication
            
            # Add to message history for topic
            self.message_history[topic].append(publication)
            
            # Limit history size
            if len(self.message_history[topic]) > 1000:
                self.message_history[topic] = self.message_history[topic][-1000:]
            
            # Find matching subscriptions
            matching_subscriptions = await self._find_matching_subscriptions(topic)
            
            if not matching_subscriptions:
                self.logger.debug(f"No subscribers found for topic: {topic}")
            else:
                # Deliver to subscribers
                await self._deliver_to_subscribers(publication, matching_subscriptions)
            
            self.stats["messages_published"] += 1
            
            self.logger.debug(f"Message published to {topic}: {publication.publication_id}")
            
            return publication.publication_id
            
        except Exception as e:
            self.logger.error(f"Error publishing to {topic}: {str(e)}")
            raise
    
    async def publish_to_scope(
        self,
        topic: str,
        payload: Dict[str, Any],
        target_scope: EventScope,
        publisher_id: str,
        **kwargs
    ) -> str:
        """Publish message to specific scope"""
        # Filter subscriptions by scope
        scoped_topic = f"{target_scope.value}.{topic}"
        return await self.publish(scoped_topic, payload, publisher_id, **kwargs)
    
    async def replay_messages(
        self,
        topic: str,
        subscriber_id: str,
        from_time: Optional[datetime] = None,
        to_time: Optional[datetime] = None,
        max_messages: int = 100
    ) -> int:
        """Replay historical messages to a subscriber"""
        try:
            if topic not in self.message_history:
                return 0
            
            # Get subscriber subscriptions
            subscriber_subs = self.subscriber_subscriptions.get(subscriber_id, set())
            if not subscriber_subs:
                return 0
            
            # Filter messages by time range
            messages = self.message_history[topic]
            if from_time:
                messages = [m for m in messages if m.published_at >= from_time]
            if to_time:
                messages = [m for m in messages if m.published_at <= to_time]
            
            # Limit number of messages
            messages = messages[-max_messages:]
            
            replayed_count = 0
            
            for message in messages:
                # Find matching subscriptions for this subscriber
                for sub_id in subscriber_subs:
                    if sub_id in self.subscriptions:
                        subscription = self.subscriptions[sub_id]
                        if self._topic_matches_pattern(topic, subscription.topic_pattern):
                            await self._deliver_to_subscription(message, subscription, is_replay=True)
                            replayed_count += 1
            
            self.logger.info(f"Replayed {replayed_count} messages to {subscriber_id}")
            
            return replayed_count
            
        except Exception as e:
            self.logger.error(f"Error replaying messages: {str(e)}")
            return 0
    
    async def _setup_default_topics(self):
        """Set up default system topics"""
        default_topics = [
            Topic(
                topic_id="system_events",
                name="System Events",
                description="Core system events",
                topic_type=TopicType.BROADCAST,
                scope=EventScope.GLOBAL
            ),
            Topic(
                topic_id="si_events",
                name="SI Service Events", 
                description="System Integrator service events",
                topic_type=TopicType.BROADCAST,
                scope=EventScope.SI_SERVICES,
                service_role=ServiceRole.SYSTEM_INTEGRATOR
            ),
            Topic(
                topic_id="app_events",
                name="APP Service Events",
                description="Access Point Provider service events", 
                topic_type=TopicType.BROADCAST,
                scope=EventScope.APP_SERVICES,
                service_role=ServiceRole.ACCESS_POINT_PROVIDER
            ),
            Topic(
                topic_id="hybrid_events",
                name="Hybrid Service Events",
                description="Cross-cutting hybrid service events",
                topic_type=TopicType.BROADCAST,
                scope=EventScope.HYBRID,
                service_role=ServiceRole.HYBRID
            ),
            Topic(
                topic_id="notifications",
                name="Notifications",
                description="User and system notifications",
                topic_type=TopicType.ROUND_ROBIN,
                scope=EventScope.GLOBAL
            ),
            Topic(
                topic_id="alerts",
                name="System Alerts",
                description="Critical system alerts",
                topic_type=TopicType.BROADCAST,
                scope=EventScope.GLOBAL
            ),
            Topic(
                topic_id="metrics",
                name="System Metrics",
                description="Performance and health metrics",
                topic_type=TopicType.LOAD_BALANCED,
                scope=EventScope.GLOBAL,
                retention_policy=timedelta(hours=24)
            )
        ]
        
        for topic in default_topics:
            await self.create_topic(topic)
    
    async def _map_subscription_to_topics(self, subscription: Subscription):
        """Map subscription to matching topics"""
        for topic_id, topic in self.topics.items():
            if self._topic_matches_pattern(topic_id, subscription.topic_pattern):
                self.topic_subscriptions[topic_id].add(subscription.subscription_id)
        
        # Also check topic names
        for topic_id, topic in self.topics.items():
            if self._topic_matches_pattern(topic.name, subscription.topic_pattern):
                self.topic_subscriptions[topic_id].add(subscription.subscription_id)
    
    async def _find_matching_subscriptions(self, topic: str) -> List[Subscription]:
        """Find subscriptions matching a topic"""
        matching_subscriptions = []
        
        # Direct topic match
        if topic in self.topic_subscriptions:
            for sub_id in self.topic_subscriptions[topic]:
                if sub_id in self.subscriptions and self.subscriptions[sub_id].active:
                    matching_subscriptions.append(self.subscriptions[sub_id])
        
        # Pattern matching for all subscriptions
        for subscription in self.subscriptions.values():
            if (subscription.active and 
                self._topic_matches_pattern(topic, subscription.topic_pattern) and
                subscription not in matching_subscriptions):
                matching_subscriptions.append(subscription)
        
        return matching_subscriptions
    
    def _topic_matches_pattern(self, topic: str, pattern: str) -> bool:
        """Check if topic matches subscription pattern"""
        if pattern == "*":
            return True
        if pattern == topic:
            return True
        
        # Support for wildcard patterns
        if "*" in pattern or "?" in pattern:
            return fnmatch.fnmatch(topic, pattern)
        
        # Support for hierarchical patterns (e.g., "events.*", "*.notifications")
        if "." in pattern:
            pattern_parts = pattern.split(".")
            topic_parts = topic.split(".")
            
            if len(pattern_parts) != len(topic_parts):
                return False
            
            for p_part, t_part in zip(pattern_parts, topic_parts):
                if p_part != "*" and p_part != t_part:
                    return False
            
            return True
        
        return False
    
    async def _deliver_to_subscribers(self, publication: Publication, subscriptions: List[Subscription]):
        """Deliver message to matching subscribers"""
        if not subscriptions:
            return
        
        # Find topic configuration
        topic_config = None
        for topic in self.topics.values():
            if topic.topic_id == publication.topic or topic.name == publication.topic:
                topic_config = topic
                break
        
        if not topic_config:
            # Default to broadcast for unknown topics
            topic_type = TopicType.BROADCAST
        else:
            topic_type = topic_config.topic_type
        
        # Deliver based on topic type
        if topic_type == TopicType.BROADCAST:
            await self._broadcast_delivery(publication, subscriptions)
        elif topic_type == TopicType.ROUND_ROBIN:
            await self._round_robin_delivery(publication, subscriptions)
        elif topic_type == TopicType.PRIORITY:
            await self._priority_delivery(publication, subscriptions)
        elif topic_type == TopicType.LOAD_BALANCED:
            await self._load_balanced_delivery(publication, subscriptions)
    
    async def _broadcast_delivery(self, publication: Publication, subscriptions: List[Subscription]):
        """Deliver message to all subscribers"""
        delivery_tasks = []
        
        for subscription in subscriptions:
            task = asyncio.create_task(
                self._deliver_to_subscription(publication, subscription)
            )
            delivery_tasks.append(task)
        
        if delivery_tasks:
            await asyncio.gather(*delivery_tasks, return_exceptions=True)
    
    async def _round_robin_delivery(self, publication: Publication, subscriptions: List[Subscription]):
        """Deliver message using round-robin"""
        if not subscriptions:
            return
        
        # Get current round-robin index for this topic
        topic_key = f"rr_{publication.topic}"
        current_index = self.round_robin_state.get(topic_key, 0)
        
        # Select subscription
        selected_subscription = subscriptions[current_index % len(subscriptions)]
        
        # Update round-robin state
        self.round_robin_state[topic_key] = (current_index + 1) % len(subscriptions)
        
        # Deliver message
        await self._deliver_to_subscription(publication, selected_subscription)
    
    async def _priority_delivery(self, publication: Publication, subscriptions: List[Subscription]):
        """Deliver message to highest priority subscriber"""
        if not subscriptions:
            return
        
        # Sort by priority (highest first)
        sorted_subscriptions = sorted(subscriptions, key=lambda s: s.priority, reverse=True)
        
        # Deliver to highest priority subscriber
        await self._deliver_to_subscription(publication, sorted_subscriptions[0])
    
    async def _load_balanced_delivery(self, publication: Publication, subscriptions: List[Subscription]):
        """Deliver message using load balancing"""
        if not subscriptions:
            return
        
        # Simple load balancing based on message count
        # Select subscription with lowest message count
        selected_subscription = min(subscriptions, key=lambda s: s.message_count)
        
        await self._deliver_to_subscription(publication, selected_subscription)
    
    async def _deliver_to_subscription(
        self, 
        publication: Publication, 
        subscription: Subscription,
        is_replay: bool = False
    ):
        """Deliver message to a specific subscription"""
        try:
            # Check filters
            if not await self._apply_filters(publication, subscription):
                return
            
            # Apply transformations
            transformed_payload = await self._apply_transformations(publication, subscription)
            
            # Prepare delivery payload
            delivery_payload = {
                "publication_id": publication.publication_id,
                "topic": publication.topic,
                "payload": transformed_payload,
                "publisher_id": publication.publisher_id,
                "priority": publication.priority.value,
                "correlation_id": publication.correlation_id,
                "tenant_id": publication.tenant_id,
                "headers": publication.headers,
                "published_at": publication.published_at.isoformat(),
                "is_replay": is_replay
            }
            
            # Execute callback
            if asyncio.iscoroutinefunction(subscription.callback):
                result = await subscription.callback(delivery_payload)
            else:
                result = subscription.callback(delivery_payload)
            
            # Update subscription activity
            subscription.last_activity = datetime.now(timezone.utc)
            subscription.message_count += 1
            
            # Handle delivery guarantee
            if subscription.delivery_mode == DeliveryMode.AT_LEAST_ONCE:
                # Store for acknowledgment tracking
                self.pending_deliveries[f"{publication.publication_id}:{subscription.subscription_id}"] = publication
            
            # Create delivery receipt
            receipt = DeliveryReceipt(
                receipt_id=str(uuid.uuid4()),
                publication_id=publication.publication_id,
                subscription_id=subscription.subscription_id,
                delivery_status="delivered"
            )
            
            self.delivery_receipts[receipt.receipt_id] = receipt
            self.stats["messages_delivered"] += 1
            
            self.logger.debug(f"Message delivered to {subscription.subscriber_id}")
            
        except Exception as e:
            self.logger.error(f"Error delivering message to {subscription.subscription_id}: {str(e)}")
            
            # Handle delivery failure
            await self._handle_delivery_failure(publication, subscription, str(e))
    
    async def _apply_filters(self, publication: Publication, subscription: Subscription) -> bool:
        """Apply subscription filters"""
        try:
            for filter_name, filter_config in subscription.filters.items():
                if filter_name in self.message_filters:
                    filter_func = self.message_filters[filter_name]
                    if not await filter_func(publication, filter_config):
                        return False
                elif filter_name in publication.payload:
                    # Simple equality filter
                    if publication.payload[filter_name] != filter_config:
                        return False
                elif filter_name in publication.headers:
                    # Header filter
                    if publication.headers[filter_name] != filter_config:
                        return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error applying filters: {str(e)}")
            return True  # Default to allow delivery on filter error
    
    async def _apply_transformations(self, publication: Publication, subscription: Subscription) -> Dict[str, Any]:
        """Apply message transformations"""
        try:
            transformed_payload = publication.payload.copy()
            
            for transform_rule in subscription.transform_rules:
                if transform_rule in self.message_transformers:
                    transformer = self.message_transformers[transform_rule]
                    transformed_payload = await transformer(transformed_payload, publication.headers)
            
            return transformed_payload
            
        except Exception as e:
            self.logger.error(f"Error applying transformations: {str(e)}")
            return publication.payload  # Return original on error
    
    async def _handle_delivery_failure(self, publication: Publication, subscription: Subscription, error: str):
        """Handle message delivery failure"""
        try:
            subscription.error_count += 1
            
            # Create failure receipt
            receipt = DeliveryReceipt(
                receipt_id=str(uuid.uuid4()),
                publication_id=publication.publication_id,
                subscription_id=subscription.subscription_id,
                delivery_status="failed",
                error_message=error
            )
            
            self.delivery_receipts[receipt.receipt_id] = receipt
            self.stats["delivery_failures"] += 1
            
            # Check retry policy
            retry_policy = subscription.retry_policy
            max_retries = retry_policy.get("max_retries", 3)
            
            if receipt.retry_count < max_retries:
                # Schedule retry
                backoff_factor = retry_policy.get("backoff_factor", 2.0)
                retry_delay = min(60.0, (backoff_factor ** receipt.retry_count))
                retry_time = datetime.now(timezone.utc) + timedelta(seconds=retry_delay)
                
                self.retry_queue.append((retry_time, publication, subscription))
                self.stats["retries_attempted"] += 1
                
                self.logger.info(f"Scheduled retry for {subscription.subscription_id} in {retry_delay}s")
            else:
                # Move to failed deliveries
                self.failed_deliveries[f"{publication.publication_id}:{subscription.subscription_id}"] = publication
                
                self.logger.warning(f"Max retries exceeded for {subscription.subscription_id}")
            
        except Exception as e:
            self.logger.error(f"Error handling delivery failure: {str(e)}")
    
    async def _setup_transformers_and_filters(self):
        """Set up built-in message transformers and filters"""
        # Built-in transformers
        self.message_transformers["add_timestamp"] = self._add_timestamp_transformer
        self.message_transformers["flatten_payload"] = self._flatten_payload_transformer
        self.message_transformers["extract_fields"] = self._extract_fields_transformer
        
        # Built-in filters
        self.message_filters["tenant_filter"] = self._tenant_filter
        self.message_filters["priority_filter"] = self._priority_filter
        self.message_filters["time_filter"] = self._time_filter
    
    async def _add_timestamp_transformer(self, payload: Dict[str, Any], headers: Dict[str, Any]) -> Dict[str, Any]:
        """Add timestamp to payload"""
        payload["_transformed_at"] = datetime.now(timezone.utc).isoformat()
        return payload
    
    async def _flatten_payload_transformer(self, payload: Dict[str, Any], headers: Dict[str, Any]) -> Dict[str, Any]:
        """Flatten nested payload structure"""
        def flatten_dict(d, parent_key='', sep='_'):
            items = []
            for k, v in d.items():
                new_key = f"{parent_key}{sep}{k}" if parent_key else k
                if isinstance(v, dict):
                    items.extend(flatten_dict(v, new_key, sep=sep).items())
                else:
                    items.append((new_key, v))
            return dict(items)
        
        return flatten_dict(payload)
    
    async def _extract_fields_transformer(self, payload: Dict[str, Any], headers: Dict[str, Any]) -> Dict[str, Any]:
        """Extract specific fields from payload"""
        # This would be configured per subscription
        return payload
    
    async def _tenant_filter(self, publication: Publication, filter_config: Any) -> bool:
        """Filter by tenant ID"""
        return publication.tenant_id == filter_config
    
    async def _priority_filter(self, publication: Publication, filter_config: Any) -> bool:
        """Filter by message priority"""
        if isinstance(filter_config, str):
            return publication.priority.value == filter_config
        elif isinstance(filter_config, list):
            return publication.priority.value in filter_config
        return True
    
    async def _time_filter(self, publication: Publication, filter_config: Dict[str, Any]) -> bool:
        """Filter by time range"""
        current_time = datetime.now(timezone.utc)
        
        if "start_time" in filter_config:
            start_time = datetime.fromisoformat(filter_config["start_time"])
            if current_time < start_time:
                return False
        
        if "end_time" in filter_config:
            end_time = datetime.fromisoformat(filter_config["end_time"])
            if current_time > end_time:
                return False
        
        return True
    
    async def _retry_processor(self):
        """Process retry queue"""
        while self.is_running:
            try:
                await asyncio.sleep(5)  # Check every 5 seconds
                
                current_time = datetime.now(timezone.utc)
                ready_retries = []
                
                # Find retries that are ready
                for retry_time, publication, subscription in self.retry_queue[:]:
                    if retry_time <= current_time:
                        ready_retries.append((publication, subscription))
                        self.retry_queue.remove((retry_time, publication, subscription))
                
                # Process ready retries
                for publication, subscription in ready_retries:
                    await self._deliver_to_subscription(publication, subscription)
                
            except Exception as e:
                self.logger.error(f"Error in retry processor: {str(e)}")
    
    async def _process_retry_queue(self, force: bool = False):
        """Process all pending retries"""
        try:
            retries_to_process = self.retry_queue.copy() if force else []
            
            if not force:
                current_time = datetime.now(timezone.utc)
                retries_to_process = [
                    (pub, sub) for retry_time, pub, sub in self.retry_queue
                    if retry_time <= current_time
                ]
            
            for publication, subscription in retries_to_process:
                try:
                    await self._deliver_to_subscription(publication, subscription)
                except Exception as e:
                    self.logger.error(f"Error processing retry: {str(e)}")
            
            if force:
                self.retry_queue.clear()
                
        except Exception as e:
            self.logger.error(f"Error processing retry queue: {str(e)}")
    
    async def _cleanup_task(self):
        """Periodic cleanup of old data"""
        while self.is_running:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes
                
                current_time = datetime.now(timezone.utc)
                cutoff_time = current_time - timedelta(hours=24)
                
                # Clean old publications
                old_publications = [
                    pub_id for pub_id, pub in self.publications.items()
                    if pub.published_at < cutoff_time
                ]
                
                for pub_id in old_publications:
                    del self.publications[pub_id]
                
                # Clean old delivery receipts
                old_receipts = [
                    receipt_id for receipt_id, receipt in self.delivery_receipts.items()
                    if receipt.delivery_time < cutoff_time
                ]
                
                for receipt_id in old_receipts:
                    del self.delivery_receipts[receipt_id]
                
                # Clear pattern cache periodically
                if current_time > self.cache_expiry:
                    self._clear_pattern_cache()
                
                if old_publications or old_receipts:
                    self.logger.debug(f"Cleaned up {len(old_publications)} publications and {len(old_receipts)} receipts")
                
            except Exception as e:
                self.logger.error(f"Error in cleanup task: {str(e)}")
    
    async def _metrics_task(self):
        """Emit periodic metrics"""
        while self.is_running:
            try:
                await asyncio.sleep(60)  # Emit every minute
                
                # Emit pub-sub metrics
                await self.event_bus.emit(
                    event_type="pubsub.metrics",
                    payload={
                        "stats": self.stats.copy(),
                        "topics": len(self.topics),
                        "subscriptions": len(self.subscriptions),
                        "pending_deliveries": len(self.pending_deliveries),
                        "failed_deliveries": len(self.failed_deliveries),
                        "retry_queue_size": len(self.retry_queue)
                    },
                    source="pubsub_coordinator",
                    scope=EventScope.GLOBAL,
                    priority=EventPriority.LOW
                )
                
            except Exception as e:
                self.logger.error(f"Error in metrics task: {str(e)}")
    
    def _clear_pattern_cache(self):
        """Clear pattern matching cache"""
        self.pattern_cache.clear()
        self.cache_expiry = datetime.now(timezone.utc) + timedelta(minutes=10)
    
    async def _register_event_handlers(self):
        """Register handlers with event bus"""
        await self.event_bus.subscribe(
            event_pattern="pubsub.*",
            callback=self._handle_pubsub_event,
            subscriber="pubsub_coordinator"
        )
    
    async def _handle_pubsub_event(self, event: Event):
        """Handle pub-sub related events"""
        try:
            if event.event_type == "pubsub.subscription.ack":
                # Handle subscription acknowledgment
                pub_id = event.payload.get("publication_id")
                sub_id = event.payload.get("subscription_id")
                
                if pub_id and sub_id:
                    delivery_key = f"{pub_id}:{sub_id}"
                    if delivery_key in self.pending_deliveries:
                        del self.pending_deliveries[delivery_key]
            
        except Exception as e:
            self.logger.error(f"Error handling pub-sub event: {str(e)}")
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get pub-sub statistics"""
        return {
            "stats": self.stats.copy(),
            "topics": len(self.topics),
            "subscriptions": len(self.subscriptions),
            "active_subscriptions": sum(1 for s in self.subscriptions.values() if s.active),
            "pending_deliveries": len(self.pending_deliveries),
            "failed_deliveries": len(self.failed_deliveries),
            "retry_queue_size": len(self.retry_queue),
            "publications": len(self.publications),
            "delivery_receipts": len(self.delivery_receipts)
        }
    
    async def get_topic_info(self, topic_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a topic"""
        if topic_id not in self.topics:
            return None
        
        topic = self.topics[topic_id]
        subscriber_count = len(self.topic_subscriptions.get(topic_id, set()))
        message_count = len(self.message_history.get(topic_id, []))
        
        return {
            "topic": asdict(topic),
            "subscriber_count": subscriber_count,
            "message_count": message_count,
            "last_message": (
                self.message_history[topic_id][-1].published_at.isoformat()
                if message_count > 0 else None
            )
        }
    
    async def get_subscription_info(self, subscription_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a subscription"""
        if subscription_id not in self.subscriptions:
            return None
        
        subscription = self.subscriptions[subscription_id]
        
        return {
            "subscription_id": subscription_id,
            "subscriber_id": subscription.subscriber_id,
            "topic_pattern": subscription.topic_pattern,
            "subscription_type": subscription.subscription_type.value,
            "delivery_mode": subscription.delivery_mode.value,
            "message_count": subscription.message_count,
            "error_count": subscription.error_count,
            "last_activity": subscription.last_activity.isoformat(),
            "active": subscription.active
        }


# Global pub-sub coordinator instance
_global_pubsub_coordinator: Optional[PubSubCoordinator] = None


def get_pubsub_coordinator() -> PubSubCoordinator:
    """Get global pub-sub coordinator instance"""
    global _global_pubsub_coordinator
    if _global_pubsub_coordinator is None:
        _global_pubsub_coordinator = PubSubCoordinator()
    return _global_pubsub_coordinator


async def initialize_pubsub_coordinator(event_bus: Optional[EventBus] = None) -> PubSubCoordinator:
    """Initialize and start the global pub-sub coordinator"""
    global _global_pubsub_coordinator
    _global_pubsub_coordinator = PubSubCoordinator(event_bus)
    await _global_pubsub_coordinator.start()
    return _global_pubsub_coordinator