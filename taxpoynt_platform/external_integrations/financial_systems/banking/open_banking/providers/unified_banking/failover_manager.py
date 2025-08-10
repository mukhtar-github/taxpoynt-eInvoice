"""
Failover Manager for Provider Reliability
=========================================
Advanced failover management system for banking provider operations.
Provides automatic failover, circuit breaker patterns, and recovery
mechanisms to ensure high availability and reliability.

Key Features:
- Automatic provider failover
- Circuit breaker pattern implementation
- Intelligent recovery mechanisms
- Failure pattern detection
- Provider health monitoring
- Graceful degradation
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Tuple
from enum import Enum
from dataclasses import dataclass, field
import time

from ...base import BaseBankingConnector
from .models import (
    BankingProviderType, ProviderStatus, FailoverPolicy,
    CircuitBreakerState, FailoverEvent, RecoveryAttempt
)
from .exceptions import (
    FailoverError, CircuitBreakerOpenError, NoHealthyProvidersError,
    FailoverTimeoutError, MaxRetriesExceededError
)

from .....shared.logging import get_logger
from .....shared.exceptions import IntegrationError


class FailoverStrategy(Enum):
    """Failover strategies for different scenarios."""
    IMMEDIATE = "immediate"  # Fail over immediately on error
    THRESHOLD_BASED = "threshold_based"  # Fail over after error threshold
    CIRCUIT_BREAKER = "circuit_breaker"  # Use circuit breaker pattern
    GRACEFUL = "graceful"  # Allow current operations to complete
    AGGRESSIVE = "aggressive"  # Fail over on any sign of degradation


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""
    failure_threshold: int = 5  # Failures before opening
    success_threshold: int = 3  # Successes before closing
    timeout_seconds: int = 60  # Time before trying half-open
    window_size_seconds: int = 300  # Time window for failure counting
    max_consecutive_failures: int = 10


@dataclass
class FailoverConfig:
    """Configuration for failover behavior."""
    strategy: FailoverStrategy = FailoverStrategy.CIRCUIT_BREAKER
    max_retry_attempts: int = 3
    retry_delay_seconds: float = 1.0
    exponential_backoff: bool = True
    circuit_breaker: CircuitBreakerConfig = field(default_factory=CircuitBreakerConfig)
    health_check_interval: int = 30  # seconds
    recovery_timeout: int = 300  # seconds
    enable_auto_recovery: bool = True


@dataclass
class ProviderFailureInfo:
    """Information about provider failures."""
    provider_type: BankingProviderType
    failure_count: int = 0
    consecutive_failures: int = 0
    last_failure_time: Optional[datetime] = None
    first_failure_time: Optional[datetime] = None
    failure_window_start: Optional[datetime] = None
    total_failures_in_window: int = 0
    circuit_state: CircuitBreakerState = CircuitBreakerState.CLOSED
    last_success_time: Optional[datetime] = None


class FailoverManager:
    """
    Advanced failover manager providing high availability for banking operations.
    
    This manager implements multiple failover strategies including circuit breaker
    patterns, intelligent recovery mechanisms, and health monitoring to ensure
    continuous service availability across banking providers.
    """
    
    def __init__(self, config: FailoverConfig):
        """
        Initialize failover manager.
        
        Args:
            config: Failover configuration
        """
        self.config = config
        self.logger = get_logger(__name__)
        
        # Provider management
        self.providers: Dict[BankingProviderType, BaseBankingConnector] = {}
        self.provider_status: Dict[BankingProviderType, ProviderStatus] = {}
        self.failure_info: Dict[BankingProviderType, ProviderFailureInfo] = {}
        
        # Failover state
        self.active_failovers: Dict[str, FailoverEvent] = {}
        self.recovery_attempts: List[RecoveryAttempt] = []
        self.health_check_tasks: Dict[BankingProviderType, asyncio.Task] = {}
        
        # Metrics
        self.total_failovers = 0
        self.successful_recoveries = 0
        self.failed_recoveries = 0
        
        self.logger.info("Initialized failover manager")
    
    def register_provider(
        self,
        provider_type: BankingProviderType,
        provider: BaseBankingConnector
    ) -> None:
        """
        Register a provider with the failover manager.
        
        Args:
            provider_type: Type of banking provider
            provider: Provider connector instance
        """
        self.providers[provider_type] = provider
        self.provider_status[provider_type] = ProviderStatus.HEALTHY
        self.failure_info[provider_type] = ProviderFailureInfo(provider_type)
        
        # Start health check monitoring
        if self.config.enable_auto_recovery:
            self._start_health_monitoring(provider_type)
        
        self.logger.info(f"Registered provider with failover: {provider_type}")
    
    async def execute_with_failover(
        self,
        operation: Callable,
        primary_provider: BankingProviderType,
        fallback_providers: List[BankingProviderType],
        operation_id: str,
        *args,
        **kwargs
    ) -> Any:
        """
        Execute operation with automatic failover support.
        
        Args:
            operation: Operation to execute
            primary_provider: Primary provider to try first
            fallback_providers: Fallback providers in order
            operation_id: Unique operation identifier
            *args: Operation arguments
            **kwargs: Operation keyword arguments
            
        Returns:
            Operation result
            
        Raises:
            FailoverError: If all providers fail
        """
        providers_to_try = [primary_provider] + fallback_providers
        last_exception = None
        
        for attempt, provider_type in enumerate(providers_to_try):
            try:
                # Check if provider is available
                if not await self._is_provider_available(provider_type):
                    self.logger.warning(f"Provider {provider_type} not available, skipping")
                    continue
                
                # Check circuit breaker
                if not await self._check_circuit_breaker(provider_type):
                    self.logger.warning(f"Circuit breaker open for {provider_type}, skipping")
                    continue
                
                provider = self.providers[provider_type]
                
                self.logger.info(
                    f"Executing {operation_id} on {provider_type} (attempt {attempt + 1})"
                )
                
                # Execute operation with timeout
                result = await asyncio.wait_for(
                    operation(provider, *args, **kwargs),
                    timeout=self.config.recovery_timeout
                )
                
                # Record success
                await self._record_success(provider_type)
                
                if attempt > 0:
                    # This was a failover success
                    await self._record_failover_success(
                        operation_id, primary_provider, provider_type
                    )
                
                return result
                
            except asyncio.TimeoutError as e:
                last_exception = FailoverTimeoutError(f"Operation timeout on {provider_type}")
                await self._record_failure(provider_type, last_exception)
                
            except Exception as e:
                last_exception = e
                await self._record_failure(provider_type, e)
                
                self.logger.error(
                    f"Operation {operation_id} failed on {provider_type}: {str(e)}"
                )
        
        # All providers failed
        await self._record_complete_failover_failure(operation_id, providers_to_try)
        
        raise FailoverError(
            f"Operation {operation_id} failed on all providers. "
            f"Last error: {str(last_exception)}"
        )
    
    async def failover_provider(
        self,
        from_provider: BankingProviderType,
        to_provider: BankingProviderType,
        reason: str
    ) -> bool:
        """
        Manually trigger failover from one provider to another.
        
        Args:
            from_provider: Provider to failover from
            to_provider: Provider to failover to
            reason: Reason for failover
            
        Returns:
            True if failover successful
            
        Raises:
            FailoverError: If failover fails
        """
        try:
            self.logger.info(f"Manual failover: {from_provider} -> {to_provider}: {reason}")
            
            # Check target provider availability
            if not await self._is_provider_available(to_provider):
                raise FailoverError(f"Target provider {to_provider} not available")
            
            # Mark source provider as unhealthy
            await self._mark_provider_unhealthy(from_provider, reason)
            
            # Create failover event
            failover_event = FailoverEvent(
                event_id=f"manual_{int(time.time())}",
                from_provider=from_provider,
                to_provider=to_provider,
                reason=reason,
                timestamp=datetime.utcnow(),
                manual=True
            )
            
            self.active_failovers[failover_event.event_id] = failover_event
            self.total_failovers += 1
            
            self.logger.info(f"Manual failover completed: {failover_event.event_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Manual failover failed: {str(e)}")
            raise FailoverError(f"Manual failover failed: {str(e)}")
    
    async def recover_provider(
        self,
        provider_type: BankingProviderType,
        force: bool = False
    ) -> bool:
        """
        Attempt to recover a failed provider.
        
        Args:
            provider_type: Provider to recover
            force: Force recovery even if not ready
            
        Returns:
            True if recovery successful
        """
        try:
            self.logger.info(f"Attempting provider recovery: {provider_type}")
            
            failure_info = self.failure_info.get(provider_type)
            if not failure_info:
                return True  # No failure info means already healthy
            
            # Check if ready for recovery
            if not force and not await self._is_ready_for_recovery(provider_type):
                self.logger.info(f"Provider {provider_type} not ready for recovery")
                return False
            
            # Attempt provider health check
            provider = self.providers[provider_type]
            health_status = await provider.health_check()
            
            if health_status.get('healthy', False):
                # Recovery successful
                await self._mark_provider_recovered(provider_type)
                
                recovery_attempt = RecoveryAttempt(
                    provider_type=provider_type,
                    timestamp=datetime.utcnow(),
                    successful=True,
                    attempt_count=failure_info.consecutive_failures
                )
                self.recovery_attempts.append(recovery_attempt)
                self.successful_recoveries += 1
                
                self.logger.info(f"Provider recovery successful: {provider_type}")
                return True
            else:
                # Recovery failed
                recovery_attempt = RecoveryAttempt(
                    provider_type=provider_type,
                    timestamp=datetime.utcnow(),
                    successful=False,
                    attempt_count=failure_info.consecutive_failures,
                    error=health_status.get('error', 'Health check failed')
                )
                self.recovery_attempts.append(recovery_attempt)
                self.failed_recoveries += 1
                
                self.logger.warning(f"Provider recovery failed: {provider_type}")
                return False
                
        except Exception as e:
            self.logger.error(f"Provider recovery error: {str(e)}")
            return False
    
    async def get_healthy_providers(self) -> List[BankingProviderType]:
        """
        Get list of currently healthy providers.
        
        Returns:
            List of healthy provider types
        """
        healthy = []
        
        for provider_type, status in self.provider_status.items():
            if status == ProviderStatus.HEALTHY:
                # Double-check circuit breaker
                if await self._check_circuit_breaker(provider_type):
                    healthy.append(provider_type)
        
        return healthy
    
    async def get_failover_metrics(self) -> Dict[str, Any]:
        """
        Get comprehensive failover metrics.
        
        Returns:
            Failover metrics and statistics
        """
        return {
            'total_failovers': self.total_failovers,
            'successful_recoveries': self.successful_recoveries,
            'failed_recoveries': self.failed_recoveries,
            'active_failovers': len(self.active_failovers),
            'provider_status': {
                provider.value: status.value 
                for provider, status in self.provider_status.items()
            },
            'circuit_breaker_states': {
                provider.value: info.circuit_state.value
                for provider, info in self.failure_info.items()
            },
            'recent_recovery_attempts': len([
                r for r in self.recovery_attempts[-10:]
                if r.timestamp > datetime.utcnow() - timedelta(hours=1)
            ])
        }
    
    async def _is_provider_available(self, provider_type: BankingProviderType) -> bool:
        """Check if provider is available for operations."""
        status = self.provider_status.get(provider_type, ProviderStatus.UNKNOWN)
        return status == ProviderStatus.HEALTHY
    
    async def _check_circuit_breaker(self, provider_type: BankingProviderType) -> bool:
        """Check circuit breaker state for provider."""
        failure_info = self.failure_info.get(provider_type)
        if not failure_info:
            return True
        
        now = datetime.utcnow()
        
        if failure_info.circuit_state == CircuitBreakerState.CLOSED:
            return True
        elif failure_info.circuit_state == CircuitBreakerState.OPEN:
            # Check if timeout has passed
            if (failure_info.last_failure_time and
                now - failure_info.last_failure_time > 
                timedelta(seconds=self.config.circuit_breaker.timeout_seconds)):
                
                # Move to half-open
                failure_info.circuit_state = CircuitBreakerState.HALF_OPEN
                self.logger.info(f"Circuit breaker half-open: {provider_type}")
                return True
            return False
        elif failure_info.circuit_state == CircuitBreakerState.HALF_OPEN:
            return True
        
        return False
    
    async def _record_success(self, provider_type: BankingProviderType) -> None:
        """Record successful operation for provider."""
        failure_info = self.failure_info.get(provider_type)
        if not failure_info:
            return
        
        failure_info.last_success_time = datetime.utcnow()
        failure_info.consecutive_failures = 0
        
        # Handle circuit breaker state transitions
        if failure_info.circuit_state == CircuitBreakerState.HALF_OPEN:
            # Check if enough successes to close circuit
            if failure_info.consecutive_failures == 0:  # First success
                failure_info.circuit_state = CircuitBreakerState.CLOSED
                self.logger.info(f"Circuit breaker closed: {provider_type}")
    
    async def _record_failure(
        self,
        provider_type: BankingProviderType,
        exception: Exception
    ) -> None:
        """Record failed operation for provider."""
        failure_info = self.failure_info.get(provider_type)
        if not failure_info:
            return
        
        now = datetime.utcnow()
        failure_info.last_failure_time = now
        failure_info.failure_count += 1
        failure_info.consecutive_failures += 1
        
        if not failure_info.first_failure_time:
            failure_info.first_failure_time = now
        
        # Update failure window
        if not failure_info.failure_window_start:
            failure_info.failure_window_start = now
            failure_info.total_failures_in_window = 1
        else:
            window_duration = now - failure_info.failure_window_start
            if window_duration.total_seconds() > self.config.circuit_breaker.window_size_seconds:
                # Reset window
                failure_info.failure_window_start = now
                failure_info.total_failures_in_window = 1
            else:
                failure_info.total_failures_in_window += 1
        
        # Check circuit breaker thresholds
        await self._update_circuit_breaker_state(provider_type, failure_info)
        
        # Check if provider should be marked unhealthy
        if (failure_info.consecutive_failures >= 
            self.config.circuit_breaker.max_consecutive_failures):
            await self._mark_provider_unhealthy(provider_type, str(exception))
    
    async def _update_circuit_breaker_state(
        self,
        provider_type: BankingProviderType,
        failure_info: ProviderFailureInfo
    ) -> None:
        """Update circuit breaker state based on failures."""
        if failure_info.circuit_state == CircuitBreakerState.CLOSED:
            if (failure_info.total_failures_in_window >= 
                self.config.circuit_breaker.failure_threshold):
                failure_info.circuit_state = CircuitBreakerState.OPEN
                self.logger.warning(f"Circuit breaker opened: {provider_type}")
        
        elif failure_info.circuit_state == CircuitBreakerState.HALF_OPEN:
            # Any failure in half-open state opens circuit
            failure_info.circuit_state = CircuitBreakerState.OPEN
            self.logger.warning(f"Circuit breaker re-opened: {provider_type}")
    
    async def _mark_provider_unhealthy(
        self,
        provider_type: BankingProviderType,
        reason: str
    ) -> None:
        """Mark provider as unhealthy."""
        self.provider_status[provider_type] = ProviderStatus.UNHEALTHY
        self.logger.warning(f"Provider marked unhealthy: {provider_type} - {reason}")
    
    async def _mark_provider_recovered(self, provider_type: BankingProviderType) -> None:
        """Mark provider as recovered and healthy."""
        self.provider_status[provider_type] = ProviderStatus.HEALTHY
        
        # Reset failure info
        failure_info = self.failure_info.get(provider_type)
        if failure_info:
            failure_info.consecutive_failures = 0
            failure_info.circuit_state = CircuitBreakerState.CLOSED
            failure_info.last_success_time = datetime.utcnow()
        
        self.logger.info(f"Provider recovered: {provider_type}")
    
    async def _is_ready_for_recovery(self, provider_type: BankingProviderType) -> bool:
        """Check if provider is ready for recovery attempt."""
        failure_info = self.failure_info.get(provider_type)
        if not failure_info or not failure_info.last_failure_time:
            return True
        
        # Wait for recovery timeout
        time_since_failure = datetime.utcnow() - failure_info.last_failure_time
        return time_since_failure.total_seconds() >= self.config.recovery_timeout
    
    def _start_health_monitoring(self, provider_type: BankingProviderType) -> None:
        """Start background health monitoring for provider."""
        async def health_monitor():
            while provider_type in self.providers:
                try:
                    await asyncio.sleep(self.config.health_check_interval)
                    
                    if self.provider_status[provider_type] == ProviderStatus.UNHEALTHY:
                        await self.recover_provider(provider_type)
                        
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    self.logger.error(f"Health monitoring error for {provider_type}: {str(e)}")
        
        task = asyncio.create_task(health_monitor())
        self.health_check_tasks[provider_type] = task
    
    async def _record_failover_success(
        self,
        operation_id: str,
        from_provider: BankingProviderType,
        to_provider: BankingProviderType
    ) -> None:
        """Record successful failover operation."""
        self.logger.info(
            f"Failover success for {operation_id}: {from_provider} -> {to_provider}"
        )
    
    async def _record_complete_failover_failure(
        self,
        operation_id: str,
        attempted_providers: List[BankingProviderType]
    ) -> None:
        """Record complete failover failure across all providers."""
        self.logger.error(
            f"Complete failover failure for {operation_id}. "
            f"Attempted providers: {[p.value for p in attempted_providers]}"
        )