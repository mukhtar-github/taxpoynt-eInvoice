from uuid import UUID
from datetime import datetime
from typing import Optional, Dict, Any, List, Literal
from pydantic import BaseModel, constr, validator, HttpUrl, Field # type: ignore
from enum import Enum

# Integration types
class IntegrationType(str, Enum):
    ODOO = "odoo"
    CUSTOM = "custom"


# Odoo Authentication Methods
class OdooAuthMethod(str, Enum):
    PASSWORD = "password"
    API_KEY = "api_key"


# FIRS Environment Types
class FIRSEnvironment(str, Enum):
    SANDBOX = "sandbox"
    PRODUCTION = "production"


# Odoo-specific configuration schema
class OdooConfig(BaseModel):
    url: HttpUrl = Field(..., description="Odoo server URL (e.g., https://example.odoo.com)")
    database: str = Field(..., description="Odoo database name")
    username: str = Field(..., description="Odoo username (email)")
    auth_method: OdooAuthMethod = Field(default=OdooAuthMethod.API_KEY, description="Authentication method")
    password: Optional[str] = Field(None, description="Password (if auth_method is 'password')")
    api_key: Optional[str] = Field(None, description="API key (if auth_method is 'api_key')")
    version: str = Field(default="16.0", description="Odoo version")
    rpc_path: str = Field(default="/jsonrpc", description="RPC endpoint path")
    timeout: int = Field(default=30, description="Connection timeout in seconds")
    firs_environment: FIRSEnvironment = Field(default=FIRSEnvironment.SANDBOX, description="FIRS environment (sandbox or production)")
    include_draft_invoices: bool = Field(default=False, description="Include draft invoices in sync")
    fetch_attachments: bool = Field(default=False, description="Fetch invoice PDF attachments")
    max_records_per_page: int = Field(default=100, ge=10, le=500, description="Maximum records per page for pagination")
    
    @validator('api_key')
    def validate_api_key(cls, v, values):
        if values.get('auth_method') == OdooAuthMethod.API_KEY and not v:
            raise ValueError('API key is required when auth_method is api_key')
        return v
    
    @validator('password')
    def validate_password(cls, v, values):
        if values.get('auth_method') == OdooAuthMethod.PASSWORD and not v:
            raise ValueError('Password is required when auth_method is password')
        return v


# Sync frequency options
class SyncFrequency(str, Enum):
    REALTIME = "realtime"
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"


# Shared properties
class IntegrationBase(BaseModel):
    name: constr(min_length=1, max_length=100) # type: ignore
    description: Optional[str] = None
    integration_type: IntegrationType = IntegrationType.CUSTOM
    config: Dict[str, Any]
    sync_frequency: SyncFrequency = SyncFrequency.HOURLY


# Properties to receive on integration creation
class IntegrationCreate(IntegrationBase):
    client_id: UUID


# Properties to receive on integration update
class IntegrationUpdate(BaseModel):
    name: Optional[constr(min_length=1, max_length=100)] = None # type: ignore
    description: Optional[str] = None
    integration_type: Optional[IntegrationType] = None
    config: Optional[Dict[str, Any]] = None
    status: Optional[str] = None
    sync_frequency: Optional[SyncFrequency] = None

    @validator('status')
    def validate_status(cls, v):
        allowed_statuses = ['configured', 'active', 'failed', 'paused']
        if v not in allowed_statuses:
            raise ValueError(f'Status must be one of {allowed_statuses}')
        return v


# Odoo Integration Create
class OdooIntegrationCreate(BaseModel):
    client_id: UUID
    name: constr(min_length=1, max_length=100) # type: ignore
    description: Optional[str] = None
    odoo_config: OdooConfig
    sync_frequency: SyncFrequency = SyncFrequency.HOURLY


# Properties shared by models in DB
class IntegrationInDBBase(IntegrationBase):
    id: UUID
    client_id: UUID
    created_at: datetime
    updated_at: datetime
    created_by: Optional[UUID] = None
    last_tested: Optional[datetime] = None
    last_sync: Optional[datetime] = None
    next_sync: Optional[datetime] = None
    status: str

    class Config:
        from_attributes = True


# Properties to return to client
class Integration(IntegrationInDBBase):
    pass


# Properties stored in DB
class IntegrationInDB(IntegrationInDBBase):
    pass


# Integration History
class IntegrationHistoryBase(BaseModel):
    integration_id: UUID
    changed_by: UUID
    previous_config: Optional[Dict[str, Any]] = None
    new_config: Dict[str, Any]
    change_reason: Optional[str] = None


class IntegrationHistoryCreate(IntegrationHistoryBase):
    pass


class IntegrationHistoryInDBBase(IntegrationHistoryBase):
    id: UUID
    changed_at: datetime

    class Config:
        from_attributes = True


class IntegrationHistory(IntegrationHistoryInDBBase):
    pass


class IntegrationHistoryInDB(IntegrationHistoryInDBBase):
    pass


# Integration Test Response
class IntegrationTestResult(BaseModel):
    success: bool
    message: str
    details: Optional[Dict[str, Any]] = None


# Integration Template Create
class IntegrationTemplateCreate(BaseModel):
    template_id: str
    client_id: UUID
    config_values: Optional[Dict[str, Any]] = None


# Odoo Connection Test Request
class OdooConnectionTestRequest(BaseModel):
    url: HttpUrl
    database: str
    username: str
    auth_method: OdooAuthMethod
    password: Optional[str] = None
    api_key: Optional[str] = None
    firs_environment: FIRSEnvironment = FIRSEnvironment.SANDBOX


# Integration Monitoring Status
class IntegrationMonitoringStatus(BaseModel):
    integration_id: str
    name: str
    status: str
    last_checked: Optional[datetime] = None
    next_check: Optional[datetime] = None
    uptime_percentage: Optional[float] = None
    consecutive_failures: int = 0
    last_error: Optional[str] = None
    is_being_monitored: bool = False
    
    class Config:
        from_attributes = True


# Odoo Invoice Fetch Parameters
class OdooInvoiceFetchParams(BaseModel):
    from_date: Optional[datetime] = Field(None, description="Fetch invoices from this date")
    to_date: Optional[datetime] = Field(None, description="Fetch invoices up to this date")
    include_draft: bool = Field(False, description="Include draft invoices")
    include_attachments: bool = Field(False, description="Include invoice PDF attachments")
    page: int = Field(1, ge=1, description="Page number for pagination")
    page_size: int = Field(20, ge=1, le=100, description="Number of items per page")


# Integration Configuration Export/Import
class IntegrationExport(BaseModel):
    integration_id: UUID
    name: str
    description: Optional[str] = None
    integration_type: IntegrationType
    config: Dict[str, Any]
    sync_frequency: SyncFrequency
    created_at: datetime
    exported_at: datetime = Field(default_factory=datetime.utcnow)
    export_version: str = "1.0"


class IntegrationImport(BaseModel):
    name: str
    description: Optional[str] = None
    integration_type: IntegrationType
    config: Dict[str, Any]
    sync_frequency: SyncFrequency
    client_id: UUID