"""
CSID registry model for TaxPoynt eInvoice APP functionality.

This module defines models for storing Cryptographic Signature Identifiers (CSIDs)
that are used for cryptographic stamping of e-invoices.
"""

import uuid
import enum
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, func, Text # type: ignore
from sqlalchemy.dialects.postgresql import UUID, JSONB # type: ignore
from sqlalchemy.orm import relationship # type: ignore
from app.db.base import Base # type: ignore


class CSIDStatus(str, enum.Enum):
    """Enumeration of CSID statuses."""
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    PENDING = "pending"


class CSIDRegistry(Base):
    """
    Model for storing Cryptographic Signature Identifiers (CSIDs) and their status.
    """
    __tablename__ = "csid_registry"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    csid = Column(String(100), nullable=False, unique=True)
    certificate_id = Column(UUID(as_uuid=True), ForeignKey("certificates.id"), index=True)
    
    # Timestamps and lifecycle
    creation_time = Column(DateTime, nullable=False, server_default=func.now())
    expiration_time = Column(DateTime)
    is_active = Column(Boolean, default=True, index=True)
    revocation_time = Column(DateTime)
    revocation_reason = Column(String(255))
    
    # Additional metadata
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    metadata = Column(JSONB)
    
    # Relationships
    organization = relationship("Organization", back_populates="csids")
    certificate = relationship("Certificate", back_populates="csids")
    created_by_user = relationship("User", foreign_keys=[created_by])
    
    def get_metadata(self) -> dict:
        """Get CSID metadata as a dictionary"""
        return {
            "id": str(self.id),
            "organization_id": str(self.organization_id),
            "csid": self.csid,
            "certificate_id": str(self.certificate_id) if self.certificate_id else None,
            "creation_time": self.creation_time.isoformat() if self.creation_time else None,
            "expiration_time": self.expiration_time.isoformat() if self.expiration_time else None,
            "is_active": self.is_active,
            "revocation_time": self.revocation_time.isoformat() if self.revocation_time else None,
            "revocation_reason": self.revocation_reason,
            "created_by": str(self.created_by) if self.created_by else None,
            "metadata": self.metadata
        }
    
    def get_status(self) -> CSIDStatus:
        """Get the current status of the CSID"""
        if not self.is_active:
            if self.revocation_time:
                return CSIDStatus.REVOKED
            return CSIDStatus.PENDING
        
        now = datetime.utcnow()
        if self.expiration_time and self.expiration_time < now:
            return CSIDStatus.EXPIRED
            
        return CSIDStatus.ACTIVE
