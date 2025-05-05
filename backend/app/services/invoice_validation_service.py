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
        self.load_default_rules()
    
    def load_default_rules(self):
        """Load the default validation rules based on BIS Billing 3.0 and FIRS requirements."""
        # Required fields validation
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
