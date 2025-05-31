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
    
    def retry_transmission(self, transmission_id: UUID, max_retries: int = 3, retry_delay: int = 0, 
                    force: bool = False, user_id: Optional[UUID] = None) -> Tuple[bool, str]:
        """
        Retry a failed or pending transmission with exponential backoff.
        
        Args:
            transmission_id: ID of the transmission to retry
            max_retries: Maximum number of retry attempts (default: 3)
            retry_delay: Base delay between retries in seconds (default: 0, immediate retry)
            force: If True, retry even if status is not failed
            user_id: User ID initiating the retry operation
            
        Returns:
            Tuple with (success: bool, message: str)
            
        The retry mechanism implements exponential backoff by calculating each retry's delay as:
        delay = retry_delay * (2 ^ (retry_count - 1))
        
        Example:
            - First retry: delay = retry_delay
            - Second retry: delay = retry_delay * 2
            - Third retry: delay = retry_delay * 4
            - And so on...
        """
        # Get the transmission record
        transmission = self.db.query(TransmissionRecord).filter(TransmissionRecord.id == transmission_id).first()
        
        if not transmission:
            return False, "Transmission not found"
            
        # Check if transmission can be retried
        if not force and transmission.status not in [TransmissionStatus.FAILED, TransmissionStatus.PENDING]:
            return False, f"Cannot retry transmission with status '{transmission.status}'. Status must be 'failed' or 'pending'."
        
        # Check if retry count exceeds max_retries
        if transmission.retry_count >= max_retries:
            return False, f"Maximum retry attempts reached ({max_retries})."
        
        # Calculate next retry delay using exponential backoff
        # Formula: base_delay * (2 ^ retry_count)
        current_retry_count = transmission.retry_count
        next_retry_delay = retry_delay * (2 ** current_retry_count) if retry_delay > 0 else 0
        
        # Update transmission record
        transmission.retry_count += 1
        transmission.last_retry_time = datetime.utcnow()
        transmission.status = TransmissionStatus.RETRYING
        
        # Update metadata to include retry information
        metadata = transmission.transmission_metadata or {}
        retry_history = metadata.get('retry_history', [])
        
        retry_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'attempt': transmission.retry_count,
            'status': 'initiated',
            'delay_seconds': next_retry_delay,
            'max_retries': max_retries,
            'details': f"Manual retry initiated{' (forced)' if force else ''}",
            'initiated_by': str(user_id) if user_id else None
        }
        
        retry_history.append(retry_entry)
        metadata['retry_history'] = retry_history
        metadata['retry_strategy'] = {
            'max_retries': max_retries,
            'base_delay': retry_delay,
            'current_delay': next_retry_delay,
            'algorithm': 'exponential_backoff'
        }
        
        transmission.transmission_metadata = metadata
        self.db.commit()
        
        # For immediate retries, attempt transmission now
        # For delayed retries, a separate background job would pick this up
        if next_retry_delay == 0:
            # Attempt immediate retry
            try:
                # Logic to resend the transmission would go here
                # This would typically be handled by a background worker
                # For now, we'll just mark it as completed for demonstration
                return True, "Transmission retry initiated successfully"
            except Exception as e:
                logger.error(f"Error retrying transmission {transmission_id}: {str(e)}")
                return False, f"Error retrying transmission: {str(e)}"
        else:
            # For delayed retries, return success but note the delay
            return True, f"Transmission retry scheduled with {next_retry_delay} seconds delay"
    
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
        
    def get_transmission_timeline(self, 
        organization_id: Optional[UUID] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        interval: str = 'day'
    ) -> List[Dict[str, Any]]:
        """
        Get time-series data for transmissions based on specified interval.
        
        Args:
            organization_id: Filter by organization ID
            start_date: Start date for timeline
            end_date: End date for timeline
            interval: Time interval ('hour', 'day', 'week', 'month')
            
        Returns:
            List of time periods with transmission counts and statuses
        """
        # Default to last 30 days if no dates specified
        if not end_date:
            end_date = datetime.now()
        if not start_date:
            start_date = end_date - timedelta(days=30)
            
        # Define time interval for grouping
        if interval == 'hour':
            date_trunc_arg = 'hour'
        elif interval == 'week':
            date_trunc_arg = 'week'
        elif interval == 'month':
            date_trunc_arg = 'month'
        else:  # default to day
            date_trunc_arg = 'day'
            
        # Get time periods with transmission counts by status
        query = self.db.query(
            func.date_trunc(date_trunc_arg, TransmissionRecord.transmission_time).label('period'),
            TransmissionRecord.status,
            func.count(TransmissionRecord.id).label('count')
        )
        
        # Apply filters
        if organization_id:
            query = query.filter(TransmissionRecord.organization_id == organization_id)
        if start_date:
            query = query.filter(TransmissionRecord.transmission_time >= start_date)
        if end_date:
            query = query.filter(TransmissionRecord.transmission_time <= end_date)
            
        # Group by period and status
        results = query.group_by(
            func.date_trunc(date_trunc_arg, TransmissionRecord.transmission_time),
            TransmissionRecord.status
        ).order_by(
            func.date_trunc(date_trunc_arg, TransmissionRecord.transmission_time)
        ).all()
        
        # Format results into timeline data
        timeline_data = []
        current_period = None
        period_data = None
        
        for period, status, count in results:
            # Convert period to ISO format string
            period_iso = period.isoformat()
            
            # If new period, create new entry
            if period_iso != current_period:
                # Add previous period data to timeline if exists
                if period_data:
                    timeline_data.append(period_data)
                
                # Initialize new period data
                period_data = {
                    'period': period_iso,
                    'total': 0,
                    'pending': 0,
                    'in_progress': 0,
                    'completed': 0,
                    'failed': 0,
                    'retrying': 0,
                    'cancelled': 0
                }
                current_period = period_iso
            
            # Update status count
            if status == TransmissionStatus.PENDING:
                period_data['pending'] = count
            elif status == TransmissionStatus.IN_PROGRESS:
                period_data['in_progress'] = count
            elif status == TransmissionStatus.COMPLETED:
                period_data['completed'] = count
            elif status == TransmissionStatus.FAILED:
                period_data['failed'] = count
            elif status == TransmissionStatus.RETRYING:
                period_data['retrying'] = count
            elif status == TransmissionStatus.CANCELED:  # Note the difference in spelling
                period_data['cancelled'] = count
                
            # Update total
            period_data['total'] += count
        
        # Add last period data if exists
        if period_data:
            timeline_data.append(period_data)
            
        return timeline_data
    
    def get_transmission_history(self, transmission_id: UUID) -> Dict[str, Any]:
        """
        Get detailed history and debug information for a specific transmission.
        
        Args:
            transmission_id: UUID of the transmission record
            
        Returns:
            Dictionary with transmission details, history, and debugging info
        """
        # Get base transmission record
        transmission = self.get_transmission(transmission_id)
        if not transmission:
            raise ValueError(f"Transmission with ID {transmission_id} not found")
            
        # Extract metadata for timeline reconstruction
        history = []
        metadata = transmission.transmission_metadata or {}
        
        # Add creation event
        history.append({
            'timestamp': transmission.transmission_time.isoformat(),
            'event': 'created',
            'status': TransmissionStatus.PENDING,
            'details': 'Transmission record created'
        })
        
        # Add retry events if any
        if transmission.retry_count > 0 and 'retry_history' in metadata:
            retry_history = metadata.get('retry_history', [])
            for retry in retry_history:
                history.append({
                    'timestamp': retry.get('timestamp'),
                    'event': 'retry',
                    'status': retry.get('status'),
                    'details': retry.get('details', 'Retry attempt')
                })
                
        # Add completion/failure event if applicable
        if transmission.status in [TransmissionStatus.COMPLETED, TransmissionStatus.FAILED]:
            history.append({
                'timestamp': metadata.get('completion_time', transmission.last_retry_time or transmission.transmission_time).isoformat(),
                'event': 'completed' if transmission.status == TransmissionStatus.COMPLETED else 'failed',
                'status': transmission.status,
                'details': metadata.get('completion_details', 'Transmission completed/failed')
            })
            
        # Add cancellation event if applicable
        if transmission.status == TransmissionStatus.CANCELED:
            history.append({
                'timestamp': metadata.get('cancellation_time', transmission.last_retry_time or transmission.transmission_time).isoformat(),
                'event': 'cancelled',
                'status': transmission.status,
                'details': metadata.get('cancellation_reason', 'Transmission cancelled')
            })
            
        # Sort history by timestamp
        history.sort(key=lambda x: x['timestamp'])
        
        # Extract debugging information
        debug_info = {
            'encryption_metadata': transmission.encryption_metadata or {},
            'response_data': transmission.response_data or {},
            'retry_count': transmission.retry_count,
            'error_details': metadata.get('error_details', {})
        }
        
        # Construct result
        result = {
            'transmission': transmission,
            'history': history,
            'debug_info': debug_info
        }
        
        return result
    
    def batch_update_transmissions(self, 
        transmission_ids: List[UUID], 
        update_data: Dict[str, Any],
        current_user_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Update multiple transmissions in a single batch operation.
        
        Args:
            transmission_ids: List of transmission IDs to update
            update_data: Dictionary of fields to update
            current_user_id: ID of user performing the update
            
        Returns:
            Dictionary with update statistics
        """
        if not transmission_ids:
            return {'updated': 0, 'failed': 0, 'errors': []}
            
        # Validate update data
        valid_fields = {
            'status', 'transmission_metadata', 'response_data'
        }
        
        update_fields = {}
        for field, value in update_data.items():
            if field in valid_fields:
                update_fields[field] = value
                
        if not update_fields:
            return {'updated': 0, 'failed': 0, 'errors': ['No valid fields to update']}
            
        # Add update metadata
        if 'transmission_metadata' not in update_fields:
            update_fields['transmission_metadata'] = {}
        
        if isinstance(update_fields['transmission_metadata'], dict):
            update_fields['transmission_metadata']['batch_updated_at'] = datetime.now().isoformat()
            update_fields['transmission_metadata']['batch_updated_by'] = str(current_user_id) if current_user_id else None
        
        # Track results
        results = {'updated': 0, 'failed': 0, 'errors': []}
        
        # Perform batch update
        try:
            # SQLAlchemy update query for batch operation
            update_query = {
                getattr(TransmissionRecord, k): v 
                for k, v in update_fields.items() 
                if not isinstance(v, dict) and hasattr(TransmissionRecord, k)
            }
            
            # Handle JSONB fields separately for proper merging
            if 'transmission_metadata' in update_fields and isinstance(update_fields['transmission_metadata'], dict):
                update_query[TransmissionRecord.transmission_metadata] = \
                    func.jsonb_set(TransmissionRecord.transmission_metadata, '{}', 
                                 func.cast(update_fields['transmission_metadata'], JSONB), True)
            
            if 'response_data' in update_fields and isinstance(update_fields['response_data'], dict):
                update_query[TransmissionRecord.response_data] = \
                    func.jsonb_set(TransmissionRecord.response_data, '{}', 
                                 func.cast(update_fields['response_data'], JSONB), True)
            
            # Execute update
            updated = self.db.query(TransmissionRecord).filter(
                TransmissionRecord.id.in_(transmission_ids)
            ).update(update_query, synchronize_session=False)
            
            self.db.commit()
            results['updated'] = updated
            
        except Exception as e:
            self.db.rollback()
            results['failed'] = len(transmission_ids)
            results['errors'].append(str(e))
            
        return results
        
    def process_transmission_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process webhook notifications for transmission status updates.
        
        Args:
            webhook_data: Dictionary with webhook payload
            
        Returns:
            Dictionary with processing results
        """
        # Extract required fields
        transmission_id = webhook_data.get('transmission_id')
        if not transmission_id:
            raise ValueError("Missing transmission_id in webhook data")
            
        try:
            # Convert transmission_id to UUID
            transmission_uuid = UUID(transmission_id)
        except ValueError:
            raise ValueError(f"Invalid transmission_id format: {transmission_id}")
            
        # Get transmission record
        transmission = self.get_transmission(transmission_uuid)
        if not transmission:
            raise ValueError(f"Transmission with ID {transmission_id} not found")
            
        # Extract status update
        new_status = webhook_data.get('status')
        if not new_status:
            raise ValueError("Missing status in webhook data")
            
        # Map webhook status to system status
        status_mapping = {
            'received': TransmissionStatus.IN_PROGRESS,
            'processing': TransmissionStatus.IN_PROGRESS,
            'accepted': TransmissionStatus.COMPLETED,
            'rejected': TransmissionStatus.FAILED,
            'error': TransmissionStatus.FAILED
        }
        
        system_status = status_mapping.get(new_status.lower())
        if not system_status:
            raise ValueError(f"Unknown status in webhook data: {new_status}")
            
        # Prepare update data
        update_data = {
            'status': system_status,
            'response_data': webhook_data.get('response_data', {})
        }
        
        # Update transmission metadata
        metadata = transmission.transmission_metadata or {}
        webhook_history = metadata.get('webhook_history', [])
        webhook_history.append({
            'timestamp': datetime.now().isoformat(),
            'webhook_data': webhook_data
        })
        
        metadata['webhook_history'] = webhook_history
        metadata['last_webhook_update'] = datetime.now().isoformat()
        
        if system_status == TransmissionStatus.COMPLETED:
            metadata['completion_time'] = datetime.now().isoformat()
            metadata['completion_details'] = webhook_data.get('details', 'Completed via webhook')
        elif system_status == TransmissionStatus.FAILED:
            metadata['error_details'] = webhook_data.get('error', {})
            
        update_data['transmission_metadata'] = metadata
        
        # Update the transmission record
        try:
            self.update_transmission(transmission_uuid, update_data)
            
            # Return success response
            return {
                'status': 'success',
                'transmission_id': str(transmission_uuid),
                'updated_status': system_status,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            # Log the error
            logger.error(f"Error updating transmission from webhook: {str(e)}")
            
            # Return error response
            return {
                'status': 'error',
                'transmission_id': str(transmission_uuid),
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
