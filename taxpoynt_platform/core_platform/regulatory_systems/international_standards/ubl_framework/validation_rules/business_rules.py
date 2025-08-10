"""
UBL Business Rules
=================
Business logic validation rules for UBL invoices.
Industry-specific and contextual validation rules.
"""
from typing import List, Dict, Any, Set
from datetime import datetime, date, timedelta
from decimal import Decimal
import re

from ..base_ubl_validator import ValidationResult
from ..ubl_models import UBLInvoice


class BusinessRules:
    """
    UBL business logic validation rules.
    
    Implements business context validation, industry-specific rules,
    and logical consistency checks for invoice data.
    """
    
    # Common business sectors and their validation rules
    BUSINESS_SECTORS = {
        'RETAIL': {
            'typical_payment_terms': [7, 14, 30],
            'common_currencies': ['NGN', 'USD'],
            'max_line_items': 100
        },
        'MANUFACTURING': {
            'typical_payment_terms': [30, 45, 60, 90],
            'common_currencies': ['NGN', 'USD', 'EUR'],
            'max_line_items': 500
        },
        'SERVICES': {
            'typical_payment_terms': [30, 45],
            'common_currencies': ['NGN', 'USD'],
            'max_line_items': 50
        },
        'CONSTRUCTION': {
            'typical_payment_terms': [30, 60, 90],
            'common_currencies': ['NGN', 'USD'],
            'max_line_items': 200
        }
    }
    
    @staticmethod
    def validate_business_context(ubl_invoice: UBLInvoice, business_context: Dict[str, Any] = None) -> ValidationResult:
        """Validate invoice against business context."""
        result = ValidationResult()
        
        if not business_context:
            return result
        
        business_sector = business_context.get('sector', '').upper()
        
        if business_sector in BusinessRules.BUSINESS_SECTORS:
            sector_rules = BusinessRules.BUSINESS_SECTORS[business_sector]
            
            # Validate payment terms
            if hasattr(ubl_invoice, 'payment_terms') and ubl_invoice.payment_terms:
                payment_days = BusinessRules._extract_payment_days(ubl_invoice.payment_terms)
                if payment_days and payment_days not in sector_rules['typical_payment_terms']:
                    result.add_info(f"Unusual payment terms for {business_sector} sector: {payment_days} days (BUS-01)")
            
            # Validate currency
            if hasattr(ubl_invoice, 'document_currency_code') and ubl_invoice.document_currency_code:
                if ubl_invoice.document_currency_code not in sector_rules['common_currencies']:
                    result.add_info(f"Unusual currency for {business_sector} sector: {ubl_invoice.document_currency_code} (BUS-02)")
            
            # Validate line item count
            if ubl_invoice.invoice_lines:
                line_count = len(ubl_invoice.invoice_lines)
                if line_count > sector_rules['max_line_items']:
                    result.add_warning(f"High number of line items for {business_sector} sector: {line_count} (BUS-03)")
        
        return result
    
    @staticmethod
    def validate_payment_terms(ubl_invoice: UBLInvoice) -> ValidationResult:
        """Validate payment terms and due dates."""
        result = ValidationResult()
        
        # Validate due date vs issue date
        if ubl_invoice.issue_date and hasattr(ubl_invoice, 'due_date') and ubl_invoice.due_date:
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
                
                payment_days = (due_date - issue_date).days
                
                # Business logic checks
                if payment_days < 0:
                    result.add_error("Due date cannot be before issue date (BUS-04)")
                elif payment_days == 0:
                    result.add_info("Payment due immediately (same day) (BUS-05)")
                elif payment_days > 365:
                    result.add_warning(f"Very long payment terms: {payment_days} days (BUS-06)")
                elif payment_days > 180:
                    result.add_info(f"Long payment terms: {payment_days} days (BUS-07)")
                
                # Common payment terms validation
                common_terms = [7, 14, 15, 30, 45, 60, 90, 120]
                if payment_days not in common_terms and payment_days > 0:
                    closest_term = min(common_terms, key=lambda x: abs(x - payment_days))
                    result.add_info(f"Unusual payment terms: {payment_days} days (closest standard: {closest_term}) (BUS-08)")
                    
            except (ValueError, AttributeError, TypeError):
                result.add_warning("Could not validate payment terms due to date format issues (BUS-09)")
        
        return result
    
    @staticmethod
    def validate_invoice_amounts(ubl_invoice: UBLInvoice) -> ValidationResult:
        """Validate invoice amounts for business reasonableness."""
        result = ValidationResult()
        
        if not ubl_invoice.legal_monetary_total:
            return result
        
        totals = ubl_invoice.legal_monetary_total
        
        # Check for zero-amount invoices
        if totals.payable_amount is not None:
            payable = Decimal(str(totals.payable_amount))
            
            if payable == 0:
                result.add_info("Zero-amount invoice detected (BUS-10)")
            elif payable < 0:
                result.add_warning("Negative invoice amount - ensure this is a credit note (BUS-11)")
            elif payable > Decimal('10000000'):  # 10 million threshold
                result.add_info(f"Very high invoice amount: {payable} (BUS-12)")
        
        # Validate line item amounts
        if ubl_invoice.invoice_lines:
            for i, line in enumerate(ubl_invoice.invoice_lines, 1):
                if line.line_extension_amount is not None:
                    line_amount = Decimal(str(line.line_extension_amount))
                    
                    if line_amount == 0:
                        result.add_info(f"Line {i}: Zero-amount line item (BUS-13)")
                    elif line_amount < 0:
                        result.add_warning(f"Line {i}: Negative line amount (BUS-14)")
                
                # Check quantity reasonableness
                if line.invoiced_quantity and line.invoiced_quantity.value:
                    qty = Decimal(str(line.invoiced_quantity.value))
                    
                    if qty <= 0:
                        result.add_error(f"Line {i}: Invalid quantity: {qty} (BUS-15)")
                    elif qty > Decimal('999999'):
                        result.add_info(f"Line {i}: Very high quantity: {qty} (BUS-16)")
                    elif qty != int(qty) and qty < 1:
                        # Fractional quantities less than 1
                        result.add_info(f"Line {i}: Fractional quantity less than 1: {qty} (BUS-17)")
        
        return result
    
    @staticmethod
    def validate_party_relationships(ubl_invoice: UBLInvoice) -> ValidationResult:
        """Validate business relationships between parties."""
        result = ValidationResult()
        
        # Check if supplier and customer are the same (self-billing)
        if ubl_invoice.supplier_party and ubl_invoice.customer_party:
            supplier_name = ""
            customer_name = ""
            
            if ubl_invoice.supplier_party.party_name:
                supplier_name = ubl_invoice.supplier_party.party_name.name.lower().strip()
            
            if ubl_invoice.customer_party.party_name:
                customer_name = ubl_invoice.customer_party.party_name.name.lower().strip()
            
            if supplier_name and customer_name:
                # Check for identical names
                if supplier_name == customer_name:
                    result.add_warning("Supplier and customer have identical names - verify if this is intentional (BUS-18)")
                
                # Check for similar names (potential data entry errors)
                similarity = BusinessRules._calculate_name_similarity(supplier_name, customer_name)
                if 0.7 <= similarity < 1.0:
                    result.add_info(f"Supplier and customer names are very similar - verify accuracy (BUS-19)")
            
            # Check addresses
            if (ubl_invoice.supplier_party.postal_address and 
                ubl_invoice.customer_party.postal_address):
                
                supplier_addr = ubl_invoice.supplier_party.postal_address
                customer_addr = ubl_invoice.customer_party.postal_address
                
                # Check for same address
                if (supplier_addr.street_name == customer_addr.street_name and
                    supplier_addr.city_name == customer_addr.city_name and
                    supplier_addr.postal_zone == customer_addr.postal_zone):
                    result.add_info("Supplier and customer have the same address (BUS-20)")
        
        return result
    
    @staticmethod
    def validate_invoice_sequence(ubl_invoice: UBLInvoice, previous_invoices: List[str] = None) -> ValidationResult:
        """Validate invoice numbering sequence."""
        result = ValidationResult()
        
        if not previous_invoices or not ubl_invoice.id:
            return result
        
        current_id = ubl_invoice.id
        
        # Check for duplicate invoice IDs
        if current_id in previous_invoices:
            result.add_error(f"Duplicate invoice ID detected: {current_id} (BUS-21)")
        
        # Check for sequential numbering (if numeric)
        numeric_ids = []
        for inv_id in previous_invoices + [current_id]:
            # Extract numeric part if present
            numbers = re.findall(r'\d+', inv_id)
            if numbers:
                numeric_ids.append(int(numbers[-1]))  # Use last number found
        
        if len(numeric_ids) >= 2:
            numeric_ids.sort()
            gaps = []
            for i in range(1, len(numeric_ids)):
                if numeric_ids[i] - numeric_ids[i-1] > 1:
                    gaps.append((numeric_ids[i-1], numeric_ids[i]))
            
            if gaps:
                result.add_info(f"Gaps in invoice numbering sequence detected: {gaps} (BUS-22)")
        
        return result
    
    @staticmethod
    def validate_invoice_references(ubl_invoice: UBLInvoice) -> ValidationResult:
        """Validate invoice references and related documents."""
        result = ValidationResult()
        
        # Check order reference
        if hasattr(ubl_invoice, 'order_reference') and ubl_invoice.order_reference:
            order_ref = ubl_invoice.order_reference
            if isinstance(order_ref, str) and len(order_ref.strip()) == 0:
                result.add_warning("Empty order reference provided (BUS-23)")
        
        # Check billing reference for credit notes
        if (ubl_invoice.invoice_type_code in ['381', '383'] and  # Credit note types
            hasattr(ubl_invoice, 'billing_reference')):
            
            if not ubl_invoice.billing_reference:
                result.add_warning("Credit note should reference original invoice (BUS-24)")
            elif isinstance(ubl_invoice.billing_reference, list) and len(ubl_invoice.billing_reference) == 0:
                result.add_warning("Credit note should reference original invoice (BUS-25)")
        
        return result
    
    @staticmethod
    def validate_industry_specific_rules(ubl_invoice: UBLInvoice, industry: str = None) -> ValidationResult:
        """Validate industry-specific business rules."""
        result = ValidationResult()
        
        if not industry:
            return result
        
        industry = industry.upper()
        
        if industry == 'HEALTHCARE':
            # Healthcare-specific validations
            if ubl_invoice.invoice_lines:
                for i, line in enumerate(ubl_invoice.invoice_lines, 1):
                    if line.item and line.item.name:
                        item_name = line.item.name.lower()
                        if any(keyword in item_name for keyword in ['medicine', 'drug', 'pharmaceutical']):
                            # Check for required healthcare fields
                            result.add_info(f"Line {i}: Healthcare item detected - ensure regulatory compliance (BUS-26)")
        
        elif industry == 'AUTOMOTIVE':
            # Automotive industry validations
            if ubl_invoice.invoice_lines:
                for i, line in enumerate(ubl_invoice.invoice_lines, 1):
                    if line.item and line.item.name:
                        item_name = line.item.name.lower()
                        if any(keyword in item_name for keyword in ['vehicle', 'car', 'auto', 'engine']):
                            result.add_info(f"Line {i}: Automotive item detected - verify specifications (BUS-27)")
        
        elif industry == 'FOOD_BEVERAGE':
            # Food & beverage industry validations
            if ubl_invoice.invoice_lines:
                for i, line in enumerate(ubl_invoice.invoice_lines, 1):
                    if line.item and line.item.name:
                        item_name = line.item.name.lower()
                        if any(keyword in item_name for keyword in ['food', 'beverage', 'drink', 'meal']):
                            # Check for expiration dates, batch numbers, etc.
                            result.add_info(f"Line {i}: Food/beverage item detected - verify safety compliance (BUS-28)")
        
        return result
    
    @staticmethod
    def _extract_payment_days(payment_terms: Any) -> int:
        """Extract payment days from payment terms."""
        if isinstance(payment_terms, str):
            # Look for patterns like "NET 30", "30 DAYS", etc.
            numbers = re.findall(r'\d+', payment_terms)
            if numbers:
                return int(numbers[0])
        elif isinstance(payment_terms, dict):
            # Handle structured payment terms
            return payment_terms.get('payment_days', 0)
        elif hasattr(payment_terms, 'payment_days'):
            return getattr(payment_terms, 'payment_days', 0)
        
        return 0
    
    @staticmethod
    def _calculate_name_similarity(name1: str, name2: str) -> float:
        """Calculate similarity between two names."""
        from difflib import SequenceMatcher
        return SequenceMatcher(None, name1, name2).ratio()