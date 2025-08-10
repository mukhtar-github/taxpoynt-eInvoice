"""
Status Management Package for APP Role

This package provides comprehensive submission status management services including:
- Real-time status tracking and lifecycle management
- FIRS acknowledgment processing and validation
- Error classification and automated resolution
- Multi-channel notification delivery
- Webhook callback management with retry mechanisms

Usage:
    from taxpoynt_platform.app_services.status_management import (
        StatusTracker, AcknowledgmentHandler, ErrorProcessor,
        NotificationService, CallbackManager
    )
"""

# Status Tracking
from .status_tracker import (
    StatusTracker,
    SubmissionStatus,
    SubmissionType,
    Priority,
    StatusTransition,
    SubmissionRecord,
    StatusQuery,
    StatusStatistics,
    create_status_tracker,
    create_status_query,
    track_submission_lifecycle,
    get_status_summary
)

# Acknowledgment Handling
from .acknowledgment_handler import (
    AcknowledgmentHandler,
    AckType,
    AckFormat,
    AckStatus,
    AckValidationRule,
    FIRSAcknowledgment,
    AckProcessingResult,
    AckPattern,
    create_acknowledgment_handler,
    create_ack_validation_rule,
    process_firs_acknowledgment,
    get_acknowledgment_summary
)

# Error Processing
from .error_processor import (
    ErrorProcessor,
    ErrorSeverity,
    ErrorCategory,
    ErrorType,
    ResolutionStrategy,
    ErrorPattern,
    ErrorResolution,
    SubmissionError,
    ErrorAnalysis,
    ErrorReport,
    create_error_processor,
    create_error_pattern,
    process_submission_error,
    get_error_summary
)

# Notification Service
from .notification_service import (
    NotificationService,
    NotificationChannel,
    NotificationType,
    NotificationPriority,
    DeliveryStatus,
    NotificationTemplate,
    NotificationPreference,
    NotificationRecipient,
    NotificationMessage,
    DeliveryResult,
    NotificationStats,
    create_notification_service,
    create_notification_recipient,
    create_notification_preferences,
    send_status_notification,
    get_notification_summary
)

# Callback Management
from .callback_manager import (
    CallbackManager,
    CallbackType,
    CallbackStatus,
    AuthenticationMethod,
    CallbackEndpoint,
    CallbackDelivery,
    CallbackEvent,
    CallbackStats,
    create_callback_manager,
    create_callback_endpoint,
    register_status_callback,
    send_status_callback,
    get_callback_summary
)

# Package metadata
__version__ = "1.0.0"
__author__ = "TaxPoynt Platform Team"
__description__ = "Status Management Services for APP Role"

# Export all public classes and functions
__all__ = [
    # Status Tracking
    "StatusTracker",
    "SubmissionStatus",
    "SubmissionType",
    "Priority",
    "StatusTransition",
    "SubmissionRecord",
    "StatusQuery",
    "StatusStatistics",
    "create_status_tracker",
    "create_status_query",
    "track_submission_lifecycle",
    "get_status_summary",
    
    # Acknowledgment Handling
    "AcknowledgmentHandler",
    "AckType",
    "AckFormat",
    "AckStatus",
    "AckValidationRule",
    "FIRSAcknowledgment",
    "AckProcessingResult",
    "AckPattern",
    "create_acknowledgment_handler",
    "create_ack_validation_rule",
    "process_firs_acknowledgment",
    "get_acknowledgment_summary",
    
    # Error Processing
    "ErrorProcessor",
    "ErrorSeverity",
    "ErrorCategory",
    "ErrorType",
    "ResolutionStrategy",
    "ErrorPattern",
    "ErrorResolution",
    "SubmissionError",
    "ErrorAnalysis",
    "ErrorReport",
    "create_error_processor",
    "create_error_pattern",
    "process_submission_error",
    "get_error_summary",
    
    # Notification Service
    "NotificationService",
    "NotificationChannel",
    "NotificationType",
    "NotificationPriority",
    "DeliveryStatus",
    "NotificationTemplate",
    "NotificationPreference",
    "NotificationRecipient",
    "NotificationMessage",
    "DeliveryResult",
    "NotificationStats",
    "create_notification_service",
    "create_notification_recipient",
    "create_notification_preferences",
    "send_status_notification",
    "get_notification_summary",
    
    # Callback Management
    "CallbackManager",
    "CallbackType",
    "CallbackStatus",
    "AuthenticationMethod",
    "CallbackEndpoint",
    "CallbackDelivery",
    "CallbackEvent",
    "CallbackStats",
    "create_callback_manager",
    "create_callback_endpoint",
    "register_status_callback",
    "send_status_callback",
    "get_callback_summary",
]


# Convenience factory functions for complete status management suite
async def create_status_management_suite(database_path: str = "status_management.db",
                                        smtp_config: Optional[Dict[str, Any]] = None,
                                        enable_callbacks: bool = True,
                                        enable_notifications: bool = True):
    """
    Create a complete status management service suite
    
    Args:
        database_path: Database path for status tracking
        smtp_config: SMTP configuration for notifications
        enable_callbacks: Enable callback management
        enable_notifications: Enable notification service
        
    Returns:
        Tuple of (status_tracker, acknowledgment_handler, error_processor,
                 notification_service, callback_manager)
    """
    # Create status tracker
    status_tracker = create_status_tracker(database_path)
    await status_tracker.start()
    
    # Create acknowledgment handler
    acknowledgment_handler = create_acknowledgment_handler(status_tracker)
    await acknowledgment_handler.start()
    
    # Create error processor
    error_processor = create_error_processor(status_tracker)
    await error_processor.start()
    
    # Create notification service
    notification_service = None
    if enable_notifications:
        notification_service = create_notification_service(smtp_config)
        await notification_service.start()
    
    # Create callback manager
    callback_manager = None
    if enable_callbacks:
        callback_manager = create_callback_manager()
        await callback_manager.start()
    
    return (
        status_tracker,
        acknowledgment_handler,
        error_processor,
        notification_service,
        callback_manager
    )


async def complete_submission_workflow(document_id: str,
                                     submission_type: SubmissionType,
                                     submitted_by: str,
                                     organization_id: str,
                                     notification_recipients: Optional[List[NotificationRecipient]] = None,
                                     callback_endpoints: Optional[List[str]] = None,
                                     suite: Optional[tuple] = None) -> Dict[str, Any]:
    """
    Complete submission workflow with status management
    
    Args:
        document_id: Document identifier
        submission_type: Type of submission
        submitted_by: User submitting
        organization_id: Organization identifier
        notification_recipients: Recipients for notifications
        callback_endpoints: Callback endpoint URLs
        suite: Status management suite (optional)
        
    Returns:
        Dict with workflow results
    """
    if not suite:
        suite = await create_status_management_suite()
    
    status_tracker, ack_handler, error_processor, notification_service, callback_manager = suite
    
    # Create submission
    submission_id = await status_tracker.create_submission(
        document_id=document_id,
        submission_type=submission_type,
        submitted_by=submitted_by,
        organization_id=organization_id
    )
    
    # Register callback endpoints if provided
    registered_callbacks = []
    if callback_manager and callback_endpoints:
        for endpoint_url in callback_endpoints:
            try:
                endpoint_id = callback_manager.register_endpoint(
                    url=endpoint_url,
                    callback_types={CallbackType.STATUS_CHANGE, CallbackType.ERROR_NOTIFICATION},
                    organization_id=organization_id
                )
                registered_callbacks.append(endpoint_id)
            except Exception as e:
                logger.warning(f"Failed to register callback endpoint {endpoint_url}: {e}")
    
    # Setup status change listener for notifications
    if notification_service and notification_recipients:
        async def status_change_listener(submission_id, old_status, new_status):
            try:
                submission = await status_tracker.get_submission(submission_id)
                if submission:
                    await notification_service.send_status_change_notification(
                        submission, old_status, new_status, notification_recipients
                    )
            except Exception as e:
                logger.error(f"Failed to send status notification: {e}")
        
        await status_tracker.add_status_listener(submission_id, status_change_listener)
    
    return {
        'submission_id': submission_id,
        'document_id': document_id,
        'status': SubmissionStatus.PENDING.value,
        'callback_endpoints_registered': len(registered_callbacks),
        'notification_recipients': len(notification_recipients or []),
        'workflow_initialized': True
    }


async def process_submission_lifecycle_event(submission_id: str,
                                           event_type: str,
                                           event_data: Dict[str, Any],
                                           suite: Optional[tuple] = None) -> Dict[str, Any]:
    """
    Process submission lifecycle event
    
    Args:
        submission_id: Submission identifier
        event_type: Type of event (status_change, acknowledgment, error)
        event_data: Event data
        suite: Status management suite
        
    Returns:
        Dict with processing results
    """
    if not suite:
        suite = await create_status_management_suite()
    
    status_tracker, ack_handler, error_processor, notification_service, callback_manager = suite
    
    results = {
        'submission_id': submission_id,
        'event_type': event_type,
        'processed': False,
        'actions_taken': []
    }
    
    try:
        if event_type == 'status_change':
            # Update status
            new_status = SubmissionStatus(event_data['new_status'])
            success = await status_tracker.update_status(
                submission_id=submission_id,
                new_status=new_status,
                reason=event_data.get('reason', 'Status update'),
                metadata=event_data.get('metadata', {})
            )
            
            if success:
                results['processed'] = True
                results['actions_taken'].append('status_updated')
                
                # Trigger callbacks
                if callback_manager:
                    submission = await status_tracker.get_submission(submission_id)
                    if submission:
                        old_status = SubmissionStatus(event_data.get('old_status')) if event_data.get('old_status') else None
                        callback_ids = await callback_manager.trigger_status_change_callback(
                            submission, old_status, new_status
                        )
                        results['actions_taken'].append(f'callbacks_triggered:{len(callback_ids)}')
        
        elif event_type == 'acknowledgment':
            # Process acknowledgment
            ack_result = await ack_handler.process_acknowledgment(
                raw_content=event_data['content'],
                content_type=event_data.get('content_type', 'application/json'),
                headers=event_data.get('headers'),
                source_ip=event_data.get('source_ip')
            )
            
            results['processed'] = ack_result.success
            results['actions_taken'].extend(ack_result.actions_taken)
        
        elif event_type == 'error':
            # Process error
            error = await error_processor.process_error(
                submission_id=submission_id,
                error_message=event_data['error_message'],
                error_code=event_data.get('error_code'),
                error_details=event_data.get('error_details', {}),
                component=event_data.get('component', 'unknown'),
                operation=event_data.get('operation', 'unknown'),
                stage=event_data.get('stage', 'unknown')
            )
            
            results['processed'] = True
            results['actions_taken'].append('error_processed')
            results['error_id'] = error.error_id
            results['error_type'] = error.error_type.value
            results['resolution_strategy'] = error.resolution_strategy.value
        
        return results
        
    except Exception as e:
        results['error'] = str(e)
        logger.error(f"Failed to process lifecycle event for {submission_id}: {e}")
        return results


async def status_management_health_check(*services):
    """
    Check health of status management services
    
    Args:
        *services: Variable number of service instances
        
    Returns:
        Dict with health status of each service
    """
    health_status = {}
    
    for service in services:
        service_name = service.__class__.__name__
        
        try:
            # Check if service has metrics method
            if hasattr(service, 'get_metrics'):
                metrics = service.get_metrics()
                health_status[service_name] = {
                    'status': 'healthy',
                    'metrics': metrics
                }
            else:
                health_status[service_name] = {
                    'status': 'healthy',
                    'message': 'Service is operational'
                }
        except Exception as e:
            health_status[service_name] = {
                'status': 'unhealthy',
                'error': str(e)
            }
    
    return health_status


# Configuration helpers
class StatusManagementConfig:
    """Configuration helper for status management services"""
    
    # Default configurations
    DEFAULT_TIMEOUT = 3600  # 1 hour
    DEFAULT_MAX_RETRIES = 3
    DEFAULT_NOTIFICATION_CHANNELS = [NotificationChannel.EMAIL, NotificationChannel.WEBHOOK]
    DEFAULT_CALLBACK_TYPES = [CallbackType.STATUS_CHANGE, CallbackType.ERROR_NOTIFICATION]
    
    # Production settings
    PRODUCTION_SETTINGS = {
        'status_tracker': {
            'default_timeout': 3600,
            'cleanup_interval': 86400
        },
        'acknowledgment_handler': {
            'validation_enabled': True,
            'signature_verification_enabled': True,
            'retry_interval': 300
        },
        'error_processor': {
            'enable_auto_resolution': True,
            'max_retry_attempts': 3
        },
        'notification_service': {
            'batch_size': 100,
            'retry_interval': 300
        },
        'callback_manager': {
            'max_concurrent_deliveries': 50,
            'default_timeout': 30,
            'max_retry_attempts': 3
        }
    }
    
    # Development settings
    DEVELOPMENT_SETTINGS = {
        'status_tracker': {
            'default_timeout': 7200,
            'cleanup_interval': 3600
        },
        'acknowledgment_handler': {
            'validation_enabled': False,
            'signature_verification_enabled': False,
            'retry_interval': 60
        },
        'error_processor': {
            'enable_auto_resolution': False,
            'max_retry_attempts': 1
        },
        'notification_service': {
            'batch_size': 10,
            'retry_interval': 60
        },
        'callback_manager': {
            'max_concurrent_deliveries': 10,
            'default_timeout': 60,
            'max_retry_attempts': 1
        }
    }
    
    @classmethod
    def get_config(cls, environment: str = "production") -> dict:
        """Get configuration for environment"""
        if environment.lower() == "production":
            return cls.PRODUCTION_SETTINGS.copy()
        else:
            return cls.DEVELOPMENT_SETTINGS.copy()


# Package initialization
def get_package_info():
    """Get package information"""
    return {
        'name': 'taxpoynt_platform.app_services.status_management',
        'version': __version__,
        'author': __author__,
        'description': __description__,
        'services': [
            'StatusTracker',
            'AcknowledgmentHandler',
            'ErrorProcessor',
            'NotificationService',
            'CallbackManager'
        ]
    }