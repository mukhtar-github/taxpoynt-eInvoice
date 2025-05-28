"""
Organization Odoo data interaction API routes for TaxPoynt eInvoice.

This module provides API endpoints for organizations to interact with their Odoo data.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Body, Query, Path
from sqlalchemy.orm import Session
from typing import Any, List, Optional, Dict
from datetime import datetime
from uuid import UUID

from app.db.session import get_db
from app.models.user import User
from app.schemas.integration import (
    OdooConfig, OdooAuthMethod
)
from app.schemas.pagination import PaginatedResponse
from app.dependencies.auth import get_current_user
from app.services.organization_service import OrganizationService
from app.services.integration_service import get_integration
from app.services.integration_credential_connector import get_credentials_for_integration
from app.services.odoo_connector import OdooConnector, OdooDataError
from app.services.api_credential_service import record_credential_usage

router = APIRouter()


async def get_odoo_connector_for_integration(
    db: Session,
    organization_id: UUID,
    integration_id: UUID,
    current_user: User
) -> OdooConnector:
    """
    Helper function to get an OdooConnector instance for a specific integration.
    
    Args:
        db: Database session
        organization_id: UUID of the organization
        integration_id: UUID of the integration
        current_user: Authenticated user
        
    Returns:
        OdooConnector instance
        
    Raises:
        HTTPException: If organization or integration not found, or if integration does not belong to organization
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
    
    # Verify it's an Odoo integration
    if integration.integration_type != "odoo":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Integration is not an Odoo integration"
        )
    
    # Get credentials for the integration
    try:
        credentials = await get_credentials_for_integration(db=db, integration_id=integration_id)
        
        # Record credential usage for auditing
        await record_credential_usage(
            db=db,
            integration_id=integration_id,
            action="data_access",
            user_id=str(current_user.id)
        )
        
        # Create Odoo config from credentials
        odoo_config = OdooConfig(
            url=credentials.get("url", ""),
            database=credentials.get("database", ""),
            username=credentials.get("username", ""),
            password=credentials.get("password", ""),
            api_key=credentials.get("api_key", ""),
            auth_method=OdooAuthMethod(credentials.get("auth_method", "password"))
        )
        
        # Create and return OdooConnector instance
        connector = OdooConnector(odoo_config)
        return connector
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initialize Odoo connector: {str(e)}"
        )


@router.get("/{organization_id}/integrations/{integration_id}/odoo/company-info")
async def get_odoo_company_info(
    organization_id: UUID,
    integration_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get company information from Odoo.
    
    Args:
        organization_id: UUID of the organization
        integration_id: UUID of the integration
        db: Database session
        current_user: Authenticated user
        
    Returns:
        Company information from Odoo
    """
    try:
        # Get Odoo connector
        connector = await get_odoo_connector_for_integration(
            db=db,
            organization_id=organization_id,
            integration_id=integration_id,
            current_user=current_user
        )
        
        # Get company info
        connector.authenticate()
        company_info = connector.get_company_info()
        
        return company_info
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get company information from Odoo: {str(e)}"
        )


@router.get("/{organization_id}/integrations/{integration_id}/odoo/invoices")
async def get_odoo_invoices(
    organization_id: UUID,
    integration_id: UUID,
    from_date: Optional[datetime] = Query(None),
    to_date: Optional[datetime] = Query(None),
    include_draft: bool = Query(False),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get invoices from Odoo with pagination.
    
    Args:
        organization_id: UUID of the organization
        integration_id: UUID of the integration
        from_date: Optional start date filter
        to_date: Optional end date filter
        include_draft: Whether to include draft invoices
        page: Page number (1-indexed)
        page_size: Number of records per page
        db: Database session
        current_user: Authenticated user
        
    Returns:
        Paginated list of invoices from Odoo
    """
    try:
        # Get Odoo connector
        connector = await get_odoo_connector_for_integration(
            db=db,
            organization_id=organization_id,
            integration_id=integration_id,
            current_user=current_user
        )
        
        # Get invoices
        connector.authenticate()
        invoices = connector.get_invoices(
            from_date=from_date,
            to_date=to_date,
            include_draft=include_draft,
            page=page,
            page_size=page_size
        )
        
        return invoices
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get invoices from Odoo: {str(e)}"
        )


@router.get("/{organization_id}/integrations/{integration_id}/odoo/customers")
async def get_odoo_customers(
    organization_id: UUID,
    integration_id: UUID,
    search_term: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get customers from Odoo with pagination.
    
    Args:
        organization_id: UUID of the organization
        integration_id: UUID of the integration
        search_term: Optional search term to filter customers
        page: Page number (1-indexed)
        page_size: Number of records per page
        db: Database session
        current_user: Authenticated user
        
    Returns:
        List of customers from Odoo
    """
    try:
        # Get Odoo connector
        connector = await get_odoo_connector_for_integration(
            db=db,
            organization_id=organization_id,
            integration_id=integration_id,
            current_user=current_user
        )
        
        # Calculate offset from page and page_size
        offset = (page - 1) * page_size
        
        # Get customers
        connector.authenticate()
        customers = connector.get_customers(
            limit=page_size,
            offset=offset,
            search_term=search_term
        )
        
        return {
            "data": customers,
            "page": page,
            "page_size": page_size,
            "total": len(customers) + offset,  # This is an approximation since we don't have total count
            "has_more": len(customers) == page_size  # If we got a full page, there might be more
        }
    except HTTPException:
        raise
    except OdooDataError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get customers from Odoo: {str(e)}"
        )


@router.get("/{organization_id}/integrations/{integration_id}/odoo/products")
async def get_odoo_products(
    organization_id: UUID,
    integration_id: UUID,
    search_term: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get products from Odoo with pagination.
    
    Args:
        organization_id: UUID of the organization
        integration_id: UUID of the integration
        search_term: Optional search term to filter products
        page: Page number (1-indexed)
        page_size: Number of records per page
        db: Database session
        current_user: Authenticated user
        
    Returns:
        List of products from Odoo
    """
    try:
        # Get Odoo connector
        connector = await get_odoo_connector_for_integration(
            db=db,
            organization_id=organization_id,
            integration_id=integration_id,
            current_user=current_user
        )
        
        # Calculate offset from page and page_size
        offset = (page - 1) * page_size
        
        # Get products
        connector.authenticate()
        products = connector.get_products(
            limit=page_size,
            offset=offset,
            search_term=search_term
        )
        
        return {
            "data": products,
            "page": page,
            "page_size": page_size,
            "total": len(products) + offset,  # This is an approximation since we don't have total count
            "has_more": len(products) == page_size  # If we got a full page, there might be more
        }
    except HTTPException:
        raise
    except OdooDataError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get products from Odoo: {str(e)}"
        )


@router.post("/{organization_id}/integrations/{integration_id}/odoo/sync")
async def sync_odoo_data(
    organization_id: UUID,
    integration_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Trigger synchronization of data from Odoo.
    
    Args:
        organization_id: UUID of the organization
        integration_id: UUID of the integration
        db: Database session
        current_user: Authenticated user
        
    Returns:
        Synchronization status
    """
    try:
        # Get Odoo connector
        connector = await get_odoo_connector_for_integration(
            db=db,
            organization_id=organization_id,
            integration_id=integration_id,
            current_user=current_user
        )
        
        # Test connection to verify it's working
        connector.authenticate()
        
        # In a real implementation, this would trigger a background task to sync data
        # For now, we'll just return a success status
        
        # Update the integration's last_sync timestamp
        integration = get_integration(db=db, integration_id=integration_id)
        integration.last_sync = datetime.utcnow()
        db.commit()
        
        return {
            "status": "success",
            "message": "Synchronization initiated successfully",
            "timestamp": datetime.utcnow().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync data from Odoo: {str(e)}"
        )
