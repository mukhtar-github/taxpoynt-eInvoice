"""Unit tests for encryption utilities."""

import json
import base64
import unittest
from typing import Dict, Any

from app.utils.encryption import (
    encrypt_with_gcm,
    decrypt_with_gcm,
    generate_secret_key,
    encrypt_field,
    decrypt_field,
    encrypt_dict_fields,
    decrypt_dict_fields
)


class TestEncryptionUtils(unittest.TestCase):
    """Test encryption utilities."""
    
    def setUp(self):
        """Set up test data."""
        self.test_key = generate_secret_key()
        self.test_string = "sensitive data to be encrypted"
        self.test_dict = {"name": "test", "secret": "confidential"}
        self.test_nested_dict = {
            "api_config": {
                "url": "https://api.example.com",
                "api_key": "super_secret_key",
                "timeout": 30
            },
            "database": {
                "host": "db.example.com",
                "password": "db_password"
            }
        }
        self.sensitive_fields = ["api_key", "password"]
    
    def test_gcm_encryption_decryption(self):
        """Test AES-GCM encryption and decryption."""
        encrypted = encrypt_with_gcm(self.test_string, self.test_key)
        
        # Check that encrypted value is different from original
        self.assertNotEqual(encrypted, self.test_string)
        
        # Check that we can decrypt back to original
        decrypted = decrypt_with_gcm(encrypted, self.test_key)
        self.assertEqual(decrypted, self.test_string)
    
    def test_dict_encryption_decryption(self):
        """Test dict encryption and decryption."""
        encrypted = encrypt_with_gcm(self.test_dict, self.test_key)
        
        # Check that encrypted value is different from original
        self.assertNotEqual(encrypted, self.test_dict)
        
        # Check that we can decrypt back to original
        decrypted = decrypt_with_gcm(encrypted, self.test_key, as_dict=True)
        self.assertEqual(decrypted, self.test_dict)
    
    def test_field_encryption(self):
        """Test field encryption and decryption."""
        encrypted = encrypt_field(self.test_string, self.test_key)
        
        # Check that encrypted value is different from original
        self.assertNotEqual(encrypted, self.test_string)
        
        # Check that we can decrypt back to original
        decrypted = decrypt_field(encrypted, self.test_key)
        self.assertEqual(decrypted, self.test_string)
    
    def test_dict_fields_encryption(self):
        """Test encryption of specific fields in a dictionary."""
        encrypted_dict = encrypt_dict_fields(self.test_nested_dict, self.sensitive_fields, self.test_key)
        
        # Original dictionary should not be modified
        self.assertEqual(self.test_nested_dict["api_config"]["api_key"], "super_secret_key")
        self.assertEqual(self.test_nested_dict["database"]["password"], "db_password")
        
        # Sensitive fields should be encrypted
        self.assertNotEqual(encrypted_dict["api_config"]["api_key"], "super_secret_key")
        self.assertNotEqual(encrypted_dict["database"]["password"], "db_password")
        
        # Non-sensitive fields should remain unchanged
        self.assertEqual(encrypted_dict["api_config"]["url"], "https://api.example.com")
        self.assertEqual(encrypted_dict["api_config"]["timeout"], 30)
        self.assertEqual(encrypted_dict["database"]["host"], "db.example.com")
        
        # Decrypt and verify
        decrypted_dict = decrypt_dict_fields(encrypted_dict, self.sensitive_fields, self.test_key)
        self.assertEqual(decrypted_dict, self.test_nested_dict)
    
    def test_none_values(self):
        """Test handling of None values."""
        # Encryption should return None for None input
        self.assertIsNone(encrypt_with_gcm(None, self.test_key))
        self.assertIsNone(encrypt_field(None, self.test_key))
        
        # Decryption should return None for None input
        self.assertIsNone(decrypt_with_gcm(None, self.test_key))
        self.assertIsNone(decrypt_field(None, self.test_key))
    
    def test_different_key_fails(self):
        """Test that decryption with wrong key fails."""
        encrypted = encrypt_with_gcm(self.test_string, self.test_key)
        different_key = generate_secret_key()
        
        # Decryption with different key should fail
        with self.assertRaises(Exception):
            decrypt_with_gcm(encrypted, different_key)


if __name__ == "__main__":
    unittest.main() 