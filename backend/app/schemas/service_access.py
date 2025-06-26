"""
Service Access Pydantic Schemas

This module contains Pydantic schemas for service access management API endpoints.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import UUID

from pydantic import BaseModel, Field, validator

from app.models.user_service_access import ServiceType, AccessLevel


class ServiceAccessCreate(BaseModel):
    """Schema for creating service access."""
    service_type: ServiceType = Field(..., description="Type of service to grant access to")
    access_level: AccessLevel = Field(..., description="Level of access to grant")
    expires_at: Optional[datetime] = Field(None, description="When the access expires (optional)")
    notes: Optional[str] = Field(None, description="Notes about why access was granted")
    
    @validator('expires_at')
    def validate_expiry_date(cls, v):
        if v and v <= datetime.utcnow():
            raise ValueError('Expiry date must be in the future')
        return v


class ServiceAccessUpdate(BaseModel):
    """Schema for updating service access."""
    access_level: Optional[AccessLevel] = Field(None, description="New access level")
    expires_at: Optional[datetime] = Field(None, description="New expiry date")
    is_active: Optional[bool] = Field(None, description="Whether access is active")
    notes: Optional[str] = Field(None, description="Updated notes")
    
    @validator('expires_at')
    def validate_expiry_date(cls, v):
        if v and v <= datetime.utcnow():
            raise ValueError('Expiry date must be in the future')
        return v


class ServiceAccessResponse(BaseModel):
    """Schema for service access response."""
    id: UUID
    user_id: UUID
    service_type: str
    access_level: str
    granted_by: Optional[UUID]
    granted_at: datetime
    expires_at: Optional[datetime]
    is_active: bool
    notes: Optional[str]
    
    class Config:
        from_attributes = True


class UserServiceAccessListResponse(BaseModel):
    """Schema for listing user's service access."""
    user_id: UUID
    total_access_records: int
    active_services: int
    access_records: List[ServiceAccessResponse]
    
    class Config:
        from_attributes = True


class ServiceSummaryResponse(BaseModel):
    """Schema for service summary information."""
    service_type: str
    name: str
    description: str
    access_level: Optional[str]
    features: List[str]
    
    class Config:
        from_attributes = True


class ServiceAccessAuditResponse(BaseModel):
    """Schema for service access audit log."""
    id: UUID
    user_service_access_id: UUID
    action: str
    changed_by: Optional[UUID]
    change_reason: Optional[str]
    old_values: Optional[str]
    new_values: Optional[str]
    timestamp: datetime
    
    class Config:
        from_attributes = True


class BulkServiceAccessRequest(BaseModel):
    """Schema for bulk service access operations."""
    user_ids: List[UUID] = Field(..., description="List of user IDs")
    service_type: ServiceType = Field(..., description="Service type to grant")
    access_level: AccessLevel = Field(..., description="Access level to grant")
    expires_at: Optional[datetime] = Field(None, description="Expiry date for all access")
    notes: Optional[str] = Field(None, description="Notes for all access grants")
    
    @validator('user_ids')
    def validate_user_ids(cls, v):
        if len(v) == 0:
            raise ValueError('At least one user ID is required')
        if len(v) > 100:
            raise ValueError('Cannot grant access to more than 100 users at once')
        return v


class UserServiceDashboard(BaseModel):
    """Schema for user service dashboard information."""
    user_id: UUID
    email: str
    full_name: Optional[str]
    total_services: int
    services: Dict[str, Any]
    last_login: Optional[datetime]
    
    class Config:
        from_attributes = True


class ServiceAccessStats(BaseModel):
    """Schema for service access statistics."""
    total_users: int
    users_by_service: Dict[str, int]
    users_by_access_level: Dict[str, int]
    active_access_records: int
    expired_access_records: int
    
    class Config:
        from_attributes = True


class ServiceMigrationRequest(BaseModel):
    """Schema for migrating users from old role system to service access."""
    dry_run: bool = Field(default=True, description="Whether to perform a dry run")
    preserve_existing_access: bool = Field(default=True, description="Whether to preserve existing service access")
    
    class Config:
        from_attributes = True


class ServiceMigrationResponse(BaseModel):
    """Schema for service migration response."""
    total_users_processed: int
    successful_migrations: int
    failed_migrations: int
    users_with_existing_access: int
    migration_details: List[Dict[str, Any]]
    
    class Config:
        from_attributes = True