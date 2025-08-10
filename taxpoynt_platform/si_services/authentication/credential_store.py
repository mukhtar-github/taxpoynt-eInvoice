"""
Secure Credential Storage Service

This module provides secure storage and management of authentication credentials
for SI services, including encryption, key derivation, secure deletion, and
credential rotation capabilities.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import secrets
import hashlib
import hmac
import base64
from pathlib import Path
import aiofiles
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt

logger = logging.getLogger(__name__)


class CredentialType(Enum):
    """Types of credentials"""
    PASSWORD = "password"
    API_KEY = "api_key"
    OAUTH_TOKEN = "oauth_token"
    CERTIFICATE = "certificate"
    PRIVATE_KEY = "private_key"
    JWT_SECRET = "jwt_secret"
    ENCRYPTION_KEY = "encryption_key"
    DATABASE_CREDENTIAL = "database_credential"
    CUSTOM = "custom"


class EncryptionAlgorithm(Enum):
    """Encryption algorithms"""
    FERNET = "fernet"
    AES_256_GCM = "aes_256_gcm"
    CHACHA20_POLY1305 = "chacha20_poly1305"


class CredentialStatus(Enum):
    """Credential status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    EXPIRED = "expired"
    ROTATED = "rotated"
    COMPROMISED = "compromised"


@dataclass
class CredentialMetadata:
    """Metadata for stored credentials"""
    credential_id: str
    credential_type: CredentialType
    service_identifier: str
    description: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    last_accessed: Optional[datetime] = None
    access_count: int = 0
    status: CredentialStatus = CredentialStatus.ACTIVE
    tags: List[str] = field(default_factory=list)
    rotation_policy: Optional[str] = None
    backup_count: int = 0


@dataclass
class StoredCredential:
    """Encrypted stored credential"""
    metadata: CredentialMetadata
    encrypted_data: str
    encryption_algorithm: EncryptionAlgorithm
    salt: str
    iv: Optional[str] = None
    checksum: Optional[str] = None


@dataclass
class CredentialStoreConfig:
    """Configuration for credential store"""
    storage_path: str
    master_key: Optional[str] = None
    encryption_algorithm: EncryptionAlgorithm = EncryptionAlgorithm.FERNET
    key_derivation_iterations: int = 100000
    enable_backup: bool = True
    backup_retention_days: int = 30
    auto_rotation_enabled: bool = False
    rotation_interval_days: int = 90
    access_log_enabled: bool = True
    max_access_attempts: int = 3
    lockout_duration_minutes: int = 15


class SecureCredentialStore:
    """
    Secure credential storage service with encryption, key derivation,
    and secure credential management for SI authentication services.
    """
    
    def __init__(self, config: CredentialStoreConfig):
        self.config = config
        self.credentials: Dict[str, StoredCredential] = {}
        self.access_attempts: Dict[str, List[datetime]] = {}
        self.master_key: Optional[bytes] = None
        self.cipher_suite: Optional[Fernet] = None
        
        # Setup storage path
        self.storage_path = Path(config.storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Backup path
        if config.enable_backup:
            self.backup_path = self.storage_path / "backups"
            self.backup_path.mkdir(exist_ok=True)
        else:
            self.backup_path = None
        
        # Access log
        self.access_log_path = self.storage_path / "access.log" if config.access_log_enabled else None
    
    async def initialize(self) -> None:
        """Initialize credential store"""
        try:
            # Setup master key
            await self._setup_master_key()
            
            # Load existing credentials
            await self._load_stored_credentials()
            
            # Setup rotation task if enabled
            if self.config.auto_rotation_enabled:
                asyncio.create_task(self._rotation_loop())
            
            logger.info("Secure credential store initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize credential store: {e}")
            raise
    
    async def store_credential(
        self,
        credential_id: str,
        credential_type: CredentialType,
        service_identifier: str,
        credential_data: Union[str, Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Store a credential securely"""
        try:
            # Check if credential already exists
            if credential_id in self.credentials:
                logger.warning(f"Credential {credential_id} already exists, updating")
            
            # Prepare credential data for encryption
            if isinstance(credential_data, dict):
                data_to_encrypt = json.dumps(credential_data)
            else:
                data_to_encrypt = str(credential_data)
            
            # Encrypt credential data
            encrypted_data, salt, iv = await self._encrypt_data(data_to_encrypt)
            
            # Create metadata
            cred_metadata = CredentialMetadata(
                credential_id=credential_id,
                credential_type=credential_type,
                service_identifier=service_identifier,
                description=metadata.get("description") if metadata else None,
                expires_at=metadata.get("expires_at") if metadata else None,
                tags=metadata.get("tags", []) if metadata else [],
                rotation_policy=metadata.get("rotation_policy") if metadata else None
            )
            
            # Create checksum for integrity verification
            checksum = hashlib.sha256(data_to_encrypt.encode()).hexdigest()
            
            # Create stored credential
            stored_credential = StoredCredential(
                metadata=cred_metadata,
                encrypted_data=encrypted_data,
                encryption_algorithm=self.config.encryption_algorithm,
                salt=salt,
                iv=iv,
                checksum=checksum
            )
            
            # Store in memory
            self.credentials[credential_id] = stored_credential
            
            # Persist to disk
            await self._persist_credential(stored_credential)
            
            # Create backup if enabled
            if self.config.enable_backup:
                await self._backup_credential(stored_credential)
            
            # Log access
            await self._log_access("store", credential_id, True)
            
            logger.info(f"Stored credential: {credential_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store credential {credential_id}: {e}")
            await self._log_access("store", credential_id, False, str(e))
            return False
    
    async def retrieve_credential(
        self,
        credential_id: str,
        decrypt: bool = True
    ) -> Optional[Union[str, Dict[str, Any]]]:
        """Retrieve and optionally decrypt a credential"""
        try:
            # Check access attempts
            if not await self._check_access_attempts(credential_id):
                return None
            
            # Find credential
            stored_credential = self.credentials.get(credential_id)
            if not stored_credential:
                await self._log_access("retrieve", credential_id, False, "Not found")
                return None
            
            # Check status
            if stored_credential.metadata.status != CredentialStatus.ACTIVE:
                await self._log_access("retrieve", credential_id, False, f"Status: {stored_credential.metadata.status}")
                return None
            
            # Check expiration
            if (stored_credential.metadata.expires_at and 
                datetime.now() > stored_credential.metadata.expires_at):
                stored_credential.metadata.status = CredentialStatus.EXPIRED
                await self._log_access("retrieve", credential_id, False, "Expired")
                return None
            
            # Update access metadata
            stored_credential.metadata.last_accessed = datetime.now()
            stored_credential.metadata.access_count += 1
            
            if not decrypt:
                await self._log_access("retrieve", credential_id, True, "Metadata only")
                return stored_credential.metadata.__dict__
            
            # Decrypt credential data
            decrypted_data = await self._decrypt_data(
                stored_credential.encrypted_data,
                stored_credential.salt,
                stored_credential.iv
            )
            
            if decrypted_data is None:
                await self._log_access("retrieve", credential_id, False, "Decryption failed")
                return None
            
            # Verify integrity
            if stored_credential.checksum:
                expected_checksum = hashlib.sha256(decrypted_data.encode()).hexdigest()
                if expected_checksum != stored_credential.checksum:
                    logger.error(f"Integrity check failed for credential {credential_id}")
                    await self._log_access("retrieve", credential_id, False, "Integrity check failed")
                    return None
            
            # Try to parse as JSON, fallback to string
            try:
                credential_data = json.loads(decrypted_data)
            except json.JSONDecodeError:
                credential_data = decrypted_data
            
            await self._log_access("retrieve", credential_id, True)
            return credential_data
            
        except Exception as e:
            logger.error(f"Failed to retrieve credential {credential_id}: {e}")
            await self._log_access("retrieve", credential_id, False, str(e))
            await self._record_access_attempt(credential_id)
            return None
    
    async def update_credential(
        self,
        credential_id: str,
        credential_data: Union[str, Dict[str, Any]],
        metadata_updates: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Update an existing credential"""
        try:
            stored_credential = self.credentials.get(credential_id)
            if not stored_credential:
                return False
            
            # Create backup before update
            if self.config.enable_backup:
                await self._backup_credential(stored_credential)
            
            # Prepare new credential data
            if isinstance(credential_data, dict):
                data_to_encrypt = json.dumps(credential_data)
            else:
                data_to_encrypt = str(credential_data)
            
            # Encrypt new data
            encrypted_data, salt, iv = await self._encrypt_data(data_to_encrypt)
            
            # Update stored credential
            stored_credential.encrypted_data = encrypted_data
            stored_credential.salt = salt
            stored_credential.iv = iv
            stored_credential.checksum = hashlib.sha256(data_to_encrypt.encode()).hexdigest()
            stored_credential.metadata.updated_at = datetime.now()
            
            # Update metadata if provided
            if metadata_updates:
                for key, value in metadata_updates.items():
                    if hasattr(stored_credential.metadata, key):
                        setattr(stored_credential.metadata, key, value)
            
            # Persist updated credential
            await self._persist_credential(stored_credential)
            
            await self._log_access("update", credential_id, True)
            logger.info(f"Updated credential: {credential_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update credential {credential_id}: {e}")
            await self._log_access("update", credential_id, False, str(e))
            return False
    
    async def delete_credential(
        self,
        credential_id: str,
        secure_delete: bool = True
    ) -> bool:
        """Delete a credential"""
        try:
            stored_credential = self.credentials.get(credential_id)
            if not stored_credential:
                return False
            
            # Create final backup if enabled
            if self.config.enable_backup:
                await self._backup_credential(stored_credential)
            
            # Remove from memory
            del self.credentials[credential_id]
            
            # Remove from disk
            credential_file = self.storage_path / f"{credential_id}.json"
            if credential_file.exists():
                if secure_delete:
                    await self._secure_delete_file(credential_file)
                else:
                    credential_file.unlink()
            
            await self._log_access("delete", credential_id, True)
            logger.info(f"Deleted credential: {credential_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete credential {credential_id}: {e}")
            await self._log_access("delete", credential_id, False, str(e))
            return False
    
    async def list_credentials(
        self,
        service_identifier: Optional[str] = None,
        credential_type: Optional[CredentialType] = None,
        status: Optional[CredentialStatus] = None,
        include_metadata_only: bool = True
    ) -> List[Dict[str, Any]]:
        """List stored credentials with optional filters"""
        try:
            results = []
            
            for credential_id, stored_credential in self.credentials.items():
                metadata = stored_credential.metadata
                
                # Apply filters
                if service_identifier and metadata.service_identifier != service_identifier:
                    continue
                if credential_type and metadata.credential_type != credential_type:
                    continue
                if status and metadata.status != status:
                    continue
                
                # Prepare result
                result = {
                    "credential_id": credential_id,
                    "credential_type": metadata.credential_type.value,
                    "service_identifier": metadata.service_identifier,
                    "description": metadata.description,
                    "created_at": metadata.created_at.isoformat(),
                    "updated_at": metadata.updated_at.isoformat(),
                    "expires_at": metadata.expires_at.isoformat() if metadata.expires_at else None,
                    "last_accessed": metadata.last_accessed.isoformat() if metadata.last_accessed else None,
                    "access_count": metadata.access_count,
                    "status": metadata.status.value,
                    "tags": metadata.tags
                }
                
                if not include_metadata_only:
                    # Include encrypted data info (but not the actual data)
                    result.update({
                        "encryption_algorithm": stored_credential.encryption_algorithm.value,
                        "has_checksum": stored_credential.checksum is not None
                    })
                
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to list credentials: {e}")
            return []
    
    async def rotate_credential(
        self,
        credential_id: str,
        new_credential_data: Union[str, Dict[str, Any]]
    ) -> bool:
        """Rotate a credential while maintaining history"""
        try:
            stored_credential = self.credentials.get(credential_id)
            if not stored_credential:
                return False
            
            # Mark current credential as rotated
            stored_credential.metadata.status = CredentialStatus.ROTATED
            
            # Create backup of current credential
            if self.config.enable_backup:
                await self._backup_credential(stored_credential)
                stored_credential.metadata.backup_count += 1
            
            # Update with new credential data
            success = await self.update_credential(credential_id, new_credential_data, {
                "status": CredentialStatus.ACTIVE,
                "updated_at": datetime.now()
            })
            
            if success:
                await self._log_access("rotate", credential_id, True)
                logger.info(f"Rotated credential: {credential_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to rotate credential {credential_id}: {e}")
            await self._log_access("rotate", credential_id, False, str(e))
            return False
    
    async def _encrypt_data(self, data: str) -> Tuple[str, str, Optional[str]]:
        """Encrypt data using configured algorithm"""
        try:
            if self.config.encryption_algorithm == EncryptionAlgorithm.FERNET:
                if not self.cipher_suite:
                    raise ValueError("Cipher suite not initialized")
                
                encrypted_data = self.cipher_suite.encrypt(data.encode())
                encoded_data = base64.b64encode(encrypted_data).decode()
                
                # For Fernet, salt is embedded, no separate IV
                return encoded_data, "", None
            
            else:
                raise NotImplementedError(f"Encryption algorithm {self.config.encryption_algorithm} not implemented")
                
        except Exception as e:
            logger.error(f"Data encryption failed: {e}")
            raise
    
    async def _decrypt_data(
        self,
        encrypted_data: str,
        salt: str,
        iv: Optional[str]
    ) -> Optional[str]:
        """Decrypt data using configured algorithm"""
        try:
            if self.config.encryption_algorithm == EncryptionAlgorithm.FERNET:
                if not self.cipher_suite:
                    return None
                
                encrypted_bytes = base64.b64decode(encrypted_data.encode())
                decrypted_data = self.cipher_suite.decrypt(encrypted_bytes)
                return decrypted_data.decode()
            
            else:
                logger.error(f"Decryption algorithm {self.config.encryption_algorithm} not implemented")
                return None
                
        except Exception as e:
            logger.error(f"Data decryption failed: {e}")
            return None
    
    async def _setup_master_key(self) -> None:
        """Setup master encryption key"""
        try:
            if self.config.master_key:
                # Use provided master key
                master_key_bytes = self.config.master_key.encode()
            else:
                # Generate master key
                master_key_bytes = secrets.token_bytes(32)
                logger.warning("Using generated master key - configure for production")
            
            # Derive encryption key using PBKDF2
            salt = secrets.token_bytes(16)
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=self.config.key_derivation_iterations,
            )
            
            self.master_key = kdf.derive(master_key_bytes)
            
            # Setup cipher suite
            if self.config.encryption_algorithm == EncryptionAlgorithm.FERNET:
                # Fernet requires a URL-safe base64 encoded key
                fernet_key = base64.urlsafe_b64encode(self.master_key)
                self.cipher_suite = Fernet(fernet_key)
            
            logger.info("Master encryption key initialized")
            
        except Exception as e:
            logger.error(f"Master key setup failed: {e}")
            raise
    
    async def _persist_credential(self, stored_credential: StoredCredential) -> None:
        """Persist credential to disk"""
        try:
            credential_file = self.storage_path / f"{stored_credential.metadata.credential_id}.json"
            
            # Prepare data for storage (exclude the actual credential data)
            storage_data = {
                "metadata": {
                    "credential_id": stored_credential.metadata.credential_id,
                    "credential_type": stored_credential.metadata.credential_type.value,
                    "service_identifier": stored_credential.metadata.service_identifier,
                    "description": stored_credential.metadata.description,
                    "created_at": stored_credential.metadata.created_at.isoformat(),
                    "updated_at": stored_credential.metadata.updated_at.isoformat(),
                    "expires_at": stored_credential.metadata.expires_at.isoformat() if stored_credential.metadata.expires_at else None,
                    "last_accessed": stored_credential.metadata.last_accessed.isoformat() if stored_credential.metadata.last_accessed else None,
                    "access_count": stored_credential.metadata.access_count,
                    "status": stored_credential.metadata.status.value,
                    "tags": stored_credential.metadata.tags,
                    "rotation_policy": stored_credential.metadata.rotation_policy,
                    "backup_count": stored_credential.metadata.backup_count
                },
                "encrypted_data": stored_credential.encrypted_data,
                "encryption_algorithm": stored_credential.encryption_algorithm.value,
                "salt": stored_credential.salt,
                "iv": stored_credential.iv,
                "checksum": stored_credential.checksum
            }
            
            async with aiofiles.open(credential_file, 'w') as f:
                await f.write(json.dumps(storage_data, indent=2))
                
        except Exception as e:
            logger.error(f"Failed to persist credential: {e}")
            raise
    
    async def _load_stored_credentials(self) -> None:
        """Load credentials from disk"""
        try:
            credential_files = list(self.storage_path.glob("*.json"))
            loaded_count = 0
            
            for credential_file in credential_files:
                try:
                    if credential_file.name in ["access.log", "token_state.json"]:
                        continue
                    
                    async with aiofiles.open(credential_file, 'r') as f:
                        storage_data = json.loads(await f.read())
                    
                    # Reconstruct credential metadata
                    metadata_data = storage_data["metadata"]
                    metadata = CredentialMetadata(
                        credential_id=metadata_data["credential_id"],
                        credential_type=CredentialType(metadata_data["credential_type"]),
                        service_identifier=metadata_data["service_identifier"],
                        description=metadata_data.get("description"),
                        created_at=datetime.fromisoformat(metadata_data["created_at"]),
                        updated_at=datetime.fromisoformat(metadata_data["updated_at"]),
                        expires_at=datetime.fromisoformat(metadata_data["expires_at"]) if metadata_data.get("expires_at") else None,
                        last_accessed=datetime.fromisoformat(metadata_data["last_accessed"]) if metadata_data.get("last_accessed") else None,
                        access_count=metadata_data.get("access_count", 0),
                        status=CredentialStatus(metadata_data.get("status", "active")),
                        tags=metadata_data.get("tags", []),
                        rotation_policy=metadata_data.get("rotation_policy"),
                        backup_count=metadata_data.get("backup_count", 0)
                    )
                    
                    # Reconstruct stored credential
                    stored_credential = StoredCredential(
                        metadata=metadata,
                        encrypted_data=storage_data["encrypted_data"],
                        encryption_algorithm=EncryptionAlgorithm(storage_data["encryption_algorithm"]),
                        salt=storage_data["salt"],
                        iv=storage_data.get("iv"),
                        checksum=storage_data.get("checksum")
                    )
                    
                    self.credentials[metadata.credential_id] = stored_credential
                    loaded_count += 1
                    
                except Exception as e:
                    logger.warning(f"Failed to load credential from {credential_file}: {e}")
            
            logger.info(f"Loaded {loaded_count} credentials from storage")
            
        except Exception as e:
            logger.error(f"Failed to load stored credentials: {e}")
    
    async def _backup_credential(self, stored_credential: StoredCredential) -> None:
        """Create backup of credential"""
        if not self.backup_path:
            return
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = self.backup_path / f"{stored_credential.metadata.credential_id}_{timestamp}.json"
            
            backup_data = {
                "credential_id": stored_credential.metadata.credential_id,
                "backup_timestamp": datetime.now().isoformat(),
                "metadata": stored_credential.metadata.__dict__,
                "encrypted_data": stored_credential.encrypted_data,
                "encryption_algorithm": stored_credential.encryption_algorithm.value,
                "salt": stored_credential.salt,
                "checksum": stored_credential.checksum
            }
            
            async with aiofiles.open(backup_file, 'w') as f:
                await f.write(json.dumps(backup_data, indent=2, default=str))
                
        except Exception as e:
            logger.error(f"Failed to backup credential: {e}")
    
    async def _secure_delete_file(self, file_path: Path) -> None:
        """Securely delete a file by overwriting"""
        try:
            if not file_path.exists():
                return
            
            file_size = file_path.stat().st_size
            
            # Overwrite with random data multiple times
            for _ in range(3):
                async with aiofiles.open(file_path, 'r+b') as f:
                    await f.write(secrets.token_bytes(file_size))
                    await f.flush()
            
            # Finally delete the file
            file_path.unlink()
            
        except Exception as e:
            logger.error(f"Secure file deletion failed: {e}")
    
    async def _check_access_attempts(self, credential_id: str) -> bool:
        """Check if access attempts are within limits"""
        try:
            current_time = datetime.now()
            
            if credential_id not in self.access_attempts:
                return True
            
            # Remove old attempts outside lockout window
            lockout_start = current_time - timedelta(minutes=self.config.lockout_duration_minutes)
            self.access_attempts[credential_id] = [
                attempt for attempt in self.access_attempts[credential_id]
                if attempt > lockout_start
            ]
            
            # Check if within limit
            return len(self.access_attempts[credential_id]) < self.config.max_access_attempts
            
        except Exception:
            return True  # Allow on error
    
    async def _record_access_attempt(self, credential_id: str) -> None:
        """Record failed access attempt"""
        try:
            if credential_id not in self.access_attempts:
                self.access_attempts[credential_id] = []
            
            self.access_attempts[credential_id].append(datetime.now())
            
        except Exception as e:
            logger.error(f"Failed to record access attempt: {e}")
    
    async def _log_access(
        self,
        operation: str,
        credential_id: str,
        success: bool,
        details: Optional[str] = None
    ) -> None:
        """Log access to credentials"""
        if not self.access_log_path:
            return
        
        try:
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "operation": operation,
                "credential_id": credential_id,
                "success": success,
                "details": details
            }
            
            async with aiofiles.open(self.access_log_path, 'a') as f:
                await f.write(json.dumps(log_entry) + "\n")
                
        except Exception as e:
            logger.error(f"Access logging failed: {e}")
    
    async def _rotation_loop(self) -> None:
        """Background credential rotation loop"""
        while True:
            try:
                await self._check_rotation_policies()
                await asyncio.sleep(24 * 3600)  # Check daily
            except Exception as e:
                logger.error(f"Rotation loop error: {e}")
                await asyncio.sleep(3600)  # Retry in an hour
    
    async def _check_rotation_policies(self) -> None:
        """Check and apply credential rotation policies"""
        try:
            current_time = datetime.now()
            
            for credential_id, stored_credential in self.credentials.items():
                metadata = stored_credential.metadata
                
                if (metadata.status == CredentialStatus.ACTIVE and
                    metadata.rotation_policy):
                    
                    # Simple time-based rotation policy
                    if metadata.rotation_policy == "auto":
                        rotation_interval = timedelta(days=self.config.rotation_interval_days)
                        if current_time - metadata.updated_at > rotation_interval:
                            logger.info(f"Credential {credential_id} due for rotation")
                            # In practice, this would trigger external rotation process
                            
        except Exception as e:
            logger.error(f"Rotation policy check failed: {e}")
    
    def get_store_stats(self) -> Dict[str, Any]:
        """Get credential store statistics"""
        try:
            stats = {
                "total_credentials": len(self.credentials),
                "active_credentials": len([c for c in self.credentials.values() if c.metadata.status == CredentialStatus.ACTIVE]),
                "expired_credentials": len([c for c in self.credentials.values() if c.metadata.status == CredentialStatus.EXPIRED]),
                "credential_types": {},
                "service_identifiers": set(),
                "config": {
                    "encryption_algorithm": self.config.encryption_algorithm.value,
                    "backup_enabled": self.config.enable_backup,
                    "auto_rotation_enabled": self.config.auto_rotation_enabled,
                    "access_log_enabled": self.config.access_log_enabled
                }
            }
            
            # Count by type and collect service identifiers
            for stored_credential in self.credentials.values():
                cred_type = stored_credential.metadata.credential_type.value
                stats["credential_types"][cred_type] = stats["credential_types"].get(cred_type, 0) + 1
                stats["service_identifiers"].add(stored_credential.metadata.service_identifier)
            
            stats["service_identifiers"] = list(stats["service_identifiers"])
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get store stats: {e}")
            return {}


# Factory function for creating credential store
def create_credential_store(config: CredentialStoreConfig) -> SecureCredentialStore:
    """Factory function to create secure credential store"""
    return SecureCredentialStore(config)