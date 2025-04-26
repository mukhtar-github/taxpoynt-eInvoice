from enum import Enum
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field # type: ignore
from datetime import date


class ValidationSeverity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class ValidationIssue(BaseModel):
    field: str
    message: str
    severity: ValidationSeverity = ValidationSeverity.ERROR
    code: str


class ValidationResult(BaseModel):
    is_valid: bool
    issues: List[ValidationIssue] = []


class ValidationRule(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    rule_type: str  # schema, business_logic, format
    field_path: Optional[str] = None
    validation_logic: Dict[str, Any]
    error_message: str
    severity: ValidationSeverity = ValidationSeverity.ERROR
    active: bool = True


class PartyAddress(BaseModel):
    tin: str
    email: str
    telephone: str
    business_description: str
    street_name: str
    city_name: str
    postal_zone: Optional[str] = None
    country: str


class Party(BaseModel):
    party_name: str
    postal_address: PartyAddress


class MonetaryTotal(BaseModel):
    line_extension_amount: float
    tax_exclusive_amount: float
    tax_inclusive_amount: float
    payable_amount: float


class ItemIdentification(BaseModel):
    name: str
    description: str
    sellers_item_identification: str


class Price(BaseModel):
    price_amount: float
    base_quantity: int
    price_unit: str


class InvoiceLine(BaseModel):
    hsn_code: str
    product_category: str
    invoiced_quantity: int
    line_extension_amount: float
    item: ItemIdentification
    price: Price


class InvoiceDeliveryPeriod(BaseModel):
    start_date: str
    end_date: str


class DocumentReference(BaseModel):
    irn: str
    issue_date: str


class AllowanceCharge(BaseModel):
    charge_indicator: bool
    amount: float


class TaxCategory(BaseModel):
    id: str
    percent: float


class TaxSubtotal(BaseModel):
    taxable_amount: float
    tax_amount: float
    tax_category: TaxCategory


class TaxTotal(BaseModel):
    tax_amount: float
    tax_subtotal: List[TaxSubtotal]


class PaymentMeans(BaseModel):
    payment_means_code: int
    payment_due_date: str


class Invoice(BaseModel):
    business_id: str
    irn: str
    issue_date: str
    due_date: Optional[str] = None
    issue_time: Optional[str] = None
    invoice_type_code: str
    payment_status: str = "PENDING"
    note: Optional[str] = None
    tax_point_date: Optional[str] = None
    document_currency_code: str
    tax_currency_code: Optional[str] = None
    accounting_cost: Optional[str] = None
    buyer_reference: Optional[str] = None
    invoice_delivery_period: Optional[InvoiceDeliveryPeriod] = None
    order_reference: Optional[str] = None
    billing_reference: Optional[List[DocumentReference]] = None
    dispatch_document_reference: Optional[List[DocumentReference]] = None
    receipt_document_reference: Optional[List[DocumentReference]] = None
    originator_document_reference: Optional[List[DocumentReference]] = None
    contract_document_reference: Optional[List[DocumentReference]] = None
    additional_document_reference: Optional[List[DocumentReference]] = None
    accounting_supplier_party: Party
    accounting_customer_party: Party
    actual_delivery_date: Optional[str] = None
    payment_means: Optional[List[PaymentMeans]] = None
    payment_terms_note: Optional[str] = None
    allowance_charge: Optional[List[AllowanceCharge]] = None
    tax_total: Optional[List[TaxTotal]] = None
    legal_monetary_total: MonetaryTotal
    invoice_line: List[InvoiceLine]


class InvoiceValidationRequest(BaseModel):
    invoice: Invoice


class InvoiceValidationResponse(BaseModel):
    is_valid: bool
    validation_issues: List[ValidationIssue] = []


class BatchValidationRequest(BaseModel):
    invoices: List[Invoice]


class BatchValidationResponse(BaseModel):
    results: List[InvoiceValidationResponse]
    overall_valid: bool 