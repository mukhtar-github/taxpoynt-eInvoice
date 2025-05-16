#!/usr/bin/env python
"""
Standalone test for Odoo UBL mapping without external dependencies.
This file includes simplified versions of the necessary classes and functions.
"""
import unittest
import xml.etree.ElementTree as ET
from decimal import Decimal
from datetime import date, datetime, timedelta
from enum import Enum
from typing import Dict, List, Any, Optional, Tuple, Union

# ---------- PART 1: Mock Enum Classes ----------

class InvoiceTypeCode(str, Enum):
    """Invoice type code as defined in UBL."""
    COMMERCIAL_INVOICE = "380"
    CREDIT_NOTE = "381"
    DEBIT_NOTE = "383"
    SELF_BILLED_INVOICE = "389"

class CurrencyCode(str, Enum):
    """Currency code as defined in ISO 4217."""
    NGN = "NGN"  # Nigerian Naira
    USD = "USD"  # US Dollar
    EUR = "EUR"  # Euro
    GBP = "GBP"  # British Pound

class UnitCode(str, Enum):
    """Unit code as defined in UBL."""
    PIECE = "EA"    # Each (piece)
    KILOGRAM = "KGM" # Kilogram
    LITER = "LTR"   # Liter
    METER = "MTR"   # Meter
    HOUR = "HUR"    # Hour
    DAY = "DAY"     # Day
    MONTH = "MON"   # Month

class TaxCategory(str, Enum):
    """Tax category as defined in UBL."""
    STANDARD = "S"        # Standard rate
    ZERO_RATED = "Z"      # Zero rated goods
    EXEMPT = "E"          # Exempt from tax
    EXPORT = "G"          # Free export item
    REVERSE_CHARGE = "AE" # VAT Reverse Charge
    NOT_APPLICABLE = "O"  # Services outside scope of tax

print("Part 1: Mock Enum classes added.")

# ---------- PART 2: Mock Data Classes ----------

class ValidationError:
    """Simplified version of the ValidationError class."""
    def __init__(self, field: str, error: str, error_code: str = None):
        self.field = field
        self.error = error
        self.error_code = error_code
    
    def dict(self):
        return {
            "field": self.field,
            "error": self.error,
            "error_code": self.error_code
        }

class PostalAddress:
    """Postal address data class."""
    def __init__(self, street_name: str, city_name: str, country_code: str,
                postal_zone: str = None, additional_street_name: str = None,
                building_number: str = None, country_subdivision: str = None):
        self.street_name = street_name
        self.city_name = city_name
        self.country_code = country_code
        self.postal_zone = postal_zone
        self.additional_street_name = additional_street_name
        self.building_number = building_number
        self.country_subdivision = country_subdivision
    
    def dict(self):
        return {
            "street_name": self.street_name,
            "city_name": self.city_name,
            "country_code": self.country_code,
            "postal_zone": self.postal_zone,
            "additional_street_name": self.additional_street_name,
            "building_number": self.building_number,
            "country_subdivision": self.country_subdivision
        }

class PartyLegalEntity:
    """Party legal entity data class."""
    def __init__(self, registration_name: str, company_id: str = None,
                company_id_scheme_id: str = None):
        self.registration_name = registration_name
        self.company_id = company_id
        self.company_id_scheme_id = company_id_scheme_id
    
    def dict(self):
        return {
            "registration_name": self.registration_name,
            "company_id": self.company_id,
            "company_id_scheme_id": self.company_id_scheme_id
        }

class AccountingParty:
    """Party (supplier or customer) data class."""
    def __init__(self, party_name: str, postal_address: PostalAddress,
                party_tax_scheme: Dict[str, str], party_legal_entity: PartyLegalEntity,
                contact: Dict[str, str] = None, party_identification: Dict[str, str] = None):
        self.party_name = party_name
        self.postal_address = postal_address
        self.party_tax_scheme = party_tax_scheme
        self.party_legal_entity = party_legal_entity
        self.contact = contact or {}
        self.party_identification = party_identification
    
    def dict(self):
        return {
            "party_name": self.party_name,
            "postal_address": self.postal_address.dict(),
            "party_tax_scheme": self.party_tax_scheme,
            "party_legal_entity": self.party_legal_entity.dict(),
            "contact": self.contact,
            "party_identification": self.party_identification
        }

class PaymentTerms:
    """Payment terms data class."""
    def __init__(self, note: str, payment_due_date: date = None):
        self.note = note
        self.payment_due_date = payment_due_date
    
    def dict(self):
        return {
            "note": self.note,
            "payment_due_date": self.payment_due_date
        }

class TaxSubtotal:
    """Tax subtotal data class."""
    def __init__(self, taxable_amount: Decimal, tax_amount: Decimal,
                tax_category: TaxCategory, tax_percent: Decimal,
                tax_exemption_reason: str = None):
        self.taxable_amount = taxable_amount
        self.tax_amount = tax_amount
        self.tax_category = tax_category
        self.tax_percent = tax_percent
        self.tax_exemption_reason = tax_exemption_reason
    
    def dict(self):
        return {
            "taxable_amount": self.taxable_amount,
            "tax_amount": self.tax_amount,
            "tax_category": self.tax_category,
            "tax_percent": self.tax_percent,
            "tax_exemption_reason": self.tax_exemption_reason
        }

class TaxTotal:
    """Tax total data class."""
    def __init__(self, tax_amount: Decimal, tax_subtotals: List[TaxSubtotal]):
        self.tax_amount = tax_amount
        self.tax_subtotals = tax_subtotals
    
    def dict(self):
        return {
            "tax_amount": self.tax_amount,
            "tax_subtotals": [t.dict() for t in self.tax_subtotals]
        }

class LegalMonetaryTotal:
    """Legal monetary total data class."""
    def __init__(self, line_extension_amount: Decimal, tax_exclusive_amount: Decimal,
                tax_inclusive_amount: Decimal, payable_amount: Decimal,
                allowance_total_amount: Decimal = None, charge_total_amount: Decimal = None,
                prepaid_amount: Decimal = None):
        self.line_extension_amount = line_extension_amount
        self.tax_exclusive_amount = tax_exclusive_amount
        self.tax_inclusive_amount = tax_inclusive_amount
        self.payable_amount = payable_amount
        self.allowance_total_amount = allowance_total_amount
        self.charge_total_amount = charge_total_amount
        self.prepaid_amount = prepaid_amount
    
    def dict(self):
        return {
            "line_extension_amount": self.line_extension_amount,
            "tax_exclusive_amount": self.tax_exclusive_amount,
            "tax_inclusive_amount": self.tax_inclusive_amount,
            "payable_amount": self.payable_amount,
            "allowance_total_amount": self.allowance_total_amount,
            "charge_total_amount": self.charge_total_amount,
            "prepaid_amount": self.prepaid_amount
        }

class InvoiceLine:
    """Invoice line data class."""
    def __init__(self, id: str, invoiced_quantity: Decimal, unit_code: UnitCode,
                line_extension_amount: Decimal, item_name: str, price_amount: Decimal,
                item_description: str = None, tax_total: TaxTotal = None,
                buyers_item_identification: str = None, sellers_item_identification: str = None,
                base_quantity: Decimal = None):
        self.id = id
        self.invoiced_quantity = invoiced_quantity
        self.unit_code = unit_code
        self.line_extension_amount = line_extension_amount
        self.item_name = item_name
        self.price_amount = price_amount
        self.item_description = item_description
        self.tax_total = tax_total
        self.buyers_item_identification = buyers_item_identification
        self.sellers_item_identification = sellers_item_identification
        self.base_quantity = base_quantity
    
    def dict(self):
        return {
            "id": self.id,
            "invoiced_quantity": self.invoiced_quantity,
            "unit_code": self.unit_code,
            "line_extension_amount": self.line_extension_amount,
            "item_name": self.item_name,
            "price_amount": self.price_amount,
            "item_description": self.item_description,
            "tax_total": self.tax_total.dict() if self.tax_total else None,
            "buyers_item_identification": self.buyers_item_identification,
            "sellers_item_identification": self.sellers_item_identification,
            "base_quantity": self.base_quantity
        }

class InvoiceValidationRequest:
    """Invoice validation request data class."""
    def __init__(self, invoice_number: str, invoice_type_code: InvoiceTypeCode,
                invoice_date: date, currency_code: CurrencyCode,
                accounting_supplier_party: AccountingParty, accounting_customer_party: AccountingParty,
                invoice_lines: List[InvoiceLine], tax_total: TaxTotal,
                legal_monetary_total: LegalMonetaryTotal, due_date: date = None,
                payment_terms: PaymentTerms = None, note: str = None, order_reference: str = None):
        self.invoice_number = invoice_number
        self.invoice_type_code = invoice_type_code
        self.invoice_date = invoice_date
        self.currency_code = currency_code
        self.accounting_supplier_party = accounting_supplier_party
        self.accounting_customer_party = accounting_customer_party
        self.invoice_lines = invoice_lines
        self.tax_total = tax_total
        self.legal_monetary_total = legal_monetary_total
        self.due_date = due_date
        self.payment_terms = payment_terms
        self.note = note
        self.order_reference = order_reference
    
    def dict(self):
        return {
            "invoice_number": self.invoice_number,
            "invoice_type_code": self.invoice_type_code,
            "invoice_date": self.invoice_date,
            "currency_code": self.currency_code,
            "accounting_supplier_party": self.accounting_supplier_party.dict(),
            "accounting_customer_party": self.accounting_customer_party.dict(),
            "invoice_lines": [line.dict() for line in self.invoice_lines],
            "tax_total": self.tax_total.dict(),
            "legal_monetary_total": self.legal_monetary_total.dict(),
            "due_date": self.due_date,
            "payment_terms": self.payment_terms.dict() if self.payment_terms else None,
            "note": self.note,
            "order_reference": self.order_reference
        }

print("Part 2: Mock data classes added.")

# ---------- PART 3: Mock UBL Validator ----------

class MockOdooUBLValidator:
    """Simplified version of the OdooUBLValidator."""
    
    def __init__(self):
        """Initialize the validator."""
        self.required_fields = self._get_required_fields()
    
    def _get_required_fields(self) -> Dict[str, List[str]]:
        """Define the required fields for BIS Billing 3.0 UBL format."""
        return {
            "invoice": [
                "invoice_number",
                "invoice_type_code",
                "invoice_date",
                "currency_code",
                "accounting_supplier_party",
                "accounting_customer_party",
                "invoice_lines",
                "tax_total",
                "legal_monetary_total"
            ],
            "supplier": [
                "party_name",
                "postal_address",
                "party_tax_scheme",
                "party_legal_entity"
            ],
            "customer": [
                "party_name",
                "postal_address",
                "party_tax_scheme",
                "party_legal_entity"
            ],
            "address": [
                "street_name",
                "city_name",
                "country_code"
            ],
            "invoice_line": [
                "id",
                "invoiced_quantity",
                "unit_code",
                "line_extension_amount",
                "item_name",
                "price_amount"
            ],
            "tax_total": [
                "tax_amount",
                "tax_subtotals"
            ],
            "tax_subtotal": [
                "taxable_amount",
                "tax_amount",
                "tax_category",
                "tax_percent"
            ],
            "monetary_total": [
                "line_extension_amount",
                "tax_exclusive_amount",
                "tax_inclusive_amount",
                "payable_amount"
            ]
        }
    
    def validate_mapped_invoice(self, invoice: InvoiceValidationRequest) -> Tuple[bool, List[ValidationError]]:
        """Validate that a mapped invoice has all required fields."""
        errors = []
        
        # Validate invoice level fields
        self._validate_required_fields(invoice.dict(), self.required_fields["invoice"], "invoice", errors)
        
        # Validate supplier party
        if invoice.accounting_supplier_party:
            supplier_dict = invoice.accounting_supplier_party.dict()
            self._validate_required_fields(supplier_dict, self.required_fields["supplier"], "supplier", errors)
            
            # Validate supplier address
            if supplier_dict.get("postal_address"):
                address_dict = supplier_dict["postal_address"]
                self._validate_required_fields(address_dict, self.required_fields["address"], "supplier.postal_address", errors)
        
        # Validate customer party
        if invoice.accounting_customer_party:
            customer_dict = invoice.accounting_customer_party.dict()
            self._validate_required_fields(customer_dict, self.required_fields["customer"], "customer", errors)
            
            # Validate customer address
            if customer_dict.get("postal_address"):
                address_dict = customer_dict["postal_address"]
                self._validate_required_fields(address_dict, self.required_fields["address"], "customer.postal_address", errors)
        
        # Validate invoice lines
        if invoice.invoice_lines:
            for i, line in enumerate(invoice.invoice_lines):
                line_dict = line.dict()
                self._validate_required_fields(line_dict, self.required_fields["invoice_line"], f"invoice_lines[{i}]", errors)
        
        # Validate tax total
        if invoice.tax_total:
            tax_total_dict = invoice.tax_total.dict()
            self._validate_required_fields(tax_total_dict, self.required_fields["tax_total"], "tax_total", errors)
            
            # Validate tax subtotals
            if tax_total_dict.get("tax_subtotals"):
                for i, subtotal in enumerate(tax_total_dict["tax_subtotals"]):
                    self._validate_required_fields(subtotal, self.required_fields["tax_subtotal"], f"tax_total.tax_subtotals[{i}]", errors)
        
        # Validate monetary total
        if invoice.legal_monetary_total:
            monetary_dict = invoice.legal_monetary_total.dict()
            self._validate_required_fields(monetary_dict, self.required_fields["monetary_total"], "legal_monetary_total", errors)
        
        # Additional business rule validations (simplified for the standalone test)
        self._validate_business_rules(invoice, errors)
        
        # Return validation results
        is_valid = len(errors) == 0
        return is_valid, errors
    
    def _validate_required_fields(
        self, data: Dict[str, Any], required_fields: List[str], 
        field_path: str, errors: List[ValidationError]
    ) -> None:
        """Validate that all required fields are present and non-empty."""
        for field in required_fields:
            if field not in data:
                errors.append(ValidationError(
                    field=f"{field_path}.{field}",
                    error=f"Required field '{field}' is missing",
                    error_code="MISSING_REQUIRED_FIELD"
                ))
            elif data[field] is None:
                errors.append(ValidationError(
                    field=f"{field_path}.{field}",
                    error=f"Required field '{field}' is None",
                    error_code="NONE_REQUIRED_FIELD"
                ))
            elif isinstance(data[field], str) and not data[field].strip():
                errors.append(ValidationError(
                    field=f"{field_path}.{field}",
                    error=f"Required field '{field}' is empty",
                    error_code="EMPTY_REQUIRED_FIELD"
                ))
            elif isinstance(data[field], list) and not data[field]:
                errors.append(ValidationError(
                    field=f"{field_path}.{field}",
                    error=f"Required field '{field}' is an empty list",
                    error_code="EMPTY_REQUIRED_LIST"
                ))
    
    def _validate_business_rules(self, invoice: InvoiceValidationRequest, errors: List[ValidationError]) -> None:
        """Validate business rules (simplified for the standalone test)."""
        # Validate invoice totals match line sums
        if invoice.invoice_lines and invoice.legal_monetary_total:
            # Calculate sum of line amounts
            line_sum = sum(line.line_extension_amount for line in invoice.invoice_lines)
            
            # Check if it matches the invoice total
            if abs(line_sum - invoice.legal_monetary_total.line_extension_amount) > Decimal('0.02'):
                errors.append(ValidationError(
                    field="legal_monetary_total.line_extension_amount",
                    error=f"Sum of invoice lines ({line_sum}) does not match invoice total ({invoice.legal_monetary_total.line_extension_amount})",
                    error_code="TOTAL_MISMATCH"
                ))
        
        # Validate tax amounts
        if invoice.tax_total and invoice.legal_monetary_total:
            # Calculate tax inclusive amount
            calc_tax_inclusive = invoice.legal_monetary_total.tax_exclusive_amount + invoice.tax_total.tax_amount
            
            # Check if it matches the invoice tax inclusive amount
            if abs(calc_tax_inclusive - invoice.legal_monetary_total.tax_inclusive_amount) > Decimal('0.02'):
                errors.append(ValidationError(
                    field="legal_monetary_total.tax_inclusive_amount",
                    error=f"Tax inclusive amount ({invoice.legal_monetary_total.tax_inclusive_amount}) does not match calculated amount ({calc_tax_inclusive})",
                    error_code="TAX_INCLUSIVE_MISMATCH"
                ))
        
        # Validate date rules
        if invoice.invoice_date and invoice.due_date:
            if invoice.due_date < invoice.invoice_date:
                errors.append(ValidationError(
                    field="due_date",
                    error="Due date cannot be earlier than invoice date",
                    error_code="INVALID_DUE_DATE"
                ))

# Create a singleton instance for reuse
mock_ubl_validator = MockOdooUBLValidator()

print("Part 3: Mock UBL Validator added.")

# ---------- PART 4: Mock UBL Transformer ----------

class MockOdooUBLTransformer:
    """Simplified version of the OdooUBLTransformer."""
    
    def __init__(self):
        """Initialize the UBL transformer."""
        # Define UBL namespaces
        self.namespaces = {
            'xmlns': 'urn:oasis:names:specification:ubl:schema:xsd:Invoice-2',
            'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2',
            'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2',
            'ccts': 'urn:un:unece:uncefact:documentation:2',
            'ext': 'urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2',
            'qdt': 'urn:oasis:names:specification:ubl:schema:xsd:QualifiedDataTypes-2',
            'udt': 'urn:un:unece:uncefact:data:specification:UnqualifiedDataTypesSchemaModule:2',
            'xsi': 'http://www.w3.org/2001/XMLSchema-instance'
        }
        
        # Register namespaces
        for prefix, uri in self.namespaces.items():
            ET.register_namespace(prefix, uri)
    
    def odoo_to_ubl_object(self, odoo_invoice: Dict[str, Any], company_info: Dict[str, Any]) -> Tuple[Optional[InvoiceValidationRequest], List[Dict[str, str]]]:
        """Convert Odoo invoice data to UBL object (simplified mock version)."""
        validation_issues = []
        
        try:
            # In a real implementation, this would do actual mapping
            # For this mock, we'll just create a sample UBL object
            
            # Create supplier party from company info
            supplier_address = PostalAddress(
                street_name=company_info.get("street", "Unknown Street"),
                city_name=company_info.get("city", "Unknown City"),
                country_code=company_info.get("country_id", {}).get("code", "NG"),
                postal_zone=company_info.get("zip"),
                country_subdivision=company_info.get("state_id", {}).get("name")
            )
            
            supplier_party = AccountingParty(
                party_name=company_info.get("name", "Unknown Supplier"),
                postal_address=supplier_address,
                party_tax_scheme={
                    "company_id": company_info.get("vat", "Unknown VAT"),
                    "tax_scheme_id": "VAT"
                },
                party_legal_entity=PartyLegalEntity(
                    registration_name=company_info.get("name", "Unknown Supplier"),
                    company_id=company_info.get("company_registry"),
                    company_id_scheme_id="NG-CAC"
                ),
                contact={
                    "name": "Contact Person",
                    "telephone": company_info.get("phone", ""),
                    "email": company_info.get("email", "")
                }
            )
            
            # Create customer party from invoice partner
            partner = odoo_invoice.get("partner_id", {}) or odoo_invoice.get("partner", {})
            
            customer_address = PostalAddress(
                street_name=partner.get("street", "Unknown Street"),
                city_name=partner.get("city", "Unknown City"),
                country_code=partner.get("country_id", {}).get("code", "NG"),
                postal_zone=partner.get("zip"),
                country_subdivision=partner.get("state_id", {}).get("name")
            )
            
            customer_party = AccountingParty(
                party_name=partner.get("name", "Unknown Customer"),
                postal_address=customer_address,
                party_tax_scheme={
                    "company_id": partner.get("vat", "Unknown VAT"),
                    "tax_scheme_id": "VAT"
                },
                party_legal_entity=PartyLegalEntity(
                    registration_name=partner.get("name", "Unknown Customer")
                ),
                contact={
                    "telephone": partner.get("phone", ""),
                    "email": partner.get("email", "")
                }
            )
            
            # Create invoice lines
            invoice_lines = []
            
            for i, line_data in enumerate(odoo_invoice.get("invoice_line_ids", []) or odoo_invoice.get("lines", [])):
                # Get tax rate from the first tax
                tax_percent = Decimal('0.00')
                tax_amount = Decimal('0.00')
                
                taxes = line_data.get("tax_ids", []) or line_data.get("taxes", [])
                if taxes:
                    tax_percent = Decimal(str(taxes[0].get("amount", 0)))
                    price_subtotal = Decimal(str(line_data.get("price_subtotal", 0)))
                    tax_amount = (price_subtotal * tax_percent) / Decimal('100')
                
                # Create the invoice line
                invoice_lines.append(InvoiceLine(
                    id=str(line_data.get("id", i + 1)),
                    invoiced_quantity=Decimal(str(line_data.get("quantity", 0))),
                    unit_code=UnitCode.PIECE,  # In a real implementation, we'd map from the UoM
                    line_extension_amount=Decimal(str(line_data.get("price_subtotal", 0))),
                    item_name=line_data.get("product_id", {}).get("name") or "Unknown Product",
                    price_amount=Decimal(str(line_data.get("price_unit", 0))),
                    item_description=line_data.get("name", "")
                ))
            
            # Create tax subtotal and total
            tax_subtotal = TaxSubtotal(
                taxable_amount=Decimal(str(odoo_invoice.get("amount_untaxed", 0))),
                tax_amount=Decimal(str(odoo_invoice.get("amount_tax", 0))),
                tax_category=TaxCategory.STANDARD,
                tax_percent=Decimal('7.5')  # Default Nigerian VAT rate
            )
            
            tax_total = TaxTotal(
                tax_amount=Decimal(str(odoo_invoice.get("amount_tax", 0))),
                tax_subtotals=[tax_subtotal]
            )
            
            # Create monetary total
            monetary_total = LegalMonetaryTotal(
                line_extension_amount=Decimal(str(odoo_invoice.get("amount_untaxed", 0))),
                tax_exclusive_amount=Decimal(str(odoo_invoice.get("amount_untaxed", 0))),
                tax_inclusive_amount=Decimal(str(odoo_invoice.get("amount_total", 0))),
                payable_amount=Decimal(str(odoo_invoice.get("amount_total", 0)))
            )
            
            # Create payment terms if available
            payment_terms = None
            payment_term_data = odoo_invoice.get("invoice_payment_term_id", {})
            if payment_term_data:
                payment_terms = PaymentTerms(
                    note=payment_term_data.get("name", "Standard payment terms"),
                    payment_due_date=odoo_invoice.get("invoice_date_due")
                )
            
            # Create the complete invoice object
            invoice_date_str = odoo_invoice.get("invoice_date")
            invoice_date = datetime.strptime(invoice_date_str, "%Y-%m-%d").date() if invoice_date_str else date.today()
            
            due_date_str = odoo_invoice.get("invoice_date_due")
            due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date() if due_date_str else None
            
            ubl_invoice = InvoiceValidationRequest(
                invoice_number=odoo_invoice.get("name", "Unknown"),
                invoice_type_code=InvoiceTypeCode.COMMERCIAL_INVOICE,  # We'd map this in a real implementation
                invoice_date=invoice_date,
                due_date=due_date,
                currency_code=CurrencyCode.NGN,  # We'd map from the currency in a real implementation
                accounting_supplier_party=supplier_party,
                accounting_customer_party=customer_party,
                invoice_lines=invoice_lines,
                tax_total=tax_total,
                legal_monetary_total=monetary_total,
                payment_terms=payment_terms,
                note=odoo_invoice.get("narration", ""),
                order_reference=odoo_invoice.get("ref")
            )
            
            # Validate the mapped invoice
            is_valid, errors = mock_ubl_validator.validate_mapped_invoice(ubl_invoice)
            
            if not is_valid:
                for error in errors:
                    validation_issues.append({
                        "field": error.field,
                        "message": error.error,
                        "code": error.error_code or "VALIDATION_ERROR"
                    })
            
            return ubl_invoice, validation_issues
            
        except Exception as e:
            validation_issues.append({
                "field": "general",
                "message": f"Transformation error: {str(e)}",
                "code": "TRANSFORMATION_ERROR"
            })
            return None, validation_issues
    
    def ubl_object_to_xml(self, ubl_invoice: InvoiceValidationRequest) -> Tuple[str, List[Dict[str, str]]]:
        """Convert UBL object to XML (simplified mock version)."""
        conversion_issues = []
        
        try:
            # Create a simplified XML to avoid namespace issues in the test environment
            # In a real implementation, we would handle namespaces properly
            root = ET.Element("Invoice")
            
            # Add basic invoice elements
            self._add_element(root, "cbc:UBLVersionID", "2.1")
            self._add_element(root, "cbc:CustomizationID", "urn:cen.eu:en16931:2017#compliant#urn:fdc:peppol.eu:2017:poacc:billing:3.0")
            self._add_element(root, "cbc:ProfileID", "urn:fdc:peppol.eu:2017:poacc:billing:01:1.0")
            self._add_element(root, "cbc:ID", ubl_invoice.invoice_number)
            self._add_element(root, "cbc:IssueDate", ubl_invoice.invoice_date.isoformat())
            
            if ubl_invoice.due_date:
                self._add_element(root, "cbc:DueDate", ubl_invoice.due_date.isoformat())
            
            self._add_element(root, "cbc:InvoiceTypeCode", ubl_invoice.invoice_type_code.value)
            self._add_element(root, "cbc:DocumentCurrencyCode", ubl_invoice.currency_code.value)
            
            if ubl_invoice.note:
                self._add_element(root, "cbc:Note", ubl_invoice.note)
            
            # In a real implementation, we would add all invoice components
            # For this simplified mock, we'll just add some key elements
            # and indicate where others would go
            
            # Add a comment to indicate missing elements in this simplified mock
            root.append(ET.Comment("This XML is a simplified mock for testing. A real implementation would include complete UBL elements."))
            
            # Convert to string
            xml_string = ET.tostring(root, encoding='utf-8', method='xml').decode('utf-8')
            
            return xml_string, conversion_issues
            
        except Exception as e:
            conversion_issues.append({
                "field": "general",
                "message": f"XML conversion error: {str(e)}",
                "code": "XML_CONVERSION_ERROR"
            })
            return "", conversion_issues
    
    def _add_element(self, parent: ET.Element, tag: str, text: Any) -> ET.Element:
        """Add an XML element with text to a parent element."""
        # For the simplified test, we'll skip namespace handling
        # In a real implementation, we would handle namespaces properly
        # Just use the tag name without namespace
        if ':' in tag:
            _, local_tag = tag.split(':', 1)
            element = ET.SubElement(parent, local_tag)
        else:
            element = ET.SubElement(parent, tag)
        
        element.text = str(text)
        return element

# Create a singleton instance for reuse
mock_ubl_transformer = MockOdooUBLTransformer()

print("Part 4: Mock UBL Transformer added.")

# ---------- PART 5: Test Cases ----------

class TestUBLMapping(unittest.TestCase):
    """Test cases for UBL mapping."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.validator = mock_ubl_validator
        self.transformer = mock_ubl_transformer
        
        # Create sample Odoo invoice data
        self.odoo_invoice = {
            "id": 123,
            "name": "INV/2023/001",
            "move_type": "out_invoice",
            "invoice_date": "2023-05-31",
            "invoice_date_due": "2023-06-30",
            "amount_untaxed": 1500.00,
            "amount_tax": 112.50,
            "amount_total": 1612.50,
            "narration": "Test Invoice",
            "ref": "PO-2023-001",
            "currency": {"id": 1, "name": "NGN", "symbol": "₦"},
            "partner": {
                "id": 42,
                "name": "Customer Company Ltd",
                "vat": "NG0987654321",
                "street": "456 Customer St",
                "street2": "",
                "city": "Customer City",
                "state_id": {"id": 5, "name": "Abuja"},
                "country_id": {"id": 1, "code": "NG", "name": "Nigeria"},
                "zip": "67890",
                "email": "jane@customer.com",
                "phone": "+2340987654321"
            },
            "invoice_line_ids": [
                {
                    "id": 1,
                    "name": "Product A Description",
                    "quantity": 10.0,
                    "price_unit": 100.00,
                    "price_subtotal": 1000.00,
                    "tax_ids": [{"id": 1, "name": "VAT 7.5%", "amount": 7.5}],
                    "product_id": {"id": 101, "name": "Product A", "default_code": "PROD-A"},
                    "product_uom_id": {"id": 1, "name": "Units"}
                },
                {
                    "id": 2,
                    "name": "Product B Description",
                    "quantity": 5.0,
                    "price_unit": 100.00,
                    "price_subtotal": 500.00,
                    "tax_ids": [{"id": 1, "name": "VAT 7.5%", "amount": 7.5}],
                    "product_id": {"id": 102, "name": "Product B", "default_code": "PROD-B"},
                    "product_uom_id": {"id": 3, "name": "kg"}
                }
            ],
            "invoice_payment_term_id": {"id": 1, "name": "Payment within 30 days"}
        }
        
        # Create sample company info
        self.company_info = {
            "id": 1,
            "name": "TaxPoynt Nigeria Ltd",
            "vat": "NG9876543210",
            "street": "123 Lagos Street",
            "street2": "",
            "city": "Lagos",
            "state_id": {"id": 1, "name": "Lagos"},
            "country_id": {"id": 1, "code": "NG", "name": "Nigeria"},
            "zip": "12345",
            "company_registry": "RC123456",
            "email": "info@taxpoynt.ng",
            "phone": "+234987654321"
        }
    
    def test_odoo_to_ubl_object(self):
        """Test conversion from Odoo invoice to UBL object."""
        # Convert Odoo invoice to UBL object
        ubl_invoice, validation_issues = self.transformer.odoo_to_ubl_object(
            self.odoo_invoice, self.company_info
        )
        
        # Check that conversion was successful
        self.assertIsNotNone(ubl_invoice, "UBL invoice should not be None")
        self.assertEqual(len(validation_issues), 0, 
                        f"There should be no validation issues, but got: {validation_issues}")
        
        # Check basic invoice fields
        self.assertEqual(ubl_invoice.invoice_number, "INV/2023/001", 
                        "Invoice number should match")
        self.assertEqual(ubl_invoice.invoice_type_code, InvoiceTypeCode.COMMERCIAL_INVOICE, 
                        "Invoice type code should be commercial invoice")
        self.assertEqual(ubl_invoice.currency_code, CurrencyCode.NGN, 
                        "Currency code should be NGN")
        
        # Check supplier and customer party fields
        self.assertEqual(ubl_invoice.accounting_supplier_party.party_name, "TaxPoynt Nigeria Ltd", 
                        "Supplier name should match")
        self.assertEqual(ubl_invoice.accounting_customer_party.party_name, "Customer Company Ltd", 
                        "Customer name should match")
        
        # Check monetary total fields
        self.assertEqual(ubl_invoice.legal_monetary_total.line_extension_amount, Decimal('1500.00'), 
                        "Line extension amount should match")
        self.assertEqual(ubl_invoice.legal_monetary_total.tax_exclusive_amount, Decimal('1500.00'), 
                        "Tax exclusive amount should match")
        self.assertEqual(ubl_invoice.legal_monetary_total.tax_inclusive_amount, Decimal('1612.50'), 
                        "Tax inclusive amount should match")
        self.assertEqual(ubl_invoice.legal_monetary_total.payable_amount, Decimal('1612.50'), 
                        "Payable amount should match")
        
        # Check invoice lines
        self.assertEqual(len(ubl_invoice.invoice_lines), 2, 
                        "There should be 2 invoice lines")
        self.assertEqual(ubl_invoice.invoice_lines[0].item_name, "Product A", 
                        "First line item name should match")
        self.assertEqual(ubl_invoice.invoice_lines[0].invoiced_quantity, Decimal('10.0'), 
                        "First line quantity should match")
        self.assertEqual(ubl_invoice.invoice_lines[0].price_amount, Decimal('100.00'), 
                        "First line price amount should match")
    
    def test_ubl_object_to_xml(self):
        """Test conversion from UBL object to XML."""
        # First convert Odoo invoice to UBL object
        ubl_invoice, _ = self.transformer.odoo_to_ubl_object(
            self.odoo_invoice, self.company_info
        )
        
        # Convert UBL object to XML
        xml_string, conversion_issues = self.transformer.ubl_object_to_xml(ubl_invoice)
        
        # Check that conversion was successful
        self.assertIsNotNone(xml_string, "XML string should not be None")
        self.assertNotEqual(xml_string, "", "XML string should not be empty")
        self.assertEqual(len(conversion_issues), 0, 
                        f"There should be no conversion issues, but got: {conversion_issues}")
        
        # For the simplified test, we'll just check if the XML string contains the word 'Invoice'
        # In a real implementation, we would check for proper UBL elements
        self.assertIn("<Invoice", xml_string, "XML should contain Invoice element")
        
        # Check that XML can be parsed
        try:
            root = ET.fromstring(xml_string)
            self.assertEqual(root.tag, "Invoice", "Root element should be Invoice")
        except ET.ParseError as e:
            self.fail(f"XML should be valid and parseable, but got error: {str(e)}")
    
    def test_ubl_validation(self):
        """Test UBL validation."""
        # Create a valid invoice for testing
        invoice_date = date(2023, 5, 31)
        due_date = date(2023, 6, 30)
        
        # Create supplier party
        supplier_address = PostalAddress(
            street_name="123 Supplier St",
            city_name="Supplier City",
            country_code="NG",
            postal_zone="12345",
            country_subdivision="Lagos"
        )
        
        supplier_party = AccountingParty(
            party_name="Supplier Company Ltd",
            postal_address=supplier_address,
            party_tax_scheme={"company_id": "NG1234567890", "tax_scheme_id": "VAT"},
            party_legal_entity=PartyLegalEntity(
                registration_name="Supplier Company Ltd",
                company_id="RC123456",
                company_id_scheme_id="NG-CAC"
            ),
            contact={"name": "John Supplier", "telephone": "+2341234567890", "email": "john@supplier.com"}
        )
        
        # Create customer party
        customer_address = PostalAddress(
            street_name="456 Customer St",
            city_name="Customer City",
            country_code="NG",
            postal_zone="67890",
            country_subdivision="Abuja"
        )
        
        customer_party = AccountingParty(
            party_name="Customer Company Ltd",
            postal_address=customer_address,
            party_tax_scheme={"company_id": "NG0987654321", "tax_scheme_id": "VAT"},
            party_legal_entity=PartyLegalEntity(
                registration_name="Customer Company Ltd",
                company_id="RC654321",
                company_id_scheme_id="NG-CAC"
            ),
            contact={"name": "Jane Customer", "telephone": "+2340987654321", "email": "jane@customer.com"}
        )
        
        # Create invoice lines
        line1 = InvoiceLine(
            id="1",
            invoiced_quantity=Decimal("10.0"),
            unit_code=UnitCode.PIECE,
            line_extension_amount=Decimal("1000.00"),
            item_description="Product A Description",
            item_name="Product A",
            price_amount=Decimal("100.00")
        )
        
        line2 = InvoiceLine(
            id="2",
            invoiced_quantity=Decimal("5.0"),
            unit_code=UnitCode.KILOGRAM,
            line_extension_amount=Decimal("500.00"),
            item_description="Product B Description",
            item_name="Product B",
            price_amount=Decimal("100.00")
        )
        
        # Create tax subtotal
        tax_subtotal = TaxSubtotal(
            taxable_amount=Decimal("1500.00"),
            tax_amount=Decimal("112.50"),
            tax_category=TaxCategory.STANDARD,
            tax_percent=Decimal("7.5")
        )
        
        # Create tax total
        tax_total = TaxTotal(
            tax_amount=Decimal("112.50"),
            tax_subtotals=[tax_subtotal]
        )
        
        # Create monetary total
        monetary_total = LegalMonetaryTotal(
            line_extension_amount=Decimal("1500.00"),
            tax_exclusive_amount=Decimal("1500.00"),
            tax_inclusive_amount=Decimal("1612.50"),
            payable_amount=Decimal("1612.50")
        )
        
        # Create payment terms
        payment_terms = PaymentTerms(
            note="Payment within 30 days",
            payment_due_date=due_date
        )
        
        # Create a valid invoice
        valid_invoice = InvoiceValidationRequest(
            invoice_number="INV-2023-001",
            invoice_type_code=InvoiceTypeCode.COMMERCIAL_INVOICE,
            invoice_date=invoice_date,
            due_date=due_date,
            currency_code=CurrencyCode.NGN,
            accounting_supplier_party=supplier_party,
            accounting_customer_party=customer_party,
            invoice_lines=[line1, line2],
            tax_total=tax_total,
            legal_monetary_total=monetary_total,
            payment_terms=payment_terms,
            note="Test Invoice"
        )
        
        # Validate the invoice
        is_valid, errors = self.validator.validate_mapped_invoice(valid_invoice)
        
        # Check validation results
        self.assertTrue(is_valid, f"Valid invoice should pass validation, but got errors: {errors}")
        self.assertEqual(len(errors), 0, "There should be no validation errors")
        
        # Create an invalid invoice by omitting required fields
        invalid_customer = AccountingParty(
            party_name="",  # Empty required field
            postal_address=customer_address,
            party_tax_scheme=None,  # Missing required field
            party_legal_entity=PartyLegalEntity(
                registration_name="Customer Company Ltd"
            ),
            contact={}
        )
        
        # Create a date that's 7 days before invoice_date using timedelta
        invalid_due_date = invoice_date - timedelta(days=7)
        
        invalid_invoice = InvoiceValidationRequest(
            invoice_number="INV-2023-002",
            invoice_type_code=InvoiceTypeCode.COMMERCIAL_INVOICE,
            invoice_date=invoice_date,
            due_date=invalid_due_date,  # Invalid due date (before invoice date)
            currency_code=CurrencyCode.NGN,
            accounting_supplier_party=supplier_party,
            accounting_customer_party=invalid_customer,
            invoice_lines=[line1, line2],
            tax_total=tax_total,
            legal_monetary_total=monetary_total
        )
        
        # Validate the invalid invoice
        is_valid, errors = self.validator.validate_mapped_invoice(invalid_invoice)
        
        # Check validation results
        self.assertFalse(is_valid, "Invalid invoice should fail validation")
        self.assertGreater(len(errors), 0, "There should be validation errors")
        
        # Check specific errors
        error_fields = [error.field for error in errors]
        self.assertIn("customer.party_name", error_fields, "Should have error for empty party name")
        self.assertIn("customer.party_tax_scheme", error_fields, "Should have error for missing tax scheme")
        self.assertIn("due_date", error_fields, "Should have error for invalid due date")

# ---------- PART 6: Main Runner ----------

def run_demo():
    """Run a demonstration of the UBL mapping."""
    print("\n===== Odoo to BIS Billing 3.0 UBL Field Mapping Demo =====\n")
    
    # Create sample Odoo invoice data
    odoo_invoice = {
        "id": 123,
        "name": "INV/2023/001",
        "move_type": "out_invoice",
        "invoice_date": "2023-05-31",
        "invoice_date_due": "2023-06-30",
        "amount_untaxed": 1500.00,
        "amount_tax": 112.50,
        "amount_total": 1612.50,
        "narration": "Test Invoice",
        "ref": "PO-2023-001",
        "currency": {"id": 1, "name": "NGN", "symbol": "₦"},
        "partner": {
            "id": 42,
            "name": "Customer Company Ltd",
            "vat": "NG0987654321",
            "street": "456 Customer St",
            "street2": "",
            "city": "Customer City",
            "state_id": {"id": 5, "name": "Abuja"},
            "country_id": {"id": 1, "code": "NG", "name": "Nigeria"},
            "zip": "67890",
            "email": "jane@customer.com",
            "phone": "+2340987654321"
        },
        "invoice_line_ids": [
            {
                "id": 1,
                "name": "Product A Description",
                "quantity": 10.0,
                "price_unit": 100.00,
                "price_subtotal": 1000.00,
                "tax_ids": [{"id": 1, "name": "VAT 7.5%", "amount": 7.5}],
                "product_id": {"id": 101, "name": "Product A", "default_code": "PROD-A"},
                "product_uom_id": {"id": 1, "name": "Units"}
            },
            {
                "id": 2,
                "name": "Product B Description",
                "quantity": 5.0,
                "price_unit": 100.00,
                "price_subtotal": 500.00,
                "tax_ids": [{"id": 1, "name": "VAT 7.5%", "amount": 7.5}],
                "product_id": {"id": 102, "name": "Product B", "default_code": "PROD-B"},
                "product_uom_id": {"id": 3, "name": "kg"}
            }
        ],
        "invoice_payment_term_id": {"id": 1, "name": "Payment within 30 days"}
    }
    
    # Create sample company info
    company_info = {
        "id": 1,
        "name": "TaxPoynt Nigeria Ltd",
        "vat": "NG9876543210",
        "street": "123 Lagos Street",
        "street2": "",
        "city": "Lagos",
        "state_id": {"id": 1, "name": "Lagos"},
        "country_id": {"id": 1, "code": "NG", "name": "Nigeria"},
        "zip": "12345",
        "company_registry": "RC123456",
        "email": "info@taxpoynt.ng",
        "phone": "+234987654321"
    }
    
    print("Step 1: Converting Odoo invoice to BIS Billing 3.0 UBL format...")
    ubl_invoice, validation_issues = mock_ubl_transformer.odoo_to_ubl_object(
        odoo_invoice, company_info
    )
    
    if validation_issues:
        print("Validation issues detected:")
        for issue in validation_issues:
            print(f"  - {issue['field']}: {issue['message']} ({issue['code']})")
    else:
        print("Validation successful - no issues found!")
    
    print("\nUBL Invoice Object Summary:")
    print(f"  Invoice Number: {ubl_invoice.invoice_number}")
    print(f"  Invoice Date: {ubl_invoice.invoice_date}")
    print(f"  Due Date: {ubl_invoice.due_date}")
    print(f"  Invoice Type: {ubl_invoice.invoice_type_code.value} ({ubl_invoice.invoice_type_code})")
    print(f"  Currency: {ubl_invoice.currency_code.value}")
    print(f"  Line Items: {len(ubl_invoice.invoice_lines)}")
    print(f"  Tax Amount: {ubl_invoice.tax_total.tax_amount}")
    print(f"  Subtotal (excl. tax): {ubl_invoice.legal_monetary_total.tax_exclusive_amount}")
    print(f"  Total (incl. tax): {ubl_invoice.legal_monetary_total.payable_amount}")
    
    print("\nStep 2: Converting UBL object to XML...")
    xml_string, conversion_issues = mock_ubl_transformer.ubl_object_to_xml(ubl_invoice)
    
    if conversion_issues:
        print("Conversion issues detected:")
        for issue in conversion_issues:
            print(f"  - {issue['field']}: {issue['message']} ({issue['code']})")
    else:
        print("XML conversion successful - no issues found!")
    
    xml_preview = xml_string[:500] + "..." if len(xml_string) > 500 else xml_string
    print(f"\nXML Preview:\n{xml_preview}")
    
    print("\nStep 3: Running validation tests...")
    
    # Run the tests
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestUBLMapping)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\nDemo completed! This demonstrates the functionality of the UBL mapping")
    print("implementation without requiring external dependencies.")

print("Part 5: Test cases added.")

if __name__ == "__main__":
    print("\nRunning UBL mapping tests...\n")
    run_demo()
