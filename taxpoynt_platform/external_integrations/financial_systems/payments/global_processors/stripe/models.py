"""
Stripe Payment Processor Models
==============================

Data models for Stripe integration with comprehensive global payment support.

Features:
- Global payment processing across 40+ countries
- NDPR-compliant data structures with privacy protection
- Support for cards, wallets, bank transfers, and alternative payments
- Multi-currency support (135+ currencies)
- Comprehensive transaction classification for FIRS compliance
- Advanced fraud detection and 3D Secure support
"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional, Any

from .....connector_framework.base_payment_connector import (
    PaymentTransaction, PaymentStatus, PaymentChannel, PaymentType
)


class StripeEnvironment(str, Enum):
    """Stripe environment types"""
    TEST = "test"
    LIVE = "live"


class StripePaymentMethod(str, Enum):
    """Stripe payment methods"""
    CARD = "card"
    BANK_TRANSFER = "bank_transfer"
    SEPA_DEBIT = "sepa_debit"
    ACH_DEBIT = "ach_debit"
    ALIPAY = "alipay"
    APPLE_PAY = "apple_pay"
    GOOGLE_PAY = "google_pay"
    WECHAT_PAY = "wechat_pay"
    IDEAL = "ideal"
    SOFORT = "sofort"
    GIROPAY = "giropay"
    BANCONTACT = "bancontact"
    EPS = "eps"
    PRZELEWY24 = "p24"
    KLARNA = "klarna"
    AFTERPAY = "afterpay_clearpay"
    AFFIRM = "affirm"
    GRABPAY = "grabpay"
    FPXX = "fpx"
    BOLETO = "boleto"
    OXXO = "oxxo"


class StripeCurrency(str, Enum):
    """Major currencies supported by Stripe"""
    # Major global currencies
    USD = "usd"
    EUR = "eur"
    GBP = "gbp"
    JPY = "jpy"
    CNY = "cny"
    
    # African currencies
    NGN = "ngn"
    GHS = "ghs"
    KES = "kes"
    UGX = "ugx"
    TZS = "tzs"
    ZAR = "zar"
    
    # Other regional currencies
    INR = "inr"
    BRL = "brl"
    MXN = "mxn"
    CAD = "cad"
    AUD = "aud"
    CHF = "chf"
    SEK = "sek"
    NOK = "nok"
    DKK = "dkk"
    PLN = "pln"
    SGD = "sgd"
    HKD = "hkd"


class StripeCountry(str, Enum):
    """Countries where Stripe operates"""
    # Major markets
    UNITED_STATES = "US"
    UNITED_KINGDOM = "GB"
    CANADA = "CA"
    AUSTRALIA = "AU"
    
    # European Union
    GERMANY = "DE"
    FRANCE = "FR"
    ITALY = "IT"
    SPAIN = "ES"
    NETHERLANDS = "NL"
    AUSTRIA = "AT"
    BELGIUM = "BE"
    DENMARK = "DK"
    FINLAND = "FI"
    IRELAND = "IE"
    LUXEMBOURG = "LU"
    NORWAY = "NO"
    POLAND = "PL"
    PORTUGAL = "PT"
    SWEDEN = "SE"
    SWITZERLAND = "CH"
    
    # Asia Pacific
    JAPAN = "JP"
    SINGAPORE = "SG"
    HONG_KONG = "HK"
    MALAYSIA = "MY"
    NEW_ZEALAND = "NZ"
    
    # Latin America
    BRAZIL = "BR"
    MEXICO = "MX"
    
    # Africa
    SOUTH_AFRICA = "ZA"
    
    # Other
    INDIA = "IN"


class StripePaymentStatus(str, Enum):
    """Stripe-specific payment statuses"""
    REQUIRES_PAYMENT_METHOD = "requires_payment_method"
    REQUIRES_CONFIRMATION = "requires_confirmation"
    REQUIRES_ACTION = "requires_action"
    PROCESSING = "processing"
    REQUIRES_CAPTURE = "requires_capture"
    CANCELED = "canceled"
    SUCCEEDED = "succeeded"


class StripeFraudOutcome(str, Enum):
    """Stripe fraud detection outcomes"""
    MANUAL_REVIEW = "manual_review"
    PASS = "pass"
    FAIL = "fail"


@dataclass
class StripeCard:
    """Stripe card payment details"""
    
    last4: Optional[str] = None
    brand: Optional[str] = None  # visa, mastercard, amex, etc.
    country: Optional[str] = None
    exp_month: Optional[int] = None
    exp_year: Optional[int] = None
    fingerprint: Optional[str] = None
    funding: Optional[str] = None  # credit, debit, prepaid
    
    # 3D Secure
    three_d_secure: Optional[str] = None  # required, optional, not_supported
    
    # CVC check
    cvc_check: Optional[str] = None  # pass, fail, unavailable
    
    # Address verification
    address_line1_check: Optional[str] = None
    address_postal_code_check: Optional[str] = None


@dataclass
class StripeBillingDetails:
    """Billing details for payments"""
    
    address: Optional[Dict[str, str]] = None
    email: Optional[str] = None
    name: Optional[str] = None
    phone: Optional[str] = None


@dataclass
class StripeOutcome:
    """Payment outcome details"""
    
    network_status: Optional[str] = None
    reason: Optional[str] = None
    risk_level: Optional[str] = None
    risk_score: Optional[int] = None
    seller_message: Optional[str] = None
    type: Optional[str] = None


@dataclass
class StripeFraudDetails:
    """Fraud detection details"""
    
    stripe_report: Optional[str] = None
    user_report: Optional[str] = None


@dataclass
class StripeCustomer:
    """Stripe customer information"""
    
    id: Optional[str] = None
    email: Optional[str] = None
    name: Optional[str] = None
    phone: Optional[str] = None
    
    # Business customer details
    business_name: Optional[str] = None
    business_type: Optional[str] = None
    business_tax_id: Optional[str] = None
    
    # Location
    country: Optional[StripeCountry] = None
    address: Optional[Dict[str, str]] = None
    
    # Billing
    currency: Optional[StripeCurrency] = None
    default_payment_method: Optional[str] = None
    
    # Account details
    created: Optional[datetime] = None
    delinquent: bool = False
    
    # Privacy protection
    privacy_protected: bool = False
    consent_granted: bool = False


@dataclass
class StripeTransaction(PaymentTransaction):
    """
    Stripe transaction with global payment support
    """
    
    # Stripe specific fields
    stripe_id: Optional[str] = None
    payment_intent_id: Optional[str] = None
    charge_id: Optional[str] = None
    transfer_group: Optional[str] = None
    
    # Payment method details
    payment_method_type: Optional[StripePaymentMethod] = None
    card_details: Optional[StripeCard] = None
    billing_details: Optional[StripeBillingDetails] = None
    
    # Geographic information
    country: Optional[StripeCountry] = None
    
    # Currency and conversion
    presentment_currency: Optional[StripeCurrency] = None
    settlement_currency: Optional[StripeCurrency] = None
    exchange_rate: Optional[Decimal] = None
    
    # Customer information
    customer: Optional[StripeCustomer] = None
    
    # Payment flow
    confirmation_method: Optional[str] = None  # automatic, manual
    capture_method: Optional[str] = None      # automatic, manual
    setup_future_usage: Optional[str] = None  # on_session, off_session
    
    # Security and fraud
    outcome: Optional[StripeOutcome] = None
    fraud_details: Optional[StripeFraudDetails] = None
    
    # Fees and settlement
    application_fee: Optional[Decimal] = None
    processing_fee: Optional[Decimal] = None
    net_amount: Optional[Decimal] = None
    
    # Receipts and documentation
    receipt_email: Optional[str] = None
    receipt_number: Optional[str] = None
    receipt_url: Optional[str] = None
    
    # Transfer and marketplace
    destination_account: Optional[str] = None
    transfer_data: Optional[Dict[str, Any]] = None
    on_behalf_of: Optional[str] = None
    
    # Subscription and recurring
    subscription_id: Optional[str] = None
    invoice_id: Optional[str] = None
    
    # Dispute information
    disputed: bool = False
    dispute_reason: Optional[str] = None
    dispute_status: Optional[str] = None
    
    # Classification for tax compliance
    business_income_classified: bool = False
    classification_confidence: Optional[float] = None
    requires_human_review: bool = False
    firs_compliant: bool = False
    invoice_generated: bool = False
    
    # Global compliance
    tax_rate: Optional[Decimal] = None
    tax_amount: Optional[Decimal] = None
    local_regulations_met: bool = False
    cross_border_transaction: bool = False
    
    # Stripe specific timestamps
    created: Optional[datetime] = None
    updated: Optional[datetime] = None


@dataclass
class StripeRefund:
    """Stripe refund information"""
    
    id: str
    charge: str
    amount: Decimal
    currency: StripeCurrency
    reason: Optional[str] = None
    status: Optional[str] = None
    
    # Metadata
    metadata: Optional[Dict[str, str]] = None
    receipt_number: Optional[str] = None
    
    # Timestamps
    created: Optional[datetime] = None


@dataclass
class StripeWebhookEvent:
    """Stripe webhook event structure"""
    
    id: str
    type: str  # payment_intent.succeeded, charge.failed, etc.
    api_version: str
    
    # Event data
    data: Dict[str, Any]
    
    # Request info
    request: Optional[Dict[str, str]] = None
    
    # Event metadata
    created: Optional[datetime] = None
    livemode: bool = False
    pending_webhooks: int = 0
    
    # Verification
    verified: bool = False
    signature_valid: bool = False
    
    # Processing
    processed: bool = False
    processing_time: Optional[float] = None
    error_message: Optional[str] = None


# Global country to currency mapping for Stripe
STRIPE_COUNTRY_CURRENCIES = {
    StripeCountry.UNITED_STATES: StripeCurrency.USD,
    StripeCountry.UNITED_KINGDOM: StripeCurrency.GBP,
    StripeCountry.CANADA: StripeCurrency.CAD,
    StripeCountry.AUSTRALIA: StripeCurrency.AUD,
    StripeCountry.GERMANY: StripeCurrency.EUR,
    StripeCountry.FRANCE: StripeCurrency.EUR,
    StripeCountry.ITALY: StripeCurrency.EUR,
    StripeCountry.SPAIN: StripeCurrency.EUR,
    StripeCountry.NETHERLANDS: StripeCurrency.EUR,
    StripeCountry.AUSTRIA: StripeCurrency.EUR,
    StripeCountry.BELGIUM: StripeCurrency.EUR,
    StripeCountry.DENMARK: StripeCurrency.DKK,
    StripeCountry.FINLAND: StripeCurrency.EUR,
    StripeCountry.IRELAND: StripeCurrency.EUR,
    StripeCountry.LUXEMBOURG: StripeCurrency.EUR,
    StripeCountry.NORWAY: StripeCurrency.NOK,
    StripeCountry.POLAND: StripeCurrency.PLN,
    StripeCountry.PORTUGAL: StripeCurrency.EUR,
    StripeCountry.SWEDEN: StripeCurrency.SEK,
    StripeCountry.SWITZERLAND: StripeCurrency.CHF,
    StripeCountry.JAPAN: StripeCurrency.JPY,
    StripeCountry.SINGAPORE: StripeCurrency.SGD,
    StripeCountry.HONG_KONG: StripeCurrency.HKD,
    StripeCountry.NEW_ZEALAND: StripeCurrency.USD,  # Often USD for international
    StripeCountry.BRAZIL: StripeCurrency.BRL,
    StripeCountry.MEXICO: StripeCurrency.MXN,
    StripeCountry.SOUTH_AFRICA: StripeCurrency.ZAR,
    StripeCountry.INDIA: StripeCurrency.INR,
}

# Payment method availability by country
STRIPE_PAYMENT_METHODS_BY_COUNTRY = {
    StripeCountry.UNITED_STATES: [
        StripePaymentMethod.CARD, StripePaymentMethod.ACH_DEBIT,
        StripePaymentMethod.APPLE_PAY, StripePaymentMethod.GOOGLE_PAY,
        StripePaymentMethod.KLARNA, StripePaymentMethod.AFFIRM,
        StripePaymentMethod.AFTERPAY
    ],
    StripeCountry.UNITED_KINGDOM: [
        StripePaymentMethod.CARD, StripePaymentMethod.BANK_TRANSFER,
        StripePaymentMethod.APPLE_PAY, StripePaymentMethod.GOOGLE_PAY
    ],
    StripeCountry.GERMANY: [
        StripePaymentMethod.CARD, StripePaymentMethod.SEPA_DEBIT,
        StripePaymentMethod.SOFORT, StripePaymentMethod.GIROPAY,
        StripePaymentMethod.EPS, StripePaymentMethod.KLARNA
    ],
    StripeCountry.NETHERLANDS: [
        StripePaymentMethod.CARD, StripePaymentMethod.SEPA_DEBIT,
        StripePaymentMethod.IDEAL, StripePaymentMethod.BANCONTACT
    ],
    # Add more countries as needed
}


__all__ = [
    'StripeEnvironment',
    'StripePaymentMethod',
    'StripeCurrency',
    'StripeCountry',
    'StripePaymentStatus',
    'StripeFraudOutcome',
    'StripeCard',
    'StripeBillingDetails',
    'StripeOutcome',
    'StripeFraudDetails',
    'StripeCustomer',
    'StripeTransaction',
    'StripeRefund',
    'StripeWebhookEvent',
    'STRIPE_COUNTRY_CURRENCIES',
    'STRIPE_PAYMENT_METHODS_BY_COUNTRY'
]