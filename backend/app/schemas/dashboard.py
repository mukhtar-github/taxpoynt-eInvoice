"""
Dashboard schema definitions.

This module defines Pydantic models for dashboard API responses,
including metrics for IRN generation, validation, Odoo integration,
and system health.
"""
from typing import Dict, List, Any, Optional, Union
from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime


class TimeRangeEnum(str, Enum):
    """Time range options for metrics."""
    DAY = "24h"
    WEEK = "7d"
    MONTH = "30d"
    ALL = "all"


class CommonErrorModel(BaseModel):
    """Model for common validation errors."""
    error_code: str
    count: int
    percentage: float


class HourlyGenerationModel(BaseModel):
    """Model for hourly IRN generation data."""
    hour: int
    timestamp: str
    count: int


class DailyGenerationModel(BaseModel):
    """Model for daily IRN generation data."""
    day: int
    date: str
    count: int


class HourlyValidationModel(BaseModel):
    """Model for hourly validation data."""
    hour: int
    timestamp: str
    total: int
    success: int
    failure: int
    success_rate: float


class DailyB2BvsB2CModel(BaseModel):
    """Model for daily B2B vs B2C breakdown."""
    day: int
    date: str
    b2b_count: int
    b2c_count: int
    total: int


class IntegrationStatusModel(BaseModel):
    """Model for integration status."""
    integration_id: str
    name: str
    organization_id: str
    is_active: bool
    created_at: str
    last_validated: Optional[str] = None
    last_validation_success: Optional[bool] = None


class HourlyRequestModel(BaseModel):
    """Model for hourly API request data."""
    hour: int
    timestamp: str
    requests: int
    errors: int
    error_rate: float


class HourlyCountModel(BaseModel):
    """Model for hourly count data."""
    hour: int
    timestamp: str
    count: int


class EndpointPopularityModel(BaseModel):
    """Model for endpoint popularity data."""
    endpoint: str
    count: int
    percentage: float


class IRNSummaryModel(BaseModel):
    """Summary model for IRN metrics."""
    total_irns: int
    active_irns: int
    unused_irns: int
    expired_irns: int


class ValidationSummaryModel(BaseModel):
    """Summary model for validation metrics."""
    total_validations: int
    success_rate: float
    common_errors: List[CommonErrorModel]


class B2BVsB2CSummaryModel(BaseModel):
    """Summary model for B2B vs B2C metrics."""
    b2b_percentage: float
    b2c_percentage: float
    b2b_success_rate: float
    b2c_success_rate: float


class OdooSummaryModel(BaseModel):
    """Summary model for Odoo integration metrics."""
    active_integrations: int
    total_invoices: int
    success_rate: float


class SystemSummaryModel(BaseModel):
    """Summary model for system health metrics."""
    total_requests: int
    error_rate: float
    avg_response_time: float


class DashboardSummaryResponse(BaseModel):
    """Response model for dashboard summary."""
    timestamp: str
    irn_summary: IRNSummaryModel
    validation_summary: ValidationSummaryModel
    b2b_vs_b2c_summary: B2BVsB2CSummaryModel
    odoo_summary: OdooSummaryModel
    system_summary: SystemSummaryModel


class IRNMetricsResponse(BaseModel):
    """Response model for IRN generation metrics."""
    total_count: int
    status_counts: Dict[str, int]
    hourly_generation: List[HourlyGenerationModel]
    daily_generation: List[DailyGenerationModel]
    time_range: str


class ValidationMetricsResponse(BaseModel):
    """Response model for validation metrics."""
    total_count: int
    success_count: int
    failure_count: int
    success_rate: float
    common_errors: List[CommonErrorModel]
    hourly_validation: List[HourlyValidationModel]
    time_range: str


class B2BVsB2CMetricsResponse(BaseModel):
    """Response model for B2B vs B2C metrics."""
    total_count: int
    b2b_count: int
    b2c_count: int
    b2b_percentage: float
    b2c_percentage: float
    b2b_success_rate: float
    b2c_success_rate: float
    daily_breakdown: List[DailyB2BvsB2CModel]
    time_range: str


class OdooIntegrationMetricsResponse(BaseModel):
    """Response model for Odoo integration metrics."""
    total_integrations: int
    active_integrations: int
    inactive_integrations: int
    total_invoices: int
    successful_invoices: int
    success_rate: float
    integration_statuses: List[IntegrationStatusModel]
    hourly_counts: List[HourlyCountModel]
    time_range: str


class SystemHealthMetricsResponse(BaseModel):
    """Response model for system health metrics."""
    total_requests: int
    error_requests: int
    error_rate: float
    avg_response_time: float
    hourly_requests: List[HourlyRequestModel]
    endpoint_popularity: List[EndpointPopularityModel]
    time_range: str
