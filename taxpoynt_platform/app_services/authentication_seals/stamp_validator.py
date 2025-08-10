"""
Cryptographic Stamp Validator Service for APP Role

This service validates cryptographic stamps and signatures including:
- Digital signature verification
- HMAC stamp validation
- Certificate chain verification
- Timestamp validation
- Cryptographic integrity checks
"""

import base64
import hashlib
import hmac
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend
from cryptography.x509 import load_pem_x509_certificate, Certificate
from cryptography.hazmat.primitives.serialization import load_pem_public_key
from cryptography.exceptions import InvalidSignature

from .seal_generator import SealType, SealAlgorithm, AuthenticationSeal, SealMetadata

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ValidationStatus(Enum):
    """Validation status for stamps"""
    VALID = "valid"
    INVALID = "invalid"
    EXPIRED = "expired"
    REVOKED = "revoked"
    MALFORMED = "malformed"
    UNKNOWN = "unknown"


class ValidationError(Enum):
    """Types of validation errors"""
    INVALID_SIGNATURE = "invalid_signature"
    EXPIRED_TIMESTAMP = "expired_timestamp"
    MALFORMED_STRUCTURE = "malformed_structure"
    INVALID_CERTIFICATE = "invalid_certificate"
    HASH_MISMATCH = "hash_mismatch"
    ALGORITHM_MISMATCH = "algorithm_mismatch"
    KEY_NOT_FOUND = "key_not_found"
    REVOKED_CERTIFICATE = "revoked_certificate"
    UNTRUSTED_ISSUER = "untrusted_issuer"


@dataclass
class ValidationResult:
    """Result of stamp validation"""
    is_valid: bool
    status: ValidationStatus
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    validated_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    issuer: Optional[str] = None
    certificate_thumbprint: Optional[str] = None
    algorithm: Optional[SealAlgorithm] = None
    validation_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CertificateInfo:
    """Certificate information"""
    subject: str
    issuer: str
    serial_number: str
    not_before: datetime
    not_after: datetime
    thumbprint: str
    algorithm: str
    key_size: int
    is_valid: bool
    validation_errors: List[str] = field(default_factory=list)


@dataclass
class TrustStore:
    """Trust store for certificate validation"""
    trusted_certificates: List[Certificate] = field(default_factory=list)
    trusted_issuers: List[str] = field(default_factory=list)
    revoked_certificates: List[str] = field(default_factory=list)
    crl_urls: List[str] = field(default_factory=list)


class StampValidator:
    """
    Cryptographic stamp validator service for APP role
    
    Handles:
    - Digital signature verification
    - HMAC stamp validation
    - Certificate chain verification
    - Timestamp validation
    - Cryptographic integrity checks
    """
    
    def __init__(self, 
                 hmac_key: Optional[bytes] = None,
                 trust_store: Optional[TrustStore] = None,
                 time_tolerance: int = 300):  # 5 minutes
        self.hmac_key = hmac_key
        self.trust_store = trust_store or TrustStore()
        self.time_tolerance = time_tolerance
        
        # Cache for certificates and keys
        self.certificate_cache: Dict[str, Certificate] = {}
        self.public_key_cache: Dict[str, Any] = {}
        
        # Validation rules
        self.validation_rules = {
            SealType.DIGITAL_SIGNATURE: self._validate_digital_signature,
            SealType.CRYPTOGRAPHIC_STAMP: self._validate_cryptographic_stamp,
            SealType.DOCUMENT_HASH: self._validate_document_hash,
            SealType.TIMESTAMP_SEAL: self._validate_timestamp_seal,
            SealType.INTEGRITY_SEAL: self._validate_integrity_seal,
            SealType.COMPOSITE_SEAL: self._validate_composite_seal
        }
        
        # Metrics
        self.metrics = {
            'total_validations': 0,
            'successful_validations': 0,
            'failed_validations': 0,
            'validations_by_type': {},
            'validations_by_algorithm': {},
            'average_validation_time': 0.0,
            'common_errors': {}
        }
    
    async def validate_stamp(self, 
                           seal: AuthenticationSeal,
                           document_data: Union[Dict[str, Any], str, bytes],
                           trusted_certificates: Optional[List[str]] = None) -> ValidationResult:
        """
        Validate cryptographic stamp
        
        Args:
            seal: Authentication seal to validate
            document_data: Original document data
            trusted_certificates: Optional list of trusted certificates
            
        Returns:
            ValidationResult with validation outcome
        """
        start_time = time.time()
        
        try:
            # Add trusted certificates if provided
            if trusted_certificates:
                await self._add_trusted_certificates(trusted_certificates)
            
            # Get validation function for seal type
            validator = self.validation_rules.get(seal.seal_type)
            if not validator:
                return ValidationResult(
                    is_valid=False,
                    status=ValidationStatus.UNKNOWN,
                    errors=[ValidationError.ALGORITHM_MISMATCH],
                    validation_time=time.time() - start_time
                )
            
            # Validate seal
            result = await validator(seal, document_data)
            
            # Update validation time
            result.validation_time = time.time() - start_time
            
            # Update metrics
            self._update_metrics(seal.seal_type, seal.algorithm, result.validation_time, result.is_valid)
            
            logger.info(f"Stamp validation completed for {seal.seal_id}: {result.status.value}")
            
            return result
            
        except Exception as e:
            validation_time = time.time() - start_time
            
            result = ValidationResult(
                is_valid=False,
                status=ValidationStatus.INVALID,
                errors=[ValidationError.MALFORMED_STRUCTURE],
                validation_time=validation_time,
                metadata={'error': str(e)}
            )
            
            # Update metrics
            self._update_metrics(seal.seal_type, seal.algorithm, validation_time, False)
            
            logger.error(f"Stamp validation error for {seal.seal_id}: {e}")
            
            return result
    
    async def _validate_digital_signature(self, 
                                        seal: AuthenticationSeal,
                                        document_data: Union[Dict[str, Any], str, bytes]) -> ValidationResult:
        """Validate digital signature"""
        try:
            # Decode seal value
            seal_structure = json.loads(base64.b64decode(seal.seal_value).decode('utf-8'))
            
            # Extract components
            signature_b64 = seal_structure.get('signature')
            payload = seal_structure.get('payload')
            certificate_pem = seal_structure.get('certificate')
            
            if not signature_b64 or not payload:
                return ValidationResult(
                    is_valid=False,
                    status=ValidationStatus.MALFORMED,
                    errors=[ValidationError.MALFORMED_STRUCTURE]
                )
            
            # Decode signature
            signature = base64.b64decode(signature_b64)
            
            # Get public key
            public_key = None
            certificate = None
            
            if certificate_pem:
                certificate = load_pem_x509_certificate(certificate_pem.encode('utf-8'), default_backend())
                public_key = certificate.public_key()
                
                # Validate certificate
                cert_validation = await self._validate_certificate(certificate)
                if not cert_validation['is_valid']:
                    return ValidationResult(
                        is_valid=False,
                        status=ValidationStatus.INVALID,
                        errors=[ValidationError.INVALID_CERTIFICATE],
                        warnings=cert_validation['errors']
                    )
            
            if not public_key:
                return ValidationResult(
                    is_valid=False,
                    status=ValidationStatus.INVALID,
                    errors=[ValidationError.KEY_NOT_FOUND]
                )
            
            # Verify document hash
            data_bytes = self._prepare_data_for_verification(document_data)
            expected_hash = hashlib.sha256(data_bytes).hexdigest()
            
            if payload.get('data_hash') != expected_hash:
                return ValidationResult(
                    is_valid=False,
                    status=ValidationStatus.INVALID,
                    errors=[ValidationError.HASH_MISMATCH]
                )
            
            # Verify timestamp
            timestamp_str = payload.get('timestamp')
            if timestamp_str:
                timestamp_validation = await self._validate_timestamp(timestamp_str)
                if not timestamp_validation['is_valid']:
                    return ValidationResult(
                        is_valid=False,
                        status=ValidationStatus.EXPIRED,
                        errors=[ValidationError.EXPIRED_TIMESTAMP],
                        warnings=timestamp_validation['warnings']
                    )
            
            # Verify signature
            payload_bytes = json.dumps(payload, sort_keys=True).encode('utf-8')
            
            try:
                if seal.algorithm == SealAlgorithm.RSA_SHA256:
                    public_key.verify(
                        signature,
                        payload_bytes,
                        padding.PKCS1v15(),
                        hashes.SHA256()
                    )
                elif seal.algorithm == SealAlgorithm.RSA_PSS_SHA256:
                    public_key.verify(
                        signature,
                        payload_bytes,
                        padding.PSS(
                            mgf=padding.MGF1(hashes.SHA256()),
                            salt_length=padding.PSS.MAX_LENGTH
                        ),
                        hashes.SHA256()
                    )
                else:
                    return ValidationResult(
                        is_valid=False,
                        status=ValidationStatus.INVALID,
                        errors=[ValidationError.ALGORITHM_MISMATCH]
                    )
                
                return ValidationResult(
                    is_valid=True,
                    status=ValidationStatus.VALID,
                    expires_at=seal.metadata.expires_at,
                    issuer=payload.get('issuer'),
                    certificate_thumbprint=self._get_certificate_thumbprint(certificate) if certificate else None,
                    algorithm=seal.algorithm
                )
                
            except InvalidSignature:
                return ValidationResult(
                    is_valid=False,
                    status=ValidationStatus.INVALID,
                    errors=[ValidationError.INVALID_SIGNATURE]
                )
            
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                status=ValidationStatus.MALFORMED,
                errors=[ValidationError.MALFORMED_STRUCTURE],
                metadata={'error': str(e)}
            )
    
    async def _validate_cryptographic_stamp(self, 
                                          seal: AuthenticationSeal,
                                          document_data: Union[Dict[str, Any], str, bytes]) -> ValidationResult:
        """Validate cryptographic stamp"""
        if not self.hmac_key:
            return ValidationResult(
                is_valid=False,
                status=ValidationStatus.INVALID,
                errors=[ValidationError.KEY_NOT_FOUND]
            )
        
        try:
            # Decode seal value
            seal_structure = json.loads(base64.b64decode(seal.seal_value).decode('utf-8'))
            
            # Extract components
            stamp_b64 = seal_structure.get('stamp')
            payload = seal_structure.get('payload')
            
            if not stamp_b64 or not payload:
                return ValidationResult(
                    is_valid=False,
                    status=ValidationStatus.MALFORMED,
                    errors=[ValidationError.MALFORMED_STRUCTURE]
                )
            
            # Decode stamp
            stamp = base64.b64decode(stamp_b64)
            
            # Verify document hash
            data_bytes = self._prepare_data_for_verification(document_data)
            expected_hash = hashlib.sha256(data_bytes).hexdigest()
            
            if payload.get('data_hash') != expected_hash:
                return ValidationResult(
                    is_valid=False,
                    status=ValidationStatus.INVALID,
                    errors=[ValidationError.HASH_MISMATCH]
                )
            
            # Verify timestamp
            timestamp_str = payload.get('timestamp')
            if timestamp_str:
                timestamp_validation = await self._validate_timestamp(timestamp_str)
                if not timestamp_validation['is_valid']:
                    return ValidationResult(
                        is_valid=False,
                        status=ValidationStatus.EXPIRED,
                        errors=[ValidationError.EXPIRED_TIMESTAMP],
                        warnings=timestamp_validation['warnings']
                    )
            
            # Verify HMAC stamp
            payload_bytes = json.dumps(payload, sort_keys=True).encode('utf-8')
            
            if seal.algorithm == SealAlgorithm.HMAC_SHA256:
                expected_stamp = hmac.new(
                    self.hmac_key,
                    payload_bytes,
                    hashlib.sha256
                ).digest()
            elif seal.algorithm == SealAlgorithm.HMAC_SHA512:
                expected_stamp = hmac.new(
                    self.hmac_key,
                    payload_bytes,
                    hashlib.sha512
                ).digest()
            else:
                return ValidationResult(
                    is_valid=False,
                    status=ValidationStatus.INVALID,
                    errors=[ValidationError.ALGORITHM_MISMATCH]
                )
            
            if hmac.compare_digest(stamp, expected_stamp):
                return ValidationResult(
                    is_valid=True,
                    status=ValidationStatus.VALID,
                    expires_at=seal.metadata.expires_at,
                    algorithm=seal.algorithm
                )
            else:
                return ValidationResult(
                    is_valid=False,
                    status=ValidationStatus.INVALID,
                    errors=[ValidationError.INVALID_SIGNATURE]
                )
                
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                status=ValidationStatus.MALFORMED,
                errors=[ValidationError.MALFORMED_STRUCTURE],
                metadata={'error': str(e)}
            )
    
    async def _validate_document_hash(self, 
                                    seal: AuthenticationSeal,
                                    document_data: Union[Dict[str, Any], str, bytes]) -> ValidationResult:
        """Validate document hash"""
        try:
            # Decode seal value
            seal_structure = json.loads(base64.b64decode(seal.seal_value).decode('utf-8'))
            
            # Extract components
            stored_hash = seal_structure.get('hash')
            algorithm = seal_structure.get('algorithm')
            
            if not stored_hash or not algorithm:
                return ValidationResult(
                    is_valid=False,
                    status=ValidationStatus.MALFORMED,
                    errors=[ValidationError.MALFORMED_STRUCTURE]
                )
            
            # Verify algorithm
            if algorithm != seal.algorithm.value:
                return ValidationResult(
                    is_valid=False,
                    status=ValidationStatus.INVALID,
                    errors=[ValidationError.ALGORITHM_MISMATCH]
                )
            
            # Calculate hash
            data_bytes = self._prepare_data_for_verification(document_data)
            
            if seal.algorithm == SealAlgorithm.SHA256:
                calculated_hash = hashlib.sha256(data_bytes).hexdigest()
            elif seal.algorithm == SealAlgorithm.SHA512:
                calculated_hash = hashlib.sha512(data_bytes).hexdigest()
            else:
                return ValidationResult(
                    is_valid=False,
                    status=ValidationStatus.INVALID,
                    errors=[ValidationError.ALGORITHM_MISMATCH]
                )
            
            # Verify data size if provided
            stored_size = seal_structure.get('data_size')
            if stored_size and stored_size != len(data_bytes):
                return ValidationResult(
                    is_valid=False,
                    status=ValidationStatus.INVALID,
                    errors=[ValidationError.HASH_MISMATCH],
                    warnings=['Data size mismatch']
                )
            
            # Verify timestamp
            timestamp_str = seal_structure.get('timestamp')
            if timestamp_str:
                timestamp_validation = await self._validate_timestamp(timestamp_str)
                if not timestamp_validation['is_valid']:
                    return ValidationResult(
                        is_valid=False,
                        status=ValidationStatus.EXPIRED,
                        errors=[ValidationError.EXPIRED_TIMESTAMP],
                        warnings=timestamp_validation['warnings']
                    )
            
            # Compare hashes
            if stored_hash == calculated_hash:
                return ValidationResult(
                    is_valid=True,
                    status=ValidationStatus.VALID,
                    expires_at=seal.metadata.expires_at,
                    algorithm=seal.algorithm
                )
            else:
                return ValidationResult(
                    is_valid=False,
                    status=ValidationStatus.INVALID,
                    errors=[ValidationError.HASH_MISMATCH]
                )
                
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                status=ValidationStatus.MALFORMED,
                errors=[ValidationError.MALFORMED_STRUCTURE],
                metadata={'error': str(e)}
            )
    
    async def _validate_timestamp_seal(self, 
                                     seal: AuthenticationSeal,
                                     document_data: Union[Dict[str, Any], str, bytes]) -> ValidationResult:
        """Validate timestamp seal"""
        if not self.hmac_key:
            return ValidationResult(
                is_valid=False,
                status=ValidationStatus.INVALID,
                errors=[ValidationError.KEY_NOT_FOUND]
            )
        
        try:
            # Decode seal value
            seal_structure = json.loads(base64.b64decode(seal.seal_value).decode('utf-8'))
            
            # Extract components
            timestamp_data = seal_structure.get('timestamp_data')
            integrity_check = seal_structure.get('integrity_check')
            
            if not timestamp_data or not integrity_check:
                return ValidationResult(
                    is_valid=False,
                    status=ValidationStatus.MALFORMED,
                    errors=[ValidationError.MALFORMED_STRUCTURE]
                )
            
            # Verify document hash
            data_bytes = self._prepare_data_for_verification(document_data)
            expected_hash = hashlib.sha256(data_bytes).hexdigest()
            
            if timestamp_data.get('data_hash') != expected_hash:
                return ValidationResult(
                    is_valid=False,
                    status=ValidationStatus.INVALID,
                    errors=[ValidationError.HASH_MISMATCH]
                )
            
            # Verify timestamp integrity
            timestamp_bytes = json.dumps(timestamp_data, sort_keys=True).encode('utf-8')
            expected_hmac = hmac.new(
                self.hmac_key,
                timestamp_bytes,
                hashlib.sha256
            ).digest()
            
            stored_hmac = base64.b64decode(integrity_check)
            
            if not hmac.compare_digest(stored_hmac, expected_hmac):
                return ValidationResult(
                    is_valid=False,
                    status=ValidationStatus.INVALID,
                    errors=[ValidationError.INVALID_SIGNATURE]
                )
            
            # Verify timestamp validity
            timestamp_str = timestamp_data.get('timestamp')
            if timestamp_str:
                timestamp_validation = await self._validate_timestamp(timestamp_str)
                if not timestamp_validation['is_valid']:
                    return ValidationResult(
                        is_valid=False,
                        status=ValidationStatus.EXPIRED,
                        errors=[ValidationError.EXPIRED_TIMESTAMP],
                        warnings=timestamp_validation['warnings']
                    )
            
            return ValidationResult(
                is_valid=True,
                status=ValidationStatus.VALID,
                expires_at=seal.metadata.expires_at,
                algorithm=seal.algorithm
            )
            
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                status=ValidationStatus.MALFORMED,
                errors=[ValidationError.MALFORMED_STRUCTURE],
                metadata={'error': str(e)}
            )
    
    async def _validate_integrity_seal(self, 
                                     seal: AuthenticationSeal,
                                     document_data: Union[Dict[str, Any], str, bytes]) -> ValidationResult:
        """Validate integrity seal"""
        try:
            # Decode seal value
            seal_structure = json.loads(base64.b64decode(seal.seal_value).decode('utf-8'))
            
            # Extract components
            integrity_data = seal_structure.get('integrity_data')
            signature_b64 = seal_structure.get('signature')
            certificate_pem = seal_structure.get('certificate')
            
            if not integrity_data or not signature_b64:
                return ValidationResult(
                    is_valid=False,
                    status=ValidationStatus.MALFORMED,
                    errors=[ValidationError.MALFORMED_STRUCTURE]
                )
            
            # Get public key
            public_key = None
            certificate = None
            
            if certificate_pem:
                certificate = load_pem_x509_certificate(certificate_pem.encode('utf-8'), default_backend())
                public_key = certificate.public_key()
                
                # Validate certificate
                cert_validation = await self._validate_certificate(certificate)
                if not cert_validation['is_valid']:
                    return ValidationResult(
                        is_valid=False,
                        status=ValidationStatus.INVALID,
                        errors=[ValidationError.INVALID_CERTIFICATE],
                        warnings=cert_validation['errors']
                    )
            
            if not public_key:
                return ValidationResult(
                    is_valid=False,
                    status=ValidationStatus.INVALID,
                    errors=[ValidationError.KEY_NOT_FOUND]
                )
            
            # Verify document integrity
            data_bytes = self._prepare_data_for_verification(document_data)
            expected_hash = hashlib.sha256(data_bytes).hexdigest()
            expected_size = len(data_bytes)
            expected_checksum = hashlib.md5(data_bytes).hexdigest()
            
            if (integrity_data.get('data_hash') != expected_hash or
                integrity_data.get('data_size') != expected_size or
                integrity_data.get('checksum') != expected_checksum):
                return ValidationResult(
                    is_valid=False,
                    status=ValidationStatus.INVALID,
                    errors=[ValidationError.HASH_MISMATCH]
                )
            
            # Verify timestamp
            timestamp_str = integrity_data.get('timestamp')
            if timestamp_str:
                timestamp_validation = await self._validate_timestamp(timestamp_str)
                if not timestamp_validation['is_valid']:
                    return ValidationResult(
                        is_valid=False,
                        status=ValidationStatus.EXPIRED,
                        errors=[ValidationError.EXPIRED_TIMESTAMP],
                        warnings=timestamp_validation['warnings']
                    )
            
            # Verify signature
            signature = base64.b64decode(signature_b64)
            payload_bytes = json.dumps(integrity_data, sort_keys=True).encode('utf-8')
            
            try:
                if seal.algorithm == SealAlgorithm.RSA_PSS_SHA256:
                    public_key.verify(
                        signature,
                        payload_bytes,
                        padding.PSS(
                            mgf=padding.MGF1(hashes.SHA256()),
                            salt_length=padding.PSS.MAX_LENGTH
                        ),
                        hashes.SHA256()
                    )
                else:
                    public_key.verify(
                        signature,
                        payload_bytes,
                        padding.PKCS1v15(),
                        hashes.SHA256()
                    )
                
                return ValidationResult(
                    is_valid=True,
                    status=ValidationStatus.VALID,
                    expires_at=seal.metadata.expires_at,
                    certificate_thumbprint=self._get_certificate_thumbprint(certificate) if certificate else None,
                    algorithm=seal.algorithm
                )
                
            except InvalidSignature:
                return ValidationResult(
                    is_valid=False,
                    status=ValidationStatus.INVALID,
                    errors=[ValidationError.INVALID_SIGNATURE]
                )
            
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                status=ValidationStatus.MALFORMED,
                errors=[ValidationError.MALFORMED_STRUCTURE],
                metadata={'error': str(e)}
            )
    
    async def _validate_composite_seal(self, 
                                     seal: AuthenticationSeal,
                                     document_data: Union[Dict[str, Any], str, bytes]) -> ValidationResult:
        """Validate composite seal"""
        try:
            # Decode seal value
            seal_structure = json.loads(base64.b64decode(seal.seal_value).decode('utf-8'))
            
            # Extract components
            layers = seal_structure.get('layers', {})
            composite_hash = seal_structure.get('composite_hash')
            
            if not layers or not composite_hash:
                return ValidationResult(
                    is_valid=False,
                    status=ValidationStatus.MALFORMED,
                    errors=[ValidationError.MALFORMED_STRUCTURE]
                )
            
            # Verify composite hash
            layer_values = []
            for layer_name in sorted(layers.keys()):
                layer_values.append(layers[layer_name])
            
            calculated_composite = hashlib.sha256(
                ''.join(layer_values).encode('utf-8')
            ).hexdigest()
            
            if composite_hash != calculated_composite:
                return ValidationResult(
                    is_valid=False,
                    status=ValidationStatus.INVALID,
                    errors=[ValidationError.HASH_MISMATCH]
                )
            
            # Validate each layer
            validation_results = []
            
            for layer_name, layer_value in layers.items():
                # Create temporary seal for layer validation
                if layer_name == 'hash':
                    layer_seal = AuthenticationSeal(
                        seal_id=f"{seal.seal_id}_hash",
                        document_id=seal.document_id,
                        seal_type=SealType.DOCUMENT_HASH,
                        seal_value=layer_value,
                        algorithm=SealAlgorithm.SHA256,
                        status=seal.status,
                        metadata=seal.metadata
                    )
                    result = await self._validate_document_hash(layer_seal, document_data)
                    
                elif layer_name == 'stamp':
                    layer_seal = AuthenticationSeal(
                        seal_id=f"{seal.seal_id}_stamp",
                        document_id=seal.document_id,
                        seal_type=SealType.CRYPTOGRAPHIC_STAMP,
                        seal_value=layer_value,
                        algorithm=SealAlgorithm.HMAC_SHA256,
                        status=seal.status,
                        metadata=seal.metadata
                    )
                    result = await self._validate_cryptographic_stamp(layer_seal, document_data)
                    
                elif layer_name == 'signature':
                    layer_seal = AuthenticationSeal(
                        seal_id=f"{seal.seal_id}_signature",
                        document_id=seal.document_id,
                        seal_type=SealType.DIGITAL_SIGNATURE,
                        seal_value=layer_value,
                        algorithm=SealAlgorithm.RSA_SHA256,
                        status=seal.status,
                        metadata=seal.metadata
                    )
                    result = await self._validate_digital_signature(layer_seal, document_data)
                
                validation_results.append(result)
            
            # Determine overall result
            all_valid = all(result.is_valid for result in validation_results)
            all_errors = []
            all_warnings = []
            
            for result in validation_results:
                all_errors.extend(result.errors)
                all_warnings.extend(result.warnings)
            
            if all_valid:
                return ValidationResult(
                    is_valid=True,
                    status=ValidationStatus.VALID,
                    expires_at=seal.metadata.expires_at,
                    algorithm=seal.algorithm,
                    warnings=all_warnings
                )
            else:
                return ValidationResult(
                    is_valid=False,
                    status=ValidationStatus.INVALID,
                    errors=all_errors,
                    warnings=all_warnings
                )
            
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                status=ValidationStatus.MALFORMED,
                errors=[ValidationError.MALFORMED_STRUCTURE],
                metadata={'error': str(e)}
            )
    
    async def _validate_certificate(self, certificate: Certificate) -> Dict[str, Any]:
        """Validate certificate"""
        try:
            current_time = datetime.utcnow()
            
            # Check validity period
            if current_time < certificate.not_valid_before:
                return {
                    'is_valid': False,
                    'errors': ['Certificate not yet valid']
                }
            
            if current_time > certificate.not_valid_after:
                return {
                    'is_valid': False,
                    'errors': ['Certificate expired']
                }
            
            # Check if certificate is revoked
            thumbprint = self._get_certificate_thumbprint(certificate)
            if thumbprint in self.trust_store.revoked_certificates:
                return {
                    'is_valid': False,
                    'errors': ['Certificate revoked']
                }
            
            # Check trusted issuers
            issuer = certificate.issuer.rfc4514_string()
            if self.trust_store.trusted_issuers and issuer not in self.trust_store.trusted_issuers:
                return {
                    'is_valid': False,
                    'errors': ['Untrusted issuer']
                }
            
            return {
                'is_valid': True,
                'errors': []
            }
            
        except Exception as e:
            return {
                'is_valid': False,
                'errors': [f'Certificate validation error: {str(e)}']
            }
    
    async def _validate_timestamp(self, timestamp_str: str) -> Dict[str, Any]:
        """Validate timestamp"""
        try:
            # Parse timestamp
            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            current_time = datetime.utcnow()
            
            # Check if timestamp is too old or too new
            time_diff = abs((current_time - timestamp).total_seconds())
            
            if time_diff > self.time_tolerance:
                return {
                    'is_valid': False,
                    'warnings': [f'Timestamp outside tolerance: {time_diff} seconds']
                }
            
            return {
                'is_valid': True,
                'warnings': []
            }
            
        except Exception as e:
            return {
                'is_valid': False,
                'warnings': [f'Invalid timestamp format: {str(e)}']
            }
    
    def _prepare_data_for_verification(self, document_data: Union[Dict[str, Any], str, bytes]) -> bytes:
        """Prepare document data for verification"""
        if isinstance(document_data, dict):
            return json.dumps(document_data, sort_keys=True).encode('utf-8')
        elif isinstance(document_data, str):
            return document_data.encode('utf-8')
        elif isinstance(document_data, bytes):
            return document_data
        else:
            return str(document_data).encode('utf-8')
    
    def _get_certificate_thumbprint(self, certificate: Certificate) -> str:
        """Get certificate thumbprint"""
        cert_der = certificate.public_bytes(serialization.Encoding.DER)
        return hashlib.sha256(cert_der).hexdigest()
    
    async def _add_trusted_certificates(self, certificates: List[str]):
        """Add trusted certificates"""
        for cert_pem in certificates:
            try:
                certificate = load_pem_x509_certificate(cert_pem.encode('utf-8'), default_backend())
                self.trust_store.trusted_certificates.append(certificate)
                
                # Cache certificate
                thumbprint = self._get_certificate_thumbprint(certificate)
                self.certificate_cache[thumbprint] = certificate
                
            except Exception as e:
                logger.warning(f"Failed to load certificate: {e}")
    
    def _update_metrics(self, 
                       seal_type: SealType,
                       algorithm: SealAlgorithm,
                       validation_time: float,
                       success: bool):
        """Update validation metrics"""
        self.metrics['total_validations'] += 1
        
        if success:
            self.metrics['successful_validations'] += 1
        else:
            self.metrics['failed_validations'] += 1
        
        # Update type and algorithm metrics
        type_key = seal_type.value
        self.metrics['validations_by_type'][type_key] = self.metrics['validations_by_type'].get(type_key, 0) + 1
        
        algo_key = algorithm.value
        self.metrics['validations_by_algorithm'][algo_key] = self.metrics['validations_by_algorithm'].get(algo_key, 0) + 1
        
        # Update average validation time
        total_validations = self.metrics['total_validations']
        current_avg = self.metrics['average_validation_time']
        self.metrics['average_validation_time'] = (
            (current_avg * (total_validations - 1) + validation_time) / total_validations
        )
    
    async def validate_batch_stamps(self, 
                                  seals: List[Tuple[AuthenticationSeal, Union[Dict[str, Any], str, bytes]]]) -> List[ValidationResult]:
        """Validate multiple stamps"""
        results = []
        
        for seal, document_data in seals:
            result = await self.validate_stamp(seal, document_data)
            results.append(result)
        
        return results
    
    def add_trusted_issuer(self, issuer: str):
        """Add trusted issuer"""
        self.trust_store.trusted_issuers.append(issuer)
    
    def revoke_certificate(self, thumbprint: str):
        """Revoke certificate"""
        self.trust_store.revoked_certificates.append(thumbprint)
    
    def get_certificate_info(self, certificate: Certificate) -> CertificateInfo:
        """Get certificate information"""
        try:
            return CertificateInfo(
                subject=certificate.subject.rfc4514_string(),
                issuer=certificate.issuer.rfc4514_string(),
                serial_number=str(certificate.serial_number),
                not_before=certificate.not_valid_before,
                not_after=certificate.not_valid_after,
                thumbprint=self._get_certificate_thumbprint(certificate),
                algorithm=certificate.signature_algorithm_oid._name,
                key_size=certificate.public_key().key_size,
                is_valid=True
            )
        except Exception as e:
            return CertificateInfo(
                subject="Unknown",
                issuer="Unknown",
                serial_number="Unknown",
                not_before=datetime.utcnow(),
                not_after=datetime.utcnow(),
                thumbprint="Unknown",
                algorithm="Unknown",
                key_size=0,
                is_valid=False,
                validation_errors=[str(e)]
            )
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get validation metrics"""
        return {
            **self.metrics,
            'success_rate': (
                self.metrics['successful_validations'] / 
                max(self.metrics['total_validations'], 1)
            ) * 100,
            'trusted_certificates': len(self.trust_store.trusted_certificates),
            'trusted_issuers': len(self.trust_store.trusted_issuers),
            'revoked_certificates': len(self.trust_store.revoked_certificates)
        }


# Factory functions for easy setup
def create_stamp_validator(hmac_key: Optional[bytes] = None,
                         trust_store: Optional[TrustStore] = None) -> StampValidator:
    """Create stamp validator instance"""
    return StampValidator(hmac_key, trust_store)


def create_trust_store(trusted_certificates: Optional[List[str]] = None,
                      trusted_issuers: Optional[List[str]] = None) -> TrustStore:
    """Create trust store"""
    trust_store = TrustStore()
    
    if trusted_certificates:
        for cert_pem in trusted_certificates:
            try:
                certificate = load_pem_x509_certificate(cert_pem.encode('utf-8'), default_backend())
                trust_store.trusted_certificates.append(certificate)
            except Exception as e:
                logger.warning(f"Failed to load certificate: {e}")
    
    if trusted_issuers:
        trust_store.trusted_issuers.extend(trusted_issuers)
    
    return trust_store


async def validate_seal(seal: AuthenticationSeal,
                       document_data: Union[Dict[str, Any], str, bytes],
                       hmac_key: Optional[bytes] = None) -> ValidationResult:
    """Validate authentication seal"""
    validator = create_stamp_validator(hmac_key)
    return await validator.validate_stamp(seal, document_data)