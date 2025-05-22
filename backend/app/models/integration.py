import uuid
import enum
from sqlalchemy import Column, String, ForeignKey, DateTime, Text, func, Boolean, Enum # type: ignore
from sqlalchemy.dialects.postgresql import UUID, JSONB # type: ignore
from sqlalchemy.orm import relationship # type: ignore
from app.db.base import Base # type: ignore


class IntegrationType(str, enum.Enum):
    ODOO = "odoo"
    CUSTOM = "custom"
    # More integration types can be added here as needed


class Integration(Base):
    __tablename__ = "integrations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(UUID(as_uuid=True), ForeignKey("clients.id"), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    integration_type = Column(Enum(IntegrationType), nullable=False, default=IntegrationType.CUSTOM)
    config = Column(JSONB, nullable=False)
    config_encrypted = Column(Boolean, nullable=False, default=False)  # Flag to indicate if config is encrypted
    encryption_key_id = Column(String(100), ForeignKey("encryption_keys.id"))  # Reference to the key used for encryption
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    last_tested = Column(DateTime)
    status = Column(String(20), nullable=False, default="configured")
    sync_frequency = Column(String(20), default="hourly")  # hourly, daily, realtime
    last_sync = Column(DateTime)
    next_sync = Column(DateTime)

    # Relationships
    client = relationship("Client", back_populates="integrations")
    history = relationship("IntegrationHistory", back_populates="integration")
    irn_records = relationship("IRNRecord", back_populates="integration")
    submission_records = relationship("SubmissionRecord", back_populates="integration")
    encryption_key = relationship("EncryptionKey")


class IntegrationHistory(Base):
    __tablename__ = "integration_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    integration_id = Column(UUID(as_uuid=True), ForeignKey("integrations.id"), nullable=False)
    changed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    previous_config = Column(JSONB)
    previous_config_encrypted = Column(Boolean, nullable=False, default=False)
    new_config = Column(JSONB, nullable=False)
    new_config_encrypted = Column(Boolean, nullable=False, default=False)
    encryption_key_id = Column(String(100), ForeignKey("encryption_keys.id"))
    changed_at = Column(DateTime, nullable=False, server_default=func.now())
    change_reason = Column(String(255))

    # Relationships
    integration = relationship("Integration", back_populates="history")
    encryption_key = relationship("EncryptionKey")