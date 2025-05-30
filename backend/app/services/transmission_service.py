"""
Transmission service for TaxPoynt eInvoice APP functionality.

This module provides functionality for:
- Creating and tracking secure transmissions to FIRS
- Handling encryption of payloads
- Managing retry strategies for failed transmissions
"""

import uuid
import logging
import json
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Union, Tuple
from uuid import UUID

from sqlalchemy import and_, or_, func
from sqlalchemy.orm import Session

from app.models.transmission import TransmissionRecord, TransmissionStatus
from app.models.certificate import Certificate, CertificateStatus
from app.models.submission import Submission
from app.schemas.transmission import TransmissionCreate, TransmissionUpdate
from app.services.key_service import KeyManagementService

logger = logging.getLogger(__name__)


class TransmissionService:
    """Service for secure transmission management."""
    
    def __init__(self, db: Session, key_service: KeyManagementService):
        self.db = db
        self.key_service = key_service
    
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
            submission = self.db.query(Submission).filter(
                Submission.id == transmission_in.submission_id
            ).first()
            
            if not submission:
                raise ValueError("Submission not found")
            
            # Use submission data as payload
            payload = submission.data
        
        if not payload:
            raise ValueError("No payload provided and no submission data available")
        
        # Encrypt payload if requested
        encrypted_payload = None
        encryption_metadata = None
        
        if transmission_in.encrypt_payload:
            # Convert payload to string if it's a dict
            if isinstance(payload, dict):
                payload_str = json.dumps(payload)
            else:
                payload_str = str(payload)
            
            # Encrypt the payload
            encryption_key_id, encrypted_data = self.key_service.encrypt_data(
                payload_str, 
                context={
                    "purpose": "transmission", 
                    "organization_id": str(transmission_in.organization_id),
                    "certificate_id": str(transmission_in.certificate_id) if transmission_in.certificate_id else None,
                    "submission_id": str(transmission_in.submission_id) if transmission_in.submission_id else None
                }
            )
            
            encrypted_payload = encrypted_data
            encryption_metadata = {
                "encryption_key_id": encryption_key_id,
                "encryption_timestamp": datetime.utcnow().isoformat(),
                "is_encrypted": True
            }
        else:
            # Store payload as-is (as a string)
            if isinstance(payload, dict):
                encrypted_payload = json.dumps(payload)
            else:
                encrypted_payload = str(payload)
            
            encryption_metadata = {
                "is_encrypted": False
            }
        
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
        
        logger.info(f"Updated transmission {transmission_id}")
        return db_transmission
    
    def retry_transmission(
        self, 
        transmission_id: UUID,
        max_retries: Optional[int] = None,
        retry_delay: Optional[int] = None,
        force: bool = False,
        user_id: Optional[UUID] = None
    ) -> Tuple[bool, str]:
        """
        Retry a failed or pending transmission.
        
        Returns a tuple of (success, message)
        """
        db_transmission = self.get_transmission(transmission_id)
        if not db_transmission:
            return False, "Transmission not found"
        
        # Check if can retry
        if not force and not db_transmission.can_retry(max_retries or 3):
            return False, f"Cannot retry transmission with status {db_transmission.status} or retry count {db_transmission.retry_count}"
        
        # Update retry information
        current_metadata = db_transmission.transmission_metadata or {}
        if not current_metadata.get('retry_history'):
            current_metadata['retry_history'] = []
        
        # Add retry entry
        current_metadata['retry_history'].append({
            'timestamp': datetime.utcnow().isoformat(),
            'user_id': str(user_id) if user_id else None,
            'retry_count': db_transmission.retry_count + 1,
            'forced': force,
            'previous_status': db_transmission.status
        })
        
        # Update transmission
        db_transmission.status = TransmissionStatus.RETRYING
        db_transmission.retry_count += 1
        db_transmission.last_retry_time = datetime.utcnow()
        db_transmission.transmission_metadata = current_metadata
        
        self.db.commit()
        
        logger.info(f"Retrying transmission {transmission_id}, retry count: {db_transmission.retry_count}")
        return True, f"Transmission {transmission_id} queued for retry"
    
    def get_decrypted_payload(self, transmission_id: UUID) -> Optional[str]:
        """Get decrypted payload for a transmission."""
        db_transmission = self.get_transmission(transmission_id)
        if not db_transmission or not db_transmission.encrypted_payload:
            return None
        
        # If not encrypted, return as is
        if not db_transmission.encryption_metadata or not db_transmission.encryption_metadata.get('is_encrypted'):
            return db_transmission.encrypted_payload
        
        # Get encryption key ID
        encryption_key_id = db_transmission.encryption_metadata.get('encryption_key_id')
        if not encryption_key_id:
            logger.error(f"No encryption key ID found for transmission {transmission_id}")
            return None
        
        # Decrypt data
        try:
            decrypted_data = self.key_service.decrypt_data(
                encryption_key_id,
                db_transmission.encrypted_payload
            )
            return decrypted_data
        except Exception as e:
            logger.error(f"Error decrypting payload for transmission {transmission_id}: {e}")
            return None
    
    def get_transmission_statistics(
        self, 
        organization_id: Optional[UUID] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get transmission statistics."""
        query = self.db.query(
            TransmissionRecord.status,
            func.count(TransmissionRecord.id).label('count')
        )
        
        if organization_id:
            query = query.filter(TransmissionRecord.organization_id == organization_id)
        
        if start_date:
            query = query.filter(TransmissionRecord.transmission_time >= start_date)
        
        if end_date:
            query = query.filter(TransmissionRecord.transmission_time <= end_date)
        
        # Group by status
        query = query.group_by(TransmissionRecord.status)
        
        # Execute query
        results = query.all()
        
        # Build statistics
        stats = {
            'total': 0,
            'pending': 0,
            'in_progress': 0,
            'completed': 0,
            'failed': 0,
            'retrying': 0,
            'canceled': 0
        }
        
        for status, count in results:
            stats[status.lower()] = count
            stats['total'] += count
        
        # Calculate success rate
        if stats['total'] > 0:
            success_rate = stats['completed'] / stats['total']
        else:
            success_rate = 0
        
        stats['success_rate'] = success_rate
        
        return stats
