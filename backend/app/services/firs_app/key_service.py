"""
Key Management Service for TaxPoynt eInvoice - Access Point Provider Functions.

This module provides Access Point Provider (APP) role functionality for secure
key management, encryption operations, and cryptographic security for FIRS
transmission protocols and authentication mechanisms.

APP Role Responsibilities:
- Storing and retrieving encryption keys for FIRS transmission security
- Key rotation and lifecycle management for APP operations
- Cryptographic key version management for secure communication
- Secure key storage and access control for transmission protocols
"""

import base64
import json
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
from uuid import UUID
from pathlib import Path

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db # type: ignore
from app.utils.encryption import (
    generate_secret_key, 
    get_app_encryption_key, 
    generate_key_id,
    create_key_entry,
    encrypt_with_gcm,
    decrypt_with_gcm
)
from app.core.config import settings

logger = logging.getLogger(__name__)


class KeyManagementService:
    """
    Access Point Provider service for managing encryption keys and cryptographic security.
    
    This service provides APP role functions for secure key management, encryption
    operations, and cryptographic protocols required for FIRS transmission security
    and authentication mechanisms.
    """
    
    def __init__(self, db: Session = None):
        self.db = db
        self._encryption_key = None
        self._key_registry = {}
        self._initialized = False
        self._loaded_keys = False
        
    def initialize(self):
        """Initialize the APP key management service for FIRS security."""
        if not self._initialized:
            # Set default app encryption key for FIRS transmission
            self._encryption_key = get_app_encryption_key()
            
            # Add to registry with FIRS compliance metadata
            default_key_id = "app_default"
            self._key_registry[default_key_id] = {
                "id": default_key_id,
                "key": base64.b64encode(self._encryption_key).decode(),
                "created_at": datetime.now().isoformat(),
                "active": True,
                "firs_compliant": True,
                "app_provider": "TaxPoynt",
                "key_purpose": "transmission_security"
            }
            
            self._initialized = True
            logger.info("Initialized APP key management service for FIRS transmission security")
            
    def _ensure_initialized(self):
        """Ensure the APP service is initialized for FIRS operations."""
        if not self._initialized:
            self.initialize()
    
    def get_current_key(self) -> bytes:
        """
        Get the current active encryption key for FIRS transmission - APP Role Function.
        
        Returns the current encryption key used by Access Point Provider
        for secure FIRS transmission and authentication protocols.
        
        Returns:
            bytes: The current encryption key for FIRS transmission
        """
        self._ensure_initialized()
        return self._encryption_key
    
    def get_key_by_id(self, key_id: str) -> Optional[bytes]:
        """
        Get a key by its ID for APP operations - APP Role Function.
        
        Retrieves specific encryption keys used by Access Point Provider
        for FIRS transmission security and cryptographic operations.
        
        Args:
            key_id: The key ID for APP operations
            
        Returns:
            bytes: The encryption key or None if not found
        """
        self._ensure_initialized()
        
        if key_id in self._key_registry:
            key_data = self._key_registry[key_id]
            return base64.b64decode(key_data["key"])
        
        # If not in memory, try to load from storage
        self._load_keys_from_storage()
        
        if key_id in self._key_registry:
            key_data = self._key_registry[key_id]
            return base64.b64decode(key_data["key"])
            
        return None
    
    def _load_keys_from_storage(self):
        """
        Load keys from persistent storage for APP operations.
        In production, this would use a secure storage solution like AWS KMS,
        HashiCorp Vault, or Azure Key Vault for FIRS compliance.
        """        
        # Skip if already loaded
        if self._loaded_keys:
            return
            
        # First check environment
        storage_file = None
        if hasattr(settings, 'KEY_STORAGE_FILE'):
            storage_file = settings.KEY_STORAGE_FILE
            
        # If environment variable not set, use default location
        if not storage_file:
            storage_dir = Path(settings.BASE_DIR) / "keys"
            storage_file = storage_dir / "key_registry.enc"
            
        # If storage file exists, load keys
        try:
            if os.path.exists(storage_file):
                # In production, use a proper secure storage solution for FIRS compliance
                # This is only for development/testing
                with open(storage_file, "rb") as f:
                    encrypted_data = f.read()
                    
                # The master key would be stored in a secure environment variable
                # or retrieved from a secure key management service
                master_key = get_app_encryption_key()
                
                # Decrypt the key registry
                decrypted_data = decrypt_with_gcm(encrypted_data, master_key, as_dict=True)
                
                if decrypted_data and isinstance(decrypted_data, dict):
                    self._key_registry.update(decrypted_data)
                    
            self._loaded_keys = True
            logger.info("Loaded APP encryption keys from secure storage")
                
        except Exception as e:
            # Log the error but don't crash
            logger.error(f"Error loading APP keys from storage: {e}")
            
    def _save_keys_to_storage(self):
        """
        Save keys to persistent storage for APP security.
        In production, this would use a secure storage solution like AWS KMS,
        HashiCorp Vault, or Azure Key Vault for FIRS compliance.
        """
        # Get storage location
        storage_file = None
        if hasattr(settings, 'KEY_STORAGE_FILE'):
            storage_file = settings.KEY_STORAGE_FILE
            
        # If environment variable not set, use default location
        if not storage_file:
            storage_dir = Path(settings.BASE_DIR) / "keys"
            os.makedirs(storage_dir, exist_ok=True)
            storage_file = storage_dir / "key_registry.enc"
            
        try:
            # In production, use a proper secure storage solution for FIRS compliance
            # This is only for development/testing
            
            # The master key would be stored in a secure environment variable
            # or retrieved from a secure key management service
            master_key = get_app_encryption_key()
            
            # Create backup of registry first
            if os.path.exists(storage_file):
                backup_file = f"{storage_file}.bak"
                with open(storage_file, "rb") as src, open(backup_file, "wb") as dst:
                    dst.write(src.read())
            
            # Encrypt and save the key registry
            encrypted_data = encrypt_with_gcm(self._key_registry, master_key)
            
            with open(storage_file, "wb") as f:
                f.write(encrypted_data)
                
            logger.info("Saved APP encryption keys to secure storage")
                
        except Exception as e:
            # Log the error but don't crash
            logger.error(f"Error saving APP keys to storage: {e}")
    
    def rotate_key(self, organization_id: Optional[UUID] = None) -> str:
        """
        Generate a new encryption key for APP operations - APP Role Function.
        
        Rotates encryption keys used by Access Point Provider for FIRS transmission
        security and ensures continued cryptographic compliance.
        
        Args:
            organization_id: Optional organization ID for organization-specific keys
            
        Returns:
            str: ID of the new key for APP operations
        """
        self._ensure_initialized()
        
        # Generate new key for FIRS transmission
        key_id, new_key = generate_key_id(), generate_secret_key()
        
        # Create key entry with FIRS compliance metadata
        key_entry = create_key_entry(key_id, new_key)
        key_entry.update({
            "firs_compliant": True,
            "app_provider": "TaxPoynt",
            "key_purpose": "transmission_security",
            "rotation_timestamp": datetime.now().isoformat(),
            "organization_id": str(organization_id) if organization_id else None
        })
        
        # Deactivate old keys
        for k_id in self._key_registry:
            self._key_registry[k_id]["active"] = False
        
        # Add to registry
        self._key_registry[key_id] = key_entry
        
        # Update current key
        self._encryption_key = new_key
        
        # Persist changes
        self._save_keys_to_storage()
        
        logger.info(f"Rotated APP encryption key for FIRS transmission security: {key_id}")
        
        return key_id
    
    def list_keys(self) -> List[Dict[str, Any]]:
        """
        List all registered APP keys (without the actual key material) - APP Role Function.
        
        Returns metadata for encryption keys used by Access Point Provider
        for FIRS transmission security and audit purposes.
        
        Returns:
            List of key metadata dictionaries for APP operations
        """
        self._ensure_initialized()
        self._load_keys_from_storage()
        
        # Return metadata without the actual key material
        result = []
        for key_id, key_data in self._key_registry.items():
            metadata = key_data.copy()
            metadata.pop("key", None)  # Remove the actual key for security
            metadata["app_managed"] = True
            result.append(metadata)
            
        return result
    
    def encrypt_data(self, data: Any, context: Optional[Dict[str, str]] = None) -> Tuple[str, str]:
        """
        Encrypt data for FIRS transmission - APP Role Function.
        
        Provides Access Point Provider encryption for sensitive data before
        FIRS transmission, ensuring data security and compliance.
        
        Args:
            data: The data to encrypt for FIRS transmission
            context: Optional context for encryption (e.g., purpose, organization)
            
        Returns:
            Tuple of (key_id, encrypted_data) for APP transmission
        """
        self._ensure_initialized()
        
        # Determine key to use based on context
        key_id = None
        key = self.get_current_key()
        
        # Find the active key ID
        for k_id, k_data in self._key_registry.items():
            if k_data.get("active", False):
                key_id = k_id
                break
        
        if not key_id:
            raise HTTPException(status_code=500, detail="No active encryption key for APP operations")
        
        # Add FIRS transmission metadata to data
        transmission_data = {
            "payload": data,
            "app_provider": "TaxPoynt",
            "encryption_timestamp": datetime.now().isoformat(),
            "firs_ready": True
        }
        
        if context:
            transmission_data["context"] = context
        
        # Encrypt the data
        encrypted = encrypt_with_gcm(transmission_data, key)
        
        logger.debug(f"Encrypted data for FIRS transmission using key {key_id}")
        
        return key_id, encrypted
    
    def decrypt_data(self, key_id: str, encrypted_data: str) -> Any:
        """
        Decrypt data from FIRS transmission - APP Role Function.
        
        Provides Access Point Provider decryption for data received from
        FIRS or other secure transmission sources.
        
        Args:
            key_id: The key ID used for encryption
            encrypted_data: The encrypted data to decrypt
            
        Returns:
            The decrypted data from FIRS transmission
        """
        self._ensure_initialized()
        
        key = self.get_key_by_id(key_id)
        if not key:
            raise HTTPException(status_code=400, detail=f"APP encryption key {key_id} not found")
        
        # Decrypt the data
        decrypted_data = decrypt_with_gcm(encrypted_data, key, as_dict=True)
        
        # Extract the original payload if it's in our format
        if isinstance(decrypted_data, dict) and "payload" in decrypted_data:
            payload = decrypted_data["payload"]
            logger.debug(f"Decrypted FIRS transmission data using key {key_id}")
            return payload
        
        return decrypted_data
    
    def encrypt_value(self, value: Any, key_id: Optional[str] = None) -> Dict[str, str]:
        """
        Encrypt a value using APP encryption - APP Role Function.
        
        Provides Access Point Provider value encryption for secure storage
        and FIRS transmission protocols.
        
        Args:
            value: The value to encrypt
            key_id: Optional key ID to use for encryption
            
        Returns:
            Dict containing the encrypted value and key ID
        """
        self._ensure_initialized()
        
        # Determine which key to use
        key = None
        if key_id:
            key = self.get_key_by_id(key_id)
            if not key:
                raise HTTPException(status_code=400, detail=f"APP key {key_id} not found")
        else:
            key = self.get_current_key()
            # Find the key ID for the current key
            for k_id, k_data in self._key_registry.items():
                if k_data.get("active", False):
                    key_id = k_id
                    break
        
        # Encrypt the value
        encrypted = encrypt_with_gcm(value, key)
        
        return {
            "encrypted_value": encrypted,
            "key_id": key_id,
            "app_encrypted": True,
            "firs_compatible": True
        }
    
    def decrypt_value(self, encrypted_data: Dict[str, str], as_dict: bool = False) -> Any:
        """
        Decrypt a value using APP decryption - APP Role Function.
        
        Provides Access Point Provider value decryption for secure data
        retrieval and FIRS transmission processing.
        
        Args:
            encrypted_data: Dict with encrypted_value and key_id
            as_dict: Whether to parse result as JSON dict
            
        Returns:
            The decrypted value for APP processing
        """
        self._ensure_initialized()
        
        encrypted_value = encrypted_data.get("encrypted_value")
        key_id = encrypted_data.get("key_id")
        
        if not encrypted_value or not key_id:
            raise HTTPException(status_code=400, detail="Missing encrypted value or key ID for APP decryption")
        
        key = self.get_key_by_id(key_id)
        if not key:
            raise HTTPException(status_code=400, detail=f"APP decryption key {key_id} not found")
        
        return decrypt_with_gcm(encrypted_value, key, as_dict)
    
    def create_firs_transmission_key(self, organization_id: UUID) -> str:
        """
        Create a specific key for FIRS transmission - APP Role Function.
        
        Generates dedicated encryption keys for Access Point Provider
        FIRS transmission operations and secure communication.
        
        Args:
            organization_id: Organization ID for the transmission key
            
        Returns:
            str: ID of the new FIRS transmission key
        """
        self._ensure_initialized()
        
        # Generate new key specifically for FIRS transmission
        key_id = f"firs_transmission_{organization_id}_{generate_key_id()}"
        new_key = generate_secret_key()
        
        # Create key entry with FIRS transmission metadata
        key_entry = create_key_entry(key_id, new_key)
        key_entry.update({
            "firs_compliant": True,
            "app_provider": "TaxPoynt",
            "key_purpose": "firs_transmission",
            "organization_id": str(organization_id),
            "created_for": "transmission_security",
            "transmission_ready": True
        })
        
        # Add to registry
        self._key_registry[key_id] = key_entry
        
        # Persist changes
        self._save_keys_to_storage()
        
        logger.info(f"Created FIRS transmission key for organization {organization_id}: {key_id}")
        
        return key_id


# Global instance for dependency injection
def get_key_service(db: Session = Depends(get_db)) -> KeyManagementService:
    """Dependency for the APP key management service."""
    service = KeyManagementService(db)
    service.initialize()
    return service