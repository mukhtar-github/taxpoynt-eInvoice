"""
Organization service for TaxPoynt eInvoice.

This module provides a service for managing organization data.
"""
import logging
import uuid
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

from sqlalchemy.orm import Session
from fastapi import UploadFile, HTTPException, status

from app.models.organization import Organization
from app.schemas.organization import OrganizationCreate, OrganizationUpdate, BrandingSettings
from app.core.config import settings

logger = logging.getLogger(__name__)


class OrganizationService:
    """Service for managing organization data"""

    def __init__(self, db: Session):
        """Initialize the organization service with database session"""
        self.db = db

    def get_organization(self, organization_id: uuid.UUID) -> Optional[Organization]:
        """
        Get organization by ID.
        
        Args:
            organization_id: UUID of the organization
            
        Returns:
            Organization or None if not found
        """
        return self.db.query(Organization).filter(Organization.id == organization_id).first()

    def get_organizations(self, skip: int = 0, limit: int = 100) -> List[Organization]:
        """
        Get list of organizations.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of organizations
        """
        return self.db.query(Organization).offset(skip).limit(limit).all()

    def create_organization(self, organization_data: OrganizationCreate) -> Organization:
        """
        Create a new organization.
        
        Args:
            organization_data: Data for creating organization
            
        Returns:
            Created organization
        """
        organization = Organization(
            **organization_data.dict(),
            created_at=datetime.utcnow()
        )
        self.db.add(organization)
        self.db.commit()
        self.db.refresh(organization)
        logger.info(f"Created organization: {organization.name} with ID: {organization.id}")
        return organization

    def update_organization(
        self, organization_id: uuid.UUID, organization_data: OrganizationUpdate
    ) -> Optional[Organization]:
        """
        Update an existing organization.
        
        Args:
            organization_id: UUID of the organization to update
            organization_data: Updated organization data
            
        Returns:
            Updated organization or None if not found
        """
        organization = self.get_organization(organization_id)
        if not organization:
            return None

        # Update organization attributes
        update_data = organization_data.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(organization, key, value)

        organization.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(organization)
        logger.info(f"Updated organization: {organization.name} with ID: {organization.id}")
        return organization

    def delete_organization(self, organization_id: uuid.UUID) -> bool:
        """
        Delete an organization.
        
        Args:
            organization_id: UUID of the organization to delete
            
        Returns:
            True if deleted successfully, False if not found
        """
        organization = self.get_organization(organization_id)
        if not organization:
            return False

        self.db.delete(organization)
        self.db.commit()
        logger.info(f"Deleted organization with ID: {organization_id}")
        return True

    async def upload_organization_logo(
        self, organization_id: uuid.UUID, logo: UploadFile
    ) -> str:
        """
        Upload and store organization logo.
        
        Args:
            organization_id: UUID of the organization
            logo: Uploaded logo file
            
        Returns:
            URL of the uploaded logo
            
        Raises:
            HTTPException: If organization not found or file upload fails
        """
        organization = self.get_organization(organization_id)
        if not organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )

        # TODO: Implement actual file upload to a storage service
        # For Railway deployment, we would use a cloud storage service like S3
        # This is a placeholder implementation
        
        # Validate file type
        if not logo.content_type.startswith("image/"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must be an image"
            )
            
        # Generate a logo URL (in a real implementation, this would be the URL from the storage service)
        logo_url = f"{settings.API_V1_STR}/static/logos/{organization_id}_{logo.filename}"
        
        # Update the organization with the logo URL
        organization.logo_url = logo_url
        organization.updated_at = datetime.utcnow()
        self.db.commit()
        
        logger.info(f"Updated logo for organization: {organization.name}")
        return logo_url

    def update_branding_settings(
        self, organization_id: uuid.UUID, branding: BrandingSettings
    ) -> Optional[Organization]:
        """
        Update organization branding settings.
        
        Args:
            organization_id: UUID of the organization
            branding: Branding settings to update
            
        Returns:
            Updated organization or None if not found
        """
        organization = self.get_organization(organization_id)
        if not organization:
            return None
            
        # Update branding settings
        organization.branding_settings = branding.dict(exclude_unset=True)
        organization.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(organization)
        
        logger.info(f"Updated branding settings for organization: {organization.name}")
        return organization
