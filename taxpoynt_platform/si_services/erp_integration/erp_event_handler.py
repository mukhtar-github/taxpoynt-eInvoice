"""
ERP Event Handler Service

This module handles real-time events from ERP systems for SI processing,
including webhook processing, event queue management, event filtering,
and triggering appropriate SI workflows based on ERP events.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import hashlib
from pathlib import Path
from collections import defaultdict, deque
import aiohttp
from aiohttp import web
import hmac

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Types of ERP events"""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    STATUS_CHANGE = "status_change"
    PAYMENT_RECEIVED = "payment_received"
    PAYMENT_FAILED = "payment_failed"
    INVOICE_APPROVED = "invoice_approved"
    INVOICE_REJECTED = "invoice_rejected"
    SYNC_REQUEST = "sync_request"
    HEALTH_CHECK = "health_check"
    CUSTOM = "custom"


class EventSource(Enum):
    """Sources of events"""
    WEBHOOK = "webhook"
    POLLING = "polling"
    MESSAGE_QUEUE = "message_queue"
    API_CALLBACK = "api_callback"
    INTERNAL = "internal"


class EventStatus(Enum):
    """Status of event processing"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    SKIPPED = "skipped"


class EventPriority(Enum):
    """Priority levels for event processing"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


@dataclass
class ERPEvent:
    """Represents an ERP event"""
    event_id: str
    event_type: EventType
    source: EventSource
    erp_system: str
    entity_type: str
    entity_id: str
    timestamp: datetime
    payload: Dict[str, Any]
    headers: Dict[str, str] = field(default_factory=dict)
    priority: EventPriority = EventPriority.NORMAL
    status: EventStatus = EventStatus.PENDING
    retry_count: int = 0
    max_retries: int = 3
    processed_at: Optional[datetime] = None
    error_details: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EventFilter:
    """Filter criteria for event processing"""
    event_types: Optional[Set[EventType]] = None
    erp_systems: Optional[Set[str]] = None
    entity_types: Optional[Set[str]] = None
    priority_threshold: EventPriority = EventPriority.LOW
    time_window_minutes: Optional[int] = None
    custom_conditions: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EventHandler:
    """Defines an event handler"""
    handler_id: str
    handler_name: str
    event_filter: EventFilter
    handler_function: Callable
    enabled: bool = True
    async_processing: bool = True
    timeout_seconds: int = 30
    retry_on_failure: bool = True
    description: Optional[str] = None


@dataclass
class WebhookConfig:
    """Configuration for webhook endpoints"""
    endpoint_path: str
    erp_system: str
    secret_key: Optional[str] = None
    signature_header: str = "X-Signature"
    signature_algorithm: str = "sha256"
    enabled: bool = True
    rate_limit_per_minute: int = 100
    validate_signature: bool = True


@dataclass
class EventMetrics:
    """Metrics for event processing"""
    total_events: int = 0
    processed_events: int = 0
    failed_events: int = 0
    skipped_events: int = 0
    average_processing_time: float = 0.0
    events_per_minute: float = 0.0
    active_handlers: int = 0
    queue_depth: int = 0


@dataclass
class EventHandlerConfig:
    """Configuration for event handler service"""
    max_concurrent_events: int = 10
    event_queue_size: int = 1000
    webhook_server_port: int = 8080
    webhook_server_host: str = "0.0.0.0"
    enable_webhook_server: bool = True
    enable_event_persistence: bool = True
    event_retention_days: int = 30
    max_retry_attempts: int = 3
    retry_delay_seconds: int = 60
    health_check_interval: int = 300
    rate_limit_window_minutes: int = 1
    enable_event_deduplication: bool = True
    deduplication_window_minutes: int = 5
    event_storage_path: Optional[str] = None


class ERPEventHandler:
    """
    Service for handling real-time events from ERP systems with
    webhook processing, event filtering, and workflow triggering.
    """
    
    def __init__(self, config: EventHandlerConfig):
        self.config = config
        self.event_handlers: Dict[str, EventHandler] = {}
        self.webhook_configs: Dict[str, WebhookConfig] = {}
        self.event_queue: asyncio.Queue = asyncio.Queue(maxsize=config.event_queue_size)
        self.processed_events: deque = deque(maxlen=10000)
        self.metrics = EventMetrics()
        
        # Event processing state
        self.is_running = False
        self.worker_tasks: List[asyncio.Task] = []
        self.webhook_server: Optional[web.Application] = None
        self.webhook_runner: Optional[web.AppRunner] = None
        self.monitoring_task: Optional[asyncio.Task] = None
        
        # Event deduplication
        self.event_fingerprints: Dict[str, datetime] = {}
        
        # Rate limiting
        self.rate_limit_counters: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        
        # Processing semaphore
        self.processing_semaphore = asyncio.Semaphore(config.max_concurrent_events)
        
        # Setup storage
        if config.event_storage_path:
            self.storage_path = Path(config.event_storage_path)
            self.storage_path.mkdir(parents=True, exist_ok=True)
        else:
            self.storage_path = None
    
    async def start_event_handler(self) -> None:
        """Start the event handler service"""
        if self.is_running:
            return
        
        self.is_running = True
        logger.info("Starting ERP Event Handler")
        
        # Start webhook server if enabled
        if self.config.enable_webhook_server:
            await self._start_webhook_server()
        
        # Start event processing workers
        for i in range(self.config.max_concurrent_events):
            task = asyncio.create_task(self._event_worker(f"worker-{i}"))
            self.worker_tasks.append(task)
        
        # Start monitoring task
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        
        # Load existing handlers
        await self._load_event_handlers()
    
    async def stop_event_handler(self) -> None:
        """Stop the event handler service"""
        if not self.is_running:
            return
        
        self.is_running = False
        logger.info("Stopping ERP Event Handler")
        
        # Stop webhook server
        if self.webhook_runner:
            await self.webhook_runner.cleanup()
        
        # Cancel worker tasks
        for task in self.worker_tasks:
            task.cancel()
        
        # Cancel monitoring task
        if self.monitoring_task:
            self.monitoring_task.cancel()
        
        # Wait for tasks to complete
        await asyncio.gather(
            *[t for t in self.worker_tasks + [self.monitoring_task] if t],
            return_exceptions=True
        )
        
        self.worker_tasks.clear()
        
        # Save current state
        await self._save_event_state()
    
    async def _start_webhook_server(self) -> None:
        """Start the webhook server"""
        try:
            self.webhook_server = web.Application()
            
            # Add webhook routes
            self.webhook_server.router.add_post("/webhook/{erp_system}", self._handle_webhook)
            self.webhook_server.router.add_get("/health", self._health_check)
            
            # Add middleware
            self.webhook_server.middlewares.append(self._rate_limit_middleware)
            self.webhook_server.middlewares.append(self._logging_middleware)
            
            # Start server
            self.webhook_runner = web.AppRunner(self.webhook_server)
            await self.webhook_runner.setup()
            
            site = web.TCPSite(
                self.webhook_runner,
                self.config.webhook_server_host,
                self.config.webhook_server_port
            )
            await site.start()
            
            logger.info(f"Webhook server started on {self.config.webhook_server_host}:{self.config.webhook_server_port}")
            
        except Exception as e:
            logger.error(f"Failed to start webhook server: {e}")
            raise
    
    async def _handle_webhook(self, request: web.Request) -> web.Response:
        """Handle incoming webhook requests"""
        try:
            erp_system = request.match_info['erp_system']
            
            # Get webhook config
            webhook_config = self.webhook_configs.get(erp_system)
            if not webhook_config or not webhook_config.enabled:
                return web.Response(status=404, text="Webhook not configured")
            
            # Validate signature if enabled
            if webhook_config.validate_signature and webhook_config.secret_key:
                if not await self._validate_webhook_signature(request, webhook_config):
                    return web.Response(status=401, text="Invalid signature")
            
            # Parse payload
            try:
                payload = await request.json()
            except Exception:
                payload = {"raw_body": await request.text()}
            
            # Create event
            event = await self._create_event_from_webhook(request, erp_system, payload)
            
            if event:
                # Queue event for processing
                await self._queue_event(event)
                return web.Response(status=200, text="Event received")
            else:
                return web.Response(status=400, text="Invalid event")
                
        except Exception as e:
            logger.error(f"Webhook handling failed: {e}")
            return web.Response(status=500, text="Internal server error")
    
    async def _validate_webhook_signature(
        self,
        request: web.Request,
        config: WebhookConfig
    ) -> bool:
        """Validate webhook signature"""
        try:
            signature_header = request.headers.get(config.signature_header)
            if not signature_header:
                return False
            
            body = await request.read()
            
            # Calculate expected signature
            if config.signature_algorithm == "sha256":
                expected_signature = hmac.new(
                    config.secret_key.encode(),
                    body,
                    hashlib.sha256
                ).hexdigest()
                
                # Compare signatures
                if signature_header.startswith("sha256="):
                    provided_signature = signature_header[7:]
                else:
                    provided_signature = signature_header
                
                return hmac.compare_digest(expected_signature, provided_signature)
            
            return False
            
        except Exception as e:
            logger.error(f"Signature validation failed: {e}")
            return False
    
    async def _create_event_from_webhook(
        self,
        request: web.Request,
        erp_system: str,
        payload: Dict[str, Any]
    ) -> Optional[ERPEvent]:
        """Create event from webhook payload"""
        try:
            # Extract event information from payload
            event_type = self._determine_event_type(payload)
            entity_type = payload.get("entity_type", "unknown")
            entity_id = payload.get("entity_id", payload.get("id", "unknown"))
            
            # Generate event ID
            event_id = self._generate_event_id(erp_system, entity_type, entity_id)
            
            # Create event
            event = ERPEvent(
                event_id=event_id,
                event_type=event_type,
                source=EventSource.WEBHOOK,
                erp_system=erp_system,
                entity_type=entity_type,
                entity_id=entity_id,
                timestamp=datetime.now(),
                payload=payload,
                headers=dict(request.headers),
                priority=self._determine_event_priority(payload)
            )
            
            return event
            
        except Exception as e:
            logger.error(f"Failed to create event from webhook: {e}")
            return None
    
    def _determine_event_type(self, payload: Dict[str, Any]) -> EventType:
        """Determine event type from payload"""
        try:
            # Check for explicit event type
            event_type_str = payload.get("event_type", "").lower()
            
            if event_type_str:
                for event_type in EventType:
                    if event_type.value == event_type_str:
                        return event_type
            
            # Infer from action
            action = payload.get("action", "").lower()
            if action in ["create", "created"]:
                return EventType.CREATE
            elif action in ["update", "updated", "modify", "modified"]:
                return EventType.UPDATE
            elif action in ["delete", "deleted", "remove", "removed"]:
                return EventType.DELETE
            elif action in ["approve", "approved"]:
                return EventType.INVOICE_APPROVED
            elif action in ["reject", "rejected"]:
                return EventType.INVOICE_REJECTED
            elif action in ["payment", "paid"]:
                return EventType.PAYMENT_RECEIVED
            
            # Default to update
            return EventType.UPDATE
            
        except Exception:
            return EventType.CUSTOM
    
    def _determine_event_priority(self, payload: Dict[str, Any]) -> EventPriority:
        """Determine event priority from payload"""
        try:
            # Check for explicit priority
            priority_str = payload.get("priority", "").lower()
            
            if priority_str == "urgent":
                return EventPriority.URGENT
            elif priority_str == "high":
                return EventPriority.HIGH
            elif priority_str == "low":
                return EventPriority.LOW
            
            # Infer priority from event type
            event_type = self._determine_event_type(payload)
            
            if event_type in [EventType.PAYMENT_FAILED, EventType.INVOICE_REJECTED]:
                return EventPriority.HIGH
            elif event_type in [EventType.CREATE, EventType.PAYMENT_RECEIVED]:
                return EventPriority.NORMAL
            
            return EventPriority.NORMAL
            
        except Exception:
            return EventPriority.NORMAL
    
    async def _queue_event(self, event: ERPEvent) -> bool:
        """Queue event for processing"""
        try:
            # Check for duplicates if enabled
            if self.config.enable_event_deduplication:
                if await self._is_duplicate_event(event):
                    logger.debug(f"Skipping duplicate event {event.event_id}")
                    self.metrics.skipped_events += 1
                    return True
            
            # Add to queue
            await self.event_queue.put(event)
            self.metrics.total_events += 1
            self.metrics.queue_depth = self.event_queue.qsize()
            
            logger.debug(f"Queued event {event.event_id}")
            return True
            
        except asyncio.QueueFull:
            logger.warning(f"Event queue full, dropping event {event.event_id}")
            return False
        except Exception as e:
            logger.error(f"Failed to queue event {event.event_id}: {e}")
            return False
    
    async def _is_duplicate_event(self, event: ERPEvent) -> bool:
        """Check if event is a duplicate"""
        try:
            # Create fingerprint
            fingerprint = self._create_event_fingerprint(event)
            
            # Check if fingerprint exists within deduplication window
            if fingerprint in self.event_fingerprints:
                last_seen = self.event_fingerprints[fingerprint]
                time_diff = datetime.now() - last_seen
                
                if time_diff.total_seconds() < (self.config.deduplication_window_minutes * 60):
                    return True
            
            # Store fingerprint
            self.event_fingerprints[fingerprint] = datetime.now()
            
            # Clean old fingerprints
            cutoff_time = datetime.now() - timedelta(minutes=self.config.deduplication_window_minutes)
            fingerprints_to_remove = [
                fp for fp, timestamp in self.event_fingerprints.items()
                if timestamp < cutoff_time
            ]
            
            for fp in fingerprints_to_remove:
                del self.event_fingerprints[fp]
            
            return False
            
        except Exception as e:
            logger.error(f"Duplicate check failed: {e}")
            return False
    
    def _create_event_fingerprint(self, event: ERPEvent) -> str:
        """Create fingerprint for event deduplication"""
        try:
            # Create fingerprint from key event attributes
            fingerprint_data = {
                "erp_system": event.erp_system,
                "entity_type": event.entity_type,
                "entity_id": event.entity_id,
                "event_type": event.event_type.value
            }
            
            # Add payload hash for additional uniqueness
            payload_str = json.dumps(event.payload, sort_keys=True)
            payload_hash = hashlib.md5(payload_str.encode()).hexdigest()
            fingerprint_data["payload_hash"] = payload_hash
            
            fingerprint_str = json.dumps(fingerprint_data, sort_keys=True)
            return hashlib.sha256(fingerprint_str.encode()).hexdigest()
            
        except Exception as e:
            logger.error(f"Fingerprint creation failed: {e}")
            return f"{event.erp_system}_{event.entity_type}_{event.entity_id}"
    
    async def _event_worker(self, worker_name: str) -> None:
        """Worker task for processing events"""
        logger.info(f"Starting event worker: {worker_name}")
        
        while self.is_running:
            try:
                # Get event from queue
                event = await asyncio.wait_for(self.event_queue.get(), timeout=1.0)
                
                # Process event
                await self._process_event(event, worker_name)
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Event worker {worker_name} error: {e}")
                await asyncio.sleep(1.0)
        
        logger.info(f"Event worker {worker_name} stopped")
    
    async def _process_event(self, event: ERPEvent, worker_name: str) -> None:
        """Process a single event"""
        async with self.processing_semaphore:
            try:
                event.status = EventStatus.PROCESSING
                start_time = datetime.now()
                
                logger.debug(f"Worker {worker_name} processing event {event.event_id}")
                
                # Find matching handlers
                matching_handlers = await self._find_matching_handlers(event)
                
                if not matching_handlers:
                    logger.debug(f"No handlers found for event {event.event_id}")
                    event.status = EventStatus.SKIPPED
                    self.metrics.skipped_events += 1
                    return
                
                # Execute handlers
                success = True
                for handler in matching_handlers:
                    try:
                        if handler.async_processing:
                            await self._execute_async_handler(handler, event)
                        else:
                            await self._execute_sync_handler(handler, event)
                    except Exception as e:
                        logger.error(f"Handler {handler.handler_id} failed for event {event.event_id}: {e}")
                        success = False
                        
                        if handler.retry_on_failure and event.retry_count < event.max_retries:
                            # Schedule retry
                            await self._schedule_retry(event)
                            return
                
                # Update event status
                if success:
                    event.status = EventStatus.COMPLETED
                    self.metrics.processed_events += 1
                else:
                    event.status = EventStatus.FAILED
                    self.metrics.failed_events += 1
                
                # Update processing time
                processing_time = (datetime.now() - start_time).total_seconds()
                self._update_processing_metrics(processing_time)
                
            except Exception as e:
                logger.error(f"Event processing failed for {event.event_id}: {e}")
                event.status = EventStatus.FAILED
                event.error_details = str(e)
                self.metrics.failed_events += 1
            
            finally:
                event.processed_at = datetime.now()
                self.processed_events.append(event)
                
                # Update queue depth metric
                self.metrics.queue_depth = self.event_queue.qsize()
    
    async def _find_matching_handlers(self, event: ERPEvent) -> List[EventHandler]:
        """Find handlers that match the event"""
        matching_handlers = []
        
        for handler in self.event_handlers.values():
            if not handler.enabled:
                continue
            
            if await self._handler_matches_event(handler, event):
                matching_handlers.append(handler)
        
        # Sort by priority (higher priority first)
        matching_handlers.sort(key=lambda h: self._get_handler_priority(h), reverse=True)
        
        return matching_handlers
    
    async def _handler_matches_event(self, handler: EventHandler, event: ERPEvent) -> bool:
        """Check if handler matches event criteria"""
        try:
            filter_criteria = handler.event_filter
            
            # Check event types
            if filter_criteria.event_types and event.event_type not in filter_criteria.event_types:
                return False
            
            # Check ERP systems
            if filter_criteria.erp_systems and event.erp_system not in filter_criteria.erp_systems:
                return False
            
            # Check entity types
            if filter_criteria.entity_types and event.entity_type not in filter_criteria.entity_types:
                return False
            
            # Check priority threshold
            if event.priority.value < filter_criteria.priority_threshold.value:
                return False
            
            # Check time window
            if filter_criteria.time_window_minutes:
                time_diff = datetime.now() - event.timestamp
                if time_diff.total_seconds() > (filter_criteria.time_window_minutes * 60):
                    return False
            
            # Check custom conditions
            for condition_key, condition_value in filter_criteria.custom_conditions.items():
                if condition_key not in event.payload or event.payload[condition_key] != condition_value:
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Handler matching failed: {e}")
            return False
    
    def _get_handler_priority(self, handler: EventHandler) -> int:
        """Get handler priority for sorting"""
        # For now, all handlers have equal priority
        # This could be extended to support handler priorities
        return 1
    
    async def _execute_async_handler(self, handler: EventHandler, event: ERPEvent) -> None:
        """Execute async event handler"""
        try:
            # Execute with timeout
            await asyncio.wait_for(
                handler.handler_function(event),
                timeout=handler.timeout_seconds
            )
            
        except asyncio.TimeoutError:
            raise Exception(f"Handler {handler.handler_id} timed out")
        except Exception as e:
            raise Exception(f"Handler {handler.handler_id} failed: {e}")
    
    async def _execute_sync_handler(self, handler: EventHandler, event: ERPEvent) -> None:
        """Execute sync event handler"""
        try:
            # Run sync handler in thread pool
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, handler.handler_function, event)
            
        except Exception as e:
            raise Exception(f"Sync handler {handler.handler_id} failed: {e}")
    
    async def _schedule_retry(self, event: ERPEvent) -> None:
        """Schedule event retry"""
        try:
            event.retry_count += 1
            event.status = EventStatus.RETRYING
            
            # Wait before retry
            await asyncio.sleep(self.config.retry_delay_seconds)
            
            # Re-queue event
            await self.event_queue.put(event)
            
            logger.info(f"Scheduled retry {event.retry_count} for event {event.event_id}")
            
        except Exception as e:
            logger.error(f"Failed to schedule retry for event {event.event_id}: {e}")
    
    def _update_processing_metrics(self, processing_time: float) -> None:
        """Update processing time metrics"""
        try:
            # Simple moving average
            if self.metrics.average_processing_time == 0:
                self.metrics.average_processing_time = processing_time
            else:
                # Weighted average (new time gets 20% weight)
                self.metrics.average_processing_time = (
                    self.metrics.average_processing_time * 0.8 + processing_time * 0.2
                )
        except Exception as e:
            logger.error(f"Metrics update failed: {e}")
    
    async def _monitoring_loop(self) -> None:
        """Background monitoring loop"""
        while self.is_running:
            try:
                await self._update_metrics()
                await self._cleanup_old_events()
                await self._health_check_handlers()
                
                await asyncio.sleep(60)  # Monitor every minute
                
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                await asyncio.sleep(60)
    
    async def _update_metrics(self) -> None:
        """Update service metrics"""
        try:
            # Update events per minute
            current_time = datetime.now()
            minute_ago = current_time - timedelta(minutes=1)
            
            recent_events = sum(
                1 for event in self.processed_events
                if event.processed_at and event.processed_at > minute_ago
            )
            
            self.metrics.events_per_minute = recent_events
            self.metrics.active_handlers = len([h for h in self.event_handlers.values() if h.enabled])
            
        except Exception as e:
            logger.error(f"Metrics update failed: {e}")
    
    async def _cleanup_old_events(self) -> None:
        """Clean up old processed events"""
        try:
            cutoff_time = datetime.now() - timedelta(days=self.config.event_retention_days)
            
            # Remove old events from processed_events deque
            # Note: deque doesn't support efficient removal from middle
            # In production, consider using a different data structure
            
            # Clean old fingerprints
            fingerprints_to_remove = [
                fp for fp, timestamp in self.event_fingerprints.items()
                if timestamp < cutoff_time
            ]
            
            for fp in fingerprints_to_remove:
                del self.event_fingerprints[fp]
                
        except Exception as e:
            logger.error(f"Event cleanup failed: {e}")
    
    async def _health_check_handlers(self) -> None:
        """Perform health checks on event handlers"""
        try:
            # Check if handlers are responsive
            # This could include pinging external services, checking database connections, etc.
            pass
        except Exception as e:
            logger.error(f"Handler health check failed: {e}")
    
    def _generate_event_id(self, erp_system: str, entity_type: str, entity_id: str) -> str:
        """Generate unique event ID"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        source_hash = hashlib.md5(f"{erp_system}_{entity_type}_{entity_id}".encode()).hexdigest()[:8]
        return f"event_{source_hash}_{timestamp}"
    
    # Middleware functions
    
    async def _rate_limit_middleware(self, request: web.Request, handler) -> web.Response:
        """Rate limiting middleware"""
        try:
            client_ip = request.remote
            current_time = datetime.now()
            
            # Get rate limit counter for this IP
            counter = self.rate_limit_counters[client_ip]
            
            # Remove old entries
            minute_ago = current_time - timedelta(minutes=self.config.rate_limit_window_minutes)
            while counter and counter[0] < minute_ago:
                counter.popleft()
            
            # Check rate limit
            if len(counter) >= 100:  # Default rate limit
                return web.Response(status=429, text="Rate limit exceeded")
            
            # Add current request
            counter.append(current_time)
            
            return await handler(request)
            
        except Exception as e:
            logger.error(f"Rate limiting error: {e}")
            return await handler(request)
    
    async def _logging_middleware(self, request: web.Request, handler) -> web.Response:
        """Logging middleware"""
        start_time = datetime.now()
        
        try:
            response = await handler(request)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"Webhook request: {request.method} {request.path} -> {response.status} ({processing_time:.3f}s)")
            
            return response
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Webhook request failed: {request.method} {request.path} -> {e} ({processing_time:.3f}s)")
            raise
    
    async def _health_check(self, request: web.Request) -> web.Response:
        """Health check endpoint"""
        health_data = {
            "status": "healthy" if self.is_running else "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "metrics": {
                "total_events": self.metrics.total_events,
                "processed_events": self.metrics.processed_events,
                "failed_events": self.metrics.failed_events,
                "queue_depth": self.metrics.queue_depth,
                "active_handlers": self.metrics.active_handlers,
                "events_per_minute": self.metrics.events_per_minute
            }
        }
        
        return web.json_response(health_data)
    
    # Public API methods
    
    async def register_event_handler(self, handler: EventHandler) -> bool:
        """Register a new event handler"""
        try:
            self.event_handlers[handler.handler_id] = handler
            await self._save_handler_config(handler)
            
            logger.info(f"Registered event handler: {handler.handler_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register handler {handler.handler_id}: {e}")
            return False
    
    async def unregister_event_handler(self, handler_id: str) -> bool:
        """Unregister an event handler"""
        try:
            if handler_id in self.event_handlers:
                del self.event_handlers[handler_id]
                logger.info(f"Unregistered event handler: {handler_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to unregister handler {handler_id}: {e}")
            return False
    
    async def register_webhook(self, config: WebhookConfig) -> bool:
        """Register a webhook configuration"""
        try:
            self.webhook_configs[config.erp_system] = config
            await self._save_webhook_config(config)
            
            logger.info(f"Registered webhook for {config.erp_system}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register webhook for {config.erp_system}: {e}")
            return False
    
    async def send_event(self, event: ERPEvent) -> bool:
        """Manually send an event for processing"""
        return await self._queue_event(event)
    
    def get_event_metrics(self) -> EventMetrics:
        """Get current event metrics"""
        return self.metrics
    
    def get_recent_events(self, limit: int = 100) -> List[ERPEvent]:
        """Get recent processed events"""
        return list(self.processed_events)[-limit:]
    
    def get_active_handlers(self) -> List[EventHandler]:
        """Get all active event handlers"""
        return [h for h in self.event_handlers.values() if h.enabled]
    
    async def _save_handler_config(self, handler: EventHandler) -> None:
        """Save handler configuration"""
        if not self.storage_path:
            return
        
        try:
            handler_file = self.storage_path / f"handler_{handler.handler_id}.json"
            handler_data = {
                "handler_id": handler.handler_id,
                "handler_name": handler.handler_name,
                "enabled": handler.enabled,
                "async_processing": handler.async_processing,
                "timeout_seconds": handler.timeout_seconds,
                "description": handler.description
            }
            
            with open(handler_file, 'w') as f:
                json.dump(handler_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save handler config: {e}")
    
    async def _save_webhook_config(self, config: WebhookConfig) -> None:
        """Save webhook configuration"""
        if not self.storage_path:
            return
        
        try:
            webhook_file = self.storage_path / f"webhook_{config.erp_system}.json"
            webhook_data = {
                "endpoint_path": config.endpoint_path,
                "erp_system": config.erp_system,
                "enabled": config.enabled,
                "rate_limit_per_minute": config.rate_limit_per_minute,
                "validate_signature": config.validate_signature
            }
            
            with open(webhook_file, 'w') as f:
                json.dump(webhook_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save webhook config: {e}")
    
    async def _load_event_handlers(self) -> None:
        """Load event handlers from storage"""
        if not self.storage_path:
            return
        
        try:
            for handler_file in self.storage_path.glob("handler_*.json"):
                with open(handler_file, 'r') as f:
                    handler_data = json.load(f)
                
                logger.info(f"Loaded event handler: {handler_data['handler_id']}")
                
        except Exception as e:
            logger.error(f"Failed to load event handlers: {e}")
    
    async def _save_event_state(self) -> None:
        """Save current event processing state"""
        if not self.storage_path:
            return
        
        try:
            state_data = {
                "metrics": {
                    "total_events": self.metrics.total_events,
                    "processed_events": self.metrics.processed_events,
                    "failed_events": self.metrics.failed_events,
                    "average_processing_time": self.metrics.average_processing_time
                },
                "timestamp": datetime.now().isoformat()
            }
            
            state_file = self.storage_path / "event_state.json"
            with open(state_file, 'w') as f:
                json.dump(state_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save event state: {e}")


# Factory function for creating ERP event handler
def create_erp_event_handler(config: Optional[EventHandlerConfig] = None) -> ERPEventHandler:
    """Factory function to create an ERP event handler"""
    if config is None:
        config = EventHandlerConfig()
    
    return ERPEventHandler(config)