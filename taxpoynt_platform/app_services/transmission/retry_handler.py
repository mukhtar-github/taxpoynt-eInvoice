"""
Transmission Retry Handler Service for APP Role

This service handles retry logic for failed transmissions with:
- Intelligent retry strategies
- Exponential backoff with jitter
- Circuit breaker pattern
- Dead letter queue for persistent failures
- Retry analytics and monitoring
"""

import asyncio
import json
import time
import random
import math
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
import logging
from collections import defaultdict, deque

from .secure_transmitter import (
    SecureTransmitter, TransmissionRequest, TransmissionResult,
    TransmissionStatus, SecurityLevel
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RetryStrategy(Enum):
    """Retry strategy types"""
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    FIXED_DELAY = "fixed_delay"
    LINEAR_BACKOFF = "linear_backoff"
    FIBONACCI_BACKOFF = "fibonacci_backoff"
    CUSTOM = "custom"


class RetryReason(Enum):
    """Reasons for retry"""
    NETWORK_ERROR = "network_error"
    TIMEOUT = "timeout"
    SERVER_ERROR = "server_error"
    AUTHENTICATION_ERROR = "authentication_error"
    RATE_LIMIT = "rate_limit"
    TEMPORARY_FAILURE = "temporary_failure"
    CIRCUIT_BREAKER = "circuit_breaker"
    UNKNOWN = "unknown"


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class RetryPolicy:
    """Retry policy configuration"""
    max_attempts: int = 3
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF
    base_delay: float = 1.0
    max_delay: float = 60.0
    backoff_multiplier: float = 2.0
    jitter_factor: float = 0.1
    timeout: float = 300.0
    retry_on_status: List[TransmissionStatus] = field(default_factory=lambda: [TransmissionStatus.FAILED])
    retry_on_reasons: List[RetryReason] = field(default_factory=lambda: [
        RetryReason.NETWORK_ERROR, RetryReason.TIMEOUT, RetryReason.SERVER_ERROR,
        RetryReason.RATE_LIMIT, RetryReason.TEMPORARY_FAILURE
    ])
    circuit_breaker_enabled: bool = True
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: float = 30.0


@dataclass
class RetryAttempt:
    """Individual retry attempt"""
    attempt_number: int
    scheduled_at: datetime
    executed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[TransmissionResult] = None
    error_message: Optional[str] = None
    delay: float = 0.0
    reason: Optional[RetryReason] = None


@dataclass
class RetryRequest:
    """Retry request information"""
    retry_id: str
    original_request: TransmissionRequest
    original_result: TransmissionResult
    retry_policy: RetryPolicy
    created_at: datetime
    attempts: List[RetryAttempt] = field(default_factory=list)
    current_attempt: int = 0
    next_retry_at: Optional[datetime] = None
    final_result: Optional[TransmissionResult] = None
    is_completed: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CircuitBreaker:
    """Circuit breaker for endpoint protection"""
    endpoint: str
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None
    next_attempt_time: Optional[datetime] = None
    failure_threshold: int = 5
    recovery_timeout: float = 30.0
    half_open_success_threshold: int = 3


class RetryHandler:
    """
    Transmission retry handler service for APP role
    
    Handles:
    - Intelligent retry strategies with backoff
    - Circuit breaker pattern for endpoint protection
    - Dead letter queue for persistent failures
    - Retry analytics and monitoring
    - Adaptive retry policies
    """
    
    def __init__(self, 
                 secure_transmitter: SecureTransmitter,
                 default_retry_policy: Optional[RetryPolicy] = None,
                 max_concurrent_retries: int = 50,
                 dead_letter_queue_size: int = 1000):
        self.secure_transmitter = secure_transmitter
        self.default_retry_policy = default_retry_policy or RetryPolicy()
        self.max_concurrent_retries = max_concurrent_retries
        self.dead_letter_queue_size = dead_letter_queue_size
        
        # Internal state
        self._retry_requests: Dict[str, RetryRequest] = {}
        self._scheduled_retries: Dict[str, asyncio.Task] = {}
        self._circuit_breakers: Dict[str, CircuitBreaker] = {}
        self._dead_letter_queue: deque = deque(maxlen=dead_letter_queue_size)
        
        # Control
        self._is_running = False
        self._retry_semaphore = asyncio.Semaphore(max_concurrent_retries)
        self._monitor_task: Optional[asyncio.Task] = None
        
        # Metrics
        self.metrics = {
            'total_retries': 0,
            'successful_retries': 0,
            'failed_retries': 0,
            'circuit_breaker_trips': 0,
            'dead_letter_items': 0,
            'average_retry_delay': 0.0,
            'retry_success_rate': 0.0,
            'endpoint_health': {},
            'retry_reasons': defaultdict(int)
        }
        
        # Analytics
        self._retry_analytics = {
            'delays': deque(maxlen=1000),
            'success_rates': deque(maxlen=1000),
            'failure_patterns': defaultdict(list)
        }
    
    async def start(self):
        """Start the retry handler service"""
        if self._is_running:
            return
        
        self._is_running = True
        
        # Start monitoring task
        self._monitor_task = asyncio.create_task(self._monitor_circuit_breakers())
        
        logger.info("Retry handler started")
    
    async def stop(self):
        """Stop the retry handler service"""
        if not self._is_running:
            return
        
        self._is_running = False
        
        # Cancel monitoring task
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        
        # Cancel all scheduled retries
        for task in self._scheduled_retries.values():
            task.cancel()
        
        if self._scheduled_retries:
            await asyncio.gather(*self._scheduled_retries.values(), return_exceptions=True)
        
        self._scheduled_retries.clear()
        
        logger.info("Retry handler stopped")
    
    async def handle_failed_transmission(self, 
                                       transmission_request: TransmissionRequest,
                                       transmission_result: TransmissionResult,
                                       retry_policy: Optional[RetryPolicy] = None) -> str:
        """
        Handle a failed transmission for retry
        
        Args:
            transmission_request: Original transmission request
            transmission_result: Failed transmission result
            retry_policy: Custom retry policy (optional)
            
        Returns:
            Retry ID for tracking
        """
        # Use provided policy or default
        policy = retry_policy or self.default_retry_policy
        
        # Check if retry is warranted
        if not self._should_retry(transmission_result, policy):
            logger.info(f"Transmission {transmission_request.document_id} not eligible for retry")
            return ""
        
        # Check circuit breaker
        endpoint = transmission_request.destination_endpoint
        if not self._check_circuit_breaker(endpoint):
            logger.warning(f"Circuit breaker open for {endpoint}, skipping retry")
            return ""
        
        # Create retry request
        retry_id = str(uuid.uuid4())
        retry_request = RetryRequest(
            retry_id=retry_id,
            original_request=transmission_request,
            original_result=transmission_result,
            retry_policy=policy,
            created_at=datetime.utcnow()
        )
        
        # Store retry request
        self._retry_requests[retry_id] = retry_request
        
        # Schedule first retry
        await self._schedule_retry(retry_request)
        
        # Update metrics
        self.metrics['total_retries'] += 1
        reason = self._determine_retry_reason(transmission_result)
        self.metrics['retry_reasons'][reason.value] += 1
        
        logger.info(f"Retry {retry_id} scheduled for transmission {transmission_request.document_id}")
        
        return retry_id
    
    def _should_retry(self, result: TransmissionResult, policy: RetryPolicy) -> bool:
        """Check if transmission should be retried"""
        # Check status
        if result.status not in policy.retry_on_status:
            return False
        
        # Check retry reason
        reason = self._determine_retry_reason(result)
        if reason not in policy.retry_on_reasons:
            return False
        
        return True
    
    def _determine_retry_reason(self, result: TransmissionResult) -> RetryReason:
        """Determine retry reason from transmission result"""
        if not result.error_message:
            return RetryReason.UNKNOWN
        
        error_message = result.error_message.lower()
        
        if 'network' in error_message or 'connection' in error_message:
            return RetryReason.NETWORK_ERROR
        elif 'timeout' in error_message:
            return RetryReason.TIMEOUT
        elif 'server error' in error_message or '5' in error_message:
            return RetryReason.SERVER_ERROR
        elif 'authentication' in error_message or 'auth' in error_message:
            return RetryReason.AUTHENTICATION_ERROR
        elif 'rate limit' in error_message or 'throttle' in error_message:
            return RetryReason.RATE_LIMIT
        elif 'temporary' in error_message:
            return RetryReason.TEMPORARY_FAILURE
        else:
            return RetryReason.UNKNOWN
    
    def _check_circuit_breaker(self, endpoint: str) -> bool:
        """Check if circuit breaker allows requests"""
        if endpoint not in self._circuit_breakers:
            self._circuit_breakers[endpoint] = CircuitBreaker(
                endpoint=endpoint,
                failure_threshold=self.default_retry_policy.circuit_breaker_threshold,
                recovery_timeout=self.default_retry_policy.circuit_breaker_timeout
            )
        
        circuit_breaker = self._circuit_breakers[endpoint]
        
        if circuit_breaker.state == CircuitState.CLOSED:
            return True
        elif circuit_breaker.state == CircuitState.OPEN:
            # Check if recovery time has passed
            if (circuit_breaker.next_attempt_time and 
                datetime.utcnow() >= circuit_breaker.next_attempt_time):
                circuit_breaker.state = CircuitState.HALF_OPEN
                logger.info(f"Circuit breaker for {endpoint} moved to HALF_OPEN")
                return True
            return False
        else:  # HALF_OPEN
            return True
    
    def _update_circuit_breaker(self, endpoint: str, success: bool):
        """Update circuit breaker state"""
        if endpoint not in self._circuit_breakers:
            return
        
        circuit_breaker = self._circuit_breakers[endpoint]
        
        if success:
            circuit_breaker.success_count += 1
            circuit_breaker.last_success_time = datetime.utcnow()
            
            if circuit_breaker.state == CircuitState.HALF_OPEN:
                if circuit_breaker.success_count >= circuit_breaker.half_open_success_threshold:
                    circuit_breaker.state = CircuitState.CLOSED
                    circuit_breaker.failure_count = 0
                    circuit_breaker.success_count = 0
                    logger.info(f"Circuit breaker for {endpoint} moved to CLOSED")
        else:
            circuit_breaker.failure_count += 1
            circuit_breaker.last_failure_time = datetime.utcnow()
            
            if circuit_breaker.failure_count >= circuit_breaker.failure_threshold:
                circuit_breaker.state = CircuitState.OPEN
                circuit_breaker.next_attempt_time = datetime.utcnow() + timedelta(
                    seconds=circuit_breaker.recovery_timeout
                )
                self.metrics['circuit_breaker_trips'] += 1
                logger.warning(f"Circuit breaker for {endpoint} tripped to OPEN")
    
    async def _schedule_retry(self, retry_request: RetryRequest):
        """Schedule a retry attempt"""
        if retry_request.current_attempt >= retry_request.retry_policy.max_attempts:
            await self._move_to_dead_letter_queue(retry_request)
            return
        
        # Calculate delay
        delay = self._calculate_delay(retry_request)
        retry_request.next_retry_at = datetime.utcnow() + timedelta(seconds=delay)
        
        # Create retry attempt
        attempt = RetryAttempt(
            attempt_number=retry_request.current_attempt + 1,
            scheduled_at=retry_request.next_retry_at,
            delay=delay,
            reason=self._determine_retry_reason(retry_request.original_result)
        )
        
        retry_request.attempts.append(attempt)
        retry_request.current_attempt += 1
        
        # Schedule the retry
        task = asyncio.create_task(self._execute_retry_after_delay(retry_request, attempt, delay))
        self._scheduled_retries[retry_request.retry_id] = task
        
        # Update analytics
        self._retry_analytics['delays'].append(delay)
        
        logger.info(f"Retry {retry_request.retry_id} attempt {attempt.attempt_number} scheduled in {delay:.2f}s")
    
    def _calculate_delay(self, retry_request: RetryRequest) -> float:
        """Calculate retry delay based on strategy"""
        policy = retry_request.retry_policy
        attempt = retry_request.current_attempt
        
        if policy.strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            delay = policy.base_delay * (policy.backoff_multiplier ** attempt)
        elif policy.strategy == RetryStrategy.FIXED_DELAY:
            delay = policy.base_delay
        elif policy.strategy == RetryStrategy.LINEAR_BACKOFF:
            delay = policy.base_delay * (attempt + 1)
        elif policy.strategy == RetryStrategy.FIBONACCI_BACKOFF:
            delay = policy.base_delay * self._fibonacci(attempt + 1)
        else:
            delay = policy.base_delay
        
        # Apply jitter
        if policy.jitter_factor > 0:
            jitter = delay * policy.jitter_factor * random.uniform(-1, 1)
            delay += jitter
        
        # Cap at max delay
        delay = min(delay, policy.max_delay)
        
        return max(0, delay)
    
    def _fibonacci(self, n: int) -> int:
        """Calculate Fibonacci number"""
        if n <= 1:
            return n
        
        a, b = 0, 1
        for _ in range(2, n + 1):
            a, b = b, a + b
        
        return b
    
    async def _execute_retry_after_delay(self, 
                                       retry_request: RetryRequest,
                                       attempt: RetryAttempt,
                                       delay: float):
        """Execute retry after delay"""
        try:
            # Wait for delay
            await asyncio.sleep(delay)
            
            # Execute retry
            await self._execute_retry(retry_request, attempt)
            
        except asyncio.CancelledError:
            logger.info(f"Retry {retry_request.retry_id} attempt {attempt.attempt_number} cancelled")
        except Exception as e:
            logger.error(f"Error executing retry {retry_request.retry_id}: {e}")
            attempt.error_message = str(e)
        finally:
            # Clean up scheduled task
            if retry_request.retry_id in self._scheduled_retries:
                del self._scheduled_retries[retry_request.retry_id]
    
    async def _execute_retry(self, retry_request: RetryRequest, attempt: RetryAttempt):
        """Execute a retry attempt"""
        # Acquire retry semaphore
        async with self._retry_semaphore:
            attempt.executed_at = datetime.utcnow()
            
            try:
                # Check circuit breaker again
                endpoint = retry_request.original_request.destination_endpoint
                if not self._check_circuit_breaker(endpoint):
                    attempt.error_message = "Circuit breaker open"
                    await self._schedule_retry(retry_request)
                    return
                
                # Execute transmission
                result = await self.secure_transmitter.transmit_document(
                    retry_request.original_request
                )
                
                attempt.result = result
                attempt.completed_at = datetime.utcnow()
                
                # Update circuit breaker
                success = result.status == TransmissionStatus.DELIVERED
                self._update_circuit_breaker(endpoint, success)
                
                if success:
                    # Retry successful
                    retry_request.final_result = result
                    retry_request.is_completed = True
                    
                    # Update metrics
                    self.metrics['successful_retries'] += 1
                    self._update_success_rate()
                    
                    logger.info(f"Retry {retry_request.retry_id} succeeded on attempt {attempt.attempt_number}")
                    
                else:
                    # Retry failed, schedule next attempt
                    attempt.error_message = result.error_message
                    
                    if retry_request.current_attempt < retry_request.retry_policy.max_attempts:
                        await self._schedule_retry(retry_request)
                    else:
                        # Max attempts reached
                        await self._move_to_dead_letter_queue(retry_request)
                
            except Exception as e:
                attempt.error_message = str(e)
                attempt.completed_at = datetime.utcnow()
                
                # Update circuit breaker
                endpoint = retry_request.original_request.destination_endpoint
                self._update_circuit_breaker(endpoint, False)
                
                # Schedule next retry if possible
                if retry_request.current_attempt < retry_request.retry_policy.max_attempts:
                    await self._schedule_retry(retry_request)
                else:
                    await self._move_to_dead_letter_queue(retry_request)
                
                logger.error(f"Retry {retry_request.retry_id} attempt {attempt.attempt_number} failed: {e}")
    
    async def _move_to_dead_letter_queue(self, retry_request: RetryRequest):
        """Move failed retry to dead letter queue"""
        retry_request.is_completed = True
        
        # Add to dead letter queue
        dead_letter_item = {
            'retry_id': retry_request.retry_id,
            'document_id': retry_request.original_request.document_id,
            'attempts': len(retry_request.attempts),
            'final_error': retry_request.attempts[-1].error_message if retry_request.attempts else None,
            'moved_at': datetime.utcnow().isoformat(),
            'original_request': retry_request.original_request.__dict__,
            'retry_policy': retry_request.retry_policy.__dict__
        }
        
        self._dead_letter_queue.append(dead_letter_item)
        
        # Update metrics
        self.metrics['failed_retries'] += 1
        self.metrics['dead_letter_items'] += 1
        self._update_success_rate()
        
        logger.warning(f"Retry {retry_request.retry_id} moved to dead letter queue after {len(retry_request.attempts)} attempts")
    
    def _update_success_rate(self):
        """Update retry success rate"""
        total_completed = self.metrics['successful_retries'] + self.metrics['failed_retries']
        if total_completed > 0:
            self.metrics['retry_success_rate'] = (
                self.metrics['successful_retries'] / total_completed
            ) * 100
            
            # Update analytics
            self._retry_analytics['success_rates'].append(self.metrics['retry_success_rate'])
    
    async def _monitor_circuit_breakers(self):
        """Monitor circuit breaker health"""
        while self._is_running:
            try:
                current_time = datetime.utcnow()
                
                # Update endpoint health metrics
                for endpoint, circuit_breaker in self._circuit_breakers.items():
                    health_score = 100.0
                    
                    if circuit_breaker.state == CircuitState.OPEN:
                        health_score = 0.0
                    elif circuit_breaker.state == CircuitState.HALF_OPEN:
                        health_score = 50.0
                    elif circuit_breaker.failure_count > 0:
                        health_score = max(0, 100 - (circuit_breaker.failure_count * 20))
                    
                    self.metrics['endpoint_health'][endpoint] = {
                        'health_score': health_score,
                        'state': circuit_breaker.state.value,
                        'failure_count': circuit_breaker.failure_count,
                        'success_count': circuit_breaker.success_count,
                        'last_failure': circuit_breaker.last_failure_time.isoformat() if circuit_breaker.last_failure_time else None,
                        'last_success': circuit_breaker.last_success_time.isoformat() if circuit_breaker.last_success_time else None
                    }
                
                # Calculate average retry delay
                if self._retry_analytics['delays']:
                    self.metrics['average_retry_delay'] = sum(self._retry_analytics['delays']) / len(self._retry_analytics['delays'])
                
                # Sleep before next monitoring cycle
                await asyncio.sleep(30)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in circuit breaker monitor: {e}")
                await asyncio.sleep(5)
    
    async def get_retry_status(self, retry_id: str) -> Optional[RetryRequest]:
        """Get retry status by ID"""
        return self._retry_requests.get(retry_id)
    
    async def get_active_retries(self) -> List[RetryRequest]:
        """Get list of active retries"""
        return [req for req in self._retry_requests.values() if not req.is_completed]
    
    async def cancel_retry(self, retry_id: str) -> bool:
        """Cancel an active retry"""
        if retry_id in self._scheduled_retries:
            task = self._scheduled_retries[retry_id]
            task.cancel()
            del self._scheduled_retries[retry_id]
            
            # Mark as completed
            if retry_id in self._retry_requests:
                self._retry_requests[retry_id].is_completed = True
            
            logger.info(f"Retry {retry_id} cancelled")
            return True
        return False
    
    def get_dead_letter_queue(self) -> List[Dict[str, Any]]:
        """Get dead letter queue items"""
        return list(self._dead_letter_queue)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get retry handler metrics"""
        return {
            **self.metrics,
            'active_retries': len([req for req in self._retry_requests.values() if not req.is_completed]),
            'scheduled_retries': len(self._scheduled_retries),
            'completed_retries': len([req for req in self._retry_requests.values() if req.is_completed]),
            'circuit_breakers': len(self._circuit_breakers),
            'dead_letter_queue_size': len(self._dead_letter_queue)
        }


# Factory functions for easy setup
def create_retry_policy(max_attempts: int = 3,
                       strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF,
                       base_delay: float = 1.0,
                       max_delay: float = 60.0,
                       backoff_multiplier: float = 2.0) -> RetryPolicy:
    """Create retry policy"""
    return RetryPolicy(
        max_attempts=max_attempts,
        strategy=strategy,
        base_delay=base_delay,
        max_delay=max_delay,
        backoff_multiplier=backoff_multiplier
    )


async def create_retry_handler(secure_transmitter: SecureTransmitter,
                              retry_policy: Optional[RetryPolicy] = None) -> RetryHandler:
    """Create and start retry handler"""
    handler = RetryHandler(secure_transmitter, retry_policy)
    await handler.start()
    return handler