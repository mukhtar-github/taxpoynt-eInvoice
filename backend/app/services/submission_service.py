"""
Submission tracking and status update service for FIRS invoice submissions.

This service provides functions for:
1. Creating and updating submission records
2. Tracking submission status history
3. Managing webhook notifications for status changes
4. Processing status updates from FIRS API
"""

from typing import Dict, Any, List, Optional, Tuple, Union
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
import httpx
import json
import asyncio
from datetime import datetime, timedelta
from uuid import UUID, uuid4

from app.models.submission import (
    SubmissionRecord, 
    SubmissionStatusUpdate, 
    SubmissionNotification,
    SubmissionStatus,
    NotificationStatus
)
from app.models.irn import IRNRecord, IRNStatus
from app.models.integration import Integration
from app.core.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


async def create_submission_record(
    db: Session,
    submission_id: str,
    irn: str,
    integration_id: str,
    source_type: str,
    status: SubmissionStatus = SubmissionStatus.PENDING,
    status_message: Optional[str] = None,
    request_data: Optional[Dict[str, Any]] = None,
    response_data: Optional[Dict[str, Any]] = None,
    source_id: Optional[str] = None,
    submitted_by: Optional[UUID] = None,
    webhook_enabled: bool = False,
    webhook_url: Optional[str] = None,
) -> SubmissionRecord:
    """
    Create a new submission record to track an invoice submission to FIRS.
    
    Args:
        db: Database session
        submission_id: Unique submission ID from FIRS API
        irn: Invoice Reference Number (IRN)
        integration_id: Integration ID
        source_type: Source of the submission (e.g., 'odoo', 'manual', 'api')
        status: Initial submission status
        status_message: Optional status message
        request_data: Optional request data sent to FIRS API
        response_data: Optional response data from FIRS API
        source_id: Optional source identifier (e.g., Odoo invoice ID)
        submitted_by: Optional User ID of the submitter
        webhook_enabled: Whether webhook notifications are enabled
        webhook_url: Optional webhook URL for notifications
        
    Returns:
        The created submission record
    """
    # Validate that the IRN exists
    irn_record = db.query(IRNRecord).filter(IRNRecord.irn == irn).first()
    if not irn_record:
        logger.error(f"Cannot create submission record: IRN {irn} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"IRN {irn} not found"
        )
    
    # Create submission record
    submission = SubmissionRecord(
        submission_id=submission_id,
        irn=irn,
        integration_id=integration_id,
        status=status,
        status_message=status_message,
        request_data=request_data,
        response_data=response_data,
        source_type=source_type,
        source_id=source_id,
        submitted_by=submitted_by,
        webhook_enabled=webhook_enabled,
        webhook_url=webhook_url
    )
    
    # Create initial status update
    status_update = SubmissionStatusUpdate(
        status=status,
        message=status_message,
        response_data=response_data
    )
    
    submission.status_updates.append(status_update)
    
    db.add(submission)
    db.commit()
    db.refresh(submission)
    
    logger.info(f"Created submission record for IRN {irn} with submission ID {submission_id}")
    return submission


async def update_submission_status(
    db: Session,
    submission_id: str,
    status: SubmissionStatus,
    message: Optional[str] = None,
    response_data: Optional[Dict[str, Any]] = None,
    trigger_webhook: bool = True
) -> SubmissionRecord:
    """
    Update the status of a submission record.
    
    Args:
        db: Database session
        submission_id: Unique submission ID from FIRS API
        status: New submission status
        message: Optional status message
        response_data: Optional response data from FIRS API
        trigger_webhook: Whether to trigger webhook notification
        
    Returns:
        The updated submission record
    """
    # Find the submission record
    submission = db.query(SubmissionRecord).filter(
        SubmissionRecord.submission_id == submission_id
    ).first()
    
    if not submission:
        logger.error(f"Cannot update status: Submission {submission_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Submission {submission_id} not found"
        )
    
    # Create status update record
    status_update = SubmissionStatusUpdate(
        submission_id=submission.id,
        status=status,
        message=message,
        response_data=response_data
    )
    
    # Update main record
    submission.status = status
    submission.status_message = message
    submission.last_updated = datetime.utcnow()
    
    if response_data:
        submission.response_data = response_data
    
    db.add(status_update)
    db.add(submission)
    db.commit()
    db.refresh(submission)
    db.refresh(status_update)
    
    logger.info(f"Updated submission {submission_id} status to {status.value}")
    
    # Trigger webhook notification if enabled
    if trigger_webhook and submission.webhook_enabled and submission.webhook_url:
        await create_webhook_notification(db, submission.id, status_update.id)
    
    return submission


async def create_webhook_notification(
    db: Session,
    submission_id: UUID,
    status_update_id: UUID
) -> SubmissionNotification:
    """
    Create a webhook notification record for a status update.
    
    Args:
        db: Database session
        submission_id: Submission record ID
        status_update_id: Status update record ID
        
    Returns:
        The created notification record
    """
    # Get the submission and status update
    submission = db.query(SubmissionRecord).filter(SubmissionRecord.id == submission_id).first()
    status_update = db.query(SubmissionStatusUpdate).filter(SubmissionStatusUpdate.id == status_update_id).first()
    
    if not submission or not status_update:
        logger.error(f"Cannot create webhook notification: Submission or status update not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission or status update not found"
        )
    
    if not submission.webhook_url:
        logger.error(f"Cannot create webhook notification: No webhook URL configured")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No webhook URL configured"
        )
    
    # Create notification payload
    payload = {
        "event": "submission_status_update",
        "submission_id": submission.submission_id,
        "irn": submission.irn,
        "status": status_update.status.value,
        "message": status_update.message,
        "timestamp": status_update.timestamp.isoformat(),
        "source_type": submission.source_type,
        "source_id": submission.source_id
    }
    
    # Create notification record
    notification = SubmissionNotification(
        submission_id=submission.id,
        status_update_id=status_update.id,
        webhook_url=submission.webhook_url,
        payload=payload,
        status=NotificationStatus.PENDING,
        next_attempt=datetime.utcnow()
    )
    
    db.add(notification)
    db.commit()
    db.refresh(notification)
    
    logger.info(f"Created webhook notification for submission {submission.submission_id}")
    
    # Trigger delivery in background
    asyncio.create_task(deliver_webhook_notification(db, notification.id))
    
    return notification


async def deliver_webhook_notification(
    db: Session,
    notification_id: UUID,
    retry_count: int = 3,
    retry_delay: int = 60  # seconds
) -> bool:
    """
    Deliver a webhook notification to its configured URL.
    
    Args:
        db: Database session
        notification_id: Notification record ID
        retry_count: Number of retry attempts on failure
        retry_delay: Delay between retry attempts in seconds
        
    Returns:
        True if delivery was successful, False otherwise
    """
    notification = db.query(SubmissionNotification).filter(SubmissionNotification.id == notification_id).first()
    
    if not notification:
        logger.error(f"Cannot deliver webhook notification: Notification {notification_id} not found")
        return False
    
    # Update attempt tracking
    notification.attempts += 1
    notification.last_attempt = datetime.utcnow()
    notification.status = NotificationStatus.PENDING
    db.add(notification)
    db.commit()
    db.refresh(notification)
    
    try:
        # Send webhook notification
        async with httpx.AsyncClient(timeout=10.0) as client:
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "TaxPoynt-eInvoice/1.0",
                "X-TaxPoynt-Event": "submission_status_update",
                "X-TaxPoynt-Signature": compute_webhook_signature(notification.payload)
            }
            
            response = await client.post(
                notification.webhook_url,
                json=notification.payload,
                headers=headers
            )
            
            # Update notification with response
            notification.response_code = response.status_code
            notification.response_body = response.text[:1000]  # Limit response size
            
            # Check if successful
            if 200 <= response.status_code < 300:
                notification.status = NotificationStatus.DELIVERED
                notification.next_attempt = None
                logger.info(f"Successfully delivered webhook notification {notification_id}")
                db.add(notification)
                db.commit()
                return True
            else:
                logger.warning(
                    f"Webhook delivery failed with status {response.status_code}: {response.text[:100]}"
                )
                raise Exception(f"Webhook delivery failed with status {response.status_code}")
                
    except Exception as e:
        # Handle delivery failure
        notification.status = NotificationStatus.FAILED
        notification.error_message = str(e)[:500]  # Limit error message size
        
        # Schedule retry if attempts remain
        if notification.attempts < retry_count:
            notification.status = NotificationStatus.RETRY
            notification.next_attempt = datetime.utcnow() + timedelta(seconds=retry_delay)
            logger.info(f"Scheduling webhook retry {notification.attempts}/{retry_count} in {retry_delay}s")
            
            # Schedule retry task
            asyncio.create_task(
                retry_webhook_delivery(db, notification.id, retry_count, retry_delay)
            )
        
        db.add(notification)
        db.commit()
        return False


async def retry_webhook_delivery(
    db: Session,
    notification_id: UUID,
    retry_count: int,
    retry_delay: int
) -> None:
    """
    Retry webhook delivery after a delay.
    
    Args:
        db: Database session
        notification_id: Notification record ID
        retry_count: Maximum number of retry attempts
        retry_delay: Delay between retry attempts in seconds
    """
    # Wait for the retry delay
    await asyncio.sleep(retry_delay)
    
    # Attempt delivery again
    await deliver_webhook_notification(db, notification_id, retry_count, retry_delay * 2)


def compute_webhook_signature(payload: Dict[str, Any]) -> str:
    """
    Compute a signature for webhook payload verification.
    
    Args:
        payload: Webhook payload
        
    Returns:
        Signature string for the payload
    """
    import hmac
    import hashlib
    
    # Convert payload to JSON string
    payload_str = json.dumps(payload, sort_keys=True)
    
    # Compute HMAC using webhook secret
    signature = hmac.new(
        settings.WEBHOOK_SECRET.encode(),
        payload_str.encode(),
        hashlib.sha256
    ).hexdigest()
    
    return signature


async def process_status_update_from_firs(
    db: Session,
    status_data: Dict[str, Any]
) -> SubmissionRecord:
    """
    Process a status update received from FIRS.
    
    This function handles webhook callbacks from FIRS with status updates.
    
    Args:
        db: Database session
        status_data: Status update data from FIRS
        
    Returns:
        The updated submission record
    """
    # Extract key information from status data
    submission_id = status_data.get("submission_id")
    if not submission_id:
        logger.error("Cannot process FIRS status update: Missing submission_id")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing submission_id in status update"
        )
    
    # Map FIRS status to internal status
    firs_status = status_data.get("status", "").lower()
    internal_status = map_firs_status_to_internal(firs_status)
    
    # Update submission status
    return await update_submission_status(
        db=db,
        submission_id=submission_id,
        status=internal_status,
        message=status_data.get("message"),
        response_data=status_data,
        trigger_webhook=True
    )


def map_firs_status_to_internal(firs_status: str) -> SubmissionStatus:
    """
    Map FIRS API status values to internal submission status enum.
    
    Args:
        firs_status: Status string from FIRS API
        
    Returns:
        Corresponding internal SubmissionStatus
    """
    status_mapping = {
        "pending": SubmissionStatus.PENDING,
        "processing": SubmissionStatus.PROCESSING,
        "validated": SubmissionStatus.VALIDATED,
        "signed": SubmissionStatus.SIGNED,
        "accepted": SubmissionStatus.ACCEPTED,
        "rejected": SubmissionStatus.REJECTED,
        "failed": SubmissionStatus.FAILED,
        "error": SubmissionStatus.ERROR,
        "cancelled": SubmissionStatus.CANCELLED
    }
    
    return status_mapping.get(firs_status.lower(), SubmissionStatus.PENDING)
