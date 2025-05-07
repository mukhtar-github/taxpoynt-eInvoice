"""Schemas for API credential management."""
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.api_credential import CredentialType


class ApiCredentialBase(BaseModel):
    """Base schema for API credentials."""
    name: str
    description: Optional[str] = None
    credential_type: CredentialType
    
    # These fields should be encrypted before storage
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    
    # Additional configuration specific to the service
    additional_config: Optional[Dict[str, Any]] = None


class ApiCredentialCreate(ApiCredentialBase):
    """Schema for creating API credentials."""
    organization_id: UUID


class ApiCredentialUpdate(BaseModel):
    """Schema for updating API credentials."""
    name: Optional[str] = None
    description: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    additional_config: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    expires_at: Optional[datetime] = None


class ApiCredentialInDB(ApiCredentialBase):
    """Schema for API credential in database."""
    id: UUID
    organization_id: UUID
    created_by: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    is_active: bool
    is_encrypted: bool

    class Config:
        from_attributes = True


class ApiCredential(ApiCredentialInDB):
    """Schema for API credential responses."""
    # In responses, sensitive fields are masked or removed
    client_id: Optional[str] = Field(None, description="Partially masked")
    client_secret: Optional[str] = Field(None, description="Masked in responses")
    api_key: Optional[str] = Field(None, description="Partially masked")
    api_secret: Optional[str] = Field(None, description="Masked in responses")
    
    @classmethod
    def from_db_model(cls, db_credential, mask_sensitive: bool = True):
        """Convert DB model to response schema with optional masking."""
        data = ApiCredentialInDB.model_validate(db_credential).model_dump()
        
        if mask_sensitive:
            # Mask sensitive fields for display
            if data.get('client_id'):
                data['client_id'] = cls._mask_value(data['client_id'])
            if data.get('client_secret'):
                data['client_secret'] = "********"
            if data.get('api_key'):
                data['api_key'] = cls._mask_value(data['api_key'])
            if data.get('api_secret'):
                data['api_secret'] = "********"
        
        return cls(**data)
    
    @staticmethod
    def _mask_value(value: str) -> str:
        """Mask a value showing only first 4 and last 4 characters."""
        if not value or len(value) < 8:
            return "********" 
        return f"{value[:4]}...{value[-4:]}"


class FirsApiCredential(BaseModel):
    """Specialized schema for FIRS API credentials."""
    client_id: str
    client_secret: str
    environment: str = "sandbox"  # sandbox or production


class OdooApiCredential(BaseModel):
    """Specialized schema for Odoo API credentials."""
    url: str
    database: str
    username: str
    password: str
    api_key: Optional[str] = None
