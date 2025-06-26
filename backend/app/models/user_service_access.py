"""
User Service Access Models

This module contains models for implementing service-based user permissions,
allowing users to have granular access to different TaxPoynt services.
"""

import uuid
from datetime import datetime
from enum import Enum as PyEnum
from typing import List

from sqlalchemy import Column, String, ForeignKey, DateTime, Boolean, Enum, func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID

from app.db.base_class import Base


class ServiceType(PyEnum):
    """Types of services TaxPoynt provides"""
    SYSTEM_INTEGRATION = "system_integration"      # ERP/CRM integrations
    ACCESS_POINT_PROVIDER = "access_point_provider" # FIRS e-invoicing
    NIGERIAN_COMPLIANCE = "nigerian_compliance"     # Regulatory monitoring
    ORGANIZATION_MANAGEMENT = "organization_management" # Admin functions


class AccessLevel(PyEnum):
    """Access levels for each service"""
    READ = "read"           # View only
    WRITE = "write"         # Create/modify
    ADMIN = "admin"         # Full control
    OWNER = "owner"         # TaxPoynt executives only


class UserServiceAccess(Base):
    """Many-to-many relationship: Users can access multiple services with different permissions"""
    __tablename__ = "user_service_access"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    service_type = Column(Enum(ServiceType), nullable=False)
    access_level = Column(Enum(AccessLevel), nullable=False)
    
    # Audit fields
    granted_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    granted_at = Column(DateTime, default=func.now(), nullable=False)
    expires_at = Column(DateTime, nullable=True)  # Optional expiration
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Additional metadata
    notes = Column(String, nullable=True)  # Reason for granting access
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, onupdate=func.now(), nullable=True)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="service_access")
    granted_by_user = relationship("User", foreign_keys=[granted_by])


class ServiceAccessAuditLog(Base):
    """Audit log for service access changes"""
    __tablename__ = "service_access_audit_log"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_service_access_id = Column(UUID(as_uuid=True), ForeignKey("user_service_access.id"), nullable=False)
    action = Column(String(50), nullable=False)  # granted, revoked, modified, expired
    
    # Who made the change
    changed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    change_reason = Column(String, nullable=True)
    
    # What changed
    old_values = Column(String, nullable=True)  # JSON string of old values
    new_values = Column(String, nullable=True)  # JSON string of new values
    
    # When
    timestamp = Column(DateTime, default=func.now(), nullable=False)
    
    # Relationships
    service_access = relationship("UserServiceAccess")
    changed_by_user = relationship("User")


# Access level hierarchy for permission checking
ACCESS_LEVEL_HIERARCHY = {
    AccessLevel.READ: 1,
    AccessLevel.WRITE: 2,
    AccessLevel.ADMIN: 3,
    AccessLevel.OWNER: 4
}


def has_required_access_level(user_level: AccessLevel, required_level: AccessLevel) -> bool:
    """Check if user's access level meets or exceeds required level"""
    return ACCESS_LEVEL_HIERARCHY[user_level] >= ACCESS_LEVEL_HIERARCHY[required_level]


# Service descriptions for frontend display
SERVICE_DESCRIPTIONS = {
    ServiceType.SYSTEM_INTEGRATION: {
        "name": "System Integration",
        "description": "ERP and CRM integration services including Odoo, SAP, Salesforce, and HubSpot connections",
        "features": ["ERP Integration", "CRM Sync", "Data Mapping", "Webhook Management"]
    },
    ServiceType.ACCESS_POINT_PROVIDER: {
        "name": "e-Invoicing (APP)",
        "description": "FIRS-certified Access Point Provider services for electronic invoicing and tax compliance",
        "features": ["IRN Generation", "FIRS Submission", "Invoice Validation", "Tax Calculation"]
    },
    ServiceType.NIGERIAN_COMPLIANCE: {
        "name": "Nigerian Compliance",
        "description": "Regulatory compliance monitoring for NITDA, NDPR, and other Nigerian requirements",
        "features": ["NITDA Tracking", "NDPR Compliance", "Regulatory Reporting", "Penalty Management"]
    },
    ServiceType.ORGANIZATION_MANAGEMENT: {
        "name": "Organization Management",
        "description": "Administrative functions for managing organizations, users, and platform settings",
        "features": ["User Management", "Role Assignment", "Organization Settings", "Audit Logs"]
    }
}