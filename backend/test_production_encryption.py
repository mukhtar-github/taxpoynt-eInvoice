#!/usr/bin/env python3
"""
Test script for production credential encryption implementation.

This script validates that the new encryption system works correctly
and prevents the security vulnerability of hardcoded dev keys in production.
"""

import os
import sys
import unittest
from unittest.mock import patch

# Add the app directory to path
sys.path.append('/home/mukhtar-tanimu/taxpoynt-eInvoice/backend')

from app.core.config import Settings
from app.utils.encryption_utils import ProductionEncryption, get_production_encryption


class TestProductionEncryption(unittest.TestCase):
    """Test production encryption functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.test_key = "test_encryption_key_for_testing_2024"
        self.encryptor = ProductionEncryption(self.test_key)
    
    def test_encrypt_decrypt_credential(self):
        """Test basic encrypt/decrypt functionality."""
        test_credential = "super_secret_api_key_123"
        
        # Encrypt
        encrypted = self.encryptor.encrypt_credential(test_credential)
        self.assertIsInstance(encrypted, str)
        self.assertNotEqual(encrypted, test_credential)
        
        # Decrypt
        decrypted = self.encryptor.decrypt_credential(encrypted)
        self.assertEqual(decrypted, test_credential)
    
    def test_encrypt_decrypt_dict(self):
        """Test dictionary encryption with sensitive fields."""
        test_data = {
            "username": "test_user",
            "password": "secret_password",
            "api_key": "secret_api_key",
            "normal_field": "not_encrypted"
        }
        
        # Encrypt
        encrypted_data = self.encryptor.encrypt_dict(test_data)
        
        # Check that sensitive fields are encrypted
        self.assertNotEqual(encrypted_data["password"], test_data["password"])
        self.assertNotEqual(encrypted_data["api_key"], test_data["api_key"])
        # Non-sensitive fields should remain unchanged
        self.assertEqual(encrypted_data["username"], test_data["username"])
        self.assertEqual(encrypted_data["normal_field"], test_data["normal_field"])
        
        # Decrypt
        decrypted_data = self.encryptor.decrypt_dict(encrypted_data)
        self.assertEqual(decrypted_data, test_data)
    
    def test_empty_credential_handling(self):
        """Test handling of empty/invalid credentials."""
        with self.assertRaises(ValueError):
            self.encryptor.encrypt_credential("")
            
        with self.assertRaises(ValueError):
            self.encryptor.decrypt_credential("")


class TestProductionConfig(unittest.TestCase):
    """Test production configuration security."""
    
    def test_production_env_requires_encryption_key(self):
        """Test that production environment requires encryption key."""
        with patch.dict(os.environ, {"APP_ENV": "production"}, clear=False):
            with patch.dict(os.environ, {}, clear=True):  # Clear ENCRYPTION_KEY
                settings = Settings()
                with self.assertRaises(ValueError) as context:
                    _ = settings.ENCRYPTION_KEY
                self.assertIn("ENCRYPTION_KEY environment variable is required in production", str(context.exception))
    
    def test_production_env_requires_credential_encryption_key(self):
        """Test that production environment requires credential encryption key."""
        with patch.dict(os.environ, {"APP_ENV": "production"}, clear=False):
            with patch.dict(os.environ, {}, clear=True):  # Clear both keys
                settings = Settings()
                with self.assertRaises(ValueError) as context:
                    _ = settings.CREDENTIAL_ENCRYPTION_KEY
                self.assertIn("CREDENTIAL_ENCRYPTION_KEY or ENCRYPTION_KEY environment variable is required in production", str(context.exception))
    
    def test_development_env_allows_fallback(self):
        """Test that development environment allows fallback to dev key."""
        with patch.dict(os.environ, {"APP_ENV": "development"}, clear=False):
            with patch.dict(os.environ, {}, clear=True):  # Clear encryption keys
                settings = Settings()
                # Should not raise an exception
                encryption_key = settings.ENCRYPTION_KEY
                credential_key = settings.CREDENTIAL_ENCRYPTION_KEY
                
                # Should use development fallback
                self.assertEqual(encryption_key, "development_encryption_key_please_change_in_production")
                self.assertEqual(credential_key, "development_encryption_key_please_change_in_production")
    
    def test_environment_variable_override(self):
        """Test that environment variables properly override defaults."""
        test_key = "custom_production_key_123"
        with patch.dict(os.environ, {
            "APP_ENV": "production",
            "ENCRYPTION_KEY": test_key,
            "CREDENTIAL_ENCRYPTION_KEY": test_key
        }, clear=False):
            settings = Settings()
            self.assertEqual(settings.ENCRYPTION_KEY, test_key)
            self.assertEqual(settings.CREDENTIAL_ENCRYPTION_KEY, test_key)


def test_integration():
    """Test integration between config and encryption utils."""
    print("Testing integration...")
    
    # Test with custom key
    test_key = "integration_test_key_2024"
    with patch.dict(os.environ, {
        "APP_ENV": "development",
        "ENCRYPTION_KEY": test_key
    }, clear=False):
        encryptor = get_production_encryption()
        
        test_credential = "integration_test_secret"
        encrypted = encryptor.encrypt_credential(test_credential)
        decrypted = encryptor.decrypt_credential(encrypted)
        
        assert decrypted == test_credential, "Integration test failed"
        print("✓ Integration test passed")


if __name__ == "__main__":
    print("Running production encryption tests...")
    print("=" * 50)
    
    # Run unit tests
    unittest.main(argv=[''], exit=False, verbosity=2)
    
    print("\n" + "=" * 50)
    
    # Run integration test
    test_integration()
    
    print("\n" + "=" * 50)
    print("All tests completed!")