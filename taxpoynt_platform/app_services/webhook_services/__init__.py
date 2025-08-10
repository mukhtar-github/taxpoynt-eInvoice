"""
TaxPoynt Platform - APP Services: Webhook Services
Comprehensive webhook management system for FIRS integration
"""

from .webhook_receiver import (
    WebhookReceiver,
    WebhookPayload,
    WebhookMetadata,
    WebhookEventType,
    WebhookStatus,
    create_webhook_receiver,
    get_firs_webhook_config
)

from .event_processor import (
    EventProcessor,
    EventHandler,
    ProcessingContext,
    ProcessingResult,
    ProcessingStatus,
    ProcessingPriority,
    SubmissionStatusHandler,
    InvoiceApprovalHandler,
    InvoiceRejectionHandler,
    CertificateExpiryHandler,
    SystemMaintenanceHandler,
    create_event_processor
)

from .signature_validator import (
    SignatureValidator,
    SignatureConfig,
    ValidationContext,
    ValidationReport,
    ValidationResult,
    SignatureAlgorithm,
    HMACValidator,
    RSAValidator,
    JWTValidator,
    create_signature_validator,
    get_firs_signature_configs
)

from .retry_scheduler import (
    RetryScheduler,
    RetryConfig,
    RetryJob,
    RetryStrategy,
    RetryStatus,
    BackoffCalculator,
    FixedDelayCalculator,
    ExponentialBackoffCalculator,
    LinearBackoffCalculator,
    create_retry_scheduler,
    create_retry_config
)

from .event_dispatcher import (
    EventDispatcher,
    DispatchTarget,
    DispatchJob,
    DispatchMethod,
    DispatchStatus,
    DispatchPriority,
    DispatchHandler,
    WebhookDispatchHandler,
    MessageQueueDispatchHandler,
    DatabaseDispatchHandler,
    EmailDispatchHandler,
    create_event_dispatcher,
    create_webhook_target
)

__version__ = "1.0.0"

__all__ = [
    # Webhook Receiver
    "WebhookReceiver",
    "WebhookPayload", 
    "WebhookMetadata",
    "WebhookEventType",
    "WebhookStatus",
    "create_webhook_receiver",
    "get_firs_webhook_config",
    
    # Event Processor
    "EventProcessor",
    "EventHandler",
    "ProcessingContext",
    "ProcessingResult", 
    "ProcessingStatus",
    "ProcessingPriority",
    "SubmissionStatusHandler",
    "InvoiceApprovalHandler",
    "InvoiceRejectionHandler",
    "CertificateExpiryHandler",
    "SystemMaintenanceHandler",
    "create_event_processor",
    
    # Signature Validator
    "SignatureValidator",
    "SignatureConfig",
    "ValidationContext",
    "ValidationReport",
    "ValidationResult", 
    "SignatureAlgorithm",
    "HMACValidator",
    "RSAValidator",
    "JWTValidator",
    "create_signature_validator",
    "get_firs_signature_configs",
    
    # Retry Scheduler
    "RetryScheduler",
    "RetryConfig",
    "RetryJob",
    "RetryStrategy",
    "RetryStatus",
    "BackoffCalculator",
    "FixedDelayCalculator", 
    "ExponentialBackoffCalculator",
    "LinearBackoffCalculator",
    "create_retry_scheduler",
    "create_retry_config",
    
    # Event Dispatcher
    "EventDispatcher",
    "DispatchTarget",
    "DispatchJob",
    "DispatchMethod",
    "DispatchStatus",
    "DispatchPriority",
    "DispatchHandler",
    "WebhookDispatchHandler",
    "MessageQueueDispatchHandler",
    "DatabaseDispatchHandler", 
    "EmailDispatchHandler",
    "create_event_dispatcher",
    "create_webhook_target"
]


class WebhookServiceManager:
    """
    Comprehensive webhook service manager that coordinates all webhook services
    Provides a unified interface for webhook processing workflow
    """
    
    def __init__(self,
                 webhook_secret: str,
                 max_concurrent_processing: int = 10,
                 max_concurrent_retries: int = 5,
                 max_concurrent_dispatches: int = 10):
        """
        Initialize webhook service manager
        
        Args:
            webhook_secret: Secret for webhook signature validation
            max_concurrent_processing: Max concurrent event processing
            max_concurrent_retries: Max concurrent retry processing
            max_concurrent_dispatches: Max concurrent event dispatching
        """
        # Initialize core services
        self.webhook_receiver = create_webhook_receiver(webhook_secret)
        self.signature_validator = create_signature_validator()
        self.event_processor = create_event_processor(max_concurrent_processing)
        self.retry_scheduler = create_retry_scheduler(max_concurrent_retries)
        self.event_dispatcher = create_event_dispatcher(max_concurrent_dispatches)
        
        # Configure signature validation for FIRS
        self._configure_signature_validation(webhook_secret)
        
        # Set up retry processing
        self.retry_scheduler.set_retry_processor(self._process_retry)
        
        # Service state
        self.is_initialized = False
    
    def _configure_signature_validation(self, webhook_secret: str):
        """Configure standard FIRS signature validation"""
        # Configure HMAC SHA256 for standard webhooks
        self.signature_validator.configure(
            name="firs_webhook",
            algorithm=SignatureAlgorithm.HMAC_SHA256,
            secret_key=webhook_secret,
            tolerance_seconds=300,
            require_timestamp=True,
            prevent_replay=True
        )
    
    async def _process_retry(self, payload: WebhookPayload, metadata: WebhookMetadata) -> ProcessingResult:
        """Process webhook retry through event processor"""
        return await self.event_processor.process_event(payload, metadata)
    
    async def start_services(self):
        """Start all webhook services"""
        if self.is_initialized:
            return
        
        # Start schedulers and processors
        await self.event_processor.start_scheduler() if hasattr(self.event_processor, 'start_scheduler') else None
        await self.retry_scheduler.start_scheduler()
        await self.event_dispatcher.start_dispatcher()
        
        self.is_initialized = True
    
    async def stop_services(self):
        """Stop all webhook services"""
        if not self.is_initialized:
            return
        
        # Stop schedulers and processors
        await self.event_processor.stop_scheduler() if hasattr(self.event_processor, 'stop_scheduler') else None
        await self.retry_scheduler.stop_scheduler()
        await self.event_dispatcher.stop_dispatcher()
        
        self.is_initialized = False
    
    async def process_webhook(self, request) -> dict:
        """
        Process incoming webhook through complete workflow
        
        Args:
            request: FastAPI request object
            
        Returns:
            Processing result dictionary
        """
        try:
            # Step 1: Receive and validate webhook
            payload, metadata = await self.webhook_receiver.receive_webhook(request)
            
            # Step 2: Validate signature
            raw_body = await request.body()
            signature = metadata.signature or ""
            
            validation_report = await self.signature_validator.validate_signature(
                config_name="firs_webhook",
                payload=raw_body,
                signature=signature,
                headers=metadata.headers,
                source_ip=metadata.source_ip
            )
            
            if validation_report.result != ValidationResult.VALID:
                return {
                    'status': 'rejected',
                    'reason': 'signature_validation_failed',
                    'details': validation_report.to_dict()
                }
            
            # Step 3: Process event
            processing_result = await self.event_processor.process_event(payload, metadata)
            
            if not processing_result.success:
                # Step 4: Schedule retry if processing failed
                retry_job_id = await self.retry_scheduler.schedule_retry(
                    webhook_payload=payload,
                    webhook_metadata=metadata,
                    failure_reason=processing_result.message
                )
                
                return {
                    'status': 'retry_scheduled',
                    'retry_job_id': retry_job_id,
                    'details': processing_result.to_dict()
                }
            
            # Step 5: Dispatch processed event
            dispatch_job_ids = await self.event_dispatcher.dispatch_event(
                event_type=payload.event_type,
                payload=processing_result.data or payload.data,
                metadata={
                    'webhook_id': metadata.webhook_id,
                    'source_ip': metadata.source_ip,
                    'processing_result': processing_result.to_dict()
                }
            )
            
            return {
                'status': 'processed',
                'processing_result': processing_result.to_dict(),
                'dispatch_jobs': dispatch_job_ids
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    async def register_dispatch_target(self, target: DispatchTarget):
        """Register a new dispatch target"""
        self.event_dispatcher.register_target(target)
    
    async def get_comprehensive_status(self) -> dict:
        """Get comprehensive status of all webhook services"""
        return {
            'webhook_receiver': await self.webhook_receiver.health_check(),
            'signature_validator': await self.signature_validator.health_check(), 
            'event_processor': await self.event_processor.health_check(),
            'retry_scheduler': await self.retry_scheduler.health_check(),
            'event_dispatcher': await self.event_dispatcher.health_check(),
            'service_manager': {
                'is_initialized': self.is_initialized,
                'timestamp': __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat()
            }
        }
    
    async def cleanup(self):
        """Cleanup all webhook services"""
        await self.stop_services()
        
        # Cleanup individual services
        await self.webhook_receiver.cleanup()
        await self.signature_validator.cleanup()
        await self.event_processor.cleanup()
        await self.retry_scheduler.cleanup()
        await self.event_dispatcher.cleanup()


def create_webhook_service_manager(webhook_secret: str, **kwargs) -> WebhookServiceManager:
    """
    Create a complete webhook service manager with all components
    
    Args:
        webhook_secret: Secret for webhook signature validation
        **kwargs: Additional configuration options
        
    Returns:
        Configured WebhookServiceManager instance
    """
    return WebhookServiceManager(webhook_secret, **kwargs)


# Service configuration helpers
def get_default_webhook_config() -> dict:
    """Get default webhook service configuration"""
    return {
        'webhook_secret': None,  # Must be provided
        'max_concurrent_processing': 10,
        'max_concurrent_retries': 5,
        'max_concurrent_dispatches': 10,
        'signature_validation': {
            'algorithm': 'hmac_sha256',
            'tolerance_seconds': 300,
            'require_timestamp': True,
            'prevent_replay': True
        },
        'retry_config': {
            'max_attempts': 5,
            'strategy': 'exponential_backoff',
            'base_delay_seconds': 60,
            'max_delay_seconds': 3600
        },
        'dispatch_config': {
            'timeout_seconds': 30,
            'max_attempts': 3,
            'retry_strategy': 'exponential'
        }
    }


def get_firs_integration_config() -> dict:
    """Get FIRS-specific integration configuration"""
    return {
        'supported_events': [event.value for event in WebhookEventType],
        'signature_algorithms': [alg.value for alg in SignatureAlgorithm],
        'dispatch_methods': [method.value for method in DispatchMethod],
        'webhook_endpoints': {
            'receive': '/webhooks/firs',
            'status': '/webhooks/status',
            'health': '/webhooks/health'
        },
        'security': {
            'signature_header': 'x-firs-signature',
            'timestamp_header': 'x-webhook-timestamp',
            'webhook_id_header': 'x-webhook-id',
            'required_headers': ['content-type', 'user-agent']
        }
    }