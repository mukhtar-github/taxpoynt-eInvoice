"""
Transmission performance metrics model for TaxPoynt eInvoice Platform functionality.

This module defines models for tracking and analyzing performance metrics
of transmission operations to support optimization and monitoring.
"""

import uuid
from datetime import datetime, date
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Float, func, Date
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.db.base import Base


class TransmissionDailyMetrics(Base):
    """
    Model for daily aggregated transmission performance metrics.
    """
    __tablename__ = "transmission_daily_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False, 
        index=True
    )
    metric_date = Column(Date, nullable=False, index=True)
    
    # Volume metrics
    total_transmissions = Column(Integer, default=0)
    successful_transmissions = Column(Integer, default=0)
    failed_transmissions = Column(Integer, default=0)
    pending_transmissions = Column(Integer, default=0)
    
    # Performance metrics
    avg_processing_time_ms = Column(Float, default=0.0)
    avg_encryption_time_ms = Column(Float, default=0.0)
    avg_network_time_ms = Column(Float, default=0.0)
    avg_payload_size_bytes = Column(Integer, default=0)
    
    # Success metrics
    first_attempt_success_rate = Column(Float, default=0.0)
    avg_attempts_to_success = Column(Float, default=1.0)
    
    # Additional metrics
    peak_hour_transmissions = Column(Integer, default=0)
    peak_hour = Column(Integer, default=0)  # 0-23 hour of day
    
    # Relationships
    organization = relationship("Organization")
    
    # Composite unique constraint
    __table_args__ = (
        {'schema': 'public'},
        {'comment': 'Daily aggregated transmission performance metrics'},
        {'info': {'is_view': False}},
    )


class TransmissionMetricsSnapshot(Base):
    """
    Model for point-in-time transmission metrics snapshots.
    """
    __tablename__ = "transmission_metrics_snapshots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False, 
        index=True
    )
    transmission_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("transmission_records.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Timing information
    snapshot_time = Column(DateTime, nullable=False, server_default=func.now(), index=True)
    
    # Metrics
    encryption_time_ms = Column(Float, nullable=True)
    network_time_ms = Column(Float, nullable=True)
    total_processing_time_ms = Column(Float, nullable=True)
    payload_size_bytes = Column(Integer, nullable=True)
    retry_count = Column(Integer, default=0)
    
    # Context
    api_endpoint = Column(String(255), nullable=True)
    certificate_type = Column(String(50), nullable=True)
    payload_type = Column(String(50), nullable=True)
    transmission_mode = Column(String(50), nullable=True)  # sync, async, etc.
    
    # Additional metric data
    metric_details = Column(JSONB, nullable=True)
    
    # Relationships
    organization = relationship("Organization")
    transmission = relationship("TransmissionRecord")
    
    def __repr__(self):
        return f"<TransmissionMetricsSnapshot(id={self.id}, transmission_id={self.transmission_id}, " \
               f"total_processing_time_ms={self.total_processing_time_ms})>"
