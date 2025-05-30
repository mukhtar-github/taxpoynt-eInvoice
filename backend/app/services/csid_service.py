"""
CSID generation service for TaxPoynt eInvoice APP functionality.

This module provides functionality for:
- Generating and managing Cryptographic Signature Identifiers (CSIDs)
- Associating CSIDs with certificates
- Validating and verifying CSIDs
"""

import uuid
import logging
import secrets
import string
import hashlib
import base64
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID

from sqlalchemy import and_, or_, func
from sqlalchemy.orm import Session

from app.models.csid import CSIDRegistry, CSIDStatus
from app.models.certificate import Certificate, CertificateStatus
from app.schemas.csid import CSIDCreate, CSIDUpdate

logger = logging.getLogger(__name__)


class CSIDService:
    """Service for CSID generation and management."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_csid(
        self, 
        csid_in: CSIDCreate, 
        user_id: Optional[UUID] = None
    ) -> CSIDRegistry:
        """
        Create a new CSID for a certificate.
        """
        # Verify certificate exists and is valid
        certificate = self.db.query(Certificate).filter(
            Certificate.id == csid_in.certificate_id,
            Certificate.status == CertificateStatus.ACTIVE
        ).first()
        
        if not certificate:
            raise ValueError("Certificate not found or not active")
        
        # Generate CSID
        csid = self._generate_csid(certificate.id, certificate.organization_id)
        
        # Set expiration time (default to certificate expiration if not provided)
        expiration_time = csid_in.expiration_time
        if not expiration_time and certificate.valid_to:
            expiration_time = certificate.valid_to
        
        # Create CSID registry entry
        db_csid = CSIDRegistry(
            id=uuid.uuid4(),
            organization_id=csid_in.organization_id,
            csid=csid,
            certificate_id=csid_in.certificate_id,
            expiration_time=expiration_time,
            is_active=True,
            created_by=user_id,
            metadata=csid_in.metadata or {}
        )
        
        self.db.add(db_csid)
        self.db.commit()
        self.db.refresh(db_csid)
        
        logger.info(f"Created CSID {csid} for certificate {csid_in.certificate_id}")
        return db_csid
    
    def get_csid(self, csid_id: UUID) -> Optional[CSIDRegistry]:
        """Get a CSID by ID."""
        return self.db.query(CSIDRegistry).filter(CSIDRegistry.id == csid_id).first()
    
    def get_csid_by_value(self, csid: str) -> Optional[CSIDRegistry]:
        """Get a CSID by its value."""
        return self.db.query(CSIDRegistry).filter(CSIDRegistry.csid == csid).first()
    
    def get_csids(
        self,
        organization_id: Optional[UUID] = None,
        certificate_id: Optional[UUID] = None,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[CSIDRegistry]:
        """Get CSIDs with optional filtering."""
        query = self.db.query(CSIDRegistry)
        
        if organization_id:
            query = query.filter(CSIDRegistry.organization_id == organization_id)
        
        if certificate_id:
            query = query.filter(CSIDRegistry.certificate_id == certificate_id)
        
        if is_active is not None:
            query = query.filter(CSIDRegistry.is_active == is_active)
        
        return query.order_by(CSIDRegistry.creation_time.desc()).offset(skip).limit(limit).all()
    
    def update_csid(
        self,
        csid_id: UUID,
        csid_in: CSIDUpdate,
        user_id: Optional[UUID] = None
    ) -> Optional[CSIDRegistry]:
        """Update a CSID."""
        db_csid = self.get_csid(csid_id)
        if not db_csid:
            return None
        
        update_data = csid_in.dict(exclude_unset=True)
        
        # Add audit info to metadata
        if 'metadata' in update_data and update_data['metadata']:
            current_metadata = db_csid.metadata or {}
            if not current_metadata.get('audit_trail'):
                current_metadata['audit_trail'] = []
            
            # Add audit entry
            current_metadata['audit_trail'].append({
                'timestamp': datetime.utcnow().isoformat(),
                'user_id': str(user_id) if user_id else None,
                'action': 'update',
                'fields_updated': list(update_data.keys())
            })
            
            update_data['metadata'] = current_metadata
        
        for key, value in update_data.items():
            setattr(db_csid, key, value)
        
        self.db.commit()
        self.db.refresh(db_csid)
        
        logger.info(f"Updated CSID {csid_id}")
        return db_csid
    
    def revoke_csid(
        self, 
        csid_id: UUID, 
        reason: str,
        user_id: Optional[UUID] = None
    ) -> bool:
        """Revoke an active CSID."""
        db_csid = self.get_csid(csid_id)
        if not db_csid:
            return False
        
        # Can only revoke active CSIDs
        if not db_csid.is_active:
            logger.warning(f"Cannot revoke inactive CSID {csid_id}")
            return False
        
        # Update metadata with revocation reason
        current_metadata = db_csid.metadata or {}
        current_metadata['revocation_reason'] = reason
        current_metadata['revoked_by'] = str(user_id) if user_id else None
        
        # Add audit trail
        if not current_metadata.get('audit_trail'):
            current_metadata['audit_trail'] = []
        
        current_metadata['audit_trail'].append({
            'timestamp': datetime.utcnow().isoformat(),
            'user_id': str(user_id) if user_id else None,
            'action': 'revoke',
            'reason': reason
        })
        
        # Update CSID
        db_csid.is_active = False
        db_csid.revocation_time = datetime.utcnow()
        db_csid.revocation_reason = reason
        db_csid.metadata = current_metadata
        
        self.db.commit()
        
        logger.info(f"Revoked CSID {csid_id}")
        return True
    
    def verify_csid(self, csid: str) -> Tuple[bool, CSIDStatus, List[str]]:
        """
        Verify a CSID's validity.
        
        Returns a tuple of (is_valid, status, error_messages)
        """
        errors = []
        
        # Find CSID in registry
        db_csid = self.get_csid_by_value(csid)
        if not db_csid:
            return False, CSIDStatus.PENDING, ["CSID not found in registry"]
        
        # Get status
        status = db_csid.get_status()
        
        # Check if CSID is valid
        if status == CSIDStatus.ACTIVE:
            return True, status, []
        elif status == CSIDStatus.EXPIRED:
            errors.append(f"CSID has expired (expiration: {db_csid.expiration_time.isoformat()})")
        elif status == CSIDStatus.REVOKED:
            errors.append(f"CSID has been revoked (reason: {db_csid.revocation_reason})")
        else:
            errors.append(f"CSID status is {status}")
        
        return False, status, errors
    
    def _generate_csid(self, certificate_id: UUID, organization_id: UUID) -> str:
        """
        Generate a unique CSID based on FIRS requirements.
        
        Format: TAXPOYNT-[ORG_PREFIX]-[TIMESTAMP]-[RANDOM]-[CHECKSUM]
        
        This is a placeholder implementation - the actual format should follow
        FIRS specifications when they are available.
        """
        # Generate components
        timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        
        # Create organization prefix (first 4 chars of organization_id)
        org_prefix = str(organization_id).replace('-', '')[:4].upper()
        
        # Generate random component (6 characters)
        alphabet = string.ascii_uppercase + string.digits
        random_component = ''.join(secrets.choice(alphabet) for _ in range(6))
        
        # Create base CSID without checksum
        base_csid = f"TAXPOYNT-{org_prefix}-{timestamp}-{random_component}"
        
        # Generate checksum (last 4 chars of SHA-256 hash)
        checksum_input = f"{base_csid}:{certificate_id}:{organization_id}"
        checksum = hashlib.sha256(checksum_input.encode()).hexdigest()[-4:].upper()
        
        # Final CSID
        return f"{base_csid}-{checksum}"
