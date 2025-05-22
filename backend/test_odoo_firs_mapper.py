#!/usr/bin/env python3
"""
Test script for OdooFIRSMapper functionality.

This script tests the mapping functionality from Odoo data format to FIRS-compliant
format according to BIS Billing 3.0 standard. It validates the correctness of the
mapper implementation without requiring the full API integration.
"""

import os
import sys
import json
import logging
from pprint import pprint
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger("mapper_test")

# Import the mapper
from app.utils.odoo_firs_mapper import OdooFIRSMapper

def test_partner_mapping():
    """Test partner to party mapping functionality."""
    logger.info("Testing partner to party mapping...")
    
    # Create a test mapper instance
    mapper = OdooFIRSMapper()
    
    # Test supplier data
    supplier_data = {
        "name": "Test Supplier Ltd",
        "vat": "NG31569955-0001",
        "email": "supplier@example.com",
        "phone": "08012345678",
        "street": "123 Test Street",
        "street2": "Floor 2",
        "city": "Lagos",
        "state": "Lagos",
        "zip": "100001",
        "country_code": "NG"
    }
    
    # Test customer data with missing fields
    customer_data = {
        "name": "Test Customer",
        "vat": "12345678-0001",
        # Missing email
        "phone": "08087654321",
        "street": "456 Test Avenue",
        "city": "Abuja",
        # Missing zip
        "country_code": "NG"
    }
    
    # Map supplier data
    supplier_party = mapper.map_partner_to_party(supplier_data, is_supplier=True)
    
    # Map customer data
    customer_party = mapper.map_partner_to_party(customer_data, is_supplier=False)
    
    # Validate supplier mapping
    assert supplier_party["party_name"] == "Test Supplier Ltd", "Supplier name mapping failed"
    assert supplier_party["tin"] == "31569955-0001", "Supplier TIN mapping failed"
    assert supplier_party["email"] == "supplier@example.com", "Supplier email mapping failed"
    assert supplier_party["postal_address"]["street_name"] == "123 Test Street", "Supplier street mapping failed"
    
    # Validate customer mapping and placeholder handling
    assert customer_party["party_name"] == "Test Customer", "Customer name mapping failed"
    assert customer_party["tin"] == "12345678-0001", "Customer TIN mapping failed"
    assert customer_party["email"].endswith("@taxpoynt.example.com"), "Customer missing email should have placeholder"
    assert customer_party["postal_address"]["street_name"] == "456 Test Avenue", "Customer street mapping failed"
    
    logger.info("Partner mapping tests passed ✓")
    return True

def test_line_item_mapping():
    """Test invoice line item mapping functionality."""
    logger.info("Testing line item mapping...")
    
    # Create a test mapper instance
    mapper = OdooFIRSMapper()
    
    # Test line item with tax
    line_with_tax = {
        "id": 1,
        "name": "Test Product with VAT",
        "quantity": 2,
        "price_unit": 100.0,
        "discount": 10.0,
        "tax_ids": [{"id": "vat15", "amount": 15.0}],
        "uom": "Unit"
    }
    
    # Test line item without tax (zero-rated)
    line_without_tax = {
        "id": 2,
        "name": "Test Product without VAT",
        "quantity": 1,
        "price_unit": 50.0,
        "discount": 0.0,
        "tax_ids": [{"id": "vat0", "amount": 0.0}],
        "uom": "EA"
    }
    
    # Map line items
    mapped_line_with_tax = mapper.map_line_item(line_with_tax)
    mapped_line_without_tax = mapper.map_line_item(line_without_tax)
    
    # Validate taxed line item
    assert mapped_line_with_tax["id"] == "LINE-1", "Line ID mapping failed"
    assert mapped_line_with_tax["invoiced_quantity"] == 2, "Line quantity mapping failed"
    assert mapped_line_with_tax["price"]["price_amount"] == 100.0, "Line price mapping failed"
    assert "tax_total" in mapped_line_with_tax, "Line with tax should have tax_total field"
    assert mapped_line_with_tax["tax_total"]["tax_subtotal"]["tax_category"]["percent"] == 15.0, "Line tax rate mapping failed"
    
    # Validate zero-rated line item
    assert mapped_line_without_tax["id"] == "LINE-2", "Line ID mapping failed"
    assert mapped_line_without_tax["invoiced_quantity"] == 1, "Line quantity mapping failed"
    assert mapped_line_without_tax["item"]["name"] == "Test Product without VAT", "Line name mapping failed"
    
    logger.info("Line item mapping tests passed ✓")
    return True

def test_full_invoice_mapping():
    """Test full Odoo invoice to FIRS invoice mapping."""
    logger.info("Testing full invoice mapping...")
    
    # Create a test mapper instance
    mapper = OdooFIRSMapper()
    
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
    
    # Map the invoice
    firs_invoice = mapper.map_odoo_invoice_to_firs(odoo_invoice)
    
    # Validate basic invoice data
    assert firs_invoice["business_id"], "Business ID should be generated"
    assert firs_invoice["irn"], "IRN should be generated"
    assert firs_invoice["issue_date"] == "2023-05-01", "Issue date mapping failed"
    assert firs_invoice["due_date"] == "2023-06-01", "Due date mapping failed"
    assert firs_invoice["document_currency_code"] == "NGN", "Currency mapping failed"
    
    # Validate parties
    assert firs_invoice["accounting_supplier_party"]["party_name"] == "Test Company Ltd", "Supplier mapping failed"
    assert firs_invoice["accounting_customer_party"]["party_name"] == "Test Customer", "Customer mapping failed"
    
    # Validate line items
    assert len(firs_invoice["invoice_line"]) == 2, "Line items count mismatch"
    
    # Validate monetary totals
    assert "legal_monetary_total" in firs_invoice, "Legal monetary total missing"
    assert firs_invoice["legal_monetary_total"]["payable_amount"] > 0, "Payable amount should be positive"
    
    # Validate payment info
    assert "payment_terms_note" in firs_invoice, "Payment terms missing"
    assert firs_invoice["payment_terms_note"] == "30 Days", "Payment terms mapping failed"
    
    # Print the mapped invoice for inspection
    logger.info("FIRS Invoice structure:")
    print(json.dumps(firs_invoice, indent=2))
    
    logger.info("Full invoice mapping tests passed ✓")
    return True

if __name__ == "__main__":
    logger.info("Starting OdooFIRSMapper tests...")
    
    # Run all tests
    tests_passed = all([
        test_partner_mapping(),
        test_line_item_mapping(),
        test_full_invoice_mapping()
    ])
    
    if tests_passed:
        logger.info("All mapper tests PASSED! ✓")
        sys.exit(0)
    else:
        logger.error("Some mapper tests FAILED! ✗")
        sys.exit(1)
