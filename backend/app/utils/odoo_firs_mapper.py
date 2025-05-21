"""
Odoo to FIRS UBL Mapping Utility

This module provides utilities for mapping Odoo invoice data to the FIRS e-Invoice
format using the UBL (Universal Business Language) standard. It ensures that all
required fields for FIRS compliance are correctly mapped and validated.
"""

import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
from uuid import uuid4

from app.core.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

class OdooFIRSMapper:
    """
    Maps Odoo invoice data to FIRS-compliant format.
    
    This class handles the transformation of Odoo invoice data to the
    format required by the FIRS e-Invoice API, ensuring that all required
    fields are present and correctly formatted.
    """
    
    def __init__(self):
        """Initialize the mapper with reference data."""
        self.reference_data_dir = os.path.join(settings.REFERENCE_DATA_DIR, 'firs')
        self._load_reference_data()
    
    def _load_reference_data(self):
        """Load reference data from JSON files."""
        try:
            # Load invoice types
            invoice_types_path = os.path.join(self.reference_data_dir, 'invoice_types.json')
            with open(invoice_types_path, 'r') as f:
                self.invoice_types = json.load(f).get('invoice_types', [])
            logger.info(f"Loaded {len(self.invoice_types)} invoice types from reference data")
            
            # Load currencies
            currencies_path = os.path.join(self.reference_data_dir, 'currencies.json')
            with open(currencies_path, 'r') as f:
                self.currencies = json.load(f).get('currencies', [])
            logger.info(f"Loaded {len(self.currencies)} currencies from reference data")
            
            # Load VAT exemptions
            vat_exemptions_path = os.path.join(self.reference_data_dir, 'vat_exemptions.json')
            with open(vat_exemptions_path, 'r') as f:
                self.vat_exemptions = json.load(f).get('vat_exemptions', [])
            logger.info(f"Loaded {len(self.vat_exemptions)} VAT exemptions from reference data")
            
        except Exception as e:
            logger.error(f"Error loading reference data: {str(e)}")
            # Initialize with empty lists if loading fails
            self.invoice_types = []
            self.currencies = []
            self.vat_exemptions = []
    
    def get_invoice_type_code(self, odoo_type: str) -> str:
        """
        Map Odoo invoice type to FIRS invoice type code.
        
        Args:
            odoo_type: Odoo invoice type ('out_invoice', 'out_refund', etc.)
            
        Returns:
            FIRS invoice type code
        """
        # Default mapping
        type_mapping = {
            'out_invoice': 'standard',
            'out_refund': 'credit_note',
            'in_invoice': 'standard',
            'in_refund': 'credit_note',
            'entry': 'standard'
        }
        
        firs_type = type_mapping.get(odoo_type, 'standard')
        
        # Validate against reference data if available
        if self.invoice_types:
            valid_types = [t.get('code') for t in self.invoice_types]
            if firs_type not in valid_types:
                logger.warning(f"Invoice type {firs_type} not found in reference data. Using 'standard' as fallback.")
                firs_type = 'standard'
        
        return firs_type
    
    def get_currency_code(self, odoo_currency: str) -> str:
        """
        Map Odoo currency to FIRS currency code.
        
        Args:
            odoo_currency: Odoo currency code
            
        Returns:
            FIRS currency code
        """
        # Default is NGN if not found
        default_currency = 'NGN'
        
        if not odoo_currency:
            return default_currency
            
        # If we have reference data, validate against it
        if self.currencies:
            valid_codes = [c.get('code') for c in self.currencies]
            if odoo_currency.upper() in valid_codes:
                return odoo_currency.upper()
            logger.warning(f"Currency {odoo_currency} not found in reference data. Using {default_currency} as fallback.")
        
        return default_currency
    
    def get_vat_exemption_code(self, odoo_tax_id: Optional[str], tax_rate: float) -> Optional[str]:
        """
        Map Odoo tax to FIRS VAT exemption code.
        
        Args:
            odoo_tax_id: Odoo tax ID
            tax_rate: Tax rate percentage
            
        Returns:
            FIRS VAT exemption code or None if not exempt
        """
        # If tax rate is 0, we need an exemption code
        if tax_rate == 0:
            # Default exemption code
            default_exemption = 'VAT-EXEMPT-1'
            
            # If we have reference data, find a suitable exemption
            if self.vat_exemptions:
                # First try to match by code if odoo_tax_id looks like an exemption code
                for exemption in self.vat_exemptions:
                    if exemption.get('code') == odoo_tax_id:
                        return exemption.get('code')
                
                # If not found, use the first exemption as default
                if self.vat_exemptions:
                    return self.vat_exemptions[0].get('code', default_exemption)
            
            return default_exemption
        
        # Not exempt
        return None
    
    def map_partner_to_party(self, partner_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map Odoo partner data to FIRS party format.
        
        Args:
            partner_data: Odoo partner data
            
        Returns:
            FIRS party data
        """
        # Extract TIN from VAT number if available
        tin = partner_data.get('vat', '').strip()
        # If TIN starts with "NG", remove it
        if tin and tin.upper().startswith('NG'):
            tin = tin[2:].strip()
        
        # Format Nigerian TIN (12345678-1234)
        if tin and len(tin) >= 12:
            base_tin = tin[:8]
            suffix = tin[8:].replace('-', '').strip()[:4]
            tin = f"{base_tin}-{suffix}"
        
        address = partner_data.get('address', {})
        if not address and 'street' in partner_data:
            # If address is not a nested object, construct it from flat fields
            address = {
                'street': partner_data.get('street', ''),
                'street2': partner_data.get('street2', ''),
                'city': partner_data.get('city', ''),
                'state': partner_data.get('state_id', {}).get('name', '') if isinstance(partner_data.get('state_id'), dict) else partner_data.get('state', ''),
                'zip': partner_data.get('zip', ''),
                'country': partner_data.get('country_id', {}).get('code', 'NG') if isinstance(partner_data.get('country_id'), dict) else partner_data.get('country_code', 'NG')
            }
        
        # Format the address string
        address_str = ", ".join(filter(None, [
            address.get('street', ''),
            address.get('street2', ''),
            address.get('city', ''),
            address.get('state', ''),
            address.get('zip', '')
        ]))
        
        return {
            "name": partner_data.get('name', ''),
            "tin": tin,
            "address": {
                "street": address.get('street', ''),
                "city": address.get('city', ''),
                "state": address.get('state', ''),
                "country": address.get('country', 'NG'),
                "formatted": address_str
            },
            "contact": {
                "email": partner_data.get('email', ''),
                "phone": partner_data.get('phone', partner_data.get('mobile', ''))
            }
        }
    
    def map_line_item(self, line_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map Odoo invoice line to FIRS line item.
        
        Args:
            line_data: Odoo invoice line data
            
        Returns:
            FIRS line item data
        """
        # Extract tax information
        tax_rate = 0.0
        taxes = line_data.get('tax_ids', [])
        if taxes and isinstance(taxes, list):
            # Get the average tax rate if multiple taxes
            tax_sum = sum(tax.get('amount', 0) for tax in taxes if isinstance(tax, dict))
            tax_rate = tax_sum / len(taxes) if taxes else 0.0
        elif isinstance(taxes, dict):
            tax_rate = taxes.get('amount', 0.0)
        
        # If tax_rate is provided directly, use that
        if 'tax_rate' in line_data:
            tax_rate = line_data.get('tax_rate', 0.0)
        
        # Calculate amounts
        quantity = float(line_data.get('quantity', 1))
        unit_price = float(line_data.get('price_unit', 0.0))
        discount_percentage = float(line_data.get('discount', 0.0))
        
        # Calculate discount amount
        discount_amount = (unit_price * quantity * discount_percentage / 100)
        
        # Calculate subtotal (before tax)
        subtotal = (unit_price * quantity) - discount_amount
        
        # Calculate tax amount
        tax_amount = subtotal * (tax_rate / 100)
        
        # Calculate total (with tax)
        total = subtotal + tax_amount
        
        # Get VAT exemption code if applicable
        vat_exemption = None
        if tax_rate == 0:
            tax_id = line_data.get('tax_ids', [])
            if isinstance(tax_id, list) and tax_id and isinstance(tax_id[0], dict):
                tax_id = tax_id[0].get('id', '')
            vat_exemption = self.get_vat_exemption_code(tax_id, tax_rate)
        
        return {
            "item_id": line_data.get('id', str(uuid4())),
            "description": line_data.get('name', ''),
            "quantity": quantity,
            "unit_of_measure": line_data.get('uom_id', {}).get('name', 'Unit') if isinstance(line_data.get('uom_id'), dict) else line_data.get('uom', 'Unit'),
            "unit_price": unit_price,
            "discount_percentage": discount_percentage,
            "discount_amount": discount_amount,
            "tax_rate": tax_rate,
            "tax_amount": tax_amount,
            "subtotal": subtotal,
            "total": total,
            "vat_exemption_code": vat_exemption
        }
    
    def map_odoo_invoice_to_firs(self, odoo_invoice: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map Odoo invoice to FIRS invoice format.
        
        Args:
            odoo_invoice: Odoo invoice data
            
        Returns:
            FIRS-compliant invoice data
        """
        # Extract basic invoice information
        invoice_number = odoo_invoice.get('name', '') or odoo_invoice.get('number', '')
        invoice_date = odoo_invoice.get('invoice_date', '') or odoo_invoice.get('date_invoice', '')
        
        # Format date if it's a datetime object
        if isinstance(invoice_date, datetime):
            invoice_date = invoice_date.strftime('%Y-%m-%d')
        
        # Get invoice type
        odoo_type = odoo_invoice.get('type', 'out_invoice')
        invoice_type = self.get_invoice_type_code(odoo_type)
        
        # Get currency
        currency_code = odoo_invoice.get('currency_id', {}).get('name', 'NGN') if isinstance(odoo_invoice.get('currency_id'), dict) else odoo_invoice.get('currency', 'NGN')
        currency_code = self.get_currency_code(currency_code)
        
        # Map partners to parties
        partner_data = odoo_invoice.get('partner_id', {}) if isinstance(odoo_invoice.get('partner_id'), dict) else odoo_invoice.get('partner', {})
        company_data = odoo_invoice.get('company_id', {}) if isinstance(odoo_invoice.get('company_id'), dict) else odoo_invoice.get('company', {})
        
        customer = self.map_partner_to_party(partner_data)
        supplier = self.map_partner_to_party(company_data)
        
        # Map line items
        line_items = []
        lines = odoo_invoice.get('invoice_line_ids', []) or odoo_invoice.get('invoice_lines', []) or odoo_invoice.get('lines', [])
        
        for line in lines:
            line_items.append(self.map_line_item(line))
        
        # Calculate totals
        subtotal = sum(item['subtotal'] for item in line_items)
        tax_total = sum(item['tax_amount'] for item in line_items)
        discount_total = sum(item['discount_amount'] for item in line_items)
        grand_total = subtotal + tax_total
        
        # Build the FIRS invoice structure
        firs_invoice = {
            "invoice_number": invoice_number,
            "invoice_type": invoice_type,
            "invoice_date": invoice_date,
            "due_date": odoo_invoice.get('date_due', invoice_date),
            "currency_code": currency_code,
            "customer": customer,
            "supplier": supplier,
            "items": line_items,
            "totals": {
                "subtotal": subtotal,
                "tax_total": tax_total,
                "discount_total": discount_total,
                "grand_total": grand_total
            },
            "payment_terms": odoo_invoice.get('payment_term_id', {}).get('name', '') if isinstance(odoo_invoice.get('payment_term_id'), dict) else odoo_invoice.get('payment_terms', ''),
            "notes": odoo_invoice.get('narration', '') or odoo_invoice.get('comment', ''),
            "metadata": {
                "odoo_id": odoo_invoice.get('id', ''),
                "transformed_at": datetime.now().isoformat()
            }
        }
        
        # Validate the invoice has all required fields
        self._validate_firs_invoice(firs_invoice)
        
        return firs_invoice
    
    def _validate_firs_invoice(self, invoice: Dict[str, Any]) -> None:
        """
        Validate that the FIRS invoice has all required fields.
        
        Args:
            invoice: FIRS invoice data
            
        Raises:
            ValueError: If any required fields are missing
        """
        required_fields = [
            'invoice_number', 
            'invoice_type', 
            'invoice_date', 
            'currency_code',
            'customer',
            'supplier',
            'items',
            'totals'
        ]
        
        missing_fields = [field for field in required_fields if field not in invoice]
        
        if missing_fields:
            raise ValueError(f"FIRS invoice missing required fields: {', '.join(missing_fields)}")
        
        # Validate customer and supplier have required fields
        for party_type in ['customer', 'supplier']:
            party = invoice.get(party_type, {})
            party_required_fields = ['name', 'address']
            party_missing_fields = [field for field in party_required_fields if field not in party]
            
            if party_missing_fields:
                raise ValueError(f"{party_type.capitalize()} missing required fields: {', '.join(party_missing_fields)}")
        
        # Validate at least one line item exists
        if not invoice.get('items', []):
            raise ValueError("Invoice must have at least one line item")

# Create a default instance for easy importing
odoo_firs_mapper = OdooFIRSMapper()
