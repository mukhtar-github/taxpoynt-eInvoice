"""
Failover Manager Service

Handles integration failures and implements failover and recovery scenarios.
Provides circuit breaker patterns, automatic failover, and recovery mechanisms.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Set, Callable, Union
from enum import Enum
from dataclasses import dataclass, field
import json
import random
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


class FailoverState(Enum):
    """Failover system states"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILED = "failed"
    RECOVERING = "recovering"
    MAINTENANCE = "maintenance"


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"       # Normal operation
    OPEN = "open"          # Failing, rejecting requests
    HALF_OPEN = "half_open" # Testing if service recovered


class FailoverStrategy(Enum):
    """Failover strategies"""
    ROUND_ROBIN = "round_robin"
    PRIORITY = "priority"
    RANDOM = "random"
    WEIGHTED = "weighted"
    LEAST_CONNECTIONS = "least_connections"
    HEALTH_BASED = "health_based"


class RecoveryStrategy(Enum):
    """Recovery strategies"""
    IMMEDIATE = "immediate"
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"
    FIXED_INTERVAL = "fixed_interval"
    MANUAL = "manual"


@dataclass
class FailoverTarget:
    """Failover target configuration"""
    target_id: str
    system_id: str
    endpoint: str
    priority: int = 1
    weight: float = 1.0
    max_connections: int = 100
    timeout: int = 30
    enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration"""
    system_id: str
    failure_threshold: int = 5
    success_threshold: int = 3
    timeout: int = 60
    evaluation_window: int = 300  # seconds
    min_requests: int = 10
    enabled: bool = True


@dataclass
class FailoverConfig:
    """Failover configuration"""
    system_id: str
    primary_target: FailoverTarget
    failover_targets: List[FailoverTarget] = field(default_factory=list)
    strategy: FailoverStrategy = FailoverStrategy.PRIORITY
    circuit_breaker: Optional[CircuitBreakerConfig] = None
    recovery_strategy: RecoveryStrategy = RecoveryStrategy.EXPONENTIAL_BACKOFF
    max_retries: int = 3
    retry_delay: float = 1.0
    health_check_interval: int = 60
    auto_failback: bool = True
    enabled: bool = True


@dataclass
class FailureRecord:
    """Record of a failure event"""
    system_id: str
    target_id: str
    failure_type: str
    error_message: str
    timestamp: datetime
    duration: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FailoverEvent:
    """Failover event record"""
    event_id: str
    system_id: str
    event_type: str  # failover, failback, circuit_open, circuit_close
    source_target: Optional[str] = None
    destination_target: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    reason: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SystemStatus:
    """Current status of a system with failover"""
    system_id: str
    state: FailoverState
    active_target: Optional[FailoverTarget] = None
    circuit_state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure: Optional[datetime] = None
    last_success: Optional[datetime] = None
    recovery_attempts: int = 0
    current_connections: int = 0
    next_health_check: Optional[datetime] = None


class CircuitBreaker:
    """Circuit breaker implementation"""
    
    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.next_attempt_time = None
        self.request_count = 0
        self.failure_window: List[datetime] = []
        
    async def call(self, func: Callable, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        if not self.config.enabled:
            return await self._execute_function(func, *args, **kwargs)
        
        # Check circuit state
        if self.state == CircuitState.OPEN:
            if datetime.now() < self.next_attempt_time:
                raise CircuitBreakerOpenError(f"Circuit breaker is open for {self.config.system_id}")
            else:
                # Transition to half-open
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
        
        try:
            # Execute function
            result = await self._execute_function(func, *args, **kwargs)
            
            # Record success
            await self._record_success()
            
            return result
            
        except Exception as e:
            # Record failure
            await self._record_failure()
            raise
    
    async def _execute_function(self, func: Callable, *args, **kwargs):
        """Execute the actual function"""
        if asyncio.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        else:
            return func(*args, **kwargs)
    
    async def _record_success(self):
        """Record successful execution"""
        self.success_count += 1
        self.request_count += 1
        
        if self.state == CircuitState.HALF_OPEN:
            if self.success_count >= self.config.success_threshold:
                # Close circuit
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.failure_window.clear()
                logger.info(f"Circuit breaker closed for {self.config.system_id}")
    
    async def _record_failure(self):
        """Record failed execution"""
        self.failure_count += 1
        self.request_count += 1
        self.last_failure_time = datetime.now()
        
        # Add to failure window
        self.failure_window.append(self.last_failure_time)
        
        # Clean old failures from window
        cutoff_time = self.last_failure_time - timedelta(seconds=self.config.evaluation_window)
        self.failure_window = [f for f in self.failure_window if f > cutoff_time]
        
        # Check if we should open circuit
        if (self.state == CircuitState.CLOSED and 
            len(self.failure_window) >= self.config.failure_threshold and
            self.request_count >= self.config.min_requests):
            
            # Open circuit
            self.state = CircuitState.OPEN
            self.next_attempt_time = self.last_failure_time + timedelta(seconds=self.config.timeout)
            logger.warning(f"Circuit breaker opened for {self.config.system_id}")
        
        elif self.state == CircuitState.HALF_OPEN:
            # Go back to open
            self.state = CircuitState.OPEN
            self.next_attempt_time = self.last_failure_time + timedelta(seconds=self.config.timeout)
    
    def get_state(self) -> CircuitState:
        """Get current circuit state"""
        return self.state
    
    def get_stats(self) -> Dict[str, Any]:
        """Get circuit breaker statistics"""
        return {
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "request_count": self.request_count,
            "failure_window_size": len(self.failure_window),
            "last_failure": self.last_failure_time.isoformat() if self.last_failure_time else None,
            "next_attempt": self.next_attempt_time.isoformat() if self.next_attempt_time else None
        }


class CircuitBreakerOpenError(Exception):
    """Exception raised when circuit breaker is open"""
    pass


class TargetSelector:
    """Select appropriate target based on strategy"""
    
    def __init__(self):
        self.selection_strategies = {
            FailoverStrategy.ROUND_ROBIN: self._round_robin_select,
            FailoverStrategy.PRIORITY: self._priority_select,
            FailoverStrategy.RANDOM: self._random_select,
            FailoverStrategy.WEIGHTED: self._weighted_select,
            FailoverStrategy.HEALTH_BASED: self._health_based_select,
        }
        self.round_robin_indices: Dict[str, int] = {}
    
    def select_target(
        self, 
        system_id: str, 
        targets: List[FailoverTarget], 
        strategy: FailoverStrategy,
        health_scores: Optional[Dict[str, float]] = None,
        connection_counts: Optional[Dict[str, int]] = None
    ) -> Optional[FailoverTarget]:
        """Select target based on strategy"""
        
        # Filter enabled targets
        available_targets = [t for t in targets if t.enabled]
        
        if not available_targets:
            return None
        
        if strategy in self.selection_strategies:
            return self.selection_strategies[strategy](
                system_id, available_targets, health_scores, connection_counts
            )
        else:
            return self._priority_select(system_id, available_targets, health_scores, connection_counts)
    
    def _round_robin_select(
        self, 
        system_id: str, 
        targets: List[FailoverTarget],
        health_scores: Optional[Dict[str, float]] = None,
        connection_counts: Optional[Dict[str, int]] = None
    ) -> FailoverTarget:
        """Round-robin target selection"""
        if system_id not in self.round_robin_indices:
            self.round_robin_indices[system_id] = 0
        
        index = self.round_robin_indices[system_id] % len(targets)
        self.round_robin_indices[system_id] = (index + 1) % len(targets)
        
        return targets[index]
    
    def _priority_select(
        self, 
        system_id: str, 
        targets: List[FailoverTarget],
        health_scores: Optional[Dict[str, float]] = None,
        connection_counts: Optional[Dict[str, int]] = None
    ) -> FailoverTarget:
        """Priority-based target selection"""
        return max(targets, key=lambda t: t.priority)
    
    def _random_select(
        self, 
        system_id: str, 
        targets: List[FailoverTarget],
        health_scores: Optional[Dict[str, float]] = None,
        connection_counts: Optional[Dict[str, int]] = None
    ) -> FailoverTarget:
        """Random target selection"""
        return random.choice(targets)
    
    def _weighted_select(
        self, 
        system_id: str, 
        targets: List[FailoverTarget],
        health_scores: Optional[Dict[str, float]] = None,
        connection_counts: Optional[Dict[str, int]] = None
    ) -> FailoverTarget:
        """Weighted random target selection"""
        weights = [t.weight for t in targets]
        return random.choices(targets, weights=weights)[0]
    
    def _health_based_select(
        self, 
        system_id: str, 
        targets: List[FailoverTarget],
        health_scores: Optional[Dict[str, float]] = None,
        connection_counts: Optional[Dict[str, int]] = None
    ) -> FailoverTarget:
        """Health-based target selection"""
        if health_scores:
            # Select target with best health score
            best_target = None
            best_score = -1
            
            for target in targets:
                score = health_scores.get(target.target_id, 0.5)
                if score > best_score:
                    best_score = score
                    best_target = target
            
            if best_target:
                return best_target
        
        # Fallback to priority selection
        return self._priority_select(system_id, targets, health_scores, connection_counts)


class RecoveryManager:
    """Manage recovery strategies and backoff algorithms"""
    
    def __init__(self):
        self.recovery_attempts: Dict[str, int] = {}
        self.last_attempt_times: Dict[str, datetime] = {}
    
    async def calculate_next_attempt(
        self, 
        system_id: str, 
        strategy: RecoveryStrategy, 
        base_delay: float = 1.0,
        max_delay: float = 300.0
    ) -> datetime:
        """Calculate next recovery attempt time"""
        
        attempts = self.recovery_attempts.get(system_id, 0)
        
        if strategy == RecoveryStrategy.IMMEDIATE:
            delay = 0
        elif strategy == RecoveryStrategy.EXPONENTIAL_BACKOFF:
            delay = min(base_delay * (2 ** attempts), max_delay)
        elif strategy == RecoveryStrategy.LINEAR_BACKOFF:
            delay = min(base_delay * (attempts + 1), max_delay)
        elif strategy == RecoveryStrategy.FIXED_INTERVAL:
            delay = base_delay
        else:  # MANUAL
            delay = float('inf')  # Never automatically retry
        
        next_attempt = datetime.now() + timedelta(seconds=delay)
        self.last_attempt_times[system_id] = next_attempt
        
        return next_attempt
    
    def record_attempt(self, system_id: str):
        """Record recovery attempt"""
        self.recovery_attempts[system_id] = self.recovery_attempts.get(system_id, 0) + 1
    
    def record_success(self, system_id: str):
        """Record successful recovery"""
        self.recovery_attempts.pop(system_id, None)
        self.last_attempt_times.pop(system_id, None)
    
    def get_attempt_count(self, system_id: str) -> int:
        """Get current attempt count"""
        return self.recovery_attempts.get(system_id, 0)


class FailoverManager:
    """Main failover and recovery management service"""
    
    def __init__(self):
        self.configurations: Dict[str, FailoverConfig] = {}
        self.system_status: Dict[str, SystemStatus] = {}
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.target_selector = TargetSelector()
        self.recovery_manager = RecoveryManager()
        self.failure_history: List[FailureRecord] = []
        self.failover_events: List[FailoverEvent] = []
        self.health_check_tasks: Dict[str, asyncio.Task] = {}
        self.event_handlers: List[Callable] = []
        
    async def register_failover_config(self, config: FailoverConfig) -> bool:
        """
        Register failover configuration for a system
        
        Args:
            config: Failover configuration
            
        Returns:
            Registration success status
        """
        try:
            system_id = config.system_id
            
            # Store configuration
            self.configurations[system_id] = config
            
            # Initialize system status
            self.system_status[system_id] = SystemStatus(
                system_id=system_id,
                state=FailoverState.HEALTHY,
                active_target=config.primary_target
            )
            
            # Setup circuit breaker if configured
            if config.circuit_breaker:
                self.circuit_breakers[system_id] = CircuitBreaker(config.circuit_breaker)
            
            # Start health check task
            if config.health_check_interval > 0:
                self.health_check_tasks[system_id] = asyncio.create_task(
                    self._health_check_loop(system_id)
                )
            
            logger.info(f"Registered failover configuration for {system_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register failover config for {config.system_id}: {e}")
            return False
    
    @asynccontextmanager
    async def execute_with_failover(self, system_id: str, operation: Callable, *args, **kwargs):
        """
        Execute operation with failover protection
        
        Args:
            system_id: System identifier
            operation: Function to execute
            *args, **kwargs: Arguments for the operation
            
        Yields:
            Operation result
        """
        if system_id not in self.configurations:
            raise ValueError(f"Failover not configured for {system_id}")
        
        config = self.configurations[system_id]
        status = self.system_status[system_id]
        
        if not config.enabled:
            # Execute without failover
            result = await self._execute_operation(operation, *args, **kwargs)
            yield result
            return
        
        max_attempts = config.max_retries + 1
        last_error = None
        
        for attempt in range(max_attempts):
            try:
                # Get current target
                current_target = await self._get_current_target(system_id)
                
                if not current_target:
                    raise NoAvailableTargetsError(f"No available targets for {system_id}")
                
                # Update connection count
                status.current_connections += 1
                
                try:
                    # Execute with circuit breaker if configured
                    if system_id in self.circuit_breakers:
                        circuit_breaker = self.circuit_breakers[system_id]
                        result = await circuit_breaker.call(operation, current_target, *args, **kwargs)
                    else:
                        result = await self._execute_operation(operation, current_target, *args, **kwargs)
                    
                    # Record success
                    await self._record_success(system_id, current_target)
                    
                    yield result
                    return
                    
                finally:
                    status.current_connections -= 1
                    
            except Exception as e:
                last_error = e
                
                # Record failure
                await self._record_failure(system_id, status.active_target, str(e))
                
                # Check if we should failover
                if attempt < max_attempts - 1:
                    failover_occurred = await self._attempt_failover(system_id)
                    
                    if failover_occurred:
                        # Wait before retry
                        await asyncio.sleep(config.retry_delay)
                        continue
                
                # No more retries or failover failed
                break
        
        # All attempts failed
        raise FailoverExhaustedException(
            f"All failover attempts exhausted for {system_id}: {last_error}"
        )
    
    async def _execute_operation(self, operation: Callable, *args, **kwargs):
        """Execute the actual operation"""
        if asyncio.iscoroutinefunction(operation):
            return await operation(*args, **kwargs)
        else:
            return operation(*args, **kwargs)
    
    async def _get_current_target(self, system_id: str) -> Optional[FailoverTarget]:
        """Get current active target for system"""
        config = self.configurations[system_id]
        status = self.system_status[system_id]
        
        # Check if current target is healthy
        if status.active_target and status.active_target.enabled:
            return status.active_target
        
        # Select new target
        all_targets = [config.primary_target] + config.failover_targets
        available_targets = [t for t in all_targets if t.enabled and t != status.active_target]
        
        if not available_targets:
            return None
        
        # Get health scores (mock implementation)
        health_scores = await self._get_health_scores(system_id, available_targets)
        
        # Select target
        selected_target = self.target_selector.select_target(
            system_id, 
            available_targets, 
            config.strategy,
            health_scores
        )
        
        if selected_target and selected_target != status.active_target:
            # Record failover event
            await self._record_failover_event(
                system_id, 
                "failover",
                status.active_target.target_id if status.active_target else None,
                selected_target.target_id,
                "Target selection"
            )
            
            status.active_target = selected_target
        
        return selected_target
    
    async def _get_health_scores(
        self, 
        system_id: str, 
        targets: List[FailoverTarget]
    ) -> Dict[str, float]:
        """Get health scores for targets (mock implementation)"""
        # TODO: Integrate with health_monitor to get actual health scores
        return {target.target_id: 0.8 for target in targets}
    
    async def _record_success(self, system_id: str, target: FailoverTarget):
        """Record successful operation"""
        status = self.system_status[system_id]
        status.success_count += 1
        status.last_success = datetime.now()
        
        # Update system state
        if status.state in [FailoverState.FAILED, FailoverState.RECOVERING]:
            status.state = FailoverState.HEALTHY
            status.recovery_attempts = 0
            self.recovery_manager.record_success(system_id)
            
            await self._record_failover_event(
                system_id, 
                "recovery_success",
                None,
                target.target_id,
                "System recovered"
            )
    
    async def _record_failure(self, system_id: str, target: Optional[FailoverTarget], error_message: str):
        """Record failed operation"""
        status = self.system_status[system_id]
        status.failure_count += 1
        status.last_failure = datetime.now()
        
        # Add to failure history
        failure_record = FailureRecord(
            system_id=system_id,
            target_id=target.target_id if target else "unknown",
            failure_type="operation_failure",
            error_message=error_message,
            timestamp=datetime.now()
        )
        self.failure_history.append(failure_record)
        
        # Update system state
        if status.state == FailoverState.HEALTHY:
            status.state = FailoverState.DEGRADED
        elif status.state == FailoverState.DEGRADED:
            status.state = FailoverState.FAILED
    
    async def _attempt_failover(self, system_id: str) -> bool:
        """Attempt to failover to another target"""
        config = self.configurations[system_id]
        status = self.system_status[system_id]
        
        # Get all targets except current one
        all_targets = [config.primary_target] + config.failover_targets
        available_targets = [
            t for t in all_targets 
            if t.enabled and t != status.active_target
        ]
        
        if not available_targets:
            logger.warning(f"No failover targets available for {system_id}")
            return False
        
        # Select failover target
        health_scores = await self._get_health_scores(system_id, available_targets)
        failover_target = self.target_selector.select_target(
            system_id, 
            available_targets, 
            config.strategy,
            health_scores
        )
        
        if failover_target:
            old_target = status.active_target
            status.active_target = failover_target
            status.state = FailoverState.RECOVERING
            
            await self._record_failover_event(
                system_id,
                "failover",
                old_target.target_id if old_target else None,
                failover_target.target_id,
                "Automatic failover due to failure"
            )
            
            logger.info(f"Failed over {system_id} to {failover_target.target_id}")
            return True
        
        return False
    
    async def _record_failover_event(
        self, 
        system_id: str, 
        event_type: str, 
        source_target: Optional[str], 
        destination_target: Optional[str], 
        reason: str
    ):
        """Record failover event"""
        event = FailoverEvent(
            event_id=f"{system_id}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
            system_id=system_id,
            event_type=event_type,
            source_target=source_target,
            destination_target=destination_target,
            reason=reason
        )
        
        self.failover_events.append(event)
        
        # Notify event handlers
        for handler in self.event_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                logger.error(f"Event handler error: {e}")
    
    async def _health_check_loop(self, system_id: str):
        """Continuous health check for system"""
        config = self.configurations[system_id]
        
        while True:
            try:
                await asyncio.sleep(config.health_check_interval)
                
                # Perform health check on current target
                status = self.system_status[system_id]
                if status.active_target:
                    health_result = await self._perform_health_check(system_id, status.active_target)
                    
                    if health_result:
                        await self._record_success(system_id, status.active_target)
                    else:
                        await self._record_failure(
                            system_id, 
                            status.active_target, 
                            "Health check failed"
                        )
                        
                        # Attempt failover if in failed state
                        if status.state == FailoverState.FAILED:
                            await self._attempt_failover(system_id)
                
                # Check for automatic failback
                if config.auto_failback and status.active_target != config.primary_target:
                    await self._check_failback_conditions(system_id)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check error for {system_id}: {e}")
    
    async def _perform_health_check(self, system_id: str, target: FailoverTarget) -> bool:
        """Perform health check on target"""
        # TODO: Implement actual health check logic
        # This would integrate with health_monitor or perform direct checks
        
        # Mock implementation
        await asyncio.sleep(0.1)
        return True
    
    async def _check_failback_conditions(self, system_id: str):
        """Check if conditions are met for failback to primary"""
        config = self.configurations[system_id]
        status = self.system_status[system_id]
        
        # Check if primary target is healthy
        primary_health = await self._perform_health_check(system_id, config.primary_target)
        
        if primary_health and status.state == FailoverState.HEALTHY:
            # Failback to primary
            old_target = status.active_target
            status.active_target = config.primary_target
            
            await self._record_failover_event(
                system_id,
                "failback",
                old_target.target_id if old_target else None,
                config.primary_target.target_id,
                "Automatic failback to primary"
            )
            
            logger.info(f"Failed back {system_id} to primary target")
    
    async def manual_failover(self, system_id: str, target_id: str) -> bool:
        """
        Manually trigger failover to specific target
        
        Args:
            system_id: System identifier
            target_id: Target to failover to
            
        Returns:
            Failover success status
        """
        if system_id not in self.configurations:
            return False
        
        config = self.configurations[system_id]
        status = self.system_status[system_id]
        
        # Find target
        all_targets = [config.primary_target] + config.failover_targets
        target = next((t for t in all_targets if t.target_id == target_id), None)
        
        if not target or not target.enabled:
            return False
        
        # Perform failover
        old_target = status.active_target
        status.active_target = target
        
        await self._record_failover_event(
            system_id,
            "manual_failover",
            old_target.target_id if old_target else None,
            target.target_id,
            "Manual failover triggered"
        )
        
        logger.info(f"Manual failover {system_id} to {target_id}")
        return True
    
    async def get_system_status(self, system_id: str) -> Optional[SystemStatus]:
        """Get failover status for system"""
        return self.system_status.get(system_id)
    
    async def get_all_system_statuses(self) -> Dict[str, SystemStatus]:
        """Get failover status for all systems"""
        return self.system_status.copy()
    
    async def get_circuit_breaker_stats(self, system_id: str) -> Optional[Dict[str, Any]]:
        """Get circuit breaker statistics"""
        if system_id in self.circuit_breakers:
            return self.circuit_breakers[system_id].get_stats()
        return None
    
    async def get_failure_history(self, system_id: Optional[str] = None, hours: int = 24) -> List[FailureRecord]:
        """Get failure history"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        filtered_failures = [
            failure for failure in self.failure_history
            if failure.timestamp >= cutoff_time
        ]
        
        if system_id:
            filtered_failures = [
                failure for failure in filtered_failures
                if failure.system_id == system_id
            ]
        
        return filtered_failures
    
    async def get_failover_events(self, system_id: Optional[str] = None, hours: int = 24) -> List[FailoverEvent]:
        """Get failover events"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        filtered_events = [
            event for event in self.failover_events
            if event.timestamp >= cutoff_time
        ]
        
        if system_id:
            filtered_events = [
                event for event in filtered_events
                if event.system_id == system_id
            ]
        
        return filtered_events
    
    def add_event_handler(self, handler: Callable):
        """Add failover event handler"""
        self.event_handlers.append(handler)
    
    async def cleanup_history(self, days: int = 7):
        """Clean up old failure and event history"""
        cutoff_time = datetime.now() - timedelta(days=days)
        
        # Clean failure history
        self.failure_history = [
            failure for failure in self.failure_history
            if failure.timestamp >= cutoff_time
        ]
        
        # Clean event history
        self.failover_events = [
            event for event in self.failover_events
            if event.timestamp >= cutoff_time
        ]
        
        logger.info(f"Cleaned up failover history older than {days} days")
    
    async def shutdown(self):
        """Shutdown failover manager"""
        # Cancel health check tasks
        for task in self.health_check_tasks.values():
            task.cancel()
        
        # Wait for tasks to complete
        if self.health_check_tasks:
            await asyncio.gather(*self.health_check_tasks.values(), return_exceptions=True)
        
        # Clear data
        self.configurations.clear()
        self.system_status.clear()
        self.circuit_breakers.clear()
        self.health_check_tasks.clear()
        self.event_handlers.clear()
        
        logger.info("Failover manager shutdown complete")


class NoAvailableTargetsError(Exception):
    """Exception raised when no targets are available"""
    pass


class FailoverExhaustedException(Exception):
    """Exception raised when all failover attempts are exhausted"""
    pass


# Global instance
failover_manager = FailoverManager()


async def register_system_failover(config: FailoverConfig) -> bool:
    """Register failover configuration with global manager"""
    return await failover_manager.register_failover_config(config)


async def execute_with_system_failover(system_id: str, operation: Callable, *args, **kwargs):
    """Execute operation with global failover manager"""
    async with failover_manager.execute_with_failover(system_id, operation, *args, **kwargs) as result:
        return result