"""
Submission tracking models for FIRS invoice submissions.

This module provides models for tracking the status of invoice submissions
to the Federal Inland Revenue Service (FIRS) API, allowing for comprehensive
status history and notification tracking.
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, Enum as SQLEnum, Text, Boolean, Integer # type: ignore
from sqlalchemy.sql import func # type: ignore
from sqlalchemy.orm import relationship # type: ignore
from sqlalchemy.dialects.postgresql import UUID # type: ignore
import enum
from uuid import uuid4
from datetime import datetime
from typing import Optional, List, Dict, Any

from app.db.base_class import Base # type: ignore


class SubmissionStatus(str, enum.Enum):
    """Submission status enumeration for FIRS invoice submissions."""
    PENDING = "pending"
    PROCESSING = "processing"
    VALIDATED = "validated"
    SIGNED = "signed"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    FAILED = "failed"
    ERROR = "error"
    CANCELLED = "cancelled"


class NotificationStatus(str, enum.Enum):
    """Status of webhook notifications for submission updates."""
    PENDING = "pending"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETRY = "retry"


class SubmissionRecord(Base):
    """
    Records and tracks FIRS invoice submissions.
    
    This model stores the complete submission history with all status updates,
    allowing for comprehensive tracking and auditing of invoice submissions.
    """
    __tablename__ = "submission_records"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    submission_id = Column(String(100), nullable=False, unique=True, index=True)
    irn = Column(String(50), ForeignKey("irn_records.irn"), nullable=False, index=True)
    integration_id = Column(String(36), ForeignKey("integrations.id"), nullable=False)
    
    # Status tracking
    status = Column(SQLEnum(SubmissionStatus), nullable=False, default=SubmissionStatus.PENDING)
    status_message = Column(String(512), nullable=True)
    last_updated = Column(DateTime, nullable=False, default=func.now())
    created_at = Column(DateTime, nullable=False, default=func.now())
    
    # Submission details
    request_data = Column(JSON, nullable=True)  # Data sent in submission
    response_data = Column(JSON, nullable=True)  # Most recent response data
    
    # Source information
    source_type = Column(String(50), nullable=False)  # e.g., 'odoo', 'manual', 'api'
    source_id = Column(String(100), nullable=True)  # e.g., Odoo invoice ID
    
    # User information
    submitted_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Webhook notification tracking
    webhook_enabled = Column(Boolean, nullable=False, default=False)
    webhook_url = Column(String(512), nullable=True)
    
    # Relationships
    irn_record = relationship("IRNRecord", back_populates="submission_records")
    integration = relationship("Integration", back_populates="submission_records")
    status_updates = relationship("SubmissionStatusUpdate", back_populates="submission", 
                                 order_by="desc(SubmissionStatusUpdate.timestamp)")
    notifications = relationship("SubmissionNotification", back_populates="submission",
                               order_by="desc(SubmissionNotification.timestamp)")
    
    def update_status(self, status: SubmissionStatus, message: Optional[str] = None, 
                      response_data: Optional[Dict[str, Any]] = None) -> "SubmissionStatusUpdate":
        """
        Update the submission status and create a status update record.
        
        Args:
            status: New submission status
            message: Optional status message
            response_data: Optional response data from FIRS API
            
        Returns:
            The created status update record
        """
        # Update the main record
        self.status = status
        self.status_message = message
        self.last_updated = datetime.utcnow()
        
        if response_data:
            self.response_data = response_data
        
        # Create a status update record
        status_update = SubmissionStatusUpdate(
            submission_id=self.id,
            status=status,
            message=message,
            response_data=response_data
        )
        
        return status_update


class SubmissionStatusUpdate(Base):
    """
    Tracks individual status updates for a submission.
    
    This model creates an audit trail of all status changes to a submission,
    with timestamps and relevant response data for each update.
    """
    __tablename__ = "submission_status_updates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    submission_id = Column(UUID(as_uuid=True), ForeignKey("submission_records.id"), nullable=False)
    status = Column(SQLEnum(SubmissionStatus), nullable=False)
    message = Column(String(512), nullable=True)
    response_data = Column(JSON, nullable=True)
    timestamp = Column(DateTime, nullable=False, default=func.now())
    
    # Relationships
    submission = relationship("SubmissionRecord", back_populates="status_updates")


class SubmissionNotification(Base):
    """
    Tracks webhook notifications for submission status updates.
    
    This model records the delivery status and details for each webhook
    notification sent for submission status updates.
    """
    __tablename__ = "submission_notifications"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    submission_id = Column(UUID(as_uuid=True), ForeignKey("submission_records.id"), nullable=False)
    status_update_id = Column(UUID(as_uuid=True), ForeignKey("submission_status_updates.id"), nullable=False)
    
    # Notification details
    webhook_url = Column(String(512), nullable=False)
    payload = Column(JSON, nullable=False)
    
    # Status tracking
    status = Column(SQLEnum(NotificationStatus), nullable=False, default=NotificationStatus.PENDING)
    attempts = Column(Integer, nullable=False, default=0)
    last_attempt = Column(DateTime, nullable=True)
    next_attempt = Column(DateTime, nullable=True)
    response_code = Column(Integer, nullable=True)
    response_body = Column(Text, nullable=True)
    error_message = Column(String(512), nullable=True)
    timestamp = Column(DateTime, nullable=False, default=func.now())
    
    # Relationships
    submission = relationship("SubmissionRecord", back_populates="notifications")
