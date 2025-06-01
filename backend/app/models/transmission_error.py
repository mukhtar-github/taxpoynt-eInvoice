"""
Transmission error reporting models for TaxPoynt eInvoice Platform functionality.

This module defines models for detailed error tracking, categorization,
and reporting of transmission errors to support troubleshooting and analysis.
"""

import uuid
import enum
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Integer, func, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.db.base import Base


class ErrorSeverity(str, enum.Enum):
    """Enumeration of error severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ErrorCategory(str, enum.Enum):
    """Enumeration of error categories."""
    NETWORK = "network"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    VALIDATION = "validation"
    ENCRYPTION = "encryption"
    SIGNATURE = "signature"
    TIMEOUT = "timeout"
    SYSTEM = "system"
    INTEGRATION = "integration"
    OTHER = "other"


class TransmissionError(Base):
    """
    Model for detailed tracking of transmission errors.
    """
    __tablename__ = "transmission_errors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transmission_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("transmission_records.id", ondelete="CASCADE"),
        nullable=False, 
        index=True
    )
    
    # Error information
    error_time = Column(DateTime, nullable=False, server_default=func.now(), index=True)
    error_message = Column(Text, nullable=False)
    error_code = Column(String(50), nullable=True)
    error_category = Column(String(50), default=ErrorCategory.OTHER)
    severity = Column(String(50), default=ErrorSeverity.MEDIUM)
    
    # Error context
    operation_phase = Column(String(50))  # e.g., "encryption", "transmission", "receipt-verification"
    error_details = Column(JSONB)
    stack_trace = Column(Text, nullable=True)
    
    # Resolution tracking
    is_resolved = Column(Boolean, default=False)
    resolved_time = Column(DateTime, nullable=True)
    resolution_notes = Column(Text, nullable=True)
    resolution_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Retry information
    retry_attempted = Column(Boolean, default=False)
    retry_count = Column(Integer, default=0)
    last_retry_time = Column(DateTime, nullable=True)
    retry_successful = Column(Boolean, nullable=True)
    
    # Relationships
    transmission = relationship("TransmissionRecord", back_populates="errors")
    resolution_user = relationship("User", foreign_keys=[resolution_user_id])
    
    def __repr__(self):
        return f"<TransmissionError(id={self.id}, transmission_id={self.transmission_id}, " \
               f"category={self.error_category}, severity={self.severity}, resolved={self.is_resolved})>"
