"""
FIRS Hybrid Circuit Breaker Service for TaxPoynt eInvoice - Hybrid SI+APP Functions.

This module provides Hybrid FIRS functionality for comprehensive circuit breaker protection
that combines System Integrator (SI) and Access Point Provider (APP) operations for unified
failure protection and resilience in FIRS e-invoicing workflows.

Hybrid FIRS Responsibilities:
- Cross-role circuit breaker protection for both SI integration and APP transmission failures
- Unified failure tracking and threshold management for SI and APP operations
- Hybrid circuit breaker coordination for comprehensive FIRS workflow protection
- Shared resilience patterns covering both SI ERP connections and APP FIRS API calls
- Cross-functional failure recovery and service restoration for SI and APP operations
"""

import asyncio
import time
import logging
from datetime import datetime, timedelta
from typing import Any, Callable, Awaitable, Optional, Type, Union, Dict, List
from enum import Enum
from uuid import uuid4
from dataclasses import dataclass, field

from app.utils.logger import get_logger
from app.core.config import settings

logger = get_logger(__name__)

# Hybrid FIRS circuit breaker configuration
HYBRID_CIRCUIT_BREAKER_VERSION = "1.0"
DEFAULT_SI_FAILURE_THRESHOLD = 5
DEFAULT_APP_FAILURE_THRESHOLD = 3
DEFAULT_HYBRID_FAILURE_THRESHOLD = 7
FIRS_COMPLIANCE_CIRCUIT_THRESHOLD = 2
CIRCUIT_BREAKER_METRICS_CACHE_DURATION = 300  # 5 minutes


class HybridCircuitBreakerState(Enum):
    """Enhanced circuit breaker states for hybrid SI+APP operations."""
    CLOSED = "closed"                    # Normal operation
    OPEN = "open"                       # Failing, rejecting calls
    HALF_OPEN = "half_open"             # Testing if service recovered
    
    # Hybrid-specific states
    SI_DEGRADED = "si_degraded"         # SI operations limited
    APP_DEGRADED = "app_degraded"       # APP operations limited
    HYBRID_DEGRADED = "hybrid_degraded" # Cross-role operations limited
    FIRS_ISOLATED = "firs_isolated"     # FIRS compliance issues
    MAINTENANCE = "maintenance"         # Manual maintenance mode


class HybridCircuitBreakerError(Exception):
    """Enhanced exception for hybrid circuit breaker failures."""
    def __init__(
        self, 
        message: str, 
        state: HybridCircuitBreakerState,
        si_context: Optional[Dict[str, Any]] = None,
        app_context: Optional[Dict[str, Any]] = None,
        hybrid_context: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.state = state
        self.si_context = si_context or {}
        self.app_context = app_context or {}
        self.hybrid_context = hybrid_context or {}
        super().__init__(message)


@dataclass
class HybridCircuitBreakerMetrics:
    """Comprehensive metrics for hybrid circuit breaker operations."""
    # Basic metrics
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    circuit_open_count: int = 0
    
    # Hybrid-specific metrics
    si_calls: int = 0
    si_failures: int = 0
    app_calls: int = 0
    app_failures: int = 0
    hybrid_calls: int = 0
    hybrid_failures: int = 0
    
    # FIRS compliance metrics
    firs_compliance_failures: int = 0
    firs_api_failures: int = 0
    erp_integration_failures: int = 0
    certificate_failures: int = 0
    transmission_failures: int = 0
    
    # Timing metrics
    average_response_time: float = 0.0
    max_response_time: float = 0.0
    min_response_time: float = float('inf')
    
    # State tracking
    state_changes: List[Dict[str, Any]] = field(default_factory=list)
    last_state_change: float = field(default_factory=time.time)
    last_failure_time: Optional[float] = None
    
    # Analytics
    failure_rate_si: float = 0.0
    failure_rate_app: float = 0.0
    failure_rate_hybrid: float = 0.0
    uptime_percentage: float = 100.0
    
    def calculate_rates(self):
        """Calculate failure rates and metrics."""
        # SI failure rate
        if self.si_calls > 0:
            self.failure_rate_si = (self.si_failures / self.si_calls) * 100
        
        # APP failure rate
        if self.app_calls > 0:
            self.failure_rate_app = (self.app_failures / self.app_calls) * 100
        
        # Hybrid failure rate
        if self.hybrid_calls > 0:
            self.failure_rate_hybrid = (self.hybrid_failures / self.hybrid_calls) * 100
        
        # Overall uptime
        if self.total_calls > 0:
            self.uptime_percentage = (self.successful_calls / self.total_calls) * 100


class HybridFIRSCircuitBreaker:
    """
    Hybrid FIRS circuit breaker for comprehensive failure protection.
    
    This service provides Hybrid FIRS functions for circuit breaker protection
    that combine System Integrator (SI) and Access Point Provider (APP) operations
    for unified failure protection and resilience in Nigerian e-invoicing compliance.
    
    Hybrid Circuit Breaker Functions:
    1. Cross-role circuit breaker protection for both SI integration and APP transmission failures
    2. Unified failure tracking and threshold management for SI and APP operations
    3. Hybrid circuit breaker coordination for comprehensive FIRS workflow protection
    4. Shared resilience patterns covering both SI ERP connections and APP FIRS API calls
    5. Cross-functional failure recovery and service restoration for SI and APP operations
    """
    
    def __init__(
        self,
        name: str = "hybrid_firs_circuit_breaker",
        si_failure_threshold: int = DEFAULT_SI_FAILURE_THRESHOLD,
        app_failure_threshold: int = DEFAULT_APP_FAILURE_THRESHOLD,
        hybrid_failure_threshold: int = DEFAULT_HYBRID_FAILURE_THRESHOLD,
        firs_compliance_threshold: int = FIRS_COMPLIANCE_CIRCUIT_THRESHOLD,
        recovery_timeout: int = 60,
        expected_exception: Type[Exception] = Exception,
        timeout: float = 30.0,
        half_open_max_calls: int = 3,
        time_window: int = 300,  # 5 minutes
        enable_firs_monitoring: bool = True
    ):
        """
        Initialize the Hybrid FIRS circuit breaker with enhanced capabilities.
        
        Args:
            name: Circuit breaker identifier
            si_failure_threshold: Failure threshold for SI operations
            app_failure_threshold: Failure threshold for APP operations
            hybrid_failure_threshold: Failure threshold for hybrid operations
            firs_compliance_threshold: FIRS compliance failure threshold
            recovery_timeout: Seconds to wait before trying half-open state
            expected_exception: Exception type that triggers circuit breaker
            timeout: Default timeout for calls in seconds
            half_open_max_calls: Max calls allowed in half-open state
            time_window: Time window for failure tracking (seconds)
            enable_firs_monitoring: Whether to enable FIRS-specific monitoring
        """
        self.name = name
        self.si_failure_threshold = si_failure_threshold
        self.app_failure_threshold = app_failure_threshold
        self.hybrid_failure_threshold = hybrid_failure_threshold
        self.firs_compliance_threshold = firs_compliance_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.timeout = timeout
        self.half_open_max_calls = half_open_max_calls
        self.time_window = time_window
        self.enable_firs_monitoring = enable_firs_monitoring
        
        # State management
        self._state = HybridCircuitBreakerState.CLOSED
        self._half_open_calls = 0
        
        # Enhanced metrics
        self.metrics = HybridCircuitBreakerMetrics()
        
        # Failure tracking
        self._si_failure_times: List[float] = []
        self._app_failure_times: List[float] = []
        self._hybrid_failure_times: List[float] = []
        self._firs_failure_times: List[float] = []
        
        # Context tracking
        self.si_context = {}
        self.app_context = {}
        self.hybrid_context = {}
        self.firs_context = {}
        
        # Analytics
        self.failure_patterns = {}
        self.performance_history = []
        self.alert_history = []
        
        logger.info(f"Hybrid FIRS Circuit Breaker '{self.name}' initialized (Version: {HYBRID_CIRCUIT_BREAKER_VERSION})")
    
    @property
    def state(self) -> str:
        """Get current circuit breaker state."""
        return self._state.value
    
    @property
    def is_open(self) -> bool:
        """Check if circuit breaker is in open state."""
        return self._state == HybridCircuitBreakerState.OPEN
    
    @property
    def is_closed(self) -> bool:
        """Check if circuit breaker is in closed state."""
        return self._state == HybridCircuitBreakerState.CLOSED
    
    @property
    def is_half_open(self) -> bool:
        """Check if circuit breaker is in half-open state."""
        return self._state == HybridCircuitBreakerState.HALF_OPEN
    
    def get_enhanced_metrics(self) -> Dict[str, Any]:
        """
        Get comprehensive circuit breaker metrics - Hybrid FIRS Function.
        
        Provides detailed metrics for both SI and APP operations with
        FIRS compliance monitoring and hybrid analytics.
        
        Returns:
            Dict containing comprehensive circuit breaker metrics
        """
        self.metrics.calculate_rates()
        
        current_time = time.time()
        
        # Clean old failure times
        self._clean_old_failures(current_time)
        
        enhanced_metrics = {
            "circuit_breaker_name": self.name,
            "state": self._state.value,
            "hybrid_version": HYBRID_CIRCUIT_BREAKER_VERSION,
            
            # Basic metrics
            "total_calls": self.metrics.total_calls,
            "successful_calls": self.metrics.successful_calls,
            "failed_calls": self.metrics.failed_calls,
            "success_rate": (self.metrics.successful_calls / self.metrics.total_calls * 100) if self.metrics.total_calls > 0 else 0,
            
            # Hybrid-specific metrics
            "si_metrics": {
                "calls": self.metrics.si_calls,
                "failures": self.metrics.si_failures,
                "failure_rate": self.metrics.failure_rate_si,
                "current_failures_in_window": len(self._si_failure_times)
            },
            "app_metrics": {
                "calls": self.metrics.app_calls,
                "failures": self.metrics.app_failures,
                "failure_rate": self.metrics.failure_rate_app,
                "current_failures_in_window": len(self._app_failure_times)
            },
            "hybrid_metrics": {
                "calls": self.metrics.hybrid_calls,
                "failures": self.metrics.hybrid_failures,
                "failure_rate": self.metrics.failure_rate_hybrid,
                "current_failures_in_window": len(self._hybrid_failure_times)
            },
            
            # FIRS compliance metrics
            "firs_metrics": {
                "compliance_failures": self.metrics.firs_compliance_failures,
                "api_failures": self.metrics.firs_api_failures,
                "erp_failures": self.metrics.erp_integration_failures,
                "certificate_failures": self.metrics.certificate_failures,
                "transmission_failures": self.metrics.transmission_failures,
                "firs_failures_in_window": len(self._firs_failure_times)
            },
            
            # Performance metrics
            "performance": {
                "average_response_time": self.metrics.average_response_time,
                "max_response_time": self.metrics.max_response_time,
                "min_response_time": self.metrics.min_response_time if self.metrics.min_response_time != float('inf') else 0,
                "uptime_percentage": self.metrics.uptime_percentage
            },
            
            # Threshold information
            "thresholds": {
                "si_failure_threshold": self.si_failure_threshold,
                "app_failure_threshold": self.app_failure_threshold,
                "hybrid_failure_threshold": self.hybrid_failure_threshold,
                "firs_compliance_threshold": self.firs_compliance_threshold
            },
            
            # State information
            "state_info": {
                "circuit_open_count": self.metrics.circuit_open_count,
                "last_state_change": self.metrics.last_state_change,
                "time_since_last_failure": current_time - self.metrics.last_failure_time if self.metrics.last_failure_time else None,
                "half_open_calls": self._half_open_calls,
                "max_half_open_calls": self.half_open_max_calls
            },
            
            # Analytics
            "analytics": {
                "failure_patterns": dict(self.failure_patterns),
                "recent_alerts": self.alert_history[-10:] if self.alert_history else [],
                "state_changes": self.metrics.state_changes[-5:] if self.metrics.state_changes else []
            },
            
            "timestamp": current_time,
            "firs_monitoring_enabled": self.enable_firs_monitoring
        }
        
        return enhanced_metrics

    async def call_with_hybrid_protection(
        self,
        func: Callable[..., Awaitable[Any]],
        *args,
        operation_type: str = "hybrid",
        si_context: Optional[Dict[str, Any]] = None,
        app_context: Optional[Dict[str, Any]] = None,
        hybrid_context: Optional[Dict[str, Any]] = None,
        firs_context: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None,
        **kwargs
    ) -> Any:
        """
        Execute function with hybrid circuit breaker protection - Hybrid FIRS Function.
        
        Provides comprehensive circuit breaker protection that considers both SI and APP
        operations with enhanced FIRS compliance monitoring.
        
        Args:
            func: Async function to call
            *args: Function arguments
            operation_type: Type of operation ("si", "app", "hybrid", "firs")
            si_context: SI-specific context
            app_context: APP-specific context
            hybrid_context: Hybrid operation context
            firs_context: FIRS-specific context
            timeout: Call timeout override
            **kwargs: Function keyword arguments
            
        Returns:
            Function result with enhanced error handling
            
        Raises:
            HybridCircuitBreakerError: When circuit is open
            TimeoutError: When call times out
            Exception: Original exception from function
        """
        call_id = str(uuid4())
        call_timeout = timeout or self.timeout
        start_time = time.time()
        
        # Enhanced context preparation
        enhanced_context = {
            "call_id": call_id,
            "operation_type": operation_type,
            "si_context": si_context or {},
            "app_context": app_context or {},
            "hybrid_context": hybrid_context or {},
            "firs_context": firs_context or {},
            "timestamp": start_time,
            "timeout": call_timeout
        }
        
        # Check if circuit breaker allows the call
        if not self._can_execute_hybrid(operation_type, enhanced_context):
            error_message = f"Hybrid Circuit Breaker '{self.name}' is {self._state.value} for {operation_type} operations"
            
            self._log_circuit_breaker_rejection(operation_type, enhanced_context, error_message)
            
            raise HybridCircuitBreakerError(
                error_message,
                self._state,
                si_context=si_context,
                app_context=app_context,
                hybrid_context=hybrid_context
            )
        
        # Track call initiation
        self._track_call_initiation(operation_type, enhanced_context)
        
        try:
            # Execute function with timeout and monitoring
            if asyncio.iscoroutinefunction(func):
                result = await asyncio.wait_for(func(*args, **kwargs), timeout=call_timeout)
            else:
                result = await asyncio.wait_for(
                    asyncio.to_thread(func, *args, **kwargs), 
                    timeout=call_timeout
                )
            
            # Handle successful call
            execution_time = time.time() - start_time
            self._on_hybrid_success(operation_type, enhanced_context, execution_time)
            
            logger.debug(
                f"Hybrid Circuit Breaker call succeeded ({operation_type})",
                extra={
                    "call_id": call_id,
                    "function": func.__name__,
                    "operation_type": operation_type,
                    "execution_time": execution_time,
                    "circuit_state": self._state.value,
                    "si_context": si_context,
                    "app_context": app_context
                }
            )
            
            return result
            
        except asyncio.TimeoutError as e:
            # Handle timeout
            execution_time = time.time() - start_time
            self._on_hybrid_failure(operation_type, "timeout", enhanced_context, execution_time, str(e))
            
            logger.warning(
                f"Hybrid Circuit Breaker call timed out ({operation_type})",
                extra={
                    "call_id": call_id,
                    "function": func.__name__,
                    "operation_type": operation_type,
                    "timeout": call_timeout,
                    "execution_time": execution_time,
                    "circuit_state": self._state.value
                }
            )
            
            raise TimeoutError(f"Hybrid call timed out after {call_timeout}s") from e
            
        except self.expected_exception as e:
            # Handle expected failure
            execution_time = time.time() - start_time
            self._on_hybrid_failure(operation_type, "expected_exception", enhanced_context, execution_time, str(e))
            
            logger.warning(
                f"Hybrid Circuit Breaker call failed ({operation_type}): {str(e)}",
                extra={
                    "call_id": call_id,
                    "function": func.__name__,
                    "operation_type": operation_type,
                    "execution_time": execution_time,
                    "circuit_state": self._state.value,
                    "error": str(e),
                    "error_type": e.__class__.__name__
                }
            )
            
            raise
            
        except Exception as e:
            # Handle unexpected exception
            execution_time = time.time() - start_time
            self._on_hybrid_failure(operation_type, "unexpected_exception", enhanced_context, execution_time, str(e))
            
            logger.error(
                f"Hybrid Circuit Breaker call failed with unexpected error ({operation_type}): {str(e)}",
                extra={
                    "call_id": call_id,
                    "function": func.__name__,
                    "operation_type": operation_type,
                    "execution_time": execution_time,
                    "circuit_state": self._state.value,
                    "error": str(e),
                    "error_type": e.__class__.__name__
                }
            )
            
            raise

    def _can_execute_hybrid(self, operation_type: str, context: Dict[str, Any]) -> bool:
        """
        Check if hybrid circuit breaker allows execution - Hybrid FIRS Function.
        
        Provides enhanced execution permission logic that considers both SI and APP
        operations with FIRS compliance requirements.
        
        Args:
            operation_type: Type of operation
            context: Enhanced operation context
            
        Returns:
            True if call can be executed, False otherwise
        """
        current_time = time.time()
        
        # Clean old failures
        self._clean_old_failures(current_time)
        
        # Check global circuit state
        if self._state == HybridCircuitBreakerState.CLOSED:
            return True
        
        elif self._state == HybridCircuitBreakerState.OPEN:
            # Check recovery timeout
            if (self.metrics.last_failure_time and 
                current_time - self.metrics.last_failure_time >= self.recovery_timeout):
                
                self._transition_to_half_open(current_time, "recovery_timeout_reached")
                return True
            
            return False
        
        elif self._state == HybridCircuitBreakerState.HALF_OPEN:
            if self._half_open_calls < self.half_open_max_calls:
                self._half_open_calls += 1
                return True
            return False
        
        elif self._state in [HybridCircuitBreakerState.SI_DEGRADED, 
                           HybridCircuitBreakerState.APP_DEGRADED, 
                           HybridCircuitBreakerState.HYBRID_DEGRADED]:
            # Allow calls but with degraded performance expectations
            return self._check_degraded_mode_permission(operation_type, context)
        
        elif self._state == HybridCircuitBreakerState.FIRS_ISOLATED:
            # Only allow non-FIRS operations
            return not self._is_firs_operation(context)
        
        elif self._state == HybridCircuitBreakerState.MAINTENANCE:
            # No calls allowed during maintenance
            return False
        
        return False

    def _check_degraded_mode_permission(self, operation_type: str, context: Dict[str, Any]) -> bool:
        """Check if operation is allowed in degraded mode."""
        if self._state == HybridCircuitBreakerState.SI_DEGRADED and operation_type == "si":
            return False
        elif self._state == HybridCircuitBreakerState.APP_DEGRADED and operation_type == "app":
            return False
        elif self._state == HybridCircuitBreakerState.HYBRID_DEGRADED and operation_type == "hybrid":
            return False
        
        return True

    def _is_firs_operation(self, context: Dict[str, Any]) -> bool:
        """Check if operation involves FIRS compliance."""
        firs_indicators = [
            "firs_api", "transmission", "submission", "certificate", 
            "irn", "validation", "compliance"
        ]
        
        firs_context = context.get("firs_context", {})
        if firs_context:
            return True
        
        # Check other contexts for FIRS-related operations
        all_context = {
            **context.get("si_context", {}),
            **context.get("app_context", {}),
            **context.get("hybrid_context", {})
        }
        
        for key, value in all_context.items():
            if any(indicator in str(key).lower() or indicator in str(value).lower() 
                   for indicator in firs_indicators):
                return True
        
        return False

    def _track_call_initiation(self, operation_type: str, context: Dict[str, Any]) -> None:
        """Track call initiation for metrics."""
        self.metrics.total_calls += 1
        
        if operation_type == "si":
            self.metrics.si_calls += 1
        elif operation_type == "app":
            self.metrics.app_calls += 1
        elif operation_type == "hybrid":
            self.metrics.hybrid_calls += 1

    def _on_hybrid_success(self, operation_type: str, context: Dict[str, Any], execution_time: float) -> None:
        """
        Handle successful hybrid call - Hybrid FIRS Function.
        
        Processes successful calls with enhanced SI+APP context tracking
        and FIRS compliance monitoring.
        """
        self.metrics.successful_calls += 1
        
        # Update performance metrics
        self._update_performance_metrics(execution_time)
        
        # Handle state transitions on success
        if self._state == HybridCircuitBreakerState.HALF_OPEN:
            if self._half_open_calls >= self.half_open_max_calls:
                self._close_circuit("half_open_success_threshold_reached")
        
        elif self._state in [HybridCircuitBreakerState.SI_DEGRADED, 
                           HybridCircuitBreakerState.APP_DEGRADED, 
                           HybridCircuitBreakerState.HYBRID_DEGRADED]:
            # Check if we can recover from degraded state
            self._check_degraded_recovery(operation_type)
        
        # Track success patterns
        self._track_success_pattern(operation_type, context, execution_time)

    def _on_hybrid_failure(self, operation_type: str, failure_type: str, context: Dict[str, Any], execution_time: float, error_message: str) -> None:
        """
        Handle hybrid call failure - Hybrid FIRS Function.
        
        Processes failures with enhanced SI+APP context tracking
        and FIRS compliance impact assessment.
        """
        current_time = time.time()
        
        self.metrics.failed_calls += 1
        self.metrics.last_failure_time = current_time
        
        # Track by operation type
        if operation_type == "si":
            self.metrics.si_failures += 1
            self._si_failure_times.append(current_time)
        elif operation_type == "app":
            self.metrics.app_failures += 1
            self._app_failure_times.append(current_time)
        elif operation_type == "hybrid":
            self.metrics.hybrid_failures += 1
            self._hybrid_failure_times.append(current_time)
        
        # Track FIRS-specific failures
        if self._is_firs_operation(context):
            self.metrics.firs_compliance_failures += 1
            self._firs_failure_times.append(current_time)
            
            # Categorize FIRS failures
            if "api" in error_message.lower() or "firs" in error_message.lower():
                self.metrics.firs_api_failures += 1
            elif "certificate" in error_message.lower():
                self.metrics.certificate_failures += 1
            elif "transmission" in error_message.lower():
                self.metrics.transmission_failures += 1
            elif "integration" in error_message.lower() or "erp" in error_message.lower():
                self.metrics.erp_integration_failures += 1
        
        # Update performance metrics
        self._update_performance_metrics(execution_time)
        
        # Track failure patterns
        self._track_failure_pattern(operation_type, failure_type, context, error_message)
        
        # Check state transitions
        self._check_failure_state_transitions(operation_type, current_time)

    def _check_failure_state_transitions(self, operation_type: str, current_time: float) -> None:
        """Check if failures warrant state transitions."""
        if self._state == HybridCircuitBreakerState.HALF_OPEN:
            # Any failure in half-open reopens circuit
            self._open_circuit("half_open_failure")
            return
        
        if self._state == HybridCircuitBreakerState.CLOSED:
            # Check thresholds for opening circuit
            si_failures = len(self._si_failure_times)
            app_failures = len(self._app_failure_times)
            hybrid_failures = len(self._hybrid_failure_times)
            firs_failures = len(self._firs_failure_times)
            
            # FIRS compliance threshold (highest priority)
            if self.enable_firs_monitoring and firs_failures >= self.firs_compliance_threshold:
                self._transition_to_firs_isolated("firs_compliance_threshold_exceeded")
            
            # Operation-specific thresholds
            elif si_failures >= self.si_failure_threshold:
                self._transition_to_degraded("si", "si_failure_threshold_exceeded")
            elif app_failures >= self.app_failure_threshold:
                self._transition_to_degraded("app", "app_failure_threshold_exceeded")
            elif hybrid_failures >= self.hybrid_failure_threshold:
                self._transition_to_degraded("hybrid", "hybrid_failure_threshold_exceeded")
            
            # Overall failure threshold
            elif (si_failures + app_failures + hybrid_failures) >= max(self.si_failure_threshold, self.app_failure_threshold, self.hybrid_failure_threshold):
                self._open_circuit("overall_failure_threshold_exceeded")

    def _update_performance_metrics(self, execution_time: float) -> None:
        """Update performance metrics with execution time."""
        if execution_time > self.metrics.max_response_time:
            self.metrics.max_response_time = execution_time
        
        if execution_time < self.metrics.min_response_time:
            self.metrics.min_response_time = execution_time
        
        # Update average (simple moving average)
        if self.metrics.total_calls > 1:
            self.metrics.average_response_time = (
                (self.metrics.average_response_time * (self.metrics.total_calls - 1) + execution_time) 
                / self.metrics.total_calls
            )
        else:
            self.metrics.average_response_time = execution_time

    def _track_failure_pattern(self, operation_type: str, failure_type: str, context: Dict[str, Any], error_message: str) -> None:
        """Track failure patterns for analysis."""
        pattern_key = f"{operation_type}_{failure_type}"
        
        if pattern_key not in self.failure_patterns:
            self.failure_patterns[pattern_key] = {
                "count": 0,
                "first_occurrence": time.time(),
                "last_occurrence": None,
                "error_samples": []
            }
        
        pattern = self.failure_patterns[pattern_key]
        pattern["count"] += 1
        pattern["last_occurrence"] = time.time()
        
        # Keep sample of recent errors
        if len(pattern["error_samples"]) < 5:
            pattern["error_samples"].append({
                "timestamp": time.time(),
                "message": error_message[:200],  # Truncate long messages
                "context": str(context)[:500]
            })

    def _track_success_pattern(self, operation_type: str, context: Dict[str, Any], execution_time: float) -> None:
        """Track success patterns for analysis."""
        # Keep performance history
        if len(self.performance_history) >= 100:
            self.performance_history.pop(0)
        
        self.performance_history.append({
            "timestamp": time.time(),
            "operation_type": operation_type,
            "execution_time": execution_time,
            "state": self._state.value
        })

    def _clean_old_failures(self, current_time: float) -> None:
        """Remove failures outside the time window."""
        cutoff_time = current_time - self.time_window
        
        self._si_failure_times = [t for t in self._si_failure_times if t > cutoff_time]
        self._app_failure_times = [t for t in self._app_failure_times if t > cutoff_time]
        self._hybrid_failure_times = [t for t in self._hybrid_failure_times if t > cutoff_time]
        self._firs_failure_times = [t for t in self._firs_failure_times if t > cutoff_time]

    def _transition_to_half_open(self, current_time: float, reason: str) -> None:
        """Transition to half-open state."""
        self._change_state(HybridCircuitBreakerState.HALF_OPEN, reason)
        self._half_open_calls = 0

    def _transition_to_degraded(self, operation_type: str, reason: str) -> None:
        """Transition to operation-specific degraded state."""
        if operation_type == "si":
            self._change_state(HybridCircuitBreakerState.SI_DEGRADED, reason)
        elif operation_type == "app":
            self._change_state(HybridCircuitBreakerState.APP_DEGRADED, reason)
        elif operation_type == "hybrid":
            self._change_state(HybridCircuitBreakerState.HYBRID_DEGRADED, reason)

    def _transition_to_firs_isolated(self, reason: str) -> None:
        """Transition to FIRS isolated state."""
        self._change_state(HybridCircuitBreakerState.FIRS_ISOLATED, reason)

    def _open_circuit(self, reason: str) -> None:
        """Open the circuit breaker."""
        if self._state != HybridCircuitBreakerState.OPEN:
            self.metrics.circuit_open_count += 1
            self._change_state(HybridCircuitBreakerState.OPEN, reason)

    def _close_circuit(self, reason: str) -> None:
        """Close the circuit breaker."""
        if self._state != HybridCircuitBreakerState.CLOSED:
            self._half_open_calls = 0
            self._change_state(HybridCircuitBreakerState.CLOSED, reason)

    def _change_state(self, new_state: HybridCircuitBreakerState, reason: str) -> None:
        """Change circuit breaker state with logging."""
        old_state = self._state
        self._state = new_state
        current_time = time.time()
        self.metrics.last_state_change = current_time
        
        # Record state change
        state_change = {
            "timestamp": current_time,
            "from_state": old_state.value,
            "to_state": new_state.value,
            "reason": reason,
            "metrics_snapshot": {
                "total_calls": self.metrics.total_calls,
                "failed_calls": self.metrics.failed_calls,
                "si_failures": len(self._si_failure_times),
                "app_failures": len(self._app_failure_times),
                "hybrid_failures": len(self._hybrid_failure_times),
                "firs_failures": len(self._firs_failure_times)
            }
        }
        
        self.metrics.state_changes.append(state_change)
        
        # Keep only recent state changes
        if len(self.metrics.state_changes) > 20:
            self.metrics.state_changes = self.metrics.state_changes[-20:]
        
        # Log state change
        logger.warning(
            f"Hybrid Circuit Breaker '{self.name}' state changed: {old_state.value} -> {new_state.value}",
            extra={
                "reason": reason,
                "circuit_breaker": self.name,
                "old_state": old_state.value,
                "new_state": new_state.value,
                "metrics": state_change["metrics_snapshot"]
            }
        )
        
        # Create alert
        self._create_alert(f"State changed from {old_state.value} to {new_state.value}", reason, "state_change")

    def _create_alert(self, message: str, reason: str, alert_type: str) -> None:
        """Create an alert for important events."""
        alert = {
            "timestamp": time.time(),
            "type": alert_type,
            "message": message,
            "reason": reason,
            "state": self._state.value,
            "circuit_breaker": self.name
        }
        
        self.alert_history.append(alert)
        
        # Keep only recent alerts
        if len(self.alert_history) > 50:
            self.alert_history = self.alert_history[-50:]

    def _check_degraded_recovery(self, operation_type: str) -> None:
        """Check if we can recover from degraded state."""
        # Simple recovery logic - could be enhanced
        current_time = time.time()
        
        # If no failures in the last recovery_timeout period, consider recovery
        if self.metrics.last_failure_time and (current_time - self.metrics.last_failure_time) >= self.recovery_timeout:
            if self._state in [HybridCircuitBreakerState.SI_DEGRADED, 
                             HybridCircuitBreakerState.APP_DEGRADED, 
                             HybridCircuitBreakerState.HYBRID_DEGRADED]:
                self._close_circuit("degraded_state_recovery")

    def _log_circuit_breaker_rejection(self, operation_type: str, context: Dict[str, Any], error_message: str) -> None:
        """Log circuit breaker rejection with context."""
        logger.warning(
            f"Hybrid Circuit Breaker rejected {operation_type} call: {error_message}",
            extra={
                "circuit_breaker": self.name,
                "operation_type": operation_type,
                "state": self._state.value,
                "context": context,
                "rejection_reason": error_message
            }
        )

    def reset_hybrid_circuit(self) -> None:
        """
        Reset hybrid circuit breaker to closed state - Hybrid FIRS Function.
        
        Provides manual reset capability with enhanced logging and context clearing.
        This should be used carefully and typically only for testing or manual recovery.
        """
        old_state = self._state
        
        # Reset state
        self._state = HybridCircuitBreakerState.CLOSED
        self._half_open_calls = 0
        
        # Clear failure tracking
        self._si_failure_times.clear()
        self._app_failure_times.clear()
        self._hybrid_failure_times.clear()
        self._firs_failure_times.clear()
        
        # Reset some metrics but keep historical data
        self.metrics.last_failure_time = None
        self.metrics.last_state_change = time.time()
        
        # Log reset
        logger.info(
            f"Hybrid Circuit Breaker '{self.name}' manually reset from {old_state.value} to CLOSED",
            extra={
                "circuit_breaker": self.name,
                "previous_state": old_state.value,
                "reset_timestamp": time.time()
            }
        )
        
        self._create_alert("Circuit breaker manually reset", "manual_reset", "reset")

    def force_maintenance_mode(self) -> None:
        """
        Force circuit breaker into maintenance mode - Hybrid FIRS Function.
        
        Useful for planned maintenance or when external services are known to be down.
        """
        self._change_state(HybridCircuitBreakerState.MAINTENANCE, "manual_maintenance_mode")
        logger.info(f"Hybrid Circuit Breaker '{self.name}' forced into maintenance mode")

    def exit_maintenance_mode(self) -> None:
        """
        Exit maintenance mode and return to normal operation - Hybrid FIRS Function.
        """
        if self._state == HybridCircuitBreakerState.MAINTENANCE:
            self._close_circuit("maintenance_mode_exit")
            logger.info(f"Hybrid Circuit Breaker '{self.name}' exited maintenance mode")


# Legacy compatibility classes
class CircuitBreaker(HybridFIRSCircuitBreaker):
    """Legacy CircuitBreaker class for backward compatibility."""
    
    def __init__(self, *args, **kwargs):
        # Map old parameters to new ones
        name = kwargs.pop('name', 'legacy_circuit_breaker')
        failure_threshold = kwargs.pop('failure_threshold', 5)
        
        super().__init__(
            name=name,
            si_failure_threshold=failure_threshold,
            app_failure_threshold=failure_threshold,
            hybrid_failure_threshold=failure_threshold,
            *args,
            **kwargs
        )
    
    async def call(self, func, *args, timeout=None, **kwargs):
        """Legacy call method."""
        return await self.call_with_hybrid_protection(
            func, 
            *args, 
            operation_type="legacy",
            timeout=timeout,
            **kwargs
        )
    
    def reset(self):
        """Legacy reset method."""
        self.reset_hybrid_circuit()
    
    def force_open(self):
        """Legacy force open method."""
        self._open_circuit("manual_force_open")


class TimedCircuitBreaker(HybridFIRSCircuitBreaker):
    """Legacy TimedCircuitBreaker class for backward compatibility."""
    
    def __init__(self, time_window=60, *args, **kwargs):
        super().__init__(time_window=time_window, *args, **kwargs)


class CircuitBreakerState(Enum):
    """Legacy state enum for backward compatibility."""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreakerError(HybridCircuitBreakerError):
    """Legacy error class for backward compatibility."""
    
    def __init__(self, message: str):
        super().__init__(message, HybridCircuitBreakerState.OPEN)