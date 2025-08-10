"""
Unified Error Handling Patterns
===============================

Comprehensive error handling for financial service integrations.
Provides error classification, recovery strategies, and monitoring.
"""

import logging
import traceback
import asyncio
from typing import Dict, List, Optional, Any, Union, Callable, Type
from datetime import datetime, timedelta
from decimal import Decimal
from dataclasses import dataclass, field
from enum import Enum
import json
from functools import wraps

logger = logging.getLogger(__name__)

class ErrorSeverity(str, Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ErrorCategory(str, Enum):
    """Error categories"""
    NETWORK = "network"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    VALIDATION = "validation"
    RATE_LIMIT = "rate_limit"
    SYSTEM = "system"
    BUSINESS_LOGIC = "business_logic"
    DATA_FORMAT = "data_format"
    TIMEOUT = "timeout"
    CONFIGURATION = "configuration"

class RecoveryStrategy(str, Enum):
    """Error recovery strategies"""
    RETRY = "retry"
    FALLBACK = "fallback"
    CIRCUIT_BREAKER = "circuit_breaker"
    GRACEFUL_DEGRADATION = "graceful_degradation"
    ESCALATE = "escalate"
    IGNORE = "ignore"

@dataclass
class ErrorContext:
    """Error context information"""
    
    operation: str
    service: str
    user_id: Optional[str] = None
    request_id: Optional[str] = None
    
    # Request details
    endpoint: Optional[str] = None
    method: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    # System context
    timestamp: datetime = field(default_factory=datetime.utcnow)
    environment: str = "production"
    version: str = "1.0.0"
    
    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ErrorInfo:
    """Comprehensive error information"""
    
    # Basic error info
    error_type: str
    error_message: str
    error_code: Optional[str] = None
    
    # Classification
    category: ErrorCategory
    severity: ErrorSeverity
    
    # Context
    context: ErrorContext
    
    # Technical details
    stack_trace: Optional[str] = None
    inner_error: Optional['ErrorInfo'] = None
    
    # Recovery
    recovery_strategy: RecoveryStrategy
    retry_count: int = 0
    max_retries: int = 3
    
    # Timestamps
    first_occurrence: datetime = field(default_factory=datetime.utcnow)
    last_occurrence: datetime = field(default_factory=datetime.utcnow)
    occurrence_count: int = 1
    
    # Resolution
    resolved: bool = False
    resolution_notes: Optional[str] = None
    resolved_at: Optional[datetime] = None

class FinancialServiceError(Exception):
    """Base exception for financial service errors"""
    
    def __init__(self, 
                 message: str,
                 error_code: Optional[str] = None,
                 category: ErrorCategory = ErrorCategory.SYSTEM,
                 severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                 context: Optional[ErrorContext] = None,
                 inner_error: Optional[Exception] = None):
        
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.category = category
        self.severity = severity
        self.context = context
        self.inner_error = inner_error

class AuthenticationError(FinancialServiceError):
    """Authentication related errors"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message, 
            category=ErrorCategory.AUTHENTICATION,
            severity=ErrorSeverity.HIGH,
            **kwargs
        )

class ValidationError(FinancialServiceError):
    """Data validation errors"""
    
    def __init__(self, message: str, field: Optional[str] = None, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.MEDIUM,
            **kwargs
        )
        self.field = field

class RateLimitError(FinancialServiceError):
    """Rate limit exceeded errors"""
    
    def __init__(self, message: str, retry_after: Optional[int] = None, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.RATE_LIMIT,
            severity=ErrorSeverity.MEDIUM,
            **kwargs
        )
        self.retry_after = retry_after

class NetworkError(FinancialServiceError):
    """Network connectivity errors"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.HIGH,
            **kwargs
        )

class BusinessLogicError(FinancialServiceError):
    """Business logic validation errors"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.BUSINESS_LOGIC,
            severity=ErrorSeverity.MEDIUM,
            **kwargs
        )

class ErrorClassifier:
    """Classify errors and determine recovery strategies"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.ErrorClassifier")
        
        # Error classification rules
        self.classification_rules = {
            # Network errors
            'ConnectionError': (ErrorCategory.NETWORK, ErrorSeverity.HIGH, RecoveryStrategy.RETRY),
            'TimeoutError': (ErrorCategory.TIMEOUT, ErrorSeverity.MEDIUM, RecoveryStrategy.RETRY),
            'ConnectTimeout': (ErrorCategory.NETWORK, ErrorSeverity.HIGH, RecoveryStrategy.RETRY),
            'ReadTimeout': (ErrorCategory.TIMEOUT, ErrorSeverity.MEDIUM, RecoveryStrategy.RETRY),
            
            # HTTP errors
            '400': (ErrorCategory.VALIDATION, ErrorSeverity.MEDIUM, RecoveryStrategy.ESCALATE),
            '401': (ErrorCategory.AUTHENTICATION, ErrorSeverity.HIGH, RecoveryStrategy.ESCALATE),
            '403': (ErrorCategory.AUTHORIZATION, ErrorSeverity.HIGH, RecoveryStrategy.ESCALATE),
            '404': (ErrorCategory.CONFIGURATION, ErrorSeverity.MEDIUM, RecoveryStrategy.ESCALATE),
            '429': (ErrorCategory.RATE_LIMIT, ErrorSeverity.MEDIUM, RecoveryStrategy.RETRY),
            '500': (ErrorCategory.SYSTEM, ErrorSeverity.HIGH, RecoveryStrategy.RETRY),
            '502': (ErrorCategory.NETWORK, ErrorSeverity.HIGH, RecoveryStrategy.RETRY),
            '503': (ErrorCategory.SYSTEM, ErrorSeverity.HIGH, RecoveryStrategy.RETRY),
            '504': (ErrorCategory.TIMEOUT, ErrorSeverity.HIGH, RecoveryStrategy.RETRY),
            
            # Specific service errors
            'insufficient_funds': (ErrorCategory.BUSINESS_LOGIC, ErrorSeverity.MEDIUM, RecoveryStrategy.ESCALATE),
            'invalid_account': (ErrorCategory.VALIDATION, ErrorSeverity.MEDIUM, RecoveryStrategy.ESCALATE),
            'duplicate_transaction': (ErrorCategory.BUSINESS_LOGIC, ErrorSeverity.LOW, RecoveryStrategy.IGNORE),
        }
    
    def classify_error(self, 
                      error: Exception,
                      context: Optional[ErrorContext] = None) -> ErrorInfo:
        """Classify error and create ErrorInfo"""
        
        error_type = type(error).__name__
        error_message = str(error)
        
        # Try to get HTTP status code
        status_code = None
        if hasattr(error, 'status_code'):
            status_code = str(error.status_code)
        elif hasattr(error, 'response') and hasattr(error.response, 'status_code'):
            status_code = str(error.response.status_code)
        
        # Check for specific error patterns in message
        error_code = None
        for pattern, (category, severity, strategy) in self.classification_rules.items():
            if (pattern in error_type or 
                pattern in error_message.lower() or 
                pattern == status_code):
                
                error_code = pattern
                break
        else:
            # Default classification
            category = ErrorCategory.SYSTEM
            severity = ErrorSeverity.MEDIUM
            strategy = RecoveryStrategy.RETRY
        
        # Handle specific error types
        if isinstance(error, FinancialServiceError):
            category = error.category
            severity = error.severity
            error_code = error.error_code
        
        # Create ErrorInfo
        error_info = ErrorInfo(
            error_type=error_type,
            error_message=error_message,
            error_code=error_code,
            category=category,
            severity=severity,
            context=context or ErrorContext(operation="unknown", service="unknown"),
            stack_trace=traceback.format_exc(),
            recovery_strategy=strategy
        )
        
        # Handle inner errors
        if hasattr(error, '__cause__') and error.__cause__:
            error_info.inner_error = self.classify_error(error.__cause__, context)
        
        return error_info

class RetryHandler:
    """Handle retry logic with exponential backoff"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.RetryHandler")
    
    async def should_retry(self, error_info: ErrorInfo) -> bool:
        """Determine if error should be retried"""
        
        # Check retry strategy
        if error_info.recovery_strategy != RecoveryStrategy.RETRY:
            return False
        
        # Check retry count
        if error_info.retry_count >= error_info.max_retries:
            return False
        
        # Category-specific retry logic
        if error_info.category == ErrorCategory.AUTHENTICATION:
            return False  # Don't retry auth errors
        
        if error_info.category == ErrorCategory.VALIDATION:
            return False  # Don't retry validation errors
        
        if error_info.category == ErrorCategory.RATE_LIMIT:
            return True  # Always retry rate limits with backoff
        
        return True
    
    async def calculate_delay(self, error_info: ErrorInfo) -> float:
        """Calculate retry delay in seconds"""
        
        base_delay = 1.0  # Base delay in seconds
        
        # Exponential backoff: delay = base_delay * (2 ^ retry_count)
        delay = base_delay * (2 ** error_info.retry_count)
        
        # Category-specific adjustments
        if error_info.category == ErrorCategory.RATE_LIMIT:
            # Rate limit errors might have specific retry-after header
            if hasattr(error_info, 'retry_after') and error_info.retry_after:
                delay = max(delay, error_info.retry_after)
        
        # Add jitter to prevent thundering herd
        import random
        jitter = random.uniform(0.1, 0.5)
        delay += jitter
        
        # Cap maximum delay
        max_delay = 300  # 5 minutes
        delay = min(delay, max_delay)
        
        return delay
    
    async def execute_with_retry(self,
                               operation: Callable,
                               context: ErrorContext,
                               max_retries: int = 3) -> Any:
        """Execute operation with retry logic"""
        
        last_error_info = None
        
        for attempt in range(max_retries + 1):
            try:
                if asyncio.iscoroutinefunction(operation):
                    return await operation()
                else:
                    return operation()
                    
            except Exception as e:
                # Classify error
                classifier = ErrorClassifier()
                error_info = classifier.classify_error(e, context)
                error_info.retry_count = attempt
                error_info.max_retries = max_retries
                
                last_error_info = error_info
                
                # Check if should retry
                if attempt < max_retries and await self.should_retry(error_info):
                    delay = await self.calculate_delay(error_info)
                    
                    self.logger.warning(
                        f"Retrying operation {context.operation} after {delay:.2f}s "
                        f"(attempt {attempt + 1}/{max_retries + 1}): {error_info.error_message}"
                    )
                    
                    await asyncio.sleep(delay)
                    continue
                else:
                    # Max retries exceeded or non-retryable error
                    self.logger.error(
                        f"Operation {context.operation} failed after {attempt + 1} attempts: "
                        f"{error_info.error_message}"
                    )
                    raise e
        
        # Should not reach here
        if last_error_info:
            raise Exception(f"Operation failed: {last_error_info.error_message}")

class CircuitBreaker:
    """Circuit breaker pattern implementation"""
    
    def __init__(self, 
                 failure_threshold: int = 5,
                 recovery_timeout: int = 60,
                 expected_exception: Type[Exception] = Exception):
        
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
        
        self.logger = logging.getLogger(f"{__name__}.CircuitBreaker")
    
    async def call(self, operation: Callable, *args, **kwargs) -> Any:
        """Execute operation with circuit breaker protection"""
        
        if self.state == 'OPEN':
            if self._should_attempt_reset():
                self.state = 'HALF_OPEN'
                self.logger.info("Circuit breaker transitioning to HALF_OPEN")
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            if asyncio.iscoroutinefunction(operation):
                result = await operation(*args, **kwargs)
            else:
                result = operation(*args, **kwargs)
            
            # Success - reset failure count
            if self.state == 'HALF_OPEN':
                self.state = 'CLOSED'
                self.logger.info("Circuit breaker reset to CLOSED")
            
            self.failure_count = 0
            return result
            
        except self.expected_exception as e:
            self._record_failure()
            raise e
    
    def _should_attempt_reset(self) -> bool:
        """Check if should attempt to reset circuit breaker"""
        
        if self.last_failure_time is None:
            return True
        
        time_since_failure = (datetime.utcnow() - self.last_failure_time).total_seconds()
        return time_since_failure >= self.recovery_timeout
    
    def _record_failure(self):
        """Record a failure"""
        
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        
        if self.failure_count >= self.failure_threshold:
            self.state = 'OPEN'
            self.logger.error(
                f"Circuit breaker opened after {self.failure_count} failures"
            )

class ErrorHandler:
    """Main error handler orchestrator"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.ErrorHandler")
        self.classifier = ErrorClassifier()
        self.retry_handler = RetryHandler()
        
        # Error storage for monitoring
        self.error_history: List[ErrorInfo] = []
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        
        # Error handlers by category
        self.category_handlers: Dict[ErrorCategory, Callable] = {}
    
    def register_category_handler(self, 
                                category: ErrorCategory, 
                                handler: Callable):
        """Register custom handler for error category"""
        
        self.category_handlers[category] = handler
        self.logger.info(f"Registered handler for {category}")
    
    async def handle_error(self, 
                          error: Exception,
                          context: ErrorContext,
                          auto_retry: bool = True) -> Optional[Any]:
        """Handle error with appropriate strategy"""
        
        # Classify error
        error_info = self.classifier.classify_error(error, context)
        
        # Store error for monitoring
        self._store_error(error_info)
        
        # Log error
        self._log_error(error_info)
        
        # Execute category-specific handler
        if error_info.category in self.category_handlers:
            try:
                result = await self.category_handlers[error_info.category](error_info)
                if result is not None:
                    return result
            except Exception as handler_error:
                self.logger.error(f"Category handler failed: {handler_error}")
        
        # Execute recovery strategy
        if error_info.recovery_strategy == RecoveryStrategy.RETRY and auto_retry:
            return await self._handle_retry_strategy(error_info, context)
        elif error_info.recovery_strategy == RecoveryStrategy.CIRCUIT_BREAKER:
            return await self._handle_circuit_breaker_strategy(error_info, context)
        elif error_info.recovery_strategy == RecoveryStrategy.GRACEFUL_DEGRADATION:
            return await self._handle_graceful_degradation(error_info, context)
        elif error_info.recovery_strategy == RecoveryStrategy.ESCALATE:
            await self._handle_escalation(error_info, context)
        elif error_info.recovery_strategy == RecoveryStrategy.IGNORE:
            self.logger.info(f"Ignoring error as per strategy: {error_info.error_message}")
            return None
        
        # Re-raise if no strategy handled it
        raise error
    
    async def _handle_retry_strategy(self, 
                                   error_info: ErrorInfo, 
                                   context: ErrorContext) -> Optional[Any]:
        """Handle retry strategy"""
        
        # This would typically be called within a retry loop
        # For now, just log the intent
        self.logger.info(f"Error marked for retry: {error_info.error_message}")
        return None
    
    async def _handle_circuit_breaker_strategy(self, 
                                             error_info: ErrorInfo, 
                                             context: ErrorContext) -> Optional[Any]:
        """Handle circuit breaker strategy"""
        
        service_key = f"{context.service}:{context.operation}"
        
        if service_key not in self.circuit_breakers:
            self.circuit_breakers[service_key] = CircuitBreaker()
        
        circuit_breaker = self.circuit_breakers[service_key]
        circuit_breaker._record_failure()
        
        self.logger.warning(f"Circuit breaker recorded failure for {service_key}")
        return None
    
    async def _handle_graceful_degradation(self, 
                                         error_info: ErrorInfo, 
                                         context: ErrorContext) -> Optional[Any]:
        """Handle graceful degradation"""
        
        self.logger.info(f"Implementing graceful degradation for: {error_info.error_message}")
        
        # Return fallback data structure
        return {
            'degraded': True,
            'error_category': error_info.category.value,
            'fallback_data': {},
            'message': 'Service temporarily degraded'
        }
    
    async def _handle_escalation(self, 
                               error_info: ErrorInfo, 
                               context: ErrorContext):
        """Handle error escalation"""
        
        self.logger.error(f"Escalating error: {error_info.error_message}")
        
        # In a real implementation, this would:
        # - Send alerts to monitoring systems
        # - Create support tickets
        # - Notify on-call engineers
        # - Update status pages
        
        # For now, just log at critical level
        if error_info.severity == ErrorSeverity.CRITICAL:
            self.logger.critical(f"CRITICAL ERROR ESCALATED: {error_info.error_message}")
    
    def _store_error(self, error_info: ErrorInfo):
        """Store error for monitoring and analysis"""
        
        # Check for duplicate errors
        for existing_error in self.error_history:
            if (existing_error.error_type == error_info.error_type and 
                existing_error.context.operation == error_info.context.operation):
                
                existing_error.occurrence_count += 1
                existing_error.last_occurrence = datetime.utcnow()
                return
        
        # Add new error
        self.error_history.append(error_info)
        
        # Keep only recent errors (last 1000)
        if len(self.error_history) > 1000:
            self.error_history = self.error_history[-1000:]
    
    def _log_error(self, error_info: ErrorInfo):
        """Log error with appropriate level"""
        
        log_message = (
            f"[{error_info.category.value.upper()}] "
            f"{error_info.context.service}:{error_info.context.operation} - "
            f"{error_info.error_message}"
        )
        
        if error_info.severity == ErrorSeverity.CRITICAL:
            self.logger.critical(log_message)
        elif error_info.severity == ErrorSeverity.HIGH:
            self.logger.error(log_message)
        elif error_info.severity == ErrorSeverity.MEDIUM:
            self.logger.warning(log_message)
        else:
            self.logger.info(log_message)
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics for monitoring"""
        
        if not self.error_history:
            return {'total_errors': 0}
        
        # Calculate statistics
        total_errors = len(self.error_history)
        
        # Group by category
        category_counts = {}
        severity_counts = {}
        
        for error in self.error_history:
            category_counts[error.category.value] = category_counts.get(error.category.value, 0) + 1
            severity_counts[error.severity.value] = severity_counts.get(error.severity.value, 0) + 1
        
        # Recent errors (last hour)
        hour_ago = datetime.utcnow() - timedelta(hours=1)
        recent_errors = [e for e in self.error_history if e.last_occurrence > hour_ago]
        
        return {
            'total_errors': total_errors,
            'recent_errors_last_hour': len(recent_errors),
            'category_breakdown': category_counts,
            'severity_breakdown': severity_counts,
            'circuit_breakers': {
                key: {
                    'state': cb.state,
                    'failure_count': cb.failure_count
                }
                for key, cb in self.circuit_breakers.items()
            }
        }

def error_handler(auto_retry: bool = True, 
                 max_retries: int = 3,
                 circuit_breaker: bool = False):
    """Decorator for automatic error handling"""
    
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            context = ErrorContext(
                operation=func.__name__,
                service=func.__module__,
                request_id=kwargs.get('request_id')
            )
            
            handler = ErrorHandler()
            
            try:
                if circuit_breaker:
                    # Use circuit breaker
                    service_key = f"{context.service}:{context.operation}"
                    if service_key not in handler.circuit_breakers:
                        handler.circuit_breakers[service_key] = CircuitBreaker()
                    
                    cb = handler.circuit_breakers[service_key]
                    return await cb.call(func, *args, **kwargs)
                else:
                    return await func(*args, **kwargs)
                    
            except Exception as e:
                result = await handler.handle_error(e, context, auto_retry)
                if result is not None:
                    return result
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Convert to async and run
            return asyncio.run(async_wrapper(*args, **kwargs))
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator