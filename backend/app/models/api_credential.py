"""API credential storage models."""
import uuid
from enum import Enum
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Enum as SQLAlchemyEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base_class import Base


class CredentialType(str, Enum):
    """Enum of credential types."""
    FIRS = "firs"
    ODOO = "odoo"
    OTHER = "other"


class ApiCredential(Base):
    """Secure API credential storage."""
    __tablename__ = "api_credentials"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(String(255), nullable=True)
    credential_type = Column(SQLAlchemyEnum(CredentialType), nullable=False)
    
    # Encrypted credentials
    client_id = Column(String, nullable=True)
    client_secret = Column(String, nullable=True)
    api_key = Column(String, nullable=True)
    api_secret = Column(String, nullable=True)
    
    # Additional encrypted configuration specific to the service
    additional_config = Column(String, nullable=True)
    
    # Metadata
    is_encrypted = Column(Boolean, default=True, nullable=False)
    encryption_key_id = Column(String(100), ForeignKey("encryption_keys.id"), nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    organization = relationship("Organization", back_populates="api_credentials")
    created_by_user = relationship("User")
    encryption_key = relationship("EncryptionKey")


# Update Organization model to include this relationship
from app.models.user import Organization
Organization.api_credentials = relationship("ApiCredential", back_populates="organization")
