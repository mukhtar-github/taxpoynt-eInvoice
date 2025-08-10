"""
Interswitch Data Models
======================

Data models for Interswitch interbank transaction and customer data with NDPR compliance
and specialized support for Nigerian interbank payment infrastructure.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

from taxpoynt_platform.core_platform.data_management.privacy.models import (
    PrivacyLevel, DataClassification, ConsentStatus
)


class InterswitchTransactionType(Enum):
    """Interswitch transaction types - specialized for interbank operations"""
    INTERBANK_TRANSFER = "interbank_transfer"
    NIBSS_INSTANT_PAYMENT = "nibss_instant_payment"
    RTGS_TRANSFER = "rtgs_transfer"
    ACH_TRANSFER = "ach_transfer"
    CARD_PAYMENT = "card_payment"
    DIRECT_DEBIT = "direct_debit"
    STANDING_ORDER = "standing_order"
    BULK_PAYMENT = "bulk_payment"
    SALARY_PAYMENT = "salary_payment"
    PENSION_PAYMENT = "pension_payment"
    GOVERNMENT_PAYMENT = "government_payment"
    TAX_PAYMENT = "tax_payment"


class InterswitchTransactionStatus(Enum):
    """Transaction status values"""
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESSFUL = "successful"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    REVERSED = "reversed"
    SETTLED = "settled"
    RECONCILED = "reconciled"


class InterswitchPaymentChannel(Enum):
    """Payment channels for Interswitch"""
    NIBSS_NIP = "nibss_nip"
    RTGS = "rtgs"
    ACH = "ach"
    CARD_SCHEME = "card_scheme"
    DIRECT_DEBIT = "direct_debit"
    API = "api"
    WEB_PORTAL = "web_portal"
    MOBILE_APP = "mobile_app"


@dataclass
class InterswitchCustomer:
    """
    Interswitch customer data model with NDPR compliance
    Specialized for interbank transaction customers
    """
    customer_id: str
    account_number: str
    bank_code: str
    bvn: Optional[str] = None
    
    # Customer details
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[str] = None
    
    # Interswitch specific fields
    customer_reference: Optional[str] = None
    account_type: Optional[str] = None  # Savings, Current, Domiciliary
    kyc_level: Optional[str] = None  # Tier 1, 2, 3
    bank_name: Optional[str] = None
    
    # Privacy and compliance
    privacy_level: PrivacyLevel = PrivacyLevel.STANDARD
    data_classification: DataClassification = DataClassification.PERSONAL
    consent_status: ConsentStatus = ConsentStatus.PENDING
    consent_timestamp: Optional[datetime] = None
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    interswitch_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def apply_privacy_protection(self, level: PrivacyLevel) -> 'InterswitchCustomer':
        """Apply privacy protection based on level"""
        protected = InterswitchCustomer(**self.__dict__)
        protected.privacy_level = level
        
        if level in [PrivacyLevel.HIGH, PrivacyLevel.MAXIMUM]:
            # Mask account number
            if protected.account_number:
                protected.account_number = self._mask_account(protected.account_number)
            
            # Mask phone number
            if protected.phone_number:
                protected.phone_number = self._mask_phone(protected.phone_number)
            
            # Mask email
            if protected.email:
                protected.email = self._mask_email(protected.email)
        
        if level == PrivacyLevel.MAXIMUM:
            # Full anonymization
            protected.full_name = "[REDACTED]"
            protected.bvn = "[REDACTED]"
            protected.customer_reference = "[REDACTED]"
        
        return protected
    
    def _mask_account(self, account: str) -> str:
        """Mask account number for privacy"""
        if len(account) < 4:
            return "****"
        return "*" * (len(account) - 4) + account[-4:]
    
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
class InterswitchTransaction:
    """
    Interswitch transaction data model with Nigerian business classification
    Specialized for interbank and NIBSS infrastructure transactions
    """
    transaction_id: str
    reference: str
    amount: Decimal
    currency: str = "NGN"
    
    # Transaction details
    transaction_type: InterswitchTransactionType = InterswitchTransactionType.INTERBANK_TRANSFER
    status: InterswitchTransactionStatus = InterswitchTransactionStatus.PENDING
    channel: InterswitchPaymentChannel = InterswitchPaymentChannel.NIBSS_NIP
    description: Optional[str] = None
    
    # Customer information
    customer: Optional[InterswitchCustomer] = None
    customer_id: Optional[str] = None
    
    # Interbank specific fields
    originating_bank_code: Optional[str] = None
    destination_bank_code: Optional[str] = None
    originating_account: Optional[str] = None
    destination_account: Optional[str] = None
    originating_bank_name: Optional[str] = None
    destination_bank_name: Optional[str] = None
    
    # NIBSS/CBN specific
    nibss_session_id: Optional[str] = None
    nip_session_id: Optional[str] = None
    settlement_id: Optional[str] = None
    
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
    value_date: Optional[datetime] = None
    settlement_date: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    # Additional data
    fees: Optional[Decimal] = None
    charges: Optional[Decimal] = None
    tax_amount: Optional[Decimal] = None
    net_amount: Optional[Decimal] = None
    exchange_rate: Optional[Decimal] = None
    interswitch_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def apply_privacy_protection(self, level: PrivacyLevel) -> 'InterswitchTransaction':
        """Apply privacy protection to transaction data"""
        protected = InterswitchTransaction(**self.__dict__)
        protected.privacy_level = level
        
        if level in [PrivacyLevel.HIGH, PrivacyLevel.MAXIMUM]:
            # Protect account information
            if protected.originating_account:
                protected.originating_account = self._mask_account(protected.originating_account)
            if protected.destination_account:
                protected.destination_account = self._mask_account(protected.destination_account)
        
        if level == PrivacyLevel.MAXIMUM:
            # Full transaction anonymization
            protected.description = "[REDACTED]"
            protected.originating_bank_name = "[REDACTED]"
            protected.destination_bank_name = "[REDACTED]"
            protected.nibss_session_id = "[REDACTED]"
            protected.nip_session_id = "[REDACTED]"
        
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
            'processor': 'interswitch',
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
            'value_date': self.value_date.isoformat() if self.value_date else None,
            'settlement_date': self.settlement_date.isoformat() if self.settlement_date else None,
            'privacy_level': self.privacy_level.value,
            'compliance_data': {
                'originating_bank_code': self.originating_bank_code,
                'destination_bank_code': self.destination_bank_code,
                'originating_account': self.originating_account,
                'destination_account': self.destination_account,
                'originating_bank_name': self.originating_bank_name,
                'destination_bank_name': self.destination_bank_name,
                'fees': float(self.fees) if self.fees else None,
                'charges': float(self.charges) if self.charges else None,
                'tax_amount': float(self.tax_amount) if self.tax_amount else None
            },
            'interswitch_specific': {
                'nibss_session_id': self.nibss_session_id,
                'nip_session_id': self.nip_session_id,
                'settlement_id': self.settlement_id,
                'metadata': self.interswitch_metadata
            }
        }


@dataclass
class InterswitchWebhookEvent:
    """Interswitch webhook event model"""
    event_id: str
    event_type: str
    timestamp: datetime
    data: Dict[str, Any]
    signature: Optional[str] = None
    
    def validate_signature(self, secret: str) -> bool:
        """Validate webhook signature"""
        # Implementation would verify Interswitch's webhook signature
        # This is a placeholder for the actual signature validation
        return True


@dataclass
class InterswitchApiResponse:
    """Standard Interswitch API response wrapper"""
    success: bool
    response_code: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    response_time: Optional[float] = None
    
    @classmethod
    def success_response(cls, data: Dict[str, Any], response_code: str = "00") -> 'InterswitchApiResponse':
        """Create successful response"""
        return cls(success=True, data=data, response_code=response_code)
    
    @classmethod
    def error_response(cls, code: str, message: str) -> 'InterswitchApiResponse':
        """Create error response"""
        return cls(success=False, error_code=code, error_message=message)


@dataclass
class InterswitchBankInfo:
    """Nigerian bank information for Interswitch operations"""
    bank_code: str
    bank_name: str
    swift_code: Optional[str] = None
    sort_code: Optional[str] = None
    is_active: bool = True
    supports_nip: bool = True
    supports_rtgs: bool = True
    supports_ach: bool = True


# Common Nigerian banks for Interswitch integration
NIGERIAN_BANKS = {
    "044": InterswitchBankInfo("044", "Access Bank", "ABNGNGLA"),
    "014": InterswitchBankInfo("014", "Afribank Nigeria Plc", "AFRINGLA"),
    "023": InterswitchBankInfo("023", "Citibank Nigeria Limited", "CITINGLA"),
    "050": InterswitchBankInfo("050", "Ecobank Nigeria Plc", "ECOCNGLA"),
    "040": InterswitchBankInfo("040", "Equitorial Trust Bank Limited", "ETBLNGLA"),
    "011": InterswitchBankInfo("011", "First Bank of Nigeria", "FBNINGLA"),
    "214": InterswitchBankInfo("214", "First City Monument Bank", "FCMBNGLA"),
    "070": InterswitchBankInfo("070", "Fidelity Bank", "FIDTNGLA"),
    "058": InterswitchBankInfo("058", "Guaranty Trust Bank", "GTBINGLA"),
    "030": InterswitchBankInfo("030", "Heritage Bank", "HBNGNGLA"),
    "301": InterswitchBankInfo("301", "Jaiz Bank", "JAIZNGLA"),
    "082": InterswitchBankInfo("082", "Keystone Bank", "KEYSTNGLA"),
    "221": InterswitchBankInfo("221", "Stanbic IBTC Bank", "SBICNGLA"),
    "068": InterswitchBankInfo("068", "Standard Chartered Bank", "SCBLNGLA"),
    "232": InterswitchBankInfo("232", "Sterling Bank", "STERLNGLA"),
    "033": InterswitchBankInfo("033", "United Bank For Africa", "UNAFNGLA"),
    "032": InterswitchBankInfo("032", "Union Bank of Nigeria", "UNBNNGLA"),
    "035": InterswitchBankInfo("035", "Wema Bank", "WEMANGLA"),
    "057": InterswitchBankInfo("057", "Zenith Bank", "ZEIBNGLA"),
}


# Export commonly used types
__all__ = [
    'InterswitchTransactionType',
    'InterswitchTransactionStatus', 
    'InterswitchPaymentChannel',
    'InterswitchCustomer',
    'InterswitchTransaction',
    'InterswitchWebhookEvent',
    'InterswitchApiResponse',
    'InterswitchBankInfo',
    'NIGERIAN_BANKS'
]