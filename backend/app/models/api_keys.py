import uuid
from sqlalchemy import Column, String, ForeignKey, DateTime, Boolean, func # type: ignore
from sqlalchemy.dialects.postgresql import UUID # type: ignore
from sqlalchemy.orm import relationship # type: ignore
from app.db.base import Base # type: ignore


class APIKey(Base):
    """
    Model for storing API keys with field-level encryption.
    The key field is encrypted using AES-256-GCM.
    """
    __tablename__ = "api_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    name = Column(String(100), nullable=False)
    key = Column(String(255), nullable=False)  # Encrypted API key
    prefix = Column(String(10), nullable=False, unique=True)  # Unencrypted prefix for display
    encryption_key_id = Column(String(100), ForeignKey("encryption_keys.id"))  # Reference to the key used for encryption
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    expires_at = Column(DateTime)
    last_used = Column(DateTime)
    status = Column(String(20), nullable=False, default="active")

    # Relationships
    user = relationship("User", back_populates="api_keys")
    organization = relationship("Organization", back_populates="api_keys")
    encryption_key = relationship("EncryptionKey") 