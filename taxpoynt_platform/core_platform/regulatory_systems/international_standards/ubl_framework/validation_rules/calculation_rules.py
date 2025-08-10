"""
UBL Calculation Rules
====================
Mathematical validation rules for UBL invoice calculations and totals.
"""
from typing import List, Dict, Any
from decimal import Decimal, ROUND_HALF_UP
import math

from ..base_ubl_validator import ValidationResult
from ..ubl_models import UBLInvoice


class CalculationRules:
    """
    UBL calculation validation rules.
    
    Validates mathematical accuracy of invoice calculations,
    tax computations, and monetary totals.
    """
    
    # Tolerance for floating point comparisons (0.01 for currency)
    CALCULATION_TOLERANCE = Decimal('0.01')
    
    @staticmethod
    def validate_line_calculations(ubl_invoice: UBLInvoice) -> ValidationResult:
        """Validate invoice line mathematical calculations."""
        result = ValidationResult()
        
        if not ubl_invoice.invoice_lines:
            return result
        
        for i, line in enumerate(ubl_invoice.invoice_lines, 1):
            line_prefix = f"Line {i}"
            
            # Validate quantity × price = line extension amount
            if (line.invoiced_quantity and line.invoiced_quantity.value and 
                line.price and line.price.price_amount is not None and 
                line.line_extension_amount is not None):
                
                quantity = Decimal(str(line.invoiced_quantity.value))
                price = Decimal(str(line.price.price_amount))
                stated_amount = Decimal(str(line.line_extension_amount))
                
                # Calculate expected amount
                expected_amount = quantity * price
                
                # Handle base quantity if specified
                if hasattr(line.price, 'base_quantity') and line.price.base_quantity:
                    base_qty = Decimal(str(line.price.base_quantity.value))
                    if base_qty != 0:
                        expected_amount = (quantity * price) / base_qty
                
                # Round to 2 decimal places
                expected_amount = expected_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                
                # Compare with tolerance
                if abs(expected_amount - stated_amount) > CalculationRules.CALCULATION_TOLERANCE:
                    result.add_error(f"{line_prefix}: Line extension calculation error: "
                                   f"{quantity} × {price} = {expected_amount}, but stated {stated_amount} (CALC-01)")
            
            # Validate line-level tax calculations
            if line.tax_total and line.tax_total.tax_subtotals:
                line_tax_total = Decimal('0')
                
                for tax_subtotal in line.tax_total.tax_subtotals:
                    if tax_subtotal.tax_amount:
                        line_tax_total += Decimal(str(tax_subtotal.tax_amount))
                    
                    # Validate individual tax calculation
                    if (tax_subtotal.taxable_amount and tax_subtotal.tax_amount and 
                        tax_subtotal.tax_category and hasattr(tax_subtotal.tax_category, 'percent')):
                        
                        taxable = Decimal(str(tax_subtotal.taxable_amount))
                        tax_rate = Decimal(str(tax_subtotal.tax_category.percent))
                        stated_tax = Decimal(str(tax_subtotal.tax_amount))
                        
                        expected_tax = (taxable * tax_rate / 100).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                        
                        if abs(expected_tax - stated_tax) > CalculationRules.CALCULATION_TOLERANCE:
                            result.add_error(f"{line_prefix}: Tax calculation error: "
                                           f"{taxable} × {tax_rate}% = {expected_tax}, but stated {stated_tax} (CALC-02)")
                
                # Validate line tax total
                if hasattr(line.tax_total, 'tax_amount') and line.tax_total.tax_amount:
                    stated_line_tax_total = Decimal(str(line.tax_total.tax_amount))
                    if abs(line_tax_total - stated_line_tax_total) > CalculationRules.CALCULATION_TOLERANCE:
                        result.add_error(f"{line_prefix}: Line tax total mismatch: "
                                       f"calculated {line_tax_total}, stated {stated_line_tax_total} (CALC-03)")
        
        return result
    
    @staticmethod
    def validate_monetary_totals(ubl_invoice: UBLInvoice) -> ValidationResult:
        """Validate legal monetary total calculations."""
        result = ValidationResult()
        
        if not ubl_invoice.legal_monetary_total or not ubl_invoice.invoice_lines:
            return result
        
        totals = ubl_invoice.legal_monetary_total
        
        # Calculate line extension total
        calculated_line_total = Decimal('0')
        for line in ubl_invoice.invoice_lines:
            if line.line_extension_amount is not None:
                calculated_line_total += Decimal(str(line.line_extension_amount))
        
        # Validate line extension amount
        if totals.line_extension_amount is not None:
            stated_line_total = Decimal(str(totals.line_extension_amount))
            if abs(calculated_line_total - stated_line_total) > CalculationRules.CALCULATION_TOLERANCE:
                result.add_error(f"Line extension total mismatch: "
                               f"calculated {calculated_line_total}, stated {stated_line_total} (CALC-04)")
        
        # Calculate allowances and charges
        allowance_total = Decimal('0')
        charge_total = Decimal('0')
        
        # If allowance charges are specified at document level
        if hasattr(ubl_invoice, 'allowance_charges'):
            for allowance_charge in getattr(ubl_invoice, 'allowance_charges', []):
                amount = Decimal(str(allowance_charge.amount)) if allowance_charge.amount else Decimal('0')
                if getattr(allowance_charge, 'charge_indicator', False):
                    charge_total += amount
                else:
                    allowance_total += amount
        
        # Calculate tax exclusive amount
        expected_tax_exclusive = calculated_line_total - allowance_total + charge_total
        
        if totals.tax_exclusive_amount is not None:
            stated_tax_exclusive = Decimal(str(totals.tax_exclusive_amount))
            if abs(expected_tax_exclusive - stated_tax_exclusive) > CalculationRules.CALCULATION_TOLERANCE:
                result.add_error(f"Tax exclusive amount mismatch: "
                               f"calculated {expected_tax_exclusive}, stated {stated_tax_exclusive} (CALC-05)")
        
        # Validate allowance and charge totals
        if totals.allowance_total_amount is not None:
            stated_allowance_total = Decimal(str(totals.allowance_total_amount))
            if abs(allowance_total - stated_allowance_total) > CalculationRules.CALCULATION_TOLERANCE:
                result.add_error(f"Allowance total mismatch: "
                               f"calculated {allowance_total}, stated {stated_allowance_total} (CALC-06)")
        
        if totals.charge_total_amount is not None:
            stated_charge_total = Decimal(str(totals.charge_total_amount))
            if abs(charge_total - stated_charge_total) > CalculationRules.CALCULATION_TOLERANCE:
                result.add_error(f"Charge total mismatch: "
                               f"calculated {charge_total}, stated {stated_charge_total} (CALC-07)")
        
        return result
    
    @staticmethod
    def validate_tax_totals(ubl_invoice: UBLInvoice) -> ValidationResult:
        """Validate tax total calculations."""
        result = ValidationResult()
        
        if not ubl_invoice.tax_total:
            return result
        
        # Calculate total tax from subtotals
        calculated_tax_total = Decimal('0')
        
        if ubl_invoice.tax_total.tax_subtotals:
            for tax_subtotal in ubl_invoice.tax_total.tax_subtotals:
                if tax_subtotal.tax_amount:
                    calculated_tax_total += Decimal(str(tax_subtotal.tax_amount))
        
        # Also sum tax from all invoice lines
        calculated_line_tax_total = Decimal('0')
        if ubl_invoice.invoice_lines:
            for line in ubl_invoice.invoice_lines:
                if line.tax_total and line.tax_total.tax_subtotals:
                    for tax_subtotal in line.tax_total.tax_subtotals:
                        if tax_subtotal.tax_amount:
                            calculated_line_tax_total += Decimal(str(tax_subtotal.tax_amount))
        
        # Validate document-level tax total
        if ubl_invoice.tax_total.tax_amount is not None:
            stated_tax_total = Decimal(str(ubl_invoice.tax_total.tax_amount))
            
            # Use the higher of document-level or line-level calculation
            expected_tax_total = max(calculated_tax_total, calculated_line_tax_total)
            
            if abs(expected_tax_total - stated_tax_total) > CalculationRules.CALCULATION_TOLERANCE:
                result.add_error(f"Tax total mismatch: "
                               f"calculated {expected_tax_total}, stated {stated_tax_total} (CALC-08)")
        
        # Cross-validate with legal monetary total
        if (ubl_invoice.legal_monetary_total and 
            ubl_invoice.legal_monetary_total.tax_exclusive_amount is not None and
            ubl_invoice.legal_monetary_total.tax_inclusive_amount is not None):
            
            tax_exclusive = Decimal(str(ubl_invoice.legal_monetary_total.tax_exclusive_amount))
            tax_inclusive = Decimal(str(ubl_invoice.legal_monetary_total.tax_inclusive_amount))
            
            expected_tax_from_totals = tax_inclusive - tax_exclusive
            
            if ubl_invoice.tax_total.tax_amount is not None:
                stated_tax_total = Decimal(str(ubl_invoice.tax_total.tax_amount))
                
                if abs(expected_tax_from_totals - stated_tax_total) > CalculationRules.CALCULATION_TOLERANCE:
                    result.add_error(f"Tax total inconsistent with monetary totals: "
                                   f"tax inclusive - tax exclusive = {expected_tax_from_totals}, "
                                   f"but tax total = {stated_tax_total} (CALC-09)")
        
        return result
    
    @staticmethod
    def validate_final_totals(ubl_invoice: UBLInvoice) -> ValidationResult:
        """Validate final payable amounts and totals."""
        result = ValidationResult()
        
        if not ubl_invoice.legal_monetary_total:
            return result
        
        totals = ubl_invoice.legal_monetary_total
        
        # Validate tax inclusive amount
        if (totals.tax_exclusive_amount is not None and 
            totals.tax_inclusive_amount is not None):
            
            tax_exclusive = Decimal(str(totals.tax_exclusive_amount))
            tax_inclusive = Decimal(str(totals.tax_inclusive_amount))
            
            # Calculate expected tax inclusive amount
            tax_amount = Decimal('0')
            if ubl_invoice.tax_total and ubl_invoice.tax_total.tax_amount is not None:
                tax_amount = Decimal(str(ubl_invoice.tax_total.tax_amount))
            
            expected_tax_inclusive = tax_exclusive + tax_amount
            
            if abs(expected_tax_inclusive - tax_inclusive) > CalculationRules.CALCULATION_TOLERANCE:
                result.add_error(f"Tax inclusive amount mismatch: "
                               f"{tax_exclusive} + {tax_amount} = {expected_tax_inclusive}, "
                               f"but stated {tax_inclusive} (CALC-10)")
        
        # Validate payable amount
        if (totals.tax_inclusive_amount is not None and 
            totals.payable_amount is not None):
            
            tax_inclusive = Decimal(str(totals.tax_inclusive_amount))
            payable = Decimal(str(totals.payable_amount))
            
            # Calculate adjustments (prepaid amounts, rounding, etc.)
            adjustments = Decimal('0')
            
            # Add prepaid amount if specified
            if hasattr(totals, 'prepaid_amount') and totals.prepaid_amount is not None:
                adjustments += Decimal(str(totals.prepaid_amount))
            
            # Add rounding amount if specified
            if hasattr(totals, 'payable_rounding_amount') and totals.payable_rounding_amount is not None:
                adjustments += Decimal(str(totals.payable_rounding_amount))
            
            expected_payable = tax_inclusive - adjustments
            
            if abs(expected_payable - payable) > CalculationRules.CALCULATION_TOLERANCE:
                result.add_error(f"Payable amount mismatch: "
                               f"{tax_inclusive} - {adjustments} = {expected_payable}, "
                               f"but stated {payable} (CALC-11)")
        
        return result
    
    @staticmethod
    def validate_rounding_consistency(ubl_invoice: UBLInvoice) -> ValidationResult:
        """Validate rounding consistency across all calculations."""
        result = ValidationResult()
        
        # Check all monetary amounts for consistent decimal places
        amounts_to_check = []
        
        # Collect amounts from legal monetary total
        if ubl_invoice.legal_monetary_total:
            totals = ubl_invoice.legal_monetary_total
            for field in ['line_extension_amount', 'tax_exclusive_amount', 
                         'tax_inclusive_amount', 'payable_amount']:
                value = getattr(totals, field, None)
                if value is not None:
                    amounts_to_check.append((f"Monetary total {field}", Decimal(str(value))))
        
        # Collect amounts from invoice lines
        if ubl_invoice.invoice_lines:
            for i, line in enumerate(ubl_invoice.invoice_lines, 1):
                if line.line_extension_amount is not None:
                    amounts_to_check.append((f"Line {i} extension amount", Decimal(str(line.line_extension_amount))))
                
                if line.price and line.price.price_amount is not None:
                    amounts_to_check.append((f"Line {i} price amount", Decimal(str(line.price.price_amount))))
        
        # Collect amounts from tax totals
        if ubl_invoice.tax_total:
            if ubl_invoice.tax_total.tax_amount is not None:
                amounts_to_check.append(("Tax total amount", Decimal(str(ubl_invoice.tax_total.tax_amount))))
            
            if ubl_invoice.tax_total.tax_subtotals:
                for i, subtotal in enumerate(ubl_invoice.tax_total.tax_subtotals, 1):
                    if subtotal.tax_amount is not None:
                        amounts_to_check.append((f"Tax subtotal {i} amount", Decimal(str(subtotal.tax_amount))))
        
        # Check decimal places consistency
        decimal_places = set()
        for field_name, amount in amounts_to_check:
            places = abs(amount.as_tuple().exponent)
            decimal_places.add(places)
            
            # Warn about unusual precision
            if places > 2:
                result.add_warning(f"{field_name} has {places} decimal places, "
                                 f"which may cause rounding issues (CALC-12)")
        
        # Check for mixed decimal precision
        if len(decimal_places) > 2:  # Allow 0 and 2 decimal places
            result.add_info(f"Mixed decimal precision found: {sorted(decimal_places)} decimal places (CALC-13)")
        
        return result