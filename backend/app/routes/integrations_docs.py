"""
Example route file demonstrating the enhanced OpenAPI documentation.

This file shows how to use the api_docs utilities to create consistent,
high-quality API documentation for your ERP integration endpoints.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Path, Query, Depends, HTTPException
from pydantic import BaseModel

from app.utils.api_docs import ERP_INTEGRATION_RESPONSES, get_integration_example, api_example_response
from app.dependencies.auth import get_current_user
from app.models.user import User

# Models for documentation purposes
class IntegrationConfig(BaseModel):
    """Base configuration for an ERP integration."""
    class Config:
        from_attributes = True  # formerly orm_mode = True

class OdooConfig(IntegrationConfig):
    """Configuration for an Odoo ERP integration."""
    url: str
    database: str
    auth_method: str
    username: Optional[str] = None

class IntegrationResponse(BaseModel):
    """Standardized response format for integration operations."""
    id: str
    name: str
    integration_type: str
    status: str
    created_at: str
    last_sync: Optional[str] = None
    config: Dict[str, Any]
    
    class Config:
        from_attributes = True  # formerly orm_mode = True

# Example router
router = APIRouter()

@router.get(
    "/organizations/{organization_id}/integrations",
    response_model=List[IntegrationResponse],
    responses=ERP_INTEGRATION_RESPONSES,
    tags=["integrations"],
    summary="List all ERP integrations for an organization",
    description="""
    Retrieves all ERP integrations for the specified organization.
    
    Results can be filtered by integration type and status.
    """,
)
async def list_integrations(
    organization_id: str = Path(
        ..., 
        description="Unique identifier of the organization",
        example="org-123456"
    ),
    integration_type: Optional[str] = Query(
        None, 
        description="Filter by integration type (e.g. 'odoo', 'sap')",
        example="odoo"
    ),
    status: Optional[str] = Query(
        None, 
        description="Filter by integration status (e.g. 'configured', 'error', 'syncing')",
        example="configured"
    ),
    current_user: User = Depends(get_current_user)
):
    """
    List all integrations for the specified organization.
    
    This endpoint supports filtering by integration type and status.
    
    - **organization_id**: The unique identifier of the organization
    - **integration_type**: Optional filter by integration type
    - **status**: Optional filter by integration status
    
    Returns a list of integration objects with their configuration details.
    """
    # Implementation would go here
    # This is just for documentation purposes
    return [
        get_integration_example("odoo"),
        get_integration_example("sap")
    ]

@router.get(
    "/organizations/{organization_id}/integrations/{integration_id}",
    response_model=IntegrationResponse,
    responses=ERP_INTEGRATION_RESPONSES,
    tags=["integrations"],
    summary="Get a specific ERP integration",
    description="""
    Retrieves details for a specific ERP integration.
    
    This endpoint returns the complete configuration and status information
    for the requested integration.
    """,
)
async def get_integration(
    organization_id: str = Path(
        ..., 
        description="Unique identifier of the organization",
        example="org-123456"
    ),
    integration_id: str = Path(
        ..., 
        description="Unique identifier of the integration",
        example="int-123456"
    ),
    current_user: User = Depends(get_current_user)
):
    """
    Get details for a specific integration.
    
    - **organization_id**: The unique identifier of the organization
    - **integration_id**: The unique identifier of the integration
    
    Returns the integration object with its current status and configuration.
    """
    # Implementation would go here
    # This is just for documentation purposes
    return get_integration_example("odoo")

@router.post(
    "/organizations/{organization_id}/integrations/{integration_id}/sync",
    responses={
        **ERP_INTEGRATION_RESPONSES,
        202: {
            "description": "Sync initiated successfully",
            "content": {
                "application/json": {
                    "example": api_example_response(
                        get_integration_example("odoo"), 
                        message="Sync process initiated successfully"
                    )
                }
            }
        }
    },
    tags=["integrations"],
    summary="Synchronize an ERP integration",
    description="""
    Initiates a synchronization process for the specified integration.
    
    This endpoint triggers a background task to fetch the latest data from
    the connected ERP system.
    """,
)
async def sync_integration(
    organization_id: str = Path(
        ..., 
        description="Unique identifier of the organization",
        example="org-123456"
    ),
    integration_id: str = Path(
        ..., 
        description="Unique identifier of the integration",
        example="int-123456"
    ),
    current_user: User = Depends(get_current_user)
):
    """
    Initiate a sync operation for a specific integration.
    
    - **organization_id**: The unique identifier of the organization
    - **integration_id**: The unique identifier of the integration
    
    Returns the integration object with updated status information.
    """
    # Implementation would go here
    # This is just for documentation purposes
    example = get_integration_example("odoo")
    example["status"] = "syncing"
    return api_example_response(example, message="Sync process initiated successfully")
