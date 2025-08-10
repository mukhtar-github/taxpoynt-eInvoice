"""
Base UBL Transformer
===================
Abstract base class for transforming business system data to UBL 2.1 format.
Provides common UBL transformation patterns and validation for all business systems.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from decimal import Decimal
import uuid
import logging

from .ubl_models import (
    UBLInvoice,
    UBLDocumentReference,
    UBLParty,
    UBLAddress,
    UBLContact as UBLContactInfo,
    UBLMonetaryTotal,
    UBLInvoiceLine,
    UBLTaxTotal,
    UBLTaxSubtotal,
    UBLTaxCategory,
    UBLClassifiedTaxCategory,
    UBLItem,
    UBLPrice,
    UBLAllowanceCharge
)


class UBLTransformationError(Exception):
    """Raised when UBL transformation fails."""
    pass


class BaseUBLTransformer(ABC):
    """
    Abstract base class for UBL transformers.
    
    All business system UBL transformers should extend this class to ensure
    consistent UBL 2.1 compliance and standardized transformation patterns.
    
    Features:
    - Standard UBL 2.1 transformation methods
    - Nigerian FIRS compliance validation
    - Tax calculation and formatting
    - Currency handling and conversion
    - Error handling and logging
    """
    
    def __init__(self, business_system_info: Dict[str, Any]):
        """
        Initialize base UBL transformer.
        
        Args:
            business_system_info: Business system configuration and company info
        """
        self.business_system_info = business_system_info
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Nigerian compliance defaults
        self.default_currency = "NGN"
        self.nigerian_timezone = "Africa/Lagos"
        
    @abstractmethod
    def transform_invoice(self, invoice_data: Dict[str, Any]) -> UBLInvoice:
        """
        Transform business system invoice to UBL format.
        
        Args:
            invoice_data: Raw invoice data from business system
            
        Returns:
            UBLInvoice: Standardized UBL 2.1 invoice
            
        Raises:
            UBLTransformationError: If transformation fails
        """
        pass
    
    @abstractmethod
    def transform_party(self, party_data: Dict[str, Any], party_type: str) -> UBLParty:
        """
        Transform business system party (customer/supplier) to UBL Party.
        
        Args:
            party_data: Raw party data from business system
            party_type: "customer" or "supplier"
            
        Returns:
            UBLParty: Standardized UBL party information
        """
        pass
    
    @abstractmethod
    def transform_invoice_line(self, line_data: Dict[str, Any]) -> UBLInvoiceLine:
        """
        Transform business system invoice line to UBL InvoiceLine.
        
        Args:
            line_data: Raw line item data from business system
            
        Returns:
            UBLInvoiceLine: Standardized UBL invoice line
        """
        pass
    
    # Common transformation methods (implemented for all systems)
    
    def create_document_reference(self, reference_id: str, document_type: str = "Invoice") -> UBLDocumentReference:
        """Create standardized UBL document reference."""
        return UBLDocumentReference(
            id=reference_id,
            document_type_code=document_type,
            issue_date=datetime.now().date()
        )
    
    def create_ubl_address(self, address_data: Dict[str, Any]) -> UBLAddress:
        """
        Create standardized UBL address with Nigerian formatting.
        
        Args:
            address_data: Address information from business system
            
        Returns:
            UBLAddress: Formatted UBL address
        """
        return UBLAddress(
            street_name=address_data.get('street', ''),
            city_name=address_data.get('city', ''),
            postal_zone=address_data.get('postal_code', ''),
            country_subentity=address_data.get('state', ''),
            country_identification_code=address_data.get('country_code', 'NG')
        )
    
    def create_ubl_contact(self, contact_data: Dict[str, Any]) -> UBLContactInfo:
        """Create standardized UBL contact information."""
        return UBLContactInfo(
            name=contact_data.get('name', ''),
            telephone=contact_data.get('phone', ''),
            electronic_mail=contact_data.get('email', '')
        )
    
    def calculate_monetary_total(self, line_items: List[UBLInvoiceLine], 
                               allowances: List[UBLAllowanceCharge] = None) -> UBLMonetaryTotal:
        """
        Calculate UBL monetary totals with Nigerian tax compliance.
        
        Args:
            line_items: List of UBL invoice lines
            allowances: Optional allowances/charges
            
        Returns:
            UBLMonetaryTotal: Calculated totals
        """
        allowances = allowances or []
        
        # Calculate line extension amount (before tax)
        line_extension_amount = sum(
            Decimal(str(line.line_extension_amount)) for line in line_items
        )
        
        # Calculate allowance/charge adjustments
        allowance_total = sum(
            Decimal(str(allowance.amount)) * (-1 if allowance.charge_indicator else 1)
            for allowance in allowances
        )
        
        # Tax exclusive amount
        tax_exclusive_amount = line_extension_amount + allowance_total
        
        # Calculate total tax amount (VAT in Nigeria is typically 7.5%)
        tax_amount = sum(
            sum(Decimal(str(tax_subtotal.tax_amount)) for tax_subtotal in line.tax_total.tax_subtotals)
            for line in line_items if line.tax_total
        )
        
        # Tax inclusive amount (final total)
        tax_inclusive_amount = tax_exclusive_amount + tax_amount
        
        return UBLMonetaryTotal(
            line_extension_amount=float(line_extension_amount),
            tax_exclusive_amount=float(tax_exclusive_amount),
            tax_inclusive_amount=float(tax_inclusive_amount),
            allowance_total_amount=float(abs(allowance_total)) if allowance_total < 0 else 0.0,
            charge_total_amount=float(allowance_total) if allowance_total > 0 else 0.0,
            payable_amount=float(tax_inclusive_amount)
        )
    
    def create_nigerian_tax_category(self, tax_rate: float = 7.5) -> UBLTaxCategory:
        """
        Create Nigerian VAT tax category (default 7.5%).
        
        Args:
            tax_rate: Tax rate percentage (default Nigerian VAT)
            
        Returns:
            UBLTaxCategory: Nigerian tax category
        """
        return UBLTaxCategory(
            id="VAT",
            name="Value Added Tax",
            percent=tax_rate,
            tax_scheme={
                "id": "VAT",
                "name": "Nigerian Value Added Tax"
            }
        )
    
    def validate_nigerian_compliance(self, ubl_invoice: UBLInvoice) -> bool:
        """
        Validate UBL invoice for Nigerian FIRS compliance.
        
        Args:
            ubl_invoice: UBL invoice to validate
            
        Returns:
            bool: True if compliant, False otherwise
            
        Raises:
            UBLTransformationError: If critical compliance issues found
        """
        errors = []
        
        # Required Nigerian fields
        if not ubl_invoice.id:
            errors.append("Invoice ID is required for FIRS compliance")
            
        if not ubl_invoice.issue_date:
            errors.append("Issue date is required for FIRS compliance")
            
        if not ubl_invoice.supplier_party:
            errors.append("Supplier party is required for FIRS compliance")
            
        if not ubl_invoice.customer_party:
            errors.append("Customer party is required for FIRS compliance")
            
        # Currency validation (should be NGN for local transactions)
        if hasattr(ubl_invoice, 'document_currency_code'):
            if ubl_invoice.document_currency_code not in ['NGN', 'USD', 'EUR', 'GBP']:
                self.logger.warning(f"Unusual currency code: {ubl_invoice.document_currency_code}")
        
        if errors:
            error_msg = "Nigerian FIRS compliance validation failed: " + "; ".join(errors)
            self.logger.error(error_msg)
            raise UBLTransformationError(error_msg)
            
        return True
    
    def format_nigerian_phone(self, phone: str) -> str:
        """Format phone number for Nigerian standards."""
        if not phone:
            return ""
            
        # Remove non-digits
        phone = ''.join(filter(str.isdigit, phone))
        
        # Nigerian phone number formatting
        if phone.startswith('234'):
            return f"+{phone}"
        elif phone.startswith('0') and len(phone) == 11:
            return f"+234{phone[1:]}"
        elif len(phone) == 10:
            return f"+234{phone}"
        else:
            return phone
    
    def generate_ubl_id(self) -> str:
        """Generate UUID for UBL documents."""
        return str(uuid.uuid4())