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
    canceled: int  # Using consistent spelling with the TransmissionStatus enum
    success_rate: Optional[float] = None
    average_retries: Optional[float] = None
    signed_transmissions: Optional[int] = None


# Schema for time-series data point
class TransmissionTimePoint(BaseModel):
    period: str
    total: int
    pending: int
    in_progress: int
    completed: int
    failed: int
    retrying: int
    cancelled: int


# Schema for time-series data
class TransmissionTimeline(BaseModel):
    timeline: List[TransmissionTimePoint]
    interval: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


# Schema for transmission history event
class TransmissionHistoryEvent(BaseModel):
    timestamp: str
    event: str
    status: str
    details: Optional[str] = None


# Schema for transmission debug info
class TransmissionDebugInfo(BaseModel):
    encryption_metadata: Dict[str, Any] = Field(default_factory=dict)
    response_data: Dict[str, Any] = Field(default_factory=dict)
    retry_count: int = 0
    error_details: Dict[str, Any] = Field(default_factory=dict)


# Schema for detailed transmission history
class TransmissionHistory(BaseModel):
    transmission: TransmissionWithResponse
    history: List[TransmissionHistoryEvent]
    debug_info: TransmissionDebugInfo


# Schema for batch update request
class TransmissionBatchUpdate(BaseModel):
    transmission_ids: List[UUID]
    status: Optional[TransmissionStatus] = None
    response_data: Optional[Dict[str, Any]] = None
    transmission_metadata: Optional[Dict[str, Any]] = None


# Schema for batch update response
class TransmissionBatchUpdateResponse(BaseModel):
    updated: int
    failed: int
    errors: List[str] = Field(default_factory=list)
    failed: int
    retrying: int


# Schema for transmission status notification
class TransmissionStatusNotification(BaseModel):
    transmission_id: UUID
    status: TransmissionStatus
    timestamp: datetime
    details: Optional[Dict[str, Any]] = None


# Schema for FIRS transmission request
class FIRSTransmissionRequest(BaseModel):
    payload: Dict[str, Any]
    organization_id: UUID
    certificate_id: Optional[UUID] = None
    submission_id: Optional[UUID] = None
    metadata: Optional[Dict[str, Any]] = None


# Schema for FIRS transmission retry request
class FIRSTransmissionRetryRequest(BaseModel):
    max_retries: int = 3
    force: bool = False
    immediate: bool = True
    notes: Optional[str] = None


# Response schema for transmission creation/retry
class TransmissionResponse(BaseModel):
    transmission_id: UUID
    status: TransmissionStatus
    message: str
    details: Optional[Dict[str, Any]] = None


# Response schema for transmission status
class TransmissionStatusResponse(BaseModel):
    transmission_id: UUID
    status: str
    last_updated: str
    retry_count: Optional[int] = None
    retry_history: Optional[List[Dict[str, Any]]] = None
    verification_status: Optional[str] = None
    firs_status: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


# Response schema for transmission receipt
class TransmissionReceiptResponse(BaseModel):
    receipt_id: str
    transmission_id: UUID
    timestamp: datetime
    verification_status: str
    receipt_data: Dict[str, Any]
