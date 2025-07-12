"""
Document Signing Service for TaxPoynt eInvoice - Access Point Provider Functions.

This module provides Access Point Provider (APP) role functionality for document
signing, signature verification, and cryptographic authentication for FIRS submissions.

APP Role Responsibilities:
- Document signing using stored certificates for FIRS compliance
- Digital signature verification for transmitted documents
- Cryptographic authentication for secure FIRS transmission
- Integration with certificate management for APP operations
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
from app.services.firs_si.digital_certificate_service import CertificateService
from app.utils.certificate_signing import (
    sign_document_with_certificate, 
    verify_document_signature,
    canonicalize_document,
    create_document_signature_block
)

logger = logging.getLogger(__name__)


class DocumentSigningService:
    """
    Access Point Provider service for document signing and cryptographic authentication.
    
    This service provides APP role functions for signing documents before FIRS
    transmission, verifying signatures, and ensuring cryptographic compliance
    for secure e-invoicing operations.
    """
    
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
        Sign a document with a certificate for FIRS transmission - APP Role Function.
        
        Provides Access Point Provider digital signing capabilities for documents
        before secure transmission to FIRS, ensuring authentication and integrity.
        
        Args:
            document: Document to sign for FIRS transmission
            certificate_id: Certificate ID to use for signing
            include_timestamp: Whether to include a timestamp in the signature block
            include_metadata: Whether to include certificate metadata
            
        Returns:
            Signed document and signature information ready for FIRS submission
        """
        # Get certificate with decrypted data
        cert_data = self.certificate_service.get_certificate_with_decrypted_data(certificate_id)
        if not cert_data:
            raise ValueError("Certificate not found")
            
        # Verify certificate has a private key
        if not cert_data.get("private_key_data") or not cert_data.get("has_private_key"):
            raise ValueError("Certificate does not have a private key")
            
        # Verify certificate is valid for FIRS transmission
        verification = self.certificate_service.verify_certificate(certificate_id)
        if not verification.valid:
            raise ValueError(f"Certificate is not valid for FIRS transmission: {', '.join(verification.errors)}")
            
        # Sign the document for FIRS compliance
        try:
            # Create a copy of the document without signature block
            document_copy = document.copy()
            if "signature" in document_copy:
                del document_copy["signature"]
            if "digitalSignature" in document_copy:
                del document_copy["digitalSignature"]
                
            # Sign the document with FIRS-compliant cryptographic standards
            signature = sign_document_with_certificate(
                document_copy, 
                cert_data["certificate_data"],
                cert_data["private_key_data"]
            )
            
            # Create the signature block with FIRS metadata
            signature_block = create_document_signature_block(
                document_copy,
                certificate_id,
                signature
            )
            
            # Add APP-specific metadata for FIRS transmission
            signature_block.update({
                "app_provider": "TaxPoynt",
                "firs_compliant": True,
                "signing_timestamp": datetime.utcnow().isoformat(),
                "transmission_ready": True
            })
            
            # Add signature block to document
            signed_document = document_copy.copy()
            signed_document["digitalSignature"] = signature_block
            
            # Update certificate last_used_at timestamp
            certificate = self.certificate_service.get_certificate(certificate_id)
            certificate.last_used_at = datetime.utcnow()
            self.db.add(certificate)
            self.db.commit()
            
            logger.info(f"Signed document for FIRS transmission using certificate {certificate_id}")
            
            return DocumentSignResponse(
                document=signed_document,
                signature=signature,
                signature_metadata=signature_block
            )
            
        except Exception as e:
            logger.error(f"Error signing document for FIRS transmission: {str(e)}")
            raise ValueError(f"Error signing document for FIRS transmission: {str(e)}")
            
    def verify_signature(
        self,
        document: Dict[str, Any],
        certificate_id: Optional[UUID] = None,
        signature: Optional[str] = None
    ) -> SignatureVerificationResponse:
        """
        Verify a document signature for FIRS compliance - APP Role Function.
        
        Provides Access Point Provider signature verification capabilities
        to ensure document integrity and authenticity for FIRS transmissions.
        
        Args:
            document: Signed document to verify
            certificate_id: Optional certificate ID (if not included in document)
            signature: Optional signature (if not included in document)
            
        Returns:
            Verification result with FIRS compliance status
        """
        # Extract signature information from document if not provided
        errors = []
        
        try:
            # Check if document has a signature block
            if "digitalSignature" not in document and not signature:
                return SignatureVerificationResponse(
                    valid=False,
                    errors=["Document does not contain a signature required for FIRS transmission"]
                )
                
            # Extract signature and certificate ID from document if not provided
            if not signature:
                signature = document["digitalSignature"].get("signature")
                if not signature:
                    return SignatureVerificationResponse(
                        valid=False,
                        errors=["Signature not found in document for FIRS verification"]
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
                
            # Verify signature with FIRS compliance checks
            is_valid = verify_document_signature(
                verify_data,
                signature,
                cert_data["certificate_data"]
            )
            
            # Prepare certificate info with FIRS compliance data
            certificate_info = {
                "id": str(certificate.id),
                "name": certificate.name,
                "subject": certificate.subject,
                "issuer": certificate.issuer,
                "status": certificate.status,
                "valid_from": certificate.valid_from.isoformat() if certificate.valid_from else None,
                "valid_to": certificate.valid_to.isoformat() if certificate.valid_to else None,
                "firs_compliant": True  # Mark as FIRS compliant
            }
            
            if not is_valid:
                errors.append("Invalid signature - not suitable for FIRS transmission")
                
            # Check if certificate is valid (not expired, not revoked)
            certificate_verification = self.certificate_service.verify_certificate(certificate_id)
            if not certificate_verification.valid:
                is_valid = False
                errors.extend([f"Certificate validation failed: {error}" for error in certificate_verification.errors])
                
            # Additional FIRS compliance checks
            signature_metadata = document.get("digitalSignature", {})
            if not signature_metadata.get("firs_compliant"):
                errors.append("Signature not marked as FIRS compliant")
                
            logger.info(f"Verified document signature for FIRS compliance: {'VALID' if is_valid else 'INVALID'}")
                
            return SignatureVerificationResponse(
                valid=is_valid,
                errors=errors,
                certificate_info=certificate_info
            )
            
        except Exception as e:
            logger.error(f"Error verifying signature for FIRS compliance: {str(e)}")
            return SignatureVerificationResponse(
                valid=False,
                errors=[f"Error verifying signature for FIRS compliance: {str(e)}"]
            )
    
    def sign_firs_invoice(
        self,
        invoice_data: Dict[str, Any],
        certificate_id: UUID
    ) -> Dict[str, Any]:
        """
        Sign an invoice document specifically for FIRS transmission - APP Role Function.
        
        Provides specialized Access Point Provider signing for invoice documents
        with FIRS-specific metadata and compliance requirements.
        
        Args:
            invoice_data: Invoice data to sign
            certificate_id: Certificate ID to use for signing
            
        Returns:
            Signed invoice ready for FIRS transmission
        """
        try:
            # Add FIRS-specific metadata to invoice
            firs_invoice = invoice_data.copy()
            firs_invoice["firs_metadata"] = {
                "app_provider": "TaxPoynt",
                "transmission_type": "e-invoice",
                "compliance_version": "1.0",
                "prepared_for_firs": True,
                "preparation_timestamp": datetime.utcnow().isoformat()
            }
            
            # Sign the document
            sign_result = self.sign_document(
                document=firs_invoice,
                certificate_id=certificate_id,
                include_timestamp=True,
                include_metadata=True
            )
            
            # Add additional FIRS transmission metadata
            signed_invoice = sign_result.document
            signed_invoice["firs_transmission_ready"] = True
            signed_invoice["app_signed"] = True
            
            logger.info(f"Signed invoice for FIRS transmission: {invoice_data.get('invoice_number', 'Unknown')}")
            
            return signed_invoice
            
        except Exception as e:
            logger.error(f"Error signing invoice for FIRS transmission: {str(e)}")
            raise
    
    def verify_firs_document(
        self,
        document: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Verify a document for FIRS compliance - APP Role Function.
        
        Performs comprehensive Access Point Provider verification of documents
        to ensure they meet FIRS transmission requirements.
        
        Args:
            document: Document to verify
            
        Returns:
            Verification results with FIRS compliance status
        """
        try:
            # Perform signature verification
            verification_result = self.verify_signature(document)
            
            # Additional FIRS compliance checks
            firs_compliance = {
                "signature_valid": verification_result.valid,
                "has_firs_metadata": "firs_metadata" in document,
                "transmission_ready": document.get("firs_transmission_ready", False),
                "app_signed": document.get("app_signed", False),
                "errors": verification_result.errors.copy() if verification_result.errors else []
            }
            
            # Check for required FIRS metadata
            if not firs_compliance["has_firs_metadata"]:
                firs_compliance["errors"].append("Missing FIRS metadata")
            
            if not firs_compliance["transmission_ready"]:
                firs_compliance["errors"].append("Document not marked as transmission ready")
            
            if not firs_compliance["app_signed"]:
                firs_compliance["errors"].append("Document not signed by APP provider")
            
            # Overall compliance status
            firs_compliance["firs_compliant"] = (
                firs_compliance["signature_valid"] and
                firs_compliance["has_firs_metadata"] and
                firs_compliance["transmission_ready"] and
                firs_compliance["app_signed"] and
                len(firs_compliance["errors"]) == 0
            )
            
            logger.info(f"FIRS compliance verification: {'COMPLIANT' if firs_compliance['firs_compliant'] else 'NON-COMPLIANT'}")
            
            return firs_compliance
            
        except Exception as e:
            logger.error(f"Error verifying document for FIRS compliance: {str(e)}")
            return {
                "signature_valid": False,
                "has_firs_metadata": False,
                "transmission_ready": False,
                "app_signed": False,
                "firs_compliant": False,
                "errors": [f"Verification error: {str(e)}"]
            }
            
    def get_document_hash(self, document: Dict[str, Any]) -> str:
        """
        Calculate a hash for a document for FIRS transmission integrity - APP Role Function.
        
        Provides Access Point Provider document hashing for integrity verification
        during FIRS transmission and audit purposes.
        
        Args:
            document: Document to hash
            
        Returns:
            Hexadecimal hash string for FIRS transmission integrity
        """
        canonical_data = canonicalize_document(document)
        document_hash = hashlib.sha256(canonical_data.encode()).hexdigest()
        
        logger.debug(f"Generated document hash for FIRS transmission: {document_hash}")
        
        return document_hash