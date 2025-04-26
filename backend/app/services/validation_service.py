from typing import List, Dict, Any, Optional, Tuple
import json
from jsonschema import validate, ValidationError as JsonSchemaValidationError
import re
from datetime import datetime

from app.schemas.validation import (
    Invoice,
    ValidationIssue,
    ValidationResult,
    ValidationSeverity,
    ValidationRule as ValidationRuleSchema,
)
from app.models.validation import ValidationRule
from app.crud.crud_validation import validation_rule, validation_record


class ValidationError(Exception):
    def __init__(self, message: str, field: str, code: str = "validation_error"):
        self.message = message
        self.field = field
        self.code = code
        super().__init__(self.message)


class ValidationService:
    def __init__(self):
        # Initialize with basic validation rules
        self.schema_validators = {
            "required_field": self._validate_required_field,
            "field_type": self._validate_field_type,
            "field_regex": self._validate_field_regex,
            "field_length": self._validate_field_length,
            "numeric_range": self._validate_numeric_range,
            "valid_date": self._validate_date_format,
        }
        
        self.business_validators = {
            "total_calculation": self._validate_total_calculation,
            "irn_format": self._validate_irn_format,
            "line_item_totals": self._validate_line_item_totals,
            "currency_match": self._validate_currency_match,
            "document_references": self._validate_document_references,
            "payment_means": self._validate_payment_means,
            "tax_calculations": self._validate_tax_calculations,
            "delivery_period": self._validate_delivery_period,
        }
    
    def validate_invoice(self, invoice: Invoice) -> ValidationResult:
        """
        Validate an invoice against all applicable rules
        """
        issues = []
        
        # 1. First, validate against JSON schema
        schema_issues = self._validate_schema(invoice)
        issues.extend(schema_issues)
        
        # 2. If schema is valid, perform business rule validation
        if not schema_issues:
            business_issues = self._validate_business_rules(invoice)
            issues.extend(business_issues)
        
        is_valid = len([i for i in issues if i.severity == ValidationSeverity.ERROR]) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            issues=issues
        )
    
    def _validate_schema(self, invoice: Invoice) -> List[ValidationIssue]:
        """
        Validate invoice against JSON schema
        """
        issues = []
        
        # Basic schema validation
        try:
            # The Pydantic model already validates the schema
            # This step is a placeholder for additional schema validation
            pass
        except Exception as e:
            issues.append(
                ValidationIssue(
                    field="",
                    message=f"Schema validation error: {str(e)}",
                    severity=ValidationSeverity.ERROR,
                    code="schema_error"
                )
            )
        
        # Required fields check
        required_fields = [
            ("business_id", "Business ID"),
            ("irn", "Invoice Reference Number"),
            ("issue_date", "Issue Date"),
            ("invoice_type_code", "Invoice Type Code"),
            ("document_currency_code", "Document Currency Code"),
            ("accounting_supplier_party", "Supplier Information"),
            ("accounting_customer_party", "Customer Information"),
            ("legal_monetary_total", "Monetary Total"),
            ("invoice_line", "Invoice Lines")
        ]
        
        for field, field_name in required_fields:
            if not getattr(invoice, field, None):
                issues.append(
                    ValidationIssue(
                        field=field,
                        message=f"{field_name} is required",
                        severity=ValidationSeverity.ERROR,
                        code="required_field"
                    )
                )
        
        return issues
    
    def _validate_business_rules(self, invoice: Invoice) -> List[ValidationIssue]:
        """
        Validate invoice against business rules
        """
        issues = []
        
        # Validate IRN format
        irn_pattern = r'^[A-Za-z0-9]+-[A-Za-z0-9]{8}-\d{8}$'
        if not re.match(irn_pattern, invoice.irn):
            issues.append(
                ValidationIssue(
                    field="irn",
                    message="IRN format is invalid. Expected format: InvoiceNumber-ServiceID-YYYYMMDD",
                    severity=ValidationSeverity.ERROR,
                    code="invalid_irn_format"
                )
            )
        
        # Validate monetary totals
        if invoice.legal_monetary_total:
            # Check tax inclusive amount = tax exclusive amount + tax amount
            tax_exclusive = invoice.legal_monetary_total.tax_exclusive_amount
            tax_inclusive = invoice.legal_monetary_total.tax_inclusive_amount
            
            # Simple check if tax inclusive is greater than tax exclusive
            if tax_inclusive < tax_exclusive:
                issues.append(
                    ValidationIssue(
                        field="legal_monetary_total.tax_inclusive_amount",
                        message="Tax inclusive amount must be greater than or equal to tax exclusive amount",
                        severity=ValidationSeverity.ERROR,
                        code="invalid_tax_calculation"
                    )
                )
            
            # Check if payable amount matches tax inclusive amount
            if invoice.legal_monetary_total.payable_amount != tax_inclusive:
                issues.append(
                    ValidationIssue(
                        field="legal_monetary_total.payable_amount",
                        message="Payable amount must equal tax inclusive amount",
                        severity=ValidationSeverity.ERROR,
                        code="invalid_payable_amount"
                    )
                )
            
            # Check if line extension amount matches sum of line items
            line_sum = sum(line.line_extension_amount for line in invoice.invoice_line)
            if abs(invoice.legal_monetary_total.line_extension_amount - line_sum) > 0.01:  # Allow small rounding difference
                issues.append(
                    ValidationIssue(
                        field="legal_monetary_total.line_extension_amount",
                        message="Line extension amount must equal sum of invoice line amounts",
                        severity=ValidationSeverity.ERROR,
                        code="invalid_line_sum"
                    )
                )
        
        # Validate date format for all date fields
        date_fields = [
            ("issue_date", "Issue date"),
            ("due_date", "Due date"),
            ("tax_point_date", "Tax point date"),
            ("actual_delivery_date", "Actual delivery date")
        ]
        
        for field_name, display_name in date_fields:
            field_value = getattr(invoice, field_name, None)
            if field_value:
                try:
                    datetime.strptime(field_value, "%Y-%m-%d")
                except ValueError:
                    issues.append(
                        ValidationIssue(
                            field=field_name,
                            message=f"{display_name} must be in format YYYY-MM-DD",
                            severity=ValidationSeverity.ERROR,
                            code="invalid_date_format"
                        )
                    )
        
        # Validate delivery period if provided
        if invoice.invoice_delivery_period:
            delivery_period_issue = self._validate_delivery_period(invoice)
            if delivery_period_issue:
                issues.append(delivery_period_issue)
        
        # Validate TIN format for supplier and customer
        tin_pattern = r'^\d{8}-\d{4}$'
        
        if not re.match(tin_pattern, invoice.accounting_supplier_party.postal_address.tin):
            issues.append(
                ValidationIssue(
                    field="accounting_supplier_party.postal_address.tin",
                    message="Supplier TIN format is invalid. Expected format: 12345678-0001",
                    severity=ValidationSeverity.ERROR,
                    code="invalid_tin_format"
                )
            )
        
        if not re.match(tin_pattern, invoice.accounting_customer_party.postal_address.tin):
            issues.append(
                ValidationIssue(
                    field="accounting_customer_party.postal_address.tin",
                    message="Customer TIN format is invalid. Expected format: 12345678-0001",
                    severity=ValidationSeverity.ERROR,
                    code="invalid_tin_format"
                )
            )
        
        # Validate document references if provided
        document_ref_fields = [
            "billing_reference",
            "dispatch_document_reference",
            "receipt_document_reference",
            "originator_document_reference",
            "contract_document_reference",
            "additional_document_reference"
        ]
        
        for field_name in document_ref_fields:
            references = getattr(invoice, field_name, None)
            if references:
                ref_issues = self._validate_document_references_list(references, field_name)
                issues.extend(ref_issues)
        
        # Validate payment means if provided
        if invoice.payment_means:
            payment_issues = self._validate_payment_means_list(invoice.payment_means)
            issues.extend(payment_issues)
        
        # Validate tax totals if provided
        if invoice.tax_total:
            tax_issues = self._validate_tax_calculations(invoice)
            issues.extend(tax_issues)
        
        # Check time format
        if invoice.issue_time:
            time_pattern = r'^([01]\d|2[0-3]):([0-5]\d):([0-5]\d)$'
            if not re.match(time_pattern, invoice.issue_time):
                issues.append(
                    ValidationIssue(
                        field="issue_time",
                        message="Issue time must be in format HH:MM:SS",
                        severity=ValidationSeverity.ERROR,
                        code="invalid_time_format"
                    )
                )
        
        return issues
    
    # Schema validation methods
    def _validate_required_field(self, data: Dict[str, Any], rule: Dict[str, Any]) -> Optional[ValidationIssue]:
        field = rule.get("field")
        if field not in data or data[field] is None or data[field] == "":
            return ValidationIssue(
                field=field,
                message=f"{field} is required",
                severity=ValidationSeverity(rule.get("severity", "error")),
                code="required_field"
            )
        return None
    
    def _validate_field_type(self, data: Dict[str, Any], rule: Dict[str, Any]) -> Optional[ValidationIssue]:
        field = rule.get("field")
        if field not in data:
            return None
        
        expected_type = rule.get("expected_type")
        if expected_type == "string" and not isinstance(data[field], str):
            return ValidationIssue(
                field=field,
                message=f"{field} must be a string",
                severity=ValidationSeverity(rule.get("severity", "error")),
                code="invalid_type"
            )
        elif expected_type == "number" and not isinstance(data[field], (int, float)):
            return ValidationIssue(
                field=field,
                message=f"{field} must be a number",
                severity=ValidationSeverity(rule.get("severity", "error")),
                code="invalid_type"
            )
        elif expected_type == "boolean" and not isinstance(data[field], bool):
            return ValidationIssue(
                field=field,
                message=f"{field} must be a boolean",
                severity=ValidationSeverity(rule.get("severity", "error")),
                code="invalid_type"
            )
        return None
    
    def _validate_field_regex(self, data: Dict[str, Any], rule: Dict[str, Any]) -> Optional[ValidationIssue]:
        field = rule.get("field")
        if field not in data or not isinstance(data[field], str):
            return None
        
        pattern = rule.get("pattern")
        if not re.match(pattern, data[field]):
            return ValidationIssue(
                field=field,
                message=rule.get("message", f"{field} does not match required pattern"),
                severity=ValidationSeverity(rule.get("severity", "error")),
                code="invalid_pattern"
            )
        return None
    
    def _validate_field_length(self, data: Dict[str, Any], rule: Dict[str, Any]) -> Optional[ValidationIssue]:
        field = rule.get("field")
        if field not in data or not isinstance(data[field], str):
            return None
        
        min_length = rule.get("min_length")
        max_length = rule.get("max_length")
        
        if min_length and len(data[field]) < min_length:
            return ValidationIssue(
                field=field,
                message=f"{field} must be at least {min_length} characters",
                severity=ValidationSeverity(rule.get("severity", "error")),
                code="min_length"
            )
        
        if max_length and len(data[field]) > max_length:
            return ValidationIssue(
                field=field,
                message=f"{field} must be at most {max_length} characters",
                severity=ValidationSeverity(rule.get("severity", "error")),
                code="max_length"
            )
        
        return None
    
    def _validate_numeric_range(self, data: Dict[str, Any], rule: Dict[str, Any]) -> Optional[ValidationIssue]:
        field = rule.get("field")
        if field not in data or not isinstance(data[field], (int, float)):
            return None
        
        min_value = rule.get("min_value")
        max_value = rule.get("max_value")
        
        if min_value is not None and data[field] < min_value:
            return ValidationIssue(
                field=field,
                message=f"{field} must be at least {min_value}",
                severity=ValidationSeverity(rule.get("severity", "error")),
                code="min_value"
            )
        
        if max_value is not None and data[field] > max_value:
            return ValidationIssue(
                field=field,
                message=f"{field} must be at most {max_value}",
                severity=ValidationSeverity(rule.get("severity", "error")),
                code="max_value"
            )
        
        return None
    
    def _validate_date_format(self, data: Dict[str, Any], rule: Dict[str, Any]) -> Optional[ValidationIssue]:
        field = rule.get("field")
        if field not in data or not isinstance(data[field], str):
            return None
        
        date_format = rule.get("format", "%Y-%m-%d")
        try:
            datetime.strptime(data[field], date_format)
        except ValueError:
            return ValidationIssue(
                field=field,
                message=f"{field} must be in format {date_format}",
                severity=ValidationSeverity(rule.get("severity", "error")),
                code="invalid_date_format"
            )
        
        return None
    
    # Business validation methods
    def _validate_total_calculation(self, invoice: Invoice) -> Optional[ValidationIssue]:
        if not invoice.legal_monetary_total:
            return None
        
        tax_exclusive = invoice.legal_monetary_total.tax_exclusive_amount
        tax_inclusive = invoice.legal_monetary_total.tax_inclusive_amount
        
        if tax_inclusive < tax_exclusive:
            return ValidationIssue(
                field="legal_monetary_total.tax_inclusive_amount",
                message="Tax inclusive amount must be greater than or equal to tax exclusive amount",
                severity=ValidationSeverity.ERROR,
                code="invalid_tax_calculation"
            )
        
        return None
    
    def _validate_irn_format(self, invoice: Invoice) -> Optional[ValidationIssue]:
        irn_pattern = r'^[A-Za-z0-9]+-[A-Za-z0-9]{8}-\d{8}$'
        if not re.match(irn_pattern, invoice.irn):
            return ValidationIssue(
                field="irn",
                message="IRN format is invalid. Expected format: InvoiceNumber-ServiceID-YYYYMMDD",
                severity=ValidationSeverity.ERROR,
                code="invalid_irn_format"
            )
        
        return None
    
    def _validate_line_item_totals(self, invoice: Invoice) -> Optional[ValidationIssue]:
        if not invoice.invoice_line or not invoice.legal_monetary_total:
            return None
        
        line_sum = sum(line.line_extension_amount for line in invoice.invoice_line)
        total = invoice.legal_monetary_total.line_extension_amount
        
        if abs(total - line_sum) > 0.01:  # Allow small rounding difference
            return ValidationIssue(
                field="legal_monetary_total.line_extension_amount",
                message="Line extension amount must equal sum of invoice line amounts",
                severity=ValidationSeverity.ERROR,
                code="invalid_line_sum"
            )
        
        return None
    
    def _validate_currency_match(self, invoice: Invoice) -> Optional[ValidationIssue]:
        # This is a placeholder for currency validation
        # In a real implementation, this would check if the currency is valid
        if invoice.document_currency_code and invoice.tax_currency_code:
            if invoice.document_currency_code != invoice.tax_currency_code:
                return ValidationIssue(
                    field="tax_currency_code",
                    message="Tax currency code should match document currency code in this implementation",
                    severity=ValidationSeverity.WARNING,
                    code="currency_mismatch"
                )
        return None
    
    def _validate_document_references(self, invoice: Invoice) -> Optional[ValidationIssue]:
        # Check existence of document references with valid IRNs
        document_ref_fields = [
            "billing_reference", 
            "dispatch_document_reference",
            "receipt_document_reference", 
            "originator_document_reference",
            "contract_document_reference", 
            "additional_document_reference"
        ]
        
        for field in document_ref_fields:
            references = getattr(invoice, field, None)
            if references:
                for i, ref in enumerate(references):
                    irn_pattern = r'^[A-Za-z0-9]+-[A-Za-z0-9]{8}-\d{8}$'
                    if not re.match(irn_pattern, ref.irn):
                        return ValidationIssue(
                            field=f"{field}[{i}].irn",
                            message=f"Document reference IRN format is invalid. Expected format: InvoiceNumber-ServiceID-YYYYMMDD",
                            severity=ValidationSeverity.ERROR,
                            code="invalid_reference_irn_format"
                        )
                    
                    try:
                        datetime.strptime(ref.issue_date, "%Y-%m-%d")
                    except ValueError:
                        return ValidationIssue(
                            field=f"{field}[{i}].issue_date",
                            message=f"Document reference issue date must be in format YYYY-MM-DD",
                            severity=ValidationSeverity.ERROR,
                            code="invalid_reference_date_format"
                        )
        
        return None
    
    def _validate_document_references_list(self, references: List, field_name: str) -> List[ValidationIssue]:
        issues = []
        
        for i, ref in enumerate(references):
            irn_pattern = r'^[A-Za-z0-9]+-[A-Za-z0-9]{8}-\d{8}$'
            if not re.match(irn_pattern, ref.irn):
                issues.append(
                    ValidationIssue(
                        field=f"{field_name}[{i}].irn",
                        message=f"Document reference IRN format is invalid. Expected format: InvoiceNumber-ServiceID-YYYYMMDD",
                        severity=ValidationSeverity.ERROR,
                        code="invalid_reference_irn_format"
                    )
                )
                
            try:
                datetime.strptime(ref.issue_date, "%Y-%m-%d")
            except ValueError:
                issues.append(
                    ValidationIssue(
                        field=f"{field_name}[{i}].issue_date",
                        message=f"Document reference issue date must be in format YYYY-MM-DD",
                        severity=ValidationSeverity.ERROR,
                        code="invalid_reference_date_format"
                    )
                )
                
        return issues
    
    def _validate_payment_means(self, invoice: Invoice) -> Optional[ValidationIssue]:
        if not invoice.payment_means:
            return None
        
        # Check if payment means codes are valid
        valid_payment_codes = [10, 20, 30, 42, 48, 49, 50, 97]  # Example list
        
        for i, payment in enumerate(invoice.payment_means):
            if payment.payment_means_code not in valid_payment_codes:
                return ValidationIssue(
                    field=f"payment_means[{i}].payment_means_code",
                    message=f"Payment means code is not valid",
                    severity=ValidationSeverity.ERROR,
                    code="invalid_payment_means_code"
                )
            
            try:
                datetime.strptime(payment.payment_due_date, "%Y-%m-%d")
            except ValueError:
                return ValidationIssue(
                    field=f"payment_means[{i}].payment_due_date",
                    message=f"Payment due date must be in format YYYY-MM-DD",
                    severity=ValidationSeverity.ERROR,
                    code="invalid_payment_due_date_format"
                )
        
        return None
    
    def _validate_payment_means_list(self, payment_means: List) -> List[ValidationIssue]:
        issues = []
        valid_payment_codes = [10, 20, 30, 42, 48, 49, 50, 97]  # Example list
        
        for i, payment in enumerate(payment_means):
            if payment.payment_means_code not in valid_payment_codes:
                issues.append(
                    ValidationIssue(
                        field=f"payment_means[{i}].payment_means_code",
                        message=f"Payment means code is not valid",
                        severity=ValidationSeverity.ERROR,
                        code="invalid_payment_means_code"
                    )
                )
            
            try:
                datetime.strptime(payment.payment_due_date, "%Y-%m-%d")
            except ValueError:
                issues.append(
                    ValidationIssue(
                        field=f"payment_means[{i}].payment_due_date",
                        message=f"Payment due date must be in format YYYY-MM-DD",
                        severity=ValidationSeverity.ERROR,
                        code="invalid_payment_due_date_format"
                    )
                )
                
        return issues
    
    def _validate_tax_calculations(self, invoice: Invoice) -> List[ValidationIssue]:
        issues = []
        
        if not invoice.tax_total:
            return issues
        
        # For each tax total, ensure tax amount matches sum of subtotals
        for i, tax_total in enumerate(invoice.tax_total):
            subtotal_sum = sum(subtotal.tax_amount for subtotal in tax_total.tax_subtotal)
            
            if abs(tax_total.tax_amount - subtotal_sum) > 0.01:  # Allow small rounding difference
                issues.append(
                    ValidationIssue(
                        field=f"tax_total[{i}].tax_amount",
                        message="Tax amount must equal sum of tax subtotal amounts",
                        severity=ValidationSeverity.ERROR,
                        code="invalid_tax_sum"
                    )
                )
            
            # Check percent calculations in each subtotal
            for j, subtotal in enumerate(tax_total.tax_subtotal):
                calculated_tax = subtotal.taxable_amount * (subtotal.tax_category.percent / 100)
                if abs(subtotal.tax_amount - calculated_tax) > 0.01:  # Allow small rounding difference
                    issues.append(
                        ValidationIssue(
                            field=f"tax_total[{i}].tax_subtotal[{j}].tax_amount",
                            message="Tax amount must equal taxable amount * (percent / 100)",
                            severity=ValidationSeverity.WARNING,  # Warning because rounding can cause small differences
                            code="tax_calculation_mismatch"
                        )
                    )
        
        return issues
    
    def _validate_delivery_period(self, invoice: Invoice) -> Optional[ValidationIssue]:
        if not invoice.invoice_delivery_period:
            return None
        
        try:
            start_date = datetime.strptime(invoice.invoice_delivery_period.start_date, "%Y-%m-%d")
            end_date = datetime.strptime(invoice.invoice_delivery_period.end_date, "%Y-%m-%d")
            
            if end_date < start_date:
                return ValidationIssue(
                    field="invoice_delivery_period",
                    message="Delivery period end date must be on or after start date",
                    severity=ValidationSeverity.ERROR,
                    code="invalid_delivery_period"
                )
        except ValueError:
            return ValidationIssue(
                field="invoice_delivery_period",
                message="Delivery period dates must be in format YYYY-MM-DD",
                severity=ValidationSeverity.ERROR,
                code="invalid_delivery_period_format"
            )
        
        return None


validation_service = ValidationService() 