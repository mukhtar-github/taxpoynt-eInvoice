"""
GDPR Data Models
===============
Pydantic models for European General Data Protection Regulation compliance.
"""
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field, validator
from enum import Enum


class GDPRComplianceError(Exception):
    """Raised when GDPR compliance validation fails."""
    pass


class EuropeanDataCategory(str, Enum):
    """GDPR data categories."""
    PERSONAL = "personal"                    # Basic personal data
    SPECIAL = "special"                      # Special category data (Article 9)
    BIOMETRIC = "biometric"                  # Biometric data
    GENETIC = "genetic"                      # Genetic data
    HEALTH = "health"                        # Health data
    CHILDREN = "children"                    # Data of children under 16
    CRIMINAL = "criminal"                    # Criminal convictions and offences
    LOCATION = "location"                    # Location data
    ONLINE_IDENTIFIERS = "online_identifiers"  # Online identifiers


class EuropeanLawfulBasis(str, Enum):
    """Lawful basis for processing under GDPR Article 6."""
    CONSENT = "consent"                      # Data subject consent
    CONTRACT = "contract"                    # Contract performance
    LEGAL_OBLIGATION = "legal_obligation"    # Legal compliance
    VITAL_INTERESTS = "vital_interests"      # Life or death situations
    PUBLIC_TASK = "public_task"             # Public interest or official authority
    LEGITIMATE_INTERESTS = "legitimate_interests"  # Legitimate business interests


class EuropeanDataSubjectRights(str, Enum):
    """Data subject rights under GDPR."""
    ACCESS = "access"                        # Right of access (Article 15)
    RECTIFICATION = "rectification"          # Right to rectification (Article 16)
    ERASURE = "erasure"                     # Right to erasure/be forgotten (Article 17)
    PORTABILITY = "portability"             # Right to data portability (Article 20)
    RESTRICTION = "restriction"             # Right to restriction (Article 18)
    OBJECTION = "objection"                 # Right to object (Article 21)
    AUTOMATED_DECISION = "automated_decision"  # Rights in automated decision-making (Article 22)


class GDPRBreachSeverity(str, Enum):
    """GDPR data breach severity levels."""
    LOW = "low"                             # Unlikely to result in risk
    MEDIUM = "medium"                       # Likely to result in risk
    HIGH = "high"                           # Likely to result in high risk
    CRITICAL = "critical"                   # Very likely to result in high risk


class TransferMechanism(str, Enum):
    """GDPR transfer mechanisms for international transfers."""
    ADEQUACY_DECISION = "adequacy_decision"  # EU adequacy decision
    STANDARD_CONTRACTUAL_CLAUSES = "scc"    # Standard Contractual Clauses
    BINDING_CORPORATE_RULES = "bcr"         # Binding Corporate Rules
    CERTIFICATION = "certification"          # Certification mechanism
    CODE_OF_CONDUCT = "code_of_conduct"     # Code of conduct
    DEROGATION = "derogation"               # Article 49 derogations


class EuropeanConsentRecord(BaseModel):
    """European GDPR consent record."""
    # Core consent information
    consent_id: str = Field(..., description="Unique consent identifier")
    data_subject_id: str = Field(..., description="Data subject identifier")
    
    # Consent details
    purposes: List[str] = Field(..., description="Specific processing purposes")
    data_categories: List[EuropeanDataCategory] = Field(..., description="Data categories")
    lawful_basis: EuropeanLawfulBasis = Field(..., description="Lawful basis for processing")
    
    # GDPR-specific requirements
    freely_given: bool = Field(True, description="Consent freely given")
    specific: bool = Field(True, description="Consent is specific")
    informed: bool = Field(True, description="Consent is informed")
    unambiguous: bool = Field(True, description="Consent is unambiguous")
    
    # Special category consent (Article 9)
    special_category_consent: bool = Field(False, description="Explicit consent for special categories")
    
    # Consent lifecycle
    given_date: datetime = Field(..., description="When consent was given")
    expiry_date: Optional[datetime] = Field(None, description="Consent expiration")
    withdrawn_date: Optional[datetime] = Field(None, description="When consent was withdrawn")
    renewal_required: bool = Field(False, description="Requires periodic renewal")
    
    # Technical details
    consent_method: str = Field(..., description="How consent was obtained")
    consent_string: Optional[str] = Field(None, description="IAB consent string if applicable")
    ip_address: Optional[str] = Field(None, description="IP address when consent given")
    user_agent: Optional[str] = Field(None, description="Browser/app information")
    
    # Compliance tracking
    gdpr_compliant: bool = Field(True, description="Meets GDPR requirements")
    audit_trail: List[Dict[str, Any]] = Field(default_factory=list, description="Consent audit trail")
    
    @validator('special_category_consent')
    def validate_special_category_consent(cls, v, values):
        """Validate special category consent requirements."""
        if 'data_categories' in values:
            special_categories = {
                EuropeanDataCategory.SPECIAL, EuropeanDataCategory.BIOMETRIC,
                EuropeanDataCategory.GENETIC, EuropeanDataCategory.HEALTH
            }
            
            has_special_data = any(cat in special_categories for cat in values['data_categories'])
            
            if has_special_data and not v:
                raise ValueError("Special category data requires explicit consent")
        
        return v


class GDPRBreachNotification(BaseModel):
    """European GDPR data breach notification."""
    # Breach identification
    breach_id: str = Field(..., description="Unique breach identifier")
    incident_reference: str = Field(..., description="Internal incident reference")
    
    # Breach details
    breach_type: str = Field(..., description="Type of breach")
    severity: GDPRBreachSeverity = Field(..., description="Breach severity")
    data_categories_affected: List[EuropeanDataCategory] = Field(..., description="Affected data categories")
    
    # EU/EEA specific details
    estimated_affected_subjects: int = Field(..., ge=0, description="Number of EU/EEA data subjects affected")
    eu_residents_affected: bool = Field(True, description="EU/EEA residents affected")
    cross_border_breach: bool = Field(False, description="Breach affects multiple EU member states")
    
    # Timeline (GDPR requires 72-hour notification to DPA)
    discovery_date: datetime = Field(..., description="When breach was discovered")
    dpa_notification_date: Optional[datetime] = Field(None, description="When DPA was notified")
    subject_notification_date: Optional[datetime] = Field(None, description="When subjects were notified")
    
    # Lead supervisory authority
    lead_sa: Optional[str] = Field(None, description="Lead supervisory authority")
    concerned_sas: List[str] = Field(default_factory=list, description="Concerned supervisory authorities")
    
    # Impact assessment
    likely_consequences: List[str] = Field(..., description="Likely consequences for data subjects")
    risk_to_rights: str = Field(..., description="Risk assessment to rights and freedoms")
    financial_impact_eur: Optional[Decimal] = Field(None, description="Estimated financial impact in EUR")
    
    # Mitigation measures
    containment_measures: List[str] = Field(..., description="Measures taken to contain breach")
    mitigation_actions: List[str] = Field(..., description="Actions to mitigate adverse effects")
    technical_measures: List[str] = Field(..., description="Technical security measures implemented")
    
    # GDPR regulatory compliance
    dpa_reported: bool = Field(False, description="Reported to Data Protection Authority")
    dpo_involved: bool = Field(False, description="Data Protection Officer involved")
    one_stop_shop: bool = Field(False, description="One-stop-shop mechanism applied")
    
    # Documentation
    breach_description: str = Field(..., description="Detailed breach description")
    evidence_preserved: bool = Field(True, description="Evidence preserved for investigation")
    lessons_learned: Optional[str] = Field(None, description="Lessons learned and improvements")
    
    @validator('dpa_notification_date')
    def validate_dpa_notification(cls, v, values):
        """Validate DPA notification timeline (72 hours)."""
        if v and 'discovery_date' in values:
            max_notification_time = values['discovery_date'] + timedelta(hours=72)
            if v > max_notification_time:
                raise ValueError("DPA notification exceeds 72-hour requirement")
        return v


class GDPRDataProcessingActivity(BaseModel):
    """GDPR data processing activity record (Article 30)."""
    # Activity identification
    activity_id: str = Field(..., description="Processing activity identifier")
    activity_name: str = Field(..., description="Name of processing activity")
    
    # Processing details
    purposes: List[str] = Field(..., description="Processing purposes")
    data_categories: List[EuropeanDataCategory] = Field(..., description="Categories of personal data")
    lawful_basis: EuropeanLawfulBasis = Field(..., description="Lawful basis under Article 6")
    
    # Special category processing (Article 9)
    special_category_processing: bool = Field(False, description="Processes special category data")
    article_9_condition: Optional[str] = Field(None, description="Article 9 condition if applicable")
    
    # EU/EEA context
    eu_data_subjects: bool = Field(True, description="Processes EU/EEA data subjects")
    processing_location: str = Field(..., description="Where processing occurs")
    establishment_in_eu: bool = Field(True, description="Controller/processor established in EU")
    
    # Entities involved
    data_controller: str = Field(..., description="Data controller entity")
    data_processors: List[str] = Field(default_factory=list, description="Data processor entities")
    joint_controllers: List[str] = Field(default_factory=list, description="Joint controllers if applicable")
    
    # Data lifecycle
    retention_period: str = Field(..., description="Data retention period")
    deletion_schedule: Optional[str] = Field(None, description="Automated deletion schedule")
    archival_requirements: Optional[str] = Field(None, description="Legal archival requirements")
    
    # Security measures (Article 32)
    technical_safeguards: List[str] = Field(..., description="Technical security measures")
    organizational_measures: List[str] = Field(..., description="Organizational measures")
    pseudonymization: bool = Field(False, description="Pseudonymization applied")
    encryption: bool = Field(False, description="Encryption applied")
    
    # International transfers
    international_transfers: bool = Field(False, description="Involves transfers outside EU/EEA")
    transfer_mechanism: Optional[TransferMechanism] = Field(None, description="Transfer mechanism used")
    adequacy_decision: Optional[str] = Field(None, description="Adequacy decision reference")
    safeguards_applied: List[str] = Field(default_factory=list, description="Appropriate safeguards")
    
    # Recipients
    recipients: List[str] = Field(default_factory=list, description="Categories of recipients")
    third_country_recipients: List[str] = Field(default_factory=list, description="Third country recipients")
    
    # Compliance status
    gdpr_compliant: bool = Field(True, description="GDPR compliant")
    dpia_required: bool = Field(False, description="Data Protection Impact Assessment required")
    dpia_completed: Optional[datetime] = Field(None, description="DPIA completion date")
    last_review_date: datetime = Field(..., description="Last compliance review")
    next_review_date: datetime = Field(..., description="Next scheduled review")


class GDPRComplianceResult(BaseModel):
    """Result of GDPR compliance assessment."""
    # Assessment outcome
    compliant: bool = Field(..., description="Overall GDPR compliance status")
    compliance_score: float = Field(..., ge=0.0, le=100.0, description="Compliance score percentage")
    risk_level: str = Field(..., description="Overall risk level")
    
    # Detailed results
    consent_compliance: Dict[str, Any] = Field(default_factory=dict, description="Consent compliance details")
    data_processing_compliance: Dict[str, Any] = Field(default_factory=dict, description="Processing compliance")
    security_compliance: Dict[str, Any] = Field(default_factory=dict, description="Security measures compliance")
    breach_management_compliance: Dict[str, Any] = Field(default_factory=dict, description="Breach management")
    transfer_compliance: Dict[str, Any] = Field(default_factory=dict, description="International transfer compliance")
    
    # GDPR-specific results
    article_30_compliance: Dict[str, Any] = Field(default_factory=dict, description="Article 30 record keeping")
    dpia_compliance: Dict[str, Any] = Field(default_factory=dict, description="DPIA requirements")
    data_subject_rights_compliance: Dict[str, Any] = Field(default_factory=dict, description="Data subject rights")
    
    # Issues and recommendations
    critical_issues: List[str] = Field(default_factory=list, description="Critical compliance issues")
    warnings: List[str] = Field(default_factory=list, description="Compliance warnings")
    recommendations: List[str] = Field(default_factory=list, description="Improvement recommendations")
    
    # Assessment metadata
    assessment_date: datetime = Field(default_factory=datetime.now, description="Assessment timestamp")
    assessor: str = Field(..., description="Who performed the assessment")
    next_assessment_due: datetime = Field(..., description="Next assessment due date")
    
    # EU regulatory context
    lead_supervisory_authority: Optional[str] = Field(None, description="Lead supervisory authority")
    applicable_member_states: List[str] = Field(default_factory=list, description="Applicable EU member states")
    
    # Penalties and sanctions
    potential_penalties_eur: Optional[Decimal] = Field(None, description="Potential penalties in EUR")
    max_fine_applicable: Optional[Decimal] = Field(None, description="Maximum applicable fine")
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
            'lead_supervisory_authority': self.lead_supervisory_authority,
            'applicable_member_states': self.applicable_member_states,
            'potential_penalties_eur': float(self.potential_penalties_eur) if self.potential_penalties_eur else None,
            'max_fine_applicable': float(self.max_fine_applicable) if self.max_fine_applicable else None
        }


class EuropeanPrivacySettings(BaseModel):
    """European GDPR privacy settings configuration."""
    # Data protection preferences
    privacy_level: str = Field("standard", description="Privacy protection level")
    data_minimization: bool = Field(True, description="Apply data minimization principle")
    purpose_limitation: bool = Field(True, description="Enforce purpose limitation")
    storage_limitation: bool = Field(True, description="Apply storage limitation")
    
    # EU/EEA specific settings
    eu_residents_only: bool = Field(False, description="EU/EEA residents only")
    gdpr_territorial_scope: bool = Field(True, description="Apply GDPR territorial scope")
    multi_language_support: bool = Field(True, description="Multi-language privacy notices")
    
    # Consent management
    granular_consent: bool = Field(True, description="Granular consent options")
    consent_withdrawal: bool = Field(True, description="Easy consent withdrawal")
    consent_renewal: bool = Field(True, description="Consent renewal prompts")
    
    # International transfers
    international_transfers_allowed: bool = Field(False, description="Allow international transfers")
    adequacy_countries_only: bool = Field(True, description="Transfers to adequacy countries only")
    scc_required: bool = Field(True, description="Require SCCs for non-adequacy transfers")
    
    # Data subject rights
    automated_access_requests: bool = Field(True, description="Automated access request handling")
    data_portability_format: str = Field("json", description="Data portability format")
    erasure_verification: bool = Field(True, description="Verify erasure completion")
    
    # Retention and deletion
    default_retention_days: int = Field(365, description="Default retention period in days")
    automatic_deletion: bool = Field(True, description="Enable automatic deletion")
    legal_hold_support: bool = Field(True, description="Support legal hold requirements")
    
    # Breach management
    breach_detection: bool = Field(True, description="Enable breach detection")
    automatic_dpa_notification: bool = Field(False, description="Automatic DPA notification")
    breach_register: bool = Field(True, description="Maintain breach register")
    
    # Compliance monitoring
    regular_audits: bool = Field(True, description="Enable regular compliance audits")
    audit_frequency_days: int = Field(90, description="Audit frequency in days")
    dpia_automation: bool = Field(True, description="Automated DPIA triggering")
    
    # DPO settings
    dpo_required: bool = Field(False, description="Data Protection Officer required")
    dpo_contact_info: Optional[str] = Field(None, description="DPO contact information")
    dpo_independence: bool = Field(True, description="Ensure DPO independence")