"""
Submission metrics schema definitions.

This module defines Pydantic models for submission metrics API responses,
including invoice processing metrics and status visualizations.
"""
from typing import Dict, List, Any, Optional, Union
from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime


class HourlySubmissionModel(BaseModel):
    """Model for hourly submission data."""
    hour: int
    timestamp: str
    total: int
    success: int
    failed: int
    pending: int
    success_rate: float


class DailySubmissionModel(BaseModel):
    """Model for daily submission data."""
    day: int
    date: str
    total: int
    success: int
    failed: int
    pending: int
    success_rate: float


class StatusBreakdownModel(BaseModel):
    """Model for submission status breakdown."""
    status: str
    count: int
    percentage: float


class ErrorTypeModel(BaseModel):
    """Model for submission error types."""
    error_type: str
    count: int
    percentage: float
    severity: str


class SubmissionSummaryModel(BaseModel):
    """Summary model for submission metrics."""
    total_submissions: int
    success_count: int
    failed_count: int
    pending_count: int
    success_rate: float
    avg_processing_time: float  # in seconds
    common_errors: List[ErrorTypeModel]


class SubmissionMetricsResponse(BaseModel):
    """Response model for submission metrics."""
    timestamp: str
    summary: SubmissionSummaryModel
    status_breakdown: List[StatusBreakdownModel]
    hourly_submissions: List[HourlySubmissionModel]
    daily_submissions: List[DailySubmissionModel]
    common_errors: List[ErrorTypeModel]
    time_range: str


class RetryMetricsModel(BaseModel):
    """Model for retry metrics."""
    total_retries: int
    success_count: int
    failed_count: int
    pending_count: int
    success_rate: float
    avg_attempts: float
    max_attempts_reached_count: int


class RetryMetricsResponse(BaseModel):
    """Response model for retry metrics."""
    timestamp: str
    metrics: RetryMetricsModel
    retry_breakdown_by_status: List[StatusBreakdownModel]
    retry_breakdown_by_severity: List[StatusBreakdownModel]
    time_range: str
