"""POS integration schemas for API requests and responses."""

from datetime import datetime
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field


class POSConnectionCreate(BaseModel):
    """Schema for creating a new POS connection."""
    name: str = Field(..., description="Connection name")
    platform: str = Field(..., description="POS platform (square, toast, lightspeed)")
    location_id: Optional[str] = Field(None, description="POS location/store ID")
    
    # Authentication credentials (will be encrypted)
    access_token: str = Field(..., description="POS platform access token")
    refresh_token: Optional[str] = Field(None, description="Refresh token if applicable")
    
    # Webhook configuration
    webhook_url: Optional[str] = Field(None, description="Webhook endpoint URL")
    webhook_secret: Optional[str] = Field(None, description="Webhook secret for signature verification")
    
    # Platform-specific configuration
    environment: Optional[str] = Field("production", description="Environment (sandbox/production)")
    application_id: Optional[str] = Field(None, description="Application ID for the platform")
    merchant_id: Optional[str] = Field(None, description="Merchant ID")
    
    # Additional configuration
    auto_invoice_generation: bool = Field(True, description="Automatically generate invoices for transactions")
    real_time_sync: bool = Field(True, description="Enable real-time transaction sync")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional configuration metadata")


class POSConnectionUpdate(BaseModel):
    """Schema for updating POS connection."""
    name: Optional[str] = None
    location_id: Optional[str] = None
    webhook_url: Optional[str] = None
    webhook_secret: Optional[str] = None
    auto_invoice_generation: Optional[bool] = None
    real_time_sync: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None


class POSConnectionResponse(BaseModel):
    """Schema for POS connection response."""
    id: str
    name: str
    platform: str
    location_id: Optional[str]
    status: str  # active, inactive, error
    webhook_url: Optional[str]
    environment: str
    auto_invoice_generation: bool
    real_time_sync: bool
    
    # Connection health
    last_sync_at: Optional[datetime]
    last_error: Optional[str]
    transaction_count: int = 0
    
    # Metadata
    created_at: datetime
    updated_at: datetime
    metadata: Optional[Dict[str, Any]] = None


class POSWebhookPayload(BaseModel):
    """Schema for incoming POS webhook payloads."""
    event_type: str
    event_id: str
    timestamp: datetime
    source: str
    data: Dict[str, Any]
    signature: Optional[str] = None
    merchant_id: Optional[str] = None
    location_id: Optional[str] = None


class POSTransactionCreate(BaseModel):
    """Schema for creating a transaction record."""
    transaction_id: str
    connection_id: str
    location_id: str
    amount: float
    currency: str = "USD"
    payment_method: str
    timestamp: datetime
    
    # Optional transaction details
    items: List[Dict[str, Any]] = []
    customer_info: Optional[Dict[str, Any]] = None
    tax_info: Optional[Dict[str, Any]] = None
    
    # Platform-specific data
    platform_data: Optional[Dict[str, Any]] = None
    receipt_number: Optional[str] = None
    receipt_url: Optional[str] = None


class POSTransactionResponse(BaseModel):
    """Schema for POS transaction response."""
    id: str
    transaction_id: str
    connection_id: str
    location_id: str
    amount: float
    currency: str
    payment_method: str
    timestamp: datetime
    
    # Processing status
    status: str  # pending, processed, error, cancelled
    invoice_generated: bool = False
    invoice_id: Optional[str] = None
    firs_submitted: bool = False
    irn: Optional[str] = None
    
    # Transaction details
    items: List[Dict[str, Any]] = []
    customer_info: Optional[Dict[str, Any]] = None
    tax_info: Optional[Dict[str, Any]] = None
    
    # Metadata
    created_at: datetime
    updated_at: datetime
    platform_data: Optional[Dict[str, Any]] = None
    receipt_number: Optional[str] = None
    receipt_url: Optional[str] = None


class POSLocationResponse(BaseModel):
    """Schema for POS location information."""
    location_id: str
    connection_id: str
    name: str
    platform: str
    
    # Location details
    address: Optional[Dict[str, Any]] = None
    timezone: Optional[str] = None
    currency: str = "USD"
    
    # Business information
    business_name: Optional[str] = None
    business_type: Optional[str] = None
    contact_info: Optional[Dict[str, Any]] = None
    
    # Tax and compliance
    tax_settings: Optional[Dict[str, Any]] = None
    tax_id: Optional[str] = None
    
    # Sync status
    last_sync_at: Optional[datetime] = None
    sync_status: str = "active"  # active, inactive, error
    
    # Metadata
    created_at: datetime
    updated_at: datetime
    platform_data: Optional[Dict[str, Any]] = None


class POSWebhookTestRequest(BaseModel):
    """Schema for testing webhook connectivity."""
    connection_id: str
    test_type: str = "ping"  # ping, transaction_test, signature_test
    test_data: Optional[Dict[str, Any]] = None


class POSWebhookTestResponse(BaseModel):
    """Schema for webhook test results."""
    success: bool
    message: str
    test_type: str
    connection_id: str
    
    # Test details
    response_time_ms: Optional[float] = None
    signature_valid: Optional[bool] = None
    webhook_url: Optional[str] = None
    
    # Error information
    error_code: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None
    
    # Timestamp
    tested_at: datetime = Field(default_factory=datetime.now)


class POSSyncRequest(BaseModel):
    """Schema for manual sync requests."""
    connection_id: str
    sync_type: str = "transactions"  # transactions, locations, inventory
    date_range: Optional[Dict[str, datetime]] = None
    force_refresh: bool = False


class POSSyncResponse(BaseModel):
    """Schema for sync operation results."""
    success: bool
    connection_id: str
    sync_type: str
    
    # Sync statistics
    items_processed: int = 0
    items_created: int = 0
    items_updated: int = 0
    items_failed: int = 0
    
    # Timing
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    
    # Results
    errors: List[Dict[str, Any]] = []
    warnings: List[str] = []
    summary: Optional[Dict[str, Any]] = None


class POSHealthCheckResponse(BaseModel):
    """Schema for POS connection health check."""
    connection_id: str
    platform: str
    status: str  # healthy, unhealthy, degraded
    
    # Health indicators
    api_connectivity: bool
    webhook_connectivity: Optional[bool] = None
    last_successful_sync: Optional[datetime] = None
    error_rate: float = 0.0
    
    # Performance metrics
    avg_response_time_ms: Optional[float] = None
    uptime_percentage: Optional[float] = None
    
    # Current issues
    current_errors: List[str] = []
    warnings: List[str] = []
    
    # Check timestamp
    checked_at: datetime = Field(default_factory=datetime.now)


class POSMetricsResponse(BaseModel):
    """Schema for POS connection metrics."""
    connection_id: str
    time_period: str  # hourly, daily, weekly, monthly
    
    # Transaction metrics
    total_transactions: int = 0
    total_amount: float = 0.0
    avg_transaction_amount: float = 0.0
    
    # Processing metrics
    successful_invoices: int = 0
    failed_invoices: int = 0
    firs_submissions: int = 0
    
    # Performance metrics
    avg_processing_time_ms: float = 0.0
    error_rate: float = 0.0
    uptime_percentage: float = 100.0
    
    # Time range
    start_date: datetime
    end_date: datetime
    
    # Detailed breakdown
    daily_breakdown: Optional[List[Dict[str, Any]]] = None
    payment_method_breakdown: Optional[Dict[str, int]] = None
    location_breakdown: Optional[Dict[str, int]] = None