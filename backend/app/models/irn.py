from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, Integer, Boolean, Float, Enum # type: ignore
from sqlalchemy.sql import func # type: ignore
from sqlalchemy.orm import relationship # type: ignore
from sqlalchemy.dialects.postgresql import UUID # type: ignore
import enum
from uuid import uuid4
from datetime import datetime, timedelta

from app.db.base_class import Base # type: ignore


class IRNStatus(str, enum.Enum):
    UNUSED = "unused"
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    INVALID = "invalid"


class IRNRecord(Base):
    __tablename__ = "irn_records"

    irn = Column(String(50), primary_key=True, index=True)
    integration_id = Column(String(36), ForeignKey("integrations.id"), nullable=False)
    invoice_number = Column(String(50), nullable=False, index=True)
    service_id = Column(String(8), nullable=False)
    timestamp = Column(String(8), nullable=False)
    generated_at = Column(DateTime, nullable=False, default=func.now())
    valid_until = Column(DateTime, nullable=False)
    meta_data = Column(JSON, nullable=True)
    status = Column(Enum(IRNStatus, values_callable=lambda obj: [e.value for e in obj]), nullable=False, default=IRNStatus.UNUSED)
    used_at = Column(DateTime, nullable=True)
    invoice_id = Column(String(50), nullable=True)
    hash_value = Column(String(128), nullable=True)  # For invoice data verification
    verification_code = Column(String(64), nullable=True)  # For IRN validation
    issued_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # New Odoo-specific fields
    odoo_invoice_id = Column(Integer, nullable=True)  # Direct reference to Odoo invoice ID
    
    # Relationships
    integration = relationship("Integration", back_populates="irn_records")
    invoice_data = relationship("InvoiceData", back_populates="irn_record", uselist=False)
    validation_records = relationship("IRNValidationRecord", back_populates="irn_record")
    submission_records = relationship("SubmissionRecord", back_populates="irn_record")
    
    @classmethod
    def create_with_expiry(cls, **kwargs):
        """Factory method to create an IRN record with automatically calculated expiry date"""
        if 'valid_until' not in kwargs:
            # Default expiry is 30 days from generation
            kwargs['valid_until'] = datetime.utcnow() + timedelta(days=30)
        return cls(**kwargs)


class InvoiceData(Base):
    __tablename__ = "invoice_data"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    irn = Column(String(50), ForeignKey("irn_records.irn"), nullable=False, unique=True)
    invoice_number = Column(String(50), nullable=False)
    invoice_date = Column(DateTime, nullable=False)
    customer_name = Column(String(255), nullable=False)
    customer_tax_id = Column(String(50), nullable=True)
    total_amount = Column(Float, nullable=False)
    currency_code = Column(String(3), nullable=False)
    line_items_hash = Column(String(128), nullable=True)  # Hash of line items for verification
    line_items_data = Column(JSON, nullable=True)  # Detailed line items data
    created_at = Column(DateTime, nullable=False, default=func.now())
    
    # Odoo-specific fields
    odoo_partner_id = Column(Integer, nullable=True)
    odoo_currency_id = Column(Integer, nullable=True)
    
    # Relationships
    irn_record = relationship("IRNRecord", back_populates="invoice_data")


class IRNValidationRecord(Base):
    __tablename__ = "irn_validation_records"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    irn = Column(String(50), ForeignKey("irn_records.irn"), nullable=False)
    validation_date = Column(DateTime, nullable=False, default=func.now())
    validation_status = Column(Boolean, nullable=False)
    validation_message = Column(String(512), nullable=True)
    validated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    validation_source = Column(String(50), nullable=False, default="system")  # system, api, user
    request_data = Column(JSON, nullable=True)  # Data used for the validation request
    response_data = Column(JSON, nullable=True)  # Data received in the validation response
    
    # Relationships
    irn_record = relationship("IRNRecord", back_populates="validation_records")