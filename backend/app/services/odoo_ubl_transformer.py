"""
Odoo to BIS Billing 3.0 UBL Data Transformation Service.

This module provides transformation functions for converting Odoo invoice data
to BIS Billing 3.0 UBL XML format and vice versa.
"""
import logging
import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime
import json

from app.schemas.invoice_validation import InvoiceValidationRequest
from app.services.odoo_ubl_mapper import odoo_ubl_mapper
from app.services.odoo_ubl_validator import odoo_ubl_validator

logger = logging.getLogger(__name__)

# Define UBL namespaces
NAMESPACES = {
    'xmlns': 'urn:oasis:names:specification:ubl:schema:xsd:Invoice-2',
    'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2',
    'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2',
    'ccts': 'urn:un:unece:uncefact:documentation:2',
    'ext': 'urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2',
    'qdt': 'urn:oasis:names:specification:ubl:schema:xsd:QualifiedDataTypes-2',
    'udt': 'urn:un:unece:uncefact:data:specification:UnqualifiedDataTypesSchemaModule:2',
    'xsi': 'http://www.w3.org/2001/XMLSchema-instance'
}


class OdooUBLTransformer:
    """
    Transformer for converting between Odoo invoice data and BIS Billing 3.0 UBL format.
    
    This class provides methods to:
    1. Transform Odoo invoice data to BIS Billing 3.0 UBL XML
    2. Validate the transformation against UBL schema
    3. Convert UBL XML back to structured data
    """
    
    def __init__(self):
        """Initialize the UBL transformer."""
        # Register namespaces for XML output
        for prefix, uri in NAMESPACES.items():
            ET.register_namespace(prefix, uri)
    
    def odoo_to_ubl_object(
        self, 
        odoo_invoice: Dict[str, Any], 
        company_info: Dict[str, Any]
    ) -> Tuple[InvoiceValidationRequest, List[Dict[str, str]]]:
        """
        Transform Odoo invoice data to UBL object format.
        
        Args:
            odoo_invoice: Odoo invoice data dictionary
            company_info: Company information for the supplier
            
        Returns:
            Tuple of (mapped_invoice, validation_issues)
        """
        validation_issues = []
        
        try:
            # Map Odoo invoice to UBL format
            mapped_invoice = odoo_ubl_mapper.map_invoice(odoo_invoice, company_info)
            
            # Validate the mapped invoice
            is_valid, errors = odoo_ubl_validator.validate_mapped_invoice(mapped_invoice)
            
            if not is_valid:
                # Convert validation errors to issue dictionaries
                for error in errors:
                    validation_issues.append({
                        "field": error.field,
                        "message": error.error,
                        "code": error.error_code or "VALIDATION_ERROR"
                    })
            
            return mapped_invoice, validation_issues
            
        except Exception as e:
            logger.error(f"Error transforming Odoo invoice to UBL object: {str(e)}")
            validation_issues.append({
                "field": "general",
                "message": f"Transformation error: {str(e)}",
                "code": "TRANSFORMATION_ERROR"
            })
            return None, validation_issues
    
    def ubl_object_to_xml(self, ubl_invoice: InvoiceValidationRequest) -> Tuple[str, List[Dict[str, str]]]:
        """
        Convert UBL object to UBL XML format.
        
        Args:
            ubl_invoice: UBL invoice object
            
        Returns:
            Tuple of (xml_string, conversion_issues)
        """
        conversion_issues = []
        
        try:
            # Create XML root element
            root = ET.Element("{urn:oasis:names:specification:ubl:schema:xsd:Invoice-2}Invoice")
            
            # Add namespace attributes
            for prefix, uri in NAMESPACES.items():
                if prefix == 'xmlns':
                    root.set('xmlns', uri)
                else:
                    root.set(f'xmlns:{prefix}', uri)
            
            # UBL version
            self._add_element(root, "cbc:UBLVersionID", "2.1")
            
            # Customization ID (BIS Billing 3.0)
            self._add_element(root, "cbc:CustomizationID", "urn:cen.eu:en16931:2017#compliant#urn:fdc:peppol.eu:2017:poacc:billing:3.0")
            
            # Profile ID (standard billing)
            self._add_element(root, "cbc:ProfileID", "urn:fdc:peppol.eu:2017:poacc:billing:01:1.0")
            
            # Invoice number
            self._add_element(root, "cbc:ID", ubl_invoice.invoice_number)
            
            # Invoice issue date
            self._add_element(root, "cbc:IssueDate", ubl_invoice.invoice_date.isoformat())
            
            # Due date
            if ubl_invoice.due_date:
                self._add_element(root, "cbc:DueDate", ubl_invoice.due_date.isoformat())
            
            # Invoice type code
            self._add_element(root, "cbc:InvoiceTypeCode", ubl_invoice.invoice_type_code.value)
            
            # Document currency code
            self._add_element(root, "cbc:DocumentCurrencyCode", ubl_invoice.currency_code.value)
            
            # Note (optional)
            if ubl_invoice.note:
                self._add_element(root, "cbc:Note", ubl_invoice.note)
            
            # Order reference (optional)
            if ubl_invoice.order_reference:
                order_ref = ET.SubElement(root, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}OrderReference")
                self._add_element(order_ref, "cbc:ID", ubl_invoice.order_reference)
            
            # Add accounting supplier party (seller)
            self._add_party(root, "AccountingSupplierParty", ubl_invoice.accounting_supplier_party)
            
            # Add accounting customer party (buyer)
            self._add_party(root, "AccountingCustomerParty", ubl_invoice.accounting_customer_party)
            
            # Add payment terms (optional)
            if ubl_invoice.payment_terms:
                payment_terms = ET.SubElement(root, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}PaymentTerms")
                self._add_element(payment_terms, "cbc:Note", ubl_invoice.payment_terms.note)
                if ubl_invoice.payment_terms.payment_due_date:
                    self._add_element(payment_terms, "cbc:PaymentDueDate", ubl_invoice.payment_terms.payment_due_date.isoformat())
            
            # Add tax total
            self._add_tax_total(root, ubl_invoice.tax_total)
            
            # Add legal monetary total
            self._add_monetary_total(root, ubl_invoice.legal_monetary_total)
            
            # Add invoice lines
            for line in ubl_invoice.invoice_lines:
                self._add_invoice_line(root, line)
            
            # Convert to string
            xml_string = ET.tostring(root, encoding='utf-8', method='xml').decode('utf-8')
            
            # Pretty-print XML (optional)
            # Note: In a production environment, you might want to use a library like lxml
            # for better formatting and XML handling
            return xml_string, conversion_issues
            
        except Exception as e:
            logger.error(f"Error converting UBL object to XML: {str(e)}")
            conversion_issues.append({
                "field": "general",
                "message": f"XML conversion error: {str(e)}",
                "code": "XML_CONVERSION_ERROR"
            })
            return "", conversion_issues
    
    def _add_element(self, parent: ET.Element, tag: str, text: Any) -> ET.Element:
        """Add an XML element with text to a parent element."""
        element = ET.SubElement(parent, tag)
        element.text = str(text)
        return element
    
    def _add_party(self, parent: ET.Element, party_type: str, party: Any) -> ET.Element:
        """Add a party element (supplier or customer) to the XML."""
        # This is a simplified implementation - a complete one would map all party fields
        party_element = ET.SubElement(parent, f"{{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}}{party_type}")
        party_node = ET.SubElement(party_element, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}Party")
        
        # Add party identification
        if party.party_identification:
            id_node = ET.SubElement(party_node, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}PartyIdentification")
            id_element = self._add_element(id_node, "cbc:ID", party.party_identification.id)
            if party.party_identification.scheme_id:
                id_element.set("schemeID", party.party_identification.scheme_id)
        
        # Add party name
        name_node = ET.SubElement(party_node, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}PartyName")
        self._add_element(name_node, "cbc:Name", party.party_name)
        
        # Add postal address
        self._add_address(party_node, party.postal_address)
        
        # Add tax scheme
        tax_node = ET.SubElement(party_node, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}PartyTaxScheme")
        if "company_id" in party.party_tax_scheme:
            self._add_element(tax_node, "cbc:CompanyID", party.party_tax_scheme["company_id"])
        
        tax_scheme = ET.SubElement(tax_node, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}TaxScheme")
        self._add_element(tax_scheme, "cbc:ID", party.party_tax_scheme.get("tax_scheme_id", "VAT"))
        
        # Add legal entity
        legal_node = ET.SubElement(party_node, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}PartyLegalEntity")
        self._add_element(legal_node, "cbc:RegistrationName", party.party_legal_entity.registration_name)
        
        if party.party_legal_entity.company_id:
            company_id_element = self._add_element(legal_node, "cbc:CompanyID", party.party_legal_entity.company_id)
            if party.party_legal_entity.company_id_scheme_id:
                company_id_element.set("schemeID", party.party_legal_entity.company_id_scheme_id)
        
        # Add contact information
        if party.contact:
            contact_node = ET.SubElement(party_node, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}Contact")
            if "name" in party.contact:
                self._add_element(contact_node, "cbc:Name", party.contact["name"])
            if "telephone" in party.contact:
                self._add_element(contact_node, "cbc:Telephone", party.contact["telephone"])
            if "email" in party.contact:
                self._add_element(contact_node, "cbc:ElectronicMail", party.contact["email"])
        
        return party_element
    
    def _add_address(self, parent: ET.Element, address: Any) -> ET.Element:
        """Add a postal address element to the XML."""
        address_node = ET.SubElement(parent, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}PostalAddress")
        
        # Street name
        self._add_element(address_node, "cbc:StreetName", address.street_name)
        
        # Additional street name (optional)
        if address.additional_street_name:
            self._add_element(address_node, "cbc:AdditionalStreetName", address.additional_street_name)
        
        # Building number (optional)
        if address.building_number:
            self._add_element(address_node, "cbc:BuildingNumber", address.building_number)
        
        # City name
        self._add_element(address_node, "cbc:CityName", address.city_name)
        
        # Postal zone (optional)
        if address.postal_zone:
            self._add_element(address_node, "cbc:PostalZone", address.postal_zone)
        
        # Country subdivision (optional)
        if address.country_subdivision:
            self._add_element(address_node, "cbc:CountrySubentity", address.country_subdivision)
        
        # Country
        country_node = ET.SubElement(address_node, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}Country")
        self._add_element(country_node, "cbc:IdentificationCode", address.country_code)
        
        return address_node
    
    def _add_tax_total(self, parent: ET.Element, tax_total: Any) -> ET.Element:
        """Add a tax total element to the XML."""
        tax_total_node = ET.SubElement(parent, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}TaxTotal")
        
        # Tax amount
        tax_amount_element = self._add_element(tax_total_node, "cbc:TaxAmount", tax_total.tax_amount)
        tax_amount_element.set("currencyID", "NGN")  # This should be dynamic based on invoice currency
        
        # Tax subtotals
        for subtotal in tax_total.tax_subtotals:
            subtotal_node = ET.SubElement(tax_total_node, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}TaxSubtotal")
            
            # Taxable amount
            taxable_amount_element = self._add_element(subtotal_node, "cbc:TaxableAmount", subtotal.taxable_amount)
            taxable_amount_element.set("currencyID", "NGN")  # This should be dynamic
            
            # Tax amount
            tax_amount_element = self._add_element(subtotal_node, "cbc:TaxAmount", subtotal.tax_amount)
            tax_amount_element.set("currencyID", "NGN")  # This should be dynamic
            
            # Tax category
            category_node = ET.SubElement(subtotal_node, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}TaxCategory")
            self._add_element(category_node, "cbc:ID", subtotal.tax_category.value)
            self._add_element(category_node, "cbc:Percent", subtotal.tax_percent)
            
            # Tax exemption reason (optional)
            if subtotal.tax_exemption_reason:
                self._add_element(category_node, "cbc:TaxExemptionReason", subtotal.tax_exemption_reason)
            
            # Tax scheme
            scheme_node = ET.SubElement(category_node, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}TaxScheme")
            self._add_element(scheme_node, "cbc:ID", "VAT")
        
        return tax_total_node
    
    def _add_monetary_total(self, parent: ET.Element, monetary_total: Any) -> ET.Element:
        """Add a legal monetary total element to the XML."""
        total_node = ET.SubElement(parent, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}LegalMonetaryTotal")
        
        # Line extension amount
        amount_element = self._add_element(total_node, "cbc:LineExtensionAmount", monetary_total.line_extension_amount)
        amount_element.set("currencyID", "NGN")  # This should be dynamic based on invoice currency
        
        # Tax exclusive amount
        tax_excl_element = self._add_element(total_node, "cbc:TaxExclusiveAmount", monetary_total.tax_exclusive_amount)
        tax_excl_element.set("currencyID", "NGN")  # This should be dynamic
        
        # Tax inclusive amount
        tax_incl_element = self._add_element(total_node, "cbc:TaxInclusiveAmount", monetary_total.tax_inclusive_amount)
        tax_incl_element.set("currencyID", "NGN")  # This should be dynamic
        
        # Allowance total amount (optional)
        if monetary_total.allowance_total_amount:
            allowance_element = self._add_element(total_node, "cbc:AllowanceTotalAmount", monetary_total.allowance_total_amount)
            allowance_element.set("currencyID", "NGN")  # This should be dynamic
        
        # Charge total amount (optional)
        if monetary_total.charge_total_amount:
            charge_element = self._add_element(total_node, "cbc:ChargeTotalAmount", monetary_total.charge_total_amount)
            charge_element.set("currencyID", "NGN")  # This should be dynamic
        
        # Prepaid amount (optional)
        if monetary_total.prepaid_amount:
            prepaid_element = self._add_element(total_node, "cbc:PrepaidAmount", monetary_total.prepaid_amount)
            prepaid_element.set("currencyID", "NGN")  # This should be dynamic
        
        # Payable amount
        payable_element = self._add_element(total_node, "cbc:PayableAmount", monetary_total.payable_amount)
        payable_element.set("currencyID", "NGN")  # This should be dynamic
        
        return total_node
    
    def _add_invoice_line(self, parent: ET.Element, line: Any) -> ET.Element:
        """Add an invoice line element to the XML."""
        line_node = ET.SubElement(parent, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}InvoiceLine")
        
        # Line ID
        self._add_element(line_node, "cbc:ID", line.id)
        
        # Invoiced quantity
        quantity_element = self._add_element(line_node, "cbc:InvoicedQuantity", line.invoiced_quantity)
        quantity_element.set("unitCode", line.unit_code.value)
        
        # Line extension amount
        amount_element = self._add_element(line_node, "cbc:LineExtensionAmount", line.line_extension_amount)
        amount_element.set("currencyID", "NGN")  # This should be dynamic based on invoice currency
        
        # Tax total (optional)
        if line.tax_total:
            self._add_tax_total(line_node, line.tax_total)
        
        # Item information
        item_node = ET.SubElement(line_node, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}Item")
        self._add_element(item_node, "cbc:Description", line.item_description)
        self._add_element(item_node, "cbc:Name", line.item_name)
        
        # Buyer's item identification (optional)
        if line.buyers_item_identification:
            buyer_id_node = ET.SubElement(item_node, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}BuyersItemIdentification")
            self._add_element(buyer_id_node, "cbc:ID", line.buyers_item_identification)
        
        # Seller's item identification (optional)
        if line.sellers_item_identification:
            seller_id_node = ET.SubElement(item_node, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}SellersItemIdentification")
            self._add_element(seller_id_node, "cbc:ID", line.sellers_item_identification)
        
        # Price information
        price_node = ET.SubElement(line_node, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}Price")
        price_amount_element = self._add_element(price_node, "cbc:PriceAmount", line.price_amount)
        price_amount_element.set("currencyID", "NGN")  # This should be dynamic
        
        # Base quantity (optional)
        if line.base_quantity and line.base_quantity != 1:
            base_quantity_element = self._add_element(price_node, "cbc:BaseQuantity", line.base_quantity)
            base_quantity_element.set("unitCode", line.unit_code.value)
        
        return line_node


# Create a singleton instance for reuse
odoo_ubl_transformer = OdooUBLTransformer()
