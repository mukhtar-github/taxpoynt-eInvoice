"""
CSID schemas for TaxPoynt eInvoice system.

This module defines Pydantic schemas for Cryptographic Signature Identifier (CSID) operations.
"""

from datetime import datetime
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from uuid import UUID

from app.models.csid import CSIDStatus


# Base CSID schema
class CSIDBase(BaseModel):
    metadata: Optional[Dict[str, Any]] = None


# Schema for CSID creation
class CSIDCreate(CSIDBase):
    organization_id: UUID
    certificate_id: UUID
    expiration_time: Optional[datetime] = None


# Schema for CSID update
class CSIDUpdate(BaseModel):
    is_active: Optional[bool] = None
    expiration_time: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


# Schema for CSID revocation
class CSIDRevoke(BaseModel):
    reason: str = Field(..., min_length=5, max_length=255)


# Schema representing a CSID in the database
class CSIDInDBBase(CSIDBase):
    id: UUID
    organization_id: UUID
    csid: str
    certificate_id: UUID
    creation_time: datetime
    expiration_time: Optional[datetime] = None
    is_active: bool
    revocation_time: Optional[datetime] = None
    revocation_reason: Optional[str] = None
    created_by: Optional[UUID] = None
    
    class Config:
        from_attributes = True


# Schema for returning CSID to API consumers
class CSID(CSIDInDBBase):
    """CSID schema with all fields."""
    pass


# Schema for CSID verification response
class CSIDVerification(BaseModel):
    valid: bool
    status: CSIDStatus
    errors: List[str] = []
    warnings: List[str] = []
    details: Dict[str, Any] = {}


# Schema for CSID usage statistics
class CSIDUsageStats(BaseModel):
    csid: str
    total_uses: int
    last_used: Optional[datetime] = None
    success_count: int
    failure_count: int
    usage_by_date: Dict[str, int]  # Date string -> count
