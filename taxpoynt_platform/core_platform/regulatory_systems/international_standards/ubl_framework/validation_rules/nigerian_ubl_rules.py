"""
Nigerian UBL Validation Rules
============================
Nigerian FIRS-specific UBL validation rules and e-invoicing compliance.
"""
from typing import List, Dict, Any, Set
from datetime import datetime, date
from decimal import Decimal
import re

from ..base_ubl_validator import ValidationResult
from ..ubl_models import UBLInvoice


class NigerianUBLRules:
    """
    Nigerian FIRS-specific UBL validation rules.
    
    Implements Nigerian e-invoicing requirements, tax compliance,
    and business regulations for FIRS certification.
    """
    
    # Nigerian VAT rate (as of 2024)
    NIGERIAN_VAT_RATE = Decimal('7.5')
    
    # Valid Nigerian entity types
    NIGERIAN_ENTITY_TYPES = {
        'LIMITED LIABILITY COMPANY', 'PUBLIC LIMITED COMPANY', 'PRIVATE LIMITED COMPANY',
        'PARTNERSHIP', 'SOLE PROPRIETORSHIP', 'COOPERATIVE SOCIETY',
        'NON-GOVERNMENTAL ORGANIZATION', 'GOVERNMENT AGENCY', 'FEDERAL GOVERNMENT',
        'STATE GOVERNMENT', 'LOCAL GOVERNMENT', 'INTERNATIONAL ORGANIZATION'
    }
    
    # Nigerian states for address validation
    NIGERIAN_STATES = {
        'ABIA', 'ADAMAWA', 'AKWA IBOM', 'ANAMBRA', 'BAUCHI', 'BAYELSA', 'BENUE',
        'BORNO', 'CROSS RIVER', 'DELTA', 'EBONYI', 'EDO', 'EKITI', 'ENUGU',
        'GOMBE', 'IMO', 'JIGAWA', 'KADUNA', 'KANO', 'KATSINA', 'KEBBI', 'KOGI',
        'KWARA', 'LAGOS', 'NASARAWA', 'NIGER', 'OGUN', 'ONDO', 'OSUN', 'OYO',
        'PLATEAU', 'RIVERS', 'SOKOTO', 'TARABA', 'YOBE', 'ZAMFARA', 'FCT', 'ABUJA'
    }
    
    @staticmethod
    def validate_firs_invoice_requirements(ubl_invoice: UBLInvoice) -> ValidationResult:
        """Validate FIRS mandatory invoice requirements."""
        result = ValidationResult()
        
        # FIRS Invoice ID format validation
        if ubl_invoice.id:
            if len(ubl_invoice.id) < 3:
                result.add_error("FIRS requires invoice ID with minimum 3 characters (FIRS-01)")
            
            # Check for alphanumeric format (FIRS preference)
            if not re.match(r'^[A-Za-z0-9\-_/]+$', ubl_invoice.id):
                result.add_warning("Invoice ID should contain only alphanumeric characters, hyphens, underscores, or forward slashes (FIRS-02)")
        
        # FIRS-required invoice type codes
        firs_valid_types = ['380', '381', '383', '384', '385', '386', '388', '393', '394', '395', '396']
        if ubl_invoice.invoice_type_code and ubl_invoice.invoice_type_code not in firs_valid_types:
            result.add_error(f"Invalid invoice type code for FIRS: {ubl_invoice.invoice_type_code} (FIRS-03)")
        
        # Currency requirements for Nigerian transactions
        if hasattr(ubl_invoice, 'document_currency_code'):
            if ubl_invoice.document_currency_code not in ['NGN', 'USD', 'EUR', 'GBP']:
                result.add_warning(f"Uncommon currency for Nigerian transactions: {ubl_invoice.document_currency_code} (FIRS-04)")
        
        # Date requirements
        if ubl_invoice.issue_date:
            if isinstance(ubl_invoice.issue_date, (date, datetime)):
                issue_date = ubl_invoice.issue_date
                if isinstance(issue_date, datetime):
                    issue_date = issue_date.date()
                
                # FIRS does not allow future-dated invoices
                if issue_date > date.today():
                    result.add_error("FIRS does not permit future-dated invoices (FIRS-05)")
                
                # FIRS requires invoices to be issued within reasonable timeframe
                days_old = (date.today() - issue_date).days
                if days_old > 365:
                    result.add_warning(f"Invoice is {days_old} days old, may require special handling (FIRS-06)")
        
        return result
    
    @staticmethod
    def validate_nigerian_tax_compliance(ubl_invoice: UBLInvoice) -> ValidationResult:
        """Validate Nigerian tax compliance requirements."""
        result = ValidationResult()
        
        if not ubl_invoice.tax_total:
            result.add_warning("Tax information is required for Nigerian invoices (FIRS-07)")
            return result
        
        # VAT validation
        vat_found = False
        total_tax_amount = Decimal('0')
        
        for tax_subtotal in ubl_invoice.tax_total.tax_subtotals:
            if tax_subtotal.tax_category and tax_subtotal.tax_category.id:
                tax_id = tax_subtotal.tax_category.id.upper()
                
                if tax_id in ['VAT', 'VALUE ADDED TAX']:
                    vat_found = True
                    
                    # Check VAT rate
                    if hasattr(tax_subtotal.tax_category, 'percent'):
                        vat_rate = Decimal(str(tax_subtotal.tax_category.percent))
                        if abs(vat_rate - NigerianUBLRules.NIGERIAN_VAT_RATE) > Decimal('0.1'):
                            if vat_rate == Decimal('0'):
                                result.add_info(f"Zero VAT rate applied - ensure exemption is valid (FIRS-08)")
                            else:
                                result.add_warning(f"Non-standard VAT rate: {vat_rate}% (standard: {NigerianUBLRules.NIGERIAN_VAT_RATE}%) (FIRS-09)")
                    
                    # Validate VAT calculation
                    if tax_subtotal.taxable_amount and tax_subtotal.tax_amount:
                        expected_vat = (Decimal(str(tax_subtotal.taxable_amount)) * 
                                      NigerianUBLRules.NIGERIAN_VAT_RATE / 100)
                        actual_vat = Decimal(str(tax_subtotal.tax_amount))
                        
                        if abs(expected_vat - actual_vat) > Decimal('0.01'):
                            result.add_error(f"VAT calculation error: expected {expected_vat}, got {actual_vat} (FIRS-10)")
                
                # Accumulate total tax
                if tax_subtotal.tax_amount:
                    total_tax_amount += Decimal(str(tax_subtotal.tax_amount))
        
        if not vat_found:
            result.add_warning("No VAT found on invoice - ensure VAT exemption is valid (FIRS-11)")
        
        # Validate total tax amount
        if ubl_invoice.tax_total.tax_amount:
            stated_total = Decimal(str(ubl_invoice.tax_total.tax_amount))
            if abs(total_tax_amount - stated_total) > Decimal('0.01'):
                result.add_error(f"Tax total mismatch: calculated {total_tax_amount}, stated {stated_total} (FIRS-12)")
        
        return result
    
    @staticmethod
    def validate_nigerian_business_entities(ubl_invoice: UBLInvoice) -> ValidationResult:
        """Validate Nigerian business entity information."""
        result = ValidationResult()
        
        # Supplier validation
        if ubl_invoice.supplier_party:
            supplier = ubl_invoice.supplier_party
            
            # Nigerian address validation
            if supplier.postal_address:
                address = supplier.postal_address
                
                # Country code validation
                if address.country_identification_code and address.country_identification_code.upper() != 'NG':
                    result.add_info("Supplier is not a Nigerian entity (FIRS-13)")
                else:
                    # Nigerian state validation
                    if address.country_subentity:
                        state = address.country_subentity.upper()
                        if state not in NigerianUBLRules.NIGERIAN_STATES:
                            result.add_warning(f"Invalid Nigerian state: {address.country_subentity} (FIRS-14)")
                
                # Nigerian postal code validation (6 digits)
                if address.postal_zone:
                    if not re.match(r'^\d{6}$', address.postal_zone):
                        result.add_warning(f"Nigerian postal codes should be 6 digits: {address.postal_zone} (FIRS-15)")
            
            # Nigerian phone number validation
            if supplier.contact and supplier.contact.telephone:
                phone = supplier.contact.telephone
                if not NigerianUBLRules._is_nigerian_phone(phone):
                    result.add_info("Supplier phone number may not be Nigerian format (FIRS-16)")
            
            # Business registration validation
            if hasattr(supplier, 'party_legal_entity') and supplier.party_legal_entity:
                # Check for RC number (Nigerian company registration)
                registration_name = getattr(supplier.party_legal_entity, 'registration_name', '')
                if 'RC' not in registration_name and 'BN' not in registration_name:
                    result.add_info("Supplier may not have Nigerian business registration (FIRS-17)")
        
        # Customer validation (similar checks for Nigerian customers)
        if ubl_invoice.customer_party:
            customer = ubl_invoice.customer_party
            
            if customer.postal_address and customer.postal_address.country_identification_code:
                if customer.postal_address.country_identification_code.upper() == 'NG':
                    # Apply Nigerian-specific validation for Nigerian customers
                    if customer.postal_address.country_subentity:
                        state = customer.postal_address.country_subentity.upper()
                        if state not in NigerianUBLRules.NIGERIAN_STATES:
                            result.add_warning(f"Invalid Nigerian state for customer: {customer.postal_address.country_subentity} (FIRS-18)")
        
        return result
    
    @staticmethod
    def validate_nigerian_product_requirements(ubl_invoice: UBLInvoice) -> ValidationResult:
        """Validate Nigerian product classification and requirements."""
        result = ValidationResult()
        
        if not ubl_invoice.invoice_lines:
            return result
        
        for i, line in enumerate(ubl_invoice.invoice_lines, 1):
            line_prefix = f"Line {i}"
            
            # HS Code validation (required for customs/FIRS)
            if line.item and hasattr(line.item, 'classified_tax_category'):
                # Check for HS code classification
                if hasattr(line.item, 'additional_item_property'):
                    has_hs_code = False
                    for prop in getattr(line.item, 'additional_item_property', []):
                        if getattr(prop, 'name', '').lower() in ['hs_code', 'harmonized_system_code', 'tariff_code']:
                            has_hs_code = True
                            hs_code = getattr(prop, 'value', '')
                            
                            # Validate HS code format (XXXX.XX)
                            if not re.match(r'^\d{4}\.\d{2}$', hs_code):
                                result.add_error(f"{line_prefix}: Invalid HS code format: {hs_code} (FIRS-19)")
                            break
                    
                    if not has_hs_code:
                        result.add_warning(f"{line_prefix}: HS code classification recommended for customs compliance (FIRS-20)")
            
            # Nigerian product naming requirements
            if line.item and line.item.name:
                item_name = line.item.name.lower()
                
                # Check for restricted/controlled items
                restricted_keywords = [
                    'arms', 'ammunition', 'weapons', 'explosive', 'narcotic', 'drug',
                    'tobacco', 'alcohol', 'petroleum', 'crude oil', 'currency'
                ]
                
                for keyword in restricted_keywords:
                    if keyword in item_name:
                        result.add_warning(f"{line_prefix}: Product may be restricted and require special permits (FIRS-21)")
                        break
        
        return result
    
    @staticmethod
    def validate_nigerian_withholding_tax(ubl_invoice: UBLInvoice) -> ValidationResult:
        """Validate Nigerian withholding tax requirements."""
        result = ValidationResult()
        
        # Check if invoice qualifies for withholding tax
        if ubl_invoice.legal_monetary_total and ubl_invoice.legal_monetary_total.payable_amount:
            payable_amount = Decimal(str(ubl_invoice.legal_monetary_total.payable_amount))
            
            # Nigerian WHT thresholds (simplified)
            wht_threshold = Decimal('10000')  # NGN 10,000 threshold for many services
            
            if payable_amount >= wht_threshold:
                # Check if WHT is properly applied
                wht_found = False
                
                if ubl_invoice.tax_total and ubl_invoice.tax_total.tax_subtotals:
                    for tax_subtotal in ubl_invoice.tax_total.tax_subtotals:
                        if tax_subtotal.tax_category and tax_subtotal.tax_category.id:
                            tax_id = tax_subtotal.tax_category.id.upper()
                            if 'WHT' in tax_id or 'WITHHOLDING' in tax_id:
                                wht_found = True
                                break
                
                if not wht_found:
                    result.add_info(f"Invoice amount NGN {payable_amount} may be subject to withholding tax (FIRS-22)")
        
        return result
    
    @staticmethod
    def validate_firs_digital_signature_requirements(ubl_invoice: UBLInvoice) -> ValidationResult:
        """Validate FIRS digital signature and security requirements."""
        result = ValidationResult()
        
        # Check for required FIRS fields
        required_firs_fields = [
            'business_id',  # FIRS business identifier
            'irn',          # Invoice reference number
            'tax_point_date'  # Tax point date
        ]
        
        for field in required_firs_fields:
            if not hasattr(ubl_invoice, field) or not getattr(ubl_invoice, field):
                result.add_warning(f"FIRS field '{field}' is missing or empty (FIRS-23)")
        
        # Validate IRN format (if present)
        if hasattr(ubl_invoice, 'irn') and ubl_invoice.irn:
            irn = ubl_invoice.irn
            # FIRS IRN should be unique and follow specific format
            if len(irn) < 10:
                result.add_warning(f"FIRS IRN may be too short: {irn} (FIRS-24)")
            
            if not re.match(r'^[A-Za-z0-9\-_/]+$', irn):
                result.add_warning(f"FIRS IRN should contain only alphanumeric characters: {irn} (FIRS-25)")
        
        return result
    
    @staticmethod
    def _is_nigerian_phone(phone: str) -> bool:
        """Check if phone number appears to be Nigerian format."""
        if not phone:
            return False
        
        # Clean phone number
        clean_phone = re.sub(r'[^\d+]', '', phone)
        
        # Nigerian phone patterns
        patterns = [
            r'^\+234[0-9]{10}$',     # +234xxxxxxxxxx
            r'^234[0-9]{10}$',       # 234xxxxxxxxxx  
            r'^0[0-9]{10}$',         # 0xxxxxxxxxx
            r'^[0-9]{10}$'           # xxxxxxxxxx
        ]
        
        return any(re.match(pattern, clean_phone) for pattern in patterns)