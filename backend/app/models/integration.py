import uuid
from sqlalchemy import Column, String, ForeignKey, DateTime, Text, func # type: ignore
from sqlalchemy.dialects.postgresql import UUID, JSONB # type: ignore
from sqlalchemy.orm import relationship # type: ignore
from app.db.base import Base # type: ignore


class Integration(Base):
    __tablename__ = "integrations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(UUID(as_uuid=True), ForeignKey("clients.id"), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    config = Column(JSONB, nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    last_tested = Column(DateTime)
    status = Column(String(20), nullable=False, default="configured")

    # Relationships
    client = relationship("Client", back_populates="integrations")
    history = relationship("IntegrationHistory", back_populates="integration")


class IntegrationHistory(Base):
    __tablename__ = "integration_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    integration_id = Column(UUID(as_uuid=True), ForeignKey("integrations.id"), nullable=False)
    changed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    previous_config = Column(JSONB)
    new_config = Column(JSONB, nullable=False)
    changed_at = Column(DateTime, nullable=False, server_default=func.now())
    change_reason = Column(String(255))

    # Relationships
    integration = relationship("Integration", back_populates="history") 