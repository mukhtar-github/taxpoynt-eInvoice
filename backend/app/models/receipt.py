"""
Transmission Receipt Models for TaxPoynt eInvoice Platform.

This module defines models for storing and verifying transmission receipts
from FIRS and other authorities.
"""

import uuid
import enum
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, func, Text, Enum # type: ignore
from sqlalchemy.dialects.postgresql import UUID, JSONB # type: ignore
from sqlalchemy.orm import relationship # type: ignore
from app.db.base import Base # type: ignore


class VerificationStatus(str, enum.Enum):
    """Enumeration of verification statuses for receipts."""
    PENDING = "pending"
    VERIFIED = "verified"
    FAILED = "failed"
    EXPIRED = "expired"


class TransmissionReceipt(Base):
    """
    Model for storing receipts from successful transmissions.
    """
    __tablename__ = "transmission_receipts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transmission_id = Column(UUID(as_uuid=True), ForeignKey("transmission_records.id"), nullable=False, index=True)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    
    # Receipt details
    receipt_id = Column(String(255), nullable=False, unique=True, index=True)
    receipt_timestamp = Column(DateTime, nullable=False, server_default=func.now())
    receipt_data = Column(JSONB)
    
    # Verification details
    verification_status = Column(String(50), default=VerificationStatus.PENDING, index=True)
    verification_timestamp = Column(DateTime)
    verification_result = Column(JSONB)
    
    # Tracking
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    # Relationships
    transmission = relationship("TransmissionRecord", back_populates="receipts")


# Update the TransmissionRecord model with a backref relationship
from app.models.transmission import TransmissionRecord
TransmissionRecord.receipts = relationship("TransmissionReceipt", back_populates="transmission")
