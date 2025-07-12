"""
FIRS submission tracking integration.

This module extends the FIRS service with submission tracking capabilities,
ensuring all submissions are tracked in the database with status updates.
"""

from typing import Dict, Any, List, Optional, Union
from fastapi import Depends
from sqlalchemy.orm import Session
from uuid import UUID

from app.db.session import get_db
from app.services.firs_core.firs_api_client import firs_service, InvoiceSubmissionResponse, SubmissionStatus
from app.services.submission_service import create_submission_record, update_submission_status
from app.models.submission import SubmissionStatus as DbSubmissionStatus
from app.utils.logger import get_logger

logger = get_logger(__name__)


async def track_invoice_submission(
    db: Session,
    submission_response: InvoiceSubmissionResponse,
    irn: str,
    integration_id: str,
    source_type: str = "api",
    source_id: Optional[str] = None,
    submitted_by: Optional[UUID] = None,
    request_data: Optional[Dict[str, Any]] = None,
    webhook_url: Optional[str] = None
) -> InvoiceSubmissionResponse:
    """
    Track an invoice submission in the database.
    
    This function creates a submission record for a FIRS API submission response.
    
    Args:
        db: Database session
        submission_response: Response from FIRS API submission
        irn: Invoice Reference Number
        integration_id: Integration ID
        source_type: Source of the submission (e.g., 'odoo', 'manual', 'api')
        source_id: Optional source identifier (e.g., Odoo invoice ID)
        submitted_by: Optional User ID of the submitter
        request_data: Optional request data sent to FIRS API
        webhook_url: Optional webhook URL for notifications
        
    Returns:
        The original submission response
    """
    if not submission_response.submission_id:
        logger.warning(f"Cannot track submission: Missing submission_id for IRN {irn}")
        return submission_response
    
    # Map FIRS API status to internal status
    status = map_firs_status_to_db_status(submission_response.status)
    
    try:
        # Create submission record
        await create_submission_record(
            db=db,
            submission_id=submission_response.submission_id,
            irn=irn,
            integration_id=integration_id,
            source_type=source_type,
            status=status,
            status_message=submission_response.message,
            request_data=request_data,
            response_data={
                "submission_id": submission_response.submission_id,
                "status": submission_response.status,
                "message": submission_response.message,
                "details": submission_response.details,
                "errors": submission_response.errors
            },
            source_id=source_id,
            submitted_by=submitted_by,
            webhook_enabled=bool(webhook_url),
            webhook_url=webhook_url
        )
        
        logger.info(f"Created submission tracking record for IRN {irn} with submission ID {submission_response.submission_id}")
        
    except Exception as e:
        logger.error(f"Error creating submission tracking record: {str(e)}", exc_info=True)
    
    return submission_response


async def track_status_update(
    db: Session,
    submission_id: str,
    status: str,
    message: Optional[str] = None,
    response_data: Optional[Dict[str, Any]] = None
) -> None:
    """
    Track a status update for an existing submission.
    
    Args:
        db: Database session
        submission_id: Submission ID
        status: Status string from FIRS API
        message: Optional status message
        response_data: Optional response data
    """
    try:
        # Map FIRS API status to internal status
        db_status = map_firs_status_to_db_status(status)
        
        # Update submission status
        await update_submission_status(
            db=db,
            submission_id=submission_id,
            status=db_status,
            message=message,
            response_data=response_data,
            trigger_webhook=True
        )
        
        logger.info(f"Updated submission {submission_id} status to {db_status.value}")
        
    except Exception as e:
        logger.error(f"Error updating submission status: {str(e)}", exc_info=True)


def map_firs_status_to_db_status(firs_status: Optional[str]) -> DbSubmissionStatus:
    """
    Map FIRS API status to database submission status.
    
    Args:
        firs_status: Status string from FIRS API
        
    Returns:
        Corresponding database SubmissionStatus
    """
    if not firs_status:
        return DbSubmissionStatus.PENDING
    
    status_mapping = {
        "pending": DbSubmissionStatus.PENDING,
        "processing": DbSubmissionStatus.PROCESSING,
        "validated": DbSubmissionStatus.VALIDATED,
        "signed": DbSubmissionStatus.SIGNED,
        "accepted": DbSubmissionStatus.ACCEPTED,
        "rejected": DbSubmissionStatus.REJECTED,
        "failed": DbSubmissionStatus.FAILED,
        "error": DbSubmissionStatus.ERROR,
        "cancelled": DbSubmissionStatus.CANCELLED
    }
    
    return status_mapping.get(firs_status.lower(), DbSubmissionStatus.PENDING)


# Patch the FIRS service submit_invoice method to include tracking
original_submit_invoice = firs_service.submit_invoice

async def tracked_submit_invoice(*args, **kwargs):
    """
    Wrapper around the original submit_invoice method that adds tracking.
    """
    # Call the original method
    response = await original_submit_invoice(*args, **kwargs)
    
    # Get tracking information from kwargs
    db = kwargs.get("db")
    irn = kwargs.get("irn")
    integration_id = kwargs.get("integration_id")
    source_type = kwargs.get("source_type", "api")
    source_id = kwargs.get("source_id")
    submitted_by = kwargs.get("submitted_by")
    webhook_url = kwargs.get("webhook_url")
    
    # If we have a database session and an IRN, track the submission
    if db and irn and integration_id:
        await track_invoice_submission(
            db=db,
            submission_response=response,
            irn=irn,
            integration_id=integration_id,
            source_type=source_type,
            source_id=source_id,
            submitted_by=submitted_by,
            request_data=kwargs.get("invoice_data"),
            webhook_url=webhook_url
        )
    
    return response

# Patch the FIRS service check_submission_status method to include tracking
original_check_status = firs_service.check_submission_status

async def tracked_check_status(*args, **kwargs):
    """
    Wrapper around the original check_submission_status method that adds tracking.
    """
    # Call the original method
    response = await original_check_status(*args, **kwargs)
    
    # Get tracking information from kwargs
    db = kwargs.get("db")
    submission_id = kwargs.get("submission_id")
    if not submission_id and len(args) > 0:
        submission_id = args[0]
    
    # If we have a database session and a submission ID, track the status update
    if db and submission_id:
        await track_status_update(
            db=db,
            submission_id=submission_id,
            status=response.status,
            message=response.message,
            response_data={
                "status": response.status,
                "message": response.message,
                "details": response.details,
                "timestamp": response.timestamp
            }
        )
    
    return response


# Apply the patches - this will be executed when the module is imported
firs_service.submit_invoice = tracked_submit_invoice
firs_service.check_submission_status = tracked_check_status