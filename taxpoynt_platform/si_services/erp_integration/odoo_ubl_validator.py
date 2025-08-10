"""
Odoo to BIS Billing 3.0 UBL Field Validation Service.

This module provides validation for mapped fields from Odoo to BIS Billing 3.0
UBL format to ensure all required data is present and correctly formatted.
"""
import logging
from typing import Dict, Any, List, Optional, Tuple, Union
from decimal import Decimal

from app.schemas.invoice_validation import (
    InvoiceValidationRequest, ValidationError
)

logger = logging.getLogger(__name__)


class OdooUBLValidator:
    """
    Validator for mapped Odoo to UBL invoice data.
    
    This class validates that all required fields for BIS Billing 3.0 UBL
    format are present and correctly formatted in the mapped invoice data.
    """
    
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
                "item_description",
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
        """
        Validate that a mapped invoice has all required fields for BIS Billing 3.0.
        
        Args:
            invoice: The mapped invoice data to validate
            
        Returns:
            Tuple of (is_valid, list of validation errors)
        """
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
        
        # Additional business rule validations
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
        """Validate business rules specific to BIS Billing 3.0 and FIRS requirements."""
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
        
        # Validate payable amount
        if invoice.legal_monetary_total:
            if invoice.legal_monetary_total.payable_amount != invoice.legal_monetary_total.tax_inclusive_amount:
                # Allow for prepaid amounts
                prepaid = invoice.legal_monetary_total.prepaid_amount or Decimal('0.00')
                allowance = invoice.legal_monetary_total.allowance_total_amount or Decimal('0.00')
                charge = invoice.legal_monetary_total.charge_total_amount or Decimal('0.00')
                
                calc_payable = invoice.legal_monetary_total.tax_inclusive_amount - prepaid + charge - allowance
                
                if abs(calc_payable - invoice.legal_monetary_total.payable_amount) > Decimal('0.02'):
                    errors.append(ValidationError(
                        field="legal_monetary_total.payable_amount",
                        error=f"Payable amount ({invoice.legal_monetary_total.payable_amount}) does not match calculated amount ({calc_payable})",
                        error_code="PAYABLE_MISMATCH"
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
odoo_ubl_validator = OdooUBLValidator()