"""
Transmission Key Service for TaxPoynt eInvoice - Access Point Provider Functions.

This module provides Access Point Provider (APP) role functionality for specialized
key management for secure FIRS transmissions, including automatic key rotation,
secure storage, and key versioning for transmission security.

APP Role Responsibilities:
- Automatic key rotation based on time or usage thresholds for FIRS transmission security
- Secure storage of transmission keys for APP operations
- Key versioning to support decryption of historical FIRS transmissions
- Cryptographic key lifecycle management for secure communication protocols
"""

import uuid
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional, List, Any
from uuid import UUID

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.models.encryption import EncryptionKey, EncryptionConfig
from app.utils.encryption import (
    generate_secret_key,
    encrypt_with_gcm,
    decrypt_with_gcm,
    generate_key_id,
    create_key_entry
)
from app.core.config import settings

logger = logging.getLogger(__name__)

# Key rotation thresholds for FIRS transmission security
DEFAULT_KEY_ROTATION_DAYS = 30
DEFAULT_KEY_USAGE_THRESHOLD = 1000
MAX_ACTIVE_KEYS = 3

class TransmissionKeyService:
    """
    Access Point Provider service for secure key management specific to FIRS transmissions.
    
    This service provides APP role functions for managing encryption keys used in
    secure FIRS transmission protocols, ensuring cryptographic security and
    compliance with e-invoicing requirements.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self._initialize_config()
    
    def _initialize_config(self) -> None:
        """Initialize FIRS transmission key rotation configuration if it doesn't exist."""
        config = self.db.query(EncryptionConfig).filter(
            EncryptionConfig.config_name == "transmission_key_rotation"
        ).first()
        
        if not config:
            config = EncryptionConfig(
                id=uuid.uuid4(),
                config_name="transmission_key_rotation",
                config_data={
                    "rotation_days": DEFAULT_KEY_ROTATION_DAYS,
                    "usage_threshold": DEFAULT_KEY_USAGE_THRESHOLD,
                    "max_active_keys": MAX_ACTIVE_KEYS,
                    "last_rotation": datetime.utcnow().isoformat(),
                    "firs_compliant": True,
                    "app_provider": "TaxPoynt"
                }
            )
            self.db.add(config)
            self.db.commit()
            
            # Create initial key for FIRS transmission
            self._create_new_key()
            logger.info("Initialized APP transmission key rotation configuration for FIRS security")
    
    def _create_new_key(self) -> EncryptionKey:
        """Create a new encryption key for FIRS transmissions."""
        key_id = generate_key_id()
        key_bytes = generate_secret_key()
        
        # Create key entry with FIRS compliance metadata
        key_entry = create_key_entry(key_id, key_bytes)
        key_entry.update({
            "purpose": "transmission",
            "is_active": True,
            "firs_compliant": True,
            "app_provider": "TaxPoynt",
            "transmission_type": "firs_secure",
            "created_for": "app_transmission"
        })
        
        # Store in database
        db_key = EncryptionKey(
            id=key_id,
            key_data=key_entry,
            created_at=datetime.utcnow(),
            usage_count=0
        )
        
        self.db.add(db_key)
        self.db.commit()
        self.db.refresh(db_key)
        
        logger.info(f"Created new FIRS transmission encryption key: {key_id}")
        return db_key
    
    def get_current_key(self) -> Tuple[str, bytes]:
        """
        Get the current active encryption key for FIRS transmissions - APP Role Function.
        
        Provides Access Point Provider current encryption key for secure FIRS
        transmission protocols. Automatically handles key rotation if needed.
        
        If no active key exists or rotation is needed, a new key is created.
        
        Returns:
            Tuple containing (key_id, key_bytes) for FIRS transmission
        """
        # Check if we need to rotate keys for FIRS security
        self._check_rotation_policy()
        
        # Get current active key
        key = self.db.query(EncryptionKey).filter(
            and_(
                EncryptionKey.key_data["purpose"].astext == "transmission",
                EncryptionKey.key_data["is_active"].astext == "true"
            )
        ).order_by(EncryptionKey.created_at.desc()).first()
        
        if not key:
            key = self._create_new_key()
        
        # Increment usage count for rotation tracking
        key.usage_count += 1
        self.db.commit()
        
        # Decode the stored key
        key_bytes = key.get_key_bytes()
        logger.debug(f"Retrieved current FIRS transmission key: {key.id}")
        return key.id, key_bytes
    
    def _check_rotation_policy(self) -> None:
        """Check if key rotation is needed for FIRS transmission security and perform rotation if required."""
        config = self.db.query(EncryptionConfig).filter(
            EncryptionConfig.config_name == "transmission_key_rotation"
        ).first()
        
        if not config:
            return
        
        config_data = config.config_data
        last_rotation = datetime.fromisoformat(config_data.get("last_rotation", "2020-01-01T00:00:00"))
        rotation_days = config_data.get("rotation_days", DEFAULT_KEY_ROTATION_DAYS)
        usage_threshold = config_data.get("usage_threshold", DEFAULT_KEY_USAGE_THRESHOLD)
        
        # Get current active key
        current_key = self.db.query(EncryptionKey).filter(
            and_(
                EncryptionKey.key_data["purpose"].astext == "transmission",
                EncryptionKey.key_data["is_active"].astext == "true"
            )
        ).order_by(EncryptionKey.created_at.desc()).first()
        
        # Check if rotation is needed for FIRS security
        rotation_needed = False
        
        # Time-based rotation for FIRS compliance
        if datetime.utcnow() - last_rotation > timedelta(days=rotation_days):
            logger.info(f"Time-based FIRS transmission key rotation triggered: {rotation_days} days elapsed")
            rotation_needed = True
        
        # Usage-based rotation for security
        if current_key and current_key.usage_count >= usage_threshold:
            logger.info(f"Usage-based FIRS transmission key rotation triggered: {current_key.usage_count} uses")
            rotation_needed = True
        
        if rotation_needed:
            self._rotate_keys()
            
            # Update last rotation timestamp
            config.config_data["last_rotation"] = datetime.utcnow().isoformat()
            self.db.commit()
    
    def _rotate_keys(self) -> None:
        """
        Rotate encryption keys for FIRS transmission security:
        1. Create new active key
        2. Deactivate oldest keys if max active keys is exceeded
        """
        # Create new key for FIRS transmission
        self._create_new_key()
        
        # Get config for max active keys
        config = self.db.query(EncryptionConfig).filter(
            EncryptionConfig.config_name == "transmission_key_rotation"
        ).first()
        
        max_active_keys = MAX_ACTIVE_KEYS
        if config and "max_active_keys" in config.config_data:
            max_active_keys = config.config_data["max_active_keys"]
        
        # Get active keys
        active_keys = self.db.query(EncryptionKey).filter(
            and_(
                EncryptionKey.key_data["purpose"].astext == "transmission",
                EncryptionKey.key_data["is_active"].astext == "true"
            )
        ).order_by(EncryptionKey.created_at.desc()).all()
        
        # Deactivate oldest keys if we have too many
        if len(active_keys) > max_active_keys:
            for key in active_keys[max_active_keys:]:
                key.key_data["is_active"] = False
                logger.info(f"Deactivated old FIRS transmission key: {key.id}")
            
            self.db.commit()
        
        logger.info("Completed FIRS transmission key rotation for APP security")
    
    def encrypt_payload(self, payload: Any, context: Dict[str, Any] = None) -> Tuple[str, str]:
        """
        Encrypt payload data for secure FIRS transmission - APP Role Function.
        
        Provides Access Point Provider encryption for payload data before
        secure transmission to FIRS, ensuring data integrity and confidentiality.
        
        Args:
            payload: The data to encrypt for FIRS transmission (string or dict)
            context: Additional context for the encryption
            
        Returns:
            Tuple containing (key_id, encrypted_data) for FIRS transmission
        """
        # Get current key for FIRS transmission
        key_id, key_bytes = self.get_current_key()
        
        # Add FIRS transmission header metadata
        transmission_context = context or {}
        transmission_context.update({
            "app_provider": "TaxPoynt",
            "transmission_type": "firs_secure",
            "firs_compliant": True
        })
        
        # Add header metadata for FIRS compliance
        if isinstance(payload, dict):
            payload_with_header = {
                "_header": {
                    "enc_timestamp": datetime.utcnow().isoformat(),
                    "version": "1.0",
                    "key_id": key_id,
                    "context": transmission_context,
                    "firs_transmission": True,
                    "app_encrypted": True
                },
                "payload": payload
            }
            encrypted_data = encrypt_with_gcm(payload_with_header, key_bytes)
        else:
            # If string payload, convert to dict with FIRS header
            payload_with_header = {
                "_header": {
                    "enc_timestamp": datetime.utcnow().isoformat(),
                    "version": "1.0",
                    "key_id": key_id,
                    "context": transmission_context,
                    "firs_transmission": True,
                    "app_encrypted": True
                },
                "payload": str(payload)
            }
            encrypted_data = encrypt_with_gcm(payload_with_header, key_bytes)
        
        logger.debug(f"Encrypted payload for FIRS transmission using key {key_id}")
        return key_id, encrypted_data
    
    def decrypt_payload(self, encrypted_data: str, key_id: str = None) -> Dict[str, Any]:
        """
        Decrypt an encrypted payload from FIRS transmission - APP Role Function.
        
        Provides Access Point Provider decryption for payload data received from
        FIRS transmissions or other secure communication channels.
        
        Args:
            encrypted_data: The encrypted data string from FIRS transmission
            key_id: Optional key ID (if not provided, will be extracted from header)
            
        Returns:
            Decrypted payload as dict with header metadata
        """
        if not key_id:
            # Try to decrypt with the current key first
            current_key_id, current_key_bytes = self.get_current_key()
            
            try:
                # Attempt decryption with current key
                decrypted_data = decrypt_with_gcm(encrypted_data, current_key_bytes, as_dict=True)
                
                # Check if we got a valid FIRS transmission header structure
                if "_header" in decrypted_data and "payload" in decrypted_data:
                    return decrypted_data
                
                # If no header, wrap the raw decrypted data with FIRS metadata
                return {
                    "_header": {
                        "enc_timestamp": "",
                        "version": "unknown",
                        "key_id": current_key_id,
                        "firs_transmission": True,
                        "app_decrypted": True
                    },
                    "payload": decrypted_data
                }
            except Exception as e:
                # If current key doesn't work, we need key_id
                if not key_id:
                    raise ValueError("Cannot decrypt FIRS transmission payload: key_id not provided and current key failed")
        
        # Get key by ID for FIRS transmission decryption
        key = self.db.query(EncryptionKey).filter(EncryptionKey.id == key_id).first()
        if not key:
            raise ValueError(f"FIRS transmission encryption key not found: {key_id}")
        
        # Decrypt using the specified key
        key_bytes = key.get_key_bytes()
        decrypted_data = decrypt_with_gcm(encrypted_data, key_bytes, as_dict=True)
        
        # If missing header structure, wrap the raw data with FIRS metadata
        if "_header" not in decrypted_data or "payload" not in decrypted_data:
            return {
                "_header": {
                    "enc_timestamp": "",
                    "version": "unknown",
                    "key_id": key_id,
                    "firs_transmission": True,
                    "app_decrypted": True
                },
                "payload": decrypted_data
            }
        
        logger.debug(f"Decrypted FIRS transmission payload using key {key_id}")
        return decrypted_data
    
    def get_keys_info(self) -> List[Dict[str, Any]]:
        """
        Get information about all FIRS transmission encryption keys - APP Role Function.
        
        Returns metadata about Access Point Provider encryption keys used for
        FIRS transmission security and audit purposes.
        """
        keys = self.db.query(EncryptionKey).filter(
            EncryptionKey.key_data["purpose"].astext == "transmission"
        ).order_by(EncryptionKey.created_at.desc()).all()
        
        return [{
            "id": key.id,
            "created_at": key.created_at.isoformat(),
            "is_active": key.key_data.get("is_active", False),
            "usage_count": key.usage_count,
            "last_used": key.key_data.get("last_used", ""),
            "firs_compliant": key.key_data.get("firs_compliant", False),
            "app_provider": key.key_data.get("app_provider", ""),
            "transmission_type": key.key_data.get("transmission_type", "")
        } for key in keys]
    
    def update_rotation_policy(
        self, 
        rotation_days: int = None, 
        usage_threshold: int = None,
        max_active_keys: int = None
    ) -> Dict[str, Any]:
        """
        Update the FIRS transmission key rotation policy - APP Role Function.
        
        Updates Access Point Provider key rotation policies for FIRS transmission
        security and compliance requirements.
        
        Args:
            rotation_days: Number of days before rotating keys for FIRS security
            usage_threshold: Number of uses before rotating keys
            max_active_keys: Maximum number of active keys to maintain
            
        Returns:
            Updated policy configuration for APP operations
        """
        config = self.db.query(EncryptionConfig).filter(
            EncryptionConfig.config_name == "transmission_key_rotation"
        ).first()
        
        if not config:
            self._initialize_config()
            config = self.db.query(EncryptionConfig).filter(
                EncryptionConfig.config_name == "transmission_key_rotation"
            ).first()
        
        # Update configuration for FIRS transmission security
        if rotation_days is not None:
            config.config_data["rotation_days"] = max(1, rotation_days)
        
        if usage_threshold is not None:
            config.config_data["usage_threshold"] = max(1, usage_threshold)
            
        if max_active_keys is not None:
            config.config_data["max_active_keys"] = max(1, min(10, max_active_keys))
        
        # Add FIRS compliance metadata
        config.config_data["last_updated"] = datetime.utcnow().isoformat()
        config.config_data["updated_for"] = "firs_transmission_security"
        
        self.db.commit()
        
        logger.info(f"Updated FIRS transmission key rotation policy: rotation_days={config.config_data.get('rotation_days')}, usage_threshold={config.config_data.get('usage_threshold')}")
        
        return config.config_data
    
    def create_firs_specific_key(self, organization_id: UUID) -> str:
        """
        Create a specific key for FIRS transmission for an organization - APP Role Function.
        
        Creates dedicated encryption keys for Access Point Provider FIRS transmission
        operations specific to an organization's secure communication needs.
        
        Args:
            organization_id: Organization ID for the FIRS transmission key
            
        Returns:
            str: ID of the new FIRS transmission key
        """
        key_id = f"firs_org_{organization_id}_{generate_key_id()}"
        key_bytes = generate_secret_key()
        
        # Create key entry with organization-specific FIRS metadata
        key_entry = create_key_entry(key_id, key_bytes)
        key_entry.update({
            "purpose": "transmission",
            "is_active": True,
            "firs_compliant": True,
            "app_provider": "TaxPoynt",
            "transmission_type": "firs_org_specific",
            "organization_id": str(organization_id),
            "created_for": "organization_transmission"
        })
        
        # Store in database
        db_key = EncryptionKey(
            id=key_id,
            key_data=key_entry,
            created_at=datetime.utcnow(),
            usage_count=0
        )
        
        self.db.add(db_key)
        self.db.commit()
        
        logger.info(f"Created organization-specific FIRS transmission key for {organization_id}: {key_id}")
        return key_id