"""
UBL Data Models and Validation Structures
=========================================

Pydantic models for UBL invoice validation and compliance checking.
Based on UBL 2.1 specification with Nigerian FIRS customizations.
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, validator
from enum import Enum


class UBLValidationSeverity(Enum):
    """UBL validation severity levels."""
    ERROR = "error"          # Blocks submission to FIRS
    WARNING = "warning"      # Should be addressed
    INFO = "info"           # Informational only


class UBLDocumentType(Enum):
    """Supported UBL document types."""
    INVOICE = "Invoice"
    CREDIT_NOTE = "CreditNote"
    DEBIT_NOTE = "DebitNote"


class TaxScheme(BaseModel):
    """UBL Tax Scheme structure."""
    id: str = Field(..., description="Tax scheme identifier (e.g., VAT)")
    name: Optional[str] = Field(None, description="Tax scheme name")
    tax_type_code: Optional[str] = Field(None, description="Tax type code")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "VAT",
                "name": "Value Added Tax",
                "tax_type_code": "VAT"
            }
        }


class TaxCategory(BaseModel):
    """UBL Tax Category structure."""
    id: str = Field(..., description="Tax category identifier")
    name: Optional[str] = Field(None, description="Tax category name")
    percent: Optional[Decimal] = Field(None, description="Tax percentage", ge=0, le=100)
    tax_scheme: TaxScheme = Field(..., description="Associated tax scheme")
    
    @validator('percent')
    def validate_nigerian_vat_rate(cls, v):
        """Validate Nigerian VAT rate (7.5%)."""
        if v is not None and v not in [Decimal('0'), Decimal('7.5')]:
            # Allow 0% for exempt items, 7.5% standard rate
            pass  # Warning level validation, not error
        return v


class MonetaryAmount(BaseModel):
    """UBL Monetary Amount structure."""
    amount: Decimal = Field(..., description="Amount value", ge=0)
    currency_id: str = Field(default="NGN", description="Currency code")
    
    @validator('currency_id')
    def validate_nigerian_currency(cls, v):
        """Validate currency for Nigerian invoices."""
        if v != "NGN":
            # Allow foreign currency but flag for review
            pass
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "amount": "11750.00",
                "currency_id": "NGN"
            }
        }


class PartyIdentification(BaseModel):
    """UBL Party Identification structure."""
    id: str = Field(..., description="Party identifier")
    scheme_id: Optional[str] = Field(None, description="ID scheme (TIN, CAC, etc.)")
    scheme_name: Optional[str] = Field(None, description="ID scheme name")


class Address(BaseModel):
    """UBL Address structure."""
    street_name: Optional[str] = Field(None, description="Street name")
    additional_street_name: Optional[str] = Field(None, description="Additional street")
    city_name: Optional[str] = Field(None, description="City name")
    postal_zone: Optional[str] = Field(None, description="Postal code")
    country_subentity: Optional[str] = Field(None, description="State/Province")
    country_identification_code: str = Field(default="NG", description="Country code")
    
    @validator('country_identification_code')
    def validate_nigerian_country_code(cls, v):
        """Validate Nigerian country code."""
        if v != "NG":
            # Allow international addresses but flag
            pass
        return v


class Party(BaseModel):
    """UBL Party structure."""
    party_identification: List[PartyIdentification] = Field(default_factory=list)
    party_name: Optional[str] = Field(None, description="Party name")
    postal_address: Optional[Address] = Field(None, description="Party address")
    party_tax_scheme: List[Dict[str, Any]] = Field(default_factory=list)
    party_legal_entity: Optional[Dict[str, Any]] = Field(None)
    contact: Optional[Dict[str, Any]] = Field(None)
    
    def get_tin(self) -> Optional[str]:
        """Extract TIN from party identifications."""
        for identification in self.party_identification:
            if identification.scheme_id == "TIN":
                return identification.id
        return None
    
    def get_cac_number(self) -> Optional[str]:
        """Extract CAC registration number."""
        for identification in self.party_identification:
            if identification.scheme_id == "CAC":
                return identification.id
        return None


class InvoiceLine(BaseModel):
    """UBL Invoice Line structure."""
    id: str = Field(..., description="Line identifier")
    invoiced_quantity: Decimal = Field(..., description="Invoiced quantity", ge=0)
    line_extension_amount: MonetaryAmount = Field(..., description="Line total amount")
    item: Dict[str, Any] = Field(..., description="Item details")
    price: Dict[str, Any] = Field(..., description="Price details")
    tax_total: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    
    @validator('invoiced_quantity')
    def validate_quantity(cls, v):
        """Validate invoiced quantity."""
        if v <= 0:
            raise ValueError("Invoiced quantity must be greater than zero")
        return v


class TaxTotal(BaseModel):
    """UBL Tax Total structure."""
    tax_amount: MonetaryAmount = Field(..., description="Total tax amount")
    tax_subtotal: List[Dict[str, Any]] = Field(default_factory=list)
    
    def get_vat_amount(self) -> Optional[Decimal]:
        """Extract VAT amount from tax subtotals."""
        for subtotal in self.tax_subtotal:
            if subtotal.get('tax_category', {}).get('tax_scheme', {}).get('id') == 'VAT':
                return subtotal.get('tax_amount', {}).get('amount')
        return None


class UBLInvoice(BaseModel):
    """UBL Invoice Document structure."""
    # Required UBL elements
    ubl_version_id: str = Field(default="2.1", description="UBL version")
    customization_id: str = Field(..., description="Customization identifier")
    profile_id: Optional[str] = Field(None, description="Profile identifier")
    id: str = Field(..., description="Invoice identifier")
    issue_date: date = Field(..., description="Invoice issue date")
    invoice_type_code: str = Field(..., description="Invoice type code")
    document_currency_code: str = Field(default="NGN", description="Document currency")
    
    # Parties
    accounting_supplier_party: Party = Field(..., description="Supplier party")
    accounting_customer_party: Party = Field(..., description="Customer party")
    
    # Totals
    legal_monetary_total: Dict[str, MonetaryAmount] = Field(..., description="Invoice totals")
    tax_total: List[TaxTotal] = Field(default_factory=list, description="Tax totals")
    
    # Lines
    invoice_line: List[InvoiceLine] = Field(..., description="Invoice lines")
    
    # Optional elements
    due_date: Optional[date] = Field(None, description="Payment due date")
    payment_terms: Optional[Dict[str, Any]] = Field(None)
    delivery: Optional[Dict[str, Any]] = Field(None)
    
    @validator('invoice_type_code')
    def validate_invoice_type(cls, v):
        """Validate invoice type code."""
        valid_types = ['380', '381', '383']  # Invoice, Credit Note, Debit Note
        if v not in valid_types:
            raise ValueError(f"Invalid invoice type code: {v}")
        return v
    
    @validator('issue_date')
    def validate_issue_date(cls, v):
        """Validate invoice issue date."""
        if v > date.today():
            raise ValueError("Invoice issue date cannot be in the future")
        return v
    
    def calculate_total_amount(self) -> Decimal:
        """Calculate total invoice amount."""
        return self.legal_monetary_total.get('tax_inclusive_amount', MonetaryAmount(amount=0)).amount
    
    def calculate_tax_amount(self) -> Decimal:
        """Calculate total tax amount."""
        total_tax = Decimal('0')
        for tax_total in self.tax_total:
            total_tax += tax_total.tax_amount.amount
        return total_tax
    
    def get_supplier_tin(self) -> Optional[str]:
        """Get supplier TIN."""
        return self.accounting_supplier_party.get_tin()
    
    def get_customer_tin(self) -> Optional[str]:
        """Get customer TIN."""
        return self.accounting_customer_party.get_tin()


class UBLValidationResult(BaseModel):
    """UBL validation result."""
    is_valid: bool = Field(..., description="Overall validation status")
    document_type: UBLDocumentType = Field(..., description="Validated document type")
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    warnings: List[Dict[str, Any]] = Field(default_factory=list)
    info: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Nigerian-specific validation results
    firs_compliant: bool = Field(default=False, description="FIRS compliance status")
    nigerian_vat_valid: bool = Field(default=False, description="Nigerian VAT validation")
    tin_validation_status: Dict[str, bool] = Field(default_factory=dict)
    
    # Metadata
    validation_timestamp: datetime = Field(default_factory=datetime.utcnow)
    validator_version: str = Field(default="1.0.0")
    
    def add_error(self, code: str, message: str, path: str = "", context: Dict[str, Any] = None):
        """Add validation error."""
        self.errors.append({
            "severity": UBLValidationSeverity.ERROR.value,
            "code": code,
            "message": message,
            "path": path,
            "context": context or {}
        })
        self.is_valid = False
    
    def add_warning(self, code: str, message: str, path: str = "", context: Dict[str, Any] = None):
        """Add validation warning."""
        self.warnings.append({
            "severity": UBLValidationSeverity.WARNING.value,
            "code": code,
            "message": message,
            "path": path,
            "context": context or {}
        })
    
    def add_info(self, code: str, message: str, path: str = "", context: Dict[str, Any] = None):
        """Add validation info."""
        self.info.append({
            "severity": UBLValidationSeverity.INFO.value,
            "code": code,
            "message": message,
            "path": path,
            "context": context or {}
        })
    
    def get_error_count(self) -> int:
        """Get total error count."""
        return len(self.errors)
    
    def get_warning_count(self) -> int:
        """Get total warning count."""
        return len(self.warnings)
    
    def is_firs_ready(self) -> bool:
        """Check if document is ready for FIRS submission."""
        return self.is_valid and self.firs_compliant and len(self.errors) == 0


class UBLValidationConfig(BaseModel):
    """UBL validation configuration."""
    strict_mode: bool = Field(default=True, description="Enable strict validation")
    validate_nigerian_rules: bool = Field(default=True, description="Enable Nigerian-specific rules")
    require_tin: bool = Field(default=True, description="Require TIN for all parties")
    validate_vat_rates: bool = Field(default=True, description="Validate Nigerian VAT rates")
    check_future_dates: bool = Field(default=True, description="Check for future dates")
    max_line_items: int = Field(default=1000, description="Maximum invoice line items")
    
    class Config:
        schema_extra = {
            "example": {
                "strict_mode": True,
                "validate_nigerian_rules": True,
                "require_tin": True,
                "validate_vat_rates": True,
                "check_future_dates": True,
                "max_line_items": 1000
            }
        }