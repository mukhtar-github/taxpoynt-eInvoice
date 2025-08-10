"""
Certificate Request Service (Refactored)

Refactored certificate request service that uses granular components.
Handles certificate signing requests and CA interactions.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from sqlalchemy.orm import Session

# Import granular components
from .certificate_generator import CertificateGenerator
from .key_manager import KeyManager
from .certificate_store import CertificateStore
from .ca_integration import CAIntegration, CertificateRequest, CAType

# Legacy imports for backward compatibility
from app.models.certificate_request import CertificateRequest as LegacyCertificateRequest
from app.schemas.certificate import CertificateRequestCreate, CertificateRequestUpdate
from app.core.config import settings

logger = logging.getLogger(__name__)


class CertificateRequestService:
    """
    Refactored Certificate Request Service using granular components.
    
    Handles certificate signing requests, CA communication, and request lifecycle.
    """
    
    def __init__(self, db: Optional[Session] = None):
        self.db = db
        
        # Initialize granular components
        self.certificate_generator = CertificateGenerator()
        self.key_manager = KeyManager()
        self.certificate_store = CertificateStore()
        self.ca_integration = CAIntegration()
    
    def create_certificate_request(
        self,
        subject_info: Dict[str, str],
        organization_id: str,
        certificate_type: str = "signing",
        key_size: int = 2048,
        extensions: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, str, str]:
        """
        Create certificate signing request using granular components
        
        Args:
            subject_info: Certificate subject information
            organization_id: Organization identifier
            certificate_type: Type of certificate requested
            key_size: Private key size in bits
            extensions: Additional certificate extensions
            
        Returns:
            Tuple of (request_id, csr_pem, private_key_id)
        """
        try:
            # Validate subject information
            is_valid, validation_errors = self.certificate_generator.validate_certificate_info(subject_info)
            if not is_valid:
                raise ValueError(f"Invalid subject info: {', '.join(validation_errors)}")
            
            # Generate CSR using certificate generator
            csr_pem, private_key_pem = self.certificate_generator.generate_certificate_request(
                subject_info=subject_info,
                key_size=key_size
            )
            
            # Store private key securely
            key_name = f"csr_{subject_info.get('common_name', 'unknown')}_{datetime.now().strftime('%Y%m%d')}"
            private_key_path = self.key_manager.store_key(
                key_data=private_key_pem,
                key_name=key_name,
                key_type="private"
            )
            
            # Generate request ID
            request_id = f"req_{organization_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # Store request in legacy database if available
            if self.db:
                try:
                    legacy_request = LegacyCertificateRequest(
                        request_id=request_id,
                        organization_id=organization_id,
                        certificate_type=certificate_type,
                        csr_data=csr_pem.decode('utf-8'),
                        subject_info=subject_info,
                        key_size=key_size,
                        status="pending",
                        created_at=datetime.now(),
                        metadata={
                            'private_key_path': private_key_path,
                            'extensions': extensions or {}
                        }
                    )
                    
                    self.db.add(legacy_request)
                    self.db.commit()
                    
                except Exception as e:
                    logger.warning(f"Could not store request in legacy database: {str(e)}")
            
            logger.info(f"Created certificate request: {request_id} for {subject_info.get('common_name')}")
            
            return request_id, csr_pem.decode('utf-8'), private_key_path
            
        except Exception as e:
            logger.error(f"Error creating certificate request: {str(e)}")
            raise
    
    def submit_request_to_ca(
        self,
        request_id: str,
        ca_id: str,
        validity_days: int = 365
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Submit certificate request to Certificate Authority
        
        Args:
            request_id: Certificate request identifier
            ca_id: Certificate Authority identifier
            validity_days: Requested validity period
            
        Returns:
            Tuple of (success, message, certificate_id)
        """
        try:
            # Get request details from database
            request_data = None
            if self.db:
                request_data = self.db.query(LegacyCertificateRequest).filter(
                    LegacyCertificateRequest.request_id == request_id
                ).first()
            
            if not request_data:
                return False, f"Certificate request not found: {request_id}", None
            
            # Create certificate request for CA
            cert_request = CertificateRequest(
                csr_pem=request_data.csr_data.encode('utf-8'),
                organization_id=request_data.organization_id,
                certificate_type=request_data.certificate_type,
                validity_days=validity_days,
                extensions=request_data.metadata.get('extensions', {}),
                metadata={
                    'request_id': request_id,
                    'submitted_at': datetime.now().isoformat()
                }
            )
            
            # Submit to CA using CA integration
            signed_cert_pem, success, message = self.ca_integration.submit_csr_to_ca(
                ca_id=ca_id,
                cert_request=cert_request
            )
            
            if success and signed_cert_pem:
                # Store signed certificate
                certificate_id = self.certificate_store.store_certificate(
                    certificate_pem=signed_cert_pem,
                    organization_id=request_data.organization_id,
                    certificate_type=request_data.certificate_type,
                    metadata={
                        'ca_id': ca_id,
                        'request_id': request_id,
                        'validity_days': validity_days,
                        'signed_by': 'ca_integration'
                    }
                )
                
                # Update request status in database
                if self.db:
                    try:
                        request_data.status = "completed"
                        request_data.certificate_id = certificate_id
                        request_data.completed_at = datetime.now()
                        self.db.commit()
                    except Exception as e:
                        logger.warning(f"Could not update request status: {str(e)}")
                
                logger.info(f"Successfully processed request {request_id} -> certificate {certificate_id}")
                
                return True, f"Certificate issued successfully: {certificate_id}", certificate_id
            else:
                # Update request status to failed
                if self.db:
                    try:
                        request_data.status = "failed"
                        request_data.error_message = message
                        request_data.updated_at = datetime.now()
                        self.db.commit()
                    except Exception as e:
                        logger.warning(f"Could not update request status: {str(e)}")
                
                return False, message, None
                
        except Exception as e:
            error_msg = f"Error submitting request to CA: {str(e)}"
            logger.error(error_msg)
            return False, error_msg, None
    
    def create_self_signed_certificate(
        self,
        subject_info: Dict[str, str],
        organization_id: str,
        validity_days: int = 365,
        certificate_type: str = "signing"
    ) -> Tuple[str, str]:
        """
        Create self-signed certificate directly (bypass CA)
        
        Args:
            subject_info: Certificate subject information
            organization_id: Organization identifier
            validity_days: Certificate validity period
            certificate_type: Type of certificate
            
        Returns:
            Tuple of (certificate_id, certificate_pem)
        """
        try:
            # Generate self-signed certificate
            cert_pem, key_pem = self.certificate_generator.generate_self_signed_certificate(
                subject_info=subject_info,
                validity_days=validity_days
            )
            
            # Store certificate
            certificate_id = self.certificate_store.store_certificate(
                certificate_pem=cert_pem,
                organization_id=organization_id,
                certificate_type=certificate_type,
                metadata={
                    'generation_method': 'self_signed',
                    'validity_days': validity_days,
                    'created_by': 'certificate_request_service'
                }
            )
            
            # Store private key
            key_name = f"self_signed_{subject_info.get('common_name', 'cert')}_{datetime.now().strftime('%Y%m%d')}"
            self.key_manager.store_key(key_pem, key_name, "private")
            
            logger.info(f"Created self-signed certificate: {certificate_id} for {subject_info.get('common_name')}")
            
            return certificate_id, cert_pem.decode('utf-8')
            
        except Exception as e:
            logger.error(f"Error creating self-signed certificate: {str(e)}")
            raise
    
    def create_firs_compliant_certificate(
        self,
        organization_info: Dict[str, str],
        organization_id: str,
        validity_days: int = 730
    ) -> Tuple[str, str]:
        """
        Create FIRS-compliant certificate for Nigerian e-invoicing
        
        Args:
            organization_info: Organization information
            organization_id: Organization identifier
            validity_days: Certificate validity (default 2 years for FIRS)
            
        Returns:
            Tuple of (certificate_id, certificate_pem)
        """
        try:
            # Generate FIRS-compliant certificate
            cert_pem, key_pem = self.certificate_generator.generate_firs_compliant_certificate(
                organization_info=organization_info,
                validity_days=validity_days
            )
            
            # Store certificate with FIRS-specific metadata
            certificate_id = self.certificate_store.store_certificate(
                certificate_pem=cert_pem,
                organization_id=organization_id,
                certificate_type="firs_einvoice",
                metadata={
                    'firs_compliant': True,
                    'validity_days': validity_days,
                    'country': 'NG',
                    'regulation': 'FIRS_E_INVOICE',
                    'created_by': 'firs_certificate_service'
                }
            )
            
            # Store private key with FIRS designation
            key_name = f"firs_{organization_info.get('organization_name', 'org')}_{datetime.now().strftime('%Y%m%d')}"
            self.key_manager.store_key(key_pem, key_name, "private")
            
            logger.info(f"Created FIRS-compliant certificate: {certificate_id} for {organization_info.get('organization_name')}")
            
            return certificate_id, cert_pem.decode('utf-8')
            
        except Exception as e:
            logger.error(f"Error creating FIRS-compliant certificate: {str(e)}")
            raise
    
    def get_request_status(self, request_id: str) -> Optional[Dict[str, Any]]:
        """
        Get certificate request status
        
        Args:
            request_id: Certificate request identifier
            
        Returns:
            Request status information or None
        """
        try:
            if not self.db:
                return None
            
            request_data = self.db.query(LegacyCertificateRequest).filter(
                LegacyCertificateRequest.request_id == request_id
            ).first()
            
            if not request_data:
                return None
            
            return {
                'request_id': request_data.request_id,
                'organization_id': request_data.organization_id,
                'certificate_type': request_data.certificate_type,
                'status': request_data.status,
                'subject_info': request_data.subject_info,
                'created_at': request_data.created_at.isoformat(),
                'updated_at': request_data.updated_at.isoformat() if request_data.updated_at else None,
                'completed_at': request_data.completed_at.isoformat() if request_data.completed_at else None,
                'certificate_id': getattr(request_data, 'certificate_id', None),
                'error_message': getattr(request_data, 'error_message', None)
            }
            
        except Exception as e:
            logger.error(f"Error getting request status: {str(e)}")
            return None
    
    def list_requests(
        self,
        organization_id: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List certificate requests with optional filters
        
        Args:
            organization_id: Filter by organization
            status: Filter by status
            
        Returns:
            List of certificate requests
        """
        try:
            if not self.db:
                return []
            
            query = self.db.query(LegacyCertificateRequest)
            
            if organization_id:
                query = query.filter(LegacyCertificateRequest.organization_id == organization_id)
            
            if status:
                query = query.filter(LegacyCertificateRequest.status == status)
            
            requests = query.order_by(LegacyCertificateRequest.created_at.desc()).all()
            
            return [
                {
                    'request_id': req.request_id,
                    'organization_id': req.organization_id,
                    'certificate_type': req.certificate_type,
                    'status': req.status,
                    'subject_info': req.subject_info,
                    'created_at': req.created_at.isoformat(),
                    'certificate_id': getattr(req, 'certificate_id', None)
                }
                for req in requests
            ]
            
        except Exception as e:
            logger.error(f"Error listing requests: {str(e)}")
            return []
    
    def cancel_request(self, request_id: str, reason: str = "cancelled_by_user") -> bool:
        """
        Cancel pending certificate request
        
        Args:
            request_id: Certificate request identifier
            reason: Cancellation reason
            
        Returns:
            True if cancelled successfully
        """
        try:
            if not self.db:
                return False
            
            request_data = self.db.query(LegacyCertificateRequest).filter(
                LegacyCertificateRequest.request_id == request_id
            ).first()
            
            if not request_data:
                return False
            
            if request_data.status != "pending":
                logger.warning(f"Cannot cancel request in status: {request_data.status}")
                return False
            
            request_data.status = "cancelled"
            request_data.error_message = reason
            request_data.updated_at = datetime.now()
            
            self.db.commit()
            
            logger.info(f"Cancelled certificate request: {request_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error cancelling request {request_id}: {str(e)}")
            return False
    
    def get_service_statistics(self) -> Dict[str, Any]:
        """Get certificate request service statistics"""
        stats = {
            'ca_integration': self.ca_integration.get_ca_statistics(),
            'certificate_store': self.certificate_store.get_storage_statistics(),
            'service_info': {
                'legacy_db_connected': self.db is not None,
                'timestamp': datetime.now().isoformat()
            }
        }
        
        if self.db:
            try:
                # Get request statistics from database
                total_requests = self.db.query(LegacyCertificateRequest).count()
                pending_requests = self.db.query(LegacyCertificateRequest).filter(
                    LegacyCertificateRequest.status == "pending"
                ).count()
                completed_requests = self.db.query(LegacyCertificateRequest).filter(
                    LegacyCertificateRequest.status == "completed"
                ).count()
                
                stats['request_statistics'] = {
                    'total_requests': total_requests,
                    'pending_requests': pending_requests,
                    'completed_requests': completed_requests,
                    'completion_rate': (completed_requests / total_requests * 100) if total_requests > 0 else 0
                }
                
            except Exception as e:
                logger.warning(f"Could not get request statistics: {str(e)}")
        
        return stats


# Backward compatibility functions
def create_certificate_request(
    subject_info: Dict[str, str],
    organization_id: str,
    certificate_type: str = "signing"
) -> Tuple[str, str, str]:
    """Backward compatibility function"""
    service = CertificateRequestService()
    return service.create_certificate_request(subject_info, organization_id, certificate_type)

def get_request_status(request_id: str) -> Optional[Dict[str, Any]]:
    """Backward compatibility function"""
    service = CertificateRequestService()
    return service.get_request_status(request_id)