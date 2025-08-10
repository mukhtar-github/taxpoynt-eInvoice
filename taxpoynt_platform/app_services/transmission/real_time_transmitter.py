"""
Real-Time Document Transmission Service for APP Role

This service handles real-time transmission of documents to FIRS with:
- WebSocket connections for real-time updates
- Stream processing for continuous transmission
- Priority queuing for urgent documents
- Live status updates and notifications
- Event-driven architecture
"""

import asyncio
import json
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple, Union, AsyncIterator, Callable
from dataclasses import dataclass, field
from enum import Enum
import logging
from collections import deque
import websockets
import aiohttp
from asyncio import Queue, PriorityQueue
import heapq

from .secure_transmitter import (
    SecureTransmitter, TransmissionRequest, TransmissionResult,
    TransmissionStatus, SecurityLevel, SecurityContext
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RealTimeStatus(Enum):
    """Real-time transmission status"""
    QUEUED = "queued"
    PROCESSING = "processing"
    STREAMING = "streaming"
    TRANSMITTED = "transmitted"
    ACKNOWLEDGED = "acknowledged"
    FAILED = "failed"


class PriorityLevel(Enum):
    """Priority levels for real-time transmission"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4
    CRITICAL = 5


class EventType(Enum):
    """Event types for real-time notifications"""
    DOCUMENT_QUEUED = "document_queued"
    TRANSMISSION_STARTED = "transmission_started"
    TRANSMISSION_COMPLETED = "transmission_completed"
    TRANSMISSION_FAILED = "transmission_failed"
    STREAM_CONNECTED = "stream_connected"
    STREAM_DISCONNECTED = "stream_disconnected"
    ACKNOWLEDGMENT_RECEIVED = "acknowledgment_received"


@dataclass
class RealTimeRequest:
    """Real-time transmission request"""
    request_id: str
    document_id: str
    document_type: str
    document_data: Dict[str, Any]
    destination_endpoint: str
    priority: PriorityLevel = PriorityLevel.NORMAL
    security_level: SecurityLevel = SecurityLevel.STANDARD
    requires_acknowledgment: bool = False
    timeout: int = 30
    callback_url: Optional[str] = None
    webhook_url: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def __lt__(self, other):
        """For priority queue ordering"""
        return self.priority.value > other.priority.value


@dataclass
class RealTimeEvent:
    """Real-time event notification"""
    event_id: str
    event_type: EventType
    request_id: str
    document_id: str
    timestamp: datetime
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RealTimeResult:
    """Real-time transmission result"""
    request_id: str
    document_id: str
    status: RealTimeStatus
    transmission_result: Optional[TransmissionResult] = None
    events: List[RealTimeEvent] = field(default_factory=list)
    queued_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    processing_time: Optional[float] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class StreamConnection:
    """WebSocket stream connection for real-time updates"""
    
    def __init__(self, connection_id: str, websocket, client_info: Dict[str, Any]):
        self.connection_id = connection_id
        self.websocket = websocket
        self.client_info = client_info
        self.connected_at = datetime.utcnow()
        self.last_ping = datetime.utcnow()
        self.subscriptions: set = set()
        self.is_active = True
    
    async def send_event(self, event: RealTimeEvent):
        """Send event to connected client"""
        try:
            if self.is_active:
                event_data = {
                    'event_id': event.event_id,
                    'event_type': event.event_type.value,
                    'request_id': event.request_id,
                    'document_id': event.document_id,
                    'timestamp': event.timestamp.isoformat(),
                    'data': event.data,
                    'metadata': event.metadata
                }
                await self.websocket.send(json.dumps(event_data))
        except Exception as e:
            logger.error(f"Failed to send event to {self.connection_id}: {e}")
            self.is_active = False
    
    async def ping(self):
        """Send ping to keep connection alive"""
        try:
            if self.is_active:
                await self.websocket.ping()
                self.last_ping = datetime.utcnow()
        except Exception as e:
            logger.error(f"Failed to ping {self.connection_id}: {e}")
            self.is_active = False


class RealTimeTransmitter:
    """
    Real-time document transmission service for APP role
    
    Handles:
    - Priority-based queuing system
    - WebSocket connections for live updates
    - Stream processing for continuous transmission
    - Event-driven notifications
    - Real-time status monitoring
    """
    
    def __init__(self, 
                 secure_transmitter: SecureTransmitter,
                 max_concurrent_transmissions: int = 10,
                 websocket_host: str = "localhost",
                 websocket_port: int = 8765,
                 stream_buffer_size: int = 1000):
        self.secure_transmitter = secure_transmitter
        self.max_concurrent_transmissions = max_concurrent_transmissions
        self.websocket_host = websocket_host
        self.websocket_port = websocket_port
        self.stream_buffer_size = stream_buffer_size
        
        # Queues and buffers
        self._priority_queue = PriorityQueue()
        self._processing_queue = Queue(maxsize=stream_buffer_size)
        self._event_queue = Queue(maxsize=stream_buffer_size)
        
        # Active connections and requests
        self._active_connections: Dict[str, StreamConnection] = {}
        self._active_requests: Dict[str, RealTimeRequest] = {}
        self._request_results: Dict[str, RealTimeResult] = {}
        
        # Control flags
        self._is_running = False
        self._processor_tasks: List[asyncio.Task] = []
        self._websocket_server = None
        
        # Synchronization
        self._transmission_semaphore = asyncio.Semaphore(max_concurrent_transmissions)
        
        # Metrics
        self.metrics = {
            'total_requests': 0,
            'successful_transmissions': 0,
            'failed_transmissions': 0,
            'average_processing_time': 0.0,
            'queue_size': 0,
            'active_connections': 0,
            'events_sent': 0,
            'acknowledgments_received': 0
        }
    
    async def start(self):
        """Start the real-time transmitter service"""
        if self._is_running:
            return
        
        self._is_running = True
        
        # Start processor tasks
        self._processor_tasks = [
            asyncio.create_task(self._queue_processor()),
            asyncio.create_task(self._event_processor()),
            asyncio.create_task(self._connection_monitor())
        ]
        
        # Start WebSocket server
        self._websocket_server = await websockets.serve(
            self._handle_websocket_connection,
            self.websocket_host,
            self.websocket_port
        )
        
        logger.info(f"Real-time transmitter started on ws://{self.websocket_host}:{self.websocket_port}")
    
    async def stop(self):
        """Stop the real-time transmitter service"""
        if not self._is_running:
            return
        
        self._is_running = False
        
        # Cancel processor tasks
        for task in self._processor_tasks:
            task.cancel()
        
        await asyncio.gather(*self._processor_tasks, return_exceptions=True)
        
        # Close WebSocket server
        if self._websocket_server:
            self._websocket_server.close()
            await self._websocket_server.wait_closed()
        
        # Close active connections
        for connection in self._active_connections.values():
            await connection.websocket.close()
        
        self._active_connections.clear()
        
        logger.info("Real-time transmitter stopped")
    
    async def submit_request(self, request: RealTimeRequest) -> str:
        """
        Submit a real-time transmission request
        
        Args:
            request: Real-time transmission request
            
        Returns:
            Request ID for tracking
        """
        # Store request
        self._active_requests[request.request_id] = request
        
        # Create initial result
        result = RealTimeResult(
            request_id=request.request_id,
            document_id=request.document_id,
            status=RealTimeStatus.QUEUED,
            queued_at=datetime.utcnow()
        )
        
        self._request_results[request.request_id] = result
        
        # Add to priority queue
        await self._priority_queue.put(request)
        
        # Send queued event
        await self._send_event(RealTimeEvent(
            event_id=str(uuid.uuid4()),
            event_type=EventType.DOCUMENT_QUEUED,
            request_id=request.request_id,
            document_id=request.document_id,
            timestamp=datetime.utcnow(),
            data={'priority': request.priority.value}
        ))
        
        # Update metrics
        self.metrics['total_requests'] += 1
        self.metrics['queue_size'] = self._priority_queue.qsize()
        
        logger.info(f"Request {request.request_id} queued for real-time transmission")
        
        return request.request_id
    
    async def _queue_processor(self):
        """Process priority queue for real-time transmissions"""
        while self._is_running:
            try:
                # Get next request from priority queue
                request = await self._priority_queue.get()
                
                # Update metrics
                self.metrics['queue_size'] = self._priority_queue.qsize()
                
                # Process request
                await self._process_request(request)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in queue processor: {e}")
                await asyncio.sleep(1)
    
    async def _process_request(self, request: RealTimeRequest):
        """Process a real-time transmission request"""
        # Acquire transmission semaphore
        async with self._transmission_semaphore:
            await self._transmit_request(request)
    
    async def _transmit_request(self, request: RealTimeRequest):
        """Transmit a real-time request"""
        request_id = request.request_id
        result = self._request_results.get(request_id)
        
        if not result:
            return
        
        start_time = time.time()
        
        try:
            # Update status
            result.status = RealTimeStatus.PROCESSING
            result.started_at = datetime.utcnow()
            
            # Send processing event
            await self._send_event(RealTimeEvent(
                event_id=str(uuid.uuid4()),
                event_type=EventType.TRANSMISSION_STARTED,
                request_id=request_id,
                document_id=request.document_id,
                timestamp=datetime.utcnow(),
                data={'priority': request.priority.value}
            ))
            
            # Create transmission request
            transmission_request = TransmissionRequest(
                document_id=request.document_id,
                document_type=request.document_type,
                document_data=request.document_data,
                destination_endpoint=request.destination_endpoint,
                security_level=request.security_level,
                metadata=request.metadata
            )
            
            # Stream transmission
            result.status = RealTimeStatus.STREAMING
            
            # Transmit document
            transmission_result = await self.secure_transmitter.transmit_document(
                transmission_request
            )
            
            # Update result
            result.transmission_result = transmission_result
            
            if transmission_result.status == TransmissionStatus.DELIVERED:
                result.status = RealTimeStatus.TRANSMITTED
                
                # Send completion event
                await self._send_event(RealTimeEvent(
                    event_id=str(uuid.uuid4()),
                    event_type=EventType.TRANSMISSION_COMPLETED,
                    request_id=request_id,
                    document_id=request.document_id,
                    timestamp=datetime.utcnow(),
                    data={
                        'transmission_id': transmission_result.transmission_id,
                        'processing_time': time.time() - start_time
                    }
                ))
                
                # Wait for acknowledgment if required
                if request.requires_acknowledgment:
                    await self._wait_for_acknowledgment(request, result)
                
                # Update metrics
                self.metrics['successful_transmissions'] += 1
                
            else:
                result.status = RealTimeStatus.FAILED
                result.error_message = transmission_result.error_message
                
                # Send failure event
                await self._send_event(RealTimeEvent(
                    event_id=str(uuid.uuid4()),
                    event_type=EventType.TRANSMISSION_FAILED,
                    request_id=request_id,
                    document_id=request.document_id,
                    timestamp=datetime.utcnow(),
                    data={'error': transmission_result.error_message}
                ))
                
                # Update metrics
                self.metrics['failed_transmissions'] += 1
            
            # Send webhook notification if configured
            if request.webhook_url:
                await self._send_webhook_notification(request, result)
            
        except Exception as e:
            result.status = RealTimeStatus.FAILED
            result.error_message = str(e)
            
            # Send failure event
            await self._send_event(RealTimeEvent(
                event_id=str(uuid.uuid4()),
                event_type=EventType.TRANSMISSION_FAILED,
                request_id=request_id,
                document_id=request.document_id,
                timestamp=datetime.utcnow(),
                data={'error': str(e)}
            ))
            
            # Update metrics
            self.metrics['failed_transmissions'] += 1
            
            logger.error(f"Real-time transmission failed for {request_id}: {e}")
        
        finally:
            # Finalize result
            result.completed_at = datetime.utcnow()
            result.processing_time = time.time() - start_time
            
            # Update average processing time
            if self.metrics['total_requests'] > 0:
                self.metrics['average_processing_time'] = (
                    (self.metrics['average_processing_time'] * (self.metrics['total_requests'] - 1) + 
                     result.processing_time) / self.metrics['total_requests']
                )
            
            # Remove from active requests
            if request_id in self._active_requests:
                del self._active_requests[request_id]
    
    async def _wait_for_acknowledgment(self, request: RealTimeRequest, result: RealTimeResult):
        """Wait for acknowledgment from FIRS"""
        try:
            # Wait for acknowledgment with timeout
            await asyncio.wait_for(
                self._check_acknowledgment(request.request_id),
                timeout=request.timeout
            )
            
            result.status = RealTimeStatus.ACKNOWLEDGED
            result.acknowledged_at = datetime.utcnow()
            
            # Send acknowledgment event
            await self._send_event(RealTimeEvent(
                event_id=str(uuid.uuid4()),
                event_type=EventType.ACKNOWLEDGMENT_RECEIVED,
                request_id=request.request_id,
                document_id=request.document_id,
                timestamp=datetime.utcnow()
            ))
            
            # Update metrics
            self.metrics['acknowledgments_received'] += 1
            
        except asyncio.TimeoutError:
            logger.warning(f"Acknowledgment timeout for request {request.request_id}")
    
    async def _check_acknowledgment(self, request_id: str):
        """Check for acknowledgment (placeholder)"""
        # This would typically poll FIRS for acknowledgment
        # For now, we'll simulate a delay
        await asyncio.sleep(5)
    
    async def _send_webhook_notification(self, request: RealTimeRequest, result: RealTimeResult):
        """Send webhook notification"""
        try:
            webhook_data = {
                'request_id': request.request_id,
                'document_id': request.document_id,
                'status': result.status.value,
                'timestamp': datetime.utcnow().isoformat(),
                'transmission_id': result.transmission_result.transmission_id if result.transmission_result else None,
                'processing_time': result.processing_time,
                'error_message': result.error_message
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    request.webhook_url,
                    json=webhook_data,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        logger.info(f"Webhook notification sent for {request.request_id}")
                    else:
                        logger.warning(f"Webhook notification failed: {response.status}")
                        
        except Exception as e:
            logger.error(f"Failed to send webhook notification: {e}")
    
    async def _event_processor(self):
        """Process events for real-time notifications"""
        while self._is_running:
            try:
                # Get next event
                event = await self._event_queue.get()
                
                # Send to all connected clients
                for connection in list(self._active_connections.values()):
                    if connection.is_active:
                        await connection.send_event(event)
                
                # Update metrics
                self.metrics['events_sent'] += 1
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in event processor: {e}")
                await asyncio.sleep(1)
    
    async def _connection_monitor(self):
        """Monitor WebSocket connections"""
        while self._is_running:
            try:
                current_time = datetime.utcnow()
                
                # Check connection health
                inactive_connections = []
                for connection_id, connection in self._active_connections.items():
                    # Check if connection is stale
                    if (current_time - connection.last_ping).total_seconds() > 60:
                        await connection.ping()
                    
                    # Remove inactive connections
                    if not connection.is_active:
                        inactive_connections.append(connection_id)
                
                # Clean up inactive connections
                for connection_id in inactive_connections:
                    del self._active_connections[connection_id]
                
                # Update metrics
                self.metrics['active_connections'] = len(self._active_connections)
                
                # Sleep before next check
                await asyncio.sleep(30)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in connection monitor: {e}")
                await asyncio.sleep(5)
    
    async def _handle_websocket_connection(self, websocket, path):
        """Handle WebSocket connection"""
        connection_id = str(uuid.uuid4())
        
        try:
            # Get client info
            client_info = {
                'remote_address': websocket.remote_address,
                'path': path,
                'connected_at': datetime.utcnow().isoformat()
            }
            
            # Create connection
            connection = StreamConnection(connection_id, websocket, client_info)
            self._active_connections[connection_id] = connection
            
            # Send connection event
            await self._send_event(RealTimeEvent(
                event_id=str(uuid.uuid4()),
                event_type=EventType.STREAM_CONNECTED,
                request_id="",
                document_id="",
                timestamp=datetime.utcnow(),
                data={'connection_id': connection_id}
            ))
            
            logger.info(f"WebSocket connection established: {connection_id}")
            
            # Handle messages
            async for message in websocket:
                try:
                    data = json.loads(message)
                    await self._handle_websocket_message(connection, data)
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON from {connection_id}: {message}")
                except Exception as e:
                    logger.error(f"Error handling message from {connection_id}: {e}")
        
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"WebSocket connection closed: {connection_id}")
        except Exception as e:
            logger.error(f"WebSocket error for {connection_id}: {e}")
        finally:
            # Clean up connection
            if connection_id in self._active_connections:
                del self._active_connections[connection_id]
            
            # Send disconnection event
            await self._send_event(RealTimeEvent(
                event_id=str(uuid.uuid4()),
                event_type=EventType.STREAM_DISCONNECTED,
                request_id="",
                document_id="",
                timestamp=datetime.utcnow(),
                data={'connection_id': connection_id}
            ))
    
    async def _handle_websocket_message(self, connection: StreamConnection, data: Dict[str, Any]):
        """Handle WebSocket message from client"""
        message_type = data.get('type')
        
        if message_type == 'subscribe':
            # Subscribe to specific request updates
            request_id = data.get('request_id')
            if request_id:
                connection.subscriptions.add(request_id)
                
        elif message_type == 'unsubscribe':
            # Unsubscribe from request updates
            request_id = data.get('request_id')
            if request_id:
                connection.subscriptions.discard(request_id)
                
        elif message_type == 'ping':
            # Handle ping from client
            await connection.websocket.send(json.dumps({'type': 'pong'}))
    
    async def _send_event(self, event: RealTimeEvent):
        """Send event to event queue"""
        try:
            await self._event_queue.put(event)
        except asyncio.QueueFull:
            logger.warning("Event queue full, dropping event")
    
    async def get_request_status(self, request_id: str) -> Optional[RealTimeResult]:
        """Get request status by ID"""
        return self._request_results.get(request_id)
    
    async def get_active_requests(self) -> List[RealTimeRequest]:
        """Get list of active requests"""
        return list(self._active_requests.values())
    
    async def cancel_request(self, request_id: str) -> bool:
        """Cancel an active request"""
        if request_id in self._active_requests:
            del self._active_requests[request_id]
            
            # Update result
            if request_id in self._request_results:
                result = self._request_results[request_id]
                result.status = RealTimeStatus.FAILED
                result.error_message = "Request cancelled"
                result.completed_at = datetime.utcnow()
            
            logger.info(f"Request {request_id} cancelled")
            return True
        return False
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get real-time transmission metrics"""
        return {
            **self.metrics,
            'active_requests': len(self._active_requests),
            'completed_requests': len(self._request_results),
            'success_rate': (
                self.metrics['successful_transmissions'] / 
                max(self.metrics['total_requests'], 1)
            ) * 100,
            'acknowledgment_rate': (
                self.metrics['acknowledgments_received'] / 
                max(self.metrics['successful_transmissions'], 1)
            ) * 100
        }


# Factory functions for easy setup
def create_real_time_request(document_id: str,
                           document_type: str,
                           document_data: Dict[str, Any],
                           destination_endpoint: str,
                           priority: PriorityLevel = PriorityLevel.NORMAL,
                           requires_acknowledgment: bool = False) -> RealTimeRequest:
    """Create real-time transmission request"""
    return RealTimeRequest(
        request_id=str(uuid.uuid4()),
        document_id=document_id,
        document_type=document_type,
        document_data=document_data,
        destination_endpoint=destination_endpoint,
        priority=priority,
        requires_acknowledgment=requires_acknowledgment
    )


async def create_real_time_transmitter(secure_transmitter: SecureTransmitter,
                                     websocket_host: str = "localhost",
                                     websocket_port: int = 8765) -> RealTimeTransmitter:
    """Create and start real-time transmitter"""
    transmitter = RealTimeTransmitter(
        secure_transmitter,
        websocket_host=websocket_host,
        websocket_port=websocket_port
    )
    await transmitter.start()
    return transmitter