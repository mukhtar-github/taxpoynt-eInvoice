"""
Digital Certificate Service (Refactored)

Refactored digital certificate service that uses granular components.
Handles advanced certificate operations, digital signatures, and cryptographic operations.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from sqlalchemy.orm import Session

# Import granular components
from .certificate_generator import CertificateGenerator
from .key_manager import KeyManager
from .certificate_store import CertificateStore, CertificateStatus
from .lifecycle_manager import LifecycleManager
from .ca_integration import CAIntegration

# Legacy imports for backward compatibility
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
import base64

logger = logging.getLogger(__name__)


class DigitalCertificateService:
    """
    Refactored Digital Certificate Service using granular components.
    
    Provides advanced certificate operations including digital signatures,
    certificate chain validation, and cryptographic operations.
    """
    
    def __init__(self, db: Optional[Session] = None):
        self.db = db
        
        # Initialize granular components
        self.certificate_generator = CertificateGenerator()
        self.key_manager = KeyManager()
        self.certificate_store = CertificateStore()
        self.lifecycle_manager = LifecycleManager(
            certificate_store=self.certificate_store,
            certificate_generator=self.certificate_generator,
            key_manager=self.key_manager
        )
        self.ca_integration = CAIntegration()
    
    def sign_data(
        self,
        data: str,
        certificate_id: str,
        private_key_path: Optional[str] = None,
        passphrase: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Sign data using certificate's private key
        
        Args:
            data: Data to sign
            certificate_id: Certificate ID for signing
            private_key_path: Path to private key (optional)
            passphrase: Private key passphrase (if encrypted)
            
        Returns:
            Signature information
        """
        try:
            # Get certificate info
            cert_info = self.certificate_store.get_certificate_info(certificate_id)
            if not cert_info:
                raise ValueError(f"Certificate not found: {certificate_id}")
            
            # Retrieve certificate
            cert_pem = self.certificate_store.retrieve_certificate(certificate_id)
            if not cert_pem:
                raise ValueError("Could not retrieve certificate")
            
            # Load private key
            if private_key_path:
                private_key_pem = self.key_manager.load_key(private_key_path, passphrase)
            else:
                # Try to find associated private key
                stored_keys = self.key_manager.list_stored_keys()
                private_key_pem = None
                
                # Look for key with similar name/timestamp
                for key_info in stored_keys:
                    if (cert_info.subject_cn.lower() in key_info['filename'].lower() or
                        certificate_id in key_info['filename']):
                        private_key_pem = self.key_manager.load_key(key_info['path'], passphrase)
                        break
                
                if not private_key_pem:
                    raise ValueError("Private key not found for certificate")
            
            # Load private key object
            private_key = serialization.load_pem_private_key(
                private_key_pem,
                password=passphrase.encode() if passphrase else None,
                backend=default_backend()
            )
            
            # Sign data
            data_bytes = data.encode('utf-8')
            signature = private_key.sign(
                data_bytes,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            
            # Create signature info
            signature_info = {
                'signature': base64.b64encode(signature).decode('utf-8'),
                'algorithm': 'RSA-PSS-SHA256',
                'certificate_id': certificate_id,
                'certificate_fingerprint': cert_info.fingerprint,
                'signed_at': datetime.now().isoformat(),
                'data_hash': hashes.Hash(hashes.SHA256(), backend=default_backend())
            }
            
            # Calculate data hash for verification
            digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
            digest.update(data_bytes)
            signature_info['data_hash'] = base64.b64encode(digest.finalize()).decode('utf-8')
            
            logger.info(f"Successfully signed data with certificate: {certificate_id}")
            
            return signature_info
            
        except Exception as e:
            logger.error(f"Error signing data with certificate {certificate_id}: {str(e)}")
            raise
    
    def verify_signature(
        self,
        data: str,
        signature_info: Dict[str, Any],
        certificate_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Verify digital signature
        
        Args:
            data: Original data that was signed
            signature_info: Signature information from sign_data
            certificate_id: Certificate ID to verify against (optional)
            
        Returns:
            Verification result
        """
        try:
            # Use certificate from signature info if not provided
            cert_id = certificate_id or signature_info.get('certificate_id')
            if not cert_id:
                raise ValueError("Certificate ID not provided")
            
            # Retrieve certificate
            cert_pem = self.certificate_store.retrieve_certificate(cert_id)
            if not cert_pem:
                raise ValueError(f"Certificate not found: {cert_id}")
            
            # Load certificate and extract public key
            certificate = x509.load_pem_x509_certificate(cert_pem, default_backend())
            public_key = certificate.public_key()
            
            # Decode signature
            signature_bytes = base64.b64decode(signature_info['signature'])
            data_bytes = data.encode('utf-8')
            
            # Verify signature
            try:
                public_key.verify(
                    signature_bytes,
                    data_bytes,
                    padding.PSS(
                        mgf=padding.MGF1(hashes.SHA256()),
                        salt_length=padding.PSS.MAX_LENGTH
                    ),
                    hashes.SHA256()
                )
                signature_valid = True
                verification_error = None
                
            except Exception as e:
                signature_valid = False
                verification_error = str(e)
            
            # Verify data hash
            digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
            digest.update(data_bytes)
            calculated_hash = base64.b64encode(digest.finalize()).decode('utf-8')
            data_hash_valid = calculated_hash == signature_info.get('data_hash')
            
            # Check certificate validity
            cert_validation = self.ca_integration.validate_certificate_chain(cert_pem)
            
            verification_result = {
                'is_valid': signature_valid and data_hash_valid and cert_validation[0],
                'signature_valid': signature_valid,
                'data_hash_valid': data_hash_valid,
                'certificate_valid': cert_validation[0],
                'certificate_errors': cert_validation[1],
                'verification_error': verification_error,
                'verified_at': datetime.now().isoformat(),
                'certificate_id': cert_id,
                'algorithm': signature_info.get('algorithm', 'unknown')
            }
            
            logger.info(f"Signature verification completed: {'valid' if verification_result['is_valid'] else 'invalid'}")
            
            return verification_result
            
        except Exception as e:
            logger.error(f"Error verifying signature: {str(e)}")
            return {
                'is_valid': False,
                'verification_error': str(e),
                'verified_at': datetime.now().isoformat()
            }
    
    def create_certificate_chain(
        self,
        certificate_id: str,
        include_root: bool = True
    ) -> List[str]:
        """
        Create certificate chain for certificate
        
        Args:
            certificate_id: Certificate ID
            include_root: Whether to include root CA certificate
            
        Returns:
            List of certificates in PEM format (leaf to root)
        """
        try:
            # Get certificate
            cert_pem = self.certificate_store.retrieve_certificate(certificate_id)
            if not cert_pem:
                raise ValueError(f"Certificate not found: {certificate_id}")
            
            chain = [cert_pem.decode('utf-8')]
            
            # Load certificate to check issuer
            certificate = x509.load_pem_x509_certificate(cert_pem, default_backend())
            
            # If self-signed, return just the certificate
            if certificate.issuer == certificate.subject:
                return chain
            
            # Try to find issuer certificate in registered CAs
            issuer_dn = str(certificate.issuer)
            
            for ca_id, ca_info in self.ca_integration.cas.items():
                ca_cert = x509.load_pem_x509_certificate(ca_info.certificate_pem, default_backend())
                
                if str(ca_cert.subject) == issuer_dn:
                    if include_root:
                        chain.append(ca_info.certificate_pem.decode('utf-8'))
                    break
            
            logger.info(f"Created certificate chain with {len(chain)} certificates")
            
            return chain
            
        except Exception as e:
            logger.error(f"Error creating certificate chain: {str(e)}")
            raise
    
    def export_certificate(
        self,
        certificate_id: str,
        format_type: str = "pem",
        include_chain: bool = False,
        include_private_key: bool = False,
        passphrase: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Export certificate in various formats
        
        Args:
            certificate_id: Certificate ID
            format_type: Export format (pem, der, p12, jks)
            include_chain: Include certificate chain
            include_private_key: Include private key (for supported formats)
            passphrase: Passphrase for private key protection
            
        Returns:
            Export result with certificate data
        """
        try:
            # Get certificate
            cert_pem = self.certificate_store.retrieve_certificate(certificate_id)
            if not cert_pem:
                raise ValueError(f"Certificate not found: {certificate_id}")
            
            export_result = {
                'certificate_id': certificate_id,
                'format': format_type,
                'exported_at': datetime.now().isoformat()
            }
            
            if format_type.lower() == "pem":
                export_result['certificate_pem'] = cert_pem.decode('utf-8')
                
                if include_chain:
                    chain = self.create_certificate_chain(certificate_id)
                    export_result['certificate_chain'] = chain
                
                if include_private_key:
                    # Try to find private key
                    stored_keys = self.key_manager.list_stored_keys()
                    cert_info = self.certificate_store.get_certificate_info(certificate_id)
                    
                    for key_info in stored_keys:
                        if cert_info.subject_cn.lower() in key_info['filename'].lower():
                            private_key_pem = self.key_manager.load_key(key_info['path'])
                            export_result['private_key_pem'] = private_key_pem.decode('utf-8')
                            break
            
            elif format_type.lower() == "der":
                # Convert PEM to DER
                certificate = x509.load_pem_x509_certificate(cert_pem, default_backend())
                der_data = certificate.public_bytes(serialization.Encoding.DER)
                export_result['certificate_der'] = base64.b64encode(der_data).decode('utf-8')
            
            else:
                raise ValueError(f"Unsupported export format: {format_type}")
            
            logger.info(f"Exported certificate {certificate_id} in {format_type} format")
            
            return export_result
            
        except Exception as e:
            logger.error(f"Error exporting certificate: {str(e)}")
            raise
    
    def validate_certificate_chain(
        self,
        certificate_id: str,
        intermediate_certs: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Validate certificate chain using CA integration
        
        Args:
            certificate_id: Certificate ID to validate
            intermediate_certs: List of intermediate certificates (PEM format)
            
        Returns:
            Chain validation result
        """
        try:
            # Get certificate
            cert_pem = self.certificate_store.retrieve_certificate(certificate_id)
            if not cert_pem:
                raise ValueError(f"Certificate not found: {certificate_id}")
            
            # Convert intermediate certs to bytes
            intermediate_cert_bytes = None
            if intermediate_certs:
                intermediate_cert_bytes = [cert.encode('utf-8') for cert in intermediate_certs]
            
            # Validate chain using CA integration
            is_valid, validation_errors, chain_info = self.ca_integration.validate_certificate_chain(
                certificate_pem=cert_pem,
                intermediate_certs=intermediate_cert_bytes
            )
            
            # Check revocation status
            is_revoked, revocation_info = self.ca_integration.check_certificate_revocation(cert_pem)
            
            validation_result = {
                'certificate_id': certificate_id,
                'is_valid': is_valid and not is_revoked,
                'is_revoked': is_revoked,
                'validation_errors': validation_errors,
                'chain_info': chain_info,
                'revocation_info': revocation_info,
                'validated_at': datetime.now().isoformat()
            }
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Error validating certificate chain: {str(e)}")
            raise
    
    def get_certificate_details(self, certificate_id: str) -> Dict[str, Any]:
        """
        Get comprehensive certificate details
        
        Args:
            certificate_id: Certificate ID
            
        Returns:
            Detailed certificate information
        """
        try:
            # Get certificate info from store
            cert_info = self.certificate_store.get_certificate_info(certificate_id)
            if not cert_info:
                raise ValueError(f"Certificate not found: {certificate_id}")
            
            # Get certificate PEM
            cert_pem = self.certificate_store.retrieve_certificate(certificate_id)
            
            # Extract detailed information
            detailed_info = self.certificate_generator.extract_certificate_info(cert_pem)
            
            # Get validation status
            validation_result = self.validate_certificate_chain(certificate_id)
            
            # Check if expiring
            not_after = datetime.fromisoformat(cert_info.not_after)
            days_until_expiry = (not_after - datetime.now()).days
            
            comprehensive_details = {
                'basic_info': {
                    'certificate_id': cert_info.certificate_id,
                    'subject_cn': cert_info.subject_cn,
                    'issuer_cn': cert_info.issuer_cn,
                    'serial_number': cert_info.serial_number,
                    'fingerprint': cert_info.fingerprint,
                    'status': cert_info.status.value,
                    'certificate_type': cert_info.certificate_type,
                    'organization_id': cert_info.organization_id
                },
                'validity_info': {
                    'not_before': cert_info.not_before,
                    'not_after': cert_info.not_after,
                    'days_until_expiry': days_until_expiry,
                    'is_expired': days_until_expiry < 0,
                    'is_expiring_soon': 0 <= days_until_expiry <= 30
                },
                'technical_details': detailed_info,
                'validation_status': validation_result,
                'metadata': cert_info.metadata,
                'timestamps': {
                    'created_at': cert_info.created_at,
                    'updated_at': cert_info.updated_at
                }
            }
            
            return comprehensive_details
            
        except Exception as e:
            logger.error(f"Error getting certificate details: {str(e)}")
            raise
    
    def perform_compliance_check(
        self,
        certificate_id: str,
        compliance_standard: str = "firs"
    ) -> Dict[str, Any]:
        """
        Perform compliance check for specific standard
        
        Args:
            certificate_id: Certificate ID
            compliance_standard: Standard to check against (firs, iso, etc.)
            
        Returns:
            Compliance check result
        """
        try:
            # Get certificate details
            cert_details = self.get_certificate_details(certificate_id)
            
            compliance_result = {
                'certificate_id': certificate_id,
                'compliance_standard': compliance_standard,
                'is_compliant': True,
                'issues': [],
                'recommendations': [],
                'checked_at': datetime.now().isoformat()
            }
            
            if compliance_standard.lower() == "firs":
                # FIRS-specific compliance checks
                
                # Check validity period (max 2 years for FIRS)
                validity_days = (
                    datetime.fromisoformat(cert_details['validity_info']['not_after']) -
                    datetime.fromisoformat(cert_details['validity_info']['not_before'])
                ).days
                
                if validity_days > 730:  # 2 years
                    compliance_result['is_compliant'] = False
                    compliance_result['issues'].append(f"Validity period too long: {validity_days} days (max 730 for FIRS)")
                
                # Check for Nigeria-specific information
                subject_info = cert_details['technical_details']['subject']
                if subject_info.get('country_name') != 'NG':
                    compliance_result['issues'].append("Certificate should specify Nigeria (NG) as country")
                
                # Check key size
                key_size = cert_details['technical_details']['key_size']
                if key_size < 2048:
                    compliance_result['is_compliant'] = False
                    compliance_result['issues'].append(f"Key size too small: {key_size} bits (min 2048 for FIRS)")
                
                # Check if certificate is expired
                if cert_details['validity_info']['is_expired']:
                    compliance_result['is_compliant'] = False
                    compliance_result['issues'].append("Certificate has expired")
                
                # Generate recommendations
                if not compliance_result['is_compliant']:
                    compliance_result['recommendations'].extend([
                        "Renew certificate with FIRS-compliant settings",
                        "Ensure validity period is 2 years or less",
                        "Use minimum 2048-bit RSA keys",
                        "Include Nigerian organization information"
                    ])
            
            return compliance_result
            
        except Exception as e:
            logger.error(f"Error performing compliance check: {str(e)}")
            raise
    
    def get_service_statistics(self) -> Dict[str, Any]:
        """Get comprehensive service statistics"""
        return {
            'certificate_store': self.certificate_store.get_storage_statistics(),
            'lifecycle_manager': self.lifecycle_manager.check_certificate_expiration(),
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
def sign_data(data: str, certificate_id: str, private_key_path: str) -> Dict[str, Any]:
    """Backward compatibility function"""
    service = DigitalCertificateService()
    return service.sign_data(data, certificate_id, private_key_path)

def verify_signature(data: str, signature_info: Dict[str, Any]) -> bool:
    """Backward compatibility function"""
    service = DigitalCertificateService()
    result = service.verify_signature(data, signature_info)
    return result['is_valid']