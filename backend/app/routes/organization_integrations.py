"""
Organization integration API routes for TaxPoynt eInvoice.

This module provides API endpoints for managing organization-specific integrations
with ERP systems (particularly Odoo).
"""
from fastapi import APIRouter, Depends, HTTPException, status, Body, Query, Path, File, UploadFile
from sqlalchemy.orm import Session
from typing import Any, List, Optional, Dict
from datetime import datetime
from uuid import UUID

from app.db.session import get_db
from app.models.integration import IntegrationType
from app.models.user import User
from app.schemas.integration import (
    Integration, IntegrationCreate, IntegrationUpdate, IntegrationTestResult,
    OdooIntegrationCreate, OdooConnectionTestRequest, OdooConfig
)
from app.schemas.pagination import PaginatedResponse
from app.dependencies.auth import get_current_user
from app.services.integration_service import (
    create_integration, get_integration, get_integrations, 
    update_integration, delete_integration, test_integration,
    create_odoo_integration, test_odoo_connection
)
from app.services.organization_service import OrganizationService
from app.services.odoo_connector import OdooConnector
from app.services.api_credential_service import record_credential_usage
from app.services.integration_credential_connector import create_credentials_from_integration_config, get_credentials_for_integration

router = APIRouter()


@router.post("/{organization_id}/integrations", response_model=Integration, status_code=status.HTTP_201_CREATED)
async def create_organization_integration(
    organization_id: UUID,
    integration: IntegrationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Create a new integration for an organization.
    
    Args:
        organization_id: UUID of the organization
        integration: Integration data
        db: Database session
        current_user: Authenticated user
        
    Returns:
        Created integration
    """
    # Verify organization exists
    org_service = OrganizationService(db)
    organization = org_service.get_organization(organization_id)
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    # Create integration with organization's client ID
    try:
        # Note: In a production system, we would need to verify that the user has
        # permissions to create integrations for this organization
        result = create_integration(db=db, integration_in=integration, user_id=current_user.id)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create integration: {str(e)}"
        )


@router.post("/{organization_id}/integrations/odoo", response_model=Integration, status_code=status.HTTP_201_CREATED)
async def create_organization_odoo_integration(
    organization_id: UUID,
    integration: OdooIntegrationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Create a new Odoo integration for an organization.
    
    Args:
        organization_id: UUID of the organization
        integration: Odoo integration data
        db: Database session
        current_user: Authenticated user
        
    Returns:
        Created Odoo integration
    """
    # Verify organization exists
    org_service = OrganizationService(db)
    organization = org_service.get_organization(organization_id)
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    # Create Odoo integration with organization's client ID
    try:
        # Set the client_id to the organization's ID
        integration.client_id = organization_id
        
        result = create_odoo_integration(
            db=db, 
            integration_in=integration, 
            user_id=current_user.id
        )
        
        # Create credentials in secure storage
        await create_credentials_from_integration_config(
            db=db,
            integration_id=result.id,
            config=result.config,
            user_id=current_user.id
        )
        
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create Odoo integration: {str(e)}"
        )


@router.get("/{organization_id}/integrations", response_model=List[Integration])
async def list_organization_integrations(
    organization_id: UUID,
    skip: int = 0, 
    limit: int = 100,
    integration_type: Optional[IntegrationType] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    List all integrations for an organization.
    
    Args:
        organization_id: UUID of the organization
        skip: Number of records to skip for pagination
        limit: Maximum number of records to return
        integration_type: Optional filter by integration type
        db: Database session
        current_user: Authenticated user
        
    Returns:
        List of integrations
    """
    # Verify organization exists
    org_service = OrganizationService(db)
    organization = org_service.get_organization(organization_id)
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    # Get integrations for the organization
    try:
        return get_integrations(
            db=db, 
            skip=skip, 
            limit=limit,
            client_id=organization_id,
            integration_type=integration_type
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to list integrations: {str(e)}"
        )


@router.get("/{organization_id}/integrations/{integration_id}", response_model=Integration)
async def get_organization_integration(
    organization_id: UUID,
    integration_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get a specific integration for an organization.
    
    Args:
        organization_id: UUID of the organization
        integration_id: UUID of the integration
        db: Database session
        current_user: Authenticated user
        
    Returns:
        Integration details
    """
    # Verify organization exists
    org_service = OrganizationService(db)
    organization = org_service.get_organization(organization_id)
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    # Get the integration
    integration = get_integration(db=db, integration_id=integration_id)
    if not integration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Integration not found"
        )
    
    # Verify integration belongs to the organization
    if str(integration.client_id) != str(organization_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Integration does not belong to this organization"
        )
    
    return integration


@router.put("/{organization_id}/integrations/{integration_id}", response_model=Integration)
async def update_organization_integration(
    organization_id: UUID,
    integration_id: UUID,
    integration_update: IntegrationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Update an integration for an organization.
    
    Args:
        organization_id: UUID of the organization
        integration_id: UUID of the integration
        integration_update: Updated integration data
        db: Database session
        current_user: Authenticated user
        
    Returns:
        Updated integration
    """
    # Verify organization exists
    org_service = OrganizationService(db)
    organization = org_service.get_organization(organization_id)
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    # Get the existing integration
    integration = get_integration(db=db, integration_id=integration_id)
    if not integration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Integration not found"
        )
    
    # Verify integration belongs to the organization
    if str(integration.client_id) != str(organization_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Integration does not belong to this organization"
        )
    
    # Update the integration
    try:
        updated_integration = update_integration(
            db=db,
            integration_id=integration_id,
            integration_in=integration_update,
            user_id=current_user.id
        )
        
        # If config was updated, update credentials in secure storage
        if integration_update.config is not None:
            await create_credentials_from_integration_config(
                db=db,
                integration_id=integration_id,
                config=updated_integration.config,
                user_id=current_user.id
            )
        
        return updated_integration
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update integration: {str(e)}"
        )


@router.delete("/{organization_id}/integrations/{integration_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def delete_organization_integration(
    organization_id: UUID,
    integration_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> None:
    """
    Delete an integration for an organization.
    
    Args:
        organization_id: UUID of the organization
        integration_id: UUID of the integration
        db: Database session
        current_user: Authenticated user
    """
    # Verify organization exists
    org_service = OrganizationService(db)
    organization = org_service.get_organization(organization_id)
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    # Get the existing integration
    integration = get_integration(db=db, integration_id=integration_id)
    if not integration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Integration not found"
        )
    
    # Verify integration belongs to the organization
    if str(integration.client_id) != str(organization_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Integration does not belong to this organization"
        )
    
    # Delete the integration
    try:
        delete_integration(db=db, integration_id=integration_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to delete integration: {str(e)}"
        )


@router.post("/{organization_id}/integrations/{integration_id}/test", response_model=IntegrationTestResult)
async def test_organization_integration(
    organization_id: UUID,
    integration_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Test an organization's integration connection.
    
    Args:
        organization_id: UUID of the organization
        integration_id: UUID of the integration
        db: Database session
        current_user: Authenticated user
        
    Returns:
        Test result with connection status
    """
    # Verify organization exists
    org_service = OrganizationService(db)
    organization = org_service.get_organization(organization_id)
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    # Get the existing integration
    integration = get_integration(db=db, integration_id=integration_id)
    if not integration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Integration not found"
        )
    
    # Verify integration belongs to the organization
    if str(integration.client_id) != str(organization_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Integration does not belong to this organization"
        )
    
    # Test the integration
    try:
        # Record credential usage for auditing
        await record_credential_usage(
            db=db,
            integration_id=integration_id,
            action="test_connection",
            user_id=str(current_user.id)
        )
        
        result = await test_integration(db=db, integration_id=integration_id)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to test integration: {str(e)}"
        )


@router.post("/{organization_id}/integrations/test-odoo", response_model=IntegrationTestResult)
async def test_odoo_connection_for_organization(
    organization_id: UUID,
    connection_params: OdooConnectionTestRequest = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Test connection to an Odoo server for an organization without creating an integration.
    
    Args:
        organization_id: UUID of the organization
        connection_params: Odoo connection parameters
        db: Database session
        current_user: Authenticated user
        
    Returns:
        Test result with connection status
    """
    # Verify organization exists
    org_service = OrganizationService(db)
    organization = org_service.get_organization(organization_id)
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    # Test the Odoo connection
    try:
        result = await test_odoo_connection(odoo_config=connection_params.config)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to test Odoo connection: {str(e)}"
        )
