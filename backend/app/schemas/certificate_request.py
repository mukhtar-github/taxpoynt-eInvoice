"""
Certificate request schemas for TaxPoynt eInvoice system.

This module defines Pydantic schemas for certificate request operations.
"""

from datetime import datetime
from pydantic import BaseModel, Field, validator
from typing import Dict, List, Optional, Any
from uuid import UUID

from app.models.certificate_request import CertificateRequestType, CertificateRequestStatus


# Base certificate request schema
class CertificateRequestBase(BaseModel):
    request_type: CertificateRequestType = CertificateRequestType.NEW
    request_metadata: Optional[Dict[str, Any]] = None


# Schema for certificate request creation
class CertificateRequestCreate(CertificateRequestBase):
    organization_id: UUID
    
    # CSR parameters - either provide raw CSR data or parameters to generate one
    csr_data: Optional[str] = None  # PEM encoded CSR if already generated
    
    # Parameters for CSR generation if csr_data is not provided
    common_name: Optional[str] = None
    organization_name: Optional[str] = None
    organizational_unit: Optional[str] = None
    locality: Optional[str] = None
    state_or_province: Optional[str] = None
    country: Optional[str] = None
    email: Optional[str] = None
    key_size: Optional[int] = Field(default=2048, ge=2048, le=4096)
    
    @validator('common_name', 'organization_name', always=True)
    def validate_required_fields(cls, v, values):
        # If CSR data is not provided, these fields are required for CSR generation
        if not values.get('csr_data') and not v:
            field_name = 'common_name' if v is None else 'organization_name'
            raise ValueError(f"{field_name} is required when csr_data is not provided")
        return v


# Schema for certificate request update
class CertificateRequestUpdate(BaseModel):
    status: Optional[CertificateRequestStatus] = None
    request_metadata: Optional[Dict[str, Any]] = None


# Schema for certificate request cancellation
class CertificateRequestCancel(BaseModel):
    reason: str = Field(..., min_length=5, max_length=255)


# Schema representing a certificate request in the database
class CertificateRequestInDBBase(CertificateRequestBase):
    id: UUID
    organization_id: UUID
    status: CertificateRequestStatus
    created_at: datetime
    updated_at: datetime
    created_by: Optional[UUID] = None
    
    class Config:
        from_attributes = True


# Schema for returning certificate request to API consumers
class CertificateRequest(CertificateRequestInDBBase):
    """Certificate request schema with all fields except sensitive ones."""
    pass


# Schema for certificate request status update
class CertificateRequestStatusUpdate(BaseModel):
    status: CertificateRequestStatus
    notes: Optional[str] = None
