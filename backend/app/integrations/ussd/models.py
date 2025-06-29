"""
USSD Payment Models and Data Structures
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field
from ..payments.base import PaymentStatus

class USSDSessionStatus(str, Enum):
    """USSD session status enumeration"""
    INITIATED = "initiated"
    IN_PROGRESS = "in_progress"
    WAITING_PIN = "waiting_pin"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"
    CANCELLED = "cancelled"

class USSDStepType(str, Enum):
    """USSD interaction step types"""
    MENU_SELECTION = "menu_selection"
    AMOUNT_INPUT = "amount_input"
    ACCOUNT_INPUT = "account_input"
    PIN_INPUT = "pin_input"
    CONFIRMATION = "confirmation"
    RESULT = "result"

class USSDPaymentCode(BaseModel):
    """USSD payment code structure"""
    code: str = Field(..., description="The USSD code to dial")
    reference: str = Field(..., description="Payment reference")
    amount: float = Field(..., description="Payment amount in Naira")
    amount_kobo: int = Field(..., description="Payment amount in kobo")
    bank_code: str = Field(..., description="Bank identifier code")
    bank_name: str = Field(..., description="Human-readable bank name")
    expires_at: datetime = Field(..., description="Code expiration time")
    instructions: List[str] = Field(default_factory=list, description="Step-by-step instructions")
    session_id: Optional[str] = Field(None, description="USSD session identifier")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class USSDPaymentRequest(BaseModel):
    """USSD payment request structure"""
    amount: float = Field(..., gt=0, description="Payment amount in Naira")
    currency: str = Field(default="NGN", description="Payment currency")
    customer_email: str = Field(..., description="Customer email address")
    customer_name: Optional[str] = Field(None, description="Customer name")
    customer_phone: str = Field(..., description="Customer phone number")
    bank_code: str = Field(..., description="Preferred bank code")
    reference: Optional[str] = Field(None, description="External payment reference")
    callback_url: Optional[str] = Field(None, description="Payment callback URL")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    invoice_id: Optional[str] = Field(None, description="Associated invoice ID")
    expires_in_minutes: int = Field(default=30, description="Payment expiration in minutes")

class USSDSession(BaseModel):
    """USSD session management"""
    session_id: str = Field(..., description="Unique session identifier")
    phone_number: str = Field(..., description="User's phone number")
    bank_code: str = Field(..., description="Selected bank code")
    payment_reference: str = Field(..., description="Payment reference")
    status: USSDSessionStatus = Field(default=USSDSessionStatus.INITIATED)
    current_step: USSDStepType = Field(default=USSDStepType.MENU_SELECTION)
    amount: int = Field(..., description="Amount in kobo")
    target_account: Optional[str] = Field(None, description="Target account number")
    steps_completed: List[USSDStepType] = Field(default_factory=list)
    session_data: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime = Field(..., description="Session expiration time")
    error_message: Optional[str] = Field(None, description="Error details if failed")

class USSDInstruction(BaseModel):
    """Individual USSD instruction step"""
    step_number: int = Field(..., description="Step sequence number")
    instruction: str = Field(..., description="Human-readable instruction")
    ussd_code: Optional[str] = Field(None, description="USSD code for this step")
    expected_response: Optional[str] = Field(None, description="Expected user response")
    timeout_seconds: int = Field(default=120, description="Step timeout")
    is_final: bool = Field(default=False, description="Whether this is the final step")

class USSDTransactionResult(BaseModel):
    """USSD transaction completion result"""
    reference: str = Field(..., description="Payment reference")
    status: PaymentStatus = Field(..., description="Final payment status")
    amount: int = Field(..., description="Transaction amount in kobo")
    bank_code: str = Field(..., description="Bank used for payment")
    bank_reference: Optional[str] = Field(None, description="Bank transaction reference")
    customer_phone: str = Field(..., description="Customer phone number")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    error_code: Optional[str] = Field(None, description="Error code if failed")
    error_message: Optional[str] = Field(None, description="Error description")
    session_log: List[str] = Field(default_factory=list, description="Session interaction log")

class USSDCallbackPayload(BaseModel):
    """USSD payment callback payload"""
    event_type: str = Field(..., description="Callback event type")
    reference: str = Field(..., description="Payment reference")
    status: PaymentStatus = Field(..., description="Payment status")
    amount: int = Field(..., description="Amount in kobo")
    bank_code: str = Field(..., description="Bank code")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    session_id: Optional[str] = Field(None, description="USSD session ID")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional data")

class BankUSSDCapabilities(BaseModel):
    """Bank USSD capabilities and features"""
    bank_code: str = Field(..., description="Bank identifier")
    bank_name: str = Field(..., description="Bank display name")
    supports_ussd: bool = Field(default=True, description="USSD support status")
    supports_merchant_payments: bool = Field(default=False, description="Merchant payment support")
    supports_bill_payments: bool = Field(default=False, description="Bill payment support")
    daily_limit: int = Field(..., description="Daily transaction limit in kobo")
    single_transaction_limit: int = Field(..., description="Single transaction limit in kobo")
    monthly_limit: int = Field(..., description="Monthly limit in kobo")
    session_timeout_seconds: int = Field(default=180, description="USSD session timeout")
    supported_networks: List[str] = Field(default_factory=list, description="Supported mobile networks")
    fees: Dict[str, float] = Field(default_factory=dict, description="Transaction fees")

class USSDMenuOption(BaseModel):
    """USSD menu option structure"""
    option_number: str = Field(..., description="Menu option number")
    display_text: str = Field(..., description="Option display text")
    action: str = Field(..., description="Action to perform")
    next_step: Optional[USSDStepType] = Field(None, description="Next step after selection")
    validation_required: bool = Field(default=False, description="Whether input validation is needed")

class USSDMenu(BaseModel):
    """USSD menu structure"""
    title: str = Field(..., description="Menu title")
    options: List[USSDMenuOption] = Field(..., description="Available menu options")
    timeout_seconds: int = Field(default=30, description="Menu timeout")
    back_option: bool = Field(default=True, description="Include back option")
    cancel_option: bool = Field(default=True, description="Include cancel option")

def create_ussd_payment_code(
    bank_code: str,
    amount: float,
    reference: str,
    expires_in_minutes: int = 30
) -> USSDPaymentCode:
    """Factory function to create USSD payment code"""
    from .bank_ussd_codes import get_bank_by_code
    
    bank = get_bank_by_code(bank_code)
    if not bank:
        raise ValueError(f"Unsupported bank code: {bank_code}")
    
    amount_kobo = int(amount * 100)
    expires_at = datetime.utcnow() + timedelta(minutes=expires_in_minutes)
    
    # Generate basic USSD code (would be more sophisticated in real implementation)
    ussd_code = f"{bank['code']}*{amount_kobo}*{reference}#"
    
    # Generate step-by-step instructions
    instructions = [
        f"Dial {bank['code']} on your phone",
        f"Select option for 'Transfer' or 'Payment'",
        f"Enter amount: {amount:,.2f}",
        f"Enter payment reference: {reference}",
        f"Enter your {bank['name']} USSD PIN",
        f"Confirm the transaction details",
        f"You will receive an SMS confirmation"
    ]
    
    return USSDPaymentCode(
        code=ussd_code,
        reference=reference,
        amount=amount,
        amount_kobo=amount_kobo,
        bank_code=bank_code,
        bank_name=bank['name'],
        expires_at=expires_at,
        instructions=instructions
    )