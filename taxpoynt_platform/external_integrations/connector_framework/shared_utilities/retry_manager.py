"""
Intelligent Retry Management
===========================

Advanced retry mechanisms with exponential backoff, jitter, and circuit breaker integration.
Optimized for financial service API reliability and cost management.
"""

import logging
import asyncio
import random
import time
from typing import Dict, List, Optional, Any, Callable, Union, Type
from datetime import datetime, timedelta
from decimal import Decimal
from dataclasses import dataclass, field
from enum import Enum
import json
from functools import wraps

logger = logging.getLogger(__name__)

class RetryStrategy(str, Enum):
    """Retry strategies"""
    FIXED_DELAY = "fixed_delay"
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"
    FIBONACCI_BACKOFF = "fibonacci_backoff"
    CUSTOM = "custom"

class RetryCondition(str, Enum):
    """Conditions for retry"""
    ALWAYS = "always"
    ON_EXCEPTION = "on_exception"
    ON_SPECIFIC_EXCEPTIONS = "on_specific_exceptions"
    ON_STATUS_CODE = "on_status_code"
    ON_CUSTOM_CONDITION = "on_custom_condition"

class RetryOutcome(str, Enum):
    """Retry attempt outcomes"""
    SUCCESS = "success"
    RETRY = "retry"
    ABANDON = "abandon"
    CIRCUIT_BREAKER_OPEN = "circuit_breaker_open"

@dataclass
class RetryConfig:
    """Retry configuration"""
    
    # Basic retry settings
    max_attempts: int = 3
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF
    
    # Timing configuration
    initial_delay_seconds: float = 1.0
    max_delay_seconds: float = 300.0  # 5 minutes
    multiplier: float = 2.0
    
    # Jitter configuration
    enable_jitter: bool = True
    jitter_percentage: float = 0.1  # 10% jitter
    
    # Condition configuration
    retry_condition: RetryCondition = RetryCondition.ON_EXCEPTION
    retryable_exceptions: List[Type[Exception]] = field(default_factory=list)
    retryable_status_codes: List[int] = field(default_factory=lambda: [429, 502, 503, 504])
    
    # Custom condition
    custom_condition: Optional[Callable[[Exception], bool]] = None
    
    # Circuit breaker integration
    enable_circuit_breaker: bool = False
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: int = 60
    
    # Cost management
    max_cost_per_operation: Optional[Decimal] = None
    cost_per_retry: Optional[Decimal] = None
    
    # Monitoring
    enable_metrics: bool = True
    log_retry_attempts: bool = True

@dataclass
class RetryAttempt:
    """Individual retry attempt record"""
    
    attempt_number: int
    timestamp: datetime
    delay_seconds: float
    
    # Attempt outcome
    outcome: RetryOutcome
    error: Optional[Exception] = None
    error_message: Optional[str] = None
    
    # Timing
    execution_time_ms: Optional[float] = None
    total_elapsed_ms: Optional[float] = None
    
    # Cost tracking
    attempt_cost: Optional[Decimal] = None
    cumulative_cost: Optional[Decimal] = None

@dataclass
class RetrySession:
    """Complete retry session tracking"""
    
    session_id: str
    operation_name: str
    start_time: datetime
    
    # Configuration
    config: RetryConfig
    
    # Attempts
    attempts: List[RetryAttempt] = field(default_factory=list)
    
    # Final outcome
    success: Optional[bool] = None
    final_result: Optional[Any] = None
    final_error: Optional[Exception] = None
    
    # Session metrics
    total_attempts: int = 0
    total_delay_seconds: float = 0.0
    total_execution_time_ms: float = 0.0
    total_cost: Optional[Decimal] = None
    
    # Completion
    end_time: Optional[datetime] = None
    abandoned_reason: Optional[str] = None

class DelayCalculator:
    """Calculate retry delays based on strategy"""
    
    def __init__(self, config: RetryConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.DelayCalculator")
    
    def calculate_delay(self, attempt_number: int) -> float:
        """Calculate delay for given attempt number"""
        
        if self.config.strategy == RetryStrategy.FIXED_DELAY:
            delay = self.config.initial_delay_seconds
        
        elif self.config.strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            delay = self.config.initial_delay_seconds * (self.config.multiplier ** (attempt_number - 1))
        
        elif self.config.strategy == RetryStrategy.LINEAR_BACKOFF:
            delay = self.config.initial_delay_seconds * attempt_number
        
        elif self.config.strategy == RetryStrategy.FIBONACCI_BACKOFF:
            delay = self.config.initial_delay_seconds * self._fibonacci(attempt_number)
        
        else:  # Default to exponential
            delay = self.config.initial_delay_seconds * (self.config.multiplier ** (attempt_number - 1))
        
        # Apply maximum delay cap
        delay = min(delay, self.config.max_delay_seconds)
        
        # Apply jitter if enabled
        if self.config.enable_jitter:
            delay = self._apply_jitter(delay)
        
        return delay
    
    def _fibonacci(self, n: int) -> int:
        """Calculate Fibonacci number for backoff"""
        
        if n <= 1:
            return 1
        elif n == 2:
            return 1
        else:
            a, b = 1, 1
            for _ in range(2, n):
                a, b = b, a + b
            return b
    
    def _apply_jitter(self, delay: float) -> float:
        """Apply jitter to delay"""
        
        jitter_amount = delay * self.config.jitter_percentage
        jitter = random.uniform(-jitter_amount, jitter_amount)
        
        return max(0.1, delay + jitter)  # Minimum 100ms delay

class RetryConditionChecker:
    """Check if operation should be retried"""
    
    def __init__(self, config: RetryConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.RetryConditionChecker")
    
    def should_retry(self, 
                    exception: Optional[Exception] = None,
                    result: Optional[Any] = None,
                    attempt_number: int = 1) -> bool:
        """Determine if operation should be retried"""
        
        # Check maximum attempts
        if attempt_number >= self.config.max_attempts:
            return False
        
        # Check retry condition
        if self.config.retry_condition == RetryCondition.ALWAYS:
            return True
        
        elif self.config.retry_condition == RetryCondition.ON_EXCEPTION:
            return exception is not None
        
        elif self.config.retry_condition == RetryCondition.ON_SPECIFIC_EXCEPTIONS:
            if exception is None:
                return False
            return any(isinstance(exception, exc_type) for exc_type in self.config.retryable_exceptions)
        
        elif self.config.retry_condition == RetryCondition.ON_STATUS_CODE:
            if hasattr(exception, 'status_code'):
                return exception.status_code in self.config.retryable_status_codes
            elif hasattr(exception, 'response') and hasattr(exception.response, 'status_code'):
                return exception.response.status_code in self.config.retryable_status_codes
            return False
        
        elif self.config.retry_condition == RetryCondition.ON_CUSTOM_CONDITION:
            if self.config.custom_condition and exception:
                return self.config.custom_condition(exception)
            return False
        
        return False
    
    def get_abandonment_reason(self, 
                             exception: Optional[Exception] = None,
                             attempt_number: int = 1) -> Optional[str]:
        """Get reason for abandoning retries"""
        
        if attempt_number >= self.config.max_attempts:
            return f"max_attempts_exceeded ({self.config.max_attempts})"
        
        if exception and not self.should_retry(exception, attempt_number=attempt_number):
            if isinstance(exception, (KeyboardInterrupt, SystemExit)):
                return "system_interrupt"
            elif hasattr(exception, 'status_code') and exception.status_code in [400, 401, 403, 404]:
                return f"non_retryable_status_code ({exception.status_code})"
            else:
                return f"non_retryable_exception ({type(exception).__name__})"
        
        return None

class CostTracker:
    """Track retry costs for financial optimization"""
    
    def __init__(self, config: RetryConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.CostTracker")
    
    def calculate_attempt_cost(self, attempt_number: int) -> Optional[Decimal]:
        """Calculate cost for specific attempt"""
        
        if self.config.cost_per_retry is None:
            return None
        
        # Base cost per retry
        base_cost = self.config.cost_per_retry
        
        # Exponential cost increase for excessive retries
        if attempt_number > 3:
            cost_multiplier = Decimal(str(1.5 ** (attempt_number - 3)))
            return base_cost * cost_multiplier
        
        return base_cost
    
    def should_abandon_due_to_cost(self, cumulative_cost: Optional[Decimal]) -> bool:
        """Check if should abandon due to cost limits"""
        
        if (self.config.max_cost_per_operation is None or 
            cumulative_cost is None):
            return False
        
        return cumulative_cost >= self.config.max_cost_per_operation

class CircuitBreakerIntegration:
    """Circuit breaker integration for retry management"""
    
    def __init__(self, config: RetryConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.CircuitBreakerIntegration")
        
        # Circuit breaker state
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    def should_allow_attempt(self) -> bool:
        """Check if circuit breaker allows attempt"""
        
        if not self.config.enable_circuit_breaker:
            return True
        
        if self.state == "CLOSED":
            return True
        
        elif self.state == "OPEN":
            # Check if timeout period has passed
            if (self.last_failure_time and 
                (datetime.utcnow() - self.last_failure_time).total_seconds() >= self.config.circuit_breaker_timeout):
                
                self.state = "HALF_OPEN"
                self.logger.info("Circuit breaker transitioning to HALF_OPEN")
                return True
            
            return False
        
        elif self.state == "HALF_OPEN":
            return True
        
        return False
    
    def record_success(self):
        """Record successful operation"""
        
        if self.state == "HALF_OPEN":
            self.state = "CLOSED"
            self.failure_count = 0
            self.logger.info("Circuit breaker reset to CLOSED")
    
    def record_failure(self):
        """Record failed operation"""
        
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        
        if self.failure_count >= self.config.circuit_breaker_threshold:
            self.state = "OPEN"
            self.logger.warning(f"Circuit breaker opened after {self.failure_count} failures")

class RetryManager:
    """Main retry management orchestrator"""
    
    def __init__(self, config: RetryConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.RetryManager")
        
        # Components
        self.delay_calculator = DelayCalculator(config)
        self.condition_checker = RetryConditionChecker(config)
        self.cost_tracker = CostTracker(config)
        self.circuit_breaker = CircuitBreakerIntegration(config)
        
        # Session tracking
        self.active_sessions: Dict[str, RetrySession] = {}
        self.session_counter = 0
        
        self.logger.info(f"Retry manager initialized with {config.strategy} strategy")
    
    async def execute_with_retry(self,
                               operation: Callable,
                               operation_name: str = "unknown",
                               *args,
                               **kwargs) -> Any:
        """Execute operation with retry logic"""
        
        # Create retry session
        session = self._create_retry_session(operation_name)
        
        try:
            result = await self._execute_retry_loop(session, operation, *args, **kwargs)
            session.success = True
            session.final_result = result
            return result
            
        except Exception as e:
            session.success = False
            session.final_error = e
            raise
            
        finally:
            # Complete session
            session.end_time = datetime.utcnow()
            
            # Log session summary
            if self.config.log_retry_attempts:
                await self._log_session_summary(session)
            
            # Clean up
            if session.session_id in self.active_sessions:
                del self.active_sessions[session.session_id]
    
    async def _execute_retry_loop(self,
                                session: RetrySession,
                                operation: Callable,
                                *args,
                                **kwargs) -> Any:
        """Execute the main retry loop"""
        
        last_exception = None
        
        for attempt_number in range(1, self.config.max_attempts + 1):
            # Check circuit breaker
            if not self.circuit_breaker.should_allow_attempt():
                session.abandoned_reason = "circuit_breaker_open"
                raise Exception("Circuit breaker is open - operation not allowed")
            
            # Create attempt record
            attempt = RetryAttempt(
                attempt_number=attempt_number,
                timestamp=datetime.utcnow(),
                delay_seconds=0.0
            )
            
            try:
                # Execute operation
                start_time = time.time()
                
                if asyncio.iscoroutinefunction(operation):
                    result = await operation(*args, **kwargs)
                else:
                    result = operation(*args, **kwargs)
                
                # Success!
                execution_time = (time.time() - start_time) * 1000
                attempt.outcome = RetryOutcome.SUCCESS
                attempt.execution_time_ms = execution_time
                
                # Update session
                session.attempts.append(attempt)
                session.total_attempts = len(session.attempts)
                session.total_execution_time_ms += execution_time
                
                # Record circuit breaker success
                self.circuit_breaker.record_success()
                
                return result
                
            except Exception as e:
                execution_time = (time.time() - start_time) * 1000
                last_exception = e
                
                # Update attempt record
                attempt.outcome = RetryOutcome.RETRY
                attempt.error = e
                attempt.error_message = str(e)
                attempt.execution_time_ms = execution_time
                
                # Calculate cost
                if self.config.cost_per_retry:
                    attempt.attempt_cost = self.cost_tracker.calculate_attempt_cost(attempt_number)
                    attempt.cumulative_cost = (session.total_cost or Decimal('0')) + (attempt.attempt_cost or Decimal('0'))
                    session.total_cost = attempt.cumulative_cost
                
                # Record circuit breaker failure
                self.circuit_breaker.record_failure()
                
                # Check if should retry
                should_retry = self.condition_checker.should_retry(e, attempt_number=attempt_number)
                
                # Check cost limits
                cost_exceeded = self.cost_tracker.should_abandon_due_to_cost(attempt.cumulative_cost)
                
                # Update session
                session.attempts.append(attempt)
                session.total_attempts = len(session.attempts)
                session.total_execution_time_ms += execution_time
                
                # Determine if this is the last attempt
                is_last_attempt = attempt_number >= self.config.max_attempts
                
                if not should_retry or cost_exceeded or is_last_attempt:
                    # Abandoning retries
                    attempt.outcome = RetryOutcome.ABANDON
                    
                    if cost_exceeded:
                        session.abandoned_reason = "cost_limit_exceeded"
                    else:
                        session.abandoned_reason = self.condition_checker.get_abandonment_reason(e, attempt_number)
                    
                    break
                
                # Calculate delay for next attempt
                if attempt_number < self.config.max_attempts:
                    delay = self.delay_calculator.calculate_delay(attempt_number + 1)
                    session.total_delay_seconds += delay
                    
                    # Log retry attempt
                    if self.config.log_retry_attempts:
                        self.logger.warning(
                            f"Retry attempt {attempt_number}/{self.config.max_attempts} failed for "
                            f"{session.operation_name}: {str(e)}. Retrying in {delay:.2f}s"
                        )
                    
                    # Wait before retry
                    await asyncio.sleep(delay)
        
        # All retries exhausted
        if last_exception:
            raise last_exception
        else:
            raise Exception("Operation failed after all retry attempts")
    
    def _create_retry_session(self, operation_name: str) -> RetrySession:
        """Create new retry session"""
        
        self.session_counter += 1
        session_id = f"retry_{int(datetime.utcnow().timestamp())}_{self.session_counter:06d}"
        
        session = RetrySession(
            session_id=session_id,
            operation_name=operation_name,
            start_time=datetime.utcnow(),
            config=self.config
        )
        
        self.active_sessions[session_id] = session
        return session
    
    async def _log_session_summary(self, session: RetrySession):
        """Log retry session summary"""
        
        duration_ms = 0
        if session.end_time:
            duration_ms = (session.end_time - session.start_time).total_seconds() * 1000
        
        summary = {
            'session_id': session.session_id,
            'operation': session.operation_name,
            'success': session.success,
            'total_attempts': session.total_attempts,
            'total_duration_ms': duration_ms,
            'total_delay_seconds': session.total_delay_seconds,
            'total_execution_time_ms': session.total_execution_time_ms,
            'abandoned_reason': session.abandoned_reason
        }
        
        if session.total_cost:
            summary['total_cost'] = str(session.total_cost)
        
        if session.success:
            self.logger.info(f"Retry session completed successfully: {json.dumps(summary)}")
        else:
            self.logger.error(f"Retry session failed: {json.dumps(summary)}")
    
    def get_session_statistics(self) -> Dict[str, Any]:
        """Get retry session statistics"""
        
        active_sessions = len(self.active_sessions)
        
        # Circuit breaker status
        circuit_breaker_status = {
            'state': self.circuit_breaker.state,
            'failure_count': self.circuit_breaker.failure_count,
            'last_failure': self.circuit_breaker.last_failure_time.isoformat() if self.circuit_breaker.last_failure_time else None
        }
        
        return {
            'active_sessions': active_sessions,
            'total_sessions_created': self.session_counter,
            'circuit_breaker': circuit_breaker_status,
            'config_summary': {
                'strategy': self.config.strategy.value,
                'max_attempts': self.config.max_attempts,
                'initial_delay_seconds': self.config.initial_delay_seconds,
                'max_delay_seconds': self.config.max_delay_seconds
            }
        }
    
    def reset_circuit_breaker(self):
        """Reset circuit breaker state"""
        
        self.circuit_breaker.state = "CLOSED"
        self.circuit_breaker.failure_count = 0
        self.circuit_breaker.last_failure_time = None
        
        self.logger.info("Circuit breaker manually reset")

def retry(config: Optional[RetryConfig] = None,
         max_attempts: int = 3,
         strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF,
         initial_delay: float = 1.0,
         max_delay: float = 300.0,
         retryable_exceptions: Optional[List[Type[Exception]]] = None):
    """Decorator for automatic retry functionality"""
    
    def decorator(func):
        # Create config if not provided
        if config is None:
            retry_config = RetryConfig(
                max_attempts=max_attempts,
                strategy=strategy,
                initial_delay_seconds=initial_delay,
                max_delay_seconds=max_delay,
                retryable_exceptions=retryable_exceptions or []
            )
        else:
            retry_config = config
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            retry_manager = RetryManager(retry_config)
            return await retry_manager.execute_with_retry(
                func, func.__name__, *args, **kwargs
            )
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Convert to async and run
            return asyncio.run(async_wrapper(*args, **kwargs))
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

class RetryManagerPool:
    """Pool of retry managers for different operations"""
    
    def __init__(self):
        self.managers: Dict[str, RetryManager] = {}
        self.logger = logging.getLogger(f"{__name__}.RetryManagerPool")
    
    def add_manager(self, name: str, config: RetryConfig):
        """Add retry manager to pool"""
        
        self.managers[name] = RetryManager(config)
        self.logger.info(f"Added retry manager: {name}")
    
    def get_manager(self, name: str) -> Optional[RetryManager]:
        """Get retry manager by name"""
        
        return self.managers.get(name)
    
    async def execute_with_manager(self,
                                 manager_name: str,
                                 operation: Callable,
                                 operation_name: str = "unknown",
                                 *args,
                                 **kwargs) -> Any:
        """Execute operation with specific retry manager"""
        
        manager = self.get_manager(manager_name)
        if not manager:
            raise ValueError(f"Unknown retry manager: {manager_name}")
        
        return await manager.execute_with_retry(operation, operation_name, *args, **kwargs)
    
    def get_all_statistics(self) -> Dict[str, Any]:
        """Get statistics for all managers"""
        
        return {
            name: manager.get_session_statistics()
            for name, manager in self.managers.items()
        }
    
    def reset_all_circuit_breakers(self):
        """Reset all circuit breakers"""
        
        for manager in self.managers.values():
            manager.reset_circuit_breaker()
        
        self.logger.info("All circuit breakers reset")