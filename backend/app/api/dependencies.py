from typing import Generator, Optional, List, Callable # type: ignore
from uuid import UUID # type: ignore

from fastapi import Depends, HTTPException, status, Path, Request # type: ignore
from fastapi.security import OAuth2PasswordBearer # type: ignore
from jose import jwt # type: ignore
from pydantic import ValidationError # type: ignore
from sqlalchemy.orm import Session # type: ignore

from app.db.session import get_db # type: ignore
from app.core.config import settings # type: ignore
from app.models.user import User # type: ignore
from app.models.user_role import UserRole # type: ignore
from app.models.organization import OrganizationUser # type: ignore
from app.schemas.user import TokenPayload # type: ignore
from app.services.firs_core.user_service import get_user_by_id # type: ignore

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")


def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> User:
    """
    Get the current user from the JWT token
    """
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
    except (jwt.JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )
    
    user = get_user_by_id(db, token_data.sub)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Get the current active user
    """
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def get_current_verified_user(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    Get the current active user with verified email
    """
    if not current_user.is_email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Email not verified. Please verify your email address before proceeding."
        )
    return current_user


def get_current_admin_user(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    Get the current admin user
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions"
        )
    return current_user


def get_organization_id(
    org_id: UUID = Path(..., description="Organization ID")
) -> UUID:
    """
    Extract organization ID from path
    """
    return org_id


def get_current_user_with_org(
    required_roles: List[UserRole] = [UserRole.OWNER, UserRole.ADMIN, UserRole.MEMBER]
) -> Callable:
    """
    Dependency that checks if current user has the required role in the organization
    """
    def _check_user_org_role(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user),
        org_id: UUID = Depends(get_organization_id),
    ) -> User:
        # Check if user is a system admin (they bypass organization role checks)
        if current_user.role == UserRole.ADMIN:
            return current_user
            
        # Check if user belongs to the organization with the required role
        org_user = db.query(OrganizationUser).filter(
            OrganizationUser.organization_id == org_id,
            OrganizationUser.user_id == current_user.id,
            OrganizationUser.role.in_(required_roles)
        ).first()
        
        if not org_user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User does not have the required permissions for this organization",
            )
            
        return current_user
        
    return _check_user_org_role


def get_current_organization_owner(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    org_id: UUID = Depends(get_organization_id),
) -> User:
    """
    Dependency that checks if current user is an owner of the organization
    """
    org_user = db.query(OrganizationUser).filter(
        OrganizationUser.organization_id == org_id,
        OrganizationUser.user_id == current_user.id,
        OrganizationUser.role == UserRole.OWNER
    ).first()
    
    if not org_user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not an owner of this organization",
        )
        
    return current_user


def get_current_organization_admin(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    org_id: UUID = Depends(get_organization_id),
) -> User:
    """
    Dependency that checks if current user is an admin of the organization
    """
    # Check if user is a system admin (they bypass organization role checks)
    if current_user.role == UserRole.ADMIN:
        return current_user
        
    org_user = db.query(OrganizationUser).filter(
        OrganizationUser.organization_id == org_id,
        OrganizationUser.user_id == current_user.id,
        OrganizationUser.role.in_([UserRole.OWNER, UserRole.ADMIN])
    ).first()
    
    if not org_user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have administrative permissions for this organization",
        )
        
    return current_user 