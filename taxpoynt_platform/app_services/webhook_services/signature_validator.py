"""
APP Service: Signature Validator
Validates webhook signatures for security and authenticity
"""

import asyncio
import hmac
import hashlib
import base64
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List, Union, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import json
import time
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.exceptions import InvalidSignature
import jwt


class SignatureAlgorithm(str, Enum):
    """Supported signature algorithms"""
    HMAC_SHA256 = "hmac_sha256"
    HMAC_SHA512 = "hmac_sha512"
    RSA_SHA256 = "rsa_sha256"
    RSA_SHA512 = "rsa_sha512"
    JWT_HS256 = "jwt_hs256"
    JWT_RS256 = "jwt_rs256"


class ValidationResult(str, Enum):
    """Signature validation results"""
    VALID = "valid"
    INVALID = "invalid"
    EXPIRED = "expired"
    MALFORMED = "malformed"
    ALGORITHM_MISMATCH = "algorithm_mismatch"
    KEY_NOT_FOUND = "key_not_found"
    REPLAY_ATTACK = "replay_attack"


@dataclass
class SignatureConfig:
    """Configuration for signature validation"""
    algorithm: SignatureAlgorithm
    secret_key: Optional[str] = None
    public_key: Optional[str] = None
    tolerance_seconds: int = 300  # 5 minutes
    require_timestamp: bool = True
    prevent_replay: bool = True
    max_body_size: int = 1024 * 1024  # 1MB
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ValidationContext:
    """Context for signature validation"""
    webhook_id: str
    timestamp: Optional[datetime]
    signature: str
    algorithm: SignatureAlgorithm
    payload: bytes
    headers: Dict[str, str]
    source_ip: str
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        if self.timestamp:
            data['timestamp'] = self.timestamp.isoformat()
        data['payload'] = base64.b64encode(self.payload).decode('utf-8')
        return data


@dataclass
class ValidationReport:
    """Detailed validation report"""
    result: ValidationResult
    algorithm_used: SignatureAlgorithm
    validation_time: float
    timestamp_valid: bool
    message: str
    error_details: Optional[Dict[str, Any]] = None
    security_warnings: Optional[List[str]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class HMACValidator:
    """HMAC signature validator"""
    
    def __init__(self, secret_key: str):
        self.secret_key = secret_key.encode('utf-8')
    
    async def validate(self, 
                      payload: bytes, 
                      signature: str, 
                      algorithm: SignatureAlgorithm) -> bool:
        """Validate HMAC signature"""
        try:
            # Parse signature (format: "sha256=<hash>" or just "<hash>")
            if '=' in signature:
                _, signature_hash = signature.split('=', 1)
            else:
                signature_hash = signature
            
            # Select hash algorithm
            if algorithm == SignatureAlgorithm.HMAC_SHA256:
                hash_func = hashlib.sha256
            elif algorithm == SignatureAlgorithm.HMAC_SHA512:
                hash_func = hashlib.sha512
            else:
                return False
            
            # Compute expected signature
            expected_hash = hmac.new(
                self.secret_key,
                payload,
                hash_func
            ).hexdigest()
            
            # Constant-time comparison
            return hmac.compare_digest(signature_hash, expected_hash)
            
        except Exception:
            return False


class RSAValidator:
    """RSA signature validator"""
    
    def __init__(self, public_key: str):
        self.public_key = self._load_public_key(public_key)
    
    def _load_public_key(self, key_data: str):
        """Load RSA public key"""
        try:
            # Handle different key formats
            if key_data.startswith('-----BEGIN'):
                key_bytes = key_data.encode('utf-8')
            else:
                # Assume base64 encoded
                key_bytes = base64.b64decode(key_data)
            
            return serialization.load_pem_public_key(key_bytes)
        except Exception as e:
            raise ValueError(f"Invalid public key format: {str(e)}")
    
    async def validate(self, 
                      payload: bytes, 
                      signature: str, 
                      algorithm: SignatureAlgorithm) -> bool:
        """Validate RSA signature"""
        try:
            # Decode signature
            signature_bytes = base64.b64decode(signature)
            
            # Select hash algorithm and padding
            if algorithm == SignatureAlgorithm.RSA_SHA256:
                hash_alg = hashes.SHA256()
            elif algorithm == SignatureAlgorithm.RSA_SHA512:
                hash_alg = hashes.SHA512()
            else:
                return False
            
            # Verify signature
            self.public_key.verify(
                signature_bytes,
                payload,
                padding.PKCS1v15(),
                hash_alg
            )
            return True
            
        except InvalidSignature:
            return False
        except Exception:
            return False


class JWTValidator:
    """JWT signature validator"""
    
    def __init__(self, secret_or_key: str, algorithm: SignatureAlgorithm):
        self.secret_or_key = secret_or_key
        self.algorithm = algorithm
    
    async def validate(self, 
                      payload: bytes, 
                      token: str, 
                      algorithm: SignatureAlgorithm) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """Validate JWT token"""
        try:
            # Map algorithm
            jwt_algorithm = "HS256" if algorithm == SignatureAlgorithm.JWT_HS256 else "RS256"
            
            # Decode and verify JWT
            decoded = jwt.decode(
                token,
                self.secret_or_key,
                algorithms=[jwt_algorithm]
            )
            
            # Verify payload hash if present
            if 'payload_hash' in decoded:
                expected_hash = hashlib.sha256(payload).hexdigest()
                if decoded['payload_hash'] != expected_hash:
                    return False, None
            
            return True, decoded
            
        except jwt.InvalidTokenError:
            return False, None
        except Exception:
            return False, None


class SignatureValidator:
    """
    Main signature validator for webhook security
    Supports multiple signature algorithms and validation methods
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.configurations: Dict[str, SignatureConfig] = {}
        self.validators: Dict[SignatureAlgorithm, Any] = {}
        
        # Replay attack prevention (in production, use Redis)
        self._processed_signatures: Dict[str, datetime] = {}
        self._cleanup_interval = 3600  # 1 hour
        self._last_cleanup = time.time()
        
        # Validation statistics
        self.stats = {
            'total_validations': 0,
            'successful_validations': 0,
            'failed_validations': 0,
            'replay_attempts': 0,
            'expired_signatures': 0,
            'malformed_signatures': 0,
            'algorithm_stats': {},
            'last_validation_at': None
        }
    
    def configure(self, 
                  name: str, 
                  algorithm: SignatureAlgorithm,
                  secret_key: Optional[str] = None,
                  public_key: Optional[str] = None,
                  **kwargs) -> None:
        """
        Configure signature validation for a specific endpoint or service
        
        Args:
            name: Configuration name/identifier
            algorithm: Signature algorithm to use
            secret_key: Secret key for HMAC or JWT HS256
            public_key: Public key for RSA or JWT RS256
            **kwargs: Additional configuration options
        """
        config = SignatureConfig(
            algorithm=algorithm,
            secret_key=secret_key,
            public_key=public_key,
            **kwargs
        )
        
        self.configurations[name] = config
        
        # Initialize validator
        try:
            if algorithm in [SignatureAlgorithm.HMAC_SHA256, SignatureAlgorithm.HMAC_SHA512]:
                if not secret_key:
                    raise ValueError("Secret key required for HMAC")
                self.validators[algorithm] = HMACValidator(secret_key)
                
            elif algorithm in [SignatureAlgorithm.RSA_SHA256, SignatureAlgorithm.RSA_SHA512]:
                if not public_key:
                    raise ValueError("Public key required for RSA")
                self.validators[algorithm] = RSAValidator(public_key)
                
            elif algorithm in [SignatureAlgorithm.JWT_HS256, SignatureAlgorithm.JWT_RS256]:
                key = secret_key if algorithm == SignatureAlgorithm.JWT_HS256 else public_key
                if not key:
                    raise ValueError("Key required for JWT")
                self.validators[algorithm] = JWTValidator(key, algorithm)
                
            self.logger.info(f"Configured signature validation: {name} with {algorithm.value}")
            
        except Exception as e:
            self.logger.error(f"Failed to configure signature validation {name}: {str(e)}")
            raise
    
    async def validate_signature(self, 
                                config_name: str,
                                payload: bytes,
                                signature: str,
                                headers: Optional[Dict[str, str]] = None,
                                source_ip: Optional[str] = None) -> ValidationReport:
        """
        Validate webhook signature
        
        Args:
            config_name: Name of the configuration to use
            payload: Raw payload bytes
            signature: Signature to validate
            headers: Request headers
            source_ip: Source IP address
            
        Returns:
            ValidationReport with validation results
        """
        start_time = time.time()
        headers = headers or {}
        
        try:
            # Get configuration
            config = self.configurations.get(config_name)
            if not config:
                return ValidationReport(
                    result=ValidationResult.INVALID,
                    algorithm_used=SignatureAlgorithm.HMAC_SHA256,
                    validation_time=time.time() - start_time,
                    timestamp_valid=False,
                    message=f"Configuration not found: {config_name}",
                    error_details={'config_name': config_name}
                )
            
            # Create validation context
            context = ValidationContext(
                webhook_id=headers.get('x-webhook-id', 'unknown'),
                timestamp=self._parse_timestamp(headers),
                signature=signature,
                algorithm=config.algorithm,
                payload=payload,
                headers=headers,
                source_ip=source_ip or 'unknown'
            )
            
            # Perform validation
            report = await self._perform_validation(config, context)
            
            # Update statistics
            self._update_stats(report)
            
            # Cleanup old replay prevention data
            await self._cleanup_replay_data()
            
            return report
            
        except Exception as e:
            self.logger.error(f"Signature validation error: {str(e)}")
            return ValidationReport(
                result=ValidationResult.INVALID,
                algorithm_used=SignatureAlgorithm.HMAC_SHA256,
                validation_time=time.time() - start_time,
                timestamp_valid=False,
                message=f"Validation error: {str(e)}",
                error_details={'exception': str(e)}
            )
    
    async def _perform_validation(self, 
                                 config: SignatureConfig, 
                                 context: ValidationContext) -> ValidationReport:
        """Perform the actual signature validation"""
        start_time = time.time()
        warnings = []
        
        # Check payload size
        if len(context.payload) > config.max_body_size:
            return ValidationReport(
                result=ValidationResult.INVALID,
                algorithm_used=config.algorithm,
                validation_time=time.time() - start_time,
                timestamp_valid=False,
                message="Payload too large",
                error_details={'payload_size': len(context.payload), 'max_size': config.max_body_size}
            )
        
        # Validate timestamp if required
        timestamp_valid = True
        if config.require_timestamp:
            timestamp_valid = self._validate_timestamp(context.timestamp, config.tolerance_seconds)
            if not timestamp_valid:
                return ValidationReport(
                    result=ValidationResult.EXPIRED,
                    algorithm_used=config.algorithm,
                    validation_time=time.time() - start_time,
                    timestamp_valid=False,
                    message="Timestamp validation failed",
                    error_details={'timestamp': context.timestamp.isoformat() if context.timestamp else None}
                )
        
        # Check for replay attacks
        if config.prevent_replay:
            if self._is_replay_attack(context):
                return ValidationReport(
                    result=ValidationResult.REPLAY_ATTACK,
                    algorithm_used=config.algorithm,
                    validation_time=time.time() - start_time,
                    timestamp_valid=timestamp_valid,
                    message="Replay attack detected",
                    error_details={'webhook_id': context.webhook_id}
                )
        
        # Get validator
        validator = self.validators.get(config.algorithm)
        if not validator:
            return ValidationReport(
                result=ValidationResult.ALGORITHM_MISMATCH,
                algorithm_used=config.algorithm,
                validation_time=time.time() - start_time,
                timestamp_valid=timestamp_valid,
                message=f"No validator for algorithm: {config.algorithm}",
                error_details={'algorithm': config.algorithm.value}
            )
        
        # Perform signature validation
        try:
            if config.algorithm in [SignatureAlgorithm.JWT_HS256, SignatureAlgorithm.JWT_RS256]:
                is_valid, jwt_payload = await validator.validate(
                    context.payload, context.signature, config.algorithm
                )
                if jwt_payload and 'exp' in jwt_payload:
                    exp_time = datetime.fromtimestamp(jwt_payload['exp'], timezone.utc)
                    if exp_time < datetime.now(timezone.utc):
                        timestamp_valid = False
            else:
                is_valid = await validator.validate(
                    context.payload, context.signature, config.algorithm
                )
            
            if is_valid:
                # Record for replay prevention
                if config.prevent_replay:
                    self._record_signature(context)
                
                return ValidationReport(
                    result=ValidationResult.VALID,
                    algorithm_used=config.algorithm,
                    validation_time=time.time() - start_time,
                    timestamp_valid=timestamp_valid,
                    message="Signature validation successful",
                    security_warnings=warnings if warnings else None
                )
            else:
                return ValidationReport(
                    result=ValidationResult.INVALID,
                    algorithm_used=config.algorithm,
                    validation_time=time.time() - start_time,
                    timestamp_valid=timestamp_valid,
                    message="Signature validation failed"
                )
                
        except Exception as e:
            return ValidationReport(
                result=ValidationResult.MALFORMED,
                algorithm_used=config.algorithm,
                validation_time=time.time() - start_time,
                timestamp_valid=timestamp_valid,
                message=f"Signature malformed: {str(e)}",
                error_details={'exception': str(e)}
            )
    
    def _parse_timestamp(self, headers: Dict[str, str]) -> Optional[datetime]:
        """Parse timestamp from headers"""
        timestamp_header = headers.get('x-timestamp') or headers.get('x-webhook-timestamp')
        if not timestamp_header:
            return None
        
        try:
            # Try Unix timestamp first
            if timestamp_header.isdigit():
                return datetime.fromtimestamp(int(timestamp_header), timezone.utc)
            
            # Try ISO format
            return datetime.fromisoformat(timestamp_header.replace('Z', '+00:00'))
        except (ValueError, OSError):
            return None
    
    def _validate_timestamp(self, timestamp: Optional[datetime], tolerance_seconds: int) -> bool:
        """Validate timestamp within tolerance"""
        if not timestamp:
            return False
        
        now = datetime.now(timezone.utc)
        time_diff = abs((now - timestamp).total_seconds())
        return time_diff <= tolerance_seconds
    
    def _is_replay_attack(self, context: ValidationContext) -> bool:
        """Check if this is a replay attack"""
        signature_key = f"{context.webhook_id}:{context.signature}"
        return signature_key in self._processed_signatures
    
    def _record_signature(self, context: ValidationContext):
        """Record signature to prevent replay attacks"""
        signature_key = f"{context.webhook_id}:{context.signature}"
        self._processed_signatures[signature_key] = datetime.now(timezone.utc)
    
    async def _cleanup_replay_data(self):
        """Cleanup old replay prevention data"""
        current_time = time.time()
        if current_time - self._last_cleanup < self._cleanup_interval:
            return
        
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)
        keys_to_remove = [
            key for key, timestamp in self._processed_signatures.items()
            if timestamp < cutoff_time
        ]
        
        for key in keys_to_remove:
            del self._processed_signatures[key]
        
        self._last_cleanup = current_time
        
        if keys_to_remove:
            self.logger.debug(f"Cleaned up {len(keys_to_remove)} old signature records")
    
    def _update_stats(self, report: ValidationReport):
        """Update validation statistics"""
        self.stats['total_validations'] += 1
        self.stats['last_validation_at'] = datetime.now(timezone.utc).isoformat()
        
        if report.result == ValidationResult.VALID:
            self.stats['successful_validations'] += 1
        else:
            self.stats['failed_validations'] += 1
            
            if report.result == ValidationResult.REPLAY_ATTACK:
                self.stats['replay_attempts'] += 1
            elif report.result == ValidationResult.EXPIRED:
                self.stats['expired_signatures'] += 1
            elif report.result == ValidationResult.MALFORMED:
                self.stats['malformed_signatures'] += 1
        
        # Update algorithm statistics
        alg_key = report.algorithm_used.value
        if alg_key not in self.stats['algorithm_stats']:
            self.stats['algorithm_stats'][alg_key] = {
                'total': 0,
                'successful': 0,
                'failed': 0
            }
        
        self.stats['algorithm_stats'][alg_key]['total'] += 1
        if report.result == ValidationResult.VALID:
            self.stats['algorithm_stats'][alg_key]['successful'] += 1
        else:
            self.stats['algorithm_stats'][alg_key]['failed'] += 1
    
    async def validate_multiple(self, 
                               validations: List[Dict[str, Any]]) -> List[ValidationReport]:
        """Validate multiple signatures concurrently"""
        tasks = []
        for validation in validations:
            task = self.validate_signature(
                config_name=validation['config_name'],
                payload=validation['payload'],
                signature=validation['signature'],
                headers=validation.get('headers'),
                source_ip=validation.get('source_ip')
            )
            tasks.append(task)
        
        return await asyncio.gather(*tasks)
    
    def get_configurations(self) -> Dict[str, Dict[str, Any]]:
        """Get all configured signature validations"""
        return {
            name: {
                'algorithm': config.algorithm.value,
                'require_timestamp': config.require_timestamp,
                'tolerance_seconds': config.tolerance_seconds,
                'prevent_replay': config.prevent_replay,
                'max_body_size': config.max_body_size
            }
            for name, config in self.configurations.items()
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Get signature validator health status"""
        success_rate = 0.0
        if self.stats['total_validations'] > 0:
            success_rate = (
                self.stats['successful_validations'] / self.stats['total_validations'] * 100
            )
        
        status = "healthy"
        if success_rate < 80 and self.stats['total_validations'] > 10:
            status = "degraded"
        elif self.stats['replay_attempts'] > self.stats['successful_validations']:
            status = "under_attack"
        
        return {
            'status': status,
            'service': 'signature_validator',
            'configured_algorithms': len(self.configurations),
            'success_rate': round(success_rate, 2),
            'replay_prevention_entries': len(self._processed_signatures),
            'stats': self.stats.copy(),
            'supported_algorithms': [alg.value for alg in SignatureAlgorithm],
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
    
    async def cleanup(self):
        """Cleanup validator resources"""
        self.logger.info("Signature validator cleanup initiated")
        
        # Clear replay prevention data
        self._processed_signatures.clear()
        
        # Log final statistics
        self.logger.info(f"Final validation statistics: {self.stats}")
        
        self.logger.info("Signature validator cleanup completed")


# Factory function for creating signature validator
def create_signature_validator() -> SignatureValidator:
    """Create signature validator with standard configuration"""
    return SignatureValidator()


# Standard FIRS signature configurations
def get_firs_signature_configs() -> Dict[str, Dict[str, Any]]:
    """Get standard FIRS signature configurations"""
    return {
        'firs_webhook': {
            'algorithm': SignatureAlgorithm.HMAC_SHA256,
            'tolerance_seconds': 300,
            'require_timestamp': True,
            'prevent_replay': True,
            'max_body_size': 1024 * 1024
        },
        'firs_certificate': {
            'algorithm': SignatureAlgorithm.RSA_SHA256,
            'tolerance_seconds': 600,
            'require_timestamp': True,
            'prevent_replay': True,
            'max_body_size': 2 * 1024 * 1024
        },
        'firs_jwt': {
            'algorithm': SignatureAlgorithm.JWT_HS256,
            'tolerance_seconds': 300,
            'require_timestamp': False,  # JWT has exp claim
            'prevent_replay': True,
            'max_body_size': 1024 * 1024
        }
    }