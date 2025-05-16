"""
Cryptographic signing utilities for FIRS e-Invoice system.

This module provides functions for:
- Digital signature generation and verification
- CSID (Cryptographic Stamp ID) implementation according to FIRS standards
- Secure handling of signing keys
- Signature validation for invoice documents
- Integration with the key management system

CSID Format (Cryptographic Stamp Identifier):
The CSID is a tamper-proof digital signature that verifies the authenticity and
integrity of an e-invoice according to FIRS requirements. It includes:
1. Digital signature of the invoice data
2. Signing timestamp
3. Algorithm identifiers
4. Certificate references
"""

import base64
import hashlib
import json
import os
import uuid
import logging
import secrets
import time
from datetime import datetime, timedelta
from typing import Dict, Tuple, Union, Optional, Any, List
from enum import Enum

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa, utils, ed25519
from cryptography.exceptions import InvalidSignature
from cryptography.x509 import load_pem_x509_certificate
from fastapi import HTTPException

from app.core.config import settings
from app.utils.encryption import extract_keys_from_file, load_public_key
from app.utils.key_management import key_manager, get_key_manager

logger = logging.getLogger(__name__)


class SigningAlgorithm(Enum):
    """Supported signing algorithms."""
    RSA_PSS_SHA256 = "RSA-PSS-SHA256"
    RSA_PKCS1_SHA256 = "RSA-PKCS1-SHA256"
    ED25519 = "ED25519"


class CSIDVersion(Enum):
    """CSID version identifiers."""
    V1_0 = "1.0"
    V2_0 = "2.0"


class CSIDGenerator:
    """
    Cryptographic Stamp ID (CSID) generator for FIRS e-Invoice system.
    
    CSID is a unique cryptographic identifier that provides:
    - Tamper-proof evidence of invoice authenticity
    - Verification of invoice integrity
    - Compliance with FIRS digital signing requirements
    - Audit trail for tax authorities
    
    The CSID implementation follows FIRS guidelines for secure electronic invoicing
    and supports multiple signing algorithms and key types.
    """
    
    def __init__(self, private_key_path: Optional[str] = None, key_password: Optional[str] = None):
        """
        Initialize the CSID Generator with signing keys.
        
        Args:
            private_key_path: Path to the private key for signing (if None, will check config)
            key_password: Password for private key (if None, will check config)
        """
        self.km = get_key_manager()
        self.private_key = None
        self.private_key_path = private_key_path
        self.key_password = key_password
        self.certificate_path = None
        
        # Initialize keys
        self._initialize_keys()
        
    def _initialize_keys(self):
        """
        Initialize the signing keys, creating them if necessary.
        """
        try:
            # Try to load existing keys
            if self.private_key_path and os.path.exists(self.private_key_path):
                self.private_key = self.km.load_private_key(
                    self.private_key_path, 
                    self.key_password
                )
                logger.info(f"Loaded existing signing key from {self.private_key_path}")
            else:
                # Try to find a suitable signing key
                signing_keys = [k for k in self.km.list_keys(key_type="signing") 
                              if k['extension'] == 'key']
                
                if signing_keys:
                    # Use the newest signing key available
                    newest_key = max(signing_keys, key=lambda k: k.get('timestamp', ''))
                    self.private_key_path = newest_key['path']
                    self.private_key = self.km.load_private_key(
                        self.private_key_path,
                        self.key_password
                    )
                    logger.info(f"Loaded existing signing key from {self.private_key_path}")
                else:
                    # Generate new signing keys
                    self._generate_new_keys()
        except Exception as e:
            logger.warning(f"Could not initialize signing keys: {str(e)}")
            # In development mode, generate a temporary key for testing
            if hasattr(settings, 'ENVIRONMENT') and settings.ENVIRONMENT == "development":
                self.private_key = rsa.generate_private_key(
                    public_exponent=65537,
                    key_size=2048,
                    backend=default_backend()
                )
                logger.info("Generated temporary in-memory signing key for development")
            else:
                raise ValueError(f"Failed to initialize signing keys: {str(e)}")
    
    def _generate_new_keys(self):
        """
        Generate new signing keys and certificates.
        """
        logger.info("Generating new signing keys for CSID...")
        
        # Generate RSA key pair
        self.private_key_path, public_key_path = self.km.generate_key_pair(
            key_type="signing",
            algorithm="rsa-2048",
            key_name=f"signing_rsa-2048_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        )
        
        # Load the private key
        self.private_key = self.km.load_private_key(self.private_key_path, self.key_password)
        
        # Generate a self-signed certificate for the key
        subject_name = {
            "country": "NG",
            "organization": "TaxPoynt eInvoice",
            "common_name": f"CSID Signing Key {datetime.now().strftime('%Y-%m-%d')}"
        }
        
        self.certificate_path = self.km.generate_certificate(
            private_key_path=self.private_key_path,
            subject_name=subject_name,
            valid_days=365,
            cert_name=f"signing_cert_{datetime.now().strftime('%Y%m%d%H%M%S')}.crt"
        )
        
        logger.info(f"Generated new signing key at {self.private_key_path}")
        logger.info(f"Generated self-signed certificate at {self.certificate_path}")
    
    def generate_csid(self, 
                      invoice_data: Dict, 
                      algorithm: Union[str, SigningAlgorithm] = SigningAlgorithm.RSA_PSS_SHA256,
                      version: Union[str, CSIDVersion] = CSIDVersion.V2_0
                     ) -> str:
        """
        Generate a Cryptographic Stamp ID for an invoice according to FIRS specifications.
        
        Args:
            invoice_data: Invoice data to stamp
            algorithm: Signing algorithm to use
            version: CSID version to generate
            
        Returns:
            Base64 encoded CSID
        """
        # Convert enum to string if needed
        if isinstance(algorithm, SigningAlgorithm):
            algorithm = algorithm.value
            
        if isinstance(version, CSIDVersion):
            version = version.value
        
        # 1. Create a canonical representation of the invoice data
        canonical_data = self._canonicalize_invoice(invoice_data)
        
        # 2. Generate a SHA-256 hash of the canonical data
        data_hash = hashlib.sha256(canonical_data.encode()).digest()
        
        # 3. Sign the hash with the private key using the specified algorithm
        if algorithm == SigningAlgorithm.RSA_PSS_SHA256.value:
            signature = self.private_key.sign(
                data_hash,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                utils.Prehashed(hashes.SHA256())
            )
        elif algorithm == SigningAlgorithm.RSA_PKCS1_SHA256.value:
            signature = self.private_key.sign(
                data_hash,
                padding.PKCS1v15(),
                utils.Prehashed(hashes.SHA256())
            )
        elif algorithm == SigningAlgorithm.ED25519.value:
            # ED25519 keys are handled differently
            if not isinstance(self.private_key, ed25519.Ed25519PrivateKey):
                raise ValueError("ED25519 algorithm specified but key is not ED25519")
            signature = self.private_key.sign(data_hash)
        else:
            raise ValueError(f"Unsupported signing algorithm: {algorithm}")
        
        # 4. Encode signature as base64
        signature_b64 = base64.b64encode(signature).decode('utf-8')
        
        # 5. Prepare CSID metadata
        timestamp = datetime.utcnow().isoformat()
        signature_id = str(uuid.uuid4())
        
        # 6. Create CSID data structure
        # For V1.0 (legacy format)
        if version == CSIDVersion.V1_0.value:
            csid_data = {
                "csid": signature_b64,
                "timestamp": int(time.time()),
                "algorithm": algorithm
            }
        # For V2.0 (enhanced format with FIRS compliance)
        else:  
            csid_data = {
                "version": version,
                "signature_value": signature_b64,
                "signature_id": signature_id,
                "timestamp": timestamp,
                "algorithm": algorithm,
                "key_info": {
                    "key_id": os.path.basename(self.private_key_path) if self.private_key_path else "temporary-key",
                    "certificate": os.path.basename(self.certificate_path) if self.certificate_path else None
                },
                "invoice_ref": {
                    "id": invoice_data.get("id", invoice_data.get("invoice_number", "")),
                    "hash_alg": "SHA-256",
                    "hash_value": base64.b64encode(data_hash).decode('utf-8')
                }
            }
        
        # 7. Encode the complete CSID
        return base64.b64encode(json.dumps(csid_data).encode()).decode('utf-8')
        
    def verify_csid(
        self,
        invoice_data: Dict,
        csid: str,
        public_key_path: Optional[str] = None
    ) -> Tuple[bool, str, Dict]:
        """
        Verify a CSID against invoice data.
        
        Args:
            invoice_data: Invoice data to verify
            csid: CSID to verify
            public_key_path: Path to public key for verification
            
        Returns:
            Tuple of (is_valid, message, verification_details)
        """
        verification_details = {
            "algorithm": None,
            "timestamp": None,
            "version": None,
            "signature_id": None,
            "key_info": None,
        }
        
        try:
            # 1. Decode the CSID
            csid_data = json.loads(base64.b64decode(csid).decode('utf-8'))
            
            # Determine CSID version
            version = csid_data.get("version", "1.0")
            verification_details["version"] = version
            
            # Extract data based on version
            if version == "1.0":
                signature = base64.b64decode(csid_data["csid"])
                algorithm = csid_data["algorithm"]
                timestamp = datetime.fromtimestamp(csid_data["timestamp"]).isoformat() \
                    if isinstance(csid_data["timestamp"], (int, float)) else csid_data["timestamp"]
            else:  # version 2.0+
                signature = base64.b64decode(csid_data["signature_value"])
                algorithm = csid_data["algorithm"]
                timestamp = csid_data["timestamp"]
                verification_details["signature_id"] = csid_data.get("signature_id")
                verification_details["key_info"] = csid_data.get("key_info")
            
            verification_details["algorithm"] = algorithm
            verification_details["timestamp"] = timestamp
            
            # 2. Load the verification key
            if public_key_path:
                public_key = self.km.load_public_key(public_key_path)
            else:
                # Try to find corresponding public key if key_info is available
                if version != "1.0" and csid_data.get("key_info", {}).get("key_id"):
                    key_id = csid_data["key_info"]["key_id"]
                    keys = self.km.list_keys()
                    matching_keys = [k for k in keys if k["filename"].startswith(key_id.replace(".key", ""))]
                    
                    if matching_keys:
                        for key in matching_keys:
                            if key["extension"] == "pub":
                                public_key = self.km.load_public_key(key["path"])
                                break
                        else:
                            # If no .pub file, try to extract from certificate
                            for key in matching_keys:
                                if key["extension"] == "crt":
                                    cert = self.km.load_certificate(key["path"])
                                    public_key = cert.public_key()
                                    break
                            else:
                                raise ValueError(f"Could not find public key for key_id: {key_id}")
                    else:
                        raise ValueError(f"Could not find key matching id: {key_id}")
                else:
                    # Fallback to default verification key or raise error
                    raise ValueError("No public key specified and key_info not available in CSID")
            
            # 3. Create canonical data and hash
            canonical_data = self._canonicalize_invoice(invoice_data)
            data_hash = hashlib.sha256(canonical_data.encode()).digest()
            
            # 4. Verify the signature based on algorithm
            if algorithm == SigningAlgorithm.RSA_PSS_SHA256.value:
                public_key.verify(
                    signature,
                    data_hash,
                    padding.PSS(
                        mgf=padding.MGF1(hashes.SHA256()),
                        salt_length=padding.PSS.MAX_LENGTH
                    ),
                    utils.Prehashed(hashes.SHA256())
                )
            elif algorithm == SigningAlgorithm.RSA_PKCS1_SHA256.value:
                public_key.verify(
                    signature,
                    data_hash,
                    padding.PKCS1v15(),
                    utils.Prehashed(hashes.SHA256())
                )
            elif algorithm == SigningAlgorithm.ED25519.value:
                if not isinstance(public_key, ed25519.Ed25519PublicKey):
                    raise ValueError("ED25519 algorithm specified but key is not ED25519")
                public_key.verify(signature, data_hash)
            else:
                raise ValueError(f"Unsupported verification algorithm: {algorithm}")
            
            # 5. For V2.0, verify the hash in the CSID matches our calculated hash
            if version != "1.0" and csid_data.get("invoice_ref", {}).get("hash_value"):
                stored_hash = base64.b64decode(csid_data["invoice_ref"]["hash_value"])
                if stored_hash != data_hash:
                    return False, "Invoice data hash does not match the one in CSID", verification_details
            
            return True, "CSID verification successful", verification_details
            
        except InvalidSignature:
            return False, "Invalid signature", verification_details
        except Exception as e:
            logger.error(f"Error verifying CSID: {str(e)}")
            return False, f"Verification error: {str(e)}", verification_details
    
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
        data_copy.pop('digital_signature', None)
        
        # Sort keys and ensure consistent formatting
        return json.dumps(data_copy, sort_keys=True, ensure_ascii=False, separators=(',', ':'))


def verify_csid(invoice_data: Dict, csid: str, public_key_path: Optional[str] = None) -> Tuple[bool, str, Dict]:
    """
    Verify the CSID signature of an invoice.
    
    Args:
        invoice_data: Invoice data
        csid: CSID signature to verify
        public_key_path: Path to the public key for verification
        
    Returns:
        Tuple of (is_valid, message, verification_details)
    """
    # Use the CSIDGenerator's verify_csid method for comprehensive verification
    csid_gen = csid_generator
    return csid_gen.verify_csid(invoice_data, csid, public_key_path)


def sign_invoice(invoice_data: Dict, version: Union[str, CSIDVersion] = CSIDVersion.V2_0,
              algorithm: Union[str, SigningAlgorithm] = SigningAlgorithm.RSA_PSS_SHA256) -> Dict:
    """
    Sign an invoice with CSID and return the updated invoice data.
    
    Args:
        invoice_data: Original invoice data
        version: CSID version to use
        algorithm: Signing algorithm to use
        
    Returns:
        Invoice data with CSID added
    """
    # Get CSID generator instance
    gen = csid_generator
    
    # Generate CSID
    csid = gen.generate_csid(invoice_data, algorithm=algorithm, version=version)
    
    # Convert enum to string if needed
    if isinstance(algorithm, SigningAlgorithm):
        algorithm_str = algorithm.value
    else:
        algorithm_str = algorithm
        
    if isinstance(version, CSIDVersion):
        version_str = version.value
    else:
        version_str = version
    
    # Create a copy of the invoice to avoid modifying the original
    signed_invoice = invoice_data.copy()
    
    # Add cryptographic stamp with metadata
    signed_invoice['cryptographic_stamp'] = {
        'csid': csid,
        'timestamp': datetime.utcnow().isoformat(),
        'algorithm': algorithm_str,
        'version': version_str,
        'signature_id': str(uuid.uuid4()),
        'key_info': {
            'key_id': os.path.basename(gen.private_key_path) if gen.private_key_path else "temporary-key",
            'certificate': os.path.basename(gen.certificate_path) if gen.certificate_path else None
        }
    }
    
    return signed_invoice


# Create singleton instance for easy import
csid_generator = CSIDGenerator()

