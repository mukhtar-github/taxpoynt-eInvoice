from sqlalchemy import Column, String, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from uuid import uuid4

from app.db.base_class import Base


class IRNRecord(Base):
    __tablename__ = "irn_records"

    irn = Column(String(50), primary_key=True, index=True)
    integration_id = Column(String(36), ForeignKey("integrations.id"), nullable=False)
    invoice_number = Column(String(50), nullable=False, index=True)
    service_id = Column(String(8), nullable=False)
    timestamp = Column(String(8), nullable=False)
    generated_at = Column(DateTime, nullable=False, default=func.now())
    valid_until = Column(DateTime, nullable=False)
    metadata = Column(JSON, nullable=True)
    status = Column(String(20), nullable=False, default="unused")
    used_at = Column(DateTime, nullable=True)
    invoice_id = Column(String(50), nullable=True)

    # Relationships
    integration = relationship("Integration", back_populates="irn_records") 