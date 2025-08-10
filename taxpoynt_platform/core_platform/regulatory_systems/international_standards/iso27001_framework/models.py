"""
ISO 27001 Data Models
=====================
Pydantic models for ISO 27001 information security management system compliance.
"""
from datetime import datetime, date
from decimal import Decimal
from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field, validator
from enum import Enum


class ISO27001ComplianceError(Exception):
    """Raised when ISO 27001 compliance validation fails."""
    pass


class ControlStatus(str, Enum):
    """ISO 27001 control implementation status."""
    COMPLIANT = "compliant"                     # Fully implemented and effective
    PARTIALLY_COMPLIANT = "partially_compliant" # Partially implemented
    NON_COMPLIANT = "non_compliant"             # Not implemented or ineffective
    NOT_APPLICABLE = "not_applicable"           # Not applicable to organization
    UNDER_REVIEW = "under_review"               # Currently being assessed
    PLANNED = "planned"                         # Implementation planned


class RiskLevel(str, Enum):
    """Information security risk levels."""
    CRITICAL = "critical"    # Immediate action required
    HIGH = "high"           # High priority remediation
    MEDIUM = "medium"       # Medium priority remediation
    LOW = "low"            # Low priority, monitor
    NEGLIGIBLE = "negligible"  # Acceptable risk level


class ThreatType(str, Enum):
    """Types of information security threats."""
    MALWARE = "malware"                   # Malicious software
    PHISHING = "phishing"                 # Social engineering attacks
    DATA_BREACH = "data_breach"           # Unauthorized data access
    INSIDER_THREAT = "insider_threat"     # Internal malicious activity
    DDOS = "ddos"                        # Distributed denial of service
    PHYSICAL_THEFT = "physical_theft"     # Physical asset theft
    NATURAL_DISASTER = "natural_disaster" # Environmental threats
    SYSTEM_FAILURE = "system_failure"     # Technical failures
    SUPPLIER_RISK = "supplier_risk"       # Third-party risks
    REGULATORY_CHANGE = "regulatory_change" # Compliance risks


class ControlDomain(str, Enum):
    """ISO 27001 control domains (Annex A)."""
    A05_POLICIES = "A05"           # Information Security Policies
    A06_ORGANIZATION = "A06"       # Organization of Information Security
    A07_HUMAN_RESOURCES = "A07"    # Human Resource Security
    A08_ASSET_MANAGEMENT = "A08"   # Asset Management
    A09_ACCESS_CONTROL = "A09"     # Access Control
    A10_CRYPTOGRAPHY = "A10"       # Cryptography
    A11_PHYSICAL_SECURITY = "A11"  # Physical and Environmental Security
    A12_OPERATIONS = "A12"         # Operations Security
    A13_COMMUNICATIONS = "A13"     # Communications Security
    A14_DEVELOPMENT = "A14"        # System Acquisition, Development and Maintenance
    A15_SUPPLIER = "A15"           # Supplier Relationships
    A16_INCIDENTS = "A16"          # Information Security Incident Management
    A17_CONTINUITY = "A17"         # Business Continuity Management
    A18_COMPLIANCE = "A18"         # Compliance


class AuditType(str, Enum):
    """Types of security audits."""
    INTERNAL = "internal"           # Internal audit
    EXTERNAL = "external"           # External/third-party audit
    CERTIFICATION = "certification" # Certification body audit
    SURVEILLANCE = "surveillance"   # Surveillance audit
    SELF_ASSESSMENT = "self_assessment" # Self-assessment


class IncidentSeverity(str, Enum):
    """Security incident severity levels."""
    CRITICAL = "critical"    # Business-critical impact
    HIGH = "high"           # Significant impact
    MEDIUM = "medium"       # Moderate impact
    LOW = "low"            # Minor impact
    INFORMATIONAL = "informational" # No impact


class ISO27001Control(BaseModel):
    """ISO 27001 security control definition."""
    # Control identification
    control_id: str = Field(..., description="ISO 27001 control identifier (e.g., A.5.1.1)")
    control_name: str = Field(..., description="Control name")
    domain: ControlDomain = Field(..., description="Control domain")
    
    # Control details
    objective: str = Field(..., description="Control objective")
    description: str = Field(..., description="Control description")
    implementation_guidance: Optional[str] = Field(None, description="Implementation guidance")
    
    # Assessment results
    status: ControlStatus = Field(ControlStatus.UNDER_REVIEW, description="Current implementation status")
    maturity_level: int = Field(1, ge=1, le=5, description="Maturity level (1-5)")
    effectiveness_score: float = Field(0.0, ge=0.0, le=100.0, description="Effectiveness percentage")
    
    # Risk and compliance
    risk_level: RiskLevel = Field(RiskLevel.MEDIUM, description="Associated risk level")
    compliance_percentage: float = Field(0.0, ge=0.0, le=100.0, description="Compliance percentage")
    
    # Implementation details
    responsible_party: Optional[str] = Field(None, description="Responsible person/team")
    implementation_date: Optional[date] = Field(None, description="Implementation date")
    last_review_date: Optional[date] = Field(None, description="Last review date")
    next_review_date: Optional[date] = Field(None, description="Next scheduled review")
    
    # Evidence and documentation
    evidence_documents: List[str] = Field(default_factory=list, description="Supporting evidence")
    implementation_notes: Optional[str] = Field(None, description="Implementation notes")
    
    # Nigerian context
    nitda_applicable: bool = Field(False, description="Applicable to NITDA guidelines")
    cbn_applicable: bool = Field(False, description="Applicable to CBN requirements")
    
    @validator('control_id')
    def validate_control_id(cls, v):
        """Validate ISO 27001 control ID format."""
        # Format: A.X.Y.Z where X is domain, Y is category, Z is control
        import re
        if not re.match(r'^A\.\d{1,2}\.\d{1,2}\.\d{1,2}$', v):
            raise ValueError("Control ID must be in format A.X.Y.Z")
        return v


class SecurityRisk(BaseModel):
    """Information security risk assessment."""
    # Risk identification
    risk_id: str = Field(..., description="Unique risk identifier")
    risk_name: str = Field(..., description="Risk name")
    description: str = Field(..., description="Risk description")
    
    # Risk classification
    threat_type: ThreatType = Field(..., description="Type of threat")
    affected_assets: List[str] = Field(..., description="Affected information assets")
    vulnerabilities: List[str] = Field(..., description="Identified vulnerabilities")
    
    # Risk assessment
    likelihood: int = Field(..., ge=1, le=5, description="Likelihood score (1-5)")
    impact: int = Field(..., ge=1, le=5, description="Impact score (1-5)")
    risk_score: float = Field(..., description="Calculated risk score")
    risk_level: RiskLevel = Field(..., description="Risk level classification")
    
    # Risk treatment
    treatment_strategy: str = Field(..., description="Risk treatment approach")
    mitigation_controls: List[str] = Field(default_factory=list, description="Mitigation controls")
    residual_risk_score: Optional[float] = Field(None, description="Residual risk after treatment")
    
    # Management
    risk_owner: str = Field(..., description="Risk owner")
    assessment_date: date = Field(..., description="Risk assessment date")
    review_date: Optional[date] = Field(None, description="Next review date")
    
    # Status tracking
    treatment_status: str = Field("identified", description="Treatment status")
    closure_date: Optional[date] = Field(None, description="Risk closure date")
    
    @validator('risk_score')
    def calculate_risk_score(cls, v, values):
        """Calculate risk score from likelihood and impact."""
        if 'likelihood' in values and 'impact' in values:
            calculated_score = values['likelihood'] * values['impact']
            if v != calculated_score:
                return calculated_score
        return v


class SecurityIncident(BaseModel):
    """Information security incident record."""
    # Incident identification
    incident_id: str = Field(..., description="Unique incident identifier")
    title: str = Field(..., description="Incident title")
    description: str = Field(..., description="Incident description")
    
    # Incident classification
    severity: IncidentSeverity = Field(..., description="Incident severity")
    category: ThreatType = Field(..., description="Incident category")
    affected_systems: List[str] = Field(default_factory=list, description="Affected systems")
    
    # Timeline
    detected_date: datetime = Field(..., description="Detection timestamp")
    reported_date: Optional[datetime] = Field(None, description="Reporting timestamp")
    resolved_date: Optional[datetime] = Field(None, description="Resolution timestamp")
    
    # Impact assessment
    data_compromised: bool = Field(False, description="Whether data was compromised")
    estimated_records_affected: Optional[int] = Field(None, description="Number of records affected")
    financial_impact: Optional[Decimal] = Field(None, description="Estimated financial impact")
    
    # Response details
    response_team: List[str] = Field(default_factory=list, description="Incident response team")
    containment_actions: List[str] = Field(default_factory=list, description="Containment actions taken")
    recovery_actions: List[str] = Field(default_factory=list, description="Recovery actions taken")
    
    # Root cause and lessons learned
    root_cause: Optional[str] = Field(None, description="Root cause analysis")
    lessons_learned: Optional[str] = Field(None, description="Lessons learned")
    preventive_measures: List[str] = Field(default_factory=list, description="Preventive measures")
    
    # Compliance and reporting
    regulatory_reporting_required: bool = Field(False, description="Regulatory reporting required")
    customer_notification_required: bool = Field(False, description="Customer notification required")
    
    # Nigerian context
    nitda_reported: bool = Field(False, description="Reported to NITDA")
    cbn_reported: bool = Field(False, description="Reported to CBN if applicable")


class AuditFinding(BaseModel):
    """Security audit finding."""
    # Finding identification
    finding_id: str = Field(..., description="Unique finding identifier")
    audit_id: str = Field(..., description="Parent audit identifier")
    
    # Finding details
    title: str = Field(..., description="Finding title")
    description: str = Field(..., description="Finding description")
    evidence: List[str] = Field(default_factory=list, description="Supporting evidence")
    
    # Classification
    severity: RiskLevel = Field(..., description="Finding severity")
    finding_type: str = Field(..., description="Type of finding")
    affected_controls: List[str] = Field(default_factory=list, description="Affected ISO 27001 controls")
    
    # Recommendations
    recommendation: str = Field(..., description="Recommended action")
    priority: int = Field(..., ge=1, le=5, description="Remediation priority (1-5)")
    estimated_effort: Optional[str] = Field(None, description="Estimated remediation effort")
    
    # Status tracking
    status: str = Field("open", description="Finding status")
    assigned_to: Optional[str] = Field(None, description="Assigned remediation owner")
    due_date: Optional[date] = Field(None, description="Remediation due date")
    closure_date: Optional[date] = Field(None, description="Finding closure date")
    
    # Audit context
    auditor: str = Field(..., description="Auditor name")
    audit_date: date = Field(..., description="Audit date")
    audit_type: AuditType = Field(..., description="Type of audit")


class ComplianceResult(BaseModel):
    """ISO 27001 compliance assessment result."""
    # Assessment overview
    assessment_id: str = Field(..., description="Assessment identifier")
    assessment_date: datetime = Field(default_factory=datetime.now, description="Assessment date")
    assessor: str = Field(..., description="Assessor name/organization")
    
    # Compliance metrics
    overall_compliance_percentage: float = Field(..., ge=0.0, le=100.0, description="Overall compliance %")
    compliant_controls: int = Field(..., ge=0, description="Number of compliant controls")
    total_controls: int = Field(..., ge=0, description="Total number of applicable controls")
    
    # Domain-specific compliance
    domain_compliance: Dict[str, float] = Field(default_factory=dict, description="Compliance by domain")
    
    # Risk assessment
    overall_risk_level: RiskLevel = Field(..., description="Overall organizational risk level")
    critical_risks: int = Field(0, description="Number of critical risks")
    high_risks: int = Field(0, description="Number of high risks")
    
    # Findings summary
    total_findings: int = Field(0, description="Total audit findings")
    critical_findings: int = Field(0, description="Critical findings")
    high_findings: int = Field(0, description="High priority findings")
    
    # Certification status
    certification_ready: bool = Field(False, description="Ready for certification audit")
    certification_date: Optional[date] = Field(None, description="Certification date")
    certificate_expiry: Optional[date] = Field(None, description="Certificate expiry date")
    
    # Improvement areas
    improvement_areas: List[str] = Field(default_factory=list, description="Key improvement areas")
    recommendations: List[str] = Field(default_factory=list, description="Compliance recommendations")
    
    # Nigerian compliance context
    nitda_compliance: Optional[float] = Field(None, description="NITDA guidelines compliance %")
    cbn_compliance: Optional[float] = Field(None, description="CBN requirements compliance %")
    
    # Maturity assessment
    maturity_level: float = Field(1.0, ge=1.0, le=5.0, description="Overall security maturity level")
    maturity_by_domain: Dict[str, float] = Field(default_factory=dict, description="Maturity by domain")
    
    def add_recommendation(self, recommendation: str):
        """Add compliance recommendation."""
        if recommendation not in self.recommendations:
            self.recommendations.append(recommendation)
    
    def calculate_risk_distribution(self) -> Dict[str, int]:
        """Calculate risk level distribution."""
        return {
            'critical': self.critical_risks,
            'high': self.high_risks,
            'medium': 0,  # Would be calculated from actual risks
            'low': 0,     # Would be calculated from actual risks
            'negligible': 0  # Would be calculated from actual risks
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            'assessment_id': self.assessment_id,
            'assessment_date': self.assessment_date.isoformat(),
            'overall_compliance_percentage': self.overall_compliance_percentage,
            'compliant_controls': self.compliant_controls,
            'total_controls': self.total_controls,
            'overall_risk_level': self.overall_risk_level.value,
            'certification_ready': self.certification_ready,
            'maturity_level': self.maturity_level,
            'total_findings': self.total_findings,
            'critical_findings': self.critical_findings,
            'domain_compliance': self.domain_compliance,
            'nitda_compliance': self.nitda_compliance,
            'cbn_compliance': self.cbn_compliance
        }


class ISMSScope(BaseModel):
    """Information Security Management System scope definition."""
    # Scope identification
    scope_id: str = Field(..., description="ISMS scope identifier")
    organization_name: str = Field(..., description="Organization name")
    
    # Scope boundaries
    business_units: List[str] = Field(..., description="Included business units")
    geographical_locations: List[str] = Field(..., description="Geographical scope")
    information_systems: List[str] = Field(..., description="Information systems in scope")
    
    # Assets and processes
    information_assets: List[str] = Field(..., description="Information assets in scope")
    business_processes: List[str] = Field(..., description="Business processes in scope")
    
    # Exclusions
    exclusions: List[str] = Field(default_factory=list, description="Explicitly excluded items")
    exclusion_justifications: Dict[str, str] = Field(default_factory=dict, description="Exclusion justifications")
    
    # Regulatory context
    applicable_regulations: List[str] = Field(default_factory=list, description="Applicable regulations")
    compliance_requirements: List[str] = Field(default_factory=list, description="Compliance requirements")
    
    # Nigerian context
    nigerian_operations: bool = Field(False, description="Includes Nigerian operations")
    nitda_guidelines_applicable: bool = Field(False, description="NITDA guidelines apply")
    cbn_requirements_applicable: bool = Field(False, description="CBN requirements apply")
    
    # Scope management
    approved_by: str = Field(..., description="Scope approval authority")
    approval_date: date = Field(..., description="Scope approval date")
    last_review_date: Optional[date] = Field(None, description="Last scope review")
    next_review_date: Optional[date] = Field(None, description="Next scope review")


class PolicyDocument(BaseModel):
    """Information security policy document."""
    # Document identification
    policy_id: str = Field(..., description="Policy identifier")
    title: str = Field(..., description="Policy title")
    version: str = Field(..., description="Policy version")
    
    # Content
    purpose: str = Field(..., description="Policy purpose")
    scope: str = Field(..., description="Policy scope")
    policy_statements: List[str] = Field(..., description="Policy statements")
    
    # Approval and ownership
    owner: str = Field(..., description="Policy owner")
    approved_by: str = Field(..., description="Approval authority")
    approval_date: date = Field(..., description="Approval date")
    
    # Lifecycle management
    effective_date: date = Field(..., description="Effective date")
    review_frequency: str = Field(..., description="Review frequency")
    next_review_date: date = Field(..., description="Next review date")
    
    # Distribution and awareness
    target_audience: List[str] = Field(..., description="Target audience")
    distribution_method: str = Field(..., description="Distribution method")
    awareness_training_required: bool = Field(False, description="Training required")
    
    # Compliance tracking
    compliance_monitoring: bool = Field(True, description="Compliance monitoring enabled")
    violation_consequences: Optional[str] = Field(None, description="Violation consequences")


class SecurityMetrics(BaseModel):
    """Security metrics and KPIs for ISO 27001."""
    # Metric identification
    metric_id: str = Field(..., description="Metric identifier")
    metric_name: str = Field(..., description="Metric name")
    category: str = Field(..., description="Metric category")
    
    # Measurement
    current_value: float = Field(..., description="Current metric value")
    target_value: Optional[float] = Field(None, description="Target value")
    unit_of_measure: str = Field(..., description="Unit of measurement")
    
    # Trending
    previous_value: Optional[float] = Field(None, description="Previous period value")
    trend: Optional[str] = Field(None, description="Trend direction")
    
    # Context
    measurement_period: str = Field(..., description="Measurement period")
    measurement_date: date = Field(..., description="Measurement date")
    data_source: str = Field(..., description="Data source")
    
    # Thresholds
    green_threshold: Optional[float] = Field(None, description="Green/acceptable threshold")
    amber_threshold: Optional[float] = Field(None, description="Amber/warning threshold")
    red_threshold: Optional[float] = Field(None, description="Red/critical threshold")
    
    @property
    def status(self) -> str:
        """Determine metric status based on thresholds."""
        if self.red_threshold and self.current_value >= self.red_threshold:
            return "red"
        elif self.amber_threshold and self.current_value >= self.amber_threshold:
            return "amber"
        elif self.green_threshold and self.current_value >= self.green_threshold:
            return "green"
        else:
            return "unknown"