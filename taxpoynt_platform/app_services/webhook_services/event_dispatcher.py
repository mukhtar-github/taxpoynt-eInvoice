"""
APP Service: Event Dispatcher
Dispatches processed webhook events to appropriate client systems
"""

import asyncio
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List, Callable, Awaitable, Union
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import aiohttp
import time
from abc import ABC, abstractmethod

from .webhook_receiver import WebhookPayload, WebhookMetadata, WebhookEventType
from .event_processor import ProcessingResult


class DispatchMethod(str, Enum):
    """Event dispatch methods"""
    WEBHOOK = "webhook"
    MESSAGE_QUEUE = "message_queue"
    DATABASE = "database"
    EMAIL = "email"
    SMS = "sms"
    PUSH_NOTIFICATION = "push_notification"
    WEBSOCKET = "websocket"
    CALLBACK = "callback"


class DispatchStatus(str, Enum):
    """Dispatch status"""
    PENDING = "pending"
    DISPATCHING = "dispatching"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETRY_SCHEDULED = "retry_scheduled"
    DEAD_LETTER = "dead_letter"


class DispatchPriority(str, Enum):
    """Dispatch priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class DispatchTarget:
    """Target configuration for event dispatch"""
    target_id: str
    name: str
    method: DispatchMethod
    endpoint_url: Optional[str] = None
    auth_config: Optional[Dict[str, Any]] = None
    headers: Optional[Dict[str, str]] = None
    timeout_seconds: int = 30
    retry_config: Optional[Dict[str, Any]] = None
    filter_config: Optional[Dict[str, Any]] = None
    enabled: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DispatchJob:
    """Individual dispatch job"""
    job_id: str
    target: DispatchTarget
    event_type: WebhookEventType
    payload: Dict[str, Any]
    metadata: Dict[str, Any]
    priority: DispatchPriority
    created_at: datetime
    scheduled_at: datetime
    status: DispatchStatus
    attempt_count: int = 0
    max_attempts: int = 3
    last_attempted_at: Optional[datetime] = None
    last_error: Optional[str] = None
    delivery_confirmation: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        data['scheduled_at'] = self.scheduled_at.isoformat()
        if self.last_attempted_at:
            data['last_attempted_at'] = self.last_attempted_at.isoformat()
        return data
    
    def __lt__(self, other):
        """For priority queue ordering"""
        priority_order = {
            DispatchPriority.CRITICAL: 0,
            DispatchPriority.HIGH: 1,
            DispatchPriority.NORMAL: 2,
            DispatchPriority.LOW: 3
        }
        
        if priority_order[self.priority] != priority_order[other.priority]:
            return priority_order[self.priority] < priority_order[other.priority]
        
        return self.scheduled_at < other.scheduled_at


class DispatchHandler(ABC):
    """Abstract base class for dispatch handlers"""
    
    @abstractmethod
    async def can_handle(self, method: DispatchMethod) -> bool:
        """Check if this handler can process the dispatch method"""
        pass
    
    @abstractmethod
    async def dispatch(self, job: DispatchJob) -> Dict[str, Any]:
        """Execute the dispatch job"""
        pass
    
    @abstractmethod
    async def verify_delivery(self, job: DispatchJob) -> bool:
        """Verify successful delivery if supported"""
        pass


class WebhookDispatchHandler(DispatchHandler):
    """Handler for webhook dispatching"""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def can_handle(self, method: DispatchMethod) -> bool:
        return method == DispatchMethod.WEBHOOK
    
    async def dispatch(self, job: DispatchJob) -> Dict[str, Any]:
        """Dispatch event via webhook"""
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        target = job.target
        
        try:
            # Prepare request
            headers = target.headers.copy() if target.headers else {}
            headers.setdefault('Content-Type', 'application/json')
            headers.setdefault('User-Agent', 'TaxPoynt-Webhook-Dispatcher/1.0')
            headers.setdefault('X-Event-Type', job.event_type.value)
            headers.setdefault('X-Job-ID', job.job_id)
            headers.setdefault('X-Timestamp', datetime.now(timezone.utc).isoformat())
            
            # Add authentication if configured
            if target.auth_config:
                await self._add_authentication(headers, target.auth_config)
            
            # Prepare payload
            dispatch_payload = {
                'event_type': job.event_type.value,
                'event_id': job.payload.get('event_id'),
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'data': job.payload,
                'metadata': job.metadata
            }
            
            # Send webhook
            async with self.session.post(
                target.endpoint_url,
                json=dispatch_payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=target.timeout_seconds)
            ) as response:
                
                response_data = {
                    'status_code': response.status,
                    'headers': dict(response.headers),
                    'delivered_at': datetime.now(timezone.utc).isoformat()
                }
                
                if response.status < 400:
                    response_data['success'] = True
                    response_data['response_body'] = await response.text()
                    return response_data
                else:
                    response_data['success'] = False
                    response_data['error'] = f"HTTP {response.status}: {response.reason}"
                    response_data['response_body'] = await response.text()
                    return response_data
                    
        except asyncio.TimeoutError:
            return {
                'success': False,
                'error': 'Request timeout',
                'delivered_at': datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'delivered_at': datetime.now(timezone.utc).isoformat()
            }
    
    async def _add_authentication(self, headers: Dict[str, str], auth_config: Dict[str, Any]):
        """Add authentication to request headers"""
        auth_type = auth_config.get('type')
        
        if auth_type == 'bearer':
            token = auth_config.get('token')
            if token:
                headers['Authorization'] = f"Bearer {token}"
        
        elif auth_type == 'api_key':
            key = auth_config.get('key')
            header_name = auth_config.get('header_name', 'X-API-Key')
            if key:
                headers[header_name] = key
        
        elif auth_type == 'hmac':
            # HMAC signature would be calculated here
            # Implementation depends on specific requirements
            pass
    
    async def verify_delivery(self, job: DispatchJob) -> bool:
        """Verify webhook delivery"""
        return job.delivery_confirmation and job.delivery_confirmation.get('success', False)
    
    async def cleanup(self):
        """Cleanup HTTP session"""
        if self.session:
            await self.session.close()


class MessageQueueDispatchHandler(DispatchHandler):
    """Handler for message queue dispatching"""
    
    async def can_handle(self, method: DispatchMethod) -> bool:
        return method == DispatchMethod.MESSAGE_QUEUE
    
    async def dispatch(self, job: DispatchJob) -> Dict[str, Any]:
        """Dispatch event to message queue"""
        # Implementation would depend on specific message queue system
        # (Redis, RabbitMQ, AWS SQS, etc.)
        
        try:
            # Placeholder implementation
            queue_name = job.target.endpoint_url or 'webhook_events'
            
            message = {
                'event_type': job.event_type.value,
                'payload': job.payload,
                'metadata': job.metadata,
                'dispatched_at': datetime.now(timezone.utc).isoformat()
            }
            
            # Simulate message queue dispatch
            await asyncio.sleep(0.1)  # Simulate network delay
            
            return {
                'success': True,
                'queue_name': queue_name,
                'message_id': str(uuid.uuid4()),
                'delivered_at': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'delivered_at': datetime.now(timezone.utc).isoformat()
            }
    
    async def verify_delivery(self, job: DispatchJob) -> bool:
        """Verify message queue delivery"""
        return job.delivery_confirmation and job.delivery_confirmation.get('success', False)


class DatabaseDispatchHandler(DispatchHandler):
    """Handler for database dispatching"""
    
    async def can_handle(self, method: DispatchMethod) -> bool:
        return method == DispatchMethod.DATABASE
    
    async def dispatch(self, job: DispatchJob) -> Dict[str, Any]:
        """Dispatch event to database"""
        try:
            # Implementation would depend on specific database
            # This could insert into event log, notification table, etc.
            
            record = {
                'event_type': job.event_type.value,
                'payload': json.dumps(job.payload),
                'metadata': json.dumps(job.metadata),
                'target_id': job.target.target_id,
                'created_at': datetime.now(timezone.utc)
            }
            
            # Simulate database insert
            await asyncio.sleep(0.05)
            
            return {
                'success': True,
                'record_id': str(uuid.uuid4()),
                'table_name': 'webhook_events',
                'delivered_at': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'delivered_at': datetime.now(timezone.utc).isoformat()
            }
    
    async def verify_delivery(self, job: DispatchJob) -> bool:
        """Verify database delivery"""
        return job.delivery_confirmation and job.delivery_confirmation.get('success', False)


class EmailDispatchHandler(DispatchHandler):
    """Handler for email dispatching"""
    
    async def can_handle(self, method: DispatchMethod) -> bool:
        return method == DispatchMethod.EMAIL
    
    async def dispatch(self, job: DispatchJob) -> Dict[str, Any]:
        """Dispatch event via email"""
        try:
            # Implementation would use email service (SMTP, SendGrid, etc.)
            
            email_data = {
                'to': job.target.endpoint_url,  # Email address
                'subject': f"TaxPoynt Event: {job.event_type.value}",
                'body': self._format_email_body(job),
                'sent_at': datetime.now(timezone.utc).isoformat()
            }
            
            # Simulate email sending
            await asyncio.sleep(0.2)
            
            return {
                'success': True,
                'email_id': str(uuid.uuid4()),
                'recipient': email_data['to'],
                'delivered_at': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'delivered_at': datetime.now(timezone.utc).isoformat()
            }
    
    def _format_email_body(self, job: DispatchJob) -> str:
        """Format email body for event notification"""
        return f"""
TaxPoynt Event Notification

Event Type: {job.event_type.value}
Event ID: {job.payload.get('event_id', 'N/A')}
Timestamp: {datetime.now(timezone.utc).isoformat()}

Event Data:
{json.dumps(job.payload, indent=2)}

This is an automated notification from TaxPoynt eInvoice Platform.
        """.strip()
    
    async def verify_delivery(self, job: DispatchJob) -> bool:
        """Verify email delivery"""
        return job.delivery_confirmation and job.delivery_confirmation.get('success', False)


class EventDispatcher:
    """
    Main event dispatcher that manages dispatch targets and job execution
    Handles multiple dispatch methods and retry mechanisms
    """
    
    def __init__(self, max_concurrent_dispatches: int = 10):
        self.max_concurrent_dispatches = max_concurrent_dispatches
        self.logger = logging.getLogger(__name__)
        
        # Dispatch targets registry
        self.targets: Dict[str, DispatchTarget] = {}
        
        # Dispatch handlers
        self.handlers: List[DispatchHandler] = [
            WebhookDispatchHandler(),
            MessageQueueDispatchHandler(),
            DatabaseDispatchHandler(),
            EmailDispatchHandler()
        ]
        
        # Job queues
        self.pending_jobs: List[DispatchJob] = []
        self.active_jobs: Dict[str, DispatchJob] = {}
        self.completed_jobs: List[DispatchJob] = []
        self.failed_jobs: List[DispatchJob] = []
        
        # Event filters
        self.event_filters: Dict[str, Callable[[WebhookEventType, Dict[str, Any]], bool]] = {}
        
        # Dispatcher state
        self.is_running = False
        self.dispatcher_task: Optional[asyncio.Task] = None
        
        # Statistics
        self.stats = {
            'total_dispatched': 0,
            'successful_dispatches': 0,
            'failed_dispatches': 0,
            'retry_count': 0,
            'dead_letter_count': 0,
            'average_dispatch_time': 0.0,
            'last_dispatch_at': None,
            'method_stats': {},
            'target_stats': {}
        }
        
        # Concurrency control
        self._dispatch_semaphore = asyncio.Semaphore(max_concurrent_dispatches)
    
    def register_target(self, target: DispatchTarget):
        """Register a dispatch target"""
        self.targets[target.target_id] = target
        self.logger.info(f"Registered dispatch target: {target.name} ({target.method.value})")
    
    def unregister_target(self, target_id: str) -> bool:
        """Unregister a dispatch target"""
        if target_id in self.targets:
            target = self.targets.pop(target_id)
            self.logger.info(f"Unregistered dispatch target: {target.name}")
            return True
        return False
    
    def add_event_filter(self, 
                        filter_name: str, 
                        filter_func: Callable[[WebhookEventType, Dict[str, Any]], bool]):
        """Add an event filter function"""
        self.event_filters[filter_name] = filter_func
        self.logger.info(f"Added event filter: {filter_name}")
    
    async def dispatch_event(self, 
                           event_type: WebhookEventType,
                           payload: Dict[str, Any],
                           metadata: Optional[Dict[str, Any]] = None,
                           target_ids: Optional[List[str]] = None,
                           priority: DispatchPriority = DispatchPriority.NORMAL) -> List[str]:
        """
        Dispatch an event to configured targets
        
        Args:
            event_type: Type of webhook event
            payload: Event payload data
            metadata: Additional metadata
            target_ids: Specific target IDs to dispatch to (all if None)
            priority: Dispatch priority
            
        Returns:
            List of job IDs created for the dispatch
        """
        metadata = metadata or {}
        job_ids = []
        
        # Determine target list
        if target_ids:
            targets = [self.targets[tid] for tid in target_ids if tid in self.targets]
        else:
            targets = [t for t in self.targets.values() if t.enabled]
        
        # Create dispatch jobs for each target
        for target in targets:
            # Apply filters
            if not self._should_dispatch_to_target(target, event_type, payload):
                continue
            
            job_id = str(uuid.uuid4())
            scheduled_at = datetime.now(timezone.utc)
            
            # Apply target-specific scheduling delay if configured
            if target.retry_config and 'initial_delay' in target.retry_config:
                delay_seconds = target.retry_config['initial_delay']
                scheduled_at += timedelta(seconds=delay_seconds)
            
            job = DispatchJob(
                job_id=job_id,
                target=target,
                event_type=event_type,
                payload=payload,
                metadata=metadata,
                priority=priority,
                created_at=datetime.now(timezone.utc),
                scheduled_at=scheduled_at,
                status=DispatchStatus.PENDING,
                max_attempts=target.retry_config.get('max_attempts', 3) if target.retry_config else 3
            )
            
            self.pending_jobs.append(job)
            job_ids.append(job_id)
        
        # Sort pending jobs by priority and schedule time
        self.pending_jobs.sort()
        
        self.logger.info(
            f"Scheduled {len(job_ids)} dispatch jobs for event {event_type.value}"
        )
        
        return job_ids
    
    def _should_dispatch_to_target(self, 
                                  target: DispatchTarget, 
                                  event_type: WebhookEventType, 
                                  payload: Dict[str, Any]) -> bool:
        """Check if event should be dispatched to target"""
        # Check target-specific filters
        if target.filter_config:
            event_types = target.filter_config.get('event_types', [])
            if event_types and event_type.value not in event_types:
                return False
            
            # Check payload filters
            payload_filters = target.filter_config.get('payload_filters', {})
            for key, expected_value in payload_filters.items():
                if payload.get(key) != expected_value:
                    return False
        
        # Apply global event filters
        for filter_name, filter_func in self.event_filters.items():
            try:
                if not filter_func(event_type, payload):
                    self.logger.debug(
                        f"Event filtered out by {filter_name} for target {target.target_id}"
                    )
                    return False
            except Exception as e:
                self.logger.error(
                    f"Error in event filter {filter_name}: {str(e)}"
                )
        
        return True
    
    async def start_dispatcher(self):
        """Start the event dispatcher"""
        if self.is_running:
            self.logger.warning("Event dispatcher is already running")
            return
        
        self.is_running = True
        self.dispatcher_task = asyncio.create_task(self._dispatcher_loop())
        self.logger.info("Event dispatcher started")
    
    async def stop_dispatcher(self):
        """Stop the event dispatcher"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        if self.dispatcher_task:
            self.dispatcher_task.cancel()
            try:
                await self.dispatcher_task
            except asyncio.CancelledError:
                pass
        
        # Wait for active jobs to complete
        if self.active_jobs:
            self.logger.info(f"Waiting for {len(self.active_jobs)} active jobs to complete")
            await asyncio.sleep(5)
        
        # Cleanup handlers
        for handler in self.handlers:
            if hasattr(handler, 'cleanup'):
                await handler.cleanup()
        
        self.logger.info("Event dispatcher stopped")
    
    async def _dispatcher_loop(self):
        """Main dispatcher loop"""
        self.logger.info("Event dispatcher loop started")
        
        try:
            while self.is_running:
                await self._process_pending_jobs()
                await asyncio.sleep(1)  # Check every second
                
        except asyncio.CancelledError:
            self.logger.info("Event dispatcher loop cancelled")
        except Exception as e:
            self.logger.error(f"Event dispatcher loop error: {str(e)}")
        finally:
            self.logger.info("Event dispatcher loop ended")
    
    async def _process_pending_jobs(self):
        """Process pending dispatch jobs"""
        current_time = datetime.now(timezone.utc)
        
        # Process jobs that are due (up to max concurrent limit)
        while (len(self.active_jobs) < self.max_concurrent_dispatches and 
               self.pending_jobs and 
               self.pending_jobs[0].scheduled_at <= current_time):
            
            job = self.pending_jobs.pop(0)
            
            # Skip if job target is disabled
            if not job.target.enabled:
                job.status = DispatchStatus.FAILED
                job.last_error = "Target disabled"
                self.failed_jobs.append(job)
                continue
            
            # Execute job
            await self._execute_dispatch_job(job)
    
    async def _execute_dispatch_job(self, job: DispatchJob):
        """Execute a dispatch job"""
        job.status = DispatchStatus.DISPATCHING
        job.last_attempted_at = datetime.now(timezone.utc)
        job.attempt_count += 1
        self.active_jobs[job.job_id] = job
        
        start_time = time.time()
        
        self.logger.info(
            f"Executing dispatch job {job.job_id} to {job.target.name} "
            f"(attempt {job.attempt_count}/{job.max_attempts})"
        )
        
        try:
            # Find appropriate handler
            handler = await self._find_handler(job.target.method)
            if not handler:
                raise ValueError(f"No handler for dispatch method: {job.target.method}")
            
            # Execute dispatch
            async with self._dispatch_semaphore:
                result = await handler.dispatch(job)
            
            # Record result
            job.delivery_confirmation = result
            
            if result.get('success', False):
                job.status = DispatchStatus.DELIVERED
                self.completed_jobs.append(job)
                self._update_stats(job, True, time.time() - start_time)
                
                self.logger.info(f"Dispatch job {job.job_id} completed successfully")
            else:
                await self._handle_dispatch_failure(job, result.get('error', 'Unknown error'))
                
        except Exception as e:
            await self._handle_dispatch_exception(job, str(e))
        
        finally:
            self.active_jobs.pop(job.job_id, None)
    
    async def _find_handler(self, method: DispatchMethod) -> Optional[DispatchHandler]:
        """Find appropriate handler for dispatch method"""
        for handler in self.handlers:
            if await handler.can_handle(method):
                return handler
        return None
    
    async def _handle_dispatch_failure(self, job: DispatchJob, error_message: str):
        """Handle dispatch failure"""
        job.last_error = error_message
        
        if job.attempt_count < job.max_attempts:
            # Schedule retry
            retry_delay = self._calculate_retry_delay(job.attempt_count, job.target.retry_config)
            job.scheduled_at = datetime.now(timezone.utc) + timedelta(seconds=retry_delay)
            job.status = DispatchStatus.RETRY_SCHEDULED
            
            # Re-add to pending queue
            self.pending_jobs.append(job)
            self.pending_jobs.sort()
            
            self.stats['retry_count'] += 1
            
            self.logger.warning(
                f"Dispatch job {job.job_id} failed, scheduling retry in {retry_delay}s: {error_message}"
            )
        else:
            # Move to failed jobs
            job.status = DispatchStatus.DEAD_LETTER
            self.failed_jobs.append(job)
            self.stats['dead_letter_count'] += 1
            
            self.logger.error(
                f"Dispatch job {job.job_id} moved to dead letter after {job.attempt_count} attempts: {error_message}"
            )
        
        self._update_stats(job, False, 0)
    
    async def _handle_dispatch_exception(self, job: DispatchJob, error_message: str):
        """Handle dispatch exception"""
        await self._handle_dispatch_failure(job, f"Exception: {error_message}")
    
    def _calculate_retry_delay(self, attempt_count: int, retry_config: Optional[Dict[str, Any]]) -> int:
        """Calculate retry delay in seconds"""
        if not retry_config:
            return min(60 * (2 ** (attempt_count - 1)), 3600)  # Exponential backoff, max 1 hour
        
        base_delay = retry_config.get('base_delay', 60)
        max_delay = retry_config.get('max_delay', 3600)
        strategy = retry_config.get('strategy', 'exponential')
        
        if strategy == 'fixed':
            return min(base_delay, max_delay)
        elif strategy == 'linear':
            return min(base_delay * attempt_count, max_delay)
        else:  # exponential
            return min(base_delay * (2 ** (attempt_count - 1)), max_delay)
    
    def _update_stats(self, job: DispatchJob, success: bool, dispatch_time: float):
        """Update dispatch statistics"""
        self.stats['total_dispatched'] += 1
        self.stats['last_dispatch_at'] = datetime.now(timezone.utc).isoformat()
        
        if success:
            self.stats['successful_dispatches'] += 1
        else:
            self.stats['failed_dispatches'] += 1
        
        # Update average dispatch time
        if success and dispatch_time > 0:
            current_avg = self.stats['average_dispatch_time']
            total_successful = self.stats['successful_dispatches']
            self.stats['average_dispatch_time'] = (
                (current_avg * (total_successful - 1) + dispatch_time) / total_successful
            )
        
        # Update method statistics
        method_key = job.target.method.value
        if method_key not in self.stats['method_stats']:
            self.stats['method_stats'][method_key] = {
                'total': 0,
                'successful': 0,
                'failed': 0
            }
        
        self.stats['method_stats'][method_key]['total'] += 1
        if success:
            self.stats['method_stats'][method_key]['successful'] += 1
        else:
            self.stats['method_stats'][method_key]['failed'] += 1
        
        # Update target statistics
        target_key = job.target.target_id
        if target_key not in self.stats['target_stats']:
            self.stats['target_stats'][target_key] = {
                'total': 0,
                'successful': 0,
                'failed': 0
            }
        
        self.stats['target_stats'][target_key]['total'] += 1
        if success:
            self.stats['target_stats'][target_key]['successful'] += 1
        else:
            self.stats['target_stats'][target_key]['failed'] += 1
    
    async def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a dispatch job"""
        # Check active jobs
        if job_id in self.active_jobs:
            return self.active_jobs[job_id].to_dict()
        
        # Check pending jobs
        for job in self.pending_jobs:
            if job.job_id == job_id:
                return job.to_dict()
        
        # Check completed jobs
        for job in self.completed_jobs:
            if job.job_id == job_id:
                return job.to_dict()
        
        # Check failed jobs
        for job in self.failed_jobs:
            if job.job_id == job_id:
                return job.to_dict()
        
        return None
    
    async def get_dispatch_status(self) -> Dict[str, Any]:
        """Get dispatcher status and statistics"""
        return {
            'is_running': self.is_running,
            'registered_targets': len(self.targets),
            'active_dispatches': len(self.active_jobs),
            'pending_jobs': len(self.pending_jobs),
            'completed_jobs': len(self.completed_jobs),
            'failed_jobs': len(self.failed_jobs),
            'max_concurrent': self.max_concurrent_dispatches,
            'stats': self.stats.copy(),
            'targets': {
                tid: {
                    'name': target.name,
                    'method': target.method.value,
                    'enabled': target.enabled
                }
                for tid, target in self.targets.items()
            },
            'supported_methods': [method.value for method in DispatchMethod],
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Get event dispatcher health status"""
        pending_count = len(self.pending_jobs)
        active_count = len(self.active_jobs)
        failed_count = len(self.failed_jobs)
        
        success_rate = 0.0
        if self.stats['total_dispatched'] > 0:
            success_rate = (
                self.stats['successful_dispatches'] / self.stats['total_dispatched'] * 100
            )
        
        status = "healthy"
        if not self.is_running:
            status = "stopped"
        elif pending_count > 1000:
            status = "overloaded"
        elif failed_count > pending_count and pending_count > 0:
            status = "degraded"
        elif success_rate < 80 and self.stats['total_dispatched'] > 10:
            status = "degraded"
        
        return {
            'status': status,
            'service': 'event_dispatcher',
            'is_running': self.is_running,
            'pending_jobs': pending_count,
            'active_jobs': active_count,
            'failed_jobs': failed_count,
            'success_rate': round(success_rate, 2),
            'average_dispatch_time': round(self.stats['average_dispatch_time'], 2),
            'registered_targets': len(self.targets),
            'enabled_targets': len([t for t in self.targets.values() if t.enabled]),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
    
    async def cleanup(self):
        """Cleanup dispatcher resources"""
        self.logger.info("Event dispatcher cleanup initiated")
        
        # Stop dispatcher
        await self.stop_dispatcher()
        
        # Log final statistics
        self.logger.info(f"Final dispatch statistics: {self.stats}")
        
        # Clear job queues
        self.pending_jobs.clear()
        self.active_jobs.clear()
        self.completed_jobs.clear()
        self.failed_jobs.clear()
        
        self.logger.info("Event dispatcher cleanup completed")


# Factory functions
def create_event_dispatcher(max_concurrent: int = 10) -> EventDispatcher:
    """Create event dispatcher with standard configuration"""
    return EventDispatcher(max_concurrent_dispatches=max_concurrent)


def create_webhook_target(target_id: str, 
                         name: str, 
                         endpoint_url: str,
                         auth_token: Optional[str] = None) -> DispatchTarget:
    """Create webhook dispatch target with standard configuration"""
    auth_config = None
    if auth_token:
        auth_config = {
            'type': 'bearer',
            'token': auth_token
        }
    
    return DispatchTarget(
        target_id=target_id,
        name=name,
        method=DispatchMethod.WEBHOOK,
        endpoint_url=endpoint_url,
        auth_config=auth_config,
        timeout_seconds=30,
        retry_config={
            'max_attempts': 3,
            'strategy': 'exponential',
            'base_delay': 60,
            'max_delay': 3600
        }
    )