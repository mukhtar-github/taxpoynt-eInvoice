"""
Transmission status logging model for detailed status tracking.

This module defines models for tracking status changes in transmission records
with timestamps and contextual information.
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, func, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.transmission import TransmissionStatus


class TransmissionStatusLog(Base):
    """
    Model for logging status changes in transmission records.
    """
    __tablename__ = "transmission_status_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transmission_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("transmission_records.id", ondelete="CASCADE"), 
        nullable=False, 
        index=True
    )
    
    # Status information
    previous_status = Column(String(50), nullable=True)
    current_status = Column(String(50), nullable=False)
    status_timestamp = Column(DateTime, nullable=False, server_default=func.now())
    
    # Status change context
    change_reason = Column(String(255))
    change_source = Column(String(50))  # 'system', 'webhook', 'user', 'retry_worker'
    change_detail = Column(JSONB)
    
    # Performance tracking
    processing_time_ms = Column(Integer, nullable=True)  # Time taken to process this status change
    
    # Relationships
    transmission = relationship("TransmissionRecord", back_populates="status_logs")
    
    def __repr__(self):
        return f"<TransmissionStatusLog(id={self.id}, transmission_id={self.transmission_id}, " \
               f"status={self.current_status}, timestamp={self.status_timestamp})>"
