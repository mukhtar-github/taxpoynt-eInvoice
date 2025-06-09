from sqlalchemy import Boolean, Column, Integer, String, Enum, ForeignKey, DateTime, UUID # type: ignore
import enum
from app.db.base_class import Base
from sqlalchemy.sql import func # type: ignore
from sqlalchemy.orm import relationship # type: ignore
import uuid
from app.models.user_role import UserRole

# Import models to avoid circular import issues
# These are forward references to break the circular dependencies
from app.models.certificate import Certificate as CertificateModel
from app.models.encryption import EncryptionKey, EncryptionConfig
from app.models.firs_credentials import FIRSCredentials
from app.models.organization import Organization, OrganizationUser as OrgUser



class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    is_active = Column(Boolean, default=True)
    role = Column(Enum(UserRole), default=UserRole.SI_USER)
    
    # Email verification
    is_email_verified = Column(Boolean, default=False)
    email_verification_token = Column(String, nullable=True)
    email_verification_sent_at = Column(DateTime(timezone=True), nullable=True)
    
    # Password reset
    password_reset_token = Column(String, nullable=True)
    password_reset_at = Column(DateTime(timezone=True), nullable=True)
    password_reset_expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    api_keys = relationship("APIKey", back_populates="user")


# Organization and OrganizationUser models are now in organization.py