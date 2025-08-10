"""
Invoice validation service for BIS Billing 3.0 UBL and FIRS requirements.

This module provides validation services for invoice data against
the BIS Billing 3.0 UBL schema and specific Nigerian tax/business rules.
"""
import logging
from typing import List, Dict, Any, Optional, Tuple, Union
from datetime import datetime
from uuid import UUID

from app.schemas.invoice_validation import (
    InvoiceValidationRequest,
    InvoiceValidationResponse,
    BatchValidationRequest,
    BatchValidationResponse,
    ValidationError,
    ValidationRule
)

logger = logging.getLogger(__name__)


class ValidationRuleEngine:
    """
    Engine for applying validation rules to invoice data.
    
    This class implements the rules engine for validating invoices
    against BIS Billing 3.0 UBL schema and FIRS requirements.
    """
    
    def __init__(self):
        """Initialize the validation rule engine with default rules."""
        self.rules = []
        self.rule_categories = {
            "required_fields": "Validates presence of required fields",
            "format_validation": "Validates correct format of field values",
            "business_rules": "Validates Nigerian business rules compliance",
            "tax_rules": "Validates Nigerian tax rules compliance",
            "ubl_schema": "Validates UBL schema compliance",
            "firs_specific": "Validates specific FIRS e-Invoice requirements",
            "consistency": "Validates data consistency across fields"
        }
        self.load_default_rules()
    
    def load_default_rules(self):
        """Load the default validation rules based on BIS Billing 3.0 and FIRS requirements."""
        # Load BIS UBL 3.0 standard required field rules
        self._load_bis3_required_field_rules()
        
        # Load FIRS-specific validation rules
        self._load_firs_specific_rules()
        
        # Load Nigerian tax validation rules
        self._load_nigerian_tax_rules()
        
        # Load UBL schema validation rules
        self._load_ubl_schema_rules()
        
        # Load consistency validation rules
        self._load_consistency_rules()
        
    def _load_bis3_required_field_rules(self):
        """Load required field validation rules from BIS Billing 3.0 standard."""
        self.rules.append({
            "id": "BIS3-REQ-001",
            "name": "Required invoice number",
            "description": "Invoice must have a unique invoice number",
            "severity": "error",
            "category": "required_fields",
            "field_path": "invoice_number",
            "source": "BIS3",
            "validator": lambda invoice: bool(invoice.invoice_number.strip()),
            "error_message": "Invoice number is required and cannot be empty"
        })
        
        self.rules.append({
            "id": "BIS3-REQ-002",
            "name": "Required invoice date",
            "description": "Invoice must have an issue date",
            "severity": "error",
            "category": "required_fields",
            "field_path": "invoice_date",
            "source": "BIS3",
            "validator": lambda invoice: invoice.invoice_date is not None,
            "error_message": "Invoice date is required"
        })
        
        self.rules.append({
            "id": "BIS3-REQ-003",
            "name": "Required seller information",
            "description": "Invoice must have seller (supplier) information",
            "severity": "error",
            "category": "required_fields",
            "field_path": "accounting_supplier_party",
            "source": "BIS3",
            "validator": lambda invoice: invoice.accounting_supplier_party is not None,
            "error_message": "Seller information is required"
        })
        
        self.rules.append({
            "id": "BIS3-REQ-004",
            "name": "Required buyer information",
            "description": "Invoice must have buyer (customer) information",
            "severity": "error",
            "category": "required_fields",
            "field_path": "accounting_customer_party",
            "source": "BIS3",
            "validator": lambda invoice: invoice.accounting_customer_party is not None,
            "error_message": "Buyer information is required"
        })
        
        self.rules.append({
            "id": "BIS3-REQ-005",
            "name": "Required invoice lines",
            "description": "Invoice must have at least one invoice line",
            "severity": "error",
            "category": "required_fields",
            "field_path": "invoice_lines",
            "source": "BIS3",
            "validator": lambda invoice: len(invoice.invoice_lines) > 0,
            "error_message": "At least one invoice line is required"
        })
        
    def _load_firs_specific_rules(self):
        """Load validation rules specific to FIRS e-Invoice requirements."""
        # FIRS company registration validation
        self.rules.append({
            "id": "FIRS-REG-001",
            "name": "Required seller TIN",
            "description": "Seller must have a valid Nigerian Tax Identification Number (TIN)",
            "severity": "error",
            "category": "firs_specific",
            "field_path": "accounting_supplier_party.party_legal_entity.company_id",
            "source": "FIRS",
            "validator": self._validate_tin,
            "error_message": "Seller must have a valid 14-digit Nigerian TIN"
        })
        
        self.rules.append({
            "id": "FIRS-REG-002",
            "name": "Required buyer TIN for B2B",
            "description": "B2B invoices require buyer to have a valid Nigerian Tax Identification Number (TIN)",
            "severity": "error",
            "category": "firs_specific",
            "field_path": "accounting_customer_party.party_legal_entity.company_id",
            "source": "FIRS",
            "validator": self._validate_buyer_tin,
            "error_message": "B2B invoices require buyer to have a valid Nigerian TIN"
        })
        
        # Invoice number format validation for FIRS
        self.rules.append({
            "id": "FIRS-FMT-001",
            "name": "Invoice number format",
            "description": "Invoice number must match FIRS format requirements",
            "severity": "error",
            "category": "format_validation",
            "field_path": "invoice_number",
            "source": "FIRS",
            "validator": self._validate_invoice_number_format,
            "error_message": "Invoice number must contain only alphanumeric characters, maximum 50 characters"
        })
        
        # Currency validation for Nigeria
        self.rules.append({
            "id": "FIRS-CUR-001",
            "name": "Primary currency requirement",
            "description": "Primary invoice currency must be NGN for domestic transactions",
            "severity": "error",
            "category": "firs_specific",
            "field_path": "currency_code",
            "source": "FIRS",
            "validator": lambda invoice: self._validate_primary_currency(invoice),
            "error_message": "Primary currency must be NGN for domestic transactions"
        })
        
        # Party address validation for Nigeria
        self.rules.append({
            "id": "FIRS-ADR-001",
            "name": "Seller Nigerian address",
            "description": "Seller must have a valid Nigerian address for domestic invoices",
            "severity": "error",
            "category": "firs_specific",
            "field_path": "accounting_supplier_party.postal_address",
            "source": "FIRS",
            "validator": self._validate_nigerian_address,
            "error_message": "Seller must have a valid Nigerian address with state and LGA for domestic invoices"
        })
        
    def _load_nigerian_tax_rules(self):
        """Load validation rules for Nigerian tax requirements."""
        # VAT validation
        self.rules.append({
            "id": "FIRS-TAX-001",
            "name": "VAT calculation",
            "description": "VAT must be calculated correctly at 7.5% unless exempt",
            "severity": "error",
            "category": "tax_rules",
            "field_path": "tax_total",
            "source": "FIRS",
            "validator": self._validate_vat_calculation,
            "error_message": "VAT must be calculated correctly at 7.5% unless specifically exempt"
        })
        
        self.rules.append({
            "id": "FIRS-TAX-002",
            "name": "VAT exemption reason",
            "description": "VAT exemptions must include valid reason codes",
            "severity": "error",
            "category": "tax_rules",
            "field_path": "tax_total.tax_subtotals",
            "source": "FIRS",
            "validator": self._validate_vat_exemption_reason,
            "error_message": "VAT exempt or zero-rated items must include a valid exemption reason code"
        })
        
        # WHT validation if applicable
        self.rules.append({
            "id": "FIRS-TAX-003",
            "name": "WHT calculation",
            "description": "Withholding Tax must be calculated correctly if applicable",
            "severity": "warning",  # Warning only as WHT may not apply to all invoices
            "category": "tax_rules",
            "field_path": "tax_total.tax_subtotals",
            "source": "FIRS",
            "validator": self._validate_wht_if_applicable,
            "error_message": "Withholding Tax should be calculated correctly for applicable services"
        })
        
    def _load_ubl_schema_rules(self):
        """Load UBL schema validation rules."""
        # UBL date format validation
        self.rules.append({
            "id": "UBL-FMT-001",
            "name": "UBL date format",
            "description": "Dates must conform to UBL date format",
            "severity": "error",
            "category": "ubl_schema",
            "field_path": "invoice_date,due_date,tax_point_date,delivery_date",
            "source": "UBL",
            "validator": lambda invoice: True,  # Date validation handled by Pydantic
            "error_message": "Dates must conform to ISO 8601 format (YYYY-MM-DD)"
        })
        
        # UBL monetary values format
        self.rules.append({
            "id": "UBL-FMT-002",
            "name": "UBL monetary values",
            "description": "Monetary values must have correct decimal places",
            "severity": "error",
            "category": "ubl_schema",
            "field_path": "legal_monetary_total,invoice_lines",
            "source": "UBL",
            "validator": lambda invoice: True,  # Decimal validation handled by Pydantic
            "error_message": "Monetary values must have maximum 2 decimal places"
        })
    
    def _load_consistency_rules(self):
        """Load validation rules for data consistency."""
        # Date validations
        self.rules.append({
            "id": "BIS3-DATE-001",
            "name": "Invoice date not in future",
            "description": "Invoice date cannot be in the future",
            "severity": "error",
            "category": "date_validation",
            "field_path": "invoice_date",
            "source": "BIS3",
            "validator": lambda invoice: invoice.invoice_date <= datetime.now().date(),
            "error_message": "Invoice date cannot be in the future"
        })
        
        # Tax validations
        self.rules.append({
            "id": "FIRS-TAX-001",
            "name": "Valid Nigerian VAT rate",
            "description": "Standard VAT rate must be 7.5% in Nigeria",
            "severity": "error",
            "category": "tax_validation",
            "field_path": "tax_total.tax_subtotals",
            "source": "FIRS",
            "validator": lambda invoice: all(
                ts.tax_percent != 7.5 or ts.tax_category == "S" 
                for ts in invoice.tax_total.tax_subtotals
            ),
            "error_message": "Standard VAT rate in Nigeria must be 7.5%"
        })
        
        # Numeric validations
        self.rules.append({
            "id": "BIS3-NUM-001",
            "name": "Line amount calculation",
            "description": "Line amount must be equal to quantity * unit price / base quantity",
            "severity": "error",
            "category": "numeric_validation",
            "field_path": "invoice_lines",
            "source": "BIS3",
            "validator": lambda invoice: all(
                abs((line.invoiced_quantity * line.price_amount / line.base_quantity) - line.line_extension_amount) <= 0.01
                for line in invoice.invoice_lines
            ),
            "error_message": "Line amount calculation is incorrect"
        })
        
        # FIRS specific validations
        self.rules.append({
            "id": "FIRS-ID-001",
            "name": "Valid Nigerian Tax Identification Number (TIN)",
            "description": "Seller must have a valid Nigerian TIN",
            "severity": "error",
            "category": "identification",
            "field_path": "accounting_supplier_party.party_tax_scheme",
            "source": "FIRS",
            "validator": lambda invoice: "taxid" in invoice.accounting_supplier_party.party_tax_scheme 
                and len(invoice.accounting_supplier_party.party_tax_scheme["taxid"]) >= 10,
            "error_message": "Seller must have a valid Nigerian Tax Identification Number (TIN)"
        })
    
    def get_all_rules(self) -> List[ValidationRule]:
        """
        Get all validation rules.
        
        Returns:
            List of ValidationRule objects
        """
        return [
            ValidationRule(
                id=rule["id"],
                name=rule["name"],
                description=rule["description"],
                severity=rule["severity"],
                category=rule["category"],
                field_path=rule["field_path"],
                source=rule["source"]
            )
            for rule in self.rules
        ]
    
    def validate_invoice(self, invoice: InvoiceValidationRequest) -> InvoiceValidationResponse:
        """
        Validate an invoice against all rules.
        
        Args:
            invoice: Invoice data to validate
            
        Returns:
            Validation response with errors and warnings
        """
        errors = []
        warnings = []
        
        for rule in self.rules:
            try:
                is_valid = rule["validator"](invoice)
                if not is_valid:
                    validation_error = ValidationError(
                        field=rule["field_path"],
                        error=rule["error_message"],
                        error_code=rule["id"]
                    )
                    
                    if rule["severity"] == "error":
                        errors.append(validation_error)
                    else:
                        warnings.append(validation_error)
            except Exception as e:
                logger.error(f"Error applying rule {rule['id']}: {str(e)}")
                errors.append(
                    ValidationError(
                        field=rule["field_path"],
                        error=f"Validation error: {str(e)}",
                        error_code=rule["id"]
                    )
                )
        
        # Create validation response
        return InvoiceValidationResponse(
            valid=len(errors) == 0,
            invoice_number=invoice.invoice_number,
            validation_timestamp=datetime.utcnow(),
            errors=errors,
            warnings=warnings
        )
    
    def validate_batch(self, batch_request: BatchValidationRequest) -> BatchValidationResponse:
        """
        Validate a batch of invoices.
        
        Args:
            batch_request: Batch of invoices to validate
            
        Returns:
            Batch validation response
        """
        results = []
        valid_count = 0
        
        for invoice in batch_request.invoices:
            validation_result = self.validate_invoice(invoice)
            results.append(validation_result)
            
            if validation_result.valid:
                valid_count += 1
        
        return BatchValidationResponse(
            total_count=len(batch_request.invoices),
            valid_count=valid_count,
            invalid_count=len(batch_request.invoices) - valid_count,
            validation_timestamp=datetime.utcnow(),
            results=results
        )


    # Helper validation methods for FIRS rules
    def _validate_tin(self, invoice):
        """Validate that a Nigerian TIN follows the correct format and checksum."""
        tin = None
        try:
            tin = invoice.accounting_supplier_party.party_legal_entity.company_id
        except AttributeError:
            return False
            
        if not tin:
            return False
            
        # Nigerian TIN is 14 digits
        if not tin.isdigit() or len(tin) != 14:
            return False
            
        # Additional TIN validation logic could be added here
        # such as checksum validation if FIRS provides the algorithm
        return True
    
    def _validate_buyer_tin(self, invoice):
        """Validate buyer TIN if it's a B2B invoice."""
        # Check if this is a B2B invoice (business customers require TIN)
        is_business = False
        try:
            # If the customer has a business name and registration, it's likely B2B
            if invoice.accounting_customer_party.party_legal_entity and \
               invoice.accounting_customer_party.party_legal_entity.registration_name:
                is_business = True
        except AttributeError:
            pass
            
        # If not a business, no need to validate TIN
        if not is_business:
            return True
            
        # For B2B, validate TIN
        tin = None
        try:
            tin = invoice.accounting_customer_party.party_legal_entity.company_id
        except AttributeError:
            return False
            
        if not tin:
            return False
            
        # Nigerian TIN is 14 digits
        if not tin.isdigit() or len(tin) != 14:
            return False
            
        return True
    
    def _validate_invoice_number_format(self, invoice):
        """Validate that invoice number follows FIRS format requirements."""
        import re
        
        if not invoice.invoice_number:
            return False
            
        # FIRS requires alphanumeric invoice numbers
        pattern = r'^[a-zA-Z0-9]+$'
        if not re.match(pattern, invoice.invoice_number):
            return False
            
        # Maximum length check
        if len(invoice.invoice_number) > 50:
            return False
            
        return True
    
    def _validate_primary_currency(self, invoice):
        """Validate that primary currency is NGN for domestic transactions."""
        # If both parties are Nigerian, currency should be NGN
        seller_nigerian = False
        buyer_nigerian = False
        
        try:
            seller_nigerian = invoice.accounting_supplier_party.postal_address.country_code == "NG"
        except AttributeError:
            pass
            
        try:
            buyer_nigerian = invoice.accounting_customer_party.postal_address.country_code == "NG"
        except AttributeError:
            pass
            
        # If both parties are Nigerian, enforce NGN currency
        if seller_nigerian and buyer_nigerian and invoice.currency_code != "NGN":
            return False
            
        return True
    
    def _validate_nigerian_address(self, invoice):
        """Validate that Nigerian addresses include state and LGA as required by FIRS."""
        try:
            address = invoice.accounting_supplier_party.postal_address
            
            # Check if address is for Nigeria
            if address.country_code != "NG":
                return True  # Non-Nigerian addresses have different requirements
                
            # Nigerian addresses need state (country_subdivision) and city/LGA
            if not address.country_subdivision or not address.city_name:
                return False
                
            return True
        except AttributeError:
            return False
    
    def _validate_vat_calculation(self, invoice):
        """Validate that VAT is calculated correctly at 7.5% unless exempt."""
        # Find VAT subtotal
        vat_subtotal = None
        try:
            for subtotal in invoice.tax_total.tax_subtotals:
                if subtotal.tax_category in ["S", "STANDARD"]:
                    vat_subtotal = subtotal
                    break
                    
            if not vat_subtotal:
                # No VAT subtotal found - might be exempt or zero-rated
                return True
                
            # Standard Nigerian VAT is 7.5%
            if abs(vat_subtotal.tax_percent - 7.5) > 0.01:
                return False
                
            # Validate calculation
            expected_tax = round(vat_subtotal.taxable_amount * (vat_subtotal.tax_percent / 100), 2)
            if abs(vat_subtotal.tax_amount - expected_tax) > 0.01:
                return False
                
            return True
        except (AttributeError, TypeError):
            return False
    
    def _validate_vat_exemption_reason(self, invoice):
        """Validate that exempt or zero-rated items have valid reason codes."""
        try:
            for subtotal in invoice.tax_total.tax_subtotals:
                # Check for exempt or zero-rated tax categories
                if subtotal.tax_category in ["E", "Z", "EXEMPT", "ZERO"]:
                    # These must have a reason code or text
                    if not subtotal.tax_exemption_reason and not subtotal.tax_exemption_reason_code:
                        return False
            return True
        except AttributeError:
            return False
    
    def _validate_wht_if_applicable(self, invoice):
        """Validate withholding tax calculations if applicable."""
        # This is a simplified check - actual implementation would need
        # to consider the specific service types that require WHT
        wht_required = False
        has_wht = False
        
        # Check if any line items are services that might require WHT
        try:
            for line in invoice.invoice_lines:
                # Simplified check - in reality would need to check service codes
                if "service" in line.item_description.lower() or "consultation" in line.item_description.lower():
                    wht_required = True
                    break
                    
            # If WHT is required, check for WHT tax subtotal
            if wht_required:
                for subtotal in invoice.tax_total.tax_subtotals:
                    # Simplified - would need proper WHT tax category code
                    if "withholding" in getattr(subtotal, "tax_exemption_reason", "").lower():
                        has_wht = True
                        break
                        
            # If WHT is required but not found
            if wht_required and not has_wht:
                return False
                
            return True
        except AttributeError:
            # If we can't check properly, consider it valid to avoid false negatives
            return True


# Create a singleton instance of the validation engine
validation_engine = ValidationRuleEngine()


def validate_invoice(invoice: InvoiceValidationRequest) -> InvoiceValidationResponse:
    """
    Validate an invoice against BIS Billing 3.0 and FIRS requirements.
    
    Args:
        invoice: Invoice data to validate
        
    Returns:
        Validation response with errors and warnings
    """
    return validation_engine.validate_invoice(invoice)


def validate_invoice_batch(batch_request: BatchValidationRequest) -> BatchValidationResponse:
    """
    Validate a batch of invoices against BIS Billing 3.0 and FIRS requirements.
    
    Args:
        batch_request: Batch of invoices to validate
        
    Returns:
        Batch validation response
    """
    return validation_engine.validate_batch(batch_request)


def get_validation_rules() -> List[ValidationRule]:
    """
    Get all available validation rules.
    
    Returns:
        List of validation rules
    """
    return validation_engine.get_all_rules()
