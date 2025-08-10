"""
Unified Banking Exceptions
=========================
Comprehensive exception hierarchy for unified banking operations.
Provides specific error types for different failure scenarios across
multiple banking providers with detailed error information.

Key Features:
- Provider-agnostic error types
- Detailed error context and metadata
- Compliance and audit error tracking
- Recovery and retry guidance
- Enterprise error reporting
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum

from .....shared.exceptions import IntegrationError


class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for classification."""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    RATE_LIMITING = "rate_limiting"
    NETWORK = "network"
    TIMEOUT = "timeout"
    DATA_VALIDATION = "data_validation"
    PROVIDER_ERROR = "provider_error"
    CONFIGURATION = "configuration"
    COMPLIANCE = "compliance"
    BUSINESS_RULE = "business_rule"
    SYSTEM = "system"


class BankingError(IntegrationError):
    """
    Base exception for all banking-related errors.
    
    Provides comprehensive error context including provider information,
    error classification, and recovery guidance.
    """
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        provider_type: Optional[str] = None,
        category: Optional[ErrorCategory] = None,
        severity: Optional[ErrorSeverity] = None,
        details: Optional[Dict[str, Any]] = None,
        recoverable: bool = True,
        retry_after: Optional[int] = None,
        original_error: Optional[Exception] = None
    ):
        """
        Initialize banking error.
        
        Args:
            message: Human-readable error message
            error_code: Specific error code for programmatic handling
            provider_type: Banking provider that caused the error
            category: Error category for classification
            severity: Error severity level
            details: Additional error details and context
            recoverable: Whether the error is recoverable
            retry_after: Suggested retry delay in seconds
            original_error: Original exception that caused this error
        """
        super().__init__(message)
        
        self.error_code = error_code
        self.provider_type = provider_type
        self.category = category or ErrorCategory.SYSTEM
        self.severity = severity or ErrorSeverity.MEDIUM
        self.details = details or {}
        self.recoverable = recoverable
        self.retry_after = retry_after
        self.original_error = original_error
        self.timestamp = datetime.utcnow()
        
        # Add error context to details
        self.details.update({
            'error_class': self.__class__.__name__,
            'timestamp': self.timestamp.isoformat(),
            'provider_type': self.provider_type,
            'category': self.category.value if self.category else None,
            'severity': self.severity.value if self.severity else None,
            'recoverable': self.recoverable
        })
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for serialization."""
        return {
            'error_type': self.__class__.__name__,
            'message': str(self),
            'error_code': self.error_code,
            'provider_type': self.provider_type,
            'category': self.category.value if self.category else None,
            'severity': self.severity.value if self.severity else None,
            'details': self.details,
            'recoverable': self.recoverable,
            'retry_after': self.retry_after,
            'timestamp': self.timestamp.isoformat()
        }


class BankingAggregatorError(BankingError):
    """Error in banking aggregator operations."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.SYSTEM,
            severity=ErrorSeverity.HIGH,
            **kwargs
        )


class ProviderUnavailableError(BankingError):
    """Provider is unavailable or unhealthy."""
    
    def __init__(self, message: str, provider_type: str, **kwargs):
        super().__init__(
            message,
            provider_type=provider_type,
            category=ErrorCategory.PROVIDER_ERROR,
            severity=ErrorSeverity.HIGH,
            recoverable=True,
            **kwargs
        )


class NoProvidersAvailableError(BankingError):
    """No providers are available for the operation."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.SYSTEM,
            severity=ErrorSeverity.CRITICAL,
            recoverable=False,
            **kwargs
        )


class ProviderSelectionError(BankingError):
    """Error in provider selection logic."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.SYSTEM,
            severity=ErrorSeverity.MEDIUM,
            **kwargs
        )


class LoadBalancingError(BankingError):
    """Error in load balancing operations."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.SYSTEM,
            severity=ErrorSeverity.MEDIUM,
            **kwargs
        )


class ProviderOverloadedError(BankingError):
    """Provider is overloaded and cannot handle more requests."""
    
    def __init__(self, message: str, provider_type: str, retry_after: int = 60, **kwargs):
        super().__init__(
            message,
            provider_type=provider_type,
            category=ErrorCategory.RATE_LIMITING,
            severity=ErrorSeverity.MEDIUM,
            recoverable=True,
            retry_after=retry_after,
            **kwargs
        )


class NoCapacityAvailableError(BankingError):
    """No capacity available across all providers."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.RATE_LIMITING,
            severity=ErrorSeverity.HIGH,
            recoverable=True,
            retry_after=300,  # 5 minutes
            **kwargs
        )


class LoadBalancerConfigError(BankingError):
    """Configuration error in load balancer."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.CONFIGURATION,
            severity=ErrorSeverity.HIGH,
            recoverable=False,
            **kwargs
        )


class FailoverError(BankingError):
    """Error during failover operations."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.SYSTEM,
            severity=ErrorSeverity.HIGH,
            **kwargs
        )


class CircuitBreakerOpenError(BankingError):
    """Circuit breaker is open, preventing operations."""
    
    def __init__(self, message: str, provider_type: str, retry_after: int = 60, **kwargs):
        super().__init__(
            message,
            provider_type=provider_type,
            category=ErrorCategory.PROVIDER_ERROR,
            severity=ErrorSeverity.MEDIUM,
            recoverable=True,
            retry_after=retry_after,
            **kwargs
        )


class NoHealthyProvidersError(BankingError):
    """No healthy providers available."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.SYSTEM,
            severity=ErrorSeverity.CRITICAL,
            recoverable=True,
            retry_after=300,
            **kwargs
        )


class FailoverTimeoutError(BankingError):
    """Timeout during failover operation."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.TIMEOUT,
            severity=ErrorSeverity.HIGH,
            recoverable=True,
            **kwargs
        )


class MaxRetriesExceededError(BankingError):
    """Maximum retry attempts exceeded."""
    
    def __init__(self, message: str, attempt_count: int, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.SYSTEM,
            severity=ErrorSeverity.HIGH,
            recoverable=False,
            details={'attempt_count': attempt_count},
            **kwargs
        )


class DataConsistencyError(BankingError):
    """Data consistency error across providers."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.DATA_VALIDATION,
            severity=ErrorSeverity.HIGH,
            **kwargs
        )


class InsufficientProviderError(BankingError):
    """Insufficient providers for the requested operation."""
    
    def __init__(self, message: str, required_count: int, available_count: int, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.SYSTEM,
            severity=ErrorSeverity.MEDIUM,
            details={
                'required_count': required_count,
                'available_count': available_count
            },
            **kwargs
        )


class ProviderAuthenticationError(BankingError):
    """Authentication error with provider."""
    
    def __init__(self, message: str, provider_type: str, **kwargs):
        super().__init__(
            message,
            provider_type=provider_type,
            category=ErrorCategory.AUTHENTICATION,
            severity=ErrorSeverity.HIGH,
            recoverable=True,
            **kwargs
        )


class ProviderAuthorizationError(BankingError):
    """Authorization error with provider."""
    
    def __init__(self, message: str, provider_type: str, **kwargs):
        super().__init__(
            message,
            provider_type=provider_type,
            category=ErrorCategory.AUTHORIZATION,
            severity=ErrorSeverity.HIGH,
            recoverable=False,
            **kwargs
        )


class ProviderRateLimitError(BankingError):
    """Rate limit exceeded for provider."""
    
    def __init__(self, message: str, provider_type: str, retry_after: int = 60, **kwargs):
        super().__init__(
            message,
            provider_type=provider_type,
            category=ErrorCategory.RATE_LIMITING,
            severity=ErrorSeverity.MEDIUM,
            recoverable=True,
            retry_after=retry_after,
            **kwargs
        )


class ProviderNetworkError(BankingError):
    """Network error communicating with provider."""
    
    def __init__(self, message: str, provider_type: str, **kwargs):
        super().__init__(
            message,
            provider_type=provider_type,
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.MEDIUM,
            recoverable=True,
            **kwargs
        )


class ProviderTimeoutError(BankingError):
    """Timeout error communicating with provider."""
    
    def __init__(self, message: str, provider_type: str, timeout_duration: float, **kwargs):
        super().__init__(
            message,
            provider_type=provider_type,
            category=ErrorCategory.TIMEOUT,
            severity=ErrorSeverity.MEDIUM,
            recoverable=True,
            details={'timeout_duration': timeout_duration},
            **kwargs
        )


class ProviderDataError(BankingError):
    """Data validation error from provider."""
    
    def __init__(self, message: str, provider_type: str, **kwargs):
        super().__init__(
            message,
            provider_type=provider_type,
            category=ErrorCategory.DATA_VALIDATION,
            severity=ErrorSeverity.MEDIUM,
            **kwargs
        )


class ComplianceViolationError(BankingError):
    """Compliance violation detected."""
    
    def __init__(self, message: str, violation_type: str, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.COMPLIANCE,
            severity=ErrorSeverity.CRITICAL,
            recoverable=False,
            details={'violation_type': violation_type},
            **kwargs
        )


class AuditTrailError(BankingError):
    """Error in audit trail operations."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.COMPLIANCE,
            severity=ErrorSeverity.HIGH,
            **kwargs
        )


class BusinessRuleViolationError(BankingError):
    """Business rule violation detected."""
    
    def __init__(self, message: str, rule_name: str, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.BUSINESS_RULE,
            severity=ErrorSeverity.MEDIUM,
            details={'rule_name': rule_name},
            **kwargs
        )


class ConfigurationError(BankingError):
    """Configuration error in banking system."""
    
    def __init__(self, message: str, config_section: str, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.CONFIGURATION,
            severity=ErrorSeverity.HIGH,
            recoverable=False,
            details={'config_section': config_section},
            **kwargs
        )


class BankingSecurityError(BankingError):
    """Security-related error in banking operations."""
    
    def __init__(self, message: str, security_context: Dict[str, Any], **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.AUTHORIZATION,
            severity=ErrorSeverity.CRITICAL,
            recoverable=False,
            details={'security_context': security_context},
            **kwargs
        )


# Exception mapping for provider-specific errors
PROVIDER_ERROR_MAP = {
    'authentication_failed': ProviderAuthenticationError,
    'authorization_failed': ProviderAuthorizationError,
    'rate_limit_exceeded': ProviderRateLimitError,
    'network_error': ProviderNetworkError,
    'timeout': ProviderTimeoutError,
    'data_validation_error': ProviderDataError,
    'provider_unavailable': ProviderUnavailableError,
    'circuit_breaker_open': CircuitBreakerOpenError,
    'overloaded': ProviderOverloadedError
}


def create_provider_error(
    error_type: str,
    message: str,
    provider_type: str,
    **kwargs
) -> BankingError:
    """
    Create appropriate provider error based on error type.
    
    Args:
        error_type: Type of error
        message: Error message
        provider_type: Provider that caused the error
        **kwargs: Additional error context
        
    Returns:
        Appropriate BankingError subclass instance
    """
    error_class = PROVIDER_ERROR_MAP.get(error_type, BankingError)
    return error_class(message, provider_type=provider_type, **kwargs)


def handle_provider_exception(
    exception: Exception,
    provider_type: str,
    operation_context: Dict[str, Any]
) -> BankingError:
    """
    Convert provider-specific exception to unified banking error.
    
    Args:
        exception: Original provider exception
        provider_type: Provider that raised the exception
        operation_context: Context of the operation
        
    Returns:
        Unified banking error
    """
    error_message = str(exception)
    
    # Determine error type based on exception type and message
    if 'auth' in error_message.lower():
        return ProviderAuthenticationError(
            error_message,
            provider_type=provider_type,
            original_error=exception,
            details=operation_context
        )
    elif 'rate limit' in error_message.lower():
        return ProviderRateLimitError(
            error_message,
            provider_type=provider_type,
            original_error=exception,
            details=operation_context
        )
    elif 'timeout' in error_message.lower():
        return ProviderTimeoutError(
            error_message,
            provider_type=provider_type,
            timeout_duration=operation_context.get('timeout', 30),
            original_error=exception,
            details=operation_context
        )
    elif 'network' in error_message.lower() or 'connection' in error_message.lower():
        return ProviderNetworkError(
            error_message,
            provider_type=provider_type,
            original_error=exception,
            details=operation_context
        )
    else:
        # Generic provider error
        return BankingError(
            error_message,
            provider_type=provider_type,
            category=ErrorCategory.PROVIDER_ERROR,
            original_error=exception,
            details=operation_context
        )