"""
Data models for HubSpot CRM integration.

This module defines the Pydantic models for HubSpot CRM integration
requests and responses.
"""

from datetime import datetime
from typing import Dict, Any, List, Optional

from pydantic import BaseModel, Field, validator


class HubSpotConnectionConfig(BaseModel):
    """Model for HubSpot connection configuration."""
    connection_id: Optional[str] = None
    organization_id: str
    user_id: str
    connection_name: Optional[str] = "HubSpot CRM"
    
    auth: Dict[str, Any] = Field(
        default_factory=lambda: {
            "auth_type": "oauth2",
            "token_url": "https://api.hubapi.com/oauth/v1/token",
            "scope": "crm.objects.deals.read crm.objects.contacts.read crm.objects.companies.read",
            "credentials": {
                "client_id": "",
                "client_secret": "",
                "refresh_token": ""
            }
        }
    )
    
    settings: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "organization_id": "550e8400-e29b-41d4-a716-446655440000",
                "user_id": "550e8400-e29b-41d4-a716-446655440001",
                "connection_name": "My HubSpot Account",
                "auth": {
                    "auth_type": "oauth2",
                    "token_url": "https://api.hubapi.com/oauth/v1/token",
                    "scope": "crm.objects.deals.read crm.objects.contacts.read crm.objects.companies.read",
                    "credentials": {
                        "client_id": "your-client-id",
                        "client_secret": "your-client-secret",
                        "refresh_token": "your-refresh-token"
                    }
                },
                "settings": {
                    "deal_stage_mapping": {
                        "closedwon": "paid",
                        "closedlost": "canceled"
                    }
                }
            }
        }


class HubSpotDeal(BaseModel):
    """Model for HubSpot deal data."""
    id: str
    dealname: str = Field(alias="deal_name")
    amount: Optional[float] = 0.0
    dealstage: str = Field(alias="deal_stage")
    closedate: Optional[datetime] = Field(alias="close_date", default=None)
    createdate: Optional[datetime] = Field(alias="create_date", default=None)
    owner_id: Optional[str] = None
    properties: Optional[Dict[str, Any]] = None
    
    class Config:
        """Pydantic configuration."""
        allow_population_by_field_name = True


class HubSpotCustomer(BaseModel):
    """Model for HubSpot customer data (contact or company)."""
    id: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    is_company: bool = False
    
    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "id": "123456",
                "name": "John Doe",
                "email": "john.doe@example.com",
                "phone": "+2341234567890",
                "address": "123 Main St, Lagos, Nigeria",
                "is_company": False
            }
        }


class HubSpotDealInvoice(BaseModel):
    """Model for invoice data generated from a HubSpot deal."""
    deal_id: str
    invoice_number: str
    invoice_date: datetime
    due_date: Optional[datetime] = None
    amount: float
    currency: str = "NGN"
    customer: HubSpotCustomer
    description: Optional[str] = None
    line_items: List[Dict[str, Any]]
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "deal_id": "123456",
                "invoice_number": "HUB-123456",
                "invoice_date": "2025-06-18T08:00:00Z",
                "due_date": "2025-07-18T08:00:00Z",
                "amount": 500000.00,
                "currency": "NGN",
                "customer": {
                    "id": "789012",
                    "name": "Acme Corporation",
                    "email": "info@acme.com",
                    "phone": "+2341234567890",
                    "address": "456 Business Ave, Lagos, Nigeria",
                    "is_company": True
                },
                "description": "Consulting Services - Q3 2025",
                "line_items": [
                    {
                        "description": "Consulting Services",
                        "quantity": 1,
                        "unit_price": 500000.00,
                        "amount": 500000.00
                    }
                ],
                "metadata": {
                    "source": "hubspot",
                    "deal_stage": "closedwon"
                }
            }
        }


class ConnectionTestResult(BaseModel):
    """Model for connection test results."""
    success: bool
    message: str
    details: Optional[Dict[str, Any]] = None


class HubSpotWebhookEvent(BaseModel):
    """Model for HubSpot webhook event data."""
    eventId: str
    subscriptionId: str
    portalId: int
    appId: int
    occurredAt: datetime
    subscriptionType: str
    attemptNumber: int
    objectId: str
    changeSource: str
    changeFlag: str
    propertyName: Optional[str] = None
    propertyValue: Optional[str] = None
    
    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "eventId": "event-12345",
                "subscriptionId": "sub-67890",
                "portalId": 123456,
                "appId": 789012,
                "occurredAt": "2025-06-20T10:30:00Z",
                "subscriptionType": "deal.propertyChange",
                "attemptNumber": 1,
                "objectId": "deal-123",
                "changeSource": "CRM_UI",
                "changeFlag": "UPDATED",
                "propertyName": "dealstage",
                "propertyValue": "closedwon"
            }
        }


class HubSpotWebhookPayload(BaseModel):
    """Model for complete HubSpot webhook payload."""
    events: List[HubSpotWebhookEvent]
    
    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "events": [
                    {
                        "eventId": "event-12345",
                        "subscriptionId": "sub-67890",
                        "portalId": 123456,
                        "appId": 789012,
                        "occurredAt": "2025-06-20T10:30:00Z",
                        "subscriptionType": "deal.propertyChange",
                        "attemptNumber": 1,
                        "objectId": "deal-123",
                        "changeSource": "CRM_UI",
                        "changeFlag": "UPDATED",
                        "propertyName": "dealstage",
                        "propertyValue": "closedwon"
                    }
                ]
            }
        }
