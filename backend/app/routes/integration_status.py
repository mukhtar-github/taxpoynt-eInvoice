"""
Integration status API routes.

This module provides API routes for checking the status of various integrations,
including Odoo connections and FIRS API status.
"""
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_active_user
from app.db.session import get_db
from app.schemas.user import User
from app.services.integration_status_service import IntegrationStatusService

router = APIRouter(
    prefix="/integration-status",
    tags=["integration-status"],
    responses={404: {"description": "Not found"}},
)


@router.get("/odoo", response_model=Dict[str, Any])
async def get_odoo_status(
    integration_id: str = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get status of Odoo integration.
    
    This endpoint provides information about the health and connectivity of 
    Odoo integrations, including recent submission statistics.
    
    Args:
        integration_id: Optional specific integration ID to check
    """
    return await IntegrationStatusService.get_odoo_status(
        db=db,
        integration_id=integration_id
    )


@router.get("/firs", response_model=Dict[str, Any])
async def get_firs_api_status(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get status of FIRS API.
    
    This endpoint provides information about the health and availability of
    the FIRS API, including recent submission statistics.
    """
    return await IntegrationStatusService.get_firs_api_status(db=db)


@router.get("/all", response_model=Dict[str, Any])
async def get_all_integration_status(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get status of all integrations.
    
    This endpoint provides consolidated information about all system integrations,
    including Odoo connections and FIRS API.
    """
    return await IntegrationStatusService.get_all_integration_status(db=db)
