"""
Certificate Service for TaxPoynt eInvoice system.

This service provides:
- Secure certificate storage and retrieval
- Certificate encryption/decryption
- Certificate validation
- Certificate metadata extraction
"""

import base64
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any, Union
from uuid import UUID

from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.x509.oid import NameOID
from sqlalchemy.orm import Session

from app.models.certificate import Certificate, CertificateRevocation, CertificateType, CertificateStatus
from app.schemas.certificate import CertificateCreate, CertificateUpdate, CertificateVerification
from app.services.key_service import KeyManagementService
from app.utils.encryption import encrypt_field, decrypt_field

logger = logging.getLogger(__name__)


class CertificateService:
    """Service for managing digital certificates."""
    
    def __init__(
        self, 
        db: Session,
        key_service: KeyManagementService
    ):
        self.db = db
        self.key_service = key_service
        
    def extract_certificate_metadata(self, certificate_data: str) -> Dict[str, Any]:
        """
        Extract metadata from a PEM encoded certificate.
        
        Args:
            certificate_data: PEM encoded certificate
            
        Returns:
            Dictionary of certificate metadata
        """
        try:
            # Parse the certificate
            cert = x509.load_pem_x509_certificate(
                certificate_data.encode(), 
                default_backend()
            )
            
            # Extract issuer and subject
            issuer = cert.issuer.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value
            subject = cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value
            
            # Get serial number and fingerprint
            serial_number = format(cert.serial_number, 'x')
            fingerprint = cert.fingerprint(hashes.SHA256()).hex()
            
            # Get validity dates
            valid_from = cert.not_valid_before
            valid_to = cert.not_valid_after
            
            return {
                "issuer": issuer,
                "subject": subject,
                "serial_number": serial_number,
                "fingerprint": fingerprint,
                "valid_from": valid_from,
                "valid_to": valid_to
            }
        except Exception as e:
            logger.error(f"Error extracting certificate metadata: {str(e)}")
            return {
                "issuer": None,
                "subject": None,
                "serial_number": None,
                "fingerprint": None,
                "valid_from": None,
                "valid_to": None
            }
    
    def create_certificate(self, certificate_in: CertificateCreate, user_id: UUID) -> Certificate:
        """
        Create a new certificate with encrypted data.
        
        Args:
            certificate_in: Certificate creation data
            user_id: ID of the user creating the certificate
            
        Returns:
            Created certificate
        """
        # Extract metadata from certificate if not provided
        metadata = {}
        if certificate_in.certificate_data:
            metadata = self.extract_certificate_metadata(certificate_in.certificate_data)
        
        # Use provided metadata where available, fallback to extracted
        issuer = certificate_in.issuer or metadata.get("issuer")
        subject = certificate_in.subject or metadata.get("subject")
        serial_number = certificate_in.serial_number or metadata.get("serial_number")
        fingerprint = certificate_in.fingerprint or metadata.get("fingerprint")
        valid_from = certificate_in.valid_from or metadata.get("valid_from")
        valid_to = certificate_in.valid_to or metadata.get("valid_to")
        
        # Get current key for encryption
        key_id = self.key_service.get_current_key_id()
        
        # Encrypt certificate data
        encrypted_cert_data = encrypt_field(certificate_in.certificate_data)
        
        # Encrypt private key if provided
        encrypted_private_key = None
        has_private_key = False
        if certificate_in.private_key_data:
            encrypted_private_key = encrypt_field(certificate_in.private_key_data)
            has_private_key = True
        
        # Create certificate object
        certificate = Certificate(
            organization_id=certificate_in.organization_id,
            name=certificate_in.name,
            description=certificate_in.description,
            certificate_type=certificate_in.certificate_type,
            issuer=issuer,
            subject=subject,
            serial_number=serial_number,
            fingerprint=fingerprint,
            valid_from=valid_from,
            valid_to=valid_to,
            certificate_data=encrypted_cert_data,
            is_encrypted=True,
            encryption_key_id=key_id,
            private_key_data=encrypted_private_key,
            has_private_key=has_private_key,
            created_by=user_id,
            tags=certificate_in.tags
        )
        
        # Save to database
        self.db.add(certificate)
        self.db.commit()
        self.db.refresh(certificate)
        
        return certificate
    
    def get_certificate(self, certificate_id: UUID) -> Optional[Certificate]:
        """
        Get a certificate by ID.
        
        Args:
            certificate_id: ID of the certificate
            
        Returns:
            Certificate or None if not found
        """
        return self.db.query(Certificate).filter(Certificate.id == certificate_id).first()
    
    def get_certificates(
        self, 
        organization_id: Optional[UUID] = None,
        skip: int = 0, 
        limit: int = 100
    ) -> List[Certificate]:
        """
        Get certificates with optional filtering.
        
        Args:
            organization_id: Optional organization ID filter
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of certificates
        """
        query = self.db.query(Certificate)
        
        if organization_id:
            query = query.filter(Certificate.organization_id == organization_id)
            
        return query.offset(skip).limit(limit).all()
    
    def update_certificate(
        self, 
        certificate_id: UUID,
        certificate_in: CertificateUpdate,
        user_id: UUID
    ) -> Optional[Certificate]:
        """
        Update a certificate.
        
        Args:
            certificate_id: ID of the certificate to update
            certificate_in: Update data
            user_id: ID of the user making the update
            
        Returns:
            Updated certificate or None if not found
        """
        certificate = self.get_certificate(certificate_id)
        if not certificate:
            return None
        
        update_data = certificate_in.dict(exclude_unset=True)
        
        # Apply updates
        for field, value in update_data.items():
            setattr(certificate, field, value)
            
        certificate.updated_at = datetime.utcnow()
        
        self.db.add(certificate)
        self.db.commit()
        self.db.refresh(certificate)
        
        return certificate
    
    def revoke_certificate(
        self,
        certificate_id: UUID,
        reason: str,
        user_id: UUID
    ) -> bool:
        """
        Revoke a certificate.
        
        Args:
            certificate_id: ID of the certificate to revoke
            reason: Reason for revocation
            user_id: ID of the user revoking the certificate
            
        Returns:
            True if certificate was revoked, False otherwise
        """
        certificate = self.get_certificate(certificate_id)
        if not certificate:
            return False
        
        # Update certificate status
        certificate.status = CertificateStatus.REVOKED
        
        # Create revocation record
        revocation = CertificateRevocation(
            certificate_id=certificate_id,
            revoked_by=user_id,
            reason=reason
        )
        
        self.db.add(certificate)
        self.db.add(revocation)
        self.db.commit()
        
        return True
    
    def delete_certificate(self, certificate_id: UUID) -> bool:
        """
        Delete a certificate.
        
        Args:
            certificate_id: ID of the certificate to delete
            
        Returns:
            True if certificate was deleted, False otherwise
        """
        certificate = self.get_certificate(certificate_id)
        if not certificate:
            return False
        
        self.db.delete(certificate)
        self.db.commit()
        
        return True
    
    def verify_certificate(self, certificate_id: UUID) -> CertificateVerification:
        """
        Verify a certificate's validity.
        
        Args:
            certificate_id: ID of the certificate to verify
            
        Returns:
            Verification result
        """
        certificate = self.get_certificate(certificate_id)
        if not certificate:
            return CertificateVerification(
                valid=False,
                errors=["Certificate not found"]
            )
        
        errors = []
        warnings = []
        details = {
            "subject": certificate.subject,
            "issuer": certificate.issuer,
            "status": certificate.status
        }
        
        # Check certificate status
        if certificate.status == CertificateStatus.REVOKED:
            errors.append("Certificate has been revoked")
            
        elif certificate.status == CertificateStatus.EXPIRED:
            errors.append("Certificate has expired")
            
        # Check expiration
        now = datetime.utcnow()
        if certificate.valid_to and certificate.valid_to < now:
            errors.append(f"Certificate expired on {certificate.valid_to}")
            details["expired"] = True
            details["days_expired"] = (now - certificate.valid_to).days
            
        # Check if certificate is valid but approaching expiration
        elif certificate.valid_to:
            days_remaining = (certificate.valid_to - now).days
            details["days_remaining"] = days_remaining
            
            if days_remaining < 30:
                warnings.append(f"Certificate will expire in {days_remaining} days")
        
        # Determine overall validity
        valid = len(errors) == 0
        
        return CertificateVerification(
            valid=valid,
            errors=errors,
            warnings=warnings,
            details=details
        )
    
    def decrypt_certificate_data(self, certificate_id: UUID) -> Optional[str]:
        """
        Get decrypted certificate data.
        
        Args:
            certificate_id: ID of the certificate
            
        Returns:
            Decrypted certificate data or None if not found
        """
        certificate = self.get_certificate(certificate_id)
        if not certificate or not certificate.certificate_data:
            return None
            
        if certificate.is_encrypted:
            try:
                return decrypt_field(certificate.certificate_data)
            except Exception as e:
                logger.error(f"Error decrypting certificate data: {str(e)}")
                return None
        else:
            return certificate.certificate_data
            
    def decrypt_private_key(self, certificate_id: UUID) -> Optional[str]:
        """
        Get decrypted private key.
        
        Args:
            certificate_id: ID of the certificate
            
        Returns:
            Decrypted private key or None if not available
        """
        certificate = self.get_certificate(certificate_id)
        if not certificate or not certificate.private_key_data or not certificate.has_private_key:
            return None
            
        if certificate.is_encrypted:
            try:
                return decrypt_field(certificate.private_key_data)
            except Exception as e:
                logger.error(f"Error decrypting private key: {str(e)}")
                return None
        else:
            return certificate.private_key_data
    
    def get_certificate_with_decrypted_data(self, certificate_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Get a certificate with decrypted data.
        
        Args:
            certificate_id: ID of the certificate
            
        Returns:
            Dictionary with certificate details and decrypted data
        """
        certificate = self.get_certificate(certificate_id)
        if not certificate:
            return None
            
        result = {
            "id": certificate.id,
            "name": certificate.name,
            "description": certificate.description,
            "certificate_type": certificate.certificate_type,
            "issuer": certificate.issuer,
            "subject": certificate.subject,
            "serial_number": certificate.serial_number,
            "fingerprint": certificate.fingerprint,
            "valid_from": certificate.valid_from,
            "valid_to": certificate.valid_to,
            "status": certificate.status,
            "has_private_key": certificate.has_private_key,
            "created_at": certificate.created_at,
            "certificate_data": self.decrypt_certificate_data(certificate_id)
        }
        
        if certificate.has_private_key:
            result["private_key_data"] = self.decrypt_private_key(certificate_id)
            
        return result