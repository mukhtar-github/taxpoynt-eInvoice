"""
Certificate Request Routes for TaxPoynt eInvoice APP functionality.

This module provides endpoints for:
- Creating and managing certificate signing requests (CSRs)
- Tracking certificate request status
- Handling the certificate request lifecycle
"""

from fastapi import APIRouter, Depends, HTTPException, status, Body, Query
from sqlalchemy.orm import Session
from typing import Dict, List, Optional, Any
from uuid import UUID

from app.db.session import get_db
from app.models.certificate_request import CertificateRequestStatus, CertificateRequestType
from app.schemas.certificate_request import (
    CertificateRequestCreate, CertificateRequestUpdate, CertificateRequest,
    CertificateRequestCancel, CertificateRequestStatusUpdate
)
from app.services.certificate_request_service import CertificateRequestService
from app.services.key_service import KeyManagementService, get_key_service
from app.dependencies.auth import get_current_user

router = APIRouter(prefix="/certificate-requests", tags=["certificate-requests"])


@router.post("", response_model=CertificateRequest)
async def create_certificate_request(
    request_in: CertificateRequestCreate,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user),
    key_service: KeyManagementService = Depends(get_key_service)
):
    """
    Create a new certificate request.
    
    Either provide CSR data directly, or provide parameters to generate a CSR.
    """
    certificate_request_service = CertificateRequestService(db, key_service)
    
    try:
        certificate_request = certificate_request_service.create_certificate_request(
            request_in, 
            current_user.id
        )
        return certificate_request
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("", response_model=List[CertificateRequest])
async def list_certificate_requests(
    organization_id: Optional[UUID] = Query(None, description="Filter by organization ID"),
    status: Optional[CertificateRequestStatus] = Query(None, description="Filter by status"),
    request_type: Optional[CertificateRequestType] = Query(None, description="Filter by request type"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=100, description="Maximum number of records to return"),
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user),
    key_service: KeyManagementService = Depends(get_key_service)
):
    """
    List certificate requests with optional filtering.
    """
    certificate_request_service = CertificateRequestService(db, key_service)
    
    certificate_requests = certificate_request_service.get_certificate_requests(
        organization_id=organization_id,
        status=status,
        request_type=request_type,
        skip=skip,
        limit=limit
    )
    
    return certificate_requests


@router.get("/{request_id}", response_model=CertificateRequest)
async def get_certificate_request(
    request_id: UUID,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user),
    key_service: KeyManagementService = Depends(get_key_service)
):
    """
    Get a certificate request by ID.
    """
    certificate_request_service = CertificateRequestService(db, key_service)
    certificate_request = certificate_request_service.get_certificate_request(request_id)
    
    if not certificate_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Certificate request not found"
        )
    
    return certificate_request


@router.put("/{request_id}", response_model=CertificateRequest)
async def update_certificate_request(
    request_id: UUID,
    request_in: CertificateRequestUpdate,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user),
    key_service: KeyManagementService = Depends(get_key_service)
):
    """
    Update a certificate request.
    """
    certificate_request_service = CertificateRequestService(db, key_service)
    certificate_request = certificate_request_service.update_certificate_request(
        request_id, 
        request_in, 
        current_user.id
    )
    
    if not certificate_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Certificate request not found"
        )
    
    return certificate_request


@router.put("/{request_id}/cancel", response_model=Dict[str, Any])
async def cancel_certificate_request(
    request_id: UUID,
    cancel_data: CertificateRequestCancel,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user),
    key_service: KeyManagementService = Depends(get_key_service)
):
    """
    Cancel a pending certificate request.
    """
    certificate_request_service = CertificateRequestService(db, key_service)
    success = certificate_request_service.cancel_certificate_request(
        request_id, 
        cancel_data.reason, 
        current_user.id
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not cancel certificate request. It may not exist or not be in a cancellable state."
        )
    
    return {"message": "Certificate request successfully cancelled"}


@router.put("/{request_id}/status", response_model=CertificateRequest)
async def update_certificate_request_status(
    request_id: UUID,
    status_update: CertificateRequestStatusUpdate,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user),
    key_service: KeyManagementService = Depends(get_key_service)
):
    """
    Update the status of a certificate request.
    """
    certificate_request_service = CertificateRequestService(db, key_service)
    
    # Create update object with just the status field
    update_data = CertificateRequestUpdate(status=status_update.status)
    
    # Add notes to metadata if provided
    if status_update.notes:
        metadata = {"status_update_notes": status_update.notes}
        update_data.request_metadata = metadata
    
    certificate_request = certificate_request_service.update_certificate_request(
        request_id, 
        update_data, 
        current_user.id
    )
    
    if not certificate_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Certificate request not found"
        )
    
    return certificate_request
