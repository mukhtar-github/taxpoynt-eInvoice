"""
Version 1 Response Models
========================
Standardized response models for API v1 endpoints.
"""
from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field
from datetime import datetime


class V1ResponseModel(BaseModel):
    """Standard v1 response format"""
    success: bool = True
    action: str = Field(..., description="Action that was performed")
    api_version: str = Field(default="v1", description="API version")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    data: Dict[str, Any] = Field(..., description="Response data")
    meta: Optional[Dict[str, Any]] = Field(default=None, description="Metadata")


class V1ErrorModel(BaseModel):
    """Standard v1 error format"""
    success: bool = False
    error: str = Field(..., description="Error message")
    error_code: str = Field(..., description="Error code")
    api_version: str = Field(default="v1", description="API version")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Error details")


class V1PaginationModel(BaseModel):
    """Standard v1 pagination"""
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=50, ge=1, le=1000)
    total: int = Field(..., ge=0)
    has_next: bool
    has_prev: bool


class V1BusinessSystemInfo(BaseModel):
    """Business system information for v1"""
    system_type: str = Field(..., description="Type of business system (erp, crm, pos, etc.)")
    system_name: str = Field(..., description="Name of the system (sap, salesforce, etc.)")
    connection_id: str = Field(..., description="Unique connection identifier")
    status: str = Field(..., description="Connection status")
    last_sync: Optional[datetime] = Field(default=None, description="Last sync timestamp")
    organization_id: str = Field(..., description="Associated organization ID")