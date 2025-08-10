"""
APP Service: Event Processor
Processes incoming webhook events and transforms them for internal use
"""

import asyncio
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List, Callable, Type, Union
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
from abc import ABC, abstractmethod

from .webhook_receiver import WebhookPayload, WebhookEventType, WebhookMetadata


class ProcessingStatus(str, Enum):
    """Event processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    DEAD_LETTER = "dead_letter"


class ProcessingPriority(str, Enum):
    """Event processing priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ProcessingContext:
    """Context information for event processing"""
    event_id: str
    processing_id: str
    started_at: datetime
    attempt_count: int
    max_attempts: int
    priority: ProcessingPriority
    timeout_seconds: int
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['started_at'] = self.started_at.isoformat()
        return data


@dataclass
class ProcessingResult:
    """Result of event processing"""
    success: bool
    status: ProcessingStatus
    message: str
    data: Optional[Dict[str, Any]] = None
    error_code: Optional[str] = None
    retry_after: Optional[int] = None  # seconds
    next_actions: Optional[List[str]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class EventHandler(ABC):
    """Abstract base class for event handlers"""
    
    @abstractmethod
    async def can_handle(self, event_type: WebhookEventType, payload: Dict[str, Any]) -> bool:
        """Check if this handler can process the event"""
        pass
    
    @abstractmethod
    async def process(self, 
                     payload: WebhookPayload, 
                     metadata: WebhookMetadata,
                     context: ProcessingContext) -> ProcessingResult:
        """Process the webhook event"""
        pass
    
    @abstractmethod
    def get_priority(self) -> ProcessingPriority:
        """Get processing priority for this handler"""
        pass
    
    @abstractmethod
    def get_timeout(self) -> int:
        """Get timeout in seconds for this handler"""
        pass


class SubmissionStatusHandler(EventHandler):
    """Handler for submission status events"""
    
    async def can_handle(self, event_type: WebhookEventType, payload: Dict[str, Any]) -> bool:
        return event_type == WebhookEventType.SUBMISSION_STATUS
    
    async def process(self, 
                     payload: WebhookPayload, 
                     metadata: WebhookMetadata,
                     context: ProcessingContext) -> ProcessingResult:
        try:
            submission_data = payload.data
            irn = submission_data.get('irn')
            status = submission_data.get('status')
            firs_response = submission_data.get('response')
            
            if not irn or not status:
                return ProcessingResult(
                    success=False,
                    status=ProcessingStatus.FAILED,
                    message="Missing required fields: irn or status",
                    error_code="MISSING_FIELDS"
                )
            
            # Process submission status update
            processed_data = {
                'irn': irn,
                'status': status,
                'firs_response': firs_response,
                'processed_at': datetime.now(timezone.utc).isoformat(),
                'event_id': payload.event_id
            }
            
            return ProcessingResult(
                success=True,
                status=ProcessingStatus.COMPLETED,
                message=f"Submission status updated for IRN: {irn}",
                data=processed_data,
                next_actions=['update_status_tracker', 'notify_client']
            )
            
        except Exception as e:
            return ProcessingResult(
                success=False,
                status=ProcessingStatus.FAILED,
                message=f"Error processing submission status: {str(e)}",
                error_code="PROCESSING_ERROR"
            )
    
    def get_priority(self) -> ProcessingPriority:
        return ProcessingPriority.HIGH
    
    def get_timeout(self) -> int:
        return 30


class InvoiceApprovalHandler(EventHandler):
    """Handler for invoice approval events"""
    
    async def can_handle(self, event_type: WebhookEventType, payload: Dict[str, Any]) -> bool:
        return event_type == WebhookEventType.INVOICE_APPROVED
    
    async def process(self, 
                     payload: WebhookPayload, 
                     metadata: WebhookMetadata,
                     context: ProcessingContext) -> ProcessingResult:
        try:
            approval_data = payload.data
            irn = approval_data.get('irn')
            approval_number = approval_data.get('approval_number')
            approved_at = approval_data.get('approved_at')
            
            if not irn:
                return ProcessingResult(
                    success=False,
                    status=ProcessingStatus.FAILED,
                    message="Missing required field: irn",
                    error_code="MISSING_IRN"
                )
            
            processed_data = {
                'irn': irn,
                'approval_number': approval_number,
                'approved_at': approved_at,
                'processed_at': datetime.now(timezone.utc).isoformat(),
                'event_id': payload.event_id
            }
            
            return ProcessingResult(
                success=True,
                status=ProcessingStatus.COMPLETED,
                message=f"Invoice approved for IRN: {irn}",
                data=processed_data,
                next_actions=['update_invoice_status', 'send_approval_notification']
            )
            
        except Exception as e:
            return ProcessingResult(
                success=False,
                status=ProcessingStatus.FAILED,
                message=f"Error processing invoice approval: {str(e)}",
                error_code="PROCESSING_ERROR"
            )
    
    def get_priority(self) -> ProcessingPriority:
        return ProcessingPriority.HIGH
    
    def get_timeout(self) -> int:
        return 30


class InvoiceRejectionHandler(EventHandler):
    """Handler for invoice rejection events"""
    
    async def can_handle(self, event_type: WebhookEventType, payload: Dict[str, Any]) -> bool:
        return event_type == WebhookEventType.INVOICE_REJECTED
    
    async def process(self, 
                     payload: WebhookPayload, 
                     metadata: WebhookMetadata,
                     context: ProcessingContext) -> ProcessingResult:
        try:
            rejection_data = payload.data
            irn = rejection_data.get('irn')
            rejection_reason = rejection_data.get('rejection_reason')
            error_codes = rejection_data.get('error_codes', [])
            
            if not irn:
                return ProcessingResult(
                    success=False,
                    status=ProcessingStatus.FAILED,
                    message="Missing required field: irn",
                    error_code="MISSING_IRN"
                )
            
            processed_data = {
                'irn': irn,
                'rejection_reason': rejection_reason,
                'error_codes': error_codes,
                'processed_at': datetime.now(timezone.utc).isoformat(),
                'event_id': payload.event_id,
                'retry_recommended': self._should_retry(error_codes)
            }
            
            return ProcessingResult(
                success=True,
                status=ProcessingStatus.COMPLETED,
                message=f"Invoice rejection processed for IRN: {irn}",
                data=processed_data,
                next_actions=['update_invoice_status', 'send_rejection_notification', 'analyze_errors']
            )
            
        except Exception as e:
            return ProcessingResult(
                success=False,
                status=ProcessingStatus.FAILED,
                message=f"Error processing invoice rejection: {str(e)}",
                error_code="PROCESSING_ERROR"
            )
    
    def _should_retry(self, error_codes: List[str]) -> bool:
        """Determine if rejection warrants retry"""
        retryable_codes = [
            'TEMPORARY_ERROR',
            'SYSTEM_UNAVAILABLE',
            'RATE_LIMIT_EXCEEDED'
        ]
        return any(code in retryable_codes for code in error_codes)
    
    def get_priority(self) -> ProcessingPriority:
        return ProcessingPriority.HIGH
    
    def get_timeout(self) -> int:
        return 30


class CertificateExpiryHandler(EventHandler):
    """Handler for certificate expiry events"""
    
    async def can_handle(self, event_type: WebhookEventType, payload: Dict[str, Any]) -> bool:
        return event_type == WebhookEventType.CERTIFICATE_EXPIRY
    
    async def process(self, 
                     payload: WebhookPayload, 
                     metadata: WebhookMetadata,
                     context: ProcessingContext) -> ProcessingResult:
        try:
            cert_data = payload.data
            certificate_id = cert_data.get('certificate_id')
            expires_at = cert_data.get('expires_at')
            days_until_expiry = cert_data.get('days_until_expiry')
            
            if not certificate_id:
                return ProcessingResult(
                    success=False,
                    status=ProcessingStatus.FAILED,
                    message="Missing required field: certificate_id",
                    error_code="MISSING_CERT_ID"
                )
            
            processed_data = {
                'certificate_id': certificate_id,
                'expires_at': expires_at,
                'days_until_expiry': days_until_expiry,
                'urgency_level': self._get_urgency_level(days_until_expiry),
                'processed_at': datetime.now(timezone.utc).isoformat(),
                'event_id': payload.event_id
            }
            
            return ProcessingResult(
                success=True,
                status=ProcessingStatus.COMPLETED,
                message=f"Certificate expiry processed for cert: {certificate_id}",
                data=processed_data,
                next_actions=['send_expiry_notification', 'schedule_renewal_reminder']
            )
            
        except Exception as e:
            return ProcessingResult(
                success=False,
                status=ProcessingStatus.FAILED,
                message=f"Error processing certificate expiry: {str(e)}",
                error_code="PROCESSING_ERROR"
            )
    
    def _get_urgency_level(self, days_until_expiry: Optional[int]) -> str:
        """Determine urgency level based on days until expiry"""
        if not days_until_expiry:
            return "unknown"
        
        if days_until_expiry <= 7:
            return "critical"
        elif days_until_expiry <= 30:
            return "high"
        elif days_until_expiry <= 60:
            return "medium"
        else:
            return "low"
    
    def get_priority(self) -> ProcessingPriority:
        return ProcessingPriority.NORMAL
    
    def get_timeout(self) -> int:
        return 20


class SystemMaintenanceHandler(EventHandler):
    """Handler for system maintenance events"""
    
    async def can_handle(self, event_type: WebhookEventType, payload: Dict[str, Any]) -> bool:
        return event_type == WebhookEventType.SYSTEM_MAINTENANCE
    
    async def process(self, 
                     payload: WebhookPayload, 
                     metadata: WebhookMetadata,
                     context: ProcessingContext) -> ProcessingResult:
        try:
            maintenance_data = payload.data
            maintenance_type = maintenance_data.get('type')
            start_time = maintenance_data.get('start_time')
            end_time = maintenance_data.get('end_time')
            affected_services = maintenance_data.get('affected_services', [])
            
            processed_data = {
                'maintenance_type': maintenance_type,
                'start_time': start_time,
                'end_time': end_time,
                'affected_services': affected_services,
                'impact_level': self._assess_impact(affected_services),
                'processed_at': datetime.now(timezone.utc).isoformat(),
                'event_id': payload.event_id
            }
            
            return ProcessingResult(
                success=True,
                status=ProcessingStatus.COMPLETED,
                message=f"System maintenance notification processed: {maintenance_type}",
                data=processed_data,
                next_actions=['broadcast_maintenance_notice', 'update_service_status']
            )
            
        except Exception as e:
            return ProcessingResult(
                success=False,
                status=ProcessingStatus.FAILED,
                message=f"Error processing system maintenance: {str(e)}",
                error_code="PROCESSING_ERROR"
            )
    
    def _assess_impact(self, affected_services: List[str]) -> str:
        """Assess impact level of maintenance"""
        critical_services = ['submission_api', 'irn_generation', 'authentication']
        
        if any(service in critical_services for service in affected_services):
            return "high"
        elif len(affected_services) > 2:
            return "medium"
        else:
            return "low"
    
    def get_priority(self) -> ProcessingPriority:
        return ProcessingPriority.NORMAL
    
    def get_timeout(self) -> int:
        return 15


class EventProcessor:
    """
    Main event processor that coordinates webhook event processing
    Manages handlers, queuing, retries, and processing results
    """
    
    def __init__(self, max_concurrent_processing: int = 10):
        self.max_concurrent_processing = max_concurrent_processing
        self.logger = logging.getLogger(__name__)
        
        # Event handlers registry
        self.handlers: List[EventHandler] = [
            SubmissionStatusHandler(),
            InvoiceApprovalHandler(),
            InvoiceRejectionHandler(),
            CertificateExpiryHandler(),
            SystemMaintenanceHandler()
        ]
        
        # Processing tracking
        self.active_processing: Dict[str, ProcessingContext] = {}
        self.processing_history: List[Dict[str, Any]] = []
        
        # Processing statistics
        self.stats = {
            'total_processed': 0,
            'successful_processing': 0,
            'failed_processing': 0,
            'retry_count': 0,
            'dead_letter_count': 0,
            'processing_time_avg': 0.0,
            'last_processed_at': None,
            'event_type_stats': {}
        }
        
        # Semaphore for concurrent processing control
        self._processing_semaphore = asyncio.Semaphore(max_concurrent_processing)
    
    async def process_event(self, 
                           payload: WebhookPayload, 
                           metadata: WebhookMetadata,
                           max_attempts: int = 3) -> ProcessingResult:
        """
        Process a webhook event using appropriate handler
        
        Args:
            payload: Webhook payload to process
            metadata: Webhook metadata
            max_attempts: Maximum processing attempts
            
        Returns:
            ProcessingResult with processing outcome
        """
        processing_id = str(uuid.uuid4())
        
        # Find appropriate handler
        handler = await self._find_handler(payload.event_type, payload.data)
        if not handler:
            return ProcessingResult(
                success=False,
                status=ProcessingStatus.FAILED,
                message=f"No handler found for event type: {payload.event_type}",
                error_code="NO_HANDLER"
            )
        
        # Create processing context
        context = ProcessingContext(
            event_id=payload.event_id,
            processing_id=processing_id,
            started_at=datetime.now(timezone.utc),
            attempt_count=payload.retry_count + 1,
            max_attempts=max_attempts,
            priority=handler.get_priority(),
            timeout_seconds=handler.get_timeout(),
            metadata={'source_ip': metadata.source_ip, 'webhook_id': metadata.webhook_id}
        )
        
        # Process with concurrency control
        async with self._processing_semaphore:
            self.active_processing[processing_id] = context
            
            try:
                result = await self._process_with_timeout(handler, payload, metadata, context)
                self._update_stats(payload.event_type, result, context)
                return result
                
            finally:
                self.active_processing.pop(processing_id, None)
    
    async def _find_handler(self, event_type: WebhookEventType, payload_data: Dict[str, Any]) -> Optional[EventHandler]:
        """Find appropriate handler for event type"""
        for handler in self.handlers:
            if await handler.can_handle(event_type, payload_data):
                return handler
        return None
    
    async def _process_with_timeout(self, 
                                   handler: EventHandler,
                                   payload: WebhookPayload,
                                   metadata: WebhookMetadata,
                                   context: ProcessingContext) -> ProcessingResult:
        """Process event with timeout handling"""
        try:
            # Process with timeout
            result = await asyncio.wait_for(
                handler.process(payload, metadata, context),
                timeout=context.timeout_seconds
            )
            
            # Record processing history
            self._record_processing_history(context, result)
            
            return result
            
        except asyncio.TimeoutError:
            self.logger.warning(
                f"Processing timeout for event {context.event_id} "
                f"after {context.timeout_seconds}s"
            )
            return ProcessingResult(
                success=False,
                status=ProcessingStatus.FAILED,
                message=f"Processing timeout after {context.timeout_seconds}s",
                error_code="TIMEOUT",
                retry_after=60
            )
        except Exception as e:
            self.logger.error(f"Unexpected error processing event {context.event_id}: {str(e)}")
            return ProcessingResult(
                success=False,
                status=ProcessingStatus.FAILED,
                message=f"Unexpected processing error: {str(e)}",
                error_code="UNEXPECTED_ERROR",
                retry_after=30
            )
    
    def _record_processing_history(self, context: ProcessingContext, result: ProcessingResult):
        """Record processing history for analytics"""
        processing_time = (datetime.now(timezone.utc) - context.started_at).total_seconds()
        
        history_record = {
            'processing_id': context.processing_id,
            'event_id': context.event_id,
            'attempt_count': context.attempt_count,
            'processing_time': processing_time,
            'success': result.success,
            'status': result.status.value,
            'error_code': result.error_code,
            'priority': context.priority.value,
            'completed_at': datetime.now(timezone.utc).isoformat()
        }
        
        self.processing_history.append(history_record)
        
        # Keep only last 1000 records
        if len(self.processing_history) > 1000:
            self.processing_history = self.processing_history[-1000:]
    
    def _update_stats(self, event_type: WebhookEventType, result: ProcessingResult, context: ProcessingContext):
        """Update processing statistics"""
        self.stats['total_processed'] += 1
        self.stats['last_processed_at'] = datetime.now(timezone.utc).isoformat()
        
        if result.success:
            self.stats['successful_processing'] += 1
        else:
            self.stats['failed_processing'] += 1
            
            if result.status == ProcessingStatus.DEAD_LETTER:
                self.stats['dead_letter_count'] += 1
            elif context.attempt_count > 1:
                self.stats['retry_count'] += 1
        
        # Update event type statistics
        event_key = event_type.value
        if event_key not in self.stats['event_type_stats']:
            self.stats['event_type_stats'][event_key] = {
                'total': 0,
                'successful': 0,
                'failed': 0
            }
        
        self.stats['event_type_stats'][event_key]['total'] += 1
        if result.success:
            self.stats['event_type_stats'][event_key]['successful'] += 1
        else:
            self.stats['event_type_stats'][event_key]['failed'] += 1
        
        # Update average processing time
        processing_time = (datetime.now(timezone.utc) - context.started_at).total_seconds()
        current_avg = self.stats['processing_time_avg']
        total_processed = self.stats['total_processed']
        self.stats['processing_time_avg'] = (
            (current_avg * (total_processed - 1) + processing_time) / total_processed
        )
    
    def register_handler(self, handler: EventHandler):
        """Register a new event handler"""
        self.handlers.append(handler)
        self.logger.info(f"Registered new event handler: {handler.__class__.__name__}")
    
    def unregister_handler(self, handler_class: Type[EventHandler]):
        """Unregister an event handler"""
        self.handlers = [h for h in self.handlers if not isinstance(h, handler_class)]
        self.logger.info(f"Unregistered event handler: {handler_class.__name__}")
    
    async def get_processing_status(self) -> Dict[str, Any]:
        """Get current processing status and statistics"""
        return {
            'active_processing_count': len(self.active_processing),
            'max_concurrent_processing': self.max_concurrent_processing,
            'registered_handlers': len(self.handlers),
            'stats': self.stats.copy(),
            'active_events': [
                {
                    'processing_id': context.processing_id,
                    'event_id': context.event_id,
                    'started_at': context.started_at.isoformat(),
                    'attempt_count': context.attempt_count,
                    'priority': context.priority.value
                }
                for context in self.active_processing.values()
            ],
            'handler_info': [
                {
                    'class_name': handler.__class__.__name__,
                    'priority': handler.get_priority().value,
                    'timeout': handler.get_timeout()
                }
                for handler in self.handlers
            ]
        }
    
    async def get_processing_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent processing history"""
        return self.processing_history[-limit:]
    
    async def health_check(self) -> Dict[str, Any]:
        """Get event processor health status"""
        active_count = len(self.active_processing)
        success_rate = 0.0
        
        if self.stats['total_processed'] > 0:
            success_rate = (
                self.stats['successful_processing'] / self.stats['total_processed'] * 100
            )
        
        status = "healthy"
        if active_count >= self.max_concurrent_processing:
            status = "overloaded"
        elif success_rate < 80 and self.stats['total_processed'] > 10:
            status = "degraded"
        
        return {
            'status': status,
            'service': 'event_processor',
            'active_processing': active_count,
            'max_concurrent': self.max_concurrent_processing,
            'success_rate': round(success_rate, 2),
            'average_processing_time': round(self.stats['processing_time_avg'], 2),
            'registered_handlers': len(self.handlers),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
    
    async def cleanup(self):
        """Cleanup resources and save processing history"""
        self.logger.info("Event processor cleanup initiated")
        
        # Wait for active processing to complete (with timeout)
        if self.active_processing:
            self.logger.info(f"Waiting for {len(self.active_processing)} active processes to complete")
            await asyncio.sleep(5)  # Give some time for completion
        
        # Log final statistics
        self.logger.info(f"Final processing statistics: {self.stats}")
        
        self.logger.info("Event processor cleanup completed")


# Factory function for creating event processor
def create_event_processor(max_concurrent: int = 10) -> EventProcessor:
    """Create event processor with standard configuration"""
    return EventProcessor(max_concurrent_processing=max_concurrent)