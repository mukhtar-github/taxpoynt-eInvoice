"""
Advanced CRM Features API Endpoints.

This module provides API endpoints for the advanced CRM features:
- Cross-platform data mapping capabilities
- Templating system for invoice generation from deals
- Pipeline stage tracking for predictive invoicing
"""

import logging
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
from app.integrations.crm.data_mapper import cross_platform_mapper, PlatformMapping, FieldMapping, FieldType
from app.integrations.crm.template_engine import template_engine, InvoiceTemplate, TemplateType, OutputFormat
from app.integrations.crm.pipeline_tracker import get_pipeline_tracker

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/crm/advanced",
    tags=["advanced-crm-features"],
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

class DataMappingRequest(BaseModel):
    """Request model for data mapping operations."""
    source_data: Dict[str, Any] = Field(..., description="Source data to map")
    source_platform: str = Field(..., description="Source platform name")
    target_format: str = Field("taxpoynt", description="Target format")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional context for mapping")

    class Config:
        schema_extra = {
            "example": {
                "source_data": {
                    "properties": {
                        "dealname": "Enterprise Software License",
                        "amount": "50000",
                        "dealstage": "closedwon"
                    },
                    "id": "123456789"
                },
                "source_platform": "hubspot",
                "target_format": "taxpoynt",
                "context": {"source_currency": "USD", "target_currency": "NGN"}
            }
        }


class InvoiceGenerationRequest(BaseModel):
    """Request model for invoice generation from deals."""
    template_id: Optional[str] = Field(None, description="Template ID to use")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional context")
    output_format: OutputFormat = Field(OutputFormat.JSON, description="Output format")

    class Config:
        schema_extra = {
            "example": {
                "template_id": "hubspot_default",
                "context": {"custom_tax_rate": 10.0},
                "output_format": "json"
            }
        }


class PredictiveInsightsResponse(BaseModel):
    """Response model for predictive insights."""
    deal_id: str
    current_stage: str
    predicted_next_stage: str
    probability_of_transition: float
    predicted_transition_date: datetime
    predicted_close_date: datetime
    win_probability: float
    forecasted_amount: float
    confidence_level: str
    recommendation: str
    factors: List[str]


# ==================== DATA MAPPING ENDPOINTS ====================

@router.post(
    "/data-mapping/map",
    summary="Map CRM data to TaxPoynt format",
    description="Transform data between different CRM platforms and TaxPoynt format using advanced mapping capabilities",
)
async def map_crm_data(
    mapping_request: DataMappingRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Map CRM data to TaxPoynt format using cross-platform data mapping.
    
    Args:
        mapping_request: Data mapping request
        current_user: Current authenticated user
        
    Returns:
        Dict with mapped data
    """
    try:
        logger.info(f"Data mapping requested by user {current_user.id} for platform {mapping_request.source_platform}")
        
        mapped_data = cross_platform_mapper.map_data(
            source_data=mapping_request.source_data,
            source_platform=mapping_request.source_platform,
            target_format=mapping_request.target_format,
            context=mapping_request.context
        )
        
        return {
            "success": True,
            "data": {
                "mapped_data": mapped_data,
                "source_platform": mapping_request.source_platform,
                "target_format": mapping_request.target_format,
                "mapping_applied": True
            }
        }
        
    except Exception as e:
        logger.error(f"Error mapping CRM data: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to map CRM data: {str(e)}"
        )


@router.get(
    "/data-mapping/platforms",
    summary="Get supported mapping platforms",
    description="Retrieve list of supported CRM platforms for data mapping",
)
async def get_mapping_platforms(
    current_user: User = Depends(get_current_user)
):
    """
    Get list of supported platforms for data mapping.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Dict with supported platforms
    """
    try:
        platforms = cross_platform_mapper.get_supported_platforms()
        
        return {
            "success": True,
            "data": {
                "platforms": platforms,
                "total_platforms": len(platforms)
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting mapping platforms: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get mapping platforms: {str(e)}"
        )


# ==================== TEMPLATING ENDPOINTS ====================

@router.post(
    "/templates/generate-invoice/{connection_id}/deals/{deal_id}",
    summary="Generate invoice from deal using template",
    description="Generate an invoice from a CRM deal using the templating system",
)
async def generate_invoice_from_deal(
    connection_id: UUID = Path(..., description="CRM connection ID"),
    deal_id: UUID = Path(..., description="Deal ID"),
    generation_request: InvoiceGenerationRequest = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate invoice from CRM deal using templating system.
    
    Args:
        connection_id: CRM connection ID
        deal_id: Deal ID
        generation_request: Invoice generation request
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Dict with generated invoice
    """
    try:
        # Validate connection access
        connection = db.query(CRMConnection).filter(
            CRMConnection.id == connection_id,
            CRMConnection.organization_id == current_user.organization_id
        ).first()
        
        if not connection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"CRM connection {connection_id} not found"
            )
        
        # Get deal data
        deal = db.query(CRMDeal).filter(
            CRMDeal.id == deal_id,
            CRMDeal.connection_id == connection_id
        ).first()
        
        if not deal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Deal {deal_id} not found"
            )
        
        logger.info(f"Generating invoice from deal {deal_id} for user {current_user.id}")
        
        # Use appropriate template based on platform
        template_id = generation_request.template_id or f"{connection.crm_type.value}_default"
        
        # Generate invoice using template engine
        invoice = template_engine.generate_invoice(
            deal_data=deal.deal_data,
            template_id=template_id,
            context=generation_request.context,
            output_format=generation_request.output_format
        )
        
        return {
            "success": True,
            "data": {
                "invoice": invoice,
                "deal_id": str(deal_id),
                "connection_id": str(connection_id),
                "template_id": template_id,
                "output_format": generation_request.output_format.value,
                "generated_at": datetime.utcnow().isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating invoice from deal {deal_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate invoice: {str(e)}"
        )


@router.get(
    "/templates/available",
    summary="Get available invoice templates",
    description="Retrieve list of available invoice templates for different CRM platforms",
)
async def get_available_templates(
    platform: Optional[str] = Query(None, description="Filter by CRM platform"),
    current_user: User = Depends(get_current_user)
):
    """
    Get list of available invoice templates.
    
    Args:
        platform: Optional platform filter
        current_user: Current authenticated user
        
    Returns:
        Dict with available templates
    """
    try:
        templates = template_engine.get_available_templates(platform)
        
        return {
            "success": True,
            "data": {
                "templates": templates,
                "total_templates": len(templates),
                "platform_filter": platform
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting available templates: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get available templates: {str(e)}"
        )


# ==================== PIPELINE TRACKING ENDPOINTS ====================

@router.get(
    "/pipeline/insights/{connection_id}/deals/{deal_id}",
    summary="Get predictive insights for deal",
    description="Get predictive insights and recommendations for a specific deal",
)
async def get_deal_predictive_insights(
    connection_id: UUID = Path(..., description="CRM connection ID"),
    deal_id: UUID = Path(..., description="Deal ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get predictive insights for a specific deal.
    
    Args:
        connection_id: CRM connection ID
        deal_id: Deal ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Dict with predictive insights
    """
    try:
        # Validate connection access
        connection = db.query(CRMConnection).filter(
            CRMConnection.id == connection_id,
            CRMConnection.organization_id == current_user.organization_id
        ).first()
        
        if not connection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"CRM connection {connection_id} not found"
            )
        
        # Get deal data
        deal = db.query(CRMDeal).filter(
            CRMDeal.id == deal_id,
            CRMDeal.connection_id == connection_id
        ).first()
        
        if not deal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Deal {deal_id} not found"
            )
        
        logger.info(f"Getting predictive insights for deal {deal_id} by user {current_user.id}")
        
        # Get platform-specific tracker
        tracker = get_pipeline_tracker(connection.crm_type.value)
        
        # Generate predictive insights
        insights = tracker.generate_predictive_insights(str(deal_id))
        
        if not insights:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No predictive insights available for deal {deal_id}"
            )
        
        return {
            "success": True,
            "data": {
                "insights": {
                    "deal_id": insights.deal_id,
                    "current_stage": insights.current_stage,
                    "predicted_next_stage": insights.predicted_next_stage,
                    "probability_of_transition": float(insights.probability_of_transition),
                    "predicted_transition_date": insights.predicted_transition_date.isoformat(),
                    "predicted_close_date": insights.predicted_close_date.isoformat(),
                    "win_probability": float(insights.win_probability),
                    "forecasted_amount": float(insights.forecasted_amount),
                    "confidence_level": insights.confidence_level,
                    "recommendation": insights.recommendation,
                    "factors": insights.factors
                },
                "generated_at": datetime.utcnow().isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting predictive insights for deal {deal_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get predictive insights: {str(e)}"
        )


@router.get(
    "/pipeline/metrics/{connection_id}",
    summary="Get pipeline metrics",
    description="Get comprehensive pipeline metrics and analytics for a CRM connection",
)
async def get_pipeline_metrics(
    connection_id: UUID = Path(..., description="CRM connection ID"),
    days_back: int = Query(90, ge=1, le=365, description="Number of days to analyze"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get pipeline metrics and analytics for a CRM connection.
    
    Args:
        connection_id: CRM connection ID
        days_back: Number of days to analyze
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Dict with pipeline metrics
    """
    try:
        # Validate connection access
        connection = db.query(CRMConnection).filter(
            CRMConnection.id == connection_id,
            CRMConnection.organization_id == current_user.organization_id
        ).first()
        
        if not connection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"CRM connection {connection_id} not found"
            )
        
        logger.info(f"Getting pipeline metrics for connection {connection_id} by user {current_user.id}")
        
        # Get platform-specific tracker
        tracker = get_pipeline_tracker(connection.crm_type.value)
        
        # Calculate pipeline metrics
        metrics = tracker.calculate_pipeline_metrics(days_back=days_back)
        
        return {
            "success": True,
            "data": {
                "metrics": {
                    "total_deals": metrics.total_deals,
                    "total_value": float(metrics.total_value),
                    "average_deal_size": float(metrics.average_deal_size),
                    "conversion_rate": float(metrics.conversion_rate),
                    "average_cycle_time_days": metrics.average_cycle_time.days,
                    "stage_conversion_rates": {k: float(v) for k, v in metrics.stage_conversion_rates.items()},
                    "velocity_metrics": {k: float(v) for k, v in metrics.velocity_metrics.items()},
                    "forecasted_revenue": float(metrics.forecasted_revenue),
                    "confidence_score": float(metrics.confidence_score)
                },
                "analysis_period_days": days_back,
                "connection_id": str(connection_id),
                "platform": connection.crm_type.value,
                "generated_at": datetime.utcnow().isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting pipeline metrics for connection {connection_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get pipeline metrics: {str(e)}"
        )


@router.post(
    "/pipeline/track-stage-change/{connection_id}/deals/{deal_id}",
    summary="Track deal stage change",
    description="Track and analyze a deal stage change for predictive insights",
)
async def track_deal_stage_change(
    connection_id: UUID = Path(..., description="CRM connection ID"),
    deal_id: UUID = Path(..., description="Deal ID"),
    stage_change: Dict[str, Any] = Body(..., description="Stage change data"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Track a deal stage change for predictive analytics.
    
    Args:
        connection_id: CRM connection ID
        deal_id: Deal ID
        stage_change: Stage change data
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Dict with tracking results
    """
    try:
        # Validate connection access
        connection = db.query(CRMConnection).filter(
            CRMConnection.id == connection_id,
            CRMConnection.organization_id == current_user.organization_id
        ).first()
        
        if not connection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"CRM connection {connection_id} not found"
            )
        
        # Get deal data
        deal = db.query(CRMDeal).filter(
            CRMDeal.id == deal_id,
            CRMDeal.connection_id == connection_id
        ).first()
        
        if not deal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Deal {deal_id} not found"
            )
        
        logger.info(f"Tracking stage change for deal {deal_id} by user {current_user.id}")
        
        # Get platform-specific tracker
        tracker = get_pipeline_tracker(connection.crm_type.value)
        
        # Track stage change
        from decimal import Decimal
        tracker.track_stage_change(
            deal_id=str(deal_id),
            from_stage=stage_change.get("from_stage"),
            to_stage=stage_change.get("to_stage"),
            deal_amount=Decimal(str(deal.deal_amount or "0")),
            metadata={
                "trigger_source": "api",
                "user_id": str(current_user.id),
                **stage_change.get("metadata", {})
            }
        )
        
        return {
            "success": True,
            "data": {
                "message": "Stage change tracked successfully",
                "deal_id": str(deal_id),
                "connection_id": str(connection_id),
                "stage_change": stage_change,
                "tracked_at": datetime.utcnow().isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error tracking stage change for deal {deal_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to track stage change: {str(e)}"
        )