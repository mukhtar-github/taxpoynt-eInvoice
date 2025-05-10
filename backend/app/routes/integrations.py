from fastapi import APIRouter, Depends, HTTPException, status, Body, Query # type: ignore
from sqlalchemy.orm import Session # type: ignore
from typing import Any, List, Optional
from uuid import UUID

from app.db.session import get_db
from app.models.integration import IntegrationType
from app.schemas.integration import (
    Integration, IntegrationCreate, IntegrationUpdate, IntegrationTestResult,
    OdooIntegrationCreate, OdooConnectionTestRequest, OdooConfig, IntegrationMonitoringStatus
)
from app.services.integration_service import (
    create_integration, get_integration, get_integrations, 
    update_integration, delete_integration, test_integration,
    create_odoo_integration, test_odoo_connection
)
from app.services.integration_monitor import (
    get_integration_monitoring_status, get_all_monitored_integrations,
    start_integration_monitoring, stop_integration_monitoring, run_integration_health_check
)
from app.services.user_service import get_current_user # type: ignore
from app.services.api_credential_service import get_credentials_for_integration
from app.templates.odoo_integration import get_odoo_templates, get_odoo_template, validate_odoo_config
from app.services.integration_credential_connector import create_credentials_from_integration_config, get_credentials_for_integration, migrate_integration_credentials_to_secure_storage

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


@router.post("/{integration_id}/monitor/start", response_model=IntegrationMonitoringStatus)
async def start_monitoring(
    integration_id: UUID,
    interval_minutes: int = Query(30, ge=5, le=1440),
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user)
) -> Any:
    """
    Start monitoring an integration.
    
    The system will periodically check the integration status at the specified interval.
    """
    # Check if integration exists
    integration = get_integration(db, integration_id)
    if not integration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Integration not found"
        )
    
    # Start monitoring
    success = start_integration_monitoring(db, integration_id, interval_minutes)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start monitoring"
        )
    
    # Get the updated status
    monitoring_status = get_integration_monitoring_status(db, integration_id)
    return monitoring_status


@router.post("/{integration_id}/monitor/stop", response_model=IntegrationMonitoringStatus)
async def stop_monitoring(
    integration_id: UUID,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user)
) -> Any:
    """
    Stop monitoring an integration.
    """
    # Check if integration exists
    integration = get_integration(db, integration_id)
    if not integration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Integration not found"
        )
    
    # Stop monitoring
    success = stop_integration_monitoring(db, integration_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Integration is not being monitored"
        )
    
    # Get the updated status
    monitoring_status = get_integration_monitoring_status(db, integration_id)
    return monitoring_status


@router.get("/{integration_id}/monitor/status", response_model=IntegrationMonitoringStatus)
async def get_monitoring_status(
    integration_id: UUID,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user)
) -> Any:
    """
    Get the current monitoring status of an integration.
    """
    # Check if integration exists
    integration = get_integration(db, integration_id)
    if not integration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Integration not found"
        )
    
    # Get the monitoring status
    try:
        monitoring_status = get_integration_monitoring_status(db, integration_id)
        return monitoring_status
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting monitoring status: {str(e)}"
        )


@router.get("/monitor/all", response_model=List[IntegrationMonitoringStatus])
async def get_all_monitoring_status(
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user)
) -> Any:
    """
    Get monitoring status for all integrations.
    """
    try:
        monitoring_statuses = get_all_monitored_integrations(db)
        return monitoring_statuses
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting monitoring statuses: {str(e)}"
        )


@router.post("/{integration_id}/health-check", response_model=IntegrationTestResult)
async def run_health_check(
    integration_id: UUID,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user)
) -> Any:
    """
    Run a manual health check on an integration.
    
    This will test the integration's connectivity and update its status.
    """
    # Check if integration exists
    integration = get_integration(db, integration_id)
    if not integration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Integration not found"
        )
    
    # Run the health check
    result = run_integration_health_check(db, integration_id)
    return result


@router.get("/templates/odoo", response_model=Dict[str, Any])
async def list_odoo_templates(
    current_user: Any = Depends(get_current_user)
) -> Any:
    """
    List all available Odoo integration templates.
    
    These templates provide pre-configured settings for various Odoo versions and configurations.
    """
    templates = get_odoo_templates()
    return templates


@router.get("/templates/odoo/{template_id}", response_model=Dict[str, Any])
async def get_specific_odoo_template(
    template_id: str,
    current_user: Any = Depends(get_current_user)
) -> Any:
    """
    Get a specific Odoo integration template by ID.
    
    Returns the complete template definition including schema and UI configuration.
    """
    template = get_odoo_template(template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Odoo template not found: {template_id}"
        )
    return template


@router.post("/create-from-template")
async def create_integration_from_template(
    template_id: str = Body(...),
    client_id: UUID = Body(...),
    name: str = Body(...),
    description: Optional[str] = Body(None),
    config_values: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user)
) -> Any:
    """
    Create a new integration from a template.
    
    The config_values should contain all required parameters for the template.
    """
    # Get the template
    template = None
    if template_id.startswith("odoo"):
        template = get_odoo_template(template_id)
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template not found: {template_id}"
        )
    
    # Validate config values against template schema
    if template_id.startswith("odoo"):
        errors = validate_odoo_config(config_values)
        if errors:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": "Invalid configuration values",
                    "errors": errors
                }
            )
    
    # Create integration with the given values
    integration_type = IntegrationType.ODOO if template_id.startswith("odoo") else IntegrationType.CUSTOM
    
    # Apply default values from template
    merged_config = {}
    if "default_values" in template:
        merged_config.update(template["default_values"])
    merged_config.update(config_values)
    
    integration_in = IntegrationCreate(
        client_id=client_id,
        name=name,
        description=description,
        integration_type=integration_type,
        config=merged_config
    )
    
    # Create the integration
    integration = create_integration(db, integration_in, current_user.id)
    
    # Create secure credentials from the integration config
    try:
        credential = create_credentials_from_integration_config(db, integration.id, current_user.id)
    except Exception as e:
        # Log but don't fail if credential creation fails
        logger.error(f"Error creating credentials for integration {integration.id}: {str(e)}")
    
    return Integration.from_orm(integration)


@router.post("/{integration_id}/secure-credentials")
async def migrate_to_secure_credentials(
    integration_id: UUID,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user)
) -> Any:
    """
    Migrate an integration's sensitive credentials to secure storage.
    
    This extracts sensitive information from the integration configuration
    and stores it in the secure API credentials system.
    """
    # Check if integration exists
    integration = get_integration(db, integration_id)
    if not integration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Integration not found"
        )
    
    try:
        # Migrate credentials
        credential = migrate_integration_credentials_to_secure_storage(
            db, integration_id, current_user.id
        )
        
        return {
            "success": True,
            "message": "Credentials successfully migrated to secure storage",
            "credential_id": str(credential.id),
            "name": credential.name
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error migrating credentials: {str(e)}"
        )
