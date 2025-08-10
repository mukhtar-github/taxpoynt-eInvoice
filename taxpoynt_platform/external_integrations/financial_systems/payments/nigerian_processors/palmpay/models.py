"""
PalmPay Data Models
==================

Data models for PalmPay transaction and customer data with NDPR compliance
and specialized support for inter-bank transfers and mobile money.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

from taxpoynt_platform.core_platform.data_management.privacy.models import (
    PrivacyLevel, DataClassification, ConsentStatus
)


class PalmPayTransactionType(Enum):
    """PalmPay transaction types - specialized for inter-bank transfers"""
    INTER_BANK_TRANSFER = "inter_bank_transfer"
    MOBILE_WALLET = "mobile_wallet"
    QR_PAYMENT = "qr_payment"
    BILL_PAYMENT = "bill_payment"
    AIRTIME_PURCHASE = "airtime_purchase"
    DATA_PURCHASE = "data_purchase"
    MONEY_TRANSFER = "money_transfer"
    MERCHANT_PAYMENT = "merchant_payment"
    CASH_IN = "cash_in"
    CASH_OUT = "cash_out"


class PalmPayTransactionStatus(Enum):
    """Transaction status values"""
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESSFUL = "successful"
    FAILED = "failed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    REVERSED = "reversed"


class PalmPayPaymentChannel(Enum):
    """Payment channels for PalmPay"""
    MOBILE_APP = "mobile_app"
    USSD = "ussd"
    QR_CODE = "qr_code"
    API = "api"
    AGENT_NETWORK = "agent_network"
    WEB_PORTAL = "web_portal"


@dataclass
class PalmPayCustomer:
    """
    PalmPay customer data model with NDPR compliance
    Specialized for mobile money and inter-bank transfer customers
    """
    customer_id: str
    phone_number: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    
    # PalmPay specific fields
    wallet_id: Optional[str] = None
    account_tier: Optional[str] = None  # Tier 1, 2, 3 for KYC levels
    bank_verification_number: Optional[str] = None
    national_id: Optional[str] = None
    
    # Privacy and compliance
    privacy_level: PrivacyLevel = PrivacyLevel.STANDARD
    data_classification: DataClassification = DataClassification.PERSONAL
    consent_status: ConsentStatus = ConsentStatus.PENDING
    consent_timestamp: Optional[datetime] = None
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    palmpay_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def apply_privacy_protection(self, level: PrivacyLevel) -> 'PalmPayCustomer':
        """Apply privacy protection based on level"""
        protected = PalmPayCustomer(**self.__dict__)
        protected.privacy_level = level
        
        if level in [PrivacyLevel.HIGH, PrivacyLevel.MAXIMUM]:
            # Mask phone number
            if protected.phone_number:
                protected.phone_number = self._mask_phone(protected.phone_number)
            
            # Mask email
            if protected.email:
                protected.email = self._mask_email(protected.email)
        
        if level == PrivacyLevel.MAXIMUM:
            # Full anonymization
            protected.full_name = "[REDACTED]"
            protected.bank_verification_number = "[REDACTED]"
            protected.national_id = "[REDACTED]"
        
        return protected
    
    def _mask_phone(self, phone: str) -> str:
        """Mask phone number for privacy"""
        if len(phone) < 4:
            return "****"
        return phone[:2] + "*" * (len(phone) - 4) + phone[-2:]
    
    def _mask_email(self, email: str) -> str:
        """Mask email for privacy"""
        if '@' not in email:
            return "****@****.***"
        local, domain = email.split('@', 1)
        if len(local) < 2:
            return "**@" + domain
        return local[0] + "*" * (len(local) - 2) + local[-1] + "@" + domain


@dataclass  
class PalmPayTransaction:
    """
    PalmPay transaction data model with Nigerian business classification
    Specialized for inter-bank transfers and mobile money transactions
    """
    transaction_id: str
    reference: str
    amount: Decimal
    currency: str = "NGN"
    
    # Transaction details
    transaction_type: PalmPayTransactionType = PalmPayTransactionType.MOBILE_WALLET
    status: PalmPayTransactionStatus = PalmPayTransactionStatus.PENDING
    channel: PalmPayPaymentChannel = PalmPayPaymentChannel.MOBILE_APP
    description: Optional[str] = None
    
    # Customer information
    customer: Optional[PalmPayCustomer] = None
    customer_id: Optional[str] = None
    
    # PalmPay specific fields
    sender_account: Optional[str] = None
    receiver_account: Optional[str] = None
    sender_bank: Optional[str] = None
    receiver_bank: Optional[str] = None
    session_id: Optional[str] = None
    
    # Nigerian business classification
    business_category: Optional[str] = None
    tax_category: Optional[str] = None
    firs_classification: Optional[str] = None
    ai_confidence_score: Optional[float] = None
    
    # Privacy and compliance
    privacy_level: PrivacyLevel = PrivacyLevel.STANDARD
    data_classification: DataClassification = DataClassification.TRANSACTIONAL
    consent_status: ConsentStatus = ConsentStatus.GRANTED
    
    # Timestamps
    transaction_date: datetime = field(default_factory=datetime.utcnow)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    # Additional data
    fees: Optional[Decimal] = None
    tax_amount: Optional[Decimal] = None
    net_amount: Optional[Decimal] = None
    palmpay_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def apply_privacy_protection(self, level: PrivacyLevel) -> 'PalmPayTransaction':
        """Apply privacy protection to transaction data"""
        protected = PalmPayTransaction(**self.__dict__)
        protected.privacy_level = level
        
        if level in [PrivacyLevel.HIGH, PrivacyLevel.MAXIMUM]:
            # Protect account information
            if protected.sender_account:
                protected.sender_account = self._mask_account(protected.sender_account)
            if protected.receiver_account:
                protected.receiver_account = self._mask_account(protected.receiver_account)
        
        if level == PrivacyLevel.MAXIMUM:
            # Full transaction anonymization
            protected.description = "[REDACTED]"
            protected.sender_bank = "[REDACTED]"
            protected.receiver_bank = "[REDACTED]"
        
        # Apply customer privacy protection
        if protected.customer:
            protected.customer = protected.customer.apply_privacy_protection(level)
        
        return protected
    
    def _mask_account(self, account: str) -> str:
        """Mask account number for privacy"""
        if len(account) < 4:
            return "****"
        return "*" * (len(account) - 4) + account[-4:]
    
    def to_universal_format(self) -> Dict[str, Any]:
        """Convert to Universal Transaction Processor format"""
        return {
            'processor': 'palmpay',
            'transaction_id': self.transaction_id,
            'reference': self.reference,
            'amount': float(self.amount),
            'currency': self.currency,
            'status': self.status.value,
            'type': self.transaction_type.value,
            'channel': self.channel.value,
            'description': self.description,
            'customer_id': self.customer_id,
            'business_category': self.business_category,
            'tax_category': self.tax_category,
            'firs_classification': self.firs_classification,
            'ai_confidence': self.ai_confidence_score,
            'transaction_date': self.transaction_date.isoformat(),
            'privacy_level': self.privacy_level.value,
            'compliance_data': {
                'sender_account': self.sender_account,
                'receiver_account': self.receiver_account,
                'sender_bank': self.sender_bank,
                'receiver_bank': self.receiver_bank,
                'fees': float(self.fees) if self.fees else None,
                'tax_amount': float(self.tax_amount) if self.tax_amount else None
            },
            'palmpay_specific': {
                'session_id': self.session_id,
                'metadata': self.palmpay_metadata
            }
        }


@dataclass
class PalmPayWebhookEvent:
    """PalmPay webhook event model"""
    event_id: str
    event_type: str
    timestamp: datetime
    data: Dict[str, Any]
    signature: Optional[str] = None
    
    def validate_signature(self, secret: str) -> bool:
        """Validate webhook signature"""
        # Implementation would verify PalmPay's webhook signature
        # This is a placeholder for the actual signature validation
        return True


@dataclass
class PalmPayApiResponse:
    """Standard PalmPay API response wrapper"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    response_time: Optional[float] = None
    
    @classmethod
    def success_response(cls, data: Dict[str, Any]) -> 'PalmPayApiResponse':
        """Create successful response"""
        return cls(success=True, data=data)
    
    @classmethod
    def error_response(cls, code: str, message: str) -> 'PalmPayApiResponse':
        """Create error response"""
        return cls(success=False, error_code=code, error_message=message)


# Export commonly used types
__all__ = [
    'PalmPayTransactionType',
    'PalmPayTransactionStatus', 
    'PalmPayPaymentChannel',
    'PalmPayCustomer',
    'PalmPayTransaction',
    'PalmPayWebhookEvent',
    'PalmPayApiResponse'
]