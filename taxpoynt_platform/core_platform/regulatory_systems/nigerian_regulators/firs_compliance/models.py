"""
FIRS Compliance Data Models
==========================
Pydantic models for FIRS (Federal Inland Revenue Service) compliance validation and e-invoicing.
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field, validator
from enum import Enum

class TINValidationStatus(str, Enum):
    """TIN validation status enumeration"""
    VALID = "valid"
    INVALID = "invalid"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    NOT_FOUND = "not_found"
    FORMAT_ERROR = "format_error"

class VATStatus(str, Enum):
    """VAT registration status"""
    REGISTERED = "registered"
    NOT_REGISTERED = "not_registered"
    EXEMPT = "exempt"
    ZERO_RATED = "zero_rated"
    SUSPENDED = "suspended"

class InvoiceType(str, Enum):
    """FIRS recognized invoice types"""
    STANDARD = "standard"
    CREDIT_NOTE = "credit_note"
    DEBIT_NOTE = "debit_note"
    PROFORMA = "proforma"
    RECEIPT = "receipt"
    TAX_INVOICE = "tax_invoice"

class TaxType(str, Enum):
    """Nigerian tax types"""
    VAT = "vat"
    WHT = "withholding_tax"
    CIT = "company_income_tax"
    PIT = "personal_income_tax"
    STAMP_DUTY = "stamp_duty"
    CUSTOMS_DUTY = "customs_duty"

class ComplianceLevel(str, Enum):
    """FIRS compliance assessment levels"""
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PARTIALLY_COMPLIANT = "partially_compliant"
    REQUIRES_REVIEW = "requires_review"
    CRITICAL_VIOLATION = "critical_violation"

class SubmissionStatus(str, Enum):
    """E-invoice submission status"""
    PENDING = "pending"
    SUBMITTED = "submitted"
    ACKNOWLEDGED = "acknowledged"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    EXPIRED = "expired"

class TINValidationResult(BaseModel):
    """TIN validation result model"""
    tin: str = Field(..., description="Tax Identification Number")
    is_valid: bool = Field(..., description="TIN validity status")
    status: TINValidationStatus = Field(..., description="Detailed validation status")
    taxpayer_name: Optional[str] = Field(None, description="Registered taxpayer name")
    registration_date: Optional[date] = Field(None, description="TIN registration date")
    tax_office: Optional[str] = Field(None, description="Responsible tax office")
    validation_timestamp: datetime = Field(default_factory=datetime.now)
    error_message: Optional[str] = Field(None, description="Validation error details")

    @validator('tin')
    def validate_tin_format(cls, v):
        """Validate Nigerian TIN format"""
        if not v or len(v) != 14:
            raise ValueError("Nigerian TIN must be 14 digits")
        if not v.isdigit():
            raise ValueError("TIN must contain only digits")
        return v

class VATCalculation(BaseModel):
    """VAT calculation and validation model"""
    amount_before_vat: Decimal = Field(..., description="Amount before VAT", ge=0)
    vat_rate: Decimal = Field(..., description="Applied VAT rate", ge=0, le=100)
    vat_amount: Decimal = Field(..., description="Calculated VAT amount", ge=0)
    total_amount: Decimal = Field(..., description="Total amount including VAT", ge=0)
    vat_status: VATStatus = Field(..., description="VAT registration status")
    is_vat_exempt: bool = Field(False, description="VAT exemption status")
    exemption_reason: Optional[str] = Field(None, description="VAT exemption reason")
    calculation_date: datetime = Field(default_factory=datetime.now)

    @validator('vat_amount')
    def validate_vat_calculation(cls, v, values):
        """Validate VAT calculation accuracy"""
        if 'amount_before_vat' in values and 'vat_rate' in values:
            expected_vat = values['amount_before_vat'] * (values['vat_rate'] / 100)
            if abs(v - expected_vat) > Decimal('0.01'):
                raise ValueError("VAT calculation is incorrect")
        return v

    @validator('total_amount')
    def validate_total_amount(cls, v, values):
        """Validate total amount calculation"""
        if 'amount_before_vat' in values and 'vat_amount' in values:
            expected_total = values['amount_before_vat'] + values['vat_amount']
            if abs(v - expected_total) > Decimal('0.01'):
                raise ValueError("Total amount calculation is incorrect")
        return v

class NigerianTaxInfo(BaseModel):
    """Nigerian tax information model"""
    supplier_tin: str = Field(..., description="Supplier TIN")
    customer_tin: Optional[str] = Field(None, description="Customer TIN")
    tax_office_code: str = Field(..., description="Tax office code")
    vat_calculation: VATCalculation = Field(..., description="VAT calculation details")
    withholding_tax: Optional[Decimal] = Field(None, description="Withholding tax amount", ge=0)
    stamp_duty: Optional[Decimal] = Field(None, description="Stamp duty amount", ge=0)
    currency_code: str = Field("NGN", description="Currency code")
    exchange_rate: Optional[Decimal] = Field(None, description="Exchange rate to NGN", gt=0)
    tax_period: str = Field(..., description="Tax period (YYYY-MM)")

    @validator('tax_period')
    def validate_tax_period(cls, v):
        """Validate tax period format"""
        try:
            datetime.strptime(v, '%Y-%m')
        except ValueError:
            raise ValueError("Tax period must be in YYYY-MM format")
        return v

class FIRSValidationRule(BaseModel):
    """FIRS validation rule model"""
    rule_id: str = Field(..., description="Unique rule identifier")
    rule_name: str = Field(..., description="Rule name")
    rule_type: str = Field(..., description="Rule type (format, business, calculation)")
    description: str = Field(..., description="Rule description")
    is_mandatory: bool = Field(True, description="Mandatory rule flag")
    severity_level: str = Field("error", description="Error severity level")

class FIRSValidationResult(BaseModel):
    """FIRS validation result model"""
    is_compliant: bool = Field(..., description="Overall compliance status")
    compliance_level: ComplianceLevel = Field(..., description="Compliance assessment level")
    validation_timestamp: datetime = Field(default_factory=datetime.now)
    tin_validation: TINValidationResult = Field(..., description="TIN validation results")
    tax_calculations: List[VATCalculation] = Field(default_factory=list, description="Tax calculation validations")
    
    # Validation details
    passed_rules: List[str] = Field(default_factory=list, description="Passed validation rules")
    failed_rules: List[str] = Field(default_factory=list, description="Failed validation rules")
    warnings: List[str] = Field(default_factory=list, description="Validation warnings")
    errors: List[str] = Field(default_factory=list, description="Validation errors")
    
    # Compliance metrics
    compliance_score: float = Field(0.0, description="Compliance score (0-100)", ge=0, le=100)
    mandatory_rules_passed: int = Field(0, description="Mandatory rules passed count")
    total_mandatory_rules: int = Field(0, description="Total mandatory rules count")
    
    # Additional information
    recommendations: List[str] = Field(default_factory=list, description="Compliance recommendations")
    next_review_date: Optional[date] = Field(None, description="Next compliance review date")

class EInvoiceSubmission(BaseModel):
    """E-invoice submission model"""
    submission_id: str = Field(..., description="Unique submission identifier")
    invoice_number: str = Field(..., description="Invoice number")
    supplier_tin: str = Field(..., description="Supplier TIN")
    submission_status: SubmissionStatus = Field(..., description="Submission status")
    submission_timestamp: datetime = Field(default_factory=datetime.now)
    acknowledgment_number: Optional[str] = Field(None, description="FIRS acknowledgment number")
    acknowledgment_timestamp: Optional[datetime] = Field(None, description="Acknowledgment timestamp")
    rejection_reason: Optional[str] = Field(None, description="Rejection reason if applicable")
    invoice_data: Dict[str, Any] = Field(..., description="Invoice data payload")

class FIRSComplianceStatus(BaseModel):
    """Overall FIRS compliance status model"""
    entity_tin: str = Field(..., description="Entity TIN")
    entity_name: str = Field(..., description="Entity name")
    compliance_level: ComplianceLevel = Field(..., description="Current compliance level")
    last_assessment_date: datetime = Field(..., description="Last compliance assessment date")
    
    # Compliance history
    total_invoices_submitted: int = Field(0, description="Total invoices submitted", ge=0)
    successful_submissions: int = Field(0, description="Successful submissions count", ge=0)
    rejected_submissions: int = Field(0, description="Rejected submissions count", ge=0)
    pending_submissions: int = Field(0, description="Pending submissions count", ge=0)
    
    # Compliance metrics
    submission_success_rate: float = Field(0.0, description="Submission success rate (%)", ge=0, le=100)
    average_processing_time: Optional[float] = Field(None, description="Average processing time (hours)")
    compliance_score: float = Field(0.0, description="Overall compliance score", ge=0, le=100)
    
    # Risk assessment
    risk_level: str = Field("low", description="Compliance risk level")
    risk_factors: List[str] = Field(default_factory=list, description="Identified risk factors")
    
    # Action items
    required_actions: List[str] = Field(default_factory=list, description="Required compliance actions")
    recommendations: List[str] = Field(default_factory=list, description="Compliance recommendations")

class FIRSBusinessRule(BaseModel):
    """FIRS business rule model"""
    rule_code: str = Field(..., description="Business rule code")
    rule_category: str = Field(..., description="Rule category")
    rule_description: str = Field(..., description="Rule description")
    validation_logic: str = Field(..., description="Validation logic")
    error_message: str = Field(..., description="Error message template")
    is_active: bool = Field(True, description="Rule active status")
    effective_date: date = Field(..., description="Rule effective date")
    expiry_date: Optional[date] = Field(None, description="Rule expiry date")

class TaxOfficeInfo(BaseModel):
    """Nigerian tax office information"""
    office_code: str = Field(..., description="Tax office code")
    office_name: str = Field(..., description="Tax office name")
    state: str = Field(..., description="State location")
    address: str = Field(..., description="Office address")
    phone: Optional[str] = Field(None, description="Contact phone")
    email: Optional[str] = Field(None, description="Contact email")
    jurisdiction_areas: List[str] = Field(default_factory=list, description="Jurisdiction areas")

class FIRSAuditLog(BaseModel):
    """FIRS compliance audit log"""
    log_id: str = Field(..., description="Unique log identifier")
    entity_tin: str = Field(..., description="Entity TIN")
    action_type: str = Field(..., description="Action type")
    action_description: str = Field(..., description="Action description")
    timestamp: datetime = Field(default_factory=datetime.now)
    user_id: Optional[str] = Field(None, description="User identifier")
    ip_address: Optional[str] = Field(None, description="IP address")
    result: str = Field(..., description="Action result")
    additional_data: Optional[Dict[str, Any]] = Field(None, description="Additional audit data")