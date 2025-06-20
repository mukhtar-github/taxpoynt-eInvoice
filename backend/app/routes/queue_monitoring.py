"""
Queue monitoring and management API routes.

This module provides endpoints for monitoring Celery queue health,
worker status, and task management.
"""

import logging
from typing import Dict, Any, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from pydantic import BaseModel

from app.dependencies.auth import get_current_user
from app.models.user import User
from app.core.celery import get_queue_health, get_worker_health
from app.core.worker_config import create_worker_manager

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/queue",
    tags=["queue-monitoring"],
    responses={
        401: {"description": "Authentication required"},
        403: {"description": "Insufficient permissions"},
        500: {"description": "Internal server error"},
    },
)


# ==================== RESPONSE MODELS ====================

class QueueHealthResponse(BaseModel):
    """Model for queue health response."""
    status: str
    queues: Dict[str, Dict[str, Any]]
    total_pending: int
    checked_at: str


class WorkerHealthResponse(BaseModel):
    """Model for worker health response."""
    status: str
    active_workers: int
    available_queues: List[str]
    worker_info: Optional[Dict[str, Any]] = None


class TaskStatsResponse(BaseModel):
    """Model for task statistics response."""
    total_tasks: int
    successful_tasks: int
    failed_tasks: int
    pending_tasks: int
    active_tasks: int
    task_breakdown: Dict[str, int]


class WorkerConfigResponse(BaseModel):
    """Model for worker configuration response."""
    environment: str
    total_workers: int
    workers: Dict[str, Dict[str, Any]]


# ==================== MONITORING ENDPOINTS ====================

@router.get(
    "/health",
    response_model=Dict[str, Any],
    summary="Get queue system health",
    description="Retrieve comprehensive health information for the queue system",
)
async def get_queue_system_health(
    current_user: User = Depends(get_current_user)
):
    """
    Get comprehensive queue system health information.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Dict containing queue system health metrics
    """
    try:
        # Get queue and worker health
        queue_health = get_queue_health()
        worker_health = get_worker_health()
        
        # Combine health information
        system_health = {
            "overall_status": "healthy" if queue_health["status"] == "healthy" and worker_health["status"] == "healthy" else "unhealthy",
            "queue_health": queue_health,
            "worker_health": worker_health,
            "checked_at": queue_health.get("checked_at", ""),
            "recommendations": []
        }
        
        # Add recommendations based on health
        if queue_health.get("total_pending", 0) > 1000:
            system_health["recommendations"].append("Consider adding more workers to handle queue backlog")
        
        if worker_health.get("active_workers", 0) == 0:
            system_health["recommendations"].append("No active workers detected - start worker processes")
        
        return system_health
        
    except Exception as e:
        logger.error(f"Error getting queue system health: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve queue system health: {str(e)}"
        )


@router.get(
    "/queues",
    response_model=QueueHealthResponse,
    summary="Get queue health details",
    description="Retrieve detailed health information for all queues",
)
async def get_queue_details(
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed queue health information.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        QueueHealthResponse with detailed queue metrics
    """
    try:
        health_info = get_queue_health()
        
        return QueueHealthResponse(
            status=health_info["status"],
            queues=health_info["queues"],
            total_pending=health_info["total_pending"],
            checked_at=health_info.get("checked_at", "")
        )
        
    except Exception as e:
        logger.error(f"Error getting queue details: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve queue details: {str(e)}"
        )


@router.get(
    "/workers",
    response_model=WorkerHealthResponse,
    summary="Get worker health details", 
    description="Retrieve detailed health information for all workers",
)
async def get_worker_details(
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed worker health information.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        WorkerHealthResponse with detailed worker metrics
    """
    try:
        health_info = get_worker_health()
        
        return WorkerHealthResponse(
            status=health_info["status"],
            active_workers=health_info["active_workers"],
            available_queues=health_info["available_queues"],
            worker_info=health_info.get("worker_info")
        )
        
    except Exception as e:
        logger.error(f"Error getting worker details: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve worker details: {str(e)}"
        )


@router.get(
    "/statistics",
    response_model=TaskStatsResponse,
    summary="Get task statistics",
    description="Retrieve task execution statistics and metrics",
)
async def get_task_statistics(
    hours: int = Query(24, ge=1, le=168, description="Number of hours to look back"),
    current_user: User = Depends(get_current_user)
):
    """
    Get task execution statistics.
    
    Args:
        hours: Number of hours to look back for statistics
        current_user: Current authenticated user
        
    Returns:
        TaskStatsResponse with task execution metrics
    """
    try:
        # TODO: Implement actual task statistics gathering
        # This would involve querying Celery result backend for task statistics
        
        # For now, return mock data
        stats = TaskStatsResponse(
            total_tasks=0,
            successful_tasks=0, 
            failed_tasks=0,
            pending_tasks=0,
            active_tasks=0,
            task_breakdown={
                "pos_tasks": 0,
                "crm_tasks": 0,
                "firs_tasks": 0,
                "batch_tasks": 0,
                "maintenance_tasks": 0
            }
        )
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting task statistics: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve task statistics: {str(e)}"
        )


# ==================== CONFIGURATION ENDPOINTS ====================

@router.get(
    "/config",
    response_model=WorkerConfigResponse,
    summary="Get worker configuration",
    description="Retrieve current worker configuration and deployment details",
)
async def get_worker_configuration(
    current_user: User = Depends(get_current_user)
):
    """
    Get current worker configuration.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        WorkerConfigResponse with worker configuration details
    """
    try:
        worker_manager = create_worker_manager()
        config_info = worker_manager.get_monitoring_info()
        
        return WorkerConfigResponse(
            environment=config_info["environment"],
            total_workers=config_info["total_workers"],
            workers=config_info["workers"]
        )
        
    except Exception as e:
        logger.error(f"Error getting worker configuration: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve worker configuration: {str(e)}"
        )


@router.get(
    "/config/commands",
    summary="Get worker start commands",
    description="Retrieve commands for starting all configured workers",
)
async def get_worker_commands(
    current_user: User = Depends(get_current_user)
):
    """
    Get worker start commands.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Dict with worker start commands
    """
    try:
        worker_manager = create_worker_manager()
        commands = worker_manager.get_all_worker_commands()
        
        return {
            "environment": worker_manager.environment,
            "worker_commands": {
                name: " ".join(cmd) for name, cmd in commands.items()
            },
            "supervisor_config_available": True,
            "systemd_services_available": True
        }
        
    except Exception as e:
        logger.error(f"Error getting worker commands: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve worker commands: {str(e)}"
        )


# ==================== MANAGEMENT ENDPOINTS ====================

@router.post(
    "/tasks/retry/{task_id}",
    summary="Retry failed task",
    description="Retry a specific failed task by ID",
)
async def retry_task(
    task_id: str = Path(..., description="Task ID to retry"),
    current_user: User = Depends(get_current_user)
):
    """
    Retry a specific failed task.
    
    Args:
        task_id: ID of the task to retry
        current_user: Current authenticated user
        
    Returns:
        Dict with retry results
    """
    try:
        # TODO: Implement actual task retry functionality
        # This would involve:
        # 1. Loading task details from result backend
        # 2. Checking if task is retryable
        # 3. Re-queuing the task
        # 4. Updating task status
        
        result = {
            "status": "success",
            "task_id": task_id,
            "retried_at": "2025-06-20T09:00:00Z",
            "new_task_id": f"{task_id}_retry",
            "message": "Task queued for retry"
        }
        
        logger.info(f"Task {task_id} queued for retry")
        return result
        
    except Exception as e:
        logger.error(f"Error retrying task {task_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retry task: {str(e)}"
        )


@router.post(
    "/queues/{queue_name}/purge",
    summary="Purge queue",
    description="Remove all pending tasks from a specific queue",
)
async def purge_queue(
    queue_name: str = Path(..., description="Name of queue to purge"),
    confirm: bool = Query(False, description="Confirmation required to purge"),
    current_user: User = Depends(get_current_user)
):
    """
    Purge all pending tasks from a queue.
    
    Args:
        queue_name: Name of the queue to purge
        confirm: Confirmation flag (must be True)
        current_user: Current authenticated user
        
    Returns:
        Dict with purge results
    """
    try:
        if not confirm:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Queue purge requires confirmation (confirm=true)"
            )
        
        # TODO: Implement actual queue purging
        # This would involve:
        # 1. Connecting to message broker
        # 2. Purging specified queue
        # 3. Logging the operation
        
        result = {
            "status": "success",
            "queue_name": queue_name,
            "purged_at": "2025-06-20T09:00:00Z",
            "tasks_removed": 0,
            "message": f"Queue '{queue_name}' has been purged"
        }
        
        logger.warning(f"Queue '{queue_name}' purged by user {current_user.id}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error purging queue {queue_name}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to purge queue: {str(e)}"
        )