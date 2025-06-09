"""
Submission retry models for tracking failed FIRS invoice submissions.

This module provides models for tracking retry attempts for failed submissions,
implementing exponential backoff, and recording detailed failure information.
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, Enum as SQLEnum, Integer, Text, Float, Boolean # type: ignore
from sqlalchemy.sql import func # type: ignore
from sqlalchemy.orm import relationship # type: ignore
from sqlalchemy.dialects.postgresql import UUID # type: ignore
import enum
from uuid import uuid4
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from app.db.base_class import Base # type: ignore


class RetryStatus(str, enum.Enum):
    """Status of a submission retry attempt."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    MAX_RETRIES_EXCEEDED = "max_retries_exceeded"


class FailureSeverity(str, enum.Enum):
    """Severity level of submission failures for alerting purposes."""
    LOW = "low"           # Minor issues, automatic retry should resolve
    MEDIUM = "medium"     # Significant issues, may require attention
    HIGH = "high"         # Serious issues, requires immediate attention
    CRITICAL = "critical" # Critical failure, system operations affected


class SubmissionRetry(Base):
    """
    Tracks retry attempts for failed FIRS invoice submissions.
    
    This model implements the retry mechanism for failed submissions,
    including exponential backoff and detailed failure tracking.
    """
    __tablename__ = "submission_retries"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    submission_id = Column(UUID(as_uuid=True), ForeignKey("submission_records.id"), nullable=False, index=True)
    
    # Retry tracking
    attempt_number = Column(Integer, nullable=False, default=1)
    max_attempts = Column(Integer, nullable=False, default=5)
    next_attempt_at = Column(DateTime, nullable=True, index=True)
    last_attempt_at = Column(DateTime, nullable=True)
    backoff_factor = Column(Float, nullable=False, default=2.0)  # For exponential backoff
    base_delay = Column(Integer, nullable=False, default=60)  # Base delay in seconds
    jitter = Column(Float, nullable=False, default=0.1)  # Random jitter factor (0.0-1.0)
    
    # Status tracking
    status = Column(SQLEnum(RetryStatus), nullable=False, default=RetryStatus.PENDING)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    
    # Error details
    error_type = Column(String(100), nullable=True)
    error_message = Column(String(1000), nullable=True)
    error_details = Column(JSON, nullable=True)
    stack_trace = Column(Text, nullable=True)
    
    # Alert information
    severity = Column(SQLEnum(FailureSeverity), nullable=False, default=FailureSeverity.MEDIUM)
    alert_sent = Column(Boolean, nullable=False, default=False)
    
    # Relationships
    submission = relationship("SubmissionRecord", back_populates="retry_attempts")
    
    def calculate_next_attempt(self) -> datetime:
        """
        Calculate the next retry attempt time using exponential backoff with jitter.
        
        Returns:
            Datetime when the next retry should be attempted
        """
        import random
        
        # Calculate delay using exponential backoff
        delay = self.base_delay * (self.backoff_factor ** (self.attempt_number - 1))
        
        # Add jitter to prevent thundering herd problem
        jitter_value = random.uniform(-self.jitter, self.jitter)
        delay = delay * (1 + jitter_value)
        
        # Calculate next attempt time
        return datetime.utcnow() + timedelta(seconds=delay)
    
    def increment_attempt(self) -> bool:
        """
        Increment the retry attempt counter and calculate next attempt time.
        
        Returns:
            True if more retries are available, False if max retries exceeded
        """
        self.attempt_number += 1
        self.last_attempt_at = datetime.utcnow()
        
        # Check if max retries exceeded
        if self.attempt_number > self.max_attempts:
            self.status = RetryStatus.MAX_RETRIES_EXCEEDED
            self.next_attempt_at = None
            return False
        
        # Calculate next attempt time
        self.next_attempt_at = self.calculate_next_attempt()
        self.status = RetryStatus.PENDING
        return True
    
    def set_success(self) -> None:
        """Mark the retry as successful."""
        self.status = RetryStatus.SUCCEEDED
        self.next_attempt_at = None
        self.updated_at = datetime.utcnow()
    
    def set_failure(
        self, 
        error_type: str,
        error_message: str,
        error_details: Optional[Dict[str, Any]] = None,
        stack_trace: Optional[str] = None,
        severity: Optional[FailureSeverity] = None
    ) -> None:
        """
        Record failure details for this retry attempt.
        
        Args:
            error_type: Type of error encountered
            error_message: Error message
            error_details: Additional error context
            stack_trace: Exception stack trace if available
            severity: Failure severity level
        """
        self.status = RetryStatus.FAILED
        self.error_type = error_type
        self.error_message = error_message
        self.error_details = error_details
        self.stack_trace = stack_trace
        
        # Update severity if provided
        if severity:
            self.severity = severity
        
        self.updated_at = datetime.utcnow()


# Add this relationship to the SubmissionRecord model
from app.models.submission import SubmissionRecord
SubmissionRecord.retry_attempts = relationship("SubmissionRetry", back_populates="submission", 
                                             order_by="desc(SubmissionRetry.created_at)")
