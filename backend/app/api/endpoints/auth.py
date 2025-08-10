from datetime import timedelta, datetime # type: ignore
from typing import Any, List # type: ignore
from uuid import UUID # type: ignore

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request # type: ignore
from fastapi.security import OAuth2PasswordRequestForm # type: ignore
from sqlalchemy.orm import Session # type: ignore

from app.api.dependencies import get_current_active_user, get_current_admin_user, get_current_user_with_org
from app.core.config import settings # type: ignore
from app.core.security import create_access_token, create_refresh_token, verify_refresh_token, blacklist_token # type: ignore
from app.db.session import get_db # type: ignore
from app.models.user import User, UserRole, Organization, OrganizationUser # type: ignore
from app.schemas.user import (
    User as UserSchema,
    UserCreate,
    Token,
    TokenPayload,
    PasswordReset,
    PasswordResetConfirm,
    EmailVerification,
    Organization as OrganizationSchema,
    OrganizationCreate,
    OrganizationWithUsers,
    OrganizationUser as OrganizationUserSchema,
    OrganizationUserCreate,
    OrganizationUserUpdate
)
from app.services.firs_core.user_service import (
    authenticate_user,
    create_user,
    get_user_by_email,
    get_user_by_id,
    get_user_by_reset_token,
    get_user_by_verification_token,
    reset_user_password,
    verify_user_email,
    create_organization,
    create_organization_with_owner,
    get_organization_by_id,
    get_organization_users,
    get_user_organizations,
    add_user_to_organization,
    remove_user_from_organization,
    update_user_role
)
from app.services.email_service import send_email_verification, send_password_reset

router = APIRouter()


@router.post("/login", response_model=Token)
def login_access_token(
    db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    OAuth2 compatible token login, get an access token and refresh token for future requests
    """
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user",
        )
        
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    # Create access token
    access_token = create_access_token(
        {"sub": str(user.id)}, expires_delta=access_token_expires
    )
    
    # Create refresh token
    refresh_token = create_refresh_token(
        {"sub": str(user.id)}, expires_delta=refresh_token_expires
    )
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "refresh_expires_in": settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    }


@router.post("/register", response_model=UserSchema)
def register_user(
    *,
    request: Request,
    db: Session = Depends(get_db),
    user_in: UserCreate,
) -> Any:
    """
    Create new user and send verification email
    """
    user = get_user_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="A user with this email already exists",
        )
        
    user = create_user(db, user_in, role=UserRole.SI_USER)
    
    # Send verification email
    base_url = str(request.base_url)
    send_email_verification(db, user, base_url)
    
    return user


@router.post("/register-admin", response_model=UserSchema)
def register_admin(
    *,
    request: Request,
    db: Session = Depends(get_db),
    user_in: UserCreate,
    current_user: User = Depends(get_current_admin_user),
) -> Any:
    """
    Create new admin user and send verification email
    """
    user = get_user_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="A user with this email already exists",
        )
        
    user = create_user(db, user_in, role=UserRole.ADMIN)
    
    # Send verification email
    base_url = str(request.base_url)
    send_email_verification(db, user, base_url)
    
    return user


@router.get("/verify/{token}", response_model=UserSchema)
def verify_email(
    *,
    token: str,
    db: Session = Depends(get_db),
) -> Any:
    """
    Verify user email with token
    """
    user = get_user_by_verification_token(db, token)
    if not user:
        raise HTTPException(
            status_code=400,
            detail="Invalid verification token",
        )
        
    verified_user = verify_user_email(db, user)
    return verified_user


@router.post("/password-reset", status_code=202)
def request_password_reset(
    *,
    request: Request,
    reset_in: PasswordReset,
    db: Session = Depends(get_db),
) -> Any:
    """
    Request password reset email
    """
    user = get_user_by_email(db, email=reset_in.email)
    
    # Always return success to prevent email enumeration
    if not user:
        return {"message": "If the email exists, a password reset link will be sent"}
        
    # Send password reset email
    base_url = str(request.base_url)
    send_password_reset(db, user, base_url)
    
    return {"message": "If the email exists, a password reset link will be sent"}


@router.post("/password-reset/confirm", response_model=UserSchema)
def confirm_password_reset(
    *,
    reset_in: PasswordResetConfirm,
    db: Session = Depends(get_db),
) -> Any:
    """
    Reset password with token
    """
    user = get_user_by_reset_token(db, reset_in.token)
    if not user:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired reset token",
        )
        
    if user.password_reset_expires_at < datetime.now():
        raise HTTPException(
            status_code=400,
            detail="Reset token has expired",
        )
        
    updated_user = reset_user_password(db, user, reset_in.new_password)
    return updated_user


class RefreshTokenRequest(BaseModel):
    refresh_token: str


@router.post("/refresh-token", response_model=Token)
def refresh_token(
    token_data: RefreshTokenRequest,
    db: Session = Depends(get_db)
) -> Any:
    """
    Get a new access token using a refresh token
    """
    # Verify the refresh token
    user_id = verify_refresh_token(token_data.refresh_token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    # Get the user from database
    user = get_user_by_id(db, UUID(user_id))
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user or user not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    # Blacklist the old refresh token (optional - prevents refresh token reuse)
    blacklist_token(token_data.refresh_token)
        
    # Create new tokens
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    # Create new access token
    access_token = create_access_token(
        {"sub": str(user.id)}, expires_delta=access_token_expires
    )
    
    # Create new refresh token
    new_refresh_token = create_refresh_token(
        {"sub": str(user.id)}, expires_delta=refresh_token_expires
    )
    
    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "refresh_expires_in": settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    }


@router.get("/me", response_model=UserSchema)
def read_users_me(
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get current user
    """
    return current_user


@router.get("/me/organizations", response_model=List[OrganizationSchema])
def read_user_organizations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get organizations for current user
    """
    org_users = get_user_organizations(db, current_user.id)
    
    # Extract organizations
    organizations = []
    for org_user in org_users:
        org = get_organization_by_id(db, org_user.organization_id)
        if org:
            organizations.append(org)
            
    return organizations


# Organization endpoints
@router.post("/organizations", response_model=OrganizationSchema)
def create_new_organization(
    *,
    org_in: OrganizationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Create new organization with current user as owner
    """
    result = create_organization_with_owner(db, org_in, current_user.id)
    return result["organization"]


@router.get("/organizations/{org_id}", response_model=OrganizationSchema)
def read_organization(
    *,
    org_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_with_org(required_roles=[UserRole.OWNER, UserRole.ADMIN, UserRole.MEMBER])),
) -> Any:
    """
    Get organization by ID
    """
    organization = get_organization_by_id(db, org_id)
    if not organization:
        raise HTTPException(
            status_code=404,
            detail="Organization not found",
        )
        
    return organization


@router.get("/organizations/{org_id}/users", response_model=List[OrganizationUserSchema])
def read_organization_users(
    *,
    org_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_with_org(required_roles=[UserRole.OWNER, UserRole.ADMIN])),
) -> Any:
    """
    Get all users in an organization
    """
    return get_organization_users(db, org_id)


@router.post("/organizations/{org_id}/users", response_model=OrganizationUserSchema)
def add_user_to_org(
    *,
    org_id: UUID,
    user_data: OrganizationUserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_with_org(required_roles=[UserRole.OWNER, UserRole.ADMIN])),
) -> Any:
    """
    Add user to organization
    """
    # Verify organization exists
    organization = get_organization_by_id(db, org_id)
    if not organization:
        raise HTTPException(
            status_code=404,
            detail="Organization not found",
        )
        
    # Verify user exists
    user = get_user_by_id(db, user_data.user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )
        
    # Add user to organization
    org_user = add_user_to_organization(db, user_data)
    return org_user


@router.delete("/organizations/{org_id}/users/{user_id}", status_code=204)
def remove_user_from_org(
    *,
    org_id: UUID,
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_with_org(required_roles=[UserRole.OWNER, UserRole.ADMIN])),
) -> Any:
    """
    Remove user from organization
    """
    # Verify not removing self if last owner
    if current_user.id == user_id:
        # Check if current user is owner
        org_user = db.query(OrganizationUser).filter(
            OrganizationUser.organization_id == org_id,
            OrganizationUser.user_id == current_user.id,
            OrganizationUser.role == UserRole.OWNER
        ).first()
        
        if org_user:
            # Count owners
            owners_count = db.query(OrganizationUser).filter(
                OrganizationUser.organization_id == org_id,
                OrganizationUser.role == UserRole.OWNER
            ).count()
            
            if owners_count <= 1:
                raise HTTPException(
                    status_code=400,
                    detail="Cannot remove the last owner from an organization",
                )
    
    success = remove_user_from_organization(db, org_id, user_id)
    if not success:
        raise HTTPException(
            status_code=404,
            detail="User not found in organization",
        )
        
    return None


@router.patch("/organizations/{org_id}/users/{user_id}/role", response_model=OrganizationUserSchema)
def update_organization_user_role(
    *,
    org_id: UUID,
    user_id: UUID,
    role_data: OrganizationUserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_with_org(required_roles=[UserRole.OWNER])),
) -> Any:
    """
    Update user role in organization
    """
    # Prevent changing own role if last owner
    if current_user.id == user_id and role_data.role != UserRole.OWNER:
        # Count owners
        owners_count = db.query(OrganizationUser).filter(
            OrganizationUser.organization_id == org_id,
            OrganizationUser.role == UserRole.OWNER
        ).count()
        
        if owners_count <= 1:
            raise HTTPException(
                status_code=400,
                detail="Cannot change role of the last owner",
            )
    
    updated_org_user = update_user_role(db, org_id, user_id, role_data.role)
    if not updated_org_user:
        raise HTTPException(
            status_code=404,
            detail="User not found in organization",
        )
        
    return updated_org_user 