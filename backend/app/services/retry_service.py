"""
Retry service for failed FIRS invoice submissions.

This service provides:
1. Exponential backoff retry mechanism for failed submissions
2. Detailed failure logging and tracking
3. Alert system for critical failures
"""

import traceback
import asyncio
import json
from typing import Dict, Any, List, Optional, Tuple, Union, Type
from datetime import datetime, timedelta
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.sql import text
from uuid import UUID

from app.models.submission import SubmissionRecord, SubmissionStatus
from app.models.submission_retry import SubmissionRetry, RetryStatus, FailureSeverity
from app.services.firs_service import firs_service, InvoiceSubmissionResponse
from app.core.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class RetryableError(Exception):
    """Base exception for errors that can be retried."""
    def __init__(
        self, 
        message: str, 
        error_type: str = "RetryableError",
        error_details: Optional[Dict[str, Any]] = None,
        severity: FailureSeverity = FailureSeverity.MEDIUM
    ):
        self.message = message
        self.error_type = error_type
        self.error_details = error_details or {}
        self.severity = severity
        super().__init__(message)


class PermanentError(Exception):
    """Base exception for errors that should not be retried."""
    def __init__(
        self, 
        message: str, 
        error_type: str = "PermanentError",
        error_details: Optional[Dict[str, Any]] = None,
        severity: FailureSeverity = FailureSeverity.HIGH
    ):
        self.message = message
        self.error_type = error_type
        self.error_details = error_details or {}
        self.severity = severity
        super().__init__(message)


async def schedule_submission_retry(
    db: Session,
    submission_id: UUID,
    error: Exception,
    max_attempts: int = 5,
    base_delay: int = 60,
    backoff_factor: float = 2.0,
    attempt_now: bool = False
) -> SubmissionRetry:
    """
    Schedule a retry for a failed submission.
    
    This function creates a retry record with exponential backoff timing
    and schedules a background task to attempt the retry when appropriate.
    
    Args:
        db: Database session
        submission_id: UUID of the submission to retry
        error: Exception that caused the failure
        max_attempts: Maximum number of retry attempts
        base_delay: Base delay in seconds
        backoff_factor: Multiplier for exponential backoff
        attempt_now: Whether to attempt the retry immediately
        
    Returns:
        Created SubmissionRetry record
    """
    # Find the submission record
    submission = db.query(SubmissionRecord).filter(SubmissionRecord.id == submission_id).first()
    if not submission:
        logger.error(f"Cannot schedule retry: Submission {submission_id} not found")
        raise ValueError(f"Submission {submission_id} not found")
    
    # Determine error type and severity
    error_type = getattr(error, "error_type", error.__class__.__name__)
    error_message = str(error)
    error_details = getattr(error, "error_details", {"exception_type": error.__class__.__name__})
    severity = getattr(error, "severity", FailureSeverity.MEDIUM)
    stack_trace = traceback.format_exc()
    
    # Check if this is a permanent error
    if isinstance(error, PermanentError):
        logger.error(
            f"Permanent error for submission {submission.submission_id}: "
            f"{error_type} - {error_message}"
        )
        # Create a retry record but mark it as cancelled
        retry = SubmissionRetry(
            submission_id=submission.id,
            attempt_number=1,
            max_attempts=max_attempts,
            status=RetryStatus.CANCELLED,
            error_type=error_type,
            error_message=error_message,
            error_details=error_details,
            stack_trace=stack_trace,
            severity=severity
        )
        
        # Send alert for permanent errors
        await send_alert(
            db,
            retry,
            error_message=f"Permanent failure for submission {submission.submission_id}: {error_message}",
            error_details=error_details
        )
        
        db.add(retry)
        db.commit()
        db.refresh(retry)
        return retry
    
    # Create or update retry record
    existing_retry = db.query(SubmissionRetry).filter(
        SubmissionRetry.submission_id == submission.id,
        SubmissionRetry.status.in_([RetryStatus.PENDING, RetryStatus.FAILED])
    ).order_by(SubmissionRetry.created_at.desc()).first()
    
    if existing_retry and existing_retry.attempt_number < existing_retry.max_attempts:
        # Update existing retry record
        retry = existing_retry
        retry.increment_attempt()
        retry.error_type = error_type
        retry.error_message = error_message
        retry.error_details = error_details
        retry.stack_trace = stack_trace
        retry.severity = severity
    else:
        # Create new retry record
        retry = SubmissionRetry(
            submission_id=submission.id,
            attempt_number=1,
            max_attempts=max_attempts,
            base_delay=base_delay,
            backoff_factor=backoff_factor,
            error_type=error_type,
            error_message=error_message,
            error_details=error_details,
            stack_trace=stack_trace,
            severity=severity
        )
        
        # Calculate next attempt time
        retry.next_attempt_at = retry.calculate_next_attempt()
    
    # Send alert for high/critical severity
    if severity in (FailureSeverity.HIGH, FailureSeverity.CRITICAL):
        await send_alert(
            db,
            retry,
            error_message=f"Submission {submission.submission_id} failed: {error_message}",
            error_details=error_details
        )
    
    db.add(retry)
    db.commit()
    db.refresh(retry)
    
    # Log the retry scheduling
    logger.info(
        f"Scheduled retry {retry.attempt_number}/{retry.max_attempts} for "
        f"submission {submission.submission_id} at {retry.next_attempt_at}"
    )
    
    # If attempt_now is True, process the retry immediately in the background
    if attempt_now:
        asyncio.create_task(process_submission_retry(db, retry.id))
    
    return retry


async def process_submission_retry(db: Session, retry_id: UUID) -> bool:
    """
    Process a scheduled submission retry.
    
    This function attempts to resubmit a failed submission according to the
    retry record's parameters.
    
    Args:
        db: Database session
        retry_id: UUID of the retry record to process
        
    Returns:
        True if the retry was successful, False otherwise
    """
    # Get the retry record
    retry = db.query(SubmissionRetry).filter(SubmissionRetry.id == retry_id).first()
    if not retry:
        logger.error(f"Cannot process retry: Retry record {retry_id} not found")
        return False
    
    # Get the submission record
    submission = retry.submission
    if not submission:
        logger.error(f"Cannot process retry: Submission for retry {retry_id} not found")
        retry.status = RetryStatus.CANCELLED
        db.add(retry)
        db.commit()
        return False
    
    logger.info(f"Processing retry attempt {retry.attempt_number}/{retry.max_attempts} for submission {submission.submission_id}")
    
    # Update retry status to in progress
    retry.status = RetryStatus.IN_PROGRESS
    retry.last_attempt_at = datetime.utcnow()
    db.add(retry)
    db.commit()
    
    try:
        # Attempt to resubmit the invoice
        response = await resubmit_invoice(db, submission, retry)
        
        # Handle successful resubmission
        retry.set_success()
        
        # Update submission record
        submission.status = SubmissionStatus.PENDING
        submission.last_updated = datetime.utcnow()
        submission.status_message = f"Resubmitted after {retry.attempt_number} attempts"
        
        db.add(retry)
        db.add(submission)
        db.commit()
        
        logger.info(f"Retry attempt {retry.attempt_number} succeeded for submission {submission.submission_id}")
        return True
        
    except RetryableError as e:
        # Handle retriable error
        logger.warning(
            f"Retry attempt {retry.attempt_number} failed for submission "
            f"{submission.submission_id} with retriable error: {str(e)}"
        )
        
        # Record failure details
        retry.set_failure(
            error_type=e.error_type,
            error_message=str(e),
            error_details=e.error_details,
            stack_trace=traceback.format_exc(),
            severity=e.severity
        )
        
        # Schedule next attempt if attempts remain
        has_more_attempts = retry.increment_attempt()
        
        db.add(retry)
        db.commit()
        
        # Send alert for high severity errors
        if e.severity in (FailureSeverity.HIGH, FailureSeverity.CRITICAL):
            await send_alert(
                db,
                retry,
                error_message=f"Retry {retry.attempt_number-1}/{retry.max_attempts} failed: {str(e)}",
                error_details=e.error_details
            )
        
        return False
        
    except PermanentError as e:
        # Handle permanent error
        logger.error(
            f"Retry attempt {retry.attempt_number} failed for submission "
            f"{submission.submission_id} with permanent error: {str(e)}"
        )
        
        # Record failure details
        retry.set_failure(
            error_type=e.error_type,
            error_message=str(e),
            error_details=e.error_details,
            stack_trace=traceback.format_exc(),
            severity=e.severity
        )
        
        # Mark as max retries exceeded to prevent further attempts
        retry.status = RetryStatus.MAX_RETRIES_EXCEEDED
        retry.next_attempt_at = None
        
        db.add(retry)
        db.commit()
        
        # Send alert for permanent errors
        await send_alert(
            db,
            retry,
            error_message=f"Permanent failure on retry {retry.attempt_number}/{retry.max_attempts}: {str(e)}",
            error_details=e.error_details
        )
        
        return False
        
    except Exception as e:
        # Handle unexpected errors
        logger.exception(
            f"Unexpected error during retry attempt {retry.attempt_number} "
            f"for submission {submission.submission_id}: {str(e)}"
        )
        
        # Record failure details
        retry.set_failure(
            error_type=e.__class__.__name__,
            error_message=str(e),
            error_details={"exception_type": e.__class__.__name__},
            stack_trace=traceback.format_exc(),
            severity=FailureSeverity.HIGH
        )
        
        # Schedule next attempt if attempts remain
        has_more_attempts = retry.increment_attempt()
        
        db.add(retry)
        db.commit()
        
        # Send alert for unexpected errors
        await send_alert(
            db,
            retry,
            error_message=f"Unexpected error during retry {retry.attempt_number-1}/{retry.max_attempts}: {str(e)}",
            error_details={"exception_type": e.__class__.__name__}
        )
        
        return False


async def resubmit_invoice(
    db: Session,
    submission: SubmissionRecord,
    retry: SubmissionRetry
) -> InvoiceSubmissionResponse:
    """
    Resubmit a failed invoice to FIRS.
    
    This function resubmits the invoice data from the original submission
    to the FIRS API.
    
    Args:
        db: Database session
        submission: Submission record to retry
        retry: Retry record tracking this attempt
        
    Returns:
        Response from FIRS API
    """
    # Get the original request data
    request_data = submission.request_data
    if not request_data:
        raise PermanentError(
            "Cannot resubmit: Original request data not found",
            error_type="MissingRequestData",
            severity=FailureSeverity.HIGH
        )
    
    try:
        # Get the IRN record
        irn_record = submission.irn_record
        if not irn_record:
            raise PermanentError(
                "Cannot resubmit: IRN record not found",
                error_type="MissingIRNRecord",
                severity=FailureSeverity.HIGH
            )
        
        # Attempt to resubmit
        response = await firs_service.submit_invoice(
            invoice_data=request_data,
            # Include tracking info for the submission_service
            db=db,
            irn=submission.irn,
            integration_id=submission.integration_id,
            source_type=submission.source_type,
            source_id=submission.source_id,
            submitted_by=submission.submitted_by,
            webhook_url=submission.webhook_url
        )
        
        if not response.success:
            # Determine if this is a permanent or retriable error
            if is_permanent_error(response):
                raise PermanentError(
                    f"FIRS rejected submission: {response.message}",
                    error_type="FIRSRejection",
                    error_details={
                        "firs_message": response.message,
                        "firs_errors": response.errors,
                        "firs_details": response.details
                    },
                    severity=FailureSeverity.HIGH
                )
            else:
                raise RetryableError(
                    f"FIRS submission failed: {response.message}",
                    error_type="FIRSSubmissionError",
                    error_details={
                        "firs_message": response.message,
                        "firs_errors": response.errors,
                        "firs_details": response.details
                    }
                )
        
        return response
        
    except HTTPException as e:
        # Determine if this is a permanent or retriable HTTP error
        if e.status_code in (400, 422):
            raise PermanentError(
                f"Bad request: {e.detail}",
                error_type="BadRequest",
                error_details={"status_code": e.status_code, "detail": e.detail},
                severity=FailureSeverity.HIGH
            )
        elif e.status_code in (401, 403):
            raise PermanentError(
                f"Authentication error: {e.detail}",
                error_type="AuthenticationError",
                error_details={"status_code": e.status_code, "detail": e.detail},
                severity=FailureSeverity.CRITICAL
            )
        elif e.status_code == 429:
            raise RetryableError(
                f"Rate limited: {e.detail}",
                error_type="RateLimited",
                error_details={"status_code": e.status_code, "detail": e.detail},
                severity=FailureSeverity.MEDIUM
            )
        elif e.status_code >= 500:
            raise RetryableError(
                f"FIRS API server error: {e.detail}",
                error_type="ServerError",
                error_details={"status_code": e.status_code, "detail": e.detail},
                severity=FailureSeverity.HIGH
            )
        else:
            raise RetryableError(
                f"HTTP error: {e.detail}",
                error_type="HTTPError",
                error_details={"status_code": e.status_code, "detail": e.detail}
            )


def is_permanent_error(response: InvoiceSubmissionResponse) -> bool:
    """
    Determine if an error response from FIRS should be considered permanent.
    
    Args:
        response: Response from FIRS API
        
    Returns:
        True if the error is permanent and should not be retried
    """
    # Check for validation errors or other permanent error types
    permanent_error_keywords = [
        "invalid",
        "validation",
        "format",
        "schema",
        "required field",
        "not found",
        "already exists",
        "duplicate"
    ]
    
    if response.message:
        message_lower = response.message.lower()
        for keyword in permanent_error_keywords:
            if keyword in message_lower:
                return True
    
    # Check error details
    if response.errors:
        error_types = [error.get("type", "").lower() for error in response.errors if isinstance(error, dict)]
        permanent_types = ["validation", "format", "schema", "invalid"]
        
        for error_type in error_types:
            for permanent_type in permanent_types:
                if permanent_type in error_type:
                    return True
    
    return False


async def process_pending_retries(db: Session) -> int:
    """
    Process all pending submission retries that are due.
    
    This function should be called periodically by a background task to
    process scheduled retries.
    
    Args:
        db: Database session
        
    Returns:
        Number of retries processed
    """
    try:
        # Check if table exists by making a low-impact query
        try:
            # Just check if the table exists without doing a full query
            db.execute(text("SELECT 1 FROM submission_retries LIMIT 1"))
        except Exception as table_error:
            # If table doesn't exist, log and return early
            if "relation \"submission_retries\" does not exist" in str(table_error):
                logger.warning("submission_retries table does not exist yet. Skipping retry processing.")
                return 0
            # For other errors, re-raise
            raise
            
        # Find pending retries that are due
        now = datetime.utcnow()
        pending_retries = db.query(SubmissionRetry).filter(
            SubmissionRetry.status == RetryStatus.PENDING,
            SubmissionRetry.next_attempt_at <= now
        ).all()
        
        if not pending_retries:
            return 0
        
        logger.info(f"Processing {len(pending_retries)} pending submission retries")
        
        # Process each retry
        processed_count = 0
        for retry in pending_retries:
            try:
                # Process the retry in the background
                asyncio.create_task(process_submission_retry(db, retry.id))
                processed_count += 1
            except Exception as e:
                logger.exception(f"Error scheduling retry {retry.id}: {str(e)}")
        
        return processed_count
    except Exception as e:
        logger.exception(f"Error in process_pending_retries: {str(e)}")
        return 0


async def send_alert(
    db: Session,
    retry: SubmissionRetry,
    error_message: str,
    error_details: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Send an alert for a submission failure.
    
    Args:
        db: Database session
        retry: Retry record associated with the failure
        error_message: Error message to include in the alert
        error_details: Additional error details
        
    Returns:
        True if the alert was sent successfully
    """
    # Skip if alerts are disabled
    if not settings.ENABLE_FAILURE_ALERTS:
        return False
    
    # Skip if an alert was already sent for this retry
    if retry.alert_sent:
        return False
    
    # Prepare alert data
    submission = retry.submission
    alert_data = {
        "event": "submission_failure",
        "severity": retry.severity,
        "submission_id": submission.submission_id if submission else "unknown",
        "irn": submission.irn if submission else "unknown",
        "error_message": error_message,
        "error_type": retry.error_type,
        "attempt": f"{retry.attempt_number}/{retry.max_attempts}",
        "timestamp": datetime.utcnow().isoformat(),
        "details": error_details or {}
    }
    
    try:
        # Log the alert
        if retry.severity == FailureSeverity.CRITICAL:
            logger.critical(f"CRITICAL ALERT: {error_message}")
        elif retry.severity == FailureSeverity.HIGH:
            logger.error(f"HIGH SEVERITY ALERT: {error_message}")
        else:
            logger.warning(f"ALERT: {error_message}")
        
        # Send alert via configured notification channels
        await send_notification_alert(alert_data)
        
        # Mark alert as sent
        retry.alert_sent = True
        db.add(retry)
        db.commit()
        
        return True
        
    except Exception as e:
        logger.exception(f"Error sending alert: {str(e)}")
        return False


async def send_notification_alert(alert_data: Dict[str, Any]) -> None:
    """
    Send an alert via configured notification channels.
    
    This function implements the actual alert sending logic for different channels
    like email, SMS, Slack, etc.
    
    Args:
        alert_data: Alert data to send
    """
    # Send email alerts if configured
    if settings.EMAIL_ALERTS_ENABLED:
        await send_email_alert(alert_data)
    
    # Send Slack alerts if configured
    if settings.SLACK_ALERTS_ENABLED:
        await send_slack_alert(alert_data)
    
    # Future: Add more notification channels as needed


async def send_email_alert(alert_data: Dict[str, Any]) -> None:
    """
    Send an alert via email.
    
    Args:
        alert_data: Alert data to send
    """
    # This is a placeholder for the email alert implementation
    # In a production system, this would integrate with an email service
    logger.info(f"EMAIL ALERT would be sent: {json.dumps(alert_data, indent=2)}")
    
    # Example implementation with FastAPI mail:
    # from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
    # 
    # message = MessageSchema(
    #     subject=f"ALERT: Submission Failure - {alert_data['severity']}",
    #     recipients=settings.ALERT_EMAIL_RECIPIENTS,
    #     body=format_email_alert(alert_data),
    #     subtype="html"
    # )
    # 
    # mail = FastMail(ConnectionConfig(**settings.EMAIL_CONFIG))
    # await mail.send_message(message)


async def send_slack_alert(alert_data: Dict[str, Any]) -> None:
    """
    Send an alert via Slack.
    
    Args:
        alert_data: Alert data to send
    """
    # This is a placeholder for the Slack alert implementation
    # In a production system, this would integrate with Slack's API
    logger.info(f"SLACK ALERT would be sent: {json.dumps(alert_data, indent=2)}")
    
    # Example implementation with httpx:
    # import httpx
    # 
    # webhook_url = settings.SLACK_WEBHOOK_URL
    # payload = format_slack_alert(alert_data)
    # 
    # async with httpx.AsyncClient() as client:
    #     response = await client.post(webhook_url, json=payload)
    #     if response.status_code != 200:
    #         logger.error(f"Failed to send Slack alert: {response.text}")


def format_email_alert(alert_data: Dict[str, Any]) -> str:
    """
    Format alert data as an HTML email.
    
    Args:
        alert_data: Alert data to format
        
    Returns:
        Formatted HTML email content
    """
    # Simple HTML template for email alerts
    return f"""
    <html>
        <body>
            <h2>TaxPoynt eInvoice - Submission Failure Alert</h2>
            <p><strong>Severity:</strong> {alert_data['severity']}</p>
            <p><strong>Submission ID:</strong> {alert_data['submission_id']}</p>
            <p><strong>IRN:</strong> {alert_data['irn']}</p>
            <p><strong>Error:</strong> {alert_data['error_message']}</p>
            <p><strong>Type:</strong> {alert_data['error_type']}</p>
            <p><strong>Attempt:</strong> {alert_data['attempt']}</p>
            <p><strong>Time:</strong> {alert_data['timestamp']}</p>
            <h3>Details:</h3>
            <pre>{json.dumps(alert_data['details'], indent=2)}</pre>
        </body>
    </html>
    """


def format_slack_alert(alert_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format alert data for Slack API.
    
    Args:
        alert_data: Alert data to format
        
    Returns:
        Formatted Slack API payload
    """
    # Color-code by severity
    color_map = {
        FailureSeverity.LOW: "#36a64f",      # green
        FailureSeverity.MEDIUM: "#ECB22E",   # yellow
        FailureSeverity.HIGH: "#E01E5A",     # red
        FailureSeverity.CRITICAL: "#8E0000"  # dark red
    }
    color = color_map.get(alert_data['severity'], "#000000")
    
    # Format as Slack attachment
    return {
        "text": f"*TaxPoynt eInvoice - Submission Failure Alert*",
        "attachments": [
            {
                "color": color,
                "fields": [
                    {"title": "Severity", "value": alert_data['severity'], "short": True},
                    {"title": "Submission ID", "value": alert_data['submission_id'], "short": True},
                    {"title": "IRN", "value": alert_data['irn'], "short": True},
                    {"title": "Attempt", "value": alert_data['attempt'], "short": True},
                    {"title": "Error", "value": alert_data['error_message'], "short": False},
                    {"title": "Type", "value": alert_data['error_type'], "short": True},
                    {"title": "Time", "value": alert_data['timestamp'], "short": True}
                ],
                "footer": "TaxPoynt eInvoice System"
            }
        ]
    }
