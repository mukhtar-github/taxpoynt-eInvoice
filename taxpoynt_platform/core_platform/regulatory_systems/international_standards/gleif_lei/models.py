"""
Legal Entity Identifier (LEI) Data Models
========================================
Pydantic models for LEI validation, entity verification, and GLEIF integration
supporting international regulatory compliance and entity identification.
"""
from datetime import datetime, date
from decimal import Decimal
from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field, validator
from enum import Enum


class EntityStatus(str, Enum):
    """LEI entity registration status"""
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    PENDING_TRANSFER = "PENDING_TRANSFER"
    PENDING_ARCHIVAL = "PENDING_ARCHIVAL"
    RETIRED = "RETIRED"
    MERGED = "MERGED"
    DUPLICATE = "DUPLICATE"
    LAPSED = "LAPSED"


class RegistrationAuthority(str, Enum):
    """LEI registration authorities (LOU - Local Operating Units)"""
    GLEIF = "GLEIF"
    BLOOMBERG = "549300HRGOLQ8YH7TP18"  # Bloomberg Finance L.P.
    DTCC = "549300C4PPQIQL5H8S27"  # DTCC Data Repository
    BSE = "335800GEHXTAQ8EKTH50"  # BSE (India)
    SIX = "549300PH53BKF9LDBR86"  # SIX Financial Information
    LONDON_STOCK_EXCHANGE = "213800WAVVP3ZEGDMX44"  # London Stock Exchange
    # Nigerian entities would typically use international LOUs until Nigeria has its own


class LEIValidationStatus(str, Enum):
    """LEI validation result status"""
    VALID = "valid"
    INVALID = "invalid"
    EXPIRED = "expired"
    PENDING = "pending"
    NOT_FOUND = "not_found"
    ERROR = "error"


class RelationshipType(str, Enum):
    """Types of entity relationships"""
    DIRECT_ACCOUNTING_CONSOLIDATION_PARENT = "IS_DIRECTLY_CONSOLIDATED_BY"
    ULTIMATE_ACCOUNTING_CONSOLIDATION_PARENT = "IS_ULTIMATELY_CONSOLIDATED_BY"
    DIRECT_ACCOUNTING_CONSOLIDATION_CHILD = "DIRECTLY_CONSOLIDATES"
    ULTIMATE_ACCOUNTING_CONSOLIDATION_CHILD = "ULTIMATELY_CONSOLIDATES"
    IS_FUND_MANAGED_BY = "IS_FUND_MANAGED_BY"
    IS_FEEDER_TO = "IS_FEEDER_TO"
    IS_MASTER_TO = "IS_MASTER_TO"
    IS_SUBFUND_OF = "IS_SUBFUND_OF"


class LEIRecord(BaseModel):
    """Complete LEI record with entity information"""
    lei: str = Field(..., min_length=20, max_length=20, description="20-character LEI code")
    legal_name: str = Field(..., description="Official legal name of entity")
    status: EntityStatus = Field(..., description="Current LEI status")
    initial_registration_date: date = Field(..., description="LEI initial registration date")
    last_update_date: date = Field(..., description="Last update to LEI record")
    renewal_date: date = Field(..., description="Next renewal date")
    managing_lou: str = Field(..., description="Managing Local Operating Unit")
    
    # Legal address
    legal_address: Dict[str, str] = Field(..., description="Legal address of entity")
    headquarters_address: Optional[Dict[str, str]] = Field(None, description="Headquarters address if different")
    
    # Business registry information
    business_registry_entity_id: Optional[str] = Field(None, description="Business registry identifier")
    legal_jurisdiction: str = Field(..., description="Legal jurisdiction code")
    entity_category: str = Field(..., description="Entity category classification")
    legal_form: str = Field(..., description="Legal form of entity")
    
    # Associated entity information
    associated_entity_name: Optional[str] = Field(None, description="Associated entity name")
    associated_lei: Optional[str] = Field(None, description="Associated entity LEI")
    
    # Validation information
    validation_sources: List[str] = Field(default_factory=list, description="Sources used for validation")
    validation_authorities: List[str] = Field(default_factory=list, description="Authorities that validated")
    
    # Metadata
    registration_authority: RegistrationAuthority = Field(..., description="Registration authority")
    conformity_flag: str = Field(default="", description="Exception reasons if non-conformant")
    
    @validator('lei')
    def validate_lei_format(cls, v):
        """Validate LEI format and check digit"""
        if len(v) != 20:
            raise ValueError('LEI must be exactly 20 characters')
        
        if not v.isalnum():
            raise ValueError('LEI must contain only alphanumeric characters')
        
        # LEI check digit validation (ISO 17442)
        # Move first 4 characters to end
        rearranged = v[4:] + v[:4]
        
        # Replace letters with numbers (A=10, B=11, ..., Z=35)
        numeric_string = ""
        for char in rearranged:
            if char.isalpha():
                numeric_string += str(ord(char.upper()) - ord('A') + 10)
            else:
                numeric_string += char
        
        # Calculate mod 97
        remainder = int(numeric_string) % 97
        
        if remainder != 1:
            raise ValueError('LEI check digit validation failed')
        
        return v.upper()
    
    @validator('legal_jurisdiction')
    def validate_jurisdiction(cls, v):
        """Validate legal jurisdiction format (ISO 3166-1 alpha-2)"""
        if len(v) != 2:
            raise ValueError('Legal jurisdiction must be 2-character ISO country code')
        return v.upper()


class LEIValidationResult(BaseModel):
    """LEI validation result with detailed information"""
    lei: str = Field(..., description="LEI being validated")
    validation_timestamp: datetime = Field(..., description="Validation timestamp")
    validation_status: LEIValidationStatus = Field(..., description="Validation result status")
    validation_score: float = Field(..., ge=0, le=100, description="Validation confidence score")
    
    # Validation details
    format_validation: Dict[str, Any] = Field(default_factory=dict, description="LEI format validation results")
    registry_validation: Dict[str, Any] = Field(default_factory=dict, description="Registry lookup validation")
    status_validation: Dict[str, Any] = Field(default_factory=dict, description="LEI status validation")
    
    # Entity information (if found)
    entity_record: Optional[LEIRecord] = Field(None, description="Complete LEI record if found")
    
    # Validation issues
    validation_errors: List[str] = Field(default_factory=list, description="Validation errors found")
    validation_warnings: List[str] = Field(default_factory=list, description="Validation warnings")
    
    # Recommendations
    recommendations: List[str] = Field(default_factory=list, description="Recommendations for improvement")
    next_validation_date: Optional[datetime] = Field(None, description="Recommended next validation date")
    
    @validator('validation_score')
    def calculate_validation_score(cls, v, values):
        """Calculate validation score based on validation results"""
        if values.get('validation_status') == LEIValidationStatus.VALID:
            return 100.0
        elif values.get('validation_status') == LEIValidationStatus.EXPIRED:
            return 70.0
        elif values.get('validation_status') == LEIValidationStatus.INVALID:
            return 0.0
        else:
            return 50.0  # Default for pending/not_found


class LEIRelationship(BaseModel):
    """LEI entity relationship information"""
    relationship_id: str = Field(..., description="Unique relationship identifier")
    parent_lei: str = Field(..., min_length=20, max_length=20, description="Parent entity LEI")
    child_lei: str = Field(..., min_length=20, max_length=20, description="Child entity LEI")
    relationship_type: RelationshipType = Field(..., description="Type of relationship")
    relationship_status: str = Field(..., description="Status of relationship")
    
    # Relationship details
    relationship_periods: List[Dict[str, Any]] = Field(default_factory=list, description="Relationship validity periods")
    relationship_qualifiers: List[str] = Field(default_factory=list, description="Relationship qualifiers")
    
    # Quantitative information
    accounting_standard: Optional[str] = Field(None, description="Accounting standard used")
    measurement_method: Optional[str] = Field(None, description="Measurement method")
    
    # Validation information
    validation_sources: List[str] = Field(default_factory=list, description="Relationship validation sources")
    last_update_date: date = Field(..., description="Last relationship update")


class NigerianEntityMapping(BaseModel):
    """Mapping between LEI and Nigerian entity identifiers"""
    lei: str = Field(..., min_length=20, max_length=20, description="Entity LEI")
    entity_name: str = Field(..., description="Entity legal name")
    
    # Nigerian identifiers
    tin_number: Optional[str] = Field(None, description="Nigerian Tax Identification Number")
    cac_registration_number: Optional[str] = Field(None, description="CAC registration number")
    vat_registration_number: Optional[str] = Field(None, description="VAT registration number")
    
    # Business information
    business_classification: str = Field(..., description="Nigerian business classification")
    incorporation_date: Optional[date] = Field(None, description="Date of incorporation in Nigeria")
    registered_address: Dict[str, str] = Field(..., description="Nigerian registered address")
    
    # Regulatory information
    regulatory_licenses: List[str] = Field(default_factory=list, description="Nigerian regulatory licenses")
    regulatory_status: str = Field(default="active", description="Regulatory status in Nigeria")
    
    # Mapping metadata
    mapping_date: datetime = Field(..., description="Date LEI-Nigerian ID mapping was established")
    mapping_source: str = Field(..., description="Source of mapping information")
    mapping_confidence: float = Field(..., ge=0, le=100, description="Confidence in mapping accuracy")
    
    @validator('tin_number')
    def validate_nigerian_tin(cls, v):
        """Validate Nigerian TIN format"""
        if v and (not v.isdigit() or len(v) not in [10, 11]):
            raise ValueError('Nigerian TIN must be 10-11 digits')
        return v
    
    @validator('cac_registration_number')
    def validate_cac_number(cls, v):
        """Validate CAC registration number format"""
        if v and not v.strip():
            raise ValueError('CAC registration number cannot be empty')
        return v


class LEIComplianceReport(BaseModel):
    """LEI compliance status report"""
    report_id: str = Field(..., description="Unique report identifier")
    generated_timestamp: datetime = Field(..., description="Report generation timestamp")
    reporting_period_start: date = Field(..., description="Reporting period start")
    reporting_period_end: date = Field(..., description="Reporting period end")
    
    # Entity coverage
    total_entities_analyzed: int = Field(default=0, ge=0, description="Total entities analyzed")
    entities_with_lei: int = Field(default=0, ge=0, description="Entities with valid LEI")
    entities_without_lei: int = Field(default=0, ge=0, description="Entities without LEI")
    lei_coverage_percentage: float = Field(default=0.0, ge=0, le=100, description="LEI coverage percentage")
    
    # Validation results summary
    valid_leis: int = Field(default=0, ge=0, description="Number of valid LEIs")
    expired_leis: int = Field(default=0, ge=0, description="Number of expired LEIs")
    invalid_leis: int = Field(default=0, ge=0, description="Number of invalid LEIs")
    
    # Compliance by category
    compliance_by_entity_type: Dict[str, Dict[str, int]] = Field(
        default_factory=dict, 
        description="LEI compliance by entity type"
    )
    compliance_by_jurisdiction: Dict[str, Dict[str, int]] = Field(
        default_factory=dict,
        description="LEI compliance by jurisdiction"
    )
    
    # Nigerian-specific compliance
    nigerian_entities_compliance: Dict[str, Any] = Field(
        default_factory=dict,
        description="LEI compliance for Nigerian entities"
    )
    
    # Issues and recommendations
    common_issues: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Most common LEI compliance issues"
    )
    improvement_recommendations: List[str] = Field(
        default_factory=list,
        description="Recommendations for improving LEI compliance"
    )
    
    # Action items
    entities_requiring_lei_registration: List[str] = Field(
        default_factory=list,
        description="Entities that need LEI registration"
    )
    leis_requiring_renewal: List[str] = Field(
        default_factory=list,
        description="LEIs requiring renewal"
    )
    
    # Next steps
    next_review_date: date = Field(..., description="Next compliance review date")
    priority_actions: List[str] = Field(default_factory=list, description="Priority compliance actions")
    
    @validator('lei_coverage_percentage')
    def calculate_lei_coverage(cls, v, values):
        """Calculate LEI coverage percentage"""
        total = values.get('total_entities_analyzed', 0)
        with_lei = values.get('entities_with_lei', 0)
        if total == 0:
            return 0.0
        return (with_lei / total) * 100


class GLEIFApiResponse(BaseModel):
    """GLEIF API response structure"""
    request_timestamp: datetime = Field(..., description="API request timestamp")
    response_status: str = Field(..., description="API response status")
    total_records: int = Field(default=0, ge=0, description="Total records returned")
    
    # LEI records
    lei_records: List[LEIRecord] = Field(default_factory=list, description="LEI records returned")
    
    # Relationship records
    relationship_records: List[LEIRelationship] = Field(default_factory=list, description="Relationship records")
    
    # API metadata
    api_version: str = Field(default="v1", description="GLEIF API version used")
    query_parameters: Dict[str, Any] = Field(default_factory=dict, description="Query parameters used")
    rate_limit_info: Dict[str, Any] = Field(default_factory=dict, description="API rate limit information")
    
    # Error information
    errors: List[str] = Field(default_factory=list, description="API errors encountered")
    warnings: List[str] = Field(default_factory=list, description="API warnings")


class LEIRegistrationRequest(BaseModel):
    """LEI registration request for new entities"""
    request_id: str = Field(..., description="Unique registration request identifier")
    request_timestamp: datetime = Field(..., description="Registration request timestamp")
    requesting_organization: str = Field(..., description="Organization requesting LEI")
    
    # Entity information
    legal_name: str = Field(..., description="Legal name of entity requiring LEI")
    legal_address: Dict[str, str] = Field(..., description="Legal address of entity")
    headquarters_address: Optional[Dict[str, str]] = Field(None, description="Headquarters address")
    legal_jurisdiction: str = Field(..., description="Legal jurisdiction")
    legal_form: str = Field(..., description="Legal form")
    entity_category: str = Field(..., description="Entity category")
    
    # Business registry information
    business_registry_entity_id: Optional[str] = Field(None, description="Business registry ID")
    incorporation_date: Optional[date] = Field(None, description="Date of incorporation")
    
    # Nigerian-specific information
    nigerian_identifiers: Optional[NigerianEntityMapping] = Field(None, description="Nigerian entity identifiers")
    
    # Registration details
    preferred_managing_lou: Optional[str] = Field(None, description="Preferred managing LOU")
    registration_reason: str = Field(..., description="Reason for LEI registration")
    intended_use: List[str] = Field(default_factory=list, description="Intended use cases for LEI")
    
    # Contact information
    contact_person: Dict[str, str] = Field(..., description="Contact person information")
    
    # Status tracking
    request_status: str = Field(default="submitted", description="Registration request status")
    estimated_completion_date: Optional[date] = Field(None, description="Estimated completion date")
    
    @validator('legal_jurisdiction')
    def validate_jurisdiction_format(cls, v):
        """Validate jurisdiction format"""
        if len(v) != 2:
            raise ValueError('Legal jurisdiction must be 2-character ISO country code')
        return v.upper()


class LEIAuditEvent(BaseModel):
    """LEI system audit event"""
    event_id: str = Field(..., description="Unique event identifier")
    timestamp: datetime = Field(..., description="Event timestamp")
    event_type: str = Field(..., description="Type of LEI event")
    lei: Optional[str] = Field(None, description="LEI involved in event")
    
    # Event details
    event_description: str = Field(..., description="Event description")
    event_category: str = Field(..., description="Event category")
    severity_level: str = Field(default="info", description="Event severity")
    
    # Context information
    source_system: str = Field(..., description="Source system generating event")
    user_context: Dict[str, Any] = Field(default_factory=dict, description="User context")
    api_context: Dict[str, Any] = Field(default_factory=dict, description="API context if applicable")
    
    # Compliance tracking
    compliance_impact: Optional[str] = Field(None, description="Impact on compliance status")
    remediation_required: bool = Field(default=False, description="Remediation required flag")
    remediation_steps: List[str] = Field(default_factory=list, description="Remediation steps")
    
    # Performance metrics
    response_time_ms: Optional[int] = Field(None, description="Response time in milliseconds")
    data_quality_score: Optional[float] = Field(None, description="Data quality score")


class LEIPerformanceMetrics(BaseModel):
    """LEI system performance metrics"""
    metrics_date: date = Field(..., description="Metrics reporting date")
    reporting_period: str = Field(..., description="Reporting period (daily/weekly/monthly)")
    
    # Validation metrics
    total_validations: int = Field(default=0, ge=0, description="Total LEI validations performed")
    successful_validations: int = Field(default=0, ge=0, description="Successful validations")
    failed_validations: int = Field(default=0, ge=0, description="Failed validations")
    validation_success_rate: float = Field(default=0.0, ge=0, le=100, description="Validation success rate")
    
    # Performance metrics
    average_response_time_ms: float = Field(default=0.0, ge=0, description="Average response time")
    p95_response_time_ms: float = Field(default=0.0, ge=0, description="95th percentile response time")
    api_uptime_percentage: float = Field(default=0.0, ge=0, le=100, description="API uptime percentage")
    
    # Data quality metrics
    data_completeness_score: float = Field(default=0.0, ge=0, le=100, description="Data completeness score")
    data_accuracy_score: float = Field(default=0.0, ge=0, le=100, description="Data accuracy score")
    
    # Error metrics
    error_count_by_type: Dict[str, int] = Field(default_factory=dict, description="Error counts by type")
    most_common_errors: List[str] = Field(default_factory=list, description="Most common error types")
    
    # Usage metrics
    unique_users: int = Field(default=0, ge=0, description="Unique users in period")
    api_calls: int = Field(default=0, ge=0, description="Total API calls")
    cache_hit_rate: float = Field(default=0.0, ge=0, le=100, description="Cache hit rate percentage")
    
    @validator('validation_success_rate')
    def calculate_success_rate(cls, v, values):
        """Calculate validation success rate"""
        total = values.get('total_validations', 0)
        successful = values.get('successful_validations', 0)
        if total == 0:
            return 0.0
        return (successful / total) * 100