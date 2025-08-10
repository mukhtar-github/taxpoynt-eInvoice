"""
PEPPOL PKI Certificate Management
================================
PKI certificate management system for PEPPOL network authentication,
digital signatures, and secure communication requirements.
"""
import logging
import base64
import hashlib
from typing import Dict, Any, List, Optional, Union, Tuple
from datetime import datetime, timedelta
from pathlib import Path
import ssl
import socket
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.x509.oid import NameOID, ExtensionOID

from .models import PEPPOLSecurityToken, SecurityLevel


class PEPPOLPKIManager:
    """
    PEPPOL PKI certificate management for network authentication and security
    """
    
    def __init__(self, certificate_store_path: Optional[Path] = None):
        self.logger = logging.getLogger(__name__)
        self.certificate_store = certificate_store_path or Path("./peppol_certificates")
        self.certificate_store.mkdir(exist_ok=True)
        
        self.peppol_ca_certificates = self._load_peppol_ca_certificates()
        self.certificate_cache = {}
        
    def _load_peppol_ca_certificates(self) -> Dict[str, Any]:
        """Load PEPPOL Certificate Authority certificates"""
        # In production, these would be loaded from the official PEPPOL CA
        # This is a simplified structure for the implementation
        return {
            "peppol-ca-root": {
                "issuer": "CN=PEPPOL Root CA",
                "subject": "CN=PEPPOL Root CA",
                "valid_from": datetime(2020, 1, 1),
                "valid_to": datetime(2030, 1, 1),
                "key_usage": ["digital_signature", "key_cert_sign", "crl_sign"],
                "certificate_data": None  # Would contain actual certificate
            },
            "peppol-ca-intermediate": {
                "issuer": "CN=PEPPOL Root CA",
                "subject": "CN=PEPPOL Intermediate CA",
                "valid_from": datetime(2020, 1, 1),
                "valid_to": datetime(2028, 1, 1),
                "key_usage": ["digital_signature", "key_cert_sign", "crl_sign"],
                "certificate_data": None
            }
        }
    
    def generate_certificate_request(self, participant_info: Dict[str, Any],
                                   key_size: int = 2048) -> Dict[str, Any]:
        """
        Generate Certificate Signing Request (CSR) for PEPPOL participant
        
        Args:
            participant_info: Participant information for certificate
            key_size: RSA key size (default 2048)
            
        Returns:
            CSR data and private key
        """
        try:
            # Generate private key
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=key_size
            )
            
            # Build certificate subject
            subject_components = [
                x509.NameAttribute(NameOID.COUNTRY_NAME, participant_info.get('country_code', 'NG')),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, participant_info.get('organization_name', '')),
                x509.NameAttribute(NameOID.COMMON_NAME, participant_info.get('participant_id', '')),
            ]
            
            # Add organizational unit if provided
            if participant_info.get('organizational_unit'):
                subject_components.append(
                    x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, participant_info['organizational_unit'])
                )
            
            subject = x509.Name(subject_components)
            
            # Create CSR builder
            csr_builder = x509.CertificateSigningRequestBuilder()
            csr_builder = csr_builder.subject_name(subject)
            
            # Add Subject Alternative Names for PEPPOL
            san_list = []
            if participant_info.get('dns_names'):
                for dns_name in participant_info['dns_names']:
                    san_list.append(x509.DNSName(dns_name))
            
            if participant_info.get('email'):
                san_list.append(x509.RFC822Name(participant_info['email']))
            
            if san_list:
                csr_builder = csr_builder.add_extension(
                    x509.SubjectAlternativeName(san_list),
                    critical=False
                )
            
            # Add key usage extension
            csr_builder = csr_builder.add_extension(
                x509.KeyUsage(
                    digital_signature=True,
                    key_encipherment=True,
                    data_encipherment=False,
                    key_agreement=False,
                    key_cert_sign=False,
                    crl_sign=False,
                    content_commitment=True,
                    encipher_only=False,
                    decipher_only=False
                ),
                critical=True
            )
            
            # Add extended key usage for PEPPOL
            csr_builder = csr_builder.add_extension(
                x509.ExtendedKeyUsage([
                    x509.oid.ExtendedKeyUsageOID.CLIENT_AUTH,
                    x509.oid.ExtendedKeyUsageOID.SERVER_AUTH
                ]),
                critical=True
            )
            
            # Sign the CSR
            csr = csr_builder.sign(private_key, hashes.SHA256())
            
            # Serialize CSR and private key
            csr_pem = csr.public_bytes(serialization.Encoding.PEM)
            private_key_pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
            
            return {
                "csr": csr_pem.decode('utf-8'),
                "private_key": private_key_pem.decode('utf-8'),
                "participant_id": participant_info.get('participant_id'),
                "request_timestamp": datetime.now().isoformat(),
                "key_size": key_size,
                "subject": str(subject)
            }
            
        except Exception as e:
            self.logger.error(f"Certificate request generation failed: {str(e)}")
            raise
    
    def install_certificate(self, certificate_data: bytes, private_key_data: bytes,
                          participant_id: str) -> Dict[str, Any]:
        """
        Install PEPPOL certificate and private key
        
        Args:
            certificate_data: X.509 certificate in PEM format
            private_key_data: Private key in PEM format
            participant_id: PEPPOL participant identifier
            
        Returns:
            Installation result and certificate information
        """
        try:
            # Parse certificate
            certificate = x509.load_pem_x509_certificate(certificate_data)
            
            # Validate certificate
            validation_result = self.validate_certificate(certificate_data)
            if not validation_result.get('is_valid'):
                raise ValueError(f"Invalid certificate: {validation_result.get('errors')}")
            
            # Parse private key
            try:
                private_key = serialization.load_pem_private_key(
                    private_key_data, password=None
                )
            except Exception as e:
                raise ValueError(f"Invalid private key: {str(e)}")
            
            # Verify key pair match
            if not self._verify_key_pair_match(certificate, private_key):
                raise ValueError("Certificate and private key do not match")
            
            # Store certificate and key securely
            cert_path = self.certificate_store / f"{participant_id}_cert.pem"
            key_path = self.certificate_store / f"{participant_id}_key.pem"
            
            with open(cert_path, 'wb') as f:
                f.write(certificate_data)
            
            with open(key_path, 'wb') as f:
                f.write(private_key_data)
            
            # Set secure permissions
            cert_path.chmod(0o644)
            key_path.chmod(0o600)
            
            # Extract certificate information
            cert_info = self._extract_certificate_info(certificate)
            
            # Cache certificate information
            self.certificate_cache[participant_id] = {
                "certificate": certificate,
                "private_key": private_key,
                "cert_path": cert_path,
                "key_path": key_path,
                "info": cert_info,
                "installed_timestamp": datetime.now()
            }
            
            return {
                "status": "installed",
                "participant_id": participant_id,
                "certificate_info": cert_info,
                "installation_timestamp": datetime.now().isoformat(),
                "certificate_path": str(cert_path),
                "key_path": str(key_path)
            }
            
        except Exception as e:
            self.logger.error(f"Certificate installation failed: {str(e)}")
            raise
    
    def validate_certificate(self, certificate_data: bytes) -> Dict[str, Any]:
        """
        Validate PEPPOL certificate compliance and validity
        
        Args:
            certificate_data: X.509 certificate to validate
            
        Returns:
            Validation results
        """
        try:
            validation_result = {
                "is_valid": True,
                "validation_timestamp": datetime.now().isoformat(),
                "passed_checks": [],
                "failed_checks": [],
                "warnings": [],
                "certificate_info": {}
            }
            
            # Parse certificate
            try:
                certificate = x509.load_pem_x509_certificate(certificate_data)
                validation_result["passed_checks"].append("Certificate parsed successfully")
            except Exception as e:
                validation_result["failed_checks"].append(f"Certificate parsing failed: {str(e)}")
                validation_result["is_valid"] = False
                return validation_result
            
            # Check validity period
            now = datetime.now()
            if certificate.not_valid_before <= now <= certificate.not_valid_after:
                validation_result["passed_checks"].append("Certificate is within validity period")
            else:
                validation_result["failed_checks"].append("Certificate is expired or not yet valid")
                validation_result["is_valid"] = False
            
            # Check if certificate is close to expiry (30 days warning)
            if certificate.not_valid_after - now < timedelta(days=30):
                validation_result["warnings"].append("Certificate expires within 30 days")
            
            # Validate key usage
            try:
                key_usage = certificate.extensions.get_extension_for_oid(ExtensionOID.KEY_USAGE).value
                if key_usage.digital_signature:
                    validation_result["passed_checks"].append("Digital signature capability present")
                else:
                    validation_result["failed_checks"].append("Digital signature capability missing")
                    validation_result["is_valid"] = False
            except x509.ExtensionNotFound:
                validation_result["warnings"].append("Key usage extension not found")
            
            # Validate extended key usage for PEPPOL
            try:
                ext_key_usage = certificate.extensions.get_extension_for_oid(ExtensionOID.EXTENDED_KEY_USAGE).value
                required_usages = [x509.oid.ExtendedKeyUsageOID.CLIENT_AUTH, x509.oid.ExtendedKeyUsageOID.SERVER_AUTH]
                
                for usage in required_usages:
                    if usage in ext_key_usage:
                        validation_result["passed_checks"].append(f"Extended key usage {usage.dotted_string} present")
                    else:
                        validation_result["warnings"].append(f"Extended key usage {usage.dotted_string} missing")
            except x509.ExtensionNotFound:
                validation_result["warnings"].append("Extended key usage extension not found")
            
            # Check key strength
            public_key = certificate.public_key()
            if hasattr(public_key, 'key_size'):
                if public_key.key_size >= 2048:
                    validation_result["passed_checks"].append(f"Adequate key size: {public_key.key_size} bits")
                else:
                    validation_result["failed_checks"].append(f"Insufficient key size: {public_key.key_size} bits")
                    validation_result["is_valid"] = False
            
            # Extract certificate information
            validation_result["certificate_info"] = self._extract_certificate_info(certificate)
            
            return validation_result
            
        except Exception as e:
            self.logger.error(f"Certificate validation failed: {str(e)}")
            raise
    
    def _verify_key_pair_match(self, certificate: x509.Certificate, private_key) -> bool:
        """Verify that certificate and private key are a matching pair"""
        try:
            # Get public key from certificate
            cert_public_key = certificate.public_key()
            
            # Get public key from private key
            private_public_key = private_key.public_key()
            
            # Compare public key numbers
            if hasattr(cert_public_key, 'public_numbers') and hasattr(private_public_key, 'public_numbers'):
                return (cert_public_key.public_numbers().n == private_public_key.public_numbers().n and
                       cert_public_key.public_numbers().e == private_public_key.public_numbers().e)
            
            return False
            
        except Exception:
            return False
    
    def _extract_certificate_info(self, certificate: x509.Certificate) -> Dict[str, Any]:
        """Extract detailed information from certificate"""
        
        info = {
            "subject": str(certificate.subject),
            "issuer": str(certificate.issuer),
            "serial_number": str(certificate.serial_number),
            "version": certificate.version.name,
            "not_valid_before": certificate.not_valid_before.isoformat(),
            "not_valid_after": certificate.not_valid_after.isoformat(),
            "signature_algorithm": certificate.signature_algorithm_oid._name,
            "public_key_algorithm": None,
            "public_key_size": None,
            "fingerprint_sha256": None,
            "extensions": []
        }
        
        # Public key information
        public_key = certificate.public_key()
        if hasattr(public_key, 'key_size'):
            info["public_key_size"] = public_key.key_size
            info["public_key_algorithm"] = type(public_key).__name__
        
        # Certificate fingerprint
        fingerprint = certificate.fingerprint(hashes.SHA256())
        info["fingerprint_sha256"] = fingerprint.hex().upper()
        
        # Extensions information
        for extension in certificate.extensions:
            ext_info = {
                "oid": extension.oid.dotted_string,
                "critical": extension.critical,
                "value": str(extension.value)
            }
            info["extensions"].append(ext_info)
        
        return info
    
    def sign_message(self, message_data: bytes, participant_id: str,
                    signature_algorithm: str = "SHA256") -> Dict[str, Any]:
        """
        Sign message using participant's private key
        
        Args:
            message_data: Data to sign
            participant_id: Participant identifier
            signature_algorithm: Signature algorithm to use
            
        Returns:
            Signature information
        """
        try:
            if participant_id not in self.certificate_cache:
                raise ValueError(f"Certificate not found for participant: {participant_id}")
            
            cert_data = self.certificate_cache[participant_id]
            private_key = cert_data["private_key"]
            certificate = cert_data["certificate"]
            
            # Choose hash algorithm
            if signature_algorithm.upper() == "SHA256":
                hash_algorithm = hashes.SHA256()
            elif signature_algorithm.upper() == "SHA384":
                hash_algorithm = hashes.SHA384()
            elif signature_algorithm.upper() == "SHA512":
                hash_algorithm = hashes.SHA512()
            else:
                raise ValueError(f"Unsupported signature algorithm: {signature_algorithm}")
            
            # Sign the message
            signature = private_key.sign(
                message_data,
                padding.PKCS1v15(),
                hash_algorithm
            )
            
            # Encode signature
            signature_b64 = base64.b64encode(signature).decode('utf-8')
            
            return {
                "participant_id": participant_id,
                "signature": signature_b64,
                "algorithm": f"RSA-{signature_algorithm.upper()}",
                "certificate_fingerprint": cert_data["info"]["fingerprint_sha256"],
                "signing_timestamp": datetime.now().isoformat(),
                "message_hash": hashlib.sha256(message_data).hexdigest()
            }
            
        except Exception as e:
            self.logger.error(f"Message signing failed: {str(e)}")
            raise
    
    def verify_signature(self, message_data: bytes, signature_data: str,
                        certificate_data: bytes) -> Dict[str, Any]:
        """
        Verify digital signature using certificate
        
        Args:
            message_data: Original message data
            signature_data: Base64-encoded signature
            certificate_data: Signer's certificate
            
        Returns:
            Verification results
        """
        try:
            verification_result = {
                "is_valid": False,
                "verification_timestamp": datetime.now().isoformat(),
                "signer_info": {},
                "errors": []
            }
            
            # Parse certificate
            try:
                certificate = x509.load_pem_x509_certificate(certificate_data)
                verification_result["signer_info"] = self._extract_certificate_info(certificate)
            except Exception as e:
                verification_result["errors"].append(f"Certificate parsing failed: {str(e)}")
                return verification_result
            
            # Decode signature
            try:
                signature = base64.b64decode(signature_data)
            except Exception as e:
                verification_result["errors"].append(f"Signature decoding failed: {str(e)}")
                return verification_result
            
            # Get public key from certificate
            public_key = certificate.public_key()
            
            # Verify signature (try different hash algorithms)
            hash_algorithms = [hashes.SHA256(), hashes.SHA384(), hashes.SHA512()]
            
            for hash_alg in hash_algorithms:
                try:
                    public_key.verify(
                        signature,
                        message_data,
                        padding.PKCS1v15(),
                        hash_alg
                    )
                    verification_result["is_valid"] = True
                    verification_result["algorithm"] = f"RSA-{hash_alg.name.upper()}"
                    break
                except Exception:
                    continue
            
            if not verification_result["is_valid"]:
                verification_result["errors"].append("Signature verification failed with all algorithms")
            
            return verification_result
            
        except Exception as e:
            self.logger.error(f"Signature verification failed: {str(e)}")
            raise
    
    def create_security_token(self, participant_id: str, scopes: List[str],
                            validity_hours: int = 24) -> PEPPOLSecurityToken:
        """
        Create security token for PEPPOL network authentication
        
        Args:
            participant_id: Participant identifier
            scopes: Token scopes/permissions
            validity_hours: Token validity in hours
            
        Returns:
            PEPPOL security token
        """
        try:
            if participant_id not in self.certificate_cache:
                raise ValueError(f"Certificate not found for participant: {participant_id}")
            
            # Generate token
            token_id = f"token_{participant_id}_{int(datetime.now().timestamp())}"
            issued_timestamp = datetime.now()
            expiry_timestamp = issued_timestamp + timedelta(hours=validity_hours)
            
            # Create token payload
            token_payload = {
                "token_id": token_id,
                "issued": issued_timestamp.isoformat(),
                "expires": expiry_timestamp.isoformat(),
                "participant_id": participant_id,
                "scopes": scopes
            }
            
            # Sign token
            payload_json = str(token_payload).encode('utf-8')
            signature_info = self.sign_message(payload_json, participant_id)
            
            return PEPPOLSecurityToken(
                token_id=token_id,
                issued_timestamp=issued_timestamp,
                expiry_timestamp=expiry_timestamp,
                issuer="TaxPoynt-PEPPOL-PKI",
                subject=participant_id,
                scopes=scopes,
                signature=signature_info["signature"]
            )
            
        except Exception as e:
            self.logger.error(f"Security token creation failed: {str(e)}")
            raise
    
    def validate_security_token(self, token: PEPPOLSecurityToken,
                              certificate_data: bytes) -> Dict[str, Any]:
        """
        Validate PEPPOL security token
        
        Args:
            token: Security token to validate
            certificate_data: Certificate for signature verification
            
        Returns:
            Token validation results
        """
        try:
            validation_result = {
                "is_valid": True,
                "validation_timestamp": datetime.now().isoformat(),
                "passed_checks": [],
                "failed_checks": [],
                "token_info": {
                    "token_id": token.token_id,
                    "subject": token.subject,
                    "scopes": token.scopes,
                    "expires": token.expiry_timestamp.isoformat()
                }
            }
            
            # Check token expiry
            if datetime.now() <= token.expiry_timestamp:
                validation_result["passed_checks"].append("Token is not expired")
            else:
                validation_result["failed_checks"].append("Token has expired")
                validation_result["is_valid"] = False
            
            # Verify token signature
            token_payload = {
                "token_id": token.token_id,
                "issued": token.issued_timestamp.isoformat(),
                "expires": token.expiry_timestamp.isoformat(),
                "participant_id": token.subject,
                "scopes": token.scopes
            }
            
            payload_json = str(token_payload).encode('utf-8')
            signature_verification = self.verify_signature(
                payload_json, token.signature, certificate_data
            )
            
            if signature_verification["is_valid"]:
                validation_result["passed_checks"].append("Token signature is valid")
            else:
                validation_result["failed_checks"].append("Token signature is invalid")
                validation_result["is_valid"] = False
            
            return validation_result
            
        except Exception as e:
            self.logger.error(f"Security token validation failed: {str(e)}")
            raise
    
    def get_certificate_status(self, participant_id: str) -> Dict[str, Any]:
        """
        Get certificate status and information
        
        Args:
            participant_id: Participant identifier
            
        Returns:
            Certificate status information
        """
        try:
            if participant_id not in self.certificate_cache:
                return {
                    "status": "not_installed",
                    "participant_id": participant_id,
                    "message": "No certificate found for participant"
                }
            
            cert_data = self.certificate_cache[participant_id]
            cert_info = cert_data["info"]
            
            # Check certificate validity
            not_valid_after = datetime.fromisoformat(cert_info["not_valid_after"].replace('Z', '+00:00'))
            days_until_expiry = (not_valid_after - datetime.now()).days
            
            status = "valid"
            if days_until_expiry <= 0:
                status = "expired"
            elif days_until_expiry <= 30:
                status = "expiring_soon"
            
            return {
                "status": status,
                "participant_id": participant_id,
                "certificate_info": cert_info,
                "days_until_expiry": days_until_expiry,
                "installed_timestamp": cert_data["installed_timestamp"].isoformat(),
                "certificate_path": str(cert_data["cert_path"]),
                "key_path": str(cert_data["key_path"])
            }
            
        except Exception as e:
            self.logger.error(f"Certificate status check failed: {str(e)}")
            raise