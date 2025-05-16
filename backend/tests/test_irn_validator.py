"""
Test suite for IRN validation functions.

This module tests the comprehensive validation functionality for IRNs,
including format compliance, hash verification, and validation against
invoice data with various scenarios.
"""

import unittest
import sys
import os
import json
from datetime import datetime, timedelta
from uuid import uuid4

# Add the parent directory to sys.path to make imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.utils.irn_generator import (
    generate_firs_irn,
    calculate_invoice_hash,
    generate_verification_code
)

from app.utils.irn_validator import (
    validate_irn_format,
    validate_irn_against_invoice,
    verify_irn_integrity,
    run_irn_validation_test,
    generate_validation_report
)


class TestIRNValidator(unittest.TestCase):
    """Test cases for the IRN validation functions."""
    
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
        
        # Generate a valid IRN and associated data
        irn_result = generate_firs_irn(self.invoice_data)
        self.valid_irn = irn_result['irn']
        self.hash_value = irn_result['hash_value']
        self.verification_code = irn_result['verification_code']
        self.unique_id = irn_result['unique_id']
        
        # Add unique_id to invoice data for hash verification
        self.complete_invoice_data = self.invoice_data.copy()
        self.complete_invoice_data['unique_id'] = self.unique_id
    
    def test_validate_irn_format(self):
        """Test validation of IRN format."""
        # Test with valid IRN
        is_valid, message = validate_irn_format(self.valid_irn)
        self.assertTrue(is_valid)
        
        # Test with invalid format - wrong separator
        is_valid, message = validate_irn_format("INV2025001_12345678_20250516")
        self.assertFalse(is_valid)
        
        # Test with invalid format - missing component
        is_valid, message = validate_irn_format("INV2025001-12345678")
        self.assertFalse(is_valid)
        
        # Test with invalid format - wrong timestamp
        is_valid, message = validate_irn_format("INV2025001-12345678-2025-05-16")
        self.assertFalse(is_valid)
        
        # Test with empty IRN
        is_valid, message = validate_irn_format("")
        self.assertFalse(is_valid)
    
    def test_validate_irn_against_invoice(self):
        """Test validation of IRN against invoice data."""
        # Test with valid data
        is_valid, message, details = validate_irn_against_invoice(
            self.valid_irn,
            self.invoice_data,
            verify_hash=False  # Not verifying hash for basic test
        )
        self.assertTrue(is_valid)
        
        # Test with mismatched invoice number
        modified_data = self.invoice_data.copy()
        modified_data['invoice_number'] = 'DIFFERENT001'
        is_valid, message, details = validate_irn_against_invoice(
            self.valid_irn,
            modified_data,
            verify_hash=False
        )
        self.assertFalse(is_valid)
        
        # Test with hash verification
        is_valid, message, details = validate_irn_against_invoice(
            self.valid_irn,
            self.complete_invoice_data,
            verify_hash=True,
            stored_hash=self.hash_value,
            stored_verification_code=self.verification_code
        )
        self.assertTrue(is_valid)
        
        # Test with invalid hash
        is_valid, message, details = validate_irn_against_invoice(
            self.valid_irn,
            self.complete_invoice_data,
            verify_hash=True,
            stored_hash="invalidhash",
            stored_verification_code=self.verification_code
        )
        self.assertFalse(is_valid)
    
    def test_verify_irn_integrity(self):
        """Test verification of IRN integrity."""
        # Test with valid data
        is_valid, message = verify_irn_integrity(
            self.valid_irn,
            self.verification_code,
            self.hash_value,
            self.complete_invoice_data
        )
        self.assertTrue(is_valid)
        
        # Test with invalid verification code
        is_valid, message = verify_irn_integrity(
            self.valid_irn,
            "invalidcode",
            self.hash_value,
            self.complete_invoice_data
        )
        self.assertFalse(is_valid)
        
        # Test with invalid hash
        is_valid, message = verify_irn_integrity(
            self.valid_irn,
            self.verification_code,
            "invalidhash",
            self.complete_invoice_data
        )
        self.assertFalse(is_valid)
        
        # Test with invalid IRN
        is_valid, message = verify_irn_integrity(
            "invalid-irn-format",
            self.verification_code,
            self.hash_value,
            self.complete_invoice_data
        )
        self.assertFalse(is_valid)
    
    def test_run_irn_validation_test(self):
        """Test running validation tests with various scenarios."""
        # Create test cases
        test_cases = [
            {
                'scenario': 'Valid IRN with matching data',
                'irn': self.valid_irn,
                'invoice_data': self.invoice_data,
                'verify_hash': False,
                'expected_result': True
            },
            {
                'scenario': 'Valid IRN with mismatched invoice number',
                'irn': self.valid_irn,
                'invoice_data': {'invoice_number': 'DIFFERENT001'},
                'verify_hash': False,
                'expected_result': False
            },
            {
                'scenario': 'Invalid IRN format',
                'irn': "invalid-format",
                'invoice_data': self.invoice_data,
                'verify_hash': False,
                'expected_result': False
            },
            {
                'scenario': 'Valid IRN with hash verification',
                'irn': self.valid_irn,
                'invoice_data': self.complete_invoice_data,
                'verify_hash': True,
                'stored_hash': self.hash_value,
                'stored_verification_code': self.verification_code,
                'expected_result': True
            }
        ]
        
        # Run test cases
        results = run_irn_validation_test(test_cases)
        
        # Verify results
        self.assertEqual(len(results), 4)
        self.assertTrue(results[0]['test_passed'])
        self.assertTrue(results[1]['test_passed'])
        self.assertTrue(results[2]['test_passed'])
        self.assertTrue(results[3]['test_passed'])
    
    def test_generate_validation_report(self):
        """Test generation of validation report."""
        # Test with valid data
        report = generate_validation_report(
            self.valid_irn,
            self.complete_invoice_data,
            self.hash_value,
            self.verification_code
        )
        
        self.assertEqual(report['overall_result'], 'VALID')
        self.assertTrue(report['validations']['format']['is_valid'])
        self.assertTrue(report['validations']['components']['is_valid'])
        self.assertTrue(report['validations']['invoice_match']['is_valid'])
        self.assertTrue(report['validations']['integrity']['is_valid'])
        
        # Test with invalid IRN
        report = generate_validation_report(
            "invalid-irn",
            self.complete_invoice_data,
            self.hash_value,
            self.verification_code
        )
        
        self.assertEqual(report['overall_result'], 'INVALID')
        self.assertFalse(report['validations']['format']['is_valid'])


if __name__ == "__main__":
    unittest.main()
