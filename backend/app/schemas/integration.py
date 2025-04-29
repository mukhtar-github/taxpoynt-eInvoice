from uuid import UUID
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, constr, validator # type: ignore


# Shared properties
class IntegrationBase(BaseModel):
    name: constr(min_length=1, max_length=100) # type: ignore
    description: Optional[str] = None
    config: Dict[str, Any]


# Properties to receive on integration creation
class IntegrationCreate(IntegrationBase):
    client_id: UUID


# Properties to receive on integration update
class IntegrationUpdate(BaseModel):
    name: Optional[constr(min_length=1, max_length=100)] = None # type: ignore
    description: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    status: Optional[str] = None

    @validator('status')
    def validate_status(cls, v):
        allowed_statuses = ['configured', 'active', 'failed', 'paused']
        if v not in allowed_statuses:
            raise ValueError(f'Status must be one of {allowed_statuses}')
        return v


# Properties shared by models in DB
class IntegrationInDBBase(IntegrationBase):
    id: UUID
    client_id: UUID
    created_at: datetime
    updated_at: datetime
    created_by: Optional[UUID] = None
    last_tested: Optional[datetime] = None
    status: str

    class Config:
        orm_mode = True


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
        orm_mode = True


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