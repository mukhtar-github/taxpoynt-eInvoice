import uuid
from sqlalchemy import Column, String, ForeignKey, DateTime, Boolean, Integer, func # type: ignore
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