"""
Compliance Orchestrator Data Models
==================================
Universal compliance data models for orchestrating all regulatory frameworks.
"""
from datetime import datetime, date
from decimal import Decimal
from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field, validator
from enum import Enum


class ComplianceFramework(str, Enum):
    """Supported compliance frameworks"""
    # International Standards
    UBL = "ubl"
    WCO_HS = "wco_hs"
    GDPR = "gdpr"
    NDPA = "ndpa"
    ISO_20022 = "iso_20022"
    ISO_27001 = "iso_27001"
    PEPPOL = "peppol"
    LEI = "lei"
    
    # Nigerian Regulators
    FIRS = "firs"
    NITDA = "nitda"
    CAC = "cac"
    
    # Combined/Cross-Framework
    EINVOICE_NIGERIA = "einvoice_nigeria"
    CROSS_BORDER = "cross_border"


class ComplianceStatus(str, Enum):
    """Compliance validation status"""
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PARTIALLY_COMPLIANT = "partially_compliant"
    PENDING = "pending"
    ERROR = "error"
    NOT_APPLICABLE = "not_applicable"


class ValidationSeverity(str, Enum):
    """Validation issue severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ComplianceRule(BaseModel):
    """Individual compliance rule definition"""
    rule_id: str = Field(..., description="Unique rule identifier")
    framework: ComplianceFramework = Field(..., description="Compliance framework")
    rule_name: str = Field(..., description="Human-readable rule name")
    rule_description: str = Field(..., description="Detailed rule description")
    rule_category: str = Field(..., description="Rule category")
    severity: ValidationSeverity = Field(..., description="Rule violation severity")
    
    # Rule logic
    validation_logic: str = Field(..., description="Validation logic description")
    validation_parameters: Dict[str, Any] = Field(default_factory=dict, description="Rule parameters")
    
    # Regulatory context
    regulatory_reference: str = Field(..., description="Regulatory reference/citation")
    applicable_jurisdictions: List[str] = Field(default_factory=list, description="Applicable jurisdictions")
    effective_date: date = Field(..., description="Rule effective date")
    expiry_date: Optional[date] = Field(None, description="Rule expiry date if applicable")
    
    # Business context
    business_impact: str = Field(..., description="Business impact description")
    remediation_guidance: str = Field(..., description="How to fix violations")
    
    @validator('rule_id')
    def validate_rule_id(cls, v):
        """Validate rule ID format"""
        if not v or len(v) < 3:
            raise ValueError('Rule ID must be at least 3 characters')
        return v.upper()


class ValidationResult(BaseModel):
    """Individual validation result"""
    rule_id: str = Field(..., description="Rule that was validated")
    framework: ComplianceFramework = Field(..., description="Framework being validated")
    status: ComplianceStatus = Field(..., description="Validation result status")
    severity: ValidationSeverity = Field(..., description="Issue severity if non-compliant")
    
    # Validation details
    validation_timestamp: datetime = Field(..., description="When validation was performed")
    validation_score: float = Field(..., ge=0, le=100, description="Validation score (0-100)")
    
    # Issue details
    issues_found: List[str] = Field(default_factory=list, description="Specific issues identified")
    recommendations: List[str] = Field(default_factory=list, description="Remediation recommendations")
    
    # Evidence and context
    validation_evidence: Dict[str, Any] = Field(default_factory=dict, description="Supporting evidence")
    business_context: Dict[str, Any] = Field(default_factory=dict, description="Business context")
    
    # Performance metrics
    validation_duration_ms: Optional[int] = Field(None, description="Validation duration in milliseconds")
    data_quality_score: Optional[float] = Field(None, description="Input data quality score")


class ComplianceResult(BaseModel):
    """Overall compliance result for a transaction/document"""
    compliance_id: str = Field(..., description="Unique compliance assessment identifier")
    assessment_timestamp: datetime = Field(..., description="When assessment was performed")
    document_id: str = Field(..., description="Document/transaction being assessed")
    document_type: str = Field(..., description="Type of document")
    
    # Overall compliance status
    overall_status: ComplianceStatus = Field(..., description="Overall compliance status")
    overall_score: float = Field(..., ge=0, le=100, description="Overall compliance score")
    
    # Framework-specific results
    framework_results: Dict[ComplianceFramework, ValidationResult] = Field(
        default_factory=dict, 
        description="Results by compliance framework"
    )
    
    # Issue summary
    critical_issues: int = Field(default=0, ge=0, description="Number of critical issues")
    high_issues: int = Field(default=0, ge=0, description="Number of high severity issues")
    medium_issues: int = Field(default=0, ge=0, description="Number of medium severity issues")
    low_issues: int = Field(default=0, ge=0, description="Number of low severity issues")
    
    # Recommendations and actions
    priority_actions: List[str] = Field(default_factory=list, description="Priority remediation actions")
    compliance_recommendations: List[str] = Field(default_factory=list, description="General compliance recommendations")
    
    # Business impact
    business_risk_level: str = Field(default="medium", description="Business risk level")
    regulatory_risk_level: str = Field(default="medium", description="Regulatory risk level")
    
    # Metadata
    assessed_frameworks: List[ComplianceFramework] = Field(default_factory=list, description="Frameworks assessed")
    assessment_context: Dict[str, Any] = Field(default_factory=dict, description="Assessment context")
    
    @validator('overall_score')
    def calculate_overall_score(cls, v, values):
        """Calculate overall score from framework results"""
        framework_results = values.get('framework_results', {})
        if not framework_results:
            return 0.0
        
        total_score = sum(result.validation_score for result in framework_results.values())
        return total_score / len(framework_results)


class OrchestrationContext(BaseModel):
    """Context for compliance orchestration"""
    context_id: str = Field(..., description="Unique context identifier")
    request_timestamp: datetime = Field(..., description="Request timestamp")
    
    # Document/transaction context
    document_data: Dict[str, Any] = Field(..., description="Document/transaction data")
    document_metadata: Dict[str, Any] = Field(default_factory=dict, description="Document metadata")
    
    # Business context
    sender_info: Dict[str, Any] = Field(default_factory=dict, description="Sender information")
    receiver_info: Dict[str, Any] = Field(default_factory=dict, description="Receiver information")
    transaction_context: Dict[str, Any] = Field(default_factory=dict, description="Transaction context")
    
    # Compliance requirements
    required_frameworks: List[ComplianceFramework] = Field(default_factory=list, description="Required compliance frameworks")
    optional_frameworks: List[ComplianceFramework] = Field(default_factory=list, description="Optional compliance frameworks")
    jurisdiction_requirements: Dict[str, List[str]] = Field(default_factory=dict, description="Jurisdiction-specific requirements")
    
    # Assessment parameters
    assessment_level: str = Field(default="standard", description="Assessment thoroughness level")
    include_recommendations: bool = Field(default=True, description="Include recommendations in results")
    parallel_validation: bool = Field(default=True, description="Enable parallel framework validation")
    
    # Performance settings
    max_validation_time_ms: int = Field(default=30000, description="Maximum validation time per framework")
    cache_results: bool = Field(default=True, description="Cache validation results")
    
    @validator('required_frameworks')
    def validate_required_frameworks(cls, v):
        """Ensure at least one framework is required"""
        if not v:
            raise ValueError('At least one compliance framework must be required')
        return v


class ComplianceMatrix(BaseModel):
    """Compliance matrix showing framework applicability"""
    matrix_id: str = Field(..., description="Matrix identifier")
    created_timestamp: datetime = Field(..., description="Matrix creation timestamp")
    
    # Applicability matrix
    document_type_frameworks: Dict[str, List[ComplianceFramework]] = Field(
        default_factory=dict,
        description="Required frameworks by document type"
    )
    jurisdiction_frameworks: Dict[str, List[ComplianceFramework]] = Field(
        default_factory=dict,
        description="Required frameworks by jurisdiction"
    )
    business_type_frameworks: Dict[str, List[ComplianceFramework]] = Field(
        default_factory=dict,
        description="Required frameworks by business type"
    )
    
    # Framework dependencies
    framework_dependencies: Dict[ComplianceFramework, List[ComplianceFramework]] = Field(
        default_factory=dict,
        description="Framework dependencies"
    )
    framework_conflicts: Dict[ComplianceFramework, List[ComplianceFramework]] = Field(
        default_factory=dict,
        description="Conflicting frameworks"
    )
    
    # Rules matrix
    framework_rules: Dict[ComplianceFramework, List[ComplianceRule]] = Field(
        default_factory=dict,
        description="Rules by framework"
    )
    
    # Performance data
    framework_weights: Dict[ComplianceFramework, float] = Field(
        default_factory=dict,
        description="Framework importance weights"
    )
    average_validation_times: Dict[ComplianceFramework, int] = Field(
        default_factory=dict,
        description="Average validation times by framework (ms)"
    )


class AuditEvent(BaseModel):
    """Compliance audit event"""
    event_id: str = Field(..., description="Unique event identifier")
    timestamp: datetime = Field(..., description="Event timestamp")
    event_type: str = Field(..., description="Type of compliance event")
    
    # Event context
    compliance_id: Optional[str] = Field(None, description="Related compliance assessment ID")
    document_id: Optional[str] = Field(None, description="Related document ID")
    framework: Optional[ComplianceFramework] = Field(None, description="Related framework")
    
    # Event details
    event_description: str = Field(..., description="Event description")
    event_category: str = Field(..., description="Event category")
    severity_level: ValidationSeverity = Field(default=ValidationSeverity.INFO, description="Event severity")
    
    # Context information
    source_system: str = Field(..., description="Source system generating event")
    user_context: Dict[str, Any] = Field(default_factory=dict, description="User context")
    technical_details: Dict[str, Any] = Field(default_factory=dict, description="Technical event details")
    
    # Impact assessment
    compliance_impact: Optional[str] = Field(None, description="Impact on compliance status")
    business_impact: Optional[str] = Field(None, description="Business impact description")
    
    # Remediation tracking
    remediation_required: bool = Field(default=False, description="Remediation required flag")
    remediation_steps: List[str] = Field(default_factory=list, description="Remediation steps")
    remediation_status: str = Field(default="not_required", description="Remediation status")


class ComplianceReport(BaseModel):
    """Comprehensive compliance report"""
    report_id: str = Field(..., description="Unique report identifier")
    report_timestamp: datetime = Field(..., description="Report generation timestamp")
    reporting_period_start: date = Field(..., description="Reporting period start")
    reporting_period_end: date = Field(..., description="Reporting period end")
    
    # Report scope
    frameworks_covered: List[ComplianceFramework] = Field(default_factory=list, description="Frameworks included in report")
    document_types_covered: List[str] = Field(default_factory=list, description="Document types covered")
    total_assessments: int = Field(default=0, ge=0, description="Total compliance assessments")
    
    # Compliance metrics
    overall_compliance_rate: float = Field(default=0.0, ge=0, le=100, description="Overall compliance rate")
    framework_compliance_rates: Dict[ComplianceFramework, float] = Field(
        default_factory=dict,
        description="Compliance rates by framework"
    )
    
    # Issue analysis
    issue_summary: Dict[ValidationSeverity, int] = Field(
        default_factory=dict,
        description="Issue counts by severity"
    )
    top_compliance_issues: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Most common compliance issues"
    )
    
    # Performance metrics
    average_assessment_time_ms: float = Field(default=0.0, ge=0, description="Average assessment time")
    framework_performance: Dict[ComplianceFramework, Dict[str, float]] = Field(
        default_factory=dict,
        description="Performance metrics by framework"
    )
    
    # Trends and insights
    compliance_trends: Dict[str, Any] = Field(default_factory=dict, description="Compliance trends over time")
    improvement_areas: List[str] = Field(default_factory=list, description="Areas for improvement")
    
    # Recommendations
    strategic_recommendations: List[str] = Field(default_factory=list, description="Strategic recommendations")
    operational_recommendations: List[str] = Field(default_factory=list, description="Operational recommendations")
    
    # Next steps
    action_items: List[str] = Field(default_factory=list, description="Recommended action items")
    next_review_date: date = Field(..., description="Next report review date")
    
    @validator('overall_compliance_rate')
    def calculate_overall_rate(cls, v, values):
        """Calculate overall compliance rate from framework rates"""
        framework_rates = values.get('framework_compliance_rates', {})
        if not framework_rates:
            return 0.0
        
        total_rate = sum(framework_rates.values())
        return total_rate / len(framework_rates)


class FrameworkIntegration(BaseModel):
    """Framework integration configuration"""
    framework: ComplianceFramework = Field(..., description="Framework identifier")
    integration_name: str = Field(..., description="Integration name")
    
    # Integration details
    validator_class: str = Field(..., description="Validator class name")
    validator_module: str = Field(..., description="Validator module path")
    
    # Configuration
    default_enabled: bool = Field(default=True, description="Enabled by default")
    validation_timeout_ms: int = Field(default=10000, description="Validation timeout")
    retry_attempts: int = Field(default=3, description="Retry attempts on failure")
    
    # Dependencies
    required_data_fields: List[str] = Field(default_factory=list, description="Required input data fields")
    dependent_frameworks: List[ComplianceFramework] = Field(default_factory=list, description="Dependent frameworks")
    
    # Performance settings
    cache_results: bool = Field(default=True, description="Cache validation results")
    parallel_execution: bool = Field(default=True, description="Allow parallel execution")
    priority_level: int = Field(default=5, ge=1, le=10, description="Execution priority (1-10)")
    
    @validator('priority_level')
    def validate_priority(cls, v):
        """Validate priority level"""
        if v < 1 or v > 10:
            raise ValueError('Priority level must be between 1 and 10')
        return v