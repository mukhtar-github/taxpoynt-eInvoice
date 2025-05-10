"""
Document Signing Service for TaxPoynt eInvoice system.

This service provides:
- Document signing using stored certificates
- Signature verification
- Integration with the certificate management system
"""

import base64
import hashlib
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any, Union
from uuid import UUID

from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa, utils, ed25519
from cryptography.exceptions import InvalidSignature
from sqlalchemy.orm import Session

from app.models.certificate import Certificate, CertificateStatus
from app.schemas.certificate import SignatureVerificationResponse, DocumentSignResponse
from app.services.certificate_service import CertificateService
from app.utils.certificate_signing import (
    sign_document_with_certificate, 
    verify_document_signature,
    canonicalize_document,
    create_document_signature_block
)

logger = logging.getLogger(__name__)


class DocumentSigningService:
    """Service for document signing using certificates."""
    
    def __init__(
        self, 
        db: Session,
        certificate_service: CertificateService
    ):
        self.db = db
        self.certificate_service = certificate_service
        
    def sign_document(
        self,
        document: Dict[str, Any],
        certificate_id: UUID,
        include_timestamp: bool = True,
        include_metadata: bool = True
    ) -> DocumentSignResponse:
        """
        Sign a document with a certificate.
        
        Args:
            document: Document to sign
            certificate_id: Certificate ID to use for signing
            include_timestamp: Whether to include a timestamp in the signature block
            include_metadata: Whether to include certificate metadata
            
        Returns:
            Signed document and signature information
        """
        # Get certificate with decrypted data
        cert_data = self.certificate_service.get_certificate_with_decrypted_data(certificate_id)
        if not cert_data:
            raise ValueError("Certificate not found")
            
        # Verify certificate has a private key
        if not cert_data.get("private_key_data") or not cert_data.get("has_private_key"):
            raise ValueError("Certificate does not have a private key")
            
        # Verify certificate is valid
        verification = self.certificate_service.verify_certificate(certificate_id)
        if not verification.valid:
            raise ValueError(f"Certificate is not valid: {', '.join(verification.errors)}")
            
        # Sign the document
        try:
            # Create a copy of the document without signature block
            document_copy = document.copy()
            if "signature" in document_copy:
                del document_copy["signature"]
            if "digitalSignature" in document_copy:
                del document_copy["digitalSignature"]
                
            # Sign the document
            signature = sign_document_with_certificate(
                document_copy, 
                cert_data["certificate_data"],
                cert_data["private_key_data"]
            )
            
            # Create the signature block
            signature_block = create_document_signature_block(
                document_copy,
                certificate_id,
                signature
            )
            
            # Add signature block to document
            signed_document = document_copy.copy()
            signed_document["digitalSignature"] = signature_block
            
            # Update certificate last_used_at timestamp
            certificate = self.certificate_service.get_certificate(certificate_id)
            certificate.last_used_at = datetime.utcnow()
            self.db.add(certificate)
            self.db.commit()
            
            return DocumentSignResponse(
                document=signed_document,
                signature=signature,
                signature_metadata=signature_block
            )
            
        except Exception as e:
            logger.error(f"Error signing document: {str(e)}")
            raise ValueError(f"Error signing document: {str(e)}")
            
    def verify_signature(
        self,
        document: Dict[str, Any],
        certificate_id: Optional[UUID] = None,
        signature: Optional[str] = None
    ) -> SignatureVerificationResponse:
        """
        Verify a document signature.
        
        Args:
            document: Signed document
            certificate_id: Optional certificate ID (if not included in document)
            signature: Optional signature (if not included in document)
            
        Returns:
            Verification result
        """
        # Extract signature information from document if not provided
        errors = []
        
        try:
            # Check if document has a signature block
            if "digitalSignature" not in document and not signature:
                return SignatureVerificationResponse(
                    valid=False,
                    errors=["Document does not contain a signature"]
                )
                
            # Extract signature and certificate ID from document if not provided
            if not signature:
                signature = document["digitalSignature"].get("signature")
                if not signature:
                    return SignatureVerificationResponse(
                        valid=False,
                        errors=["Signature not found in document"]
                    )
                    
            if not certificate_id and "digitalSignature" in document:
                cert_id_str = document["digitalSignature"].get("certificateId")
                if cert_id_str:
                    try:
                        certificate_id = UUID(cert_id_str)
                    except ValueError:
                        return SignatureVerificationResponse(
                            valid=False,
                            errors=["Invalid certificate ID in document"]
                        )
            
            if not certificate_id:
                return SignatureVerificationResponse(
                    valid=False,
                    errors=["Certificate ID not provided or found in document"]
                )
                
            # Get certificate with decrypted data
            cert_data = self.certificate_service.get_certificate_with_decrypted_data(certificate_id)
            if not cert_data:
                return SignatureVerificationResponse(
                    valid=False,
                    errors=["Certificate not found"]
                )
                
            # Get certificate instance for metadata
            certificate = self.certificate_service.get_certificate(certificate_id)
            
            # Create a copy of the document for verification (without signature)
            verify_data = document.copy()
            if "digitalSignature" in verify_data:
                del verify_data["digitalSignature"]
                
            # Verify signature
            is_valid = verify_document_signature(
                verify_data,
                signature,
                cert_data["certificate_data"]
            )
            
            # Prepare certificate info
            certificate_info = {
                "id": str(certificate.id),
                "name": certificate.name,
                "subject": certificate.subject,
                "issuer": certificate.issuer,
                "status": certificate.status,
                "valid_from": certificate.valid_from.isoformat() if certificate.valid_from else None,
                "valid_to": certificate.valid_to.isoformat() if certificate.valid_to else None
            }
            
            if not is_valid:
                errors.append("Invalid signature")
                
            # Check if certificate is valid (not expired, not revoked)
            certificate_verification = self.certificate_service.verify_certificate(certificate_id)
            if not certificate_verification.valid:
                is_valid = False
                errors.extend(certificate_verification.errors)
                
            return SignatureVerificationResponse(
                valid=is_valid,
                errors=errors,
                certificate_info=certificate_info
            )
            
        except Exception as e:
            logger.error(f"Error verifying signature: {str(e)}")
            return SignatureVerificationResponse(
                valid=False,
                errors=[f"Error verifying signature: {str(e)}"]
            )
            
    def get_document_hash(self, document: Dict[str, Any]) -> str:
        """
        Calculate a hash for a document.
        
        Args:
            document: Document to hash
            
        Returns:
            Hexadecimal hash string
        """
        canonical_data = canonicalize_document(document)
        return hashlib.sha256(canonical_data.encode()).hexdigest()
