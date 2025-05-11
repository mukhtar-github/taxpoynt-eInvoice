"""API key management endpoints."""
from typing import Any, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.api_key import APIKeyCreate, APIKeyResponse, APIKeyFullResponse, APIKeyList
from app.crud.api_key import (
    create_api_key, 
    get_api_keys_by_user, 
    revoke_api_key, 
    get_api_keys_by_organization
)
from app.dependencies.auth import get_current_user, get_current_organization # type: ignore
from app.models.user import User
from app.models.organization import Organization # type: ignore
from app.core.security import get_permissions_for_role

router = APIRouter(prefix="/api-keys", tags=["api-keys"])


@router.post("", response_model=APIKeyFullResponse)
async def create_new_api_key(
    api_key_data: APIKeyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_organization: Organization = Depends(get_current_organization)
) -> Any:
    """
    Create a new API key for the current user and organization.
    """
    # Check if user has permission to create API keys
    user_role = current_user.get_role_in_organization(current_organization.id)
    user_permissions = get_permissions_for_role(user_role)
    
    if "create_api_keys" not in user_permissions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to create API keys"
        )
    
    # Create API key and secret key
    db_api_key, full_api_key, full_secret_key = create_api_key(
        db=db,
        user=current_user,
        organization=current_organization,
        key_data=api_key_data
    )
    
    # Return full keys (only displayed once)
    response = APIKeyFullResponse(
        id=db_api_key.id,
        name=db_api_key.name,
        description=db_api_key.description,
        prefix=db_api_key.prefix,
        secret_prefix=db_api_key.secret_prefix,
        rate_limit_per_minute=db_api_key.rate_limit_per_minute,
        rate_limit_per_day=db_api_key.rate_limit_per_day,
        created_at=db_api_key.created_at,
        expires_at=db_api_key.expires_at,
        last_used_at=db_api_key.last_used_at,
        is_active=db_api_key.is_active,
        api_key=full_api_key,
        secret_key=full_secret_key
    )
    
    return response


@router.get("", response_model=APIKeyList)
async def list_api_keys(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_organization: Organization = Depends(get_current_organization),
    skip: int = 0,
    limit: int = 100
) -> Any:
    """
    List API keys for the current organization.
    """
    # Check if user has permission to list API keys
    user_role = current_user.get_role_in_organization(current_organization.id)
    user_permissions = get_permissions_for_role(user_role)
    
    if "list_api_keys" not in user_permissions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to list API keys"
        )
    
    # Get API keys for organization
    api_keys = get_api_keys_by_organization(db, current_organization.id)
    
    # Apply pagination
    paginated_api_keys = api_keys[skip: skip + limit]
    
    return {
        "items": paginated_api_keys,
        "total": len(api_keys)
    }


@router.delete("/{api_key_id}", response_model=None, status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_key(
    api_key_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_organization: Organization = Depends(get_current_organization)
) -> Any:
    """
    Revoke an API key.
    """
    # Check if user has permission to delete API keys
    user_role = current_user.get_role_in_organization(current_organization.id)
    user_permissions = get_permissions_for_role(user_role)
    
    if "delete_api_keys" not in user_permissions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to revoke API keys"
        )
    
    # Revoke the API key
    success = revoke_api_key(db, api_key_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"API key with id {api_key_id} not found"
        )