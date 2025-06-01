"""
FIRS Encryption Utilities

This module provides specialized encryption functions for FIRS submissions
following their security protocols and standards.
"""

import base64
import json
import logging
import os
import uuid
from datetime import datetime
from typing import Dict, Any, Tuple, Optional, Union

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import load_pem_public_key
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

logger = logging.getLogger(__name__)

class FIRSEncryptionUtility:
    """Provides FIRS-specific encryption capabilities for secure data transmission."""
    
    def __init__(self, public_key_path: Optional[str] = None):
        """
        Initialize the FIRS encryption utility.
        
        Args:
            public_key_path: Path to FIRS public key for encryption
        """
        self.public_key_path = public_key_path
        self._public_key = None
        
    @property
    def public_key(self):
        """Lazily load public key."""
        if self._public_key is None and self.public_key_path:
            try:
                with open(self.public_key_path, 'rb') as key_file:
                    self._public_key = load_pem_public_key(
                        key_file.read(),
                        backend=default_backend()
                    )
            except Exception as e:
                logger.error(f"Failed to load FIRS public key: {str(e)}")
                raise ValueError(f"Could not load FIRS public key: {str(e)}")
        return self._public_key
    
    def encrypt_firs_payload(self, payload: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """
        Encrypt a payload for FIRS submission using their required format.
        
        Args:
            payload: The payload to encrypt
            
        Returns:
            Tuple of (encrypted_payload, encryption_metadata)
        """
        if not payload:
            raise ValueError("No payload provided for encryption")
            
        # Generate a random AES key
        aes_key = os.urandom(32)  # 256 bits for AES-256
        iv = os.urandom(16)       # 128 bits for GCM mode
        
        # Convert payload to canonical JSON for consistency
        canonical_payload = json.dumps(payload, sort_keys=True)
        payload_bytes = canonical_payload.encode('utf-8')
        
        # Encrypt payload with AES
        cipher = Cipher(
            algorithms.AES(aes_key),
            modes.GCM(iv),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(payload_bytes) + encryptor.finalize()
        tag = encryptor.tag
        
        # Encrypt the AES key with FIRS public key
        if not self.public_key:
            raise ValueError("FIRS public key is not available for encryption")
            
        encrypted_aes_key = self.public_key.encrypt(
            aes_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        
        # Create the encrypted package structure according to FIRS requirements
        encrypted_package = {
            "header": {
                "algorithm": "RSA-OAEP-AES-256-GCM",
                "encryption_id": str(uuid.uuid4()),
                "timestamp": datetime.utcnow().isoformat(),
                "version": "1.0",
                "sender_info": {
                    "system": "TaxPoynt-eInvoice"
                }
            },
            "encrypted_key": base64.b64encode(encrypted_aes_key).decode('utf-8'),
            "iv": base64.b64encode(iv).decode('utf-8'),
            "ciphertext": base64.b64encode(ciphertext).decode('utf-8'),
            "tag": base64.b64encode(tag).decode('utf-8')
        }
        
        # Metadata for tracking and auditing
        encryption_metadata = {
            "encryption_id": encrypted_package["header"]["encryption_id"],
            "timestamp": encrypted_package["header"]["timestamp"],
            "algorithm": encrypted_package["header"]["algorithm"],
            "is_encrypted": True,
            "encrypted_for": "FIRS",
            "public_key_id": self.public_key_path if self.public_key_path else "default_firs_key"
        }
        
        # Return the full serialized package and metadata
        return json.dumps(encrypted_package), encryption_metadata
        
    def create_secure_header(self, payload_hash: str, certificate_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a secure header for FIRS transmissions with all required metadata.
        
        Args:
            payload_hash: SHA-256 hash of the canonical payload
            certificate_id: Optional ID of the certificate used for signing
            
        Returns:
            Dict containing the secure header
        """
        header = {
            "message_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0",
            "payload_hash": payload_hash,
            "content_type": "application/json",
            "security": {
                "encryption_method": "RSA-OAEP-AES-256-GCM",
                "hash_algorithm": "SHA-256"
            }
        }
        
        if certificate_id:
            header["security"]["certificate_id"] = certificate_id
            
        return header
