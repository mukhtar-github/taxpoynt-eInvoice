"""
Salesforce Synchronization API Endpoints.

This module provides REST API endpoints for managing Salesforce data synchronization,
including manual sync triggers, batch import management, and sync status monitoring.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query, Path
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.core.auth import get_current_user, require_permissions
from app.models.user import User
from app.models.crm import CRMConnection
from app.integrations.crm.salesforce.sync_manager import (
    SalesforceSyncManager,
    SyncMode,
    create_sync_manager
)
from app.integrations.crm.salesforce.batch_processor import (
    SalesforceBatchProcessor,
    create_batch_processor
)
from app.integrations.crm.salesforce.delta_sync import (
    SalesforceDeltaSync,
    create_delta_sync
)
from app.schemas.common import StandardResponse
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/salesforce", tags=["Salesforce Sync"])


# Request/Response Models
class SyncTriggerRequest(BaseModel):
    """Request model for triggering synchronization."""
    mode: SyncMode = Field(default=SyncMode.DELTA, description="Synchronization mode")
    limit: Optional[int] = Field(default=None, ge=1, le=10000, description="Maximum records to sync")
    stage_filter: Optional[List[str]] = Field(default=None, description="Filter by opportunity stages")
    auto_generate_invoices: bool = Field(default=False, description="Auto-generate invoices for closed deals")


class BatchImportRequest(BaseModel):
    """Request model for starting batch import."""
    start_date: Optional[datetime] = Field(default=None, description="Start date for import")
    end_date: Optional[datetime] = Field(default=None, description="End date for import")
    stage_filter: Optional[List[str]] = Field(default=None, description="Filter by opportunity stages")
    batch_size: Optional[int] = Field(default=50, ge=10, le=500, description="Records per batch")


class DeltaSyncRequest(BaseModel):
    """Request model for delta synchronization."""
    force_full_comparison: bool = Field(default=False, description="Force full comparison instead of timestamp-based")
    stage_filter: Optional[List[str]] = Field(default=None, description="Filter by opportunity stages")


class SyncStatusResponse(BaseModel):
    """Response model for sync status."""
    connection_id: str
    connection_name: str
    status: str
    last_sync: Optional[datetime]
    last_successful_sync: Optional[datetime]
    total_deals: int
    total_invoices: int
    failed_deals: int
    sync_error_count: int
    is_syncing: bool = False
    active_jobs: List[Dict[str, Any]] = []


class BatchJobResponse(BaseModel):
    """Response model for batch job status."""
    job_id: str
    connection_id: str
    status: str
    total_records: int
    batch_size: int
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error_message: Optional[str]
    progress: Dict[str, Any]


# Background task tracking
active_sync_tasks: Dict[str, str] = {}  # connection_id -> task_type


@router.post("/{connection_id}/sync")
async def trigger_sync(
    connection_id: str = Path(..., description="Salesforce connection ID"),
    request: SyncTriggerRequest = SyncTriggerRequest(),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
) -> StandardResponse:
    """
    Trigger Salesforce opportunity synchronization.
    
    This endpoint starts a synchronization process that will fetch opportunities
    from Salesforce and update the local database.
    """
    try:
        # Check if sync is already running
        if connection_id in active_sync_tasks:
            raise HTTPException(
                status_code=409,
                detail=f"Sync already running for connection {connection_id}"
            )
        
        # Get sync manager
        sync_manager = await create_sync_manager(connection_id)
        
        # Verify user has access to this connection
        if sync_manager.connection.organization_id != current_user.organization_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Mark sync as running
        active_sync_tasks[connection_id] = "manual_sync"
        
        # Start sync in background
        background_tasks.add_task(
            _run_sync_task,
            connection_id,
            request.mode,
            request.limit,
            request.stage_filter,
            request.auto_generate_invoices
        )
        
        logger.info(f"Started manual sync for connection {connection_id} by user {current_user.id}")
        
        return StandardResponse(
            success=True,
            message="Synchronization started",
            data={
                "connection_id": connection_id,
                "mode": request.mode,
                "estimated_duration": "2-10 minutes",
                "status": "running"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to trigger sync for connection {connection_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{connection_id}/batch-import")
async def start_batch_import(
    connection_id: str = Path(..., description="Salesforce connection ID"),
    request: BatchImportRequest = BatchImportRequest(),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
) -> StandardResponse:
    """
    Start a batch import job for historical data.
    
    This endpoint starts a long-running batch import process that will import
    large volumes of historical data from Salesforce.
    """
    try:
        # Check if batch import is already running
        if connection_id in active_sync_tasks:
            raise HTTPException(
                status_code=409,
                detail=f"Sync operation already running for connection {connection_id}"
            )
        
        # Get batch processor
        batch_processor = await create_batch_processor(connection_id)
        
        # Verify user has access to this connection
        if batch_processor.connection.organization_id != current_user.organization_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get import estimation first
        estimation = await batch_processor.estimate_import_time(
            start_date=request.start_date,
            end_date=request.end_date,
            stage_filter=request.stage_filter,
            batch_size=request.batch_size
        )
        
        if estimation["total_records"] == 0:
            return StandardResponse(
                success=False,
                message="No records found for the specified criteria",
                data=estimation
            )
        
        # Start batch import
        job_id = await batch_processor.start_historical_import(
            start_date=request.start_date,
            end_date=request.end_date,
            stage_filter=request.stage_filter,
            batch_size=request.batch_size
        )
        
        # Mark as running
        active_sync_tasks[connection_id] = f"batch_import_{job_id}"
        
        logger.info(f"Started batch import {job_id} for connection {connection_id} by user {current_user.id}")
        
        return StandardResponse(
            success=True,
            message="Batch import started",
            data={
                "job_id": job_id,
                "connection_id": connection_id,
                "estimation": estimation,
                "status": "running"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start batch import for connection {connection_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{connection_id}/delta-sync")
async def trigger_delta_sync(
    connection_id: str = Path(..., description="Salesforce connection ID"),
    request: DeltaSyncRequest = DeltaSyncRequest(),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
) -> StandardResponse:
    """
    Trigger delta synchronization.
    
    This endpoint starts an efficient delta sync that only processes changed records
    since the last synchronization.
    """
    try:
        # Check if sync is already running
        if connection_id in active_sync_tasks:
            raise HTTPException(
                status_code=409,
                detail=f"Sync already running for connection {connection_id}"
            )
        
        # Get delta sync manager
        delta_sync = await create_delta_sync(connection_id)
        
        # Verify user has access to this connection
        if delta_sync.connection.organization_id != current_user.organization_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Mark sync as running
        active_sync_tasks[connection_id] = "delta_sync"
        
        # Start delta sync in background
        background_tasks.add_task(
            _run_delta_sync_task,
            connection_id,
            request.force_full_comparison,
            request.stage_filter
        )
        
        logger.info(f"Started delta sync for connection {connection_id} by user {current_user.id}")
        
        return StandardResponse(
            success=True,
            message="Delta synchronization started",
            data={
                "connection_id": connection_id,
                "force_full_comparison": request.force_full_comparison,
                "estimated_duration": "30 seconds - 2 minutes",
                "status": "running"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to trigger delta sync for connection {connection_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{connection_id}/status")
async def get_sync_status(
    connection_id: str = Path(..., description="Salesforce connection ID"),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
) -> StandardResponse[SyncStatusResponse]:
    """
    Get the current synchronization status for a connection.
    """
    try:
        # Get sync manager for status
        sync_manager = await create_sync_manager(connection_id)
        
        # Verify user has access to this connection
        if sync_manager.connection.organization_id != current_user.organization_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get sync status
        status = await sync_manager.get_sync_status()
        
        # Check for active jobs
        batch_processor = await create_batch_processor(connection_id)
        active_jobs = await batch_processor.get_all_jobs()
        
        # Check if currently syncing
        is_syncing = connection_id in active_sync_tasks
        
        response_data = SyncStatusResponse(
            connection_id=status["connection_id"],
            connection_name=status["connection_name"],
            status=status["status"],
            last_sync=datetime.fromisoformat(status["last_sync"]) if status["last_sync"] else None,
            last_successful_sync=datetime.fromisoformat(status["last_successful_sync"]) if status["last_successful_sync"] else None,
            total_deals=status["total_deals"],
            total_invoices=status["total_invoices"],
            failed_deals=status["failed_deals"],
            sync_error_count=status["sync_error_count"],
            is_syncing=is_syncing,
            active_jobs=active_jobs
        )
        
        return StandardResponse(
            success=True,
            message="Sync status retrieved",
            data=response_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get sync status for connection {connection_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{connection_id}/jobs/{job_id}")
async def get_job_status(
    connection_id: str = Path(..., description="Salesforce connection ID"),
    job_id: str = Path(..., description="Batch job ID"),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
) -> StandardResponse[BatchJobResponse]:
    """
    Get the status of a specific batch job.
    """
    try:
        # Get batch processor
        batch_processor = await create_batch_processor(connection_id)
        
        # Verify user has access to this connection
        if batch_processor.connection.organization_id != current_user.organization_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get job status
        job_status = await batch_processor.get_job_status(job_id)
        
        if not job_status:
            raise HTTPException(status_code=404, detail="Job not found")
        
        response_data = BatchJobResponse(**job_status)
        
        return StandardResponse(
            success=True,
            message="Job status retrieved",
            data=response_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job status {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{connection_id}/jobs/{job_id}/cancel")
async def cancel_job(
    connection_id: str = Path(..., description="Salesforce connection ID"),
    job_id: str = Path(..., description="Batch job ID"),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
) -> StandardResponse:
    """
    Cancel a running batch job.
    """
    try:
        # Get batch processor
        batch_processor = await create_batch_processor(connection_id)
        
        # Verify user has access to this connection
        if batch_processor.connection.organization_id != current_user.organization_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Cancel job
        success = await batch_processor.cancel_job(job_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Job not found or cannot be cancelled")
        
        # Remove from active tasks if it's there
        task_key = f"batch_import_{job_id}"
        if connection_id in active_sync_tasks and active_sync_tasks[connection_id] == task_key:
            del active_sync_tasks[connection_id]
        
        logger.info(f"Cancelled job {job_id} for connection {connection_id} by user {current_user.id}")
        
        return StandardResponse(
            success=True,
            message="Job cancelled successfully",
            data={"job_id": job_id, "status": "cancelled"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel job {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{connection_id}/jobs/{job_id}/retry")
async def retry_job(
    connection_id: str = Path(..., description="Salesforce connection ID"),
    job_id: str = Path(..., description="Batch job ID"),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
) -> StandardResponse:
    """
    Retry a failed batch job.
    """
    try:
        # Get batch processor
        batch_processor = await create_batch_processor(connection_id)
        
        # Verify user has access to this connection
        if batch_processor.connection.organization_id != current_user.organization_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Retry job
        success = await batch_processor.retry_failed_job(job_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Job not found or cannot be retried")
        
        # Mark as running again
        active_sync_tasks[connection_id] = f"batch_import_{job_id}"
        
        logger.info(f"Retried job {job_id} for connection {connection_id} by user {current_user.id}")
        
        return StandardResponse(
            success=True,
            message="Job restarted successfully",
            data={"job_id": job_id, "status": "running"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retry job {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{connection_id}/estimate")
async def estimate_import_time(
    connection_id: str = Path(..., description="Salesforce connection ID"),
    start_date: Optional[datetime] = Query(default=None, description="Start date for import"),
    end_date: Optional[datetime] = Query(default=None, description="End date for import"),
    stage_filter: Optional[List[str]] = Query(default=None, description="Filter by opportunity stages"),
    batch_size: int = Query(default=50, ge=10, le=500, description="Records per batch"),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
) -> StandardResponse:
    """
    Estimate the time required for a historical data import.
    """
    try:
        # Get batch processor
        batch_processor = await create_batch_processor(connection_id)
        
        # Verify user has access to this connection
        if batch_processor.connection.organization_id != current_user.organization_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get estimation
        estimation = await batch_processor.estimate_import_time(
            start_date=start_date,
            end_date=end_date,
            stage_filter=stage_filter,
            batch_size=batch_size
        )
        
        return StandardResponse(
            success=True,
            message="Import estimation completed",
            data=estimation
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to estimate import time for connection {connection_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{connection_id}/clear-cache")
async def clear_sync_cache(
    connection_id: str = Path(..., description="Salesforce connection ID"),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
) -> StandardResponse:
    """
    Clear synchronization cache for a connection.
    
    This forces the next delta sync to perform a full comparison.
    """
    try:
        # Get delta sync manager
        delta_sync = await create_delta_sync(connection_id)
        
        # Verify user has access to this connection
        if delta_sync.connection.organization_id != current_user.organization_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Clear cache
        await delta_sync.clear_cache()
        
        logger.info(f"Cleared sync cache for connection {connection_id} by user {current_user.id}")
        
        return StandardResponse(
            success=True,
            message="Sync cache cleared successfully",
            data={"connection_id": connection_id, "cache_cleared": True}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to clear cache for connection {connection_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Background task functions
async def _run_sync_task(
    connection_id: str,
    mode: SyncMode,
    limit: Optional[int],
    stage_filter: Optional[List[str]],
    auto_generate_invoices: bool
):
    """Run synchronization task in background."""
    try:
        sync_manager = await create_sync_manager(connection_id)
        
        # Update configuration
        sync_manager.config.auto_generate_invoices = auto_generate_invoices
        
        # Run sync
        result = await sync_manager.sync_opportunities_from_salesforce(
            mode=mode,
            limit=limit,
            stage_filter=stage_filter
        )
        
        logger.info(f"Background sync completed for {connection_id}: "
                   f"{result.records_processed} processed, {result.records_failed} failed")
        
    except Exception as e:
        logger.error(f"Background sync failed for {connection_id}: {str(e)}")
    finally:
        # Remove from active tasks
        if connection_id in active_sync_tasks:
            del active_sync_tasks[connection_id]


async def _run_delta_sync_task(
    connection_id: str,
    force_full_comparison: bool,
    stage_filter: Optional[List[str]]
):
    """Run delta synchronization task in background."""
    try:
        delta_sync = await create_delta_sync(connection_id)
        
        # Run delta sync
        result = await delta_sync.perform_delta_sync(
            force_full_comparison=force_full_comparison,
            stage_filter=stage_filter
        )
        
        logger.info(f"Background delta sync completed for {connection_id}: "
                   f"{result.changes_detected} changes detected, {result.changes_processed} processed")
        
    except Exception as e:
        logger.error(f"Background delta sync failed for {connection_id}: {str(e)}")
    finally:
        # Remove from active tasks
        if connection_id in active_sync_tasks:
            del active_sync_tasks[connection_id]