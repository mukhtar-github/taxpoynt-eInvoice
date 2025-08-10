"""
Secure Transmission API Routes

Exposes endpoints for secure transmission to FIRS with enhanced security features,
including encryption, retry logic, and receipt management.
"""

import uuid
import logging
from typing import Dict, List, Any, Optional, Union
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.api import deps
from app.models.transmission import TransmissionStatus
from app.schemas.transmission import (
    TransmissionCreate, 
    TransmissionResponse, 
    TransmissionStatusResponse,
    TransmissionReceiptResponse
)
from app.services.firs_app.transmission_service import FIRSTransmissionService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/firs/transmit", response_model=TransmissionResponse)
async def transmit_to_firs(
    *,
    db: Session = Depends(deps.get_db),
    background_tasks: BackgroundTasks,
    payload: Dict[str, Any],
    organization_id: UUID,
    certificate_id: Optional[UUID] = None,
    submission_id: Optional[UUID] = None,
    metadata: Optional[Dict[str, Any]] = None,
    current_user = Depends(deps.get_current_active_user),
):
    """
    Create and execute a secure transmission to FIRS.
    
    The payload will be encrypted using FIRS standards and transmitted securely.
    Returns the transmission record ID for tracking.
    """
    try:
        firs_service = FIRSTransmissionService(db)
        
        # Create the transmission record
        transmission = await firs_service.create_firs_transmission(
            payload=payload,
            organization_id=organization_id,
            certificate_id=certificate_id,
            submission_id=submission_id,
            metadata=metadata,
            user_id=current_user.id if current_user else None
        )
        
        # Add transmission to background task queue
        background_tasks.add_task(
            firs_service.transmit_to_firs,
            transmission_id=transmission.id
        )
        
        return {
            "transmission_id": transmission.id,
            "status": TransmissionStatus.PENDING,
            "message": "Transmission queued successfully"
        }
        
    except Exception as e:
        logger.error(f"Error creating FIRS transmission: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create transmission: {str(e)}"
        )


@router.get("/transmissions/{transmission_id}/status", response_model=TransmissionStatusResponse)
async def get_transmission_status(
    transmission_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_active_user),
):
    """
    Get the current status of a transmission, including retry information.
    
    For completed transmissions, includes FIRS API status information.
    """
    try:
        firs_service = FIRSTransmissionService(db)
        status_info = await firs_service.check_transmission_status(transmission_id)
        
        return status_info
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error checking transmission status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check transmission status: {str(e)}"
        )


@router.post("/transmissions/{transmission_id}/retry", response_model=TransmissionResponse)
async def retry_transmission(
    transmission_id: UUID,
    background_tasks: BackgroundTasks,
    max_retries: Optional[int] = 3,
    force: Optional[bool] = False,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_active_user),
):
    """
    Manually trigger a retry for a failed or pending transmission.
    
    Allows forcing retry for transmissions in other states if needed.
    """
    try:
        # First check if this is a FIRS transmission
        firs_service = FIRSTransmissionService(db)
        
        # Get the transmission record to check its type
        transmission = db.query(firs_service.transmission_service.__class__.db.query).filter(
            firs_service.transmission_service.__class__.db.query.id == transmission_id
        ).first()
        
        if not transmission:
            raise ValueError(f"Transmission {transmission_id} not found")
            
        # For now, we only support FIRS retries
        if transmission.transmission_metadata.get("destination") == "FIRS":
            # Add to background tasks
            background_tasks.add_task(
                firs_service.transmit_to_firs,
                transmission_id=transmission_id,
                retrying=True
            )
            
            return {
                "transmission_id": transmission_id,
                "status": TransmissionStatus.RETRYING,
                "message": "Transmission retry initiated"
            }
        else:
            raise ValueError(f"Unsupported transmission destination: {transmission.transmission_metadata.get('destination')}")
            
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error retrying transmission: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retry transmission: {str(e)}"
        )


@router.get("/transmissions/{transmission_id}/receipt", response_model=TransmissionReceiptResponse)
async def get_transmission_receipt(
    transmission_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_active_user),
):
    """
    Retrieve the receipt for a completed transmission.
    
    Returns detailed receipt information from FIRS or other authority.
    """
    try:
        # Get the transmission record
        from app.models.receipt import TransmissionReceipt
        
        receipt = db.query(TransmissionReceipt).filter(
            TransmissionReceipt.transmission_id == transmission_id
        ).first()
        
        if not receipt:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No receipt found for this transmission"
            )
            
        return {
            "receipt_id": receipt.receipt_id,
            "transmission_id": receipt.transmission_id,
            "timestamp": receipt.receipt_timestamp,
            "verification_status": receipt.verification_status,
            "receipt_data": receipt.receipt_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving transmission receipt: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve receipt: {str(e)}"
        )
