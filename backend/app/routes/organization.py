"""
Organization API routes for TaxPoynt eInvoice.

This module provides API endpoints for managing organizations.
"""
import logging
from typing import Any, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_user
from app.dependencies.db import get_db
from app.models.user import User
from app.schemas.organization import (
    Organization,
    OrganizationCreate,
    OrganizationUpdate,
    BrandingSettings,
    LogoUpload
)
from app.services.organization_service import OrganizationService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/", response_model=Organization, status_code=status.HTTP_201_CREATED)
def create_organization(
    organization: OrganizationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Create a new organization.
    
    Args:
        organization: Organization data
        db: Database session
        current_user: Authenticated user
        
    Returns:
        Created organization
    """
    organization_service = OrganizationService(db)
    return organization_service.create_organization(organization)


@router.get("/{organization_id}", response_model=Organization)
def get_organization(
    organization_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get organization by ID.
    
    Args:
        organization_id: UUID of the organization
        db: Database session
        current_user: Authenticated user
        
    Returns:
        Organization details
    """
    organization_service = OrganizationService(db)
    organization = organization_service.get_organization(organization_id)
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    return organization


@router.put("/{organization_id}", response_model=Organization)
def update_organization(
    organization_id: UUID,
    organization: OrganizationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Update organization details.
    
    Args:
        organization_id: UUID of the organization
        organization: Updated organization data
        db: Database session
        current_user: Authenticated user
        
    Returns:
        Updated organization
    """
    organization_service = OrganizationService(db)
    organization_updated = organization_service.update_organization(
        organization_id, organization
    )
    if not organization_updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    return organization_updated


@router.delete("/{organization_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
def delete_organization(
    organization_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> None:
    """
    Delete organization.
    
    Args:
        organization_id: UUID of the organization
        db: Database session
        current_user: Authenticated user
    """
    organization_service = OrganizationService(db)
    result = organization_service.delete_organization(organization_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )


@router.post("/{organization_id}/logo", response_model=LogoUpload)
async def upload_organization_logo(
    organization_id: UUID,
    logo: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Upload organization logo.
    
    Args:
        organization_id: UUID of the organization
        logo: Logo file
        db: Database session
        current_user: Authenticated user
        
    Returns:
        URL of the uploaded logo
    """
    organization_service = OrganizationService(db)
    logo_url = await organization_service.upload_organization_logo(organization_id, logo)
    return {"logo_url": logo_url}


@router.put("/{organization_id}/branding", response_model=Organization)
def update_branding_settings(
    organization_id: UUID,
    branding: BrandingSettings,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Update organization branding settings.
    
    Args:
        organization_id: UUID of the organization
        branding: Branding settings
        db: Database session
        current_user: Authenticated user
        
    Returns:
        Updated organization
    """
    organization_service = OrganizationService(db)
    organization = organization_service.update_branding_settings(organization_id, branding)
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    return organization
