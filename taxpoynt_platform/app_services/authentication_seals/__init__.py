"""
Authentication Seals Package for APP Role

This package provides comprehensive authentication seal services including:
- Authentication seal generation
- Cryptographic stamp validation
- Document integrity verification
- Seal repository management
- Document verification services

Usage:
    from taxpoynt_platform.app_services.authentication_seals import (
        SealGenerator, StampValidator, IntegrityChecker, 
        SealRepository, VerificationService
    )
"""

# Seal generation services
from .seal_generator import (
    SealGenerator,
    SealType,
    SealAlgorithm,
    SealStatus,
    SealMetadata,
    AuthenticationSeal,
    SealConfiguration,
    SealGenerationResult,
    create_seal_generator,
    create_seal_configuration,
    generate_document_seal
)

# Stamp validation services
from .stamp_validator import (
    StampValidator,
    ValidationStatus,
    ValidationError,
    ValidationResult,
    CertificateInfo,
    TrustStore,
    create_stamp_validator,
    create_trust_store,
    validate_seal
)

# Integrity checking services
from .integrity_checker import (
    IntegrityChecker,
    IntegrityLevel,
    IntegrityStatus,
    IntegrityViolation,
    IntegrityCheckpoint,
    IntegrityViolationDetail,
    IntegrityReport,
    IntegrityAnalysis,
    create_integrity_checker,
    verify_document_integrity,
    get_integrity_summary
)

# Seal repository services
from .seal_repository import (
    SealRepository,
    StorageBackend,
    SealQueryFilter,
    SealSearchCriteria,
    SealSearchResult,
    SealAuditEvent,
    RepositoryStats,
    create_seal_repository,
    create_search_criteria,
    create_and_start_repository
)

# Verification services
from .verification_service import (
    VerificationService,
    VerificationLevel,
    AuthenticityStatus,
    VerificationMethod,
    VerificationEvidence,
    VerificationResult,
    VerificationContext,
    VerificationPolicy,
    VerificationAudit,
    create_verification_service,
    create_verification_context,
    create_verification_policy,
    verify_document_authenticity,
    get_verification_summary
)

# Package metadata
__version__ = "1.0.0"
__author__ = "TaxPoynt Platform Team"
__description__ = "Authentication Seals Services for APP Role"

# Export all public classes and functions
__all__ = [
    # Seal generation
    "SealGenerator",
    "SealType",
    "SealAlgorithm",
    "SealStatus",
    "SealMetadata",
    "AuthenticationSeal",
    "SealConfiguration",
    "SealGenerationResult",
    "create_seal_generator",
    "create_seal_configuration",
    "generate_document_seal",
    
    # Stamp validation
    "StampValidator",
    "ValidationStatus",
    "ValidationError",
    "ValidationResult",
    "CertificateInfo",
    "TrustStore",
    "create_stamp_validator",
    "create_trust_store",
    "validate_seal",
    
    # Integrity checking
    "IntegrityChecker",
    "IntegrityLevel",
    "IntegrityStatus",
    "IntegrityViolation",
    "IntegrityCheckpoint",
    "IntegrityViolationDetail",
    "IntegrityReport",
    "IntegrityAnalysis",
    "create_integrity_checker",
    "verify_document_integrity",
    "get_integrity_summary",
    
    # Seal repository
    "SealRepository",
    "StorageBackend",
    "SealQueryFilter",
    "SealSearchCriteria",
    "SealSearchResult",
    "SealAuditEvent",
    "RepositoryStats",
    "create_seal_repository",
    "create_search_criteria",
    "create_and_start_repository",
    
    # Verification services
    "VerificationService",
    "VerificationLevel",
    "AuthenticityStatus",
    "VerificationMethod",
    "VerificationEvidence",
    "VerificationResult",
    "VerificationContext",
    "VerificationPolicy",
    "VerificationAudit",
    "create_verification_service",
    "create_verification_context",
    "create_verification_policy",
    "verify_document_authenticity",
    "get_verification_summary",
]


# Convenience factory functions for complete authentication seal suite
async def create_authentication_seal_suite(private_key_path: str = None,
                                          certificate_path: str = None,
                                          hmac_key: bytes = None,
                                          database_path: str = "seal_repository.db",
                                          enable_audit: bool = True):
    """
    Create a complete authentication seal service suite
    
    Args:
        private_key_path: Path to private key file for digital signatures
        certificate_path: Path to certificate file
        hmac_key: HMAC key for cryptographic stamps
        database_path: Path to seal repository database
        enable_audit: Enable audit logging
        
    Returns:
        Tuple of (seal_generator, stamp_validator, integrity_checker, 
                 seal_repository, verification_service)
    """
    # Create seal generator
    seal_generator = create_seal_generator(
        private_key_path=private_key_path,
        certificate_path=certificate_path,
        hmac_key=hmac_key
    )
    
    # Create stamp validator
    stamp_validator = create_stamp_validator(hmac_key=hmac_key)
    
    # Create integrity checker
    integrity_checker = create_integrity_checker(stamp_validator=stamp_validator)
    
    # Create seal repository
    seal_repository = create_seal_repository(
        database_path=database_path,
        enable_audit=enable_audit
    )
    await seal_repository.start()
    
    # Create verification service
    verification_service = create_verification_service(
        stamp_validator=stamp_validator,
        integrity_checker=integrity_checker,
        seal_repository=seal_repository
    )
    
    return (
        seal_generator,
        stamp_validator,
        integrity_checker,
        seal_repository,
        verification_service
    )


async def authenticate_document_complete(document_id: str,
                                       document_data: dict,
                                       verification_level: VerificationLevel = VerificationLevel.STANDARD,
                                       seal_types: List[SealType] = None) -> dict:
    """
    Complete document authentication workflow
    
    Args:
        document_id: Document identifier
        document_data: Document data to authenticate
        verification_level: Level of verification to perform
        seal_types: Types of seals to generate
        
    Returns:
        Dict with authentication results
    """
    # Create authentication suite
    suite = await create_authentication_seal_suite()
    seal_generator, stamp_validator, integrity_checker, seal_repository, verification_service = suite
    
    # Generate seals
    seal_types = seal_types or [SealType.DIGITAL_SIGNATURE, SealType.CRYPTOGRAPHIC_STAMP]
    generated_seals = []
    
    for seal_type in seal_types:
        result = await seal_generator.generate_seal(document_id, document_data, seal_type)
        if result.success:
            generated_seals.append(result.seal)
            await seal_repository.store_seal(result.seal)
    
    # Verify document authenticity
    context = create_verification_context(
        document_id=document_id,
        document_data=document_data,
        verification_level=verification_level
    )
    
    verification_result = await verification_service.verify_document(context)
    
    return {
        'document_id': document_id,
        'seals_generated': len(generated_seals),
        'seal_types': [seal.seal_type.value for seal in generated_seals],
        'verification_result': get_verification_summary(verification_result),
        'is_authentic': verification_result.is_authentic,
        'confidence_score': verification_result.confidence_score,
        'authenticity_status': verification_result.authenticity_status.value
    }


async def validate_document_seals(document_id: str,
                                document_data: dict,
                                seal_repository: SealRepository = None) -> dict:
    """
    Validate all seals for a document
    
    Args:
        document_id: Document identifier
        document_data: Document data
        seal_repository: Seal repository instance
        
    Returns:
        Dict with validation results
    """
    if not seal_repository:
        seal_repository = create_seal_repository()
        await seal_repository.start()
    
    # Get all seals for document
    seals = await seal_repository.get_seals_by_document(document_id)
    
    # Validate each seal
    stamp_validator = create_stamp_validator()
    validation_results = []
    
    for seal in seals:
        result = await stamp_validator.validate_stamp(seal, document_data)
        validation_results.append({
            'seal_id': seal.seal_id,
            'seal_type': seal.seal_type.value,
            'is_valid': result.is_valid,
            'status': result.status.value,
            'errors': [error.value for error in result.errors],
            'warnings': result.warnings
        })
    
    return {
        'document_id': document_id,
        'total_seals': len(seals),
        'valid_seals': len([r for r in validation_results if r['is_valid']]),
        'invalid_seals': len([r for r in validation_results if not r['is_valid']]),
        'validation_results': validation_results
    }


# Service health check
async def check_authentication_seal_services_health(*services):
    """
    Check health of authentication seal services
    
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
class AuthenticationSealConfig:
    """Configuration helper for authentication seal services"""
    
    # Default configurations
    DEFAULT_SEAL_TYPES = [SealType.DIGITAL_SIGNATURE, SealType.CRYPTOGRAPHIC_STAMP]
    DEFAULT_VERIFICATION_LEVEL = VerificationLevel.STANDARD
    DEFAULT_MINIMUM_CONFIDENCE = 85.0
    
    # Production settings
    PRODUCTION_SETTINGS = {
        'seal_types': [SealType.DIGITAL_SIGNATURE, SealType.CRYPTOGRAPHIC_STAMP, SealType.INTEGRITY_SEAL],
        'verification_level': VerificationLevel.COMPREHENSIVE,
        'minimum_confidence': 90.0,
        'enable_audit': True,
        'enable_caching': True,
        'seal_validity_hours': 24
    }
    
    # Development settings
    DEVELOPMENT_SETTINGS = {
        'seal_types': [SealType.DIGITAL_SIGNATURE],
        'verification_level': VerificationLevel.BASIC,
        'minimum_confidence': 70.0,
        'enable_audit': False,
        'enable_caching': True,
        'seal_validity_hours': 168
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
        'name': 'taxpoynt_platform.app_services.authentication_seals',
        'version': __version__,
        'author': __author__,
        'description': __description__,
        'services': [
            'SealGenerator',
            'StampValidator',
            'IntegrityChecker',
            'SealRepository',
            'VerificationService'
        ]
    }