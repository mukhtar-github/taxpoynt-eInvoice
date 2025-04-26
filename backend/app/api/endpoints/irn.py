from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional
import logging

from app.api.deps import get_db, get_current_active_user
from app.models.user import User
from app.models.integration import Integration
from app.schemas.irn import (
    IRNGenerateRequest,
    IRNBatchGenerateRequest,
    IRNResponse,
    IRNBatchResponse,
    IRNStatusUpdate
)
from app.crud import irn as crud_irn
from app.crud import integration as crud_integration

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/generate", response_model=IRNResponse)
def generate_irn(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    request: IRNGenerateRequest
):
    """
    Generate a single IRN for an invoice.
    
    Follows FIRS format: InvoiceNumber-ServiceID-YYYYMMDD
    """
    # Get the integration
    integration = crud_integration.get_integration_by_id(db, request.integration_id)
    if not integration:
        raise HTTPException(
            status_code=404,
            detail="Integration not found"
        )
    
    # Get service ID from organization credentials
    # For POC, use a placeholder service ID
    service_id = "94ND90NR"  # In production, retrieve from organization settings
    
    # Validate timestamp if provided
    timestamp = request.timestamp or datetime.now().strftime("%Y%m%d")
    
    # Validate IRN components
    if not crud_irn.validate_irn_format(request.invoice_number, service_id, timestamp):
        raise HTTPException(
            status_code=400,
            detail="Invalid IRN components. Invoice number must be alphanumeric with no special characters, service ID must be 8 characters, and timestamp must be in YYYYMMDD format."
        )
    
    # Create IRN record
    try:
        irn_record = crud_irn.create_irn(db, request, service_id)
        return irn_record
    except Exception as e:
        logger.error(f"Error generating IRN: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate IRN: {str(e)}"
        )


@router.post("/generate-batch", response_model=IRNBatchResponse)
def generate_batch_irn(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    request: IRNBatchGenerateRequest
):
    """
    Generate multiple IRNs in a batch.
    """
    # Get the integration
    integration = crud_integration.get_integration_by_id(db, request.integration_id)
    if not integration:
        raise HTTPException(
            status_code=404,
            detail="Integration not found"
        )
    
    # Get service ID from organization credentials
    # For POC, use a placeholder service ID
    service_id = "94ND90NR"  # In production, retrieve from organization settings
    
    # Generate IRNs for each invoice number
    irn_records = []
    timestamp = request.timestamp or datetime.now().strftime("%Y%m%d")
    
    for invoice_number in request.invoice_numbers:
        # Create individual request
        single_request = IRNGenerateRequest(
            integration_id=request.integration_id,
            invoice_number=invoice_number,
            timestamp=timestamp
        )
        
        # Validate and create IRN
        if crud_irn.validate_irn_format(invoice_number, service_id, timestamp):
            try:
                irn_record = crud_irn.create_irn(db, single_request, service_id)
                irn_records.append(irn_record)
            except Exception as e:
                logger.error(f"Error generating IRN for {invoice_number}: {str(e)}")
                # Continue with other invoice numbers
        else:
            logger.warning(f"Invalid invoice number format: {invoice_number}")
            # Continue with other invoice numbers
    
    return {
        "irns": irn_records,
        "count": len(irn_records)
    }


@router.get("/{irn}", response_model=IRNResponse)
def get_irn_details(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    irn: str
):
    """
    Get IRN details and validate its format.
    """
    irn_record = crud_irn.get_irn_by_value(db, irn)
    if not irn_record:
        raise HTTPException(
            status_code=404,
            detail="IRN not found"
        )
    
    # Check if IRN is expired
    if irn_record.valid_until < datetime.now() and irn_record.status != "expired":
        irn_record = crud_irn.update_irn_status(db, irn, "expired")
    
    return irn_record


@router.get("/", response_model=List[IRNResponse])
def list_irns(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    integration_id: str = Query(..., description="Integration ID"),
    skip: int = 0,
    limit: int = 100
):
    """
    List IRNs for a specific integration with pagination.
    """
    # Verify integration exists
    integration = crud_integration.get_integration_by_id(db, integration_id)
    if not integration:
        raise HTTPException(
            status_code=404,
            detail="Integration not found"
        )
    
    irn_records = crud_irn.get_irns_by_integration(db, integration_id, skip, limit)
    return irn_records


@router.post("/{irn}/status", response_model=IRNResponse)
def update_irn_status(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    irn: str,
    status_update: IRNStatusUpdate
):
    """
    Update the status of an IRN (used, unused, expired).
    """
    # Verify IRN exists
    irn_record = crud_irn.get_irn_by_value(db, irn)
    if not irn_record:
        raise HTTPException(
            status_code=404,
            detail="IRN not found"
        )
    
    # Validate status
    if status_update.status not in ["used", "unused", "expired"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid status. Must be one of: used, unused, expired"
        )
    
    # Update status
    updated_irn = crud_irn.update_irn_status(
        db, 
        irn, 
        status_update.status, 
        status_update.invoice_id
    )
    
    return updated_irn


@router.get("/metrics", response_model=dict)
def get_irn_metrics(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    integration_id: Optional[str] = Query(None, description="Optional integration ID to filter metrics")
):
    """
    Get IRN usage metrics (for POC, a simple count by status).
    """
    # In a production version, these would come from database aggregation queries
    return {
        "total_generated": 100,
        "used": 65,
        "unused": 30,
        "expired": 5
    } 