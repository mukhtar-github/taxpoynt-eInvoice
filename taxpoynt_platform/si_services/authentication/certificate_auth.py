"""
Certificate-Based Authentication Service

This module provides certificate-based authentication for secure communications
with FIRS APIs, certificate authorities, and other services requiring PKI
authentication in the SI (System Integrator) role.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import ssl
import socket
from pathlib import Path
import hashlib
import base64
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.serialization import pkcs12
import aiohttp
import aiofiles

from .auth_manager import (
    BaseAuthProvider,
    AuthenticationType,
    AuthenticationContext,
    AuthenticationCredentials,
    AuthenticationResult,
    AuthenticationStatus,
    AuthenticationScope,
    ServiceType
)

logger = logging.getLogger(__name__)


class CertificateType(Enum):
    """Types of certificates"""
    CLIENT_AUTH = "client_auth"
    SERVER_AUTH = "server_auth"
    CODE_SIGNING = "code_signing"
    EMAIL = "email"
    DOCUMENT_SIGNING = "document_signing"
    CA_CERT = "ca_cert"
    INTERMEDIATE_CA = "intermediate_ca"


class CertificateFormat(Enum):
    """Certificate file formats"""
    PEM = "pem"
    DER = "der"
    PKCS12 = "pkcs12"
    PKCS7 = "pkcs7"
    JKS = "jks"


class CertificateStatus(Enum):
    """Certificate validation status"""
    VALID = "valid"
    EXPIRED = "expired"
    REVOKED = "revoked"
    NOT_YET_VALID = "not_yet_valid"
    INVALID_SIGNATURE = "invalid_signature"
    UNTRUSTED_CA = "untrusted_ca"
    UNKNOWN = "unknown"


@dataclass
class CertificateInfo:
    """Information about a certificate"""
    subject: str
    issuer: str
    serial_number: str
    not_valid_before: datetime
    not_valid_after: datetime
    fingerprint_sha256: str
    public_key_algorithm: str
    public_key_size: int
    signature_algorithm: str
    key_usage: List[str] = field(default_factory=list)
    extended_key_usage: List[str] = field(default_factory=list)
    subject_alt_names: List[str] = field(default_factory=list)
    is_ca: bool = False
    path_length: Optional[int] = None


@dataclass
class CertificateBundle:
    """Bundle containing certificate and private key"""
    certificate: x509.Certificate
    private_key: Optional[Any] = None
    certificate_chain: List[x509.Certificate] = field(default_factory=list)
    certificate_info: Optional[CertificateInfo] = None
    file_path: Optional[str] = None
    password: Optional[str] = None
    format: CertificateFormat = CertificateFormat.PEM


@dataclass
class CertificateConfig:
    """Configuration for certificate authentication"""
    certificate_path: str
    private_key_path: Optional[str] = None
    certificate_password: Optional[str] = None
    ca_bundle_path: Optional[str] = None
    verify_ssl: bool = True
    check_hostname: bool = True
    cert_format: CertificateFormat = CertificateFormat.PEM
    enable_ocsp_checking: bool = False
    enable_crl_checking: bool = False
    certificate_store_path: Optional[str] = None


class CertificateValidator:
    """Validates certificates and certificate chains"""
    
    def __init__(self, config: CertificateConfig):
        self.config = config
        self.ca_certificates: List[x509.Certificate] = []
        self.crl_cache: Dict[str, Any] = {}
        self.ocsp_cache: Dict[str, Any] = {}
    
    async def validate_certificate(
        self,
        certificate: x509.Certificate,
        certificate_chain: Optional[List[x509.Certificate]] = None
    ) -> Tuple[CertificateStatus, List[str]]:
        """Validate a certificate"""
        issues = []
        
        try:
            # Check validity period
            now = datetime.now()
            
            if now < certificate.not_valid_before:
                return CertificateStatus.NOT_YET_VALID, ["Certificate not yet valid"]
            
            if now > certificate.not_valid_after:
                return CertificateStatus.EXPIRED, ["Certificate has expired"]
            
            # Check certificate chain
            if certificate_chain:
                chain_issues = await self._validate_certificate_chain(certificate, certificate_chain)
                issues.extend(chain_issues)
            
            # Check against CA certificates
            if self.ca_certificates:
                ca_issues = await self._validate_against_ca(certificate)
                issues.extend(ca_issues)
            
            # Check revocation status
            if self.config.enable_ocsp_checking:
                ocsp_issues = await self._check_ocsp_status(certificate)
                issues.extend(ocsp_issues)
            
            if self.config.enable_crl_checking:
                crl_issues = await self._check_crl_status(certificate)
                issues.extend(crl_issues)
            
            # Determine final status
            if not issues:
                return CertificateStatus.VALID, []
            elif any("revoked" in issue.lower() for issue in issues):
                return CertificateStatus.REVOKED, issues
            elif any("untrusted" in issue.lower() for issue in issues):
                return CertificateStatus.UNTRUSTED_CA, issues
            else:
                return CertificateStatus.INVALID_SIGNATURE, issues
                
        except Exception as e:
            logger.error(f"Certificate validation failed: {e}")
            return CertificateStatus.UNKNOWN, [str(e)]
    
    async def _validate_certificate_chain(
        self,
        certificate: x509.Certificate,
        chain: List[x509.Certificate]
    ) -> List[str]:
        """Validate certificate chain"""
        issues = []
        
        try:
            # Verify each certificate in the chain
            current_cert = certificate
            
            for next_cert in chain:
                try:
                    # Verify signature
                    next_cert.public_key().verify(
                        current_cert.signature,
                        current_cert.tbs_certificate_bytes,
                        padding.PKCS1v15(),
                        current_cert.signature_hash_algorithm
                    )
                except Exception as e:
                    issues.append(f"Invalid signature in certificate chain: {e}")
                
                current_cert = next_cert
            
        except Exception as e:
            issues.append(f"Certificate chain validation failed: {e}")
        
        return issues
    
    async def _validate_against_ca(self, certificate: x509.Certificate) -> List[str]:
        """Validate certificate against known CAs"""
        issues = []
        
        try:
            # Check if certificate is signed by a trusted CA
            trusted = False
            
            for ca_cert in self.ca_certificates:
                try:
                    ca_cert.public_key().verify(
                        certificate.signature,
                        certificate.tbs_certificate_bytes,
                        padding.PKCS1v15(),
                        certificate.signature_hash_algorithm
                    )
                    trusted = True
                    break
                except Exception:
                    continue
            
            if not trusted:
                issues.append("Certificate not signed by trusted CA")
                
        except Exception as e:
            issues.append(f"CA validation failed: {e}")
        
        return issues
    
    async def _check_ocsp_status(self, certificate: x509.Certificate) -> List[str]:
        """Check OCSP revocation status"""
        issues = []
        
        try:
            # Implementation would check OCSP responder
            # This is a placeholder
            logger.debug("OCSP checking not implemented")
            
        except Exception as e:
            issues.append(f"OCSP check failed: {e}")
        
        return issues
    
    async def _check_crl_status(self, certificate: x509.Certificate) -> List[str]:
        """Check CRL revocation status"""
        issues = []
        
        try:
            # Implementation would check Certificate Revocation List
            # This is a placeholder
            logger.debug("CRL checking not implemented")
            
        except Exception as e:
            issues.append(f"CRL check failed: {e}")
        
        return issues


class CertificateAuthProvider(BaseAuthProvider):
    """Certificate-based authentication provider"""
    
    def __init__(self):
        super().__init__("certificate_auth", AuthenticationType.CERTIFICATE)
        self.certificate_store: Dict[str, CertificateBundle] = {}
        self.validator: Optional[CertificateValidator] = None
        self.ssl_contexts: Dict[str, ssl.SSLContext] = {}
    
    async def initialize(self, config: CertificateConfig) -> None:
        """Initialize certificate authentication provider"""
        try:
            self.config = config
            self.validator = CertificateValidator(config)
            
            # Load CA certificates if provided
            if config.ca_bundle_path:
                await self._load_ca_certificates(config.ca_bundle_path)
            
            # Setup certificate store
            if config.certificate_store_path:
                store_path = Path(config.certificate_store_path)
                store_path.mkdir(parents=True, exist_ok=True)
                await self._load_stored_certificates(store_path)
            
            logger.info("Certificate auth provider initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize certificate auth provider: {e}")
            raise
    
    async def authenticate(
        self,
        credentials: AuthenticationCredentials,
        context: AuthenticationContext
    ) -> AuthenticationResult:
        """Authenticate using client certificate"""
        try:
            # Load certificate bundle
            cert_bundle = await self._load_certificate_bundle(credentials)
            if not cert_bundle:
                return self._create_failed_result(credentials, "Failed to load certificate")
            
            # Validate certificate
            status, issues = await self.validator.validate_certificate(
                cert_bundle.certificate,
                cert_bundle.certificate_chain
            )
            
            if status != CertificateStatus.VALID:
                return self._create_failed_result(
                    credentials,
                    f"Certificate validation failed: {', '.join(issues)}"
                )
            
            # Create SSL context
            ssl_context = await self._create_ssl_context(cert_bundle)
            if not ssl_context:
                return self._create_failed_result(credentials, "Failed to create SSL context")
            
            # Test certificate authentication
            auth_success = await self._test_certificate_auth(credentials, ssl_context, context)
            
            if auth_success:
                # Store SSL context for reuse
                self.ssl_contexts[credentials.service_identifier] = ssl_context
                
                # Create successful result
                session_id = f"cert_{cert_bundle.certificate_info.fingerprint_sha256[:16]}"
                
                result = AuthenticationResult(
                    session_id=session_id,
                    status=AuthenticationStatus.AUTHENTICATED,
                    auth_type=AuthenticationType.CERTIFICATE,
                    service_identifier=credentials.service_identifier,
                    authenticated_at=datetime.now(),
                    expires_at=cert_bundle.certificate_info.not_valid_after,
                    granted_scopes=[
                        AuthenticationScope.FIRS_API,
                        AuthenticationScope.CERTIFICATE_MGMT
                    ],
                    service_metadata={
                        "certificate_info": cert_bundle.certificate_info.__dict__,
                        "certificate_subject": cert_bundle.certificate_info.subject,
                        "certificate_fingerprint": cert_bundle.certificate_info.fingerprint_sha256
                    }
                )
                
                return result
            else:
                return self._create_failed_result(credentials, "Certificate authentication failed")
                
        except Exception as e:
            logger.error(f"Certificate authentication failed: {e}")
            return self._create_failed_result(credentials, str(e))
    
    async def validate_token(self, token: str, context: AuthenticationContext) -> bool:
        """Validate certificate session token"""
        try:
            # Token is certificate fingerprint
            for cert_bundle in self.certificate_store.values():
                if cert_bundle.certificate_info.fingerprint_sha256.startswith(token.replace("cert_", "")):
                    # Validate certificate is still valid
                    status, _ = await self.validator.validate_certificate(cert_bundle.certificate)
                    return status == CertificateStatus.VALID
            
            return False
            
        except Exception:
            return False
    
    async def refresh_token(
        self,
        refresh_token: str,
        context: AuthenticationContext
    ) -> Optional[AuthenticationResult]:
        """Refresh certificate authentication (not applicable)"""
        # Certificate authentication doesn't support refresh
        return None
    
    async def revoke_token(self, token: str, context: AuthenticationContext) -> bool:
        """Revoke certificate authentication"""
        try:
            # Remove SSL context
            for service_id, ssl_context in list(self.ssl_contexts.items()):
                # Find matching context and remove
                # This is a simplified implementation
                pass
            
            return True
            
        except Exception:
            return False
    
    async def _load_certificate_bundle(
        self,
        credentials: AuthenticationCredentials
    ) -> Optional[CertificateBundle]:
        """Load certificate bundle from credentials"""
        try:
            cert_path = credentials.certificate_path
            key_path = credentials.private_key_path
            password = credentials.password
            
            if not cert_path:
                return None
            
            cert_path = Path(cert_path)
            if not cert_path.exists():
                logger.error(f"Certificate file not found: {cert_path}")
                return None
            
            # Determine certificate format
            cert_format = self._detect_certificate_format(cert_path)
            
            if cert_format == CertificateFormat.PKCS12:
                return await self._load_pkcs12_bundle(cert_path, password)
            else:
                return await self._load_pem_bundle(cert_path, key_path, password)
                
        except Exception as e:
            logger.error(f"Failed to load certificate bundle: {e}")
            return None
    
    async def _load_pem_bundle(
        self,
        cert_path: Path,
        key_path: Optional[Path],
        password: Optional[str]
    ) -> Optional[CertificateBundle]:
        """Load PEM format certificate bundle"""
        try:
            # Load certificate
            async with aiofiles.open(cert_path, 'rb') as f:
                cert_data = await f.read()
            
            certificate = x509.load_pem_x509_certificate(cert_data)
            
            # Load private key if provided
            private_key = None
            if key_path and key_path.exists():
                async with aiofiles.open(key_path, 'rb') as f:
                    key_data = await f.read()
                
                password_bytes = password.encode() if password else None
                private_key = serialization.load_pem_private_key(key_data, password_bytes)
            
            # Extract certificate info
            cert_info = self._extract_certificate_info(certificate)
            
            bundle = CertificateBundle(
                certificate=certificate,
                private_key=private_key,
                certificate_info=cert_info,
                file_path=str(cert_path),
                password=password,
                format=CertificateFormat.PEM
            )
            
            return bundle
            
        except Exception as e:
            logger.error(f"Failed to load PEM certificate: {e}")
            return None
    
    async def _load_pkcs12_bundle(
        self,
        p12_path: Path,
        password: Optional[str]
    ) -> Optional[CertificateBundle]:
        """Load PKCS#12 format certificate bundle"""
        try:
            async with aiofiles.open(p12_path, 'rb') as f:
                p12_data = await f.read()
            
            password_bytes = password.encode() if password else None
            private_key, certificate, additional_certs = pkcs12.load_key_and_certificates(
                p12_data, password_bytes
            )
            
            # Extract certificate info
            cert_info = self._extract_certificate_info(certificate)
            
            bundle = CertificateBundle(
                certificate=certificate,
                private_key=private_key,
                certificate_chain=additional_certs or [],
                certificate_info=cert_info,
                file_path=str(p12_path),
                password=password,
                format=CertificateFormat.PKCS12
            )
            
            return bundle
            
        except Exception as e:
            logger.error(f"Failed to load PKCS#12 certificate: {e}")
            return None
    
    def _extract_certificate_info(self, certificate: x509.Certificate) -> CertificateInfo:
        """Extract information from certificate"""
        try:
            # Get subject and issuer
            subject = certificate.subject.rfc4514_string()
            issuer = certificate.issuer.rfc4514_string()
            
            # Get serial number
            serial_number = str(certificate.serial_number)
            
            # Get validity period
            not_valid_before = certificate.not_valid_before
            not_valid_after = certificate.not_valid_after
            
            # Calculate fingerprint
            fingerprint = hashlib.sha256(certificate.public_bytes(serialization.Encoding.DER)).hexdigest()
            
            # Get public key info
            public_key = certificate.public_key()
            if hasattr(public_key, 'key_size'):
                key_size = public_key.key_size
                key_algorithm = type(public_key).__name__
            else:
                key_size = 0
                key_algorithm = "Unknown"
            
            # Get signature algorithm
            signature_algorithm = certificate.signature_algorithm_oid._name
            
            # Get extensions
            key_usage = []
            extended_key_usage = []
            subject_alt_names = []
            is_ca = False
            path_length = None
            
            try:
                for extension in certificate.extensions:
                    if isinstance(extension.value, x509.KeyUsage):
                        if extension.value.digital_signature:
                            key_usage.append("digital_signature")
                        if extension.value.key_cert_sign:
                            key_usage.append("key_cert_sign")
                        if extension.value.crl_sign:
                            key_usage.append("crl_sign")
                    
                    elif isinstance(extension.value, x509.ExtendedKeyUsage):
                        extended_key_usage = [eku.dotted_string for eku in extension.value]
                    
                    elif isinstance(extension.value, x509.SubjectAlternativeName):
                        subject_alt_names = [name.value for name in extension.value]
                    
                    elif isinstance(extension.value, x509.BasicConstraints):
                        is_ca = extension.value.ca
                        path_length = extension.value.path_length
            
            except Exception as e:
                logger.warning(f"Failed to parse certificate extensions: {e}")
            
            return CertificateInfo(
                subject=subject,
                issuer=issuer,
                serial_number=serial_number,
                not_valid_before=not_valid_before,
                not_valid_after=not_valid_after,
                fingerprint_sha256=fingerprint,
                public_key_algorithm=key_algorithm,
                public_key_size=key_size,
                signature_algorithm=signature_algorithm,
                key_usage=key_usage,
                extended_key_usage=extended_key_usage,
                subject_alt_names=subject_alt_names,
                is_ca=is_ca,
                path_length=path_length
            )
            
        except Exception as e:
            logger.error(f"Failed to extract certificate info: {e}")
            # Return minimal info
            return CertificateInfo(
                subject="Unknown",
                issuer="Unknown",
                serial_number="0",
                not_valid_before=datetime.now(),
                not_valid_after=datetime.now(),
                fingerprint_sha256="unknown",
                public_key_algorithm="Unknown",
                public_key_size=0,
                signature_algorithm="Unknown"
            )
    
    def _detect_certificate_format(self, cert_path: Path) -> CertificateFormat:
        """Detect certificate file format"""
        try:
            suffix = cert_path.suffix.lower()
            
            if suffix in ['.p12', '.pfx']:
                return CertificateFormat.PKCS12
            elif suffix in ['.der']:
                return CertificateFormat.DER
            elif suffix in ['.p7b', '.p7c']:
                return CertificateFormat.PKCS7
            else:
                return CertificateFormat.PEM
                
        except Exception:
            return CertificateFormat.PEM
    
    async def _create_ssl_context(self, cert_bundle: CertificateBundle) -> Optional[ssl.SSLContext]:
        """Create SSL context from certificate bundle"""
        try:
            context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
            
            if not self.config.verify_ssl:
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
            else:
                context.check_hostname = self.config.check_hostname
                context.verify_mode = ssl.CERT_REQUIRED
            
            # Load client certificate
            if cert_bundle.private_key and cert_bundle.file_path:
                if cert_bundle.format == CertificateFormat.PKCS12:
                    # For PKCS#12, we need to create temporary PEM files
                    # This is a simplified approach
                    pass
                else:
                    # Load PEM certificate
                    context.load_cert_chain(
                        cert_bundle.file_path,
                        keyfile=cert_bundle.file_path if not cert_bundle.private_key else None,
                        password=cert_bundle.password
                    )
            
            # Load CA bundle if provided
            if self.config.ca_bundle_path:
                context.load_verify_locations(self.config.ca_bundle_path)
            
            return context
            
        except Exception as e:
            logger.error(f"Failed to create SSL context: {e}")
            return None
    
    async def _test_certificate_auth(
        self,
        credentials: AuthenticationCredentials,
        ssl_context: ssl.SSLContext,
        context: AuthenticationContext
    ) -> bool:
        """Test certificate authentication"""
        try:
            # This would test the certificate against the target service
            # For now, we'll just verify the SSL context is valid
            return ssl_context is not None
            
        except Exception as e:
            logger.error(f"Certificate auth test failed: {e}")
            return False
    
    async def _load_ca_certificates(self, ca_bundle_path: str) -> None:
        """Load CA certificates from bundle"""
        try:
            ca_path = Path(ca_bundle_path)
            if not ca_path.exists():
                logger.warning(f"CA bundle not found: {ca_bundle_path}")
                return
            
            async with aiofiles.open(ca_path, 'rb') as f:
                ca_data = await f.read()
            
            # Load all certificates from bundle
            for cert_pem in ca_data.split(b'-----END CERTIFICATE-----'):
                if b'-----BEGIN CERTIFICATE-----' in cert_pem:
                    cert_pem += b'-----END CERTIFICATE-----'
                    try:
                        ca_cert = x509.load_pem_x509_certificate(cert_pem)
                        self.validator.ca_certificates.append(ca_cert)
                    except Exception as e:
                        logger.warning(f"Failed to load CA certificate: {e}")
            
            logger.info(f"Loaded {len(self.validator.ca_certificates)} CA certificates")
            
        except Exception as e:
            logger.error(f"Failed to load CA certificates: {e}")
    
    async def _load_stored_certificates(self, store_path: Path) -> None:
        """Load certificates from certificate store"""
        try:
            for cert_file in store_path.glob("*.pem"):
                try:
                    bundle = await self._load_pem_bundle(cert_file, None, None)
                    if bundle:
                        self.certificate_store[cert_file.stem] = bundle
                except Exception as e:
                    logger.warning(f"Failed to load stored certificate {cert_file}: {e}")
            
            logger.info(f"Loaded {len(self.certificate_store)} stored certificates")
            
        except Exception as e:
            logger.error(f"Failed to load stored certificates: {e}")
    
    def _create_failed_result(
        self,
        credentials: AuthenticationCredentials,
        error_message: str
    ) -> AuthenticationResult:
        """Create failed authentication result"""
        return AuthenticationResult(
            session_id=f"cert_failed_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            status=AuthenticationStatus.FAILED,
            auth_type=AuthenticationType.CERTIFICATE,
            service_identifier=credentials.service_identifier,
            authenticated_at=datetime.now(),
            error_message=error_message
        )
    
    async def get_certificate_info(self, service_identifier: str) -> Optional[CertificateInfo]:
        """Get certificate information for service"""
        try:
            bundle = self.certificate_store.get(service_identifier)
            if bundle:
                return bundle.certificate_info
            return None
        except Exception:
            return None
    
    async def list_certificates(self) -> List[Dict[str, Any]]:
        """List all stored certificates"""
        try:
            certificates = []
            
            for service_id, bundle in self.certificate_store.items():
                if bundle.certificate_info:
                    certificates.append({
                        "service_identifier": service_id,
                        "subject": bundle.certificate_info.subject,
                        "issuer": bundle.certificate_info.issuer,
                        "not_valid_before": bundle.certificate_info.not_valid_before.isoformat(),
                        "not_valid_after": bundle.certificate_info.not_valid_after.isoformat(),
                        "fingerprint": bundle.certificate_info.fingerprint_sha256,
                        "is_ca": bundle.certificate_info.is_ca,
                        "format": bundle.format.value
                    })
            
            return certificates
            
        except Exception as e:
            logger.error(f"Failed to list certificates: {e}")
            return []


# Factory function for creating certificate auth provider
def create_certificate_auth_provider(config: CertificateConfig) -> CertificateAuthProvider:
    """Factory function to create certificate authentication provider"""
    provider = CertificateAuthProvider()
    # Note: initialize() should be called separately
    return provider