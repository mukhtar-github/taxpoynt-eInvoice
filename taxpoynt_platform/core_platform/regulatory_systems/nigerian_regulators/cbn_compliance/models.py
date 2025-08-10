"""
CBN Compliance Data Models
==========================
Pydantic models for Central Bank of Nigeria (CBN) banking compliance validation.
"""
from datetime import datetime, date
from decimal import Decimal
from typing import Dict, Any, List, Optional, Union
from enum import Enum
from pydantic import BaseModel, Field, validator

from ...compliance_engine.orchestrator.models import ComplianceStatus, RiskLevel


class CBNComplianceStatus(Enum):
    """CBN-specific compliance status levels."""
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    CONDITIONAL_COMPLIANCE = "conditional_compliance"
    UNDER_REVIEW = "under_review"
    SUSPENDED = "suspended"
    REVOKED = "revoked"
    PENDING_APPROVAL = "pending_approval"


class CBNRiskLevel(Enum):
    """CBN risk assessment levels."""
    MINIMAL = "minimal"
    LOW = "low" 
    MODERATE = "moderate"
    HIGH = "high"
    SEVERE = "severe"
    CRITICAL = "critical"


class CBNRegulationType(Enum):
    """Types of CBN regulations."""
    BANKING_LICENSE = "banking_license"
    PRUDENTIAL_GUIDELINES = "prudential_guidelines"
    KYC_REQUIREMENTS = "kyc_requirements"
    AML_COMPLIANCE = "aml_compliance"
    PAYMENT_SYSTEMS = "payment_systems"
    FOREX_REGULATIONS = "forex_regulations"
    CONSUMER_PROTECTION = "consumer_protection"
    CAPITAL_ADEQUACY = "capital_adequacy"
    RISK_MANAGEMENT = "risk_management"
    CORPORATE_GOVERNANCE = "corporate_governance"
    ELECTRONIC_PAYMENT = "electronic_payment"
    MICROFINANCE = "microfinance"
    MOBILE_MONEY = "mobile_money"


class BankingLicenseType(Enum):
    """Types of banking licenses in Nigeria."""
    COMMERCIAL_BANK = "commercial_bank"
    MERCHANT_BANK = "merchant_bank"
    MICROFINANCE_BANK = "microfinance_bank"
    SPECIALIZED_BANK = "specialized_bank"
    DEVELOPMENT_FINANCE_INSTITUTION = "development_finance_institution"
    PRIMARY_MORTGAGE_INSTITUTION = "primary_mortgage_institution"
    FINANCE_COMPANY = "finance_company"
    BUREAU_DE_CHANGE = "bureau_de_change"
    PAYMENT_SERVICE_BANK = "payment_service_bank"


class KYCTier(Enum):
    """KYC tier levels for customer verification."""
    TIER_1 = "tier_1"  # Basic KYC
    TIER_2 = "tier_2"  # Enhanced KYC
    TIER_3 = "tier_3"  # Full KYC
    CORPORATE = "corporate"  # Corporate KYC


class AMLRiskRating(Enum):
    """AML risk rating for customers and transactions."""
    LOW_RISK = "low_risk"
    MEDIUM_RISK = "medium_risk"
    HIGH_RISK = "high_risk"
    VERY_HIGH_RISK = "very_high_risk"
    PROHIBITED = "prohibited"


class TransactionType(Enum):
    """Types of financial transactions."""
    CASH_DEPOSIT = "cash_deposit"
    CASH_WITHDRAWAL = "cash_withdrawal"
    ELECTRONIC_TRANSFER = "electronic_transfer"
    INTERNATIONAL_TRANSFER = "international_transfer"
    FOREX_TRANSACTION = "forex_transaction"
    LOAN_DISBURSEMENT = "loan_disbursement"
    LOAN_REPAYMENT = "loan_repayment"
    INVESTMENT = "investment"
    TRADE_FINANCE = "trade_finance"


class PaymentSystemType(Enum):
    """Types of payment systems."""
    REAL_TIME_GROSS_SETTLEMENT = "rtgs"
    AUTOMATED_CLEARING_HOUSE = "ach"
    CARD_PAYMENT_SYSTEM = "card_payment"
    MOBILE_PAYMENT = "mobile_payment"
    INTERNET_BANKING = "internet_banking"
    POS_TERMINAL = "pos_terminal"
    ATM_NETWORK = "atm_network"
    USSD_PAYMENT = "ussd_payment"


class CBNComplianceRequest(BaseModel):
    """Request for CBN compliance validation."""
    request_id: str = Field(..., description="Unique request identifier")
    organization_id: str = Field(..., description="Organization identifier")
    regulation_types: List[CBNRegulationType] = Field(..., description="Types of regulations to validate")
    validation_data: Dict[str, Any] = Field(..., description="Data to validate")
    license_type: Optional[BankingLicenseType] = Field(None, description="Banking license type if applicable")
    effective_date: Optional[date] = Field(None, description="Effective date for compliance")
    include_recommendations: bool = Field(True, description="Include compliance recommendations")
    
    class Config:
        use_enum_values = True


class CBNValidationResult(BaseModel):
    """Result of CBN compliance validation."""
    validation_id: str = Field(..., description="Validation result identifier")
    request_id: str = Field(..., description="Original request identifier")
    overall_status: CBNComplianceStatus = Field(..., description="Overall compliance status")
    risk_level: CBNRiskLevel = Field(..., description="Risk assessment level")
    compliance_score: float = Field(..., ge=0, le=100, description="Compliance score (0-100)")
    regulation_results: Dict[str, Dict[str, Any]] = Field(..., description="Results by regulation type")
    violations: List[Dict[str, Any]] = Field(default_factory=list, description="Compliance violations")
    recommendations: List[str] = Field(default_factory=list, description="Compliance recommendations")
    next_review_date: Optional[date] = Field(None, description="Next compliance review date")
    regulatory_actions: List[str] = Field(default_factory=list, description="Required regulatory actions")
    validated_at: datetime = Field(default_factory=datetime.now, description="Validation timestamp")
    expires_at: Optional[datetime] = Field(None, description="Validation expiry timestamp")
    
    class Config:
        use_enum_values = True


class BankingLicense(BaseModel):
    """Banking license information."""
    license_number: str = Field(..., description="CBN license number")
    license_type: BankingLicenseType = Field(..., description="Type of banking license")
    institution_name: str = Field(..., description="Financial institution name")
    issued_date: date = Field(..., description="License issued date")
    expiry_date: Optional[date] = Field(None, description="License expiry date")
    status: CBNComplianceStatus = Field(..., description="License status")
    authorized_capital: Decimal = Field(..., description="Authorized capital amount")
    paid_up_capital: Decimal = Field(..., description="Paid-up capital amount")
    authorized_activities: List[str] = Field(..., description="Authorized banking activities")
    operating_locations: List[str] = Field(..., description="Authorized operating locations")
    conditions: List[str] = Field(default_factory=list, description="License conditions")
    restrictions: List[str] = Field(default_factory=list, description="License restrictions")
    last_inspection_date: Optional[date] = Field(None, description="Last CBN inspection date")
    
    @validator('paid_up_capital')
    def validate_paid_up_capital(cls, v, values):
        if 'authorized_capital' in values and v > values['authorized_capital']:
            raise ValueError('Paid-up capital cannot exceed authorized capital')
        return v
    
    class Config:
        use_enum_values = True


class KYCProfile(BaseModel):
    """Customer KYC profile information."""
    customer_id: str = Field(..., description="Customer identifier")
    kyc_tier: KYCTier = Field(..., description="KYC verification tier")
    full_name: str = Field(..., description="Customer full name")
    date_of_birth: Optional[date] = Field(None, description="Date of birth")
    nationality: str = Field(..., description="Customer nationality")
    identification_type: str = Field(..., description="ID document type")
    identification_number: str = Field(..., description="ID document number")
    bvn: Optional[str] = Field(None, description="Bank Verification Number")
    nin: Optional[str] = Field(None, description="National Identification Number")
    address: str = Field(..., description="Customer address")
    phone_number: str = Field(..., description="Phone number")
    email: Optional[str] = Field(None, description="Email address")
    occupation: str = Field(..., description="Customer occupation")
    employer: Optional[str] = Field(None, description="Employer information")
    income_source: str = Field(..., description="Source of income")
    monthly_income: Optional[Decimal] = Field(None, description="Monthly income amount")
    kyc_completion_date: date = Field(..., description="KYC completion date")
    last_update_date: date = Field(..., description="Last KYC update date")
    verification_status: CBNComplianceStatus = Field(..., description="KYC verification status")
    risk_rating: AMLRiskRating = Field(..., description="AML risk rating")
    due_diligence_level: str = Field(..., description="Due diligence level applied")
    
    @validator('bvn')
    def validate_bvn(cls, v):
        if v and len(v) != 11:
            raise ValueError('BVN must be 11 digits')
        return v
    
    @validator('nin')
    def validate_nin(cls, v):
        if v and len(v) != 11:
            raise ValueError('NIN must be 11 digits')
        return v
    
    class Config:
        use_enum_values = True


class AMLTransaction(BaseModel):
    """Anti-Money Laundering transaction record."""
    transaction_id: str = Field(..., description="Transaction identifier")
    customer_id: str = Field(..., description="Customer identifier")
    transaction_type: TransactionType = Field(..., description="Transaction type")
    amount: Decimal = Field(..., description="Transaction amount")
    currency: str = Field(default="NGN", description="Transaction currency")
    transaction_date: datetime = Field(..., description="Transaction date and time")
    originator_account: Optional[str] = Field(None, description="Originator account")
    beneficiary_account: Optional[str] = Field(None, description="Beneficiary account")
    purpose: str = Field(..., description="Transaction purpose")
    channel: str = Field(..., description="Transaction channel")
    location: Optional[str] = Field(None, description="Transaction location")
    risk_score: float = Field(..., ge=0, le=100, description="AML risk score")
    risk_factors: List[str] = Field(default_factory=list, description="Identified risk factors")
    suspicious_activity: bool = Field(default=False, description="Flagged as suspicious")
    reported_to_nfiu: bool = Field(default=False, description="Reported to NFIU")
    report_date: Optional[datetime] = Field(None, description="NFIU report date")
    compliance_officer_review: bool = Field(default=False, description="Compliance officer reviewed")
    review_notes: Optional[str] = Field(None, description="Compliance review notes")
    
    @validator('amount')
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError('Transaction amount must be positive')
        return v
    
    class Config:
        use_enum_values = True


class PaymentSystemRegistration(BaseModel):
    """Payment system operator registration."""
    registration_id: str = Field(..., description="Registration identifier")
    operator_name: str = Field(..., description="Payment system operator name")
    system_type: PaymentSystemType = Field(..., description="Payment system type")
    registration_date: date = Field(..., description="Registration date")
    license_number: str = Field(..., description="Operating license number")
    authorized_services: List[str] = Field(..., description="Authorized payment services")
    operational_guidelines: List[str] = Field(..., description="Operational guidelines")
    technical_standards: List[str] = Field(..., description="Technical standards compliance")
    risk_management_framework: str = Field(..., description="Risk management framework")
    security_standards: List[str] = Field(..., description="Security standards compliance")
    settlement_arrangements: str = Field(..., description="Settlement arrangements")
    business_continuity_plan: bool = Field(..., description="BCP in place")
    annual_fee_paid: bool = Field(default=False, description="Annual regulatory fee paid")
    last_compliance_review: Optional[date] = Field(None, description="Last compliance review date")
    status: CBNComplianceStatus = Field(..., description="Registration status")
    
    class Config:
        use_enum_values = True


class ForexTransaction(BaseModel):
    """Foreign exchange transaction record."""
    transaction_id: str = Field(..., description="Transaction identifier")
    customer_id: str = Field(..., description="Customer identifier")
    transaction_type: str = Field(..., description="Forex transaction type")
    source_currency: str = Field(..., description="Source currency")
    target_currency: str = Field(..., description="Target currency")
    source_amount: Decimal = Field(..., description="Source currency amount")
    target_amount: Decimal = Field(..., description="Target currency amount")
    exchange_rate: Decimal = Field(..., description="Applied exchange rate")
    transaction_date: datetime = Field(..., description="Transaction date")
    purpose: str = Field(..., description="Transaction purpose")
    supporting_documents: List[str] = Field(..., description="Supporting documentation")
    coi_reference: Optional[str] = Field(None, description="Certificate of Inward Investment reference")
    cdti_reference: Optional[str] = Field(None, description="Capital and Documentation Tax Incentive reference")
    regulatory_approval: Optional[str] = Field(None, description="Regulatory approval reference")
    limits_compliance: bool = Field(..., description="Within regulatory limits")
    reporting_requirement: bool = Field(..., description="Requires regulatory reporting")
    reported_to_cbn: bool = Field(default=False, description="Reported to CBN")
    compliance_status: CBNComplianceStatus = Field(..., description="Compliance status")
    
    @validator('source_amount', 'target_amount')
    def validate_amounts(cls, v):
        if v <= 0:
            raise ValueError('Transaction amounts must be positive')
        return v
    
    class Config:
        use_enum_values = True


class ConsumerComplaint(BaseModel):
    """Consumer protection complaint record."""
    complaint_id: str = Field(..., description="Complaint identifier")
    customer_id: str = Field(..., description="Customer identifier")
    financial_institution: str = Field(..., description="Financial institution name")
    complaint_type: str = Field(..., description="Type of complaint")
    complaint_category: str = Field(..., description="Complaint category")
    description: str = Field(..., description="Complaint description")
    amount_involved: Optional[Decimal] = Field(None, description="Amount involved")
    date_of_incident: date = Field(..., description="Date of incident")
    complaint_date: date = Field(..., description="Complaint registration date")
    resolution_timeframe: int = Field(..., description="Resolution timeframe (days)")
    current_status: str = Field(..., description="Current resolution status")
    resolution_date: Optional[date] = Field(None, description="Resolution date")
    resolution_details: Optional[str] = Field(None, description="Resolution details")
    customer_satisfaction: Optional[str] = Field(None, description="Customer satisfaction rating")
    escalated_to_cbn: bool = Field(default=False, description="Escalated to CBN")
    regulatory_action: Optional[str] = Field(None, description="CBN regulatory action")
    
    class Config:
        use_enum_values = True


class RiskAssessment(BaseModel):
    """Institutional risk assessment."""
    assessment_id: str = Field(..., description="Assessment identifier")
    institution_id: str = Field(..., description="Institution identifier")
    assessment_date: date = Field(..., description="Assessment date")
    assessment_type: str = Field(..., description="Type of risk assessment")
    risk_categories: Dict[str, CBNRiskLevel] = Field(..., description="Risk levels by category")
    overall_risk_rating: CBNRiskLevel = Field(..., description="Overall risk rating")
    capital_adequacy_ratio: Decimal = Field(..., description="Capital adequacy ratio")
    liquidity_ratio: Decimal = Field(..., description="Liquidity ratio")
    credit_risk_exposure: Decimal = Field(..., description="Credit risk exposure")
    operational_risk_score: float = Field(..., description="Operational risk score")
    market_risk_exposure: Decimal = Field(..., description="Market risk exposure")
    regulatory_compliance_score: float = Field(..., description="Regulatory compliance score")
    governance_rating: str = Field(..., description="Corporate governance rating")
    stress_test_results: Dict[str, Any] = Field(..., description="Stress test results")
    risk_mitigation_measures: List[str] = Field(..., description="Risk mitigation measures")
    regulatory_actions_required: List[str] = Field(default_factory=list, description="Required regulatory actions")
    next_assessment_date: date = Field(..., description="Next assessment date")
    
    @validator('capital_adequacy_ratio')
    def validate_capital_adequacy(cls, v):
        if v < 0:
            raise ValueError('Capital adequacy ratio cannot be negative')
        return v
    
    class Config:
        use_enum_values = True


class CBNRegulationUpdate(BaseModel):
    """CBN regulation update notification."""
    update_id: str = Field(..., description="Update identifier")
    regulation_type: CBNRegulationType = Field(..., description="Regulation type")
    title: str = Field(..., description="Update title")
    description: str = Field(..., description="Update description")
    effective_date: date = Field(..., description="Effective date")
    compliance_deadline: date = Field(..., description="Compliance deadline")
    affected_institutions: List[str] = Field(..., description="Affected institution types")
    implementation_requirements: List[str] = Field(..., description="Implementation requirements")
    penalties: Optional[str] = Field(None, description="Non-compliance penalties")
    guidance_documents: List[str] = Field(default_factory=list, description="Guidance documents")
    contact_information: str = Field(..., description="CBN contact for queries")
    
    class Config:
        use_enum_values = True


class CBNComplianceMetrics(BaseModel):
    """CBN compliance metrics and KPIs."""
    organization_id: str = Field(..., description="Organization identifier")
    reporting_period: str = Field(..., description="Reporting period")
    generated_at: datetime = Field(default_factory=datetime.now, description="Metrics generation timestamp")
    
    # License compliance metrics
    license_compliance_score: float = Field(..., ge=0, le=100, description="License compliance score")
    license_status: CBNComplianceStatus = Field(..., description="License status")
    license_expiry_days: Optional[int] = Field(None, description="Days until license expiry")
    
    # KYC/AML metrics
    kyc_completion_rate: float = Field(..., ge=0, le=100, description="KYC completion rate")
    aml_risk_exposure: CBNRiskLevel = Field(..., description="AML risk exposure level")
    suspicious_transactions_count: int = Field(..., description="Suspicious transactions count")
    nfiu_reports_filed: int = Field(..., description="NFIU reports filed")
    
    # Payment system metrics
    payment_system_uptime: float = Field(..., ge=0, le=100, description="Payment system uptime percentage")
    transaction_success_rate: float = Field(..., ge=0, le=100, description="Transaction success rate")
    settlement_delays: int = Field(..., description="Settlement delays count")
    
    # Risk management metrics
    capital_adequacy_ratio: Decimal = Field(..., description="Capital adequacy ratio")
    liquidity_coverage_ratio: Decimal = Field(..., description="Liquidity coverage ratio")
    overall_risk_rating: CBNRiskLevel = Field(..., description="Overall risk rating")
    
    # Consumer protection metrics
    complaints_received: int = Field(..., description="Consumer complaints received")
    complaints_resolved: int = Field(..., description="Consumer complaints resolved")
    average_resolution_time: float = Field(..., description="Average complaint resolution time (days)")
    customer_satisfaction_score: float = Field(..., ge=0, le=100, description="Customer satisfaction score")
    
    # Regulatory reporting metrics
    reports_submitted_on_time: int = Field(..., description="Reports submitted on time")
    total_reports_due: int = Field(..., description="Total reports due")
    reporting_compliance_rate: float = Field(..., ge=0, le=100, description="Reporting compliance rate")
    
    # Penalties and sanctions
    penalties_incurred: int = Field(..., description="Penalties incurred count")
    total_penalty_amount: Decimal = Field(default=0, description="Total penalty amount")
    regulatory_sanctions: List[str] = Field(default_factory=list, description="Regulatory sanctions")
    
    class Config:
        use_enum_values = True