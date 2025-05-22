#!/usr/bin/env python3
"""
Standalone test script for Odoo to FIRS mapping logic.

This script implements a simplified version of the OdooFIRSMapper class to test
the mapping logic independently from the full application stack.
"""

import os
import json
import logging
from uuid import uuid4
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pprint import pprint

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger("standalone_mapper_test")

class StandaloneOdooFIRSMapper:
    """Simplified standalone version of the OdooFIRSMapper class."""
    
    def get_currency_code(self, odoo_currency: str) -> str:
        """Map Odoo currency to FIRS currency code."""
        # Common currency mappings
        currency_map = {
            "NGN": "NGN",
            "USD": "USD",
            "EUR": "EUR",
            "GBP": "GBP",
            "Naira": "NGN",
            "Dollar": "USD",
            "Euro": "EUR",
            "Pound": "GBP"
        }
        return currency_map.get(odoo_currency, "NGN")
    
    def get_vat_exemption_code(self, odoo_tax_id: Optional[str], tax_rate: float) -> Optional[str]:
        """Map Odoo tax to FIRS VAT exemption code."""
        if tax_rate == 0:
            # Map common zero-rate exemption codes
            if odoo_tax_id and "exempt" in str(odoo_tax_id).lower():
                return "VATEX-EU-O"
            return "VATEX-NG-GDS"
        return None
    
    def map_partner_to_party(self, partner_data: Dict[str, Any], is_supplier: bool = False) -> Dict[str, Any]:
        """Map Odoo partner data to FIRS party format."""
        # Extract TIN from VAT number if available
        tin = partner_data.get('vat', '').strip()
        # If TIN starts with "NG", remove it
        if tin and tin.upper().startswith('NG'):
            tin = tin[2:].strip()
        
        # Format Nigerian TIN (12345678-1234)
        if tin and len(tin) >= 8:
            # Extract base and suffix, handling various formats
            if '-' in tin:
                parts = tin.split('-')
                base_tin = parts[0].strip()[:8]
                suffix = parts[1].strip()[:4] if len(parts) > 1 else '0001'
            else:
                base_tin = tin[:8]
                suffix = tin[8:].strip()[:4] if len(tin) > 8 else '0001'
            
            tin = f"{base_tin}-{suffix}"
        elif not tin:
            # Use default TIN format if missing (FIRS requires TIN)
            tin = "TIN-" + ("000001" if is_supplier else "000002")
            logger.warning(f"Missing TIN for {'supplier' if is_supplier else 'customer'} {partner_data.get('name', '')}, using default: {tin}")
        
        # Extract and validate email (mandatory for FIRS)
        email = partner_data.get('email', '').strip()
        if not email:
            # Use a placeholder email if missing (FIRS requires email)
            email = f"{'supplier' if is_supplier else 'customer'}@taxpoynt.example.com"
            logger.warning(f"Missing email for {'supplier' if is_supplier else 'customer'} {partner_data.get('name', '')}, using placeholder: {email}")
        
        # Extract phone (format with country code for FIRS)
        phone = partner_data.get('phone', partner_data.get('mobile', '')).strip()
        if phone and not phone.startswith('+'):
            # Add Nigeria country code if missing
            phone = f"+234{phone.lstrip('0')}"
        
        # Extract address information
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
        
        # Get street name (mandatory for FIRS)
        street_name = address.get('street', '')
        if not street_name:
            street_name = "Unknown Street"
            logger.warning(f"Missing street address for {'supplier' if is_supplier else 'customer'} {partner_data.get('name', '')}, using placeholder")
        
        # Get city name (mandatory for FIRS)
        city_name = address.get('city', '')
        if not city_name:
            city_name = "Unknown City"
            logger.warning(f"Missing city for {'supplier' if is_supplier else 'customer'} {partner_data.get('name', '')}, using placeholder")
        
        # Get country code (mandatory for FIRS)
        country_code = address.get('country', 'NG')
        if len(country_code) > 2:
            # Try to extract ISO code if full country name is provided
            country_code = country_code[:2].upper()
        
        # Get postal code
        postal_zone = address.get('zip', '')
        
        # Build party data according to FIRS API specifications
        party_data = {
            "party_name": partner_data.get('name', ''),
            "tin": tin,
            "email": email,
            "business_description": partner_data.get('business_description', f"{'Supplier' if is_supplier else 'Customer'} of goods and services")
        }
        
        # Add telephone if available
        if phone:
            party_data["telephone"] = phone
        
        # Add postal address
        party_data["postal_address"] = {
            "street_name": street_name,
            "city_name": city_name,
            "postal_zone": postal_zone,
            "country": country_code
        }
        
        # Add additional street name if available
        if address.get('street2'):
            party_data["postal_address"]["additional_street_name"] = address.get('street2')
        
        return party_data
    
    def map_line_item(self, line_data: Dict[str, Any]) -> Dict[str, Any]:
        """Map Odoo invoice line to FIRS line item according to BIS Billing 3.0 format."""
        # Extract line identification
        line_id = line_data.get('id', str(uuid4()))
        if isinstance(line_id, (int, float)):
            line_id = f"LINE-{line_id}"
        
        # Get item description
        description = line_data.get('name', '') or line_data.get('product_id', {}).get('name', '') if isinstance(line_data.get('product_id'), dict) else ''
        if not description:
            description = "Unnamed Item"
            logger.warning(f"Missing description for line item {line_id}, using placeholder")
        
        # Extract quantity information
        quantity = float(line_data.get('quantity', 1))
        if quantity <= 0:
            quantity = 1
            logger.warning(f"Invalid quantity for line item {line_id}, defaulting to 1")
        
        # Extract unit of measure
        uom = line_data.get('uom_id', {}).get('name', 'Unit') if isinstance(line_data.get('uom_id'), dict) else line_data.get('uom', 'EA')
        if not uom:
            uom = "EA"  # Each (standard UBL unit)
        
        # Extract price information
        unit_price = float(line_data.get('price_unit', 0.0))
        
        # Calculate line extension amount (quantity * unit price)
        line_extension_amount = unit_price * quantity
        
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
        
        # Calculate tax amount
        tax_amount = line_extension_amount * (tax_rate / 100)
        
        # Calculate discount
        discount_percentage = float(line_data.get('discount', 0.0))
        discount_amount = (unit_price * quantity * discount_percentage / 100)
        
        # Determine tax scheme
        tax_scheme_id = "VAT"
        if tax_rate == 0:
            tax_id = line_data.get('tax_ids', [])
            if isinstance(tax_id, list) and tax_id and isinstance(tax_id[0], dict):
                tax_id = tax_id[0].get('id', '')
            exemption_code = self.get_vat_exemption_code(tax_id, tax_rate)
            if exemption_code:
                tax_scheme_id = exemption_code
        
        # Build line item in FIRS/UBL format
        invoice_line = {
            "id": str(line_id),
            "invoiced_quantity": quantity,
            "invoiced_quantity_unit_code": uom,
            "line_extension_amount": line_extension_amount,
            "item": {
                "name": description,
                "description": description,
                "sellers_item_identification": {
                    "id": line_data.get('product_id', {}).get('default_code', f"PROD-{line_id}") if isinstance(line_data.get('product_id'), dict) else f"PROD-{line_id}"
                }
            },
            "price": {
                "price_amount": unit_price,
                "base_quantity": 1,
                "base_quantity_unit_code": uom
            }
        }
        
        # Add tax information if applicable
        if tax_rate > 0 or tax_scheme_id != "VAT":
            invoice_line["tax_total"] = {
                "tax_amount": tax_amount,
                "tax_subtotal": {
                    "taxable_amount": line_extension_amount,
                    "tax_amount": tax_amount,
                    "tax_category": {
                        "id": tax_scheme_id,
                        "percent": tax_rate,
                        "tax_scheme": {
                            "id": "FIRS"
                        }
                    }
                }
            }
        
        # Add allowance/charge for discounts if applicable
        if discount_percentage > 0 and discount_amount > 0:
            invoice_line["allowance_charge"] = {
                "charge_indicator": False,  # False = allowance (discount), True = charge
                "allowance_charge_reason": "Discount",
                "amount": discount_amount,
                "base_amount": line_extension_amount + discount_amount
            }
        
        return invoice_line
    
    def map_odoo_invoice_to_firs(self, odoo_invoice: Dict[str, Any]) -> Dict[str, Any]:
        """Map Odoo invoice to FIRS invoice format according to API specification."""
        # Extract basic invoice information
        invoice_number = odoo_invoice.get('name', '') or odoo_invoice.get('number', '')
        invoice_date = odoo_invoice.get('invoice_date', '') or odoo_invoice.get('date_invoice', '')
        
        # Format date if it's a datetime object or string
        if isinstance(invoice_date, datetime):
            invoice_date = invoice_date.strftime('%Y-%m-%d')
        elif isinstance(invoice_date, str) and 'T' in invoice_date:
            # Handle ISO format dates
            invoice_date = invoice_date.split('T')[0]
        
        # Format issue time
        issue_time = datetime.now().strftime('%H:%M:%S')
        if isinstance(odoo_invoice.get('create_date'), datetime):
            issue_time = odoo_invoice['create_date'].strftime('%H:%M:%S')
        
        # Generate IRN if not provided
        # IRN format: REF-HEXCODE-YYYYMMDD
        invoice_ref = invoice_number.replace('/', '').replace(' ', '').upper()
        if len(invoice_ref) > 8:
            invoice_ref = invoice_ref[:8]
        elif len(invoice_ref) < 3:
            invoice_ref = f"INV{invoice_ref}"
            
        hex_part = uuid4().hex[:8].upper()
        date_part = datetime.now().strftime('%Y%m%d')
        irn = f"{invoice_ref}-{hex_part}-{date_part}"
        
        # Get invoice type code
        odoo_type = odoo_invoice.get('type', 'out_invoice')
        invoice_type_code = "380"  # Commercial Invoice
        if odoo_type == 'out_refund':
            invoice_type_code = "381"  # Credit Note
        elif odoo_type == 'in_refund':
            invoice_type_code = "383"  # Debit Note
        
        # Get currency
        currency_code = odoo_invoice.get('currency_id', {}).get('name', 'NGN') if isinstance(odoo_invoice.get('currency_id'), dict) else odoo_invoice.get('currency', 'NGN')
        currency_code = self.get_currency_code(currency_code)
        
        # Map partners to parties
        partner_data = odoo_invoice.get('partner_id', {}) if isinstance(odoo_invoice.get('partner_id'), dict) else odoo_invoice.get('partner', {})
        company_data = odoo_invoice.get('company_id', {}) if isinstance(odoo_invoice.get('company_id'), dict) else odoo_invoice.get('company', {})
        
        # Get business ID (use company ID or generate one)
        business_id = str(company_data.get('id', uuid4()))
        
        # Process partners with proper FIRS formatting
        accounting_customer_party = self.map_partner_to_party(partner_data, is_supplier=False)
        accounting_supplier_party = self.map_partner_to_party(company_data, is_supplier=True)
        
        # Map line items
        invoice_lines = []
        lines = odoo_invoice.get('invoice_line_ids', []) or odoo_invoice.get('invoice_lines', []) or odoo_invoice.get('lines', [])
        
        for line in lines:
            mapped_line = self.map_line_item(line)
            if mapped_line:
                invoice_lines.append(mapped_line)
        
        # Calculate monetary totals
        total_line_extension = sum(float(line.get('line_extension_amount', 0)) for line in invoice_lines)
        total_tax_exclusive = total_line_extension
        total_tax_amount = sum(
            float(line.get('tax_total', {}).get('tax_amount', 0)) 
            for line in invoice_lines 
            if 'tax_total' in line
        )
        total_tax_inclusive = total_tax_exclusive + total_tax_amount
        
        # Build tax totals
        tax_totals = []
        if total_tax_amount > 0:
            tax_totals.append({
                "tax_amount": total_tax_amount,
                "tax_subtotal": [
                    {
                        "taxable_amount": total_tax_exclusive,
                        "tax_amount": total_tax_amount,
                        "tax_category": {
                            "id": "VAT",
                            "percent": (total_tax_amount / total_tax_exclusive * 100) if total_tax_exclusive > 0 else 0,
                            "tax_scheme": {
                                "id": "FIRS"
                            }
                        }
                    }
                ]
            })
        
        # Get due date
        due_date = odoo_invoice.get('invoice_date_due', '') or odoo_invoice.get('date_due', '')
        if isinstance(due_date, datetime):
            due_date = due_date.strftime('%Y-%m-%d')
        elif not due_date:
            # Default to 30 days from invoice date
            try:
                invoice_date_obj = datetime.strptime(invoice_date, '%Y-%m-%d')
                due_date = (invoice_date_obj + timedelta(days=30)).strftime('%Y-%m-%d')
            except:
                due_date = invoice_date
        
        # Build the FIRS-compliant invoice structure
        firs_invoice = {
            "business_id": business_id,
            "irn": irn,
            "issue_date": invoice_date,
            "due_date": due_date,
            "issue_time": issue_time,
            "invoice_type_code": invoice_type_code,
            "profile_id": "urn:firs.gov.ng:einvoicing:01:01",
            "payment_status": "PENDING",
            "document_currency_code": currency_code,
            "tax_currency_code": currency_code,
            "accounting_supplier_party": accounting_supplier_party,
            "accounting_customer_party": accounting_customer_party,
            "legal_monetary_total": {
                "line_extension_amount": total_line_extension,
                "tax_exclusive_amount": total_tax_exclusive,
                "tax_inclusive_amount": total_tax_inclusive,
                "payable_amount": total_tax_inclusive
            },
            "invoice_line": invoice_lines
        }
        
        # Add tax totals if applicable
        if tax_totals:
            firs_invoice["tax_total"] = tax_totals
        
        # Add payment means if available
        payment_term = odoo_invoice.get('payment_term_id', {}).get('name', '') if isinstance(odoo_invoice.get('payment_term_id'), dict) else odoo_invoice.get('payment_terms', '')
        if payment_term:
            firs_invoice["payment_terms_note"] = payment_term
            firs_invoice["payment_means"] = [{
                "payment_means_code": "30",  # Credit transfer
                "payment_due_date": due_date
            }]
        
        # Add notes if available
        notes = odoo_invoice.get('narration', '') or odoo_invoice.get('comment', '')
        if notes:
            firs_invoice["note"] = notes
        
        return firs_invoice

def test_mapper():
    """Run tests on the standalone mapper implementation."""
    logger.info("Starting mapper tests...")
    
    # Create mapper instance
    mapper = StandaloneOdooFIRSMapper()
    
    # Create mock Odoo invoice data
    odoo_invoice = {
        "id": 12345,
        "name": "INV/2023/00001",
        "invoice_date": "2023-05-01",
        "date_due": "2023-06-01",
        "type": "out_invoice",
        "currency": "NGN",
        "partner": {
            "name": "Test Customer",
            "vat": "12345678-0001",
            "email": "customer@example.com",
            "phone": "08087654321",
            "street": "456 Test Avenue",
            "city": "Abuja",
            "country_code": "NG"
        },
        "company": {
            "name": "Test Company Ltd",
            "vat": "NG87654321-0001",
            "email": "company@example.com",
            "phone": "08012345678",
            "street": "123 Company Street",
            "city": "Lagos",
            "zip": "100001",
            "country_code": "NG"
        },
        "lines": [
            {
                "id": 1,
                "name": "Product A",
                "quantity": 2,
                "price_unit": 100.0,
                "discount": 10.0,
                "tax_ids": [{"id": "vat15", "amount": 15.0}],
                "uom": "Unit"
            },
            {
                "id": 2,
                "name": "Product B",
                "quantity": 1,
                "price_unit": 50.0,
                "discount": 0.0,
                "tax_ids": [{"id": "vat0", "amount": 0.0}],
                "uom": "EA"
            }
        ],
        "payment_terms": "30 Days",
        "comment": "Test invoice for mapping validation"
    }
    
    # Test partner mapping
    logger.info("Testing partner mapping...")
    supplier_party = mapper.map_partner_to_party(odoo_invoice["company"], is_supplier=True)
    customer_party = mapper.map_partner_to_party(odoo_invoice["partner"], is_supplier=False)
    
    logger.info(f"Supplier party: {supplier_party['party_name']}, TIN: {supplier_party['tin']}")
    logger.info(f"Customer party: {customer_party['party_name']}, TIN: {customer_party['tin']}")
    
    # Test line item mapping
    logger.info("Testing line item mapping...")
    line_items = [mapper.map_line_item(line) for line in odoo_invoice["lines"]]
    for i, line in enumerate(line_items):
        logger.info(f"Line item {i+1}: {line['item']['name']}, Quantity: {line['invoiced_quantity']}, Amount: {line['line_extension_amount']}")
    
    # Test full invoice mapping
    logger.info("Testing full invoice mapping...")
    firs_invoice = mapper.map_odoo_invoice_to_firs(odoo_invoice)
    
    # Validate the output
    assert "business_id" in firs_invoice, "Business ID is missing"
    assert "irn" in firs_invoice, "IRN is missing"
    assert "issue_date" in firs_invoice, "Issue date is missing"
    assert "accounting_supplier_party" in firs_invoice, "Supplier party is missing"
    assert "accounting_customer_party" in firs_invoice, "Customer party is missing"
    assert "invoice_line" in firs_invoice, "Invoice lines are missing"
    assert "legal_monetary_total" in firs_invoice, "Monetary totals are missing"
    
    logger.info(f"Generated IRN: {firs_invoice['irn']}")
    logger.info(f"Generated invoice with {len(firs_invoice['invoice_line'])} line items")
    logger.info(f"Total amount: {firs_invoice['legal_monetary_total']['payable_amount']}")
    
    # Write the mapped invoice to a file for inspection
    output_file = "firs_invoice_example.json"
    with open(output_file, "w") as f:
        json.dump(firs_invoice, f, indent=2)
    
    logger.info(f"Mapped invoice written to {output_file}")
    
    # Print summary structure
    logger.info("Invoice structure summary:")
    for key in firs_invoice.keys():
        if isinstance(firs_invoice[key], dict):
            logger.info(f"  {key}: {{{', '.join(firs_invoice[key].keys())}}}")
        elif isinstance(firs_invoice[key], list):
            logger.info(f"  {key}: [{len(firs_invoice[key])} items]")
        else:
            logger.info(f"  {key}: {firs_invoice[key]}")
    
    return True

if __name__ == "__main__":
    if test_mapper():
        logger.info("All mapper tests PASSED! ✓")
        exit(0)
    else:
        logger.error("Mapper tests FAILED! ✗")
        exit(1)
