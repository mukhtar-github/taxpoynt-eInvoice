from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class KeyMetadata(BaseModel):
    """Schema for encryption key metadata (without the actual key material)."""
    id: str
    created_at: str
    rotation_date: Optional[str] = None
    active: bool
    
    class Config:
        from_attributes = True


class KeyRotateResponse(BaseModel):
    """Response for key rotation endpoint."""
    key_id: str
    message: str


class KeyListResponse(BaseModel):
    """Response for listing keys endpoint."""
    keys: List[KeyMetadata]


class EncryptedValue(BaseModel):
    """Schema for an encrypted value with its key ID."""
    encrypted_value: str
    key_id: str


class EncryptionRequest(BaseModel):
    """Request to encrypt a value."""
    value: Any
    key_id: Optional[str] = None


class EncryptionResponse(BaseModel):
    """Response with encrypted value."""
    encrypted_data: EncryptedValue 