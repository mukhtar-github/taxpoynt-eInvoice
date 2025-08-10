"""
Core Platform: Event Bus
Central event-driven communication system for the TaxPoynt platform
"""
import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Callable, Union, Set
from dataclasses import dataclass, asdict
from enum import Enum
import weakref
from concurrent.futures import ThreadPoolExecutor
import traceback

logger = logging.getLogger(__name__)


class EventPriority(str, Enum):
    """Event priority levels"""
    CRITICAL = "critical"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


class EventScope(str, Enum):
    """Event scope for targeting"""
    GLOBAL = "global"           # Platform-wide events
    SI_SERVICES = "si_services" # System Integrator services only
    APP_SERVICES = "app_services" # Access Point Provider services only
    HYBRID = "hybrid"           # Cross-cutting hybrid services
    TENANT = "tenant"           # Tenant-specific events


class EventStatus(str, Enum):
    """Event processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    DEAD_LETTER = "dead_letter"


@dataclass
class Event:
    """Core event structure"""
    event_id: str
    event_type: str
    payload: Dict[str, Any]
    source: str
    scope: EventScope
    priority: EventPriority
    timestamp: datetime
    tenant_id: Optional[str] = None
    correlation_id: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    tags: List[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Event':
        """Create event from dictionary"""
        data = data.copy()
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        data['scope'] = EventScope(data['scope'])
        data['priority'] = EventPriority(data['priority'])
        return cls(**data)


@dataclass
class EventHandler:
    """Event handler registration"""
    handler_id: str
    event_pattern: str  # Can be exact match or glob pattern
    callback: Callable
    scope: EventScope
    priority: int = 0
    active: bool = True
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class EventSubscription:
    """Event subscription tracking"""
    subscription_id: str
    subscriber: str
    event_patterns: List[str]
    scope: EventScope
    callback: Callable
    filters: Dict[str, Any] = None
    created_at: datetime = None
    last_activity: datetime = None
    
    def __post_init__(self):
        if self.filters is None:
            self.filters = {}
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)
        if self.last_activity is None:
            self.last_activity = self.created_at


class EventBus:
    """
    Central Event Bus for TaxPoynt Platform
    
    Manages event-driven communication between services, ensuring:
    - Reliable message delivery
    - Role-based event scoping
    - Priority-based processing
    - Dead letter handling
    - Retry mechanisms
    """
    
    def __init__(self, max_workers: int = 10, enable_persistence: bool = True):
        """Initialize the event bus"""
        self.max_workers = max_workers
        self.enable_persistence = enable_persistence
        
        # Event handlers and subscriptions
        self.handlers: Dict[str, EventHandler] = {}
        self.subscriptions: Dict[str, EventSubscription] = {}
        self.event_patterns: Dict[str, List[str]] = {}  # pattern -> handler_ids
        
        # Event queues by priority
        self.event_queues: Dict[EventPriority, asyncio.Queue] = {
            priority: asyncio.Queue() for priority in EventPriority
        }
        
        # Processing state
        self.processing_events: Dict[str, Event] = {}
        self.failed_events: Dict[str, Event] = {}
        self.completed_events: Dict[str, Event] = {}
        
        # Execution infrastructure
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.processing_tasks: Set[asyncio.Task] = set()
        self.is_running = False
        
        # Metrics and monitoring
        self.event_stats = {
            "total_events": 0,
            "processed_events": 0,
            "failed_events": 0,
            "retried_events": 0,
            "dead_letter_events": 0
        }
        
        # Weak references for cleanup
        self.handler_refs = weakref.WeakValueDictionary()
        
        self.logger = logging.getLogger(__name__)
    
    async def start(self):
        """Start the event bus processing"""
        if self.is_running:
            return
        
        self.is_running = True
        self.logger.info("Starting Event Bus")
        
        # Start processing tasks for each priority level
        for priority in EventPriority:
            task = asyncio.create_task(self._process_queue(priority))
            self.processing_tasks.add(task)
            task.add_done_callback(self.processing_tasks.discard)
        
        # Start maintenance task
        maintenance_task = asyncio.create_task(self._maintenance_loop())
        self.processing_tasks.add(maintenance_task)
        maintenance_task.add_done_callback(self.processing_tasks.discard)
        
        self.logger.info("Event Bus started successfully")
    
    async def stop(self):
        """Stop the event bus processing"""
        if not self.is_running:
            return
        
        self.logger.info("Stopping Event Bus")
        self.is_running = False
        
        # Cancel all processing tasks
        for task in self.processing_tasks:
            task.cancel()
        
        # Wait for tasks to complete
        if self.processing_tasks:
            await asyncio.gather(*self.processing_tasks, return_exceptions=True)
        
        # Shutdown executor
        self.executor.shutdown(wait=True)
        
        self.logger.info("Event Bus stopped")
    
    async def emit(
        self,
        event_type: str,
        payload: Dict[str, Any],
        source: str,
        scope: EventScope = EventScope.GLOBAL,
        priority: EventPriority = EventPriority.NORMAL,
        tenant_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        tags: List[str] = None,
        metadata: Dict[str, Any] = None
    ) -> str:
        """Emit an event to the bus"""
        try:
            event = Event(
                event_id=str(uuid.uuid4()),
                event_type=event_type,
                payload=payload,
                source=source,
                scope=scope,
                priority=priority,
                timestamp=datetime.now(timezone.utc),
                tenant_id=tenant_id,
                correlation_id=correlation_id,
                tags=tags or [],
                metadata=metadata or {}
            )
            
            # Add to appropriate queue
            await self.event_queues[priority].put(event)
            
            # Update statistics
            self.event_stats["total_events"] += 1
            
            self.logger.debug(f"Event emitted: {event.event_type} (ID: {event.event_id})")
            
            return event.event_id
            
        except Exception as e:
            self.logger.error(f"Error emitting event: {str(e)}")
            raise
    
    async def subscribe(
        self,
        event_pattern: str,
        callback: Callable,
        subscriber: str,
        scope: EventScope = EventScope.GLOBAL,
        filters: Dict[str, Any] = None,
        priority: int = 0
    ) -> str:
        """Subscribe to events matching a pattern"""
        try:
            subscription_id = str(uuid.uuid4())
            
            subscription = EventSubscription(
                subscription_id=subscription_id,
                subscriber=subscriber,
                event_patterns=[event_pattern],
                scope=scope,
                callback=callback,
                filters=filters or {}
            )
            
            self.subscriptions[subscription_id] = subscription
            
            # Register as handler
            handler = EventHandler(
                handler_id=subscription_id,
                event_pattern=event_pattern,
                callback=callback,
                scope=scope,
                priority=priority
            )
            
            self.handlers[subscription_id] = handler
            
            # Update pattern mapping
            if event_pattern not in self.event_patterns:
                self.event_patterns[event_pattern] = []
            self.event_patterns[event_pattern].append(subscription_id)
            
            self.logger.debug(f"Subscription created: {event_pattern} by {subscriber}")
            
            return subscription_id
            
        except Exception as e:
            self.logger.error(f"Error creating subscription: {str(e)}")
            raise
    
    async def unsubscribe(self, subscription_id: str) -> bool:
        """Unsubscribe from events"""
        try:
            if subscription_id in self.subscriptions:
                subscription = self.subscriptions[subscription_id]
                
                # Remove from handlers
                if subscription_id in self.handlers:
                    handler = self.handlers[subscription_id]
                    
                    # Remove from pattern mapping
                    if handler.event_pattern in self.event_patterns:
                        if subscription_id in self.event_patterns[handler.event_pattern]:
                            self.event_patterns[handler.event_pattern].remove(subscription_id)
                        
                        # Clean up empty patterns
                        if not self.event_patterns[handler.event_pattern]:
                            del self.event_patterns[handler.event_pattern]
                    
                    del self.handlers[subscription_id]
                
                del self.subscriptions[subscription_id]
                
                self.logger.debug(f"Subscription removed: {subscription_id}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error removing subscription: {str(e)}")
            return False
    
    async def publish_to_scope(
        self,
        event_type: str,
        payload: Dict[str, Any],
        target_scope: EventScope,
        source: str,
        priority: EventPriority = EventPriority.NORMAL,
        tenant_id: Optional[str] = None
    ) -> str:
        """Publish event to specific scope"""
        return await self.emit(
            event_type=event_type,
            payload=payload,
            source=source,
            scope=target_scope,
            priority=priority,
            tenant_id=tenant_id
        )
    
    async def _process_queue(self, priority: EventPriority):
        """Process events from a specific priority queue"""
        queue = self.event_queues[priority]
        
        while self.is_running:
            try:
                # Wait for event with timeout
                event = await asyncio.wait_for(queue.get(), timeout=1.0)
                
                # Process the event
                await self._process_event(event)
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                self.logger.error(f"Error in queue processing ({priority}): {str(e)}")
                await asyncio.sleep(1)
    
    async def _process_event(self, event: Event):
        """Process a single event"""
        try:
            # Mark as processing
            self.processing_events[event.event_id] = event
            
            # Find matching handlers
            matching_handlers = await self._find_matching_handlers(event)
            
            if not matching_handlers:
                self.logger.debug(f"No handlers found for event: {event.event_type}")
                self._complete_event(event)
                return
            
            # Execute handlers
            results = await self._execute_handlers(event, matching_handlers)
            
            # Check results
            if all(results):
                self._complete_event(event)
            else:
                await self._handle_event_failure(event)
                
        except Exception as e:
            self.logger.error(f"Error processing event {event.event_id}: {str(e)}")
            await self._handle_event_failure(event)
        finally:
            # Remove from processing
            if event.event_id in self.processing_events:
                del self.processing_events[event.event_id]
    
    async def _find_matching_handlers(self, event: Event) -> List[EventHandler]:
        """Find handlers that match the event"""
        matching_handlers = []
        
        for pattern, handler_ids in self.event_patterns.items():
            if self._pattern_matches(pattern, event.event_type):
                for handler_id in handler_ids:
                    if handler_id in self.handlers:
                        handler = self.handlers[handler_id]
                        
                        # Check scope compatibility
                        if self._scope_matches(handler.scope, event.scope):
                            # Check if handler is active
                            if handler.active:
                                matching_handlers.append(handler)
        
        # Sort by priority
        matching_handlers.sort(key=lambda h: h.priority, reverse=True)
        
        return matching_handlers
    
    async def _execute_handlers(self, event: Event, handlers: List[EventHandler]) -> List[bool]:
        """Execute event handlers"""
        results = []
        
        for handler in handlers:
            try:
                # Update subscription activity
                if handler.handler_id in self.subscriptions:
                    self.subscriptions[handler.handler_id].last_activity = datetime.now(timezone.utc)
                
                # Execute handler
                if asyncio.iscoroutinefunction(handler.callback):
                    result = await handler.callback(event)
                else:
                    # Execute in thread pool for sync handlers
                    result = await asyncio.get_event_loop().run_in_executor(
                        self.executor, handler.callback, event
                    )
                
                results.append(bool(result))
                
            except Exception as e:
                self.logger.error(f"Handler {handler.handler_id} failed for event {event.event_id}: {str(e)}")
                results.append(False)
        
        return results
    
    def _pattern_matches(self, pattern: str, event_type: str) -> bool:
        """Check if pattern matches event type"""
        if pattern == "*":
            return True
        if pattern == event_type:
            return True
        
        # Simple glob pattern matching
        if "*" in pattern:
            import fnmatch
            return fnmatch.fnmatch(event_type, pattern)
        
        return False
    
    def _scope_matches(self, handler_scope: EventScope, event_scope: EventScope) -> bool:
        """Check if handler scope matches event scope"""
        if handler_scope == EventScope.GLOBAL:
            return True
        if event_scope == EventScope.GLOBAL:
            return True
        return handler_scope == event_scope
    
    def _complete_event(self, event: Event):
        """Mark event as completed"""
        self.completed_events[event.event_id] = event
        self.event_stats["processed_events"] += 1
        self.logger.debug(f"Event completed: {event.event_id}")
    
    async def _handle_event_failure(self, event: Event):
        """Handle event processing failure"""
        event.retry_count += 1
        
        if event.retry_count <= event.max_retries:
            # Retry the event
            self.logger.info(f"Retrying event {event.event_id} (attempt {event.retry_count})")
            await self.event_queues[event.priority].put(event)
            self.event_stats["retried_events"] += 1
        else:
            # Send to dead letter
            self.logger.warning(f"Event {event.event_id} exceeded max retries, sending to dead letter")
            self.failed_events[event.event_id] = event
            self.event_stats["dead_letter_events"] += 1
            
            # Emit dead letter event
            await self.emit(
                event_type="system.event.dead_letter",
                payload={
                    "original_event_id": event.event_id,
                    "original_event_type": event.event_type,
                    "failure_reason": "max_retries_exceeded",
                    "retry_count": event.retry_count
                },
                source="event_bus",
                scope=EventScope.GLOBAL,
                priority=EventPriority.HIGH
            )
        
        self.event_stats["failed_events"] += 1
    
    async def _maintenance_loop(self):
        """Periodic maintenance tasks"""
        while self.is_running:
            try:
                await asyncio.sleep(60)  # Run every minute
                
                # Clean up old completed events
                await self._cleanup_old_events()
                
                # Health checks
                await self._perform_health_checks()
                
            except Exception as e:
                self.logger.error(f"Error in maintenance loop: {str(e)}")
    
    async def _cleanup_old_events(self):
        """Clean up old completed events"""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)
        
        # Clean completed events
        to_remove = [
            event_id for event_id, event in self.completed_events.items()
            if event.timestamp < cutoff_time
        ]
        
        for event_id in to_remove:
            del self.completed_events[event_id]
        
        if to_remove:
            self.logger.debug(f"Cleaned up {len(to_remove)} old completed events")
    
    async def _perform_health_checks(self):
        """Perform health checks and emit metrics"""
        try:
            # Queue health
            queue_sizes = {
                priority.value: queue.qsize() 
                for priority, queue in self.event_queues.items()
            }
            
            # Handler health
            active_handlers = sum(1 for h in self.handlers.values() if h.active)
            total_handlers = len(self.handlers)
            
            # Emit health metrics
            await self.emit(
                event_type="system.event_bus.health",
                payload={
                    "queue_sizes": queue_sizes,
                    "active_handlers": active_handlers,
                    "total_handlers": total_handlers,
                    "processing_events": len(self.processing_events),
                    "stats": self.event_stats
                },
                source="event_bus",
                scope=EventScope.GLOBAL,
                priority=EventPriority.LOW
            )
            
        except Exception as e:
            self.logger.error(f"Error in health checks: {str(e)}")
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get event bus statistics"""
        return {
            "stats": self.event_stats.copy(),
            "queue_sizes": {
                priority.value: queue.qsize() 
                for priority, queue in self.event_queues.items()
            },
            "handlers": {
                "total": len(self.handlers),
                "active": sum(1 for h in self.handlers.values() if h.active)
            },
            "subscriptions": len(self.subscriptions),
            "processing_events": len(self.processing_events),
            "failed_events": len(self.failed_events),
            "completed_events": len(self.completed_events)
        }
    
    async def get_event_status(self, event_id: str) -> Optional[Dict[str, Any]]:
        """Get status of specific event"""
        if event_id in self.processing_events:
            return {"status": EventStatus.PROCESSING, "event": self.processing_events[event_id]}
        elif event_id in self.completed_events:
            return {"status": EventStatus.COMPLETED, "event": self.completed_events[event_id]}
        elif event_id in self.failed_events:
            return {"status": EventStatus.DEAD_LETTER, "event": self.failed_events[event_id]}
        else:
            return None
    
    async def replay_failed_event(self, event_id: str) -> bool:
        """Replay a failed event"""
        if event_id in self.failed_events:
            event = self.failed_events[event_id]
            event.retry_count = 0  # Reset retry count
            
            await self.event_queues[event.priority].put(event)
            del self.failed_events[event_id]
            
            self.logger.info(f"Replaying failed event: {event_id}")
            return True
        
        return False


# Global event bus instance
_global_event_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """Get global event bus instance"""
    global _global_event_bus
    if _global_event_bus is None:
        _global_event_bus = EventBus()
    return _global_event_bus


async def initialize_event_bus(**kwargs) -> EventBus:
    """Initialize and start the global event bus"""
    global _global_event_bus
    _global_event_bus = EventBus(**kwargs)
    await _global_event_bus.start()
    return _global_event_bus


async def shutdown_event_bus():
    """Shutdown the global event bus"""
    global _global_event_bus
    if _global_event_bus:
        await _global_event_bus.stop()
        _global_event_bus = None