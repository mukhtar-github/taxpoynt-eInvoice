import uuid
from datetime import datetime
from sqlalchemy import Column, String, ForeignKey, DateTime, Boolean, Integer, Text, func # type: ignore
from sqlalchemy.dialects.postgresql import UUID # type: ignore
from sqlalchemy.orm import relationship # type: ignore
from app.db.base import Base # type: ignore


class APIKey(Base):
    """
    Model for storing API keys with field-level encryption.
    Supports both the original encryption-based model and the newer hashing-based model.
    """
    __tablename__ = "api_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    
    # Key can be either encrypted or hashed based on implementation needs
    key = Column(String(255), nullable=True)  # Encrypted API key (legacy approach)
    hashed_key = Column(String(255), nullable=True)  # Hashed API key (newer approach)
    
    # Prefix for display to user
    prefix = Column(String(10), nullable=False, unique=True)
    
    # Secret key fields (for two-factor API authentication)
    secret_prefix = Column(String(8), nullable=True)  # For secret key display
    hashed_secret = Column(String(255), nullable=True)  # Hashed secret key
    
    # Encryption reference
    encryption_key_id = Column(String(100), ForeignKey("encryption_keys.id"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    expires_at = Column(DateTime, nullable=True)
    last_used = Column(DateTime, nullable=True)
    last_used_at = Column(DateTime, nullable=True)  # Duplicate field for backward compatibility
    
    # Status
    status = Column(String(20), nullable=False, default="active")
    is_active = Column(Boolean, default=True, nullable=False)  # Duplicate field for backward compatibility
    
    # Rate limiting
    rate_limit_per_minute = Column(Integer, default=60, nullable=True)
    rate_limit_per_day = Column(Integer, default=10000, nullable=True)
    current_minute_requests = Column(Integer, default=0, nullable=True)
    current_day_requests = Column(Integer, default=0, nullable=True)
    last_minute_reset = Column(DateTime, default=datetime.utcnow, nullable=True)
    last_day_reset = Column(DateTime, default=datetime.utcnow, nullable=True)
    
    # Permissions
    permissions = Column(Text, nullable=True)  # JSON string of permissions

    # Relationships
    user = relationship("User", back_populates="api_keys")
    organization = relationship("Organization", back_populates="api_keys")
    encryption_key = relationship("EncryptionKey")
    usage_records = relationship("APIKeyUsage", back_populates="api_key")


class APIKeyUsage(Base):
    """
    Model for tracking API key usage statistics.
    Records endpoint access, resource consumption, and rate limiting.
    """
    __tablename__ = "api_key_usage"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    api_key_id = Column(UUID(as_uuid=True), ForeignKey("api_keys.id"), nullable=False)
    endpoint = Column(String(255), nullable=False)  # The API endpoint that was accessed
    method = Column(String(10), nullable=False)  # HTTP method used (GET, POST, etc.)
    status_code = Column(Integer, nullable=False)  # HTTP status code of the response
    response_time_ms = Column(Integer)  # Response time in milliseconds
    request_size_bytes = Column(Integer)  # Size of the request in bytes
    response_size_bytes = Column(Integer)  # Size of the response in bytes
    timestamp = Column(DateTime, nullable=False, server_default=func.now())
    ip_address = Column(String(45))  # IPv4 or IPv6 address of the client
    user_agent = Column(String(255))  # User agent of the client
    
    # Relationships
    api_key = relationship("APIKey", back_populates="usage_records")