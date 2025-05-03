"""OAuth authentication providers for social login."""
from typing import Dict, Optional, Union
from datetime import datetime, timedelta

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2AuthorizationCodeBearer
from authlib.integrations.starlette_client import OAuth, OAuthError # type: ignore
from starlette.requests import Request
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.config import settings
from app.db.session import get_db
from app.models.user import User
from app.core.security import create_access_token, create_refresh_token
from app.crud.user import get_user_by_email, create_user # type: ignore

# OAuth setup
oauth = OAuth()
oauth.register(
    name="google",
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)

oauth.register(
    name="microsoft",
    client_id=settings.MICROSOFT_CLIENT_ID,
    client_secret=settings.MICROSOFT_CLIENT_SECRET,
    server_metadata_url="https://login.microsoftonline.com/common/v2.0/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)

class TokenResponse(BaseModel):
    """Response model for token endpoint."""
    access_token: str
    token_type: str
    expires_in: int
    refresh_token: str
    user_id: str
    email: str

async def authenticate_oauth_user(
    provider: str, request: Request, db: Session
) -> Optional[TokenResponse]:
    """Authenticate user via OAuth provider and return tokens."""
    try:
        if provider not in ["google", "microsoft"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported OAuth provider: {provider}",
            )
            
        oauth_client = oauth.create_client(provider)
        token = await oauth_client.authorize_access_token(request)
        user_info = await oauth_client.parse_id_token(request, token)
        
        # Extract user information from the OAuth provider's response
        email = user_info.get("email")
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email not provided by OAuth provider",
            )
            
        # Check if the user already exists
        user = get_user_by_email(db, email=email)
        
        # If user doesn't exist, create a new one
        if not user:
            user_data = {
                "email": email,
                "full_name": user_info.get("name", ""),
                "is_verified": True,  # OAuth-authenticated users are considered verified
                "oauth_provider": provider,
                "oauth_user_id": user_info.get("sub") or user_info.get("oid"),
                # Generate a random password since we won't use it for OAuth users
                "hashed_password": "!oauth" + email,  
            }
            user = create_user(db, user_data)
        
        # Generate tokens
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        
        access_token = create_access_token(
            data={"sub": str(user.id)}, expires_delta=access_token_expires
        )
        refresh_token = create_refresh_token(
            data={"sub": str(user.id)}, expires_delta=refresh_token_expires
        )
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=access_token_expires.total_seconds(),
            refresh_token=refresh_token,
            user_id=str(user.id),
            email=user.email
        )
    except OAuthError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"OAuth authentication failed: {str(e)}",
        ) 