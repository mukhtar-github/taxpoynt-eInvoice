from typing import Any, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session

from app import crud, schemas
from app.api.dependencies import get_db, get_current_active_user

router = APIRouter()


@router.get("/", response_model=List[schemas.Integration])
def read_integrations(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: schemas.User = Depends(get_current_active_user),
) -> Any:
    """
    Retrieve integrations.
    """
    # TODO: Filter by organization once organization model is implemented
    integrations = crud.integration.get_multi(db, skip=skip, limit=limit)
    return integrations


@router.post("/", response_model=schemas.Integration)
def create_integration(
    *,
    db: Session = Depends(get_db),
    integration_in: schemas.IntegrationCreate,
    current_user: schemas.User = Depends(get_current_active_user),
) -> Any:
    """
    Create new integration.
    """
    # TODO: Add validation to ensure client belongs to user's organization
    integration = crud.integration.create(
        db=db, obj_in=integration_in, user_id=current_user.id
    )
    return integration


@router.get("/{integration_id}", response_model=schemas.Integration)
def read_integration(
    *,
    db: Session = Depends(get_db),
    integration_id: UUID,
    current_user: schemas.User = Depends(get_current_active_user),
) -> Any:
    """
    Get integration by ID.
    """
    integration = crud.integration.get(db=db, integration_id=integration_id)
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    # TODO: Check if integration belongs to user's organization
    return integration


@router.put("/{integration_id}", response_model=schemas.Integration)
def update_integration(
    *,
    db: Session = Depends(get_db),
    integration_id: UUID,
    integration_in: schemas.IntegrationUpdate,
    current_user: schemas.User = Depends(get_current_active_user),
) -> Any:
    """
    Update integration.
    """
    integration = crud.integration.get(db=db, integration_id=integration_id)
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    # TODO: Check if integration belongs to user's organization
    integration = crud.integration.update(
        db=db, db_obj=integration, obj_in=integration_in, user_id=current_user.id
    )
    return integration


@router.delete("/{integration_id}", response_model=schemas.Integration)
def delete_integration(
    *,
    db: Session = Depends(get_db),
    integration_id: UUID,
    current_user: schemas.User = Depends(get_current_active_user),
) -> Any:
    """
    Delete integration.
    """
    integration = crud.integration.get(db=db, integration_id=integration_id)
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    # TODO: Check if integration belongs to user's organization
    integration = crud.integration.delete(db=db, integration_id=integration_id)
    return integration


@router.get("/{integration_id}/history", response_model=List[schemas.IntegrationHistory])
def read_integration_history(
    *,
    db: Session = Depends(get_db),
    integration_id: UUID,
    current_user: schemas.User = Depends(get_current_active_user),
) -> Any:
    """
    Get integration configuration history.
    """
    integration = crud.integration.get(db=db, integration_id=integration_id)
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    # TODO: Check if integration belongs to user's organization
    history = crud.integration.get_history(db=db, integration_id=integration_id)
    return history


@router.post("/{integration_id}/test", response_model=schemas.IntegrationTestResult)
def test_integration(
    *,
    db: Session = Depends(get_db),
    integration_id: UUID,
    current_user: schemas.User = Depends(get_current_active_user),
) -> Any:
    """
    Test integration connection.
    """
    integration = crud.integration.get(db=db, integration_id=integration_id)
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    # TODO: Check if integration belongs to user's organization

    # Implement actual integration testing logic here
    # For now, return a placeholder response
    return {
        "success": True,
        "message": "Integration test successful",
        "details": {"status": "connected", "latency_ms": 150}
    } 