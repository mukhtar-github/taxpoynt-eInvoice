"""
Certificate Service (Refactored)

Refactored certificate service that uses granular components to eliminate duplication.
Maintains backward compatibility while leveraging the new architecture.
"""

import base64
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any, Union
from uuid import UUID
from sqlalchemy.orm import Session

# Import granular components
from .certificate_generator import CertificateGenerator
from .key_manager import KeyManager
from .certificate_store import CertificateStore, CertificateStatus
from .lifecycle_manager import LifecycleManager
from .ca_integration import CAIntegration

# Import authentication services for certificate-based auth
from taxpoynt_platform.si_services.authentication import (
    CertificateAuth,
    AuthenticationManager,
    AuthenticationError
)

# Legacy imports for backward compatibility
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from app.models.certificate import Certificate, CertificateRevocation, CertificateType, CertificateStatus as LegacyCertificateStatus
from app.schemas.certificate import CertificateCreate, CertificateUpdate, CertificateVerification
from app.services.key_service import KeyManagementService
from app.utils.encryption import encrypt_field, decrypt_field

logger = logging.getLogger(__name__)


class CertificateService:
    """
    Refactored Certificate Service using granular components.
    
    This service maintains the same interface as the original monolithic service
    but delegates all functionality to the appropriate granular components.
    """
    
    def __init__(
        self, 
        db: Session,
        key_service: Optional[KeyManagementService] = None,
        auth_manager: Optional[AuthenticationManager] = None
    ):
        self.db = db
        self.legacy_key_service = key_service
        
        # Initialize granular components
        self.certificate_generator = CertificateGenerator()
        
        # Initialize authentication services
        self.auth_manager = auth_manager or AuthenticationManager()
        self.certificate_auth = CertificateAuth()
        self.key_manager = KeyManager()
        self.certificate_store = CertificateStore()
        self.lifecycle_manager = LifecycleManager(
            certificate_store=self.certificate_store,
            certificate_generator=self.certificate_generator,
            key_manager=self.key_manager
        )
        self.ca_integration = CAIntegration()
    
    def extract_certificate_metadata(self, certificate_data: str) -> Dict[str, Any]:
        """
        Extract metadata from a PEM encoded certificate using granular components
        
        Args:
            certificate_data: PEM encoded certificate
            
        Returns:
            Dictionary containing certificate metadata
        """
        try:
            certificate_pem = certificate_data.encode('utf-8') if isinstance(certificate_data, str) else certificate_data
            
            # Use certificate generator to extract info
            cert_info = self.certificate_generator.extract_certificate_info(certificate_pem)
            
            # Convert to legacy format for backward compatibility
            metadata = {
                'subject': cert_info['subject'],
                'issuer': cert_info['issuer'],
                'serial_number': cert_info['serial_number'],
                'not_valid_before': cert_info['not_valid_before'],
                'not_valid_after': cert_info['not_valid_after'],
                'is_self_signed': cert_info['is_self_signed'],
                'key_size': cert_info['key_size'],
                'signature_algorithm': cert_info['signature_algorithm'],
                'extracted_at': datetime.now().isoformat()
            }
            
            logger.info(f"Extracted certificate metadata for {cert_info['subject'].get('common_name', 'unknown')}")
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error extracting certificate metadata: {str(e)}")
            raise
    
    def store_certificate(
        self,
        certificate_data: str,
        organization_id: str,
        certificate_type: str = "signing",
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Store certificate using granular certificate store
        
        Args:
            certificate_data: PEM encoded certificate
            organization_id: Organization identifier
            certificate_type: Type of certificate
            metadata: Additional metadata
            
        Returns:
            Certificate ID
        """
        try:
            certificate_pem = certificate_data.encode('utf-8') if isinstance(certificate_data, str) else certificate_data
            
            # Store using granular component
            certificate_id = self.certificate_store.store_certificate(
                certificate_pem=certificate_pem,
                organization_id=organization_id,
                certificate_type=certificate_type,
                metadata=metadata
            )
            
            # Also store in legacy database for backward compatibility
            if self.db:
                try:
                    cert_metadata = self.extract_certificate_metadata(certificate_data)
                    
                    legacy_cert = Certificate(
                        certificate_id=certificate_id,
                        certificate_data=certificate_data,
                        organization_id=organization_id,
                        certificate_type=certificate_type,
                        status=LegacyCertificateStatus.ACTIVE,
                        metadata=cert_metadata,
                        created_at=datetime.now()
                    )
                    
                    self.db.add(legacy_cert)
                    self.db.commit()
                    
                except Exception as e:
                    logger.warning(f"Could not store in legacy database: {str(e)}")
            
            logger.info(f"Stored certificate: {certificate_id}")
            
            return certificate_id
            
        except Exception as e:
            logger.error(f"Error storing certificate: {str(e)}")
            raise
    
    def retrieve_certificate(self, certificate_id: str) -> Optional[str]:
        """
        Retrieve certificate by ID using granular store
        
        Args:
            certificate_id: Certificate identifier
            
        Returns:
            Certificate data in PEM format or None
        """
        try:
            certificate_pem = self.certificate_store.retrieve_certificate(certificate_id)
            
            if certificate_pem:
                return certificate_pem.decode('utf-8')
            
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving certificate {certificate_id}: {str(e)}")
            return None
    
    def validate_certificate(self, certificate_data: str) -> Dict[str, Any]:
        """
        Validate certificate using granular components
        
        Args:
            certificate_data: PEM encoded certificate
            
        Returns:
            Validation result
        """
        try:
            certificate_pem = certificate_data.encode('utf-8') if isinstance(certificate_data, str) else certificate_data
            
            # Use CA integration for validation
            is_valid, validation_errors, chain_info = self.ca_integration.validate_certificate_chain(certificate_pem)
            
            # Check revocation status
            is_revoked, revocation_info = self.ca_integration.check_certificate_revocation(certificate_pem)
            
            validation_result = {
                'is_valid': is_valid and not is_revoked,
                'is_revoked': is_revoked,
                'validation_errors': validation_errors,
                'chain_info': chain_info,
                'revocation_info': revocation_info,
                'validated_at': datetime.now().isoformat()
            }
            
            logger.info(f"Certificate validation completed: {'valid' if validation_result['is_valid'] else 'invalid'}")
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Error validating certificate: {str(e)}")
            return {
                'is_valid': False,
                'validation_errors': [str(e)],
                'validated_at': datetime.now().isoformat()
            }
    
    def generate_certificate(
        self,
        subject_info: Dict[str, str],
        organization_id: str,
        validity_days: int = 365,
        certificate_type: str = "signing"
    ) -> Tuple[str, str]:
        """
        Generate new certificate using granular generator
        
        Args:
            subject_info: Certificate subject information
            organization_id: Organization identifier
            validity_days: Certificate validity period
            certificate_type: Type of certificate
            
        Returns:
            Tuple of (certificate_id, certificate_pem)
        """
        try:
            # Validate subject info
            is_valid, validation_errors = self.certificate_generator.validate_certificate_info(subject_info)
            if not is_valid:
                raise ValueError(f"Invalid subject info: {', '.join(validation_errors)}")
            
            # Generate certificate
            cert_pem, key_pem = self.certificate_generator.generate_self_signed_certificate(
                subject_info=subject_info,
                validity_days=validity_days
            )
            
            # Store certificate
            certificate_id = self.store_certificate(
                certificate_data=cert_pem.decode('utf-8'),
                organization_id=organization_id,
                certificate_type=certificate_type,
                metadata={
                    'generated_by': 'certificate_service',
                    'generation_method': 'self_signed',
                    'validity_days': validity_days
                }
            )
            
            # Store private key
            key_name = f"{subject_info.get('common_name', 'cert')}_{datetime.now().strftime('%Y%m%d')}"
            self.key_manager.store_key(key_pem, key_name, "private")
            
            logger.info(f"Generated certificate: {certificate_id} for {subject_info.get('common_name')}")
            
            return certificate_id, cert_pem.decode('utf-8')
            
        except Exception as e:
            logger.error(f"Error generating certificate: {str(e)}")
            raise
    
    def renew_certificate(self, certificate_id: str, validity_days: int = 365) -> Tuple[str, bool]:
        """
        Renew certificate using lifecycle manager
        
        Args:
            certificate_id: Certificate to renew
            validity_days: New validity period
            
        Returns:
            Tuple of (new_certificate_id, success)
        """
        try:
            new_cert_id, success = self.lifecycle_manager.renew_certificate(
                certificate_id=certificate_id,
                validity_days=validity_days
            )
            
            if success:
                logger.info(f"Renewed certificate: {certificate_id} -> {new_cert_id}")
            
            return new_cert_id, success
            
        except Exception as e:
            logger.error(f"Error renewing certificate {certificate_id}: {str(e)}")
            return "", False
    
    def revoke_certificate(self, certificate_id: str, reason: str) -> bool:
        """
        Revoke certificate using lifecycle manager
        
        Args:
            certificate_id: Certificate to revoke
            reason: Revocation reason
            
        Returns:
            True if revoked successfully
        """
        try:
            success = self.lifecycle_manager.revoke_certificate(
                certificate_id=certificate_id,
                reason=reason
            )
            
            # Also update legacy database
            if self.db and success:
                try:
                    cert = self.db.query(Certificate).filter(
                        Certificate.certificate_id == certificate_id
                    ).first()
                    
                    if cert:
                        cert.status = LegacyCertificateStatus.REVOKED
                        cert.updated_at = datetime.now()
                        self.db.commit()
                        
                except Exception as e:
                    logger.warning(f"Could not update legacy database: {str(e)}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error revoking certificate {certificate_id}: {str(e)}")
            return False
    
    def list_certificates(
        self,
        organization_id: Optional[str] = None,
        certificate_type: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List certificates using granular store
        
        Args:
            organization_id: Filter by organization
            certificate_type: Filter by certificate type
            status: Filter by status
            
        Returns:
            List of certificate information
        """
        try:
            # Convert status to granular component enum
            cert_status = None
            if status:
                status_mapping = {
                    'active': CertificateStatus.ACTIVE,
                    'expired': CertificateStatus.EXPIRED,
                    'revoked': CertificateStatus.REVOKED,
                    'archived': CertificateStatus.ARCHIVED
                }
                cert_status = status_mapping.get(status.lower())
            
            # Get certificates from granular store
            stored_certs = self.certificate_store.list_certificates(
                organization_id=organization_id,
                certificate_type=certificate_type,
                status=cert_status
            )
            
            # Convert to legacy format
            certificates = []
            for cert in stored_certs:
                certificates.append({
                    'certificate_id': cert.certificate_id,
                    'subject_cn': cert.subject_cn,
                    'issuer_cn': cert.issuer_cn,
                    'serial_number': cert.serial_number,
                    'not_before': cert.not_before,
                    'not_after': cert.not_after,
                    'status': cert.status.value,
                    'organization_id': cert.organization_id,
                    'certificate_type': cert.certificate_type,
                    'created_at': cert.created_at,
                    'metadata': cert.metadata
                })
            
            return certificates
            
        except Exception as e:
            logger.error(f"Error listing certificates: {str(e)}")
            return []
    
    def check_expiring_certificates(self, days_ahead: int = 30) -> List[Dict[str, Any]]:
        """
        Check for expiring certificates using lifecycle manager
        
        Args:
            days_ahead: Number of days to look ahead
            
        Returns:
            List of expiring certificates
        """
        try:
            expiring_certs = self.certificate_store.check_expiring_certificates(days_ahead)
            
            # Convert to legacy format
            certificates = []
            for cert in expiring_certs:
                certificates.append({
                    'certificate_id': cert.certificate_id,
                    'subject_cn': cert.subject_cn,
                    'not_after': cert.not_after,
                    'days_until_expiry': (
                        datetime.fromisoformat(cert.not_after) - datetime.now()
                    ).days,
                    'organization_id': cert.organization_id,
                    'certificate_type': cert.certificate_type
                })
            
            return certificates
            
        except Exception as e:
            logger.error(f"Error checking expiring certificates: {str(e)}")
            return []
    
    def encrypt_data(self, data: str, certificate_id: str) -> str:
        """
        Encrypt data using certificate public key
        
        Args:
            data: Data to encrypt
            certificate_id: Certificate ID for encryption
            
        Returns:
            Base64 encoded encrypted data
        """
        try:
            # Retrieve certificate
            cert_pem = self.certificate_store.retrieve_certificate(certificate_id)
            if not cert_pem:
                raise ValueError(f"Certificate not found: {certificate_id}")
            
            # Load certificate and extract public key
            certificate = x509.load_pem_x509_certificate(cert_pem, default_backend())
            public_key_pem = certificate.public_key().public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            
            # Encrypt using key manager
            encrypted_data = self.key_manager.encrypt_data(
                data=data.encode('utf-8'),
                public_key_pem=public_key_pem
            )
            
            return base64.b64encode(encrypted_data).decode('utf-8')
            
        except Exception as e:
            logger.error(f"Error encrypting data with certificate {certificate_id}: {str(e)}")
            raise
    
    async def authenticate_with_certificate(
        self,
        certificate_data: Union[str, bytes],
        private_key_data: Optional[Union[str, bytes]] = None,
        target_service: str = "firs",
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Authenticate using certificate-based authentication
        
        Args:
            certificate_data: Certificate in PEM format
            private_key_data: Private key in PEM format (optional)
            target_service: Target service for authentication
            context: Additional authentication context
            
        Returns:
            Authentication result with auth data and status
        """
        try:
            # Validate certificate first
            validation_result = self.validate_certificate(certificate_data)
            if not validation_result.get('is_valid'):
                raise AuthenticationError(
                    f"Certificate validation failed: {validation_result.get('validation_errors', [])}"
                )
            
            # Prepare certificate auth data
            cert_bytes = certificate_data.encode('utf-8') if isinstance(certificate_data, str) else certificate_data
            key_bytes = None
            if private_key_data:
                key_bytes = private_key_data.encode('utf-8') if isinstance(private_key_data, str) else private_key_data
            
            # Use certificate authentication service
            auth_result = await self.certificate_auth.authenticate_certificate(
                certificate_data=cert_bytes,
                private_key_data=key_bytes,
                target_host=context.get('host') if context else None,
                verify_chain=True,
                context=context or {}
            )
            
            if auth_result.success:
                logger.info(f"Certificate authentication successful for {target_service}")
                return {
                    'success': True,
                    'auth_data': auth_result.auth_data,
                    'ssl_context': auth_result.ssl_context,
                    'expires_at': auth_result.expires_at,
                    'service': target_service
                }
            else:
                logger.error(f"Certificate authentication failed: {auth_result.error_message}")
                return {
                    'success': False,
                    'error': auth_result.error_message,
                    'service': target_service
                }
                
        except AuthenticationError as e:
            logger.error(f"Certificate authentication error: {e}")
            return {
                'success': False,
                'error': str(e),
                'service': target_service
            }
        except Exception as e:
            logger.error(f"Unexpected error during certificate authentication: {e}")
            return {
                'success': False,
                'error': f"Authentication failed: {str(e)}",
                'service': target_service
            }
    
    async def create_ssl_context_for_service(
        self,
        certificate_id: str,
        service_type: str = "firs"
    ) -> Optional[Any]:
        """
        Create SSL context for secure communication with external services
        
        Args:
            certificate_id: ID of the certificate to use
            service_type: Type of service (firs, erp, etc.)
            
        Returns:
            SSL context object or None if failed
        """
        try:
            # Get certificate data
            certificate_data = self.get_certificate(certificate_id)
            if not certificate_data:
                raise ValueError(f"Certificate not found: {certificate_id}")
            
            # Get private key if available
            cert_x509 = x509.load_pem_x509_certificate(
                certificate_data['certificate_data'].encode('utf-8'),
                default_backend()
            )
            
            # Try to find corresponding private key
            subject_cn = None
            for attr in cert_x509.subject:
                if attr.oid == x509.NameOID.COMMON_NAME:
                    subject_cn = attr.value
                    break
            
            private_key_data = None
            if subject_cn:
                try:
                    private_key_data = self.key_manager.get_key(f"{subject_cn}*", "private")
                except:
                    logger.warning(f"Private key not found for certificate {certificate_id}")
            
            # Create SSL context using certificate auth service
            ssl_context = await self.certificate_auth.create_ssl_context(
                certificate_data=certificate_data['certificate_data'].encode('utf-8'),
                private_key_data=private_key_data.encode('utf-8') if private_key_data else None,
                verify_peer=True
            )
            
            logger.info(f"Created SSL context for service {service_type} with certificate {certificate_id}")
            return ssl_context
            
        except Exception as e:
            logger.error(f"Failed to create SSL context: {e}")
            return None
    
    async def validate_service_certificate(
        self,
        service_url: str,
        certificate_data: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Validate certificate of an external service
        
        Args:
            service_url: URL of the service to validate
            certificate_data: Optional certificate data to validate against
            
        Returns:
            Validation result with certificate details
        """
        try:
            # Use certificate auth service for validation
            validation_result = await self.certificate_auth.validate_server_certificate(
                hostname=service_url.split('://')[1].split('/')[0],
                expected_cert=certificate_data.encode('utf-8') if certificate_data else None
            )
            
            if validation_result.success:
                logger.info(f"Service certificate validation successful for {service_url}")
                return {
                    'is_valid': True,
                    'certificate_info': validation_result.certificate_info,
                    'validation_details': validation_result.validation_details,
                    'verified_at': datetime.now().isoformat()
                }
            else:
                logger.warning(f"Service certificate validation failed for {service_url}: {validation_result.error_message}")
                return {
                    'is_valid': False,
                    'error': validation_result.error_message,
                    'verified_at': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error validating service certificate for {service_url}: {e}")
            return {
                'is_valid': False,
                'error': str(e),
                'verified_at': datetime.now().isoformat()
            }
    
    def get_service_statistics(self) -> Dict[str, Any]:
        """Get comprehensive service statistics"""
        return {
            'certificate_store': self.certificate_store.get_storage_statistics(),
            'lifecycle_manager': {
                'recent_events': len(self.lifecycle_manager.get_lifecycle_events(limit=100))
            },
            'ca_integration': self.ca_integration.get_ca_statistics(),
            'key_manager': {
                'stored_keys': len(self.key_manager.list_stored_keys())
            },
            'service_info': {
                'components_loaded': True,
                'legacy_db_connected': self.db is not None,
                'timestamp': datetime.now().isoformat()
            }
        }


# Backward compatibility functions
def extract_certificate_metadata(certificate_data: str) -> Dict[str, Any]:
    """Backward compatibility function"""
    service = CertificateService(db=None)
    return service.extract_certificate_metadata(certificate_data)

def validate_certificate_data(certificate_data: str) -> bool:
    """Backward compatibility function for certificate validation"""
    try:
        service = CertificateService(db=None)
        result = service.validate_certificate(certificate_data)
        return result['is_valid']
    except Exception:
        return False