"""
Real-time POS transaction processing endpoints.

This module provides FastAPI endpoints for immediate POS transaction processing
with sub-2-second SLA requirements and circuit breaker protection.
"""

import time
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_user
from app.dependencies.db import get_db
from app.schemas.pos import POSTransactionCreate, POSTransactionResponse
from app.services.pos_queue_service import get_pos_queue_service
from app.crud.pos_connection import get_pos_connection
from app.tasks.pos_tasks import process_realtime_transaction
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.post(
    "/transactions/immediate",
    response_model=Dict[str, Any],
    status_code=status.HTTP_202_ACCEPTED,
    summary="Process transaction immediately",
    description="Process a POS transaction with sub-2-second SLA using immediate background processing"
)
async def process_immediate_transaction(
    transaction_data: POSTransactionCreate,
    connection_id: UUID,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Process a POS transaction immediately with ultra-low latency.
    
    This endpoint is designed for real-time transaction processing with:
    - Sub-2-second processing target
    - Circuit breaker protection
    - Automatic fallback to standard queues
    - Comprehensive error handling
    
    Args:
        transaction_data: Transaction data to process
        connection_id: POS connection ID
        background_tasks: FastAPI background tasks
        db: Database session
        current_user: Authenticated user
        
    Returns:
        Processing result with timing metrics
    """
    start_time = time.time()
    
    try:
        # Validate POS connection exists and belongs to user
        pos_connection = get_pos_connection(db, connection_id)
        if not pos_connection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="POS connection not found"
            )
        
        if pos_connection.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to POS connection"
            )
        
        if not pos_connection.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="POS connection is not active"
            )
        
        # Get queue service for immediate processing
        queue_service = get_pos_queue_service()
        
        # Convert transaction data to dict for processing
        transaction_dict = transaction_data.dict()
        transaction_dict["user_id"] = str(current_user.id)
        transaction_dict["organization_id"] = str(pos_connection.organization_id)
        transaction_dict["connection_type"] = pos_connection.pos_type.value
        
        # Enqueue with immediate priority
        enqueue_result = await queue_service.enqueue_transaction(
            transaction_data=transaction_dict,
            background_tasks=background_tasks,
            priority="immediate",
            connection_id=connection_id
        )
        
        processing_time = time.time() - start_time
        
        # Return immediate response with enqueue status
        response = {
            "success": enqueue_result["success"],
            "transaction_id": enqueue_result["transaction_id"],
            "connection_id": str(connection_id),
            "priority": "immediate",
            "enqueue_time": processing_time,
            "estimated_completion": enqueue_result.get("estimated_processing_time", 1.0),
            "message": "Transaction queued for immediate processing",
            "timestamp": datetime.now().isoformat()
        }
        
        if not enqueue_result["success"]:
            response["error"] = enqueue_result.get("error", "Unknown error")
            logger.error(
                f"Failed to enqueue immediate transaction: {response['error']}",
                extra={
                    "transaction_id": enqueue_result["transaction_id"],
                    "connection_id": str(connection_id),
                    "user_id": str(current_user.id)
                }
            )
        else:
            logger.info(
                f"Immediate transaction enqueued successfully in {processing_time:.3f}s",
                extra=response
            )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        processing_time = time.time() - start_time
        
        logger.error(
            f"Immediate transaction processing failed: {str(e)}",
            extra={
                "connection_id": str(connection_id),
                "processing_time": processing_time,
                "user_id": str(current_user.id),
                "error": str(e)
            }
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Transaction processing failed: {str(e)}"
        )


@router.post(
    "/transactions/high-priority",
    response_model=Dict[str, Any],
    status_code=status.HTTP_202_ACCEPTED,
    summary="Process transaction with high priority",
    description="Process a POS transaction with high priority using dedicated workers"
)
async def process_high_priority_transaction(
    transaction_data: POSTransactionCreate,
    connection_id: UUID,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Process a POS transaction with high priority.
    
    This endpoint provides high-priority processing for transactions that
    need faster than standard processing but don't require immediate processing.
    
    Args:
        transaction_data: Transaction data to process
        connection_id: POS connection ID
        background_tasks: FastAPI background tasks
        db: Database session
        current_user: Authenticated user
        
    Returns:
        Processing result with queue information
    """
    start_time = time.time()
    
    try:
        # Validate POS connection
        pos_connection = get_pos_connection(db, connection_id)
        if not pos_connection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="POS connection not found"
            )
        
        if pos_connection.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to POS connection"
            )
        
        # Get queue service
        queue_service = get_pos_queue_service()
        
        # Convert transaction data to dict
        transaction_dict = transaction_data.dict()
        transaction_dict["user_id"] = str(current_user.id)
        transaction_dict["organization_id"] = str(pos_connection.organization_id)
        transaction_dict["connection_type"] = pos_connection.pos_type.value
        
        # Enqueue with high priority
        enqueue_result = await queue_service.enqueue_transaction(
            transaction_data=transaction_dict,
            background_tasks=background_tasks,
            priority="high",
            connection_id=connection_id
        )
        
        processing_time = time.time() - start_time
        
        response = {
            "success": enqueue_result["success"],
            "transaction_id": enqueue_result["transaction_id"],
            "connection_id": str(connection_id),
            "priority": "high",
            "enqueue_time": processing_time,
            "estimated_completion": enqueue_result.get("estimated_processing_time", 2.0),
            "message": "Transaction queued for high-priority processing",
            "timestamp": datetime.now().isoformat()
        }
        
        if not enqueue_result["success"]:
            response["error"] = enqueue_result.get("error", "Unknown error")
        
        logger.info(
            f"High-priority transaction enqueued in {processing_time:.3f}s",
            extra=response
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        processing_time = time.time() - start_time
        
        logger.error(
            f"High-priority transaction processing failed: {str(e)}",
            extra={
                "connection_id": str(connection_id),
                "processing_time": processing_time,
                "user_id": str(current_user.id),
                "error": str(e)
            }
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Transaction processing failed: {str(e)}"
        )


@router.get(
    "/queue/status",
    response_model=Dict[str, Any],
    summary="Get queue status",
    description="Get current status of POS transaction processing queues"
)
async def get_queue_status(
    current_user = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get current status of all POS transaction processing queues.
    
    Returns:
        Queue status information including lengths, metrics, and health
    """
    try:
        queue_service = get_pos_queue_service()
        status = await queue_service.get_queue_status()
        
        # Add user context
        status["user_id"] = str(current_user.id)
        status["requested_at"] = datetime.now().isoformat()
        
        logger.info(
            "Queue status requested",
            extra={
                "user_id": str(current_user.id),
                "queue_status": status.get("queues", {})
            }
        )
        
        return status
        
    except Exception as e:
        logger.error(
            f"Failed to get queue status: {str(e)}",
            extra={
                "user_id": str(current_user.id),
                "error": str(e)
            }
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get queue status: {str(e)}"
        )


@router.post(
    "/queue/process-batch",
    response_model=Dict[str, Any],
    summary="Process transaction batch",
    description="Manually trigger batch processing of queued transactions"
)
async def process_transaction_batch(
    priority: str = "high",
    batch_size: int = 10,
    current_user = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Manually trigger batch processing of queued transactions.
    
    This endpoint allows administrators to manually process batches
    of transactions from specific queues.
    
    Args:
        priority: Queue priority to process (high, standard, retry)
        batch_size: Number of transactions to process
        current_user: Authenticated user
        
    Returns:
        Batch processing results
    """
    start_time = time.time()
    
    try:
        # Validate priority
        valid_priorities = ["immediate", "high", "standard", "retry"]
        if priority not in valid_priorities:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid priority. Must be one of: {valid_priorities}"
            )
        
        # Validate batch size
        if batch_size < 1 or batch_size > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Batch size must be between 1 and 100"
            )
        
        # Process batch
        queue_service = get_pos_queue_service()
        result = await queue_service.process_queue_batch(priority, batch_size)
        
        processing_time = time.time() - start_time
        
        # Add metadata
        result.update({
            "requested_by": str(current_user.id),
            "manual_trigger": True,
            "trigger_time": processing_time,
            "triggered_at": datetime.now().isoformat()
        })
        
        logger.info(
            f"Manual batch processing completed: {result.get('processed', 0)} transactions",
            extra=result
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        processing_time = time.time() - start_time
        
        logger.error(
            f"Manual batch processing failed: {str(e)}",
            extra={
                "priority": priority,
                "batch_size": batch_size,
                "processing_time": processing_time,
                "user_id": str(current_user.id),
                "error": str(e)
            }
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch processing failed: {str(e)}"
        )


@router.get(
    "/metrics/performance",
    response_model=Dict[str, Any],
    summary="Get performance metrics",
    description="Get performance metrics for POS transaction processing"
)
async def get_performance_metrics(
    current_user = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get performance metrics for POS transaction processing.
    
    Returns:
        Performance metrics including SLA compliance, throughput, and error rates
    """
    try:
        queue_service = get_pos_queue_service()
        
        # Get queue status which includes metrics
        status = await queue_service.get_queue_status()
        
        # Extract and format performance metrics
        metrics = status.get("metrics", {})
        
        # Calculate derived metrics
        total_processed = sum(
            metrics.get(f"processed_count_{metric_type}", 0)
            for metric_type in ["enqueued", "batch_processed", "immediate_success"]
        )
        
        total_failed = sum(
            metrics.get(f"failed_count_{metric_type}", 0)
            for metric_type in ["batch_failed", "immediate_failure"]
        )
        
        success_rate = (
            (total_processed / (total_processed + total_failed) * 100)
            if (total_processed + total_failed) > 0 else 100.0
        )
        
        performance_metrics = {
            "processing_stats": {
                "total_processed": total_processed,
                "total_failed": total_failed,
                "success_rate": round(success_rate, 2)
            },
            "queue_health": {
                queue: info.get("status", "unknown")
                for queue, info in status.get("queues", {}).items()
            },
            "circuit_breaker": {
                "state": status.get("circuit_breaker_state", "unknown")
            },
            "system_status": {
                "overall_health": "healthy" if success_rate > 95 else "degraded" if success_rate > 85 else "critical",
                "timestamp": datetime.now().isoformat()
            }
        }
        
        logger.info(
            "Performance metrics requested",
            extra={
                "user_id": str(current_user.id),
                "success_rate": success_rate,
                "total_processed": total_processed
            }
        )
        
        return performance_metrics
        
    except Exception as e:
        logger.error(
            f"Failed to get performance metrics: {str(e)}",
            extra={
                "user_id": str(current_user.id),
                "error": str(e)
            }
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get performance metrics: {str(e)}"
        )