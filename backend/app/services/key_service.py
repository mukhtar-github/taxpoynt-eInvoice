"""
Key Management Service for TaxPoynt eInvoice System.

This service provides functions for:
- Storing and retrieving encryption keys
- Key rotation
- Key version management
"""

import base64
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union

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


class KeyManagementService:
    """Service for managing encryption keys."""
    
    def __init__(self, db: Session = None):
        self.db = db
        self._encryption_key = None
        self._key_registry = {}
        self._initialized = False
        self._loaded_keys = False
        
    def initialize(self):
        """Initialize the key management service."""
        if not self._initialized:
            # Set default app encryption key
            self._encryption_key = get_app_encryption_key()
            
            # Add to registry
            default_key_id = "app_default"
            self._key_registry[default_key_id] = {
                "id": default_key_id,
                "key": base64.b64encode(self._encryption_key).decode(),
                "created_at": datetime.now().isoformat(),
                "active": True
            }
            
            self._initialized = True
            
    def _ensure_initialized(self):
        """Ensure the service is initialized."""
        if not self._initialized:
            self.initialize()
    
    def get_current_key(self) -> bytes:
        """
        Get the current active encryption key.
        
        Returns:
            bytes: The current encryption key
        """
        self._ensure_initialized()
        return self._encryption_key
    
    def get_key_by_id(self, key_id: str) -> Optional[bytes]:
        """
        Get a key by its ID.
        
        Args:
            key_id: The key ID
            
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
        Load keys from persistent storage.
        In production, this would use a secure storage solution.
        """
        if self._loaded_keys:
            return
            
        try:
            # In a real application, this would load from a secure database table
            # or a key management service like AWS KMS or HashiCorp Vault
            
            # For development: try to load from a local file
            keys_file = os.path.join(os.path.dirname(__file__), "../../data/keys.json")
            
            if os.path.exists(keys_file):
                with open(keys_file, "r") as f:
                    stored_keys = json.load(f)
                    
                for key_id, key_data in stored_keys.items():
                    self._key_registry[key_id] = key_data
            
            self._loaded_keys = True
        except Exception as e:
            # Log error but continue with default key
            print(f"Error loading keys: {str(e)}")
    
    def _persist_keys(self):
        """
        Save keys to persistent storage.
        In production, this would use a secure storage solution.
        """
        # In a real application, this would save to a secure database table
        # or a key management service
        
        # For development: save to a local file
        os.makedirs(os.path.join(os.path.dirname(__file__), "../../data"), exist_ok=True)
        keys_file = os.path.join(os.path.dirname(__file__), "../../data/keys.json")
        
        try:
            with open(keys_file, "w") as f:
                json.dump(self._key_registry, f, indent=2)
        except Exception as e:
            # Log error but continue
            print(f"Error persisting keys: {str(e)}")
    
    def rotate_key(self) -> str:
        """
        Generate a new encryption key and set it as the current active key.
        
        Returns:
            str: The new key ID
        """
        self._ensure_initialized()
        
        # Generate new key
        key_id, new_key = generate_key_id(), generate_secret_key()
        
        # Create key entry
        key_entry = create_key_entry(key_id, new_key)
        
        # Deactivate old keys
        for k_id in self._key_registry:
            self._key_registry[k_id]["active"] = False
        
        # Add to registry
        self._key_registry[key_id] = key_entry
        
        # Update current key
        self._encryption_key = new_key
        
        # Persist changes
        self._persist_keys()
        
        return key_id
    
    def list_keys(self) -> List[Dict[str, Any]]:
        """
        List all registered keys (without the actual key material).
        
        Returns:
            List of key metadata dictionaries
        """
        self._ensure_initialized()
        self._load_keys_from_storage()
        
        # Return metadata without the actual key material
        result = []
        for key_id, key_data in self._key_registry.items():
            metadata = key_data.copy()
            metadata.pop("key", None)  # Remove the actual key
            result.append(metadata)
            
        return result
    
    def encrypt_value(self, value: Any, key_id: Optional[str] = None) -> Dict[str, str]:
        """
        Encrypt a value using a specific key or the current active key.
        
        Args:
            value: The value to encrypt
            key_id: Optional key ID to use
            
        Returns:
            Dict containing the encrypted value and key ID
        """
        self._ensure_initialized()
        
        # Determine which key to use
        key = None
        if key_id:
            key = self.get_key_by_id(key_id)
            if not key:
                raise HTTPException(status_code=400, detail=f"Key with ID {key_id} not found")
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
            "key_id": key_id
        }
    
    def decrypt_value(self, encrypted_data: Dict[str, str], as_dict: bool = False) -> Any:
        """
        Decrypt a value using the specified key.
        
        Args:
            encrypted_data: Dict with encrypted_value and key_id
            as_dict: Whether to parse result as JSON dict
            
        Returns:
            The decrypted value
        """
        self._ensure_initialized()
        
        encrypted_value = encrypted_data.get("encrypted_value")
        key_id = encrypted_data.get("key_id")
        
        if not encrypted_value or not key_id:
            raise HTTPException(status_code=400, detail="Missing encrypted value or key ID")
        
        key = self.get_key_by_id(key_id)
        if not key:
            raise HTTPException(status_code=400, detail=f"Key with ID {key_id} not found")
        
        return decrypt_with_gcm(encrypted_value, key, as_dict)


# Global instance for dependency injection
def get_key_service(db: Session = Depends(get_db)) -> KeyManagementService:
    """Dependency for the key management service."""
    service = KeyManagementService(db)
    service.initialize()
    return service 