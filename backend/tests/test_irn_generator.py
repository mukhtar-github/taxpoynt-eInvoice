"""
Test suite for the FIRS IRN generator implementation.

This module tests the IRN generation algorithm according to FIRS specifications.
"""

import unittest
import json
import sys
import os
from datetime import datetime
from uuid import uuid4

# Add the parent directory to sys.path to make imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.utils.irn_generator import (
    extract_key_invoice_fields,
    calculate_invoice_hash,
    generate_verification_code,
    generate_service_id,
    format_invoice_number,
    generate_firs_irn,
    verify_irn,
    generate_irn_for_ubl_invoice,
    # Include validation functions from irn_generator instead of irn.py
    validate_invoice_number,
    validate_service_id,
    validate_timestamp
)


class TestIRNGenerator(unittest.TestCase):
    """Test cases for the IRN generator functions."""
    
    def setUp(self):
        """Set up test data."""
        # Sample invoice data
        self.invoice_data = {
            'invoice_number': 'INV2025001',
            'invoice_date': '2025-05-16',
            'seller_tax_id': 'NG123456789',
            'buyer_tax_id': 'NG987654321',
            'total_amount': 1500.0,
            'currency_code': 'NGN',
        }
        
        # Sample UBL invoice data (simplified for testing)
        self.ubl_invoice_data = {
            'ID': 'UBL2025001',
            'IssueDate': '2025-05-16',
            'DocumentCurrencyCode': 'NGN',
            'AccountingSupplierParty': {
                'PartyTaxScheme': {
                    'CompanyID': 'NG123456789'
                }
            },
            'AccountingCustomerParty': {
                'PartyTaxScheme': {
                    'CompanyID': 'NG987654321'
                }
            },
            'LegalMonetaryTotal': {
                'PayableAmount': 1500.0
            }
        }
    
    def test_extract_key_invoice_fields(self):
        """Test extracting key fields from invoice data."""
        result = extract_key_invoice_fields(self.invoice_data)
        
        self.assertEqual(result['invoice_number'], 'INV2025001')
        self.assertEqual(result['invoice_date'], '2025-05-16')
        self.assertEqual(result['seller_tax_id'], 'NG123456789')
        self.assertEqual(result['buyer_tax_id'], 'NG987654321')
        self.assertEqual(result['total_amount'], '1500.0')
        self.assertEqual(result['currency_code'], 'NGN')
    
    def test_calculate_invoice_hash(self):
        """Test hash calculation for invoice data."""
        unique_id = str(uuid4())
        hash_value = calculate_invoice_hash(self.invoice_data, unique_id)
        
        # Verify hash is a 64-character hex string (SHA-256)
        self.assertEqual(len(hash_value), 64)
        self.assertTrue(all(c in '0123456789abcdef' for c in hash_value))
        
        # Verify hash is deterministic for same input
        hash_value2 = calculate_invoice_hash(self.invoice_data, unique_id)
        self.assertEqual(hash_value, hash_value2)
        
        # Verify hash changes when input changes
        modified_data = self.invoice_data.copy()
        modified_data['total_amount'] = 2000.0
        hash_value3 = calculate_invoice_hash(modified_data, unique_id)
        self.assertNotEqual(hash_value, hash_value3)
    
    def test_generate_verification_code(self):
        """Test generation of verification code."""
        hash_value = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
        verification_code = generate_verification_code(hash_value)
        
        # Verify verification code is 12 characters
        self.assertEqual(len(verification_code), 12)
        
        # Verify verification code is deterministic for same input
        verification_code2 = generate_verification_code(hash_value)
        self.assertEqual(verification_code, verification_code2)
        
        # Verify verification code changes when input changes
        verification_code3 = generate_verification_code("different_hash_value")
        self.assertNotEqual(verification_code, verification_code3)
    
    def test_generate_service_id(self):
        """Test generation of service ID."""
        service_id = generate_service_id()
        
        # Verify service ID is 8 characters
        self.assertEqual(len(service_id), 8)
        
        # Verify service ID is alphanumeric
        self.assertTrue(service_id.isalnum())
        
        # Verify service ID is unique
        service_id2 = generate_service_id()
        self.assertNotEqual(service_id, service_id2)
    
    def test_format_invoice_number(self):
        """Test formatting of invoice number."""
        # Test valid invoice number
        self.assertEqual(format_invoice_number("INV2025001"), "INV2025001")
        
        # Test invoice number with special characters
        self.assertEqual(format_invoice_number("INV-2025/001"), "INV2025001")
        
        # Test empty invoice number
        formatted = format_invoice_number("")
        self.assertTrue(formatted.startswith("INV"))
        self.assertEqual(len(formatted), 17)  # "INV" + YYYYMMDDHHMMSS
        
        # Test long invoice number
        long_invoice_number = "A" * 100
        formatted = format_invoice_number(long_invoice_number)
        self.assertEqual(len(formatted), 50)
    
    def test_generate_firs_irn(self):
        """Test generation of FIRS IRN."""
        # Generate IRN with automatic service ID and timestamp
        result = generate_firs_irn(self.invoice_data)
        
        # Verify result contains all expected components
        self.assertIn("irn", result)
        self.assertIn("invoice_number", result)
        self.assertIn("service_id", result)
        self.assertIn("timestamp", result)
        self.assertIn("unique_id", result)
        self.assertIn("hash_value", result)
        self.assertIn("verification_code", result)
        
        # Verify IRN format: InvoiceNumber-ServiceID-YYYYMMDD
        irn = result["irn"]
        parts = irn.split("-")
        self.assertEqual(len(parts), 3)
        self.assertEqual(parts[0], "INV2025001")
        self.assertEqual(len(parts[1]), 8)
        self.assertEqual(len(parts[2]), 8)
        
        # Verify provided service ID and timestamp are used
        service_id = "TESTSIDD"
        timestamp = "20250516"
        result2 = generate_firs_irn(self.invoice_data, service_id, timestamp)
        self.assertEqual(result2["irn"], f"INV2025001-{service_id}-{timestamp}")
    
    def test_verify_irn(self):
        """Test verification of IRN."""
        # Generate an IRN
        result = generate_firs_irn(self.invoice_data)
        irn = result["irn"]
        
        # Verify with matching invoice data
        is_valid, message = verify_irn(irn, self.invoice_data)
        self.assertTrue(is_valid)
        self.assertEqual(message, "IRN verification successful")
        
        # Verify with mismatched invoice data
        modified_data = self.invoice_data.copy()
        modified_data["invoice_number"] = "DIFFERENT001"
        is_valid, message = verify_irn(irn, modified_data)
        self.assertFalse(is_valid)
        self.assertIn("Invoice number does not match", message)
        
        # Verify with invalid IRN format
        is_valid, message = verify_irn("invalid-irn", self.invoice_data)
        self.assertFalse(is_valid)
        self.assertIn("Invalid IRN format", message)
    
    def test_generate_irn_for_ubl_invoice(self):
        """Test generation of IRN from UBL invoice data."""
        # Generate IRN from UBL invoice data
        result = generate_irn_for_ubl_invoice(self.ubl_invoice_data)
        
        # Verify result contains all expected components
        self.assertIn("irn", result)
        self.assertIn("invoice_number", result)
        self.assertIn("service_id", result)
        self.assertIn("timestamp", result)
        self.assertIn("unique_id", result)
        self.assertIn("hash_value", result)
        self.assertIn("verification_code", result)
        
        # Verify IRN format: InvoiceNumber-ServiceID-YYYYMMDD
        irn = result["irn"]
        parts = irn.split("-")
        self.assertEqual(len(parts), 3)
        self.assertEqual(parts[0], "UBL2025001")
        self.assertEqual(len(parts[1]), 8)
        self.assertEqual(len(parts[2]), 8)
        
        # Verify with specified service ID
        service_id = "UBLSVCID"
        result2 = generate_irn_for_ubl_invoice(self.ubl_invoice_data, service_id)
        self.assertEqual(result2["service_id"], service_id)


if __name__ == "__main__":
    unittest.main()
