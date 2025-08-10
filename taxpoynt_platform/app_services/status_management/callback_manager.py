"""
Callback Manager Service for APP Role

This service manages callback mechanisms for status updates including:
- Webhook callback registration and management
- Callback delivery and retry mechanisms
- Callback authentication and security
- Real-time callback notifications
- Callback history and analytics
"""

import asyncio
import json
import time
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Set, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
import logging
from collections import defaultdict, deque
import uuid
import aiohttp
from urllib.parse import urlparse

from .status_tracker import SubmissionStatus, SubmissionRecord

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CallbackType(Enum):
    """Types of callbacks"""
    STATUS_CHANGE = "status_change"
    ERROR_NOTIFICATION = "error_notification"
    COMPLETION = "completion"
    ACKNOWLEDGMENT = "acknowledgment"
    RETRY = "retry"
    TIMEOUT = "timeout"
    CUSTOM = "custom"


class CallbackStatus(Enum):
    """Callback delivery status"""
    PENDING = "pending"
    SENDING = "sending"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETRYING = "retrying"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class AuthenticationMethod(Enum):
    """Callback authentication methods"""
    NONE = "none"
    HMAC_SHA256 = "hmac_sha256"
    BEARER_TOKEN = "bearer_token"
    BASIC_AUTH = "basic_auth"
    API_KEY = "api_key"
    CUSTOM_HEADER = "custom_header"


@dataclass
class CallbackEndpoint:
    """Callback endpoint configuration"""
    endpoint_id: str
    name: str
    url: str
    callback_types: Set[CallbackType]
    
    # Authentication
    auth_method: AuthenticationMethod = AuthenticationMethod.NONE
    auth_config: Dict[str, Any] = field(default_factory=dict)
    
    # Filtering
    submission_filters: Dict[str, Any] = field(default_factory=dict)
    status_filters: Set[SubmissionStatus] = field(default_factory=set)
    organization_filters: Set[str] = field(default_factory=set)
    
    # Delivery configuration
    timeout: int = 30
    max_retries: int = 3
    retry_backoff: int = 300  # seconds
    
    # Status
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_used: Optional[datetime] = None
    
    # Metadata
    description: str = ""
    owner_id: Optional[str] = None
    organization_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CallbackDelivery:
    """Callback delivery record"""
    delivery_id: str
    endpoint_id: str
    callback_type: CallbackType
    
    # Payload
    payload: Dict[str, Any]
    headers: Dict[str, str] = field(default_factory=dict)
    
    # Status and timing
    status: CallbackStatus = CallbackStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    scheduled_at: Optional[datetime] = None
    first_attempt_at: Optional[datetime] = None
    last_attempt_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    
    # Retry information
    retry_count: int = 0
    next_retry_at: Optional[datetime] = None
    
    # Response information
    response_status: Optional[int] = None
    response_headers: Dict[str, str] = field(default_factory=dict)
    response_body: Optional[str] = None
    response_time: Optional[float] = None
    
    # Error information
    error_message: Optional[str] = None
    error_details: Dict[str, Any] = field(default_factory=dict)
    
    # Context
    submission_id: Optional[str] = None
    document_id: Optional[str] = None
    user_id: Optional[str] = None
    organization_id: Optional[str] = None


@dataclass
class CallbackEvent:
    """Callback event structure"""
    event_id: str
    event_type: CallbackType
    submission_id: str
    document_id: Optional[str]
    timestamp: datetime
    data: Dict[str, Any]
    
    # Status information
    old_status: Optional[SubmissionStatus] = None
    new_status: Optional[SubmissionStatus] = None
    
    # Context
    user_id: Optional[str] = None
    organization_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CallbackStats:
    """Callback statistics"""
    total_callbacks: int
    delivered_callbacks: int
    failed_callbacks: int
    retry_callbacks: int
    success_rate: float
    average_response_time: float
    callbacks_by_type: Dict[str, int]
    callbacks_by_endpoint: Dict[str, int]
    callbacks_last_24h: int


class CallbackManager:
    """
    Callback manager service for APP role
    
    Handles:
    - Webhook callback registration and management
    - Callback delivery and retry mechanisms
    - Callback authentication and security
    - Real-time callback notifications
    - Callback history and analytics
    """
    
    def __init__(self,
                 max_concurrent_deliveries: int = 50,
                 default_timeout: int = 30,
                 max_retry_attempts: int = 3,
                 retry_backoff_multiplier: float = 2.0):
        
        self.max_concurrent_deliveries = max_concurrent_deliveries
        self.default_timeout = default_timeout
        self.max_retry_attempts = max_retry_attempts
        self.retry_backoff_multiplier = retry_backoff_multiplier
        
        # Storage
        self.endpoints: Dict[str, CallbackEndpoint] = {}
        self.deliveries: Dict[str, CallbackDelivery] = {}
        self.delivery_queue: deque = deque()
        self.retry_queue: deque = deque()
        
        # Event listeners
        self.event_listeners: Dict[CallbackType, List[Callable]] = defaultdict(list)
        
        # Background tasks
        self.delivery_task: Optional[asyncio.Task] = None
        self.retry_task: Optional[asyncio.Task] = None
        self.cleanup_task: Optional[asyncio.Task] = None
        self.running = False
        
        # HTTP session for callbacks
        self.http_session: Optional[aiohttp.ClientSession] = None
        
        # Semaphore for concurrent deliveries
        self.delivery_semaphore: Optional[asyncio.Semaphore] = None
        
        # Metrics
        self.metrics = {
            'total_callbacks': 0,
            'delivered_callbacks': 0,
            'failed_callbacks': 0,
            'retry_callbacks': 0,
            'callbacks_by_type': defaultdict(int),
            'callbacks_by_endpoint': defaultdict(int),
            'callbacks_by_status': defaultdict(int),
            'average_response_time': 0.0,
            'response_times': deque(maxlen=1000),
            'success_rate': 0.0,
            'endpoint_success_rates': defaultdict(float),
            'authentication_failures': 0,
            'timeout_failures': 0
        }
    
    async def start(self):
        """Start callback manager service"""
        self.running = True
        
        # Create HTTP session
        connector = aiohttp.TCPConnector(
            limit=self.max_concurrent_deliveries * 2,
            ttl_dns_cache=300,
            use_dns_cache=True
        )
        timeout = aiohttp.ClientTimeout(total=self.default_timeout)
        self.http_session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout
        )
        
        # Create semaphore for concurrent deliveries
        self.delivery_semaphore = asyncio.Semaphore(self.max_concurrent_deliveries)
        
        # Start background tasks
        self.delivery_task = asyncio.create_task(self._process_delivery_queue())
        self.retry_task = asyncio.create_task(self._process_retry_queue())
        self.cleanup_task = asyncio.create_task(self._periodic_cleanup())
        
        logger.info("Callback manager service started")
    
    async def stop(self):
        """Stop callback manager service"""
        self.running = False
        
        # Cancel background tasks
        if self.delivery_task:
            self.delivery_task.cancel()
        if self.retry_task:
            self.retry_task.cancel()
        if self.cleanup_task:
            self.cleanup_task.cancel()
        
        # Close HTTP session
        if self.http_session:
            await self.http_session.close()
        
        logger.info("Callback manager service stopped")
    
    def register_endpoint(self,
                         url: str,
                         callback_types: Set[CallbackType],
                         name: Optional[str] = None,
                         auth_method: AuthenticationMethod = AuthenticationMethod.NONE,
                         auth_config: Optional[Dict[str, Any]] = None,
                         filters: Optional[Dict[str, Any]] = None,
                         **kwargs) -> str:
        """
        Register callback endpoint
        
        Args:
            url: Callback URL
            callback_types: Types of callbacks to send
            name: Endpoint name
            auth_method: Authentication method
            auth_config: Authentication configuration
            filters: Callback filters
            **kwargs: Additional endpoint configuration
            
        Returns:
            Endpoint ID
        """
        endpoint_id = str(uuid.uuid4())
        
        # Validate URL
        parsed_url = urlparse(url)
        if not parsed_url.scheme or not parsed_url.netloc:
            raise ValueError("Invalid callback URL")
        
        # Create endpoint
        endpoint = CallbackEndpoint(
            endpoint_id=endpoint_id,
            name=name or f"Endpoint {endpoint_id[:8]}",
            url=url,
            callback_types=callback_types,
            auth_method=auth_method,
            auth_config=auth_config or {},
            **kwargs
        )
        
        # Apply filters
        if filters:
            if 'submission_filters' in filters:
                endpoint.submission_filters = filters['submission_filters']
            if 'status_filters' in filters:
                endpoint.status_filters = set(filters['status_filters'])
            if 'organization_filters' in filters:
                endpoint.organization_filters = set(filters['organization_filters'])
        
        # Store endpoint
        self.endpoints[endpoint_id] = endpoint
        
        logger.info(f"Registered callback endpoint {endpoint_id}: {url}")
        
        return endpoint_id
    
    def unregister_endpoint(self, endpoint_id: str) -> bool:
        """Unregister callback endpoint"""
        if endpoint_id in self.endpoints:
            endpoint = self.endpoints[endpoint_id]
            endpoint.is_active = False
            logger.info(f"Unregistered callback endpoint {endpoint_id}")
            return True
        
        return False
    
    async def trigger_callback(self,
                             event: CallbackEvent,
                             immediate: bool = False) -> List[str]:
        """
        Trigger callbacks for event
        
        Args:
            event: Callback event
            immediate: Send immediately (skip queue)
            
        Returns:
            List of delivery IDs
        """
        delivery_ids = []
        
        # Find matching endpoints
        matching_endpoints = self._find_matching_endpoints(event)
        
        for endpoint in matching_endpoints:
            # Create delivery
            delivery_id = await self._create_delivery(endpoint, event)
            delivery_ids.append(delivery_id)
            
            if immediate:
                # Send immediately
                await self._deliver_callback(delivery_id)
            else:
                # Queue for delivery
                self.delivery_queue.append(delivery_id)
        
        return delivery_ids
    
    async def trigger_status_change_callback(self,
                                           submission: SubmissionRecord,
                                           old_status: Optional[SubmissionStatus],
                                           new_status: SubmissionStatus) -> List[str]:
        """Trigger status change callback"""
        event = CallbackEvent(
            event_id=str(uuid.uuid4()),
            event_type=CallbackType.STATUS_CHANGE,
            submission_id=submission.submission_id,
            document_id=submission.document_id,
            timestamp=datetime.utcnow(),
            old_status=old_status,
            new_status=new_status,
            user_id=submission.submitted_by,
            organization_id=submission.organization_id,
            data={
                'submission_type': submission.submission_type.value,
                'priority': submission.priority.value,
                'created_at': submission.created_at.isoformat(),
                'updated_at': submission.updated_at.isoformat(),
                'firs_reference': submission.firs_reference,
                'acknowledgment_code': submission.acknowledgment_code
            }
        )
        
        return await self.trigger_callback(event)
    
    def _find_matching_endpoints(self, event: CallbackEvent) -> List[CallbackEndpoint]:
        """Find endpoints that match event criteria"""
        matching = []
        
        for endpoint in self.endpoints.values():
            if not endpoint.is_active:
                continue
            
            # Check callback type
            if event.event_type not in endpoint.callback_types:
                continue
            
            # Check status filters
            if endpoint.status_filters and event.new_status not in endpoint.status_filters:
                continue
            
            # Check organization filters
            if (endpoint.organization_filters and 
                event.organization_id not in endpoint.organization_filters):
                continue
            
            # Check submission filters
            if endpoint.submission_filters:
                if not self._matches_submission_filters(event, endpoint.submission_filters):
                    continue
            
            matching.append(endpoint)
        
        return matching
    
    def _matches_submission_filters(self, event: CallbackEvent, filters: Dict[str, Any]) -> bool:
        """Check if event matches submission filters"""
        # This could be extended with complex filtering logic
        # For now, simple key-value matching
        
        for key, expected_value in filters.items():
            event_value = event.data.get(key)
            
            if isinstance(expected_value, list):
                if event_value not in expected_value:
                    return False
            else:
                if event_value != expected_value:
                    return False
        
        return True
    
    async def _create_delivery(self, endpoint: CallbackEndpoint, event: CallbackEvent) -> str:
        """Create callback delivery"""
        delivery_id = str(uuid.uuid4())
        
        # Prepare payload
        payload = {
            'event_id': event.event_id,
            'event_type': event.event_type.value,
            'submission_id': event.submission_id,
            'document_id': event.document_id,
            'timestamp': event.timestamp.isoformat(),
            'data': event.data
        }
        
        # Add status information for status change events
        if event.event_type == CallbackType.STATUS_CHANGE:
            payload['old_status'] = event.old_status.value if event.old_status else None
            payload['new_status'] = event.new_status.value if event.new_status else None
        
        # Prepare headers
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'TaxPoynt-Callback/1.0',
            'X-Callback-Event-Type': event.event_type.value,
            'X-Callback-Event-ID': event.event_id,
            'X-Callback-Delivery-ID': delivery_id
        }
        
        # Add authentication headers
        auth_headers = self._prepare_auth_headers(endpoint, payload)
        headers.update(auth_headers)
        
        # Create delivery record
        delivery = CallbackDelivery(
            delivery_id=delivery_id,
            endpoint_id=endpoint.endpoint_id,
            callback_type=event.event_type,
            payload=payload,
            headers=headers,
            submission_id=event.submission_id,
            document_id=event.document_id,
            user_id=event.user_id,
            organization_id=event.organization_id
        )
        
        # Store delivery
        self.deliveries[delivery_id] = delivery
        
        # Update metrics
        self.metrics['total_callbacks'] += 1
        self.metrics['callbacks_by_type'][event.event_type.value] += 1
        self.metrics['callbacks_by_endpoint'][endpoint.endpoint_id] += 1
        
        return delivery_id
    
    def _prepare_auth_headers(self, endpoint: CallbackEndpoint, payload: Dict[str, Any]) -> Dict[str, str]:
        """Prepare authentication headers"""
        headers = {}
        
        if endpoint.auth_method == AuthenticationMethod.HMAC_SHA256:
            secret = endpoint.auth_config.get('secret', '')
            payload_str = json.dumps(payload, sort_keys=True)
            signature = hmac.new(
                secret.encode('utf-8'),
                payload_str.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            headers['X-Signature-SHA256'] = f"sha256={signature}"
            
        elif endpoint.auth_method == AuthenticationMethod.BEARER_TOKEN:
            token = endpoint.auth_config.get('token', '')
            headers['Authorization'] = f"Bearer {token}"
            
        elif endpoint.auth_method == AuthenticationMethod.BASIC_AUTH:
            username = endpoint.auth_config.get('username', '')
            password = endpoint.auth_config.get('password', '')
            import base64
            credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
            headers['Authorization'] = f"Basic {credentials}"
            
        elif endpoint.auth_method == AuthenticationMethod.API_KEY:
            api_key = endpoint.auth_config.get('api_key', '')
            key_header = endpoint.auth_config.get('header_name', 'X-API-Key')
            headers[key_header] = api_key
            
        elif endpoint.auth_method == AuthenticationMethod.CUSTOM_HEADER:
            custom_headers = endpoint.auth_config.get('headers', {})
            headers.update(custom_headers)
        
        return headers
    
    async def _process_delivery_queue(self):
        """Process callback delivery queue"""
        while self.running:
            try:
                if self.delivery_queue:
                    # Get delivery ID from queue
                    delivery_id = self.delivery_queue.popleft()
                    
                    # Process delivery with semaphore
                    async with self.delivery_semaphore:
                        await self._deliver_callback(delivery_id)
                else:
                    # No deliveries to process, wait a bit
                    await asyncio.sleep(0.1)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error processing delivery queue: {e}")
                await asyncio.sleep(1)
    
    async def _deliver_callback(self, delivery_id: str):
        """Deliver callback"""
        if delivery_id not in self.deliveries:
            return
        
        delivery = self.deliveries[delivery_id]
        endpoint = self.endpoints.get(delivery.endpoint_id)
        
        if not endpoint or not endpoint.is_active:
            delivery.status = CallbackStatus.CANCELLED
            return
        
        delivery.status = CallbackStatus.SENDING
        delivery.last_attempt_at = datetime.utcnow()
        
        if delivery.retry_count == 0:
            delivery.first_attempt_at = delivery.last_attempt_at
        
        start_time = time.time()
        
        try:
            # Make HTTP request
            async with self.http_session.post(
                endpoint.url,
                json=delivery.payload,
                headers=delivery.headers,
                timeout=aiohttp.ClientTimeout(total=endpoint.timeout)
            ) as response:
                response_time = time.time() - start_time
                
                # Store response information
                delivery.response_status = response.status
                delivery.response_headers = dict(response.headers)
                delivery.response_body = await response.text()
                delivery.response_time = response_time
                
                if 200 <= response.status < 300:
                    # Success
                    delivery.status = CallbackStatus.DELIVERED
                    delivery.delivered_at = datetime.utcnow()
                    
                    # Update endpoint last used
                    endpoint.last_used = datetime.utcnow()
                    
                    # Update metrics
                    self.metrics['delivered_callbacks'] += 1
                    self.metrics['response_times'].append(response_time)
                    self._update_average_response_time(response_time)
                    self._update_endpoint_success_rate(endpoint.endpoint_id, True)
                    
                    logger.info(f"Delivered callback {delivery_id} to {endpoint.url} "
                               f"(status: {response.status}, time: {response_time:.2f}s)")
                    
                else:
                    # HTTP error
                    raise aiohttp.ClientResponseError(
                        request_info=response.request_info,
                        history=response.history,
                        status=response.status,
                        message=f"HTTP {response.status}: {delivery.response_body}"
                    )
                    
        except asyncio.TimeoutError:
            # Timeout
            delivery.error_message = "Request timeout"
            delivery.error_details = {'timeout': endpoint.timeout}
            self.metrics['timeout_failures'] += 1
            await self._handle_delivery_failure(delivery, endpoint)
            
        except aiohttp.ClientError as e:
            # Client error
            delivery.error_message = str(e)
            delivery.error_details = {'error_type': type(e).__name__}
            await self._handle_delivery_failure(delivery, endpoint)
            
        except Exception as e:
            # Other error
            delivery.error_message = f"Unexpected error: {str(e)}"
            delivery.error_details = {'error_type': type(e).__name__}
            await self._handle_delivery_failure(delivery, endpoint)
    
    async def _handle_delivery_failure(self, delivery: CallbackDelivery, endpoint: CallbackEndpoint):
        """Handle callback delivery failure"""
        delivery.retry_count += 1
        
        # Update metrics
        self.metrics['failed_callbacks'] += 1
        self._update_endpoint_success_rate(endpoint.endpoint_id, False)
        
        # Check if we should retry
        if delivery.retry_count < min(endpoint.max_retries, self.max_retry_attempts):
            # Schedule retry
            backoff_seconds = endpoint.retry_backoff * (self.retry_backoff_multiplier ** (delivery.retry_count - 1))
            delivery.next_retry_at = datetime.utcnow() + timedelta(seconds=backoff_seconds)
            delivery.status = CallbackStatus.RETRYING
            
            self.retry_queue.append(delivery.delivery_id)
            self.metrics['retry_callbacks'] += 1
            
            logger.warning(f"Callback {delivery.delivery_id} failed, scheduled for retry in {backoff_seconds}s "
                          f"(attempt {delivery.retry_count}/{endpoint.max_retries})")
        else:
            # Max retries exceeded
            delivery.status = CallbackStatus.FAILED
            
            logger.error(f"Callback {delivery.delivery_id} failed permanently after {delivery.retry_count} attempts")
    
    async def _process_retry_queue(self):
        """Process callback retry queue"""
        while self.running:
            try:
                current_time = datetime.utcnow()
                ready_retries = []
                
                # Find deliveries ready for retry
                temp_queue = deque()
                while self.retry_queue:
                    delivery_id = self.retry_queue.popleft()
                    
                    if delivery_id in self.deliveries:
                        delivery = self.deliveries[delivery_id]
                        
                        if delivery.next_retry_at and delivery.next_retry_at <= current_time:
                            ready_retries.append(delivery_id)
                        else:
                            temp_queue.append(delivery_id)
                
                # Put non-ready deliveries back in queue
                self.retry_queue.extend(temp_queue)
                
                # Process ready retries
                for delivery_id in ready_retries:
                    async with self.delivery_semaphore:
                        await self._deliver_callback(delivery_id)
                
                await asyncio.sleep(10)  # Check every 10 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error processing retry queue: {e}")
                await asyncio.sleep(10)
    
    async def _periodic_cleanup(self):
        """Periodic cleanup of old deliveries"""
        while self.running:
            try:
                await asyncio.sleep(3600)  # Run every hour
                
                current_time = datetime.utcnow()
                cutoff_time = current_time - timedelta(hours=24)
                
                # Remove old completed deliveries
                old_deliveries = []
                for delivery_id, delivery in self.deliveries.items():
                    if (delivery.status in [CallbackStatus.DELIVERED, CallbackStatus.FAILED] and
                        delivery.last_attempt_at and
                        delivery.last_attempt_at < cutoff_time):
                        old_deliveries.append(delivery_id)
                
                for delivery_id in old_deliveries:
                    del self.deliveries[delivery_id]
                
                if old_deliveries:
                    logger.info(f"Cleaned up {len(old_deliveries)} old callback deliveries")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in periodic cleanup: {e}")
    
    def _update_average_response_time(self, response_time: float):
        """Update average response time metric"""
        response_times = list(self.metrics['response_times'])
        if response_times:
            self.metrics['average_response_time'] = sum(response_times) / len(response_times)
    
    def _update_endpoint_success_rate(self, endpoint_id: str, success: bool):
        """Update endpoint success rate"""
        current_rate = self.metrics['endpoint_success_rates'][endpoint_id]
        
        # Simple moving average
        if success:
            self.metrics['endpoint_success_rates'][endpoint_id] = min(100.0, current_rate + 0.5)
        else:
            self.metrics['endpoint_success_rates'][endpoint_id] = max(0.0, current_rate - 0.5)
        
        # Update overall success rate
        total_callbacks = self.metrics['total_callbacks']
        delivered_callbacks = self.metrics['delivered_callbacks']
        self.metrics['success_rate'] = (delivered_callbacks / total_callbacks * 100) if total_callbacks > 0 else 0
    
    def add_event_listener(self, callback_type: CallbackType, listener: Callable):
        """Add event listener for callback type"""
        self.event_listeners[callback_type].append(listener)
    
    def remove_event_listener(self, callback_type: CallbackType, listener: Callable):
        """Remove event listener"""
        if callback_type in self.event_listeners:
            try:
                self.event_listeners[callback_type].remove(listener)
            except ValueError:
                pass
    
    def get_endpoint(self, endpoint_id: str) -> Optional[CallbackEndpoint]:
        """Get callback endpoint by ID"""
        return self.endpoints.get(endpoint_id)
    
    def list_endpoints(self, organization_id: Optional[str] = None) -> List[CallbackEndpoint]:
        """List callback endpoints"""
        endpoints = list(self.endpoints.values())
        
        if organization_id:
            endpoints = [ep for ep in endpoints if ep.organization_id == organization_id]
        
        return endpoints
    
    def get_delivery(self, delivery_id: str) -> Optional[CallbackDelivery]:
        """Get callback delivery by ID"""
        return self.deliveries.get(delivery_id)
    
    def get_deliveries_by_endpoint(self, endpoint_id: str) -> List[CallbackDelivery]:
        """Get deliveries for endpoint"""
        return [delivery for delivery in self.deliveries.values()
                if delivery.endpoint_id == endpoint_id]
    
    def get_deliveries_by_submission(self, submission_id: str) -> List[CallbackDelivery]:
        """Get deliveries for submission"""
        return [delivery for delivery in self.deliveries.values()
                if delivery.submission_id == submission_id]
    
    def get_statistics(self) -> CallbackStats:
        """Get callback statistics"""
        current_time = datetime.utcnow()
        cutoff_time = current_time - timedelta(hours=24)
        
        callbacks_24h = sum(1 for delivery in self.deliveries.values()
                           if delivery.created_at > cutoff_time)
        
        return CallbackStats(
            total_callbacks=self.metrics['total_callbacks'],
            delivered_callbacks=self.metrics['delivered_callbacks'],
            failed_callbacks=self.metrics['failed_callbacks'],
            retry_callbacks=self.metrics['retry_callbacks'],
            success_rate=self.metrics['success_rate'],
            average_response_time=self.metrics['average_response_time'],
            callbacks_by_type=dict(self.metrics['callbacks_by_type']),
            callbacks_by_endpoint=dict(self.metrics['callbacks_by_endpoint']),
            callbacks_last_24h=callbacks_24h
        )
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get callback manager metrics"""
        return {
            **self.metrics,
            'active_endpoints': len([ep for ep in self.endpoints.values() if ep.is_active]),
            'total_endpoints': len(self.endpoints),
            'active_deliveries': len(self.deliveries),
            'delivery_queue_size': len(self.delivery_queue),
            'retry_queue_size': len(self.retry_queue),
            'event_listeners': sum(len(listeners) for listeners in self.event_listeners.values())
        }


# Factory functions for easy setup
def create_callback_manager(max_concurrent_deliveries: int = 50,
                          default_timeout: int = 30) -> CallbackManager:
    """Create callback manager instance"""
    return CallbackManager(
        max_concurrent_deliveries=max_concurrent_deliveries,
        default_timeout=default_timeout
    )


def create_callback_endpoint(url: str,
                           callback_types: Set[CallbackType],
                           auth_method: AuthenticationMethod = AuthenticationMethod.NONE,
                           **kwargs) -> CallbackEndpoint:
    """Create callback endpoint"""
    endpoint_id = str(uuid.uuid4())
    
    return CallbackEndpoint(
        endpoint_id=endpoint_id,
        url=url,
        callback_types=callback_types,
        auth_method=auth_method,
        **kwargs
    )


async def register_status_callback(url: str,
                                 auth_method: AuthenticationMethod = AuthenticationMethod.NONE,
                                 auth_config: Optional[Dict[str, Any]] = None,
                                 manager: Optional[CallbackManager] = None) -> str:
    """Register status change callback"""
    if not manager:
        manager = create_callback_manager()
        await manager.start()
    
    try:
        return manager.register_endpoint(
            url=url,
            callback_types={CallbackType.STATUS_CHANGE},
            auth_method=auth_method,
            auth_config=auth_config
        )
    finally:
        if not manager.running:
            await manager.stop()


async def send_status_callback(submission: SubmissionRecord,
                             old_status: Optional[SubmissionStatus],
                             new_status: SubmissionStatus,
                             manager: Optional[CallbackManager] = None) -> List[str]:
    """Send status change callback"""
    if not manager:
        manager = create_callback_manager()
        await manager.start()
    
    try:
        return await manager.trigger_status_change_callback(submission, old_status, new_status)
    finally:
        if not manager.running:
            await manager.stop()


def get_callback_summary(manager: CallbackManager) -> Dict[str, Any]:
    """Get callback manager summary"""
    metrics = manager.get_metrics()
    stats = manager.get_statistics()
    
    return {
        'total_callbacks': stats.total_callbacks,
        'success_rate': stats.success_rate,
        'delivered_callbacks': stats.delivered_callbacks,
        'failed_callbacks': stats.failed_callbacks,
        'average_response_time': stats.average_response_time,
        'active_endpoints': metrics['active_endpoints'],
        'callbacks_last_24h': stats.callbacks_last_24h,
        'delivery_queue_size': metrics['delivery_queue_size'],
        'retry_queue_size': metrics['retry_queue_size'],
        'callback_type_distribution': dict(stats.callbacks_by_type)
    }