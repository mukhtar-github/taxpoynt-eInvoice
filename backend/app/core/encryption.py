"""
Encryption utilities for secure credential storage.

This module provides encryption and decryption functions for storing
sensitive POS connection credentials securely in the database.
"""

import base64
import json
import os
from typing import Dict, Any, Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class CredentialEncryption:
    """Handles encryption and decryption of credential data."""
    
    def __init__(self, encryption_key: Optional[str] = None):
        """
        Initialize encryption handler.
        
        Args:
            encryption_key: Base64 encoded encryption key. If None, uses environment variable.
        """
        if encryption_key:
            self._key = encryption_key.encode()
        else:
            # Get encryption key from environment or generate one
            key_env = os.environ.get("CREDENTIAL_ENCRYPTION_KEY")
            if key_env:
                self._key = key_env.encode()
            else:
                # For development only - in production, this should be set in environment
                self._key = Fernet.generate_key()
        
        self._fernet = Fernet(self._key)
    
    def encrypt(self, data: Dict[str, Any]) -> str:
        """
        Encrypt credential data.
        
        Args:
            data: Dictionary containing credential data
        
        Returns:
            Base64 encoded encrypted data
        """
        try:
            # Convert to JSON string
            json_data = json.dumps(data, sort_keys=True)
            
            # Encrypt the data
            encrypted_data = self._fernet.encrypt(json_data.encode())
            
            # Return base64 encoded string
            return base64.b64encode(encrypted_data).decode()
        
        except Exception as e:
            raise ValueError(f"Failed to encrypt credentials: {str(e)}")
    
    def decrypt(self, encrypted_data: str) -> Dict[str, Any]:
        """
        Decrypt credential data.
        
        Args:
            encrypted_data: Base64 encoded encrypted data
        
        Returns:
            Dictionary containing decrypted credential data
        """
        try:
            # Decode from base64
            decoded_data = base64.b64decode(encrypted_data.encode())
            
            # Decrypt the data
            decrypted_data = self._fernet.decrypt(decoded_data)
            
            # Parse JSON
            return json.loads(decrypted_data.decode())
        
        except Exception as e:
            raise ValueError(f"Failed to decrypt credentials: {str(e)}")


# Global encryption instance
_encryption_instance = None


def get_encryption_instance() -> CredentialEncryption:
    """Get the global encryption instance."""
    global _encryption_instance
    if _encryption_instance is None:
        _encryption_instance = CredentialEncryption()
    return _encryption_instance


def encrypt_credentials(credentials: Dict[str, Any]) -> str:
    """
    Encrypt credential data using the global encryption instance.
    
    Args:
        credentials: Dictionary containing credential data
    
    Returns:
        Encrypted credential string
    """
    return get_encryption_instance().encrypt(credentials)


def decrypt_credentials(encrypted_credentials: str) -> Dict[str, Any]:
    """
    Decrypt credential data using the global encryption instance.
    
    Args:
        encrypted_credentials: Encrypted credential string
    
    Returns:
        Dictionary containing decrypted credential data
    """
    return get_encryption_instance().decrypt(encrypted_credentials)


def generate_encryption_key() -> str:
    """
    Generate a new encryption key for development/testing.
    
    Returns:
        Base64 encoded encryption key
    """
    return Fernet.generate_key().decode()


def derive_key_from_password(password: str, salt: bytes = None) -> str:
    """
    Derive an encryption key from a password using PBKDF2.
    
    Args:
        password: Password to derive key from
        salt: Salt for key derivation. If None, generates a random salt.
    
    Returns:
        Base64 encoded encryption key
    """
    if salt is None:
        salt = os.urandom(16)
    
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    return key.decode()


# Environment variable helpers
def set_encryption_key_from_env():
    """
    Set the encryption key from environment variable.
    This should be called during application startup.
    """
    global _encryption_instance
    _encryption_instance = CredentialEncryption()


def validate_encryption_setup() -> bool:
    """
    Validate that encryption is properly set up.
    
    Returns:
        True if encryption is working, False otherwise
    """
    try:
        # Test encryption/decryption with sample data
        test_data = {"test": "credential", "api_key": "sample_key"}
        
        encrypted = encrypt_credentials(test_data)
        decrypted = decrypt_credentials(encrypted)
        
        return decrypted == test_data
    
    except Exception:
        return False