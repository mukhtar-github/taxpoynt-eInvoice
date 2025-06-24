"""
Invoice model for storing invoices generated from CRM/POS integrations.

This model stores invoice data that can be used for FIRS e-invoicing
and IRN generation.
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, Numeric, Boolean, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
import enum
from uuid import uuid4
from datetime import datetime

from app.db.base_class import Base


class InvoiceStatus(str, enum.Enum):
    """Invoice status enumeration."""
    DRAFT = "draft"
    PENDING = "pending"
    SENT = "sent"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"


class InvoiceSource(str, enum.Enum):
    """Invoice source enumeration."""
    CRM = "crm"
    POS = "pos"
    ERP = "erp"
    MANUAL = "manual"


class Invoice(Base):
    """
    Invoice model for storing invoices generated from various integrations.
    
    This model stores invoice data that can be submitted to FIRS for e-invoicing
    and IRN generation. It links to CRM deals, POS transactions, or manual entries.
    """
    __tablename__ = "invoices"
    
    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid4)
    invoice_number = Column(String(100), nullable=False, unique=True, index=True)
    
    # Organization and user references
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Invoice details
    invoice_date = Column(DateTime, nullable=False, default=func.now())
    due_date = Column(DateTime, nullable=True)
    status = Column(Enum(InvoiceStatus, values_callable=lambda obj: [e.value for e in obj]), nullable=False, default=InvoiceStatus.DRAFT)
    source = Column(Enum(InvoiceSource, values_callable=lambda obj: [e.value for e in obj]), nullable=False, default=InvoiceSource.MANUAL)
    
    # Financial information
    subtotal = Column(Numeric(15, 2), nullable=False, default=0)
    tax_amount = Column(Numeric(15, 2), nullable=False, default=0)
    total_amount = Column(Numeric(15, 2), nullable=False)
    currency_code = Column(String(3), nullable=False, default="NGN")
    
    # Customer information (stored as JSON for flexibility)
    customer_data = Column(JSONB, nullable=False)
    
    # Line items and metadata
    line_items = Column(JSONB, nullable=True)
    invoice_metadata = Column(JSONB, nullable=True)
    
    # Integration source tracking
    source_connection_id = Column(UUID(as_uuid=True), nullable=True)  # CRM/POS connection ID
    source_entity_id = Column(String(255), nullable=True)  # External deal/transaction ID
    
    # FIRS/IRN integration
    irn_generated = Column(Boolean, default=False)
    irn_value = Column(String(50), nullable=True, index=True)
    firs_submitted = Column(Boolean, default=False)
    firs_submission_date = Column(DateTime, nullable=True)
    firs_reference = Column(String(100), nullable=True)
    
    # Audit fields
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, onupdate=func.now(), nullable=True)
    
    # Relationships
    organization = relationship("Organization", back_populates="invoices")
    creator = relationship("User", back_populates="created_invoices")
    
    def __repr__(self):
        return f"<Invoice(id={self.id}, number={self.invoice_number}, amount={self.total_amount})>"
    
    @property
    def customer_name(self) -> str:
        """Get customer name from customer_data."""
        if isinstance(self.customer_data, dict):
            return self.customer_data.get("name", "Unknown Customer")
        return "Unknown Customer"
    
    @property
    def customer_email(self) -> str:
        """Get customer email from customer_data."""
        if isinstance(self.customer_data, dict):
            return self.customer_data.get("email", "")
        return ""
    
    def mark_irn_generated(self, irn_value: str):
        """Mark invoice as having IRN generated."""
        self.irn_generated = True
        self.irn_value = irn_value
        self.updated_at = datetime.utcnow()
    
    def mark_firs_submitted(self, firs_reference: str = None):
        """Mark invoice as submitted to FIRS."""
        self.firs_submitted = True
        self.firs_submission_date = datetime.utcnow()
        if firs_reference:
            self.firs_reference = firs_reference
        self.updated_at = datetime.utcnow()