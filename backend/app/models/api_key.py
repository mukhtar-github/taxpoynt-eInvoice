"""API key models for system integration."""
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, ForeignKey, DateTime, Boolean, Text, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship # type: ignore

from app.db.base_class import Base # type: ignore


class APIKey(Base):
    """API key model for system integration authentication."""
    __tablename__ = "api_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # API key (prefix shown to user)
    prefix = Column(String(8), nullable=False, index=True)
    
    # Hashed API key (for security)
    hashed_key = Column(String(255), nullable=False)
    
    # Secret key (prefix shown to user)
    secret_prefix = Column(String(8), nullable=False, index=True)
    
    # Hashed Secret key (for security)
    hashed_secret = Column(String(255), nullable=False)
    
    # API key metadata
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=True)
    last_used_at = Column(DateTime, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Rate limiting
    rate_limit_per_minute = Column(Integer, default=60, nullable=False)
    rate_limit_per_day = Column(Integer, default=10000, nullable=False)
    
    # Usage tracking
    current_minute_requests = Column(Integer, default=0, nullable=False)
    current_day_requests = Column(Integer, default=0, nullable=False)
    last_minute_reset = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_day_reset = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relations
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="api_keys")
    
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    organization = relationship("Organization")
    
    # Allowance for custom permissions
    permissions = Column(Text, nullable=True)  # JSON string of permissions 