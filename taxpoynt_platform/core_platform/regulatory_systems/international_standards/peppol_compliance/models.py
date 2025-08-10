"""
PEPPOL Standards Data Models
===========================
Pydantic models for PEPPOL (Pan-European Public Procurement On-Line) 
standards compliance and international invoice safety validation.
"""
from datetime import datetime, date
from decimal import Decimal
from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field, validator
from enum import Enum


class DocumentType(str, Enum):
    """PEPPOL document types"""
    INVOICE = "invoice"
    CREDIT_NOTE = "credit_note"
    ORDER = "order"
    ORDER_RESPONSE = "order_response"
    DESPATCH_ADVICE = "despatch_advice"
    RECEIPT_ADVICE = "receipt_advice"
    CATALOGUE = "catalogue"
    CATALOGUE_RESPONSE = "catalogue_response"


class MessageStatus(str, Enum):
    """PEPPOL message delivery status"""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    ACKNOWLEDGED = "acknowledged"
    FAILED = "failed"
    REJECTED = "rejected"
    EXPIRED = "expired"


class SecurityLevel(str, Enum):
    """PEPPOL security levels"""
    BASIC = "basic"
    ENHANCED = "enhanced"
    HIGH_SECURITY = "high_security"
    CRITICAL = "critical"


class ValidationLevel(str, Enum):
    """PEPPOL validation levels"""
    SYNTAX = "syntax"
    BUSINESS_RULES = "business_rules"
    PEPPOL_RULES = "peppol_rules"
    NATIONAL_RULES = "national_rules"


class ParticipantScheme(str, Enum):
    """PEPPOL participant identifier schemes"""
    GLN = "0088"  # Global Location Number
    DUNS = "0060"  # Dun & Bradstreet
    LEI = "0199"  # Legal Entity Identifier
    NATIONAL_ID = "0007"  # National identifier
    VAT_ID = "9906"  # VAT identification number
    COMPANY_CODE = "0002"  # System Information et Repertoire des Entreprises et des Etablissements: SIRENE
    NIGERIAN_TIN = "9999"  # Nigerian Tax Identification Number (custom scheme)


class PEPPOLParticipant(BaseModel):
    """PEPPOL network participant information"""
    participant_id: str = Field(..., description="PEPPOL participant identifier")
    scheme_id: ParticipantScheme = Field(..., description="Participant identifier scheme")
    participant_name: str = Field(..., description="Legal name of participant")
    country_code: str = Field(..., max_length=2, description="ISO country code")
    registration_date: datetime = Field(..., description="PEPPOL registration date")
    status: str = Field(..., description="Participant status (active/inactive)")
    supported_documents: List[DocumentType] = Field(default_factory=list, description="Supported document types")
    capabilities: List[str] = Field(default_factory=list, description="Technical capabilities")
    service_metadata: Dict[str, Any] = Field(default_factory=dict, description="Service metadata location")
    certificates: List[Dict[str, Any]] = Field(default_factory=list, description="Digital certificates")
    contact_info: Dict[str, str] = Field(default_factory=dict, description="Contact information")
    
    @validator('participant_id')
    def validate_participant_id(cls, v, values):
        scheme = values.get('scheme_id')
        if scheme == ParticipantScheme.NIGERIAN_TIN:
            # Nigerian TIN validation
            if not v.isdigit() or len(v) not in [10, 11]:
                raise ValueError('Nigerian TIN must be 10-11 digits')
        return v


class PEPPOLDocument(BaseModel):
    """PEPPOL-compliant document structure"""
    document_id: str = Field(..., description="Unique document identifier")
    document_type: DocumentType = Field(..., description="Type of PEPPOL document")
    profile_id: str = Field(..., description="PEPPOL business process profile")
    customization_id: str = Field(..., description="Document customization identifier")
    sender_participant: PEPPOLParticipant = Field(..., description="Sending participant")
    receiver_participant: PEPPOLParticipant = Field(..., description="Receiving participant")
    document_date: date = Field(..., description="Document issue date")
    due_date: Optional[date] = Field(None, description="Payment due date")
    currency_code: str = Field(..., max_length=3, description="ISO currency code")
    total_amount: Decimal = Field(..., ge=0, description="Total document amount")
    tax_amount: Decimal = Field(..., ge=0, description="Total tax amount")
    payable_amount: Decimal = Field(..., ge=0, description="Total payable amount")
    document_content: Dict[str, Any] = Field(..., description="UBL document content")
    attachments: List[Dict[str, Any]] = Field(default_factory=list, description="Document attachments")
    digital_signatures: List[Dict[str, Any]] = Field(default_factory=list, description="Digital signatures")
    routing_metadata: Dict[str, Any] = Field(default_factory=dict, description="PEPPOL routing metadata")
    
    @validator('profile_id')
    def validate_profile_id(cls, v):
        # Common PEPPOL BIS profiles
        valid_profiles = [
            'urn:fdc:peppol.eu:2017:poacc:billing:01:1.0',  # Billing
            'urn:fdc:peppol.eu:2017:poacc:selfbilling:01:1.0',  # Self-billing
            'urn:fdc:peppol.eu:2017:poacc:ordering:01:1.0',  # Ordering
            'urn:fdc:peppol.eu:2017:poacc:despatchadvice:01:1.0'  # Despatch advice
        ]
        if v not in valid_profiles:
            raise ValueError(f'Invalid PEPPOL profile ID: {v}')
        return v


class PEPPOLValidationResult(BaseModel):
    """PEPPOL validation result"""
    document_id: str = Field(..., description="Document identifier")
    validation_timestamp: datetime = Field(..., description="Validation timestamp")
    validation_level: ValidationLevel = Field(..., description="Level of validation performed")
    is_valid: bool = Field(..., description="Overall validation result")
    validation_score: float = Field(..., ge=0, le=100, description="Validation score percentage")
    
    # Validation results by category
    syntax_validation: Dict[str, Any] = Field(default_factory=dict, description="Syntax validation results")
    business_rules_validation: Dict[str, Any] = Field(default_factory=dict, description="Business rules validation")
    peppol_rules_validation: Dict[str, Any] = Field(default_factory=dict, description="PEPPOL-specific rules validation")
    national_rules_validation: Dict[str, Any] = Field(default_factory=dict, description="National rules validation")
    
    # Detailed results
    passed_rules: List[str] = Field(default_factory=list, description="Successfully validated rules")
    failed_rules: List[str] = Field(default_factory=list, description="Failed validation rules")
    warnings: List[str] = Field(default_factory=list, description="Validation warnings")
    errors: List[str] = Field(default_factory=list, description="Validation errors")
    fatal_errors: List[str] = Field(default_factory=list, description="Fatal validation errors")
    
    # Recommendations
    recommendations: List[str] = Field(default_factory=list, description="Improvement recommendations")
    next_validation_date: Optional[datetime] = Field(None, description="Next validation due date")
    
    @validator('validation_score')
    def calculate_validation_score(cls, v, values):
        """Calculate validation score based on results"""
        total_rules = len(values.get('passed_rules', [])) + len(values.get('failed_rules', []))
        if total_rules == 0:
            return 0.0
        return (len(values.get('passed_rules', [])) / total_rules) * 100


class PEPPOLMessage(BaseModel):
    """PEPPOL message envelope"""
    message_id: str = Field(..., description="Unique message identifier")
    timestamp: datetime = Field(..., description="Message timestamp")
    sender_id: str = Field(..., description="Sender participant ID")
    receiver_id: str = Field(..., description="Receiver participant ID")
    document_type: DocumentType = Field(..., description="Document type")
    message_status: MessageStatus = Field(default=MessageStatus.PENDING, description="Message status")
    security_level: SecurityLevel = Field(default=SecurityLevel.BASIC, description="Security level")
    
    # Message content
    payload: bytes = Field(..., description="Message payload (encrypted)")
    payload_size: int = Field(..., ge=0, description="Payload size in bytes")
    content_type: str = Field(default="application/xml", description="Content MIME type")
    encoding: str = Field(default="UTF-8", description="Content encoding")
    
    # Routing information
    routing_metadata: Dict[str, Any] = Field(default_factory=dict, description="Message routing metadata")
    delivery_receipt_requested: bool = Field(default=True, description="Delivery receipt requested")
    
    # Security information
    encryption_algorithm: Optional[str] = Field(None, description="Encryption algorithm used")
    signature_algorithm: Optional[str] = Field(None, description="Digital signature algorithm")
    certificate_thumbprint: Optional[str] = Field(None, description="Certificate thumbprint")
    
    # Tracking information
    sent_timestamp: Optional[datetime] = Field(None, description="Message sent timestamp")
    delivered_timestamp: Optional[datetime] = Field(None, description="Message delivered timestamp")
    acknowledged_timestamp: Optional[datetime] = Field(None, description="Acknowledgment timestamp")
    retry_count: int = Field(default=0, ge=0, description="Delivery retry count")
    max_retries: int = Field(default=3, ge=1, description="Maximum retry attempts")
    expiry_timestamp: Optional[datetime] = Field(None, description="Message expiry timestamp")
    
    @validator('payload_size')
    def validate_payload_size(cls, v):
        # PEPPOL has message size limits
        max_size = 100 * 1024 * 1024  # 100MB limit
        if v > max_size:
            raise ValueError(f'Message payload exceeds maximum size limit: {max_size} bytes')
        return v


class PEPPOLSecurityToken(BaseModel):
    """PEPPOL security token for authentication"""
    token_id: str = Field(..., description="Token identifier")
    issued_timestamp: datetime = Field(..., description="Token issue timestamp")
    expiry_timestamp: datetime = Field(..., description="Token expiry timestamp")
    issuer: str = Field(..., description="Token issuer")
    subject: str = Field(..., description="Token subject (participant ID)")
    scopes: List[str] = Field(default_factory=list, description="Token scopes/permissions")
    token_type: str = Field(default="Bearer", description="Token type")
    signature: str = Field(..., description="Token signature")
    
    @validator('expiry_timestamp')
    def validate_expiry(cls, v, values):
        issued = values.get('issued_timestamp')
        if issued and v <= issued:
            raise ValueError('Token expiry must be after issue timestamp')
        return v


class PEPPOLAuditEvent(BaseModel):
    """PEPPOL audit event for compliance tracking"""
    event_id: str = Field(..., description="Unique event identifier")
    timestamp: datetime = Field(..., description="Event timestamp")
    event_type: str = Field(..., description="Type of event")
    participant_id: str = Field(..., description="Related participant ID")
    document_id: Optional[str] = Field(None, description="Related document ID")
    message_id: Optional[str] = Field(None, description="Related message ID")
    
    # Event details
    event_description: str = Field(..., description="Event description")
    event_category: str = Field(..., description="Event category")
    severity_level: str = Field(default="info", description="Event severity")
    
    # Context information
    source_system: str = Field(..., description="Source system generating event")
    user_context: Dict[str, Any] = Field(default_factory=dict, description="User context")
    technical_details: Dict[str, Any] = Field(default_factory=dict, description="Technical event details")
    
    # Compliance tracking
    compliance_impact: Optional[str] = Field(None, description="Impact on compliance status")
    remediation_required: bool = Field(default=False, description="Remediation required flag")
    remediation_steps: List[str] = Field(default_factory=list, description="Remediation steps")


class PEPPOLComplianceReport(BaseModel):
    """PEPPOL compliance status report"""
    report_id: str = Field(..., description="Unique report identifier")
    generated_timestamp: datetime = Field(..., description="Report generation timestamp")
    reporting_period_start: date = Field(..., description="Reporting period start date")
    reporting_period_end: date = Field(..., description="Reporting period end date")
    participant_id: str = Field(..., description="Participant ID for this report")
    
    # Compliance metrics
    total_documents_processed: int = Field(default=0, ge=0, description="Total documents processed")
    successful_validations: int = Field(default=0, ge=0, description="Successful validations")
    failed_validations: int = Field(default=0, ge=0, description="Failed validations")
    compliance_percentage: float = Field(default=0.0, ge=0, le=100, description="Overall compliance percentage")
    
    # Document type breakdown
    document_type_metrics: Dict[str, Dict[str, int]] = Field(
        default_factory=dict, 
        description="Metrics by document type"
    )
    
    # Validation results summary
    validation_summary: Dict[str, Any] = Field(
        default_factory=dict,
        description="Summary of validation results"
    )
    
    # Common issues
    common_errors: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Most common validation errors"
    )
    
    # Recommendations
    improvement_recommendations: List[str] = Field(
        default_factory=list,
        description="Recommendations for improvement"
    )
    
    # Next steps
    next_review_date: date = Field(..., description="Next compliance review date")
    action_items: List[str] = Field(default_factory=list, description="Action items for compliance improvement")
    
    @validator('compliance_percentage')
    def calculate_compliance_percentage(cls, v, values):
        """Calculate compliance percentage"""
        total = values.get('total_documents_processed', 0)
        successful = values.get('successful_validations', 0)
        if total == 0:
            return 0.0
        return (successful / total) * 100


class NigerianPEPPOLExtension(BaseModel):
    """Nigerian-specific PEPPOL extensions"""
    tin_number: str = Field(..., description="Nigerian Tax Identification Number")
    cac_registration: Optional[str] = Field(None, description="CAC registration number")
    vat_registration: Optional[str] = Field(None, description="VAT registration number")
    business_classification: str = Field(..., description="Nigerian business classification")
    regulatory_approvals: List[str] = Field(default_factory=list, description="Required regulatory approvals")
    local_currency_requirements: Dict[str, Any] = Field(
        default_factory=dict,
        description="Local currency and exchange rate requirements"
    )
    
    @validator('tin_number')
    def validate_nigerian_tin(cls, v):
        """Validate Nigerian TIN format"""
        if not v.isdigit() or len(v) not in [10, 11]:
            raise ValueError('Nigerian TIN must be 10-11 digits')
        return v