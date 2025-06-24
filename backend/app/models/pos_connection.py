"""
SQLAlchemy model for POS connections and transactions.

This module defines the database models for POS connection configuration
and transaction data for integration with various Point of Sale platforms.
"""

import uuid
import enum
from datetime import datetime
from typing import List, Optional

from sqlalchemy import Column, String, ForeignKey, DateTime, Boolean, func, Text, Enum, Numeric, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.db.base_class import Base


class POSType(str, enum.Enum):
    """Enumeration of supported POS platforms."""
    SQUARE = "square"
    TOAST = "toast"
    LIGHTSPEED = "lightspeed"
    FLUTTERWAVE = "flutterwave"
    PAYSTACK = "paystack"
    CUSTOM = "custom"


class POSConnection(Base):
    """
    Model for storing POS connection information and credentials.
    """
    __tablename__ = "pos_connections"
    
    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    pos_type = Column(Enum(POSType, values_callable=lambda obj: [e.value for e in obj]), nullable=False)
    location_name = Column(String(255))
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
    organization = relationship("Organization", back_populates="pos_connections")
    transactions = relationship("POSTransaction", back_populates="connection", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_pos_connections_user_id', user_id),
        Index('idx_pos_connections_organization_id', organization_id),
        Index('idx_pos_connections_pos_type', pos_type),
    )


class POSTransaction(Base):
    """
    Model for storing POS transaction data imported from connected POS platforms.
    
    This table uses PostgreSQL table partitioning to handle high-volume transaction data.
    Partitioning is done by transaction_timestamp on a monthly basis.
    """
    __tablename__ = "pos_transactions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    connection_id = Column(UUID(as_uuid=True), ForeignKey("pos_connections.id"), nullable=False)
    external_transaction_id = Column(String(255), nullable=False)
    transaction_amount = Column(Numeric(15, 2))
    tax_amount = Column(Numeric(15, 2))
    items = Column(JSONB)
    customer_data = Column(JSONB)
    transaction_timestamp = Column(DateTime, nullable=False)  # Used for partitioning
    invoice_generated = Column(Boolean, default=False)
    invoice_transmitted = Column(Boolean, default=False)
    invoice_id = Column(UUID(as_uuid=True), ForeignKey("invoices.id"), nullable=True)
    processing_errors = Column(JSONB, nullable=True)
    transaction_metadata = Column(JSONB, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, onupdate=func.now(), nullable=True)
    
    # Relationships
    connection = relationship("POSConnection", back_populates="transactions")
    
    # Partition by transaction_timestamp for high-volume handling
    # The actual partitioning is done in the Alembic migration script
    
    # Indexes - note that indexes on partitioned tables need special handling
    __table_args__ = (
        Index('idx_pos_transactions_connection_id', connection_id),
        Index('idx_pos_transactions_external_id', external_transaction_id),
        Index('idx_pos_transactions_invoice_id', invoice_id),
        # Index crucial for partitioning and filtering
        Index('idx_pos_transactions_timestamp', transaction_timestamp),
        # Compound index for efficient filtering by connection and date range
        Index('idx_pos_transactions_conn_timestamp', connection_id, transaction_timestamp),
        # Performance index for invoice status reports
        Index('idx_pos_transaction_invoice_status', connection_id, invoice_generated, invoice_transmitted),
        {'postgresql_partition_by': 'RANGE (transaction_timestamp)'}
    )
