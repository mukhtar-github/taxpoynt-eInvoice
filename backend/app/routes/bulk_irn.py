"""
Bulk IRN (Invoice Reference Number) router with endpoints for generating and
validating IRNs in batch operations.
"""
from typing import Any, List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.models.organization import Organization
from app.schemas.irn import (
    IRNBatchGenerateRequest,
    IRNBatchResponse,
    IRNValidationBatchRequest,
    IRNValidationBatchResponse
)
from app.services.bulk_irn_service import (
    start_bulk_irn_generation,
    get_bulk_generation_status,
    validate_multiple_irns
)
from app.dependencies.auth import get_current_user, get_current_organization

router = APIRouter(prefix="/bulk-irn", tags=["bulk-irn"])


@router.post("", response_model=dict)
async def generate_irns_in_bulk(
    batch_request: IRNBatchGenerateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_organization: Organization = Depends(get_current_organization)
) -> Any:
    """
    Generate IRNs in bulk for multiple invoice numbers.
    
    This endpoint starts a background task to generate IRNs for all the provided
    invoice numbers. It returns a batch ID that can be used to check the status
    of the generation process.
    """
    # Validate batch size
    if len(batch_request.invoice_numbers) > 1000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Batch size cannot exceed 1000 invoice numbers"
        )
    
    # Start background task for bulk generation
    batch_id = start_bulk_irn_generation(
        background_tasks,
        db,
        batch_request,
        current_user.id,
        current_organization.id
    )
    
    return {
        "batch_id": batch_id,
        "message": f"Bulk IRN generation started for {len(batch_request.invoice_numbers)} invoices",
        "status_endpoint": f"/bulk-irn/status/{batch_id}"
    }


@router.get("/status/{batch_id}")
async def get_bulk_irn_generation_status(
    batch_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Check the status of a bulk IRN generation job.
    
    This endpoint returns the current status of a bulk generation job, including
    how many IRNs have been successfully generated, how many have failed, and the
    overall progress.
    """
    # Get status from cache
    status = get_bulk_generation_status(batch_id)
    
    if status.get("status") == "not_found":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bulk IRN generation job with ID {batch_id} not found"
        )
    
    return status


@router.post("/validate", response_model=IRNValidationBatchResponse)
async def validate_irns_in_bulk(
    validation_request: IRNValidationBatchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Validate multiple IRNs in a single request.
    
    This endpoint checks the validity of multiple IRNs at once and returns
    the validation results for each IRN.
    """
    # Validate batch size
    if len(validation_request.irn_values) > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot validate more than 100 IRNs in a single request"
        )
    
    # Validate the IRNs
    validation_results = await validate_multiple_irns(
        db,
        validation_request.irn_values,
        current_user.id
    )
    
    return validation_results


@router.post("/firs-validate", response_model=dict)
async def validate_irns_with_firs(
    validation_request: IRNValidationBatchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Validate IRNs with the FIRS sandbox API.
    
    This endpoint sends the IRNs to the FIRS sandbox API for validation
    and returns the validation results. This is used to test integration
    with the FIRS e-Invoicing system.
    """
    # Validate batch size for FIRS API (it may have different limits)
    if len(validation_request.irn_values) > 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot validate more than 50 IRNs with FIRS in a single request"
        )
    
    # Import here to avoid circular import
    from app.services.firs_service import validate_irns_with_firs_sandbox
    
    # Send to FIRS sandbox for validation
    firs_results = await validate_irns_with_firs_sandbox(
        db,
        validation_request.irn_values,
        current_user.id
    )
    
    return firs_results
