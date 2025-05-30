import uuid
from datetime import datetime
from sqlalchemy import Column, String, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.db.base_class import Base
from app.models.user import UserRole


class Organization(Base):
    """
    Organization model represents a customer organization in the system.
    """
    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    tax_id = Column(String, nullable=True)
    address = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    email = Column(String, nullable=True)
    website = Column(String, nullable=True)
    status = Column(String, default="active", nullable=False)
    firs_service_id = Column(String, nullable=True)
    # New fields for company branding
    logo_url = Column(String, nullable=True)
    branding_settings = Column(JSONB, nullable=True)  # Store UI customization (colors, theme)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, nullable=True)
    
    # Relationships
    api_keys = relationship("APIKey", back_populates="organization", cascade="all, delete-orphan")
    organization_users = relationship("OrganizationUser", back_populates="organization", cascade="all, delete-orphan")
    integrations = relationship("Integration", back_populates="organization", cascade="all, delete-orphan")
    
    # APP-related relationships
    certificates = relationship("Certificate", back_populates="organization", cascade="all, delete-orphan")
    certificate_requests = relationship("CertificateRequest", back_populates="organization", cascade="all, delete-orphan")
    csids = relationship("CSIDRegistry", back_populates="organization", cascade="all, delete-orphan")
    transmissions = relationship("TransmissionRecord", back_populates="organization", cascade="all, delete-orphan")
    encryption_keys = relationship("EncryptionKey", back_populates="organization")
    encryption_config = relationship("EncryptionConfig", back_populates="organization", uselist=False)
    

class OrganizationUser(Base):
    """
    OrganizationUser model represents the many-to-many relationship between users and organizations,
    including the role of the user within the organization.
    """
    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organization.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    role = Column(String, default=UserRole.MEMBER.value, nullable=False)  # Role within the organization
    is_primary = Column(Boolean, default=False, nullable=False)  # Is this the primary organization for the user
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, nullable=True)
    
    # Relationships
    organization = relationship("Organization", back_populates="organization_users")
    user = relationship("User", back_populates="organization_users")
