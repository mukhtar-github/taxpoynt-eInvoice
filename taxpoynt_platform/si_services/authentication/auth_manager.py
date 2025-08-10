"""
Authentication Manager Service

This module provides centralized authentication management for SI services,
coordinating various authentication methods and providers to ensure secure
access to ERP systems, FIRS APIs, and internal platform services.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Union, Type
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from abc import ABC, abstractmethod
import json
from pathlib import Path
import hashlib
import secrets

logger = logging.getLogger(__name__)


class AuthenticationType(Enum):
    """Types of authentication methods"""
    BASIC = "basic"
    OAUTH2 = "oauth2"
    API_KEY = "api_key"
    JWT = "jwt"
    CERTIFICATE = "certificate"
    SAML = "saml"
    LDAP = "ldap"
    MULTI_FACTOR = "multi_factor"
    CUSTOM = "custom"


class AuthenticationStatus(Enum):
    """Status of authentication operations"""
    PENDING = "pending"
    AUTHENTICATED = "authenticated"
    FAILED = "failed"
    EXPIRED = "expired"
    REFRESHING = "refreshing"
    REVOKED = "revoked"
    LOCKED = "locked"


class AuthenticationScope(Enum):
    """Scope of authentication access"""
    ERP_READ = "erp_read"
    ERP_WRITE = "erp_write"
    FIRS_API = "firs_api"
    CERTIFICATE_MGMT = "certificate_mgmt"
    ADMIN = "admin"
    SYSTEM = "system"
    TENANT_ADMIN = "tenant_admin"
    USER = "user"


class ServiceType(Enum):
    """Types of services requiring authentication"""
    ERP_SYSTEM = "erp_system"
    FIRS_API = "firs_api"
    CERTIFICATE_AUTHORITY = "certificate_authority"
    INTERNAL_SERVICE = "internal_service"
    EXTERNAL_API = "external_api"
    DATABASE = "database"


@dataclass
class AuthenticationContext:
    """Context for authentication operations"""
    user_id: Optional[str] = None
    tenant_id: Optional[str] = None
    service_type: Optional[ServiceType] = None
    requested_scopes: List[AuthenticationScope] = field(default_factory=list)
    client_info: Dict[str, Any] = field(default_factory=dict)
    session_metadata: Dict[str, Any] = field(default_factory=dict)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    request_id: Optional[str] = None


@dataclass
class AuthenticationCredentials:
    """Credentials for authentication"""
    credential_id: str
    auth_type: AuthenticationType
    service_identifier: str
    username: Optional[str] = None
    password: Optional[str] = None
    api_key: Optional[str] = None
    token: Optional[str] = None
    certificate_path: Optional[str] = None
    private_key_path: Optional[str] = None
    oauth_client_id: Optional[str] = None
    oauth_client_secret: Optional[str] = None
    custom_params: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    is_encrypted: bool = False


@dataclass
class AuthenticationResult:
    """Result of authentication operation"""
    session_id: str
    status: AuthenticationStatus
    auth_type: AuthenticationType
    service_identifier: str
    authenticated_at: datetime
    expires_at: Optional[datetime] = None
    granted_scopes: List[AuthenticationScope] = field(default_factory=list)
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    user_info: Dict[str, Any] = field(default_factory=dict)
    service_metadata: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    retry_count: int = 0
    last_used: datetime = field(default_factory=datetime.now)


@dataclass
class AuthenticationConfig:
    """Configuration for authentication manager"""
    enable_session_caching: bool = True
    session_timeout_minutes: int = 60
    max_retry_attempts: int = 3
    token_refresh_threshold_minutes: int = 10
    enable_credential_encryption: bool = True
    credential_storage_path: Optional[str] = None
    enable_audit_logging: bool = True
    audit_log_path: Optional[str] = None
    max_concurrent_authentications: int = 20
    enable_rate_limiting: bool = True
    rate_limit_per_minute: int = 100
    enable_mfa: bool = False
    session_cleanup_interval_minutes: int = 30


class BaseAuthProvider(ABC):
    """Abstract base class for authentication providers"""
    
    def __init__(self, provider_id: str, auth_type: AuthenticationType):
        self.provider_id = provider_id
        self.auth_type = auth_type
        self.is_enabled = True
    
    @abstractmethod
    async def authenticate(
        self,
        credentials: AuthenticationCredentials,
        context: AuthenticationContext
    ) -> AuthenticationResult:
        """Authenticate using the provider"""
        pass
    
    @abstractmethod
    async def validate_token(
        self,
        token: str,
        context: AuthenticationContext
    ) -> bool:
        """Validate authentication token"""
        pass
    
    @abstractmethod
    async def refresh_token(
        self,
        refresh_token: str,
        context: AuthenticationContext
    ) -> Optional[AuthenticationResult]:
        """Refresh authentication token"""
        pass
    
    @abstractmethod
    async def revoke_token(
        self,
        token: str,
        context: AuthenticationContext
    ) -> bool:
        """Revoke authentication token"""
        pass


class AuthenticationManager:
    """
    Central authentication manager for SI services that coordinates
    various authentication providers and manages authentication sessions.
    """
    
    def __init__(self, config: AuthenticationConfig):
        self.config = config
        self.auth_providers: Dict[str, BaseAuthProvider] = {}
        self.active_sessions: Dict[str, AuthenticationResult] = {}
        self.credential_cache: Dict[str, AuthenticationCredentials] = {}
        
        # Authentication state
        self.is_running = False
        self.cleanup_task: Optional[asyncio.Task] = None
        self.audit_logger: Optional[logging.Logger] = None
        
        # Rate limiting
        from collections import defaultdict, deque
        self.rate_limit_counters: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        
        # Concurrency control
        self.auth_semaphore = asyncio.Semaphore(config.max_concurrent_authentications)
        
        # Setup storage paths
        if config.credential_storage_path:
            self.storage_path = Path(config.credential_storage_path)
            self.storage_path.mkdir(parents=True, exist_ok=True)
        else:
            self.storage_path = None
        
        # Setup audit logging
        if config.enable_audit_logging:
            self._setup_audit_logging()
    
    async def start_auth_manager(self) -> None:
        """Start the authentication manager"""
        if self.is_running:
            return
        
        self.is_running = True
        logger.info("Starting Authentication Manager")
        
        # Start cleanup task
        self.cleanup_task = asyncio.create_task(self._session_cleanup_loop())
        
        # Load stored credentials
        await self._load_stored_credentials()
        
        # Initialize providers
        await self._initialize_auth_providers()
    
    async def stop_auth_manager(self) -> None:
        """Stop the authentication manager"""
        if not self.is_running:
            return
        
        self.is_running = False
        logger.info("Stopping Authentication Manager")
        
        # Cancel cleanup task
        if self.cleanup_task:
            self.cleanup_task.cancel()
        
        # Revoke all active sessions
        await self._revoke_all_sessions()
        
        # Save current state
        await self._save_auth_state()
    
    async def register_auth_provider(
        self,
        provider: BaseAuthProvider,
        service_types: List[ServiceType]
    ) -> bool:
        """Register an authentication provider"""
        try:
            provider_key = f"{provider.provider_id}_{provider.auth_type.value}"
            self.auth_providers[provider_key] = provider
            
            # Store provider metadata
            provider.service_types = service_types
            
            logger.info(f"Registered auth provider: {provider_key}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register auth provider {provider.provider_id}: {e}")
            return False
    
    async def authenticate(
        self,
        service_identifier: str,
        auth_type: AuthenticationType,
        credentials: Optional[AuthenticationCredentials] = None,
        context: Optional[AuthenticationContext] = None
    ) -> Optional[AuthenticationResult]:
        """Authenticate to a service"""
        async with self.auth_semaphore:
            try:
                context = context or AuthenticationContext()
                
                # Check rate limiting
                if not await self._check_rate_limit(context):
                    logger.warning("Authentication rate limit exceeded")
                    return None
                
                # Get or create credentials
                if not credentials:
                    credentials = await self._get_stored_credentials(service_identifier, auth_type)
                    if not credentials:
                        logger.error(f"No credentials found for {service_identifier}")
                        return None
                
                # Check for existing valid session
                existing_session = await self._get_existing_session(service_identifier, auth_type)
                if existing_session and await self._is_session_valid(existing_session):
                    existing_session.last_used = datetime.now()
                    await self._audit_log("session_reused", {
                        "session_id": existing_session.session_id,
                        "service": service_identifier
                    })
                    return existing_session
                
                # Find appropriate provider
                provider = await self._find_auth_provider(auth_type, service_identifier)
                if not provider:
                    logger.error(f"No auth provider found for {auth_type.value}")
                    return None
                
                # Perform authentication
                result = await provider.authenticate(credentials, context)
                
                if result.status == AuthenticationStatus.AUTHENTICATED:
                    # Cache session
                    self.active_sessions[result.session_id] = result
                    
                    # Audit log
                    await self._audit_log("authentication_success", {
                        "session_id": result.session_id,
                        "service": service_identifier,
                        "auth_type": auth_type.value,
                        "user_id": context.user_id
                    })
                    
                    logger.info(f"Authentication successful for {service_identifier}")
                else:
                    await self._audit_log("authentication_failed", {
                        "service": service_identifier,
                        "auth_type": auth_type.value,
                        "error": result.error_message,
                        "user_id": context.user_id
                    })
                
                return result
                
            except Exception as e:
                logger.error(f"Authentication failed for {service_identifier}: {e}")
                await self._audit_log("authentication_error", {
                    "service": service_identifier,
                    "error": str(e)
                })
                return None
    
    async def validate_session(self, session_id: str) -> bool:
        """Validate an authentication session"""
        try:
            session = self.active_sessions.get(session_id)
            if not session:
                return False
            
            # Check if session is valid
            if not await self._is_session_valid(session):
                # Remove invalid session
                await self._remove_session(session_id)
                return False
            
            # Update last used
            session.last_used = datetime.now()
            return True
            
        except Exception as e:
            logger.error(f"Session validation failed for {session_id}: {e}")
            return False
    
    async def refresh_session(self, session_id: str) -> Optional[AuthenticationResult]:
        """Refresh an authentication session"""
        try:
            session = self.active_sessions.get(session_id)
            if not session or not session.refresh_token:
                return None
            
            # Find provider
            provider = await self._find_auth_provider(session.auth_type, session.service_identifier)
            if not provider:
                return None
            
            # Create context for refresh
            context = AuthenticationContext(
                service_type=ServiceType.ERP_SYSTEM,  # Default
                session_metadata=session.service_metadata
            )
            
            # Refresh token
            refreshed_session = await provider.refresh_token(session.refresh_token, context)
            
            if refreshed_session and refreshed_session.status == AuthenticationStatus.AUTHENTICATED:
                # Update session
                self.active_sessions[session_id] = refreshed_session
                
                await self._audit_log("session_refreshed", {
                    "session_id": session_id,
                    "service": session.service_identifier
                })
                
                return refreshed_session
            
            return None
            
        except Exception as e:
            logger.error(f"Session refresh failed for {session_id}: {e}")
            return None
    
    async def revoke_session(self, session_id: str) -> bool:
        """Revoke an authentication session"""
        try:
            session = self.active_sessions.get(session_id)
            if not session:
                return False
            
            # Find provider and revoke
            provider = await self._find_auth_provider(session.auth_type, session.service_identifier)
            if provider and session.access_token:
                context = AuthenticationContext()
                await provider.revoke_token(session.access_token, context)
            
            # Remove from active sessions
            await self._remove_session(session_id)
            
            await self._audit_log("session_revoked", {
                "session_id": session_id,
                "service": session.service_identifier
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Session revocation failed for {session_id}: {e}")
            return False
    
    async def store_credentials(
        self,
        credentials: AuthenticationCredentials,
        encrypt: bool = True
    ) -> bool:
        """Store authentication credentials securely"""
        try:
            if encrypt and self.config.enable_credential_encryption:
                credentials = await self._encrypt_credentials(credentials)
            
            # Cache credentials
            cache_key = f"{credentials.service_identifier}_{credentials.auth_type.value}"
            self.credential_cache[cache_key] = credentials
            
            # Persist to storage
            if self.storage_path:
                await self._save_credentials_to_storage(credentials)
            
            await self._audit_log("credentials_stored", {
                "service": credentials.service_identifier,
                "auth_type": credentials.auth_type.value,
                "encrypted": encrypt
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to store credentials: {e}")
            return False
    
    async def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get information about an authentication session"""
        try:
            session = self.active_sessions.get(session_id)
            if not session:
                return None
            
            return {
                "session_id": session.session_id,
                "status": session.status.value,
                "auth_type": session.auth_type.value,
                "service": session.service_identifier,
                "authenticated_at": session.authenticated_at.isoformat(),
                "expires_at": session.expires_at.isoformat() if session.expires_at else None,
                "granted_scopes": [scope.value for scope in session.granted_scopes],
                "last_used": session.last_used.isoformat(),
                "is_valid": await self._is_session_valid(session)
            }
            
        except Exception as e:
            logger.error(f"Failed to get session info for {session_id}: {e}")
            return None
    
    async def list_active_sessions(
        self,
        service_identifier: Optional[str] = None,
        auth_type: Optional[AuthenticationType] = None
    ) -> List[Dict[str, Any]]:
        """List active authentication sessions"""
        try:
            sessions = []
            
            for session in self.active_sessions.values():
                # Apply filters
                if service_identifier and session.service_identifier != service_identifier:
                    continue
                if auth_type and session.auth_type != auth_type:
                    continue
                
                session_info = await self.get_session_info(session.session_id)
                if session_info:
                    sessions.append(session_info)
            
            return sessions
            
        except Exception as e:
            logger.error(f"Failed to list active sessions: {e}")
            return []
    
    async def get_auth_status(self) -> Dict[str, Any]:
        """Get authentication manager status"""
        try:
            return {
                "is_running": self.is_running,
                "active_sessions": len(self.active_sessions),
                "registered_providers": len(self.auth_providers),
                "cached_credentials": len(self.credential_cache),
                "supported_auth_types": [auth_type.value for auth_type in AuthenticationType],
                "config": {
                    "session_timeout_minutes": self.config.session_timeout_minutes,
                    "max_retry_attempts": self.config.max_retry_attempts,
                    "enable_audit_logging": self.config.enable_audit_logging,
                    "enable_credential_encryption": self.config.enable_credential_encryption
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get auth status: {e}")
            return {}
    
    # Private helper methods
    
    async def _get_existing_session(
        self,
        service_identifier: str,
        auth_type: AuthenticationType
    ) -> Optional[AuthenticationResult]:
        """Get existing session for service"""
        for session in self.active_sessions.values():
            if (session.service_identifier == service_identifier and 
                session.auth_type == auth_type and
                session.status == AuthenticationStatus.AUTHENTICATED):
                return session
        return None
    
    async def _is_session_valid(self, session: AuthenticationResult) -> bool:
        """Check if session is still valid"""
        try:
            # Check status
            if session.status != AuthenticationStatus.AUTHENTICATED:
                return False
            
            # Check expiration
            if session.expires_at and datetime.now() > session.expires_at:
                return False
            
            # Check timeout
            timeout_threshold = datetime.now() - timedelta(minutes=self.config.session_timeout_minutes)
            if session.last_used < timeout_threshold:
                return False
            
            return True
            
        except Exception:
            return False
    
    async def _find_auth_provider(
        self,
        auth_type: AuthenticationType,
        service_identifier: str
    ) -> Optional[BaseAuthProvider]:
        """Find appropriate authentication provider"""
        try:
            # Look for exact match first
            provider_key = f"{service_identifier}_{auth_type.value}"
            if provider_key in self.auth_providers:
                return self.auth_providers[provider_key]
            
            # Look for auth type match
            for key, provider in self.auth_providers.items():
                if provider.auth_type == auth_type and provider.is_enabled:
                    return provider
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to find auth provider: {e}")
            return None
    
    async def _get_stored_credentials(
        self,
        service_identifier: str,
        auth_type: AuthenticationType
    ) -> Optional[AuthenticationCredentials]:
        """Get stored credentials for service"""
        try:
            cache_key = f"{service_identifier}_{auth_type.value}"
            
            # Check cache first
            if cache_key in self.credential_cache:
                credentials = self.credential_cache[cache_key]
                if credentials.is_encrypted:
                    credentials = await self._decrypt_credentials(credentials)
                return credentials
            
            # Load from storage
            if self.storage_path:
                return await self._load_credentials_from_storage(service_identifier, auth_type)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get stored credentials: {e}")
            return None
    
    async def _check_rate_limit(self, context: AuthenticationContext) -> bool:
        """Check if request is within rate limits"""
        if not self.config.enable_rate_limiting:
            return True
        
        try:
            # Use IP address or user ID as rate limit key
            rate_key = context.ip_address or context.user_id or "unknown"
            current_time = datetime.now()
            
            # Get rate limit counter
            counter = self.rate_limit_counters[rate_key]
            
            # Remove old entries
            minute_ago = current_time - timedelta(minutes=1)
            while counter and counter[0] < minute_ago:
                counter.popleft()
            
            # Check limit
            if len(counter) >= self.config.rate_limit_per_minute:
                return False
            
            # Add current request
            counter.append(current_time)
            return True
            
        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            return True  # Allow on error
    
    async def _remove_session(self, session_id: str) -> None:
        """Remove session from active sessions"""
        try:
            if session_id in self.active_sessions:
                del self.active_sessions[session_id]
        except Exception as e:
            logger.error(f"Failed to remove session {session_id}: {e}")
    
    async def _session_cleanup_loop(self) -> None:
        """Background task for session cleanup"""
        while self.is_running:
            try:
                await self._cleanup_expired_sessions()
                await asyncio.sleep(self.config.session_cleanup_interval_minutes * 60)
            except Exception as e:
                logger.error(f"Session cleanup error: {e}")
                await asyncio.sleep(60)
    
    async def _cleanup_expired_sessions(self) -> None:
        """Clean up expired sessions"""
        try:
            expired_sessions = []
            
            for session_id, session in self.active_sessions.items():
                if not await self._is_session_valid(session):
                    expired_sessions.append(session_id)
            
            for session_id in expired_sessions:
                await self._remove_session(session_id)
            
            if expired_sessions:
                logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
                
        except Exception as e:
            logger.error(f"Session cleanup failed: {e}")
    
    async def _revoke_all_sessions(self) -> None:
        """Revoke all active sessions"""
        try:
            session_ids = list(self.active_sessions.keys())
            for session_id in session_ids:
                await self.revoke_session(session_id)
        except Exception as e:
            logger.error(f"Failed to revoke all sessions: {e}")
    
    async def _encrypt_credentials(self, credentials: AuthenticationCredentials) -> AuthenticationCredentials:
        """Encrypt sensitive credential data"""
        # Implementation would use proper encryption (AES, etc.)
        # This is a placeholder for the encryption logic
        encrypted_credentials = credentials
        encrypted_credentials.is_encrypted = True
        return encrypted_credentials
    
    async def _decrypt_credentials(self, credentials: AuthenticationCredentials) -> AuthenticationCredentials:
        """Decrypt credential data"""
        # Implementation would use proper decryption
        # This is a placeholder for the decryption logic
        decrypted_credentials = credentials
        decrypted_credentials.is_encrypted = False
        return decrypted_credentials
    
    async def _save_credentials_to_storage(self, credentials: AuthenticationCredentials) -> None:
        """Save credentials to persistent storage"""
        if not self.storage_path:
            return
        
        try:
            cred_file = self.storage_path / f"{credentials.credential_id}.json"
            cred_data = {
                "credential_id": credentials.credential_id,
                "auth_type": credentials.auth_type.value,
                "service_identifier": credentials.service_identifier,
                "username": credentials.username,
                "created_at": credentials.created_at.isoformat(),
                "expires_at": credentials.expires_at.isoformat() if credentials.expires_at else None,
                "is_encrypted": credentials.is_encrypted
                # Note: Sensitive data should be properly encrypted before storage
            }
            
            with open(cred_file, 'w') as f:
                json.dump(cred_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save credentials to storage: {e}")
    
    async def _load_credentials_from_storage(
        self,
        service_identifier: str,
        auth_type: AuthenticationType
    ) -> Optional[AuthenticationCredentials]:
        """Load credentials from persistent storage"""
        if not self.storage_path:
            return None
        
        try:
            # Search for matching credentials file
            for cred_file in self.storage_path.glob("*.json"):
                with open(cred_file, 'r') as f:
                    cred_data = json.load(f)
                
                if (cred_data.get("service_identifier") == service_identifier and
                    cred_data.get("auth_type") == auth_type.value):
                    
                    # Reconstruct credentials object
                    credentials = AuthenticationCredentials(
                        credential_id=cred_data["credential_id"],
                        auth_type=AuthenticationType(cred_data["auth_type"]),
                        service_identifier=cred_data["service_identifier"],
                        username=cred_data.get("username"),
                        created_at=datetime.fromisoformat(cred_data["created_at"]),
                        expires_at=datetime.fromisoformat(cred_data["expires_at"]) if cred_data.get("expires_at") else None,
                        is_encrypted=cred_data.get("is_encrypted", False)
                    )
                    
                    return credentials
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to load credentials from storage: {e}")
            return None
    
    async def _load_stored_credentials(self) -> None:
        """Load all stored credentials into cache"""
        if not self.storage_path:
            return
        
        try:
            for cred_file in self.storage_path.glob("*.json"):
                with open(cred_file, 'r') as f:
                    cred_data = json.load(f)
                
                credentials = AuthenticationCredentials(
                    credential_id=cred_data["credential_id"],
                    auth_type=AuthenticationType(cred_data["auth_type"]),
                    service_identifier=cred_data["service_identifier"],
                    username=cred_data.get("username"),
                    created_at=datetime.fromisoformat(cred_data["created_at"]),
                    is_encrypted=cred_data.get("is_encrypted", False)
                )
                
                cache_key = f"{credentials.service_identifier}_{credentials.auth_type.value}"
                self.credential_cache[cache_key] = credentials
            
            logger.info(f"Loaded {len(self.credential_cache)} stored credentials")
            
        except Exception as e:
            logger.error(f"Failed to load stored credentials: {e}")
    
    async def _initialize_auth_providers(self) -> None:
        """Initialize default authentication providers"""
        # This would be implemented to load and initialize providers
        # based on configuration
        pass
    
    async def _save_auth_state(self) -> None:
        """Save current authentication state"""
        try:
            if not self.storage_path:
                return
            
            state_data = {
                "active_sessions_count": len(self.active_sessions),
                "registered_providers": list(self.auth_providers.keys()),
                "cached_credentials": len(self.credential_cache),
                "timestamp": datetime.now().isoformat()
            }
            
            state_file = self.storage_path / "auth_state.json"
            with open(state_file, 'w') as f:
                json.dump(state_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save auth state: {e}")
    
    def _setup_audit_logging(self) -> None:
        """Setup audit logging for authentication events"""
        try:
            self.audit_logger = logging.getLogger("auth_audit")
            
            if self.config.audit_log_path:
                audit_path = Path(self.config.audit_log_path)
                audit_path.mkdir(parents=True, exist_ok=True)
                
                handler = logging.FileHandler(audit_path / "auth_audit.log")
                formatter = logging.Formatter(
                    '%(asctime)s - %(levelname)s - %(message)s'
                )
                handler.setFormatter(formatter)
                self.audit_logger.addHandler(handler)
                self.audit_logger.setLevel(logging.INFO)
                
        except Exception as e:
            logger.error(f"Failed to setup audit logging: {e}")
    
    async def _audit_log(self, event_type: str, event_data: Dict[str, Any]) -> None:
        """Log authentication audit event"""
        try:
            if not self.audit_logger:
                return
            
            audit_entry = {
                "event_type": event_type,
                "timestamp": datetime.now().isoformat(),
                "data": event_data
            }
            
            self.audit_logger.info(json.dumps(audit_entry))
            
        except Exception as e:
            logger.error(f"Audit logging failed: {e}")
    
    def _generate_session_id(self) -> str:
        """Generate unique session ID"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        random_part = secrets.token_hex(8)
        return f"auth_session_{timestamp}_{random_part}"


# Factory function for creating authentication manager
def create_auth_manager(config: Optional[AuthenticationConfig] = None) -> AuthenticationManager:
    """Factory function to create an authentication manager"""
    if config is None:
        config = AuthenticationConfig()
    
    return AuthenticationManager(config)