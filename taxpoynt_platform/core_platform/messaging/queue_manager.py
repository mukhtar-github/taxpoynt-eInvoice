"""
Core Platform: Queue Manager
Advanced message queue management with priority, persistence, and monitoring
"""
import asyncio
import json
import logging
import pickle
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Set, Union, Callable, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
import aiofiles
import heapq
from concurrent.futures import ThreadPoolExecutor

from .event_bus import Event, EventPriority, EventScope

logger = logging.getLogger(__name__)


class QueueType(str, Enum):
    """Types of message queues"""
    PRIORITY = "priority"           # Priority-based queue
    FIFO = "fifo"                  # First-in-first-out
    LIFO = "lifo"                  # Last-in-first-out
    DELAYED = "delayed"            # Delayed message processing
    BATCH = "batch"                # Batch processing queue
    STREAMING = "streaming"        # Real-time streaming queue


class QueueStrategy(str, Enum):
    """Queue processing strategies"""
    SINGLE_CONSUMER = "single_consumer"
    MULTIPLE_CONSUMER = "multiple_consumer"
    WORK_STEALING = "work_stealing"
    ROUND_ROBIN = "round_robin"
    LOAD_BALANCED = "load_balanced"


class MessageStatus(str, Enum):
    """Message processing status"""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRY = "retry"
    DEAD_LETTER = "dead_letter"
    EXPIRED = "expired"


@dataclass
class QueuedMessage:
    """Queued message with metadata"""
    message_id: str
    queue_name: str
    payload: Dict[str, Any]
    priority: int = 0
    scheduled_time: Optional[datetime] = None
    created_time: datetime = None
    processing_time: Optional[datetime] = None
    completion_time: Optional[datetime] = None
    expiry_time: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3
    status: MessageStatus = MessageStatus.QUEUED
    consumer_id: Optional[str] = None
    correlation_id: Optional[str] = None
    tenant_id: Optional[str] = None
    tags: List[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.created_time is None:
            self.created_time = datetime.now(timezone.utc)
        if self.tags is None:
            self.tags = []
        if self.metadata is None:
            self.metadata = {}
        if self.scheduled_time is None:
            self.scheduled_time = self.created_time
    
    def __lt__(self, other):
        """For priority queue ordering"""
        return (self.priority, self.scheduled_time) > (other.priority, other.scheduled_time)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        # Convert datetime objects to ISO strings
        for field in ['created_time', 'processing_time', 'completion_time', 'expiry_time', 'scheduled_time']:
            if data[field]:
                data[field] = data[field].isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QueuedMessage':
        """Create from dictionary"""
        data = data.copy()
        # Convert ISO strings back to datetime objects
        for field in ['created_time', 'processing_time', 'completion_time', 'expiry_time', 'scheduled_time']:
            if data.get(field):
                data[field] = datetime.fromisoformat(data[field])
        data['status'] = MessageStatus(data['status'])
        return cls(**data)


@dataclass
class QueueConfiguration:
    """Queue configuration"""
    queue_name: str
    queue_type: QueueType
    max_size: int = 10000
    max_workers: int = 5
    strategy: QueueStrategy = QueueStrategy.SINGLE_CONSUMER
    batch_size: int = 10
    batch_timeout: float = 5.0
    message_ttl: Optional[timedelta] = None
    enable_persistence: bool = True
    persistence_path: Optional[Path] = None
    auto_ack: bool = True
    dead_letter_queue: Optional[str] = None
    retry_delays: List[float] = None
    metrics_enabled: bool = True
    
    def __post_init__(self):
        if self.retry_delays is None:
            self.retry_delays = [1.0, 5.0, 15.0, 60.0]  # Exponential backoff


@dataclass
class QueueMetrics:
    """Queue performance metrics"""
    queue_name: str
    total_messages: int = 0
    queued_messages: int = 0
    processing_messages: int = 0
    completed_messages: int = 0
    failed_messages: int = 0
    retry_messages: int = 0
    dead_letter_messages: int = 0
    expired_messages: int = 0
    average_processing_time: float = 0.0
    peak_queue_size: int = 0
    current_queue_size: int = 0
    last_updated: datetime = None
    
    def __post_init__(self):
        if self.last_updated is None:
            self.last_updated = datetime.now(timezone.utc)


class MessageQueue:
    """
    Individual message queue with advanced features
    """
    
    def __init__(self, config: QueueConfiguration):
        """Initialize the message queue"""
        self.config = config
        self.queue_name = config.queue_name
        
        # Queue storage based on type
        if config.queue_type == QueueType.PRIORITY:
            self.messages = []  # Priority heap
        else:
            self.messages = asyncio.Queue(maxsize=config.max_size)
        
        # Message tracking
        self.message_registry: Dict[str, QueuedMessage] = {}
        self.processing_messages: Dict[str, QueuedMessage] = {}
        self.completed_messages: Dict[str, QueuedMessage] = {}
        self.failed_messages: Dict[str, QueuedMessage] = {}
        
        # Consumer management
        self.consumers: Dict[str, Callable] = {}
        self.active_workers: Set[str] = set()
        self.worker_tasks: Set[asyncio.Task] = set()
        
        # Batch processing
        self.batch_buffer: List[QueuedMessage] = []
        self.last_batch_time = datetime.now(timezone.utc)
        
        # Metrics
        self.metrics = QueueMetrics(queue_name=config.queue_name)
        
        # Persistence
        self.persistence_lock = asyncio.Lock()
        
        # Control state
        self.is_running = False
        self.is_paused = False
        
        self.logger = logging.getLogger(f"{__name__}.{config.queue_name}")
    
    async def start(self):
        """Start queue processing"""
        if self.is_running:
            return
        
        self.is_running = True
        self.logger.info(f"Starting queue: {self.queue_name}")
        
        # Load persisted messages
        if self.config.enable_persistence:
            await self._load_persisted_messages()
        
        # Start worker tasks
        for i in range(self.config.max_workers):
            worker_id = f"{self.queue_name}_worker_{i}"
            task = asyncio.create_task(self._worker_loop(worker_id))
            self.worker_tasks.add(task)
            task.add_done_callback(self.worker_tasks.discard)
        
        # Start maintenance tasks
        asyncio.create_task(self._maintenance_loop())
        asyncio.create_task(self._batch_processor_loop())
        asyncio.create_task(self._metrics_loop())
        
        self.logger.info(f"Queue started: {self.queue_name}")
    
    async def stop(self):
        """Stop queue processing"""
        if not self.is_running:
            return
        
        self.logger.info(f"Stopping queue: {self.queue_name}")
        self.is_running = False
        
        # Cancel worker tasks
        for task in self.worker_tasks:
            task.cancel()
        
        # Wait for workers to finish
        if self.worker_tasks:
            await asyncio.gather(*self.worker_tasks, return_exceptions=True)
        
        # Persist remaining messages
        if self.config.enable_persistence:
            await self._persist_messages()
        
        self.logger.info(f"Queue stopped: {self.queue_name}")
    
    async def pause(self):
        """Pause queue processing"""
        self.is_paused = True
        self.logger.info(f"Queue paused: {self.queue_name}")
    
    async def resume(self):
        """Resume queue processing"""
        self.is_paused = False
        self.logger.info(f"Queue resumed: {self.queue_name}")
    
    async def enqueue(
        self,
        payload: Dict[str, Any],
        priority: int = 0,
        scheduled_time: Optional[datetime] = None,
        expiry_time: Optional[datetime] = None,
        correlation_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        tags: List[str] = None,
        metadata: Dict[str, Any] = None
    ) -> str:
        """Enqueue a message"""
        try:
            if not self.is_running:
                raise RuntimeError(f"Queue {self.queue_name} is not running")
            
            # Create message
            message = QueuedMessage(
                message_id=str(uuid.uuid4()),
                queue_name=self.queue_name,
                payload=payload,
                priority=priority,
                scheduled_time=scheduled_time,
                expiry_time=expiry_time or (
                    datetime.now(timezone.utc) + self.config.message_ttl 
                    if self.config.message_ttl else None
                ),
                correlation_id=correlation_id,
                tenant_id=tenant_id,
                tags=tags or [],
                metadata=metadata or {}
            )
            
            # Add to queue based on type
            if self.config.queue_type == QueueType.PRIORITY:
                heapq.heappush(self.messages, message)
            elif self.config.queue_type == QueueType.DELAYED:
                # For delayed messages, store until scheduled time
                self.message_registry[message.message_id] = message
            else:
                await self.messages.put(message)
            
            # Register message
            self.message_registry[message.message_id] = message
            
            # Update metrics
            self.metrics.total_messages += 1
            self.metrics.queued_messages += 1
            self.metrics.current_queue_size = len(self.message_registry)
            
            if self.metrics.current_queue_size > self.metrics.peak_queue_size:
                self.metrics.peak_queue_size = self.metrics.current_queue_size
            
            self.logger.debug(f"Message enqueued: {message.message_id}")
            
            return message.message_id
            
        except Exception as e:
            self.logger.error(f"Error enqueueing message: {str(e)}")
            raise
    
    async def dequeue(self, consumer_id: str, timeout: Optional[float] = None) -> Optional[QueuedMessage]:
        """Dequeue a message"""
        try:
            if not self.is_running or self.is_paused:
                return None
            
            message = None
            
            # Get message based on queue type
            if self.config.queue_type == QueueType.PRIORITY:
                if self.messages:
                    message = heapq.heappop(self.messages)
            else:
                try:
                    message = await asyncio.wait_for(
                        self.messages.get(), 
                        timeout=timeout or 1.0
                    )
                except asyncio.TimeoutError:
                    return None
            
            if message:
                # Check if message is ready to process
                current_time = datetime.now(timezone.utc)
                
                if message.scheduled_time and message.scheduled_time > current_time:
                    # Put message back if not ready
                    await self._requeue_message(message)
                    return None
                
                # Check expiry
                if message.expiry_time and message.expiry_time <= current_time:
                    await self._handle_expired_message(message)
                    return None
                
                # Mark as processing
                message.status = MessageStatus.PROCESSING
                message.processing_time = current_time
                message.consumer_id = consumer_id
                
                self.processing_messages[message.message_id] = message
                
                # Update metrics
                self.metrics.queued_messages -= 1
                self.metrics.processing_messages += 1
                
                return message
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error dequeuing message: {str(e)}")
            return None
    
    async def ack_message(self, message_id: str, result: Any = None) -> bool:
        """Acknowledge successful message processing"""
        try:
            if message_id in self.processing_messages:
                message = self.processing_messages[message_id]
                
                # Mark as completed
                message.status = MessageStatus.COMPLETED
                message.completion_time = datetime.now(timezone.utc)
                
                # Calculate processing time
                if message.processing_time:
                    processing_duration = (message.completion_time - message.processing_time).total_seconds()
                    
                    # Update average processing time
                    total_processed = self.metrics.completed_messages + 1
                    self.metrics.average_processing_time = (
                        (self.metrics.average_processing_time * self.metrics.completed_messages + processing_duration) / 
                        total_processed
                    )
                
                # Move to completed
                self.completed_messages[message_id] = message
                del self.processing_messages[message_id]
                
                # Update metrics
                self.metrics.processing_messages -= 1
                self.metrics.completed_messages += 1
                self.metrics.current_queue_size = len(self.message_registry)
                
                self.logger.debug(f"Message acknowledged: {message_id}")
                
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error acknowledging message {message_id}: {str(e)}")
            return False
    
    async def nack_message(self, message_id: str, error: str = None) -> bool:
        """Negative acknowledge - message processing failed"""
        try:
            if message_id in self.processing_messages:
                message = self.processing_messages[message_id]
                
                # Increment retry count
                message.retry_count += 1
                
                # Check if we should retry
                if message.retry_count <= message.max_retries:
                    # Calculate retry delay
                    retry_delays = self.config.retry_delays
                    delay_index = min(message.retry_count - 1, len(retry_delays) - 1)
                    retry_delay = retry_delays[delay_index]
                    
                    # Schedule retry
                    message.scheduled_time = datetime.now(timezone.utc) + timedelta(seconds=retry_delay)
                    message.status = MessageStatus.RETRY
                    
                    # Add error to metadata
                    if not message.metadata:
                        message.metadata = {}
                    if 'errors' not in message.metadata:
                        message.metadata['errors'] = []
                    message.metadata['errors'].append({
                        'timestamp': datetime.now(timezone.utc).isoformat(),
                        'error': error,
                        'retry_count': message.retry_count
                    })
                    
                    # Requeue for retry
                    await self._requeue_message(message)
                    
                    # Update metrics
                    self.metrics.retry_messages += 1
                    
                    self.logger.info(f"Message scheduled for retry: {message_id} (attempt {message.retry_count})")
                
                else:
                    # Move to dead letter queue
                    await self._send_to_dead_letter(message, error)
                
                # Remove from processing
                del self.processing_messages[message_id]
                self.metrics.processing_messages -= 1
                
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error nacking message {message_id}: {str(e)}")
            return False
    
    async def register_consumer(self, consumer_id: str, callback: Callable) -> bool:
        """Register a message consumer"""
        try:
            self.consumers[consumer_id] = callback
            self.logger.info(f"Consumer registered: {consumer_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error registering consumer {consumer_id}: {str(e)}")
            return False
    
    async def unregister_consumer(self, consumer_id: str) -> bool:
        """Unregister a message consumer"""
        try:
            if consumer_id in self.consumers:
                del self.consumers[consumer_id]
                self.active_workers.discard(consumer_id)
                self.logger.info(f"Consumer unregistered: {consumer_id}")
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"Error unregistering consumer {consumer_id}: {str(e)}")
            return False
    
    async def _worker_loop(self, worker_id: str):
        """Main worker processing loop"""
        self.active_workers.add(worker_id)
        
        try:
            while self.is_running:
                try:
                    if self.is_paused:
                        await asyncio.sleep(1)
                        continue
                    
                    # Get next message
                    message = await self.dequeue(worker_id, timeout=5.0)
                    
                    if message:
                        # Process message
                        await self._process_message(message, worker_id)
                    
                except Exception as e:
                    self.logger.error(f"Error in worker {worker_id}: {str(e)}")
                    await asyncio.sleep(1)
        
        finally:
            self.active_workers.discard(worker_id)
    
    async def _process_message(self, message: QueuedMessage, worker_id: str):
        """Process a single message"""
        try:
            # Find appropriate consumer
            consumer_callback = None
            
            # Strategy-based consumer selection
            if self.config.strategy == QueueStrategy.SINGLE_CONSUMER:
                if self.consumers:
                    consumer_callback = next(iter(self.consumers.values()))
            elif self.config.strategy == QueueStrategy.ROUND_ROBIN:
                if self.consumers:
                    consumer_ids = list(self.consumers.keys())
                    index = hash(message.message_id) % len(consumer_ids)
                    consumer_callback = self.consumers[consumer_ids[index]]
            else:
                # Default to first available consumer
                if self.consumers:
                    consumer_callback = next(iter(self.consumers.values()))
            
            if consumer_callback:
                # Execute consumer
                if asyncio.iscoroutinefunction(consumer_callback):
                    result = await consumer_callback(message)
                else:
                    result = consumer_callback(message)
                
                # Handle result
                if result:
                    await self.ack_message(message.message_id, result)
                else:
                    await self.nack_message(message.message_id, "Consumer returned False")
            else:
                # No consumer available - requeue
                await self._requeue_message(message)
                
        except Exception as e:
            self.logger.error(f"Error processing message {message.message_id}: {str(e)}")
            await self.nack_message(message.message_id, str(e))
    
    async def _requeue_message(self, message: QueuedMessage):
        """Requeue a message"""
        try:
            # Reset processing state
            message.status = MessageStatus.QUEUED
            message.processing_time = None
            message.consumer_id = None
            
            # Add back to queue
            if self.config.queue_type == QueueType.PRIORITY:
                heapq.heappush(self.messages, message)
            else:
                await self.messages.put(message)
            
        except Exception as e:
            self.logger.error(f"Error requeuing message {message.message_id}: {str(e)}")
    
    async def _send_to_dead_letter(self, message: QueuedMessage, error: str = None):
        """Send message to dead letter queue"""
        try:
            message.status = MessageStatus.DEAD_LETTER
            
            if error and message.metadata:
                if 'final_error' not in message.metadata:
                    message.metadata['final_error'] = error
            
            self.failed_messages[message.message_id] = message
            
            # Update metrics
            self.metrics.failed_messages += 1
            self.metrics.dead_letter_messages += 1
            
            self.logger.warning(f"Message sent to dead letter: {message.message_id}")
            
        except Exception as e:
            self.logger.error(f"Error sending message to dead letter: {str(e)}")
    
    async def _handle_expired_message(self, message: QueuedMessage):
        """Handle expired message"""
        try:
            message.status = MessageStatus.EXPIRED
            self.failed_messages[message.message_id] = message
            
            # Update metrics
            self.metrics.expired_messages += 1
            
            self.logger.debug(f"Message expired: {message.message_id}")
            
        except Exception as e:
            self.logger.error(f"Error handling expired message: {str(e)}")
    
    async def _batch_processor_loop(self):
        """Process messages in batches if configured"""
        while self.is_running:
            try:
                if self.config.queue_type == QueueType.BATCH:
                    current_time = datetime.now(timezone.utc)
                    time_since_last_batch = (current_time - self.last_batch_time).total_seconds()
                    
                    if (len(self.batch_buffer) >= self.config.batch_size or 
                        time_since_last_batch >= self.config.batch_timeout):
                        
                        if self.batch_buffer:
                            await self._process_batch(self.batch_buffer.copy())
                            self.batch_buffer.clear()
                            self.last_batch_time = current_time
                
                await asyncio.sleep(1)
                
            except Exception as e:
                self.logger.error(f"Error in batch processor: {str(e)}")
    
    async def _process_batch(self, batch: List[QueuedMessage]):
        """Process a batch of messages"""
        try:
            # Find batch consumer
            batch_consumer = None
            for consumer in self.consumers.values():
                if hasattr(consumer, '__batch_processor__'):
                    batch_consumer = consumer
                    break
            
            if batch_consumer:
                if asyncio.iscoroutinefunction(batch_consumer):
                    results = await batch_consumer(batch)
                else:
                    results = batch_consumer(batch)
                
                # Handle batch results
                if isinstance(results, list) and len(results) == len(batch):
                    for message, result in zip(batch, results):
                        if result:
                            await self.ack_message(message.message_id, result)
                        else:
                            await self.nack_message(message.message_id, "Batch processing failed")
                else:
                    # All succeeded or all failed
                    for message in batch:
                        if results:
                            await self.ack_message(message.message_id)
                        else:
                            await self.nack_message(message.message_id, "Batch processing failed")
            
        except Exception as e:
            self.logger.error(f"Error processing batch: {str(e)}")
            # Mark all messages in batch as failed
            for message in batch:
                await self.nack_message(message.message_id, str(e))
    
    async def _maintenance_loop(self):
        """Periodic maintenance tasks"""
        while self.is_running:
            try:
                await asyncio.sleep(60)  # Run every minute
                
                # Clean up old completed messages
                await self._cleanup_old_messages()
                
                # Process delayed messages
                await self._process_delayed_messages()
                
                # Persist messages if enabled
                if self.config.enable_persistence:
                    await self._persist_messages()
                
            except Exception as e:
                self.logger.error(f"Error in maintenance loop: {str(e)}")
    
    async def _cleanup_old_messages(self):
        """Clean up old completed and failed messages"""
        try:
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)
            
            # Clean completed messages
            to_remove = [
                msg_id for msg_id, msg in self.completed_messages.items()
                if msg.completion_time and msg.completion_time < cutoff_time
            ]
            
            for msg_id in to_remove:
                del self.completed_messages[msg_id]
                if msg_id in self.message_registry:
                    del self.message_registry[msg_id]
            
            # Clean failed messages (keep them longer)
            failed_cutoff = datetime.now(timezone.utc) - timedelta(days=7)
            to_remove = [
                msg_id for msg_id, msg in self.failed_messages.items()
                if msg.completion_time and msg.completion_time < failed_cutoff
            ]
            
            for msg_id in to_remove:
                del self.failed_messages[msg_id]
                if msg_id in self.message_registry:
                    del self.message_registry[msg_id]
            
            if to_remove:
                self.logger.debug(f"Cleaned up {len(to_remove)} old messages")
                
        except Exception as e:
            self.logger.error(f"Error cleaning up old messages: {str(e)}")
    
    async def _process_delayed_messages(self):
        """Process delayed messages that are now ready"""
        try:
            if self.config.queue_type != QueueType.DELAYED:
                return
            
            current_time = datetime.now(timezone.utc)
            ready_messages = []
            
            for message in self.message_registry.values():
                if (message.status == MessageStatus.QUEUED and 
                    message.scheduled_time and 
                    message.scheduled_time <= current_time):
                    ready_messages.append(message)
            
            # Add ready messages to queue
            for message in ready_messages:
                await self.messages.put(message)
                
        except Exception as e:
            self.logger.error(f"Error processing delayed messages: {str(e)}")
    
    async def _metrics_loop(self):
        """Update metrics periodically"""
        while self.is_running:
            try:
                await asyncio.sleep(30)  # Update every 30 seconds
                
                self.metrics.last_updated = datetime.now(timezone.utc)
                self.metrics.current_queue_size = len(self.message_registry)
                
            except Exception as e:
                self.logger.error(f"Error updating metrics: {str(e)}")
    
    async def _persist_messages(self):
        """Persist messages to storage"""
        try:
            if not self.config.enable_persistence or not self.config.persistence_path:
                return
            
            async with self.persistence_lock:
                persistence_file = self.config.persistence_path / f"{self.queue_name}.json"
                
                # Prepare data for persistence
                persistence_data = {
                    'queue_name': self.queue_name,
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'messages': [msg.to_dict() for msg in self.message_registry.values()],
                    'metrics': asdict(self.metrics)
                }
                
                # Write to file
                async with aiofiles.open(persistence_file, 'w') as f:
                    await f.write(json.dumps(persistence_data, indent=2))
                
        except Exception as e:
            self.logger.error(f"Error persisting messages: {str(e)}")
    
    async def _load_persisted_messages(self):
        """Load persisted messages from storage"""
        try:
            if not self.config.persistence_path:
                return
            
            persistence_file = self.config.persistence_path / f"{self.queue_name}.json"
            
            if not persistence_file.exists():
                return
            
            async with aiofiles.open(persistence_file, 'r') as f:
                content = await f.read()
                persistence_data = json.loads(content)
            
            # Restore messages
            for msg_data in persistence_data.get('messages', []):
                message = QueuedMessage.from_dict(msg_data)
                
                # Only restore queued and retry messages
                if message.status in [MessageStatus.QUEUED, MessageStatus.RETRY]:
                    self.message_registry[message.message_id] = message
                    
                    if self.config.queue_type == QueueType.PRIORITY:
                        heapq.heappush(self.messages, message)
                    else:
                        await self.messages.put(message)
            
            self.logger.info(f"Loaded {len(persistence_data.get('messages', []))} persisted messages")
            
        except Exception as e:
            self.logger.error(f"Error loading persisted messages: {str(e)}")
    
    def get_metrics(self) -> QueueMetrics:
        """Get current queue metrics"""
        self.metrics.current_queue_size = len(self.message_registry)
        self.metrics.last_updated = datetime.now(timezone.utc)
        return self.metrics
    
    def get_status(self) -> Dict[str, Any]:
        """Get queue status"""
        return {
            'queue_name': self.queue_name,
            'queue_type': self.config.queue_type.value,
            'is_running': self.is_running,
            'is_paused': self.is_paused,
            'active_workers': len(self.active_workers),
            'consumers': len(self.consumers),
            'metrics': asdict(self.get_metrics())
        }


class QueueManager:
    """
    Queue Manager for TaxPoynt Platform
    
    Manages multiple message queues with different characteristics:
    - Priority queues for urgent messages
    - FIFO queues for ordered processing
    - Delayed queues for scheduled messages
    - Batch queues for bulk processing
    - Streaming queues for real-time data
    """
    
    def __init__(self, persistence_root: Optional[Path] = None):
        """Initialize the queue manager"""
        self.queues: Dict[str, MessageQueue] = {}
        self.queue_configs: Dict[str, QueueConfiguration] = {}
        self.persistence_root = persistence_root or Path("./queue_data")
        
        # Global metrics
        self.global_metrics = {
            'total_queues': 0,
            'total_messages': 0,
            'total_processed': 0,
            'total_failed': 0
        }
        
        self.logger = logging.getLogger(__name__)
        self.is_initialized = False
    
    async def initialize(self):
        """Initialize the queue manager"""
        if self.is_initialized:
            return
        
        self.logger.info("Initializing Queue Manager")
        
        # Create persistence directory
        if not self.persistence_root.exists():
            self.persistence_root.mkdir(parents=True, exist_ok=True)
        
        # Set up default queues
        await self._setup_default_queues()
        
        self.is_initialized = True
        self.logger.info("Queue Manager initialized")
    
    async def create_queue(self, config: QueueConfiguration) -> bool:
        """Create a new message queue"""
        try:
            if config.queue_name in self.queues:
                self.logger.warning(f"Queue already exists: {config.queue_name}")
                return False
            
            # Set persistence path
            if config.enable_persistence and not config.persistence_path:
                config.persistence_path = self.persistence_root
            
            # Create queue
            queue = MessageQueue(config)
            await queue.start()
            
            self.queues[config.queue_name] = queue
            self.queue_configs[config.queue_name] = config
            
            self.global_metrics['total_queues'] += 1
            
            self.logger.info(f"Queue created: {config.queue_name} ({config.queue_type.value})")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error creating queue {config.queue_name}: {str(e)}")
            return False
    
    async def delete_queue(self, queue_name: str, force: bool = False) -> bool:
        """Delete a message queue"""
        try:
            if queue_name not in self.queues:
                return False
            
            queue = self.queues[queue_name]
            
            # Check if queue is empty
            if not force and queue.get_metrics().current_queue_size > 0:
                self.logger.warning(f"Cannot delete non-empty queue: {queue_name}")
                return False
            
            # Stop queue
            await queue.stop()
            
            # Remove from tracking
            del self.queues[queue_name]
            del self.queue_configs[queue_name]
            
            self.global_metrics['total_queues'] -= 1
            
            self.logger.info(f"Queue deleted: {queue_name}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error deleting queue {queue_name}: {str(e)}")
            return False
    
    async def get_queue(self, queue_name: str) -> Optional[MessageQueue]:
        """Get a queue by name"""
        return self.queues.get(queue_name)
    
    async def enqueue_message(
        self,
        queue_name: str,
        payload: Dict[str, Any],
        **kwargs
    ) -> Optional[str]:
        """Enqueue a message to a specific queue"""
        try:
            queue = self.queues.get(queue_name)
            if not queue:
                self.logger.error(f"Queue not found: {queue_name}")
                return None
            
            message_id = await queue.enqueue(payload, **kwargs)
            
            self.global_metrics['total_messages'] += 1
            
            return message_id
            
        except Exception as e:
            self.logger.error(f"Error enqueueing message to {queue_name}: {str(e)}")
            return None
    
    async def register_consumer(
        self,
        queue_name: str,
        consumer_id: str,
        callback: Callable
    ) -> bool:
        """Register a consumer for a queue"""
        try:
            queue = self.queues.get(queue_name)
            if not queue:
                self.logger.error(f"Queue not found: {queue_name}")
                return False
            
            return await queue.register_consumer(consumer_id, callback)
            
        except Exception as e:
            self.logger.error(f"Error registering consumer: {str(e)}")
            return False
    
    async def _setup_default_queues(self):
        """Set up default system queues"""
        default_queues = [
            QueueConfiguration(
                queue_name="priority_events",
                queue_type=QueueType.PRIORITY,
                max_workers=3,
                message_ttl=timedelta(hours=1)
            ),
            QueueConfiguration(
                queue_name="si_processing",
                queue_type=QueueType.FIFO,
                max_workers=5,
                strategy=QueueStrategy.LOAD_BALANCED
            ),
            QueueConfiguration(
                queue_name="app_notifications",
                queue_type=QueueType.FIFO,
                max_workers=3,
                strategy=QueueStrategy.ROUND_ROBIN
            ),
            QueueConfiguration(
                queue_name="batch_processing",
                queue_type=QueueType.BATCH,
                batch_size=50,
                batch_timeout=10.0,
                max_workers=2
            ),
            QueueConfiguration(
                queue_name="delayed_tasks",
                queue_type=QueueType.DELAYED,
                max_workers=2
            ),
            QueueConfiguration(
                queue_name="dead_letter",
                queue_type=QueueType.FIFO,
                max_workers=1,
                enable_persistence=True
            )
        ]
        
        for config in default_queues:
            await self.create_queue(config)
    
    async def get_global_metrics(self) -> Dict[str, Any]:
        """Get global queue manager metrics"""
        # Update global metrics
        total_messages = 0
        total_processed = 0
        total_failed = 0
        
        for queue in self.queues.values():
            metrics = queue.get_metrics()
            total_messages += metrics.total_messages
            total_processed += metrics.completed_messages
            total_failed += metrics.failed_messages
        
        self.global_metrics.update({
            'total_messages': total_messages,
            'total_processed': total_processed,
            'total_failed': total_failed
        })
        
        return self.global_metrics.copy()
    
    async def get_all_queue_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all queues"""
        status = {}
        
        for queue_name, queue in self.queues.items():
            status[queue_name] = queue.get_status()
        
        return status
    
    async def pause_queue(self, queue_name: str) -> bool:
        """Pause a specific queue"""
        queue = self.queues.get(queue_name)
        if queue:
            await queue.pause()
            return True
        return False
    
    async def resume_queue(self, queue_name: str) -> bool:
        """Resume a specific queue"""
        queue = self.queues.get(queue_name)
        if queue:
            await queue.resume()
            return True
        return False
    
    async def shutdown(self):
        """Shutdown all queues"""
        self.logger.info("Shutting down Queue Manager")
        
        shutdown_tasks = []
        for queue in self.queues.values():
            shutdown_tasks.append(queue.stop())
        
        if shutdown_tasks:
            await asyncio.gather(*shutdown_tasks, return_exceptions=True)
        
        self.queues.clear()
        self.queue_configs.clear()
        
        self.logger.info("Queue Manager shutdown complete")


# Global queue manager instance
_global_queue_manager: Optional[QueueManager] = None


def get_queue_manager() -> QueueManager:
    """Get global queue manager instance"""
    global _global_queue_manager
    if _global_queue_manager is None:
        _global_queue_manager = QueueManager()
    return _global_queue_manager


async def initialize_queue_manager(persistence_root: Optional[Path] = None) -> QueueManager:
    """Initialize and start the global queue manager"""
    global _global_queue_manager
    _global_queue_manager = QueueManager(persistence_root)
    await _global_queue_manager.initialize()
    return _global_queue_manager