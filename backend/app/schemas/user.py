from typing import Optional, List # type: ignore
from datetime import datetime
from uuid import UUID # type: ignore
from pydantic import BaseModel, EmailStr, Field, validator # type: ignore
import re

from app.models.user import UserRole


class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    is_active: bool = True


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")
    
    @validator('password')
    def password_complexity(cls, v):
        """Validate password meets complexity requirements"""
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        return v


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = Field(None, min_length=8, description="Password must be at least 8 characters")


class PasswordReset(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)
    
    @validator('new_password')
    def password_complexity(cls, v):
        """Validate password meets complexity requirements"""
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        return v


class EmailVerification(BaseModel):
    token: str


class UserInDBBase(UserBase):
    id: UUID
    role: UserRole
    is_email_verified: bool = False
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True


class User(UserInDBBase):
    pass


class UserResponse(UserInDBBase):
    """Response model for user data, excluding sensitive information"""
    pass


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    refresh_expires_in: Optional[int] = None


class TokenPayload(BaseModel):
    sub: Optional[UUID] = None


# Organization schemas
class OrganizationBase(BaseModel):
    name: str
    tax_id: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    website: Optional[str] = None


class OrganizationCreate(OrganizationBase):
    pass


class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    tax_id: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    website: Optional[str] = None
    status: Optional[str] = None
    firs_service_id: Optional[str] = None


class OrganizationInDBBase(OrganizationBase):
    id: UUID
    status: str
    firs_service_id: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Organization(OrganizationInDBBase):
    pass


class OrganizationWithUsers(Organization):
    users: List["UserOrganization"] = []


# Organization User schemas
class OrganizationUserBase(BaseModel):
    organization_id: UUID
    user_id: UUID
    role: UserRole = UserRole.MEMBER


class OrganizationUserCreate(OrganizationUserBase):
    pass


class OrganizationUserUpdate(BaseModel):
    role: Optional[UserRole] = None


class OrganizationUserInDBBase(OrganizationUserBase):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class OrganizationUser(OrganizationUserInDBBase):
    pass


class UserOrganization(BaseModel):
    id: UUID
    email: EmailStr
    full_name: Optional[str] = None
    role: UserRole

    class Config:
        from_attributes = True 