"""
Flutterwave Payment Processor Models
===================================

Data models for Flutterwave integration with comprehensive Pan-African coverage.

Features:
- Multi-country payment support across 34+ African countries
- NDPR-compliant data structures with privacy protection
- Support for mobile money, cards, bank transfers, and alternative payments
- African currency support (NGN, GHS, KES, UGX, ZAR, XOF, XAF, etc.)
- Comprehensive transaction classification for FIRS compliance
"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional, Any

from .....connector_framework.base_payment_connector import (
    PaymentTransaction, PaymentStatus, PaymentChannel, PaymentType
)


class FlutterwaveEnvironment(str, Enum):
    """Flutterwave environment types"""
    SANDBOX = "sandbox"
    PRODUCTION = "production"


class FlutterwavePaymentMethod(str, Enum):
    """Flutterwave payment methods"""
    CARD = "card"
    ACCOUNT = "account"
    MOBILE_MONEY = "mobile_money"
    USSD = "ussd"
    QR_CODE = "qr"
    BANK_TRANSFER = "bank_transfer"
    VOUCHER = "voucher"
    CRYPTO = "crypto"
    APPLE_PAY = "applepay"
    GOOGLE_PAY = "googlepay"


class FlutterwaveCurrency(str, Enum):
    """African currencies supported by Flutterwave"""
    # Nigerian Naira
    NGN = "NGN"
    # Ghanaian Cedi
    GHS = "GHS"
    # Kenyan Shilling
    KES = "KES"
    # Ugandan Shilling
    UGX = "UGX"
    # Tanzanian Shilling
    TZS = "TZS"
    # Rwandan Franc
    RWF = "RWF"
    # Zambian Kwacha
    ZMW = "ZMW"
    # South African Rand
    ZAR = "ZAR"
    # West African CFA Franc
    XOF = "XOF"
    # Central African CFA Franc
    XAF = "XAF"
    # US Dollar (for international)
    USD = "USD"
    # Euro (for international)
    EUR = "EUR"
    # British Pound (for international)
    GBP = "GBP"


class FlutterwaveCountry(str, Enum):
    """African countries supported by Flutterwave"""
    NIGERIA = "NG"
    GHANA = "GH"
    KENYA = "KE"
    UGANDA = "UG"
    TANZANIA = "TZ"
    RWANDA = "RW"
    ZAMBIA = "ZM"
    SOUTH_AFRICA = "ZA"
    SENEGAL = "SN"
    MALI = "ML"
    BURKINA_FASO = "BF"
    COTE_DIVOIRE = "CI"
    CAMEROON = "CM"
    CHAD = "TD"
    CENTRAL_AFRICAN_REPUBLIC = "CF"
    CONGO = "CG"
    DEMOCRATIC_REPUBLIC_CONGO = "CD"
    EQUATORIAL_GUINEA = "GQ"
    GABON = "GA"


class MobileMoneyProvider(str, Enum):
    """African mobile money providers"""
    # Nigeria
    OPAY = "opay"
    PALM_PAY = "palmpay"
    
    # Ghana
    MTN_MOBILE_MONEY_GH = "mtn_gh"
    VODAFONE_CASH = "vodafone_cash"
    AIRTELTIGO_MONEY = "airteltigo"
    
    # Kenya
    M_PESA_KE = "mpesa_ke"
    AIRTEL_MONEY_KE = "airtel_ke"
    EQUITEL = "equitel"
    
    # Uganda
    MTN_MOBILE_MONEY_UG = "mtn_ug"
    AIRTEL_MONEY_UG = "airtel_ug"
    
    # Tanzania
    M_PESA_TZ = "mpesa_tz"
    AIRTEL_MONEY_TZ = "airtel_tz"
    TIGO_PESA = "tigo_pesa"
    
    # Rwanda
    MTN_MOBILE_MONEY_RW = "mtn_rw"
    AIRTEL_MONEY_RW = "airtel_rw"
    
    # Zambia
    MTN_MOBILE_MONEY_ZM = "mtn_zm"
    AIRTEL_MONEY_ZM = "airtel_zm"
    
    # Francophone Africa
    ORANGE_MONEY = "orange_money"
    MOOV_MONEY = "moov_money"


@dataclass
class FlutterwaveTransactionFee:
    """Transaction fee structure"""
    
    total_fee: Decimal
    flutterwave_fee: Decimal
    merchant_fee: Decimal
    stamp_duty: Optional[Decimal] = None
    
    # Fee breakdown by type
    processing_fee: Optional[Decimal] = None
    currency_conversion_fee: Optional[Decimal] = None
    cross_border_fee: Optional[Decimal] = None
    
    # Nigerian specific
    vat: Optional[Decimal] = None
    vat_rate: Optional[Decimal] = None


@dataclass
class FlutterwaveCard:
    """Card payment details"""
    
    first_6digits: Optional[str] = None
    last_4digits: Optional[str] = None
    card_type: Optional[str] = None  # visa, mastercard, verve
    country: Optional[str] = None
    issuer: Optional[str] = None
    auth_model: Optional[str] = None  # pin, avs_noauth, noauth
    token: Optional[str] = None


@dataclass
class FlutterwaveMobileMoney:
    """Mobile money payment details"""
    
    provider: MobileMoneyProvider
    phone_number: str
    country: FlutterwaveCountry
    voucher_code: Optional[str] = None
    wallet_id: Optional[str] = None


@dataclass
class FlutterwaveCustomer:
    """Flutterwave customer information"""
    
    id: Optional[int] = None
    name: Optional[str] = None
    email: Optional[str] = None
    phone_number: Optional[str] = None
    
    # Business customer details
    business_name: Optional[str] = None
    business_type: Optional[str] = None
    business_registration: Optional[str] = None
    
    # Location
    country: Optional[FlutterwaveCountry] = None
    state: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    
    # KYC and verification
    is_verified: bool = False
    kyc_level: Optional[str] = None
    
    # Privacy protection
    privacy_protected: bool = False
    consent_granted: bool = False
    
    created_at: Optional[datetime] = None


@dataclass
class FlutterwaveTransaction(PaymentTransaction):
    """
    Flutterwave transaction with Pan-African payment support
    """
    
    # Flutterwave specific fields
    flw_ref: Optional[str] = None
    tx_ref: Optional[str] = None
    flw_id: Optional[int] = None
    device_fingerprint: Optional[str] = None
    
    # Payment method details
    payment_method: Optional[FlutterwavePaymentMethod] = None
    card_details: Optional[FlutterwaveCard] = None
    mobile_money_details: Optional[FlutterwaveMobileMoney] = None
    
    # Geographic information
    country: Optional[FlutterwaveCountry] = None
    country_name: Optional[str] = None
    
    # Currency and rates
    local_currency: Optional[FlutterwaveCurrency] = None
    local_amount: Optional[Decimal] = None
    exchange_rate: Optional[Decimal] = None
    
    # Customer information
    customer: Optional[FlutterwaveCustomer] = None
    
    # Fee information
    fee_details: Optional[FlutterwaveTransactionFee] = None
    
    # Processor response
    processor_response: Optional[str] = None
    auth_model: Optional[str] = None
    auth_url: Optional[str] = None
    
    # App and merchant
    app_fee: Optional[Decimal] = None
    merchant_fee: Optional[Decimal] = None
    
    # Additional metadata
    order_id: Optional[str] = None
    payment_plan: Optional[str] = None
    subaccount: Optional[str] = None
    
    # Nigerian compliance
    business_income_classified: bool = False
    classification_confidence: Optional[float] = None
    requires_human_review: bool = False
    firs_compliant: bool = False
    invoice_generated: bool = False
    
    # Multi-country compliance
    local_tax_rate: Optional[Decimal] = None
    local_regulations_met: bool = False
    cross_border_transaction: bool = False
    
    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class FlutterwaveRefund:
    """Flutterwave refund information"""
    
    id: int
    tx_id: int
    flw_ref: str
    wallet_id: int
    amount_refunded: Decimal
    status: str
    destination: str
    comment: Optional[str] = None
    created_at: Optional[datetime] = None


@dataclass
class FlutterwaveWebhookEvent:
    """Flutterwave webhook event structure"""
    
    event: str  # charge.completed, transfer.completed, etc.
    event_type: str
    
    # Transaction data
    data: Dict[str, Any]
    
    # Event metadata
    event_id: Optional[str] = None
    created_at: Optional[datetime] = None
    
    # Verification
    verified: bool = False
    signature_valid: bool = False
    
    # Processing
    processed: bool = False
    processing_time: Optional[float] = None
    error_message: Optional[str] = None


# African country to currency mapping
AFRICAN_COUNTRY_CURRENCIES = {
    FlutterwaveCountry.NIGERIA: FlutterwaveCurrency.NGN,
    FlutterwaveCountry.GHANA: FlutterwaveCurrency.GHS,
    FlutterwaveCountry.KENYA: FlutterwaveCurrency.KES,
    FlutterwaveCountry.UGANDA: FlutterwaveCurrency.UGX,
    FlutterwaveCountry.TANZANIA: FlutterwaveCurrency.TZS,
    FlutterwaveCountry.RWANDA: FlutterwaveCurrency.RWF,
    FlutterwaveCountry.ZAMBIA: FlutterwaveCurrency.ZMW,
    FlutterwaveCountry.SOUTH_AFRICA: FlutterwaveCurrency.ZAR,
    FlutterwaveCountry.SENEGAL: FlutterwaveCurrency.XOF,
    FlutterwaveCountry.MALI: FlutterwaveCurrency.XOF,
    FlutterwaveCountry.BURKINA_FASO: FlutterwaveCurrency.XOF,
    FlutterwaveCountry.COTE_DIVOIRE: FlutterwaveCurrency.XOF,
    FlutterwaveCountry.CAMEROON: FlutterwaveCurrency.XAF,
    FlutterwaveCountry.CHAD: FlutterwaveCurrency.XAF,
    FlutterwaveCountry.CENTRAL_AFRICAN_REPUBLIC: FlutterwaveCurrency.XAF,
    FlutterwaveCountry.CONGO: FlutterwaveCurrency.XAF,
    FlutterwaveCountry.DEMOCRATIC_REPUBLIC_CONGO: FlutterwaveCurrency.XAF,
    FlutterwaveCountry.EQUATORIAL_GUINEA: FlutterwaveCurrency.XAF,
    FlutterwaveCountry.GABON: FlutterwaveCurrency.XAF,
}

# Mobile money provider to country mapping
MOBILE_MONEY_COUNTRIES = {
    MobileMoneyProvider.MTN_MOBILE_MONEY_GH: FlutterwaveCountry.GHANA,
    MobileMoneyProvider.VODAFONE_CASH: FlutterwaveCountry.GHANA,
    MobileMoneyProvider.AIRTELTIGO_MONEY: FlutterwaveCountry.GHANA,
    MobileMoneyProvider.M_PESA_KE: FlutterwaveCountry.KENYA,
    MobileMoneyProvider.AIRTEL_MONEY_KE: FlutterwaveCountry.KENYA,
    MobileMoneyProvider.EQUITEL: FlutterwaveCountry.KENYA,
    MobileMoneyProvider.MTN_MOBILE_MONEY_UG: FlutterwaveCountry.UGANDA,
    MobileMoneyProvider.AIRTEL_MONEY_UG: FlutterwaveCountry.UGANDA,
    MobileMoneyProvider.M_PESA_TZ: FlutterwaveCountry.TANZANIA,
    MobileMoneyProvider.AIRTEL_MONEY_TZ: FlutterwaveCountry.TANZANIA,
    MobileMoneyProvider.TIGO_PESA: FlutterwaveCountry.TANZANIA,
    MobileMoneyProvider.MTN_MOBILE_MONEY_RW: FlutterwaveCountry.RWANDA,
    MobileMoneyProvider.AIRTEL_MONEY_RW: FlutterwaveCountry.RWANDA,
    MobileMoneyProvider.MTN_MOBILE_MONEY_ZM: FlutterwaveCountry.ZAMBIA,
    MobileMoneyProvider.AIRTEL_MONEY_ZM: FlutterwaveCountry.ZAMBIA,
}


__all__ = [
    'FlutterwaveEnvironment',
    'FlutterwavePaymentMethod',
    'FlutterwaveCurrency',
    'FlutterwaveCountry',
    'MobileMoneyProvider',
    'FlutterwaveTransactionFee',
    'FlutterwaveCard',
    'FlutterwaveMobileMoney',
    'FlutterwaveCustomer',
    'FlutterwaveTransaction',
    'FlutterwaveRefund',
    'FlutterwaveWebhookEvent',
    'AFRICAN_COUNTRY_CURRENCIES',
    'MOBILE_MONEY_COUNTRIES'
]