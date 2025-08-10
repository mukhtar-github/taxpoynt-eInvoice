"""
Webhook Framework
================

Standardized webhook handling for financial service integrations.
Provides secure webhook validation, processing, and retry mechanisms.
"""

import logging
import hashlib
import hmac
import json
import asyncio
from typing import Dict, List, Optional, Any, Callable, Union
from datetime import datetime, timedelta
from decimal import Decimal
from dataclasses import dataclass, field
from enum import Enum
import aiohttp
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class WebhookEvent(str, Enum):
    """Standard webhook event types"""
    PAYMENT_SUCCESS = "payment.success"
    PAYMENT_FAILED = "payment.failed"
    PAYMENT_PENDING = "payment.pending"
    TRANSACTION_CREATED = "transaction.created"
    TRANSACTION_UPDATED = "transaction.updated"
    ACCOUNT_UPDATED = "account.updated"
    CUSTOMER_CREATED = "customer.created"
    REFUND_PROCESSED = "refund.processed"
    DISPUTE_CREATED = "dispute.created"
    SETTLEMENT_COMPLETED = "settlement.completed"

class WebhookStatus(str, Enum):
    """Webhook delivery status"""
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"
    ABANDONED = "abandoned"

@dataclass
class WebhookPayload:
    """Standardized webhook payload"""
    
    event: WebhookEvent
    data: Dict[str, Any]
    timestamp: datetime
    webhook_id: str
    source: str
    
    # Signature validation
    signature: Optional[str] = None
    signature_method: str = "sha256"
    
    # Metadata
    version: str = "1.0"
    test_mode: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class WebhookEndpoint:
    """Webhook endpoint configuration"""
    
    url: str
    secret: str
    events: List[WebhookEvent]
    active: bool = True
    
    # Retry configuration
    max_retries: int = 3
    retry_delay_seconds: int = 60
    timeout_seconds: int = 30
    
    # Validation
    verify_ssl: bool = True
    allowed_ips: List[str] = field(default_factory=list)
    
    # Headers
    custom_headers: Dict[str, str] = field(default_factory=dict)

@dataclass
class WebhookDelivery:
    """Webhook delivery attempt record"""
    
    delivery_id: str
    webhook_id: str
    endpoint_url: str
    payload: WebhookPayload
    
    # Delivery status  
    status: WebhookStatus
    attempt_count: int = 0
    max_attempts: int = 3
    
    # Timing
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_attempt_at: Optional[datetime] = None
    next_retry_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    
    # Response details
    response_status_code: Optional[int] = None
    response_body: Optional[str] = None
    error_message: Optional[str] = None

class WebhookValidator:
    """Webhook signature validation"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.WebhookValidator")
    
    def validate_signature(self, 
                         payload: str, 
                         signature: str, 
                         secret: str,
                         method: str = "sha256") -> bool:
        """Validate webhook signature"""
        
        try:
            if method == "sha256":
                expected_signature = self._generate_sha256_signature(payload, secret)
            elif method == "sha1":
                expected_signature = self._generate_sha1_signature(payload, secret)
            else:
                raise ValueError(f"Unsupported signature method: {method}")
            
            # Secure comparison to prevent timing attacks
            return hmac.compare_digest(signature, expected_signature)
            
        except Exception as e:
            self.logger.error(f"Signature validation error: {e}")
            return False
    
    def _generate_sha256_signature(self, payload: str, secret: str) -> str:
        """Generate SHA256 HMAC signature"""
        
        signature = hmac.new(
            secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return f"sha256={signature}"
    
    def _generate_sha1_signature(self, payload: str, secret: str) -> str:
        """Generate SHA1 HMAC signature"""
        
        signature = hmac.new(
            secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha1
        ).hexdigest()
        
        return f"sha1={signature}"
    
    def validate_timestamp(self, 
                         timestamp: Union[str, datetime, int], 
                         tolerance_minutes: int = 5) -> bool:
        """Validate webhook timestamp to prevent replay attacks"""
        
        try:
            # Convert timestamp to datetime
            if isinstance(timestamp, str):
                webhook_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            elif isinstance(timestamp, int):
                webhook_time = datetime.fromtimestamp(timestamp)
            else:
                webhook_time = timestamp
            
            # Check if timestamp is within tolerance
            current_time = datetime.utcnow()
            time_diff = abs((current_time - webhook_time).total_seconds())
            
            return time_diff <= (tolerance_minutes * 60)
            
        except Exception as e:
            self.logger.error(f"Timestamp validation error: {e}")
            return False

class WebhookProcessor:
    """Process incoming webhooks"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.WebhookProcessor")
        self.validator = WebhookValidator()
        self.handlers: Dict[WebhookEvent, List[Callable]] = {}
        self.global_handlers: List[Callable] = []
    
    def register_handler(self, 
                        event: WebhookEvent, 
                        handler: Callable):
        """Register event-specific handler"""
        
        if event not in self.handlers:
            self.handlers[event] = []
        
        self.handlers[event].append(handler)
        self.logger.info(f"Registered handler for {event}")
    
    def register_global_handler(self, handler: Callable):
        """Register handler for all events"""
        
        self.global_handlers.append(handler)
        self.logger.info("Registered global webhook handler")
    
    async def process_webhook(self, 
                            raw_payload: str,
                            headers: Dict[str, str],
                            endpoint_config: WebhookEndpoint) -> Dict[str, Any]:
        """Process incoming webhook"""
        
        try:
            # Validate signature
            signature = headers.get('x-signature', headers.get('signature', ''))
            if not self.validator.validate_signature(raw_payload, signature, endpoint_config.secret):
                raise ValueError("Invalid webhook signature")
            
            # Parse payload
            payload_data = json.loads(raw_payload)
            
            # Create webhook payload object
            webhook_payload = WebhookPayload(
                event=WebhookEvent(payload_data.get('event')),
                data=payload_data.get('data', {}),
                timestamp=datetime.fromisoformat(payload_data.get('timestamp')),
                webhook_id=payload_data.get('webhook_id'),
                source=payload_data.get('source'),
                signature=signature,
                version=payload_data.get('version', '1.0'),
                test_mode=payload_data.get('test_mode', False)
            )
            
            # Validate timestamp
            if not self.validator.validate_timestamp(webhook_payload.timestamp):
                raise ValueError("Webhook timestamp outside tolerance window")
            
            # Process with handlers
            results = await self._execute_handlers(webhook_payload)
            
            return {
                'status': 'success',
                'webhook_id': webhook_payload.webhook_id,
                'processed_at': datetime.utcnow().isoformat(),
                'handler_results': results
            }
            
        except Exception as e:
            self.logger.error(f"Webhook processing error: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'processed_at': datetime.utcnow().isoformat()
            }
    
    async def _execute_handlers(self, payload: WebhookPayload) -> List[Dict[str, Any]]:
        """Execute registered handlers"""
        
        results = []
        
        # Execute event-specific handlers
        event_handlers = self.handlers.get(payload.event, [])
        for handler in event_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    result = await handler(payload)
                else:
                    result = handler(payload)
                
                results.append({
                    'handler': handler.__name__,
                    'status': 'success',
                    'result': result
                })
                
            except Exception as e:
                self.logger.error(f"Handler {handler.__name__} failed: {e}")
                results.append({
                    'handler': handler.__name__,
                    'status': 'error',
                    'error': str(e)
                })
        
        # Execute global handlers
        for handler in self.global_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    result = await handler(payload)
                else:
                    result = handler(payload)
                
                results.append({
                    'handler': f"global_{handler.__name__}",
                    'status': 'success',
                    'result': result
                })
                
            except Exception as e:
                self.logger.error(f"Global handler {handler.__name__} failed: {e}")
                results.append({
                    'handler': f"global_{handler.__name__}",
                    'status': 'error',
                    'error': str(e)
                })
        
        return results

class WebhookDeliveryManager:
    """Manage outgoing webhook deliveries"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.WebhookDeliveryManager")
        self.delivery_queue: List[WebhookDelivery] = []
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def initialize(self):
        """Initialize HTTP session"""
        
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={'User-Agent': 'TaxPoynt-Webhook-Delivery/1.0'}
        )
    
    async def close(self):
        """Close HTTP session"""
        
        if self.session:
            await self.session.close()
    
    async def send_webhook(self, 
                          endpoint: WebhookEndpoint,
                          payload: WebhookPayload) -> WebhookDelivery:
        """Send webhook to endpoint"""
        
        if not self.session:
            await self.initialize()
        
        # Create delivery record
        delivery = WebhookDelivery(
            delivery_id=f"del_{int(datetime.utcnow().timestamp())}_{payload.webhook_id}",
            webhook_id=payload.webhook_id,
            endpoint_url=endpoint.url,
            payload=payload,
            status=WebhookStatus.PENDING,
            max_attempts=endpoint.max_retries
        )
        
        # Attempt delivery
        await self._attempt_delivery(delivery, endpoint)
        
        # Add to queue for retry management
        self.delivery_queue.append(delivery)
        
        return delivery
    
    async def _attempt_delivery(self, 
                               delivery: WebhookDelivery, 
                               endpoint: WebhookEndpoint):
        """Attempt webhook delivery"""
        
        delivery.attempt_count += 1
        delivery.last_attempt_at = datetime.utcnow()
        delivery.status = WebhookStatus.PROCESSING
        
        try:
            # Prepare payload
            payload_json = {
                'event': delivery.payload.event,
                'data': delivery.payload.data,
                'timestamp': delivery.payload.timestamp.isoformat(),
                'webhook_id': delivery.payload.webhook_id,
                'source': delivery.payload.source,
                'version': delivery.payload.version,
                'test_mode': delivery.payload.test_mode
            }
            
            payload_str = json.dumps(payload_json, default=str)
            
            # Generate signature
            signature = self._generate_signature(payload_str, endpoint.secret)
            
            # Prepare headers
            headers = {
                'Content-Type': 'application/json',
                'X-Signature': signature,
                'X-Webhook-ID': delivery.payload.webhook_id,
                'X-Timestamp': delivery.payload.timestamp.isoformat()
            }
            headers.update(endpoint.custom_headers)
            
            # Make HTTP request
            async with self.session.post(
                endpoint.url,
                data=payload_str,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=endpoint.timeout_seconds),
                ssl=endpoint.verify_ssl
            ) as response:
                
                delivery.response_status_code = response.status
                delivery.response_body = await response.text()
                
                if 200 <= response.status < 300:
                    delivery.status = WebhookStatus.SUCCESS
                    delivery.delivered_at = datetime.utcnow()
                    self.logger.info(f"Webhook delivered successfully: {delivery.delivery_id}")
                else:
                    raise aiohttp.ClientResponseError(
                        request_info=response.request_info,
                        history=response.history,
                        status=response.status
                    )
        
        except Exception as e:
            delivery.error_message = str(e)
            
            # Schedule retry if attempts remaining
            if delivery.attempt_count < delivery.max_attempts:
                delivery.status = WebhookStatus.RETRYING
                retry_delay = endpoint.retry_delay_seconds * (2 ** (delivery.attempt_count - 1))  # Exponential backoff
                delivery.next_retry_at = datetime.utcnow() + timedelta(seconds=retry_delay)
                
                self.logger.warning(f"Webhook delivery failed, scheduling retry: {delivery.delivery_id}")
            else:
                delivery.status = WebhookStatus.ABANDONED
                self.logger.error(f"Webhook delivery abandoned after {delivery.attempt_count} attempts: {delivery.delivery_id}")
    
    def _generate_signature(self, payload: str, secret: str) -> str:
        """Generate webhook signature"""
        
        signature = hmac.new(
            secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return f"sha256={signature}"
    
    async def process_retry_queue(self):
        """Process pending webhook retries"""
        
        current_time = datetime.utcnow()
        retries_processed = 0
        
        for delivery in self.delivery_queue:
            if (delivery.status == WebhookStatus.RETRYING and 
                delivery.next_retry_at and 
                current_time >= delivery.next_retry_at):
                
                # Find endpoint configuration (this would come from storage in real implementation)
                endpoint = WebhookEndpoint(
                    url=delivery.endpoint_url,
                    secret="",  # Would be retrieved from storage
                    events=[],
                    max_retries=delivery.max_attempts
                )
                
                await self._attempt_delivery(delivery, endpoint)
                retries_processed += 1
        
        if retries_processed > 0:
            self.logger.info(f"Processed {retries_processed} webhook retries")
    
    def get_delivery_statistics(self) -> Dict[str, Any]:
        """Get webhook delivery statistics"""
        
        if not self.delivery_queue:
            return {'total_deliveries': 0}
        
        total_deliveries = len(self.delivery_queue)
        successful_deliveries = sum(1 for d in self.delivery_queue if d.status == WebhookStatus.SUCCESS)
        failed_deliveries = sum(1 for d in self.delivery_queue if d.status == WebhookStatus.FAILED)
        abandoned_deliveries = sum(1 for d in self.delivery_queue if d.status == WebhookStatus.ABANDONED)
        pending_retries = sum(1 for d in self.delivery_queue if d.status == WebhookStatus.RETRYING)
        
        return {
            'total_deliveries': total_deliveries,
            'successful_deliveries': successful_deliveries,
            'failed_deliveries': failed_deliveries,
            'abandoned_deliveries': abandoned_deliveries,
            'pending_retries': pending_retries,
            'success_rate_percent': round((successful_deliveries / total_deliveries) * 100, 2),
            'average_attempts': round(
                sum(d.attempt_count for d in self.delivery_queue) / total_deliveries, 2
            )
        }

class WebhookFramework:
    """Complete webhook framework"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.WebhookFramework")
        self.processor = WebhookProcessor()
        self.delivery_manager = WebhookDeliveryManager()
        self.endpoints: Dict[str, WebhookEndpoint] = {}
    
    async def initialize(self):
        """Initialize webhook framework"""
        
        await self.delivery_manager.initialize()
        self.logger.info("Webhook framework initialized")
    
    async def close(self):
        """Close webhook framework"""
        
        await self.delivery_manager.close()
        self.logger.info("Webhook framework closed")
    
    def add_endpoint(self, endpoint_id: str, endpoint: WebhookEndpoint):
        """Add webhook endpoint"""
        
        self.endpoints[endpoint_id] = endpoint
        self.logger.info(f"Added webhook endpoint: {endpoint_id} -> {endpoint.url}")
    
    def register_handler(self, event: WebhookEvent, handler: Callable):
        """Register event handler"""
        
        self.processor.register_handler(event, handler)
    
    async def receive_webhook(self, 
                            endpoint_id: str,
                            raw_payload: str,
                            headers: Dict[str, str]) -> Dict[str, Any]:
        """Receive and process incoming webhook"""
        
        if endpoint_id not in self.endpoints:
            raise ValueError(f"Unknown webhook endpoint: {endpoint_id}")
        
        endpoint = self.endpoints[endpoint_id]
        return await self.processor.process_webhook(raw_payload, headers, endpoint)
    
    async def send_webhook(self, 
                          endpoint_id: str,
                          event: WebhookEvent,
                          data: Dict[str, Any],
                          webhook_id: Optional[str] = None) -> WebhookDelivery:
        """Send webhook to endpoint"""
        
        if endpoint_id not in self.endpoints:
            raise ValueError(f"Unknown webhook endpoint: {endpoint_id}")
        
        endpoint = self.endpoints[endpoint_id]
        
        # Check if endpoint is configured for this event
        if event not in endpoint.events:
            raise ValueError(f"Endpoint {endpoint_id} not configured for event {event}")
        
        # Create payload
        payload = WebhookPayload(
            event=event,
            data=data,
            timestamp=datetime.utcnow(),
            webhook_id=webhook_id or f"wh_{int(datetime.utcnow().timestamp())}",
            source="taxpoynt_platform"
        )
        
        return await self.delivery_manager.send_webhook(endpoint, payload)
    
    async def process_retries(self):
        """Process pending webhook retries"""
        
        await self.delivery_manager.process_retry_queue()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive webhook statistics"""
        
        return {
            'framework_info': {
                'total_endpoints': len(self.endpoints),
                'active_endpoints': sum(1 for e in self.endpoints.values() if e.active),
                'total_event_handlers': sum(len(handlers) for handlers in self.processor.handlers.values()),
                'global_handlers': len(self.processor.global_handlers)
            },
            'delivery_statistics': self.delivery_manager.get_delivery_statistics(),
            'endpoint_summary': {
                endpoint_id: {
                    'url': endpoint.url,
                    'active': endpoint.active,
                    'events': [e.value for e in endpoint.events],
                    'max_retries': endpoint.max_retries
                }
                for endpoint_id, endpoint in self.endpoints.items()
            }
        }