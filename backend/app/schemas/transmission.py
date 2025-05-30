"""
Transmission schemas for TaxPoynt eInvoice system.

This module defines Pydantic schemas for secure transmission operations.
"""

from datetime import datetime
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any, Union
from uuid import UUID

from app.models.transmission import TransmissionStatus


# Base transmission schema
class TransmissionBase(BaseModel):
    transmission_metadata: Optional[Dict[str, Any]] = None


# Schema for transmission creation
class TransmissionCreate(TransmissionBase):
    organization_id: UUID
    certificate_id: UUID
    submission_id: Optional[UUID] = None
    
    # Either provide submission_id or payload directly
    payload: Optional[Dict[str, Any]] = None
    
    # Additional options
    encrypt_payload: bool = True
    retry_strategy: Optional[Dict[str, Any]] = None  # Custom retry parameters


# Schema for transmission update
class TransmissionUpdate(BaseModel):
    status: Optional[TransmissionStatus] = None
    response_data: Optional[Dict[str, Any]] = None
    transmission_metadata: Optional[Dict[str, Any]] = None


# Schema for transmission retry
class TransmissionRetry(BaseModel):
    max_retries: Optional[int] = None
    retry_delay: Optional[int] = None  # Seconds
    force: bool = False
    notes: Optional[str] = None


# Schema representing a transmission in the database
class TransmissionInDBBase(TransmissionBase):
    id: UUID
    organization_id: UUID
    certificate_id: Optional[UUID] = None
    submission_id: Optional[UUID] = None
    transmission_time: datetime
    status: TransmissionStatus
    retry_count: int
    last_retry_time: Optional[datetime] = None
    created_by: Optional[UUID] = None
    
    class Config:
        from_attributes = True


# Schema for returning transmission to API consumers
class Transmission(TransmissionInDBBase):
    """Transmission schema with all fields except sensitive ones."""
    pass


# Schema for returning transmission with response data
class TransmissionWithResponse(Transmission):
    response_data: Optional[Dict[str, Any]] = None


# Schema for transmission batch status
class TransmissionBatchStatus(BaseModel):
    total: int
    pending: int
    in_progress: int
    completed: int
    failed: int
    retrying: int
    canceled: int
    success_rate: float


# Schema for transmission status notification
class TransmissionStatusNotification(BaseModel):
    transmission_id: UUID
    status: TransmissionStatus
    timestamp: datetime
    details: Optional[Dict[str, Any]] = None
