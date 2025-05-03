from fastapi import APIRouter, Depends, HTTPException, status, Body # type: ignore
from sqlalchemy.orm import Session # type: ignore
from typing import Any, List, Optional
from uuid import UUID

from app.db.session import get_db
from app.models.integration import IntegrationType
from app.schemas.integration import (
    Integration, IntegrationCreate, IntegrationUpdate, IntegrationTestResult,
    OdooIntegrationCreate, OdooConnectionTestRequest, OdooConfig
)
from app.services.integration_service import (
    create_integration, get_integration, get_integrations, 
    update_integration, delete_integration, test_integration,
    create_odoo_integration, test_odoo_connection
)
from app.services.user_service import get_current_user # type: ignore

router = APIRouter(prefix="/integrations", tags=["integrations"])


@router.get("", response_model=List[Integration])
async def list_integrations(
    skip: int = 0, 
    limit: int = 100,
    client_id: Optional[UUID] = None,
    integration_type: Optional[IntegrationType] = None,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user)
) -> Any:
    """
    Retrieve integrations.
    
    Optionally filter by client_id and/or integration_type.
    """
    return get_integrations(
        db=db, 
        skip=skip, 
        limit=limit,
        client_id=client_id,
        integration_type=integration_type
    )


@router.post("", response_model=Integration)
async def create_new_integration(
    integration_in: IntegrationCreate,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user)
) -> Any:
    """
    Create new integration.
    """
    return create_integration(
        db=db, 
        integration_in=integration_in, 
        created_by=current_user.id
    )


@router.post("/odoo", response_model=Integration)
async def create_new_odoo_integration(
    integration_in: OdooIntegrationCreate,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user)
) -> Any:
    """
    Create new Odoo integration with specific Odoo configuration.
    """
    return create_odoo_integration(
        db=db, 
        integration_in=integration_in, 
        created_by=current_user.id
    )


@router.get("/{integration_id}", response_model=Integration)
async def get_integration_by_id(
    integration_id: UUID,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user)
) -> Any:
    """
    Get a specific integration by ID.
    """
    integration = get_integration(db, integration_id)
    if not integration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Integration not found"
        )
    return integration


@router.put("/{integration_id}", response_model=Integration)
async def update_integration_by_id(
    integration_id: UUID,
    integration_in: IntegrationUpdate,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user)
) -> Any:
    """
    Update an integration.
    """
    integration = get_integration(db, integration_id)
    if not integration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Integration not found"
        )
    
    updated_integration = update_integration(
        db=db, 
        integration_id=integration_id, 
        integration_in=integration_in, 
        changed_by=current_user.id
    )
    
    return updated_integration


@router.delete("/{integration_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_integration_by_id(
    integration_id: UUID,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user)
) -> Any:
    """
    Delete an integration.
    """
    integration = get_integration(db, integration_id)
    if not integration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Integration not found"
        )
    
    delete_integration(db=db, integration_id=integration_id)
    return None


@router.post("/{integration_id}/test", response_model=IntegrationTestResult)
async def test_integration_by_id(
    integration_id: UUID,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user)
) -> Any:
    """
    Test an integration connection.
    """
    integration = get_integration(db, integration_id)
    if not integration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Integration not found"
        )
    
    result = test_integration(db=db, integration=integration)
    return result


@router.post("/odoo/test-connection", response_model=IntegrationTestResult)
async def test_odoo_connectivity(
    connection_params: OdooConnectionTestRequest = Body(...),
    current_user: Any = Depends(get_current_user)
) -> Any:
    """
    Test connection to an Odoo server without creating an integration.
    
    This endpoint allows testing Odoo connectivity parameters before 
    creating an actual integration.
    """
    result = test_odoo_connection(connection_params)
    return result
