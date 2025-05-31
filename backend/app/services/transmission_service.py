"""
Transmission service for TaxPoynt eInvoice APP functionality.

This module provides functionality for:
- Creating and tracking secure transmissions to FIRS
- Handling encryption of payloads with standardized headers
- Verifying digital signatures for transmitted content
- Managing retry strategies for failed transmissions
"""

import uuid
import logging
import json
import hashlib
import base64
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Union, Tuple
from uuid import UUID

from sqlalchemy import and_, or_, func
from sqlalchemy.orm import Session

from app.models.transmission import TransmissionRecord, TransmissionStatus
from app.models.certificate import Certificate, CertificateStatus
from app.models.csid import CSIDRegistry, CSIDStatus
from app.models.submission import Submission
from app.schemas.transmission import TransmissionCreate, TransmissionUpdate
from app.services.key_service import KeyManagementService
from app.services.transmission_key_service import TransmissionKeyService
from app.services.csid_service import CSIDService
from app.utils.crypto_signing import verify_signature

logger = logging.getLogger(__name__)


class TransmissionService:
    """Service for secure transmission management."""
    
    def __init__(self, db: Session):
        self.db = db
        
        # Initialize required services
        from app.services.transmission_key_service import TransmissionKeyService
        from app.services.csid_service import CSIDService
        
        self.transmission_key_service = TransmissionKeyService(db)
        self.csid_service = CSIDService(db)
    
    def encrypt_payload(self, payload: Dict[str, Any], certificate_id: Optional[UUID] = None) -> Tuple[str, Dict[str, Any]]:
        """
        Encrypt a payload for secure transmission with standardized headers.
        
        Args:
            payload: The payload to encrypt
            certificate_id: Optional certificate ID for signing
            
        Returns:
            Tuple of (encrypted_payload, encryption_metadata)
        """
        if not payload:
            raise ValueError("No payload provided for encryption")
            
        # Generate a unique identifier for this encryption
        encryption_id = str(uuid.uuid4())
        
        # Create metadata for the encryption
        metadata = {
            "encryption_id": encryption_id,
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0",
            "is_encrypted": True
        }
        
        # Add digital signature if certificate is provided
        if certificate_id:
            try:
                # Convert payload to canonical form for signing
                canonical_payload = json.dumps(payload, sort_keys=True)
                
                # Sign the payload
                signature, signature_metadata = self.csid_service.sign_data(
                    canonical_payload,
                    certificate_id
                )
                
                # Add signature to metadata
                metadata["signature"] = signature
                metadata["signature_metadata"] = signature_metadata
                metadata["is_signed"] = True
            except Exception as e:
                logger.error(f"Failed to sign payload: {str(e)}")
                metadata["is_signed"] = False
                metadata["signature_error"] = str(e)
        else:
            metadata["is_signed"] = False
        
        try:
            # Encrypt the payload
            encrypted_data, key_id = self.transmission_key_service.encrypt_payload(payload)
            
            # Add encryption details to metadata
            metadata["encryption_key_id"] = key_id
            metadata["encryption_algorithm"] = "AES-256-GCM"
            
            return encrypted_data, metadata
        except Exception as e:
            logger.error(f"Failed to encrypt payload: {str(e)}")
            raise ValueError(f"Payload encryption failed: {str(e)}")
    
    def verify_signature(self, payload: Dict[str, Any], signature: str, certificate_id: UUID) -> bool:
        """
        Verify a digital signature for a transmission payload.
        
        Args:
            payload: The payload that was signed
            signature: The signature to verify
            certificate_id: The ID of the certificate to use for verification
            
        Returns:
            True if signature is valid, False otherwise
        """
        try:
            # Convert payload to canonical form
            canonical_payload = json.dumps(payload, sort_keys=True)
            
            # Verify signature using CSIDService
            return self.csid_service.verify_signature(
                canonical_payload,
                signature,
                certificate_id
            )
        except Exception as e:
            logger.error(f"Signature verification failed: {str(e)}")
            return False
    
    def create_transmission(
        self, 
        transmission_in: TransmissionCreate, 
        user_id: Optional[UUID] = None
    ) -> TransmissionRecord:
        """
        Create a new transmission record.
        
        Encrypts the payload if specified and prepares for transmission to FIRS.
        """
        # Verify certificate exists and is valid
        certificate = None
        if transmission_in.certificate_id:
            certificate = self.db.query(Certificate).filter(
                Certificate.id == transmission_in.certificate_id,
                Certificate.status == CertificateStatus.ACTIVE
            ).first()
            
            if not certificate:
                raise ValueError("Certificate not found or not active")
        
        # Get payload from submission if submission_id is provided
        payload = transmission_in.payload
        if transmission_in.submission_id and not payload:
            # Fetch submission data
            submission = self.db.query(Submission).filter(
                Submission.id == transmission_in.submission_id
            ).first()
            
            if not submission:
                raise ValueError("Submission not found")
            
            # Use submission data as payload
            payload = {
                "submission_id": str(submission.id),
                "invoice_data": submission.invoice_data,
                "metadata": submission.metadata
            }
        
        # Ensure we have payload data
        if not payload:
            raise ValueError("No payload provided for transmission")
        
        # Encrypt payload if encryption is requested
        encrypted_payload = None
        encryption_metadata = None
        
        if transmission_in.encrypt_payload:
            # Encrypt and sign the payload
            encrypted_payload, encryption_metadata = self.encrypt_payload(
                payload,
                certificate_id=transmission_in.certificate_id if certificate else None
            )
        else:
            # Store payload as-is with minimal metadata
            encrypted_payload = json.dumps(payload)
            encryption_metadata = {
                "is_encrypted": False,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # Create transmission record
        db_transmission = TransmissionRecord(
            id=uuid.uuid4() if not transmission_in.id else transmission_in.id,
            organization_id=transmission_in.organization_id,
            submission_id=transmission_in.submission_id,
            certificate_id=transmission_in.certificate_id,
            status=TransmissionStatus.PENDING,
            encrypted_payload=encrypted_payload,
            encryption_metadata=encryption_metadata,
            destination=transmission_in.destination,
            destination_endpoint=transmission_in.destination_endpoint,
            retry_count=0,
            max_retries=transmission_in.max_retries or 3,
            retry_delay_seconds=transmission_in.retry_delay_seconds or 300,
            metadata=transmission_in.metadata or {}
        )
        
        # Add creation metadata
        if not db_transmission.metadata:
            db_transmission.metadata = {}
            
        db_transmission.metadata.update({
            "created_by": str(user_id) if user_id else "system",
            "created_at": datetime.utcnow().isoformat(),
            "version": "1.0"
        })
        
        # Add to database
        self.db.add(db_transmission)
        self.db.commit()
        self.db.refresh(db_transmission)
        
        logger.info(f"Created new transmission record {db_transmission.id}")
        return db_transmission
        
        submission = self.db.query(Submission).filter(
            Submission.id == transmission_in.submission_id
        ).first()
        
        if not submission:
            raise ValueError("Submission not found")
            
            # Use submission data as payload
            payload = submission.data
        
        if not payload:
            raise ValueError("No payload provided and no submission data available")
        
        # Always encrypt payload with proper formatting
        encrypted_payload = None
        encryption_metadata = None
        payload_hash = None
        
        # Generate payload hash for integrity verification
        if isinstance(payload, dict):
            payload_str = json.dumps(payload, sort_keys=True)
        else:
            payload_str = str(payload)
            
        # Create payload hash for verification
        payload_hash = hashlib.sha256(payload_str.encode('utf-8')).hexdigest()
        
        # Prepare transmission context
        transmission_context = {
            "purpose": "transmission", 
            "organization_id": str(transmission_in.organization_id),
            "certificate_id": str(transmission_in.certificate_id) if transmission_in.certificate_id else None,
            "submission_id": str(transmission_in.submission_id) if transmission_in.submission_id else None,
            "timestamp": datetime.utcnow().isoformat(),
            "payload_hash": payload_hash
        }
        
        # If a certificate is provided, add digital signature
        signature = None
        signature_metadata = None
        
        if transmission_in.certificate_id and transmission_in.sign_payload:
            try:
                # Get the certificate for signing
                certificate = self.db.query(Certificate).filter(
                    Certificate.id == transmission_in.certificate_id,
                    Certificate.status == CertificateStatus.ACTIVE
                ).first()
                
                if certificate:
                    # Find an active CSID for this certificate
                    csid = self.db.query(CSIDRegistry).filter(
                        CSIDRegistry.certificate_id == certificate.id,
                        CSIDRegistry.status == CSIDStatus.ACTIVE
                    ).first()
                    
                    if csid:
                        # Add CSID to context
                        transmission_context["csid"] = csid.csid_value
                        
                        # Sign the payload hash
                        signature, signature_metadata = self.csid_service.sign_data(
                            payload_hash,
                            certificate.id,
                            csid.id
                        )
                        
                        # Add to transmission context
                        transmission_context["signature"] = signature
                        transmission_context["signature_metadata"] = signature_metadata
            except Exception as e:
                logger.warning(f"Failed to sign payload: {str(e)}")
                # Continue without signature if it fails
        
        # Prepare payload with standard headers
        formatted_payload = {
            "version": "1.0",
            "type": "taxpoynt_transmission",
            "metadata": transmission_context,
            "content": payload
        }
        
        # Use specialized transmission key service for encryption
        encryption_key_id, encrypted_data = self.transmission_key_service.encrypt_payload(
            formatted_payload, 
            context=transmission_context
        )
        
        encrypted_payload = encrypted_data
        encryption_metadata = {
            "encryption_key_id": encryption_key_id,
            "encryption_timestamp": datetime.utcnow().isoformat(),
            "is_encrypted": True,
            "payload_hash": payload_hash,
            "has_signature": signature is not None
        }
        
        # Add signature information if available
        if signature and signature_metadata:
            encryption_metadata["signature"] = signature
            encryption_metadata["signature_metadata"] = signature_metadata
        
        # Create transmission record
        db_transmission = TransmissionRecord(
            id=uuid.uuid4(),
            organization_id=transmission_in.organization_id,
            certificate_id=transmission_in.certificate_id,
            submission_id=transmission_in.submission_id,
            status=TransmissionStatus.PENDING,
            encrypted_payload=encrypted_payload,
            encryption_metadata=encryption_metadata,
            created_by=user_id,
            transmission_metadata=transmission_in.transmission_metadata or {}
        )
        
        self.db.add(db_transmission)
        self.db.commit()
        self.db.refresh(db_transmission)
        
        logger.info(f"Created transmission record {db_transmission.id} for organization {transmission_in.organization_id}")
        return db_transmission
    
    def get_transmission(self, transmission_id: UUID) -> Optional[TransmissionRecord]:
        """Get a transmission record by ID."""
        return self.db.query(TransmissionRecord).filter(
            TransmissionRecord.id == transmission_id
        ).first()
    
    def get_transmissions(
        self,
        organization_id: Optional[UUID] = None,
        certificate_id: Optional[UUID] = None,
        submission_id: Optional[UUID] = None,
        status: Optional[TransmissionStatus] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[TransmissionRecord]:
        """Get transmissions with optional filtering."""
        query = self.db.query(TransmissionRecord)
        
        if organization_id:
            query = query.filter(TransmissionRecord.organization_id == organization_id)
        
        if certificate_id:
            query = query.filter(TransmissionRecord.certificate_id == certificate_id)
        
        if submission_id:
            query = query.filter(TransmissionRecord.submission_id == submission_id)
        
        if status:
            query = query.filter(TransmissionRecord.status == status)
        
        return query.order_by(TransmissionRecord.transmission_time.desc()).offset(skip).limit(limit).all()
    
    def update_transmission(
        self,
        transmission_id: UUID,
        transmission_in: TransmissionUpdate,
        user_id: Optional[UUID] = None
    ) -> Optional[TransmissionRecord]:
        """Update a transmission record."""
        db_transmission = self.get_transmission(transmission_id)
        if not db_transmission:
            return None
        
        update_data = transmission_in.dict(exclude_unset=True)
        
        # Add audit info to metadata
        if 'transmission_metadata' in update_data and update_data['transmission_metadata']:
            current_metadata = db_transmission.transmission_metadata or {}
            if not current_metadata.get('audit_trail'):
                current_metadata['audit_trail'] = []
            
            # Add audit entry
            current_metadata['audit_trail'].append({
                'timestamp': datetime.utcnow().isoformat(),
                'user_id': str(user_id) if user_id else None,
                'action': 'update',
                'old_status': db_transmission.status,
                'new_status': update_data.get('status', db_transmission.status)
            })
            
            update_data['transmission_metadata'] = current_metadata
        
        for key, value in update_data.items():
            setattr(db_transmission, key, value)
        
        self.db.commit()
        self.db.refresh(db_transmission)
    


    def get_transmission_statistics(
        self,
        organization_id: Optional[UUID] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get transmission statistics.
        """
        query = self.db.query(
            TransmissionRecord.status,
            func.count(TransmissionRecord.id).label('count')
        )
        
        if organization_id:
            query = query.filter(TransmissionRecord.organization_id == organization_id)
            
        if start_date:
            query = query.filter(TransmissionRecord.created_at >= start_date)
            
        if end_date:
            query = query.filter(TransmissionRecord.created_at <= end_date)
            
        results = query.group_by(TransmissionRecord.status).all()
        
        # Initialize stats
        stats = {
            'total': 0,
            'pending': 0,
            'in_progress': 0,
            'completed': 0,
            'failed': 0,
            'retrying': 0,
            'cancelled': 0
        }
        
        # Populate actual counts
        for status, count in results:
            if status == TransmissionStatus.PENDING:
                stats['pending'] = count
            elif status == TransmissionStatus.IN_PROGRESS:
                stats['in_progress'] = count
            elif status == TransmissionStatus.COMPLETED:
                stats['completed'] = count
            elif status == TransmissionStatus.FAILED:
                stats['failed'] = count
            elif status == TransmissionStatus.RETRYING:
                stats['retrying'] = count
            elif status == TransmissionStatus.CANCELLED:
                stats['cancelled'] = count
                
            # Add to total
            stats['total'] += count
        
        # Calculate success rate
        if stats['total'] > 0:
            completed = stats['completed']
            total = stats['total']
            stats['success_rate'] = round((completed / total) * 100, 2)
        else:
            stats['success_rate'] = 0.0
            
        # Get additional metrics
        if organization_id:
            # Average retry count
            avg_retry = self.db.query(func.avg(TransmissionRecord.retry_count)).filter(
                TransmissionRecord.organization_id == organization_id
            ).scalar() or 0
            stats['average_retries'] = round(float(avg_retry), 2)
            
            # Count transmissions with signatures
            signed_count = self.db.query(func.count(TransmissionRecord.id)).filter(
                TransmissionRecord.organization_id == organization_id,
                TransmissionRecord.encryption_metadata['has_signature'].astext == 'true'
            ).scalar() or 0
            stats['signed_transmissions'] = signed_count
        
        return stats
