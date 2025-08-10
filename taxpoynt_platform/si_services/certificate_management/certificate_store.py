"""
Certificate Store

Handles secure storage and retrieval of digital certificates.
Provides certificate persistence, indexing, and search capabilities.
"""

import os
import json
import logging
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from cryptography import x509
from cryptography.hazmat.backends import default_backend


class CertificateStatus(Enum):
    """Certificate status enumeration"""
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    PENDING = "pending"
    ARCHIVED = "archived"


@dataclass
class StoredCertificate:
    """Stored certificate metadata"""
    certificate_id: str
    subject_cn: str
    issuer_cn: str
    serial_number: str
    not_before: str
    not_after: str
    fingerprint: str
    status: CertificateStatus
    file_path: str
    organization_id: str
    certificate_type: str
    created_at: str
    updated_at: str
    metadata: Dict[str, Any]


class CertificateStore:
    """Secure certificate storage and management"""
    
    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = storage_path or "/tmp/certificates"
        self.index_file = os.path.join(self.storage_path, "certificate_index.json")
        self.logger = logging.getLogger(__name__)
        
        # Ensure storage directory exists
        os.makedirs(self.storage_path, exist_ok=True)
        
        # Load existing index
        self.certificate_index = self._load_index()
    
    def store_certificate(
        self,
        certificate_pem: bytes,
        organization_id: str,
        certificate_type: str = "signing",
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Store certificate in secure storage
        
        Args:
            certificate_pem: Certificate in PEM format
            organization_id: Organization identifier
            certificate_type: Type of certificate (signing, tls, ca, etc.)
            metadata: Additional metadata
            
        Returns:
            Certificate ID
        """
        try:
            # Parse certificate
            certificate = x509.load_pem_x509_certificate(certificate_pem, default_backend())
            
            # Generate certificate ID and fingerprint
            certificate_id = self._generate_certificate_id(certificate)
            fingerprint = self._calculate_fingerprint(certificate_pem)
            
            # Extract certificate information
            subject_cn = self._extract_common_name(certificate.subject)
            issuer_cn = self._extract_common_name(certificate.issuer)
            
            # Create filename
            filename = f"{certificate_id}.pem"
            file_path = os.path.join(self.storage_path, filename)
            
            # Write certificate to file
            with open(file_path, 'wb') as cert_file:
                cert_file.write(certificate_pem)
            
            # Set secure file permissions
            os.chmod(file_path, 0o600)
            
            # Create certificate record
            stored_cert = StoredCertificate(
                certificate_id=certificate_id,
                subject_cn=subject_cn,
                issuer_cn=issuer_cn,
                serial_number=str(certificate.serial_number),
                not_before=certificate.not_valid_before.isoformat(),
                not_after=certificate.not_valid_after.isoformat(),
                fingerprint=fingerprint,
                status=CertificateStatus.ACTIVE,
                file_path=file_path,
                organization_id=organization_id,
                certificate_type=certificate_type,
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat(),
                metadata=metadata or {}
            )
            
            # Add to index
            self.certificate_index[certificate_id] = asdict(stored_cert)
            self._save_index()
            
            self.logger.info(f"Stored certificate: {certificate_id} for organization: {organization_id}")
            
            return certificate_id
            
        except Exception as e:
            self.logger.error(f"Error storing certificate: {str(e)}")
            raise
    
    def retrieve_certificate(self, certificate_id: str) -> Optional[bytes]:
        """
        Retrieve certificate by ID
        
        Args:
            certificate_id: Certificate identifier
            
        Returns:
            Certificate PEM data or None if not found
        """
        try:
            if certificate_id not in self.certificate_index:
                return None
            
            cert_info = self.certificate_index[certificate_id]
            file_path = cert_info['file_path']
            
            if not os.path.exists(file_path):
                self.logger.warning(f"Certificate file not found: {file_path}")
                return None
            
            with open(file_path, 'rb') as cert_file:
                certificate_pem = cert_file.read()
            
            self.logger.info(f"Retrieved certificate: {certificate_id}")
            
            return certificate_pem
            
        except Exception as e:
            self.logger.error(f"Error retrieving certificate: {str(e)}")
            return None
    
    def get_certificate_info(self, certificate_id: str) -> Optional[StoredCertificate]:
        """Get certificate metadata"""
        if certificate_id not in self.certificate_index:
            return None
        
        cert_data = self.certificate_index[certificate_id]
        cert_data['status'] = CertificateStatus(cert_data['status'])
        
        return StoredCertificate(**cert_data)
    
    def list_certificates(
        self,
        organization_id: Optional[str] = None,
        certificate_type: Optional[str] = None,
        status: Optional[CertificateStatus] = None
    ) -> List[StoredCertificate]:
        """
        List certificates with optional filters
        
        Args:
            organization_id: Filter by organization
            certificate_type: Filter by certificate type
            status: Filter by status
            
        Returns:
            List of stored certificates
        """
        certificates = []
        
        for cert_id, cert_data in self.certificate_index.items():
            # Apply filters
            if organization_id and cert_data['organization_id'] != organization_id:
                continue
            
            if certificate_type and cert_data['certificate_type'] != certificate_type:
                continue
            
            if status and cert_data['status'] != status.value:
                continue
            
            # Convert status to enum
            cert_data['status'] = CertificateStatus(cert_data['status'])
            certificates.append(StoredCertificate(**cert_data))
        
        # Sort by creation date (newest first)
        return sorted(certificates, key=lambda x: x.created_at, reverse=True)
    
    def find_certificates_by_subject(self, subject_cn: str) -> List[StoredCertificate]:
        """Find certificates by subject common name"""
        certificates = []
        
        for cert_id, cert_data in self.certificate_index.items():
            if subject_cn.lower() in cert_data['subject_cn'].lower():
                cert_data['status'] = CertificateStatus(cert_data['status'])
                certificates.append(StoredCertificate(**cert_data))
        
        return certificates
    
    def update_certificate_status(
        self,
        certificate_id: str,
        status: CertificateStatus,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Update certificate status
        
        Args:
            certificate_id: Certificate identifier
            status: New status
            metadata: Additional metadata to merge
            
        Returns:
            True if updated successfully
        """
        try:
            if certificate_id not in self.certificate_index:
                return False
            
            # Update status and timestamp
            self.certificate_index[certificate_id]['status'] = status.value
            self.certificate_index[certificate_id]['updated_at'] = datetime.now().isoformat()
            
            # Merge additional metadata
            if metadata:
                existing_metadata = self.certificate_index[certificate_id].get('metadata', {})
                existing_metadata.update(metadata)
                self.certificate_index[certificate_id]['metadata'] = existing_metadata
            
            self._save_index()
            
            self.logger.info(f"Updated certificate status: {certificate_id} -> {status.value}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating certificate status: {str(e)}")
            return False
    
    def delete_certificate(self, certificate_id: str) -> bool:
        """
        Delete certificate (move to archive)
        
        Args:
            certificate_id: Certificate identifier
            
        Returns:
            True if deleted successfully
        """
        try:
            if certificate_id not in self.certificate_index:
                return False
            
            cert_info = self.certificate_index[certificate_id]
            file_path = cert_info['file_path']
            
            # Create archive directory
            archive_dir = os.path.join(self.storage_path, "archive")
            os.makedirs(archive_dir, exist_ok=True)
            
            # Move file to archive
            if os.path.exists(file_path):
                archive_path = os.path.join(archive_dir, f"archived_{os.path.basename(file_path)}")
                os.rename(file_path, archive_path)
                
                # Update file path in index and mark as archived
                self.certificate_index[certificate_id]['file_path'] = archive_path
                self.certificate_index[certificate_id]['status'] = CertificateStatus.ARCHIVED.value
                self.certificate_index[certificate_id]['updated_at'] = datetime.now().isoformat()
            else:
                # Just remove from index if file doesn't exist
                del self.certificate_index[certificate_id]
            
            self._save_index()
            
            self.logger.info(f"Archived certificate: {certificate_id}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error deleting certificate: {str(e)}")
            return False
    
    def check_expiring_certificates(self, days_ahead: int = 30) -> List[StoredCertificate]:
        """
        Check for certificates expiring within specified days
        
        Args:
            days_ahead: Number of days to look ahead
            
        Returns:
            List of expiring certificates
        """
        from datetime import timedelta
        
        expiring_certificates = []
        cutoff_date = datetime.now() + timedelta(days=days_ahead)
        
        for cert_id, cert_data in self.certificate_index.items():
            if cert_data['status'] == CertificateStatus.ACTIVE.value:
                not_after = datetime.fromisoformat(cert_data['not_after'])
                
                if not_after <= cutoff_date:
                    cert_data['status'] = CertificateStatus(cert_data['status'])
                    expiring_certificates.append(StoredCertificate(**cert_data))
        
        return sorted(expiring_certificates, key=lambda x: x.not_after)
    
    def get_storage_statistics(self) -> Dict[str, Any]:
        """Get certificate storage statistics"""
        total_certificates = len(self.certificate_index)
        
        # Count by status
        status_counts = {}
        for cert_data in self.certificate_index.values():
            status = cert_data['status']
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Count by type
        type_counts = {}
        for cert_data in self.certificate_index.values():
            cert_type = cert_data['certificate_type']
            type_counts[cert_type] = type_counts.get(cert_type, 0) + 1
        
        # Calculate storage size
        total_size = 0
        for filename in os.listdir(self.storage_path):
            if filename.endswith('.pem'):
                file_path = os.path.join(self.storage_path, filename)
                total_size += os.path.getsize(file_path)
        
        return {
            'total_certificates': total_certificates,
            'status_distribution': status_counts,
            'type_distribution': type_counts,
            'storage_size_bytes': total_size,
            'storage_size_mb': round(total_size / (1024 * 1024), 2),
            'index_file': self.index_file,
            'storage_path': self.storage_path
        }
    
    def _generate_certificate_id(self, certificate: x509.Certificate) -> str:
        """Generate unique certificate ID"""
        # Use serial number and subject hash for uniqueness
        serial = str(certificate.serial_number)
        subject_hash = hashlib.sha256(str(certificate.subject).encode()).hexdigest()[:8]
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        
        return f"cert_{serial}_{subject_hash}_{timestamp}"
    
    def _calculate_fingerprint(self, certificate_pem: bytes) -> str:
        """Calculate certificate SHA-256 fingerprint"""
        return hashlib.sha256(certificate_pem).hexdigest()
    
    def _extract_common_name(self, subject_or_issuer) -> str:
        """Extract common name from certificate subject or issuer"""
        for attribute in subject_or_issuer:
            if attribute.oid._name == 'commonName':
                return attribute.value
        return "Unknown"
    
    def _load_index(self) -> Dict[str, Any]:
        """Load certificate index from file"""
        try:
            if os.path.exists(self.index_file):
                with open(self.index_file, 'r') as index_file:
                    return json.load(index_file)
            return {}
        except Exception as e:
            self.logger.error(f"Error loading certificate index: {str(e)}")
            return {}
    
    def _save_index(self):
        """Save certificate index to file"""
        try:
            with open(self.index_file, 'w') as index_file:
                json.dump(self.certificate_index, index_file, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving certificate index: {str(e)}")
            raise