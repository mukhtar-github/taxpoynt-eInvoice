"""
Invoice validation schemas for BIS Billing 3.0 UBL and FIRS requirements.

This module provides Pydantic models for validating invoice data against
the BIS Billing 3.0 UBL schema and specific Nigerian tax/business rules.
"""
from enum import Enum
from typing import List, Optional, Dict, Any, Union
from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, Field, validator, model_validator, EmailStr, AnyHttpUrl


class CurrencyCode(str, Enum):
    """Currency codes according to ISO 4217"""
    NGN = "NGN"  # Nigerian Naira
    USD = "USD"  # US Dollar
    EUR = "EUR"  # Euro
    GBP = "GBP"  # British Pound
    # Add more as needed


class InvoiceType(str, Enum):
    """Invoice types according to BIS Billing 3.0"""
    COMMERCIAL_INVOICE = "380"  # Commercial invoice
    CREDIT_NOTE = "381"  # Credit note
    DEBIT_NOTE = "383"  # Debit note
    CORRECTED_INVOICE = "384"  # Corrected invoice
    SELF_BILLED_INVOICE = "389"  # Self-billed invoice
    PREPAYMENT_INVOICE = "386"  # Prepayment invoice


class TaxCategory(str, Enum):
    """Tax categories according to BIS Billing 3.0"""
    STANDARD = "S"  # Standard rate
    ZERO = "Z"  # Zero rated goods
    EXEMPT = "E"  # Exempt from tax
    EXPORT = "G"  # Free export item, tax not charged
    VAT_REVERSE_CHARGE = "AE"  # VAT Reverse Charge
    VAT_EXEMPT_FOR_EEA = "L"  # VAT exempt for EEA public bodies
    SERVICE_OUTSIDE_SCOPE = "O"  # Services outside scope of tax
    CANARY_ISLANDS_GENERAL = "K"  # Canary Islands general indirect tax


class UnitCode(str, Enum):
    """Unit codes according to UN/ECE Recommendation 20"""
    PIECE = "EA"  # Each (piece)
    KILOGRAM = "KGM"  # Kilogram
    LITRE = "LTR"  # Litre
    METER = "MTR"  # Meter
    HOUR = "HUR"  # Hour
    DAY = "DAY"  # Day
    WEEK = "WEE"  # Week
    MONTH = "MON"  # Month
    # Add more as needed


class PaymentMeans(str, Enum):
    """Payment means according to BIS Billing 3.0"""
    CREDIT_TRANSFER = "30"  # Credit transfer
    DIRECT_DEBIT = "49"  # Direct debit
    CASH = "10"  # Cash
    CHEQUE = "20"  # Cheque
    BANK_CARD = "48"  # Bank card
    BANK_GIRO = "50"  # Bank giro
    STANDING_ORDER = "56"  # Standing order


class Address(BaseModel):
    """Address according to BIS Billing 3.0"""
    street_name: str = Field(..., min_length=1, max_length=255)
    additional_street_name: Optional[str] = Field(None, max_length=255)
    building_number: Optional[str] = Field(None, max_length=50)
    city_name: str = Field(..., min_length=1, max_length=100)
    postal_zone: Optional[str] = Field(None, max_length=20)
    country_subdivision: Optional[str] = Field(None, max_length=100)
    country_code: str = Field(..., min_length=2, max_length=2, description="ISO 3166-1 alpha-2 country code")

    @validator('country_code')
    def validate_country_code(cls, v):
        """Validate country code is in uppercase"""
        return v.upper()


class PartyIdentification(BaseModel):
    """Party identification according to BIS Billing 3.0"""
    id: str = Field(..., min_length=1, max_length=50)
    scheme_id: Optional[str] = Field(None, max_length=50)


class PartyLegalEntity(BaseModel):
    """Party legal entity according to BIS Billing 3.0"""
    registration_name: str = Field(..., min_length=1, max_length=255)
    company_id: Optional[str] = Field(None, max_length=50, description="Business registration number")
    company_id_scheme_id: Optional[str] = Field(None, max_length=50)
    registration_address: Optional[Address] = None


class Party(BaseModel):
    """Party (supplier or customer) according to BIS Billing 3.0"""
    party_identification: Optional[PartyIdentification] = None
    party_name: str = Field(..., min_length=1, max_length=255)
    postal_address: Address
    party_tax_scheme: Dict[str, str] = Field(..., description="Tax scheme info including VAT ID")
    party_legal_entity: PartyLegalEntity
    contact: Optional[Dict[str, str]] = Field(None, description="Contact information")
    electronic_address: Optional[str] = Field(None, max_length=255, description="Electronic address identifier")


class TaxSubtotal(BaseModel):
    """Tax subtotal according to BIS Billing 3.0"""
    taxable_amount: Decimal = Field(..., ge=0, decimal_places=2)
    tax_amount: Decimal = Field(..., ge=0, decimal_places=2)
    tax_category: TaxCategory
    tax_percent: Decimal = Field(..., ge=0, decimal_places=2)
    tax_exemption_reason: Optional[str] = Field(None, max_length=255)
    tax_exemption_reason_code: Optional[str] = Field(None, max_length=50)

    @model_validator(mode='after')
    def validate_tax_amount(self) -> 'TaxSubtotal':
        """Validate tax amount is calculated correctly"""
        taxable_amount = self.taxable_amount
        tax_percent = self.tax_percent
        tax_amount = self.tax_amount
        
        if all(v is not None for v in [taxable_amount, tax_percent, tax_amount]):
            expected_tax = taxable_amount * (tax_percent / 100)
            # Allow for small rounding differences
            if abs(expected_tax - tax_amount) > 0.01:
                raise ValueError(f"Tax amount {tax_amount} does not match the expected value {expected_tax}")
        
        return self


class TaxTotal(BaseModel):
    """Tax total according to BIS Billing 3.0"""
    tax_amount: Decimal = Field(..., ge=0, decimal_places=2)
    tax_subtotals: List[TaxSubtotal]

    @validator('tax_amount')
    def validate_tax_amount(cls, v, values):
        """Validate tax amount is the sum of subtotals"""
        if 'tax_subtotals' in values and values['tax_subtotals']:
            total_tax = sum(subtotal.tax_amount for subtotal in values['tax_subtotals'])
            if abs(v - total_tax) > 0.01:
                raise ValueError(f"Tax amount {v} does not match the sum of subtotals {total_tax}")
        return v


class InvoiceLine(BaseModel):
    """Invoice line according to BIS Billing 3.0"""
    id: str = Field(..., min_length=1, max_length=50, description="Line identifier")
    invoiced_quantity: Decimal = Field(..., gt=0, description="Quantity")
    unit_code: UnitCode = Field(..., description="Unit of measure")
    line_extension_amount: Decimal = Field(..., ge=0, decimal_places=2, description="Net amount")
    item_description: str = Field(..., min_length=1, max_length=255)
    item_name: str = Field(..., min_length=1, max_length=100)
    price_amount: Decimal = Field(..., gt=0, decimal_places=2, description="Unit price")
    base_quantity: Optional[Decimal] = Field(1, gt=0, description="Base quantity")
    buyers_item_identification: Optional[str] = Field(None, max_length=50, description="Buyer's item identifier")
    sellers_item_identification: Optional[str] = Field(None, max_length=50, description="Seller's item identifier")
    standard_item_identification: Optional[Dict[str, str]] = Field(None, description="Standard item identifier")
    tax_total: Optional[TaxTotal] = Field(None, description="Tax information for the line")
    allowance_charge: Optional[List[Dict[str, Any]]] = Field(None, description="Allowances or charges")

    @model_validator(mode='after')
    def validate_line_amount(self) -> 'InvoiceLine':
        """Validate line extension amount is calculated correctly"""
        quantity = self.invoiced_quantity
        price = self.price_amount
        base_qty = self.base_quantity if self.base_quantity is not None else 1
        line_amount = self.line_extension_amount
        
        if all(v is not None for v in [quantity, price, line_amount]):
            expected_amount = (quantity * price) / base_qty
            # Allow for small rounding differences
            if abs(expected_amount - line_amount) > 0.01:
                raise ValueError(f"Line amount {line_amount} does not match the expected value {expected_amount}")
        
        return self


class AllowanceCharge(BaseModel):
    """Allowance or charge according to BIS Billing 3.0"""
    charge_indicator: bool = Field(..., description="True for charge, False for allowance")
    allowance_charge_reason: str = Field(..., min_length=1, max_length=255)
    amount: Decimal = Field(..., gt=0, decimal_places=2)
    base_amount: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    tax_category: Optional[TaxCategory] = None
    tax_percent: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    reason_code: Optional[str] = Field(None, max_length=50)


class PaymentTerms(BaseModel):
    """Payment terms according to BIS Billing 3.0"""
    note: str = Field(..., min_length=1, max_length=500, description="Payment term description")
    payment_due_date: Optional[date] = Field(None, description="Due date for payment")
    payment_means: Optional[PaymentMeans] = None
    payment_id: Optional[str] = Field(None, max_length=50, description="Payment reference")
    payment_percent: Optional[Decimal] = Field(None, ge=0, le=100, decimal_places=2)


class LegalMonetaryTotal(BaseModel):
    """Legal monetary total according to BIS Billing 3.0"""
    line_extension_amount: Decimal = Field(..., ge=0, decimal_places=2, description="Sum of invoice line net amounts")
    tax_exclusive_amount: Decimal = Field(..., ge=0, decimal_places=2, description="Total amount without tax")
    tax_inclusive_amount: Decimal = Field(..., ge=0, decimal_places=2, description="Total amount with tax")
    allowance_total_amount: Optional[Decimal] = Field(0, ge=0, decimal_places=2, description="Sum of allowances on document level")
    charge_total_amount: Optional[Decimal] = Field(0, ge=0, decimal_places=2, description="Sum of charges on document level")
    prepaid_amount: Optional[Decimal] = Field(0, ge=0, decimal_places=2, description="Amount prepaid")
    payable_amount: Decimal = Field(..., ge=0, decimal_places=2, description="Amount due for payment")

    @model_validator(mode='after')
    def validate_amounts(self) -> 'LegalMonetaryTotal':
        """Validate the monetary totals are consistent"""
        line_extension = self.line_extension_amount
        allowance_total = self.allowance_total_amount if self.allowance_total_amount is not None else 0
        charge_total = self.charge_total_amount if self.charge_total_amount is not None else 0
        tax_exclusive = self.tax_exclusive_amount
        prepaid = self.prepaid_amount if self.prepaid_amount is not None else 0
        payable = self.payable_amount
        tax_inclusive = self.tax_inclusive_amount
        
        # Validate tax_exclusive_amount
        expected_tax_exclusive = line_extension - allowance_total + charge_total
        if abs(expected_tax_exclusive - tax_exclusive) > 0.01:
            raise ValueError(f"Tax exclusive amount {tax_exclusive} does not match the expected value {expected_tax_exclusive}")
        
        # Validate payable_amount
        expected_payable = tax_inclusive - prepaid
        if abs(expected_payable - payable) > 0.01:
            raise ValueError(f"Payable amount {payable} does not match the expected value {expected_payable}")
        
        return self


class InvoiceValidationRequest(BaseModel):
    """Invoice validation request schema"""
    invoice_number: str = Field(..., min_length=1, max_length=50, description="Invoice identifier")
    invoice_type_code: InvoiceType = Field(..., description="Type of invoice")
    invoice_date: date = Field(..., description="Invoice issue date")
    due_date: Optional[date] = Field(None, description="Payment due date")
    tax_point_date: Optional[date] = Field(None, description="Tax point date/time")
    currency_code: CurrencyCode = Field(..., description="Invoice currency")
    accounting_supplier_party: Party = Field(..., description="Seller information")
    accounting_customer_party: Party = Field(..., description="Buyer information")
    invoice_lines: List[InvoiceLine] = Field(..., min_items=1, description="Invoice line items")
    allowance_charges: Optional[List[AllowanceCharge]] = Field(None, description="Document level allowances and charges")
    tax_total: TaxTotal = Field(..., description="Tax totals")
    legal_monetary_total: LegalMonetaryTotal = Field(..., description="Invoice totals")
    payment_terms: Optional[PaymentTerms] = Field(None, description="Payment terms")
    payment_means: Optional[PaymentMeans] = Field(None, description="Payment method")
    delivery_date: Optional[date] = Field(None, description="Actual delivery date")
    note: Optional[str] = Field(None, max_length=500, description="Invoice note")
    order_reference: Optional[str] = Field(None, max_length=50, description="Purchase order reference")
    contract_document_reference: Optional[str] = Field(None, max_length=50, description="Contract reference")
    additional_document_references: Optional[List[Dict[str, str]]] = Field(None, description="References to supporting documents")
    
    @validator('due_date')
    def validate_due_date(cls, v, values):
        """Validate due date is after or on invoice date"""
        invoice_date = values.get('invoice_date')
        if v and invoice_date and v < invoice_date:
            raise ValueError("Due date cannot be before invoice date")
        return v
    
    @model_validator(mode='after')
    def validate_totals(self) -> 'InvoiceValidationRequest':
        """Validate that invoice line totals match document totals"""
        invoice_lines = self.invoice_lines
        legal_monetary_total = self.legal_monetary_total
        
        if invoice_lines and legal_monetary_total:
            line_sum = sum(line.line_extension_amount for line in invoice_lines)
            if abs(line_sum - legal_monetary_total.line_extension_amount) > 0.01:
                raise ValueError(f"Sum of invoice lines ({line_sum}) does not match the document total ({legal_monetary_total.line_extension_amount})")
        
        return self


class ValidationError(BaseModel):
    """Validation error response schema"""
    field: str = Field(..., description="Field path with error")
    error: str = Field(..., description="Error description")
    error_code: Optional[str] = Field(None, description="Error code for reference")


class InvoiceValidationResponse(BaseModel):
    """Invoice validation response schema"""
    valid: bool = Field(..., description="Overall validation result")
    invoice_number: str = Field(..., description="Invoice number that was validated")
    validation_timestamp: datetime = Field(default_factory=datetime.utcnow, description="When validation was performed")
    errors: List[ValidationError] = Field(default_factory=list, description="Validation errors if any")
    warnings: List[ValidationError] = Field(default_factory=list, description="Validation warnings if any")
    schema_version: str = Field("BIS Billing 3.0", description="Schema version used for validation")


class BatchValidationRequest(BaseModel):
    """Batch invoice validation request schema"""
    invoices: List[InvoiceValidationRequest] = Field(..., min_items=1, max_items=100, description="List of invoices to validate")


class BatchValidationResponse(BaseModel):
    """Batch invoice validation response schema"""
    total_count: int = Field(..., description="Total number of invoices processed")
    valid_count: int = Field(..., description="Number of valid invoices")
    invalid_count: int = Field(..., description="Number of invalid invoices")
    validation_timestamp: datetime = Field(default_factory=datetime.utcnow, description="When validation was performed")
    results: List[InvoiceValidationResponse] = Field(..., description="Individual validation results")


class ValidationRule(BaseModel):
    """Validation rule schema"""
    id: str = Field(..., description="Rule identifier")
    name: str = Field(..., description="Rule name")
    description: str = Field(..., description="Rule description")
    severity: str = Field(..., description="Rule severity (error, warning)")
    category: str = Field(..., description="Rule category")
    field_path: Optional[str] = Field(None, description="Field path this rule applies to")
    source: str = Field(..., description="Rule source (FIRS, BIS3, custom)")


class ValidationRulesList(BaseModel):
    """List of validation rules"""
    rules: List[ValidationRule] = Field(..., description="List of validation rules")
    count: int = Field(..., description="Total number of rules")
