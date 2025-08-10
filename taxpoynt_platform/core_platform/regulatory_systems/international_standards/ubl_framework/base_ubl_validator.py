"""
Base UBL Validator
=================
Abstract base class for validating UBL documents against standards.
Provides common validation patterns and Nigerian FIRS compliance checks.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union, Tuple
from datetime import datetime
from decimal import Decimal
import logging
import re

from .ubl_models import UBLInvoice


class UBLValidationError(Exception):
    """Raised when UBL validation fails."""
    pass


class ValidationResult:
    """Container for validation results."""
    
    def __init__(self):
        self.is_valid = True
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.info: List[str] = []
    
    def add_error(self, message: str):
        """Add validation error."""
        self.errors.append(message)
        self.is_valid = False
    
    def add_warning(self, message: str):
        """Add validation warning."""
        self.warnings.append(message)
    
    def add_info(self, message: str):
        """Add validation info."""
        self.info.append(message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            'is_valid': self.is_valid,
            'errors': self.errors,
            'warnings': self.warnings,
            'info': self.info,
            'error_count': len(self.errors),
            'warning_count': len(self.warnings)
        }


class BaseUBLValidator(ABC):
    """
    Abstract base class for UBL validators.
    
    All business system UBL validators should extend this class to ensure
    consistent UBL 2.1 compliance and standardized validation patterns.
    
    Features:
    - Standard UBL 2.1 schema validation
    - Nigerian FIRS compliance validation
    - Business rule validation
    - Tax calculation verification
    - Currency and amount validation
    - Extensible validation framework
    """
    
    def __init__(self, validation_config: Dict[str, Any] = None):
        """
        Initialize base UBL validator.
        
        Args:
            validation_config: Validator configuration options
        """
        self.config = validation_config or {}
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Nigerian compliance settings
        self.nigerian_tax_rate = self.config.get('nigerian_vat_rate', 7.5)
        self.strict_compliance = self.config.get('strict_compliance', True)
        self.currency_validation = self.config.get('validate_currency', True)
        
    @abstractmethod
    def validate_business_rules(self, ubl_invoice: UBLInvoice) -> ValidationResult:
        """
        Validate business-specific rules for the invoice.
        
        Args:
            ubl_invoice: UBL invoice to validate
            
        Returns:
            ValidationResult: Business rule validation results
        """
        pass
    
    def validate_invoice(self, ubl_invoice: UBLInvoice) -> ValidationResult:
        """
        Complete UBL invoice validation.
        
        Args:
            ubl_invoice: UBL invoice to validate
            
        Returns:
            ValidationResult: Comprehensive validation results
        """
        result = ValidationResult()
        
        try:
            # 1. Schema validation
            schema_result = self.validate_schema(ubl_invoice)
            self._merge_results(result, schema_result)
            
            # 2. Nigerian FIRS compliance
            firs_result = self.validate_firs_compliance(ubl_invoice)
            self._merge_results(result, firs_result)
            
            # 3. Mathematical accuracy
            math_result = self.validate_calculations(ubl_invoice)
            self._merge_results(result, math_result)
            
            # 4. Business rules (implemented by subclasses)
            business_result = self.validate_business_rules(ubl_invoice)
            self._merge_results(result, business_result)
            
            # 5. Tax validation
            tax_result = self.validate_tax_compliance(ubl_invoice)
            self._merge_results(result, tax_result)
            
            self.logger.info(f"UBL validation completed: {len(result.errors)} errors, {len(result.warnings)} warnings")
            
        except Exception as e:
            result.add_error(f"Validation process failed: {str(e)}")
            self.logger.error(f"UBL validation error: {str(e)}")
        
        return result
    
    def validate_schema(self, ubl_invoice: UBLInvoice) -> ValidationResult:
        """
        Validate UBL invoice against UBL 2.1 schema requirements.
        
        Args:
            ubl_invoice: UBL invoice to validate
            
        Returns:
            ValidationResult: Schema validation results
        """
        result = ValidationResult()
        
        # Required fields validation
        if not ubl_invoice.id:
            result.add_error("Invoice ID is required")
        
        if not ubl_invoice.issue_date:
            result.add_error("Issue date is required")
        
        if not ubl_invoice.invoice_type_code:
            result.add_error("Invoice type code is required")
        
        # Party validation
        if not ubl_invoice.supplier_party:
            result.add_error("Supplier party is required")
        else:
            self._validate_party(ubl_invoice.supplier_party, "Supplier", result)
        
        if not ubl_invoice.customer_party:
            result.add_error("Customer party is required")
        else:
            self._validate_party(ubl_invoice.customer_party, "Customer", result)
        
        # Invoice lines validation
        if not ubl_invoice.invoice_lines or len(ubl_invoice.invoice_lines) == 0:
            result.add_error("At least one invoice line is required")
        else:
            for i, line in enumerate(ubl_invoice.invoice_lines):
                self._validate_invoice_line(line, i + 1, result)
        
        # Legal monetary total validation
        if not ubl_invoice.legal_monetary_total:
            result.add_error("Legal monetary total is required")
        
        return result
    
    def validate_firs_compliance(self, ubl_invoice: UBLInvoice) -> ValidationResult:
        """
        Validate Nigerian FIRS e-invoicing compliance requirements.
        
        Args:
            ubl_invoice: UBL invoice to validate
            
        Returns:
            ValidationResult: FIRS compliance validation results
        """
        result = ValidationResult()
        
        # Nigerian business requirements
        if not ubl_invoice.id or len(ubl_invoice.id) < 3:
            result.add_error("FIRS requires invoice ID with minimum 3 characters")
        
        # Currency validation for Nigerian market
        if self.currency_validation:
            if hasattr(ubl_invoice, 'document_currency_code'):
                if ubl_invoice.document_currency_code not in ['NGN', 'USD', 'EUR', 'GBP']:
                    result.add_warning(f"Unusual currency for Nigerian market: {ubl_invoice.document_currency_code}")
        
        # Tax compliance (Nigerian VAT)
        if ubl_invoice.tax_total:
            for tax_subtotal in ubl_invoice.tax_total.tax_subtotals:
                if hasattr(tax_subtotal, 'tax_category') and tax_subtotal.tax_category:
                    if tax_subtotal.tax_category.id == "VAT":
                        expected_rate = self.nigerian_tax_rate
                        actual_rate = getattr(tax_subtotal.tax_category, 'percent', 0)
                        if abs(actual_rate - expected_rate) > 0.1:
                            result.add_warning(f"VAT rate {actual_rate}% differs from standard Nigerian VAT {expected_rate}%")
        
        # Supplier validation for Nigerian entities
        if ubl_invoice.supplier_party:
            self._validate_nigerian_entity(ubl_invoice.supplier_party, "Supplier", result)
        
        # Date validation
        if ubl_invoice.issue_date:
            if ubl_invoice.issue_date > datetime.now().date():
                result.add_error("FIRS does not allow future-dated invoices")
        
        return result
    
    def validate_calculations(self, ubl_invoice: UBLInvoice) -> ValidationResult:
        """
        Validate mathematical accuracy of UBL invoice calculations.
        
        Args:
            ubl_invoice: UBL invoice to validate
            
        Returns:
            ValidationResult: Calculation validation results
        """
        result = ValidationResult()
        
        if not ubl_invoice.invoice_lines or not ubl_invoice.legal_monetary_total:
            result.add_warning("Cannot validate calculations: missing invoice lines or monetary total")
            return result
        
        try:
            # Calculate expected totals
            calculated_line_total = sum(
                Decimal(str(line.line_extension_amount)) 
                for line in ubl_invoice.invoice_lines
            )
            
            # Validate line extension amount
            if ubl_invoice.legal_monetary_total.line_extension_amount is not None:
                stated_line_total = Decimal(str(ubl_invoice.legal_monetary_total.line_extension_amount))
                if abs(calculated_line_total - stated_line_total) > Decimal('0.01'):
                    result.add_error(f"Line extension amount mismatch: calculated {calculated_line_total}, stated {stated_line_total}")
            
            # Validate tax calculations
            calculated_tax_total = Decimal('0')
            for line in ubl_invoice.invoice_lines:
                if line.tax_total:
                    for tax_subtotal in line.tax_total.tax_subtotals:
                        calculated_tax_total += Decimal(str(tax_subtotal.tax_amount))
            
            if ubl_invoice.tax_total:
                stated_tax_total = sum(
                    Decimal(str(subtotal.tax_amount)) 
                    for subtotal in ubl_invoice.tax_total.tax_subtotals
                )
                if abs(calculated_tax_total - stated_tax_total) > Decimal('0.01'):
                    result.add_error(f"Tax total mismatch: calculated {calculated_tax_total}, stated {stated_tax_total}")
            
            # Validate payable amount
            if ubl_invoice.legal_monetary_total.payable_amount is not None:
                expected_payable = calculated_line_total + calculated_tax_total
                stated_payable = Decimal(str(ubl_invoice.legal_monetary_total.payable_amount))
                if abs(expected_payable - stated_payable) > Decimal('0.01'):
                    result.add_error(f"Payable amount mismatch: expected {expected_payable}, stated {stated_payable}")
        
        except (ValueError, TypeError, AttributeError) as e:
            result.add_error(f"Calculation validation error: {str(e)}")
        
        return result
    
    def validate_tax_compliance(self, ubl_invoice: UBLInvoice) -> ValidationResult:
        """
        Validate tax compliance and calculations.
        
        Args:
            ubl_invoice: UBL invoice to validate
            
        Returns:
            ValidationResult: Tax validation results
        """
        result = ValidationResult()
        
        # Check if tax information is present
        if not ubl_invoice.tax_total:
            result.add_warning("No tax total information found")
            return result
        
        # Validate tax categories and rates
        for tax_subtotal in ubl_invoice.tax_total.tax_subtotals:
            if not tax_subtotal.tax_category:
                result.add_error("Tax category is required for tax subtotal")
                continue
            
            # Nigerian VAT validation
            if tax_subtotal.tax_category.id == "VAT":
                if not hasattr(tax_subtotal.tax_category, 'percent'):
                    result.add_error("VAT rate percentage is required")
                else:
                    rate = tax_subtotal.tax_category.percent
                    if rate < 0 or rate > 100:
                        result.add_error(f"Invalid VAT rate: {rate}%")
                    elif rate != self.nigerian_tax_rate:
                        result.add_info(f"Non-standard VAT rate: {rate}% (standard: {self.nigerian_tax_rate}%)")
        
        return result
    
    def _validate_party(self, party, party_type: str, result: ValidationResult):
        """Validate UBL party information."""
        if not party.party_name or not party.party_name.name:
            result.add_error(f"{party_type} name is required")
        
        if not party.postal_address:
            result.add_warning(f"{party_type} address is recommended")
        
        if hasattr(party, 'contact') and party.contact:
            if not party.contact.electronic_mail and not party.contact.telephone:
                result.add_warning(f"{party_type} contact information (email or phone) is recommended")
    
    def _validate_invoice_line(self, line, line_number: int, result: ValidationResult):
        """Validate UBL invoice line."""
        if not line.id:
            result.add_error(f"Line {line_number}: Line ID is required")
        
        if not line.invoiced_quantity or line.invoiced_quantity.value <= 0:
            result.add_error(f"Line {line_number}: Positive invoiced quantity is required")
        
        if not line.line_extension_amount or line.line_extension_amount < 0:
            result.add_error(f"Line {line_number}: Non-negative line extension amount is required")
        
        if not line.item or not line.item.name:
            result.add_error(f"Line {line_number}: Item name is required")
    
    def _validate_nigerian_entity(self, party, party_type: str, result: ValidationResult):
        """Validate Nigerian business entity requirements."""
        # Check for Nigerian address
        if party.postal_address:
            if hasattr(party.postal_address, 'country_identification_code'):
                if party.postal_address.country_identification_code != 'NG':
                    result.add_info(f"{party_type} is not a Nigerian entity")
        
        # Check for Nigerian phone number format
        if hasattr(party, 'contact') and party.contact and party.contact.telephone:
            phone = party.contact.telephone
            if not self._is_nigerian_phone(phone):
                result.add_info(f"{party_type} phone number may not be Nigerian format")
    
    def _is_nigerian_phone(self, phone: str) -> bool:
        """Check if phone number appears to be Nigerian format."""
        if not phone:
            return False
        
        # Nigerian phone patterns
        patterns = [
            r'^\+234[0-9]{10}$',  # +234xxxxxxxxxx
            r'^234[0-9]{10}$',    # 234xxxxxxxxxx
            r'^0[0-9]{10}$',      # 0xxxxxxxxxx
            r'^[0-9]{10}$'        # xxxxxxxxxx
        ]
        
        return any(re.match(pattern, phone) for pattern in patterns)
    
    def _merge_results(self, main_result: ValidationResult, additional_result: ValidationResult):
        """Merge additional validation results into main result."""
        main_result.errors.extend(additional_result.errors)
        main_result.warnings.extend(additional_result.warnings)
        main_result.info.extend(additional_result.info)
        if not additional_result.is_valid:
            main_result.is_valid = False