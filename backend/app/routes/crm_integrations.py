"""
FastAPI routes for CRM integrations management.

This module provides comprehensive API endpoints for managing CRM connections
and deal processing across different CRM platforms.
"""

import logging
import json
from typing import Dict, Any, List, Optional
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.models.crm_connection import CRMConnection, CRMDeal, CRMType
from app.models.user import User
from app.schemas.pagination import PaginatedResponse, PaginationParams
from app.integrations.base.errors import IntegrationError
from app.integrations.base.factory import get_connector_factory
from app.tasks.hubspot_tasks import process_hubspot_deal, sync_hubspot_deals
from app.services.firs_app.secure_communication_service import get_encryption_service, EncryptionService
from app.integrations.crm.data_mapper import cross_platform_mapper
from app.integrations.crm.template_engine import template_engine
from app.integrations.crm.pipeline_tracker import get_pipeline_tracker

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/crm",
    tags=["crm-integrations"],
    responses={
        400: {"description": "Bad request"},
        401: {"description": "Authentication required"},
        403: {"description": "Insufficient permissions"},
        404: {"description": "Resource not found"},
        422: {"description": "Validation error"},
        500: {"description": "Internal server error"},
    },
)


# ==================== REQUEST/RESPONSE MODELS ====================

class CRMConnectionCreate(BaseModel):
    """Model for creating a new CRM connection."""
    crm_type: CRMType = Field(..., description="CRM platform type")
    connection_name: str = Field(..., min_length=1, max_length=255, description="Display name for the connection")
    credentials: Dict[str, Any] = Field(..., description="Platform-specific credentials")
    connection_settings: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional connection settings")
    webhook_secret: Optional[str] = Field(None, description="Webhook secret for event verification")

    class Config:
        schema_extra = {
            "example": {
                "crm_type": "hubspot",
                "connection_name": "Main HubSpot Account",
                "credentials": {
                    "auth_type": "oauth2",
                    "client_id": "your-client-id",
                    "client_secret": "your-client-secret", 
                    "refresh_token": "your-refresh-token"
                },
                "connection_settings": {
                    "deal_stage_mapping": {
                        "closedwon": "generate_invoice",
                        "closedlost": "cancel_deal"
                    },
                    "auto_sync_deals": True,
                    "sync_interval_hours": 6
                },
                "webhook_secret": "your-webhook-secret"
            }
        }


class CRMConnectionUpdate(BaseModel):
    """Model for updating an existing CRM connection."""
    connection_name: Optional[str] = Field(None, min_length=1, max_length=255)
    credentials: Optional[Dict[str, Any]] = Field(None)
    connection_settings: Optional[Dict[str, Any]] = Field(None)
    webhook_secret: Optional[str] = Field(None)
    is_active: Optional[bool] = Field(None)


class CRMConnectionResponse(BaseModel):
    """Model for CRM connection response."""
    id: UUID
    crm_type: CRMType
    connection_name: str
    is_active: bool
    last_sync_at: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]
    webhook_url: Optional[str]
    connection_settings: Optional[Dict[str, Any]]

    class Config:
        from_attributes = True


class CRMDealResponse(BaseModel):
    """Model for CRM deal response."""
    id: UUID
    external_deal_id: str
    deal_title: Optional[str]
    deal_amount: Optional[float]
    customer_data: Optional[Dict[str, Any]]
    deal_stage: Optional[str]
    expected_close_date: Optional[datetime]
    invoice_generated: bool
    invoice_id: Optional[UUID]
    deal_metadata: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class CRMConnectionTestResult(BaseModel):
    """Model for connection test results."""
    success: bool
    message: str
    platform_info: Optional[Dict[str, Any]] = None
    error_details: Optional[Dict[str, Any]] = None


class DealProcessRequest(BaseModel):
    """Model for manual deal processing request."""
    action: str = Field(..., description="Action to perform: 'sync', 'generate_invoice', 'cancel'")
    force: bool = Field(False, description="Force processing even if already processed")


# ==================== HELPER FUNCTIONS ====================

def _get_user_crm_connection(
    db: Session, 
    connection_id: UUID, 
    user: User
) -> CRMConnection:
    """
    Get a CRM connection for the current user with permission validation.
    
    Args:
        db: Database session
        connection_id: CRM connection ID
        user: Current user
        
    Returns:
        CRMConnection object
        
    Raises:
        HTTPException: If connection not found or user lacks permission
    """
    connection = db.query(CRMConnection).filter(
        CRMConnection.id == connection_id,
        CRMConnection.organization_id == user.current_organization_id
    ).first()
    
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"CRM connection {connection_id} not found"
        )
    
    return connection


def _paginate_query(query, page: int, page_size: int):
    """
    Apply pagination to a SQLAlchemy query.
    
    Args:
        query: SQLAlchemy query object
        page: Page number (1-based)
        page_size: Number of items per page
        
    Returns:
        Tuple of (paginated_items, total_count, pagination_info)
    """
    total = query.count()
    offset = (page - 1) * page_size
    items = query.offset(offset).limit(page_size).all()
    
    pages = (total + page_size - 1) // page_size
    has_next = page < pages
    has_prev = page > 1
    
    return items, total, {
        "page": page,
        "page_size": page_size,
        "pages": pages,
        "has_next": has_next,
        "has_prev": has_prev,
        "next_page": page + 1 if has_next else None,
        "prev_page": page - 1 if has_prev else None
    }


# ==================== CRM CONNECTION ENDPOINTS ====================

@router.post(
    "/{platform}/connect",
    response_model=CRMConnectionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Connect to CRM platform",
    description="Create a new connection to a CRM platform with secure credential storage",
)
async def connect_crm_platform(
    platform: str = Path(..., description="CRM platform name (hubspot, salesforce, etc.)"),
    connection_data: CRMConnectionCreate = Body(..., description="Connection configuration"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    encryption_service: EncryptionService = Depends(get_encryption_service)
):
    """
    Connect to a CRM platform.
    
    This endpoint validates the platform, tests the connection, encrypts credentials,
    and stores the connection configuration in the database.
    
    Args:
        platform: CRM platform identifier
        connection_data: Connection configuration and credentials
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        CRMConnectionResponse with the created connection details
        
    Raises:
        HTTPException: If platform is unsupported, connection test fails, or creation fails
    """
    try:
        # Validate platform
        try:
            crm_type = CRMType(platform.lower())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported CRM platform: {platform}"
            )
        
        # Ensure the provided crm_type matches the platform
        if connection_data.crm_type != crm_type:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"CRM type mismatch: URL platform '{platform}' != payload type '{connection_data.crm_type}'"
            )
        
        # Test connection before saving
        logger.info(f"Testing {platform} connection for user {current_user.id}")
        
        try:
            factory = get_connector_factory()
            connector = factory.create_connector(
                platform=platform,
                config={
                    "credentials": connection_data.credentials,
                    "settings": connection_data.connection_settings
                }
            )
            
            test_result = await connector.test_connection()
            if not test_result.success:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Connection test failed: {test_result.message}"
                )
        except IntegrationError as e:
            logger.error(f"Integration error during connection test: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Connection test failed: {e.message}"
            )
        
        # Encrypt credentials before storing
        encrypted_credentials_dict = encryption_service.encrypt_integration_config(connection_data.credentials)
        encrypted_credentials = json.dumps(encrypted_credentials_dict)
        
        # Create database record
        db_connection = CRMConnection(
            user_id=current_user.id,
            organization_id=current_user.current_organization_id,
            crm_type=crm_type,
            connection_name=connection_data.connection_name,
            credentials_encrypted=encrypted_credentials,
            connection_settings=connection_data.connection_settings,
            webhook_secret=connection_data.webhook_secret,
            is_active=True
        )
        
        db.add(db_connection)
        db.commit()
        db.refresh(db_connection)
        
        logger.info(f"Created {platform} connection {db_connection.id} for user {current_user.id}")
        
        return CRMConnectionResponse.from_orm(db_connection)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error creating {platform} connection: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create CRM connection: {str(e)}"
        )


@router.get(
    "/connections",
    response_model=PaginatedResponse[CRMConnectionResponse],
    summary="List CRM connections",
    description="Retrieve paginated list of CRM connections for the current organization",
)
async def list_crm_connections(
    pagination: PaginationParams = Depends(),
    platform: Optional[str] = Query(None, description="Filter by CRM platform"),
    active_only: bool = Query(True, description="Show only active connections"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List CRM connections for the current organization.
    
    Args:
        pagination: Pagination parameters
        platform: Optional platform filter
        active_only: Filter for active connections only
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        PaginatedResponse containing CRM connections
    """
    try:
        query = db.query(CRMConnection).filter(
            CRMConnection.organization_id == current_user.current_organization_id
        )
        
        # Apply filters
        if platform:
            try:
                crm_type = CRMType(platform.lower())
                query = query.filter(CRMConnection.crm_type == crm_type.value)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid platform filter: {platform}"
                )
        
        if active_only:
            query = query.filter(CRMConnection.is_active == True)
        
        # Order by creation date (newest first)
        query = query.order_by(CRMConnection.created_at.desc())
        
        # Apply pagination
        items, total, pagination_info = _paginate_query(
            query, pagination.page, pagination.page_size
        )
        
        # Convert to response models
        response_items = [CRMConnectionResponse.from_orm(item) for item in items]
        
        return PaginatedResponse(
            items=response_items,
            total=total,
            **pagination_info
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing CRM connections: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve CRM connections"
        )


@router.get(
    "/connections/{connection_id}",
    response_model=CRMConnectionResponse,
    summary="Get CRM connection details",
    description="Retrieve detailed information about a specific CRM connection",
)
async def get_crm_connection(
    connection_id: UUID = Path(..., description="CRM connection ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get details of a specific CRM connection.
    
    Args:
        connection_id: CRM connection ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        CRMConnectionResponse with connection details
    """
    try:
        connection = _get_user_crm_connection(db, connection_id, current_user)
        return CRMConnectionResponse.from_orm(connection)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting CRM connection {connection_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve CRM connection"
        )


@router.put(
    "/connections/{connection_id}",
    response_model=CRMConnectionResponse,
    summary="Update CRM connection",
    description="Update configuration and settings for an existing CRM connection",
)
async def update_crm_connection(
    connection_id: UUID = Path(..., description="CRM connection ID"),
    update_data: CRMConnectionUpdate = Body(..., description="Updated connection data"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    encryption_service: EncryptionService = Depends(get_encryption_service)
):
    """
    Update an existing CRM connection.
    
    Args:
        connection_id: CRM connection ID
        update_data: Updated connection configuration
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        CRMConnectionResponse with updated connection details
    """
    try:
        connection = _get_user_crm_connection(db, connection_id, current_user)
        
        # Update fields if provided
        update_dict = update_data.dict(exclude_unset=True)
        
        for field, value in update_dict.items():
            if field == "credentials" and value is not None:
                # Encrypt new credentials
                encrypted_credentials_dict = encryption_service.encrypt_integration_config(value)
                encrypted_credentials = json.dumps(encrypted_credentials_dict)
                setattr(connection, "credentials_encrypted", encrypted_credentials)
            elif hasattr(connection, field):
                setattr(connection, field, value)
        
        db.commit()
        db.refresh(connection)
        
        logger.info(f"Updated CRM connection {connection_id} for user {current_user.id}")
        
        return CRMConnectionResponse.from_orm(connection)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating CRM connection {connection_id}: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update CRM connection"
        )


@router.delete(
    "/connections/{connection_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete CRM connection", 
    description="Delete a CRM connection and all associated data",
)
async def delete_crm_connection(
    connection_id: UUID = Path(..., description="CRM connection ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a CRM connection.
    
    This will also delete all associated deals and webhook configurations.
    
    Args:
        connection_id: CRM connection ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        204 No Content on successful deletion
    """
    try:
        connection = _get_user_crm_connection(db, connection_id, current_user)
        
        # Log deletion for audit trail
        logger.info(f"Deleting CRM connection {connection_id} for user {current_user.id}")
        
        # Delete the connection (cascades to deals due to foreign key)
        db.delete(connection)
        db.commit()
        
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting CRM connection {connection_id}: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete CRM connection"
        )


@router.post(
    "/connections/{connection_id}/test",
    response_model=CRMConnectionTestResult,
    summary="Test CRM connection",
    description="Test connectivity and authentication for an existing CRM connection",
)
async def test_crm_connection(
    connection_id: UUID = Path(..., description="CRM connection ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    encryption_service: EncryptionService = Depends(get_encryption_service)
):
    """
    Test an existing CRM connection.
    
    Args:
        connection_id: CRM connection ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        CRMConnectionTestResult with test results
    """
    try:
        connection = _get_user_crm_connection(db, connection_id, current_user)
        
        # Decrypt credentials
        encrypted_credentials_dict = json.loads(connection.credentials_encrypted)
        credentials = encryption_service.decrypt_integration_config(encrypted_credentials_dict)
        
        try:
            factory = get_connector_factory()
            connector = factory.create_connector(
                platform=connection.crm_type.value,
                config={
                    "credentials": credentials,
                    "settings": connection.connection_settings or {}
                }
            )
            
            test_result = await connector.test_connection()
            
            # Update last_sync_at if test is successful
            if test_result.success:
                connection.last_sync_at = datetime.utcnow()
                db.commit()
            
            return CRMConnectionTestResult(
                success=test_result.success,
                message=test_result.message,
                platform_info=test_result.details
            )
            
        except IntegrationError as e:
            logger.error(f"Integration error testing connection {connection_id}: {str(e)}")
            return CRMConnectionTestResult(
                success=False,
                message=f"Connection test failed: {e.message}",
                error_details={"error_type": e.__class__.__name__, "details": str(e)}
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing CRM connection {connection_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to test CRM connection"
        )


# ==================== DEAL MANAGEMENT ENDPOINTS ====================

@router.get(
    "/connections/{connection_id}/deals",
    response_model=PaginatedResponse[CRMDealResponse],
    summary="List CRM deals",
    description="Retrieve paginated list of deals from a CRM connection",
)
async def list_crm_deals(
    connection_id: UUID = Path(..., description="CRM connection ID"),
    pagination: PaginationParams = Depends(),
    stage: Optional[str] = Query(None, description="Filter by deal stage"),
    invoice_status: Optional[str] = Query(None, description="Filter by invoice status: 'generated', 'pending', 'all'"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List deals from a CRM connection.
    
    Args:
        connection_id: CRM connection ID
        pagination: Pagination parameters
        stage: Optional deal stage filter
        invoice_status: Optional invoice status filter
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        PaginatedResponse containing CRM deals
    """
    try:
        # Validate connection access
        connection = _get_user_crm_connection(db, connection_id, current_user)
        
        query = db.query(CRMDeal).filter(
            CRMDeal.connection_id == connection_id
        )
        
        # Apply filters
        if stage:
            query = query.filter(CRMDeal.deal_stage == stage)
        
        if invoice_status:
            if invoice_status == "generated":
                query = query.filter(CRMDeal.invoice_generated == True)
            elif invoice_status == "pending":
                query = query.filter(CRMDeal.invoice_generated == False)
            # 'all' shows everything, no additional filter needed
        
        # Order by creation date (newest first)
        query = query.order_by(CRMDeal.created_at.desc())
        
        # Apply pagination
        items, total, pagination_info = _paginate_query(
            query, pagination.page, pagination.page_size
        )
        
        # Convert to response models
        response_items = [CRMDealResponse.from_orm(item) for item in items]
        
        return PaginatedResponse(
            items=response_items,
            total=total,
            **pagination_info
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing deals for connection {connection_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve CRM deals"
        )


@router.get(
    "/connections/{connection_id}/deals/{deal_id}",
    response_model=CRMDealResponse,
    summary="Get CRM deal details",
    description="Retrieve detailed information about a specific CRM deal",
)
async def get_crm_deal(
    connection_id: UUID = Path(..., description="CRM connection ID"),
    deal_id: UUID = Path(..., description="CRM deal ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get details of a specific CRM deal.
    
    Args:
        connection_id: CRM connection ID
        deal_id: CRM deal ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        CRMDealResponse with deal details
    """
    try:
        # Validate connection access
        connection = _get_user_crm_connection(db, connection_id, current_user)
        
        deal = db.query(CRMDeal).filter(
            CRMDeal.id == deal_id,
            CRMDeal.connection_id == connection_id
        ).first()
        
        if not deal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Deal {deal_id} not found in connection {connection_id}"
            )
        
        return CRMDealResponse.from_orm(deal)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting deal {deal_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve CRM deal"
        )


@router.post(
    "/connections/{connection_id}/deals/{deal_id}/process",
    summary="Process CRM deal",
    description="Manually trigger processing of a specific CRM deal (sync, invoice generation, etc.)",
)
async def process_crm_deal(
    connection_id: UUID = Path(..., description="CRM connection ID"),
    deal_id: UUID = Path(..., description="CRM deal ID"),
    process_request: DealProcessRequest = Body(..., description="Processing action to perform"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Process a CRM deal with the specified action.
    
    Args:
        connection_id: CRM connection ID
        deal_id: CRM deal ID
        process_request: Processing action configuration
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Dict with processing results
    """
    try:
        # Validate connection access
        connection = _get_user_crm_connection(db, connection_id, current_user)
        
        deal = db.query(CRMDeal).filter(
            CRMDeal.id == deal_id,
            CRMDeal.connection_id == connection_id
        ).first()
        
        if not deal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Deal {deal_id} not found in connection {connection_id}"
            )
        
        logger.info(f"Processing deal {deal_id} with action '{process_request.action}' for user {current_user.id}")
        
        # Route to appropriate platform-specific processing
        if connection.crm_type == "hubspot":
            if process_request.action == "sync":
                result = await sync_hubspot_deals(str(connection_id), days_back=30)
            elif process_request.action in ["generate_invoice", "process"]:
                result = await process_hubspot_deal(deal.external_deal_id, str(connection_id))
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unsupported action '{process_request.action}' for {connection.crm_type.value}"
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail=f"Deal processing not yet implemented for {connection.crm_type.value}"
            )
        
        return {
            "message": f"Deal processing completed with action '{process_request.action}'",
            "connection_id": str(connection_id),
            "deal_id": str(deal_id),
            "action": process_request.action,
            "result": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing deal {deal_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process CRM deal: {str(e)}"
        )


@router.post(
    "/connections/{connection_id}/sync",
    summary="Sync CRM connection",
    description="Manually trigger a full synchronization of deals from the CRM platform",
)
async def sync_crm_connection(
    connection_id: UUID = Path(..., description="CRM connection ID"),
    days_back: int = Query(30, ge=1, le=365, description="Number of days to look back for deals"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Manually trigger synchronization of deals from a CRM connection.
    
    Args:
        connection_id: CRM connection ID
        days_back: Number of days to look back for deals
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Dict with synchronization results
    """
    try:
        # Validate connection access
        connection = _get_user_crm_connection(db, connection_id, current_user)
        
        logger.info(f"Manual sync triggered for connection {connection_id} by user {current_user.id}")
        
        # Route to appropriate platform-specific sync
        if connection.crm_type == "hubspot":
            result = await sync_hubspot_deals(str(connection_id), days_back)
        else:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail=f"Sync not yet implemented for {connection.crm_type.value}"
            )
        
        # Update last sync time
        connection.last_sync_at = datetime.utcnow()
        db.commit()
        
        return {
            "message": "CRM synchronization completed",
            "connection_id": str(connection_id),
            "platform": connection.crm_type.value,
            "days_back": days_back,
            "result": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error syncing connection {connection_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync CRM connection: {str(e)}"
        )