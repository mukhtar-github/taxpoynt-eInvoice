from fastapi import APIRouter, Depends, HTTPException, status, Body, Query, Path # type: ignore
from sqlalchemy.orm import Session # type: ignore
from typing import Any, List, Optional, Dict
from datetime import datetime
from uuid import UUID

from app.db.session import get_db
from app.models.integration import IntegrationType
from app.schemas.integration import (
    Integration, IntegrationCreate, IntegrationUpdate, IntegrationTestResult,
    OdooIntegrationCreate, OdooConnectionTestRequest, OdooConfig, IntegrationMonitoringStatus,
    OdooInvoiceFetchParams, FIRSEnvironment, IntegrationExport, IntegrationImport
)
from app.schemas.pagination import PaginatedResponse
from app.services.integration_service import (
    create_integration, get_integration, get_integrations, 
    update_integration, delete_integration, test_integration,
    create_odoo_integration, test_odoo_connection, test_odoo_firs_connection,
    export_integration_config, import_integration_config
)
from app.services.odoo_service import fetch_odoo_invoices
from app.services.integration_monitor import (
    get_integration_monitoring_status, get_all_monitored_integrations,
    start_integration_monitoring, stop_integration_monitoring, run_integration_health_check
)
from app.dependencies.auth import get_current_user
from app.services.api_credential_service import record_credential_usage
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


@router.post("/odoo/test-firs-connection", response_model=IntegrationTestResult)
async def test_odoo_firs_connectivity(
    connection_params: OdooConnectionTestRequest = Body(...),
    environment: FIRSEnvironment = Query(FIRSEnvironment.SANDBOX),
    current_user: Any = Depends(get_current_user)
) -> Any:
    """
    Test connection to FIRS through an Odoo server without creating an integration.
    
    This endpoint tests both Odoo connectivity and FIRS integration capabilities
    in either sandbox or production environment.
    """
    # Ensure the environment is set correctly
    connection_params.firs_environment = environment
    result = test_odoo_firs_connection(connection_params)
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


@router.get("/{integration_id}/invoices")
async def fetch_odoo_invoices_by_integration(
    integration_id: UUID = Path(...),
    from_date: Optional[datetime] = Query(None),
    to_date: Optional[datetime] = Query(None),
    include_draft: bool = Query(False),
    include_attachments: bool = Query(False),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user)
) -> Any:
    """
    Fetch invoices from an Odoo integration with pagination support.
    
    This endpoint retrieves invoices from an Odoo server based on the
    integration configuration. Results are paginated.
    """
    # Check if integration exists
    integration = get_integration(db, integration_id)
    if not integration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Integration not found"
        )
    
    # Verify that it's an Odoo integration
    if integration.integration_type != IntegrationType.ODOO.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This endpoint only supports Odoo integrations"
        )
    
    # Get the Odoo configuration from the integration
    odoo_config = OdooConfig(**integration.config)
    
    # Fetch invoices
    result = fetch_odoo_invoices(
        config=odoo_config,
        from_date=from_date,
        to_date=to_date,
        include_draft=include_draft,
        include_attachments=include_attachments,
        page=page,
        page_size=page_size
    )
    
    # Check for errors in the result
    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching invoices: {result['error']['error']}"
        )
    
    return result


@router.post("/odoo/{integration_id}/invoices")
async def fetch_odoo_invoices_with_params(
    integration_id: UUID = Path(...),
    params: OdooInvoiceFetchParams = Body(...),
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user)
) -> Any:
    """
    Fetch invoices from an Odoo integration using body parameters.
    
    This endpoint is similar to GET /integrations/{integration_id}/invoices
    but accepts parameters in the request body instead of query params.
    """
    # Check if integration exists
    integration = get_integration(db, integration_id)
    if not integration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Integration not found"
        )
    
    # Verify that it's an Odoo integration
    if integration.integration_type != IntegrationType.ODOO.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This endpoint only supports Odoo integrations"
        )
    
    # Get the Odoo configuration from the integration
    odoo_config = OdooConfig(**integration.config)
    
    # Fetch invoices
    result = fetch_odoo_invoices(
        config=odoo_config,
        from_date=params.from_date,
        to_date=params.to_date,
        include_draft=params.include_draft,
        include_attachments=params.include_attachments,
        page=params.page,
        page_size=params.page_size
    )
    
    # Check for errors in the result
    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching invoices: {result['error']['error']}"
        )
    
    return result


@router.post("/{integration_id}/export", response_model=IntegrationExport)
async def export_integration(
    integration_id: UUID,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user)
) -> Any:
    """
    Export an integration configuration.
    
    This endpoint exports the configuration of an integration, which can be
    imported later to create a new integration with the same settings.
    Sensitive fields like passwords and API keys will be removed.
    """
    # Check if integration exists
    integration = get_integration(db, integration_id)
    if not integration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Integration not found"
        )
    
    # Export the integration
    try:
        export_data = export_integration_config(db, integration_id)
        return export_data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error exporting integration: {str(e)}"
        )


@router.post("/import", response_model=Integration)
async def import_integration(
    import_data: IntegrationImport,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user)
) -> Any:
    """
    Import an integration configuration.
    
    This endpoint creates a new integration based on exported configuration.
    Note that sensitive fields like passwords and API keys need to be provided
    again since they are not included in the export.
    """
    try:
        new_integration = import_integration_config(db, import_data, current_user.id)
        return new_integration
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error importing integration: {str(e)}"
        )


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
