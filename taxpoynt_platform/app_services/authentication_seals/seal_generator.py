"""
Authentication Seal Generator Service for APP Role

This service generates authentication seals for documents including:
- Digital signatures with PKI
- Cryptographic stamps
- Document hashes and checksums
- Timestamp seals
- Multi-layer authentication seals
"""

import hashlib
import hmac
import json
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging
import base64
import os

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.x509 import load_pem_x509_certificate
from cryptography.hazmat.primitives.serialization import load_pem_private_key, load_pem_public_key

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SealType(Enum):
    """Types of authentication seals"""
    DIGITAL_SIGNATURE = "digital_signature"
    CRYPTOGRAPHIC_STAMP = "cryptographic_stamp"
    DOCUMENT_HASH = "document_hash"
    TIMESTAMP_SEAL = "timestamp_seal"
    INTEGRITY_SEAL = "integrity_seal"
    COMPOSITE_SEAL = "composite_seal"


class SealAlgorithm(Enum):
    """Cryptographic algorithms for seals"""
    RSA_SHA256 = "rsa_sha256"
    RSA_PSS_SHA256 = "rsa_pss_sha256"
    HMAC_SHA256 = "hmac_sha256"
    HMAC_SHA512 = "hmac_sha512"
    SHA256 = "sha256"
    SHA512 = "sha512"
    AES_256_GCM = "aes_256_gcm"


class SealStatus(Enum):
    """Status of authentication seals"""
    PENDING = "pending"
    GENERATED = "generated"
    VERIFIED = "verified"
    INVALID = "invalid"
    EXPIRED = "expired"
    REVOKED = "revoked"


@dataclass
class SealMetadata:
    """Metadata for authentication seals"""
    seal_id: str
    seal_type: SealType
    algorithm: SealAlgorithm
    created_at: datetime
    expires_at: Optional[datetime] = None
    issuer: str = "TaxPoynt-APP"
    version: str = "1.0"
    certificate_thumbprint: Optional[str] = None
    key_id: Optional[str] = None
    additional_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AuthenticationSeal:
    """Complete authentication seal"""
    seal_id: str
    document_id: str
    seal_type: SealType
    seal_value: str
    algorithm: SealAlgorithm
    status: SealStatus
    metadata: SealMetadata
    verification_data: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class SealConfiguration:
    """Configuration for seal generation"""
    algorithm: SealAlgorithm
    key_size: int = 2048
    validity_hours: int = 24
    include_timestamp: bool = True
    include_certificate: bool = True
    compression: bool = False
    encoding: str = "base64"
    additional_claims: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SealGenerationResult:
    """Result of seal generation"""
    seal: AuthenticationSeal
    success: bool
    error_message: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    generation_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class SealGenerator:
    """
    Authentication seal generator service for APP role
    
    Handles:
    - Digital signatures with PKI
    - Cryptographic stamps
    - Document hashes and checksums
    - Timestamp seals
    - Multi-layer authentication seals
    """
    
    def __init__(self, 
                 private_key_path: Optional[str] = None,
                 certificate_path: Optional[str] = None,
                 hmac_key: Optional[bytes] = None,
                 default_algorithm: SealAlgorithm = SealAlgorithm.RSA_SHA256):
        self.private_key_path = private_key_path
        self.certificate_path = certificate_path
        self.hmac_key = hmac_key or os.urandom(32)
        self.default_algorithm = default_algorithm
        
        # Load cryptographic materials
        self.private_key = None
        self.certificate = None
        self.public_key = None
        
        if private_key_path:
            self._load_private_key(private_key_path)
        
        if certificate_path:
            self._load_certificate(certificate_path)
        
        # Default configurations
        self.default_configs = {
            SealType.DIGITAL_SIGNATURE: SealConfiguration(
                algorithm=SealAlgorithm.RSA_SHA256,
                key_size=2048,
                validity_hours=24,
                include_timestamp=True,
                include_certificate=True
            ),
            SealType.CRYPTOGRAPHIC_STAMP: SealConfiguration(
                algorithm=SealAlgorithm.HMAC_SHA256,
                validity_hours=48,
                include_timestamp=True,
                include_certificate=False
            ),
            SealType.DOCUMENT_HASH: SealConfiguration(
                algorithm=SealAlgorithm.SHA256,
                validity_hours=168,  # 7 days
                include_timestamp=True,
                include_certificate=False
            ),
            SealType.TIMESTAMP_SEAL: SealConfiguration(
                algorithm=SealAlgorithm.HMAC_SHA256,
                validity_hours=8760,  # 1 year
                include_timestamp=True,
                include_certificate=False
            ),
            SealType.INTEGRITY_SEAL: SealConfiguration(
                algorithm=SealAlgorithm.RSA_PSS_SHA256,
                key_size=2048,
                validity_hours=24,
                include_timestamp=True,
                include_certificate=True
            )
        }
        
        # Metrics
        self.metrics = {
            'total_seals_generated': 0,
            'successful_generations': 0,
            'failed_generations': 0,
            'seals_by_type': {},
            'seals_by_algorithm': {},
            'average_generation_time': 0.0
        }
    
    def _load_private_key(self, key_path: str):
        """Load private key from file"""
        try:
            with open(key_path, 'rb') as key_file:
                self.private_key = load_pem_private_key(
                    key_file.read(),
                    password=None,
                    backend=default_backend()
                )
            logger.info(f"Private key loaded from {key_path}")
        except Exception as e:
            logger.error(f"Failed to load private key: {e}")
    
    def _load_certificate(self, cert_path: str):
        """Load certificate from file"""
        try:
            with open(cert_path, 'rb') as cert_file:
                self.certificate = load_pem_x509_certificate(
                    cert_file.read(),
                    backend=default_backend()
                )
                self.public_key = self.certificate.public_key()
            logger.info(f"Certificate loaded from {cert_path}")
        except Exception as e:
            logger.error(f"Failed to load certificate: {e}")
    
    async def generate_seal(self, 
                          document_id: str,
                          document_data: Union[Dict[str, Any], str, bytes],
                          seal_type: SealType,
                          config: Optional[SealConfiguration] = None) -> SealGenerationResult:
        """
        Generate authentication seal for document
        
        Args:
            document_id: Document identifier
            document_data: Document data to seal
            seal_type: Type of seal to generate
            config: Optional seal configuration
            
        Returns:
            SealGenerationResult with generated seal
        """
        start_time = time.time()
        
        # Use default config if not provided
        if config is None:
            config = self.default_configs.get(seal_type, SealConfiguration(self.default_algorithm))
        
        # Generate seal ID
        seal_id = str(uuid.uuid4())
        
        try:
            # Generate seal based on type
            if seal_type == SealType.DIGITAL_SIGNATURE:
                seal_value = await self._generate_digital_signature(document_data, config)
            elif seal_type == SealType.CRYPTOGRAPHIC_STAMP:
                seal_value = await self._generate_cryptographic_stamp(document_data, config)
            elif seal_type == SealType.DOCUMENT_HASH:
                seal_value = await self._generate_document_hash(document_data, config)
            elif seal_type == SealType.TIMESTAMP_SEAL:
                seal_value = await self._generate_timestamp_seal(document_data, config)
            elif seal_type == SealType.INTEGRITY_SEAL:
                seal_value = await self._generate_integrity_seal(document_data, config)
            elif seal_type == SealType.COMPOSITE_SEAL:
                seal_value = await self._generate_composite_seal(document_data, config)
            else:
                raise ValueError(f"Unsupported seal type: {seal_type}")
            
            # Create seal metadata
            metadata = SealMetadata(
                seal_id=seal_id,
                seal_type=seal_type,
                algorithm=config.algorithm,
                created_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(hours=config.validity_hours) if config.validity_hours else None,
                certificate_thumbprint=self._get_certificate_thumbprint() if config.include_certificate else None,
                key_id=self._get_key_id(),
                additional_data=config.additional_claims
            )
            
            # Create authentication seal
            seal = AuthenticationSeal(
                seal_id=seal_id,
                document_id=document_id,
                seal_type=seal_type,
                seal_value=seal_value,
                algorithm=config.algorithm,
                status=SealStatus.GENERATED,
                metadata=metadata,
                verification_data=self._create_verification_data(document_data, config)
            )
            
            # Create result
            generation_time = time.time() - start_time
            result = SealGenerationResult(
                seal=seal,
                success=True,
                generation_time=generation_time
            )
            
            # Update metrics
            self._update_metrics(seal_type, config.algorithm, generation_time, True)
            
            logger.info(f"Seal generated successfully: {seal_id} ({seal_type.value})")
            
            return result
            
        except Exception as e:
            # Handle generation error
            generation_time = time.time() - start_time
            result = SealGenerationResult(
                seal=None,
                success=False,
                error_message=str(e),
                generation_time=generation_time
            )
            
            # Update metrics
            self._update_metrics(seal_type, config.algorithm, generation_time, False)
            
            logger.error(f"Seal generation failed for {document_id}: {e}")
            
            return result
    
    async def _generate_digital_signature(self, 
                                        document_data: Union[Dict[str, Any], str, bytes],
                                        config: SealConfiguration) -> str:
        """Generate digital signature seal"""
        if not self.private_key:
            raise ValueError("Private key not loaded for digital signature")
        
        # Prepare data for signing
        data_bytes = self._prepare_data_for_signing(document_data)
        
        # Create signature payload
        signature_payload = {
            'data_hash': hashlib.sha256(data_bytes).hexdigest(),
            'timestamp': datetime.utcnow().isoformat(),
            'algorithm': config.algorithm.value,
            'issuer': 'TaxPoynt-APP'
        }
        
        if config.additional_claims:
            signature_payload.update(config.additional_claims)
        
        payload_bytes = json.dumps(signature_payload, sort_keys=True).encode('utf-8')
        
        # Sign based on algorithm
        if config.algorithm == SealAlgorithm.RSA_SHA256:
            signature = self.private_key.sign(
                payload_bytes,
                padding.PKCS1v15(),
                hashes.SHA256()
            )
        elif config.algorithm == SealAlgorithm.RSA_PSS_SHA256:
            signature = self.private_key.sign(
                payload_bytes,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
        else:
            raise ValueError(f"Unsupported signature algorithm: {config.algorithm}")
        
        # Encode signature
        encoded_signature = base64.b64encode(signature).decode('utf-8')
        
        # Create seal structure
        seal_structure = {
            'signature': encoded_signature,
            'payload': signature_payload,
            'certificate': self._get_certificate_pem() if config.include_certificate else None
        }
        
        return base64.b64encode(json.dumps(seal_structure).encode('utf-8')).decode('utf-8')
    
    async def _generate_cryptographic_stamp(self, 
                                          document_data: Union[Dict[str, Any], str, bytes],
                                          config: SealConfiguration) -> str:
        """Generate cryptographic stamp seal"""
        # Prepare data for stamping
        data_bytes = self._prepare_data_for_signing(document_data)
        
        # Create stamp payload
        stamp_payload = {
            'data_hash': hashlib.sha256(data_bytes).hexdigest(),
            'timestamp': datetime.utcnow().isoformat(),
            'nonce': str(uuid.uuid4()),
            'algorithm': config.algorithm.value
        }
        
        if config.additional_claims:
            stamp_payload.update(config.additional_claims)
        
        payload_bytes = json.dumps(stamp_payload, sort_keys=True).encode('utf-8')
        
        # Create HMAC stamp
        if config.algorithm == SealAlgorithm.HMAC_SHA256:
            stamp = hmac.new(
                self.hmac_key,
                payload_bytes,
                hashlib.sha256
            ).digest()
        elif config.algorithm == SealAlgorithm.HMAC_SHA512:
            stamp = hmac.new(
                self.hmac_key,
                payload_bytes,
                hashlib.sha512
            ).digest()
        else:
            raise ValueError(f"Unsupported stamp algorithm: {config.algorithm}")
        
        # Create stamp structure
        stamp_structure = {
            'stamp': base64.b64encode(stamp).decode('utf-8'),
            'payload': stamp_payload
        }
        
        return base64.b64encode(json.dumps(stamp_structure).encode('utf-8')).decode('utf-8')
    
    async def _generate_document_hash(self, 
                                    document_data: Union[Dict[str, Any], str, bytes],
                                    config: SealConfiguration) -> str:
        """Generate document hash seal"""
        # Prepare data for hashing
        data_bytes = self._prepare_data_for_signing(document_data)
        
        # Create hash based on algorithm
        if config.algorithm == SealAlgorithm.SHA256:
            hash_obj = hashlib.sha256()
        elif config.algorithm == SealAlgorithm.SHA512:
            hash_obj = hashlib.sha512()
        else:
            raise ValueError(f"Unsupported hash algorithm: {config.algorithm}")
        
        hash_obj.update(data_bytes)
        document_hash = hash_obj.hexdigest()
        
        # Create hash structure
        hash_structure = {
            'hash': document_hash,
            'algorithm': config.algorithm.value,
            'timestamp': datetime.utcnow().isoformat(),
            'data_size': len(data_bytes)
        }
        
        if config.additional_claims:
            hash_structure.update(config.additional_claims)
        
        return base64.b64encode(json.dumps(hash_structure).encode('utf-8')).decode('utf-8')
    
    async def _generate_timestamp_seal(self, 
                                     document_data: Union[Dict[str, Any], str, bytes],
                                     config: SealConfiguration) -> str:
        """Generate timestamp seal"""
        # Prepare data for timestamping
        data_bytes = self._prepare_data_for_signing(document_data)
        
        # Create timestamp payload
        timestamp_payload = {
            'data_hash': hashlib.sha256(data_bytes).hexdigest(),
            'timestamp': datetime.utcnow().isoformat(),
            'unix_timestamp': int(time.time()),
            'timezone': 'UTC',
            'precision': 'seconds'
        }
        
        if config.additional_claims:
            timestamp_payload.update(config.additional_claims)
        
        payload_bytes = json.dumps(timestamp_payload, sort_keys=True).encode('utf-8')
        
        # Create HMAC for timestamp integrity
        timestamp_hmac = hmac.new(
            self.hmac_key,
            payload_bytes,
            hashlib.sha256
        ).digest()
        
        # Create timestamp structure
        timestamp_structure = {
            'timestamp_data': timestamp_payload,
            'integrity_check': base64.b64encode(timestamp_hmac).decode('utf-8')
        }
        
        return base64.b64encode(json.dumps(timestamp_structure).encode('utf-8')).decode('utf-8')
    
    async def _generate_integrity_seal(self, 
                                     document_data: Union[Dict[str, Any], str, bytes],
                                     config: SealConfiguration) -> str:
        """Generate integrity seal"""
        if not self.private_key:
            raise ValueError("Private key not loaded for integrity seal")
        
        # Prepare data for integrity checking
        data_bytes = self._prepare_data_for_signing(document_data)
        
        # Create integrity payload
        integrity_payload = {
            'data_hash': hashlib.sha256(data_bytes).hexdigest(),
            'data_size': len(data_bytes),
            'timestamp': datetime.utcnow().isoformat(),
            'checksum': hashlib.md5(data_bytes).hexdigest(),
            'algorithm': config.algorithm.value
        }
        
        if config.additional_claims:
            integrity_payload.update(config.additional_claims)
        
        payload_bytes = json.dumps(integrity_payload, sort_keys=True).encode('utf-8')
        
        # Sign integrity payload
        if config.algorithm == SealAlgorithm.RSA_PSS_SHA256:
            signature = self.private_key.sign(
                payload_bytes,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
        else:
            signature = self.private_key.sign(
                payload_bytes,
                padding.PKCS1v15(),
                hashes.SHA256()
            )
        
        # Create integrity structure
        integrity_structure = {
            'integrity_data': integrity_payload,
            'signature': base64.b64encode(signature).decode('utf-8'),
            'certificate': self._get_certificate_pem() if config.include_certificate else None
        }
        
        return base64.b64encode(json.dumps(integrity_structure).encode('utf-8')).decode('utf-8')
    
    async def _generate_composite_seal(self, 
                                     document_data: Union[Dict[str, Any], str, bytes],
                                     config: SealConfiguration) -> str:
        """Generate composite seal with multiple layers"""
        # Generate multiple seal types
        hash_config = SealConfiguration(SealAlgorithm.SHA256, validity_hours=config.validity_hours)
        stamp_config = SealConfiguration(SealAlgorithm.HMAC_SHA256, validity_hours=config.validity_hours)
        
        document_hash = await self._generate_document_hash(document_data, hash_config)
        crypto_stamp = await self._generate_cryptographic_stamp(document_data, stamp_config)
        
        # Create composite structure
        composite_structure = {
            'layers': {
                'hash': document_hash,
                'stamp': crypto_stamp
            },
            'composite_hash': hashlib.sha256(
                (document_hash + crypto_stamp).encode('utf-8')
            ).hexdigest(),
            'timestamp': datetime.utcnow().isoformat(),
            'algorithm': config.algorithm.value
        }
        
        # Add digital signature if private key available
        if self.private_key:
            sig_config = SealConfiguration(SealAlgorithm.RSA_SHA256, validity_hours=config.validity_hours)
            digital_signature = await self._generate_digital_signature(document_data, sig_config)
            composite_structure['layers']['signature'] = digital_signature
        
        return base64.b64encode(json.dumps(composite_structure).encode('utf-8')).decode('utf-8')
    
    def _prepare_data_for_signing(self, document_data: Union[Dict[str, Any], str, bytes]) -> bytes:
        """Prepare document data for signing"""
        if isinstance(document_data, dict):
            return json.dumps(document_data, sort_keys=True).encode('utf-8')
        elif isinstance(document_data, str):
            return document_data.encode('utf-8')
        elif isinstance(document_data, bytes):
            return document_data
        else:
            return str(document_data).encode('utf-8')
    
    def _get_certificate_thumbprint(self) -> Optional[str]:
        """Get certificate thumbprint"""
        if not self.certificate:
            return None
        
        cert_der = self.certificate.public_bytes(serialization.Encoding.DER)
        thumbprint = hashlib.sha256(cert_der).hexdigest()
        return thumbprint
    
    def _get_certificate_pem(self) -> Optional[str]:
        """Get certificate in PEM format"""
        if not self.certificate:
            return None
        
        cert_pem = self.certificate.public_bytes(serialization.Encoding.PEM)
        return cert_pem.decode('utf-8')
    
    def _get_key_id(self) -> str:
        """Get key identifier"""
        if self.private_key:
            # Use thumbprint of public key
            public_key_der = self.private_key.public_key().public_bytes(
                encoding=serialization.Encoding.DER,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            return hashlib.sha256(public_key_der).hexdigest()[:16]
        else:
            # Use HMAC key hash
            return hashlib.sha256(self.hmac_key).hexdigest()[:16]
    
    def _create_verification_data(self, 
                                document_data: Union[Dict[str, Any], str, bytes],
                                config: SealConfiguration) -> Dict[str, Any]:
        """Create verification data for seal"""
        data_bytes = self._prepare_data_for_signing(document_data)
        
        return {
            'data_hash': hashlib.sha256(data_bytes).hexdigest(),
            'data_size': len(data_bytes),
            'algorithm': config.algorithm.value,
            'key_id': self._get_key_id(),
            'created_at': datetime.utcnow().isoformat()
        }
    
    def _update_metrics(self, 
                       seal_type: SealType,
                       algorithm: SealAlgorithm,
                       generation_time: float,
                       success: bool):
        """Update generation metrics"""
        self.metrics['total_seals_generated'] += 1
        
        if success:
            self.metrics['successful_generations'] += 1
        else:
            self.metrics['failed_generations'] += 1
        
        # Update type and algorithm metrics
        type_key = seal_type.value
        self.metrics['seals_by_type'][type_key] = self.metrics['seals_by_type'].get(type_key, 0) + 1
        
        algo_key = algorithm.value
        self.metrics['seals_by_algorithm'][algo_key] = self.metrics['seals_by_algorithm'].get(algo_key, 0) + 1
        
        # Update average generation time
        total_generations = self.metrics['total_seals_generated']
        current_avg = self.metrics['average_generation_time']
        self.metrics['average_generation_time'] = (
            (current_avg * (total_generations - 1) + generation_time) / total_generations
        )
    
    async def generate_batch_seals(self, 
                                 documents: List[Tuple[str, Union[Dict[str, Any], str, bytes]]],
                                 seal_type: SealType,
                                 config: Optional[SealConfiguration] = None) -> List[SealGenerationResult]:
        """Generate seals for multiple documents"""
        results = []
        
        for document_id, document_data in documents:
            result = await self.generate_seal(document_id, document_data, seal_type, config)
            results.append(result)
        
        return results
    
    def get_supported_algorithms(self) -> List[SealAlgorithm]:
        """Get list of supported algorithms"""
        return list(SealAlgorithm)
    
    def get_supported_seal_types(self) -> List[SealType]:
        """Get list of supported seal types"""
        return list(SealType)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get seal generation metrics"""
        return {
            **self.metrics,
            'success_rate': (
                self.metrics['successful_generations'] / 
                max(self.metrics['total_seals_generated'], 1)
            ) * 100,
            'has_private_key': self.private_key is not None,
            'has_certificate': self.certificate is not None
        }


# Factory functions for easy setup
def create_seal_generator(private_key_path: Optional[str] = None,
                         certificate_path: Optional[str] = None,
                         hmac_key: Optional[bytes] = None,
                         algorithm: SealAlgorithm = SealAlgorithm.RSA_SHA256) -> SealGenerator:
    """Create seal generator instance"""
    return SealGenerator(private_key_path, certificate_path, hmac_key, algorithm)


def create_seal_configuration(algorithm: SealAlgorithm,
                            validity_hours: int = 24,
                            include_timestamp: bool = True,
                            include_certificate: bool = True,
                            **kwargs) -> SealConfiguration:
    """Create seal configuration"""
    return SealConfiguration(
        algorithm=algorithm,
        validity_hours=validity_hours,
        include_timestamp=include_timestamp,
        include_certificate=include_certificate,
        **kwargs
    )


async def generate_document_seal(document_id: str,
                               document_data: Union[Dict[str, Any], str, bytes],
                               seal_type: SealType = SealType.DIGITAL_SIGNATURE,
                               private_key_path: Optional[str] = None,
                               certificate_path: Optional[str] = None) -> SealGenerationResult:
    """Generate document seal"""
    generator = create_seal_generator(private_key_path, certificate_path)
    return await generator.generate_seal(document_id, document_data, seal_type)