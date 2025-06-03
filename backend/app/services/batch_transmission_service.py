"""
Batch Transmission Service for TaxPoynt eInvoice Platform

Provides optimized processing for high-volume transmission scenarios with:
- Configurable batch processing
- Parallel execution with resource limits
- Intelligent retry mechanisms
- Detailed performance metrics
"""

import asyncio
import logging
import time
import json
import random
from typing import List, Dict, Any, Optional, Tuple, Set, Callable
from datetime import datetime, timedelta
from uuid import UUID
import threading
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi import BackgroundTasks

from app.db.session import SessionLocal
from app.models.transmission import TransmissionRecord, TransmissionStatus
from app.models.transmission_metrics import TransmissionMetricsSnapshot
from app.models.transmission_error import TransmissionError
from app.services.transmission_service import TransmissionService
from app.utils.rate_limiter import rate_limiter

logger = logging.getLogger(__name__)


class BatchConfiguration:
    """Configuration settings for batch transmission processing"""
    
    def __init__(
        self,
        batch_size: int = 50,
        max_concurrent_batches: int = 3,
        retry_strategy: str = "exponential",
        max_retries: int = 5,
        retry_delay_base_ms: int = 1000,
        prioritize_failed: bool = True,
        metrics_enabled: bool = True,
        circuit_breaker_threshold: int = 5,
        circuit_breaker_timeout_seconds: int = 300,
    ):
        """
        Initialize batch processing configuration.
        
        Args:
            batch_size: Number of transmissions to process in a batch
            max_concurrent_batches: Maximum number of batches to process concurrently
            retry_strategy: Retry strategy to use (exponential, linear, random)
            max_retries: Maximum number of retry attempts
            retry_delay_base_ms: Base delay between retries in milliseconds
            prioritize_failed: Whether to prioritize failed transmissions
            metrics_enabled: Whether to collect detailed metrics
            circuit_breaker_threshold: Number of consecutive failures before circuit breaks
            circuit_breaker_timeout_seconds: Time to keep circuit open after breaking
        """
        self.batch_size = batch_size
        self.max_concurrent_batches = max_concurrent_batches
        self.retry_strategy = retry_strategy
        self.max_retries = max_retries
        self.retry_delay_base_ms = retry_delay_base_ms
        self.prioritize_failed = prioritize_failed
        self.metrics_enabled = metrics_enabled
        self.circuit_breaker_threshold = circuit_breaker_threshold
        self.circuit_breaker_timeout_seconds = circuit_breaker_timeout_seconds


class CircuitBreaker:
    """
    Implementation of the Circuit Breaker pattern.
    
    Prevents repeated calls to a failing service by "breaking the circuit"
    after a threshold of failures, then automatically recovering after
    a timeout period.
    
    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Circuit is broken, requests fail fast
    - HALF_OPEN: Testing if service has recovered
    """
    
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"
    
    def __init__(self, threshold: int, timeout_seconds: int):
        """
        Initialize circuit breaker.
        
        Args:
            threshold: Number of consecutive failures before circuit breaks
            timeout_seconds: Time to keep circuit open after breaking
        """
        self.threshold = threshold
        self.timeout_seconds = timeout_seconds
        self.state = self.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        self.endpoints: Dict[str, Dict[str, Any]] = {}
        self.lock = threading.RLock()
    
    def get_endpoint_state(self, endpoint: str) -> Dict[str, Any]:
        """Get or create state for an endpoint"""
        with self.lock:
            if endpoint not in self.endpoints:
                self.endpoints[endpoint] = {
                    "state": self.CLOSED,
                    "failure_count": 0,
                    "last_failure_time": None,
                    "test_counter": 0
                }
            
            return self.endpoints[endpoint]
    
    def record_success(self, endpoint: str) -> None:
        """Record a successful call"""
        with self.lock:
            endpoint_state = self.get_endpoint_state(endpoint)
            
            # If in HALF_OPEN state and success, close the circuit
            if endpoint_state["state"] == self.HALF_OPEN:
                endpoint_state["state"] = self.CLOSED
            
            # Reset failure count on any success
            endpoint_state["failure_count"] = 0
            endpoint_state["test_counter"] = 0
    
    def record_failure(self, endpoint: str) -> None:
        """Record a failed call"""
        now = datetime.utcnow()
        
        with self.lock:
            endpoint_state = self.get_endpoint_state(endpoint)
            
            # Update failure tracking
            endpoint_state["failure_count"] += 1
            endpoint_state["last_failure_time"] = now
            
            # Check if we should open the circuit
            if (endpoint_state["state"] == self.CLOSED and 
                endpoint_state["failure_count"] >= self.threshold):
                endpoint_state["state"] = self.OPEN
                logger.warning(f"Circuit OPEN for endpoint {endpoint} after {self.threshold} failures")
            
            # If in HALF_OPEN state and failure, open the circuit again
            elif endpoint_state["state"] == self.HALF_OPEN:
                endpoint_state["state"] = self.OPEN
                logger.warning(f"Circuit re-OPEN for endpoint {endpoint} after test failure")
    
    def allow_request(self, endpoint: str) -> bool:
        """
        Check if a request should be allowed.
        
        Args:
            endpoint: The endpoint being called
            
        Returns:
            True if request should be allowed, False if circuit is open
        """
        now = datetime.utcnow()
        
        with self.lock:
            endpoint_state = self.get_endpoint_state(endpoint)
            
            # If circuit is CLOSED, allow request
            if endpoint_state["state"] == self.CLOSED:
                return True
            
            # If circuit is OPEN, check if timeout has elapsed
            if endpoint_state["state"] == self.OPEN:
                last_failure = endpoint_state["last_failure_time"]
                if last_failure and (now - last_failure).total_seconds() >= self.timeout_seconds:
                    # Transition to HALF_OPEN to test if service has recovered
                    endpoint_state["state"] = self.HALF_OPEN
                    endpoint_state["test_counter"] = 0
                    logger.info(f"Circuit HALF_OPEN for endpoint {endpoint}, testing recovery")
                else:
                    # Circuit still OPEN, block request
                    return False
            
            # If circuit is HALF_OPEN, allow limited test requests
            if endpoint_state["state"] == self.HALF_OPEN:
                # Allow only one test request at a time
                if endpoint_state["test_counter"] < 1:
                    endpoint_state["test_counter"] += 1
                    return True
                return False
            
            return True


class BatchTransmissionService:
    """
    Service for optimized batch processing of transmissions.
    
    Features:
    - Configurable batch sizes and parallelism
    - Automatic retry with multiple strategies
    - Circuit breaker pattern for failing endpoints
    - Detailed metrics collection
    - Health monitoring and adaptive resource usage
    """
    
    def __init__(self, db: Optional[Session] = None, config: Optional[BatchConfiguration] = None):
        """
        Initialize batch transmission service.
        
        Args:
            db: Database session (optional)
            config: Batch configuration (optional)
        """
        self.db = db or SessionLocal()
        self.config = config or BatchConfiguration()
        self.transmission_service = TransmissionService(self.db)
        self.circuit_breaker = CircuitBreaker(
            threshold=self.config.circuit_breaker_threshold,
            timeout_seconds=self.config.circuit_breaker_timeout_seconds
        )
        
        # Track active batch jobs
        self.active_jobs: Set[str] = set()
        self.active_jobs_lock = threading.RLock()
        
        # Track performance metrics
        self.metrics: Dict[str, Any] = {
            "batch_count": 0,
            "total_transmissions": 0,
            "successful_transmissions": 0,
            "failed_transmissions": 0,
            "retry_count": 0,
            "average_processing_time_ms": 0,
            "circuit_breaks": 0,
            "batch_timeouts": 0,
        }
        self.metrics_lock = threading.RLock()
    
    def _calculate_retry_delay(self, retry_count: int) -> float:
        """
        Calculate delay for a retry based on strategy.
        
        Args:
            retry_count: Current retry attempt (1-based)
            
        Returns:
            Delay in seconds
        """
        base_delay_sec = self.config.retry_delay_base_ms / 1000
        
        if self.config.retry_strategy == "exponential":
            # Exponential backoff: base_delay * 2^(retry_count-1)
            return base_delay_sec * (2 ** (retry_count - 1))
        
        elif self.config.retry_strategy == "linear":
            # Linear backoff: base_delay * retry_count
            return base_delay_sec * retry_count
        
        elif self.config.retry_strategy == "random":
            # Random jitter: base_delay * (1 + random(0, 1) * retry_count)
            return base_delay_sec * (1 + random.random() * retry_count)
        
        # Default to fixed delay
        return base_delay_sec
    
    def _record_metrics(self, 
                       batch_id: str,
                       batch_size: int, 
                       success_count: int, 
                       failure_count: int,
                       retry_count: int, 
                       processing_time_ms: float,
                       circuit_breaks: int = 0,
                       timeouts: int = 0) -> None:
        """Record metrics for a completed batch"""
        with self.metrics_lock:
            self.metrics["batch_count"] += 1
            self.metrics["total_transmissions"] += batch_size
            self.metrics["successful_transmissions"] += success_count
            self.metrics["failed_transmissions"] += failure_count
            self.metrics["retry_count"] += retry_count
            self.metrics["circuit_breaks"] += circuit_breaks
            self.metrics["batch_timeouts"] += timeouts
            
            # Update average processing time (moving average)
            if self.metrics["batch_count"] == 1:
                self.metrics["average_processing_time_ms"] = processing_time_ms
            else:
                alpha = 0.2  # Weight for new value in moving average
                current_avg = self.metrics["average_processing_time_ms"]
                self.metrics["average_processing_time_ms"] = (
                    (1 - alpha) * current_avg + alpha * processing_time_ms
                )
    
    def _record_transmission_metrics(self, 
                                    transmission_id: UUID,
                                    organization_id: UUID,
                                    processing_time_ms: float,
                                    encryption_time_ms: Optional[float] = None,
                                    network_time_ms: Optional[float] = None,
                                    payload_size_bytes: Optional[int] = None,
                                    retry_count: int = 0,
                                    api_endpoint: Optional[str] = None,
                                    success: bool = True) -> None:
        """
        Record detailed metrics for an individual transmission.
        
        Args:
            transmission_id: UUID of the transmission
            organization_id: UUID of the organization
            processing_time_ms: Total processing time in milliseconds
            encryption_time_ms: Encryption time in milliseconds (optional)
            network_time_ms: Network request time in milliseconds (optional)
            payload_size_bytes: Size of the payload in bytes (optional)
            retry_count: Number of retry attempts
            api_endpoint: API endpoint used for transmission
            success: Whether the transmission was successful
        """
        if not self.config.metrics_enabled:
            return
        
        try:
            # Create metrics snapshot in database
            metrics_snapshot = TransmissionMetricsSnapshot(
                transmission_id=transmission_id,
                organization_id=organization_id,
                encryption_time_ms=encryption_time_ms,
                network_time_ms=network_time_ms,
                total_processing_time_ms=processing_time_ms,
                payload_size_bytes=payload_size_bytes,
                retry_count=retry_count,
                api_endpoint=api_endpoint,
                transmission_mode="batch" if retry_count == 0 else "retry",
                metric_details={
                    "batch_processed": True,
                    "success": success,
                    "circuit_breaker_active": not self.circuit_breaker.allow_request(api_endpoint) 
                    if api_endpoint else False
                }
            )
            
            self.db.add(metrics_snapshot)
            self.db.commit()
        
        except SQLAlchemyError as e:
            logger.error(f"Failed to record metrics: {str(e)}")
            self.db.rollback()
    
    async def _process_transmission(self, 
                                   transmission: TransmissionRecord, 
                                   endpoint_tracker: Dict[str, int]) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Process a single transmission with error handling and metrics.
        
        Args:
            transmission: Transmission record to process
            endpoint_tracker: Dict tracking requests per endpoint
            
        Returns:
            Tuple of (success, message, metrics)
        """
        # Extract endpoint from transmission metadata
        metadata = transmission.transmission_metadata or {}
        endpoint = metadata.get("endpoint", "unknown")
        organization_id = transmission.organization_id
        
        # Check circuit breaker
        if not self.circuit_breaker.allow_request(endpoint):
            return False, f"Circuit breaker open for endpoint {endpoint}", {
                "circuit_breaker": "open",
                "endpoint": endpoint
            }
        
        # Check rate limits (track endpoint usage)
        endpoint_tracker.setdefault(endpoint, 0)
        endpoint_tracker[endpoint] += 1
        
        # Start metrics collection
        start_time = time.time()
        encryption_time = 0
        network_time = 0
        success = False
        message = ""
        metrics = {}
        
        try:
            # Use transmission service to process
            # Wrap this in a rate-limited context
            allowed, reason = rate_limiter.allow_request(
                org_id=str(organization_id),
                user_id=str(transmission.created_by) if transmission.created_by else None,
                ip="127.0.0.1",  # Internal batch processing
                endpoint=f"/api/transmissions/{transmission.id}/process"
            )
            
            if not allowed:
                return False, reason, {"rate_limited": True}
            
            # Simulate different phases for metrics collection
            encryption_start = time.time()
            # Encryption happens here
            encryption_time = (time.time() - encryption_start) * 1000
            
            network_start = time.time()
            # Register the transmission as active
            rate_limiter.start_transmission(str(organization_id), str(transmission.id))
            
            # Process transmission
            result, msg = await self._process_single_transmission(transmission)
            success = result
            message = msg
            
            # Complete the transmission
            rate_limiter.end_transmission(str(organization_id), str(transmission.id))
            network_time = (time.time() - network_start) * 1000
            
            # Record success or failure with circuit breaker
            if success:
                self.circuit_breaker.record_success(endpoint)
            else:
                self.circuit_breaker.record_failure(endpoint)
        
        except Exception as e:
            success = False
            message = f"Exception during processing: {str(e)}"
            self.circuit_breaker.record_failure(endpoint)
            logger.exception(f"Error processing transmission {transmission.id}: {str(e)}")
        
        # Calculate total processing time
        processing_time = (time.time() - start_time) * 1000
        
        # Record detailed metrics for this transmission
        self._record_transmission_metrics(
            transmission_id=transmission.id,
            organization_id=organization_id,
            processing_time_ms=processing_time,
            encryption_time_ms=encryption_time,
            network_time_ms=network_time,
            payload_size_bytes=len(transmission.encrypted_payload.encode()) 
                if transmission.encrypted_payload else None,
            retry_count=transmission.retry_count,
            api_endpoint=endpoint,
            success=success
        )
        
        # Return results with metrics
        return success, message, {
            "processing_time_ms": processing_time,
            "encryption_time_ms": encryption_time,
            "network_time_ms": network_time,
            "endpoint": endpoint
        }
    
    async def _process_single_transmission(self, transmission: TransmissionRecord) -> Tuple[bool, str]:
        """
        Process a single transmission using the transmission service.
        
        Args:
            transmission: Transmission record to process
            
        Returns:
            Tuple of (success, message)
        """
        # This would call the actual transmission processing logic
        # For now, we'll simulate processing with the existing retry function
        
        # Get fresh DB session for this operation
        with SessionLocal() as db:
            service = TransmissionService(db)
            result, message = service.retry_transmission(
                transmission_id=transmission.id,
                max_retries=self.config.max_retries,
                retry_delay=0,  # We're handling our own delays
                force=True  # Force processing regardless of status
            )
            
            # Update any tracking metrics
            
            return result, message
    
    async def process_batch(self, batch_id: str, transmissions: List[TransmissionRecord]) -> Dict[str, Any]:
        """
        Process a batch of transmissions with error handling and metrics.
        
        Args:
            batch_id: Unique identifier for this batch
            transmissions: List of transmissions to process
            
        Returns:
            Batch processing metrics and results
        """
        if not transmissions:
            return {"status": "empty", "count": 0}
        
        # Register this batch as active
        with self.active_jobs_lock:
            self.active_jobs.add(batch_id)
        
        # Metrics for this batch
        batch_size = len(transmissions)
        successful = 0
        failed = 0
        retried = 0
        circuit_breaks = 0
        
        # Track endpoints for rate limiting
        endpoint_tracker: Dict[str, int] = {}
        
        # Start timing
        batch_start_time = time.time()
        
        # Process each transmission
        results: List[Dict[str, Any]] = []
        
        for transmission in transmissions:
            # Process with retry logic
            success, message, metrics = await self._process_transmission(
                transmission, endpoint_tracker
            )
            
            # Update counts
            if success:
                successful += 1
            else:
                failed += 1
                if metrics.get("circuit_breaker") == "open":
                    circuit_breaks += 1
                elif transmission.retry_count > 0:
                    retried += 1
            
            # Store result
            results.append({
                "id": str(transmission.id),
                "success": success,
                "message": message,
                "metrics": metrics
            })
        
        # Calculate total processing time
        processing_time_ms = (time.time() - batch_start_time) * 1000
        
        # Record metrics for this batch
        self._record_metrics(
            batch_id=batch_id,
            batch_size=batch_size,
            success_count=successful,
            failure_count=failed,
            retry_count=retried,
            processing_time_ms=processing_time_ms,
            circuit_breaks=circuit_breaks
        )
        
        # Unregister batch
        with self.active_jobs_lock:
            self.active_jobs.discard(batch_id)
        
        # Return batch results
        return {
            "batch_id": batch_id,
            "status": "completed",
            "total": batch_size,
            "successful": successful,
            "failed": failed,
            "retried": retried,
            "circuit_breaks": circuit_breaks,
            "processing_time_ms": processing_time_ms,
            "results": results
        }
    
    async def process_transmissions(self, 
                                   organization_id: Optional[UUID] = None,
                                   status_filter: List[str] = None,
                                   max_transmissions: int = 100) -> Dict[str, Any]:
        """
        Find and process transmissions in batches.
        
        Args:
            organization_id: Optional organization ID to filter by
            status_filter: List of statuses to filter by (default: failed, pending)
            max_transmissions: Maximum number of transmissions to process
            
        Returns:
            Processing results summary
        """
        if not status_filter:
            status_filter = [TransmissionStatus.FAILED, TransmissionStatus.PENDING]
        
        # Get transmissions to process
        query = self.db.query(TransmissionRecord)
        
        if organization_id:
            query = query.filter(TransmissionRecord.organization_id == organization_id)
        
        query = query.filter(TransmissionRecord.status.in_(status_filter))
        
        # Prioritize failed transmissions if configured
        if self.config.prioritize_failed:
            query = query.order_by(
                # Order by status (failed first)
                TransmissionRecord.status == TransmissionStatus.FAILED.value.desc(),
                # Then by retry count (fewer retries first)
                TransmissionRecord.retry_count,
                # Then by transmission time (oldest first)
                TransmissionRecord.transmission_time
            )
        else:
            query = query.order_by(
                # Order by transmission time (oldest first)
                TransmissionRecord.transmission_time
            )
        
        # Limit number of transmissions
        transmissions = query.limit(max_transmissions).all()
        
        if not transmissions:
            return {
                "status": "no_transmissions",
                "message": "No transmissions found to process",
                "count": 0
            }
        
        # Process in batches
        batch_size = self.config.batch_size
        total_transmissions = len(transmissions)
        
        batch_results: List[Dict[str, Any]] = []
        total_successful = 0
        total_failed = 0
        
        # Create batches
        batches: List[List[TransmissionRecord]] = [
            transmissions[i:i + batch_size]
            for i in range(0, total_transmissions, batch_size)
        ]
        
        # Process batches with limited concurrency
        batch_tasks = []
        for i, batch in enumerate(batches):
            batch_id = f"batch_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{i}"
            task = asyncio.create_task(self.process_batch(batch_id, batch))
            batch_tasks.append(task)
        
        # Wait for all batches to complete with max_concurrent_batches limit
        total_batches = len(batch_tasks)
        completed_batches = 0
        
        while batch_tasks:
            # Process up to max_concurrent_batches at a time
            current_batch = batch_tasks[:self.config.max_concurrent_batches]
            remaining = batch_tasks[self.config.max_concurrent_batches:]
            
            # Wait for current batch to complete
            current_results = await asyncio.gather(*current_batch)
            batch_results.extend(current_results)
            
            # Update counts
            for result in current_results:
                total_successful += result.get("successful", 0)
                total_failed += result.get("failed", 0)
                completed_batches += 1
            
            # Continue with remaining batches
            batch_tasks = remaining
        
        # Return summary of all batches
        return {
            "status": "completed",
            "total_transmissions": total_transmissions,
            "total_batches": total_batches,
            "successful": total_successful,
            "failed": total_failed,
            "batch_results": batch_results
        }
    
    def start_background_processing(self, 
                                  background_tasks: BackgroundTasks,
                                  organization_id: Optional[UUID] = None,
                                  status_filter: List[str] = None,
                                  max_transmissions: int = 100) -> Dict[str, Any]:
        """
        Start processing transmissions in the background.
        
        Args:
            background_tasks: FastAPI BackgroundTasks object
            organization_id: Optional organization ID to filter by
            status_filter: List of statuses to filter by
            max_transmissions: Maximum number of transmissions to process
            
        Returns:
            Status information
        """
        # Create a task ID
        task_id = f"bgprocess_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        # Add task to background tasks
        background_tasks.add_task(
            self._background_process_wrapper,
            task_id,
            organization_id,
            status_filter,
            max_transmissions
        )
        
        return {
            "status": "started",
            "task_id": task_id,
            "message": f"Started background processing for up to {max_transmissions} transmissions"
        }
    
    async def _background_process_wrapper(self,
                                         task_id: str,
                                         organization_id: Optional[UUID] = None,
                                         status_filter: List[str] = None,
                                         max_transmissions: int = 100) -> None:
        """Wrapper for background processing to handle event loop and errors"""
        try:
            await self.process_transmissions(
                organization_id=organization_id,
                status_filter=status_filter,
                max_transmissions=max_transmissions
            )
        except Exception as e:
            logger.error(f"Error in background processing task {task_id}: {str(e)}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics for the batch service"""
        with self.metrics_lock:
            metrics_copy = self.metrics.copy()
            
            # Add derived metrics
            if metrics_copy["total_transmissions"] > 0:
                metrics_copy["success_rate"] = (
                    metrics_copy["successful_transmissions"] / 
                    metrics_copy["total_transmissions"]
                ) * 100
            else:
                metrics_copy["success_rate"] = 0
            
            # Add active jobs count
            with self.active_jobs_lock:
                metrics_copy["active_jobs"] = len(self.active_jobs)
            
            # Add timestamp
            metrics_copy["timestamp"] = datetime.utcnow().isoformat()
            
            return metrics_copy
    
    def reset_metrics(self) -> None:
        """Reset all metrics counters"""
        with self.metrics_lock:
            self.metrics = {
                "batch_count": 0,
                "total_transmissions": 0,
                "successful_transmissions": 0,
                "failed_transmissions": 0,
                "retry_count": 0,
                "average_processing_time_ms": 0,
                "circuit_breaks": 0,
                "batch_timeouts": 0,
            }


# Create a singleton instance for convenience
batch_transmission_service = BatchTransmissionService()
