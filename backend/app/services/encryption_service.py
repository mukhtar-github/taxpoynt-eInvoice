"""
Encryption Service for TaxPoynt eInvoice System.

This service provides:
- Field-level encryption for database records
- Configuration data encryption
- Helpers for encrypted model operations
"""

from typing import Any, Dict, List, Optional, Union
import json
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.deps import get_db # type: ignore
from app.utils.encryption import (
    encrypt_field,
    decrypt_field,
    encrypt_dict_fields,
    decrypt_dict_fields
)
from app.services.key_service import KeyManagementService, get_key_service


class EncryptionService:
    """Service for handling encryption operations."""
    
    def __init__(
        self, 
        db: Session,
        key_service: KeyManagementService
    ):
        self.db = db
        self.key_service = key_service
        
    def encrypt_integration_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Encrypt sensitive fields in an integration configuration.
        
        Args:
            config: Integration configuration dictionary
            
        Returns:
            Dict with sensitive fields encrypted
        """
        # Define sensitive fields that should be encrypted
        sensitive_fields = [
            "api_key", 
            "secret_key", 
            "password", 
            "token",
            "access_token",
            "refresh_token",
            "client_secret",
            "private_key",
            "auth"
        ]
        
        # Encrypt nested fields
        result = config.copy()
        
        # Handle nested dictionaries
        for key, value in result.items():
            if isinstance(value, dict):
                # Process nested dictionaries
                result[key] = self.encrypt_integration_config(value)
            elif key in sensitive_fields and value is not None:
                # Encrypt sensitive field
                key_data = self.key_service.encrypt_value(value)
                result[key] = key_data
                
        return result
    
    def decrypt_integration_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Decrypt sensitive fields in an integration configuration.
        
        Args:
            config: Integration configuration with encrypted fields
            
        Returns:
            Dict with sensitive fields decrypted
        """
        result = config.copy()
        
        # Handle nested dictionaries and encrypted fields
        for key, value in result.items():
            if isinstance(value, dict):
                # Check if this is an encrypted value with key_id
                if "encrypted_value" in value and "key_id" in value:
                    # This is an encrypted value
                    result[key] = self.key_service.decrypt_value(value)
                else:
                    # This is a nested dictionary, process recursively
                    result[key] = self.decrypt_integration_config(value)
                
        return result
        
    def encrypt_api_key(self, api_key: str) -> Dict[str, str]:
        """
        Encrypt an API key.
        
        Args:
            api_key: Plain text API key
            
        Returns:
            Dict with encrypted value and key ID
        """
        return self.key_service.encrypt_value(api_key)
    
    def decrypt_api_key(self, encrypted_data: Dict[str, str]) -> str:
        """
        Decrypt an API key.
        
        Args:
            encrypted_data: Dict with encrypted value and key ID
            
        Returns:
            Decrypted API key
        """
        return self.key_service.decrypt_value(encrypted_data)
    
    def encrypt_firs_credentials(self, api_key: str, secret_key: str) -> Dict[str, Dict[str, str]]:
        """
        Encrypt FIRS API credentials.
        
        Args:
            api_key: FIRS API key
            secret_key: FIRS secret key
            
        Returns:
            Dict with encrypted credentials
        """
        return {
            "api_key": self.key_service.encrypt_value(api_key),
            "secret_key": self.key_service.encrypt_value(secret_key)
        }
    
    def decrypt_firs_credentials(
        self, 
        encrypted_api_key: Dict[str, str], 
        encrypted_secret_key: Dict[str, str]
    ) -> Dict[str, str]:
        """
        Decrypt FIRS API credentials.
        
        Args:
            encrypted_api_key: Encrypted API key dict
            encrypted_secret_key: Encrypted secret key dict
            
        Returns:
            Dict with decrypted credentials
        """
        return {
            "api_key": self.key_service.decrypt_value(encrypted_api_key),
            "secret_key": self.key_service.decrypt_value(encrypted_secret_key)
        }


def get_encryption_service(
    db: Session = Depends(get_db),
    key_service: KeyManagementService = Depends(get_key_service)
) -> EncryptionService:
    """Dependency for the encryption service."""
    return EncryptionService(db, key_service) 