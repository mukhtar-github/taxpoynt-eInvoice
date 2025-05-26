from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field, validator, root_validator, UUID4
from datetime import datetime
from enum import Enum


class OrganizationBase(BaseModel):
    """Base schema for organization data"""
    name: str
    tax_id: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    status: Optional[str] = "active"
    firs_service_id: Optional[str] = None
    logo_url: Optional[str] = None
    branding_settings: Optional[Dict[str, Any]] = None


class OrganizationCreate(OrganizationBase):
    """Schema for creating a new organization"""
    pass


class OrganizationUpdate(BaseModel):
    """Schema for updating an organization"""
    name: Optional[str] = None
    tax_id: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    status: Optional[str] = None
    firs_service_id: Optional[str] = None
    logo_url: Optional[str] = None
    branding_settings: Optional[Dict[str, Any]] = None


class OrganizationInDB(OrganizationBase):
    """Schema for organization data as stored in the database"""
    id: UUID4
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True


class Organization(OrganizationInDB):
    """Schema for complete organization data"""
    pass


class OrganizationWithUsers(Organization):
    """Schema for organization with users data"""
    users: List = []


class BrandingSettings(BaseModel):
    """Schema for organization branding settings"""
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    accent_color: Optional[str] = None
    logo_position: Optional[str] = "left"
    theme: Optional[str] = "light"
    custom_css: Optional[str] = None
    display_name: Optional[str] = None  # Alternative display name


class LogoUpload(BaseModel):
    """Schema for logo upload response"""
    logo_url: str
