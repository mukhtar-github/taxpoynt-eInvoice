"""
NDPA Data Models
===============
Pydantic models for Nigerian Data Protection Act compliance and validation.
"""
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field, validator
from enum import Enum


class NDPAComplianceError(Exception):
    """Raised when NDPA compliance validation fails."""
    pass


class NigerianDataCategory(str, Enum):
    """NDPA data categories."""
    PERSONAL = "personal"                    # Basic personal data
    SENSITIVE = "sensitive"                  # Sensitive personal data
    BIOMETRIC = "biometric"                  # Biometric data
    FINANCIAL = "financial"                  # Financial information
    HEALTH = "health"                        # Health data
    CHILDREN = "children"                    # Data of minors
    CRIMINAL = "criminal"                    # Criminal records
    LOCATION = "location"                    # Location data


class NigerianLawfulBasis(str, Enum):
    """Lawful basis for processing under NDPA."""
    CONSENT = "consent"                      # Data subject consent
    CONTRACT = "contract"                    # Contract performance
    LEGAL_OBLIGATION = "legal_obligation"    # Legal compliance
    VITAL_INTERESTS = "vital_interests"      # Life or death situations
    PUBLIC_TASK = "public_task"             # Public interest
    LEGITIMATE_INTERESTS = "legitimate_interests"  # Legitimate business interests


class NigerianDataSubjectRights(str, Enum):
    """Data subject rights under NDPA."""
    ACCESS = "access"                        # Right to access data
    RECTIFICATION = "rectification"          # Right to correction
    ERASURE = "erasure"                     # Right to deletion
    PORTABILITY = "portability"             # Right to data portability
    RESTRICTION = "restriction"             # Right to restrict processing
    OBJECTION = "objection"                 # Right to object
    WITHDRAWAL = "withdrawal"               # Right to withdraw consent
    NOTIFICATION = "notification"           # Right to breach notification


class NigerianEntityType(str, Enum):
    """Nigerian business entity types for NDPA compliance."""
    DATA_CONTROLLER = "data_controller"      # Determines purposes of processing
    DATA_PROCESSOR = "data_processor"       # Processes on behalf of controller
    JOINT_CONTROLLER = "joint_controller"   # Joint determination of purposes
    DATA_PROTECTION_OFFICER = "dpo"         # Data protection officer
    THIRD_PARTY = "third_party"             # External party


class NDPABreachSeverity(str, Enum):
    """NDPA data breach severity levels."""
    LOW = "low"                             # Minimal risk to rights
    MEDIUM = "medium"                       # Some risk to rights
    HIGH = "high"                           # High risk to rights
    CRITICAL = "critical"                   # Severe risk to rights


class NigerianConsentRecord(BaseModel):
    """Nigerian NDPA consent record."""
    # Core consent information
    consent_id: str = Field(..., description="Unique consent identifier")
    data_subject_id: str = Field(..., description="Data subject identifier")
    
    # Consent details
    purposes: List[str] = Field(..., description="Processing purposes")
    data_categories: List[NigerianDataCategory] = Field(..., description="Data categories")
    lawful_basis: NigerianLawfulBasis = Field(..., description="Lawful basis for processing")
    
    # Nigerian-specific requirements
    consent_language: str = Field("english", description="Language of consent (English/local)")
    nigerian_resident: bool = Field(True, description="Data subject is Nigerian resident")
    local_representative: Optional[str] = Field(None, description="Local representative if non-resident")
    
    # Consent lifecycle
    given_date: datetime = Field(..., description="When consent was given")
    expiry_date: Optional[datetime] = Field(None, description="Consent expiration")
    withdrawn_date: Optional[datetime] = Field(None, description="When consent was withdrawn")
    renewal_required: bool = Field(False, description="Requires periodic renewal")
    
    # Technical details
    consent_method: str = Field(..., description="How consent was obtained")
    ip_address: Optional[str] = Field(None, description="IP address when consent given")
    user_agent: Optional[str] = Field(None, description="Browser/app information")
    
    # Compliance tracking
    nitda_compliant: bool = Field(True, description="Meets NITDA requirements")
    audit_trail: List[Dict[str, Any]] = Field(default_factory=list, description="Consent audit trail")
    
    @validator('expiry_date')
    def validate_expiry_date(cls, v, values):
        """Validate consent expiry date."""
        if v and 'given_date' in values:
            if v <= values['given_date']:
                raise ValueError("Expiry date must be after given date")
            
            # NDPA recommends consent renewal every 2 years for sensitive data
            max_duration = timedelta(days=730)  # 2 years
            if v - values['given_date'] > max_duration:
                raise ValueError("Consent duration exceeds recommended 2 years")
        return v


class NDPABreachNotification(BaseModel):
    """Nigerian NDPA data breach notification."""
    # Breach identification
    breach_id: str = Field(..., description="Unique breach identifier")
    incident_reference: str = Field(..., description="Internal incident reference")
    
    # Breach details
    breach_type: str = Field(..., description="Type of breach")
    severity: NDPABreachSeverity = Field(..., description="Breach severity")
    data_categories_affected: List[NigerianDataCategory] = Field(..., description="Affected data categories")
    
    # Nigerian requirements
    estimated_affected_subjects: int = Field(..., ge=0, description="Number of Nigerian data subjects affected")
    nigerian_residents_only: bool = Field(True, description="Only Nigerian residents affected")
    cross_border_impact: bool = Field(False, description="Impact on cross-border transfers")
    
    # Timeline (NDPA requires 72-hour notification)
    discovery_date: datetime = Field(..., description="When breach was discovered")
    nitda_notification_date: Optional[datetime] = Field(None, description="When NITDA was notified")
    subject_notification_date: Optional[datetime] = Field(None, description="When subjects were notified")
    
    # Impact assessment
    likely_consequences: List[str] = Field(..., description="Likely consequences for data subjects")
    risk_to_rights: str = Field(..., description="Risk assessment to rights and freedoms")
    financial_impact_ngn: Optional[Decimal] = Field(None, description="Estimated financial impact in Naira")
    
    # Mitigation measures
    containment_measures: List[str] = Field(..., description="Measures taken to contain breach")
    mitigation_actions: List[str] = Field(..., description="Actions to mitigate adverse effects")
    technical_measures: List[str] = Field(..., description="Technical security measures implemented")
    
    # Nigerian regulatory compliance
    nitda_reported: bool = Field(False, description="Reported to NITDA")
    police_reported: bool = Field(False, description="Reported to Nigerian Police if criminal")
    dpo_involved: bool = Field(False, description="Data Protection Officer involved")
    
    # Documentation
    breach_description: str = Field(..., description="Detailed breach description")
    evidence_preserved: bool = Field(True, description="Evidence preserved for investigation")
    lessons_learned: Optional[str] = Field(None, description="Lessons learned and improvements")
    
    @validator('nitda_notification_date')
    def validate_nitda_notification(cls, v, values):
        """Validate NITDA notification timeline (72 hours)."""
        if v and 'discovery_date' in values:
            max_notification_time = values['discovery_date'] + timedelta(hours=72)
            if v > max_notification_time:
                raise ValueError("NITDA notification exceeds 72-hour requirement")
        return v


class NDPADataProcessingActivity(BaseModel):
    """NDPA data processing activity record."""
    # Activity identification
    activity_id: str = Field(..., description="Processing activity identifier")
    activity_name: str = Field(..., description="Name of processing activity")
    
    # Processing details
    purposes: List[str] = Field(..., description="Processing purposes")
    data_categories: List[NigerianDataCategory] = Field(..., description="Categories of data")
    lawful_basis: NigerianLawfulBasis = Field(..., description="Lawful basis")
    
    # Nigerian context
    nigerian_data_subjects: bool = Field(True, description="Processes Nigerian data subjects")
    data_location: str = Field("nigeria", description="Where data is stored/processed")
    local_processing: bool = Field(True, description="Processing occurs in Nigeria")
    
    # Entities involved
    data_controller: str = Field(..., description="Data controller entity")
    data_processors: List[str] = Field(default_factory=list, description="Data processor entities")
    third_parties: List[str] = Field(default_factory=list, description="Third parties with access")
    
    # Data lifecycle
    retention_period: str = Field(..., description="Data retention period")
    deletion_schedule: Optional[str] = Field(None, description="Automated deletion schedule")
    archival_requirements: Optional[str] = Field(None, description="Archival requirements")
    
    # Security measures
    technical_safeguards: List[str] = Field(..., description="Technical security measures")
    organizational_measures: List[str] = Field(..., description="Organizational measures")
    access_controls: List[str] = Field(..., description="Access control measures")
    
    # Cross-border considerations
    international_transfers: bool = Field(False, description="Involves international transfers")
    adequacy_decision: Optional[str] = Field(None, description="Adequacy decision reference")
    safeguards_applied: List[str] = Field(default_factory=list, description="Transfer safeguards")
    
    # Compliance status
    nitda_compliant: bool = Field(True, description="NITDA compliant")
    last_review_date: datetime = Field(..., description="Last compliance review")
    next_review_date: datetime = Field(..., description="Next scheduled review")
    risk_assessment_score: Optional[int] = Field(None, ge=1, le=10, description="Risk score (1-10)")


class NDPAComplianceResult(BaseModel):
    """Result of NDPA compliance assessment."""
    # Assessment outcome
    compliant: bool = Field(..., description="Overall NDPA compliance status")
    compliance_score: float = Field(..., ge=0.0, le=100.0, description="Compliance score percentage")
    risk_level: str = Field(..., description="Overall risk level")
    
    # Detailed results
    consent_compliance: Dict[str, Any] = Field(default_factory=dict, description="Consent compliance details")
    data_processing_compliance: Dict[str, Any] = Field(default_factory=dict, description="Processing compliance")
    security_compliance: Dict[str, Any] = Field(default_factory=dict, description="Security measures compliance")
    breach_management_compliance: Dict[str, Any] = Field(default_factory=dict, description="Breach management")
    
    # Nigerian-specific results
    nitda_requirements_met: List[str] = Field(default_factory=list, description="Met NITDA requirements")
    nitda_requirements_missing: List[str] = Field(default_factory=list, description="Missing NITDA requirements")
    nigerian_law_compliance: bool = Field(True, description="Nigerian law compliance")
    
    # Issues and recommendations
    critical_issues: List[str] = Field(default_factory=list, description="Critical compliance issues")
    warnings: List[str] = Field(default_factory=list, description="Compliance warnings")
    recommendations: List[str] = Field(default_factory=list, description="Improvement recommendations")
    
    # Assessment metadata
    assessment_date: datetime = Field(default_factory=datetime.now, description="Assessment timestamp")
    assessor: str = Field(..., description="Who performed the assessment")
    next_assessment_due: datetime = Field(..., description="Next assessment due date")
    
    # Penalties and sanctions
    potential_penalties_ngn: Optional[Decimal] = Field(None, description="Potential penalties in Naira")
    sanction_risk: str = Field("low", description="Risk of regulatory sanctions")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            'compliant': self.compliant,
            'compliance_score': self.compliance_score,
            'risk_level': self.risk_level,
            'assessment_date': self.assessment_date.isoformat(),
            'critical_issues_count': len(self.critical_issues),
            'warnings_count': len(self.warnings),
            'nitda_requirements_met': len(self.nitda_requirements_met),
            'nitda_requirements_missing': len(self.nitda_requirements_missing),
            'nigerian_law_compliance': self.nigerian_law_compliance,
            'potential_penalties_ngn': float(self.potential_penalties_ngn) if self.potential_penalties_ngn else None
        }


class NigerianPrivacySettings(BaseModel):
    """Nigerian privacy settings configuration."""
    # Data protection preferences
    privacy_level: str = Field("standard", description="Privacy protection level")
    data_minimization: bool = Field(True, description="Apply data minimization")
    consent_required: bool = Field(True, description="Explicit consent required")
    
    # Nigerian-specific settings
    nigerian_resident_only: bool = Field(False, description="Nigerian residents only")
    local_storage_required: bool = Field(True, description="Require local data storage")
    english_language_required: bool = Field(True, description="Require English language support")
    
    # Cross-border restrictions
    international_transfers_allowed: bool = Field(False, description="Allow international transfers")
    approved_countries: List[str] = Field(default_factory=list, description="Approved destination countries")
    transfer_safeguards: List[str] = Field(default_factory=list, description="Required transfer safeguards")
    
    # Retention and deletion
    default_retention_days: int = Field(365, description="Default retention period in days")
    automatic_deletion: bool = Field(True, description="Enable automatic deletion")
    deletion_verification: bool = Field(True, description="Verify deletion completion")
    
    # Notification preferences
    breach_notification_enabled: bool = Field(True, description="Enable breach notifications")
    privacy_policy_updates: bool = Field(True, description="Notify of privacy policy updates")
    consent_renewal_reminders: bool = Field(True, description="Send consent renewal reminders")
    
    # Compliance monitoring
    regular_audits: bool = Field(True, description="Enable regular compliance audits")
    audit_frequency_days: int = Field(90, description="Audit frequency in days")
    risk_assessments: bool = Field(True, description="Enable privacy risk assessments")