"""
Cryptographic signing utilities for FIRS e-Invoice system.

This module provides functions for:
- Digital signature generation and verification
- CSID (Cryptographic Stamp ID) implementation
- Secure handling of signing keys
- Signature validation for invoice documents
"""

import base64
import hashlib
import json
import os
import uuid
from datetime import datetime
from typing import Dict, Tuple, Union, Optional, Any, List

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa, utils
from cryptography.exceptions import InvalidSignature
from fastapi import HTTPException

from app.core.config import settings
from app.utils.encryption import extract_keys_from_file, load_public_key


class CSIDGenerator:
    """
    Cryptographic Stamp ID (CSID) generator for FIRS e-Invoice system.
    
    CSID is a unique cryptographic identifier that provides:
    - Tamper-proof evidence of invoice authenticity
    - Verification of invoice integrity
    - Compliance with FIRS digital signing requirements
    """
    
    def __init__(self, private_key_path: Optional[str] = None):
        """
        Initialize the CSID Generator with signing keys.
        
        Args:
            private_key_path: Path to the private key for signing (if None, will check config)
        """
        self.private_key = self._load_private_key(private_key_path)
        
    def _load_private_key(self, private_key_path: Optional[str]) -> rsa.RSAPrivateKey:
        """
        Load the RSA private key for signing.
        
        Args:
            private_key_path: Path to private key file
            
        Returns:
            RSA private key object
        """
        try:
            path = private_key_path or settings.SIGNING_PRIVATE_KEY_PATH
            
            if not path or not os.path.exists(path):
                raise ValueError("Private key file not found")
                
            with open(path, "rb") as key_file:
                private_key = serialization.load_pem_private_key(
                    key_file.read(),
                    password=settings.SIGNING_KEY_PASSWORD.encode() if settings.SIGNING_KEY_PASSWORD else None,
                    backend=default_backend()
                )
                
            if not isinstance(private_key, rsa.RSAPrivateKey):
                raise TypeError("The loaded key is not an RSA private key")
                
            return private_key
            
        except Exception as e:
            # In development mode, generate a temporary key for testing
            if settings.ENVIRONMENT == "development":
                return rsa.generate_private_key(
                    public_exponent=65537,
                    key_size=2048,
                    backend=default_backend()
                )
            else:
                raise HTTPException(
                    status_code=500, 
                    detail=f"Failed to load private key: {str(e)}"
                )
    
    def generate_csid(self, invoice_data: Dict) -> str:
        """
        Generate a Cryptographic Stamp ID for an invoice.
        
        Args:
            invoice_data: Invoice data to stamp
            
        Returns:
            Base64 encoded CSID
        """
        # 1. Create a canonical representation of the invoice data
        canonical_data = self._canonicalize_invoice(invoice_data)
        
        # 2. Generate a SHA-256 hash of the canonical data
        data_hash = hashlib.sha256(canonical_data.encode()).digest()
        
        # 3. Sign the hash with the private key
        signature = self.private_key.sign(
            data_hash,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            utils.Prehashed(hashes.SHA256())
        )
        
        # 4. Encode signature as base64
        csid = base64.b64encode(signature).decode('utf-8')
        
        # 5. Add to invoice metadata
        timestamp = int(datetime.utcnow().timestamp())
        csid_data = {
            "csid": csid,
            "timestamp": timestamp,
            "algorithm": "RSA-PSS-SHA256"
        }
        
        return base64.b64encode(json.dumps(csid_data).encode()).decode('utf-8')
    
    def _canonicalize_invoice(self, invoice_data: Dict) -> str:
        """
        Create a canonical JSON representation of invoice data.
        
        This ensures consistent hashing regardless of field order.
        
        Args:
            invoice_data: Invoice data dictionary
            
        Returns:
            Canonical JSON string
        """
        # Create a copy of the invoice data without any signature fields
        data_copy = invoice_data.copy()
        
        # Remove any existing signature or CSID fields
        data_copy.pop('signature', None)
        data_copy.pop('csid', None)
        data_copy.pop('cryptographic_stamp', None)
        
        # Sort keys and ensure consistent formatting
        return json.dumps(data_copy, sort_keys=True, ensure_ascii=False, separators=(',', ':'))


def verify_csid(invoice_data: Dict, csid: str, public_key_path: Optional[str] = None) -> bool:
    """
    Verify the CSID signature of an invoice.
    
    Args:
        invoice_data: Invoice data
        csid: CSID signature to verify
        public_key_path: Path to the public key for verification
        
    Returns:
        True if signature is valid, False otherwise
    """
    try:
        # 1. Decode the CSID data
        csid_data = json.loads(base64.b64decode(csid).decode('utf-8'))
        signature = base64.b64decode(csid_data["csid"])
        
        # 2. Load public key
        public_key = _load_verification_key(public_key_path)
        
        # 3. Create canonical representation and hash
        canonical_data = _canonicalize_invoice_for_verification(invoice_data)
        data_hash = hashlib.sha256(canonical_data.encode()).digest()
        
        # 4. Verify signature
        public_key.verify(
            signature,
            data_hash,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            utils.Prehashed(hashes.SHA256())
        )
        
        return True
        
    except InvalidSignature:
        return False
    except Exception as e:
        # Log the error but return False for verification
        print(f"Error verifying CSID: {str(e)}")
        return False


def _load_verification_key(public_key_path: Optional[str] = None) -> rsa.RSAPublicKey:
    """
    Load the public key for CSID verification.
    
    Args:
        public_key_path: Path to public key file
        
    Returns:
        RSA public key object
    """
    try:
        path = public_key_path or settings.VERIFICATION_PUBLIC_KEY_PATH
        
        if not path or not os.path.exists(path):
            raise ValueError("Public key file not found")
            
        with open(path, "rb") as key_file:
            public_key = serialization.load_pem_public_key(
                key_file.read(),
                backend=default_backend()
            )
            
        if not isinstance(public_key, rsa.RSAPublicKey):
            raise TypeError("The loaded key is not an RSA public key")
            
        return public_key
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to load verification key: {str(e)}"
        )


def _canonicalize_invoice_for_verification(invoice_data: Dict) -> str:
    """
    Create a canonical JSON representation of invoice data for verification.
    
    Args:
        invoice_data: Invoice data dictionary
        
    Returns:
        Canonical JSON string
    """
    # Create a copy of the invoice data without any signature fields
    data_copy = invoice_data.copy()
    
    # Remove any existing signature or CSID fields
    data_copy.pop('signature', None)
    data_copy.pop('csid', None)
    data_copy.pop('cryptographic_stamp', None)
    
    # Sort keys and ensure consistent formatting
    return json.dumps(data_copy, sort_keys=True, ensure_ascii=False, separators=(',', ':'))


def sign_invoice(invoice_data: Dict) -> Dict:
    """
    Sign an invoice with CSID and return the updated invoice data.
    
    Args:
        invoice_data: Original invoice data
        
    Returns:
        Invoice data with CSID added
    """
    csid_generator = CSIDGenerator()
    csid = csid_generator.generate_csid(invoice_data)
    
    # Create a copy of the invoice to avoid modifying the original
    signed_invoice = invoice_data.copy()
    signed_invoice['cryptographic_stamp'] = {
        'csid': csid,
        'timestamp': datetime.utcnow().isoformat(),
        'algorithm': 'RSA-PSS-SHA256',
        'version': '1.0'
    }
    
    return signed_invoice


# Create singleton instance for easy import
csid_generator = CSIDGenerator()

