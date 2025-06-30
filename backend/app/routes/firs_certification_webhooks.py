"""
FIRS Certification Webhook routes for enhanced e-invoicing compliance.

This module provides webhook endpoints specifically for FIRS certification testing:
1. Invoice status updates (validation, signing, confirmation)
2. Transmission status updates (submit, acknowledge, error)
3. Validation result notifications
"""

from typing import Dict, Any, Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
from sqlalchemy.orm import Session
import hmac
import hashlib

from app.db.session import get_db
from app.core.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/api/v1/webhooks/firs-certification",
    tags=["firs-certification-webhooks"],
    responses={404: {"description": "Not found"}},
)


def verify_firs_signature(payload: bytes, signature: str) -> bool:
    """
    Verify the signature of a webhook payload from FIRS.
    
    Args:
        payload: Raw request body bytes
        signature: Signature from the X-FIRS-Signature header
        
    Returns:
        True if signature is valid, False otherwise
    """
    if not settings.FIRS_WEBHOOK_SECRET:
        logger.warning("FIRS webhook secret not configured, skipping signature verification")
        return True
    
    # Compute expected signature
    computed_signature = hmac.new(
        settings.FIRS_WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    # Compare signatures with constant-time comparison
    return hmac.compare_digest(computed_signature, signature)


@router.post("/invoice-status")
async def firs_invoice_status_webhook(
    request: Request,
    db: Session = Depends(get_db),
    x_firs_signature: Optional[str] = Header(None, alias="X-FIRS-Signature")
):
    """
    Handle FIRS invoice status update webhooks for certification testing.
    
    This endpoint receives status updates from FIRS for invoice processing,
    including validation, signing, transmission, and confirmation status.
    """
    try:
        # Get raw request body for signature verification
        body = await request.body()
        
        # Verify webhook signature if provided
        if x_firs_signature and not verify_firs_signature(body, x_firs_signature):
            logger.warning(f"Invalid FIRS signature for invoice status webhook")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook signature"
            )
        
        # Parse webhook payload
        payload = await request.json()
        
        # Extract key information
        irn = payload.get('irn')
        invoice_status = payload.get('status')
        business_id = payload.get('business_id')
        timestamp = payload.get('timestamp')
        error_details = payload.get('error_details')
        
        logger.info(f"Received FIRS invoice status webhook: IRN={irn}, Status={invoice_status}")
        
        # Process the status update
        await process_firs_invoice_status_update(
            db=db,
            irn=irn,
            status=invoice_status,
            business_id=business_id,
            timestamp=timestamp,
            error_details=error_details
        )
        
        return {"status": "success", "message": "Invoice status update processed"}
        
    except Exception as e:
        logger.error(f"Error processing FIRS invoice status webhook: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process webhook"
        )


@router.post("/transmission-status")
async def firs_transmission_status_webhook(
    request: Request,
    db: Session = Depends(get_db),
    x_firs_signature: Optional[str] = Header(None, alias="X-FIRS-Signature")
):
    """
    Handle FIRS transmission status update webhooks for certification testing.
    
    This endpoint receives updates about invoice transmission to/from FIRS,
    including transmission success, failure, and acknowledgment status.
    """
    try:
        # Get raw request body for signature verification
        body = await request.body()
        
        # Verify webhook signature if provided
        if x_firs_signature and not verify_firs_signature(body, x_firs_signature):
            logger.warning(f"Invalid FIRS signature for transmission status webhook")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook signature"
            )
        
        # Parse webhook payload
        payload = await request.json()
        
        # Extract key information
        irn = payload.get('irn')
        transmission_id = payload.get('transmission_id')
        transmission_status = payload.get('status')
        timestamp = payload.get('timestamp')
        error_details = payload.get('error_details')
        
        logger.info(f"Received FIRS transmission status webhook: IRN={irn}, TransmissionID={transmission_id}, Status={transmission_status}")
        
        # Process the transmission status update
        await process_firs_transmission_status_update(
            db=db,
            irn=irn,
            transmission_id=transmission_id,
            status=transmission_status,
            timestamp=timestamp,
            error_details=error_details
        )
        
        return {"status": "success", "message": "Transmission status update processed"}
        
    except Exception as e:
        logger.error(f"Error processing FIRS transmission status webhook: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process webhook"
        )


@router.post("/validation-result")
async def firs_validation_result_webhook(
    request: Request,
    db: Session = Depends(get_db),
    x_firs_signature: Optional[str] = Header(None, alias="X-FIRS-Signature")
):
    """
    Handle FIRS validation result webhooks for certification testing.
    
    This endpoint receives validation results from FIRS for invoice
    structure, content, and compliance checking.
    """
    try:
        # Get raw request body for signature verification
        body = await request.body()
        
        # Verify webhook signature if provided
        if x_firs_signature and not verify_firs_signature(body, x_firs_signature):
            logger.warning(f"Invalid FIRS signature for validation result webhook")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook signature"
            )
        
        # Parse webhook payload
        payload = await request.json()
        
        # Extract key information
        irn = payload.get('irn')
        validation_status = payload.get('status')
        validation_errors = payload.get('validation_errors', [])
        timestamp = payload.get('timestamp')
        
        logger.info(f"Received FIRS validation result webhook: IRN={irn}, Status={validation_status}")
        
        # Process the validation result
        await process_firs_validation_result(
            db=db,
            irn=irn,
            status=validation_status,
            validation_errors=validation_errors,
            timestamp=timestamp
        )
        
        return {"status": "success", "message": "Validation result processed"}
        
    except Exception as e:
        logger.error(f"Error processing FIRS validation result webhook: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process webhook"
        )


# Helper functions for processing webhook data
async def process_firs_invoice_status_update(
    db: Session,
    irn: str,
    status: str,
    business_id: str,
    timestamp: str,
    error_details: Optional[Dict[str, Any]] = None
):
    """Process FIRS invoice status update."""
    # Implementation will use existing submission service patterns
    logger.info(f"Processing invoice status update: {irn} -> {status}")
    
    # Update IRN status in database
    from app.models.irn import IRNRecord, IRNStatus
    
    # Find the IRN record
    irn_record = db.query(IRNRecord).filter(IRNRecord.irn == irn).first()
    if irn_record:
        # Update status based on FIRS response
        if status.lower() == "validated":
            irn_record.status = IRNStatus.VALIDATED
        elif status.lower() == "signed":
            irn_record.status = IRNStatus.SIGNED
        elif status.lower() == "transmitted":
            irn_record.status = IRNStatus.TRANSMITTED
        elif status.lower() == "confirmed":
            irn_record.status = IRNStatus.CONFIRMED
        elif status.lower() == "failed":
            irn_record.status = IRNStatus.FAILED
        
        irn_record.last_updated = timestamp
        if error_details:
            irn_record.error_message = str(error_details)
        
        db.commit()
        logger.info(f"Updated IRN {irn} status to {irn_record.status}")
    else:
        logger.warning(f"IRN record not found: {irn}")


async def process_firs_transmission_status_update(
    db: Session,
    irn: str,
    transmission_id: str,
    status: str,
    timestamp: str,
    error_details: Optional[Dict[str, Any]] = None
):
    """Process FIRS transmission status update."""
    logger.info(f"Processing transmission status update: {irn} -> {status}")
    
    # Update transmission status in database
    from app.models.transmission import Transmission, TransmissionStatus
    
    # Find the transmission record
    transmission = db.query(Transmission).filter(
        Transmission.irn == irn,
        Transmission.transmission_id == transmission_id
    ).first()
    
    if transmission:
        # Update status based on FIRS response
        if status.lower() == "submitted":
            transmission.status = TransmissionStatus.SUBMITTED
        elif status.lower() == "acknowledged":
            transmission.status = TransmissionStatus.ACKNOWLEDGED
        elif status.lower() == "processed":
            transmission.status = TransmissionStatus.PROCESSED
        elif status.lower() == "failed":
            transmission.status = TransmissionStatus.FAILED
        
        transmission.last_updated = timestamp
        if error_details:
            transmission.error_message = str(error_details)
        
        db.commit()
        logger.info(f"Updated transmission {transmission_id} status to {transmission.status}")
    else:
        logger.warning(f"Transmission record not found: {transmission_id}")


async def process_firs_validation_result(
    db: Session,
    irn: str,
    status: str,
    validation_errors: List[Dict[str, Any]],
    timestamp: str
):
    """Process FIRS validation result."""
    logger.info(f"Processing validation result: {irn} -> {status}")
    
    # Update validation status in database
    from app.models.validation import ValidationRecord, ValidationStatus
    
    # Find or create validation record
    validation_record = db.query(ValidationRecord).filter(
        ValidationRecord.irn == irn
    ).first()
    
    if not validation_record:
        validation_record = ValidationRecord(
            irn=irn,
            validation_id=f"val_{irn}_{timestamp}"
        )
        db.add(validation_record)
    
    # Update validation status
    if status.lower() == "passed":
        validation_record.status = ValidationStatus.PASSED
    elif status.lower() == "failed":
        validation_record.status = ValidationStatus.FAILED
    elif status.lower() == "warning":
        validation_record.status = ValidationStatus.WARNING
    
    validation_record.validation_errors = validation_errors
    validation_record.validated_at = timestamp
    
    db.commit()
    logger.info(f"Updated validation for IRN {irn} with status {validation_record.status}")


@router.post("/unified")
async def firs_unified_webhook(
    request: Request,
    db: Session = Depends(get_db),
    x_firs_signature: Optional[str] = Header(None, alias="X-FIRS-Signature")
):
    """
    Unified FIRS webhook endpoint to handle all webhook events.
    
    This single endpoint handles all FIRS webhook events:
    - Invoice status updates
    - Transmission status updates  
    - Validation results
    
    The event type is determined by the 'event_type' field in the payload.
    """
    try:
        # Get raw request body for signature verification
        body = await request.body()
        
        # Verify webhook signature if provided
        if x_firs_signature and not verify_firs_signature(body, x_firs_signature):
            logger.warning(f"Invalid FIRS signature for unified webhook")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook signature"
            )
        
        # Parse webhook payload
        payload = await request.json()
        
        # Extract event type to determine processing
        event_type = payload.get('event_type', '').lower()
        irn = payload.get('irn')
        timestamp = payload.get('timestamp')
        
        logger.info(f"Received FIRS unified webhook: Type={event_type}, IRN={irn}")
        
        # Route to appropriate handler based on event type
        if event_type in ['invoice_status', 'invoice-status', 'status']:
            # Handle invoice status updates
            invoice_status = payload.get('status')
            business_id = payload.get('business_id')
            error_details = payload.get('error_details')
            
            await process_firs_invoice_status_update(
                db=db,
                irn=irn,
                status=invoice_status,
                business_id=business_id,
                timestamp=timestamp,
                error_details=error_details
            )
            
        elif event_type in ['transmission_status', 'transmission-status', 'transmission']:
            # Handle transmission status updates
            transmission_id = payload.get('transmission_id')
            transmission_status = payload.get('status')
            error_details = payload.get('error_details')
            
            await process_firs_transmission_status_update(
                db=db,
                irn=irn,
                transmission_id=transmission_id,
                status=transmission_status,
                timestamp=timestamp,
                error_details=error_details
            )
            
        elif event_type in ['validation_result', 'validation-result', 'validation']:
            # Handle validation results
            validation_status = payload.get('status')
            validation_errors = payload.get('validation_errors', [])
            
            await process_firs_validation_result(
                db=db,
                irn=irn,
                status=validation_status,
                validation_errors=validation_errors,
                timestamp=timestamp
            )
            
        else:
            # Handle unknown event types gracefully
            logger.warning(f"Unknown FIRS webhook event type: {event_type}")
            # Still process as a generic status update
            status_value = payload.get('status')
            if status_value and irn:
                await process_firs_invoice_status_update(
                    db=db,
                    irn=irn,
                    status=status_value,
                    business_id=payload.get('business_id'),
                    timestamp=timestamp,
                    error_details=payload.get('error_details')
                )
        
        return {
            "status": "success", 
            "message": f"Webhook event '{event_type}' processed successfully",
            "irn": irn,
            "timestamp": timestamp
        }
        
    except Exception as e:
        logger.error(f"Error processing FIRS unified webhook: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process webhook"
        )