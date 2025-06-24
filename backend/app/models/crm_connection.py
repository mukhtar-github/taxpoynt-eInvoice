"""
SQLAlchemy model for CRM connections.

This module defines the database models for CRM connection configuration
and deal data for integration with various CRM platforms.
"""

import uuid
import enum
from datetime import datetime
from typing import List, Optional

from sqlalchemy import Column, String, ForeignKey, DateTime, Boolean, func, Text, Enum, Numeric, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.db.base_class import Base


class CRMType(str, enum.Enum):
    """Enumeration of supported CRM platforms."""
    HUBSPOT = "hubspot"
    SALESFORCE = "salesforce"
    PIPEDRIVE = "pipedrive"
    ZOHO = "zoho"
    CUSTOM = "custom"


class CRMConnection(Base):
    """
    Model for storing CRM connection information and credentials.
    """
    __tablename__ = "crm_connections"
    
    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    crm_type = Column(Enum(CRMType, values_callable=lambda obj: [e.value for e in obj]), nullable=False)
    connection_name = Column(String(255))
    credentials_encrypted = Column(Text)
    connection_settings = Column(JSONB, nullable=True)
    webhook_url = Column(String(500), nullable=True)
    webhook_secret = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    last_sync_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, onupdate=func.now(), nullable=True)
    
    # Relationships
    user = relationship("User")
    organization = relationship("Organization", back_populates="crm_connections")
    deals = relationship("CRMDeal", back_populates="connection", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_crm_connections_user_id', user_id),
        Index('idx_crm_connections_organization_id', organization_id),
        Index('idx_crm_connections_crm_type', crm_type),
    )


class CRMDeal(Base):
    """
    Model for storing CRM deal data imported from connected CRM platforms.
    """
    __tablename__ = "crm_deals"
    
    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    connection_id = Column(UUID(as_uuid=True), ForeignKey("crm_connections.id"), nullable=False)
    external_deal_id = Column(String(255), nullable=False)
    deal_title = Column(String(255))
    deal_amount = Column(Numeric(15, 2))
    customer_data = Column(JSONB)
    deal_stage = Column(String(100))
    expected_close_date = Column(DateTime, nullable=True)
    invoice_generated = Column(Boolean, default=False)
    invoice_id = Column(UUID(as_uuid=True), ForeignKey("invoices.id"), nullable=True)
    deal_metadata = Column(JSONB, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, onupdate=func.now(), nullable=True)
    
    # Relationships
    connection = relationship("CRMConnection", back_populates="deals")
    
    # Indexes
    __table_args__ = (
        Index('idx_crm_deals_connection_id', connection_id),
        Index('idx_crm_deals_external_deal_id', external_deal_id),
        Index('idx_crm_deals_invoice_id', invoice_id),
        # Composite index for efficient filtering by connection and deal stage
        Index('idx_crm_deals_connection_stage', connection_id, deal_stage),
    )
