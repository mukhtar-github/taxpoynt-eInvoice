"""
Security Compliance Package for APP Role

This package provides comprehensive security and compliance services including:
- TLS 1.3 secure communications management
- Document encryption and key management
- Security audit logging and compliance
- Access control and authorization
- Threat detection and response

Usage:
    from taxpoynt_platform.app_services.security_compliance import (
        TLSManager, EncryptionService, AuditLogger, 
        AccessController, ThreatDetector
    )
"""

# TLS Management
from .tls_manager import (
    TLSManager,
    TLSVersion,
    CipherSuite,
    ConnectionState,
    SecurityLevel,
    TLSConfiguration,
    CertificateInfo,
    TLSConnectionInfo,
    TLSSession,
    SecurityEvent,
    create_tls_manager,
    create_tls_configuration,
    establish_secure_connection,
    make_secure_http_request,
    get_tls_security_summary
)

# Encryption Services
from .encryption_service import (
    EncryptionService,
    EncryptionAlgorithm,
    KeyDerivationMethod,
    EncryptionLevel,
    EncryptionKey,
    EncryptionConfig,
    EncryptedData,
    FieldEncryptionRule,
    EncryptionOperation,
    create_encryption_service,
    create_encryption_config,
    encrypt_document_data,
    decrypt_document_data,
    get_encryption_summary
)

# Audit Logging
from .audit_logger import (
    AuditLogger,
    AuditLevel,
    EventCategory,
    ComplianceStandard,
    LogFormat,
    AuditContext,
    AuditEvent,
    AuditFilter,
    LogIntegrityCheck,
    AuditReport,
    create_audit_logger,
    create_audit_context,
    create_audit_filter,
    log_security_event,
    get_audit_summary
)

# Access Control
from .access_controller import (
    AccessController,
    AccessLevel,
    PermissionType,
    ResourceType,
    SessionStatus,
    AccessDecision,
    Permission,
    Role,
    User,
    Session,
    AccessRequest,
    AccessResult,
    RateLimitRule,
    AccessPattern,
    create_access_controller,
    create_access_request,
    check_user_access,
    get_access_summary
)

# Threat Detection
from .threat_detector import (
    ThreatDetector,
    ThreatLevel,
    ThreatType,
    ThreatStatus,
    ResponseAction,
    ThreatSignature,
    ThreatIndicator,
    SecurityEvent as ThreatSecurityEvent,
    ThreatDetection,
    BehavioralPattern,
    AttackPattern,
    ThreatResponse,
    create_threat_detector,
    create_security_event,
    detect_threats_in_event,
    get_threat_summary
)

# Package metadata
__version__ = "1.0.0"
__author__ = "TaxPoynt Platform Team"
__description__ = "Security Compliance Services for APP Role"

# Export all public classes and functions
__all__ = [
    # TLS Management
    "TLSManager",
    "TLSVersion",
    "CipherSuite",
    "ConnectionState",
    "SecurityLevel",
    "TLSConfiguration",
    "CertificateInfo",
    "TLSConnectionInfo",
    "TLSSession",
    "SecurityEvent",
    "create_tls_manager",
    "create_tls_configuration",
    "establish_secure_connection",
    "make_secure_http_request",
    "get_tls_security_summary",
    
    # Encryption Services
    "EncryptionService",
    "EncryptionAlgorithm",
    "KeyDerivationMethod",
    "EncryptionLevel",
    "EncryptionKey",
    "EncryptionConfig",
    "EncryptedData",
    "FieldEncryptionRule",
    "EncryptionOperation",
    "create_encryption_service",
    "create_encryption_config",
    "encrypt_document_data",
    "decrypt_document_data",
    "get_encryption_summary",
    
    # Audit Logging
    "AuditLogger",
    "AuditLevel",
    "EventCategory",
    "ComplianceStandard",
    "LogFormat",
    "AuditContext",
    "AuditEvent",
    "AuditFilter",
    "LogIntegrityCheck",
    "AuditReport",
    "create_audit_logger",
    "create_audit_context",
    "create_audit_filter",
    "log_security_event",
    "get_audit_summary",
    
    # Access Control
    "AccessController",
    "AccessLevel",
    "PermissionType",
    "ResourceType",
    "SessionStatus",
    "AccessDecision",
    "Permission",
    "Role",
    "User",
    "Session",
    "AccessRequest",
    "AccessResult",
    "RateLimitRule",
    "AccessPattern",
    "create_access_controller",
    "create_access_request",
    "check_user_access",
    "get_access_summary",
    
    # Threat Detection
    "ThreatDetector",
    "ThreatLevel",
    "ThreatType",
    "ThreatStatus",
    "ResponseAction",
    "ThreatSignature",
    "ThreatIndicator",
    "ThreatSecurityEvent",
    "ThreatDetection",
    "BehavioralPattern",
    "AttackPattern",
    "ThreatResponse",
    "create_threat_detector",
    "create_security_event",
    "detect_threats_in_event",
    "get_threat_summary",
]


# Convenience factory functions for complete security compliance suite
async def create_security_compliance_suite(tls_config: Optional[TLSConfiguration] = None,
                                          encryption_config: Optional[EncryptionConfig] = None,
                                          audit_log_directory: str = "audit_logs",
                                          jwt_secret: Optional[str] = None,
                                          detection_window: int = 300):
    """
    Create a complete security compliance service suite
    
    Args:
        tls_config: TLS configuration
        encryption_config: Encryption configuration
        audit_log_directory: Audit log directory
        jwt_secret: JWT secret for access control
        detection_window: Threat detection window
        
    Returns:
        Tuple of (tls_manager, encryption_service, audit_logger, 
                 access_controller, threat_detector)
    """
    # Create TLS manager
    tls_manager = create_tls_manager(tls_config)
    
    # Create encryption service
    encryption_service = create_encryption_service(encryption_config)
    
    # Create audit logger
    audit_logger = create_audit_logger(audit_log_directory)
    await audit_logger.start()
    
    # Create access controller
    access_controller = create_access_controller(jwt_secret)
    
    # Create threat detector
    threat_detector = create_threat_detector(detection_window)
    await threat_detector.start()
    
    return (
        tls_manager,
        encryption_service,
        audit_logger,
        access_controller,
        threat_detector
    )


async def secure_document_processing_workflow(document_id: str,
                                            document_data: dict,
                                            user_id: str,
                                            source_ip: str,
                                            suite: Optional[tuple] = None) -> dict:
    """
    Complete secure document processing workflow
    
    Args:
        document_id: Document identifier
        document_data: Document data to process
        user_id: User performing the operation
        source_ip: Source IP address
        suite: Security compliance suite (optional)
        
    Returns:
        Dict with processing results
    """
    if not suite:
        suite = await create_security_compliance_suite()
    
    tls_manager, encryption_service, audit_logger, access_controller, threat_detector = suite
    
    # Create security event for threat detection
    security_event = create_security_event(
        source_ip=source_ip,
        event_type="document_processing",
        resource="invoice",
        payload={'document_id': document_id, 'operation': 'process'},
        user_id=user_id
    )
    
    # Check for threats
    threats = await threat_detector.process_event(security_event)
    if threats:
        high_threats = [t for t in threats if t.threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]]
        if high_threats:
            await audit_logger.log_security_incident(
                "document_processing_threat",
                "high",
                f"Threats detected during document processing: {len(high_threats)} high/critical threats"
            )
            return {
                'success': False,
                'reason': 'Security threats detected',
                'threats': len(threats)
            }
    
    # Check access permissions
    access_request = create_access_request(
        user_id=user_id,
        resource_type=ResourceType.INVOICE,
        permission_type=PermissionType.CREATE,
        ip_address=source_ip
    )
    
    access_result = await access_controller.check_permission(access_request)
    if not access_result.allowed:
        await audit_logger.log_event(
            level=AuditLevel.WARNING,
            category=EventCategory.AUTHORIZATION,
            event_type="access_denied",
            message=f"Access denied for document processing: {access_result.reason}",
            details={'user_id': user_id, 'document_id': document_id}
        )
        return {
            'success': False,
            'reason': f'Access denied: {access_result.reason}'
        }
    
    try:
        # Encrypt document
        encrypted_data = await encryption_service.encrypt_document(
            document_data,
            document_id
        )
        
        # Log successful processing
        await audit_logger.log_event(
            level=AuditLevel.INFO,
            category=EventCategory.DATA_MODIFICATION,
            event_type="document_processed",
            message=f"Document processed successfully: {document_id}",
            details={
                'user_id': user_id,
                'document_id': document_id,
                'encrypted': True
            },
            compliance_tags=[ComplianceStandard.FIRS, ComplianceStandard.GDPR]
        )
        
        return {
            'success': True,
            'document_id': document_id,
            'encrypted': True,
            'threats_detected': len(threats),
            'access_granted': True
        }
        
    except Exception as e:
        # Log error
        await audit_logger.log_event(
            level=AuditLevel.ERROR,
            category=EventCategory.SYSTEM,
            event_type="document_processing_error",
            message=f"Document processing failed: {str(e)}",
            details={'user_id': user_id, 'document_id': document_id, 'error': str(e)}
        )
        
        return {
            'success': False,
            'reason': f'Processing error: {str(e)}'
        }


async def security_health_check(*services):
    """
    Check health of security compliance services
    
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
class SecurityComplianceConfig:
    """Configuration helper for security compliance services"""
    
    # Default configurations
    DEFAULT_TLS_VERSION = TLSVersion.TLS_1_3
    DEFAULT_ENCRYPTION_ALGORITHM = EncryptionAlgorithm.AES_256_GCM
    DEFAULT_AUDIT_LEVEL = AuditLevel.INFO
    DEFAULT_ACCESS_LEVEL = AccessLevel.STANDARD
    DEFAULT_THREAT_LEVEL = ThreatLevel.MEDIUM
    
    # Production settings
    PRODUCTION_SETTINGS = {
        'tls_version': TLSVersion.TLS_1_3,
        'encryption_algorithm': EncryptionAlgorithm.AES_256_GCM,
        'audit_level': AuditLevel.INFO,
        'access_level': AccessLevel.STANDARD,
        'threat_detection_enabled': True,
        'auto_response_enabled': True,
        'audit_compression': True,
        'session_timeout': 3600,
        'detection_window': 300
    }
    
    # Development settings
    DEVELOPMENT_SETTINGS = {
        'tls_version': TLSVersion.TLS_1_2,
        'encryption_algorithm': EncryptionAlgorithm.AES_256_GCM,
        'audit_level': AuditLevel.DEBUG,
        'access_level': AccessLevel.READ_ONLY,
        'threat_detection_enabled': True,
        'auto_response_enabled': False,
        'audit_compression': False,
        'session_timeout': 7200,
        'detection_window': 600
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
        'name': 'taxpoynt_platform.app_services.security_compliance',
        'version': __version__,
        'author': __author__,
        'description': __description__,
        'services': [
            'TLSManager',
            'EncryptionService',
            'AuditLogger',
            'AccessController',
            'ThreatDetector'
        ]
    }