import uuid # type: ignore
from sqlalchemy import Column, String, Text, Boolean, TIMESTAMP, JSON, ForeignKey, UUID # type: ignore
from sqlalchemy.sql import func # type: ignore  

from app.db.base_class import Base # type: ignore


class ValidationRule(Base):
    __tablename__ = "validation_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    rule_type = Column(String(50), nullable=False)  # schema, business_logic, format
    field_path = Column(String(255), nullable=True)
    validation_logic = Column(JSON, nullable=False)
    error_message = Column(Text, nullable=False)
    severity = Column(String(20), nullable=False, default="error")  # error, warning, info
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)
    active = Column(Boolean, nullable=False, default=True)


class ValidationRecord(Base):
    __tablename__ = "validation_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    integration_id = Column(UUID(as_uuid=True), ForeignKey("integrations.id"), nullable=False)
    irn = Column(String(50), ForeignKey("irn_records.irn"), nullable=True)
    invoice_data = Column(JSON, nullable=False)
    is_valid = Column(Boolean, nullable=False)
    validation_time = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    issues = Column(JSON, nullable=True)
    external_id = Column(String(100), nullable=True) 