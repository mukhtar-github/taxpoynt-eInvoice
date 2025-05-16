"""
Test suite for cryptographic signing and CSID implementation.

This module tests the comprehensive CSID (Cryptographic Stamp ID) implementation
for the FIRS e-Invoice system, including key management, signing, and verification.
"""

import unittest
import sys
import os
import json
import tempfile
import shutil
from datetime import datetime
from uuid import uuid4

# Add the parent directory to sys.path to make imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.utils.crypto_signing import (
    CSIDGenerator, 
    sign_invoice, 
    verify_csid,
    SigningAlgorithm,
    CSIDVersion,
    csid_generator
)

from app.utils.key_management import KeyManager


class TestCryptoSigning(unittest.TestCase):
    """Test cases for the cryptographic signing implementation."""
    
    def setUp(self):
        """Set up test data and temporary directory for keys."""
        # Create a temporary directory for test keys
        self.temp_dir = tempfile.mkdtemp()
        
        # Initialize key manager with temporary directory
        self.key_manager = KeyManager(keys_dir=self.temp_dir)
        
        # Generate test keys
        self.private_key_path, self.public_key_path = self.key_manager.generate_key_pair(
            key_type="signing",
            algorithm="rsa-2048",
            key_name="test_signing_key"
        )
        
        # Initialize CSID generator with test keys
        self.csid_gen = CSIDGenerator(private_key_path=self.private_key_path)
        
        # Sample invoice data
        self.invoice_data = {
            'invoice_number': 'INV2025001',
            'invoice_date': '2025-05-16',
            'seller_tax_id': 'NG123456789',
            'buyer_tax_id': 'NG987654321',
            'total_amount': 1500.0,
            'currency_code': 'NGN',
            'items': [
                {
                    'description': 'Product A',
                    'quantity': 2,
                    'unit_price': 500.0,
                    'amount': 1000.0,
                    'tax_rate': 7.5
                },
                {
                    'description': 'Service B',
                    'quantity': 1,
                    'unit_price': 500.0,
                    'amount': 500.0,
                    'tax_rate': 7.5
                }
            ],
            'total_tax': 112.5,
            'status': 'issued'
        }
    
    def tearDown(self):
        """Clean up temporary directory after tests."""
        shutil.rmtree(self.temp_dir)
    
    def test_key_generation(self):
        """Test generation of cryptographic keys."""
        # Verify key files exist
        self.assertTrue(os.path.exists(self.private_key_path))
        self.assertTrue(os.path.exists(self.public_key_path))
        
        # Test loading keys
        private_key = self.key_manager.load_private_key(self.private_key_path)
        public_key = self.key_manager.load_public_key(self.public_key_path)
        
        self.assertIsNotNone(private_key)
        self.assertIsNotNone(public_key)
    
    def test_csid_generation_v1(self):
        """Test generation of CSID v1.0."""
        # Generate CSIDv1
        csid = self.csid_gen.generate_csid(
            self.invoice_data,
            algorithm=SigningAlgorithm.RSA_PSS_SHA256,
            version=CSIDVersion.V1_0
        )
        
        # Verify CSID structure
        csid_data = json.loads(json.loads(json.dumps(csid_data := {"csid": csid}))["csid"])
        csid_data = json.loads(json.loads(json.dumps(csid_data))["csid"])
        
        # Decode CSID
        decoded_csid = json.loads(json.loads(json.dumps({"decoded": csid_data}))["decoded"])
        
        self.assertIn("csid", decoded_csid)
        self.assertIn("timestamp", decoded_csid)
        self.assertIn("algorithm", decoded_csid)
        self.assertEqual(decoded_csid["algorithm"], SigningAlgorithm.RSA_PSS_SHA256.value)
    
    def test_csid_generation_v2(self):
        """Test generation of CSID v2.0."""
        # Generate CSIDv2
        csid = self.csid_gen.generate_csid(
            self.invoice_data,
            algorithm=SigningAlgorithm.RSA_PSS_SHA256,
            version=CSIDVersion.V2_0
        )
        
        # Verify CSID format
        csid_data = json.loads(json.loads(json.dumps(csid_data := {"csid": csid}))["csid"])
        csid_data = json.loads(json.loads(json.dumps(csid_data))["csid"])
        
        # Decode CSID
        decoded_csid = json.loads(json.loads(json.dumps({"decoded": csid_data}))["decoded"])
        
        self.assertEqual(decoded_csid["version"], CSIDVersion.V2_0.value)
        self.assertIn("signature_value", decoded_csid)
        self.assertIn("signature_id", decoded_csid)
        self.assertIn("timestamp", decoded_csid)
        self.assertIn("algorithm", decoded_csid)
        self.assertIn("key_info", decoded_csid)
        self.assertIn("invoice_ref", decoded_csid)
    
    def test_sign_invoice(self):
        """Test signing an invoice with CSID."""
        # Sign the invoice
        signed_invoice = sign_invoice(
            self.invoice_data,
            version=CSIDVersion.V2_0,
            algorithm=SigningAlgorithm.RSA_PSS_SHA256
        )
        
        # Verify signed invoice structure
        self.assertIn("cryptographic_stamp", signed_invoice)
        crypto_stamp = signed_invoice["cryptographic_stamp"]
        
        self.assertIn("csid", crypto_stamp)
        self.assertIn("timestamp", crypto_stamp)
        self.assertIn("algorithm", crypto_stamp)
        self.assertIn("version", crypto_stamp)
        self.assertIn("signature_id", crypto_stamp)
        self.assertIn("key_info", crypto_stamp)
    
    def test_verify_csid(self):
        """Test verification of CSID."""
        # Sign the invoice
        signed_invoice = sign_invoice(self.invoice_data)
        csid = signed_invoice["cryptographic_stamp"]["csid"]
        
        # Verify the CSID
        result, message, details = verify_csid(
            self.invoice_data,
            csid,
            self.public_key_path
        )
        
        # Check verification result
        self.assertTrue(result)
        self.assertEqual(message, "CSID verification successful")
        self.assertIn("algorithm", details)
        self.assertIn("timestamp", details)
        self.assertIn("version", details)
    
    def test_tampered_invoice_detection(self):
        """Test detection of tampered invoice data."""
        # Sign the invoice
        signed_invoice = sign_invoice(self.invoice_data)
        csid = signed_invoice["cryptographic_stamp"]["csid"]
        
        # Tamper with the invoice data
        tampered_invoice = self.invoice_data.copy()
        tampered_invoice["total_amount"] = 2000.0  # Change total amount
        
        # Verify the CSID against tampered data
        result, message, details = verify_csid(
            tampered_invoice,
            csid,
            self.public_key_path
        )
        
        # Check verification result
        self.assertFalse(result)
        self.assertNotEqual(message, "CSID verification successful")


if __name__ == "__main__":
    unittest.main()
