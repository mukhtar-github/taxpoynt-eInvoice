from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any
from datetime import datetime
import re


class IRNGenerateRequest(BaseModel):
    """Schema for IRN generation request"""
    integration_id: str = Field(..., description="ID of the integration")
    invoice_number: str = Field(..., description="Invoice number from accounting system")
    timestamp: Optional[str] = Field(None, description="Date in YYYYMMDD format")

    @validator('invoice_number')
    def validate_invoice_number(cls, v):
        if not re.match(r'^[a-zA-Z0-9]+$', v):
            raise ValueError('Invoice number must be alphanumeric with no special characters')
        return v

    @validator('timestamp')
    def validate_timestamp(cls, v):
        if v is None:
            return v
        if not re.match(r'^\d{8}$', v):
            raise ValueError('Timestamp must be in YYYYMMDD format')
        return v


class IRNBatchGenerateRequest(BaseModel):
    """Schema for batch IRN generation request"""
    integration_id: str = Field(..., description="ID of the integration")
    invoice_numbers: list[str] = Field(..., description="List of invoice numbers")
    timestamp: Optional[str] = Field(None, description="Date in YYYYMMDD format")


class IRNResponse(BaseModel):
    """Schema for IRN response"""
    irn: str = Field(..., description="Generated IRN")
    status: str = Field(..., description="IRN status")
    generated_at: datetime = Field(..., description="Timestamp of generation")
    valid_until: datetime = Field(..., description="Expiration timestamp")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

    class Config:
        orm_mode = True


class IRNBatchResponse(BaseModel):
    """Schema for batch IRN generation response"""
    irns: list[IRNResponse] = Field(..., description="List of generated IRNs")
    count: int = Field(..., description="Number of IRNs generated")


class IRNStatusUpdate(BaseModel):
    """Schema for updating IRN status"""
    status: str = Field(..., description="New status (used, unused, expired)")
    invoice_id: Optional[str] = Field(None, description="External invoice ID that used this IRN")
    used_at: Optional[datetime] = Field(None, description="When the IRN was used") 