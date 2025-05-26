"""
Entity Lookup Router.

This module provides endpoints for looking up business entities via the FIRS API
with proper authentication handling and error management.
"""
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import logging
import uuid

from app.services.firs_service import firs_service
from app.dependencies.auth import get_current_user
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/entity",
    tags=["Entity Lookup"],
    responses={404: {"description": "Not found"}},
)


class EntityLookupResponse(BaseModel):
    """Response model for entity lookup."""
    success: bool = Field(..., description="Whether the lookup was successful")
    message: str = Field(..., description="Status message")
    entity: Optional[Dict[str, Any]] = Field(None, description="Entity details if found")
    error: Optional[Dict[str, Any]] = Field(None, description="Error details if lookup failed")


@router.get("/lookup/{tin}", response_model=EntityLookupResponse)
async def lookup_entity_by_tin(
    tin: str,
    use_sandbox: Optional[bool] = None,
    current_user: User = Depends(get_current_user)
) -> EntityLookupResponse:
    """
    Look up an entity by TIN with proper authentication.
    
    This endpoint handles the authentication flow and format conversion
    required by the FIRS API.
    
    Args:
        tin: The Tax Identification Number (TIN) to look up
        use_sandbox: Override sandbox setting (optional)
        current_user: Authenticated user
        
    Returns:
        EntityLookupResponse with entity details if found
    """
    try:
        logger.info(f"Looking up entity with TIN: {tin} (User: {current_user.email})")
        
        # Step 1: Try direct lookup first (some FIRS API implementations support TIN lookup)
        try:
            # Try direct lookup with TIN
            entity = await firs_service.get_entity(tin)
            return EntityLookupResponse(
                success=True,
                message=f"Entity found with TIN: {tin}",
                entity=entity
            )
        except HTTPException as e:
            if e.status_code != 400:  # If it's not a validation error, re-raise
                raise
            logger.info(f"Direct TIN lookup failed, trying search method")
        
        # Step 2: If direct lookup fails, try searching by reference
        search_params = {"reference": tin}
        search_results = await firs_service.search_entities(search_params)
        
        # Check if we have results
        items = search_results.get("data", {}).get("items", [])
        if items and len(items) > 0:
            # Found at least one match
            entity = items[0]  # Get the first match
            return EntityLookupResponse(
                success=True,
                message=f"Entity found by search with TIN: {tin}",
                entity=entity
            )
            
        # Step 3: If all else fails, try party transmit lookup
        # This approach is specific to FIRS API and uses a different endpoint
        # Implement only if needed - would require extending the FIRS service
        
        # No entity found
        return EntityLookupResponse(
            success=False,
            message=f"No entity found with TIN: {tin}",
            error={
                "code": "ENTITY_NOT_FOUND",
                "message": f"No entity found with TIN: {tin}"
            }
        )
        
    except HTTPException as e:
        logger.error(f"Error looking up entity: {str(e)}")
        return EntityLookupResponse(
            success=False,
            message=f"Error looking up entity: {e.detail}",
            error={
                "code": e.status_code,
                "message": str(e.detail)
            }
        )
    except Exception as e:
        logger.error(f"Unexpected error looking up entity: {str(e)}")
        return EntityLookupResponse(
            success=False,
            message=f"Unexpected error looking up entity: {str(e)}",
            error={
                "code": "INTERNAL_ERROR",
                "message": str(e)
            }
        )
