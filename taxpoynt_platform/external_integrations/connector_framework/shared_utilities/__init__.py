"""
Shared Utilities for Connector Framework
========================================

Common utilities and frameworks for financial service integrations.
Provides webhook handling, rate limiting, error management, audit logging, and retry mechanisms.
"""

from .webhook_framework import (
    WebhookFramework,
    WebhookProcessor, 
    WebhookDeliveryManager,
    WebhookValidator,
    WebhookEvent,
    WebhookStatus,
    WebhookPayload,
    WebhookEndpoint,
    WebhookDelivery
)

from .rate_limiter import (
    RateLimiter,
    RateLimitManager,
    RateLimitConfig,
    RateLimitResult,
    RateLimitStrategy,
    RateLimitScope,
    TokenBucketLimiter,
    SlidingWindowLimiter,
    AdaptiveLimiter
)

from .error_handler import (
    ErrorHandler,
    ErrorClassifier,
    RetryHandler,
    CircuitBreaker,
    FinancialServiceError,
    AuthenticationError,
    ValidationError,
    RateLimitError,
    NetworkError,
    BusinessLogicError,
    ErrorCategory,
    ErrorSeverity,
    RecoveryStrategy,
    ErrorContext,
    ErrorInfo,
    error_handler
)

from .audit_logger import (
    AuditLogger,
    AuditEvent,
    AuditEventType,
    ComplianceFramework,
    AuditLevel,
    UserContext,
    SystemContext, 
    DataContext
)

from .retry_manager import (
    RetryManager,
    RetryManagerPool, 
    RetryConfig,
    RetrySession,
    RetryAttempt,
    RetryStrategy,
    RetryCondition,
    RetryOutcome,
    DelayCalculator,
    RetryConditionChecker,
    CostTracker,
    CircuitBreakerIntegration,
    retry
)

__version__ = "1.0.0"
__author__ = "TaxPoynt Platform Team"

__all__ = [
    # Webhook Framework
    "WebhookFramework",
    "WebhookProcessor", 
    "WebhookDeliveryManager",
    "WebhookValidator",
    "WebhookEvent",
    "WebhookStatus",
    "WebhookPayload",
    "WebhookEndpoint",
    "WebhookDelivery",
    
    # Rate Limiting
    "RateLimiter",
    "RateLimitManager",
    "RateLimitConfig",
    "RateLimitResult",
    "RateLimitStrategy",
    "RateLimitScope",
    "TokenBucketLimiter",
    "SlidingWindowLimiter",
    "AdaptiveLimiter",
    
    # Error Handling
    "ErrorHandler",
    "ErrorClassifier",
    "RetryHandler",
    "CircuitBreaker",
    "FinancialServiceError",
    "AuthenticationError",
    "ValidationError",
    "RateLimitError",
    "NetworkError",
    "BusinessLogicError",
    "ErrorCategory",
    "ErrorSeverity",
    "RecoveryStrategy",
    "ErrorContext",
    "ErrorInfo",
    "error_handler",  # Decorator
    
    # Audit Logging
    "AuditLogger",
    "AuditEvent",
    "AuditEventType",
    "ComplianceFramework",
    "AuditLevel",
    "UserContext",
    "SystemContext", 
    "DataContext",
    
    # Retry Management
    "RetryManager",
    "RetryManagerPool", 
    "RetryConfig",
    "RetrySession",
    "RetryAttempt",
    "RetryStrategy",
    "RetryCondition",
    "RetryOutcome",
    "DelayCalculator",
    "RetryConditionChecker",
    "CostTracker",
    "CircuitBreakerIntegration",
    "retry"  # Decorator
]