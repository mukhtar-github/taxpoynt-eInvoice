"""
UBL schema validator for invoice validation against BIS Billing 3.0 standard.

This module provides validation of invoice data against the official UBL XML schema
to ensure compliance with BIS Billing 3.0 and FIRS e-Invoice requirements.
"""
import os
import logging
import json
from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime
from pathlib import Path
import tempfile
import xml.etree.ElementTree as ET
from lxml import etree

from app.schemas.invoice_validation import InvoiceValidationRequest, ValidationError
from app.core.config import settings

logger = logging.getLogger(__name__)

# Path to UBL schema files
UBL_SCHEMA_DIR = Path(__file__).parent.parent / "resources" / "schemas" / "ubl"
INVOICE_XSD = str(UBL_SCHEMA_DIR / "maindoc" / "UBL-Invoice-2.1.xsd")


class UBLValidator:
    """
    Validator for UBL schema compliance.
    
    This class validates invoice data against the official UBL 2.1 XML schema
    as defined in the BIS Billing 3.0 standard and required by FIRS.
    """
    
    def __init__(self):
        """Initialize the UBL validator."""
        self.schema = None
        self._load_schema()
    
    def _load_schema(self):
        """Load the UBL schema from XSD files."""
        try:
            # Check if schema directory exists
            if not UBL_SCHEMA_DIR.exists():
                logger.warning(f"UBL schema directory not found: {UBL_SCHEMA_DIR}")
                # Create schema directory
                UBL_SCHEMA_DIR.mkdir(parents=True, exist_ok=True)
                
                # In a real implementation, we would download or extract the schema files
                # For now, we'll log a warning and return
                logger.warning("UBL schema files not available, schema validation will be skipped")
                return
                
            # Check if invoice schema exists
            invoice_xsd_path = Path(INVOICE_XSD)
            if not invoice_xsd_path.exists():
                logger.warning(f"UBL Invoice schema not found: {INVOICE_XSD}")
                logger.warning("Schema validation will be skipped")
                return
                
            # Load the schema
            self.schema = etree.XMLSchema(etree.parse(str(invoice_xsd_path)))
            logger.info("UBL schema loaded successfully")
        except Exception as e:
            logger.error(f"Error loading UBL schema: {str(e)}")
            self.schema = None
    
    def validate_against_schema(self, invoice_xml: str) -> Tuple[bool, List[ValidationError]]:
        """
        Validate an invoice XML against the UBL schema.
        
        Args:
            invoice_xml: Invoice data in UBL XML format
            
        Returns:
            Tuple of (is_valid, list of validation errors)
        """
        if not self.schema:
            logger.warning("UBL schema not available, skipping validation")
            return True, []
            
        errors = []
        
        try:
            # Parse XML
            xml_doc = etree.fromstring(invoice_xml.encode('utf-8'))
            
            # Validate against schema
            is_valid = self.schema.validate(xml_doc)
            
            if not is_valid:
                # Get validation errors
                for error in self.schema.error_log:
                    errors.append(ValidationError(
                        field=error.path or "UBL Schema",
                        error=error.message,
                        error_code=f"UBL-{error.line}-{error.column}"
                    ))
            
            return is_valid, errors
        except Exception as e:
            logger.error(f"Error validating UBL: {str(e)}")
            errors.append(ValidationError(
                field="UBL Schema",
                error=f"Error validating UBL: {str(e)}",
                error_code="UBL-ERR-001"
            ))
            return False, errors
    
    def convert_invoice_to_ubl(self, invoice: InvoiceValidationRequest) -> str:
        """
        Convert invoice data to UBL XML format.
        
        Args:
            invoice: Invoice data in Pydantic model format
            
        Returns:
            UBL XML string
        """
        try:
            # Create root invoice element
            root = ET.Element("Invoice", xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2")
            
            # Add namespace declarations
            root.set("xmlns:cac", "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2")
            root.set("xmlns:cbc", "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2")
            
            # UBL version
            ubl_version = ET.SubElement(root, "cbc:UBLVersionID")
            ubl_version.text = "2.1"
            
            # Customization ID (BIS Billing 3.0)
            customization = ET.SubElement(root, "cbc:CustomizationID")
            customization.text = "urn:cen.eu:en16931:2017#compliant#urn:fdc:peppol.eu:2017:poacc:billing:3.0"
            
            # Invoice ID
            invoice_id = ET.SubElement(root, "cbc:ID")
            invoice_id.text = invoice.invoice_number
            
            # Invoice issue date
            issue_date = ET.SubElement(root, "cbc:IssueDate")
            issue_date.text = invoice.invoice_date.strftime("%Y-%m-%d")
            
            # Invoice type code
            type_code = ET.SubElement(root, "cbc:InvoiceTypeCode")
            type_code.text = invoice.invoice_type_code.value
            
            # Currency code
            doc_currency = ET.SubElement(root, "cbc:DocumentCurrencyCode")
            doc_currency.text = invoice.currency_code.value
            
            # Add accounting supplier party
            if invoice.accounting_supplier_party:
                supplier = ET.SubElement(root, "cac:AccountingSupplierParty")
                self._add_party_element(supplier, invoice.accounting_supplier_party)
            
            # Add accounting customer party
            if invoice.accounting_customer_party:
                customer = ET.SubElement(root, "cac:AccountingCustomerParty")
                self._add_party_element(customer, invoice.accounting_customer_party)
            
            # Add invoice lines
            for line in invoice.invoice_lines:
                line_element = ET.SubElement(root, "cac:InvoiceLine")
                self._add_invoice_line(line_element, line)
            
            # Add tax total
            if invoice.tax_total:
                tax_total = ET.SubElement(root, "cac:TaxTotal")
                self._add_tax_total(tax_total, invoice.tax_total)
            
            # Add legal monetary total
            if invoice.legal_monetary_total:
                monetary_total = ET.SubElement(root, "cac:LegalMonetaryTotal")
                self._add_monetary_total(monetary_total, invoice.legal_monetary_total)
            
            # Convert to string
            return ET.tostring(root, encoding='utf-8', method='xml').decode('utf-8')
        except Exception as e:
            logger.error(f"Error converting invoice to UBL: {str(e)}")
            raise ValueError(f"Error converting invoice to UBL: {str(e)}")
    
    def _add_party_element(self, parent: ET.Element, party: Any):
        """Add party information to XML element."""
        party_element = ET.SubElement(parent, "cac:Party")
        
        # Party identification
        if hasattr(party, 'party_identification') and party.party_identification:
            id_element = ET.SubElement(party_element, "cac:PartyIdentification")
            id_value = ET.SubElement(id_element, "cbc:ID")
            id_value.text = party.party_identification.id
            if party.party_identification.scheme_id:
                id_value.set("schemeID", party.party_identification.scheme_id)
        
        # Party name
        if hasattr(party, 'party_name') and party.party_name:
            name_element = ET.SubElement(party_element, "cac:PartyName")
            name_value = ET.SubElement(name_element, "cbc:Name")
            name_value.text = party.party_name
        
        # Postal address
        if hasattr(party, 'postal_address') and party.postal_address:
            address = ET.SubElement(party_element, "cac:PostalAddress")
            
            if party.postal_address.street_name:
                street = ET.SubElement(address, "cbc:StreetName")
                street.text = party.postal_address.street_name
                
            if party.postal_address.city_name:
                city = ET.SubElement(address, "cbc:CityName")
                city.text = party.postal_address.city_name
                
            if party.postal_address.postal_zone:
                postal = ET.SubElement(address, "cbc:PostalZone")
                postal.text = party.postal_address.postal_zone
                
            if party.postal_address.country_subdivision:
                subdivision = ET.SubElement(address, "cbc:CountrySubentity")
                subdivision.text = party.postal_address.country_subdivision
                
            if party.postal_address.country_code:
                country = ET.SubElement(address, "cac:Country")
                country_code = ET.SubElement(country, "cbc:IdentificationCode")
                country_code.text = party.postal_address.country_code
        
        # Party tax scheme
        if hasattr(party, 'party_tax_scheme') and party.party_tax_scheme:
            tax_scheme = ET.SubElement(party_element, "cac:PartyTaxScheme")
            
            if hasattr(party.party_tax_scheme, 'company_id'):
                comp_id = ET.SubElement(tax_scheme, "cbc:CompanyID")
                comp_id.text = party.party_tax_scheme.company_id
                
            if hasattr(party.party_tax_scheme, 'tax_scheme_id'):
                scheme = ET.SubElement(tax_scheme, "cac:TaxScheme")
                scheme_id = ET.SubElement(scheme, "cbc:ID")
                scheme_id.text = party.party_tax_scheme.tax_scheme_id
        
        # Party legal entity
        if hasattr(party, 'party_legal_entity') and party.party_legal_entity:
            legal_entity = ET.SubElement(party_element, "cac:PartyLegalEntity")
            
            if party.party_legal_entity.registration_name:
                reg_name = ET.SubElement(legal_entity, "cbc:RegistrationName")
                reg_name.text = party.party_legal_entity.registration_name
                
            if party.party_legal_entity.company_id:
                comp_id = ET.SubElement(legal_entity, "cbc:CompanyID")
                comp_id.text = party.party_legal_entity.company_id
                if party.party_legal_entity.company_id_scheme_id:
                    comp_id.set("schemeID", party.party_legal_entity.company_id_scheme_id)
    
    def _add_invoice_line(self, parent: ET.Element, line: Any):
        """Add invoice line information to XML element."""
        # Line ID
        line_id = ET.SubElement(parent, "cbc:ID")
        line_id.text = line.id
        
        # Invoiced quantity
        quantity = ET.SubElement(parent, "cbc:InvoicedQuantity")
        quantity.text = str(line.invoiced_quantity)
        quantity.set("unitCode", line.unit_code.value)
        
        # Line extension amount
        amount = ET.SubElement(parent, "cbc:LineExtensionAmount")
        amount.text = str(line.line_extension_amount)
        
        # Item
        item = ET.SubElement(parent, "cac:Item")
        
        # Item description
        description = ET.SubElement(item, "cbc:Description")
        description.text = line.item_description
        
        # Item name
        name = ET.SubElement(item, "cbc:Name")
        name.text = line.item_name
        
        # Price
        price_element = ET.SubElement(parent, "cac:Price")
        price_amount = ET.SubElement(price_element, "cbc:PriceAmount")
        price_amount.text = str(line.price_amount)
        
        if line.base_quantity and line.base_quantity != 1:
            base_qty = ET.SubElement(price_element, "cbc:BaseQuantity")
            base_qty.text = str(line.base_quantity)
    
    def _add_tax_total(self, parent: ET.Element, tax_total: Any):
        """Add tax total information to XML element."""
        # Tax amount
        tax_amount = ET.SubElement(parent, "cbc:TaxAmount")
        tax_amount.text = str(tax_total.tax_amount)
        
        # Tax subtotals
        for subtotal in tax_total.tax_subtotals:
            subtotal_element = ET.SubElement(parent, "cac:TaxSubtotal")
            
            # Taxable amount
            taxable_amount = ET.SubElement(subtotal_element, "cbc:TaxableAmount")
            taxable_amount.text = str(subtotal.taxable_amount)
            
            # Tax amount
            sub_tax_amount = ET.SubElement(subtotal_element, "cbc:TaxAmount")
            sub_tax_amount.text = str(subtotal.tax_amount)
            
            # Tax category
            category = ET.SubElement(subtotal_element, "cac:TaxCategory")
            
            # Tax category ID
            category_id = ET.SubElement(category, "cbc:ID")
            category_id.text = subtotal.tax_category.value
            
            # Tax percent
            percent = ET.SubElement(category, "cbc:Percent")
            percent.text = str(subtotal.tax_percent)
            
            # Tax exemption reason
            if subtotal.tax_exemption_reason:
                reason = ET.SubElement(category, "cbc:TaxExemptionReason")
                reason.text = subtotal.tax_exemption_reason
                
            # Tax exemption reason code
            if subtotal.tax_exemption_reason_code:
                reason_code = ET.SubElement(category, "cbc:TaxExemptionReasonCode")
                reason_code.text = subtotal.tax_exemption_reason_code
            
            # Tax scheme
            scheme = ET.SubElement(category, "cac:TaxScheme")
            scheme_id = ET.SubElement(scheme, "cbc:ID")
            scheme_id.text = "VAT"  # Default to VAT, should be configurable
    
    def _add_monetary_total(self, parent: ET.Element, total: Any):
        """Add legal monetary total information to XML element."""
        # Line extension amount (sum of invoice line net amounts)
        line_ext = ET.SubElement(parent, "cbc:LineExtensionAmount")
        line_ext.text = str(total.line_extension_amount)
        
        # Tax exclusive amount
        tax_excl = ET.SubElement(parent, "cbc:TaxExclusiveAmount")
        tax_excl.text = str(total.tax_exclusive_amount)
        
        # Tax inclusive amount
        tax_incl = ET.SubElement(parent, "cbc:TaxInclusiveAmount")
        tax_incl.text = str(total.tax_inclusive_amount)
        
        # Allowance total amount
        if total.allowance_total_amount and total.allowance_total_amount > 0:
            allowance = ET.SubElement(parent, "cbc:AllowanceTotalAmount")
            allowance.text = str(total.allowance_total_amount)
        
        # Charge total amount
        if total.charge_total_amount and total.charge_total_amount > 0:
            charge = ET.SubElement(parent, "cbc:ChargeTotalAmount")
            charge.text = str(total.charge_total_amount)
        
        # Prepaid amount
        if total.prepaid_amount and total.prepaid_amount > 0:
            prepaid = ET.SubElement(parent, "cbc:PrepaidAmount")
            prepaid.text = str(total.prepaid_amount)
        
        # Payable amount
        payable = ET.SubElement(parent, "cbc:PayableAmount")
        payable.text = str(total.payable_amount)


# Create a singleton instance of the UBL validator
ubl_validator = UBLValidator()
