"""
Pre-Submission Validation Services Package for APP Role

This package provides comprehensive validation services including:
- FIRS-specific validation rules
- Pre-submission checks
- Document format validation
- Data completeness verification
- Validation error handling

Usage:
    from taxpoynt_platform.app_services.validation import (
        FIRSValidator, SubmissionValidator, FormatValidator,
        CompletenessChecker, ValidationErrorHandler
    )
"""

# FIRS validation services
from .firs_validator import (
    FIRSValidator,
    FIRSValidationReport,
    ValidationResult,
    ValidationSeverity,
    DocumentType,
    TaxType,
    create_firs_validator,
    validate_document_for_firs
)

# Submission validation services
from .submission_validator import (
    SubmissionValidator,
    SubmissionValidationReport,
    SubmissionCheck,
    SubmissionContext,
    SubmissionReadiness,
    CheckCategory,
    CheckStatus,
    create_submission_validator,
    create_submission_context,
    validate_document_submission
)

# Format validation services
from .format_validator import (
    FormatValidator,
    FormatValidationReport,
    FormatValidationResult,
    FormatType,
    FieldType,
    FormatSeverity,
    create_format_validator,
    validate_document_format,
    validate_xml_document
)

# Completeness checking services
from .completeness_checker import (
    CompletenessChecker,
    CompletenessReport,
    CompletenessResult,
    CompletenessRule,
    CompletenessLevel,
    CompletionStatus,
    CompletionSeverity,
    create_completeness_checker,
    check_document_completeness,
    get_completeness_summary
)

# Error handling services
from .error_handler import (
    ValidationErrorHandler,
    ErrorHandlingReport,
    ValidationError,
    ErrorGroup,
    ErrorAnalysis,
    ErrorCategory,
    ErrorPattern,
    ErrorResolution,
    create_error_handler,
    handle_validation_errors,
    get_error_summary
)

# Package metadata
__version__ = "1.0.0"
__author__ = "TaxPoynt Platform Team"
__description__ = "Pre-Submission Validation Services for APP Role"

# Export all public classes and functions
__all__ = [
    # FIRS validation
    "FIRSValidator",
    "FIRSValidationReport",
    "ValidationResult",
    "ValidationSeverity",
    "DocumentType",
    "TaxType",
    "create_firs_validator",
    "validate_document_for_firs",
    
    # Submission validation
    "SubmissionValidator",
    "SubmissionValidationReport",
    "SubmissionCheck",
    "SubmissionContext",
    "SubmissionReadiness",
    "CheckCategory",
    "CheckStatus",
    "create_submission_validator",
    "create_submission_context",
    "validate_document_submission",
    
    # Format validation
    "FormatValidator",
    "FormatValidationReport",
    "FormatValidationResult",
    "FormatType",
    "FieldType",
    "FormatSeverity",
    "create_format_validator",
    "validate_document_format",
    "validate_xml_document",
    
    # Completeness checking
    "CompletenessChecker",
    "CompletenessReport",
    "CompletenessResult",
    "CompletenessRule",
    "CompletenessLevel",
    "CompletionStatus",
    "CompletionSeverity",
    "create_completeness_checker",
    "check_document_completeness",
    "get_completeness_summary",
    
    # Error handling
    "ValidationErrorHandler",
    "ErrorHandlingReport",
    "ValidationError",
    "ErrorGroup",
    "ErrorAnalysis",
    "ErrorCategory",
    "ErrorPattern",
    "ErrorResolution",
    "create_error_handler",
    "handle_validation_errors",
    "get_error_summary",
]


# Convenience factory functions for complete validation suite
async def create_validation_suite(completeness_level: CompletenessLevel = CompletenessLevel.STANDARD,
                                 schema_version: str = "1.0",
                                 enable_error_analytics: bool = True):
    """
    Create a complete validation service suite
    
    Args:
        completeness_level: Level of completeness checking
        schema_version: Schema version for format validation
        enable_error_analytics: Enable error analytics
        
    Returns:
        Tuple of (firs_validator, submission_validator, format_validator, 
                 completeness_checker, error_handler)
    """
    # Create validators
    firs_validator = create_firs_validator()
    submission_validator = create_submission_validator(firs_validator)
    format_validator = create_format_validator(schema_version)
    completeness_checker = create_completeness_checker(completeness_level)
    error_handler = create_error_handler(enable_error_analytics)
    
    return (
        firs_validator,
        submission_validator,
        format_validator,
        completeness_checker,
        error_handler
    )


async def validate_document_comprehensive(document: dict,
                                        submission_endpoint: str,
                                        completeness_level: CompletenessLevel = CompletenessLevel.STANDARD,
                                        **kwargs) -> ErrorHandlingReport:
    """
    Perform comprehensive document validation
    
    Args:
        document: Document data to validate
        submission_endpoint: Submission endpoint for validation
        completeness_level: Level of completeness checking
        **kwargs: Additional arguments for submission context
        
    Returns:
        ErrorHandlingReport with comprehensive validation results
    """
    # Create validation suite
    validators = await create_validation_suite(completeness_level)
    firs_validator, submission_validator, format_validator, completeness_checker, error_handler = validators
    
    # Run all validations
    firs_report = await firs_validator.validate_document(document)
    
    submission_context = create_submission_context(document, submission_endpoint, **kwargs)
    submission_report = await submission_validator.validate_submission(submission_context)
    
    format_report = await format_validator.validate_document_format(document)
    
    completeness_report = await completeness_checker.check_completeness(document)
    
    # Handle all errors
    error_report = await error_handler.handle_validation_errors(
        document.get('document_id', 'unknown'),
        firs_report,
        submission_report,
        format_report,
        completeness_report
    )
    
    return error_report


async def validate_document_quick(document: dict) -> dict:
    """
    Quick document validation with basic checks
    
    Args:
        document: Document data to validate
        
    Returns:
        Dict with validation summary
    """
    # Create basic validators
    firs_validator = create_firs_validator()
    format_validator = create_format_validator()
    
    # Run basic validations
    firs_report = await firs_validator.validate_document(document)
    format_report = await format_validator.validate_document_format(document)
    
    return {
        'document_id': document.get('document_id', 'unknown'),
        'is_valid': firs_report.is_valid and format_report.is_valid,
        'firs_compliance': firs_report.is_valid,
        'format_compliance': format_report.is_valid,
        'total_errors': len(firs_report.errors) + len(format_report.errors),
        'firs_errors': len(firs_report.errors),
        'format_errors': len(format_report.errors),
        'warnings': len(firs_report.warnings) + len(format_report.warnings)
    }


# Service health check
async def check_validation_services_health(*services):
    """
    Check health of validation services
    
    Args:
        *services: Variable number of validation service instances
        
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
class ValidationConfig:
    """Configuration helper for validation services"""
    
    # Default configurations
    DEFAULT_COMPLETENESS_LEVEL = CompletenessLevel.STANDARD
    DEFAULT_SCHEMA_VERSION = "1.0"
    DEFAULT_ENABLE_ANALYTICS = True
    
    # Production settings
    PRODUCTION_SETTINGS = {
        'completeness_level': CompletenessLevel.COMPREHENSIVE,
        'schema_version': '1.0',
        'enable_analytics': True,
        'enable_caching': True,
        'validation_timeout': 30
    }
    
    # Development settings
    DEVELOPMENT_SETTINGS = {
        'completeness_level': CompletenessLevel.BASIC,
        'schema_version': '1.0',
        'enable_analytics': False,
        'enable_caching': False,
        'validation_timeout': 60
    }
    
    @classmethod
    def get_config(cls, environment: str = "production") -> dict:
        """Get configuration for environment"""
        if environment.lower() == "production":
            return cls.PRODUCTION_SETTINGS.copy()
        else:
            return cls.DEVELOPMENT_SETTINGS.copy()


# Error handling helpers
class ValidationException(Exception):
    """Base exception for validation errors"""
    pass


class FIRSValidationException(ValidationException):
    """FIRS validation specific exception"""
    pass


class SubmissionValidationException(ValidationException):
    """Submission validation specific exception"""
    pass


class FormatValidationException(ValidationException):
    """Format validation specific exception"""
    pass


class CompletenessValidationException(ValidationException):
    """Completeness validation specific exception"""
    pass


# Utility functions
def validate_document_structure(document: dict) -> bool:
    """Basic document structure validation"""
    required_fields = ['document_id', 'document_type']
    return all(field in document for field in required_fields)


def get_validation_summary(error_report: ErrorHandlingReport) -> dict:
    """Get validation summary from error report"""
    return {
        'document_id': error_report.document_id,
        'total_errors': error_report.total_errors,
        'resolved_errors': error_report.resolved_errors,
        'unresolved_errors': error_report.unresolved_errors,
        'is_valid': error_report.unresolved_errors == 0,
        'error_groups': len(error_report.error_groups),
        'estimated_fix_time': error_report.error_analysis.estimated_total_fix_time,
        'user_summary': error_report.user_friendly_summary
    }


def merge_validation_reports(*reports) -> dict:
    """Merge multiple validation reports"""
    merged = {
        'total_errors': 0,
        'total_warnings': 0,
        'is_valid': True,
        'reports': []
    }
    
    for report in reports:
        if hasattr(report, 'errors'):
            merged['total_errors'] += len(report.errors)
            merged['is_valid'] = merged['is_valid'] and report.is_valid
        
        if hasattr(report, 'warnings'):
            merged['total_warnings'] += len(report.warnings)
        
        merged['reports'].append({
            'type': report.__class__.__name__,
            'valid': getattr(report, 'is_valid', True),
            'errors': len(getattr(report, 'errors', [])),
            'warnings': len(getattr(report, 'warnings', []))
        })
    
    return merged


# Package initialization
def get_package_info():
    """Get package information"""
    return {
        'name': 'taxpoynt_platform.app_services.validation',
        'version': __version__,
        'author': __author__,
        'description': __description__,
        'services': [
            'FIRSValidator',
            'SubmissionValidator',
            'FormatValidator',
            'CompletenessChecker',
            'ValidationErrorHandler'
        ]
    }