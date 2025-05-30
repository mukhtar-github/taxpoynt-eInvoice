"""
Certificate request model for TaxPoynt eInvoice APP functionality.

This module defines models for storing certificate signing requests (CSRs)
and tracking their status through the request lifecycle.
"""

import uuid
import enum
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, func, JSON, Text # type: ignore
from sqlalchemy.dialects.postgresql import UUID, JSONB # type: ignore
from sqlalchemy.orm import relationship # type: ignore
from app.db.base import Base # type: ignore


class CertificateRequestType(str, enum.Enum):
    """Enumeration of certificate request types."""
    NEW = "new"
    RENEWAL = "renewal"
    REPLACEMENT = "replacement"
    REVOCATION = "revocation"


class CertificateRequestStatus(str, enum.Enum):
    """Enumeration of certificate request statuses."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    ISSUED = "issued"
    CANCELED = "canceled"
    ERROR = "error"


class CertificateRequest(Base):
    """
    Model for storing certificate signing requests (CSRs) and tracking their status.
    """
    __tablename__ = "certificate_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    request_type = Column(String(50), nullable=False, default=CertificateRequestType.NEW)
    
    # CSR data - stored encrypted
    csr_data = Column(Text)
    is_encrypted = Column(Boolean, default=True)
    encryption_key_id = Column(String(100), ForeignKey("encryption_keys.id"))
    
    # Status tracking
    status = Column(String(50), default=CertificateRequestStatus.PENDING, index=True)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Additional metadata
    request_metadata = Column(JSONB)
    
    # Relationships
    organization = relationship("Organization", back_populates="certificate_requests")
    encryption_key = relationship("EncryptionKey")
    created_by_user = relationship("User", foreign_keys=[created_by])
    certificate = relationship("Certificate", back_populates="certificate_request", uselist=False)
    
    def get_metadata(self) -> dict:
        """Get certificate request metadata as a dictionary"""
        return {
            "id": str(self.id),
            "organization_id": str(self.organization_id),
            "request_type": self.request_type,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "created_by": str(self.created_by) if self.created_by else None,
            "metadata": self.request_metadata
        }
