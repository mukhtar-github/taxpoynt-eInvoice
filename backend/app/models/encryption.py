import uuid
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, func, Integer # type: ignore
from sqlalchemy.dialects.postgresql import UUID, JSONB # type: ignore
from sqlalchemy.orm import relationship # type: ignore
from app.db.base import Base # type: ignore


class EncryptionKey(Base):
    """
    Model for storing encryption key metadata.
    Note: The actual key material is NOT stored in this table.
    """
    __tablename__ = "encryption_keys"

    id = Column(String(100), primary_key=True)  # key ID (e.g., key_20250426123045_a1b2c3)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"))
    name = Column(String(255), nullable=False)
    description = Column(String(255))
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    rotation_date = Column(DateTime)  # Scheduled rotation date
    last_used = Column(DateTime)
    active = Column(Boolean, nullable=False, default=True)
    key_metadata = Column(JSONB)  # Additional metadata (e.g., key type, purpose)

    # Relationships
    organization = relationship("Organization", back_populates="encryption_keys")


class EncryptionConfig(Base):
    """
    Model for storing encryption configuration.
    """
    __tablename__ = "encryption_configs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    key_rotation_days = Column(Integer, nullable=False, default=90)  # Days between key rotations
    encryption_algorithm = Column(String(50), nullable=False, default="AES-256-GCM")
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    settings = Column(JSONB)  # Additional encryption settings

    # Relationships
    organization = relationship("Organization", back_populates="encryption_config") 