"""
Secure Transmission Services Package for APP Role

This package provides comprehensive document transmission capabilities including:
- Secure document transmission with end-to-end encryption
- Batch processing for multiple documents
- Real-time transmission with WebSocket streaming
- Intelligent retry handling with circuit breaker patterns
- Delivery tracking with full audit trails

Usage:
    from taxpoynt_platform.app_services.transmission import (
        SecureTransmitter, BatchTransmitter, RealTimeTransmitter,
        RetryHandler, DeliveryTracker
    )
"""

# Core transmission services
from .secure_transmitter import (
    SecureTransmitter,
    TransmissionRequest,
    TransmissionResult,
    TransmissionStatus,
    SecurityLevel,
    SecurityContext,
    create_security_context,
    create_transmission_request,
    create_secure_transmitter
)

# Batch transmission services
from .batch_transmitter import (
    BatchTransmitter,
    BatchRequest,
    BatchResult,
    BatchItem,
    BatchItemResult,
    BatchStatus,
    BatchStrategy,
    create_batch_item,
    create_batch_request,
    create_batch_transmitter
)

# Real-time transmission services
from .real_time_transmitter import (
    RealTimeTransmitter,
    RealTimeRequest,
    RealTimeResult,
    RealTimeEvent,
    RealTimeStatus,
    PriorityLevel,
    EventType,
    StreamConnection,
    create_real_time_request,
    create_real_time_transmitter
)

# Retry handling services
from .retry_handler import (
    RetryHandler,
    RetryRequest,
    RetryResult,
    RetryPolicy,
    RetryAttempt,
    RetryStrategy,
    RetryReason,
    CircuitBreaker,
    CircuitState,
    create_retry_policy,
    create_retry_handler
)

# Delivery tracking services
from .delivery_tracker import (
    DeliveryTracker,
    DeliveryTrackingRequest,
    DeliveryRecord,
    DeliveryStatus,
    TrackingEvent,
    TrackingEventType,
    DeliveryAnalytics,
    create_delivery_tracking_request,
    create_delivery_tracker
)

# Package metadata
__version__ = "1.0.0"
__author__ = "TaxPoynt Platform Team"
__description__ = "Secure Transmission Services for APP Role"

# Export all public classes and functions
__all__ = [
    # Core transmission
    "SecureTransmitter",
    "TransmissionRequest",
    "TransmissionResult",
    "TransmissionStatus",
    "SecurityLevel",
    "SecurityContext",
    "create_security_context",
    "create_transmission_request",
    "create_secure_transmitter",
    
    # Batch transmission
    "BatchTransmitter",
    "BatchRequest",
    "BatchResult",
    "BatchItem",
    "BatchItemResult",
    "BatchStatus",
    "BatchStrategy",
    "create_batch_item",
    "create_batch_request",
    "create_batch_transmitter",
    
    # Real-time transmission
    "RealTimeTransmitter",
    "RealTimeRequest",
    "RealTimeResult",
    "RealTimeEvent",
    "RealTimeStatus",
    "PriorityLevel",
    "EventType",
    "StreamConnection",
    "create_real_time_request",
    "create_real_time_transmitter",
    
    # Retry handling
    "RetryHandler",
    "RetryRequest",
    "RetryResult",
    "RetryPolicy",
    "RetryAttempt",
    "RetryStrategy",
    "RetryReason",
    "CircuitBreaker",
    "CircuitState",
    "create_retry_policy",
    "create_retry_handler",
    
    # Delivery tracking
    "DeliveryTracker",
    "DeliveryTrackingRequest",
    "DeliveryRecord",
    "DeliveryStatus",
    "TrackingEvent",
    "TrackingEventType",
    "DeliveryAnalytics",
    "create_delivery_tracking_request",
    "create_delivery_tracker",
]


# Convenience factory functions for complete service setup
async def create_transmission_suite(base_url: str,
                                   security_context: SecurityContext,
                                   websocket_host: str = "localhost",
                                   websocket_port: int = 8765,
                                   database_path: str = "delivery_tracking.db"):
    """
    Create a complete transmission service suite
    
    Args:
        base_url: FIRS API base URL
        security_context: Security context for authentication
        websocket_host: WebSocket server host
        websocket_port: WebSocket server port
        database_path: Database path for delivery tracking
        
    Returns:
        Tuple of (secure_transmitter, batch_transmitter, real_time_transmitter, 
                 retry_handler, delivery_tracker)
    """
    # Create secure transmitter
    secure_transmitter = await create_secure_transmitter(base_url, security_context)
    
    # Create batch transmitter
    batch_transmitter = await create_batch_transmitter(secure_transmitter)
    
    # Create real-time transmitter
    real_time_transmitter = await create_real_time_transmitter(
        secure_transmitter, websocket_host, websocket_port
    )
    
    # Create retry handler
    retry_handler = await create_retry_handler(secure_transmitter)
    
    # Create delivery tracker
    delivery_tracker = await create_delivery_tracker(secure_transmitter, database_path)
    
    return (
        secure_transmitter,
        batch_transmitter,
        real_time_transmitter,
        retry_handler,
        delivery_tracker
    )


async def create_production_transmission_setup(client_id: str,
                                             api_key: str,
                                             encryption_key: bytes,
                                             signing_key: bytes,
                                             certificate_chain: list,
                                             base_url: str = "https://firs-api.gov.ng"):
    """
    Create production-ready transmission setup
    
    Args:
        client_id: FIRS client ID
        api_key: FIRS API key
        encryption_key: Encryption key for documents
        signing_key: Signing key for authentication
        certificate_chain: Certificate chain for TLS
        base_url: FIRS API base URL
        
    Returns:
        Complete transmission service suite
    """
    # Create security context
    security_context = create_security_context(
        client_id=client_id,
        api_key=api_key,
        encryption_key=encryption_key,
        signing_key=signing_key,
        certificate_chain=certificate_chain
    )
    
    # Create transmission suite
    return await create_transmission_suite(
        base_url=base_url,
        security_context=security_context,
        websocket_host="0.0.0.0",
        websocket_port=8765,
        database_path="production_delivery_tracking.db"
    )


# Service health check
async def check_transmission_services_health(*services):
    """
    Check health of transmission services
    
    Args:
        *services: Variable number of transmission service instances
        
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
                    'message': 'Service is running'
                }
        except Exception as e:
            health_status[service_name] = {
                'status': 'unhealthy',
                'error': str(e)
            }
    
    return health_status


# Service cleanup
async def cleanup_transmission_services(*services):
    """
    Cleanup transmission services
    
    Args:
        *services: Variable number of transmission service instances
    """
    for service in services:
        try:
            if hasattr(service, 'stop'):
                await service.stop()
        except Exception as e:
            print(f"Error stopping {service.__class__.__name__}: {e}")


# Configuration helpers
class TransmissionConfig:
    """Configuration helper for transmission services"""
    
    # Default configurations
    DEFAULT_SECURITY_LEVEL = SecurityLevel.STANDARD
    DEFAULT_BATCH_STRATEGY = BatchStrategy.OPTIMIZED
    DEFAULT_RETRY_STRATEGY = RetryStrategy.EXPONENTIAL_BACKOFF
    DEFAULT_PRIORITY_LEVEL = PriorityLevel.NORMAL
    
    # Production settings
    PRODUCTION_SETTINGS = {
        'max_concurrent_transmissions': 20,
        'max_concurrent_batches': 10,
        'max_concurrent_retries': 50,
        'connection_timeout': 30,
        'read_timeout': 60,
        'max_retries': 3,
        'websocket_port': 8765,
        'database_path': 'production_delivery_tracking.db'
    }
    
    # Development settings
    DEVELOPMENT_SETTINGS = {
        'max_concurrent_transmissions': 5,
        'max_concurrent_batches': 3,
        'max_concurrent_retries': 10,
        'connection_timeout': 10,
        'read_timeout': 30,
        'max_retries': 2,
        'websocket_port': 8766,
        'database_path': 'dev_delivery_tracking.db'
    }
    
    @classmethod
    def get_config(cls, environment: str = "production") -> dict:
        """Get configuration for environment"""
        if environment.lower() == "production":
            return cls.PRODUCTION_SETTINGS.copy()
        else:
            return cls.DEVELOPMENT_SETTINGS.copy()


# Error handling helpers
class TransmissionError(Exception):
    """Base exception for transmission errors"""
    pass


class SecurityError(TransmissionError):
    """Security-related transmission error"""
    pass


class BatchError(TransmissionError):
    """Batch processing error"""
    pass


class RetryError(TransmissionError):
    """Retry handling error"""
    pass


class DeliveryError(TransmissionError):
    """Delivery tracking error"""
    pass


# Utility functions
def validate_transmission_request(request: TransmissionRequest) -> bool:
    """Validate transmission request"""
    return (
        bool(request.document_id) and
        bool(request.document_type) and
        bool(request.document_data) and
        bool(request.destination_endpoint)
    )


def validate_batch_request(request: BatchRequest) -> bool:
    """Validate batch request"""
    return (
        bool(request.batch_id) and
        bool(request.batch_name) and
        bool(request.items) and
        len(request.items) > 0
    )


def validate_real_time_request(request: RealTimeRequest) -> bool:
    """Validate real-time request"""
    return (
        bool(request.request_id) and
        bool(request.document_id) and
        bool(request.document_type) and
        bool(request.document_data) and
        bool(request.destination_endpoint)
    )


# Package initialization
def get_package_info():
    """Get package information"""
    return {
        'name': 'taxpoynt_platform.app_services.transmission',
        'version': __version__,
        'author': __author__,
        'description': __description__,
        'services': [
            'SecureTransmitter',
            'BatchTransmitter',
            'RealTimeTransmitter',
            'RetryHandler',
            'DeliveryTracker'
        ]
    }