"""
Certificate schemas for TaxPoynt eInvoice system.

This module defines Pydantic schemas for certificate operations.
"""

from datetime import datetime
from enum import Enum
from pydantic import BaseModel, validator, Field
from typing import Dict, List, Optional, Any, Union
from uuid import UUID

from app.models.certificate import CertificateType, CertificateStatus


# Base certificate schema
class CertificateBase(BaseModel):
    name: str
    description: Optional[str] = None
    certificate_type: CertificateType = CertificateType.X509
    tags: Optional[Dict[str, str]] = None


# Schema for certificate creation
class CertificateCreate(CertificateBase):
    organization_id: UUID
    certificate_data: str  # PEM encoded certificate
    private_key_data: Optional[str] = None  # PEM encoded private key
    password: Optional[str] = None  # Password for encrypted private key
    
    # Certificate metadata (optional, will be extracted from certificate if not provided)
    issuer: Optional[str] = None
    subject: Optional[str] = None
    serial_number: Optional[str] = None
    fingerprint: Optional[str] = None
    valid_from: Optional[datetime] = None
    valid_to: Optional[datetime] = None
    

# Schema for certificate update
class CertificateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[CertificateStatus] = None
    tags: Optional[Dict[str, str]] = None


# Schema for certificate revocation
class CertificateRevoke(BaseModel):
    reason: str = Field(..., min_length=5, max_length=255)


# Schema for certificate verification response
class CertificateVerification(BaseModel):
    valid: bool
    errors: List[str] = []
    warnings: List[str] = []
    details: Dict[str, Any] = {}


# Schema representing a certificate in the database
class CertificateInDBBase(CertificateBase):
    id: UUID
    organization_id: UUID
    certificate_type: CertificateType
    issuer: Optional[str] = None
    subject: Optional[str] = None
    serial_number: Optional[str] = None
    fingerprint: Optional[str] = None
    valid_from: Optional[datetime] = None
    valid_to: Optional[datetime] = None
    status: CertificateStatus
    has_private_key: bool
    created_at: datetime
    updated_at: datetime
    last_used_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# Schema for returning certificate to API consumers
class Certificate(CertificateInDBBase):
    """Certificate schema with all fields except sensitive ones."""
    pass


# Schema for returning certificate with encrypted certificate data
class CertificateWithData(Certificate):
    certificate_data: str
    is_encrypted: bool


# Schema for importing certificates from files
class CertificateImport(BaseModel):
    organization_id: UUID
    name: str
    description: Optional[str] = None
    certificate_file_content: str  # Base64 encoded file content
    file_type: str  # File extension or mime type
    password: Optional[str] = None  # Password for encrypted certificates/keystores


# Schema for certificate export request
class CertificateExport(BaseModel):
    format: str = Field("PEM", description="Export format: PEM, DER, etc.")
    include_private_key: bool = False
    password: Optional[str] = None  # For encrypting the exported private key


# Schema for certificate export response
class CertificateExportResponse(BaseModel):
    file_content: str  # Base64 encoded file content
    file_name: str
    content_type: str


# Schema for document signing request
class DocumentSignRequest(BaseModel):
    certificate_id: UUID
    document: Dict[str, Any]
    include_timestamp: bool = True
    include_metadata: bool = True


# Schema for document signing response
class DocumentSignResponse(BaseModel):
    document: Dict[str, Any]
    signature: str
    signature_metadata: Dict[str, Any]


# Schema for document signature verification request
class SignatureVerificationRequest(BaseModel):
    document: Dict[str, Any]
    certificate_id: Optional[UUID] = None  # If not provided, extract from document
    signature: Optional[str] = None  # If not provided, extract from document


# Schema for document signature verification response
class SignatureVerificationResponse(BaseModel):
    valid: bool
    errors: List[str] = []
    certificate_info: Optional[Dict[str, Any]] = None
