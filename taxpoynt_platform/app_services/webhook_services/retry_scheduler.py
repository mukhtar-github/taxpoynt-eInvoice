"""
APP Service: Retry Scheduler
Schedules and manages retries for failed webhook processing
"""

import asyncio
import logging
import heapq
import json
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List, Callable, Awaitable
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import time
import math
from abc import ABC, abstractmethod

from .webhook_receiver import WebhookPayload, WebhookMetadata
from .event_processor import ProcessingResult, ProcessingStatus


class RetryStrategy(str, Enum):
    """Retry strategy types"""
    FIXED_DELAY = "fixed_delay"
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"
    CUSTOM = "custom"


class RetryStatus(str, Enum):
    """Retry job status"""
    SCHEDULED = "scheduled"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    DEAD_LETTER = "dead_letter"


@dataclass
class RetryConfig:
    """Configuration for retry behavior"""
    max_attempts: int = 5
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF
    base_delay_seconds: int = 60  # 1 minute
    max_delay_seconds: int = 3600  # 1 hour
    backoff_multiplier: float = 2.0
    jitter_enabled: bool = True
    jitter_max_seconds: int = 30
    dead_letter_after_attempts: int = 10
    priority_boost_on_retry: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RetryJob:
    """Individual retry job"""
    job_id: str
    webhook_payload: WebhookPayload
    webhook_metadata: WebhookMetadata
    attempt_count: int
    max_attempts: int
    next_retry_at: datetime
    created_at: datetime
    last_attempted_at: Optional[datetime]
    status: RetryStatus
    config: RetryConfig
    failure_reasons: List[str]
    processing_results: List[Dict[str, Any]]
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['next_retry_at'] = self.next_retry_at.isoformat()
        data['created_at'] = self.created_at.isoformat()
        if self.last_attempted_at:
            data['last_attempted_at'] = self.last_attempted_at.isoformat()
        return data
    
    def __lt__(self, other):
        """For priority queue ordering"""
        return self.next_retry_at < other.next_retry_at


class BackoffCalculator(ABC):
    """Abstract base class for backoff calculation"""
    
    @abstractmethod
    def calculate_delay(self, attempt_count: int, config: RetryConfig) -> int:
        """Calculate delay in seconds for the given attempt"""
        pass


class FixedDelayCalculator(BackoffCalculator):
    """Fixed delay backoff calculator"""
    
    def calculate_delay(self, attempt_count: int, config: RetryConfig) -> int:
        return min(config.base_delay_seconds, config.max_delay_seconds)


class ExponentialBackoffCalculator(BackoffCalculator):
    """Exponential backoff calculator"""
    
    def calculate_delay(self, attempt_count: int, config: RetryConfig) -> int:
        delay = config.base_delay_seconds * (config.backoff_multiplier ** (attempt_count - 1))
        return min(int(delay), config.max_delay_seconds)


class LinearBackoffCalculator(BackoffCalculator):
    """Linear backoff calculator"""
    
    def calculate_delay(self, attempt_count: int, config: RetryConfig) -> int:
        delay = config.base_delay_seconds * attempt_count
        return min(delay, config.max_delay_seconds)


class RetryScheduler:
    """
    Manages retry scheduling for failed webhook processing
    Implements various backoff strategies and dead letter queuing
    """
    
    def __init__(self, 
                 default_config: Optional[RetryConfig] = None,
                 max_concurrent_retries: int = 5):
        self.default_config = default_config or RetryConfig()
        self.max_concurrent_retries = max_concurrent_retries
        self.logger = logging.getLogger(__name__)
        
        # Priority queue for scheduled retries (min-heap by next_retry_at)
        self.retry_queue: List[RetryJob] = []
        self.active_retries: Dict[str, RetryJob] = {}
        self.completed_retries: List[RetryJob] = []
        self.dead_letter_queue: List[RetryJob] = []
        
        # Backoff calculators
        self.backoff_calculators = {
            RetryStrategy.FIXED_DELAY: FixedDelayCalculator(),
            RetryStrategy.EXPONENTIAL_BACKOFF: ExponentialBackoffCalculator(),
            RetryStrategy.LINEAR_BACKOFF: LinearBackoffCalculator()
        }
        
        # Retry processing callback
        self.retry_processor: Optional[Callable[[WebhookPayload, WebhookMetadata], Awaitable[ProcessingResult]]] = None
        
        # Scheduler state
        self.is_running = False
        self.scheduler_task: Optional[asyncio.Task] = None
        
        # Statistics
        self.stats = {
            'total_retries_scheduled': 0,
            'total_retries_attempted': 0,
            'successful_retries': 0,
            'failed_retries': 0,
            'dead_letter_jobs': 0,
            'cancelled_jobs': 0,
            'average_retry_delay': 0.0,
            'last_retry_at': None,
            'strategy_stats': {}
        }
    
    def set_retry_processor(self, processor: Callable[[WebhookPayload, WebhookMetadata], Awaitable[ProcessingResult]]):
        """Set the callback function for processing retries"""
        self.retry_processor = processor
    
    async def schedule_retry(self, 
                            webhook_payload: WebhookPayload,
                            webhook_metadata: WebhookMetadata,
                            failure_reason: str,
                            config: Optional[RetryConfig] = None) -> str:
        """
        Schedule a retry for failed webhook processing
        
        Args:
            webhook_payload: Original webhook payload
            webhook_metadata: Original webhook metadata
            failure_reason: Reason for the failure
            config: Retry configuration (uses default if not provided)
            
        Returns:
            Job ID for the scheduled retry
        """
        job_config = config or self.default_config
        job_id = str(uuid.uuid4())
        
        # Calculate next retry time
        attempt_count = webhook_payload.retry_count + 1
        delay_seconds = self._calculate_delay(attempt_count, job_config)
        next_retry_at = datetime.now(timezone.utc) + timedelta(seconds=delay_seconds)
        
        # Create retry job
        retry_job = RetryJob(
            job_id=job_id,
            webhook_payload=webhook_payload,
            webhook_metadata=webhook_metadata,
            attempt_count=attempt_count,
            max_attempts=job_config.max_attempts,
            next_retry_at=next_retry_at,
            created_at=datetime.now(timezone.utc),
            last_attempted_at=None,
            status=RetryStatus.SCHEDULED,
            config=job_config,
            failure_reasons=[failure_reason],
            processing_results=[]
        )
        
        # Add to retry queue
        heapq.heappush(self.retry_queue, retry_job)
        
        # Update statistics
        self.stats['total_retries_scheduled'] += 1
        self._update_strategy_stats(job_config.strategy, 'scheduled')
        
        self.logger.info(
            f"Scheduled retry {job_id} for webhook {webhook_metadata.webhook_id} "
            f"(attempt {attempt_count}/{job_config.max_attempts}) "
            f"in {delay_seconds} seconds"
        )
        
        return job_id
    
    def _calculate_delay(self, attempt_count: int, config: RetryConfig) -> int:
        """Calculate delay for retry attempt"""
        calculator = self.backoff_calculators.get(config.strategy)
        if not calculator:
            calculator = self.backoff_calculators[RetryStrategy.EXPONENTIAL_BACKOFF]
        
        base_delay = calculator.calculate_delay(attempt_count, config)
        
        # Add jitter if enabled
        if config.jitter_enabled:
            import random
            jitter = random.randint(0, config.jitter_max_seconds)
            base_delay += jitter
        
        return base_delay
    
    async def start_scheduler(self):
        """Start the retry scheduler"""
        if self.is_running:
            self.logger.warning("Retry scheduler is already running")
            return
        
        self.is_running = True
        self.scheduler_task = asyncio.create_task(self._scheduler_loop())
        self.logger.info("Retry scheduler started")
    
    async def stop_scheduler(self):
        """Stop the retry scheduler"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        if self.scheduler_task:
            self.scheduler_task.cancel()
            try:
                await self.scheduler_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("Retry scheduler stopped")
    
    async def _scheduler_loop(self):
        """Main scheduler loop"""
        self.logger.info("Retry scheduler loop started")
        
        try:
            while self.is_running:
                await self._process_due_retries()
                await asyncio.sleep(10)  # Check every 10 seconds
                
        except asyncio.CancelledError:
            self.logger.info("Retry scheduler loop cancelled")
        except Exception as e:
            self.logger.error(f"Retry scheduler loop error: {str(e)}")
        finally:
            self.logger.info("Retry scheduler loop ended")
    
    async def _process_due_retries(self):
        """Process retries that are due for execution"""
        current_time = datetime.now(timezone.utc)
        
        # Process due retries (up to max concurrent limit)
        while (len(self.active_retries) < self.max_concurrent_retries and 
               self.retry_queue and 
               self.retry_queue[0].next_retry_at <= current_time):
            
            retry_job = heapq.heappop(self.retry_queue)
            
            # Skip if job was cancelled
            if retry_job.status == RetryStatus.CANCELLED:
                continue
            
            # Move to dead letter if max attempts exceeded
            if retry_job.attempt_count > retry_job.config.dead_letter_after_attempts:
                await self._move_to_dead_letter(retry_job, "Max attempts exceeded")
                continue
            
            # Start retry processing
            await self._execute_retry(retry_job)
    
    async def _execute_retry(self, retry_job: RetryJob):
        """Execute a retry job"""
        if not self.retry_processor:
            self.logger.error(f"No retry processor configured for job {retry_job.job_id}")
            return
        
        retry_job.status = RetryStatus.RUNNING
        retry_job.last_attempted_at = datetime.now(timezone.utc)
        self.active_retries[retry_job.job_id] = retry_job
        
        self.logger.info(
            f"Executing retry {retry_job.job_id} "
            f"(attempt {retry_job.attempt_count}/{retry_job.max_attempts})"
        )
        
        # Update payload retry count
        retry_job.webhook_payload.retry_count = retry_job.attempt_count
        
        try:
            # Execute retry processing
            result = await self.retry_processor(
                retry_job.webhook_payload,
                retry_job.webhook_metadata
            )
            
            # Record result
            retry_job.processing_results.append(result.to_dict())
            
            # Handle result
            if result.success:
                await self._handle_retry_success(retry_job, result)
            else:
                await self._handle_retry_failure(retry_job, result)
                
        except Exception as e:
            self.logger.error(f"Retry execution error for job {retry_job.job_id}: {str(e)}")
            await self._handle_retry_exception(retry_job, str(e))
        
        finally:
            self.active_retries.pop(retry_job.job_id, None)
            self.stats['total_retries_attempted'] += 1
            self.stats['last_retry_at'] = datetime.now(timezone.utc).isoformat()
    
    async def _handle_retry_success(self, retry_job: RetryJob, result: ProcessingResult):
        """Handle successful retry"""
        retry_job.status = RetryStatus.COMPLETED
        self.completed_retries.append(retry_job)
        
        self.stats['successful_retries'] += 1
        self._update_strategy_stats(retry_job.config.strategy, 'successful')
        
        self.logger.info(
            f"Retry {retry_job.job_id} completed successfully "
            f"after {retry_job.attempt_count} attempts"
        )
    
    async def _handle_retry_failure(self, retry_job: RetryJob, result: ProcessingResult):
        """Handle failed retry"""
        retry_job.failure_reasons.append(result.message)
        
        # Check if should retry again
        if retry_job.attempt_count < retry_job.max_attempts:
            # Schedule next retry
            delay_seconds = self._calculate_delay(retry_job.attempt_count + 1, retry_job.config)
            retry_job.next_retry_at = datetime.now(timezone.utc) + timedelta(seconds=delay_seconds)
            retry_job.status = RetryStatus.SCHEDULED
            retry_job.attempt_count += 1
            
            heapq.heappush(self.retry_queue, retry_job)
            
            self.logger.info(
                f"Retry {retry_job.job_id} failed, scheduling next attempt "
                f"({retry_job.attempt_count}/{retry_job.max_attempts}) in {delay_seconds}s"
            )
        else:
            # Move to dead letter
            await self._move_to_dead_letter(retry_job, "Max retry attempts exceeded")
        
        self.stats['failed_retries'] += 1
        self._update_strategy_stats(retry_job.config.strategy, 'failed')
    
    async def _handle_retry_exception(self, retry_job: RetryJob, error_message: str):
        """Handle retry execution exception"""
        retry_job.failure_reasons.append(f"Exception: {error_message}")
        
        # Treat as failure and reschedule if possible
        if retry_job.attempt_count < retry_job.max_attempts:
            delay_seconds = self._calculate_delay(retry_job.attempt_count + 1, retry_job.config)
            retry_job.next_retry_at = datetime.now(timezone.utc) + timedelta(seconds=delay_seconds)
            retry_job.status = RetryStatus.SCHEDULED
            retry_job.attempt_count += 1
            
            heapq.heappush(self.retry_queue, retry_job)
        else:
            await self._move_to_dead_letter(retry_job, f"Exception during retry: {error_message}")
        
        self.stats['failed_retries'] += 1
    
    async def _move_to_dead_letter(self, retry_job: RetryJob, reason: str):
        """Move job to dead letter queue"""
        retry_job.status = RetryStatus.DEAD_LETTER
        retry_job.failure_reasons.append(f"Dead letter: {reason}")
        self.dead_letter_queue.append(retry_job)
        
        self.stats['dead_letter_jobs'] += 1
        self._update_strategy_stats(retry_job.config.strategy, 'dead_letter')
        
        self.logger.warning(
            f"Moved retry job {retry_job.job_id} to dead letter queue: {reason}"
        )
    
    def _update_strategy_stats(self, strategy: RetryStrategy, outcome: str):
        """Update statistics for retry strategy"""
        strategy_key = strategy.value
        if strategy_key not in self.stats['strategy_stats']:
            self.stats['strategy_stats'][strategy_key] = {
                'scheduled': 0,
                'successful': 0,
                'failed': 0,
                'dead_letter': 0
            }
        
        self.stats['strategy_stats'][strategy_key][outcome] += 1
    
    async def cancel_retry(self, job_id: str) -> bool:
        """Cancel a scheduled retry"""
        # Check active retries
        if job_id in self.active_retries:
            self.logger.warning(f"Cannot cancel active retry job {job_id}")
            return False
        
        # Find and cancel in retry queue
        for job in self.retry_queue:
            if job.job_id == job_id:
                job.status = RetryStatus.CANCELLED
                self.stats['cancelled_jobs'] += 1
                self.logger.info(f"Cancelled retry job {job_id}")
                return True
        
        return False
    
    async def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a retry job"""
        # Check active retries
        if job_id in self.active_retries:
            return self.active_retries[job_id].to_dict()
        
        # Check scheduled retries
        for job in self.retry_queue:
            if job.job_id == job_id:
                return job.to_dict()
        
        # Check completed retries
        for job in self.completed_retries:
            if job.job_id == job_id:
                return job.to_dict()
        
        # Check dead letter queue
        for job in self.dead_letter_queue:
            if job.job_id == job_id:
                return job.to_dict()
        
        return None
    
    async def get_queue_status(self) -> Dict[str, Any]:
        """Get status of all retry queues"""
        return {
            'scheduled_retries': len(self.retry_queue),
            'active_retries': len(self.active_retries),
            'completed_retries': len(self.completed_retries),
            'dead_letter_queue': len(self.dead_letter_queue),
            'max_concurrent_retries': self.max_concurrent_retries,
            'is_running': self.is_running,
            'next_retry_at': (
                self.retry_queue[0].next_retry_at.isoformat() 
                if self.retry_queue else None
            ),
            'stats': self.stats.copy(),
            'active_jobs': [
                {
                    'job_id': job.job_id,
                    'attempt_count': job.attempt_count,
                    'webhook_id': job.webhook_metadata.webhook_id,
                    'started_at': job.last_attempted_at.isoformat() if job.last_attempted_at else None
                }
                for job in self.active_retries.values()
            ]
        }
    
    async def requeue_dead_letter_job(self, job_id: str) -> bool:
        """Requeue a job from dead letter queue"""
        for i, job in enumerate(self.dead_letter_queue):
            if job.job_id == job_id:
                # Remove from dead letter and reschedule
                dead_job = self.dead_letter_queue.pop(i)
                dead_job.status = RetryStatus.SCHEDULED
                dead_job.next_retry_at = datetime.now(timezone.utc) + timedelta(seconds=60)
                
                heapq.heappush(self.retry_queue, dead_job)
                
                self.logger.info(f"Requeued dead letter job {job_id}")
                return True
        
        return False
    
    async def clear_completed_jobs(self, older_than_hours: int = 24):
        """Clear completed jobs older than specified hours"""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=older_than_hours)
        
        original_count = len(self.completed_retries)
        self.completed_retries = [
            job for job in self.completed_retries
            if job.created_at > cutoff_time
        ]
        
        cleared_count = original_count - len(self.completed_retries)
        if cleared_count > 0:
            self.logger.info(f"Cleared {cleared_count} completed retry jobs")
        
        return cleared_count
    
    async def health_check(self) -> Dict[str, Any]:
        """Get retry scheduler health status"""
        queue_size = len(self.retry_queue)
        active_count = len(self.active_retries)
        dead_letter_count = len(self.dead_letter_queue)
        
        success_rate = 0.0
        if self.stats['total_retries_attempted'] > 0:
            success_rate = (
                self.stats['successful_retries'] / self.stats['total_retries_attempted'] * 100
            )
        
        status = "healthy"
        if not self.is_running:
            status = "stopped"
        elif queue_size > 1000:
            status = "overloaded"
        elif dead_letter_count > queue_size and queue_size > 0:
            status = "degraded"
        
        return {
            'status': status,
            'service': 'retry_scheduler',
            'is_running': self.is_running,
            'queue_size': queue_size,
            'active_retries': active_count,
            'dead_letter_size': dead_letter_count,
            'success_rate': round(success_rate, 2),
            'max_concurrent': self.max_concurrent_retries,
            'supported_strategies': [strategy.value for strategy in RetryStrategy],
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
    
    async def cleanup(self):
        """Cleanup scheduler resources"""
        self.logger.info("Retry scheduler cleanup initiated")
        
        # Stop scheduler
        await self.stop_scheduler()
        
        # Log final statistics
        self.logger.info(f"Final retry statistics: {self.stats}")
        
        # Clear queues
        self.retry_queue.clear()
        self.active_retries.clear()
        self.completed_retries.clear()
        self.dead_letter_queue.clear()
        
        self.logger.info("Retry scheduler cleanup completed")


# Factory functions
def create_retry_scheduler(max_concurrent: int = 5) -> RetryScheduler:
    """Create retry scheduler with standard configuration"""
    return RetryScheduler(max_concurrent_retries=max_concurrent)


def create_retry_config(strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF,
                       max_attempts: int = 5,
                       base_delay: int = 60) -> RetryConfig:
    """Create retry configuration with standard settings"""
    return RetryConfig(
        max_attempts=max_attempts,
        strategy=strategy,
        base_delay_seconds=base_delay
    )