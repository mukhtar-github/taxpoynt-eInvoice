"""
Submission dashboard API routes.

This module provides API routes for the submission monitoring dashboard,
including metrics for invoice processing, status breakdowns, and retry analytics.
"""
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_active_user
from app.db.session import get_db
from app.schemas.user import User
from app.schemas.dashboard import TimeRangeEnum
from app.services.submission_metrics_service import SubmissionMetricsService
from app.schemas.submission_metrics import (
    SubmissionMetricsResponse,
    RetryMetricsResponse
)

router = APIRouter(
    prefix="/dashboard/submission",
    tags=["submission-dashboard"],
    responses={404: {"description": "Not found"}},
)


@router.get("/metrics", response_model=SubmissionMetricsResponse)
async def get_submission_metrics(
    time_range: TimeRangeEnum = TimeRangeEnum.DAY,
    organization_id: Optional[str] = None,
    integration_type: Optional[str] = None,
    status_filter: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get metrics about invoice submission processing.
    
    This endpoint provides comprehensive metrics about invoice submissions,
    including success rates, processing times, and error statistics.
    
    Args:
        time_range: Time range for metrics (24h, 7d, 30d, all)
        organization_id: Optional filter by organization
        integration_type: Optional filter by integration type
        status_filter: Optional filter by submission status
    """
    return SubmissionMetricsService.get_submission_metrics(
        db=db,
        time_range=time_range.value,
        organization_id=organization_id,
        integration_type=integration_type,
        status_filter=status_filter
    )


@router.get("/retry-metrics", response_model=RetryMetricsResponse)
async def get_retry_metrics(
    time_range: TimeRangeEnum = TimeRangeEnum.DAY,
    organization_id: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get metrics about submission retry attempts.
    
    This endpoint provides metrics about retry attempts for failed submissions,
    including success rates, common errors, and severity breakdowns.
    
    Args:
        time_range: Time range for metrics (24h, 7d, 30d, all)
        organization_id: Optional filter by organization
    """
    return SubmissionMetricsService.get_retry_metrics(
        db=db,
        time_range=time_range.value,
        organization_id=organization_id
    )


@router.get("/odoo-metrics", response_model=SubmissionMetricsResponse)
async def get_odoo_submission_metrics(
    time_range: TimeRangeEnum = TimeRangeEnum.DAY,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get metrics specific to Odoo invoice submissions.
    
    This endpoint provides specialized metrics for Odoo integration,
    focusing on the ERP-first integration strategy.
    
    Args:
        time_range: Time range for metrics (24h, 7d, 30d, all)
    """
    return SubmissionMetricsService.get_odoo_submission_metrics(
        db=db,
        time_range=time_range.value
    )
