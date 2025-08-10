"""
Odoo to BIS Billing 3.0 UBL Field Mapping Service.

This module provides field mapping and transformation functions to convert
Odoo invoice data to BIS Billing 3.0 UBL format required by FIRS.
"""
import logging
import re
from typing import Dict, Any, List, Optional, Union, Tuple
from datetime import datetime, date
from decimal import Decimal, ROUND_HALF_UP
import asyncio

from app.schemas.invoice_validation import (
    InvoiceValidationRequest, InvoiceType, Party, Address, 
    PartyIdentification, PartyLegalEntity, TaxTotal, TaxSubtotal,
    TaxCategory, InvoiceLine, UnitCode, LegalMonetaryTotal,
    AllowanceCharge, PaymentTerms, PaymentMeans, CurrencyCode
)
from app.services.odoo_firs_service_code_mapper import odoo_firs_service_code_mapper

logger = logging.getLogger(__name__)


class OdooUBLMapper:
    """
    Mapper class for converting Odoo invoice data to BIS Billing 3.0 UBL format.
    
    This class provides methods to transform and map invoice data from Odoo to
    the UBL format required by FIRS for e-invoicing.
    """
    
    # Constants
    DEFAULT_COUNTRY_CODE = "NG"  # Nigeria
    
    # Unit code mapping (Odoo uom -> UBL code)
    UNIT_CODE_MAPPING = {
        "unit(s)": UnitCode.PIECE,
        "units": UnitCode.PIECE,
        "ea": UnitCode.PIECE,
        "each": UnitCode.PIECE,
        "kg": UnitCode.KILOGRAM,
        "kgs": UnitCode.KILOGRAM,
        "l": UnitCode.LITRE,
        "ltr": UnitCode.LITRE,
        "litre": UnitCode.LITRE,
        "m": UnitCode.METER,
        "meter": UnitCode.METER,
        "hr": UnitCode.HOUR,
        "hour": UnitCode.HOUR,
        "day": UnitCode.DAY,
        "days": UnitCode.DAY,
        "week": UnitCode.WEEK,
        "weeks": UnitCode.WEEK,
        "month": UnitCode.MONTH,
        "months": UnitCode.MONTH,
    }
    
    # Tax category mapping (Odoo tax -> UBL category)
    TAX_CATEGORY_MAPPING = {
        "vat": TaxCategory.STANDARD,
        "vat_0": TaxCategory.ZERO,
        "exempt": TaxCategory.EXEMPT,
        "export": TaxCategory.EXPORT,
        "reverse": TaxCategory.VAT_REVERSE_CHARGE,
        "not_applicable": TaxCategory.SERVICE_OUTSIDE_SCOPE,
    }
    
    # Payment means mapping (Odoo payment method -> UBL payment means)
    PAYMENT_MEANS_MAPPING = {
        "bank_transfer": PaymentMeans.CREDIT_TRANSFER,
        "direct_debit": PaymentMeans.DIRECT_DEBIT,
        "cash": PaymentMeans.CASH,
        "check": PaymentMeans.CHEQUE,
        "cheque": PaymentMeans.CHEQUE,
        "card": PaymentMeans.BANK_CARD,
        "bank_card": PaymentMeans.BANK_CARD,
        "bank_giro": PaymentMeans.BANK_GIRO,
        "standing_order": PaymentMeans.STANDING_ORDER,
    }
    
    def __init__(self):
        """Initialize the Odoo to UBL mapper."""
        pass
    
    def map_invoice(self, odoo_invoice: Dict[str, Any], company_info: Dict[str, Any]) -> InvoiceValidationRequest:
        """
        Map an Odoo invoice to BIS Billing 3.0 UBL format.
        
        Args:
            odoo_invoice: Odoo invoice data
            company_info: Company information for the supplier
            
        Returns:
            Mapped invoice data in UBL format as an InvoiceValidationRequest object
        """
        try:
            # Map invoice header information
            invoice_type = self._map_invoice_type(odoo_invoice.get("move_type", "out_invoice"))
            invoice_date = self._parse_date(odoo_invoice.get("invoice_date"))
            due_date = self._parse_date(odoo_invoice.get("invoice_date_due"))
            
            # Map currency
            currency_code = self._map_currency_code(odoo_invoice.get("currency", {}).get("name", "NGN"))
            
            # Map supplier party (seller)
            accounting_supplier_party = self._map_supplier_party(company_info)
            
            # Map customer party (buyer)
            accounting_customer_party = self._map_customer_party(odoo_invoice.get("partner", {}))
            
            # Map invoice lines
            invoice_lines = self._map_invoice_lines(odoo_invoice.get("lines", []))
            
            # Map tax information
            tax_total = self._map_tax_total(odoo_invoice, invoice_lines)
            
            # Map document totals
            legal_monetary_total = self._map_legal_monetary_total(odoo_invoice)
            
            # Map payment terms
            payment_terms = self._map_payment_terms(odoo_invoice)
            
            # Create the UBL invoice request
            ubl_invoice = InvoiceValidationRequest(
                invoice_number=odoo_invoice.get("invoice_number", odoo_invoice.get("name", "")),
                invoice_type_code=invoice_type,
                invoice_date=invoice_date,
                due_date=due_date,
                currency_code=currency_code,
                accounting_supplier_party=accounting_supplier_party,
                accounting_customer_party=accounting_customer_party,
                invoice_lines=invoice_lines,
                tax_total=tax_total,
                legal_monetary_total=legal_monetary_total,
                payment_terms=payment_terms,
                payment_means=self._map_payment_means(odoo_invoice),
                order_reference=odoo_invoice.get("ref", ""),
                note=odoo_invoice.get("narration", "")
            )
            
            return ubl_invoice
            
        except Exception as e:
            logger.error(f"Error mapping Odoo invoice to UBL: {str(e)}")
            raise ValueError(f"Error mapping invoice to UBL format: {str(e)}")
    
    def _map_invoice_type(self, odoo_type: str) -> InvoiceType:
        """Map Odoo invoice type to UBL invoice type."""
        type_mapping = {
            "out_invoice": InvoiceType.COMMERCIAL_INVOICE,
            "out_refund": InvoiceType.CREDIT_NOTE,
            "in_invoice": InvoiceType.COMMERCIAL_INVOICE,
            "in_refund": InvoiceType.CREDIT_NOTE,
            "entry": InvoiceType.COMMERCIAL_INVOICE
        }
        return type_mapping.get(odoo_type, InvoiceType.COMMERCIAL_INVOICE)
    
    def _map_currency_code(self, odoo_currency: str) -> CurrencyCode:
        """Map Odoo currency to UBL currency code."""
        try:
            # Attempt to convert to CurrencyCode enum
            return CurrencyCode(odoo_currency)
        except ValueError:
            # Default to NGN if not found
            logger.warning(f"Currency code {odoo_currency} not found in UBL schema, defaulting to NGN")
            return CurrencyCode.NGN
    
    def _map_supplier_party(self, company_info: Dict[str, Any]) -> Party:
        """Map company info to UBL supplier party."""
        # Create address
        address = Address(
            street_name=company_info.get("street", ""),
            additional_street_name=company_info.get("street2", ""),
            city_name=company_info.get("city", ""),
            postal_zone=company_info.get("zip", ""),
            country_subdivision=company_info.get("state", {}).get("name", ""),
            country_code=company_info.get("country", {}).get("code", self.DEFAULT_COUNTRY_CODE)
        )
        
        # Create party identification
        party_id = PartyIdentification(
            id=company_info.get("vat", company_info.get("company_registry", "")),
            scheme_id="VAT"
        )
        
        # Create party legal entity
        legal_entity = PartyLegalEntity(
            registration_name=company_info.get("name", ""),
            company_id=company_info.get("company_registry", ""),
            company_id_scheme_id="FIRS"
        )
        
        # Create party tax scheme
        party_tax_scheme = {
            "tax_scheme_id": "VAT",
            "company_id": company_info.get("vat", ""),
            "registration_name": company_info.get("name", "")
        }
        
        # Create contact information
        contact = {
            "name": company_info.get("name", ""),
            "telephone": company_info.get("phone", ""),
            "email": company_info.get("email", "")
        }
        
        # Create supplier party
        return Party(
            party_identification=party_id,
            party_name=company_info.get("name", ""),
            postal_address=address,
            party_tax_scheme=party_tax_scheme,
            party_legal_entity=legal_entity,
            contact=contact,
            electronic_address=company_info.get("email", "")
        )
    
    def _map_customer_party(self, partner: Dict[str, Any]) -> Party:
        """Map Odoo partner to UBL customer party."""
        # Create address
        address = Address(
            street_name=partner.get("street", "Unknown"),
            additional_street_name=partner.get("street2", ""),
            city_name=partner.get("city", "Unknown"),
            postal_zone=partner.get("zip", ""),
            country_subdivision=partner.get("state_name", ""),
            country_code=partner.get("country_code", self.DEFAULT_COUNTRY_CODE)
        )
        
        # Create party identification
        party_id = PartyIdentification(
            id=partner.get("vat", partner.get("ref", str(partner.get("id", "")))),
            scheme_id="VAT"
        )
        
        # Create party legal entity
        legal_entity = PartyLegalEntity(
            registration_name=partner.get("name", "Unknown"),
            company_id=partner.get("vat", ""),
            company_id_scheme_id="FIRS"
        )
        
        # Create party tax scheme
        party_tax_scheme = {
            "tax_scheme_id": "VAT",
            "company_id": partner.get("vat", ""),
            "registration_name": partner.get("name", "Unknown")
        }
        
        # Create contact information
        contact = {
            "name": partner.get("name", "Unknown"),
            "telephone": partner.get("phone", ""),
            "email": partner.get("email", "")
        }
        
        # Create customer party
        return Party(
            party_identification=party_id,
            party_name=partner.get("name", "Unknown"),
            postal_address=address,
            party_tax_scheme=party_tax_scheme,
            party_legal_entity=legal_entity,
            contact=contact,
            electronic_address=partner.get("email", "")
        )
    
    async def _map_invoice_lines_async(self, odoo_lines: List[Dict[str, Any]]) -> List[InvoiceLine]:
        """Map Odoo invoice lines to UBL invoice lines asynchronously with service code mapping."""
        ubl_lines = []
        
        for i, line in enumerate(odoo_lines):
            # Get tax information
            tax_info = self._get_line_tax_info(line)
            
            # Map unit code
            unit_code = self._map_unit_code(line.get("uom_id", {}).get("name", "ea"))
            
            # Get product information for service code mapping
            product = line.get("product", {})
            product_name = product.get("name", line.get("name", ""))
            product_category = product.get("categ_id", {}).get("name", "")
            product_description = line.get("name", "")
            
            # Try to map service code
            service_code = None
            try:
                # Try to get service code suggestion
                service_code_data = await odoo_firs_service_code_mapper.suggest_service_code(
                    product_name=product_name,
                    category=product_category,
                    description=product_description
                )
                
                if service_code_data and service_code_data.get("confidence", 0) > 0.4:
                    service_code = service_code_data.get("code")
                    logger.info(f"Mapped product '{product_name}' to service code '{service_code}' "
                               f"({service_code_data.get('name', '')}) with confidence "
                               f"{service_code_data.get('confidence', 0):.2f}")
            except Exception as e:
                logger.warning(f"Error mapping service code for '{product_name}': {str(e)}")
            
            # Create invoice line
            ubl_line = InvoiceLine(
                id=str(i + 1),
                invoiced_quantity=Decimal(str(line.get("quantity", 1))),
                unit_code=unit_code,
                line_extension_amount=Decimal(str(line.get("price_subtotal", 0))),
                item_description=line.get("name", ""),
                item_name=product_name[:100],
                price_amount=Decimal(str(line.get("price_unit", 0))),
                buyers_item_identification=product.get("default_code", ""),
                sellers_item_identification=product.get("id", ""),
                service_code=service_code,
                tax_total=tax_info
            )
            
            ubl_lines.append(ubl_line)
            
        return ubl_lines
    
    def _map_invoice_lines(self, odoo_lines: List[Dict[str, Any]]) -> List[InvoiceLine]:
        """Map Odoo invoice lines to UBL invoice lines.
        
        This is a synchronous wrapper around the async version for backward compatibility.
        """
        try:
            # Try to run the async version in a new event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(self._map_invoice_lines_async(odoo_lines))
            finally:
                loop.close()
        except Exception as e:
            logger.error(f"Error in async service code mapping: {str(e)}")
            
            # Fallback to non-service code version if async fails
            ubl_lines = []
            
            for i, line in enumerate(odoo_lines):
                # Get tax information
                tax_info = self._get_line_tax_info(line)
                
                # Map unit code
                unit_code = self._map_unit_code(line.get("uom_id", {}).get("name", "ea"))
                
                # Create invoice line without service code
                ubl_line = InvoiceLine(
                    id=str(i + 1),
                    invoiced_quantity=Decimal(str(line.get("quantity", 1))),
                    unit_code=unit_code,
                    line_extension_amount=Decimal(str(line.get("price_subtotal", 0))),
                    item_description=line.get("name", ""),
                    item_name=line.get("product", {}).get("name", line.get("name", ""))[:100],
                    price_amount=Decimal(str(line.get("price_unit", 0))),
                    buyers_item_identification=line.get("product", {}).get("default_code", ""),
                    sellers_item_identification=line.get("product", {}).get("id", ""),
                    tax_total=tax_info
                )
                
                ubl_lines.append(ubl_line)
            
            return ubl_lines
    
    def _get_line_tax_info(self, line: Dict[str, Any]) -> Optional[TaxTotal]:
        """Extract tax information from an invoice line."""
        taxes = line.get("taxes", [])
        if not taxes:
            return None
            
        tax_subtotals = []
        total_tax_amount = Decimal("0.00")
        
        for tax in taxes:
            # Get tax rate
            tax_percent = Decimal(str(tax.get("amount", 0)))
            
            # Get taxable amount
            taxable_amount = Decimal(str(line.get("price_subtotal", 0)))
            
            # Calculate tax amount
            tax_amount = (taxable_amount * tax_percent) / Decimal("100.0")
            tax_amount = tax_amount.quantize(Decimal("0.01"), ROUND_HALF_UP)
            
            # Add to total
            total_tax_amount += tax_amount
            
            # Map tax category
            tax_name = tax.get("name", "").lower()
            tax_category = self._map_tax_category(tax_name)
            
            # Create tax subtotal
            subtotal = TaxSubtotal(
                taxable_amount=taxable_amount,
                tax_amount=tax_amount,
                tax_category=tax_category,
                tax_percent=tax_percent
            )
            
            tax_subtotals.append(subtotal)
        
        # Create tax total
        return TaxTotal(
            tax_amount=total_tax_amount,
            tax_subtotals=tax_subtotals
        ) if tax_subtotals else None
    
    def _map_unit_code(self, odoo_uom: str) -> UnitCode:
        """Map Odoo UoM to UBL unit code."""
        # Convert to lowercase for case-insensitive matching
        uom_lower = odoo_uom.lower()
        
        # Try direct mapping
        if uom_lower in self.UNIT_CODE_MAPPING:
            return self.UNIT_CODE_MAPPING[uom_lower]
        
        # Try partial matching
        for odoo_key, ubl_value in self.UNIT_CODE_MAPPING.items():
            if odoo_key in uom_lower or uom_lower in odoo_key:
                return ubl_value
        
        # Default to EA (each) if no match found
        logger.warning(f"Unit code {odoo_uom} not mapped, defaulting to EA (each)")
        return UnitCode.PIECE
    
    def _map_tax_category(self, tax_name: str) -> TaxCategory:
        """Map Odoo tax name to UBL tax category."""
        # Check for direct mapping
        for key, value in self.TAX_CATEGORY_MAPPING.items():
            if key in tax_name:
                return value
                
        # Default to standard VAT for Nigeria
        return TaxCategory.STANDARD
    
    def _map_tax_total(self, odoo_invoice: Dict[str, Any], invoice_lines: List[InvoiceLine]) -> TaxTotal:
        """Calculate overall tax total from invoice data."""
        # Extract tax subtotals from lines
        all_subtotals = []
        for line in invoice_lines:
            if line.tax_total and line.tax_total.tax_subtotals:
                all_subtotals.extend(line.tax_total.tax_subtotals)
        
        # Group by tax category and percent
        grouped_taxes = {}
        for subtotal in all_subtotals:
            key = (subtotal.tax_category, subtotal.tax_percent)
            if key not in grouped_taxes:
                grouped_taxes[key] = {
                    "taxable_amount": Decimal("0.00"),
                    "tax_amount": Decimal("0.00"),
                    "tax_category": subtotal.tax_category,
                    "tax_percent": subtotal.tax_percent
                }
            grouped_taxes[key]["taxable_amount"] += subtotal.taxable_amount
            grouped_taxes[key]["tax_amount"] += subtotal.tax_amount
        
        # Create consolidated tax subtotals
        consolidated_subtotals = []
        total_tax_amount = Decimal("0.00")
        
        for tax_info in grouped_taxes.values():
            subtotal = TaxSubtotal(
                taxable_amount=tax_info["taxable_amount"],
                tax_amount=tax_info["tax_amount"],
                tax_category=tax_info["tax_category"],
                tax_percent=tax_info["tax_percent"]
            )
            consolidated_subtotals.append(subtotal)
            total_tax_amount += tax_info["tax_amount"]
        
        # If no subtotals were found, use the document level tax amount
        if not consolidated_subtotals:
            tax_amount = Decimal(str(odoo_invoice.get("amount_tax", 0)))
            tax_excl_amount = Decimal(str(odoo_invoice.get("amount_untaxed", 0)))
            
            # Calculate approximate tax rate
            tax_percent = Decimal("0.00")
            if tax_excl_amount > Decimal("0.00"):
                tax_percent = (tax_amount / tax_excl_amount) * Decimal("100.0")
                tax_percent = tax_percent.quantize(Decimal("0.01"), ROUND_HALF_UP)
            
            subtotal = TaxSubtotal(
                taxable_amount=tax_excl_amount,
                tax_amount=tax_amount,
                tax_category=TaxCategory.STANDARD,
                tax_percent=tax_percent
            )
            consolidated_subtotals.append(subtotal)
            total_tax_amount = tax_amount
        
        # Create tax total
        return TaxTotal(
            tax_amount=total_tax_amount,
            tax_subtotals=consolidated_subtotals
        )
    
    def _map_legal_monetary_total(self, odoo_invoice: Dict[str, Any]) -> LegalMonetaryTotal:
        """Map Odoo invoice totals to UBL legal monetary total."""
        # Get required values
        amount_untaxed = Decimal(str(odoo_invoice.get("amount_untaxed", 0)))
        amount_tax = Decimal(str(odoo_invoice.get("amount_tax", 0)))
        amount_total = Decimal(str(odoo_invoice.get("amount_total", 0)))
        
        # Create legal monetary total
        return LegalMonetaryTotal(
            line_extension_amount=amount_untaxed,
            tax_exclusive_amount=amount_untaxed,
            tax_inclusive_amount=amount_total,
            payable_amount=amount_total
        )
    
    def _map_payment_terms(self, odoo_invoice: Dict[str, Any]) -> Optional[PaymentTerms]:
        """Map Odoo payment terms to UBL payment terms."""
        payment_term_note = odoo_invoice.get("invoice_payment_term_id", {}).get("name", "")
        if not payment_term_note:
            return None
            
        # Create payment terms
        return PaymentTerms(
            note=payment_term_note,
            payment_due_date=self._parse_date(odoo_invoice.get("invoice_date_due"))
        )
    
    def _map_payment_means(self, odoo_invoice: Dict[str, Any]) -> Optional[PaymentMeans]:
        """Map Odoo payment method to UBL payment means."""
        payment_method = odoo_invoice.get("payment_method_id", {}).get("name", "").lower()
        
        if not payment_method:
            return None
        
        # Try to map from known payment methods
        for key, value in self.PAYMENT_MEANS_MAPPING.items():
            if key in payment_method:
                return value
                
        # Default to credit transfer
        return PaymentMeans.CREDIT_TRANSFER
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[date]:
        """Parse date string to date object."""
        if not date_str:
            return None
            
        # Handle different date formats
        if isinstance(date_str, date):
            return date_str
            
        try:
            # Try ISO format first (YYYY-MM-DD)
            return datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            try:
                # Try EU format (DD.MM.YYYY)
                return datetime.strptime(date_str, "%d.%m.%Y").date()
            except ValueError:
                try:
                    # Try US format (MM/DD/YYYY)
                    return datetime.strptime(date_str, "%m/%d/%Y").date()
                except ValueError:
                    logger.warning(f"Could not parse date: {date_str}")
                    return None


# Create a singleton instance for reuse
odoo_ubl_mapper = OdooUBLMapper()