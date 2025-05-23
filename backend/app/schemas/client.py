from uuid import UUID
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, constr # type: ignore


# Shared properties
class ClientBase(BaseModel):
    name: constr(min_length=1, max_length=100) # type: ignore
    tax_id: constr(min_length=1, max_length=50) # type: ignore
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    industry: Optional[str] = None


# Properties to receive on client creation
class ClientCreate(ClientBase):
    organization_id: UUID


# Properties to receive on client update
class ClientUpdate(BaseModel):
    name: Optional[constr(min_length=1, max_length=100)] = None # type: ignore
    tax_id: Optional[constr(min_length=1, max_length=50)] = None # type: ignore
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    industry: Optional[str] = None
    status: Optional[str] = None


# Properties shared by models in DB
class ClientInDBBase(ClientBase):
    id: UUID
    organization_id: UUID
    created_at: datetime
    updated_at: datetime
    status: str

    class Config:
        from_attributes = True


# Properties to return to client
class Client(ClientInDBBase):
    pass


# Properties stored in DB
class ClientInDB(ClientInDBBase):
    pass 