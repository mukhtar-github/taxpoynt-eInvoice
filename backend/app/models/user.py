from sqlalchemy import Boolean, Column, Integer, String, Enum, ForeignKey, DateTime, UUID # type: ignore
import enum
from datetime import datetime
from typing import List
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
    created_invoices = relationship("Invoice", back_populates="creator")
    organization_users = relationship("OrganizationUser", back_populates="user", cascade="all, delete-orphan")
    
    # Service access relationships
    service_access = relationship("UserServiceAccess", foreign_keys="UserServiceAccess.user_id", back_populates="user", cascade="all, delete-orphan")
    
    def has_service_access(self, service_type, access_level="read") -> bool:
        """Check if user has access to a specific service with required level"""
        from app.models.user_service_access import ServiceType, AccessLevel, has_required_access_level
        
        # Convert string inputs to enums if needed
        if isinstance(service_type, str):
            service_type = ServiceType(service_type)
        if isinstance(access_level, str):
            access_level = AccessLevel(access_level)
        
        for access in self.service_access:
            if (access.service_type == service_type and 
                access.is_active and 
                (access.expires_at is None or access.expires_at > datetime.utcnow()) and
                has_required_access_level(access.access_level, access_level)):
                return True
        return False
    
    def get_accessible_services(self) -> List:
        """Get list of services user can access"""
        from app.models.user_service_access import ServiceType
        
        services = []
        for access in self.service_access:
            if (access.is_active and 
                (access.expires_at is None or access.expires_at > datetime.utcnow())):
                services.append(access.service_type)
        return list(set(services))
    
    def get_service_access_level(self, service_type) -> str:
        """Get the highest access level for a specific service"""
        from app.models.user_service_access import ServiceType, AccessLevel, ACCESS_LEVEL_HIERARCHY
        
        if isinstance(service_type, str):
            service_type = ServiceType(service_type)
        
        highest_level = None
        highest_level_value = 0
        
        for access in self.service_access:
            if (access.service_type == service_type and 
                access.is_active and 
                (access.expires_at is None or access.expires_at > datetime.utcnow())):
                level_value = ACCESS_LEVEL_HIERARCHY[access.access_level]
                if level_value > highest_level_value:
                    highest_level = access.access_level
                    highest_level_value = level_value
        
        return highest_level.value if highest_level else None


# Organization and OrganizationUser models are now in organization.py