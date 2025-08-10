"""
Standard UBL Validation Rules
============================
Core UBL 2.1 schema validation rules and international standards compliance.
"""
from typing import List, Dict, Any
from datetime import datetime, date
from decimal import Decimal
import re

from ..base_ubl_validator import ValidationResult
from ..ubl_models import UBLInvoice


class StandardUBLRules:
    """
    Standard UBL 2.1 validation rules.
    
    Implements core UBL schema requirements and international standards
    for invoice document validation.
    """
    
    @staticmethod
    def validate_document_structure(ubl_invoice: UBLInvoice) -> ValidationResult:
        """Validate basic UBL document structure."""
        result = ValidationResult()
        
        # Required root elements
        if not ubl_invoice.id:
            result.add_error("Invoice ID is mandatory (UBL-SR-01)")
        elif len(ubl_invoice.id) > 100:
            result.add_error("Invoice ID must not exceed 100 characters (UBL-SR-02)")
        
        if not ubl_invoice.issue_date:
            result.add_error("Issue date is mandatory (UBL-SR-03)")
        
        if not ubl_invoice.invoice_type_code:
            result.add_error("Invoice type code is mandatory (UBL-SR-04)")
        elif ubl_invoice.invoice_type_code not in ['380', '381', '383', '386', '393', '395']:
            result.add_warning(f"Non-standard invoice type code: {ubl_invoice.invoice_type_code} (UBL-SR-05)")
        
        return result
    
    @staticmethod
    def validate_party_information(ubl_invoice: UBLInvoice) -> ValidationResult:
        """Validate supplier and customer party information."""
        result = ValidationResult()
        
        # Supplier party validation
        if not ubl_invoice.supplier_party:
            result.add_error("Supplier party is mandatory (UBL-SR-06)")
        else:
            supplier = ubl_invoice.supplier_party
            
            if not supplier.party_name or not supplier.party_name.name:
                result.add_error("Supplier party name is mandatory (UBL-SR-07)")
            
            if not supplier.postal_address:
                result.add_warning("Supplier postal address is recommended (UBL-SR-08)")
            elif supplier.postal_address:
                if not supplier.postal_address.country_identification_code:
                    result.add_error("Supplier country code is mandatory (UBL-SR-09)")
                elif len(supplier.postal_address.country_identification_code) != 2:
                    result.add_error("Supplier country code must be ISO 3166-1 alpha-2 (UBL-SR-10)")
        
        # Customer party validation
        if not ubl_invoice.customer_party:
            result.add_error("Customer party is mandatory (UBL-SR-11)")
        else:
            customer = ubl_invoice.customer_party
            
            if not customer.party_name or not customer.party_name.name:
                result.add_error("Customer party name is mandatory (UBL-SR-12)")
            
            if not customer.postal_address:
                result.add_warning("Customer postal address is recommended (UBL-SR-13)")
            elif customer.postal_address:
                if not customer.postal_address.country_identification_code:
                    result.add_error("Customer country code is mandatory (UBL-SR-14)")
        
        return result
    
    @staticmethod
    def validate_invoice_lines(ubl_invoice: UBLInvoice) -> ValidationResult:
        """Validate invoice line items."""
        result = ValidationResult()
        
        if not ubl_invoice.invoice_lines:
            result.add_error("At least one invoice line is mandatory (UBL-SR-15)")
            return result
        
        for i, line in enumerate(ubl_invoice.invoice_lines, 1):
            line_prefix = f"Line {i}"
            
            # Line ID
            if not line.id:
                result.add_error(f"{line_prefix}: Line ID is mandatory (UBL-SR-16)")
            
            # Invoiced quantity
            if not line.invoiced_quantity:
                result.add_error(f"{line_prefix}: Invoiced quantity is mandatory (UBL-SR-17)")
            elif line.invoiced_quantity.value <= 0:
                result.add_error(f"{line_prefix}: Invoiced quantity must be positive (UBL-SR-18)")
            elif not line.invoiced_quantity.unit_code:
                result.add_warning(f"{line_prefix}: Unit code is recommended (UBL-SR-19)")
            
            # Line extension amount
            if line.line_extension_amount is None:
                result.add_error(f"{line_prefix}: Line extension amount is mandatory (UBL-SR-20)")
            elif line.line_extension_amount < 0:
                result.add_error(f"{line_prefix}: Line extension amount cannot be negative (UBL-SR-21)")
            
            # Item information
            if not line.item:
                result.add_error(f"{line_prefix}: Item is mandatory (UBL-SR-22)")
            elif not line.item.name:
                result.add_error(f"{line_prefix}: Item name is mandatory (UBL-SR-23)")
            
            # Price information
            if not line.price:
                result.add_warning(f"{line_prefix}: Price information is recommended (UBL-SR-24)")
            elif line.price.price_amount is not None and line.price.price_amount < 0:
                result.add_error(f"{line_prefix}: Price amount cannot be negative (UBL-SR-25)")
        
        return result
    
    @staticmethod
    def validate_monetary_totals(ubl_invoice: UBLInvoice) -> ValidationResult:
        """Validate legal monetary totals."""
        result = ValidationResult()
        
        if not ubl_invoice.legal_monetary_total:
            result.add_error("Legal monetary total is mandatory (UBL-SR-26)")
            return result
        
        totals = ubl_invoice.legal_monetary_total
        
        # Required amounts
        if totals.line_extension_amount is None:
            result.add_error("Line extension amount is mandatory (UBL-SR-27)")
        elif totals.line_extension_amount < 0:
            result.add_error("Line extension amount cannot be negative (UBL-SR-28)")
        
        if totals.tax_exclusive_amount is None:
            result.add_error("Tax exclusive amount is mandatory (UBL-SR-29)")
        elif totals.tax_exclusive_amount < 0:
            result.add_error("Tax exclusive amount cannot be negative (UBL-SR-30)")
        
        if totals.tax_inclusive_amount is None:
            result.add_error("Tax inclusive amount is mandatory (UBL-SR-31)")
        elif totals.tax_inclusive_amount < 0:
            result.add_error("Tax inclusive amount cannot be negative (UBL-SR-32)")
        
        if totals.payable_amount is None:
            result.add_error("Payable amount is mandatory (UBL-SR-33)")
        elif totals.payable_amount < 0:
            result.add_error("Payable amount cannot be negative (UBL-SR-34)")
        
        return result
    
    @staticmethod
    def validate_tax_information(ubl_invoice: UBLInvoice) -> ValidationResult:
        """Validate tax totals and categories."""
        result = ValidationResult()
        
        if not ubl_invoice.tax_total:
            result.add_warning("Tax total information is recommended (UBL-SR-35)")
            return result
        
        # Tax total amount
        if ubl_invoice.tax_total.tax_amount is None:
            result.add_error("Tax total amount is mandatory when tax total is present (UBL-SR-36)")
        elif ubl_invoice.tax_total.tax_amount < 0:
            result.add_error("Tax total amount cannot be negative (UBL-SR-37)")
        
        # Tax subtotals
        if not ubl_invoice.tax_total.tax_subtotals:
            result.add_warning("Tax subtotals are recommended when tax total is present (UBL-SR-38)")
        else:
            for i, subtotal in enumerate(ubl_invoice.tax_total.tax_subtotals, 1):
                subtotal_prefix = f"Tax subtotal {i}"
                
                if subtotal.taxable_amount is None:
                    result.add_error(f"{subtotal_prefix}: Taxable amount is mandatory (UBL-SR-39)")
                elif subtotal.taxable_amount < 0:
                    result.add_error(f"{subtotal_prefix}: Taxable amount cannot be negative (UBL-SR-40)")
                
                if subtotal.tax_amount is None:
                    result.add_error(f"{subtotal_prefix}: Tax amount is mandatory (UBL-SR-41)")
                elif subtotal.tax_amount < 0:
                    result.add_error(f"{subtotal_prefix}: Tax amount cannot be negative (UBL-SR-42)")
                
                if not subtotal.tax_category:
                    result.add_error(f"{subtotal_prefix}: Tax category is mandatory (UBL-SR-43)")
                elif not subtotal.tax_category.id:
                    result.add_error(f"{subtotal_prefix}: Tax category ID is mandatory (UBL-SR-44)")
        
        return result
    
    @staticmethod
    def validate_currency_codes(ubl_invoice: UBLInvoice) -> ValidationResult:
        """Validate currency codes according to ISO 4217."""
        result = ValidationResult()
        
        # Common currency codes for validation
        valid_currencies = {
            'AED', 'AFN', 'ALL', 'AMD', 'ANG', 'AOA', 'ARS', 'AUD', 'AWG', 'AZN',
            'BAM', 'BBD', 'BDT', 'BGN', 'BHD', 'BIF', 'BMD', 'BND', 'BOB', 'BRL', 'BSD', 'BTN', 'BWP', 'BYN', 'BZD',
            'CAD', 'CDF', 'CHF', 'CLP', 'CNY', 'COP', 'CRC', 'CUC', 'CUP', 'CVE', 'CZK',
            'DJF', 'DKK', 'DOP', 'DZD',
            'EGP', 'ERN', 'ETB', 'EUR',
            'FJD', 'FKP',
            'GBP', 'GEL', 'GHS', 'GIP', 'GMD', 'GNF', 'GTQ', 'GYD',
            'HKD', 'HNL', 'HRK', 'HTG', 'HUF',
            'IDR', 'ILS', 'INR', 'IQD', 'IRR', 'ISK',
            'JMD', 'JOD', 'JPY',
            'KES', 'KGS', 'KHR', 'KMF', 'KPW', 'KRW', 'KWD', 'KYD', 'KZT',
            'LAK', 'LBP', 'LKR', 'LRD', 'LSL', 'LYD',
            'MAD', 'MDL', 'MGA', 'MKD', 'MMK', 'MNT', 'MOP', 'MRU', 'MUR', 'MVR', 'MWK', 'MXN', 'MYR', 'MZN',
            'NAD', 'NGN', 'NIO', 'NOK', 'NPR', 'NZD',
            'OMR',
            'PAB', 'PEN', 'PGK', 'PHP', 'PKR', 'PLN', 'PYG',
            'QAR',
            'RON', 'RSD', 'RUB', 'RWF',
            'SAR', 'SBD', 'SCR', 'SDG', 'SEK', 'SGD', 'SHP', 'SLE', 'SLL', 'SOS', 'SRD', 'STN', 'SYP', 'SZL',
            'THB', 'TJS', 'TMT', 'TND', 'TOP', 'TRY', 'TTD', 'TVD', 'TWD', 'TZS',
            'UAH', 'UGX', 'USD', 'UYU', 'UZS',
            'VED', 'VES', 'VND', 'VUV',
            'WST',
            'XAF', 'XCD', 'XDR', 'XOF', 'XPF',
            'YER',
            'ZAR', 'ZMW', 'ZWL'
        }
        
        # Document currency
        if hasattr(ubl_invoice, 'document_currency_code') and ubl_invoice.document_currency_code:
            if ubl_invoice.document_currency_code not in valid_currencies:
                result.add_error(f"Invalid document currency code: {ubl_invoice.document_currency_code} (UBL-SR-45)")
        
        # Tax currency
        if hasattr(ubl_invoice, 'tax_currency_code') and ubl_invoice.tax_currency_code:
            if ubl_invoice.tax_currency_code not in valid_currencies:
                result.add_error(f"Invalid tax currency code: {ubl_invoice.tax_currency_code} (UBL-SR-46)")
        
        return result
    
    @staticmethod
    def validate_date_formats(ubl_invoice: UBLInvoice) -> ValidationResult:
        """Validate date formats and logical consistency."""
        result = ValidationResult()
        
        # Issue date validation
        if ubl_invoice.issue_date:
            if isinstance(ubl_invoice.issue_date, str):
                try:
                    datetime.strptime(ubl_invoice.issue_date, '%Y-%m-%d')
                except ValueError:
                    result.add_error("Issue date must be in YYYY-MM-DD format (UBL-SR-47)")
            
            # Future date check
            if isinstance(ubl_invoice.issue_date, (date, datetime)):
                issue_date = ubl_invoice.issue_date
                if isinstance(issue_date, datetime):
                    issue_date = issue_date.date()
                if issue_date > date.today():
                    result.add_warning("Issue date is in the future (UBL-SR-48)")
        
        # Due date validation
        if hasattr(ubl_invoice, 'due_date') and ubl_invoice.due_date:
            if isinstance(ubl_invoice.due_date, str):
                try:
                    datetime.strptime(ubl_invoice.due_date, '%Y-%m-%d')
                except ValueError:
                    result.add_error("Due date must be in YYYY-MM-DD format (UBL-SR-49)")
            
            # Due date should be after or equal to issue date
            if ubl_invoice.issue_date and ubl_invoice.due_date:
                try:
                    if isinstance(ubl_invoice.issue_date, str):
                        issue_date = datetime.strptime(ubl_invoice.issue_date, '%Y-%m-%d').date()
                    else:
                        issue_date = ubl_invoice.issue_date
                        if isinstance(issue_date, datetime):
                            issue_date = issue_date.date()
                    
                    if isinstance(ubl_invoice.due_date, str):
                        due_date = datetime.strptime(ubl_invoice.due_date, '%Y-%m-%d').date()
                    else:
                        due_date = ubl_invoice.due_date
                        if isinstance(due_date, datetime):
                            due_date = due_date.date()
                    
                    if due_date < issue_date:
                        result.add_error("Due date cannot be before issue date (UBL-SR-50)")
                        
                except (ValueError, AttributeError, TypeError):
                    result.add_warning("Could not validate date relationship (UBL-SR-51)")
        
        return result
    
    @staticmethod
    def validate_numeric_formats(ubl_invoice: UBLInvoice) -> ValidationResult:
        """Validate numeric formats and precision."""
        result = ValidationResult()
        
        # Check monetary amounts for reasonable precision (max 2 decimal places for most currencies)
        def check_decimal_precision(amount: float, field_name: str, max_decimals: int = 2):
            if amount is not None:
                decimal_amount = Decimal(str(amount))
                decimal_places = abs(decimal_amount.as_tuple().exponent)
                if decimal_places > max_decimals:
                    result.add_warning(f"{field_name} has more than {max_decimals} decimal places (UBL-SR-52)")
        
        # Check legal monetary total amounts
        if ubl_invoice.legal_monetary_total:
            totals = ubl_invoice.legal_monetary_total
            check_decimal_precision(totals.line_extension_amount, "Line extension amount")
            check_decimal_precision(totals.tax_exclusive_amount, "Tax exclusive amount")
            check_decimal_precision(totals.tax_inclusive_amount, "Tax inclusive amount")
            check_decimal_precision(totals.payable_amount, "Payable amount")
        
        # Check invoice line amounts
        if ubl_invoice.invoice_lines:
            for i, line in enumerate(ubl_invoice.invoice_lines, 1):
                check_decimal_precision(line.line_extension_amount, f"Line {i} extension amount")
                if line.price and line.price.price_amount is not None:
                    check_decimal_precision(line.price.price_amount, f"Line {i} price amount")
        
        return result