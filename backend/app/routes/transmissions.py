"""
Transmission Routes for TaxPoynt eInvoice APP functionality.

This module provides endpoints for:
- Creating and tracking secure transmissions to FIRS
- Managing retry strategies for failed transmissions
- Monitoring transmission status
"""

from fastapi import APIRouter, Depends, HTTPException, status, Body, Query
from sqlalchemy.orm import Session
from typing import Dict, List, Optional, Any
from uuid import UUID
from datetime import datetime, timedelta

from app.db.session import get_db
from app.models.transmission import TransmissionStatus
from app.schemas.transmission import (
    TransmissionCreate, TransmissionUpdate, Transmission, TransmissionWithResponse, 
    TransmissionRetry, TransmissionBatchStatus, TransmissionTimeline, TransmissionTimePoint,
    TransmissionHistory, TransmissionHistoryEvent, TransmissionDebugInfo,
    TransmissionBatchUpdate, TransmissionBatchUpdateResponse
)
from app.services.firs_app.transmission_service import TransmissionService
from app.services.firs_app.key_service import KeyManagementService, get_key_service
from app.dependencies.auth import get_current_user

router = APIRouter(prefix="/transmissions", tags=["transmissions"])


@router.post("", response_model=Transmission)
async def create_transmission(
    transmission_in: TransmissionCreate,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user),
    key_service: KeyManagementService = Depends(get_key_service)
):
    """
    Create a new transmission record.
    
    Encrypts the payload if specified and prepares for transmission to FIRS.
    """
    transmission_service = TransmissionService(db, key_service)
    
    try:
        transmission = transmission_service.create_transmission(
            transmission_in, 
            current_user.id
        )
        return transmission
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/timeline", response_model=TransmissionTimeline)
async def get_transmission_timeline(
    organization_id: Optional[UUID] = Query(None, description="Filter by organization ID"),
    start_date: Optional[datetime] = Query(None, description="Start date for timeline"),
    end_date: Optional[datetime] = Query(None, description="End date for timeline"),
    interval: str = Query("day", description="Time interval for grouping (hour, day, week, month)"),
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user),
    key_service: KeyManagementService = Depends(get_key_service)
):
    """
    Get time-series data for transmissions based on specified interval.
    """
    transmission_service = TransmissionService(db, key_service)
    
    # Validate interval parameter
    valid_intervals = {'hour', 'day', 'week', 'month'}
    if interval not in valid_intervals:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid interval. Must be one of: {', '.join(valid_intervals)}"
        )
    
    # Get timeline data
    timeline_data = transmission_service.get_transmission_timeline(
        organization_id=organization_id,
        start_date=start_date,
        end_date=end_date,
        interval=interval
    )
    
    return TransmissionTimeline(
        timeline=[TransmissionTimePoint(**point) for point in timeline_data],
        interval=interval,
        start_date=start_date,
        end_date=end_date
    )


@router.get("/{transmission_id}/history", response_model=TransmissionHistory)
async def get_transmission_history(
    transmission_id: UUID,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user),
    key_service: KeyManagementService = Depends(get_key_service)
):
    """
    Get detailed history and debug information for a specific transmission.
    """
    transmission_service = TransmissionService(db, key_service)
    
    try:
        history_data = transmission_service.get_transmission_history(transmission_id)
        
        # Convert history events to proper schema format
        history_events = [
            TransmissionHistoryEvent(**event) for event in history_data['history']
        ]
        
        # Create the response model
        return TransmissionHistory(
            transmission=history_data['transmission'],
            history=history_events,
            debug_info=TransmissionDebugInfo(**history_data['debug_info'])
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving transmission history: {str(e)}"
        )


@router.post("/batch", response_model=TransmissionBatchUpdateResponse)
async def batch_update_transmissions(
    update_data: TransmissionBatchUpdate,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user),
    key_service: KeyManagementService = Depends(get_key_service)
):
    """
    Update multiple transmissions in a single batch operation.
    """
    transmission_service = TransmissionService(db, key_service)
    
    if not update_data.transmission_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No transmission IDs provided"
        )
    
    # Prepare the update fields
    update_fields = {}
    if update_data.status is not None:
        update_fields['status'] = update_data.status
    if update_data.response_data is not None:
        update_fields['response_data'] = update_data.response_data
    if update_data.transmission_metadata is not None:
        update_fields['transmission_metadata'] = update_data.transmission_metadata
    
    if not update_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )
    
    # Perform the batch update
    result = transmission_service.batch_update_transmissions(
        transmission_ids=update_data.transmission_ids,
        update_data=update_fields,
        current_user_id=current_user.id
    )
    
    return TransmissionBatchUpdateResponse(**result)


@router.post("/webhook", status_code=status.HTTP_202_ACCEPTED)
async def process_transmission_webhook(
    webhook_data: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    key_service: KeyManagementService = Depends(get_key_service)
):
    """
    Process webhook notifications for transmission status updates.
    
    This endpoint does not require authentication as it's called by external systems.
    Instead, it uses webhook secrets or signatures for verification.
    """
    transmission_service = TransmissionService(db, key_service)
    
    try:
        # Validate minimum required webhook data
        if 'transmission_id' not in webhook_data or 'status' not in webhook_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing required fields: transmission_id and status"
            )
        
        # Process the webhook asynchronously
        result = transmission_service.process_transmission_webhook(webhook_data)
        
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        # Log the error but don't expose details to the caller
        logger.error(f"Error processing webhook: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing webhook"
        )


@router.get("", response_model=List[Transmission])
async def list_transmissions(
    organization_id: Optional[UUID] = Query(None, description="Filter by organization ID"),
    certificate_id: Optional[UUID] = Query(None, description="Filter by certificate ID"),
    submission_id: Optional[UUID] = Query(None, description="Filter by submission ID"),
    status: Optional[TransmissionStatus] = Query(None, description="Filter by status"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=100, description="Maximum number of records to return"),
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user),
    key_service: KeyManagementService = Depends(get_key_service)
):
    """
    List transmissions with optional filtering.
    """
    transmission_service = TransmissionService(db, key_service)
    
    transmissions = transmission_service.get_transmissions(
        organization_id=organization_id,
        certificate_id=certificate_id,
        submission_id=submission_id,
        status=status,
        skip=skip,
        limit=limit
    )
    
    return transmissions


@router.get("/{transmission_id}", response_model=TransmissionWithResponse)
async def get_transmission(
    transmission_id: UUID,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user),
    key_service: KeyManagementService = Depends(get_key_service)
):
    """
    Get a transmission record by ID, including response data.
    """
    transmission_service = TransmissionService(db, key_service)
    transmission = transmission_service.get_transmission(transmission_id)
    
    if not transmission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transmission not found"
        )
    
    return transmission


@router.put("/{transmission_id}", response_model=Transmission)
async def update_transmission(
    transmission_id: UUID,
    transmission_in: TransmissionUpdate,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user),
    key_service: KeyManagementService = Depends(get_key_service)
):
    """
    Update a transmission record.
    """
    transmission_service = TransmissionService(db, key_service)
    transmission = transmission_service.update_transmission(
        transmission_id, 
        transmission_in, 
        current_user.id
    )
    
    if not transmission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transmission not found"
        )
    
    return transmission


@router.post("/{transmission_id}/retry", response_model=Dict[str, Any])
async def retry_transmission(
    transmission_id: UUID,
    retry_data: TransmissionRetry = Body(None),
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user),
    key_service: KeyManagementService = Depends(get_key_service)
):
    """
    Retry a failed or pending transmission.
    """
    transmission_service = TransmissionService(db, key_service)
    
    # Set default values if not provided
    max_retries = retry_data.max_retries if retry_data and retry_data.max_retries is not None else 3
    retry_delay = retry_data.retry_delay if retry_data and retry_data.retry_delay is not None else 0
    force = retry_data.force if retry_data and retry_data.force is not None else False
    
    success, message = transmission_service.retry_transmission(
        transmission_id,
        max_retries=max_retries,
        retry_delay=retry_delay,
        force=force,
        user_id=current_user.id
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    return {"message": message}


@router.get("/statistics", response_model=TransmissionBatchStatus)
async def get_transmission_statistics(
    organization_id: Optional[UUID] = Query(None, description="Filter by organization ID"),
    start_date: Optional[datetime] = Query(None, description="Start date for statistics"),
    end_date: Optional[datetime] = Query(None, description="End date for statistics"),
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user),
    key_service: KeyManagementService = Depends(get_key_service)
):
    """
    Get transmission statistics.
    """
    transmission_service = TransmissionService(db, key_service)
    
    # Default to last 30 days if no dates provided
    if not start_date:
        start_date = datetime.utcnow() - timedelta(days=30)
    
    if not end_date:
        end_date = datetime.utcnow()
    
    stats = transmission_service.get_transmission_statistics(
        organization_id=organization_id,
        start_date=start_date,
        end_date=end_date
    )
    
    return TransmissionBatchStatus(
        total=stats.get('total', 0),
        pending=stats.get('pending', 0),
        in_progress=stats.get('in_progress', 0),
        completed=stats.get('completed', 0),
        failed=stats.get('failed', 0),
        retrying=stats.get('retrying', 0),
        canceled=stats.get('canceled', 0),
        success_rate=stats.get('success_rate', 0.0),
        average_retries=stats.get('average_retries', 0.0),
        signed_transmissions=stats.get('signed_transmissions', 0)
    )
