"""
CAC Compliance Data Models
==========================
Pydantic models for CAC (Corporate Affairs Commission) compliance validation and corporate entity verification.
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field, validator
from enum import Enum

class EntityType(str, Enum):
    """Nigerian entity types registered with CAC"""
    PRIVATE_LIMITED_COMPANY = "private_limited_company"  # Ltd
    PUBLIC_LIMITED_COMPANY = "public_limited_company"    # Plc
    LIMITED_LIABILITY_PARTNERSHIP = "limited_liability_partnership"  # LLP
    BUSINESS_NAME = "business_name"  # BN
    INCORPORATED_TRUSTEES = "incorporated_trustees"  # IT (NGOs)
    UNLIMITED_LIABILITY_COMPANY = "unlimited_liability_company"
    COMPANY_LIMITED_BY_GUARANTEE = "company_limited_by_guarantee"
    FOREIGN_COMPANY = "foreign_company"

class EntityStatus(str, Enum):
    """CAC entity registration status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    STRUCK_OFF = "struck_off"
    DISSOLVED = "dissolved"
    IN_LIQUIDATION = "in_liquidation"
    UNDER_INVESTIGATION = "under_investigation"

class ComplianceStatus(str, Enum):
    """CAC compliance status levels"""
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PARTIALLY_COMPLIANT = "partially_compliant"
    FILING_OVERDUE = "filing_overdue"
    PENALTIES_OUTSTANDING = "penalties_outstanding"

class FilingType(str, Enum):
    """CAC filing types"""
    ANNUAL_RETURN = "annual_return"
    FINANCIAL_STATEMENTS = "financial_statements"
    CHANGE_OF_DIRECTORS = "change_of_directors"
    CHANGE_OF_ADDRESS = "change_of_address"
    CHANGE_OF_SHARE_CAPITAL = "change_of_share_capital"
    ALLOTMENT_OF_SHARES = "allotment_of_shares"
    TRANSFER_OF_SHARES = "transfer_of_shares"
    SPECIAL_RESOLUTION = "special_resolution"
    ORDINARY_RESOLUTION = "ordinary_resolution"

class DirectorType(str, Enum):
    """Director types in Nigerian companies"""
    EXECUTIVE_DIRECTOR = "executive_director"
    NON_EXECUTIVE_DIRECTOR = "non_executive_director"
    INDEPENDENT_DIRECTOR = "independent_director"
    CHAIRMAN = "chairman"
    MANAGING_DIRECTOR = "managing_director"
    COMPANY_SECRETARY = "company_secretary"

class ShareholderType(str, Enum):
    """Shareholder types"""
    INDIVIDUAL = "individual"
    CORPORATE = "corporate"
    FOREIGN_INDIVIDUAL = "foreign_individual"
    FOREIGN_CORPORATE = "foreign_corporate"
    GOVERNMENT = "government"

class RCValidationResult(BaseModel):
    """RC number validation result model"""
    rc_number: str = Field(..., description="Registration Certificate number")
    is_valid: bool = Field(..., description="RC number validity status")
    entity_name: Optional[str] = Field(None, description="Registered entity name")
    entity_type: Optional[EntityType] = Field(None, description="Entity type")
    registration_date: Optional[date] = Field(None, description="Registration date")
    registration_state: Optional[str] = Field(None, description="State of registration")
    entity_status: Optional[EntityStatus] = Field(None, description="Current entity status")
    validation_timestamp: datetime = Field(default_factory=datetime.now)
    error_message: Optional[str] = Field(None, description="Validation error details")

    @validator('rc_number')
    def validate_rc_format(cls, v):
        """Validate Nigerian RC number format"""
        if not v:
            raise ValueError("RC number is required")
        
        # Remove common prefixes
        clean_rc = v.upper().replace('RC', '').replace('-', '').strip()
        
        # RC numbers are typically 6-7 digits
        if not clean_rc.isdigit() or len(clean_rc) < 6 or len(clean_rc) > 7:
            raise ValueError("RC number must be 6-7 digits")
        
        return clean_rc

class BusinessNameValidation(BaseModel):
    """Business name validation and availability model"""
    proposed_name: str = Field(..., description="Proposed business name")
    is_available: bool = Field(..., description="Name availability status")
    is_valid_format: bool = Field(..., description="Name format validity")
    similarity_matches: List[str] = Field(default_factory=list, description="Similar existing names")
    reserved_words_violations: List[str] = Field(default_factory=list, description="Reserved words used")
    format_violations: List[str] = Field(default_factory=list, description="Format violations")
    suggestions: List[str] = Field(default_factory=list, description="Alternative name suggestions")
    validation_timestamp: datetime = Field(default_factory=datetime.now)

class DirectorInfo(BaseModel):
    """Nigerian company director information"""
    full_name: str = Field(..., description="Director full name")
    director_type: DirectorType = Field(..., description="Type of directorship")
    nationality: str = Field(..., description="Director nationality")
    date_of_birth: Optional[date] = Field(None, description="Date of birth")
    appointment_date: date = Field(..., description="Date of appointment")
    resignation_date: Optional[date] = Field(None, description="Date of resignation if applicable")
    residential_address: str = Field(..., description="Residential address")
    phone_number: Optional[str] = Field(None, description="Contact phone number")
    email: Optional[str] = Field(None, description="Contact email")
    bvn: Optional[str] = Field(None, description="Bank Verification Number")
    nin: Optional[str] = Field(None, description="National Identification Number")
    passport_number: Optional[str] = Field(None, description="Passport number for foreign directors")
    is_active: bool = Field(True, description="Active director status")

    @validator('nationality')
    def validate_nationality(cls, v):
        """Validate nationality format"""
        if not v or len(v.strip()) < 2:
            raise ValueError("Nationality must be specified")
        return v.strip().title()

    @validator('bvn')
    def validate_bvn(cls, v):
        """Validate BVN format for Nigerian directors"""
        if v and (not v.isdigit() or len(v) != 11):
            raise ValueError("BVN must be 11 digits")
        return v

    @validator('nin')
    def validate_nin(cls, v):
        """Validate NIN format"""
        if v and (not v.isdigit() or len(v) != 11):
            raise ValueError("NIN must be 11 digits")
        return v

class ShareholderInfo(BaseModel):
    """Shareholder information model"""
    name: str = Field(..., description="Shareholder name")
    shareholder_type: ShareholderType = Field(..., description="Type of shareholder")
    nationality: str = Field(..., description="Shareholder nationality")
    shares_held: int = Field(..., description="Number of shares held", ge=1)
    share_percentage: Decimal = Field(..., description="Percentage ownership", ge=0, le=100)
    share_class: str = Field("ordinary", description="Class of shares")
    acquisition_date: date = Field(..., description="Date of share acquisition")
    consideration_paid: Optional[Decimal] = Field(None, description="Amount paid for shares", ge=0)
    address: str = Field(..., description="Shareholder address")
    phone_number: Optional[str] = Field(None, description="Contact phone")
    email: Optional[str] = Field(None, description="Contact email")
    
    # For corporate shareholders
    corporate_rc_number: Optional[str] = Field(None, description="RC number if shareholder is a company")
    
    # For individual shareholders
    bvn: Optional[str] = Field(None, description="BVN for Nigerian individual shareholders")
    nin: Optional[str] = Field(None, description="NIN for identification")

class EntityRegistration(BaseModel):
    """Complete entity registration information"""
    rc_number: str = Field(..., description="Registration Certificate number")
    entity_name: str = Field(..., description="Official entity name")
    entity_type: EntityType = Field(..., description="Type of entity")
    registration_date: date = Field(..., description="Date of registration")
    registration_state: str = Field(..., description="State where registered")
    registered_address: str = Field(..., description="Registered office address")
    postal_address: Optional[str] = Field(None, description="Postal address")
    email: Optional[str] = Field(None, description="Official email address")
    phone_number: Optional[str] = Field(None, description="Official phone number")
    website: Optional[str] = Field(None, description="Company website")
    
    # Capital structure
    authorized_share_capital: Decimal = Field(..., description="Authorized share capital", ge=0)
    issued_share_capital: Decimal = Field(..., description="Issued share capital", ge=0)
    paid_up_share_capital: Decimal = Field(..., description="Paid up share capital", ge=0)
    
    # Key personnel
    directors: List[DirectorInfo] = Field(default_factory=list, description="List of directors")
    shareholders: List[ShareholderInfo] = Field(default_factory=list, description="List of shareholders")
    
    # Business information
    principal_business_activity: str = Field(..., description="Main business activity")
    business_commencement_date: Optional[date] = Field(None, description="Business commencement date")
    financial_year_end: str = Field("31-Dec", description="Financial year end date")
    
    # Status
    entity_status: EntityStatus = Field(EntityStatus.ACTIVE, description="Current entity status")
    status_change_date: Optional[date] = Field(None, description="Last status change date")
    status_change_reason: Optional[str] = Field(None, description="Reason for status change")

class CACFilingStatus(BaseModel):
    """CAC filing compliance status"""
    rc_number: str = Field(..., description="RC number")
    entity_name: str = Field(..., description="Entity name")
    filing_year: int = Field(..., description="Filing year")
    
    # Annual return status
    annual_return_filed: bool = Field(False, description="Annual return filing status")
    annual_return_due_date: Optional[date] = Field(None, description="Annual return due date")
    annual_return_filed_date: Optional[date] = Field(None, description="Date annual return was filed")
    annual_return_penalty: Optional[Decimal] = Field(None, description="Penalty for late filing", ge=0)
    
    # Financial statements status
    financial_statements_filed: bool = Field(False, description="Financial statements filing status")
    financial_statements_due_date: Optional[date] = Field(None, description="Financial statements due date")
    financial_statements_filed_date: Optional[date] = Field(None, description="Date financial statements filed")
    financial_statements_penalty: Optional[Decimal] = Field(None, description="Penalty for late filing", ge=0)
    
    # Other filings
    other_filings: List[Dict[str, Any]] = Field(default_factory=list, description="Other required filings")
    
    # Penalties and compliance
    total_penalties: Decimal = Field(Decimal('0'), description="Total outstanding penalties", ge=0)
    penalties_paid: Decimal = Field(Decimal('0'), description="Penalties paid", ge=0)
    outstanding_penalties: Decimal = Field(Decimal('0'), description="Outstanding penalties", ge=0)
    
    # Compliance status
    is_compliant: bool = Field(True, description="Overall compliance status")
    compliance_issues: List[str] = Field(default_factory=list, description="List of compliance issues")
    next_filing_due_date: Optional[date] = Field(None, description="Next filing due date")

class CACValidationResult(BaseModel):
    """Comprehensive CAC validation result"""
    rc_number: str = Field(..., description="RC number validated")
    is_compliant: bool = Field(..., description="Overall CAC compliance status")
    compliance_status: ComplianceStatus = Field(..., description="Detailed compliance status")
    validation_timestamp: datetime = Field(default_factory=datetime.now)
    
    # Registration validation
    rc_validation: RCValidationResult = Field(..., description="RC number validation results")
    entity_registration: Optional[EntityRegistration] = Field(None, description="Complete registration details")
    
    # Compliance checks
    filing_status: Optional[CACFilingStatus] = Field(None, description="Filing compliance status")
    
    # Validation details
    passed_checks: List[str] = Field(default_factory=list, description="Passed validation checks")
    failed_checks: List[str] = Field(default_factory=list, description="Failed validation checks")
    warnings: List[str] = Field(default_factory=list, description="Validation warnings")
    errors: List[str] = Field(default_factory=list, description="Validation errors")
    
    # Compliance metrics
    compliance_score: float = Field(0.0, description="Compliance score (0-100)", ge=0, le=100)
    filing_compliance_rate: float = Field(0.0, description="Filing compliance rate (%)", ge=0, le=100)
    
    # Recommendations
    recommendations: List[str] = Field(default_factory=list, description="Compliance recommendations")
    required_actions: List[str] = Field(default_factory=list, description="Required compliance actions")
    next_review_date: Optional[date] = Field(None, description="Next compliance review date")

class CACComplianceStatus(BaseModel):
    """Overall CAC compliance status for an entity"""
    rc_number: str = Field(..., description="RC number")
    entity_name: str = Field(..., description="Entity name")
    entity_type: EntityType = Field(..., description="Entity type")
    current_status: EntityStatus = Field(..., description="Current registration status")
    compliance_level: ComplianceStatus = Field(..., description="Compliance level")
    last_assessment_date: datetime = Field(..., description="Last compliance assessment")
    
    # Filing history
    total_required_filings: int = Field(0, description="Total required filings", ge=0)
    completed_filings: int = Field(0, description="Completed filings", ge=0)
    overdue_filings: int = Field(0, description="Overdue filings", ge=0)
    pending_filings: int = Field(0, description="Pending filings", ge=0)
    
    # Compliance metrics
    filing_completion_rate: float = Field(0.0, description="Filing completion rate (%)", ge=0, le=100)
    average_filing_delay: Optional[float] = Field(None, description="Average filing delay (days)")
    compliance_score: float = Field(0.0, description="Overall compliance score", ge=0, le=100)
    
    # Financial obligations
    total_fees_due: Decimal = Field(Decimal('0'), description="Total fees due", ge=0)
    penalties_outstanding: Decimal = Field(Decimal('0'), description="Outstanding penalties", ge=0)
    last_payment_date: Optional[date] = Field(None, description="Last payment date")
    
    # Risk assessment
    risk_level: str = Field("low", description="Compliance risk level")
    risk_factors: List[str] = Field(default_factory=list, description="Identified risk factors")
    
    # Action items
    immediate_actions: List[str] = Field(default_factory=list, description="Immediate required actions")
    upcoming_deadlines: List[Dict[str, Any]] = Field(default_factory=list, description="Upcoming compliance deadlines")
    recommendations: List[str] = Field(default_factory=list, description="Compliance recommendations")

class CACBusinessRule(BaseModel):
    """CAC business rule model"""
    rule_code: str = Field(..., description="Business rule code")
    rule_category: str = Field(..., description="Rule category")
    rule_description: str = Field(..., description="Rule description")
    entity_types: List[EntityType] = Field(..., description="Applicable entity types")
    validation_logic: str = Field(..., description="Validation logic description")
    error_message: str = Field(..., description="Error message template")
    is_mandatory: bool = Field(True, description="Mandatory rule flag")
    effective_date: date = Field(..., description="Rule effective date")
    expiry_date: Optional[date] = Field(None, description="Rule expiry date")

class CACStateOffice(BaseModel):
    """CAC state office information"""
    state_code: str = Field(..., description="State code")
    state_name: str = Field(..., description="State name")
    office_address: str = Field(..., description="Office address")
    phone_numbers: List[str] = Field(default_factory=list, description="Phone numbers")
    email: Optional[str] = Field(None, description="Office email")
    services_offered: List[str] = Field(default_factory=list, description="Services offered")
    operating_hours: str = Field("8:00 AM - 4:00 PM", description="Operating hours")

class CACSearchResult(BaseModel):
    """CAC entity search result"""
    search_query: str = Field(..., description="Search query used")
    search_type: str = Field(..., description="Type of search (name, rc_number, director)")
    total_results: int = Field(0, description="Total results found", ge=0)
    results: List[Dict[str, Any]] = Field(default_factory=list, description="Search results")
    search_timestamp: datetime = Field(default_factory=datetime.now)
    search_duration_ms: Optional[float] = Field(None, description="Search duration in milliseconds")

class CACAuditLog(BaseModel):
    """CAC compliance audit log"""
    log_id: str = Field(..., description="Unique log identifier")
    rc_number: str = Field(..., description="RC number")
    action_type: str = Field(..., description="Action type")
    action_description: str = Field(..., description="Action description")
    timestamp: datetime = Field(default_factory=datetime.now)
    user_id: Optional[str] = Field(None, description="User identifier")
    ip_address: Optional[str] = Field(None, description="IP address")
    result: str = Field(..., description="Action result")
    before_state: Optional[Dict[str, Any]] = Field(None, description="State before action")
    after_state: Optional[Dict[str, Any]] = Field(None, description="State after action")
    additional_data: Optional[Dict[str, Any]] = Field(None, description="Additional audit data")