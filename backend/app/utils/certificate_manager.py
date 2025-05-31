"""
Certificate management utilities for FIRS e-Invoice system.

This module provides comprehensive certificate management functions for:
- Certificate loading and validation
- Certificate storage and retrieval
- Certificate verification
- Integration with the FIRS cryptographic stamping system
"""

import os
import base64
import logging
import datetime
from pathlib import Path
from typing import Dict, Tuple, Union, Optional, Any, List

from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.exceptions import InvalidSignature

from app.core.config import settings
from app.utils.key_management import KeyManager, get_key_manager

logger = logging.getLogger(__name__)


class CertificateManager:
    """
    Certificate Manager for FIRS e-Invoice cryptographic stamping operations.
    
    This class handles all aspects of certificate lifecycle:
    - Storage: Securely storing certificates with proper permissions
    - Retrieval: Loading certificates for cryptographic operations
    - Validation: Verifying certificate validity and authenticity
    - Integration with FIRS cryptographic stamping requirements
    """
    
    def __init__(
        self,
        certs_dir: Optional[str] = None,
        key_manager: Optional[KeyManager] = None
    ):
        """
        Initialize the Certificate Manager.
        
        Args:
            certs_dir: Directory for certificate storage
            key_manager: KeyManager instance for key operations
        """
        self.certs_dir = certs_dir or os.environ.get(
            "CERTS_DIRECTORY", 
            settings.CERTS_DIRECTORY if hasattr(settings, "CERTS_DIRECTORY") else None
        )
        
        if not self.certs_dir:
            self.certs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../certs")
        
        # Ensure certificates directory exists
        Path(self.certs_dir).mkdir(parents=True, exist_ok=True)
        
        # Get or create key manager
        self.key_manager = key_manager or get_key_manager()
    
    def store_certificate(
        self, 
        certificate_data: Union[str, bytes], 
        name: Optional[str] = None,
        overwrite: bool = False
    ) -> str:
        """
        Store a certificate for future use.
        
        Args:
            certificate_data: PEM encoded certificate data
            name: Name for the certificate file
            overwrite: Whether to overwrite existing certificate
            
        Returns:
            Path to the stored certificate
        """
        # Convert string to bytes if needed
        if isinstance(certificate_data, str):
            certificate_data = certificate_data.encode()
        
        # Generate a default name if not provided
        if not name:
            timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            name = f"cert_{timestamp}"
        
        # Ensure it has the correct extension
        if not name.endswith(".crt") and not name.endswith(".pem"):
            name = f"{name}.crt"
        
        cert_path = os.path.join(self.certs_dir, name)
        
        # Check if file already exists
        if not overwrite and os.path.exists(cert_path):
            raise FileExistsError(f"Certificate file already exists: {cert_path}")
        
        # Write the certificate to file
        with open(cert_path, 'wb') as f:
            f.write(certificate_data)
        
        # Set appropriate permissions
        os.chmod(cert_path, 0o644)  # Read for all, write for owner
        
        logger.info(f"Stored certificate: {name}")
        return cert_path
    
    def load_certificate(self, cert_path: str) -> x509.Certificate:
        """
        Load a certificate from file.
        
        Args:
            cert_path: Path to the certificate file
            
        Returns:
            x509.Certificate object
        """
        if not os.path.exists(cert_path):
            raise FileNotFoundError(f"Certificate file not found: {cert_path}")
        
        try:
            with open(cert_path, "rb") as cert_file:
                cert_data = cert_file.read()
                
            return x509.load_pem_x509_certificate(cert_data, default_backend())
        except Exception as e:
            logger.error(f"Failed to load certificate: {str(e)}")
            raise ValueError(f"Failed to load certificate: {str(e)}")
    
    def validate_certificate(self, cert_path: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Validate a certificate's authenticity and expiration.
        
        Args:
            cert_path: Path to the certificate file
            
        Returns:
            Tuple of (is_valid, validation_details)
        """
        try:
            cert = self.load_certificate(cert_path)
            
            # Check if the certificate is expired
            now = datetime.datetime.now()
            not_valid_before = cert.not_valid_before
            not_valid_after = cert.not_valid_after
            
            is_expired = now > not_valid_after
            is_not_yet_valid = now < not_valid_before
            
            # Extract certificate information
            subject = cert.subject
            issuer = cert.issuer
            
            # Create validation details
            validation_details = {
                "subject": {attr.oid._name: attr.value for attr in subject},
                "issuer": {attr.oid._name: attr.value for attr in issuer},
                "serial_number": cert.serial_number,
                "not_valid_before": not_valid_before.isoformat(),
                "not_valid_after": not_valid_after.isoformat(),
                "is_expired": is_expired,
                "is_not_yet_valid": is_not_yet_valid,
                "public_key_type": type(cert.public_key()).__name__
            }
            
            is_valid = not (is_expired or is_not_yet_valid)
            
            return is_valid, validation_details
        except Exception as e:
            logger.error(f"Certificate validation failed: {str(e)}")
            return False, {"error": str(e)}
    
    def extract_public_key(self, cert_path: str) -> Any:
        """
        Extract the public key from a certificate.
        
        Args:
            cert_path: Path to the certificate file
            
        Returns:
            Public key object
        """
        cert = self.load_certificate(cert_path)
        return cert.public_key()
    
    def get_or_create_firs_stamp_certificate(self) -> str:
        """
        Get an existing FIRS stamping certificate or create a self-signed one for testing.
        
        Returns:
            Path to the FIRS stamping certificate
        """
        # Look for existing FIRS certificates
        firs_certs = [f for f in os.listdir(self.certs_dir) 
                     if f.startswith("firs_") and (f.endswith(".crt") or f.endswith(".pem"))]
        
        if firs_certs:
            # Use the newest FIRS certificate
            newest_cert = max(firs_certs, key=lambda f: os.path.getmtime(os.path.join(self.certs_dir, f)))
            return os.path.join(self.certs_dir, newest_cert)
        
        # No FIRS certificate found, create a self-signed one for testing
        logger.warning("No FIRS certificate found. Creating a self-signed certificate for testing.")
        
        # Generate a key pair for the certificate
        private_key_path, public_key_path = self.key_manager.generate_key_pair(
            key_type="signing",
            algorithm="rsa-2048",
            key_name=f"firs_signing_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
        )
        
        # Load the private key
        private_key = self.key_manager.load_private_key(private_key_path)
        
        # Generate a self-signed certificate
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "NG"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Federal Inland Revenue Service (Test)"),
            x509.NameAttribute(NameOID.COMMON_NAME, "FIRS e-Invoice Stamping Certificate")
        ])
        
        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            private_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.datetime.utcnow()
        ).not_valid_after(
            datetime.datetime.utcnow() + datetime.timedelta(days=365)
        ).add_extension(
            x509.BasicConstraints(ca=True, path_length=None), critical=True
        ).sign(private_key, hashes.SHA256(), default_backend())
        
        # Serialize the certificate
        cert_pem = cert.public_bytes(serialization.Encoding.PEM)
        
        # Store the certificate
        cert_path = self.store_certificate(
            cert_pem,
            name=f"firs_test_cert_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.crt"
        )
        
        return cert_path
    
    def verify_stamped_document(self, document_data: bytes, signature: bytes, cert_path: str) -> bool:
        """
        Verify a signature on a document using a certificate.
        
        Args:
            document_data: Original document data
            signature: Signature to verify
            cert_path: Path to the certificate containing the public key
            
        Returns:
            True if signature is valid, False otherwise
        """
        try:
            # Extract the public key from the certificate
            cert = self.load_certificate(cert_path)
            public_key = cert.public_key()
            
            # Verify the signature
            if isinstance(public_key, rsa.RSAPublicKey):
                public_key.verify(
                    signature,
                    document_data,
                    padding.PSS(
                        mgf=padding.MGF1(hashes.SHA256()),
                        salt_length=padding.PSS.MAX_LENGTH
                    ),
                    hashes.SHA256()
                )
            else:
                # Handle other key types if needed
                raise ValueError(f"Unsupported key type: {type(public_key)}")
            
            return True
        except InvalidSignature:
            logger.warning("Signature verification failed: Invalid signature")
            return False
        except Exception as e:
            logger.error(f"Signature verification failed: {str(e)}")
            return False


# Create a singleton instance for easy import
certificate_manager = CertificateManager()


def get_certificate_manager() -> CertificateManager:
    """
    Get or create the certificate manager instance.
    
    Returns:
        CertificateManager instance
    """
    global certificate_manager
    if not certificate_manager:
        certificate_manager = CertificateManager()
    
    return certificate_manager
