from fastapi import APIRouter, Depends, HTTPException, status, Request, Response # type: ignore
from fastapi.security import OAuth2PasswordRequestForm # type: ignore
from sqlalchemy.orm import Session # type: ignore
from typing import Any

from app.core.security import authenticate_user, create_access_token, create_refresh_token, verify_refresh_token
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import TokenSchema, RefreshTokenSchema
from app.schemas.user import UserCreate, UserResponse
from app.crud.user import create_user, get_user_by_email # type: ignore
from app.auth.oauth import oauth, authenticate_oauth_user
from app.services.email_service import send_email_verification, verify_email_token
from app.core.config import settings
from app.services.user_service import verify_user_email

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login", response_model=TokenSchema)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: Session = Depends(get_db)
) -> Any:
    """
    Authenticate user and return access and refresh tokens.
    """
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account not verified",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "refresh_token": refresh_token,
        "user_id": str(user.id),
        "email": user.email,
    }

@router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate, db: Session = Depends(get_db)) -> Any:
    """
    Register a new user.
    """
    # Check if user already exists
    db_user = get_user_by_email(db, email=user_data.email)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
    # Create new user
    user = create_user(db, user_data)
    
    # Send verification email with link to verify endpoint
    send_email_verification(db, user, f"{settings.API_V1_STR}/auth")
    
    return user

@router.post("/refresh", response_model=TokenSchema)
async def refresh_token(token_data: RefreshTokenSchema, db: Session = Depends(get_db)) -> Any:
    """
    Refresh access token using a valid refresh token.
    """
    user_id = verify_refresh_token(token_data.refresh_token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create new access token
    access_token = create_access_token(data={"sub": user_id})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "refresh_token": token_data.refresh_token,
        "user_id": user_id,
    }

# OAuth login routes
@router.get("/login/{provider}")
async def login_oauth(provider: str, request: Request):
    """
    Initiate OAuth login flow for the specified provider.
    """
    if provider not in ["google", "microsoft"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported OAuth provider: {provider}",
        )
    
    client = oauth.create_client(provider)
    redirect_uri = request.url_for(f"auth_callback", provider=provider)
    return await client.authorize_redirect(request, redirect_uri)

@router.get("/login/{provider}/callback", name="auth_callback")
async def auth_callback(provider: str, request: Request, db: Session = Depends(get_db)):
    """
    Handle OAuth callback and authenticate user.
    """
    token_response = await authenticate_oauth_user(provider, request, db)
    
    # In a real-world scenario, you would redirect to the frontend with the tokens
    # For now, we'll just return the token response
    return token_response

@router.get("/verify/{token}")
async def verify_email(token: str, db: Session = Depends(get_db)) -> Any:
    """
    Verify user's email using the token sent via email.
    """
    user = verify_email_token(db, token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token",
        )
    
    # Mark user as verified
    verify_user_email(db, user)
    
    return {"message": "Email verification successful. You can now log in."}

@router.post("/logout")
async def logout(response: Response):
    """
    Logout user and invalidate tokens.
    """
    # For JWT-based auth, the frontend should discard the tokens
    # Here we can add the token to a blocklist if needed
    
    # If using cookies for refresh tokens, clear them
    response.delete_cookie(key="refresh_token")
    
    return {"detail": "Successfully logged out"} 