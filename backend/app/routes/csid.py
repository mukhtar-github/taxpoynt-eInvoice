"""
CSID Routes for TaxPoynt eInvoice APP functionality.

This module provides endpoints for:
- Creating and managing Cryptographic Signature Identifiers (CSIDs)
- Verifying and validating CSIDs
- Revoking CSIDs
"""

from fastapi import APIRouter, Depends, HTTPException, status, Body, Query
from sqlalchemy.orm import Session
from typing import Dict, List, Optional, Any
from uuid import UUID

from app.db.session import get_db
from app.models.csid import CSIDStatus
from app.schemas.csid import (
    CSIDCreate, CSIDUpdate, CSID, CSIDRevoke, CSIDVerification
)
from app.services.csid_service import CSIDService
from app.dependencies.auth import get_current_user

router = APIRouter(prefix="/csids", tags=["csids"])


@router.post("", response_model=CSID)
async def create_csid(
    csid_in: CSIDCreate,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user)
):
    """
    Create a new CSID for a certificate.
    """
    csid_service = CSIDService(db)
    
    try:
        csid = csid_service.create_csid(csid_in, current_user.id)
        return csid
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("", response_model=List[CSID])
async def list_csids(
    organization_id: Optional[UUID] = Query(None, description="Filter by organization ID"),
    certificate_id: Optional[UUID] = Query(None, description="Filter by certificate ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=100, description="Maximum number of records to return"),
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user)
):
    """
    List CSIDs with optional filtering.
    """
    csid_service = CSIDService(db)
    
    csids = csid_service.get_csids(
        organization_id=organization_id,
        certificate_id=certificate_id,
        is_active=is_active,
        skip=skip,
        limit=limit
    )
    
    return csids


@router.get("/{csid_id}", response_model=CSID)
async def get_csid(
    csid_id: UUID,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user)
):
    """
    Get a CSID by ID.
    """
    csid_service = CSIDService(db)
    csid = csid_service.get_csid(csid_id)
    
    if not csid:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="CSID not found"
        )
    
    return csid


@router.get("/verify/{csid_value}", response_model=CSIDVerification)
async def verify_csid(
    csid_value: str,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user)
):
    """
    Verify a CSID's validity.
    """
    csid_service = CSIDService(db)
    is_valid, status, errors = csid_service.verify_csid(csid_value)
    
    return CSIDVerification(
        valid=is_valid,
        status=status,
        errors=errors,
        warnings=[],
        details={}
    )


@router.put("/{csid_id}", response_model=CSID)
async def update_csid(
    csid_id: UUID,
    csid_in: CSIDUpdate,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user)
):
    """
    Update a CSID.
    """
    csid_service = CSIDService(db)
    csid = csid_service.update_csid(
        csid_id, 
        csid_in, 
        current_user.id
    )
    
    if not csid:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="CSID not found"
        )
    
    return csid


@router.put("/{csid_id}/revoke", response_model=Dict[str, Any])
async def revoke_csid(
    csid_id: UUID,
    revoke_data: CSIDRevoke,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user)
):
    """
    Revoke an active CSID.
    """
    csid_service = CSIDService(db)
    success = csid_service.revoke_csid(
        csid_id, 
        revoke_data.reason, 
        current_user.id
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not revoke CSID. It may not exist or not be in an active state."
        )
    
    return {"message": "CSID successfully revoked"}
