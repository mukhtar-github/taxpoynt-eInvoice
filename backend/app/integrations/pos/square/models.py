"""Square POS specific models and data structures."""

from datetime import datetime
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field


class SquareMoney(BaseModel):
    """Square money object representation."""
    amount: int  # Amount in smallest currency unit (e.g., cents)
    currency: str = "USD"


class SquareOrderLineItem(BaseModel):
    """Square order line item."""
    name: str
    quantity: str
    base_price_money: SquareMoney
    gross_sales_money: Optional[SquareMoney] = None
    total_tax_money: Optional[SquareMoney] = None
    total_discount_money: Optional[SquareMoney] = None
    variation_name: Optional[str] = None
    catalog_object_id: Optional[str] = None
    metadata: Optional[Dict[str, str]] = None


class SquarePayment(BaseModel):
    """Square payment information."""
    id: str
    status: str
    amount_money: SquareMoney
    source_type: str
    card_details: Optional[Dict[str, Any]] = None
    cash_details: Optional[Dict[str, Any]] = None
    application_details: Optional[Dict[str, Any]] = None
    processing_fee: Optional[List[Dict[str, Any]]] = None
    receipt_number: Optional[str] = None
    receipt_url: Optional[str] = None


class SquareOrder(BaseModel):
    """Square order object."""
    id: str
    location_id: str
    state: str
    version: int
    created_at: datetime
    updated_at: datetime
    line_items: List[SquareOrderLineItem] = []
    total_money: SquareMoney
    total_tax_money: Optional[SquareMoney] = None
    total_discount_money: Optional[SquareMoney] = None
    total_service_charge_money: Optional[SquareMoney] = None
    net_amounts: Optional[Dict[str, SquareMoney]] = None
    source: Optional[Dict[str, Any]] = None
    customer_id: Optional[str] = None
    fulfillments: Optional[List[Dict[str, Any]]] = None
    metadata: Optional[Dict[str, str]] = None


class SquareTransaction(BaseModel):
    """Square transaction model matching the base POSTransaction structure."""
    transaction_id: str
    location_id: str
    amount: float
    currency: str
    payment_method: str
    timestamp: datetime
    items: List[Dict[str, Any]] = []
    customer_info: Optional[Dict[str, Any]] = None
    tax_info: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    
    # Square-specific fields
    order_id: Optional[str] = None
    payment_id: Optional[str] = None
    receipt_number: Optional[str] = None
    receipt_url: Optional[str] = None
    square_order: Optional[SquareOrder] = None
    square_payment: Optional[SquarePayment] = None


class SquareLocation(BaseModel):
    """Square location/store information."""
    location_id: str = Field(alias="id")
    name: str
    address: Optional[Dict[str, Any]] = None
    timezone: Optional[str] = None
    currency: str
    tax_settings: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    
    # Square-specific fields
    business_name: Optional[str] = None
    type: Optional[str] = None
    website_url: Optional[str] = None
    business_hours: Optional[Dict[str, Any]] = None
    business_email: Optional[str] = None
    description: Optional[str] = None
    twitter_username: Optional[str] = None
    instagram_username: Optional[str] = None
    facebook_url: Optional[str] = None
    coordinates: Optional[Dict[str, float]] = None
    logo_url: Optional[str] = None
    pos_background_url: Optional[str] = None
    mcc: Optional[str] = None
    full_format_logo_url: Optional[str] = None
    tax_ids: Optional[Dict[str, str]] = None


class SquareWebhookEvent(BaseModel):
    """Square webhook event structure."""
    merchant_id: str
    type: str
    event_id: str
    created_at: datetime
    data: Dict[str, Any]
    
    # Additional Square webhook fields
    location_id: Optional[str] = None
    api_version: Optional[str] = None


class SquareCustomer(BaseModel):
    """Square customer information."""
    id: str
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    company_name: Optional[str] = None
    nickname: Optional[str] = None
    email_address: Optional[str] = None
    phone_number: Optional[str] = None
    address: Optional[Dict[str, Any]] = None
    birthday: Optional[str] = None
    reference_id: Optional[str] = None
    note: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None
    creation_source: Optional[str] = None
    group_ids: Optional[List[str]] = None
    segment_ids: Optional[List[str]] = None
    version: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class SquareInventoryAdjustment(BaseModel):
    """Square inventory adjustment for real-time stock tracking."""
    id: str
    reference_id: Optional[str] = None
    from_state: Optional[str] = None
    to_state: Optional[str] = None
    location_id: str
    catalog_object_id: str
    catalog_object_type: str
    quantity: str
    total_price_money: Optional[SquareMoney] = None
    occurred_at: datetime
    created_at: datetime
    source: Optional[Dict[str, Any]] = None
    employee_id: Optional[str] = None
    transaction_id: Optional[str] = None
    refund_id: Optional[str] = None
    purchase_order_id: Optional[str] = None
    goods_receipt_id: Optional[str] = None


class SquareWebhookSignature(BaseModel):
    """Square webhook signature validation model."""
    signature: str
    notification_url: str
    request_body: str
    
    def is_valid(self, signature_key: str) -> bool:
        """
        Validate Square webhook signature.
        
        Args:
            signature_key: Square webhook signature key
            
        Returns:
            bool: True if signature is valid
        """
        import hmac
        import hashlib
        
        # Square uses SHA-1 HMAC for webhook signatures
        expected_signature = hmac.new(
            signature_key.encode('utf-8'),
            (self.notification_url + self.request_body).encode('utf-8'),
            hashlib.sha1
        ).digest()
        
        import base64
        expected_signature_b64 = base64.b64encode(expected_signature).decode('utf-8')
        
        return hmac.compare_digest(self.signature, expected_signature_b64)