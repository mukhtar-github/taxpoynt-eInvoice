"""
POS Queue Service for real-time transaction processing.

This service provides high-priority queue management for POS transactions
with sub-2-second SLA requirements and circuit breaker protection.
"""

import json
import time
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Callable, Awaitable
from uuid import UUID, uuid4

import redis
from fastapi import BackgroundTasks
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.redis import get_redis_client
from app.db.session import SessionLocal
from app.services.circuit_breaker import CircuitBreaker
from app.crud.pos_transaction import create_pos_transaction, update_pos_transaction
from app.crud.pos_connection import get_pos_connection
from app.utils.logger import get_logger

logger = get_logger(__name__)


class POSQueueService:
    """Service for handling high-priority POS transaction processing with circuit breaker protection."""
    
    def __init__(self):
        """Initialize the POS queue service."""
        self.redis_client = get_redis_client()
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=30,
            expected_exception=Exception
        )
        
        # Queue configurations
        self.queues = {
            "immediate": "pos_immediate_queue",      # Ultra-high priority
            "high": "pos_high_priority_queue",       # High priority  
            "standard": "pos_standard_queue",        # Standard processing
            "retry": "pos_retry_queue",              # Failed transactions
            "dead_letter": "pos_dead_letter_queue"   # Permanently failed
        }
        
        # Performance metrics
        self.metrics = {
            "processed_count": "pos_processed_count",
            "failed_count": "pos_failed_count",
            "avg_processing_time": "pos_avg_processing_time",
            "queue_lengths": "pos_queue_lengths"
        }
        
        # SLA configuration
        self.sla_targets = {
            "immediate": 1.0,    # 1 second
            "high": 2.0,         # 2 seconds
            "standard": 5.0,     # 5 seconds
            "retry": 10.0        # 10 seconds
        }
    
    async def enqueue_transaction(
        self, 
        transaction_data: Dict[str, Any], 
        background_tasks: BackgroundTasks,
        priority: str = "high",
        connection_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Enqueue a transaction for processing with specified priority.
        
        Args:
            transaction_data: Transaction data to process
            background_tasks: FastAPI background tasks
            priority: Processing priority (immediate, high, standard)
            connection_id: POS connection ID
            
        Returns:
            Dict containing enqueue result and transaction ID
        """
        transaction_id = str(uuid4())
        enqueue_time = datetime.now()
        
        try:
            # Validate transaction data
            if not self._validate_transaction_data(transaction_data):
                raise ValueError("Invalid transaction data format")
            
            # Create queue entry
            queue_entry = {
                "id": transaction_id,
                "connection_id": str(connection_id) if connection_id else None,
                "data": transaction_data,
                "priority": priority,
                "attempts": 0,
                "max_attempts": 3,
                "enqueued_at": enqueue_time.isoformat(),
                "sla_target": self.sla_targets.get(priority, 5.0)
            }
            
            # For immediate priority, process in background task for ultra-low latency
            if priority == "immediate":
                background_tasks.add_task(
                    self._process_immediate_transaction,
                    queue_entry
                )
                
                # Also add to persistent queue for guaranteed processing
                await self._add_to_persistent_queue(queue_entry, "high")
            else:
                # Add to appropriate priority queue
                await self._add_to_persistent_queue(queue_entry, priority)
            
            # Update metrics
            await self._update_metrics("enqueued", priority)
            
            logger.info(
                f"Transaction {transaction_id} enqueued with priority {priority}",
                extra={
                    "transaction_id": transaction_id,
                    "priority": priority,
                    "connection_id": connection_id
                }
            )
            
            return {
                "success": True,
                "transaction_id": transaction_id,
                "priority": priority,
                "estimated_processing_time": self.sla_targets.get(priority, 5.0),
                "enqueued_at": enqueue_time.isoformat()
            }
            
        except Exception as e:
            logger.error(
                f"Failed to enqueue transaction: {str(e)}",
                extra={
                    "transaction_data": transaction_data,
                    "priority": priority,
                    "error": str(e)
                }
            )
            
            return {
                "success": False,
                "error": str(e),
                "transaction_id": transaction_id
            }
    
    async def _process_immediate_transaction(self, queue_entry: Dict[str, Any]) -> None:
        """
        Process transaction immediately for ultra-low latency (sub-1-second).
        
        Args:
            queue_entry: Queue entry containing transaction data
        """
        start_time = time.time()
        transaction_id = queue_entry["id"]
        
        try:
            # Use circuit breaker to protect against cascading failures
            result = await self.circuit_breaker.call(
                self._process_transaction_with_timeout,
                queue_entry,
                timeout=0.8  # 800ms timeout for immediate processing
            )
            
            processing_time = time.time() - start_time
            
            if processing_time <= self.sla_targets["immediate"]:
                await self._update_metrics("immediate_success", processing_time)
                logger.info(
                    f"Immediate transaction {transaction_id} processed in {processing_time:.3f}s"
                )
            else:
                await self._update_metrics("immediate_sla_miss", processing_time)
                logger.warning(
                    f"Immediate transaction {transaction_id} missed SLA: {processing_time:.3f}s"
                )
            
        except Exception as e:
            processing_time = time.time() - start_time
            await self._update_metrics("immediate_failure", processing_time)
            
            logger.error(
                f"Immediate transaction {transaction_id} failed: {str(e)}",
                extra={
                    "transaction_id": transaction_id,
                    "processing_time": processing_time,
                    "error": str(e)
                }
            )
            
            # Add to retry queue for later processing
            queue_entry["attempts"] += 1
            queue_entry["last_error"] = str(e)
            queue_entry["failed_at"] = datetime.now().isoformat()
            
            await self._add_to_persistent_queue(queue_entry, "retry")
    
    async def _process_transaction_with_timeout(
        self, 
        queue_entry: Dict[str, Any], 
        timeout: float
    ) -> Dict[str, Any]:
        """
        Process transaction with timeout protection.
        
        Args:
            queue_entry: Queue entry containing transaction data
            timeout: Maximum processing time in seconds
            
        Returns:
            Processing result
        """
        return await asyncio.wait_for(
            self._process_transaction_core(queue_entry),
            timeout=timeout
        )
    
    async def _process_transaction_core(self, queue_entry: Dict[str, Any]) -> Dict[str, Any]:
        """
        Core transaction processing logic.
        
        Args:
            queue_entry: Queue entry containing transaction data
            
        Returns:
            Processing result
        """
        transaction_data = queue_entry["data"]
        connection_id = queue_entry.get("connection_id")
        
        with SessionLocal() as db:
            try:
                # Create transaction record
                transaction_record = create_pos_transaction(
                    db=db,
                    transaction_in=transaction_data,
                    connection_id=UUID(connection_id) if connection_id else None
                )
                
                # Process transaction (simplified for now)
                # In real implementation, this would:
                # 1. Validate transaction data
                # 2. Generate invoice
                # 3. Submit to FIRS
                # 4. Update transaction status
                
                result = {
                    "success": True,
                    "transaction_id": str(transaction_record.id),
                    "invoice_generated": True,
                    "firs_submitted": False,  # Would be updated after actual submission
                    "processed_at": datetime.now().isoformat()
                }
                
                # Update transaction record with processing result
                update_pos_transaction(
                    db=db,
                    transaction_id=transaction_record.id,
                    update_data={
                        "invoice_generated": True,
                        "transaction_metadata": {
                            **transaction_record.transaction_metadata,
                            "processing_result": result
                        }
                    }
                )
                
                return result
                
            except Exception as e:
                logger.error(f"Transaction processing failed: {str(e)}")
                raise
    
    async def _add_to_persistent_queue(
        self, 
        queue_entry: Dict[str, Any], 
        priority: str
    ) -> None:
        """
        Add entry to persistent Redis queue.
        
        Args:
            queue_entry: Entry to add to queue
            priority: Queue priority level
        """
        queue_name = self.queues.get(priority, self.queues["standard"])
        
        try:
            # Serialize queue entry
            serialized_entry = json.dumps(queue_entry, default=str)
            
            # Add to queue (left push for FIFO processing)
            self.redis_client.lpush(queue_name, serialized_entry)
            
            # Set TTL for queue entries (24 hours)
            self.redis_client.expire(queue_name, 86400)
            
            # Update queue length metrics
            queue_length = self.redis_client.llen(queue_name)
            self.redis_client.hset(
                self.metrics["queue_lengths"],
                priority,
                queue_length
            )
            
        except Exception as e:
            logger.error(f"Failed to add to persistent queue: {str(e)}")
            raise
    
    async def process_queue_batch(
        self, 
        priority: str = "high", 
        batch_size: int = 10
    ) -> Dict[str, Any]:
        """
        Process a batch of transactions from specified queue.
        
        Args:
            priority: Queue priority to process
            batch_size: Number of transactions to process
            
        Returns:
            Batch processing results
        """
        queue_name = self.queues.get(priority, self.queues["standard"])
        processed = 0
        failed = 0
        results = []
        
        try:
            for _ in range(batch_size):
                # Get next entry from queue (right pop for FIFO)
                entry_data = self.redis_client.rpop(queue_name)
                
                if not entry_data:
                    break  # Queue is empty
                
                try:
                    queue_entry = json.loads(entry_data)
                    
                    # Check if entry has exceeded max attempts
                    if queue_entry.get("attempts", 0) >= queue_entry.get("max_attempts", 3):
                        await self._move_to_dead_letter(queue_entry)
                        failed += 1
                        continue
                    
                    # Process the transaction
                    start_time = time.time()
                    result = await self._process_transaction_core(queue_entry)
                    processing_time = time.time() - start_time
                    
                    # Check SLA compliance
                    sla_target = queue_entry.get("sla_target", 5.0)
                    sla_met = processing_time <= sla_target
                    
                    results.append({
                        "transaction_id": queue_entry["id"],
                        "success": True,
                        "processing_time": processing_time,
                        "sla_met": sla_met,
                        "result": result
                    })
                    
                    processed += 1
                    await self._update_metrics("batch_processed", processing_time)
                    
                except Exception as e:
                    # Increment attempts and re-queue or move to dead letter
                    queue_entry["attempts"] = queue_entry.get("attempts", 0) + 1
                    queue_entry["last_error"] = str(e)
                    queue_entry["failed_at"] = datetime.now().isoformat()
                    
                    if queue_entry["attempts"] < queue_entry.get("max_attempts", 3):
                        await self._add_to_persistent_queue(queue_entry, "retry")
                    else:
                        await self._move_to_dead_letter(queue_entry)
                    
                    failed += 1
                    await self._update_metrics("batch_failed")
                    
                    results.append({
                        "transaction_id": queue_entry.get("id", "unknown"),
                        "success": False,
                        "error": str(e),
                        "attempts": queue_entry["attempts"]
                    })
            
            return {
                "processed": processed,
                "failed": failed,
                "batch_size": len(results),
                "queue": priority,
                "results": results
            }
            
        except Exception as e:
            logger.error(f"Batch processing failed: {str(e)}")
            return {
                "processed": processed,
                "failed": failed,
                "error": str(e),
                "queue": priority
            }
    
    async def _move_to_dead_letter(self, queue_entry: Dict[str, Any]) -> None:
        """
        Move failed entry to dead letter queue.
        
        Args:
            queue_entry: Failed queue entry
        """
        queue_entry["moved_to_dead_letter_at"] = datetime.now().isoformat()
        await self._add_to_persistent_queue(queue_entry, "dead_letter")
        
        logger.warning(
            f"Transaction {queue_entry.get('id')} moved to dead letter queue",
            extra={"queue_entry": queue_entry}
        )
    
    async def _update_metrics(
        self, 
        metric_type: str, 
        value: Optional[float] = None
    ) -> None:
        """
        Update performance metrics in Redis.
        
        Args:
            metric_type: Type of metric to update
            value: Optional metric value
        """
        try:
            timestamp = datetime.now().isoformat()
            
            if metric_type in ["enqueued", "batch_processed", "immediate_success"]:
                self.redis_client.incr(f"{self.metrics['processed_count']}:{metric_type}")
                
                if value is not None:
                    # Update rolling average processing time
                    self.redis_client.lpush(
                        f"{self.metrics['avg_processing_time']}:{metric_type}",
                        f"{value}:{timestamp}"
                    )
                    # Keep only last 100 measurements
                    self.redis_client.ltrim(
                        f"{self.metrics['avg_processing_time']}:{metric_type}",
                        0, 99
                    )
            
            elif metric_type in ["batch_failed", "immediate_failure"]:
                self.redis_client.incr(f"{self.metrics['failed_count']}:{metric_type}")
            
            elif metric_type in ["immediate_sla_miss"]:
                self.redis_client.incr(f"pos_sla_misses:{metric_type}")
                
                if value is not None:
                    self.redis_client.lpush(
                        f"pos_sla_miss_times:{metric_type}",
                        f"{value}:{timestamp}"
                    )
                    self.redis_client.ltrim(
                        f"pos_sla_miss_times:{metric_type}",
                        0, 99
                    )
            
        except Exception as e:
            logger.error(f"Failed to update metrics: {str(e)}")
    
    async def get_queue_status(self) -> Dict[str, Any]:
        """
        Get current status of all queues.
        
        Returns:
            Dict containing queue status information
        """
        try:
            status = {}
            
            for priority, queue_name in self.queues.items():
                length = self.redis_client.llen(queue_name)
                
                status[priority] = {
                    "queue_name": queue_name,
                    "length": length,
                    "sla_target": self.sla_targets.get(priority),
                    "status": "healthy" if length < 100 else "warning" if length < 500 else "critical"
                }
            
            # Get performance metrics
            metrics = {}
            for metric_name, metric_key in self.metrics.items():
                if metric_name == "queue_lengths":
                    metrics[metric_name] = self.redis_client.hgetall(metric_key)
                else:
                    # Get counts for different metric types
                    for metric_type in ["enqueued", "batch_processed", "immediate_success", "batch_failed", "immediate_failure"]:
                        key = f"{metric_key}:{metric_type}"
                        count = self.redis_client.get(key)
                        metrics[f"{metric_name}_{metric_type}"] = int(count) if count else 0
            
            return {
                "queues": status,
                "metrics": metrics,
                "circuit_breaker_state": self.circuit_breaker.state,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get queue status: {str(e)}")
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _validate_transaction_data(self, transaction_data: Dict[str, Any]) -> bool:
        """
        Validate transaction data format.
        
        Args:
            transaction_data: Transaction data to validate
            
        Returns:
            True if valid, False otherwise
        """
        required_fields = ["transaction_id", "amount", "timestamp"]
        
        try:
            # Check required fields
            for field in required_fields:
                if field not in transaction_data:
                    logger.error(f"Missing required field: {field}")
                    return False
            
            # Validate data types
            if not isinstance(transaction_data["amount"], (int, float)):
                logger.error("Amount must be numeric")
                return False
            
            if transaction_data["amount"] <= 0:
                logger.error("Amount must be positive")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Transaction validation failed: {str(e)}")
            return False


# Global service instance
_pos_queue_service = None


def get_pos_queue_service() -> POSQueueService:
    """Get the global POS queue service instance."""
    global _pos_queue_service
    if _pos_queue_service is None:
        _pos_queue_service = POSQueueService()
    return _pos_queue_service