"""
Core Platform Messaging Package
Event-driven communication infrastructure for TaxPoynt Platform
"""

# Event Bus Components
from .event_bus import (
    EventBus,
    Event,
    EventPriority,
    EventScope,
    EventStatus,
    EventTrend,
    EventFrequency,
    get_event_bus,
    initialize_event_bus,
    shutdown_event_bus
)

# Message Router Components
from .message_router import (
    MessageRouter,
    ServiceRole,
    RoutingStrategy,
    MessageType,
    RoutingRule,
    ServiceEndpoint,
    RoutingContext,
    RoutedMessage,
    get_message_router,
    initialize_message_router
)

# Queue Manager Components
from .queue_manager import (
    QueueManager,
    MessageQueue,
    QueueType,
    QueueStrategy,
    MessageStatus,
    QueuedMessage,
    QueueConfiguration,
    QueueMetrics,
    get_queue_manager,
    initialize_queue_manager
)

# Pub-Sub Coordinator Components
from .pub_sub_coordinator import (
    PubSubCoordinator,
    Topic,
    Subscription,
    Publication,
    SubscriptionType,
    DeliveryMode,
    TopicType,
    DeliveryReceipt,
    get_pubsub_coordinator,
    initialize_pubsub_coordinator
)

# Dead Letter Handler Components
from .dead_letter_handler import (
    DeadLetterHandler,
    DeadLetterMessage,
    FailureContext,
    FailureReason,
    RecoveryAction,
    RecoveryPlan,
    DeadLetterStats,
    AlertLevel,
    get_dead_letter_handler,
    initialize_dead_letter_handler
)

__all__ = [
    # Event Bus
    "EventBus",
    "Event", 
    "EventPriority",
    "EventScope",
    "EventStatus",
    "EventTrend",
    "EventFrequency",
    "get_event_bus",
    "initialize_event_bus",
    "shutdown_event_bus",
    
    # Message Router
    "MessageRouter",
    "ServiceRole",
    "RoutingStrategy", 
    "MessageType",
    "RoutingRule",
    "ServiceEndpoint",
    "RoutingContext",
    "RoutedMessage",
    "get_message_router",
    "initialize_message_router",
    
    # Queue Manager
    "QueueManager",
    "MessageQueue",
    "QueueType",
    "QueueStrategy",
    "MessageStatus",
    "QueuedMessage", 
    "QueueConfiguration",
    "QueueMetrics",
    "get_queue_manager",
    "initialize_queue_manager",
    
    # Pub-Sub Coordinator
    "PubSubCoordinator",
    "Topic",
    "Subscription",
    "Publication",
    "SubscriptionType",
    "DeliveryMode",
    "TopicType", 
    "DeliveryReceipt",
    "get_pubsub_coordinator",
    "initialize_pubsub_coordinator",
    
    # Dead Letter Handler
    "DeadLetterHandler",
    "DeadLetterMessage",
    "FailureContext",
    "FailureReason",
    "RecoveryAction",
    "RecoveryPlan",
    "DeadLetterStats",
    "AlertLevel",
    "get_dead_letter_handler",
    "initialize_dead_letter_handler"
]

# Version information
__version__ = "1.0.0"
__author__ = "TaxPoynt Platform Team"
__description__ = "Event-driven messaging infrastructure for TaxPoynt platform"

# Package metadata
PACKAGE_INFO = {
    "name": "taxpoynt_platform.core_platform.messaging",
    "version": __version__,
    "description": __description__,
    "components": [
        "Event Bus - Central event system",
        "Message Router - Role-based routing", 
        "Queue Manager - Message queue management",
        "Pub-Sub Coordinator - Publish-subscribe patterns",
        "Dead Letter Handler - Failed message processing"
    ],
    "features": [
        "Cross-service event communication",
        "Role-based message routing (SI/APP/Hybrid)",
        "Priority queue management",
        "Reliable message delivery",
        "Dead letter queue handling",
        "Message persistence",
        "Real-time monitoring",
        "Automatic recovery",
        "Poison message detection"
    ]
}


async def initialize_messaging_infrastructure(
    enable_persistence: bool = True,
    max_workers: int = 10,
    storage_path: str = "./messaging_data"
) -> dict:
    """
    Initialize complete messaging infrastructure
    
    Returns dictionary with initialized components
    """
    from pathlib import Path
    
    storage_path = Path(storage_path)
    
    # Initialize Event Bus
    event_bus = await initialize_event_bus(
        max_workers=max_workers,
        enable_persistence=enable_persistence
    )
    
    # Initialize Message Router
    message_router = await initialize_message_router(event_bus)
    
    # Initialize Queue Manager  
    queue_manager = await initialize_queue_manager(storage_path / "queues")
    
    # Initialize Pub-Sub Coordinator
    pubsub_coordinator = await initialize_pubsub_coordinator(event_bus)
    
    # Initialize Dead Letter Handler
    dead_letter_handler = await initialize_dead_letter_handler(
        event_bus, 
        storage_path / "dead_letters"
    )
    
    return {
        "event_bus": event_bus,
        "message_router": message_router,
        "queue_manager": queue_manager,
        "pubsub_coordinator": pubsub_coordinator,
        "dead_letter_handler": dead_letter_handler
    }


async def shutdown_messaging_infrastructure():
    """Shutdown all messaging components"""
    try:
        # Get global instances
        event_bus = get_event_bus()
        message_router = get_message_router()
        queue_manager = get_queue_manager()
        pubsub_coordinator = get_pubsub_coordinator()
        dead_letter_handler = get_dead_letter_handler()
        
        # Shutdown in reverse order
        await dead_letter_handler.stop()
        await pubsub_coordinator.stop()
        await queue_manager.shutdown()
        # Message router doesn't have explicit shutdown
        await event_bus.stop()
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error during messaging infrastructure shutdown: {str(e)}")


def get_messaging_stats() -> dict:
    """Get comprehensive messaging statistics"""
    try:
        # This would be implemented to gather stats from all components
        # For now, return basic info
        return {
            "components_initialized": True,
            "version": __version__,
            "package_info": PACKAGE_INFO
        }
    except Exception:
        return {"error": "Could not gather messaging stats"}