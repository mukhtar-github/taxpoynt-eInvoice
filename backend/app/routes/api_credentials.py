"""Routes for secure API credential management."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.db.session import get_db
from app.models.api_credential import CredentialType
from app.schemas.api_credential import (
    ApiCredential, ApiCredentialCreate, ApiCredentialUpdate,
    FirsApiCredential, OdooApiCredential
)
from app.services.api_credential_service import (
    create_api_credential, get_api_credential, get_organization_credentials,
    update_api_credential, delete_api_credential, record_credential_usage,
    create_firs_credential, create_odoo_credential,
    get_firs_credentials, get_odoo_credentials
)
from app.dependencies.auth import get_current_user, get_current_active_user

router = APIRouter(prefix="/api-credentials", tags=["api-credentials"])


@router.post("", response_model=ApiCredential, status_code=status.HTTP_201_CREATED)
async def create_credential(
    credential_in: ApiCredentialCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    Create a new API credential with encryption.
    
    All sensitive fields are encrypted before storage.
    """
    # Create credential with current user as creator
    return create_api_credential(
        db=db, 
        credential_in=credential_in,
        created_by=current_user.id
    )


@router.get("/{credential_id}", response_model=ApiCredential)
async def get_credential(
    credential_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    Get an API credential by ID.
    
    Sensitive fields will be masked in the response.
    """
    credential = get_api_credential(db, credential_id)
    if not credential:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API credential not found"
        )
    
    # Security check: credential must belong to user's organization
    # This assumes current_user has an organizations relationship
    user_orgs = [org.id for org in current_user.organizations]
    if credential.organization_id not in user_orgs:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this credential"
        )
    
    # Record usage
    record_credential_usage(db, credential_id)
    
    # Return with masked sensitive fields
    return ApiCredential.from_db_model(credential)


@router.get("", response_model=List[ApiCredential])
async def list_organization_credentials(
    organization_id: UUID,
    credential_type: Optional[CredentialType] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    Get all API credentials for an organization.
    
    Can be filtered by credential type.
    Sensitive fields will be masked in the response.
    """
    # Security check: organization must be accessible to user
    user_orgs = [org.id for org in current_user.organizations]
    if organization_id not in user_orgs:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this organization's credentials"
        )
    
    credentials = get_organization_credentials(
        db=db,
        organization_id=organization_id,
        credential_type=credential_type
    )
    
    # Return with masked sensitive fields
    return [ApiCredential.from_db_model(cred) for cred in credentials]


@router.put("/{credential_id}", response_model=ApiCredential)
async def update_credential(
    credential_id: UUID,
    credential_in: ApiCredentialUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    Update an API credential.
    
    Only provided fields will be updated.
    Sensitive fields will be encrypted before storage.
    """
    # Check if credential exists
    credential = get_api_credential(db, credential_id)
    if not credential:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API credential not found"
        )
    
    # Security check: credential must belong to user's organization
    user_orgs = [org.id for org in current_user.organizations]
    if credential.organization_id not in user_orgs:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this credential"
        )
    
    # Update the credential
    updated = update_api_credential(
        db=db,
        credential_id=credential_id,
        credential_in=credential_in,
        updated_by=current_user.id
    )
    
    # Return with masked sensitive fields
    return ApiCredential.from_db_model(updated)


@router.delete("/{credential_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_credential(
    credential_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Delete an API credential."""
    # Check if credential exists
    credential = get_api_credential(db, credential_id)
    if not credential:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API credential not found"
        )
    
    # Security check: credential must belong to user's organization
    user_orgs = [org.id for org in current_user.organizations]
    if credential.organization_id not in user_orgs:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this credential"
        )
    
    # Delete the credential
    delete_api_credential(db, credential_id)


@router.post("/firs", response_model=ApiCredential, status_code=status.HTTP_201_CREATED)
async def create_firs_api_credential(
    organization_id: UUID,
    credential_data: FirsApiCredential,
    name: str,
    description: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    Create a specialized FIRS API credential.
    
    Uses a simplified schema specific to FIRS API.
    """
    # Security check: organization must be accessible to user
    user_orgs = [org.id for org in current_user.organizations]
    if organization_id not in user_orgs:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create credentials for this organization"
        )
    
    # Create FIRS credential
    credential = create_firs_credential(
        db=db,
        organization_id=organization_id,
        credential_data=credential_data,
        name=name,
        description=description,
        created_by=current_user.id
    )
    
    # Return with masked sensitive fields
    return ApiCredential.from_db_model(credential)


@router.post("/odoo", response_model=ApiCredential, status_code=status.HTTP_201_CREATED)
async def create_odoo_api_credential(
    organization_id: UUID,
    credential_data: OdooApiCredential,
    name: str,
    description: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    Create a specialized Odoo API credential.
    
    Uses a simplified schema specific to Odoo API.
    """
    # Security check: organization must be accessible to user
    user_orgs = [org.id for org in current_user.organizations]
    if organization_id not in user_orgs:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create credentials for this organization"
        )
    
    # Create Odoo credential
    credential = create_odoo_credential(
        db=db,
        organization_id=organization_id,
        credential_data=credential_data,
        name=name,
        description=description,
        created_by=current_user.id
    )
    
    # Return with masked sensitive fields
    return ApiCredential.from_db_model(credential)


@router.get("/firs/organization/{organization_id}", response_model=List[ApiCredential])
async def list_firs_credentials(
    organization_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    Get all FIRS API credentials for an organization.
    
    Sensitive fields will be masked in the response.
    """
    # Security check: organization must be accessible to user
    user_orgs = [org.id for org in current_user.organizations]
    if organization_id not in user_orgs:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this organization's credentials"
        )
    
    credentials = get_firs_credentials(db, organization_id)
    
    # Return with masked sensitive fields
    return [ApiCredential.from_db_model(cred) for cred in credentials]


@router.get("/odoo/organization/{organization_id}", response_model=List[ApiCredential])
async def list_odoo_credentials(
    organization_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    Get all Odoo API credentials for an organization.
    
    Sensitive fields will be masked in the response.
    """
    # Security check: organization must be accessible to user
    user_orgs = [org.id for org in current_user.organizations]
    if organization_id not in user_orgs:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this organization's credentials"
        )
    
    credentials = get_odoo_credentials(db, organization_id)
    
    # Return with masked sensitive fields
    return [ApiCredential.from_db_model(cred) for cred in credentials]
