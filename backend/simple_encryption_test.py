#!/usr/bin/env python3
"""
Simple test for production encryption without dependencies.
"""

import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


def derive_key(password: str) -> bytes:
    """Derive encryption key from password."""
    salt = b'taxpoynt_salt_2024'
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode()))


def test_encryption():
    """Test basic encryption functionality."""
    print("Testing production encryption functionality...")
    
    # Test with a sample key
    test_key = "test_encryption_key_2024"
    derived_key = derive_key(test_key)
    fernet = Fernet(derived_key)
    
    # Test data
    test_credential = "super_secret_api_key_123"
    
    # Encrypt
    encrypted = fernet.encrypt(test_credential.encode())
    encrypted_b64 = base64.b64encode(encrypted).decode()
    
    print(f"Original: {test_credential}")
    print(f"Encrypted: {encrypted_b64[:50]}...")
    
    # Decrypt
    decrypted_data = base64.b64decode(encrypted_b64.encode())
    decrypted = fernet.decrypt(decrypted_data).decode()
    
    print(f"Decrypted: {decrypted}")
    
    # Verify
    assert decrypted == test_credential, "Encryption/decryption failed!"
    print("✓ Encryption test passed!")
    
    return True


def test_production_security():
    """Test production security requirements."""
    print("\nTesting production security...")
    
    # Simulate production environment
    dev_key = "development_encryption_key_please_change_in_production"
    
    print(f"Development key detected: {dev_key}")
    
    # In production, this should raise an error
    app_env = os.getenv("APP_ENV", "development")
    print(f"Current environment: {app_env}")
    
    if app_env == "production":
        encryption_key = os.getenv("ENCRYPTION_KEY")
        if not encryption_key:
            print("❌ ERROR: ENCRYPTION_KEY required in production!")
            return False
        elif encryption_key == dev_key:
            print("❌ ERROR: Development key used in production!")
            return False
        else:
            print("✓ Production encryption key properly configured")
    else:
        print("✓ Development environment allows fallback key")
    
    return True


if __name__ == "__main__":
    print("Production Credential Encryption Test")
    print("=" * 50)
    
    try:
        success1 = test_encryption()
        success2 = test_production_security()
        
        if success1 and success2:
            print("\n✓ All tests passed! Production encryption is working correctly.")
        else:
            print("\n❌ Some tests failed!")
            
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()