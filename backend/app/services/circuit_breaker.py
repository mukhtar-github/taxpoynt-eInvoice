"""
Circuit Breaker pattern implementation for external API calls.

This module provides circuit breaker functionality to protect against
cascading failures when making external API calls to POS systems.
"""

import asyncio
import time
import logging
from datetime import datetime, timedelta
from typing import Any, Callable, Awaitable, Optional, Type, Union
from enum import Enum

from app.utils.logger import get_logger

logger = get_logger(__name__)


class CircuitBreakerState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"       # Normal operation
    OPEN = "open"           # Failing, rejecting calls
    HALF_OPEN = "half_open" # Testing if service recovered


class CircuitBreakerError(Exception):
    """Raised when circuit breaker is open."""
    pass


class CircuitBreaker:
    """
    Circuit breaker implementation for protecting external API calls.
    
    The circuit breaker prevents cascading failures by:
    - Tracking failure rates
    - Opening when failure threshold is exceeded
    - Allowing limited testing when in half-open state
    - Automatically recovering when service is healthy
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: Type[Exception] = Exception,
        timeout: float = 30.0,
        half_open_max_calls: int = 3
    ):
        """
        Initialize circuit breaker.
        
        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before trying half-open state
            expected_exception: Exception type that triggers circuit breaker
            timeout: Default timeout for calls in seconds
            half_open_max_calls: Max calls allowed in half-open state
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.timeout = timeout
        self.half_open_max_calls = half_open_max_calls
        
        # State tracking
        self._state = CircuitBreakerState.CLOSED
        self._failure_count = 0
        self._last_failure_time: Optional[float] = None
        self._half_open_calls = 0
        
        # Metrics
        self._total_calls = 0
        self._successful_calls = 0
        self._failed_calls = 0
        self._circuit_open_count = 0
        self._last_state_change = time.time()
    
    @property
    def state(self) -> str:
        """Get current circuit breaker state."""
        return self._state.value
    
    @property
    def failure_rate(self) -> float:
        """Get current failure rate percentage."""
        if self._total_calls == 0:
            return 0.0
        return (self._failed_calls / self._total_calls) * 100
    
    @property
    def metrics(self) -> dict:
        """Get circuit breaker metrics."""
        return {
            "state": self._state.value,
            "failure_count": self._failure_count,
            "total_calls": self._total_calls,
            "successful_calls": self._successful_calls,
            "failed_calls": self._failed_calls,
            "failure_rate": self.failure_rate,
            "circuit_open_count": self._circuit_open_count,
            "last_state_change": self._last_state_change,
            "time_since_last_failure": time.time() - self._last_failure_time if self._last_failure_time else None
        }
    
    async def call(
        self,
        func: Callable[..., Awaitable[Any]],
        *args,
        timeout: Optional[float] = None,
        **kwargs
    ) -> Any:
        """
        Call a function with circuit breaker protection.
        
        Args:
            func: Async function to call
            *args: Function arguments
            timeout: Call timeout override
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            CircuitBreakerError: When circuit is open
            TimeoutError: When call times out
            Exception: Original exception from function
        """
        call_timeout = timeout or self.timeout
        
        # Check if circuit breaker should allow the call
        if not self._can_execute():
            raise CircuitBreakerError(
                f"Circuit breaker is {self._state.value}. "
                f"Failure count: {self._failure_count}/{self.failure_threshold}"
            )
        
        self._total_calls += 1
        start_time = time.time()
        
        try:
            # Execute function with timeout
            if asyncio.iscoroutinefunction(func):
                result = await asyncio.wait_for(func(*args, **kwargs), timeout=call_timeout)
            else:
                result = await asyncio.wait_for(
                    asyncio.to_thread(func, *args, **kwargs), 
                    timeout=call_timeout
                )
            
            # Call succeeded
            self._on_success()
            
            execution_time = time.time() - start_time
            logger.debug(
                f"Circuit breaker call succeeded in {execution_time:.3f}s",
                extra={
                    "function": func.__name__,
                    "execution_time": execution_time,
                    "circuit_state": self._state.value
                }
            )
            
            return result
            
        except asyncio.TimeoutError as e:
            # Timeout is treated as failure
            execution_time = time.time() - start_time
            self._on_failure()
            
            logger.warning(
                f"Circuit breaker call timed out after {execution_time:.3f}s",
                extra={
                    "function": func.__name__,
                    "timeout": call_timeout,
                    "circuit_state": self._state.value
                }
            )
            
            raise TimeoutError(f"Call timed out after {call_timeout}s") from e
            
        except self.expected_exception as e:
            # Expected exception triggers circuit breaker
            execution_time = time.time() - start_time
            self._on_failure()
            
            logger.warning(
                f"Circuit breaker call failed: {str(e)}",
                extra={
                    "function": func.__name__,
                    "execution_time": execution_time,
                    "circuit_state": self._state.value,
                    "error": str(e)
                }
            )
            
            raise
            
        except Exception as e:
            # Unexpected exceptions don't trigger circuit breaker
            execution_time = time.time() - start_time
            
            logger.error(
                f"Circuit breaker call failed with unexpected error: {str(e)}",
                extra={
                    "function": func.__name__,
                    "execution_time": execution_time,
                    "circuit_state": self._state.value,
                    "error": str(e)
                }
            )
            
            raise
    
    def _can_execute(self) -> bool:
        """
        Check if circuit breaker allows execution.
        
        Returns:
            True if call can be executed, False otherwise
        """
        current_time = time.time()
        
        if self._state == CircuitBreakerState.CLOSED:
            # Normal operation
            return True
            
        elif self._state == CircuitBreakerState.OPEN:
            # Check if recovery timeout has passed
            if (self._last_failure_time and 
                current_time - self._last_failure_time >= self.recovery_timeout):
                
                # Transition to half-open state
                self._state = CircuitBreakerState.HALF_OPEN
                self._half_open_calls = 0
                self._last_state_change = current_time
                
                logger.info(
                    "Circuit breaker transitioning to half-open state",
                    extra={
                        "failure_count": self._failure_count,
                        "time_since_failure": current_time - self._last_failure_time
                    }
                )
                
                return True
            
            return False
            
        elif self._state == CircuitBreakerState.HALF_OPEN:
            # Allow limited calls in half-open state
            if self._half_open_calls < self.half_open_max_calls:
                self._half_open_calls += 1
                return True
            
            return False
        
        return False
    
    def _on_success(self) -> None:
        """Handle successful call."""
        self._successful_calls += 1
        
        if self._state == CircuitBreakerState.HALF_OPEN:
            # Success in half-open state - check if we can close circuit
            if self._half_open_calls >= self.half_open_max_calls:
                self._close_circuit()
        
        elif self._state == CircuitBreakerState.CLOSED:
            # Reset failure count on success
            if self._failure_count > 0:
                self._failure_count = 0
                logger.debug("Circuit breaker failure count reset after success")
    
    def _on_failure(self) -> None:
        """Handle failed call."""
        self._failed_calls += 1
        self._failure_count += 1
        self._last_failure_time = time.time()
        
        if self._state == CircuitBreakerState.HALF_OPEN:
            # Failure in half-open state - reopen circuit
            self._open_circuit()
            
        elif self._state == CircuitBreakerState.CLOSED:
            # Check if failure threshold exceeded
            if self._failure_count >= self.failure_threshold:
                self._open_circuit()
    
    def _open_circuit(self) -> None:
        """Open the circuit breaker."""
        if self._state != CircuitBreakerState.OPEN:
            self._state = CircuitBreakerState.OPEN
            self._circuit_open_count += 1
            self._last_state_change = time.time()
            
            logger.warning(
                "Circuit breaker opened due to failures",
                extra={
                    "failure_count": self._failure_count,
                    "failure_threshold": self.failure_threshold,
                    "total_calls": self._total_calls,
                    "failure_rate": self.failure_rate
                }
            )
    
    def _close_circuit(self) -> None:
        """Close the circuit breaker."""
        if self._state != CircuitBreakerState.CLOSED:
            self._state = CircuitBreakerState.CLOSED
            self._failure_count = 0
            self._half_open_calls = 0
            self._last_state_change = time.time()
            
            logger.info(
                "Circuit breaker closed - service recovered",
                extra={
                    "total_calls": self._total_calls,
                    "successful_calls": self._successful_calls,
                    "failure_rate": self.failure_rate
                }
            )
    
    def reset(self) -> None:
        """
        Manually reset circuit breaker to closed state.
        This should be used carefully and typically only for testing.
        """
        self._state = CircuitBreakerState.CLOSED
        self._failure_count = 0
        self._half_open_calls = 0
        self._last_failure_time = None
        self._last_state_change = time.time()
        
        logger.info("Circuit breaker manually reset")
    
    def force_open(self) -> None:
        """
        Manually force circuit breaker to open state.
        Useful for maintenance or when external service is known to be down.
        """
        self._open_circuit()
        logger.info("Circuit breaker manually forced open")


class TimedCircuitBreaker(CircuitBreaker):
    """
    Circuit breaker with time-window based failure tracking.
    
    This variant tracks failures within a rolling time window rather than
    just consecutive failures.
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        time_window: int = 60,
        recovery_timeout: int = 60,
        expected_exception: Type[Exception] = Exception,
        timeout: float = 30.0,
        half_open_max_calls: int = 3
    ):
        """
        Initialize timed circuit breaker.
        
        Args:
            failure_threshold: Number of failures in time window before opening
            time_window: Time window in seconds for tracking failures
            recovery_timeout: Seconds to wait before trying half-open state
            expected_exception: Exception type that triggers circuit breaker
            timeout: Default timeout for calls in seconds
            half_open_max_calls: Max calls allowed in half-open state
        """
        super().__init__(failure_threshold, recovery_timeout, expected_exception, timeout, half_open_max_calls)
        self.time_window = time_window
        self._failure_times: list[float] = []
    
    def _on_failure(self) -> None:
        """Handle failed call with time window tracking."""
        self._failed_calls += 1
        current_time = time.time()
        self._failure_times.append(current_time)
        self._last_failure_time = current_time
        
        # Remove failures outside time window
        cutoff_time = current_time - self.time_window
        self._failure_times = [t for t in self._failure_times if t > cutoff_time]
        
        # Update failure count to reflect current window
        self._failure_count = len(self._failure_times)
        
        if self._state == CircuitBreakerState.HALF_OPEN:
            # Failure in half-open state - reopen circuit
            self._open_circuit()
            
        elif self._state == CircuitBreakerState.CLOSED:
            # Check if failure threshold exceeded in time window
            if self._failure_count >= self.failure_threshold:
                self._open_circuit()
    
    def _on_success(self) -> None:
        """Handle successful call with time window consideration."""
        self._successful_calls += 1
        
        if self._state == CircuitBreakerState.HALF_OPEN:
            # Success in half-open state - check if we can close circuit
            if self._half_open_calls >= self.half_open_max_calls:
                self._close_circuit()
        
        # Note: We don't reset failure count on success for timed circuit breaker
        # Failures naturally age out of the time window