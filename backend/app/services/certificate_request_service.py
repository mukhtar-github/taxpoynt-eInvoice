"""
Certificate request service for TaxPoynt eInvoice APP functionality.

This module provides functionality for:
- Creating and managing certificate signing requests (CSRs)
- Generating CSRs from provided parameters
- Tracking certificate request status
"""

import uuid
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any, Union
from uuid import UUID

from sqlalchemy.orm import Session
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend

from app.models.certificate_request import CertificateRequest, CertificateRequestStatus, CertificateRequestType
from app.schemas.certificate_request import CertificateRequestCreate, CertificateRequestUpdate
from app.services.key_service import KeyManagementService

logger = logging.getLogger(__name__)


class CertificateRequestService:
    """Service for managing certificate requests."""
    
    def __init__(self, db: Session, key_service: KeyManagementService):
        self.db = db
        self.key_service = key_service
    
    def create_certificate_request(
        self, 
        request_in: CertificateRequestCreate, 
        user_id: Optional[UUID] = None
    ) -> CertificateRequest:
        """
        Create a new certificate request.
        
        If CSR data is provided, it will be stored directly.
        If CSR parameters are provided, a CSR will be generated.
        """
        csr_data = request_in.csr_data
        
        # If no CSR data provided, generate one from parameters
        if not csr_data and request_in.common_name:
            csr_data = self._generate_csr(
                common_name=request_in.common_name,
                organization_name=request_in.organization_name,
                organizational_unit=request_in.organizational_unit,
                locality=request_in.locality,
                state_or_province=request_in.state_or_province,
                country=request_in.country,
                email=request_in.email,
                key_size=request_in.key_size or 2048
            )
        
        # Encrypt CSR data if it contains private key information
        encrypted_csr_data = None
        encryption_key_id = None
        is_encrypted = False
        
        if csr_data:
            # For now, we always encrypt CSR data as it may contain sensitive info
            encryption_key_id, encrypted_csr_data = self.key_service.encrypt_data(
                csr_data, 
                context={"purpose": "certificate_request", "organization_id": str(request_in.organization_id)}
            )
            is_encrypted = True
        
        # Create certificate request DB record
        db_certificate_request = CertificateRequest(
            id=uuid.uuid4(),
            organization_id=request_in.organization_id,
            request_type=request_in.request_type,
            csr_data=encrypted_csr_data if is_encrypted else csr_data,
            is_encrypted=is_encrypted,
            encryption_key_id=encryption_key_id,
            status=CertificateRequestStatus.PENDING,
            created_by=user_id,
            request_metadata=request_in.request_metadata or {}
        )
        
        self.db.add(db_certificate_request)
        self.db.commit()
        self.db.refresh(db_certificate_request)
        
        logger.info(f"Created certificate request {db_certificate_request.id} for organization {request_in.organization_id}")
        return db_certificate_request
    
    def get_certificate_request(self, request_id: UUID) -> Optional[CertificateRequest]:
        """Get a certificate request by ID."""
        return self.db.query(CertificateRequest).filter(CertificateRequest.id == request_id).first()
    
    def get_certificate_requests(
        self,
        organization_id: Optional[UUID] = None,
        status: Optional[CertificateRequestStatus] = None,
        request_type: Optional[CertificateRequestType] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[CertificateRequest]:
        """Get certificate requests with optional filtering."""
        query = self.db.query(CertificateRequest)
        
        if organization_id:
            query = query.filter(CertificateRequest.organization_id == organization_id)
        
        if status:
            query = query.filter(CertificateRequest.status == status)
        
        if request_type:
            query = query.filter(CertificateRequest.request_type == request_type)
        
        return query.offset(skip).limit(limit).all()
    
    def update_certificate_request(
        self,
        request_id: UUID,
        request_in: CertificateRequestUpdate,
        user_id: Optional[UUID] = None
    ) -> Optional[CertificateRequest]:
        """Update a certificate request."""
        db_certificate_request = self.get_certificate_request(request_id)
        if not db_certificate_request:
            return None
        
        update_data = request_in.dict(exclude_unset=True)
        
        # Add audit info to metadata
        if 'request_metadata' in update_data and update_data['request_metadata']:
            current_metadata = db_certificate_request.request_metadata or {}
            if not current_metadata.get('audit_trail'):
                current_metadata['audit_trail'] = []
            
            # Add audit entry
            current_metadata['audit_trail'].append({
                'timestamp': datetime.utcnow().isoformat(),
                'user_id': str(user_id) if user_id else None,
                'action': 'update',
                'old_status': db_certificate_request.status,
                'new_status': update_data.get('status', db_certificate_request.status)
            })
            
            update_data['request_metadata'] = current_metadata
        
        for key, value in update_data.items():
            setattr(db_certificate_request, key, value)
        
        db_certificate_request.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(db_certificate_request)
        
        logger.info(f"Updated certificate request {request_id}")
        return db_certificate_request
    
    def cancel_certificate_request(
        self, 
        request_id: UUID, 
        reason: str,
        user_id: Optional[UUID] = None
    ) -> bool:
        """Cancel a pending certificate request."""
        db_certificate_request = self.get_certificate_request(request_id)
        if not db_certificate_request:
            return False
        
        # Can only cancel pending requests
        if db_certificate_request.status != CertificateRequestStatus.PENDING:
            logger.warning(f"Cannot cancel certificate request {request_id} with status {db_certificate_request.status}")
            return False
        
        # Update metadata with cancellation reason
        current_metadata = db_certificate_request.request_metadata or {}
        current_metadata['cancellation_reason'] = reason
        current_metadata['cancelled_by'] = str(user_id) if user_id else None
        current_metadata['cancelled_at'] = datetime.utcnow().isoformat()
        
        # Add audit trail
        if not current_metadata.get('audit_trail'):
            current_metadata['audit_trail'] = []
        
        current_metadata['audit_trail'].append({
            'timestamp': datetime.utcnow().isoformat(),
            'user_id': str(user_id) if user_id else None,
            'action': 'cancel',
            'reason': reason
        })
        
        # Update status and metadata
        db_certificate_request.status = CertificateRequestStatus.CANCELED
        db_certificate_request.request_metadata = current_metadata
        db_certificate_request.updated_at = datetime.utcnow()
        
        self.db.commit()
        
        logger.info(f"Cancelled certificate request {request_id}")
        return True
    
    def get_decrypted_csr_data(self, request_id: UUID) -> Optional[str]:
        """Get decrypted CSR data for a certificate request."""
        db_certificate_request = self.get_certificate_request(request_id)
        if not db_certificate_request or not db_certificate_request.csr_data:
            return None
        
        # If not encrypted, return as is
        if not db_certificate_request.is_encrypted:
            return db_certificate_request.csr_data
        
        # Decrypt data
        try:
            decrypted_data = self.key_service.decrypt_data(
                db_certificate_request.encryption_key_id,
                db_certificate_request.csr_data
            )
            return decrypted_data
        except Exception as e:
            logger.error(f"Error decrypting CSR data for request {request_id}: {e}")
            return None
    
    def _generate_csr(
        self,
        common_name: str,
        organization_name: Optional[str] = None,
        organizational_unit: Optional[str] = None,
        locality: Optional[str] = None,
        state_or_province: Optional[str] = None,
        country: Optional[str] = None,
        email: Optional[str] = None,
        key_size: int = 2048
    ) -> str:
        """
        Generate a Certificate Signing Request (CSR) with the provided parameters.
        
        Returns the PEM-encoded CSR.
        """
        # Generate private key
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=key_size,
            backend=default_backend()
        )
        
        # Build subject name
        name_attributes = [x509.NameAttribute(NameOID.COMMON_NAME, common_name)]
        
        if organization_name:
            name_attributes.append(x509.NameAttribute(NameOID.ORGANIZATION_NAME, organization_name))
        
        if organizational_unit:
            name_attributes.append(x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, organizational_unit))
        
        if locality:
            name_attributes.append(x509.NameAttribute(NameOID.LOCALITY_NAME, locality))
        
        if state_or_province:
            name_attributes.append(x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, state_or_province))
        
        if country:
            name_attributes.append(x509.NameAttribute(NameOID.COUNTRY_NAME, country))
        
        if email:
            name_attributes.append(x509.NameAttribute(NameOID.EMAIL_ADDRESS, email))
        
        # Create CSR
        csr = x509.CertificateSigningRequestBuilder().subject_name(
            x509.Name(name_attributes)
        ).sign(private_key, hashes.SHA256(), default_backend())
        
        # Serialize private key and CSR to PEM format
        private_key_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ).decode('utf-8')
        
        csr_pem = csr.public_bytes(serialization.Encoding.PEM).decode('utf-8')
        
        # Return combined PEM data
        return f"{private_key_pem}\n{csr_pem}"
