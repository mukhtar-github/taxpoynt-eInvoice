"""
Main router for all integrations.

This module collects and organizes all integration routers
into a single FastAPI router structure.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies.auth import get_current_user
from app.integrations.base.factory import get_available_integrations
from app.integrations.crm.hubspot.router import router as hubspot_router

# Import additional integrations as they are implemented
# from app.integrations.crm.salesforce.router import router as salesforce_router
# from app.integrations.crm.pipedrive.router import router as pipedrive_router
# from app.integrations.pos.square.router import router as square_router
# from app.integrations.pos.toast.router import router as toast_router
# from app.integrations.pos.lightspeed.router import router as lightspeed_router

logger = logging.getLogger(__name__)

# Main integrations router
router = APIRouter(
    prefix="/integrations",
    tags=["integrations"],
)

# CRM integrations router
crm_router = APIRouter(
    prefix="/crm",
    tags=["crm-integrations"],
)

# POS integrations router
pos_router = APIRouter(
    prefix="/pos",
    tags=["pos-integrations"],
)

# Include integration type routers in main router
router.include_router(crm_router)
router.include_router(pos_router)

# Include platform-specific routers in their respective type routers
crm_router.include_router(hubspot_router)
# Include other CRM routers as they are implemented
# crm_router.include_router(salesforce_router)
# crm_router.include_router(pipedrive_router)

# Include POS routers as they are implemented
# pos_router.include_router(square_router)
# pos_router.include_router(toast_router)
# pos_router.include_router(lightspeed_router)


@router.get(
    "/available",
    summary="Get available integrations",
    description="Get a list of all available integrations and their capabilities"
)
async def list_available_integrations(
    integration_type: str = None,
    current_user: dict = Depends(get_current_user),
):
    """
    Get a list of available integrations.
    
    Args:
        integration_type: Optional filter for integration type (crm, pos, erp)
        current_user: Current authenticated user
        
    Returns:
        Dict of available integrations
    """
    try:
        integrations = get_available_integrations(integration_type)
        return integrations
    except Exception as e:
        logger.error(f"Error retrieving available integrations: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )
