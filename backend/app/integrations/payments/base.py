"""
Base payment connector for Nigerian payment gateways
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from enum import Enum
from datetime import datetime
from pydantic import BaseModel


class PaymentStatus(str, Enum):
    """Payment status enumeration"""
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class PaymentChannel(str, Enum):
    """Payment channel enumeration"""
    CARD = "card"
    BANK_TRANSFER = "bank_transfer"
    USSD = "ussd"
    QR_CODE = "qr"
    MOBILE_MONEY = "mobile_money"
    BANK = "bank"


class PaymentInitResponse(BaseModel):
    """Payment initialization response"""
    payment_id: str
    reference: str
    authorization_url: Optional[str] = None
    access_code: Optional[str] = None
    status: PaymentStatus
    amount: int  # Amount in kobo for NGN
    currency: str = "NGN"
    channels: list[PaymentChannel]
    expires_at: Optional[datetime] = None


class PaymentVerificationResponse(BaseModel):
    """Payment verification response"""
    payment_id: str
    reference: str
    status: PaymentStatus
    amount: int
    currency: str
    channel: Optional[PaymentChannel] = None
    gateway_response: str
    paid_at: Optional[datetime] = None
    customer_email: str
    customer_name: Optional[str] = None
    metadata: Dict[str, Any] = {}


class WebhookResponse(BaseModel):
    """Webhook processing response"""
    event_type: str
    payment_id: str
    reference: str
    status: PaymentStatus
    processed: bool
    invoice_updated: bool = False
    error: Optional[str] = None


class BasePaymentConnector(ABC):
    """Base class for Nigerian payment gateway connectors"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.base_url = self._get_base_url()
        self.public_key = config.get("public_key")
        self.secret_key = config.get("secret_key")
        
    @abstractmethod
    def _get_base_url(self) -> str:
        """Get the base URL for the payment gateway"""
        pass
    
    @abstractmethod
    async def initialize_payment(
        self,
        amount: int,
        email: str,
        reference: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> PaymentInitResponse:
        """Initialize a payment transaction"""
        pass
    
    @abstractmethod
    async def verify_payment(self, reference: str) -> PaymentVerificationResponse:
        """Verify payment status"""
        pass
    
    @abstractmethod
    async def process_webhook(self, payload: Dict[str, Any]) -> WebhookResponse:
        """Process webhook events"""
        pass
    
    def generate_reference(self, prefix: str = "TXP") -> str:
        """Generate unique payment reference"""
        import uuid
        return f"{prefix}_{uuid.uuid4().hex[:12].upper()}"
    
    def kobo_to_naira(self, amount_kobo: int) -> float:
        """Convert kobo to naira"""
        return amount_kobo / 100
    
    def naira_to_kobo(self, amount_naira: float) -> int:
        """Convert naira to kobo"""
        return int(amount_naira * 100)