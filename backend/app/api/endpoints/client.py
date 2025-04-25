from typing import Any, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, schemas
from app.api.dependencies import get_db, get_current_active_user

router = APIRouter()


@router.get("/", response_model=List[schemas.Client])
def read_clients(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: schemas.User = Depends(get_current_active_user),
) -> Any:
    """
    Retrieve clients for the current user's organization.
    """
    # TODO: Replace this with actual organization ID once organization model is implemented
    organization_id = current_user.id  # Temporary: using user ID as organization ID
    clients = crud.client.get_by_organization_id(
        db, organization_id=organization_id, skip=skip, limit=limit
    )
    return clients


@router.post("/", response_model=schemas.Client)
def create_client(
    *,
    db: Session = Depends(get_db),
    client_in: schemas.ClientCreate,
    current_user: schemas.User = Depends(get_current_active_user),
) -> Any:
    """
    Create new client.
    """
    # TODO: Add validation to ensure client belongs to user's organization
    client = crud.client.create(db=db, obj_in=client_in)
    return client


@router.get("/{client_id}", response_model=schemas.Client)
def read_client(
    *,
    db: Session = Depends(get_db),
    client_id: UUID,
    current_user: schemas.User = Depends(get_current_active_user),
) -> Any:
    """
    Get client by ID.
    """
    client = crud.client.get(db=db, client_id=client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    # TODO: Check if client belongs to user's organization
    return client


@router.put("/{client_id}", response_model=schemas.Client)
def update_client(
    *,
    db: Session = Depends(get_db),
    client_id: UUID,
    client_in: schemas.ClientUpdate,
    current_user: schemas.User = Depends(get_current_active_user),
) -> Any:
    """
    Update client.
    """
    client = crud.client.get(db=db, client_id=client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    # TODO: Check if client belongs to user's organization
    client = crud.client.update(db=db, db_obj=client, obj_in=client_in)
    return client


@router.delete("/{client_id}", response_model=schemas.Client)
def delete_client(
    *,
    db: Session = Depends(get_db),
    client_id: UUID,
    current_user: schemas.User = Depends(get_current_active_user),
) -> Any:
    """
    Delete client.
    """
    client = crud.client.get(db=db, client_id=client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    # TODO: Check if client belongs to user's organization
    client = crud.client.delete(db=db, client_id=client_id)
    return client 