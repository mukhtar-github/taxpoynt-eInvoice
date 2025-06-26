"""
Toast POS specific models and data structures.

This module defines Pydantic models for Toast POS data structures including
orders, menu items, locations, and webhook events.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from decimal import Decimal

from pydantic import BaseModel, validator


class ToastMoney(BaseModel):
    """Model representing Toast monetary values."""
    amount: int  # Amount in cents
    currency: str = "USD"
    
    @property
    def dollars(self) -> float:
        """Convert cents to dollars."""
        return self.amount / 100.0


class ToastMenuItem(BaseModel):
    """Model representing a Toast menu item."""
    guid: str
    name: str
    description: Optional[str] = None
    sku: Optional[str] = None
    price: Optional[ToastMoney] = None
    plu: Optional[str] = None  # Price Look Up code
    category: Optional[str] = None
    visibility: str = "VISIBLE"  # VISIBLE, HIDDEN
    modifiers: List[Dict[str, Any]] = []


class ToastOrderItem(BaseModel):
    """Model representing an item in a Toast order."""
    guid: str
    menu_item_guid: str
    quantity: float
    price: ToastMoney
    base_price: ToastMoney
    modifiers: List[Dict[str, Any]] = []
    special_instructions: Optional[str] = None
    voided: bool = False
    tax_amount: Optional[ToastMoney] = None


class ToastCustomer(BaseModel):
    """Model representing a Toast customer."""
    guid: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    
    @property
    def full_name(self) -> str:
        """Get customer's full name."""
        parts = [self.first_name, self.last_name]
        return " ".join(filter(None, parts))


class ToastPayment(BaseModel):
    """Model representing a Toast payment."""
    guid: str
    type: str  # CREDIT_CARD, CASH, GIFT_CARD, etc.
    amount: ToastMoney
    tip_amount: Optional[ToastMoney] = None
    processing_fee: Optional[ToastMoney] = None
    refunded_amount: Optional[ToastMoney] = None
    card_type: Optional[str] = None
    last_four: Optional[str] = None


class ToastOrder(BaseModel):
    """Model representing a complete Toast order."""
    guid: str
    restaurant_guid: str
    entity_type: str  # ORDER, CHECK
    external_id: Optional[str] = None
    order_number: Optional[str] = None
    table: Optional[Dict[str, Any]] = None
    service_area: Optional[Dict[str, Any]] = None
    dining_option: Optional[Dict[str, Any]] = None
    order_type: str  # DINE_IN, TAKEOUT, DELIVERY, etc.
    state: str  # OPEN, CLOSED, CANCELLED, etc.
    voided: bool = False
    created_date: datetime
    modified_date: datetime
    closed_date: Optional[datetime] = None
    
    # Financial information
    total_amount: ToastMoney
    tax_amount: ToastMoney
    tip_amount: Optional[ToastMoney] = None
    service_charge_amount: Optional[ToastMoney] = None
    discount_amount: Optional[ToastMoney] = None
    
    # Order contents
    selections: List[ToastOrderItem] = []
    payments: List[ToastPayment] = []
    
    # Customer information
    customer: Optional[ToastCustomer] = None
    
    # Additional metadata  
    server: Optional[Dict[str, Any]] = None
    source: str = "POS"
    delivery_info: Optional[Dict[str, Any]] = None
    
    @validator('created_date', 'modified_date', pre=True)
    def parse_datetime(cls, v):
        if isinstance(v, str):
            # Handle Toast datetime format
            return datetime.fromisoformat(v.replace('Z', '+00:00'))
        return v
    
    @property
    def is_completed(self) -> bool:
        """Check if order is completed and paid."""
        return self.state == "CLOSED" and not self.voided


class ToastLocation(BaseModel):
    """Model representing a Toast restaurant location."""
    guid: str
    name: str
    external_id: Optional[str] = None
    description: Optional[str] = None
    address: Optional[Dict[str, Any]] = None
    timezone: str = "America/New_York"
    currency: str = "USD"
    phone: Optional[str] = None
    website: Optional[str] = None
    
    # Business information
    management_group_guid: Optional[str] = None
    restaurant_group_guid: Optional[str] = None
    
    # Tax settings
    tax_rates: List[Dict[str, Any]] = []
    service_charges: List[Dict[str, Any]] = []
    
    # Operational settings
    ordering_enabled: bool = True
    delivery_enabled: bool = False
    takeout_enabled: bool = True
    
    @property
    def address_string(self) -> str:
        """Get formatted address string."""
        if not self.address:
            return ""
        
        address_parts = [
            self.address.get("address1", ""),
            self.address.get("address2", ""),
            self.address.get("city", ""),
            self.address.get("state", ""),
            self.address.get("zip", "")
        ]
        return ", ".join(filter(None, address_parts))


class ToastWebhookEvent(BaseModel):
    """Model representing a Toast webhook event."""
    event_type: str
    guid: str
    restaurant_guid: str
    timestamp: datetime
    data: Dict[str, Any]
    
    # Common event types
    EVENT_ORDER_SENT = "ORDER_SENT"
    EVENT_ORDER_MODIFIED = "ORDER_MODIFIED" 
    EVENT_ORDER_CLOSED = "ORDER_CLOSED"
    EVENT_PAYMENT_CREATED = "PAYMENT_CREATED"
    EVENT_MENU_UPDATED = "MENU_UPDATED"
    
    @validator('timestamp', pre=True)
    def parse_timestamp(cls, v):
        if isinstance(v, str):
            return datetime.fromisoformat(v.replace('Z', '+00:00'))
        return v


class ToastMenuCategory(BaseModel):
    """Model representing a Toast menu category."""
    guid: str
    name: str
    description: Optional[str] = None
    sort_order: int = 0
    visibility: str = "VISIBLE"
    items: List[ToastMenuItem] = []


class ToastMenu(BaseModel):
    """Model representing a complete Toast menu."""
    guid: str
    name: str
    restaurant_guid: str
    visibility: str = "VISIBLE"
    categories: List[ToastMenuCategory] = []
    modified_date: datetime
    
    @property
    def total_items(self) -> int:
        """Get total number of menu items across all categories."""
        return sum(len(category.items) for category in self.categories)


class ToastAPIError(BaseModel):
    """Model representing Toast API error response."""
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None
    field: Optional[str] = None


class ToastAPIResponse(BaseModel):
    """Model representing Toast API response wrapper."""
    success: bool = True
    data: Optional[Any] = None
    error: Optional[ToastAPIError] = None
    pagination: Optional[Dict[str, Any]] = None