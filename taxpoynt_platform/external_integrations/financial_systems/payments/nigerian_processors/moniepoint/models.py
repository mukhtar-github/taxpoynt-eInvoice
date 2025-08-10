"""
Moniepoint Data Models
=====================

Data models for Moniepoint payment processor integration.
Designed for Nigerian agent banking and business payment scenarios.

Features:
- Agent banking transaction structure
- POS terminal transaction support
- Business payment categorization
- NDPR-compliant data handling
- Nigerian banking integration
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


class MoniepointTransactionType(Enum):
    """Moniepoint-specific transaction types."""
    AGENT_BANKING = "agent_banking"
    POS_PAYMENT = "pos_payment"
    MOBILE_MONEY = "mobile_money"
    BUSINESS_PAYMENT = "business_payment"
    BILL_PAYMENT = "bill_payment"
    FUNDS_TRANSFER = "funds_transfer"
    CASH_DEPOSIT = "cash_deposit"
    CASH_WITHDRAWAL = "cash_withdrawal"
    CROSS_BORDER = "cross_border"


class MoniepointChannel(Enum):
    """Moniepoint payment channels."""
    AGENT_POS = "agent_pos"
    MOBILE_APP = "mobile_app"
    WEB_PORTAL = "web_portal"
    API = "api"
    USSD = "ussd"
    QR_CODE = "qr_code"


class AgentInfo(Enum):
    """Agent banking information levels."""
    VERIFIED_AGENT = "verified_agent"
    SUPER_AGENT = "super_agent"
    TERMINAL_AGENT = "terminal_agent"
    MOBILE_AGENT = "mobile_agent"


@dataclass
class MoniepointCustomer(PaymentCustomer):
    """Extended customer model for Moniepoint with agent banking context."""
    
    # Agent banking specific
    agent_id: Optional[str] = None
    agent_name: Optional[str] = None
    agent_location: Optional[str] = None
    agent_tier: Optional[AgentInfo] = None
    
    # Business verification
    business_verification_status: Optional[str] = None
    business_category: Optional[str] = None
    business_registration_number: Optional[str] = None
    
    # Transaction limits
    daily_transaction_limit: Optional[Decimal] = None
    transaction_count_today: Optional[int] = None
    
    # KYC information
    kyc_level: Optional[str] = None  # Level 1, 2, 3 per CBN guidelines
    bvn_linked: bool = False
    nin_linked: bool = False


@dataclass
class MoniepointTransaction(PaymentTransaction):
    """Extended transaction model for Moniepoint with agent banking features."""
    
    # Moniepoint specific identifiers
    moniepoint_transaction_id: str = ""
    moniepoint_reference: str = ""
    agent_reference: Optional[str] = None
    
    # Agent banking context
    agent_id: Optional[str] = None
    agent_name: Optional[str] = None
    agent_terminal_id: Optional[str] = None
    agent_location: Optional[str] = None
    agent_commission: Optional[Decimal] = None
    
    # Moniepoint transaction details
    moniepoint_transaction_type: Optional[MoniepointTransactionType] = None
    channel: Optional[MoniepointChannel] = None
    
    # Business context
    business_category: Optional[str] = None
    transaction_purpose: Optional[str] = None
    beneficiary_account: Optional[str] = None
    beneficiary_bank_code: Optional[str] = None
    beneficiary_bank_name: Optional[str] = None
    
    # Nigerian banking compliance
    cbn_transaction_code: Optional[str] = None
    nibss_session_id: Optional[str] = None
    narration: Optional[str] = None
    
    # Regulatory information
    foreign_exchange_rate: Optional[Decimal] = None
    regulatory_code: Optional[str] = None
    compliance_notes: List[str] = None
    
    # Settlement information
    settlement_bank: Optional[str] = None
    settlement_account: Optional[str] = None
    settlement_date: Optional[datetime] = None
    settlement_reference: Optional[str] = None
    
    # Risk and fraud detection
    risk_score: Optional[float] = None
    fraud_flags: List[str] = None
    transaction_velocity: Optional[str] = None  # high, medium, low
    
    # Mobile money specific (for Moniepoint mobile services)
    mobile_number: Optional[str] = None
    mobile_network: Optional[str] = None  # MTN, Airtel, Glo, 9mobile
    mobile_money_provider: Optional[str] = None
    
    # Business intelligence fields
    merchant_category_code: Optional[str] = None
    industry_classification: Optional[str] = None
    geographic_zone: Optional[str] = None  # Lagos, Abuja, Port Harcourt, etc.
    
    # Enhanced metadata for Nigerian business context
    nigerian_metadata: Optional[Dict[str, Any]] = None


@dataclass 
class MoniepointRefund:
    """Moniepoint refund transaction model."""
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
    
    # Agent context
    agent_id: Optional[str] = None
    agent_approval_required: bool = False
    
    # Compliance
    refund_approval_reference: Optional[str] = None
    regulatory_approval: bool = False
    
    # Metadata
    refund_metadata: Optional[Dict[str, Any]] = None


@dataclass
class MoniepointSettlement:
    """Moniepoint settlement information."""
    settlement_id: str
    settlement_reference: str
    settlement_date: datetime
    
    # Amount details
    gross_amount: Decimal
    fees: Decimal
    net_amount: Decimal
    currency: str = "NGN"
    
    # Settlement account
    settlement_bank_code: str
    settlement_account_number: str
    settlement_account_name: str
    
    # Transactions included
    transaction_count: int
    transaction_ids: List[str]
    
    # Agent banking specific
    agent_settlements: Optional[List[Dict[str, Any]]] = None
    commission_breakdown: Optional[Dict[str, Decimal]] = None
    
    # Status and processing
    settlement_status: str = "pending"  # pending, processing, completed, failed
    processing_bank: Optional[str] = None
    processing_reference: Optional[str] = None
    
    # Nigerian banking compliance
    cbn_settlement_code: Optional[str] = None
    nibss_settlement_reference: Optional[str] = None


@dataclass
class MoniepointWebhookEvent:
    """Moniepoint webhook event structure."""
    event_id: str
    event_type: str
    event_timestamp: datetime
    
    # Transaction context
    transaction_id: Optional[str] = None
    transaction_reference: Optional[str] = None
    agent_id: Optional[str] = None
    
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
    business_impact: Optional[str] = None  # invoice_required, settlement_update, etc.
    requires_compliance_action: bool = False


# Nigerian business categories for Moniepoint transactions
NIGERIAN_BUSINESS_CATEGORIES = {
    "retail": "Retail Trade",
    "wholesale": "Wholesale Trade", 
    "manufacturing": "Manufacturing",
    "agriculture": "Agriculture",
    "technology": "Information Technology",
    "financial_services": "Financial Services",
    "telecommunications": "Telecommunications",
    "transportation": "Transportation",
    "construction": "Construction",
    "hospitality": "Hospitality",
    "healthcare": "Healthcare",
    "education": "Education",
    "real_estate": "Real Estate",
    "oil_gas": "Oil and Gas",
    "mining": "Mining",
    "utilities": "Utilities",
    "government": "Government Services"
}

# Agent banking transaction codes (CBN guidelines)
AGENT_BANKING_CODES = {
    "cash_deposit": "50001",
    "cash_withdrawal": "50002", 
    "funds_transfer": "50003",
    "bill_payment": "50004",
    "airtime_purchase": "50005",
    "account_opening": "50006",
    "balance_inquiry": "50007",
    "mini_statement": "50008"
}

# Risk assessment thresholds for Nigerian context
NIGERIAN_RISK_THRESHOLDS = {
    "high_value_threshold": Decimal("500000"),  # ₦500,000
    "suspicious_velocity_threshold": 10,  # transactions per hour
    "agent_daily_limit": Decimal("2000000"),  # ₦2,000,000
    "cross_border_threshold": Decimal("10000"),  # $10,000 equivalent
    "cash_transaction_reporting_threshold": Decimal("5000000")  # ₦5,000,000
}


def create_moniepoint_transaction_from_api_data(api_data: Dict[str, Any]) -> MoniepointTransaction:
    """Create MoniepointTransaction from API response data."""
    
    return MoniepointTransaction(
        transaction_id=api_data.get('id', ''),
        reference=api_data.get('reference', ''),
        amount=Decimal(str(api_data.get('amount', 0))) / 100,  # Convert from kobo
        currency=api_data.get('currency', 'NGN'),
        payment_method=PaymentMethod.BANK_TRANSFER,  # Default for Moniepoint
        payment_status=PaymentStatus.SUCCESS if api_data.get('status') == 'success' else PaymentStatus.PENDING,
        transaction_type=TransactionType.PAYMENT,
        created_at=datetime.fromisoformat(api_data.get('created_at', datetime.now().isoformat())),
        
        # Moniepoint specific
        moniepoint_transaction_id=api_data.get('moniepoint_id', ''),
        moniepoint_reference=api_data.get('moniepoint_reference', ''),
        agent_id=api_data.get('agent_id'),
        agent_name=api_data.get('agent_name'),
        agent_terminal_id=api_data.get('terminal_id'),
        
        # Business context
        business_category=api_data.get('business_category'),
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
        nigerian_metadata={
            'processor': 'moniepoint',
            'agent_banking': True,
            'compliance_checked': False
        }
    )


# Export main models
__all__ = [
    'MoniepointTransaction',
    'MoniepointCustomer',
    'MoniepointRefund',
    'MoniepointSettlement',
    'MoniepointWebhookEvent',
    'MoniepointTransactionType',
    'MoniepointChannel',
    'AgentInfo',
    'NIGERIAN_BUSINESS_CATEGORIES',
    'AGENT_BANKING_CODES',
    'NIGERIAN_RISK_THRESHOLDS',
    'create_moniepoint_transaction_from_api_data'
]