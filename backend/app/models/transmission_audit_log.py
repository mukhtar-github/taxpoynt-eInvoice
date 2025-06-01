"""
Transmission audit logging model for comprehensive operational tracking.

This module defines models for tracking all transmission-related operations
for security auditing, compliance, and troubleshooting.
"""

import uuid
import enum
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, JSON, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.db.base import Base


class AuditActionType(str, enum.Enum):
    """Enumeration of audit action types."""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    RETRY = "retry"
    WEBHOOK = "webhook"
    EXPORT = "export"
    SIGN = "sign"
    ENCRYPT = "encrypt"
    DECRYPT = "decrypt"
    VERIFY = "verify"
    OTHER = "other"


class TransmissionAuditLog(Base):
    """
    Model for comprehensive audit logging of transmission operations.
    """
    __tablename__ = "transmission_audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transmission_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("transmission_records.id", ondelete="SET NULL"), 
        nullable=True,  # Can be NULL for system-wide operations
        index=True
    )
    
    # Action information
    action_type = Column(String(50), nullable=False, index=True)
    action_timestamp = Column(DateTime, nullable=False, server_default=func.now(), index=True)
    action_status = Column(String(50), nullable=False, default="success")
    
    # User and system info
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(255), nullable=True)
    
    # Organization context
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True)
    
    # Detailed information
    resource_path = Column(String(255), nullable=True)  # API endpoint or resource identifier
    request_method = Column(String(10), nullable=True)  # HTTP method
    request_body = Column(JSONB, nullable=True)         # Request data (sanitized)
    response_code = Column(Integer, nullable=True)      # HTTP response code
    error_message = Column(Text, nullable=True)         # Error details if applicable
    
    # Additional context
    context_data = Column(JSONB, nullable=True)         # Any additional contextual info
    
    # Relationships
    transmission = relationship("TransmissionRecord")
    user = relationship("User")
    organization = relationship("Organization")
    
    def __repr__(self):
        return f"<TransmissionAuditLog(id={self.id}, action={self.action_type}, " \
               f"timestamp={self.action_timestamp}, status={self.action_status})>"
