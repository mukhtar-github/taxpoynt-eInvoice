"""
Certificate storage model for TaxPoynt eInvoice system.

This module defines models for storing digital certificates securely,
with support for certificate metadata and encrypted content.
"""

import uuid
import enum
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, func, JSON, Text, LargeBinary # type: ignore
from sqlalchemy.dialects.postgresql import UUID, JSONB # type: ignore
from sqlalchemy.orm import relationship # type: ignore
from app.db.base import Base # type: ignore


class CertificateType(str, enum.Enum):
    """Enumeration of certificate types."""
    X509 = "x509"
    PEM = "pem"
    DER = "der"
    PKCS12 = "pkcs12"
    JKS = "jks"
    OTHER = "other"


class CertificateStatus(str, enum.Enum):
    """Enumeration of certificate statuses."""
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    PENDING = "pending"


class Certificate(Base):
    """
    Model for storing certificate metadata and encrypted content.
    """
    __tablename__ = "certificates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(String(500))
    certificate_type = Column(String(20), nullable=False, default=CertificateType.X509)
    
    # Metadata fields
    issuer = Column(String(255))
    subject = Column(String(255))
    serial_number = Column(String(100))
    fingerprint = Column(String(100))
    valid_from = Column(DateTime)
    valid_to = Column(DateTime)
    status = Column(String(20), default=CertificateStatus.ACTIVE)
    
    # Certificate content - stored encrypted
    certificate_data = Column(Text)
    is_encrypted = Column(Boolean, default=True, nullable=False)
    encryption_key_id = Column(String(100), ForeignKey("encryption_keys.id"))
    
    # Private key - stored encrypted separately for additional security
    private_key_data = Column(Text)
    has_private_key = Column(Boolean, default=False)
    
    # Additional metadata
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    last_used_at = Column(DateTime)
    tags = Column(JSONB)
    
    # Relationships
    organization = relationship("Organization", back_populates="certificates")
    encryption_key = relationship("EncryptionKey")
    created_by_user = relationship("User", foreign_keys=[created_by])
    revocation = relationship("CertificateRevocation", back_populates="certificate", uselist=False)
    
    def get_metadata(self) -> dict:
        """Get certificate metadata as a dictionary"""
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "certificate_type": self.certificate_type,
            "issuer": self.issuer,
            "subject": self.subject,
            "serial_number": self.serial_number,
            "fingerprint": self.fingerprint,
            "valid_from": self.valid_from.isoformat() if self.valid_from else None,
            "valid_to": self.valid_to.isoformat() if self.valid_to else None,
            "status": self.status,
            "has_private_key": self.has_private_key,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
            "organization_id": str(self.organization_id),
            "revoked": hasattr(self, 'revocation') and self.revocation is not None,
        }
    
    def is_valid(self) -> bool:
        """Check if certificate is valid (not expired, not revoked)"""
        now = datetime.utcnow()
        
        # Check if certificate is active
        if self.status != CertificateStatus.ACTIVE:
            return False
        
        # Check if certificate is revoked
        if hasattr(self, 'revocation') and self.revocation is not None:
            return False
        
        # Check if certificate is expired
        if self.valid_to and self.valid_to < now:
            return False
        
        # Check if certificate is not yet valid
        if self.valid_from and self.valid_from > now:
            return False
            
        return True


class CertificateRevocation(Base):
    """
    Model for tracking certificate revocations.
    """
    __tablename__ = "certificate_revocations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    certificate_id = Column(UUID(as_uuid=True), ForeignKey("certificates.id"), nullable=False)
    revoked_at = Column(DateTime, nullable=False, server_default=func.now())
    revoked_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    reason = Column(String(255))
    
    # Relationships
    certificate = relationship("Certificate", back_populates="revocation")
    revoked_by_user = relationship("User")
