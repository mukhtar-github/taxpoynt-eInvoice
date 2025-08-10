"""
Secrets Coordinator Service

This service coordinates secure secret management across the TaxPoynt platform,
providing centralized secret storage, rotation, and access control.
"""

import asyncio
import json
import hashlib
import os
import base64
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Set, Callable
from dataclasses import dataclass, field
from enum import Enum
import logging
from pathlib import Path
import secrets as py_secrets

from taxpoynt_platform.core_platform.shared.base_service import BaseService
from taxpoynt_platform.core_platform.shared.exceptions import (
    ConfigurationError,
    ValidationError,
    SecurityError
)


class SecretType(Enum):
    """Secret type definitions"""
    API_KEY = "api_key"
    DATABASE_PASSWORD = "database_password"
    JWT_SECRET = "jwt_secret"
    ENCRYPTION_KEY = "encryption_key"
    CERTIFICATE = "certificate"
    PRIVATE_KEY = "private_key"
    OAUTH_TOKEN = "oauth_token"
    WEBHOOK_SECRET = "webhook_secret"
    FIRS_CREDENTIALS = "firs_credentials"


class SecretStatus(Enum):
    """Secret status definitions"""
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    PENDING_ROTATION = "pending_rotation"
    ROTATING = "rotating"


class AccessLevel(Enum):
    """Access level definitions"""
    READ_ONLY = "read_only"
    READ_WRITE = "read_write"
    ADMIN = "admin"
    SYSTEM = "system"


class RotationStrategy(Enum):
    """Secret rotation strategies"""
    MANUAL = "manual"
    SCHEDULED = "scheduled"
    ON_DEMAND = "on_demand"
    AUTO_ROTATE = "auto_rotate"


@dataclass
class Secret:
    """Secret definition"""
    secret_id: str
    name: str
    secret_type: SecretType
    encrypted_value: str
    status: SecretStatus = SecretStatus.ACTIVE
    description: Optional[str] = None
    tags: Set[str] = field(default_factory=set)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    created_by: str = "system"
    updated_by: str = "system"
    version: int = 1
    expires_at: Optional[datetime] = None
    rotation_strategy: RotationStrategy = RotationStrategy.MANUAL
    rotation_interval: Optional[timedelta] = None
    last_rotated: Optional[datetime] = None
    next_rotation: Optional[datetime] = None
    environment: Optional[str] = None
    tenant_id: Optional[str] = None
    service: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    access_count: int = 0
    last_accessed: Optional[datetime] = None


@dataclass
class SecretAccess:
    """Secret access control"""
    secret_id: str
    principal_type: str  # user, service, role
    principal_id: str
    access_level: AccessLevel
    granted_by: str
    granted_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    conditions: Dict[str, Any] = field(default_factory=dict)
    active: bool = True


@dataclass
class SecretRotation:
    """Secret rotation tracking"""
    rotation_id: str
    secret_id: str
    old_version: int
    new_version: int
    rotation_type: str  # scheduled, manual, emergency
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    status: str = "in_progress"  # in_progress, completed, failed
    error_message: Optional[str] = None
    initiated_by: str = "system"
    rollback_available: bool = True


@dataclass
class SecretAuditEntry:
    """Secret audit log entry"""
    entry_id: str
    secret_id: str
    action: str
    principal_id: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    details: Dict[str, Any] = field(default_factory=dict)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    success: bool = True
    error_message: Optional[str] = None


class SecretsCoordinator(BaseService):
    """
    Secrets Coordinator Service
    
    Coordinates secure secret management across the TaxPoynt platform,
    providing centralized secret storage, rotation, and access control.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.logger = logging.getLogger(__name__)
        
        # Secret storage
        self.secrets: Dict[str, Secret] = {}
        self.secret_versions: Dict[str, Dict[int, str]] = {}  # secret_id -> version -> encrypted_value
        
        # Access control
        self.access_controls: Dict[str, List[SecretAccess]] = {}  # secret_id -> access_list
        self.access_cache: Dict[str, bool] = {}  # cache access decisions
        self.cache_ttl: timedelta = timedelta(minutes=5)
        self.cache_timestamps: Dict[str, datetime] = {}
        
        # Rotation management
        self.rotation_schedules: Dict[str, asyncio.Task] = {}
        self.rotation_history: Dict[str, List[SecretRotation]] = {}
        self.rotation_queue: asyncio.Queue = asyncio.Queue()
        
        # Audit logging
        self.audit_log: List[SecretAuditEntry] = []
        
        # Encryption
        self.master_key: Optional[str] = None
        self.key_derivation_salt: Optional[bytes] = None
        
        # Secret generators
        self.generators: Dict[SecretType, Callable] = {}
        
        # Validation
        self.validators: Dict[SecretType, Callable] = {}
        
        # Monitoring
        self.access_monitors: List[Callable] = []
        self.rotation_monitors: List[Callable] = []
        
        # Performance metrics
        self.metrics = {
            'secrets_managed': 0,
            'access_grants': 0,
            'access_denials': 0,
            'rotations_performed': 0,
            'encryption_operations': 0,
            'decryption_operations': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'audit_entries': 0
        }
        
        # Background tasks
        self.background_tasks: Dict[str, asyncio.Task] = {}
    
    async def initialize(self) -> None:
        """Initialize secrets coordinator"""
        try:
            self.logger.info("Initializing SecretsCoordinator")
            
            # Initialize encryption
            await self._initialize_encryption()
            
            # Load secret generators
            await self._initialize_secret_generators()
            
            # Load validators
            await self._initialize_validators()
            
            # Start background workers
            await self._start_background_workers()
            
            # Load default secrets if needed
            await self._load_default_secrets()
            
            self.logger.info("SecretsCoordinator initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize SecretsCoordinator: {str(e)}")
            raise ConfigurationError(f"Initialization failed: {str(e)}")
    
    async def create_secret(
        self,
        secret_id: str,
        name: str,
        value: str,
        secret_type: SecretType,
        description: Optional[str] = None,
        tags: Optional[Set[str]] = None,
        expires_at: Optional[datetime] = None,
        rotation_strategy: RotationStrategy = RotationStrategy.MANUAL,
        rotation_interval: Optional[timedelta] = None,
        environment: Optional[str] = None,
        tenant_id: Optional[str] = None,
        service: Optional[str] = None,
        created_by: str = "system"
    ) -> Secret:
        """Create new secret"""
        try:
            # Validate secret doesn't exist
            if secret_id in self.secrets:
                raise ValidationError(f"Secret {secret_id} already exists")
            
            # Validate secret value
            await self._validate_secret_value(secret_type, value)
            
            # Encrypt secret value
            encrypted_value = await self._encrypt_secret(value)
            
            # Create secret
            secret = Secret(
                secret_id=secret_id,
                name=name,
                secret_type=secret_type,
                encrypted_value=encrypted_value,
                description=description,
                tags=tags or set(),
                expires_at=expires_at,
                rotation_strategy=rotation_strategy,
                rotation_interval=rotation_interval,
                environment=environment,
                tenant_id=tenant_id,
                service=service,
                created_by=created_by
            )
            
            # Calculate next rotation if scheduled
            if rotation_strategy == RotationStrategy.SCHEDULED and rotation_interval:
                secret.next_rotation = datetime.utcnow() + rotation_interval
            
            # Store secret
            self.secrets[secret_id] = secret
            self.secret_versions[secret_id] = {1: encrypted_value}
            self.access_controls[secret_id] = []
            self.rotation_history[secret_id] = []
            
            # Schedule rotation if needed
            if secret.next_rotation:
                await self._schedule_rotation(secret_id, secret.next_rotation)
            
            # Log audit entry
            await self._log_audit_entry(
                secret_id=secret_id,
                action="create",
                principal_id=created_by,
                details={'secret_type': secret_type.value, 'name': name}
            )
            
            self.metrics['secrets_managed'] += 1
            self.logger.info(f"Secret created: {secret_id}")
            
            return secret
            
        except Exception as e:
            self.logger.error(f"Failed to create secret {secret_id}: {str(e)}")
            raise ConfigurationError(f"Secret creation failed: {str(e)}")
    
    async def get_secret(
        self,
        secret_id: str,
        principal_type: str,
        principal_id: str,
        decrypt: bool = True,
        version: Optional[int] = None
    ) -> Optional[str]:
        """Get secret value with access control"""
        try:
            # Check if secret exists
            if secret_id not in self.secrets:
                await self._log_audit_entry(
                    secret_id=secret_id,
                    action="access_denied",
                    principal_id=principal_id,
                    success=False,
                    details={'reason': 'secret_not_found'}
                )
                return None
            
            # Check access permissions
            if not await self._check_access(secret_id, principal_type, principal_id, AccessLevel.READ_ONLY):
                await self._log_audit_entry(
                    secret_id=secret_id,
                    action="access_denied",
                    principal_id=principal_id,
                    success=False,
                    details={'reason': 'insufficient_permissions'}
                )
                self.metrics['access_denials'] += 1
                return None
            
            secret = self.secrets[secret_id]
            
            # Check if secret is active
            if secret.status != SecretStatus.ACTIVE:
                await self._log_audit_entry(
                    secret_id=secret_id,
                    action="access_denied",
                    principal_id=principal_id,
                    success=False,
                    details={'reason': f'secret_status_{secret.status.value}'}
                )
                return None
            
            # Check expiration
            if secret.expires_at and datetime.utcnow() > secret.expires_at:
                await self._log_audit_entry(
                    secret_id=secret_id,
                    action="access_denied",
                    principal_id=principal_id,
                    success=False,
                    details={'reason': 'secret_expired'}
                )
                return None
            
            # Get encrypted value
            if version is None:
                encrypted_value = secret.encrypted_value
            else:
                if secret_id in self.secret_versions and version in self.secret_versions[secret_id]:
                    encrypted_value = self.secret_versions[secret_id][version]
                else:
                    return None
            
            # Decrypt if requested
            if decrypt:
                value = await self._decrypt_secret(encrypted_value)
            else:
                value = encrypted_value
            
            # Update access tracking
            secret.access_count += 1
            secret.last_accessed = datetime.utcnow()
            
            # Log audit entry
            await self._log_audit_entry(
                secret_id=secret_id,
                action="access_granted",
                principal_id=principal_id,
                details={'version': version or secret.version}
            )
            
            # Notify monitors
            await self._notify_access_monitors(secret_id, principal_id)
            
            self.metrics['access_grants'] += 1
            return value
            
        except Exception as e:
            self.logger.error(f"Failed to get secret {secret_id}: {str(e)}")
            await self._log_audit_entry(
                secret_id=secret_id,
                action="access_error",
                principal_id=principal_id,
                success=False,
                error_message=str(e)
            )
            return None
    
    async def update_secret(
        self,
        secret_id: str,
        value: str,
        principal_type: str,
        principal_id: str,
        updated_by: str = "system"
    ) -> bool:
        """Update secret value"""
        try:
            # Check if secret exists
            if secret_id not in self.secrets:
                return False
            
            # Check access permissions
            if not await self._check_access(secret_id, principal_type, principal_id, AccessLevel.READ_WRITE):
                self.metrics['access_denials'] += 1
                return False
            
            secret = self.secrets[secret_id]
            
            # Validate new value
            await self._validate_secret_value(secret.secret_type, value)
            
            # Encrypt new value
            encrypted_value = await self._encrypt_secret(value)
            
            # Store old version
            old_version = secret.version
            new_version = old_version + 1
            
            if secret_id not in self.secret_versions:
                self.secret_versions[secret_id] = {}
            
            # Keep old version
            self.secret_versions[secret_id][old_version] = secret.encrypted_value
            self.secret_versions[secret_id][new_version] = encrypted_value
            
            # Update secret
            secret.encrypted_value = encrypted_value
            secret.version = new_version
            secret.updated_at = datetime.utcnow()
            secret.updated_by = updated_by
            
            # Log audit entry
            await self._log_audit_entry(
                secret_id=secret_id,
                action="update",
                principal_id=principal_id,
                details={'old_version': old_version, 'new_version': new_version}
            )
            
            self.logger.info(f"Secret updated: {secret_id} (version {new_version})")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update secret {secret_id}: {str(e)}")
            return False
    
    async def delete_secret(
        self,
        secret_id: str,
        principal_type: str,
        principal_id: str,
        permanent: bool = False
    ) -> bool:
        """Delete or revoke secret"""
        try:
            # Check if secret exists
            if secret_id not in self.secrets:
                return False
            
            # Check access permissions
            if not await self._check_access(secret_id, principal_type, principal_id, AccessLevel.ADMIN):
                self.metrics['access_denials'] += 1
                return False
            
            secret = self.secrets[secret_id]
            
            if permanent:
                # Permanently delete secret
                del self.secrets[secret_id]
                if secret_id in self.secret_versions:
                    del self.secret_versions[secret_id]
                if secret_id in self.access_controls:
                    del self.access_controls[secret_id]
                if secret_id in self.rotation_history:
                    del self.rotation_history[secret_id]
                
                # Cancel rotation if scheduled
                if secret_id in self.rotation_schedules:
                    self.rotation_schedules[secret_id].cancel()
                    del self.rotation_schedules[secret_id]
                
                action = "delete_permanent"
            else:
                # Revoke secret
                secret.status = SecretStatus.REVOKED
                secret.updated_at = datetime.utcnow()
                action = "revoke"
            
            # Log audit entry
            await self._log_audit_entry(
                secret_id=secret_id,
                action=action,
                principal_id=principal_id
            )
            
            self.logger.info(f"Secret {action}: {secret_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete secret {secret_id}: {str(e)}")
            return False
    
    async def grant_access(
        self,
        secret_id: str,
        principal_type: str,
        principal_id: str,
        access_level: AccessLevel,
        granted_by: str,
        expires_at: Optional[datetime] = None,
        conditions: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Grant access to secret"""
        try:
            # Check if secret exists
            if secret_id not in self.secrets:
                return False
            
            # Create access control entry
            access = SecretAccess(
                secret_id=secret_id,
                principal_type=principal_type,
                principal_id=principal_id,
                access_level=access_level,
                granted_by=granted_by,
                expires_at=expires_at,
                conditions=conditions or {}
            )
            
            # Store access control
            if secret_id not in self.access_controls:
                self.access_controls[secret_id] = []
            
            self.access_controls[secret_id].append(access)
            
            # Clear access cache
            await self._clear_access_cache(secret_id, principal_id)
            
            # Log audit entry
            await self._log_audit_entry(
                secret_id=secret_id,
                action="grant_access",
                principal_id=granted_by,
                details={
                    'target_principal': principal_id,
                    'access_level': access_level.value,
                    'expires_at': expires_at.isoformat() if expires_at else None
                }
            )
            
            self.logger.info(f"Access granted: {secret_id} to {principal_id} ({access_level.value})")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to grant access to secret {secret_id}: {str(e)}")
            return False
    
    async def revoke_access(
        self,
        secret_id: str,
        principal_id: str,
        revoked_by: str
    ) -> bool:
        """Revoke access to secret"""
        try:
            if secret_id not in self.access_controls:
                return False
            
            # Find and deactivate access
            revoked = False
            for access in self.access_controls[secret_id]:
                if access.principal_id == principal_id and access.active:
                    access.active = False
                    revoked = True
            
            if revoked:
                # Clear access cache
                await self._clear_access_cache(secret_id, principal_id)
                
                # Log audit entry
                await self._log_audit_entry(
                    secret_id=secret_id,
                    action="revoke_access",
                    principal_id=revoked_by,
                    details={'target_principal': principal_id}
                )
                
                self.logger.info(f"Access revoked: {secret_id} from {principal_id}")
            
            return revoked
            
        except Exception as e:
            self.logger.error(f"Failed to revoke access to secret {secret_id}: {str(e)}")
            return False
    
    async def rotate_secret(
        self,
        secret_id: str,
        initiated_by: str = "system",
        rotation_type: str = "manual"
    ) -> bool:
        """Rotate secret value"""
        try:
            # Check if secret exists
            if secret_id not in self.secrets:
                return False
            
            secret = self.secrets[secret_id]
            
            # Create rotation record
            rotation_id = f"rot_{secret_id}_{int(datetime.utcnow().timestamp())}"
            rotation = SecretRotation(
                rotation_id=rotation_id,
                secret_id=secret_id,
                old_version=secret.version,
                new_version=secret.version + 1,
                rotation_type=rotation_type,
                initiated_by=initiated_by
            )
            
            try:
                # Generate new secret value
                new_value = await self._generate_secret_value(secret.secret_type)
                
                # Encrypt new value
                encrypted_value = await self._encrypt_secret(new_value)
                
                # Store old version
                if secret_id not in self.secret_versions:
                    self.secret_versions[secret_id] = {}
                
                self.secret_versions[secret_id][secret.version] = secret.encrypted_value
                self.secret_versions[secret_id][rotation.new_version] = encrypted_value
                
                # Update secret
                secret.encrypted_value = encrypted_value
                secret.version = rotation.new_version
                secret.last_rotated = datetime.utcnow()
                secret.updated_at = datetime.utcnow()
                
                # Schedule next rotation if applicable
                if secret.rotation_strategy == RotationStrategy.SCHEDULED and secret.rotation_interval:
                    secret.next_rotation = datetime.utcnow() + secret.rotation_interval
                    await self._schedule_rotation(secret_id, secret.next_rotation)
                
                # Complete rotation
                rotation.completed_at = datetime.utcnow()
                rotation.status = "completed"
                
                # Store rotation history
                if secret_id not in self.rotation_history:
                    self.rotation_history[secret_id] = []
                
                self.rotation_history[secret_id].append(rotation)
                
                # Log audit entry
                await self._log_audit_entry(
                    secret_id=secret_id,
                    action="rotate",
                    principal_id=initiated_by,
                    details={
                        'rotation_id': rotation_id,
                        'old_version': rotation.old_version,
                        'new_version': rotation.new_version,
                        'rotation_type': rotation_type
                    }
                )
                
                # Notify monitors
                await self._notify_rotation_monitors(secret_id, rotation)
                
                self.metrics['rotations_performed'] += 1
                self.logger.info(f"Secret rotated: {secret_id} (version {rotation.new_version})")
                
                return True
                
            except Exception as e:
                # Mark rotation as failed
                rotation.status = "failed"
                rotation.error_message = str(e)
                rotation.completed_at = datetime.utcnow()
                
                if secret_id not in self.rotation_history:
                    self.rotation_history[secret_id] = []
                
                self.rotation_history[secret_id].append(rotation)
                
                self.logger.error(f"Secret rotation failed: {secret_id} - {str(e)}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to rotate secret {secret_id}: {str(e)}")
            return False
    
    async def generate_secret(
        self,
        secret_type: SecretType,
        length: Optional[int] = None,
        include_special: bool = True
    ) -> str:
        """Generate new secret value"""
        try:
            if secret_type in self.generators:
                generator = self.generators[secret_type]
                return await generator(length, include_special)
            else:
                return await self._default_generator(secret_type, length, include_special)
                
        except Exception as e:
            self.logger.error(f"Failed to generate secret for type {secret_type}: {str(e)}")
            raise ConfigurationError(f"Secret generation failed: {str(e)}")
    
    async def get_secret_metadata(self, secret_id: str) -> Optional[Dict[str, Any]]:
        """Get secret metadata (without value)"""
        try:
            if secret_id not in self.secrets:
                return None
            
            secret = self.secrets[secret_id]
            
            return {
                'secret_id': secret.secret_id,
                'name': secret.name,
                'secret_type': secret.secret_type.value,
                'status': secret.status.value,
                'description': secret.description,
                'tags': list(secret.tags),
                'created_at': secret.created_at.isoformat(),
                'updated_at': secret.updated_at.isoformat(),
                'created_by': secret.created_by,
                'updated_by': secret.updated_by,
                'version': secret.version,
                'expires_at': secret.expires_at.isoformat() if secret.expires_at else None,
                'rotation_strategy': secret.rotation_strategy.value,
                'last_rotated': secret.last_rotated.isoformat() if secret.last_rotated else None,
                'next_rotation': secret.next_rotation.isoformat() if secret.next_rotation else None,
                'environment': secret.environment,
                'tenant_id': secret.tenant_id,
                'service': secret.service,
                'access_count': secret.access_count,
                'last_accessed': secret.last_accessed.isoformat() if secret.last_accessed else None
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get secret metadata {secret_id}: {str(e)}")
            return None
    
    async def list_secrets(
        self,
        environment: Optional[str] = None,
        tenant_id: Optional[str] = None,
        service: Optional[str] = None,
        secret_type: Optional[SecretType] = None,
        status: Optional[SecretStatus] = None
    ) -> List[Dict[str, Any]]:
        """List secrets with filters"""
        try:
            secrets_list = []
            
            for secret in self.secrets.values():
                # Apply filters
                if environment and secret.environment != environment:
                    continue
                if tenant_id and secret.tenant_id != tenant_id:
                    continue
                if service and secret.service != service:
                    continue
                if secret_type and secret.secret_type != secret_type:
                    continue
                if status and secret.status != status:
                    continue
                
                # Get metadata
                metadata = await self.get_secret_metadata(secret.secret_id)
                if metadata:
                    secrets_list.append(metadata)
            
            return secrets_list
            
        except Exception as e:
            self.logger.error(f"Failed to list secrets: {str(e)}")
            return []
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get secrets coordinator health status"""
        try:
            # Calculate expiring secrets
            expiring_soon = 0
            expired = 0
            now = datetime.utcnow()
            week_from_now = now + timedelta(days=7)
            
            for secret in self.secrets.values():
                if secret.expires_at:
                    if secret.expires_at < now:
                        expired += 1
                    elif secret.expires_at < week_from_now:
                        expiring_soon += 1
            
            # Calculate due rotations
            due_rotations = 0
            for secret in self.secrets.values():
                if secret.next_rotation and secret.next_rotation < now:
                    due_rotations += 1
            
            return {
                'service': 'SecretsCoordinator',
                'status': 'healthy',
                'timestamp': datetime.utcnow().isoformat(),
                'metrics': self.metrics,
                'secrets': {
                    'total': len(self.secrets),
                    'by_type': {
                        secret_type.value: len([s for s in self.secrets.values() if s.secret_type == secret_type])
                        for secret_type in SecretType
                    },
                    'by_status': {
                        status.value: len([s for s in self.secrets.values() if s.status == status])
                        for status in SecretStatus
                    },
                    'expiring_soon': expiring_soon,
                    'expired': expired,
                    'due_rotations': due_rotations
                },
                'access_controls': {
                    'total_grants': sum(len(controls) for controls in self.access_controls.values()),
                    'secrets_with_access': len(self.access_controls)
                },
                'rotations': {
                    'scheduled': len(self.rotation_schedules),
                    'total_history': sum(len(history) for history in self.rotation_history.values())
                },
                'cache': {
                    'access_cache_size': len(self.access_cache),
                    'hit_ratio': (
                        self.metrics['cache_hits'] / 
                        (self.metrics['cache_hits'] + self.metrics['cache_misses'])
                        if (self.metrics['cache_hits'] + self.metrics['cache_misses']) > 0
                        else 0
                    )
                },
                'audit': {
                    'total_entries': len(self.audit_log)
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get health status: {str(e)}")
            return {
                'service': 'SecretsCoordinator',
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    async def _initialize_encryption(self) -> None:
        """Initialize encryption system"""
        # In production, this would use proper key management
        # For demo purposes, generate a key
        if not self.master_key:
            self.master_key = base64.b64encode(py_secrets.token_bytes(32)).decode()
        
        if not self.key_derivation_salt:
            self.key_derivation_salt = py_secrets.token_bytes(32)
    
    async def _initialize_secret_generators(self) -> None:
        """Initialize secret value generators"""
        self.generators = {
            SecretType.API_KEY: self._generate_api_key,
            SecretType.JWT_SECRET: self._generate_jwt_secret,
            SecretType.ENCRYPTION_KEY: self._generate_encryption_key,
            SecretType.WEBHOOK_SECRET: self._generate_webhook_secret
        }
    
    async def _initialize_validators(self) -> None:
        """Initialize secret validators"""
        self.validators = {
            SecretType.API_KEY: lambda v: len(v) >= 32,
            SecretType.DATABASE_PASSWORD: lambda v: len(v) >= 8,
            SecretType.JWT_SECRET: lambda v: len(v) >= 32,
            SecretType.ENCRYPTION_KEY: lambda v: len(v) >= 32,
            SecretType.WEBHOOK_SECRET: lambda v: len(v) >= 16
        }
    
    async def _start_background_workers(self) -> None:
        """Start background worker tasks"""
        # Rotation worker
        async def rotation_worker():
            while True:
                try:
                    await asyncio.sleep(3600)  # Check every hour
                    await self._check_due_rotations()
                except Exception as e:
                    self.logger.error(f"Rotation worker error: {str(e)}")
                    await asyncio.sleep(60)
        
        # Expiration worker
        async def expiration_worker():
            while True:
                try:
                    await asyncio.sleep(3600)  # Check every hour
                    await self._check_expired_secrets()
                except Exception as e:
                    self.logger.error(f"Expiration worker error: {str(e)}")
                    await asyncio.sleep(60)
        
        # Audit cleanup worker
        async def audit_cleanup_worker():
            while True:
                try:
                    await asyncio.sleep(86400)  # Check daily
                    await self._cleanup_audit_log()
                except Exception as e:
                    self.logger.error(f"Audit cleanup worker error: {str(e)}")
                    await asyncio.sleep(3600)
        
        self.background_tasks['rotation'] = asyncio.create_task(rotation_worker())
        self.background_tasks['expiration'] = asyncio.create_task(expiration_worker())
        self.background_tasks['audit_cleanup'] = asyncio.create_task(audit_cleanup_worker())
    
    async def _load_default_secrets(self) -> None:
        """Load default system secrets if they don't exist"""
        default_secrets = [
            ('system_jwt_secret', 'System JWT Secret', SecretType.JWT_SECRET),
            ('system_encryption_key', 'System Encryption Key', SecretType.ENCRYPTION_KEY),
            ('firs_api_key', 'FIRS API Key', SecretType.FIRS_CREDENTIALS)
        ]
        
        for secret_id, name, secret_type in default_secrets:
            if secret_id not in self.secrets:
                value = await self.generate_secret(secret_type)
                await self.create_secret(
                    secret_id=secret_id,
                    name=name,
                    value=value,
                    secret_type=secret_type,
                    rotation_strategy=RotationStrategy.SCHEDULED,
                    rotation_interval=timedelta(days=90),
                    created_by="system_initialization"
                )
                
                # Grant system access
                await self.grant_access(
                    secret_id=secret_id,
                    principal_type="system",
                    principal_id="taxpoynt_platform",
                    access_level=AccessLevel.SYSTEM,
                    granted_by="system_initialization"
                )
    
    async def _encrypt_secret(self, value: str) -> str:
        """Encrypt secret value"""
        try:
            # For demo purposes, use base64 encoding
            # In production, use proper encryption (AES-GCM, Fernet, etc.)
            encoded = base64.b64encode(value.encode()).decode()
            self.metrics['encryption_operations'] += 1
            return encoded
        except Exception as e:
            raise SecurityError(f"Encryption failed: {str(e)}")
    
    async def _decrypt_secret(self, encrypted_value: str) -> str:
        """Decrypt secret value"""
        try:
            # For demo purposes, use base64 decoding
            # In production, use proper decryption
            decoded = base64.b64decode(encrypted_value.encode()).decode()
            self.metrics['decryption_operations'] += 1
            return decoded
        except Exception as e:
            raise SecurityError(f"Decryption failed: {str(e)}")
    
    async def _validate_secret_value(self, secret_type: SecretType, value: str) -> None:
        """Validate secret value"""
        if secret_type in self.validators:
            validator = self.validators[secret_type]
            if not validator(value):
                raise ValidationError(f"Invalid value for secret type {secret_type.value}")
    
    async def _generate_secret_value(self, secret_type: SecretType) -> str:
        """Generate new secret value for rotation"""
        if secret_type in self.generators:
            generator = self.generators[secret_type]
            return await generator()
        else:
            return await self._default_generator(secret_type)
    
    async def _default_generator(
        self,
        secret_type: SecretType,
        length: Optional[int] = None,
        include_special: bool = True
    ) -> str:
        """Default secret generator"""
        if length is None:
            length = 32
        
        if include_special:
            chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*"
        else:
            chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        
        return ''.join(py_secrets.choice(chars) for _ in range(length))
    
    async def _generate_api_key(self, length: Optional[int] = None, include_special: bool = True) -> str:
        """Generate API key"""
        return f"ak_{py_secrets.token_urlsafe(32)}"
    
    async def _generate_jwt_secret(self, length: Optional[int] = None, include_special: bool = True) -> str:
        """Generate JWT secret"""
        return py_secrets.token_urlsafe(64)
    
    async def _generate_encryption_key(self, length: Optional[int] = None, include_special: bool = True) -> str:
        """Generate encryption key"""
        return base64.b64encode(py_secrets.token_bytes(32)).decode()
    
    async def _generate_webhook_secret(self, length: Optional[int] = None, include_special: bool = True) -> str:
        """Generate webhook secret"""
        return f"whsec_{py_secrets.token_urlsafe(24)}"
    
    async def _check_access(
        self,
        secret_id: str,
        principal_type: str,
        principal_id: str,
        required_level: AccessLevel
    ) -> bool:
        """Check access permissions with caching"""
        cache_key = f"{secret_id}:{principal_type}:{principal_id}:{required_level.value}"
        
        # Check cache first
        if cache_key in self.access_cache:
            timestamp = self.cache_timestamps.get(cache_key)
            if timestamp and datetime.utcnow() - timestamp < self.cache_ttl:
                self.metrics['cache_hits'] += 1
                return self.access_cache[cache_key]
            else:
                # Remove expired entry
                del self.access_cache[cache_key]
                if cache_key in self.cache_timestamps:
                    del self.cache_timestamps[cache_key]
        
        # Check access
        has_access = await self._check_access_direct(secret_id, principal_type, principal_id, required_level)
        
        # Cache result
        self.access_cache[cache_key] = has_access
        self.cache_timestamps[cache_key] = datetime.utcnow()
        
        # Limit cache size
        if len(self.access_cache) > 10000:
            oldest_key = min(self.cache_timestamps.keys(), key=self.cache_timestamps.get)
            del self.access_cache[oldest_key]
            del self.cache_timestamps[oldest_key]
        
        self.metrics['cache_misses'] += 1
        return has_access
    
    async def _check_access_direct(
        self,
        secret_id: str,
        principal_type: str,
        principal_id: str,
        required_level: AccessLevel
    ) -> bool:
        """Check access permissions directly"""
        if secret_id not in self.access_controls:
            return False
        
        # Level hierarchy: SYSTEM > ADMIN > READ_WRITE > READ_ONLY
        level_hierarchy = {
            AccessLevel.READ_ONLY: 1,
            AccessLevel.READ_WRITE: 2,
            AccessLevel.ADMIN: 3,
            AccessLevel.SYSTEM: 4
        }
        
        required_level_value = level_hierarchy[required_level]
        
        for access in self.access_controls[secret_id]:
            if (access.principal_type == principal_type and 
                access.principal_id == principal_id and 
                access.active):
                
                # Check expiration
                if access.expires_at and datetime.utcnow() > access.expires_at:
                    continue
                
                # Check level
                access_level_value = level_hierarchy[access.access_level]
                if access_level_value >= required_level_value:
                    # Check conditions if any
                    if await self._check_access_conditions(access.conditions):
                        return True
        
        return False
    
    async def _check_access_conditions(self, conditions: Dict[str, Any]) -> bool:
        """Check access conditions"""
        # Implement condition checking logic
        # For now, return True if no conditions or all conditions pass
        return True
    
    async def _clear_access_cache(self, secret_id: str, principal_id: Optional[str] = None) -> None:
        """Clear access cache"""
        if principal_id:
            # Clear specific principal
            keys_to_remove = [
                key for key in self.access_cache.keys()
                if key.startswith(f"{secret_id}:") and f":{principal_id}:" in key
            ]
        else:
            # Clear all for secret
            keys_to_remove = [
                key for key in self.access_cache.keys()
                if key.startswith(f"{secret_id}:")
            ]
        
        for key in keys_to_remove:
            del self.access_cache[key]
            if key in self.cache_timestamps:
                del self.cache_timestamps[key]
    
    async def _schedule_rotation(self, secret_id: str, rotation_time: datetime) -> None:
        """Schedule secret rotation"""
        async def rotation_task():
            await asyncio.sleep((rotation_time - datetime.utcnow()).total_seconds())
            await self.rotate_secret(secret_id, "scheduled_rotation", "scheduled")
        
        if secret_id in self.rotation_schedules:
            self.rotation_schedules[secret_id].cancel()
        
        self.rotation_schedules[secret_id] = asyncio.create_task(rotation_task())
    
    async def _check_due_rotations(self) -> None:
        """Check for due rotations"""
        now = datetime.utcnow()
        
        for secret in self.secrets.values():
            if (secret.next_rotation and 
                secret.next_rotation <= now and 
                secret.status == SecretStatus.ACTIVE):
                await self.rotate_secret(secret.secret_id, "automatic_rotation", "scheduled")
    
    async def _check_expired_secrets(self) -> None:
        """Check for expired secrets"""
        now = datetime.utcnow()
        
        for secret in self.secrets.values():
            if (secret.expires_at and 
                secret.expires_at <= now and 
                secret.status == SecretStatus.ACTIVE):
                secret.status = SecretStatus.EXPIRED
                secret.updated_at = now
                
                await self._log_audit_entry(
                    secret_id=secret.secret_id,
                    action="expired",
                    principal_id="system",
                    details={'expired_at': now.isoformat()}
                )
    
    async def _cleanup_audit_log(self) -> None:
        """Clean up old audit log entries"""
        # Keep last 30 days of audit entries
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        
        original_count = len(self.audit_log)
        self.audit_log = [
            entry for entry in self.audit_log
            if entry.timestamp > cutoff_date
        ]
        
        cleaned_count = original_count - len(self.audit_log)
        if cleaned_count > 0:
            self.logger.info(f"Cleaned up {cleaned_count} old audit entries")
    
    async def _log_audit_entry(
        self,
        secret_id: str,
        action: str,
        principal_id: str,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> None:
        """Log audit entry"""
        entry = SecretAuditEntry(
            entry_id=f"audit_{int(datetime.utcnow().timestamp())}_{py_secrets.token_hex(8)}",
            secret_id=secret_id,
            action=action,
            principal_id=principal_id,
            details=details or {},
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            error_message=error_message
        )
        
        self.audit_log.append(entry)
        self.metrics['audit_entries'] += 1
        
        # Limit audit log size
        if len(self.audit_log) > 100000:
            self.audit_log = self.audit_log[-50000:]
    
    async def _notify_access_monitors(self, secret_id: str, principal_id: str) -> None:
        """Notify access monitors"""
        for monitor in self.access_monitors:
            try:
                if asyncio.iscoroutinefunction(monitor):
                    await monitor(secret_id, principal_id)
                else:
                    monitor(secret_id, principal_id)
            except Exception as e:
                self.logger.error(f"Access monitor error: {str(e)}")
    
    async def _notify_rotation_monitors(self, secret_id: str, rotation: SecretRotation) -> None:
        """Notify rotation monitors"""
        for monitor in self.rotation_monitors:
            try:
                if asyncio.iscoroutinefunction(monitor):
                    await monitor(secret_id, rotation)
                else:
                    monitor(secret_id, rotation)
            except Exception as e:
                self.logger.error(f"Rotation monitor error: {str(e)}")
    
    async def cleanup(self) -> None:
        """Cleanup secrets coordinator resources"""
        try:
            # Cancel background tasks
            for task in self.background_tasks.values():
                if not task.done():
                    task.cancel()
            
            # Cancel rotation schedules
            for task in self.rotation_schedules.values():
                if not task.done():
                    task.cancel()
            
            # Clear caches
            self.access_cache.clear()
            self.cache_timestamps.clear()
            
            self.logger.info("SecretsCoordinator cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during SecretsCoordinator cleanup: {str(e)}")