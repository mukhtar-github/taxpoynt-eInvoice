"""
Production-grade encryption utilities for credential management.

This module provides secure encryption/decryption functions for sensitive 
credentials and API keys in production environments.
"""

import os
import base64
import logging
from typing import Union, Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)


class ProductionEncryption:
    """Production-grade encryption utility using Fernet symmetric encryption."""
    
    def __init__(self, encryption_key: Optional[str] = None):
        """
        Initialize encryption utility.
        
        Args:
            encryption_key: Base encryption key (will be strengthened with PBKDF2)
        """
        self.encryption_key = encryption_key
        self._fernet = None
        
    def _get_fernet(self) -> Fernet:
        """Get or create Fernet cipher instance."""
        if self._fernet is None:
            if not self.encryption_key:
                raise ValueError("Encryption key not provided")
                
            # Use PBKDF2 to derive a proper key from the provided encryption key
            salt = b'taxpoynt_salt_2024'  # Fixed salt for consistency
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(self.encryption_key.encode()))
            self._fernet = Fernet(key)
            
        return self._fernet
    
    def encrypt_credential(self, credential: str) -> str:
        """
        Encrypt a credential string.
        
        Args:
            credential: Plain text credential to encrypt
            
        Returns:
            Base64 encoded encrypted credential
        """
        if not credential:
            raise ValueError("Credential cannot be empty")
            
        try:
            fernet = self._get_fernet()
            encrypted_data = fernet.encrypt(credential.encode())
            return base64.b64encode(encrypted_data).decode()
        except Exception as e:
            logger.error(f"Failed to encrypt credential: {str(e)}")
            raise ValueError(f"Encryption failed: {str(e)}")
    
    def decrypt_credential(self, encrypted_credential: str) -> str:
        """
        Decrypt an encrypted credential.
        
        Args:
            encrypted_credential: Base64 encoded encrypted credential
            
        Returns:
            Decrypted plain text credential
        """
        if not encrypted_credential:
            raise ValueError("Encrypted credential cannot be empty")
            
        try:
            fernet = self._get_fernet()
            encrypted_data = base64.b64decode(encrypted_credential.encode())
            decrypted_data = fernet.decrypt(encrypted_data)
            return decrypted_data.decode()
        except Exception as e:
            logger.error(f"Failed to decrypt credential: {str(e)}")
            raise ValueError(f"Decryption failed: {str(e)}")
    
    def encrypt_dict(self, data: dict) -> dict:
        """
        Encrypt sensitive fields in a dictionary.
        
        Args:
            data: Dictionary with potentially sensitive data
            
        Returns:
            Dictionary with encrypted sensitive fields
        """
        sensitive_fields = {
            'password', 'secret', 'key', 'token', 'api_key', 
            'client_secret', 'private_key', 'credential'
        }
        
        encrypted_data = data.copy()
        
        for field, value in data.items():
            if any(sensitive in field.lower() for sensitive in sensitive_fields):
                if isinstance(value, str) and value:
                    encrypted_data[field] = self.encrypt_credential(value)
                    
        return encrypted_data
    
    def decrypt_dict(self, encrypted_data: dict) -> dict:
        """
        Decrypt sensitive fields in a dictionary.
        
        Args:
            encrypted_data: Dictionary with encrypted sensitive fields
            
        Returns:
            Dictionary with decrypted sensitive fields
        """
        sensitive_fields = {
            'password', 'secret', 'key', 'token', 'api_key',
            'client_secret', 'private_key', 'credential'
        }
        
        decrypted_data = encrypted_data.copy()
        
        for field, value in encrypted_data.items():
            if any(sensitive in field.lower() for sensitive in sensitive_fields):
                if isinstance(value, str) and value:
                    try:
                        decrypted_data[field] = self.decrypt_credential(value)
                    except ValueError:
                        # Value might not be encrypted, leave as is
                        pass
                        
        return decrypted_data


def get_production_encryption(encryption_key: Optional[str] = None) -> ProductionEncryption:
    """
    Get a production encryption instance.
    
    Args:
        encryption_key: Optional encryption key, will use config if not provided
        
    Returns:
        ProductionEncryption instance
    """
    if not encryption_key:
        from app.core.config import settings
        encryption_key = settings.CREDENTIAL_ENCRYPTION_KEY
        
    return ProductionEncryption(encryption_key)


def encrypt_credential_for_storage(credential: str, encryption_key: Optional[str] = None) -> str:
    """
    Convenience function to encrypt a credential for database storage.
    
    Args:
        credential: Plain text credential
        encryption_key: Optional encryption key
        
    Returns:
        Encrypted credential ready for storage
    """
    encryptor = get_production_encryption(encryption_key)
    return encryptor.encrypt_credential(credential)


def decrypt_credential_from_storage(encrypted_credential: str, encryption_key: Optional[str] = None) -> str:
    """
    Convenience function to decrypt a credential from database storage.
    
    Args:
        encrypted_credential: Encrypted credential from storage
        encryption_key: Optional encryption key
        
    Returns:
        Decrypted plain text credential
    """
    decryptor = get_production_encryption(encryption_key)
    return decryptor.decrypt_credential(encrypted_credential)