"""
FIRS service with retry capability.

This module extends the core FIRS service with retry capabilities,
integrating the exponential backoff retry mechanism and failure alerting.
"""

import traceback
from typing import Dict, Any, Optional, Union
from sqlalchemy.orm import Session
from uuid import UUID

from app.services.firs_service import firs_service, InvoiceSubmissionResponse
from app.services.retry_service import (
    schedule_submission_retry, 
    RetryableError, 
    PermanentError,
    FailureSeverity
)
from app.models.submission import SubmissionRecord
from app.core.config_retry import retry_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


async def submit_invoice_with_retry(
    db: Session,
    invoice_data: Dict[str, Any],
    submission_record: SubmissionRecord,
    retry_on_failure: bool = True,
    max_attempts: Optional[int] = None,
    base_delay: Optional[int] = None,
    backoff_factor: Optional[float] = None
) -> InvoiceSubmissionResponse:
    """
    Submit an invoice to FIRS with automatic retry on failure.
    
    This function wraps the standard FIRS submit_invoice method with retry
    capabilities, detailed failure logging, and alerting for critical failures.
    
    Args:
        db: Database session
        invoice_data: Invoice data to submit
        submission_record: Submission record to associate with this attempt
        retry_on_failure: Whether to schedule a retry on failure
        max_attempts: Maximum number of retry attempts (default from settings)
        base_delay: Base delay between retries in seconds (default from settings)
        backoff_factor: Multiplier for exponential backoff (default from settings)
        
    Returns:
        Response from FIRS API
    """
    try:
        # Set default retry parameters from settings
        max_attempts = max_attempts or retry_settings.MAX_RETRY_ATTEMPTS
        base_delay = base_delay or retry_settings.BASE_RETRY_DELAY
        backoff_factor = backoff_factor or retry_settings.RETRY_BACKOFF_FACTOR
        
        # Call the original submit_invoice method
        response = await firs_service.submit_invoice(invoice_data)
        
        # Check if the submission was successful
        if not response.success and retry_on_failure:
            logger.warning(
                f"FIRS submission failed for {submission_record.submission_id}: {response.message}"
            )
            
            # Determine if this is a permanent or retriable error
            if is_permanent_error(response):
                # Create a permanent error record but don't schedule retry
                await schedule_submission_retry(
                    db=db,
                    submission_id=submission_record.id,
                    error=PermanentError(
                        f"FIRS rejected submission: {response.message}",
                        error_type="FIRSRejection",
                        error_details={
                            "firs_message": response.message,
                            "firs_errors": response.errors,
                            "firs_details": response.details
                        },
                        severity=FailureSeverity.HIGH
                    )
                )
            else:
                # Schedule a retry for retriable errors
                await schedule_submission_retry(
                    db=db,
                    submission_id=submission_record.id,
                    error=RetryableError(
                        f"FIRS submission failed: {response.message}",
                        error_type="FIRSSubmissionError",
                        error_details={
                            "firs_message": response.message,
                            "firs_errors": response.errors,
                            "firs_details": response.details
                        }
                    ),
                    max_attempts=max_attempts,
                    base_delay=base_delay,
                    backoff_factor=backoff_factor
                )
        
        return response
        
    except Exception as e:
        # Log the error
        logger.exception(
            f"Exception during FIRS submission for {submission_record.submission_id}: {str(e)}"
        )
        
        # Schedule a retry if appropriate
        if retry_on_failure:
            await schedule_submission_retry(
                db=db,
                submission_id=submission_record.id,
                error=e,
                max_attempts=max_attempts,
                base_delay=base_delay,
                backoff_factor=backoff_factor
            )
        
        # Create a fallback response
        return InvoiceSubmissionResponse(
            success=False,
            message=f"Exception during submission: {str(e)}",
            errors=[{"type": "exception", "message": str(e)}]
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


# Create a patched version of the check_submission_status method with failure logging
async def check_submission_status_with_logging(
    submission_id: str,
    log_detailed_status: bool = True
) -> Dict[str, Any]:
    """
    Check submission status with enhanced logging.
    
    This function wraps the standard FIRS check_submission_status method
    with detailed logging for better tracking and analysis.
    
    Args:
        submission_id: FIRS submission ID
        log_detailed_status: Whether to log detailed status information
        
    Returns:
        Status information from FIRS API
    """
    try:
        # Call the original method
        status_response = await firs_service.check_submission_status(submission_id)
        
        # Log detailed status information if enabled
        if log_detailed_status and retry_settings.DETAILED_FAILURE_LOGGING:
            if status_response.status.lower() in ("failed", "rejected", "error"):
                logger.warning(
                    f"FIRS submission {submission_id} failed with status {status_response.status}: "
                    f"{status_response.message}"
                )
                
                if status_response.details:
                    logger.debug(f"Failure details for {submission_id}: {status_response.details}")
        
        return status_response
        
    except Exception as e:
        logger.exception(f"Error checking submission status for {submission_id}: {str(e)}")
        raise
