import uuid
from sqlalchemy import Column, String, ForeignKey, DateTime, Text, func, Boolean # type: ignore
from sqlalchemy.dialects.postgresql import UUID # type: ignore
from sqlalchemy.orm import relationship # type: ignore
from app.db.base_class import Base # type: ignore


class FIRSCredentials(Base):
    """
    Model for storing FIRS API credentials with field-level encryption.
    Sensitive fields are encrypted using AES-256-GCM.
    """
    __tablename__ = "firs_credentials"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    api_key = Column(String(255), nullable=False)  # Encrypted FIRS API key
    secret_key = Column(String(255), nullable=False)  # Encrypted FIRS secret key
    service_id = Column(String(8), nullable=False)  # FIRS assigned Service ID
    public_key = Column(Text)  # FIRS provided public key for encryption
    certificate = Column(Text)  # FIRS provided certificate for signing
    encryption_key_id = Column(String(100), ForeignKey("encryption_keys.id"))  # Reference to the key used for encryption
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    status = Column(String(20), nullable=False, default="active")

    # Relationships
    organization = relationship("Organization", back_populates="firs_credentials")
    encryption_key = relationship("EncryptionKey") 