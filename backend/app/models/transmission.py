"""
Transmission records model for TaxPoynt eInvoice APP functionality.

This module defines models for securely tracking and managing
encrypted transmissions to FIRS and other authorities.
"""

import uuid
import enum
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, func, Text # type: ignore
from sqlalchemy.dialects.postgresql import UUID, JSONB # type: ignore
from sqlalchemy.orm import relationship # type: ignore
from app.db.base import Base # type: ignore


class TransmissionStatus(str, enum.Enum):
    """Enumeration of transmission statuses."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    CANCELED = "canceled"


class TransmissionRecord(Base):
    """
    Model for tracking secure transmissions of invoices and other documents.
    """
    __tablename__ = "transmission_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    certificate_id = Column(UUID(as_uuid=True), ForeignKey("certificates.id"), index=True)
    submission_id = Column(UUID(as_uuid=True), ForeignKey("submissions.id"), index=True)
    
    # Transmission details
    transmission_time = Column(DateTime, nullable=False, server_default=func.now())
    status = Column(String(50), default=TransmissionStatus.PENDING, index=True)
    encrypted_payload = Column(Text)
    encryption_metadata = Column(JSONB)
    response_data = Column(JSONB)
    
    # Retry information
    retry_count = Column(Integer, default=0)
    last_retry_time = Column(DateTime)
    
    # Additional metadata
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    transmission_metadata = Column(JSONB)
    
    # Relationships
    organization = relationship("Organization", back_populates="transmissions")
    certificate = relationship("Certificate")
    submission = relationship("Submission", back_populates="transmissions")
    created_by_user = relationship("User", foreign_keys=[created_by])
    
    def get_metadata(self) -> dict:
        """Get transmission metadata as a dictionary"""
        return {
            "id": str(self.id),
            "organization_id": str(self.organization_id),
            "certificate_id": str(self.certificate_id) if self.certificate_id else None,
            "submission_id": str(self.submission_id) if self.submission_id else None,
            "transmission_time": self.transmission_time.isoformat() if self.transmission_time else None,
            "status": self.status,
            "retry_count": self.retry_count,
            "last_retry_time": self.last_retry_time.isoformat() if self.last_retry_time else None,
            "created_by": str(self.created_by) if self.created_by else None,
            "metadata": self.transmission_metadata
        }
    
    def can_retry(self, max_retries: int = 3) -> bool:
        """Check if transmission can be retried"""
        if self.status not in [TransmissionStatus.FAILED, TransmissionStatus.PENDING]:
            return False
            
        if self.retry_count >= max_retries:
            return False
            
        return True
