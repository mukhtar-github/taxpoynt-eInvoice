from typing import Any, List, Dict
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session

from app import crud, schemas
from app.api.dependencies import get_db, get_current_active_user
from app.services import integration as integration_service

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
    # Validate the configuration
    is_valid, errors, integration = integration_service.validate_and_create_integration(
        db=db, 
        obj_in=integration_in, 
        user_id=current_user.id
    )
    
    if not is_valid:
        raise HTTPException(
            status_code=400, 
            detail={"message": "Invalid integration configuration", "errors": errors}
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
    integration = integration_service.get_integration(db=db, integration_id=integration_id)
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    
    # Use the connection testing service
    result = integration_service.test_integration_connection(db=db, integration_id=integration_id)
    
    # Update integration status based on test result
    if result.success:
        integration_service.update_integration(
            db=db,
            db_obj=integration,
            obj_in=schemas.IntegrationUpdate(status="active"),
            user_id=current_user.id
        )
    else:
        integration_service.update_integration(
            db=db,
            db_obj=integration,
            obj_in=schemas.IntegrationUpdate(status="failed"),
            user_id=current_user.id
        )
    
    return result


@router.get("/templates", response_model=Dict[str, Any])
def get_integration_templates(
    current_user: schemas.User = Depends(get_current_active_user),
) -> Any:
    """
    Get all available integration templates.
    """
    return integration_service.get_integration_templates()


@router.get("/templates/{template_id}", response_model=Dict[str, Any])
def get_integration_template(
    template_id: str,
    current_user: schemas.User = Depends(get_current_active_user),
) -> Any:
    """
    Get a specific integration template.
    """
    template = integration_service.get_integration_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template


@router.post("/from-template", response_model=schemas.Integration)
def create_from_template(
    *,
    db: Session = Depends(get_db),
    data: schemas.IntegrationTemplateCreate,
    current_user: schemas.User = Depends(get_current_active_user),
) -> Any:
    """
    Create a new integration from a template.
    """
    integration = integration_service.create_integration_from_template(
        db=db,
        template_id=data.template_id,
        client_id=data.client_id,
        user_id=current_user.id,
        config_values=data.config_values
    )
    
    if not integration:
        raise HTTPException(status_code=404, detail="Template not found")
    
    return integration


@router.post("/validate", response_model=Dict[str, Any])
def validate_integration(
    *,
    config: Dict[str, Any],
    current_user: schemas.User = Depends(get_current_active_user),
) -> Any:
    """
    Validate an integration configuration without creating it.
    """
    is_valid, errors = integration_service.validate_integration_config(config)
    
    return {
        "valid": is_valid,
        "errors": errors
    }


@router.post("/{integration_id}/monitor/start", response_model=Dict[str, Any])
def start_monitoring_integration(
    *,
    db: Session = Depends(get_db),
    integration_id: UUID,
    interval_minutes: int = 30,
    current_user: schemas.User = Depends(get_current_active_user),
) -> Any:
    """
    Start monitoring an integration.
    """
    integration = integration_service.get_integration(db=db, integration_id=integration_id)
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    
    success = integration_service.start_integration_monitoring(
        db=db,
        integration_id=integration_id,
        interval_minutes=interval_minutes
    )
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to start monitoring")
    
    return {
        "message": f"Monitoring started for integration {integration_id}",
        "interval_minutes": interval_minutes,
        "integration_id": str(integration_id),
        "status": "monitoring"
    }


@router.post("/{integration_id}/monitor/stop", response_model=Dict[str, Any])
def stop_monitoring_integration(
    *,
    db: Session = Depends(get_db),
    integration_id: UUID,
    current_user: schemas.User = Depends(get_current_active_user),
) -> Any:
    """
    Stop monitoring an integration.
    """
    integration = integration_service.get_integration(db=db, integration_id=integration_id)
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    
    success = integration_service.stop_integration_monitoring(
        db=db,
        integration_id=integration_id
    )
    
    return {
        "message": "Monitoring stopped" if success else "Integration was not being monitored",
        "integration_id": str(integration_id),
        "status": "stopped"
    }


@router.get("/{integration_id}/status", response_model=Dict[str, Any])
def get_integration_status(
    *,
    db: Session = Depends(get_db),
    integration_id: UUID,
    current_user: schemas.User = Depends(get_current_active_user),
) -> Any:
    """
    Get the current status of an integration.
    """
    integration = integration_service.get_integration(db=db, integration_id=integration_id)
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    
    status = integration_service.get_integration_status(
        db=db,
        integration_id=integration_id
    )
    
    return {
        "integration_id": str(integration_id),
        "name": integration.name,
        "status": status.get("status", integration.status),
        "last_checked": status.get("last_checked", integration.last_tested),
        "message": status.get("message", "Status information not available"),
        "details": status.get("details", {})
    }


@router.get("/monitoring", response_model=List[Dict[str, Any]])
def get_monitored_integrations(
    *,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_active_user),
) -> Any:
    """
    Get a list of all integrations being monitored.
    """
    return integration_service.get_all_monitored_integrations(db=db) 