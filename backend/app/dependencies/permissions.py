"""Permission-based dependency functions for role-based access control."""
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Callable
from uuid import UUID

from app.core.permissions import Permission, user_has_permission
from app.dependencies.auth import get_current_active_user
from app.db.session import get_db
from app.models.user import User, Organization, OrganizationUser
from app.services.user_service import get_user_organizations


def has_permission(required_permission: Permission):
    """
    Dependency for checking if the current user has a specific permission.
    """
    async def permission_dependency(
        current_user: User = Depends(get_current_active_user)
    ) -> User:
        # Check global permission based on user role
        if user_has_permission(current_user.role, required_permission):
            return current_user
        
        # Permission denied
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Not enough permissions to perform this action"
        )
    
    return permission_dependency


def has_organization_permission(required_permission: Permission):
    """
    Dependency for checking if the user has a permission within an organization.
    This is more granular than global permissions.
    """
    async def organization_permission_dependency(
        organization_id: UUID,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ) -> User:
        # Get user's role in the specific organization
        org_user = db.query(OrganizationUser).filter(
            OrganizationUser.user_id == current_user.id,
            OrganizationUser.organization_id == organization_id
        ).first()
        
        if not org_user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User is not a member of this organization"
            )
        
        # Check permission based on user's role in this organization
        if user_has_permission(org_user.role, required_permission):
            return current_user
        
        # Permission denied
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Not enough permissions to perform this action in this organization"
        )
    
    return organization_permission_dependency


def is_organization_admin():
    """
    Dependency for checking if the user is an admin or owner of an organization.
    """
    async def is_admin_dependency(
        organization_id: UUID,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ) -> User:
        # Get user's role in the organization
        org_user = db.query(OrganizationUser).filter(
            OrganizationUser.user_id == current_user.id,
            OrganizationUser.organization_id == organization_id
        ).first()
        
        if not org_user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User is not a member of this organization"
            )
        
        # Check if user is admin or owner
        if org_user.role not in ["admin", "owner"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin or owner role required"
            )
        
        return current_user
    
    return is_admin_dependency


def is_organization_owner():
    """
    Dependency for checking if the user is the owner of an organization.
    """
    async def is_owner_dependency(
        organization_id: UUID,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ) -> User:
        # Get user's role in the organization
        org_user = db.query(OrganizationUser).filter(
            OrganizationUser.user_id == current_user.id,
            OrganizationUser.organization_id == organization_id
        ).first()
        
        if not org_user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User is not a member of this organization"
            )
        
        # Check if user is the owner
        if org_user.role != "owner":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Owner role required"
            )
        
        return current_user
    
    return is_owner_dependency


def get_user_with_organizations(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> User:
    """
    Get current user with their organizations.
    Used for efficient checking of organization access.
    """
    # Get user's organizations
    organizations = get_user_organizations(db, current_user.id)
    
    # Attach organizations to user object for convenience
    current_user.organizations = organizations
    
    return current_user


def is_verified_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Check if the user has verified their email.
    """
    if not current_user.is_email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email verification required"
        )
    
    return current_user
