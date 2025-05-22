"""
Webhook routes for FIRS submission status notifications.

This module provides endpoints for:
1. Receiving webhook notifications from FIRS about submission status updates
2. Handling internal status notification events
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, Body, HTTPException, status, Request, Header
from sqlalchemy.orm import Session
import hmac
import hashlib

from app.database.session import get_db
from app.models.submission import SubmissionRecord, SubmissionStatus
from app.services.submission_service import process_status_update_from_firs
from app.core.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/api/v1/webhooks",
    tags=["webhooks"],
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


@router.post("/firs/status", status_code=status.HTTP_200_OK)
async def firs_status_webhook(
    request: Request,
    x_firs_signature: Optional[str] = Header(None),
    payload: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
):
    """
    Webhook endpoint for receiving FIRS invoice submission status updates.
    
    This endpoint receives status notifications from FIRS when the status
    of a submission changes, allowing for real-time tracking and processing.
    """
    # Verify webhook signature if provided
    if x_firs_signature:
        # Get raw request body for signature verification
        body = await request.body()
        
        if not verify_firs_signature(body, x_firs_signature):
            logger.warning("Invalid FIRS webhook signature")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid signature"
            )
    
    # Process the webhook payload
    try:
        logger.info(f"Received FIRS status webhook: {payload.get('event_type')} for submission {payload.get('submission_id')}")
        
        # Extract submission ID and verify it exists
        submission_id = payload.get("submission_id")
        if not submission_id:
            logger.error("Missing submission_id in webhook payload")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing submission_id in payload"
            )
        
        # Check if this is a status update event
        event_type = payload.get("event_type", "").lower()
        if event_type != "status_update":
            logger.info(f"Ignoring non-status event: {event_type}")
            return {"status": "success", "message": f"Event {event_type} acknowledged but not processed"}
        
        # Process the status update
        updated_submission = await process_status_update_from_firs(db, payload)
        
        return {
            "status": "success",
            "message": f"Status updated to {updated_submission.status.value}",
            "submission_id": submission_id
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error processing FIRS webhook: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing webhook: {str(e)}"
        )


@router.post("/internal/status/{submission_id}", status_code=status.HTTP_200_OK)
async def internal_status_update(
    submission_id: str,
    payload: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
):
    """
    Internal webhook endpoint for updating submission status.
    
    This endpoint allows internal systems to update submission status
    without going through the FIRS API, useful for test environments
    and handling cases where FIRS webhooks are not configured.
    """
    try:
        logger.info(f"Received internal status update for submission {submission_id}")
        
        # Validate the status value
        status_value = payload.get("status")
        try:
            submission_status = SubmissionStatus(status_value)
        except ValueError:
            logger.error(f"Invalid status value: {status_value}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status value: {status_value}"
            )
        
        # Check if submission exists
        submission = db.query(SubmissionRecord).filter(
            SubmissionRecord.submission_id == submission_id
        ).first()
        
        if not submission:
            logger.error(f"Submission not found: {submission_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Submission {submission_id} not found"
            )
        
        # Process the status update
        from app.services.submission_service import update_submission_status
        updated_submission = await update_submission_status(
            db=db,
            submission_id=submission_id,
            status=submission_status,
            message=payload.get("message"),
            response_data=payload.get("details"),
            trigger_webhook=payload.get("trigger_webhook", True)
        )
        
        return {
            "status": "success",
            "message": f"Status updated to {updated_submission.status.value}",
            "submission_id": submission_id
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error processing internal status update: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing status update: {str(e)}"
        )
