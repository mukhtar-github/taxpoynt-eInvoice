"""
Certificate-based digital signing utilities for TaxPoynt eInvoice system.

This module provides functions for:
- Document signing using stored certificates
- Digital signature validation
- Working with X.509 certificates for signing and verification
- Hash calculation for documents
"""

import base64
import hashlib
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, Union, List
from uuid import UUID

from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa, utils, ed25519
from cryptography.exceptions import InvalidSignature

logger = logging.getLogger(__name__)


def sign_document_with_certificate(document_data: Dict[str, Any], certificate_data: str, private_key_data: str) -> str:
    """
    Sign a document using a certificate and private key.
    
    Args:
        document_data: Document to sign
        certificate_data: PEM-encoded certificate
        private_key_data: PEM-encoded private key
        
    Returns:
        Base64 encoded signature
    """
    try:
        # Load the private key
        private_key = serialization.load_pem_private_key(
            private_key_data.encode() if isinstance(private_key_data, str) else private_key_data,
            password=None,
            backend=default_backend()
        )
        
        # Create a canonical representation of the document
        canonical_data = canonicalize_document(document_data)
        
        # Calculate document hash
        document_hash = hashlib.sha256(canonical_data.encode()).digest()
        
        # Sign the hash
        if isinstance(private_key, rsa.RSAPrivateKey):
            signature = private_key.sign(
                document_hash,
                padding.PKCS1v15(),
                hashes.SHA256()
            )
        elif isinstance(private_key, ed25519.Ed25519PrivateKey):
            signature = private_key.sign(document_hash)
        else:
            raise ValueError("Unsupported private key type")
            
        # Return base64 encoded signature
        return base64.b64encode(signature).decode()
        
    except Exception as e:
        logger.error(f"Error signing document: {str(e)}")
        raise ValueError(f"Failed to sign document: {str(e)}")


def verify_document_signature(
    document_data: Dict[str, Any], 
    signature: str, 
    certificate_data: str
) -> bool:
    """
    Verify a document signature using a certificate.
    
    Args:
        document_data: Document to verify
        signature: Base64 encoded signature
        certificate_data: PEM-encoded certificate
        
    Returns:
        True if signature is valid, False otherwise
    """
    try:
        # Load the certificate
        cert = x509.load_pem_x509_certificate(
            certificate_data.encode() if isinstance(certificate_data, str) else certificate_data,
            default_backend()
        )
        
        # Get public key from certificate
        public_key = cert.public_key()
        
        # Create a canonical representation of the document
        canonical_data = canonicalize_document(document_data)
        
        # Calculate document hash
        document_hash = hashlib.sha256(canonical_data.encode()).digest()
        
        # Decode the signature
        signature_bytes = base64.b64decode(signature)
        
        # Verify the signature
        if isinstance(public_key, rsa.RSAPublicKey):
            public_key.verify(
                signature_bytes,
                document_hash,
                padding.PKCS1v15(),
                hashes.SHA256()
            )
        elif isinstance(public_key, ed25519.Ed25519PublicKey):
            public_key.verify(signature_bytes, document_hash)
        else:
            raise ValueError("Unsupported public key type")
            
        return True
        
    except InvalidSignature:
        return False
    except Exception as e:
        logger.error(f"Error verifying signature: {str(e)}")
        return False


def canonicalize_document(document_data: Dict[str, Any]) -> str:
    """
    Create a canonical representation of a document for signing/verification.
    
    This ensures consistent byte representation regardless of whitespace or key order.
    
    Args:
        document_data: Document data
        
    Returns:
        Canonical JSON string
    """
    # Create a deep copy of the document to avoid modifying the original
    doc_copy = json.loads(json.dumps(document_data))
    
    # Remove any existing signature fields to avoid cycles
    if "signature" in doc_copy:
        del doc_copy["signature"]
    if "digitalSignature" in doc_copy:
        del doc_copy["digitalSignature"]
    
    # Sort keys and remove whitespace for consistent representation
    return json.dumps(doc_copy, sort_keys=True, separators=(',', ':'))


def create_document_signature_block(
    document_data: Dict[str, Any],
    certificate_id: Union[UUID, str],
    signature: str
) -> Dict[str, Any]:
    """
    Create a signature block to add to a document.
    
    Args:
        document_data: Document that was signed
        certificate_id: ID of the certificate used for signing
        signature: Base64 encoded signature
        
    Returns:
        Signature block dictionary
    """
    return {
        "signature": signature,
        "signedAt": datetime.utcnow().isoformat(),
        "certificateId": str(certificate_id),
        "algorithm": "SHA256withRSA",
        "canonicalizationMethod": "json-canonicalization",
        "documentHash": hashlib.sha256(canonicalize_document(document_data).encode()).hexdigest()
    }


def extract_certificate_info(certificate_data: str) -> Dict[str, Any]:
    """
    Extract information from a certificate.
    
    Args:
        certificate_data: PEM-encoded certificate
        
    Returns:
        Dictionary of certificate information
    """
    try:
        cert = x509.load_pem_x509_certificate(
            certificate_data.encode() if isinstance(certificate_data, str) else certificate_data,
            default_backend()
        )
        
        # Extract basic information
        info = {
            "subject": str(cert.subject),
            "issuer": str(cert.issuer),
            "notBefore": cert.not_valid_before.isoformat(),
            "notAfter": cert.not_valid_after.isoformat(),
            "serialNumber": cert.serial_number,
            "version": cert.version.value,
            "signatureAlgorithm": cert.signature_algorithm_oid._name
        }
        
        # Extract extensions if present
        extensions = {}
        try:
            for ext in cert.extensions:
                extensions[ext.oid._name] = str(ext.value)
        except:
            pass
            
        info["extensions"] = extensions
        
        return info
        
    except Exception as e:
        logger.error(f"Error extracting certificate info: {str(e)}")
        raise ValueError(f"Failed to extract certificate info: {str(e)}")


def sign_invoice(
    invoice_data: Dict[str, Any], 
    certificate_id: Union[UUID, str],
    certificate_data: str, 
    private_key_data: str
) -> Dict[str, Any]:
    """
    Sign an invoice and add the signature block.
    
    Args:
        invoice_data: Invoice data
        certificate_id: ID of the certificate
        certificate_data: PEM-encoded certificate
        private_key_data: PEM-encoded private key
        
    Returns:
        Invoice with signature block added
    """
    # Create a copy of the invoice
    signed_invoice = invoice_data.copy()
    
    # Generate signature
    signature = sign_document_with_certificate(invoice_data, certificate_data, private_key_data)
    
    # Create and add signature block
    signed_invoice["digitalSignature"] = create_document_signature_block(
        invoice_data,
        certificate_id,
        signature
    )
    
    return signed_invoice


def verify_invoice_signature(invoice_data: Dict[str, Any], certificate_data: str) -> bool:
    """
    Verify an invoice signature.
    
    Args:
        invoice_data: Invoice data with signature block
        certificate_data: PEM-encoded certificate
        
    Returns:
        True if signature is valid, False otherwise
    """
    # Check if invoice has a signature block
    if "digitalSignature" not in invoice_data:
        return False
        
    signature = invoice_data["digitalSignature"].get("signature")
    if not signature:
        return False
    
    # Create a copy for verification (without signature field)
    verify_data = invoice_data.copy()
    del verify_data["digitalSignature"]
    
    # Verify signature
    return verify_document_signature(verify_data, signature, certificate_data)
