"""
IRN (Invoice Reference Number) router with endpoints for generating, validating, and querying IRNs.
"""
from typing import Any, List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.models.organization import Organization
from app.schemas.irn import (
    IRNResponse,
    IRNCreate,
    IRNList,
    IRNValidationRequest,
    IRNValidationResponse,
    IRNStatus
)
from app.crud.irn import (
    create_irn,
    get_irn,
    get_irns_by_organization,
    validate_irn,
    update_irn_status
)
from app.dependencies.auth import get_current_user, get_current_organization
from app.services.firs_si.irn_generation_service import generate_irn, verify_irn

router = APIRouter(prefix="/irn", tags=["irn"])


@router.post("", response_model=IRNResponse)
async def generate_new_irn(
    irn_data: IRNCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_organization: Organization = Depends(get_current_organization)
) -> Any:
    """
    Generate a new Invoice Reference Number (IRN).
    
    This endpoint takes invoice data from Odoo, validates it,
    and generates a unique IRN that can be used for tax compliance.
    """
    # Generate IRN using the service
    irn_value, verification_code, hash_value = generate_irn(irn_data.invoice_data)
    
    # Store the IRN in the database
    db_irn = create_irn(
        db=db,
        user=current_user,
        organization=current_organization,
        irn_data=irn_data,
        irn_value=irn_value,
        verification_code=verification_code,
        hash_value=hash_value
    )
    
    return db_irn


@router.get("/{irn_id}", response_model=IRNResponse)
async def get_irn_by_id(
    irn_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_organization: Organization = Depends(get_current_organization)
) -> Any:
    """
    Get IRN details by ID.
    """
    # Get IRN from database
    db_irn = get_irn(db, irn_id, current_organization.id)
    
    if not db_irn:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"IRN with id {irn_id} not found"
        )
    
    return db_irn


@router.get("", response_model=IRNList)
async def list_irns(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_organization: Organization = Depends(get_current_organization),
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None
) -> Any:
    """
    List IRNs for the current organization.
    Optionally filter by status.
    """
    # Get IRNs from database
    db_irns = get_irns_by_organization(
        db, 
        organization_id=current_organization.id,
        status=status,
        skip=skip,
        limit=limit
    )
    
    return {
        "items": db_irns,
        "total": len(db_irns)
    }


@router.post("/validate", response_model=IRNValidationResponse)
async def validate_irn_endpoint(
    validation_request: IRNValidationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Validate an IRN.
    
    This endpoint verifies if an IRN is valid by checking:
    1. If it exists in the database
    2. If it has not expired
    3. If the invoice data hash matches
    """
    # Verify IRN
    is_valid, message = verify_irn(
        db,
        validation_request.irn_value,
        validation_request.verification_code,
        validation_request.invoice_data
    )
    
    # Log the validation attempt
    validation_record = validate_irn(
        db,
        validation_request.irn_value,
        is_valid,
        message,
        validated_by=current_user.email
    )
    
    return {
        "is_valid": is_valid,
        "message": message,
        "validation_date": validation_record.validation_date
    }


@router.put("/{irn_id}/status", response_model=IRNResponse)
async def update_irn_status_endpoint(
    irn_id: UUID,
    status: IRNStatus,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_organization: Organization = Depends(get_current_organization)
) -> Any:
    """
    Update the status of an IRN.
    
    This allows for:
    - Revoking an IRN if an invoice is canceled
    - Manually expiring an IRN
    - Reactivating an IRN in special cases
    """
    # Get IRN from database
    db_irn = get_irn(db, irn_id, current_organization.id)
    
    if not db_irn:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"IRN with id {irn_id} not found"
        )
    
    # Update IRN status
    updated_irn = update_irn_status(
        db,
        db_irn,
        status,
        updated_by=current_user.email
    )
    
    return updated_irn
