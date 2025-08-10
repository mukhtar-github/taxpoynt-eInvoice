"""
OPay Data Models
===============

Data models for OPay payment processor integration.
Designed for Nigerian mobile money and digital wallet scenarios.

Features:
- Mobile money transaction structure
- Digital wallet transaction support
- QR code payment categorization
- NDPR-compliant data handling
- Nigerian fintech integration
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, Any, List
from enum import Enum

from ....connector_framework.base_payment_connector import (
    PaymentTransaction, PaymentCustomer, PaymentMethod, 
    PaymentStatus, TransactionType
)


class OPayTransactionType(Enum):
    """OPay-specific transaction types."""
    WALLET_TRANSFER = "wallet_transfer"
    MOBILE_MONEY = "mobile_money"
    QR_PAYMENT = "qr_payment"
    BUSINESS_PAYMENT = "business_payment"
    BILL_PAYMENT = "bill_payment"
    AIRTIME_PURCHASE = "airtime_purchase"
    DATA_PURCHASE = "data_purchase"
    MERCHANT_PAYMENT = "merchant_payment"
    P2P_TRANSFER = "p2p_transfer"
    BANK_TRANSFER = "bank_transfer"
    CARD_PAYMENT = "card_payment"
    CRYPTO_PAYMENT = "crypto_payment"


class OPayChannel(Enum):
    """OPay payment channels."""
    MOBILE_APP = "mobile_app"
    WEB_PORTAL = "web_portal"
    QR_CODE = "qr_code"
    API = "api"
    USSD = "ussd"
    POS_TERMINAL = "pos_terminal"
    SDK = "sdk"


class OPayWalletType(Enum):
    """OPay wallet types."""
    PERSONAL_WALLET = "personal_wallet"
    BUSINESS_WALLET = "business_wallet"
    MERCHANT_WALLET = "merchant_wallet"
    AGENT_WALLET = "agent_wallet"


class OPayKYCLevel(Enum):
    """KYC verification levels."""
    LEVEL_0 = "level_0"  # Basic registration
    LEVEL_1 = "level_1"  # Phone verification
    LEVEL_2 = "level_2"  # ID verification
    LEVEL_3 = "level_3"  # Full KYC with BVN


@dataclass
class OPayCustomer(PaymentCustomer):
    """Extended customer model for OPay with mobile money context."""
    
    # OPay wallet information
    wallet_id: Optional[str] = None
    wallet_type: Optional[OPayWalletType] = None
    wallet_balance: Optional[Decimal] = None
    wallet_status: Optional[str] = None
    
    # Mobile money specific
    mobile_network: Optional[str] = None  # MTN, Airtel, Glo, 9mobile
    mobile_money_provider: Optional[str] = None
    
    # Business verification
    business_verification_status: Optional[str] = None
    business_category: Optional[str] = None
    business_registration_number: Optional[str] = None
    merchant_category_code: Optional[str] = None
    
    # KYC and verification
    kyc_level: Optional[OPayKYCLevel] = None
    bvn_verified: bool = False
    nin_verified: bool = False
    email_verified: bool = False
    phone_verified: bool = False
    
    # Transaction limits
    daily_transaction_limit: Optional[Decimal] = None
    monthly_transaction_limit: Optional[Decimal] = None
    single_transaction_limit: Optional[Decimal] = None
    transactions_today: Optional[int] = None
    
    # Risk profile
    risk_score: Optional[float] = None
    risk_level: Optional[str] = None  # low, medium, high
    fraud_flags: List[str] = None


@dataclass
class OPayTransaction(PaymentTransaction):
    """Extended transaction model for OPay with mobile money features."""
    
    # OPay specific identifiers
    opay_transaction_id: str = ""
    opay_reference: str = ""
    wallet_transaction_id: Optional[str] = None
    
    # Mobile money context
    sender_wallet_id: Optional[str] = None
    receiver_wallet_id: Optional[str] = None
    sender_phone: Optional[str] = None
    receiver_phone: Optional[str] = None
    
    # OPay transaction details
    opay_transaction_type: Optional[OPayTransactionType] = None
    channel: Optional[OPayChannel] = None
    wallet_type: Optional[OPayWalletType] = None
    
    # Payment method details
    qr_code_id: Optional[str] = None
    merchant_code: Optional[str] = None
    terminal_id: Optional[str] = None
    card_last_four: Optional[str] = None
    card_brand: Optional[str] = None
    
    # Business context
    business_category: Optional[str] = None
    merchant_business_name: Optional[str] = None
    transaction_purpose: Optional[str] = None
    
    # Mobile network details
    mobile_network: Optional[str] = None
    mobile_operator_code: Optional[str] = None
    
    # Nigerian banking compliance
    cbn_transaction_code: Optional[str] = None
    narration: Optional[str] = None
    
    # Bill payment specific
    bill_type: Optional[str] = None  # electricity, water, cable_tv, internet
    bill_provider: Optional[str] = None
    bill_account_number: Optional[str] = None
    bill_customer_name: Optional[str] = None
    
    # Settlement information
    settlement_status: Optional[str] = None
    settlement_date: Optional[datetime] = None
    settlement_account: Optional[str] = None
    settlement_bank_code: Optional[str] = None
    
    # Risk and fraud detection
    risk_score: Optional[float] = None
    fraud_flags: List[str] = None
    velocity_check: Optional[str] = None  # normal, medium, high
    geolocation: Optional[Dict[str, Any]] = None
    device_fingerprint: Optional[str] = None
    
    # Crypto payment specific (if applicable)
    crypto_currency: Optional[str] = None
    crypto_amount: Optional[Decimal] = None
    exchange_rate: Optional[Decimal] = None
    
    # Enhanced metadata for Nigerian business context
    opay_metadata: Optional[Dict[str, Any]] = None


@dataclass 
class OPayRefund:
    """OPay refund transaction model."""
    refund_id: str
    original_transaction_id: str
    refund_reference: str
    amount: Decimal
    currency: str = "NGN"
    reason: str = ""
    status: str = "pending"
    
    # Timestamps
    requested_at: datetime
    processed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Wallet context
    refund_wallet_id: Optional[str] = None
    refund_method: Optional[str] = None  # wallet, bank_account, card
    
    # Approval workflow
    requires_approval: bool = False
    approval_reference: Optional[str] = None
    approved_by: Optional[str] = None
    
    # Metadata
    refund_metadata: Optional[Dict[str, Any]] = None


@dataclass
class OPaySettlement:
    """OPay settlement information."""
    settlement_id: str
    settlement_reference: str
    settlement_date: datetime
    
    # Amount details
    gross_amount: Decimal
    fees: Decimal
    charges: Decimal
    net_amount: Decimal
    currency: str = "NGN"
    
    # Settlement destination
    settlement_wallet_id: Optional[str] = None
    settlement_bank_code: Optional[str] = None
    settlement_account_number: Optional[str] = None
    settlement_account_name: Optional[str] = None
    
    # Transactions included
    transaction_count: int
    transaction_ids: List[str]
    
    # Business context
    merchant_settlements: Optional[List[Dict[str, Any]]] = None
    commission_breakdown: Optional[Dict[str, Decimal]] = None
    
    # Status and processing
    settlement_status: str = "pending"  # pending, processing, completed, failed
    processing_batch_id: Optional[str] = None
    
    # Nigerian compliance
    cbn_settlement_code: Optional[str] = None
    tax_deductions: Optional[Decimal] = None


@dataclass
class OPayWebhookEvent:
    """OPay webhook event structure."""
    event_id: str
    event_type: str
    event_timestamp: datetime
    
    # Transaction context
    transaction_id: Optional[str] = None
    transaction_reference: Optional[str] = None
    wallet_id: Optional[str] = None
    
    # Event data
    event_data: Dict[str, Any] = None
    raw_payload: str = ""
    
    # Verification
    signature: str = ""
    verified: bool = False
    
    # Processing
    processed: bool = False
    processing_timestamp: Optional[datetime] = None
    processing_errors: List[str] = None
    
    # Business context
    business_impact: Optional[str] = None
    requires_compliance_action: bool = False


# Nigerian business categories for OPay transactions
OPAY_BUSINESS_CATEGORIES = {
    "fintech": "Financial Technology",
    "e_commerce": "E-commerce",
    "ride_hailing": "Transportation/Ride Hailing",
    "food_delivery": "Food and Beverage Delivery",
    "logistics": "Logistics and Delivery",
    "retail": "Retail Trade",
    "telecommunications": "Telecommunications",
    "utilities": "Utilities and Bill Payment",
    "entertainment": "Entertainment and Media",
    "education": "Education Services",
    "healthcare": "Healthcare Services",
    "real_estate": "Real Estate",
    "agriculture": "Agriculture and Farming",
    "manufacturing": "Manufacturing",
    "professional_services": "Professional Services"
}

# Mobile money transaction codes (CBN guidelines)
MOBILE_MONEY_CODES = {
    "wallet_transfer": "70001",
    "mobile_money": "70002",
    "bill_payment": "70003",
    "airtime_purchase": "70004",
    "merchant_payment": "70005",
    "p2p_transfer": "70006",
    "bank_transfer": "70007",
    "qr_payment": "70008"
}

# Risk assessment thresholds for Nigerian mobile money
NIGERIAN_MOBILE_MONEY_THRESHOLDS = {
    "high_value_threshold": Decimal("200000"),  # ₦200,000
    "suspicious_velocity_threshold": 15,  # transactions per hour
    "daily_wallet_limit": Decimal("500000"),  # ₦500,000
    "kyc_upgrade_threshold": Decimal("50000"),  # ₦50,000
    "business_verification_threshold": Decimal("1000000")  # ₦1,000,000
}

# KYC transaction limits
KYC_TRANSACTION_LIMITS = {
    OPayKYCLevel.LEVEL_0: Decimal("5000"),    # ₦5,000
    OPayKYCLevel.LEVEL_1: Decimal("50000"),   # ₦50,000
    OPayKYCLevel.LEVEL_2: Decimal("200000"),  # ₦200,000
    OPayKYCLevel.LEVEL_3: Decimal("5000000")  # ₦5,000,000
}


def create_opay_transaction_from_api_data(api_data: Dict[str, Any]) -> OPayTransaction:
    """Create OPayTransaction from API response data."""
    
    return OPayTransaction(
        transaction_id=api_data.get('id', ''),
        reference=api_data.get('reference', ''),
        amount=Decimal(str(api_data.get('amount', 0))) / 100,  # Convert from kobo
        currency=api_data.get('currency', 'NGN'),
        payment_method=PaymentMethod.DIGITAL_WALLET,  # Default for OPay
        payment_status=PaymentStatus.SUCCESS if api_data.get('status') == 'success' else PaymentStatus.PENDING,
        transaction_type=TransactionType.PAYMENT,
        created_at=datetime.fromisoformat(api_data.get('created_at', datetime.now().isoformat())),
        
        # OPay specific
        opay_transaction_id=api_data.get('opay_id', ''),
        opay_reference=api_data.get('opay_reference', ''),
        sender_wallet_id=api_data.get('sender_wallet_id'),
        receiver_wallet_id=api_data.get('receiver_wallet_id'),
        
        # Mobile context
        sender_phone=api_data.get('sender_phone'),
        receiver_phone=api_data.get('receiver_phone'),
        mobile_network=api_data.get('mobile_network'),
        
        # Business context
        business_category=api_data.get('business_category'),
        merchant_code=api_data.get('merchant_code'),
        narration=api_data.get('narration', ''),
        
        # Customer information
        customer_email=api_data.get('customer', {}).get('email'),
        customer_phone=api_data.get('customer', {}).get('phone'),
        customer_name=api_data.get('customer', {}).get('name'),
        
        # Nigerian banking
        bank_code=api_data.get('bank_code'),
        bank_name=api_data.get('bank_name'),
        
        # Metadata
        metadata=api_data.get('metadata', {}),
        opay_metadata={
            'processor': 'opay',
            'mobile_money': True,
            'wallet_based': True,
            'compliance_checked': False
        }
    )


def determine_opay_transaction_type(description: str, channel: str = None) -> OPayTransactionType:
    """Determine OPay transaction type from description and channel."""
    
    description_lower = description.lower()
    
    # QR code payments
    if channel == 'qr_code' or 'qr' in description_lower:
        return OPayTransactionType.QR_PAYMENT
    
    # Bill payments
    if any(term in description_lower for term in ['bill', 'electricity', 'water', 'cable', 'internet']):
        return OPayTransactionType.BILL_PAYMENT
    
    # Airtime and data
    if any(term in description_lower for term in ['airtime', 'recharge', 'topup']):
        return OPayTransactionType.AIRTIME_PURCHASE
    if 'data' in description_lower:
        return OPayTransactionType.DATA_PURCHASE
    
    # Business payments
    if any(term in description_lower for term in ['merchant', 'business', 'store', 'shop']):
        return OPayTransactionType.BUSINESS_PAYMENT
    
    # Transfer types
    if any(term in description_lower for term in ['transfer', 'send', 'p2p']):
        if 'bank' in description_lower:
            return OPayTransactionType.BANK_TRANSFER
        else:
            return OPayTransactionType.P2P_TRANSFER
    
    # Default to wallet transfer
    return OPayTransactionType.WALLET_TRANSFER


def get_kyc_limit_for_level(kyc_level: OPayKYCLevel) -> Decimal:
    """Get transaction limit for KYC level."""
    return KYC_TRANSACTION_LIMITS.get(kyc_level, Decimal("0"))


def is_high_risk_transaction(transaction: OPayTransaction) -> bool:
    """Check if transaction is high risk based on OPay criteria."""
    
    risk_factors = []
    
    # Amount-based risk
    if transaction.amount >= NIGERIAN_MOBILE_MONEY_THRESHOLDS['high_value_threshold']:
        risk_factors.append('high_value')
    
    # Cross-border or crypto
    if transaction.crypto_currency:
        risk_factors.append('crypto_payment')
    
    # Multiple rapid transactions (if velocity data available)
    if transaction.velocity_check == 'high':
        risk_factors.append('high_velocity')
    
    # Unusual time patterns
    hour = transaction.created_at.hour
    if hour < 6 or hour > 23:
        risk_factors.append('unusual_time')
    
    # Unverified customer
    if hasattr(transaction, 'customer_kyc_level') and transaction.customer_kyc_level in [OPayKYCLevel.LEVEL_0, OPayKYCLevel.LEVEL_1]:
        if transaction.amount >= Decimal('50000'):  # ₦50K with low KYC
            risk_factors.append('low_kyc_high_amount')
    
    return len(risk_factors) >= 2


# Export main models
__all__ = [
    'OPayTransaction',
    'OPayCustomer',
    'OPayRefund',
    'OPaySettlement',
    'OPayWebhookEvent',
    'OPayTransactionType',
    'OPayChannel',
    'OPayWalletType',
    'OPayKYCLevel',
    'OPAY_BUSINESS_CATEGORIES',
    'MOBILE_MONEY_CODES',
    'NIGERIAN_MOBILE_MONEY_THRESHOLDS',
    'KYC_TRANSACTION_LIMITS',
    'create_opay_transaction_from_api_data',
    'determine_opay_transaction_type',
    'get_kyc_limit_for_level',
    'is_high_risk_transaction'
]