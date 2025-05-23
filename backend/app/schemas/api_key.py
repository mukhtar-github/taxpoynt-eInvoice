"""API key schemas for request/response validation."""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, UUID4, Field, validator
import uuid


class APIKeyBase(BaseModel):
    """Base schema for API key."""
    name: str
    description: Optional[str] = None
    rate_limit_per_minute: Optional[int] = Field(60, ge=1, le=1000, description="Rate limit per minute")
    rate_limit_per_day: Optional[int] = Field(10000, ge=100, le=100000, description="Rate limit per day")
    
    class Config:
        from_attributes = True


class APIKeyCreate(APIKeyBase):
    """Schema for API key creation."""
    expires_days: Optional[int] = Field(None, description="Number of days until expiration. None means no expiration.")
    
    @validator('expires_days')
    def validate_expires_days(cls, v):
        if v is not None and (v < 1 or v > 365):
            raise ValueError('expires_days must be between 1 and 365')
        return v


class APIKeyResponse(APIKeyBase):
    """Schema for API key response."""
    id: UUID4
    prefix: str
    secret_prefix: str
    created_at: datetime
    expires_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    is_active: bool


class APIKeyFullResponse(APIKeyResponse):
    """Schema for API key response including full key (only returned on creation)."""
    api_key: str
    secret_key: str


class APIKeyList(BaseModel):
    """Schema for API key list response."""
    items: List[APIKeyResponse]
    total: int


class APIKeyAuth(BaseModel):
    """Schema for API key authentication."""
    api_key: str
    secret_key: str