"""
FIRS Core Service with Retry Capability for TaxPoynt eInvoice - Core FIRS Functions.

This module provides Core FIRS functionality for retry mechanisms and failure handling,
serving as the foundation for both System Integrator (SI) and Access Point Provider (APP)
operations with robust retry policies and error management for FIRS e-invoicing.

Core FIRS Responsibilities:
- Base retry mechanisms for FIRS API operations and e-invoicing workflows
- Core error classification and permanent vs retriable error detection
- Foundation failure handling and logging for FIRS compliance operations
- Shared retry policies and backoff strategies for SI and APP operations
- Core status monitoring and submission tracking with retry capabilities
"""

import traceback
from typing import Dict, Any, Optional, Union
from sqlalchemy.orm import Session
from uuid import UUID, uuid4
from datetime import datetime, timedelta
import asyncio

from app.services.firs_core.firs_api_client import firs_service, InvoiceSubmissionResponse
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

# Core FIRS retry configuration
DEFAULT_CORE_MAX_ATTEMPTS = 5
DEFAULT_CORE_BASE_DELAY = 2
DEFAULT_CORE_BACKOFF_FACTOR = 2.0
CORE_FIRS_RETRY_VERSION = "1.0"


class CoreFIRSRetryService:
    """
    Core FIRS service providing base retry functionality for e-invoicing operations.
    
    This service provides Core FIRS functions for retry mechanisms, error handling,
    and failure management that serve as the foundation for both System Integrator (SI)
    and Access Point Provider (APP) operations in Nigerian e-invoicing compliance.
    """
    
    def __init__(self):
        self.retry_statistics = {
            "total_retries": 0,
            "permanent_failures": 0,
            "successful_retries": 0,
            "last_reset": datetime.now()
        }
        self.core_retry_policies = {
            "submission": {
                "max_attempts": DEFAULT_CORE_MAX_ATTEMPTS,
                "base_delay": DEFAULT_CORE_BASE_DELAY,
                "backoff_factor": DEFAULT_CORE_BACKOFF_FACTOR
            },
            "status_check": {
                "max_attempts": 3,
                "base_delay": 1,
                "backoff_factor": 1.5
            }
        }
        
    def get_core_retry_policy(self, operation_type: str = "submission") -> Dict[str, Any]:
        """
        Get core retry policy for FIRS operations - Core FIRS Function.
        
        Provides core retry policies for different types of FIRS operations,
        ensuring consistent retry behavior across SI and APP components.
        
        Args:
            operation_type: Type of operation (submission, status_check, etc.)
            
        Returns:
            Dict containing retry policy configuration
        """
        policy = self.core_retry_policies.get(operation_type, self.core_retry_policies["submission"])
        
        return {
            **policy,
            "firs_core_policy": True,
            "policy_version": CORE_FIRS_RETRY_VERSION,
            "operation_type": operation_type,
            "created_at": datetime.now().isoformat()
        }
    
    def update_retry_statistics(self, operation: str, success: bool = True) -> None:
        """
        Update core retry statistics for FIRS operations - Core FIRS Function.
        
        Maintains core statistics for retry operations across all FIRS components,
        providing insights for monitoring and optimization.
        
        Args:
            operation: Type of operation performed
            success: Whether the retry operation was successful
        """
        if operation == "retry":
            self.retry_statistics["total_retries"] += 1
            if success:
                self.retry_statistics["successful_retries"] += 1
        elif operation == "permanent_failure":
            self.retry_statistics["permanent_failures"] += 1
            
        logger.debug(f"Core FIRS: Updated retry statistics - {operation}: {success}")


# Global core retry service instance
core_retry_service = CoreFIRSRetryService()


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
    Submit an invoice to FIRS with core retry capability - Core FIRS Function.
    
    Provides core retry functionality for FIRS invoice submissions, serving as the
    foundation for both SI and APP operations with automatic retry on failure,
    detailed failure logging, and alerting for critical failures.
    
    Args:
        db: Database session
        invoice_data: Invoice data to submit to FIRS
        submission_record: Submission record to associate with this attempt
        retry_on_failure: Whether to schedule a retry on failure
        max_attempts: Maximum number of retry attempts (default from core policy)
        base_delay: Base delay between retries in seconds (default from core policy)
        backoff_factor: Multiplier for exponential backoff (default from core policy)
        
    Returns:
        Response from FIRS API with core retry metadata
    """
    retry_session_id = str(uuid4())
    start_time = datetime.now()
    
    try:
        # Get core retry policy
        retry_policy = core_retry_service.get_core_retry_policy("submission")
        
        # Set default retry parameters from core policy or settings
        max_attempts = max_attempts or retry_policy["max_attempts"] or retry_settings.MAX_RETRY_ATTEMPTS
        base_delay = base_delay or retry_policy["base_delay"] or retry_settings.BASE_RETRY_DELAY
        backoff_factor = backoff_factor or retry_policy["backoff_factor"] or retry_settings.RETRY_BACKOFF_FACTOR
        
        logger.info(f"Core FIRS: Starting invoice submission with retry capability (Session: {retry_session_id})")
        
        # Call the original submit_invoice method
        response = await firs_service.submit_invoice(invoice_data)
        
        # Enhance response with core retry metadata
        if hasattr(response, 'details') and isinstance(response.details, dict):
            response.details.update({
                "core_retry_session": retry_session_id,
                "retry_policy_applied": retry_policy,
                "firs_core_processed": True
            })
        
        # Check if the submission was successful
        if not response.success and retry_on_failure:
            logger.warning(
                f"Core FIRS: Submission failed for {submission_record.submission_id}: {response.message} (Session: {retry_session_id})"
            )
            
            # Determine if this is a permanent or retriable error using core classification
            if is_permanent_error_core(response):
                # Create a permanent error record but don't schedule retry
                await schedule_submission_retry(
                    db=db,
                    submission_id=submission_record.id,
                    error=PermanentError(
                        f"Core FIRS: Permanent failure - {response.message}",
                        error_type="CoreFIRSRejection",
                        error_details={
                            "firs_message": response.message,
                            "firs_errors": response.errors,
                            "firs_details": response.details,
                            "core_retry_session": retry_session_id,
                            "classification": "permanent_by_core",
                            "firs_core_classified": True
                        },
                        severity=FailureSeverity.HIGH
                    )
                )
                
                core_retry_service.update_retry_statistics("permanent_failure", False)
                
            else:
                # Schedule a retry for retriable errors
                await schedule_submission_retry(
                    db=db,
                    submission_id=submission_record.id,
                    error=RetryableError(
                        f"Core FIRS: Retriable failure - {response.message}",
                        error_type="CoreFIRSSubmissionError",
                        error_details={
                            "firs_message": response.message,
                            "firs_errors": response.errors,
                            "firs_details": response.details,
                            "core_retry_session": retry_session_id,
                            "classification": "retriable_by_core",
                            "firs_core_classified": True
                        }
                    ),
                    max_attempts=max_attempts,
                    base_delay=base_delay,
                    backoff_factor=backoff_factor
                )
                
                core_retry_service.update_retry_statistics("retry", False)
        else:
            # Success case
            core_retry_service.update_retry_statistics("retry", True)
        
        processing_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"Core FIRS: Submission completed in {processing_time:.2f} seconds (Session: {retry_session_id})")
        
        return response
        
    except Exception as e:
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # Log the error with core context
        logger.exception(
            f"Core FIRS: Exception during submission for {submission_record.submission_id}: {str(e)} "
            f"(Session: {retry_session_id}, Processing time: {processing_time:.2f}s)"
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
            
            core_retry_service.update_retry_statistics("retry", False)
        
        # Create a fallback response with core metadata
        return InvoiceSubmissionResponse(
            success=False,
            message=f"Core FIRS exception during submission: {str(e)}",
            errors=[{
                "type": "core_exception", 
                "message": str(e),
                "retry_session": retry_session_id,
                "firs_core_error": True
            }],
            details={
                "core_retry_session": retry_session_id,
                "processing_time": processing_time,
                "firs_core_processed": False
            }
        )


def is_permanent_error(response: InvoiceSubmissionResponse) -> bool:
    """
    Determine if an error response from FIRS should be considered permanent - Core FIRS Function.
    
    Provides core error classification for FIRS responses, determining whether
    errors should be retried or treated as permanent failures.
    
    Args:
        response: Response from FIRS API
        
    Returns:
        True if the error is permanent and should not be retried
    """
    return is_permanent_error_core(response)


def is_permanent_error_core(response: InvoiceSubmissionResponse) -> bool:
    """
    Core implementation for permanent error detection - Core FIRS Function.
    
    Provides enhanced core error classification with FIRS-specific patterns
    and comprehensive error analysis for e-invoicing operations.
    
    Args:
        response: Response from FIRS API
        
    Returns:
        True if the error is permanent and should not be retried
    """
    # Enhanced permanent error keywords for FIRS e-invoicing
    permanent_error_keywords = [
        "invalid",
        "validation",
        "format",
        "schema",
        "required field",
        "not found",
        "already exists",
        "duplicate",
        "unauthorized",
        "forbidden",
        "authentication failed",
        "invalid credentials",
        "malformed",
        "unsupported",
        # FIRS-specific permanent errors
        "irn already used",
        "invoice number exists",
        "taxpayer not found",
        "invalid tin",
        "certificate expired",
        "signature invalid"
    ]
    
    # Check message for permanent error indicators
    if response.message:
        message_lower = response.message.lower()
        for keyword in permanent_error_keywords:
            if keyword in message_lower:
                logger.debug(f"Core FIRS: Classified as permanent error due to keyword '{keyword}' in message")
                return True
    
    # Check error details with enhanced classification
    if response.errors:
        error_types = [error.get("type", "").lower() for error in response.errors if isinstance(error, dict)]
        permanent_types = [
            "validation", "format", "schema", "invalid", "authentication", 
            "authorization", "duplicate", "not_found", "forbidden"
        ]
        
        for error_type in error_types:
            for permanent_type in permanent_types:
                if permanent_type in error_type:
                    logger.debug(f"Core FIRS: Classified as permanent error due to error type '{error_type}'")
                    return True
    
    # Check for HTTP status codes that indicate permanent failures
    if hasattr(response, 'status_code'):
        permanent_status_codes = [400, 401, 403, 404, 409, 422]
        if response.status_code in permanent_status_codes:
            logger.debug(f"Core FIRS: Classified as permanent error due to status code {response.status_code}")
            return True
    
    logger.debug("Core FIRS: Classified as retriable error")
    return False


async def check_submission_status_with_logging(
    submission_id: str,
    log_detailed_status: bool = True
) -> Dict[str, Any]:
    """
    Check submission status with enhanced core logging - Core FIRS Function.
    
    Provides core status checking functionality with enhanced logging and
    monitoring capabilities for FIRS e-invoicing operations.
    
    This function wraps the standard FIRS check_submission_status method
    with detailed logging for better tracking and analysis across SI and APP operations.
    
    Args:
        submission_id: FIRS submission ID
        log_detailed_status: Whether to log detailed status information
        
    Returns:
        Status information from FIRS API with core logging metadata
    """
    status_check_id = str(uuid4())
    start_time = datetime.now()
    
    try:
        logger.debug(f"Core FIRS: Checking submission status for {submission_id} (Check ID: {status_check_id})")
        
        # Call the original method
        status_response = await firs_service.check_submission_status(submission_id)
        
        check_time = (datetime.now() - start_time).total_seconds()
        
        # Enhance status response with core metadata
        if hasattr(status_response, 'details') and isinstance(status_response.details, dict):
            status_response.details.update({
                "core_status_check_id": status_check_id,
                "check_duration": check_time,
                "firs_core_checked": True,
                "core_version": CORE_FIRS_RETRY_VERSION
            })
        
        # Log detailed status information if enabled
        if log_detailed_status and retry_settings.DETAILED_FAILURE_LOGGING:
            if status_response.status.lower() in ("failed", "rejected", "error"):
                logger.warning(
                    f"Core FIRS: Submission {submission_id} failed with status {status_response.status}: "
                    f"{status_response.message} (Check ID: {status_check_id})"
                )
                
                if status_response.details:
                    logger.debug(f"Core FIRS: Failure details for {submission_id}: {status_response.details}")
            else:
                logger.info(
                    f"Core FIRS: Submission {submission_id} status: {status_response.status} "
                    f"(Check time: {check_time:.2f}s, Check ID: {status_check_id})"
                )
        
        return status_response
        
    except Exception as e:
        check_time = (datetime.now() - start_time).total_seconds()
        logger.exception(
            f"Core FIRS: Error checking submission status for {submission_id}: {str(e)} "
            f"(Check time: {check_time:.2f}s, Check ID: {status_check_id})"
        )
        raise


async def get_core_retry_statistics() -> Dict[str, Any]:
    """
    Get core retry statistics for monitoring - Core FIRS Function.
    
    Provides comprehensive statistics about core retry operations
    for monitoring and optimization of FIRS e-invoicing workflows.
    
    Returns:
        Dict containing core retry statistics and metrics
    """
    stats = core_retry_service.retry_statistics.copy()
    
    # Calculate additional metrics
    total_operations = stats["total_retries"] + stats["permanent_failures"]
    success_rate = (stats["successful_retries"] / stats["total_retries"]) * 100 if stats["total_retries"] > 0 else 0
    
    stats.update({
        "total_operations": total_operations,
        "retry_success_rate_percent": round(success_rate, 2),
        "core_version": CORE_FIRS_RETRY_VERSION,
        "uptime_hours": (datetime.now() - stats["last_reset"]).total_seconds() / 3600,
        "firs_core_stats": True,
        "timestamp": datetime.now().isoformat()
    })
    
    return stats


async def reset_core_retry_statistics() -> Dict[str, Any]:
    """
    Reset core retry statistics - Core FIRS Function.
    
    Resets core retry statistics for monitoring cycles,
    useful for periodic reporting and analysis.
    
    Returns:
        Dict containing reset confirmation and previous statistics
    """
    previous_stats = core_retry_service.retry_statistics.copy()
    
    core_retry_service.retry_statistics = {
        "total_retries": 0,
        "permanent_failures": 0,
        "successful_retries": 0,
        "last_reset": datetime.now()
    }
    
    logger.info("Core FIRS: Retry statistics reset")
    
    return {
        "reset_successful": True,
        "previous_statistics": previous_stats,
        "reset_timestamp": datetime.now().isoformat(),
        "firs_core_reset": True
    }
