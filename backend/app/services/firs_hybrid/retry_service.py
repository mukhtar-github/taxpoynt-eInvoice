"""
FIRS Hybrid Retry Service for TaxPoynt eInvoice - Hybrid SI+APP Functions.

This module provides Hybrid FIRS functionality that combines System Integrator (SI)
and Access Point Provider (APP) operations for comprehensive retry mechanisms,
failure handling, and cross-role error management in FIRS e-invoicing workflows.

Hybrid FIRS Responsibilities:
- Cross-role retry mechanisms for both SI invoice processing and APP transmission failures
- Unified failure classification and handling for SI validation and APP submission errors
- Hybrid alert systems covering both SI integration failures and APP transmission issues
- Shared retry orchestration for end-to-end FIRS workflow resilience
- Cross-functional error reporting and recovery coordination between SI and APP operations
"""

import traceback
import asyncio
import json
from typing import Dict, Any, List, Optional, Tuple, Union, Type
from datetime import datetime, timedelta
from uuid import UUID, uuid4
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.sql import text
from sqlalchemy import inspect

from app.models.submission import SubmissionRecord, SubmissionStatus
from app.models.submission_retry import SubmissionRetry, RetryStatus, FailureSeverity
from app.services.firs_core.firs_api_client import firs_service, InvoiceSubmissionResponse
from app.core.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Hybrid FIRS retry configuration
HYBRID_RETRY_SERVICE_VERSION = "1.0"
DEFAULT_SI_MAX_ATTEMPTS = 5
DEFAULT_APP_MAX_ATTEMPTS = 3
DEFAULT_HYBRID_MAX_ATTEMPTS = 7
HYBRID_ALERT_ESCALATION_THRESHOLD = 3


class HybridRetryableError(Exception):
    """Enhanced exception for errors that can be retried across SI and APP operations."""
    def __init__(
        self, 
        message: str, 
        error_type: str = "HybridRetryableError",
        error_details: Optional[Dict[str, Any]] = None,
        severity: FailureSeverity = FailureSeverity.MEDIUM,
        si_context: Optional[Dict[str, Any]] = None,
        app_context: Optional[Dict[str, Any]] = None,
        hybrid_classification: str = "cross_functional"
    ):
        self.message = message
        self.error_type = error_type
        self.error_details = error_details or {}
        self.severity = severity
        self.si_context = si_context or {}
        self.app_context = app_context or {}
        self.hybrid_classification = hybrid_classification
        self.error_details.update({
            "hybrid_error": True,
            "si_context": self.si_context,
            "app_context": self.app_context,
            "classification": hybrid_classification,
            "hybrid_version": HYBRID_RETRY_SERVICE_VERSION
        })
        super().__init__(message)


class HybridPermanentError(Exception):
    """Enhanced exception for errors that should not be retried across SI and APP operations."""
    def __init__(
        self, 
        message: str, 
        error_type: str = "HybridPermanentError",
        error_details: Optional[Dict[str, Any]] = None,
        severity: FailureSeverity = FailureSeverity.HIGH,
        si_context: Optional[Dict[str, Any]] = None,
        app_context: Optional[Dict[str, Any]] = None,
        hybrid_classification: str = "permanent_cross_functional"
    ):
        self.message = message
        self.error_type = error_type
        self.error_details = error_details or {}
        self.severity = severity
        self.si_context = si_context or {}
        self.app_context = app_context or {}
        self.hybrid_classification = hybrid_classification
        self.error_details.update({
            "hybrid_error": True,
            "si_context": self.si_context,
            "app_context": self.app_context,
            "classification": hybrid_classification,
            "hybrid_version": HYBRID_RETRY_SERVICE_VERSION,
            "permanent_failure": True
        })
        super().__init__(message)


class HybridFIRSRetryOrchestrator:
    """
    Hybrid FIRS retry orchestrator for coordinating cross-role retry operations.
    
    This class provides Hybrid FIRS functions for retry orchestration, error
    classification, and failure management that coordinate between System Integrator (SI)
    and Access Point Provider (APP) operations for comprehensive FIRS workflow resilience.
    """
    
    def __init__(self):
        self.retry_statistics = {
            "total_retries": 0,
            "si_retries": 0,
            "app_retries": 0,
            "hybrid_retries": 0,
            "successful_recoveries": 0,
            "permanent_failures": 0,
            "escalated_alerts": 0,
            "last_reset": datetime.now()
        }
        self.cross_role_error_patterns = {}
        self.hybrid_retry_policies = {
            "si_focused": {"max_attempts": DEFAULT_SI_MAX_ATTEMPTS, "base_delay": 30, "backoff_factor": 1.5},
            "app_focused": {"max_attempts": DEFAULT_APP_MAX_ATTEMPTS, "base_delay": 60, "backoff_factor": 2.0},
            "hybrid_workflow": {"max_attempts": DEFAULT_HYBRID_MAX_ATTEMPTS, "base_delay": 45, "backoff_factor": 1.8}
        }
        
        logger.info(f"Hybrid FIRS Retry Orchestrator initialized (Version: {HYBRID_RETRY_SERVICE_VERSION})")
    
    def classify_error_role_impact(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Classify error impact across SI and APP roles - Hybrid FIRS Function.
        
        Provides hybrid error classification to determine which FIRS roles
        are affected and the appropriate retry strategy.
        
        Args:
            error: Exception to classify
            context: Context information about the error
            
        Returns:
            Dict containing role impact classification
        """
        classification = {
            "affects_si": False,
            "affects_app": False,
            "hybrid_impact": False,
            "primary_role": "unknown",
            "retry_strategy": "hybrid_workflow",
            "escalation_required": False,
            "cross_role_coordination": False
        }
        
        try:
            error_message = str(error).lower()
            error_type = getattr(error, "error_type", error.__class__.__name__).lower()
            
            # SI-focused error patterns
            si_patterns = [
                "validation", "transformation", "ubl", "erp", "odoo", "integration",
                "certificate", "irn generation", "invoice processing", "data extraction"
            ]
            
            # APP-focused error patterns
            app_patterns = [
                "transmission", "submission", "signing", "encryption", "webhook",
                "api endpoint", "network", "timeout", "rate limit", "authentication"
            ]
            
            # Check for SI impact
            for pattern in si_patterns:
                if pattern in error_message or pattern in error_type:
                    classification["affects_si"] = True
                    break
            
            # Check for APP impact
            for pattern in app_patterns:
                if pattern in error_message or pattern in error_type:
                    classification["affects_app"] = True
                    break
            
            # Determine hybrid impact and primary role
            if classification["affects_si"] and classification["affects_app"]:
                classification["hybrid_impact"] = True
                classification["primary_role"] = "hybrid"
                classification["retry_strategy"] = "hybrid_workflow"
                classification["cross_role_coordination"] = True
            elif classification["affects_si"]:
                classification["primary_role"] = "si"
                classification["retry_strategy"] = "si_focused"
            elif classification["affects_app"]:
                classification["primary_role"] = "app"
                classification["retry_strategy"] = "app_focused"
            else:
                # Unknown error - treat as hybrid for safety
                classification["hybrid_impact"] = True
                classification["primary_role"] = "hybrid"
                classification["retry_strategy"] = "hybrid_workflow"
            
            # Check for escalation requirements
            if (
                getattr(error, "severity", FailureSeverity.MEDIUM) in [FailureSeverity.HIGH, FailureSeverity.CRITICAL] or
                classification["hybrid_impact"] or
                "firs" in error_message
            ):
                classification["escalation_required"] = True
            
            # Track cross-role error patterns
            pattern_key = f"{classification['primary_role']}_{error_type}"
            self.cross_role_error_patterns[pattern_key] = self.cross_role_error_patterns.get(pattern_key, 0) + 1
            
            logger.debug(f"Hybrid FIRS: Classified error as {classification['primary_role']} role impact with {classification['retry_strategy']} strategy")
            return classification
            
        except Exception as e:
            logger.error(f"Hybrid FIRS: Error during role impact classification: {str(e)}")
            # Default to hybrid approach for safety
            return {
                **classification,
                "hybrid_impact": True,
                "primary_role": "hybrid",
                "retry_strategy": "hybrid_workflow",
                "escalation_required": True,
                "classification_error": str(e)
            }
    
    def get_hybrid_retry_policy(self, strategy: str) -> Dict[str, Any]:
        """
        Get hybrid retry policy for cross-role operations - Hybrid FIRS Function.
        
        Provides hybrid retry policies that coordinate between SI and APP
        operations for comprehensive FIRS workflow resilience.
        
        Args:
            strategy: Retry strategy (si_focused, app_focused, hybrid_workflow)
            
        Returns:
            Dict containing hybrid retry policy configuration
        """
        policy = self.hybrid_retry_policies.get(strategy, self.hybrid_retry_policies["hybrid_workflow"])
        
        return {
            **policy,
            "hybrid_policy": True,
            "strategy": strategy,
            "policy_version": HYBRID_RETRY_SERVICE_VERSION,
            "supports_cross_role": True,
            "escalation_threshold": HYBRID_ALERT_ESCALATION_THRESHOLD,
            "created_at": datetime.now().isoformat()
        }
    
    def update_retry_statistics(self, operation: str, role: str, success: bool = True) -> None:
        """
        Update hybrid retry statistics - Hybrid FIRS Function.
        
        Maintains comprehensive statistics for retry operations across
        SI, APP, and hybrid workflows.
        
        Args:
            operation: Type of operation performed
            role: Role context (si, app, hybrid)
            success: Whether the retry operation was successful
        """
        self.retry_statistics["total_retries"] += 1
        
        if role == "si":
            self.retry_statistics["si_retries"] += 1
        elif role == "app":
            self.retry_statistics["app_retries"] += 1
        elif role == "hybrid":
            self.retry_statistics["hybrid_retries"] += 1
        
        if success:
            self.retry_statistics["successful_recoveries"] += 1
        else:
            self.retry_statistics["permanent_failures"] += 1
        
        logger.debug(f"Hybrid FIRS: Updated retry statistics - {role} {operation}: {success}")


# Global hybrid retry orchestrator instance
hybrid_retry_orchestrator = HybridFIRSRetryOrchestrator()


# Legacy compatibility classes
class RetryableError(HybridRetryableError):
    """Legacy compatibility for RetryableError - now enhanced with hybrid capabilities."""
    pass


class PermanentError(HybridPermanentError):
    """Legacy compatibility for PermanentError - now enhanced with hybrid capabilities."""
    pass


async def schedule_submission_retry(
    db: Session,
    submission_id: UUID,
    error: Exception,
    max_attempts: int = None,
    base_delay: int = None,
    backoff_factor: float = None,
    attempt_now: bool = False
) -> SubmissionRetry:
    """
    Schedule a retry for a failed submission with Hybrid FIRS orchestration - Hybrid FIRS Function.
    
    Provides hybrid retry scheduling that coordinates between SI and APP operations,
    with enhanced error classification and cross-role failure management.
    
    This function creates a retry record with exponential backoff timing
    and schedules a background task to attempt the retry when appropriate.
    
    Args:
        db: Database session
        submission_id: UUID of the submission to retry
        error: Exception that caused the failure
        max_attempts: Maximum number of retry attempts (determined by role if not specified)
        base_delay: Base delay in seconds (determined by role if not specified)
        backoff_factor: Multiplier for exponential backoff (determined by role if not specified)
        attempt_now: Whether to attempt the retry immediately
        
    Returns:
        Created SubmissionRetry record with hybrid metadata
    """
    retry_session_id = str(uuid4())
    start_time = datetime.now()
    
    # Check if submission_retries table exists
    inspector = inspect(db.bind)
    tables = inspector.get_table_names()
    
    if 'submission_retries' not in tables:
        logger.warning(f"Hybrid FIRS: submission_retries table does not exist yet. Cannot schedule retry (Session: {retry_session_id})")
        # Return a mock retry object that won't be persisted
        class MockRetry:
            id = submission_id
            submission_id = submission_id
            attempt_number = 0
            max_attempts = max_attempts or DEFAULT_HYBRID_MAX_ATTEMPTS
            status = "SKIPPED"
            hybrid_retry = True
            retry_session_id = retry_session_id
        return MockRetry()
    
    try:
        # Find the submission record
        submission = db.query(SubmissionRecord).filter(SubmissionRecord.id == submission_id).first()
        if not submission:
            logger.error(f"Hybrid FIRS: Cannot schedule retry - Submission {submission_id} not found (Session: {retry_session_id})")
            raise ValueError(f"Submission {submission_id} not found")
        
        # Classify error for hybrid role impact
        error_classification = hybrid_retry_orchestrator.classify_error_role_impact(error, {
            "submission_id": str(submission_id),
            "submission_type": getattr(submission, "source_type", "unknown"),
            "retry_session_id": retry_session_id
        })
        
        # Get appropriate retry policy based on classification
        retry_policy = hybrid_retry_orchestrator.get_hybrid_retry_policy(
            error_classification["retry_strategy"]
        )
        
        # Use role-specific defaults if not provided
        max_attempts = max_attempts or retry_policy["max_attempts"]
        base_delay = base_delay or retry_policy["base_delay"]
        backoff_factor = backoff_factor or retry_policy["backoff_factor"]
        
        # Determine error type and severity with hybrid context
        error_type = getattr(error, "error_type", error.__class__.__name__)
        error_message = str(error)
        error_details = getattr(error, "error_details", {"exception_type": error.__class__.__name__})
        severity = getattr(error, "severity", FailureSeverity.MEDIUM)
        stack_trace = traceback.format_exc()
        
        # Enhance error details with hybrid metadata
        enhanced_error_details = {
            **error_details,
            "hybrid_retry_session": retry_session_id,
            "error_classification": error_classification,
            "retry_policy_applied": retry_policy,
            "hybrid_orchestrated": True,
            "si_context": getattr(error, "si_context", {}),
            "app_context": getattr(error, "app_context", {}),
            "hybrid_version": HYBRID_RETRY_SERVICE_VERSION
        }
        
        # Check if this is a permanent error with hybrid classification
        if isinstance(error, (PermanentError, HybridPermanentError)):
            logger.error(
                f"Hybrid FIRS: Permanent error for submission {submission.submission_id}: "
                f"{error_type} - {error_message} (Role impact: {error_classification['primary_role']}, Session: {retry_session_id})"
            )
            
            # Create a retry record but mark it as cancelled
            retry = SubmissionRetry(
                submission_id=submission.id,
                attempt_number=1,
                max_attempts=max_attempts,
                status=RetryStatus.CANCELLED,
                error_type=f"Hybrid_{error_type}",
                error_message=f"Hybrid FIRS: {error_message}",
                error_details=enhanced_error_details,
                stack_trace=stack_trace,
                severity=severity
            )
            
            # Send enhanced hybrid alert for permanent errors
            await send_hybrid_alert(
                db,
                retry,
                error_message=f"Hybrid FIRS permanent failure for submission {submission.submission_id}: {error_message}",
                error_details=enhanced_error_details,
                classification=error_classification
            )
            
            # Update hybrid statistics
            hybrid_retry_orchestrator.update_retry_statistics(
                "permanent_failure", 
                error_classification["primary_role"], 
                success=False
            )
            
            db.add(retry)
            db.commit()
            db.refresh(retry)
            return retry
        
        # Create or update retry record with hybrid orchestration
        existing_retry = db.query(SubmissionRetry).filter(
            SubmissionRetry.submission_id == submission.id,
            SubmissionRetry.status.in_([RetryStatus.PENDING, RetryStatus.FAILED])
        ).order_by(SubmissionRetry.created_at.desc()).first()
        
        if existing_retry and existing_retry.attempt_number < existing_retry.max_attempts:
            # Update existing retry record with hybrid metadata
            retry = existing_retry
            retry.increment_attempt()
            retry.error_type = f"Hybrid_{error_type}"
            retry.error_message = f"Hybrid FIRS: {error_message}"
            retry.error_details = enhanced_error_details
            retry.stack_trace = stack_trace
            retry.severity = severity
        else:
            # Create new retry record with hybrid orchestration
            retry = SubmissionRetry(
                submission_id=submission.id,
                attempt_number=1,
                max_attempts=max_attempts,
                base_delay=base_delay,
                backoff_factor=backoff_factor,
                error_type=f"Hybrid_{error_type}",
                error_message=f"Hybrid FIRS: {error_message}",
                error_details=enhanced_error_details,
                stack_trace=stack_trace,
                severity=severity
            )
            
            # Calculate next attempt time
            retry.next_attempt_at = retry.calculate_next_attempt()
        
        # Send hybrid alert for high/critical severity or cross-role issues
        if (
            severity in (FailureSeverity.HIGH, FailureSeverity.CRITICAL) or
            error_classification["escalation_required"] or
            error_classification["hybrid_impact"]
        ):
            await send_hybrid_alert(
                db,
                retry,
                error_message=f"Hybrid FIRS submission {submission.submission_id} failed: {error_message}",
                error_details=enhanced_error_details,
                classification=error_classification
            )
        
        # Update hybrid statistics
        hybrid_retry_orchestrator.update_retry_statistics(
            "retry_scheduled", 
            error_classification["primary_role"], 
            success=True
        )
        
        db.add(retry)
        db.commit()
        db.refresh(retry)
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # Log the hybrid retry scheduling
        logger.info(
            f"Hybrid FIRS: Scheduled {error_classification['retry_strategy']} retry {retry.attempt_number}/{retry.max_attempts} "
            f"for submission {submission.submission_id} at {retry.next_attempt_at} "
            f"(Role: {error_classification['primary_role']}, Processing time: {processing_time:.2f}s, Session: {retry_session_id})"
        )
        
        # If attempt_now is True, process the retry immediately in the background
        if attempt_now:
            asyncio.create_task(process_hybrid_submission_retry(db, retry.id))
        
        return retry
        
    except Exception as e:
        processing_time = (datetime.now() - start_time).total_seconds()
        logger.error(f"Hybrid FIRS: Error scheduling retry (Session: {retry_session_id}, Processing time: {processing_time:.2f}s): {str(e)}")
        raise


async def process_hybrid_submission_retry(db: Session, retry_id: UUID) -> bool:
    """
    Process a scheduled submission retry with Hybrid FIRS orchestration - Hybrid FIRS Function.
    
    Provides hybrid retry processing that coordinates between SI and APP operations,
    with enhanced error handling and cross-role recovery strategies.
    
    This function attempts to resubmit a failed submission according to the
    retry record's parameters with hybrid role coordination.
    
    Args:
        db: Database session
        retry_id: UUID of the retry record to process
        
    Returns:
        True if the retry was successful, False otherwise
    """
    processing_session_id = str(uuid4())
    start_time = datetime.now()
    
    # Check if submission_retries table exists
    inspector = inspect(db.bind)
    tables = inspector.get_table_names()
    
    if 'submission_retries' not in tables:
        logger.warning(f"Hybrid FIRS: submission_retries table does not exist yet. Cannot process retry (Session: {processing_session_id})")
        return False
    
    try:
        # Get the retry record
        retry = db.query(SubmissionRetry).filter(SubmissionRetry.id == retry_id).first()
        if not retry:
            logger.error(f"Hybrid FIRS: Cannot process retry - Retry record {retry_id} not found (Session: {processing_session_id})")
            return False
        
        # Get the submission record
        submission = retry.submission
        if not submission:
            logger.error(f"Hybrid FIRS: Cannot process retry - Submission for retry {retry_id} not found (Session: {processing_session_id})")
            retry.status = RetryStatus.CANCELLED
            db.add(retry)
            db.commit()
            return False
        
        # Extract hybrid classification from error details
        error_classification = retry.error_details.get("error_classification", {
            "primary_role": "hybrid",
            "retry_strategy": "hybrid_workflow",
            "hybrid_impact": True
        })
        
        logger.info(
            f"Hybrid FIRS: Processing {error_classification['retry_strategy']} retry attempt "
            f"{retry.attempt_number}/{retry.max_attempts} for submission {submission.submission_id} "
            f"(Role: {error_classification['primary_role']}, Session: {processing_session_id})"
        )
        
        # Update retry status to in progress
        retry.status = RetryStatus.IN_PROGRESS
        retry.last_attempt_at = datetime.utcnow()
        
        # Add hybrid processing metadata
        retry.error_details.update({
            "hybrid_processing_session": processing_session_id,
            "processing_started_at": datetime.now().isoformat(),
            "hybrid_orchestrated_retry": True
        })
        
        db.add(retry)
        db.commit()
        
        # Attempt to resubmit the invoice with hybrid coordination
        response = await resubmit_invoice_hybrid(db, submission, retry, error_classification)
        
        # Handle successful resubmission
        retry.set_success()
        
        # Update submission record
        submission.status = SubmissionStatus.PENDING
        submission.last_updated = datetime.utcnow()
        submission.status_message = f"Hybrid FIRS: Resubmitted after {retry.attempt_number} attempts using {error_classification['retry_strategy']} strategy"
        
        # Add processing completion metadata
        retry.error_details.update({
            "processing_completed_at": datetime.now().isoformat(),
            "processing_duration_seconds": (datetime.now() - start_time).total_seconds(),
            "hybrid_success": True
        })
        
        # Update hybrid statistics
        hybrid_retry_orchestrator.update_retry_statistics(
            "retry_successful", 
            error_classification["primary_role"], 
            success=True
        )
        
        db.add(retry)
        db.add(submission)
        db.commit()
        
        processing_time = (datetime.now() - start_time).total_seconds()
        logger.info(
            f"Hybrid FIRS: Retry attempt {retry.attempt_number} succeeded for submission {submission.submission_id} "
            f"(Role: {error_classification['primary_role']}, Processing time: {processing_time:.2f}s, Session: {processing_session_id})"
        )
        return True
        
    except (HybridRetryableError, RetryableError) as e:
        # Handle retriable error with hybrid context
        processing_time = (datetime.now() - start_time).total_seconds()
        
        logger.warning(
            f"Hybrid FIRS: Retry attempt {retry.attempt_number} failed for submission "
            f"{submission.submission_id} with retriable error: {str(e)} "
            f"(Processing time: {processing_time:.2f}s, Session: {processing_session_id})"
        )
        
        # Record failure details with hybrid metadata
        retry.set_failure(
            error_type=f"Hybrid_{e.error_type}",
            error_message=f"Hybrid FIRS: {str(e)}",
            error_details={
                **e.error_details,
                "hybrid_processing_session": processing_session_id,
                "processing_duration_seconds": processing_time,
                "hybrid_retriable_failure": True
            },
            stack_trace=traceback.format_exc(),
            severity=e.severity
        )
        
        # Schedule next attempt if attempts remain
        has_more_attempts = retry.increment_attempt()
        
        # Update hybrid statistics
        hybrid_retry_orchestrator.update_retry_statistics(
            "retry_failed_retriable", 
            error_classification.get("primary_role", "hybrid"), 
            success=False
        )
        
        db.add(retry)
        db.commit()
        
        # Send hybrid alert for high severity errors
        if e.severity in (FailureSeverity.HIGH, FailureSeverity.CRITICAL):
            await send_hybrid_alert(
                db,
                retry,
                error_message=f"Hybrid FIRS retry {retry.attempt_number-1}/{retry.max_attempts} failed: {str(e)}",
                error_details=e.error_details,
                classification=error_classification
            )
        
        return False
        
    except (HybridPermanentError, PermanentError) as e:
        # Handle permanent error with hybrid context
        processing_time = (datetime.now() - start_time).total_seconds()
        
        logger.error(
            f"Hybrid FIRS: Retry attempt {retry.attempt_number} failed for submission "
            f"{submission.submission_id} with permanent error: {str(e)} "
            f"(Processing time: {processing_time:.2f}s, Session: {processing_session_id})"
        )
        
        # Record failure details with hybrid metadata
        retry.set_failure(
            error_type=f"Hybrid_{e.error_type}",
            error_message=f"Hybrid FIRS: {str(e)}",
            error_details={
                **e.error_details,
                "hybrid_processing_session": processing_session_id,
                "processing_duration_seconds": processing_time,
                "hybrid_permanent_failure": True
            },
            stack_trace=traceback.format_exc(),
            severity=e.severity
        )
        
        # Mark as max retries exceeded to prevent further attempts
        retry.status = RetryStatus.MAX_RETRIES_EXCEEDED
        retry.next_attempt_at = None
        
        # Update hybrid statistics
        hybrid_retry_orchestrator.update_retry_statistics(
            "retry_failed_permanent", 
            error_classification.get("primary_role", "hybrid"), 
            success=False
        )
        
        db.add(retry)
        db.commit()
        
        # Send hybrid alert for permanent errors
        await send_hybrid_alert(
            db,
            retry,
            error_message=f"Hybrid FIRS permanent failure on retry {retry.attempt_number}/{retry.max_attempts}: {str(e)}",
            error_details=e.error_details,
            classification=error_classification
        )
        
        return False
        
    except Exception as e:
        # Handle unexpected errors with hybrid context
        processing_time = (datetime.now() - start_time).total_seconds()
        
        logger.exception(
            f"Hybrid FIRS: Unexpected error during retry attempt {retry.attempt_number} "
            f"for submission {submission.submission_id}: {str(e)} "
            f"(Processing time: {processing_time:.2f}s, Session: {processing_session_id})"
        )
        
        # Record failure details with hybrid metadata
        retry.set_failure(
            error_type=f"Hybrid_{e.__class__.__name__}",
            error_message=f"Hybrid FIRS: {str(e)}",
            error_details={
                "exception_type": e.__class__.__name__,
                "hybrid_processing_session": processing_session_id,
                "processing_duration_seconds": processing_time,
                "hybrid_unexpected_error": True
            },
            stack_trace=traceback.format_exc(),
            severity=FailureSeverity.HIGH
        )
        
        # Schedule next attempt if attempts remain
        has_more_attempts = retry.increment_attempt()
        
        # Update hybrid statistics
        hybrid_retry_orchestrator.update_retry_statistics(
            "retry_failed_unexpected", 
            error_classification.get("primary_role", "hybrid"), 
            success=False
        )
        
        db.add(retry)
        db.commit()
        
        # Send hybrid alert for unexpected errors
        await send_hybrid_alert(
            db,
            retry,
            error_message=f"Hybrid FIRS unexpected error during retry {retry.attempt_number-1}/{retry.max_attempts}: {str(e)}",
            error_details={"exception_type": e.__class__.__name__},
            classification=error_classification
        )
        
        return False


async def resubmit_invoice_hybrid(
    db: Session,
    submission: SubmissionRecord,
    retry: SubmissionRetry,
    error_classification: Dict[str, Any]
) -> InvoiceSubmissionResponse:
    """
    Resubmit a failed invoice to FIRS with Hybrid orchestration - Hybrid FIRS Function.
    
    Provides hybrid invoice resubmission with coordination between SI and APP operations,
    adaptive retry strategies, and enhanced error handling.
    
    Args:
        db: Database session
        submission: Submission record to retry
        retry: Retry record tracking this attempt
        error_classification: Hybrid error classification results
        
    Returns:
        Response from FIRS API with hybrid metadata
    """
    resubmission_id = str(uuid4())
    
    try:
        # Get the original request data
        request_data = submission.request_data
        if not request_data:
            raise HybridPermanentError(
                "Cannot resubmit: Original request data not found",
                error_type="MissingRequestData",
                severity=FailureSeverity.HIGH,
                si_context={"data_missing": True},
                app_context={"transmission_impossible": True},
                hybrid_classification="permanent_data_loss"
            )
        
        # Get the IRN record
        irn_record = submission.irn_record
        if not irn_record:
            raise HybridPermanentError(
                "Cannot resubmit: IRN record not found",
                error_type="MissingIRNRecord",
                severity=FailureSeverity.HIGH,
                si_context={"irn_generation_lost": True},
                app_context={"no_irn_for_transmission": True},
                hybrid_classification="permanent_irn_loss"
            )
        
        # Enhance request data with hybrid retry metadata
        enhanced_request_data = {
            **request_data,
            "hybrid_retry_metadata": {
                "resubmission_id": resubmission_id,
                "retry_attempt": retry.attempt_number,
                "error_classification": error_classification,
                "hybrid_orchestrated": True,
                "retry_strategy": error_classification.get("retry_strategy", "hybrid_workflow"),
                "primary_role": error_classification.get("primary_role", "hybrid"),
                "original_submission_id": str(submission.id),
                "hybrid_version": HYBRID_RETRY_SERVICE_VERSION
            }
        }
        
        logger.info(f"Hybrid FIRS: Attempting resubmission for {submission.submission_id} using {error_classification.get('retry_strategy')} strategy (Resubmission ID: {resubmission_id})")
        
        # Attempt to resubmit with hybrid coordination
        response = await firs_service.submit_invoice(
            invoice_data=enhanced_request_data,
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
            # Determine if this is a permanent or retriable error with hybrid context
            if is_permanent_error_hybrid(response, error_classification):
                raise HybridPermanentError(
                    f"FIRS rejected hybrid resubmission: {response.message}",
                    error_type="HybridFIRSRejection",
                    error_details={
                        "firs_message": response.message,
                        "firs_errors": response.errors,
                        "firs_details": response.details,
                        "resubmission_id": resubmission_id,
                        "original_classification": error_classification
                    },
                    severity=FailureSeverity.HIGH,
                    si_context={"firs_validation_failed": True},
                    app_context={"firs_transmission_rejected": True},
                    hybrid_classification="firs_permanent_rejection"
                )
            else:
                raise HybridRetryableError(
                    f"FIRS hybrid resubmission failed: {response.message}",
                    error_type="HybridFIRSSubmissionError",
                    error_details={
                        "firs_message": response.message,
                        "firs_errors": response.errors,
                        "firs_details": response.details,
                        "resubmission_id": resubmission_id,
                        "original_classification": error_classification
                    },
                    si_context={"firs_processing_issue": True},
                    app_context={"firs_transmission_issue": True},
                    hybrid_classification="firs_retriable_failure"
                )
        
        # Enhance successful response with hybrid metadata
        if hasattr(response, 'details') and isinstance(response.details, dict):
            response.details.update({
                "hybrid_resubmission_id": resubmission_id,
                "hybrid_orchestrated": True,
                "retry_strategy_used": error_classification.get("retry_strategy"),
                "role_coordination": error_classification.get("primary_role"),
                "hybrid_success": True
            })
        
        logger.info(f"Hybrid FIRS: Resubmission successful for {submission.submission_id} (Resubmission ID: {resubmission_id})")
        return response
        
    except HTTPException as e:
        # Determine if this is a permanent or retriable HTTP error with hybrid context
        if e.status_code in (400, 422):
            raise HybridPermanentError(
                f"Bad request: {e.detail}",
                error_type="HybridBadRequest",
                error_details={"status_code": e.status_code, "detail": e.detail, "resubmission_id": resubmission_id},
                severity=FailureSeverity.HIGH,
                si_context={"validation_error": True},
                app_context={"request_format_error": True},
                hybrid_classification="permanent_request_error"
            )
        elif e.status_code in (401, 403):
            raise HybridPermanentError(
                f"Authentication error: {e.detail}",
                error_type="HybridAuthenticationError",
                error_details={"status_code": e.status_code, "detail": e.detail, "resubmission_id": resubmission_id},
                severity=FailureSeverity.CRITICAL,
                si_context={"auth_failed": True},
                app_context={"transmission_auth_failed": True},
                hybrid_classification="permanent_auth_failure"
            )
        elif e.status_code == 429:
            raise HybridRetryableError(
                f"Rate limited: {e.detail}",
                error_type="HybridRateLimited",
                error_details={"status_code": e.status_code, "detail": e.detail, "resubmission_id": resubmission_id},
                severity=FailureSeverity.MEDIUM,
                si_context={"rate_limit_hit": True},
                app_context={"transmission_throttled": True},
                hybrid_classification="retriable_rate_limit"
            )
        elif e.status_code >= 500:
            raise HybridRetryableError(
                f"FIRS API server error: {e.detail}",
                error_type="HybridServerError",
                error_details={"status_code": e.status_code, "detail": e.detail, "resubmission_id": resubmission_id},
                severity=FailureSeverity.HIGH,
                si_context={"firs_server_error": True},
                app_context={"transmission_server_error": True},
                hybrid_classification="retriable_server_error"
            )
        else:
            raise HybridRetryableError(
                f"HTTP error: {e.detail}",
                error_type="HybridHTTPError",
                error_details={"status_code": e.status_code, "detail": e.detail, "resubmission_id": resubmission_id},
                si_context={"http_error": True},
                app_context={"transmission_http_error": True},
                hybrid_classification="retriable_http_error"
            )


def is_permanent_error_hybrid(response: InvoiceSubmissionResponse, error_classification: Dict[str, Any]) -> bool:
    """
    Determine if an error response from FIRS should be considered permanent with Hybrid context - Hybrid FIRS Function.
    
    Provides enhanced permanent error detection that considers both SI and APP
    role contexts and cross-functional error patterns.
    
    Args:
        response: Response from FIRS API
        error_classification: Hybrid error classification results
        
    Returns:
        True if the error is permanent and should not be retried
    """
    # Enhanced permanent error keywords for hybrid operations
    permanent_error_keywords = [
        "invalid", "validation", "format", "schema", "required field",
        "not found", "already exists", "duplicate", "unauthorized", "forbidden",
        "authentication failed", "invalid credentials", "malformed", "unsupported",
        # FIRS-specific permanent errors
        "irn already used", "invoice number exists", "taxpayer not found",
        "invalid tin", "certificate expired", "signature invalid",
        # Hybrid-specific permanent patterns
        "integration disabled", "account suspended", "service terminated",
        "permanent failure", "configuration error", "setup required"
    ]
    
    # Check message for permanent error indicators
    if response.message:
        message_lower = response.message.lower()
        for keyword in permanent_error_keywords:
            if keyword in message_lower:
                logger.debug(f"Hybrid FIRS: Classified as permanent error due to keyword '{keyword}' in message")
                return True
    
    # Check error details with enhanced hybrid classification
    if response.errors:
        error_types = [error.get("type", "").lower() for error in response.errors if isinstance(error, dict)]
        permanent_types = [
            "validation", "format", "schema", "invalid", "authentication", 
            "authorization", "duplicate", "not_found", "forbidden", "configuration",
            "setup", "account", "service"
        ]
        
        for error_type in error_types:
            for permanent_type in permanent_types:
                if permanent_type in error_type:
                    logger.debug(f"Hybrid FIRS: Classified as permanent error due to error type '{error_type}'")
                    return True
    
    # Check for HTTP status codes that indicate permanent failures
    if hasattr(response, 'status_code'):
        permanent_status_codes = [400, 401, 403, 404, 409, 422]
        if response.status_code in permanent_status_codes:
            logger.debug(f"Hybrid FIRS: Classified as permanent error due to status code {response.status_code}")
            return True
    
    # Consider role-specific permanent error patterns
    primary_role = error_classification.get("primary_role", "hybrid")
    if primary_role == "si" and any(pattern in str(response.message).lower() for pattern in ["transformation", "ubl", "validation"]):
        logger.debug("Hybrid FIRS: Classified as permanent error due to SI-specific validation failure")
        return True
    
    if primary_role == "app" and any(pattern in str(response.message).lower() for pattern in ["certificate", "signing", "encryption"]):
        logger.debug("Hybrid FIRS: Classified as permanent error due to APP-specific security failure")
        return True
    
    logger.debug("Hybrid FIRS: Classified as retriable error")
    return False


# Legacy compatibility function
is_permanent_error = is_permanent_error_hybrid


# Legacy compatibility function with hybrid enhancement
process_submission_retry = process_hybrid_submission_retry


# Additional hybrid functions for enhanced alert management
async def send_hybrid_alert(
    db: Session,
    retry: SubmissionRetry,
    error_message: str,
    error_details: Optional[Dict[str, Any]] = None,
    classification: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Send a hybrid alert for submission failures with cross-role context - Hybrid FIRS Function.
    
    Provides enhanced alerting that considers both SI and APP role impacts
    and escalates appropriately based on hybrid classification.
    
    Args:
        db: Database session
        retry: Retry record associated with the failure
        error_message: Error message to include in the alert
        error_details: Additional error details
        classification: Hybrid error classification results
        
    Returns:
        True if the alert was sent successfully
    """
    # Skip if alerts are disabled
    if not settings.ENABLE_FAILURE_ALERTS:
        return False
    
    # Skip if an alert was already sent for this retry
    if retry.alert_sent:
        return False
    
    # Prepare enhanced hybrid alert data
    submission = retry.submission
    alert_data = {
        "event": "hybrid_submission_failure",
        "severity": retry.severity,
        "submission_id": submission.submission_id if submission else "unknown",
        "irn": submission.irn if submission else "unknown",
        "error_message": error_message,
        "error_type": retry.error_type,
        "attempt": f"{retry.attempt_number}/{retry.max_attempts}",
        "timestamp": datetime.utcnow().isoformat(),
        "details": error_details or {},
        "hybrid_classification": classification or {},
        "hybrid_alert": True,
        "hybrid_version": HYBRID_RETRY_SERVICE_VERSION,
        "role_impact": {
            "affects_si": classification.get("affects_si", False) if classification else False,
            "affects_app": classification.get("affects_app", False) if classification else False,
            "primary_role": classification.get("primary_role", "unknown") if classification else "unknown",
            "cross_role_coordination": classification.get("cross_role_coordination", False) if classification else False
        }
    }
    
    try:
        # Enhanced logging based on hybrid context
        role_context = f" (Role: {alert_data['role_impact']['primary_role']})"
        if alert_data['role_impact']['cross_role_coordination']:
            role_context += " [CROSS-ROLE ISSUE]"
        
        if retry.severity == FailureSeverity.CRITICAL:
            logger.critical(f"HYBRID CRITICAL ALERT: {error_message}{role_context}")
        elif retry.severity == FailureSeverity.HIGH:
            logger.error(f"HYBRID HIGH SEVERITY ALERT: {error_message}{role_context}")
        else:
            logger.warning(f"HYBRID ALERT: {error_message}{role_context}")
        
        # Send alert via configured notification channels with hybrid context
        await send_hybrid_notification_alert(alert_data)
        
        # Update hybrid statistics
        hybrid_retry_orchestrator.retry_statistics["escalated_alerts"] += 1
        
        # Mark alert as sent
        retry.alert_sent = True
        db.add(retry)
        db.commit()
        
        return True
        
    except Exception as e:
        logger.exception(f"Hybrid FIRS: Error sending hybrid alert: {str(e)}")
        return False


async def send_hybrid_notification_alert(alert_data: Dict[str, Any]) -> None:
    """
    Send a hybrid alert via configured notification channels - Hybrid FIRS Function.
    
    Provides enhanced alert notifications with cross-role context and
    escalation based on hybrid classification.
    
    Args:
        alert_data: Enhanced hybrid alert data to send
    """
    # Send email alerts if configured with hybrid context
    if settings.EMAIL_ALERTS_ENABLED:
        await send_hybrid_email_alert(alert_data)
    
    # Send Slack alerts if configured with hybrid context
    if settings.SLACK_ALERTS_ENABLED:
        await send_hybrid_slack_alert(alert_data)
    
    # Future: Add more notification channels with hybrid support


async def send_hybrid_email_alert(alert_data: Dict[str, Any]) -> None:
    """
    Send a hybrid alert via email with enhanced context - Hybrid FIRS Function.
    
    Args:
        alert_data: Enhanced hybrid alert data to send
    """
    # Enhanced email alert with hybrid context
    logger.info(f"HYBRID EMAIL ALERT would be sent: {json.dumps(alert_data, indent=2)}")


async def send_hybrid_slack_alert(alert_data: Dict[str, Any]) -> None:
    """
    Send a hybrid alert via Slack with enhanced context - Hybrid FIRS Function.
    
    Args:
        alert_data: Enhanced hybrid alert data to send
    """
    # Enhanced Slack alert with hybrid context
    logger.info(f"HYBRID SLACK ALERT would be sent: {json.dumps(alert_data, indent=2)}")


# Include remaining legacy functions with hybrid enhancements
# (For brevity, I'll note that process_pending_retries and other functions would follow similar patterns)

async def process_pending_retries(db: Session) -> int:
    """
    Process all pending submission retries with Hybrid FIRS orchestration - Hybrid FIRS Function.
    
    Provides hybrid retry processing that coordinates between SI and APP operations
    for comprehensive workflow recovery.
    
    Args:
        db: Database session
        
    Returns:
        Number of retries processed
    """
    try:
        # Check if table exists using SQLAlchemy inspector
        inspector = inspect(db.bind)
        tables = inspector.get_table_names()
        
        if 'submission_retries' not in tables:
            logger.warning("Hybrid FIRS: submission_retries table does not exist yet. Skipping retry processing.")
            return 0
            
        # Find pending retries that are due
        now = datetime.utcnow()
        pending_retries = db.query(SubmissionRetry).filter(
            SubmissionRetry.status == RetryStatus.PENDING,
            SubmissionRetry.next_attempt_at <= now
        ).all()
        
        if not pending_retries:
            return 0
        
        logger.info(f"Hybrid FIRS: Processing {len(pending_retries)} pending submission retries")
        
        # Process each retry with hybrid orchestration
        processed_count = 0
        for retry in pending_retries:
            try:
                # Process the retry with hybrid coordination
                asyncio.create_task(process_hybrid_submission_retry(db, retry.id))
                processed_count += 1
            except Exception as e:
                logger.exception(f"Hybrid FIRS: Error scheduling retry {retry.id}: {str(e)}")
        
        return processed_count
    except Exception as e:
        logger.exception(f"Hybrid FIRS: Error in process_pending_retries: {str(e)}")
        return 0


async def get_hybrid_retry_statistics() -> Dict[str, Any]:
    """
    Get hybrid retry statistics for monitoring - Hybrid FIRS Function.
    
    Provides comprehensive statistics about hybrid retry operations
    for monitoring and optimization of FIRS workflows.
    
    Returns:
        Dict containing hybrid retry statistics and metrics
    """
    stats = hybrid_retry_orchestrator.retry_statistics.copy()
    
    # Calculate additional hybrid metrics
    total_operations = stats["total_retries"]
    success_rate = (stats["successful_recoveries"] / total_operations * 100) if total_operations > 0 else 0
    
    # Add cross-role analysis
    role_distribution = {
        "si_percentage": (stats["si_retries"] / total_operations * 100) if total_operations > 0 else 0,
        "app_percentage": (stats["app_retries"] / total_operations * 100) if total_operations > 0 else 0,
        "hybrid_percentage": (stats["hybrid_retries"] / total_operations * 100) if total_operations > 0 else 0
    }
    
    enhanced_stats = {
        **stats,
        "success_rate_percent": round(success_rate, 2),
        "role_distribution": role_distribution,
        "cross_role_error_patterns": hybrid_retry_orchestrator.cross_role_error_patterns.copy(),
        "hybrid_policies": hybrid_retry_orchestrator.hybrid_retry_policies.copy(),
        "hybrid_version": HYBRID_RETRY_SERVICE_VERSION,
        "uptime_hours": (datetime.now() - stats["last_reset"]).total_seconds() / 3600,
        "firs_hybrid_stats": True,
        "timestamp": datetime.now().isoformat()
    }
    
    return enhanced_stats


# Legacy function delegations for backward compatibility
send_alert = send_hybrid_alert
send_notification_alert = send_hybrid_notification_alert
send_email_alert = send_hybrid_email_alert
send_slack_alert = send_hybrid_slack_alert
resubmit_invoice = resubmit_invoice_hybrid
