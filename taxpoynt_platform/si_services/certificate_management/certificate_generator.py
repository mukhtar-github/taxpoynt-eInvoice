"""
Certificate Generator

Handles generation of digital certificates for System Integrator role.
Provides X.509 certificate creation, self-signed certificates, and CSR generation.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple, List
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID, ExtensionOID


class CertificateGenerator:
    """Generate digital certificates for FIRS compliance"""
    
    def __init__(self):
        self.default_key_size = 2048
        self.default_validity_days = 365
        self.logger = logging.getLogger(__name__)
    
    def generate_self_signed_certificate(
        self,
        subject_info: Dict[str, str],
        validity_days: Optional[int] = None,
        key_size: Optional[int] = None
    ) -> Tuple[bytes, bytes]:
        """
        Generate a self-signed certificate
        
        Args:
            subject_info: Certificate subject information
            validity_days: Certificate validity period in days
            key_size: Private key size in bits
            
        Returns:
            Tuple of (certificate_pem, private_key_pem)
        """
        try:
            validity_days = validity_days or self.default_validity_days
            key_size = key_size or self.default_key_size
            
            # Generate private key
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=key_size,
                backend=default_backend()
            )
            
            # Create certificate subject
            subject = self._create_subject(subject_info)
            
            # Create certificate
            certificate = x509.CertificateBuilder().subject_name(
                subject
            ).issuer_name(
                subject  # Self-signed, so issuer = subject
            ).public_key(
                private_key.public_key()
            ).serial_number(
                x509.random_serial_number()
            ).not_valid_before(
                datetime.utcnow()
            ).not_valid_after(
                datetime.utcnow() + timedelta(days=validity_days)
            ).add_extension(
                x509.SubjectAlternativeName([
                    x509.DNSName(subject_info.get('common_name', 'localhost')),
                ]),
                critical=False,
            ).add_extension(
                x509.BasicConstraints(ca=True, path_length=0),
                critical=True,
            ).add_extension(
                x509.KeyUsage(
                    digital_signature=True,
                    key_encipherment=True,
                    key_cert_sign=True,
                    crl_sign=True,
                    content_commitment=False,
                    data_encipherment=False,
                    key_agreement=False,
                    encipher_only=False,
                    decipher_only=False
                ),
                critical=True,
            ).sign(private_key, hashes.SHA256(), default_backend())
            
            # Serialize certificate and key to PEM
            cert_pem = certificate.public_bytes(serialization.Encoding.PEM)
            key_pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
            
            self.logger.info(f"Generated self-signed certificate for {subject_info.get('common_name')}")
            
            return cert_pem, key_pem
            
        except Exception as e:
            self.logger.error(f"Error generating self-signed certificate: {str(e)}")
            raise
    
    def generate_certificate_request(
        self,
        subject_info: Dict[str, str],
        key_size: Optional[int] = None
    ) -> Tuple[bytes, bytes]:
        """
        Generate a Certificate Signing Request (CSR)
        
        Args:
            subject_info: Certificate subject information
            key_size: Private key size in bits
            
        Returns:
            Tuple of (csr_pem, private_key_pem)
        """
        try:
            key_size = key_size or self.default_key_size
            
            # Generate private key
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=key_size,
                backend=default_backend()
            )
            
            # Create certificate subject
            subject = self._create_subject(subject_info)
            
            # Create CSR
            csr = x509.CertificateSigningRequestBuilder().subject_name(
                subject
            ).add_extension(
                x509.SubjectAlternativeName([
                    x509.DNSName(subject_info.get('common_name', 'localhost')),
                ]),
                critical=False,
            ).sign(private_key, hashes.SHA256(), default_backend())
            
            # Serialize CSR and key to PEM
            csr_pem = csr.public_bytes(serialization.Encoding.PEM)
            key_pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
            
            self.logger.info(f"Generated CSR for {subject_info.get('common_name')}")
            
            return csr_pem, key_pem
            
        except Exception as e:
            self.logger.error(f"Error generating CSR: {str(e)}")
            raise
    
    def generate_firs_compliant_certificate(
        self,
        organization_info: Dict[str, str],
        validity_days: Optional[int] = None
    ) -> Tuple[bytes, bytes]:
        """
        Generate FIRS-compliant certificate with required extensions
        
        Args:
            organization_info: Organization information for certificate
            validity_days: Certificate validity period
            
        Returns:
            Tuple of (certificate_pem, private_key_pem)
        """
        try:
            # Add FIRS-specific subject information
            subject_info = {
                'country_name': 'NG',  # Nigeria
                'state_or_province_name': organization_info.get('state', ''),
                'locality_name': organization_info.get('city', ''),
                'organization_name': organization_info.get('organization_name', ''),
                'organizational_unit_name': 'FIRS E-Invoice',
                'common_name': organization_info.get('common_name', ''),
                'email_address': organization_info.get('email', '')
            }
            
            validity_days = validity_days or 730  # 2 years for FIRS compliance
            
            # Generate certificate with FIRS-specific extensions
            cert_pem, key_pem = self.generate_self_signed_certificate(
                subject_info=subject_info,
                validity_days=validity_days
            )
            
            self.logger.info(f"Generated FIRS-compliant certificate for {organization_info.get('organization_name')}")
            
            return cert_pem, key_pem
            
        except Exception as e:
            self.logger.error(f"Error generating FIRS-compliant certificate: {str(e)}")
            raise
    
    def _create_subject(self, subject_info: Dict[str, str]) -> x509.Name:
        """Create X.509 subject from information dictionary"""
        subject_components = []
        
        # Add subject components if provided
        if subject_info.get('country_name'):
            subject_components.append(x509.NameAttribute(NameOID.COUNTRY_NAME, subject_info['country_name']))
        
        if subject_info.get('state_or_province_name'):
            subject_components.append(x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, subject_info['state_or_province_name']))
        
        if subject_info.get('locality_name'):
            subject_components.append(x509.NameAttribute(NameOID.LOCALITY_NAME, subject_info['locality_name']))
        
        if subject_info.get('organization_name'):
            subject_components.append(x509.NameAttribute(NameOID.ORGANIZATION_NAME, subject_info['organization_name']))
        
        if subject_info.get('organizational_unit_name'):
            subject_components.append(x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, subject_info['organizational_unit_name']))
        
        if subject_info.get('common_name'):
            subject_components.append(x509.NameAttribute(NameOID.COMMON_NAME, subject_info['common_name']))
        
        if subject_info.get('email_address'):
            subject_components.append(x509.NameAttribute(NameOID.EMAIL_ADDRESS, subject_info['email_address']))
        
        return x509.Name(subject_components)
    
    def validate_certificate_info(self, subject_info: Dict[str, str]) -> Tuple[bool, List[str]]:
        """
        Validate certificate subject information
        
        Args:
            subject_info: Certificate subject information
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        # Required fields
        required_fields = ['common_name', 'organization_name']
        for field in required_fields:
            if not subject_info.get(field):
                errors.append(f"Missing required field: {field}")
        
        # Validate email format if provided
        email = subject_info.get('email_address')
        if email and '@' not in email:
            errors.append("Invalid email address format")
        
        # Validate country code
        country = subject_info.get('country_name')
        if country and len(country) != 2:
            errors.append("Country name must be 2-letter ISO code")
        
        return len(errors) == 0, errors
    
    def extract_certificate_info(self, cert_pem: bytes) -> Dict[str, Any]:
        """
        Extract information from certificate PEM
        
        Args:
            cert_pem: Certificate in PEM format
            
        Returns:
            Dictionary with certificate information
        """
        try:
            certificate = x509.load_pem_x509_certificate(cert_pem, default_backend())
            
            # Extract subject information
            subject_info = {}
            for attribute in certificate.subject:
                if attribute.oid == NameOID.COMMON_NAME:
                    subject_info['common_name'] = attribute.value
                elif attribute.oid == NameOID.ORGANIZATION_NAME:
                    subject_info['organization_name'] = attribute.value
                elif attribute.oid == NameOID.COUNTRY_NAME:
                    subject_info['country_name'] = attribute.value
                elif attribute.oid == NameOID.EMAIL_ADDRESS:
                    subject_info['email_address'] = attribute.value
            
            # Extract issuer information
            issuer_info = {}
            for attribute in certificate.issuer:
                if attribute.oid == NameOID.COMMON_NAME:
                    issuer_info['common_name'] = attribute.value
                elif attribute.oid == NameOID.ORGANIZATION_NAME:
                    issuer_info['organization_name'] = attribute.value
            
            return {
                'subject': subject_info,
                'issuer': issuer_info,
                'serial_number': str(certificate.serial_number),
                'not_valid_before': certificate.not_valid_before.isoformat(),
                'not_valid_after': certificate.not_valid_after.isoformat(),
                'is_self_signed': certificate.issuer == certificate.subject,
                'key_size': certificate.public_key().key_size,
                'signature_algorithm': certificate.signature_algorithm_oid._name
            }
            
        except Exception as e:
            self.logger.error(f"Error extracting certificate info: {str(e)}")
            raise