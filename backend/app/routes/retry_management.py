"""
Routes for managing submission retries and failures.

This module provides API endpoints for:
1. Monitoring failed submissions
2. Manually triggering retries
3. Viewing failure logs and alerts
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc
from datetime import datetime, timedelta
from uuid import UUID

from app.database.session import get_db
from app.auth.jwt import get_current_active_user, get_current_admin_user
from app.models.user import User
from app.models.submission import SubmissionRecord, SubmissionStatus
from app.models.submission_retry import SubmissionRetry, RetryStatus, FailureSeverity
from app.services.retry_service import process_submission_retry, schedule_submission_retry, RetryableError
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/api/v1/retry-management",
    tags=["retry-management"],
    responses={404: {"description": "Not found"}},
)


@router.get("/failed-submissions", response_model=List[Dict[str, Any]])
async def get_failed_submissions(
    status: Optional[str] = Query(None, description="Filter by status"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    time_period: int = Query(24, description="Time period in hours to look back"),
    limit: int = Query(50, description="Maximum number of records to return"),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """
    Get a list of failed submissions.
    
    This endpoint returns information about failed submissions, including
    retry attempts and failure details.
    
    Only admin users can access this endpoint.
    """
    # Build the query
    query = db.query(SubmissionRetry).join(
        SubmissionRecord, SubmissionRetry.submission_id == SubmissionRecord.id
    )
    
    # Filter by status if provided
    if status:
        try:
            retry_status = RetryStatus(status)
            query = query.filter(SubmissionRetry.status == retry_status)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status value: {status}"
            )
    
    # Filter by severity if provided
    if severity:
        try:
            failure_severity = FailureSeverity(severity)
            query = query.filter(SubmissionRetry.severity == failure_severity)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid severity value: {severity}"
            )
    
    # Filter by time period
    if time_period > 0:
        lookback = datetime.utcnow() - timedelta(hours=time_period)
        query = query.filter(SubmissionRetry.created_at >= lookback)
    
    # Get the results
    failures = query.order_by(desc(SubmissionRetry.created_at)).limit(limit).all()
    
    # Format the response
    results = []
    for failure in failures:
        submission = failure.submission
        results.append({
            "retry_id": str(failure.id),
            "submission_id": submission.submission_id if submission else "unknown",
            "irn": submission.irn if submission else "unknown",
            "status": failure.status,
            "severity": failure.severity,
            "attempt": f"{failure.attempt_number}/{failure.max_attempts}",
            "error_type": failure.error_type,
            "error_message": failure.error_message,
            "created_at": failure.created_at.isoformat(),
            "next_attempt_at": failure.next_attempt_at.isoformat() if failure.next_attempt_at else None,
            "last_attempt_at": failure.last_attempt_at.isoformat() if failure.last_attempt_at else None,
            "alert_sent": failure.alert_sent
        })
    
    return results


@router.get("/retry/{retry_id}", response_model=Dict[str, Any])
async def get_retry_details(
    retry_id: UUID = Path(..., description="UUID of the retry record"),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """
    Get detailed information about a specific retry attempt.
    
    This endpoint returns detailed information about a retry attempt,
    including full error details and stack trace.
    
    Only admin users can access this endpoint.
    """
    # Get the retry record
    retry = db.query(SubmissionRetry).filter(SubmissionRetry.id == retry_id).first()
    if not retry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Retry record {retry_id} not found"
        )
    
    # Get the submission record
    submission = retry.submission
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Submission for retry {retry_id} not found"
        )
    
    # Format the response
    return {
        "retry_id": str(retry.id),
        "submission": {
            "id": str(submission.id),
            "submission_id": submission.submission_id,
            "irn": submission.irn,
            "status": submission.status,
            "created_at": submission.created_at.isoformat(),
            "integration_id": str(submission.integration_id),
            "source_type": submission.source_type,
            "source_id": submission.source_id,
            "webhook_enabled": submission.webhook_enabled,
            "webhook_url": submission.webhook_url
        },
        "retry": {
            "status": retry.status,
            "severity": retry.severity,
            "attempt_number": retry.attempt_number,
            "max_attempts": retry.max_attempts,
            "next_attempt_at": retry.next_attempt_at.isoformat() if retry.next_attempt_at else None,
            "last_attempt_at": retry.last_attempt_at.isoformat() if retry.last_attempt_at else None,
            "created_at": retry.created_at.isoformat(),
            "updated_at": retry.updated_at.isoformat(),
            "backoff_factor": retry.backoff_factor,
            "base_delay": retry.base_delay,
            "alert_sent": retry.alert_sent
        },
        "error": {
            "type": retry.error_type,
            "message": retry.error_message,
            "details": retry.error_details,
            "stack_trace": retry.stack_trace
        }
    }


@router.post("/retry/{retry_id}/trigger", response_model=Dict[str, Any])
async def trigger_retry(
    retry_id: UUID = Path(..., description="UUID of the retry record"),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """
    Manually trigger a retry attempt.
    
    This endpoint allows an admin to manually trigger a retry attempt
    for a failed submission, bypassing the scheduled retry time.
    
    Only admin users can access this endpoint.
    """
    # Get the retry record
    retry = db.query(SubmissionRetry).filter(SubmissionRetry.id == retry_id).first()
    if not retry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Retry record {retry_id} not found"
        )
    
    # Check if the retry is in a state that can be triggered
    if retry.status not in (RetryStatus.PENDING, RetryStatus.FAILED):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot trigger retry in {retry.status} state"
        )
    
    try:
        # Set the retry to pending and update the next attempt time to now
        retry.status = RetryStatus.PENDING
        retry.next_attempt_at = datetime.utcnow()
        db.add(retry)
        db.commit()
        db.refresh(retry)
        
        # Process the retry in the background
        await process_submission_retry(db, retry.id)
        
        return {
            "status": "success",
            "message": f"Retry {retry_id} triggered successfully",
            "retry_id": str(retry.id),
            "submission_id": retry.submission.submission_id if retry.submission else "unknown"
        }
        
    except Exception as e:
        logger.exception(f"Error triggering retry {retry_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error triggering retry: {str(e)}"
        )


@router.post("/submission/{submission_id}/retry", response_model=Dict[str, Any])
async def create_manual_retry(
    submission_id: str = Path(..., description="FIRS submission ID"),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """
    Create a manual retry for a submission.
    
    This endpoint allows an admin to create a new retry record for a submission,
    even if it doesn't currently have any active retry attempts.
    
    Only admin users can access this endpoint.
    """
    # Find the submission record
    submission = db.query(SubmissionRecord).filter(
        SubmissionRecord.submission_id == submission_id
    ).first()
    
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Submission {submission_id} not found"
        )
    
    try:
        # Create a new retry attempt
        error = RetryableError(
            f"Manual retry requested by {current_user.email}",
            error_type="ManualRetry",
            error_details={"requested_by": current_user.email}
        )
        
        retry = await schedule_submission_retry(
            db=db,
            submission_id=submission.id,
            error=error,
            attempt_now=True  # Process immediately
        )
        
        return {
            "status": "success",
            "message": f"Manual retry created for submission {submission_id}",
            "retry_id": str(retry.id),
            "submission_id": submission_id
        }
        
    except Exception as e:
        logger.exception(f"Error creating manual retry for {submission_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating manual retry: {str(e)}"
        )
