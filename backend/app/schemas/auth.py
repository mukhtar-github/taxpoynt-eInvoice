"""Authentication schemas for request/response validation."""
from typing import Optional
from pydantic import BaseModel, EmailStr, UUID4


class TokenSchema(BaseModel):
    """Schema for authentication token response."""
    access_token: str
    token_type: str
    refresh_token: str
    user_id: str
    email: Optional[str] = None


class RefreshTokenSchema(BaseModel):
    """Schema for token refresh request."""
    refresh_token: str


class PasswordResetRequest(BaseModel):
    """Schema for password reset request."""
    email: EmailStr


class PasswordReset(BaseModel):
    """Schema for password reset."""
    token: str
    password: str


class OAuthState(BaseModel):
    """Schema for OAuth state tracking."""
    redirect_uri: Optional[str] = None
    provider: str 