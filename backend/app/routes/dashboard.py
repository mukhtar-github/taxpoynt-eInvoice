"""
Dashboard API routes.

This module provides API routes for the monitoring dashboard,
including metrics for IRN generation, validation, Odoo integration,
and system health.
"""
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_active_superuser, get_current_active_user
from app.dependencies.db import get_db
from app.schemas.user import User
from app.services.metrics_service import MetricsService
from app.schemas.dashboard import (
    DashboardSummaryResponse, 
    IRNMetricsResponse,
    ValidationMetricsResponse,
    B2BVsB2CMetricsResponse,
    OdooIntegrationMetricsResponse,
    SystemHealthMetricsResponse,
    TimeRangeEnum
)

router = APIRouter(
    prefix="/dashboard",
    tags=["dashboard"],
    responses={404: {"description": "Not found"}},
)


@router.get("/summary", response_model=DashboardSummaryResponse)
async def get_dashboard_summary(
    organization_id: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get a summary of all metrics for the dashboard.
    """
    return MetricsService.get_dashboard_summary(db, organization_id)


@router.get("/irn", response_model=IRNMetricsResponse)
async def get_irn_metrics(
    time_range: TimeRangeEnum = TimeRangeEnum.DAY,
    organization_id: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get metrics about IRN generation.
    """
    return MetricsService.get_irn_generation_metrics(db, time_range.value, organization_id)


@router.get("/validation", response_model=ValidationMetricsResponse)
async def get_validation_metrics(
    time_range: TimeRangeEnum = TimeRangeEnum.DAY,
    organization_id: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get metrics about invoice validation.
    """
    return MetricsService.get_validation_metrics(db, time_range.value, organization_id)


@router.get("/b2b-vs-b2c", response_model=B2BVsB2CMetricsResponse)
async def get_b2b_vs_b2c_metrics(
    time_range: TimeRangeEnum = TimeRangeEnum.DAY,
    organization_id: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get metrics comparing B2B vs B2C invoice processing.
    """
    return MetricsService.get_b2b_vs_b2c_metrics(db, time_range.value, organization_id)


@router.get("/odoo", response_model=OdooIntegrationMetricsResponse)
async def get_odoo_integration_metrics(
    time_range: TimeRangeEnum = TimeRangeEnum.DAY,
    organization_id: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get metrics about Odoo integration status and performance.
    """
    return MetricsService.get_odoo_integration_metrics(db, time_range.value, organization_id)


@router.get("/system-health", response_model=SystemHealthMetricsResponse)
async def get_system_health_metrics(
    time_range: TimeRangeEnum = TimeRangeEnum.DAY,
    current_user: User = Depends(get_current_active_superuser),
    db: Session = Depends(get_db)
):
    """
    Get metrics about overall system health.
    Only accessible to superusers.
    """
    return MetricsService.get_system_health_metrics(db, time_range.value)
