"""
Encryption Service for APP Role

This service handles document encryption and decryption including:
- AES-256-GCM document encryption
- RSA key encryption and management
- Field-level encryption for sensitive data
- Key derivation and management
- Secure key storage and rotation
"""

import os
import base64
import json
import time
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging
from collections import defaultdict

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hashes, serialization, padding
from cryptography.hazmat.primitives.asymmetric import rsa, padding as asym_padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from cryptography.hazmat.backends import default_backend
from cryptography.fernet import Fernet
import argon2

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EncryptionAlgorithm(Enum):
    """Supported encryption algorithms"""
    AES_256_GCM = "aes_256_gcm"
    AES_256_CBC = "aes_256_cbc"
    AES_128_GCM = "aes_128_gcm"
    CHACHA20_POLY1305 = "chacha20_poly1305"
    FERNET = "fernet"


class KeyDerivationMethod(Enum):
    """Key derivation methods"""
    PBKDF2 = "pbkdf2"
    SCRYPT = "scrypt"
    ARGON2 = "argon2"


class EncryptionLevel(Enum):
    """Encryption security levels"""
    STANDARD = "standard"
    HIGH = "high"
    MAXIMUM = "maximum"


@dataclass
class EncryptionKey:
    """Encryption key information"""
    key_id: str
    key_data: bytes
    algorithm: EncryptionAlgorithm
    created_at: datetime
    expires_at: Optional[datetime] = None
    usage_count: int = 0
    max_usage: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EncryptionConfig:
    """Encryption configuration"""
    algorithm: EncryptionAlgorithm = EncryptionAlgorithm.AES_256_GCM
    key_derivation: KeyDerivationMethod = KeyDerivationMethod.SCRYPT
    key_size: int = 32
    iv_size: int = 12
    tag_size: int = 16
    kdf_iterations: int = 100000
    memory_cost: int = 65536
    parallelism: int = 1
    salt_size: int = 32
    enable_compression: bool = False
    enable_key_rotation: bool = True
    key_rotation_interval: int = 86400  # 24 hours


@dataclass
class EncryptedData:
    """Encrypted data container"""
    data: bytes
    iv: bytes
    tag: Optional[bytes] = None
    salt: Optional[bytes] = None
    algorithm: Optional[EncryptionAlgorithm] = None
    key_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FieldEncryptionRule:
    """Rule for field-level encryption"""
    field_path: str
    algorithm: EncryptionAlgorithm
    required: bool = True
    preserve_format: bool = False
    key_id: Optional[str] = None


@dataclass
class EncryptionOperation:
    """Encryption operation record"""
    operation_id: str
    operation_type: str  # encrypt, decrypt, key_generation, etc.
    document_id: Optional[str] = None
    key_id: Optional[str] = None
    algorithm: Optional[EncryptionAlgorithm] = None
    status: str = "pending"
    start_time: datetime = field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class EncryptionService:
    """
    Encryption service for APP role
    
    Handles:
    - AES-256-GCM document encryption
    - RSA key encryption and management
    - Field-level encryption for sensitive data
    - Key derivation and management
    - Secure key storage and rotation
    """
    
    def __init__(self, 
                 config: Optional[EncryptionConfig] = None,
                 master_key: Optional[bytes] = None):
        self.config = config or EncryptionConfig()
        self.master_key = master_key or self._generate_master_key()
        
        # Key management
        self.encryption_keys: Dict[str, EncryptionKey] = {}
        self.key_hierarchy: Dict[str, List[str]] = {}  # parent -> children
        
        # Field encryption rules
        self.field_rules: Dict[str, FieldEncryptionRule] = {}
        self._setup_default_field_rules()
        
        # Operation tracking
        self.operations: List[EncryptionOperation] = []
        
        # Key derivation functions
        self.kdf_functions = {
            KeyDerivationMethod.PBKDF2: self._derive_key_pbkdf2,
            KeyDerivationMethod.SCRYPT: self._derive_key_scrypt,
            KeyDerivationMethod.ARGON2: self._derive_key_argon2
        }
        
        # Encryption functions
        self.encryption_functions = {
            EncryptionAlgorithm.AES_256_GCM: self._encrypt_aes_gcm,
            EncryptionAlgorithm.AES_256_CBC: self._encrypt_aes_cbc,
            EncryptionAlgorithm.AES_128_GCM: self._encrypt_aes_128_gcm,
            EncryptionAlgorithm.CHACHA20_POLY1305: self._encrypt_chacha20,
            EncryptionAlgorithm.FERNET: self._encrypt_fernet
        }
        
        # Decryption functions
        self.decryption_functions = {
            EncryptionAlgorithm.AES_256_GCM: self._decrypt_aes_gcm,
            EncryptionAlgorithm.AES_256_CBC: self._decrypt_aes_cbc,
            EncryptionAlgorithm.AES_128_GCM: self._decrypt_aes_128_gcm,
            EncryptionAlgorithm.CHACHA20_POLY1305: self._decrypt_chacha20,
            EncryptionAlgorithm.FERNET: self._decrypt_fernet
        }
        
        # Metrics
        self.metrics = {
            'total_operations': 0,
            'encrypt_operations': 0,
            'decrypt_operations': 0,
            'successful_operations': 0,
            'failed_operations': 0,
            'keys_generated': 0,
            'keys_rotated': 0,
            'operations_by_algorithm': defaultdict(int),
            'average_operation_time': 0.0,
            'data_encrypted_bytes': 0,
            'data_decrypted_bytes': 0
        }
    
    def _generate_master_key(self) -> bytes:
        """Generate master encryption key"""
        return secrets.token_bytes(32)
    
    def _setup_default_field_rules(self):
        """Setup default field encryption rules"""
        sensitive_fields = [
            ('customer.personal_id', EncryptionAlgorithm.AES_256_GCM),
            ('customer.phone', EncryptionAlgorithm.AES_256_GCM),
            ('customer.email', EncryptionAlgorithm.AES_256_GCM),
            ('supplier.bank_account', EncryptionAlgorithm.AES_256_GCM),
            ('payment_details', EncryptionAlgorithm.AES_256_GCM),
            ('tax_details.tin', EncryptionAlgorithm.AES_256_GCM)
        ]
        
        for field_path, algorithm in sensitive_fields:
            self.field_rules[field_path] = FieldEncryptionRule(
                field_path=field_path,
                algorithm=algorithm,
                required=True
            )
    
    async def generate_encryption_key(self, 
                                    algorithm: EncryptionAlgorithm,
                                    key_id: Optional[str] = None,
                                    parent_key_id: Optional[str] = None,
                                    expires_in_hours: Optional[int] = None) -> EncryptionKey:
        """
        Generate new encryption key
        
        Args:
            algorithm: Encryption algorithm
            key_id: Optional key identifier
            parent_key_id: Parent key for hierarchical keys
            expires_in_hours: Key expiration time
            
        Returns:
            EncryptionKey instance
        """
        operation_id = f"keygen_{int(time.time())}_{len(self.operations)}"
        operation = EncryptionOperation(
            operation_id=operation_id,
            operation_type="key_generation",
            algorithm=algorithm
        )
        self.operations.append(operation)
        
        try:
            # Generate key ID if not provided
            if not key_id:
                key_id = f"{algorithm.value}_{int(time.time())}_{secrets.token_hex(8)}"
            
            # Determine key size based on algorithm
            if algorithm in [EncryptionAlgorithm.AES_256_GCM, EncryptionAlgorithm.AES_256_CBC]:
                key_size = 32
            elif algorithm == EncryptionAlgorithm.AES_128_GCM:
                key_size = 16
            elif algorithm == EncryptionAlgorithm.CHACHA20_POLY1305:
                key_size = 32
            else:
                key_size = self.config.key_size
            
            # Generate key data
            if parent_key_id and parent_key_id in self.encryption_keys:
                # Derive from parent key
                parent_key = self.encryption_keys[parent_key_id]
                key_data = self._derive_child_key(parent_key.key_data, key_id.encode(), key_size)
                
                # Add to hierarchy
                if parent_key_id not in self.key_hierarchy:
                    self.key_hierarchy[parent_key_id] = []
                self.key_hierarchy[parent_key_id].append(key_id)
            else:
                # Generate random key
                key_data = secrets.token_bytes(key_size)
            
            # Calculate expiration
            expires_at = None
            if expires_in_hours:
                expires_at = datetime.utcnow() + timedelta(hours=expires_in_hours)
            elif self.config.enable_key_rotation:
                expires_at = datetime.utcnow() + timedelta(seconds=self.config.key_rotation_interval)
            
            # Create encryption key
            encryption_key = EncryptionKey(
                key_id=key_id,
                key_data=key_data,
                algorithm=algorithm,
                created_at=datetime.utcnow(),
                expires_at=expires_at,
                metadata={
                    'parent_key_id': parent_key_id,
                    'key_size': key_size,
                    'generation_method': 'derived' if parent_key_id else 'random'
                }
            )
            
            # Store key
            self.encryption_keys[key_id] = encryption_key
            
            # Update metrics
            self.metrics['keys_generated'] += 1
            
            # Update operation
            operation.status = "completed"
            operation.end_time = datetime.utcnow()
            operation.key_id = key_id
            
            logger.info(f"Encryption key generated: {key_id} ({algorithm.value})")
            
            return encryption_key
            
        except Exception as e:
            operation.status = "failed"
            operation.end_time = datetime.utcnow()
            operation.error_message = str(e)
            
            logger.error(f"Failed to generate encryption key: {e}")
            raise
    
    async def encrypt_document(self, 
                             document: Union[Dict[str, Any], str, bytes],
                             document_id: str,
                             key_id: Optional[str] = None,
                             algorithm: Optional[EncryptionAlgorithm] = None) -> EncryptedData:
        """
        Encrypt document
        
        Args:
            document: Document data to encrypt
            document_id: Document identifier
            key_id: Encryption key ID
            algorithm: Encryption algorithm
            
        Returns:
            EncryptedData with encrypted document
        """
        operation_id = f"encrypt_{int(time.time())}_{len(self.operations)}"
        operation = EncryptionOperation(
            operation_id=operation_id,
            operation_type="encrypt",
            document_id=document_id,
            key_id=key_id,
            algorithm=algorithm or self.config.algorithm
        )
        self.operations.append(operation)
        
        start_time = time.time()
        
        try:
            # Use default algorithm if not specified
            algorithm = algorithm or self.config.algorithm
            
            # Get or generate encryption key
            if key_id and key_id in self.encryption_keys:
                encryption_key = self.encryption_keys[key_id]
                # Check if algorithm matches
                if encryption_key.algorithm != algorithm:
                    logger.warning(f"Algorithm mismatch for key {key_id}, generating new key")
                    encryption_key = await self.generate_encryption_key(algorithm)
                    key_id = encryption_key.key_id
            else:
                encryption_key = await self.generate_encryption_key(algorithm)
                key_id = encryption_key.key_id
            
            # Prepare data for encryption
            if isinstance(document, dict):
                data_bytes = json.dumps(document, sort_keys=True).encode('utf-8')
            elif isinstance(document, str):
                data_bytes = document.encode('utf-8')
            else:
                data_bytes = document
            
            # Compress if enabled
            if self.config.enable_compression:
                import gzip
                data_bytes = gzip.compress(data_bytes)
            
            # Encrypt data
            encryption_func = self.encryption_functions[algorithm]
            encrypted_data = await encryption_func(encryption_key.key_data, data_bytes)
            
            # Update key usage
            encryption_key.usage_count += 1
            
            # Update metrics
            operation_time = time.time() - start_time
            self.metrics['total_operations'] += 1
            self.metrics['encrypt_operations'] += 1
            self.metrics['successful_operations'] += 1
            self.metrics['operations_by_algorithm'][algorithm.value] += 1
            self.metrics['data_encrypted_bytes'] += len(data_bytes)
            self._update_average_time(operation_time)
            
            # Update operation
            operation.status = "completed"
            operation.end_time = datetime.utcnow()
            operation.key_id = key_id
            operation.metadata['data_size'] = len(data_bytes)
            operation.metadata['compressed'] = self.config.enable_compression
            
            logger.info(f"Document encrypted: {document_id} with key {key_id}")
            
            return encrypted_data
            
        except Exception as e:
            operation.status = "failed"
            operation.end_time = datetime.utcnow()
            operation.error_message = str(e)
            
            self.metrics['total_operations'] += 1
            self.metrics['failed_operations'] += 1
            
            logger.error(f"Failed to encrypt document {document_id}: {e}")
            raise
    
    async def decrypt_document(self, 
                             encrypted_data: EncryptedData,
                             document_id: str) -> Union[Dict[str, Any], str, bytes]:
        """
        Decrypt document
        
        Args:
            encrypted_data: Encrypted data to decrypt
            document_id: Document identifier
            
        Returns:
            Decrypted document data
        """
        operation_id = f"decrypt_{int(time.time())}_{len(self.operations)}"
        operation = EncryptionOperation(
            operation_id=operation_id,
            operation_type="decrypt",
            document_id=document_id,
            key_id=encrypted_data.key_id,
            algorithm=encrypted_data.algorithm
        )
        self.operations.append(operation)
        
        start_time = time.time()
        
        try:
            # Get encryption key
            if not encrypted_data.key_id or encrypted_data.key_id not in self.encryption_keys:
                raise ValueError(f"Encryption key not found: {encrypted_data.key_id}")
            
            encryption_key = self.encryption_keys[encrypted_data.key_id]
            
            # Check key expiration
            if encryption_key.expires_at and datetime.utcnow() > encryption_key.expires_at:
                logger.warning(f"Using expired key {encrypted_data.key_id} for decryption")
            
            # Decrypt data
            algorithm = encrypted_data.algorithm or encryption_key.algorithm
            decryption_func = self.decryption_functions[algorithm]
            decrypted_bytes = await decryption_func(encryption_key.key_data, encrypted_data)
            
            # Decompress if needed
            if self.config.enable_compression:
                import gzip
                try:
                    decrypted_bytes = gzip.decompress(decrypted_bytes)
                except:
                    pass  # Data might not be compressed
            
            # Try to parse as JSON
            try:
                document = json.loads(decrypted_bytes.decode('utf-8'))
            except:
                # Return as string if JSON parsing fails
                try:
                    document = decrypted_bytes.decode('utf-8')
                except:
                    # Return as bytes if string decoding fails
                    document = decrypted_bytes
            
            # Update metrics
            operation_time = time.time() - start_time
            self.metrics['total_operations'] += 1
            self.metrics['decrypt_operations'] += 1
            self.metrics['successful_operations'] += 1
            self.metrics['operations_by_algorithm'][algorithm.value] += 1
            self.metrics['data_decrypted_bytes'] += len(decrypted_bytes)
            self._update_average_time(operation_time)
            
            # Update operation
            operation.status = "completed"
            operation.end_time = datetime.utcnow()
            operation.metadata['data_size'] = len(decrypted_bytes)
            
            logger.info(f"Document decrypted: {document_id} with key {encrypted_data.key_id}")
            
            return document
            
        except Exception as e:
            operation.status = "failed"
            operation.end_time = datetime.utcnow()
            operation.error_message = str(e)
            
            self.metrics['total_operations'] += 1
            self.metrics['failed_operations'] += 1
            
            logger.error(f"Failed to decrypt document {document_id}: {e}")
            raise
    
    async def encrypt_field(self, 
                          value: Any,
                          field_path: str,
                          document_id: str) -> str:
        """
        Encrypt individual field value
        
        Args:
            value: Field value to encrypt
            field_path: Field path (e.g., 'customer.email')
            document_id: Document identifier
            
        Returns:
            Encrypted field value as base64 string
        """
        try:
            # Get field encryption rule
            rule = self.field_rules.get(field_path)
            if not rule:
                # Use default encryption for unknown fields
                rule = FieldEncryptionRule(
                    field_path=field_path,
                    algorithm=self.config.algorithm
                )
            
            # Convert value to string
            if isinstance(value, (dict, list)):
                value_str = json.dumps(value)
            else:
                value_str = str(value)
            
            # Get or generate field-specific key
            field_key_id = f"field_{hashlib.sha256(field_path.encode()).hexdigest()[:16]}"
            if field_key_id not in self.encryption_keys:
                await self.generate_encryption_key(rule.algorithm, field_key_id)
            
            encryption_key = self.encryption_keys[field_key_id]
            
            # Encrypt value
            encryption_func = self.encryption_functions[rule.algorithm]
            encrypted_data = await encryption_func(encryption_key.key_data, value_str.encode('utf-8'))
            
            # Encode as base64 string
            encrypted_container = {
                'data': base64.b64encode(encrypted_data.data).decode('utf-8'),
                'iv': base64.b64encode(encrypted_data.iv).decode('utf-8'),
                'tag': base64.b64encode(encrypted_data.tag).decode('utf-8') if encrypted_data.tag else None,
                'algorithm': rule.algorithm.value,
                'key_id': field_key_id
            }
            
            return base64.b64encode(json.dumps(encrypted_container).encode('utf-8')).decode('utf-8')
            
        except Exception as e:
            logger.error(f"Failed to encrypt field {field_path}: {e}")
            raise
    
    async def decrypt_field(self, encrypted_value: str, field_path: str) -> Any:
        """
        Decrypt individual field value
        
        Args:
            encrypted_value: Encrypted field value as base64 string
            field_path: Field path
            
        Returns:
            Decrypted field value
        """
        try:
            # Decode container
            container_data = base64.b64decode(encrypted_value.encode('utf-8'))
            container = json.loads(container_data.decode('utf-8'))
            
            # Reconstruct encrypted data
            encrypted_data = EncryptedData(
                data=base64.b64decode(container['data']),
                iv=base64.b64decode(container['iv']),
                tag=base64.b64decode(container['tag']) if container.get('tag') else None,
                algorithm=EncryptionAlgorithm(container['algorithm']),
                key_id=container['key_id']
            )
            
            # Get encryption key
            if encrypted_data.key_id not in self.encryption_keys:
                raise ValueError(f"Encryption key not found: {encrypted_data.key_id}")
            
            encryption_key = self.encryption_keys[encrypted_data.key_id]
            
            # Decrypt value
            decryption_func = self.decryption_functions[encrypted_data.algorithm]
            decrypted_bytes = await decryption_func(encryption_key.key_data, encrypted_data)
            value_str = decrypted_bytes.decode('utf-8')
            
            # Try to parse as JSON
            try:
                return json.loads(value_str)
            except:
                return value_str
                
        except Exception as e:
            logger.error(f"Failed to decrypt field {field_path}: {e}")
            raise
    
    async def _encrypt_aes_gcm(self, key: bytes, data: bytes) -> EncryptedData:
        """Encrypt using AES-256-GCM"""
        iv = os.urandom(self.config.iv_size)
        cipher = Cipher(algorithms.AES(key), modes.GCM(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        
        ciphertext = encryptor.update(data) + encryptor.finalize()
        
        return EncryptedData(
            data=ciphertext,
            iv=iv,
            tag=encryptor.tag,
            algorithm=EncryptionAlgorithm.AES_256_GCM
        )
    
    async def _decrypt_aes_gcm(self, key: bytes, encrypted_data: EncryptedData) -> bytes:
        """Decrypt using AES-256-GCM"""
        cipher = Cipher(
            algorithms.AES(key),
            modes.GCM(encrypted_data.iv, encrypted_data.tag),
            backend=default_backend()
        )
        decryptor = cipher.decryptor()
        
        return decryptor.update(encrypted_data.data) + decryptor.finalize()
    
    async def _encrypt_aes_128_gcm(self, key: bytes, data: bytes) -> EncryptedData:
        """Encrypt using AES-128-GCM"""
        iv = os.urandom(self.config.iv_size)
        cipher = Cipher(algorithms.AES(key), modes.GCM(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        
        ciphertext = encryptor.update(data) + encryptor.finalize()
        
        return EncryptedData(
            data=ciphertext,
            iv=iv,
            tag=encryptor.tag,
            algorithm=EncryptionAlgorithm.AES_128_GCM
        )
    
    async def _decrypt_aes_128_gcm(self, key: bytes, encrypted_data: EncryptedData) -> bytes:
        """Decrypt using AES-128-GCM"""
        cipher = Cipher(
            algorithms.AES(key),
            modes.GCM(encrypted_data.iv, encrypted_data.tag),
            backend=default_backend()
        )
        decryptor = cipher.decryptor()
        
        return decryptor.update(encrypted_data.data) + decryptor.finalize()
    
    async def _encrypt_aes_cbc(self, key: bytes, data: bytes) -> EncryptedData:
        """Encrypt using AES-256-CBC"""
        # Pad data to block size
        padder = padding.PKCS7(128).padder()
        padded_data = padder.update(data) + padder.finalize()
        
        iv = os.urandom(16)  # AES block size
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        
        ciphertext = encryptor.update(padded_data) + encryptor.finalize()
        
        return EncryptedData(
            data=ciphertext,
            iv=iv,
            algorithm=EncryptionAlgorithm.AES_256_CBC
        )
    
    async def _decrypt_aes_cbc(self, key: bytes, encrypted_data: EncryptedData) -> bytes:
        """Decrypt using AES-256-CBC"""
        cipher = Cipher(algorithms.AES(key), modes.CBC(encrypted_data.iv), backend=default_backend())
        decryptor = cipher.decryptor()
        
        padded_data = decryptor.update(encrypted_data.data) + decryptor.finalize()
        
        # Remove padding
        unpadder = padding.PKCS7(128).unpadder()
        data = unpadder.update(padded_data) + unpadder.finalize()
        
        return data
    
    async def _encrypt_chacha20(self, key: bytes, data: bytes) -> EncryptedData:
        """Encrypt using ChaCha20-Poly1305"""
        from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
        
        nonce = os.urandom(12)
        chacha = ChaCha20Poly1305(key)
        ciphertext = chacha.encrypt(nonce, data, None)
        
        return EncryptedData(
            data=ciphertext,
            iv=nonce,
            algorithm=EncryptionAlgorithm.CHACHA20_POLY1305
        )
    
    async def _decrypt_chacha20(self, key: bytes, encrypted_data: EncryptedData) -> bytes:
        """Decrypt using ChaCha20-Poly1305"""
        from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
        
        chacha = ChaCha20Poly1305(key)
        return chacha.decrypt(encrypted_data.iv, encrypted_data.data, None)
    
    async def _encrypt_fernet(self, key: bytes, data: bytes) -> EncryptedData:
        """Encrypt using Fernet"""
        fernet_key = base64.urlsafe_b64encode(key)
        f = Fernet(fernet_key)
        ciphertext = f.encrypt(data)
        
        return EncryptedData(
            data=ciphertext,
            iv=b'',  # Fernet handles nonce internally
            algorithm=EncryptionAlgorithm.FERNET
        )
    
    async def _decrypt_fernet(self, key: bytes, encrypted_data: EncryptedData) -> bytes:
        """Decrypt using Fernet"""
        fernet_key = base64.urlsafe_b64encode(key)
        f = Fernet(fernet_key)
        return f.decrypt(encrypted_data.data)
    
    def _derive_key_pbkdf2(self, password: bytes, salt: bytes, key_length: int) -> bytes:
        """Derive key using PBKDF2"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=key_length,
            salt=salt,
            iterations=self.config.kdf_iterations,
            backend=default_backend()
        )
        return kdf.derive(password)
    
    def _derive_key_scrypt(self, password: bytes, salt: bytes, key_length: int) -> bytes:
        """Derive key using Scrypt"""
        kdf = Scrypt(
            algorithm=hashes.SHA256(),
            length=key_length,
            salt=salt,
            n=2**14,  # CPU/memory cost
            r=8,      # Block size
            p=1,      # Parallelization
            backend=default_backend()
        )
        return kdf.derive(password)
    
    def _derive_key_argon2(self, password: bytes, salt: bytes, key_length: int) -> bytes:
        """Derive key using Argon2"""
        hasher = argon2.PasswordHasher(
            memory_cost=self.config.memory_cost,
            time_cost=self.config.kdf_iterations,
            parallelism=self.config.parallelism,
            hash_len=key_length,
            salt_len=len(salt)
        )
        hash_result = hasher.hash(password, salt=salt)
        # Extract raw hash from Argon2 output
        return base64.b64decode(hash_result.split('$')[-1])
    
    def _derive_child_key(self, parent_key: bytes, info: bytes, key_length: int) -> bytes:
        """Derive child key from parent using HKDF"""
        from cryptography.hazmat.primitives.kdf.hkdf import HKDF
        
        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=key_length,
            salt=None,
            info=info,
            backend=default_backend()
        )
        return hkdf.derive(parent_key)
    
    def _update_average_time(self, operation_time: float):
        """Update average operation time"""
        total_ops = self.metrics['total_operations']
        current_avg = self.metrics['average_operation_time']
        self.metrics['average_operation_time'] = (
            (current_avg * (total_ops - 1) + operation_time) / total_ops
        )
    
    async def rotate_key(self, key_id: str) -> EncryptionKey:
        """Rotate encryption key"""
        if key_id not in self.encryption_keys:
            raise ValueError(f"Key not found: {key_id}")
        
        old_key = self.encryption_keys[key_id]
        
        # Generate new key with same algorithm
        new_key = await self.generate_encryption_key(
            old_key.algorithm,
            f"{key_id}_rotated_{int(time.time())}"
        )
        
        # Mark old key as expired
        old_key.expires_at = datetime.utcnow()
        
        self.metrics['keys_rotated'] += 1
        
        logger.info(f"Key rotated: {key_id} -> {new_key.key_id}")
        
        return new_key
    
    async def cleanup_expired_keys(self):
        """Clean up expired keys"""
        current_time = datetime.utcnow()
        expired_keys = []
        
        for key_id, key in self.encryption_keys.items():
            if key.expires_at and key.expires_at <= current_time:
                expired_keys.append(key_id)
        
        for key_id in expired_keys:
            del self.encryption_keys[key_id]
            # Remove from hierarchy
            for parent_id, children in self.key_hierarchy.items():
                if key_id in children:
                    children.remove(key_id)
        
        if expired_keys:
            logger.info(f"Cleaned up {len(expired_keys)} expired keys")
    
    def get_key_info(self, key_id: str) -> Optional[Dict[str, Any]]:
        """Get key information"""
        if key_id not in self.encryption_keys:
            return None
        
        key = self.encryption_keys[key_id]
        return {
            'key_id': key.key_id,
            'algorithm': key.algorithm.value,
            'created_at': key.created_at.isoformat(),
            'expires_at': key.expires_at.isoformat() if key.expires_at else None,
            'usage_count': key.usage_count,
            'max_usage': key.max_usage,
            'is_expired': key.expires_at and datetime.utcnow() > key.expires_at,
            'metadata': key.metadata
        }
    
    def list_keys(self) -> List[Dict[str, Any]]:
        """List all encryption keys"""
        return [self.get_key_info(key_id) for key_id in self.encryption_keys.keys()]
    
    def get_operations(self, limit: int = 100) -> List[EncryptionOperation]:
        """Get recent operations"""
        return self.operations[-limit:]
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get encryption service metrics"""
        return {
            **self.metrics,
            'active_keys': len(self.encryption_keys),
            'key_hierarchy_depth': max(len(children) for children in self.key_hierarchy.values()) if self.key_hierarchy else 0,
            'field_encryption_rules': len(self.field_rules),
            'success_rate': (
                self.metrics['successful_operations'] / 
                max(self.metrics['total_operations'], 1)
            ) * 100 if self.metrics['total_operations'] > 0 else 0
        }


# Factory functions for easy setup
def create_encryption_service(config: Optional[EncryptionConfig] = None,
                            master_key: Optional[bytes] = None) -> EncryptionService:
    """Create encryption service instance"""
    return EncryptionService(config, master_key)


def create_encryption_config(algorithm: EncryptionAlgorithm = EncryptionAlgorithm.AES_256_GCM,
                           key_derivation: KeyDerivationMethod = KeyDerivationMethod.SCRYPT,
                           **kwargs) -> EncryptionConfig:
    """Create encryption configuration"""
    return EncryptionConfig(
        algorithm=algorithm,
        key_derivation=key_derivation,
        **kwargs
    )


async def encrypt_document_data(document: Union[Dict[str, Any], str, bytes],
                              document_id: str,
                              algorithm: EncryptionAlgorithm = EncryptionAlgorithm.AES_256_GCM) -> EncryptedData:
    """Encrypt document data"""
    service = create_encryption_service()
    return await service.encrypt_document(document, document_id, algorithm=algorithm)


async def decrypt_document_data(encrypted_data: EncryptedData,
                              document_id: str) -> Union[Dict[str, Any], str, bytes]:
    """Decrypt document data"""
    service = create_encryption_service()
    return await service.decrypt_document(encrypted_data, document_id)


def get_encryption_summary(service: EncryptionService) -> Dict[str, Any]:
    """Get encryption service summary"""
    metrics = service.get_metrics()
    
    return {
        'total_operations': metrics['total_operations'],
        'active_keys': metrics['active_keys'],
        'success_rate': metrics['success_rate'],
        'data_encrypted_mb': metrics['data_encrypted_bytes'] / (1024 * 1024),
        'data_decrypted_mb': metrics['data_decrypted_bytes'] / (1024 * 1024),
        'average_operation_time': metrics['average_operation_time'],
        'keys_generated': metrics['keys_generated'],
        'keys_rotated': metrics['keys_rotated']
    }